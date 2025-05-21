#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试WebSocket服务器订单更新推送功能
"""
import pytest
import asyncio
import json
import time
from unittest.mock import MagicMock, patch
import websockets
from decimal import Decimal

from qte.exchange.matching.matching_engine import (
    MatchingEngine, Order, OrderSide, OrderType, OrderStatus, Trade
)
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer

class TestOrderUpdates:
    """测试WebSocket服务器订单更新推送功能"""
    
    @pytest.fixture
    def matching_engine(self):
        """创建撮合引擎"""
        return MatchingEngine()
        
    @pytest.fixture
    def account_manager(self):
        """创建账户管理器"""
        account_manager = AccountManager()
        # 添加测试账户
        account_manager.create_account("test_user")
        # 充值资产
        account = account_manager.get_account("test_user")
        account.deposit("USDT", Decimal("10000"))
        account.deposit("BTC", Decimal("1"))
        return account_manager
        
    @pytest.fixture
    def websocket_server(self, matching_engine, account_manager):
        """创建WebSocket服务器"""
        server = ExchangeWebSocketServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=8765
        )
        # 创建API密钥
        server.create_api_key("test_user")
        return server
        
    @pytest.mark.asyncio
    async def test_order_update_websocket(self, websocket_server, matching_engine, account_manager):
        """测试订单更新推送"""
        # 模拟WebSocket客户端连接
        mock_websocket = MagicMock()
        mock_websocket.remote_address = ("127.0.0.1", 12345)
        
        # 使用字典存储收到的消息
        received_messages = []
        
        # 模拟send方法
        async def mock_send(message):
            received_messages.append(json.loads(message))
            
        mock_websocket.send = mock_send
        
        # 初始化客户端信息
        websocket_server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": "test_user",
            "subscriptions": set()
        }
        
        # 模拟用户订阅订单更新
        order_subscription_key = "test_user@order"
        if order_subscription_key not in websocket_server.user_subscriptions:
            websocket_server.user_subscriptions[order_subscription_key] = set()
        websocket_server.user_subscriptions[order_subscription_key].add(mock_websocket)
        
        # 模拟订单更新事件 - 创建订单
        buy_order = Order(
            order_id="test_order_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id="test_user",
            client_order_id="client_order_1",
            price_match="OPPONENT",
            self_trade_prevention_mode="EXPIRE_TAKER"
        )
        
        # 触发订单更新事件
        matching_engine._notify_order_update(buy_order, "NEW")
        
        # 等待异步任务完成
        await asyncio.sleep(0.1)
        
        # 验证WebSocket消息
        assert len(received_messages) >= 1
        
        # 找到订单更新消息
        order_messages = [msg for msg in received_messages 
                         if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE"]
        
        assert len(order_messages) >= 1
        order_msg = order_messages[0]
        
        # 验证订单字段
        assert order_msg["stream"] == order_subscription_key
        assert order_msg["data"]["e"] == "ORDER_TRADE_UPDATE"
        
        order_data = order_msg["data"]["o"]
        assert order_data["s"] == "BTCUSDT"
        assert order_data["i"] == "test_order_1"
        assert order_data["c"] == "client_order_1"
        assert order_data["S"] == "BUY"
        assert order_data["o"] == "LIMIT"
        assert order_data["p"] == "50000.0"
        assert order_data["q"] == "0.1"
        assert order_data["x"] == "NEW"
        assert order_data["X"] == "NEW"
        assert order_data["V"] == "EXPIRE_TAKER"
        assert order_data["pm"] == "OPPONENT"
        
        # 测试自成交保护模式触发的订单更新
        sell_order = Order(
            order_id="test_order_2",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=50000.0,
            user_id="test_user",
            client_order_id="client_order_2",
            self_trade_prevention_mode="EXPIRE_TAKER"
        )
        
        # 手动设置订单状态并触发更新
        sell_order.status = OrderStatus.EXPIRED_IN_MATCH
        matching_engine._notify_order_update(sell_order, "EXPIRED_IN_MATCH")
        
        # 等待异步任务完成
        await asyncio.sleep(0.1)
        
        # 重新检查消息
        order_messages = [msg for msg in received_messages 
                         if msg.get("data", {}).get("e") == "ORDER_TRADE_UPDATE" and
                           msg.get("data", {}).get("o", {}).get("i") == "test_order_2"]
        
        assert len(order_messages) >= 1
        order_msg = order_messages[0]
        
        # 验证自成交保护触发的订单状态
        order_data = order_msg["data"]["o"]
        assert order_data["i"] == "test_order_2"
        assert order_data["x"] == "EXPIRED_IN_MATCH"
        assert order_data["X"] == "EXPIRED_IN_MATCH" 