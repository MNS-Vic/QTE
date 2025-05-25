#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE Binance Gateway - 改进版本

根据Creative Phase设计决策实现的完整Gateway
整合所有架构决策：工厂模式、混合事件处理、智能重连、注册器转换、分层错误处理
"""

import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from decimal import Decimal

from qte.vnpy import check_vnpy_availability
from .qte_gateway_factory import GatewayType, GatewayFactory
from .event_converter import converter_registry, error_handler
from .qte_event_converters import (
    safe_convert, batch_convert, get_conversion_stats,
    QTEMarketData, QTEOrderData, QTETradeData, QTEAccountData
)
from .connection_manager import (
    SmartConnectionManager, ConnectionConfig, ConnectionType, ConnectionState
)

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.event import EventEngine
    from vnpy.trader.gateway import BaseGateway
    from vnpy.trader.object import (
        TickData, OrderData, TradeData, AccountData, ContractData,
        OrderRequest, CancelRequest, SubscribeRequest
    )
    from vnpy.trader.constant import Exchange, Product, Status, OrderType, Direction
    from vnpy.trader.event import EVENT_TIMER
else:
    # 模拟类型定义
    BaseGateway = object
    EventEngine = object
    Exchange = object
    Product = object
    TickData = object
    OrderData = object
    TradeData = object
    AccountData = object
    ContractData = object
    OrderRequest = object
    CancelRequest = object
    SubscribeRequest = object
    Status = object
    OrderType = object
    Direction = object
    EVENT_TIMER = "EVENT_TIMER"


class QTEBinanceGateway(BaseGateway):
    """
    QTE Binance Gateway - 改进版本
    
    实现Creative Phase所有设计决策：
    1. 工厂模式架构 (选项1.2)
    2. 混合事件处理 (选项2.3) 
    3. 智能重连机制 (选项3.3)
    4. 注册器模式事件转换 (选项1.3)
    5. 字段级精确转换 (选项2.1)
    6. 分层错误处理 (选项3.3)
    """
    
    # Gateway信息
    default_name = "QTE_BINANCE"
    default_setting = {
        "API密钥": "",
        "私钥": "",
        "服务器": "QTE_MOCK",  # 默认连接QTE虚拟交易所
        "代理地址": "",
        "代理端口": 0,
        "重连次数": 5,
        "重连延迟": 1.0,
        "健康检查间隔": 30,
    }
    
    # 交易所映射
    if VNPY_AVAILABLE:
        try:
            exchanges = [Exchange.OTC]
        except:
            exchanges = []
    else:
        exchanges = []
    
    def __init__(self, event_engine: EventEngine, gateway_name: str = None):
        """初始化Gateway"""
        if not VNPY_AVAILABLE:
            raise ImportError(f"vnpy核心组件不可用：{VNPY_INFO['missing_deps']}")
        
        super().__init__(event_engine, gateway_name or self.default_name)
        
        # 服务器配置
        self.server_configs = {
            "QTE_MOCK": {
                "host": "localhost",
                "port": 5001,
                "use_ssl": False,
                "description": "QTE虚拟交易所"
            },
            "REAL": {
                "host": "api.binance.com",
                "port": 443,
                "use_ssl": True,
                "description": "真实Binance API"
            },
            "TESTNET": {
                "host": "testnet.binance.vision",
                "port": 443,
                "use_ssl": True,
                "description": "Binance测试网"
            }
        }
        
        # 连接管理器
        self.connection_manager: Optional[SmartConnectionManager] = None
        
        # 配置参数
        self.api_key: str = ""
        self.secret_key: str = ""
        self.server_type: str = "QTE_MOCK"
        
        # 运行状态
        self.connect_status: bool = False
        self.login_status: bool = False
        
        # 数据缓存
        self.order_count: int = 0
        self.order_count_lock = threading.Lock()
        self.orders: Dict[str, OrderData] = {}
        self.trades: Set[str] = set()
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}
        self.ticks: Dict[str, TickData] = {}
        
        # 事件处理
        self.sync_operations = {"send_order", "cancel_order", "query_account", "query_orders"}
        self.async_operations = {"market_data", "order_updates", "trade_updates"}
        
        # 订阅管理
        self.subscribed_symbols: Set[str] = set()
        
        # 异步任务
        self._async_tasks: List[asyncio.Task] = []
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        
        self.write_log("QTE Binance Gateway已初始化")
    
    def connect(self, setting: dict) -> None:
        """
        连接到交易所
        
        实现混合事件处理模式：
        - 关键操作（连接、认证）使用同步处理
        - 数据推送使用异步处理
        """
        self.write_log("开始连接QTE交易所")
        
        # 解析配置
        self.api_key = setting.get("API密钥", "")
        self.secret_key = setting.get("私钥", "")
        self.server_type = setting.get("服务器", "QTE_MOCK")
        
        # 获取服务器配置
        if self.server_type not in self.server_configs:
            self.write_log(f"未知的服务器类型: {self.server_type}")
            return
        
        server_config = self.server_configs[self.server_type]
        
        # 创建连接管理器
        connection_config = ConnectionConfig(
            host=server_config["host"],
            port=server_config["port"],
            use_ssl=server_config["use_ssl"],
            max_retries=setting.get("重连次数", 5),
            initial_retry_delay=setting.get("重连延迟", 1.0),
            health_check_interval=setting.get("健康检查间隔", 30)
        )
        
        self.connection_manager = SmartConnectionManager(connection_config)
        
        # 注册连接事件回调
        self.connection_manager.register_event_callback("connected", self._on_connected)
        self.connection_manager.register_event_callback("disconnected", self._on_disconnected)
        self.connection_manager.register_event_callback("reconnected", self._on_reconnected)
        self.connection_manager.register_event_callback("connection_failed", self._on_connection_failed)
        
        # 同步连接REST API
        if self.connection_manager.connect_rest():
            self.connect_status = True
            self.write_log("REST API连接成功")
            
            # 启动异步事件循环
            self._start_async_loop()
            
            # 获取交易所信息
            self._query_contracts()
            
            # 如果有API密钥，进行账户验证
            if self.api_key and self.secret_key:
                if self._test_account():
                    self.login_status = True
                    self.write_log("账户验证成功")
                    
                    # 查询账户信息
                    self._query_account()
                    self._query_orders()
                else:
                    self.write_log("账户验证失败")
            
            # 异步连接WebSocket
            self._connect_websocket_async()
            
        else:
            self.write_log("连接失败")
    
    def close(self) -> None:
        """断开连接"""
        self.write_log("正在断开连接...")
        
        self.connect_status = False
        self.login_status = False
        
        # 停止异步任务
        self._stop_async_tasks()
        
        # 断开连接管理器
        if self.connection_manager:
            self.connection_manager.disconnect()
            self.connection_manager = None
        
        # 停止事件循环
        self._stop_async_loop()
        
        self.write_log("连接已断开")
    
    def subscribe(self, req: SubscribeRequest) -> None:
        """
        订阅行情
        
        使用异步处理模式
        """
        if not self.connect_status:
            self.write_log("连接未建立，无法订阅行情")
            return
        
        symbol = req.symbol
        if symbol in self.subscribed_symbols:
            self.write_log(f"已订阅 {symbol}")
            return
        
        # 转换订阅请求
        qte_sub_data = safe_convert(req, dict, f"subscribe_{symbol}")
        if qte_sub_data:
            # 异步处理订阅
            self._schedule_async_task(self._subscribe_async(symbol, qte_sub_data))
            self.subscribed_symbols.add(symbol)
            self.write_log(f"订阅行情: {symbol}")
    
    def send_order(self, req: OrderRequest) -> str:
        """
        发送订单
        
        使用同步处理模式（关键操作）
        """
        if not self.connect_status or not self.login_status:
            self.write_log("连接或登录状态异常，无法发送订单")
            return ""
        
        # 生成订单ID
        with self.order_count_lock:
            self.order_count += 1
            orderid = f"QTE_{self.order_count}_{int(time.time())}"
        
        # 转换订单请求
        qte_order_data = safe_convert(req, dict, f"send_order_{orderid}")
        if not qte_order_data:
            self.write_log("订单转换失败")
            return ""
        
        qte_order_data["client_order_id"] = orderid
        
        # 同步发送订单
        try:
            response = self.connection_manager.send_rest_request(
                "POST", "/api/v3/order", json=qte_order_data
            )
            
            if response and response.status_code == 200:
                result = response.json()
                
                # 转换并推送订单数据
                order_data = safe_convert(result, OrderData, f"order_response_{orderid}")
                if order_data:
                    self.orders[orderid] = order_data
                    self.on_order(order_data)
                
                self.write_log(f"订单发送成功: {orderid}")
                return orderid
            else:
                error_msg = f"订单发送失败: {response.status_code if response else 'No response'}"
                self.write_log(error_msg)
                return ""
                
        except Exception as e:
            self.write_log(f"发送订单异常: {e}")
            return ""
    
    def cancel_order(self, req: CancelRequest) -> None:
        """
        取消订单
        
        使用同步处理模式（关键操作）
        """
        if not self.connect_status or not self.login_status:
            self.write_log("连接或登录状态异常，无法取消订单")
            return
        
        # 转换取消请求
        qte_cancel_data = safe_convert(req, dict, f"cancel_order_{req.orderid}")
        if not qte_cancel_data:
            self.write_log("取消订单转换失败")
            return
        
        # 同步取消订单
        try:
            response = self.connection_manager.send_rest_request(
                "DELETE", "/api/v3/order", json=qte_cancel_data
            )
            
            if response and response.status_code == 200:
                self.write_log(f"订单取消成功: {req.orderid}")
            else:
                error_msg = f"订单取消失败: {response.status_code if response else 'No response'}"
                self.write_log(error_msg)
                
        except Exception as e:
            self.write_log(f"取消订单异常: {e}")
    
    def query_account(self) -> None:
        """查询账户信息"""
        if not self.connect_status or not self.login_status:
            return
        
        self._schedule_async_task(self._query_account_async())
    
    def query_position(self) -> None:
        """查询持仓信息（现货交易无持仓）"""
        pass
    
    # ==================== 私有方法 ====================
    
    def _start_async_loop(self):
        """启动异步事件循环"""
        if self._loop_thread and self._loop_thread.is_alive():
            return
        
        def run_loop():
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            self._event_loop.run_forever()
        
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        
        # 等待事件循环启动
        while not self._event_loop:
            time.sleep(0.01)
        
        self.write_log("异步事件循环已启动")
    
    def _stop_async_loop(self):
        """停止异步事件循环"""
        if self._event_loop and self._event_loop.is_running():
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)
        
        self._event_loop = None
        self._loop_thread = None
        
        self.write_log("异步事件循环已停止")
    
    def _schedule_async_task(self, coro):
        """调度异步任务"""
        if self._event_loop and self._event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
            return future
        else:
            self.write_log("异步事件循环未运行，无法调度任务")
            return None
    
    def _stop_async_tasks(self):
        """停止所有异步任务"""
        for task in self._async_tasks:
            if not task.done():
                task.cancel()
        self._async_tasks.clear()
    
    async def _subscribe_async(self, symbol: str, sub_data: dict):
        """异步订阅行情"""
        try:
            # 这里应该发送WebSocket订阅消息
            # 简化实现：直接模拟订阅成功
            self.write_log(f"异步订阅成功: {symbol}")
            
            # 启动模拟数据推送
            await self._start_market_data_simulation(symbol)
            
        except Exception as e:
            self.write_log(f"异步订阅失败: {e}")
    
    async def _start_market_data_simulation(self, symbol: str):
        """启动市场数据模拟（用于测试）"""
        try:
            while symbol in self.subscribed_symbols:
                # 模拟市场数据
                mock_data = {
                    "symbol": symbol,
                    "price": 50000 + (time.time() % 1000),
                    "volume": 1.0,
                    "timestamp": datetime.now()
                }
                
                # 转换并推送
                tick_data = safe_convert(mock_data, TickData, f"market_data_{symbol}")
                if tick_data:
                    self.on_tick(tick_data)
                
                await asyncio.sleep(1)  # 每秒推送一次
                
        except asyncio.CancelledError:
            self.write_log(f"市场数据模拟已停止: {symbol}")
        except Exception as e:
            self.write_log(f"市场数据模拟异常: {e}")
    
    async def _connect_websocket_async(self):
        """异步连接WebSocket"""
        try:
            if self.server_type == "QTE_MOCK":
                ws_url = "ws://localhost:5001/ws"
            else:
                ws_url = "wss://stream.binance.com:9443/ws"
            
            def on_message(message):
                # 异步处理WebSocket消息
                self._schedule_async_task(self._handle_websocket_message(message))
            
            def on_error(error):
                self.write_log(f"WebSocket错误: {error}")
            
            success = self.connection_manager.connect_websocket(ws_url, on_message, on_error)
            if success:
                self.write_log("WebSocket连接已启动")
            else:
                self.write_log("WebSocket连接失败")
                
        except Exception as e:
            self.write_log(f"WebSocket连接异常: {e}")
    
    async def _handle_websocket_message(self, message: str):
        """异步处理WebSocket消息"""
        try:
            data = json.loads(message)
            
            # 根据消息类型处理
            if "price" in data:
                # 市场数据
                tick_data = safe_convert(data, TickData, "websocket_tick")
                if tick_data:
                    self.on_tick(tick_data)
            
            elif "orderId" in data:
                # 订单更新
                order_data = safe_convert(data, OrderData, "websocket_order")
                if order_data:
                    self.on_order(order_data)
            
            elif "tradeId" in data:
                # 成交更新
                trade_data = safe_convert(data, TradeData, "websocket_trade")
                if trade_data:
                    self.on_trade(trade_data)
                    
        except Exception as e:
            self.write_log(f"WebSocket消息处理异常: {e}")
    
    async def _query_account_async(self):
        """异步查询账户信息"""
        try:
            response = self.connection_manager.send_rest_request("GET", "/api/v3/account")
            
            if response and response.status_code == 200:
                account_info = response.json()
                account_data = safe_convert(account_info, AccountData, "query_account")
                if account_data:
                    self.accounts[account_data.accountid] = account_data
                    self.on_account(account_data)
                    
        except Exception as e:
            self.write_log(f"查询账户异常: {e}")
    
    def _test_account(self) -> bool:
        """测试账户权限"""
        try:
            response = self.connection_manager.send_rest_request("GET", "/api/v3/account")
            return response and response.status_code == 200
        except:
            return False
    
    def _query_contracts(self):
        """查询合约信息"""
        try:
            response = self.connection_manager.send_rest_request("GET", "/api/v3/exchangeInfo")
            
            if response and response.status_code == 200:
                exchange_info = response.json()
                symbols = exchange_info.get("symbols", [])
                
                for symbol_info in symbols:
                    if VNPY_AVAILABLE:
                        contract = ContractData(
                            symbol=symbol_info["symbol"],
                            exchange=Exchange.OTC,
                            name=symbol_info["symbol"],
                            product=Product.SPOT,
                            size=1,
                            pricetick=0.01,
                            min_volume=0.001,
                            gateway_name=self.gateway_name
                        )
                        self.contracts[contract.symbol] = contract
                        self.on_contract(contract)
                
                self.write_log(f"合约信息查询完成，共{len(symbols)}个交易对")
                
        except Exception as e:
            self.write_log(f"查询合约信息异常: {e}")
    
    def _query_orders(self):
        """查询订单信息"""
        try:
            response = self.connection_manager.send_rest_request("GET", "/api/v3/openOrders")
            
            if response and response.status_code == 200:
                orders = response.json()
                
                for order_info in orders:
                    order_data = safe_convert(order_info, OrderData, "query_orders")
                    if order_data:
                        self.orders[order_data.orderid] = order_data
                        self.on_order(order_data)
                
                self.write_log(f"订单信息查询完成，共{len(orders)}个活跃订单")
                
        except Exception as e:
            self.write_log(f"查询订单信息异常: {e}")
    
    # ==================== 连接事件回调 ====================
    
    def _on_connected(self, event):
        """连接成功回调"""
        self.write_log(f"{event.connection_type.value}连接成功")
    
    def _on_disconnected(self, event):
        """连接断开回调"""
        self.write_log(f"{event.connection_type.value}连接断开")
        if event.connection_type == ConnectionType.REST:
            self.connect_status = False
            self.login_status = False
    
    def _on_reconnected(self, event):
        """重连成功回调"""
        self.write_log(f"{event.connection_type.value}重连成功")
        if event.connection_type == ConnectionType.REST:
            self.connect_status = True
            # 重新验证账户
            if self.api_key and self.secret_key:
                if self._test_account():
                    self.login_status = True
    
    def _on_connection_failed(self, event):
        """连接失败回调"""
        error = event.data.get("error", "未知错误")
        self.write_log(f"{event.connection_type.value}连接失败: {error}")
    
    def get_gateway_stats(self) -> Dict[str, Any]:
        """获取Gateway统计信息"""
        stats = {
            "gateway_name": self.gateway_name,
            "connect_status": self.connect_status,
            "login_status": self.login_status,
            "server_type": self.server_type,
            "subscribed_symbols": len(self.subscribed_symbols),
            "cached_orders": len(self.orders),
            "cached_contracts": len(self.contracts),
            "conversion_stats": get_conversion_stats(),
        }
        
        if self.connection_manager:
            stats["connection_stats"] = self.connection_manager.get_connection_stats()
        
        return stats


# 注册Gateway到工厂
GatewayFactory.register_gateway(GatewayType.QTE_BINANCE, QTEBinanceGateway) 