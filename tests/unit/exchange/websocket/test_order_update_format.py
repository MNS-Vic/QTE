#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket订单更新消息格式单元测试
验证订单更新消息格式符合币安API标准
"""
import pytest
import pytest_asyncio
import asyncio
import json
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch

from qte.exchange.matching.matching_engine import (
    MatchingEngine, Order, OrderSide, OrderType, OrderStatus, Trade
)
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer
from qte.exchange.account.account_manager import AccountManager


class TestOrderUpdateFormat:
    """WebSocket订单更新消息格式测试"""
    
    @pytest.fixture
    def event_loop(self):
        """创建一个事件循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()
    
    @pytest.fixture
    def matching_engine(self):
        """创建撮合引擎"""
        return MatchingEngine()
    
    @pytest.fixture
    def account_manager(self):
        """创建账户管理器"""
        account_manager = AccountManager()
        
        # 创建测试用户账户
        user_id = "test_user"
        account_manager.create_account(user_id)
        account = account_manager.get_account(user_id)
        account.deposit("USDT", Decimal("10000"))
        account.deposit("BTC", Decimal("1"))
        
        return account_manager
    
    @pytest.fixture
    def websocket_server(self, matching_engine, account_manager):
        """创建WebSocket服务器"""
        return ExchangeWebSocketServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=8765
        )
    
    @pytest.fixture
    def mock_websocket(self):
        """创建模拟WebSocket客户端"""
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        return mock_websocket
    
    @pytest.mark.asyncio
    async def test_order_update_format_new_order(self, event_loop, matching_engine, websocket_server, mock_websocket):
        """测试NEW状态订单更新消息格式"""
        # 设置模拟客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 保存发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 创建订单
        order = Order(
            order_id="test_order_new",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id=user_id,
            client_order_id="client_order_new",
            self_trade_prevention_mode="EXPIRE_TAKER",
            price_match="OPPONENT"
        )
        
        # 设置消息数据
        update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "f": "GTC",              # 有效期
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price) if order.price else "0",  # 订单价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "NEW",              # 执行类型
                    "X": "NEW",              # 订单状态
                    "z": "0.0",              # 累计成交量
                    "T": int(time.time() * 1000),  # 更新时间
                    "O": int(time.time() * 1000),  # 订单创建时间
                    "V": order.self_trade_prevention_mode,  # 自成交保护模式
                    "pm": order.price_match  # 价格匹配模式
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, update_data)
        
        # 验证消息格式
        assert len(sent_messages) == 1, "应该发送一条消息"
        message = sent_messages[0]
        
        # 验证顶层结构
        assert "data" in message, "消息缺少data字段"
        data = message["data"]
        
        # 验证事件类型
        assert data.get("e") == "ORDER_TRADE_UPDATE", "事件类型应为ORDER_TRADE_UPDATE"
        
        # 验证事件时间
        assert "E" in data, "缺少事件时间字段"
        assert isinstance(data["E"], int), "事件时间应为整数"
        
        # 验证订单详情
        assert "o" in data, "缺少订单详情字段"
        order_data = data["o"]
        
        # 验证订单字段
        assert order_data.get("s") == "BTCUSDT", "交易对不正确"
        assert order_data.get("c") == "client_order_new", "客户端订单ID不正确"
        assert order_data.get("S") == "BUY", "订单方向不正确"
        assert order_data.get("o") == "LIMIT", "订单类型不正确"
        assert order_data.get("f") == "GTC", "订单有效期不正确"
        assert float(order_data.get("q")) == 0.1, "订单数量不正确"
        assert float(order_data.get("p")) == 50000.0, "订单价格不正确"
        assert order_data.get("x") == "NEW", "执行类型不正确"
        assert order_data.get("X") == "NEW", "订单状态不正确"
        assert order_data.get("i") == "test_order_new", "订单ID不正确"
        assert order_data.get("V") == "EXPIRE_TAKER", "自成交保护模式不正确"
        assert order_data.get("pm") == "OPPONENT", "价格匹配模式不正确"
        
        # 验证必要的时间戳字段
        assert "T" in order_data, "缺少执行时间字段"
        assert "O" in order_data, "缺少订单创建时间字段"
        
        # 验证必要的数值字段
        assert "z" in order_data, "缺少累计成交数量字段"
        assert float(order_data.get("z")) == 0.0, "NEW状态的累计成交数量应为0"
        
    @pytest.mark.asyncio
    async def test_order_update_format_filled_order(self, event_loop, matching_engine, websocket_server, mock_websocket):
        """测试FILLED状态订单更新消息格式"""
        # 设置模拟客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 保存发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 创建订单
        order = Order(
            order_id="test_order_filled",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id=user_id,
            client_order_id="client_order_filled"
        )
        order.status = OrderStatus.FILLED
        
        # 使用fill方法模拟成交
        order.fill(0.1, 50000.0)
        
        # 设置TRADE消息数据
        trade_update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "f": "GTC",              # 有效期
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price),   # 订单价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "TRADE",            # 执行类型
                    "X": "PARTIALLY_FILLED", # 订单状态
                    "z": str(order.filled_quantity),  # 累计成交量
                    "T": int(time.time() * 1000),  # 更新时间
                    "n": "0.01",             # 手续费
                    "N": "BTC",              # 手续费资产
                    "L": "50000.0",          # 成交价格
                    "l": "0.1"               # 本次成交数量
                }
            }
        }
        
        # 设置FILLED消息数据
        filled_update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "f": "GTC",              # 有效期
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price),   # 订单价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "FILLED",           # 执行类型
                    "X": "FILLED",           # 订单状态
                    "z": str(order.quantity),  # 累计成交量（等于订单数量）
                    "T": int(time.time() * 1000)   # 更新时间
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, trade_update_data)
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, filled_update_data)
        
        # 验证消息格式 - TRADE消息
        assert len(sent_messages) >= 2, "应该至少发送2条消息"
        trade_message = sent_messages[0]
        
        # 验证是否有TRADE消息
        assert trade_message["data"]["o"]["x"] == "TRADE", "应该有TRADE状态更新消息"
        
        trade_data = trade_message["data"]["o"]
        
        # 验证TRADE消息关键字段
        assert trade_data.get("s") == "BTCUSDT", "交易对不正确"
        assert trade_data.get("S") == "BUY", "订单方向不正确"
        assert trade_data.get("o") == "LIMIT", "订单类型不正确"
        assert float(trade_data.get("q")) == 0.1, "订单数量不正确"
        assert float(trade_data.get("p")) == 50000.0, "订单价格不正确"
        assert trade_data.get("i") == "test_order_filled", "订单ID不正确"
        
        # 验证成交特有字段
        assert "n" in trade_data, "缺少手续费字段"
        assert "N" in trade_data, "缺少手续费资产字段"
        assert trade_data.get("N") == "BTC", "手续费资产不正确"
        assert float(trade_data.get("n")) == 0.01, "手续费数量不正确"
        assert "L" in trade_data, "缺少成交价格字段"
        assert float(trade_data.get("L")) == 50000.0, "成交价格不正确"
        assert "l" in trade_data, "缺少本次成交数量字段"
        assert float(trade_data.get("l")) == 0.1, "本次成交数量不正确"
        
        # 验证消息格式 - FILLED消息
        filled_message = sent_messages[1]
        
        # 验证是否有FILLED消息
        assert filled_message["data"]["o"]["x"] == "FILLED", "应该有FILLED状态更新消息"
        
        filled_data = filled_message["data"]["o"]
        
        # 验证FILLED消息关键字段
        assert filled_data.get("s") == "BTCUSDT", "交易对不正确"
        assert filled_data.get("S") == "BUY", "订单方向不正确"
        assert filled_data.get("o") == "LIMIT", "订单类型不正确"
        assert float(filled_data.get("q")) == 0.1, "订单数量不正确"
        assert filled_data.get("x") == "FILLED", "执行类型不正确"
        assert filled_data.get("X") == "FILLED", "订单状态不正确"
        assert filled_data.get("i") == "test_order_filled", "订单ID不正确"
        
        # 验证累计成交数量等于总数量
        assert float(filled_data.get("z")) == float(filled_data.get("q")), "FILLED状态下累计成交数量应等于总数量"
    
    @pytest.mark.asyncio
    async def test_order_update_format_canceled_order(self, event_loop, matching_engine, websocket_server, mock_websocket):
        """测试CANCELED状态订单更新消息格式"""
        # 设置模拟客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 保存发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 创建订单
        order = Order(
            order_id="test_order_canceled",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id=user_id,
            client_order_id="client_order_canceled"
        )
        order.status = OrderStatus.CANCELED
        
        # 设置消息数据
        update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price),   # 订单价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "CANCELED",         # 执行类型
                    "X": "CANCELED",         # 订单状态
                    "z": "0.0",              # 累计成交量
                    "T": int(time.time() * 1000)   # 更新时间
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, update_data)
        
        # 验证消息格式
        assert len(sent_messages) == 1, "应该发送一条消息"
        message = sent_messages[0]
        
        # 验证顶层结构
        assert "data" in message, "消息缺少data字段"
        data = message["data"]
        
        # 验证事件类型
        assert data.get("e") == "ORDER_TRADE_UPDATE", "事件类型应为ORDER_TRADE_UPDATE"
        
        # 验证订单详情
        order_data = data["o"]
        
        # 验证订单字段
        assert order_data.get("s") == "BTCUSDT", "交易对不正确"
        assert order_data.get("c") == "client_order_canceled", "客户端订单ID不正确"
        assert order_data.get("S") == "BUY", "订单方向不正确"
        assert order_data.get("o") == "LIMIT", "订单类型不正确"
        assert order_data.get("x") == "CANCELED", "执行类型不正确"
        assert order_data.get("X") == "CANCELED", "订单状态不正确"
        assert order_data.get("i") == "test_order_canceled", "订单ID不正确"
    
    @pytest.mark.asyncio
    async def test_order_update_format_expired_order(self, event_loop, matching_engine, websocket_server, mock_websocket):
        """测试EXPIRED状态订单更新消息格式"""
        # 设置模拟客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 保存发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 创建订单
        order = Order(
            order_id="test_order_expired",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id=user_id,
            client_order_id="client_order_expired",
            self_trade_prevention_mode="EXPIRE_TAKER"
        )
        order.status = OrderStatus.EXPIRED
        
        # 设置消息数据
        update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price),   # 订单价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "EXPIRED",          # 执行类型
                    "X": "EXPIRED",          # 订单状态
                    "z": "0.0",              # 累计成交量
                    "T": int(time.time() * 1000),  # 更新时间
                    "V": order.self_trade_prevention_mode  # 自成交保护模式
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, update_data)
        
        # 验证消息格式
        assert len(sent_messages) == 1, "应该发送一条消息"
        message = sent_messages[0]
        
        # 验证顶层结构
        assert "data" in message, "消息缺少data字段"
        data = message["data"]
        
        # 验证事件类型
        assert data.get("e") == "ORDER_TRADE_UPDATE", "事件类型应为ORDER_TRADE_UPDATE"
        
        # 验证订单详情
        order_data = data["o"]
        
        # 验证订单字段
        assert order_data.get("s") == "BTCUSDT", "交易对不正确"
        assert order_data.get("c") == "client_order_expired", "客户端订单ID不正确"
        assert order_data.get("S") == "BUY", "订单方向不正确"
        assert order_data.get("o") == "LIMIT", "订单类型不正确"
        assert order_data.get("x") == "EXPIRED", "执行类型不正确"
        assert order_data.get("X") == "EXPIRED", "订单状态不正确"
        assert order_data.get("i") == "test_order_expired", "订单ID不正确"
        assert order_data.get("V") == "EXPIRE_TAKER", "自成交保护模式不正确"
    
    @pytest.mark.asyncio
    async def test_order_update_format_market_order(self, event_loop, matching_engine, websocket_server, mock_websocket):
        """测试市价单订单更新消息格式"""
        # 设置模拟客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 保存发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 创建市价单
        order = Order(
            order_id="test_market_order",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1,
            price=0,  # 市价单价格为0
            user_id=user_id,
            client_order_id="client_market_order"
        )
        
        # 设置消息数据
        update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "i": order.order_id,     # 订单ID
                    "p": "0",                # 市价单价格为0
                    "q": str(order.quantity),  # 订单数量
                    "x": "NEW",              # 执行类型
                    "X": "NEW",              # 订单状态
                    "z": "0.0",              # 累计成交量
                    "T": int(time.time() * 1000)   # 更新时间
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, update_data)
        
        # 验证消息格式
        assert len(sent_messages) == 1, "应该发送一条消息"
        message = sent_messages[0]
        
        # 验证顶层结构
        data = message["data"]
        order_data = data["o"]
        
        # 验证订单字段
        assert order_data.get("o") == "MARKET", "订单类型应为MARKET"
        assert order_data.get("p") == "0", "市价单价格应为0"
        assert float(order_data.get("q")) == 0.1, "订单数量不正确"
    
    @pytest.mark.asyncio
    async def test_order_update_format_stop_order(self, event_loop, matching_engine, websocket_server, mock_websocket):
        """测试停止单订单更新消息格式"""
        # 设置模拟客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 保存发送的消息
        sent_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            sent_messages.append(json.loads(message))
        
        mock_websocket.send = mock_send
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 创建限价单，带止损价
        order = Order(
            order_id="test_stop_order",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,  # 使用普通限价单代替STOP_LOSS_LIMIT
            quantity=0.1,
            price=45000.0,
            user_id=user_id,
            client_order_id="client_stop_order",
            stop_price=48000.0
        )
        
        # 设置消息数据
        update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price),   # 订单价格
                    "P": str(order.stop_price),  # 止损价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "NEW",              # 执行类型
                    "X": "NEW",              # 订单状态
                    "z": "0.0",              # 累计成交量
                    "T": int(time.time() * 1000)   # 更新时间
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, update_data)
        
        # 验证消息格式
        assert len(sent_messages) == 1, "应该发送一条消息"
        message = sent_messages[0]
        
        # 验证顶层结构
        data = message["data"]
        order_data = data["o"]
        
        # 验证订单字段
        assert order_data.get("o") == "LIMIT", "订单类型应为LIMIT"
        assert float(order_data.get("p")) == 45000.0, "订单价格不正确"
        assert "P" in order_data, "缺少止损价字段"
        assert float(order_data.get("P")) == 48000.0, "止损价不正确"
    
    @pytest.mark.asyncio
    async def test_notification_to_multiple_clients(self, event_loop, matching_engine, websocket_server):
        """测试向多个客户端发送通知"""
        # 创建两个模拟客户端
        mock_websocket1 = MagicMock()
        mock_websocket1.remote_address = ("127.0.0.1", 12345)
        
        mock_websocket2 = MagicMock()
        mock_websocket2.remote_address = ("127.0.0.1", 12346)
        
        # 保存发送的消息
        sent_messages1 = []
        sent_messages2 = []
        
        # 模拟send方法
        async def mock_send1(message):
            sent_messages1.append(json.loads(message))
        
        async def mock_send2(message):
            sent_messages2.append(json.loads(message))
        
        mock_websocket1.send = mock_send1
        mock_websocket2.send = mock_send2
        
        # 设置客户端
        user_id = "test_user"
        websocket_server.clients[mock_websocket1] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        websocket_server.clients[mock_websocket2] = {
            "connected_at": time.time(),
            "user_id": user_id,
            "subscriptions": set()
        }
        
        # 绑定用户订阅
        order_subscription_key = f"{user_id}@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket1)
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket2)
        
        # 创建订单
        order = Order(
            order_id="test_multi_client",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id=user_id,
            client_order_id="client_multi_client"
        )
        
        # 设置消息数据
        update_data = {
            "stream": order_subscription_key,
            "data": {
                "e": "ORDER_TRADE_UPDATE",  # 事件类型
                "E": int(time.time() * 1000),  # 事件时间
                "o": {
                    "s": order.symbol,       # 交易对
                    "c": order.client_order_id or "",  # 客户端订单ID
                    "S": order.side.value,   # 订单方向
                    "o": order.order_type.value,  # 订单类型
                    "i": order.order_id,     # 订单ID
                    "p": str(order.price),   # 订单价格
                    "q": str(order.quantity),  # 订单数量
                    "x": "NEW",              # 执行类型
                    "X": "NEW",              # 订单状态
                    "z": "0.0",              # 累计成交量
                    "T": int(time.time() * 1000)   # 更新时间
                }
            }
        }
        
        # 手动调用广播消息方法
        await websocket_server._broadcast_to_user_subscribers(order_subscription_key, update_data)
        
        # 验证两个客户端都收到消息
        assert len(sent_messages1) == 1, "第一个客户端应该收到消息"
        assert len(sent_messages2) == 1, "第二个客户端应该收到消息"
        
        # 验证消息内容一致
        assert sent_messages1[0]["data"]["o"]["i"] == "test_multi_client"
        assert sent_messages2[0]["data"]["o"]["i"] == "test_multi_client" 