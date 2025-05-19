#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket服务器的单元测试
"""
import pytest
import asyncio
import json
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock

# 导入被测试的模块
from qte.exchange.websocket.websocket_server import ExchangeWebSocketServer
from qte.exchange.matching.matching_engine import MatchingEngine
from qte.exchange.account.account_manager import AccountManager


class TestWebSocketServer:
    """WebSocket服务器测试类"""
    
    @pytest.fixture
    def setup_server(self):
        """设置测试环境"""
        # 创建模拟对象
        self.matching_engine = MagicMock()
        self.account_manager = MagicMock()
        
        # 创建WebSocket服务器
        self.server = ExchangeWebSocketServer(
            matching_engine=self.matching_engine,
            account_manager=self.account_manager,
            host="localhost",
            port=8765
        )
        
        # 添加测试用户和API密钥
        self.test_user_id = "test_user"
        self.test_api_key = self.server.create_api_key(self.test_user_id)
        
        return self.server
    
    def test_server_initialization(self, setup_server):
        """测试服务器初始化"""
        assert self.server is not None
        assert self.server.matching_engine == self.matching_engine
        assert self.server.account_manager == self.account_manager
        assert self.server.host == "localhost"
        assert self.server.port == 8765
        assert self.server.is_running is False
        assert len(self.server.clients) == 0
        assert len(self.server.market_subscriptions) == 0
        assert len(self.server.user_subscriptions) == 0
    
    def test_api_key_creation(self, setup_server):
        """测试API密钥创建和验证"""
        # 测试创建API密钥
        api_key = self.server.create_api_key("new_user")
        assert api_key is not None
        assert isinstance(api_key, str)
        assert self.server.get_user_id_from_api_key(api_key) == "new_user"
        
        # 测试获取无效API密钥
        assert self.server.get_user_id_from_api_key("invalid_key") is None
    
    def test_subscribe_market(self, setup_server):
        """测试市场数据订阅"""
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set()
        }
        
        # 调用订阅方法
        self.server._subscribe_market(mock_websocket, "BTCUSDT", "trade")
        
        # 验证结果
        subscription_key = "BTCUSDT@trade"
        assert subscription_key in self.server.market_subscriptions
        assert mock_websocket in self.server.market_subscriptions[subscription_key]
        # 注意：_subscribe_market方法只更新全局market_subscriptions集合，
        # 不会更新客户端的subscriptions集合，这是在_handle_subscribe中处理的
        # 所以这里不测试客户端subscriptions是否包含subscription_key
    
    def test_unsubscribe_market(self, setup_server):
        """测试取消市场数据订阅"""
        # 模拟WebSocket连接
        mock_websocket = MagicMock()
        subscription_key = "BTCUSDT@trade"
        self.server.clients[mock_websocket] = {
            "connected_at": time.time(),
            "user_id": None,
            "subscriptions": set([subscription_key])
        }
        self.server.market_subscriptions[subscription_key] = set([mock_websocket])
        
        # 调用取消订阅方法
        self.server._unsubscribe_market(mock_websocket, "BTCUSDT", "trade")
        
        # 验证结果
        # 注意：_unsubscribe_market方法只更新全局market_subscriptions集合，
        # 不会更新客户端的subscriptions集合，这是在_handle_unsubscribe中处理的
        # 所以这里不测试客户端subscriptions是否不包含subscription_key
        assert mock_websocket not in self.server.market_subscriptions.get(subscription_key, set())