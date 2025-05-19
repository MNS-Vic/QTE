#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于模拟交易所API的简单移动均线策略

此示例展示了如何通过交易所API接口（而非直接调用内部函数）进行交易
"""
import time
import json
import logging
import threading
import asyncio
import numpy as np
import pandas as pd
import requests
import websockets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MAStrategy")

class MovingAverageStrategy:
    """基于移动均线的策略，通过交易所API接口交互"""
    
    def __init__(self, symbol: str, api_key: str, 
                 short_window: int = 5, long_window: int = 20,
                 rest_url: str = "http://localhost:5000", 
                 ws_url: str = "ws://localhost:8765"):
        """
        初始化移动均线策略
        
        Parameters
        ----------
        symbol : str
            交易对，如 "BTCUSDT"
        api_key : str
            API密钥
        short_window : int, optional
            短期均线窗口, by default 5
        long_window : int, optional
            长期均线窗口, by default 20
        rest_url : str, optional
            REST API URL, by default "http://localhost:5000"
        ws_url : str, optional
            WebSocket URL, by default "ws://localhost:8765"
        """
        self.symbol = symbol
        self.api_key = api_key
        self.short_window = short_window
        self.long_window = long_window
        self.rest_url = rest_url
        self.ws_url = ws_url
        
        # REST API请求头
        self.headers = {"X-API-KEY": api_key}
        
        # 策略状态
        self.running = False
        self.position = 0  # 1: 多头, -1: 空头, 0: 空仓
        self.last_signal = None  # 上次信号
        
        # 价格数据
        self.prices = []
        self.price_lock = threading.Lock()
        
        # WebSocket相关
        self.ws_client = None
        self.ws_thread = None
        self.trade_update_queue = asyncio.Queue()
        
        # 订单管理
        self.orders = {}  # 订单ID -> 订单信息
        self.order_lock = threading.Lock()
        
        logger.info(f"策略初始化：{symbol}, 短期={short_window}, 长期={long_window}")
    
    def start(self):
        """启动策略"""
        if self.running:
            logger.warning("策略已在运行")
            return
            
        self.running = True
        
        # 获取初始历史数据
        self._load_historical_data()
        
        # 启动WebSocket连接线程
        self.ws_thread = threading.Thread(target=self._start_ws_client)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # 启动策略主循环
        logger.info("策略启动，开始主循环")
        self._run_strategy_loop()
    
    def stop(self):
        """停止策略"""
        logger.info("正在停止策略...")
        self.running = False
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=5)
        logger.info("策略已停止")
    
    def _load_historical_data(self):
        """加载历史价格数据"""
        try:
            # 获取历史K线数据
            end_time = int(time.time() * 1000)
            start_time = end_time - (self.long_window + 100) * 60 * 1000  # 多获取一些数据
            
            # 这里应该实现获取历史K线的逻辑
            # 在实际交易所中，可以使用GET /api/v1/klines接口
            # 为简化示例，这里使用模拟数据
            
            # 模拟一些随机历史价格
            np.random.seed(42)  # 确保可重复性
            base_price = 20000
            random_moves = np.random.normal(0, 100, self.long_window + 100)
            prices = [base_price]
            for move in random_moves:
                prices.append(prices[-1] + move)
            
            with self.price_lock:
                self.prices = prices
                
            logger.info(f"加载了 {len(self.prices)} 条历史价格数据")
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
    
    def _start_ws_client(self):
        """在单独线程中启动WebSocket客户端"""
        asyncio.run(self._ws_client_loop())
    
    async def _ws_client_loop(self):
        """WebSocket客户端主循环"""
        reconnect_delay = 1  # 重连延迟，秒
        
        while self.running:
            try:
                logger.info(f"正在连接WebSocket: {self.ws_url}")
                async with websockets.connect(self.ws_url) as websocket:
                    # 认证
                    auth_msg = {
                        "method": "auth",
                        "params": {"api_key": self.api_key},
                        "id": 1
                    }
                    await websocket.send(json.dumps(auth_msg))
                    response = await websocket.recv()
                    logger.info(f"认证响应: {response}")
                    
                    # 订阅市场数据
                    subscribe_msg = {
                        "method": "subscribe",
                        "params": {
                            "streams": [f"{self.symbol}@ticker", f"{self.symbol}@trade"]
                        },
                        "id": 2
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    response = await websocket.recv()
                    logger.info(f"市场数据订阅响应: {response}")
                    
                    # 订阅用户数据
                    user_id = self._get_user_id()
                    if user_id:
                        subscribe_user_msg = {
                            "method": "subscribe",
                            "params": {
                                "streams": [f"{user_id}@account", f"{user_id}@order"]
                            },
                            "id": 3
                        }
                        await websocket.send(json.dumps(subscribe_user_msg))
                        response = await websocket.recv()
                        logger.info(f"用户数据订阅响应: {response}")
                    
                    # 重置重连延迟
                    reconnect_delay = 1
                    
                    # 接收消息
                    while self.running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            await self._process_ws_message(data)
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket连接已关闭")
                            break
            except Exception as e:
                logger.error(f"WebSocket错误: {e}")
                
            if self.running:
                logger.info(f"等待 {reconnect_delay} 秒后重新连接...")
                await asyncio.sleep(reconnect_delay)
                # 指数回退重连延迟，最大60秒
                reconnect_delay = min(reconnect_delay * 2, 60)
    
    async def _process_ws_message(self, data: Dict[str, Any]):
        """处理WebSocket消息"""
        try:
            if "stream" not in data:
                logger.warning(f"收到无效的WebSocket消息: {data}")
                return
                
            stream = data["stream"]
            
            # 处理交易对行情
            if f"{self.symbol}@ticker" in stream:
                self._process_ticker(data["data"])
                
            # 处理实时成交
            elif f"{self.symbol}@trade" in stream:
                self._process_trade(data["data"])
                
            # 处理账户更新
            elif "@account" in stream:
                self._process_account_update(data["data"])
                
            # 处理订单更新
            elif "@order" in stream:
                await self._process_order_update(data["data"])
                
        except Exception as e:
            logger.error(f"处理WebSocket消息时出错: {e}")
    
    def _process_ticker(self, data: Dict[str, Any]):
        """处理交易对行情数据"""
        # 此示例中简单记录
        logger.debug(f"收到{self.symbol}行情: 价格={data.get('p')}")
    
    def _process_trade(self, data: Dict[str, Any]):
        """处理实时成交数据"""
        price = float(data.get("p", 0))
        if price > 0:
            with self.price_lock:
                self.prices.append(price)
                # 保持合理的数据量
                if len(self.prices) > self.long_window * 10:
                    self.prices = self.prices[-self.long_window * 2:]
            
            logger.debug(f"收到{self.symbol}成交: 价格={price}, ID={data.get('t')}")
    
    def _process_account_update(self, data: Dict[str, Any]):
        """处理账户更新数据"""
        logger.info(f"账户更新: {data}")
    
    async def _process_order_update(self, data: Dict[str, Any]):
        """处理订单更新数据"""
        order_id = data.get("i")
        status = data.get("X")
        
        if order_id and status:
            with self.order_lock:
                if order_id in self.orders:
                    self.orders[order_id]["status"] = status
                    
            logger.info(f"订单更新: ID={order_id}, 状态={status}")
            
            # 将订单更新加入队列，供策略主循环处理
            await self.trade_update_queue.put(data)
    
    def _run_strategy_loop(self):
        """策略主循环"""
        check_interval = 5  # 每5秒检查一次信号
        last_check_time = 0
        
        while self.running:
            current_time = time.time()
            
            # 检查是否应该生成信号
            if current_time - last_check_time >= check_interval:
                self._check_signals()
                last_check_time = current_time
                
            # 处理其他任务
            self._check_pending_orders()
            
            # 避免CPU占用过高
            time.sleep(0.1)
    
    def _check_signals(self):
        """检查交易信号"""
        with self.price_lock:
            if len(self.prices) < self.long_window:
                logger.warning(f"价格数据不足，需要至少 {self.long_window} 条数据")
                return
                
            # 计算短期和长期均线
            short_ma = sum(self.prices[-self.short_window:]) / self.short_window
            long_ma = sum(self.prices[-self.long_window:]) / self.long_window
            
            current_price = self.prices[-1]
            
            logger.info(f"价格={current_price:.2f}, 短期MA={short_ma:.2f}, 长期MA={long_ma:.2f}")
            
            # 生成信号
            signal = 0
            if short_ma > long_ma:
                signal = 1  # 买入信号
            elif short_ma < long_ma:
                signal = -1  # 卖出信号
                
            # 执行交易
            self._execute_trades(signal, current_price)
    
    def _execute_trades(self, signal: int, current_price: float):
        """执行交易"""
        # 检查是否有新信号
        if signal == self.last_signal:
            return
            
        # 更新信号
        self.last_signal = signal
        
        # 获取账户信息
        account_info = self._get_account()
        if not account_info:
            logger.error("无法获取账户信息，跳过交易")
            return
            
        # 提取余额
        balances = account_info.get("balances", {})
        base_asset = self.symbol[:3]  # 简化处理，假设交易对格式为BASE/QUOTE
        quote_asset = self.symbol[3:]
        base_balance = 0
        quote_balance = 0
        
        for asset_info in balances:
            asset = asset_info.get("asset", "")
            if asset == base_asset:
                base_balance = float(asset_info.get("free", 0))
            elif asset == quote_asset:
                quote_balance = float(asset_info.get("free", 0))
        
        logger.info(f"账户余额: {base_asset}={base_balance}, {quote_asset}={quote_balance}")
        
        # 根据信号执行交易
        if signal == 1 and self.position <= 0:
            # 买入信号，且当前无多头持仓
            if quote_balance > 100:  # 确保有足够的资金
                order_qty = round(100 / current_price, 5)  # 使用固定资金量
                self._place_order("BUY", "LIMIT", order_qty, current_price * 1.001)  # 略高于市场价
                logger.info(f"发出买入信号: 数量={order_qty}, 价格={current_price * 1.001:.2f}")
                self.position = 1
            else:
                logger.warning(f"资金不足，无法买入: {quote_asset}={quote_balance}")
                
        elif signal == -1 and self.position >= 0:
            # 卖出信号，且当前无空头持仓
            if base_balance > 0.001:  # 确保有足够的基础资产
                order_qty = min(base_balance, 0.01)  # 限制卖出数量
                self._place_order("SELL", "LIMIT", order_qty, current_price * 0.999)  # 略低于市场价
                logger.info(f"发出卖出信号: 数量={order_qty}, 价格={current_price * 0.999:.2f}")
                self.position = -1
            else:
                logger.warning(f"持仓不足，无法卖出: {base_asset}={base_balance}")
    
    def _place_order(self, side: str, order_type: str, quantity: float, price: Optional[float] = None):
        """下单"""
        try:
            data = {
                "symbol": self.symbol,
                "side": side,
                "type": order_type,
                "quantity": str(quantity)
            }
            
            if price and order_type == "LIMIT":
                data["price"] = str(price)
                
            response = requests.post(f"{self.rest_url}/api/v1/order", 
                                    headers=self.headers, 
                                    json=data)
            
            if response.status_code == 200:
                order_result = response.json()
                order_id = order_result.get("orderId")
                if order_id:
                    with self.order_lock:
                        self.orders[order_id] = order_result
                    logger.info(f"下单成功: ID={order_id}, {side} {quantity}@{price}")
                    return order_id
                else:
                    logger.warning(f"下单成功但未返回订单ID: {order_result}")
            else:
                logger.error(f"下单失败 HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"下单过程中出错: {e}")
            
        return None
    
    def _cancel_order(self, order_id: str):
        """取消订单"""
        try:
            params = f"symbol={self.symbol}&orderId={order_id}"
            response = requests.delete(f"{self.rest_url}/api/v1/order?{params}", 
                                      headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"取消订单成功: ID={order_id}")
                return True
            else:
                logger.error(f"取消订单失败 HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"取消订单过程中出错: {e}")
            
        return False
    
    def _check_pending_orders(self):
        """检查待处理订单"""
        with self.order_lock:
            pending_orders = [order_id for order_id, order in self.orders.items() 
                             if order.get("status") in ["NEW", "PARTIALLY_FILLED"]]
            
        # 检查长时间未成交的订单
        current_time = datetime.now()
        for order_id in pending_orders:
            with self.order_lock:
                order = self.orders.get(order_id, {})
                
            order_time_str = order.get("time", 0)
            if order_time_str:
                order_time = datetime.fromtimestamp(int(order_time_str) / 1000)
                # 如果订单已挂超过60秒，考虑取消
                if (current_time - order_time).total_seconds() > 60:
                    logger.info(f"订单 {order_id} 已挂单超过60秒，准备取消")
                    self._cancel_order(order_id)
    
    def _get_account(self):
        """获取账户信息"""
        try:
            response = requests.get(f"{self.rest_url}/api/v1/account", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取账户信息失败 HTTP {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"获取账户信息过程中出错: {e}")
        return None
    
    def _get_user_id(self):
        """从账户信息中获取用户ID"""
        account_info = self._get_account()
        if account_info:
            return account_info.get("accountId")
        return None


def create_exchange_and_user():
    """创建模拟交易所和用户（仅用于示例）"""
    from qte.exchange import MockExchange
    
    # 创建模拟交易所
    exchange = MockExchange()
    exchange.start()
    
    # 注册交易对
    exchange.register_symbol("BTCUSDT", "BTC", "USDT")
    
    # 创建用户并获取API密钥
    api_key = exchange.create_user("strategy_user", "MA Strategy")
    
    # 为用户充值
    exchange.deposit("strategy_user", "BTC", 0.1)
    exchange.deposit("strategy_user", "USDT", 10000.0)
    
    return exchange, api_key


if __name__ == "__main__":
    # 创建模拟交易所和用户（实际使用时应已有交易所实例）
    exchange, api_key = create_exchange_and_user()
    
    # 创建并启动策略
    strategy = MovingAverageStrategy("BTCUSDT", api_key, short_window=5, long_window=20)
    
    try:
        strategy.start()
        # 让策略运行一段时间（实际应用中可能会持续运行）
        time.sleep(300)  # 运行5分钟
    except KeyboardInterrupt:
        logger.info("检测到键盘中断，正在停止策略...")
    finally:
        strategy.stop()
        exchange.stop()
        logger.info("策略和交易所已停止")