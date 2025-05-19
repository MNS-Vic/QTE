#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REST API服务器的单元测试
"""
import unittest
import pytest
import json
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch

# 导入被测试的模块
from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.matching.matching_engine import MatchingEngine, Order, OrderSide, OrderType, OrderStatus
from qte.exchange.account.account_manager import AccountManager


class TestRESTServer:
    """REST API服务器测试类"""

    @pytest.fixture
    def setup_server(self):
        """设置测试环境"""
        # 创建模拟对象
        self.matching_engine = MagicMock()
        self.account_manager = MagicMock()
        
        # 创建REST服务器
        self.server = ExchangeRESTServer(
            matching_engine=self.matching_engine,
            account_manager=self.account_manager,
            host="localhost",
            port=5000
        )
        
        # 创建测试客户端
        self.client = self.server.app.test_client()
        
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
        assert self.server.port == 5000
    
    def test_api_key_creation(self, setup_server):
        """测试API密钥创建和验证"""
        # 测试创建API密钥
        api_key = self.server.create_api_key("new_user")
        assert api_key is not None
        assert isinstance(api_key, str)
        assert self.server.get_user_id_from_api_key(api_key) == "new_user"
        
        # 测试获取无效API密钥
        assert self.server.get_user_id_from_api_key("invalid_key") is None
    
    def test_ping_endpoint(self, setup_server):
        """测试ping接口"""
        response = self.client.get('/api/v1/ping')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {"status": "ok"}
    
    def test_server_time_endpoint(self, setup_server):
        """测试服务器时间接口"""
        current_time = int(time.time() * 1000)
        
        response = self.client.get('/api/v1/time')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "serverTime" in data
        assert isinstance(data["serverTime"], int)
        
        # 检查时间在合理范围内（5秒内）
        server_time = data["serverTime"]
        assert abs(server_time - current_time) < 5000
    
    def test_ticker_price_endpoint(self, setup_server):
        """测试ticker价格接口"""
        # 设置模拟返回值
        self.matching_engine.get_market_price.return_value = 10000.0
        
        # 模拟order_books属性
        self.matching_engine.order_books = {"BTCUSDT": MagicMock(), "ETHUSDT": MagicMock()}
        
        # 测试单一交易对
        response = self.client.get('/api/v1/ticker/price?symbol=BTCUSDT')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["symbol"] == "BTCUSDT"
        assert data["price"] == "10000.0"
        
        # 测试所有交易对
        self.matching_engine.get_market_price.side_effect = lambda symbol: 10000.0 if symbol == "BTCUSDT" else 1000.0
        
        response = self.client.get('/api/v1/ticker/price')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["symbol"] == "BTCUSDT" or data[1]["symbol"] == "BTCUSDT"
        assert data[0]["price"] == "10000.0" or data[1]["price"] == "10000.0"
    
    def test_order_book_endpoint(self, setup_server):
        """测试订单簿接口"""
        # 创建模拟订单簿
        mock_order_book = MagicMock()
        mock_order_book.get_depth.return_value = {
            "bids": [(9900.0, 1.0), (9800.0, 2.0)],
            "asks": [(10100.0, 1.0), (10200.0, 2.0)]
        }
        self.matching_engine.get_order_book.return_value = mock_order_book
        
        response = self.client.get('/api/v1/depth?symbol=BTCUSDT&limit=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "symbol" in data
        assert "bids" in data
        assert "asks" in data
        assert len(data["bids"]) == 2
        assert len(data["asks"]) == 2
        assert data["bids"][0][0] == "9900.0"
        assert data["asks"][0][0] == "10100.0"