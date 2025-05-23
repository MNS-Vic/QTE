#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE自定义Binance现货网关

基于Binance官方最新API规范（2024-12-09）实现的vnpy Gateway
支持连接QTE本地模拟交易所或真实Binance API
"""

import json
import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlencode
from threading import Lock
from decimal import Decimal

from qte.vnpy import check_vnpy_availability

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.event import EventEngine
    from vnpy.trader.gateway import BaseGateway
    from vnpy.trader.object import (
        TickData, OrderData, TradeData, AccountData, ContractData,
        BarData, OrderRequest, CancelRequest, SubscribeRequest,
    )
    from vnpy.trader.constant import Exchange, Product, Status, OrderType, Direction
    from vnpy.trader.event import EVENT_TIMER
else:
    # 如果vnpy不可用，创建模拟类
    BaseGateway = object
    EventEngine = object
    Exchange = object
    Product = object
    # 添加所有缺失的类型定义
    TickData = object
    OrderData = object
    TradeData = object
    AccountData = object
    ContractData = object
    BarData = object
    OrderRequest = object
    CancelRequest = object
    SubscribeRequest = object
    Status = object
    OrderType = object
    Direction = object
    EVENT_TIMER = "EVENT_TIMER"

import requests
import websocket
from qte.core.time_manager import get_current_timestamp


class QTEBinanceSpotGateway(BaseGateway):
    """
    QTE自定义Binance现货网关
    
    支持两种模式：
    1. 本地模拟模式：连接QTE内部模拟交易所API
    2. 真实API模式：连接Binance官方API
    """
    
    # 网关信息
    default_name = "QTE_BINANCE_SPOT"
    default_setting = {
        "API密钥": "",
        "私钥": "",
        "服务器": "QTE_MOCK",  # 默认连接QTE虚拟交易所
        "代理地址": "",
        "代理端口": 0,
    }
    
    # 交易所映射 - 使用OTC或LOCAL代替BINANCE
    if VNPY_AVAILABLE:
        try:
            # 尝试使用OTC交易所代码代替BINANCE
            exchanges = [Exchange.OTC]  
        except:
            exchanges = []
    else:
        exchanges = []
    
    def __init__(self, event_engine: EventEngine, gateway_name: str = None):
        """初始化网关"""
        if not VNPY_AVAILABLE:
            raise ImportError(f"vnpy核心组件不可用：{VNPY_INFO['missing_deps']}")
            
        super().__init__(event_engine, gateway_name or self.default_name)
        
        # API配置
        self.api_key: str = ""
        self.secret_key: str = ""
        self.server_type: str = "REAL"
        self.proxy_host: str = ""
        self.proxy_port: int = 0
        
        # 服务器地址配置 - 重点关注QTE_MOCK
        self.server_configs = {
            "QTE_MOCK": {
                "rest_host": "http://localhost:5001",  # QTE虚拟交易所
                "ws_host": "ws://localhost:5001",      # QTE WebSocket
                "description": "QTE虚拟交易所 - 主要模式"
            },
            "REAL": {
                "rest_host": "https://api.binance.com",
                "ws_host": "wss://stream.binance.com:9443",
                "description": "真实Binance API - 仅用于参考或特殊用途"
            },
            "TESTNET": {
                "rest_host": "https://testnet.binance.vision", 
                "ws_host": "wss://testnet.binance.vision",
                "description": "Binance测试网 - 用于开发测试"
            }
        }
        
        # 运行状态
        self.connect_status: bool = False
        self.login_status: bool = False
        self.ws_api_key: str = ""
        
        # 数据缓存
        self.order_count: int = 0
        self.order_count_lock: Lock = Lock()
        self.orders: Dict[str, OrderData] = {}
        self.trades: Set[str] = set()
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}
        self.ticks: Dict[str, TickData] = {}
        
        # WebSocket连接
        self.ws_public = None
        self.ws_private = None
        
        # 请求管理
        self.requests: Dict[int, Any] = {}
        self.request_id: int = 0
        
        print(f"QTE Binance现货网关已初始化 - 目标: {self.server_configs[self.server_type]['description']}")
        
    def connect(self, setting: dict) -> None:
        """连接到交易所"""
        self.api_key = setting["API密钥"]
        self.secret_key = setting["私钥"]
        self.server_type = setting.get("服务器", "REAL")
        self.proxy_host = setting.get("代理地址", "")
        self.proxy_port = setting.get("代理端口", 0)
        
        self.write_log(f"开始连接{self.server_type}服务器")
        
        # 测试REST API连接
        if self._test_connection():
            self.connect_status = True
            self.write_log("REST API连接成功")
            
            # 获取交易所信息
            self._query_contracts()
            
            # 如果有API密钥，则进行账户相关操作
            if self.api_key and self.secret_key:
                # 测试账户权限
                if self._test_account():
                    self.login_status = True
                    self.write_log("账户验证成功")
                    
                    # 查询账户信息
                    self._query_account()
                    self._query_orders()
                    
                    # 连接私有WebSocket
                    self._connect_ws_private()
                else:
                    self.write_log("账户验证失败，请检查API密钥")
            
            # 连接公共WebSocket
            self._connect_ws_public()
            
        else:
            self.write_log("REST API连接失败")
    
    def close(self) -> None:
        """断开连接"""
        self.connect_status = False
        self.login_status = False
        
        if self.ws_public:
            self.ws_public.close()
        if self.ws_private:
            self.ws_private.close()
            
        self.write_log("连接已断开")
    
    def subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        if not self.connect_status:
            return
            
        # 通过WebSocket订阅tick数据
        symbol = req.symbol.lower()
        
        # 订阅深度数据
        self._subscribe_depth(symbol)
        
        # 订阅成交数据  
        self._subscribe_trade(symbol)
        
        # 订阅24小时统计
        self._subscribe_ticker(symbol)
    
    def send_order(self, req: OrderRequest) -> str:
        """发送委托"""
        if not self.login_status:
            self.write_log("未登录，无法发送委托")
            return ""
        
        # 生成本地订单号
        with self.order_count_lock:
            self.order_count += 1
            orderid = str(self.order_count)
        
        # 构建订单参数
        params = {
            "symbol": req.symbol,
            "side": "BUY" if req.direction == Direction.LONG else "SELL",
            "type": self._convert_order_type(req.type),
            "quantity": str(req.volume),
            "timestamp": get_current_timestamp(),
        }
        
        # 添加价格信息
        if req.type in [OrderType.LIMIT, OrderType.STOP]:
            params["price"] = str(req.price)
            params["timeInForce"] = "GTC"
        
        # 发送REST请求
        try:
            response = self._request_with_auth("POST", "/api/v3/order", params)
            if response:
                self.write_log(f"委托发送成功：{orderid}")
                return orderid
            else:
                self.write_log(f"委托发送失败：{orderid}")
                return ""
        except Exception as e:
            self.write_log(f"委托发送异常：{e}")
            return ""
    
    def cancel_order(self, req: CancelRequest) -> None:
        """撤销委托"""
        if not self.login_status:
            self.write_log("未登录，无法撤销委托")
            return
        
        params = {
            "symbol": req.symbol,
            "orderId": req.orderid,
            "timestamp": get_current_timestamp(),
        }
        
        try:
            response = self._request_with_auth("DELETE", "/api/v3/order", params)
            if response:
                self.write_log(f"委托撤销成功：{req.orderid}")
            else:
                self.write_log(f"委托撤销失败：{req.orderid}")
        except Exception as e:
            self.write_log(f"委托撤销异常：{e}")
    
    def query_account(self) -> None:
        """查询账户资金"""
        if not self.login_status:
            return
        self._query_account()
    
    def query_position(self) -> None:
        """查询持仓（现货无持仓概念）"""
        pass
    
    # ================== 私有方法 ==================
    
    def _test_connection(self) -> bool:
        """测试连接"""
        try:
            config = self.server_configs[self.server_type]
            response = requests.get(
                f"{config['rest_host']}/api/v3/ping",
                timeout=10,
                proxies=self._get_proxies()
            )
            return response.status_code == 200
        except Exception as e:
            self.write_log(f"连接测试失败：{e}")
            return False
    
    def _test_account(self) -> bool:
        """测试账户权限"""
        try:
            params = {"timestamp": get_current_timestamp()}
            response = self._request_with_auth("GET", "/api/v3/account", params)
            return response is not None
        except Exception:
            return False
    
    def _query_contracts(self) -> None:
        """查询合约信息"""
        try:
            config = self.server_configs[self.server_type]
            response = requests.get(
                f"{config['rest_host']}/api/v3/exchangeInfo",
                timeout=10,
                proxies=self._get_proxies()
            )
            
            if response.status_code == 200:
                data = response.json()
                for symbol_data in data["symbols"]:
                    if symbol_data["status"] == "TRADING":
                        contract = ContractData(
                            symbol=symbol_data["symbol"],
                            exchange=Exchange.BINANCE,
                            name=symbol_data["symbol"],
                            product=Product.SPOT,
                            size=1,
                            pricetick=float(next(
                                f["tickSize"] for f in symbol_data["filters"] 
                                if f["filterType"] == "PRICE_FILTER"
                            )),
                            min_volume=float(next(
                                f["minQty"] for f in symbol_data["filters"]
                                if f["filterType"] == "LOT_SIZE"
                            )),
                            gateway_name=self.gateway_name
                        )
                        self.contracts[contract.symbol] = contract
                        self.on_contract(contract)
                
                self.write_log(f"合约信息查询成功，共{len(self.contracts)}个合约")
            
        except Exception as e:
            self.write_log(f"合约信息查询失败：{e}")
    
    def _query_account(self) -> None:
        """查询账户信息"""
        try:
            params = {"timestamp": get_current_timestamp()}
            response = self._request_with_auth("GET", "/api/v3/account", params)
            
            if response:
                for balance_data in response["balances"]:
                    asset = balance_data["asset"]
                    free = float(balance_data["free"])
                    locked = float(balance_data["locked"])
                    
                    if free > 0 or locked > 0:
                        account = AccountData(
                            accountid=asset,
                            balance=free + locked,
                            frozen=locked,
                            gateway_name=self.gateway_name
                        )
                        self.accounts[asset] = account
                        self.on_account(account)
                
                self.write_log("账户信息查询成功")
                
        except Exception as e:
            self.write_log(f"账户信息查询失败：{e}")
    
    def _query_orders(self) -> None:
        """查询活动订单"""
        try:
            params = {"timestamp": get_current_timestamp()}
            response = self._request_with_auth("GET", "/api/v3/openOrders", params)
            
            if response:
                for order_data in response:
                    order = self._parse_order_data(order_data)
                    self.orders[order.orderid] = order
                    self.on_order(order)
                
                self.write_log(f"活动订单查询成功，共{len(response)}个订单")
                
        except Exception as e:
            self.write_log(f"活动订单查询失败：{e}")
    
    def _request_with_auth(self, method: str, path: str, params: dict = None) -> Optional[dict]:
        """发送带签名的请求"""
        if params is None:
            params = {}
        
        # 添加API密钥
        headers = {"X-MBX-APIKEY": self.api_key}
        
        # 生成签名
        if self.secret_key:
            query_string = urlencode(sorted(params.items()))
            signature = hmac.new(
                self.secret_key.encode(),
                query_string.encode(),
                hashlib.sha256
            ).hexdigest()
            params["signature"] = signature
        
        # 发送请求
        config = self.server_configs[self.server_type]
        url = f"{config['rest_host']}{path}"
        
        try:
            if method == "GET":
                response = requests.get(
                    url, params=params, headers=headers,
                    timeout=10, proxies=self._get_proxies()
                )
            elif method == "POST":
                response = requests.post(
                    url, data=params, headers=headers,
                    timeout=10, proxies=self._get_proxies()
                )
            elif method == "DELETE":
                response = requests.delete(
                    url, params=params, headers=headers,
                    timeout=10, proxies=self._get_proxies()
                )
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                self.write_log(f"请求失败：{response.status_code} {response.text}")
                return None
                
        except Exception as e:
            self.write_log(f"请求异常：{e}")
            return None
    
    def _get_proxies(self) -> Optional[dict]:
        """获取代理配置"""
        if self.proxy_host and self.proxy_port:
            return {
                "http": f"http://{self.proxy_host}:{self.proxy_port}",
                "https": f"https://{self.proxy_host}:{self.proxy_port}"
            }
        return None
    
    def _convert_order_type(self, order_type: OrderType) -> str:
        """转换订单类型"""
        if order_type == OrderType.MARKET:
            return "MARKET"
        elif order_type == OrderType.LIMIT:
            return "LIMIT" 
        elif order_type == OrderType.STOP:
            return "STOP_LOSS_LIMIT"
        else:
            return "LIMIT"
    
    def _parse_order_data(self, data: dict) -> OrderData:
        """解析订单数据"""
        order = OrderData(
            symbol=data["symbol"],
            exchange=Exchange.BINANCE,
            orderid=str(data["orderId"]),
            type=self._parse_order_type(data["type"]),
            direction=Direction.LONG if data["side"] == "BUY" else Direction.SHORT,
            offset=Offset.NONE,
            price=float(data["price"]) if data["price"] else 0,
            volume=float(data["origQty"]),
            traded=float(data["executedQty"]),
            status=self._parse_order_status(data["status"]),
            datetime=datetime.fromtimestamp(data["time"] / 1000, timezone.utc),
            gateway_name=self.gateway_name
        )
        return order
    
    def _parse_order_type(self, type_str: str) -> OrderType:
        """解析订单类型"""
        if type_str == "MARKET":
            return OrderType.MARKET
        elif type_str == "LIMIT":
            return OrderType.LIMIT
        elif type_str in ["STOP_LOSS", "STOP_LOSS_LIMIT"]:
            return OrderType.STOP
        else:
            return OrderType.LIMIT
    
    def _parse_order_status(self, status_str: str) -> Status:
        """解析订单状态"""
        if status_str == "NEW":
            return Status.NOTTRADED
        elif status_str == "PARTIALLY_FILLED":
            return Status.PARTTRADED
        elif status_str == "FILLED":
            return Status.ALLTRADED
        elif status_str == "CANCELED":
            return Status.CANCELLED
        elif status_str == "REJECTED":
            return Status.REJECTED
        else:
            return Status.SUBMITTING
    
    def _connect_ws_public(self) -> None:
        """连接公共WebSocket"""
        try:
            from qte.exchange.websocket.websocket_client import ExchangeWebSocketClient
            import asyncio
            
            # 创建WebSocket客户端
            ws_host, ws_port = self._parse_websocket_address()
            self.ws_public_client = ExchangeWebSocketClient(
                host=ws_host,
                port=ws_port
            )
            
            # 在后台启动WebSocket连接
            asyncio.create_task(self._start_public_websocket())
            self.write_log("公共WebSocket连接启动中...")
            
        except Exception as e:
            self.write_log(f"启动公共WebSocket失败: {e}")
    
    def _connect_ws_private(self) -> None:
        """连接私有WebSocket"""
        if not self.api_key or not self.secret_key:
            self.write_log("私有WebSocket需要API密钥，跳过连接")
            return
            
        try:
            from qte.exchange.websocket.websocket_client import ExchangeWebSocketClient
            import asyncio
            
            # 创建带认证的WebSocket客户端
            ws_host, ws_port = self._parse_websocket_address()
            self.ws_private_client = ExchangeWebSocketClient(
                host=ws_host,
                port=ws_port,
                api_key=self.api_key
            )
            
            # 在后台启动WebSocket连接
            asyncio.create_task(self._start_private_websocket())
            self.write_log("私有WebSocket连接启动中...")
            
        except Exception as e:
            self.write_log(f"启动私有WebSocket失败: {e}")
    
    def _parse_websocket_address(self) -> tuple:
        """解析WebSocket地址"""
        server_config = self.server_configs.get(self.server_type, {})
        ws_host = server_config.get("ws_host", "ws://localhost:8765")
        
        # 解析host和port
        if "://" in ws_host:
            ws_host = ws_host.split("://")[1]
        
        if ":" in ws_host:
            host, port = ws_host.split(":")
            return host, int(port)
        else:
            return ws_host, 8765
    
    async def _start_public_websocket(self):
        """启动公共WebSocket连接"""
        try:
            # 连接WebSocket
            connected = await self.ws_public_client.connect()
            if not connected:
                self.write_log("公共WebSocket连接失败")
                return
            
            self.write_log("公共WebSocket连接成功")
            
            # 注册消息回调
            for symbol in self.subscribed_symbols:
                stream = f"{symbol.lower()}@ticker"
                self.ws_public_client.add_message_callback(stream, self._on_public_message)
                
            # 订阅已请求的行情
            if hasattr(self, 'subscribed_symbols') and self.subscribed_symbols:
                streams = [f"{symbol.lower()}@ticker" for symbol in self.subscribed_symbols]
                await self.ws_public_client.subscribe(streams)
                self.write_log(f"已订阅公共行情: {streams}")
                
        except Exception as e:
            self.write_log(f"公共WebSocket启动错误: {e}")
    
    async def _start_private_websocket(self):
        """启动私有WebSocket连接"""
        try:
            # 连接并认证WebSocket
            connected = await self.ws_private_client.connect()
            if not connected:
                self.write_log("私有WebSocket连接失败")
                return
            
            self.write_log("私有WebSocket连接成功")
            
            # 订阅用户数据流
            user_stream = f"user@{self.api_key}"
            self.ws_private_client.add_message_callback(user_stream, self._on_private_message)
            await self.ws_private_client.subscribe([user_stream])
            self.write_log(f"已订阅私有数据流: {user_stream}")
            
        except Exception as e:
            self.write_log(f"私有WebSocket启动错误: {e}")
    
    def _on_public_message(self, message: dict):
        """处理公共WebSocket消息"""
        try:
            if message.get("stream") and "@ticker" in message["stream"]:
                # 处理行情数据
                data = message.get("data", {})
                symbol = data.get("symbol", "").upper()
                
                if symbol:
                    tick = TickData(
                        symbol=symbol,
                        exchange=Exchange.OTC,
                        datetime=datetime.now(),
                        last_price=float(data.get("price", 0)),
                        volume=float(data.get("volume", 0)),
                        open_price=float(data.get("open", 0)),
                        high_price=float(data.get("high", 0)),
                        low_price=float(data.get("low", 0)),
                        pre_close=float(data.get("prevClose", 0)),
                        gateway_name=self.gateway_name
                    )
                    self.on_tick(tick)
                    
        except Exception as e:
            self.write_log(f"处理公共WebSocket消息错误: {e}")
    
    def _on_private_message(self, message: dict):
        """处理私有WebSocket消息"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "order":
                # 处理订单更新
                order_data = message.get("data", {})
                order = self._parse_order_data(order_data)
                self.on_order(order)
                
            elif msg_type == "trade":
                # 处理成交更新
                trade_data = message.get("data", {})
                trade = self._parse_trade_data(trade_data)
                self.on_trade(trade)
                
            elif msg_type == "account":
                # 处理账户更新
                account_data = message.get("data", {})
                account = self._parse_account_data(account_data)
                self.on_account(account)
                
        except Exception as e:
            self.write_log(f"处理私有WebSocket消息错误: {e}")
    
    def _parse_trade_data(self, data: dict) -> TradeData:
        """解析成交数据"""
        return TradeData(
            symbol=data["symbol"],
            exchange=Exchange.OTC,
            orderid=data["orderId"],
            tradeid=data["tradeId"],
            direction=Direction.LONG if data["side"] == "BUY" else Direction.SHORT,
            price=float(data["price"]),
            volume=float(data["quantity"]),
            datetime=datetime.fromtimestamp(data["timestamp"] / 1000),
            gateway_name=self.gateway_name
        )
    
    def _parse_account_data(self, data: dict) -> AccountData:
        """解析账户数据"""
        return AccountData(
            accountid=data.get("accountId", "default"),
            balance=float(data.get("balance", 0)),
            frozen=float(data.get("frozen", 0)),
            gateway_name=self.gateway_name
        )
    
    def _subscribe_depth(self, symbol: str) -> None:
        """订阅深度数据"""
        # WebSocket深度订阅实现
        pass
    
    def _subscribe_trade(self, symbol: str) -> None:
        """订阅成交数据"""
        # WebSocket成交订阅实现
        pass
    
    def _subscribe_ticker(self, symbol: str) -> None:
        """订阅行情统计"""
        # WebSocket统计订阅实现
        pass


# 如果vnpy不可用，提供一个空的实现
if not VNPY_AVAILABLE:
    class QTEBinanceSpotGateway:
        """vnpy不可用时的空实现"""
        def __init__(self, *args, **kwargs):
            raise ImportError("vnpy未安装，请先安装vnpy包")

__all__ = ["QTEBinanceSpotGateway"] 