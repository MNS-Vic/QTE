#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API增强功能测试

测试新实现的API增强功能
"""
import json
import time
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from decimal import Decimal

from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.matching.matching_engine import MatchingEngine, OrderStatus
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.rest_api.error_codes import *

class TestAPIEnhancements:
    """测试新实现的API增强功能"""
    
    @pytest.fixture
    def setup_server(self):
        """设置测试服务器"""
        # 创建模拟对象
        self.matching_engine = MagicMock(spec=MatchingEngine)
        self.account_manager = MagicMock(spec=AccountManager)
        
        # 创建服务器实例
        self.server = ExchangeRESTServer(
            matching_engine=self.matching_engine,
            account_manager=self.account_manager,
            host="localhost",
            port=5000
        )
        
        # 创建测试客户端
        self.client = self.server.app.test_client()
        
        # 创建测试用户和API密钥
        self.test_user_id = "test_user"
        self.test_api_key = self.server.create_api_key(self.test_user_id)
        
        # 返回服务器实例
        return self.server
    
    def test_trading_day_endpoint(self, setup_server):
        """测试交易日信息端点"""
        # 测试tradingDay端点
        response = self.client.get('/api/v3/ticker/tradingDay')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 验证响应字段
        assert "timezone" in data
        assert "serverTime" in data
        assert "tradingDayStart" in data
        assert "tradingDayEnd" in data
        
        # 验证时区为UTC
        assert data["timezone"] == "UTC"
        
        # 验证交易日起止时间
        assert data["tradingDayEnd"] - data["tradingDayStart"] == 86400000  # 一天的毫秒数
        
        # 验证serverTime在合理范围内
        now = int(time.time() * 1000)
        assert abs(data["serverTime"] - now) < 1000  # 允许1秒误差
    
    def test_klines_timezone_support(self, setup_server):
        """测试K线数据时区支持"""
        # 测试默认UTC时区
        response = self.client.get('/api/v3/klines?symbol=BTCUSDT&interval=1d')
        assert response.status_code == 200
        utc_data = json.loads(response.data)
        utc_open_time = utc_data[0][0]  # 开盘时间
        
        # 测试中国时区
        response = self.client.get('/api/v3/klines?symbol=BTCUSDT&interval=1d&timeZone=China')
        assert response.status_code == 200
        china_data = json.loads(response.data)
        china_open_time = china_data[0][0]  # 开盘时间
        
        # 验证中国时区与UTC时区的时差为8小时
        assert china_open_time - utc_open_time == 8 * 3600 * 1000  # 8小时的毫秒数
        
        # 测试无效时区
        response = self.client.get('/api/v3/klines?symbol=BTCUSDT&interval=1d&timeZone=Invalid')
        assert response.status_code == 400
        error_data = json.loads(response.data)
        assert error_data["code"] == INVALID_PARAM
    
    def test_order_test_endpoint(self, setup_server):
        """测试订单测试端点"""
        # 测试有效订单
        response = self.client.post(
            '/api/v3/order/test',
            json={
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "1.0",
                "price": "10000"
            },
            headers={'X-API-KEY': self.test_api_key}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {}  # 成功时应返回空对象
        
        # 测试无效订单（缺少必要参数）
        response = self.client.post(
            '/api/v3/order/test',
            json={
                "symbol": "BTCUSDT",
                "side": "BUY"
                # 缺少type和quantity
            },
            headers={'X-API-KEY': self.test_api_key}
        )
        assert response.status_code == 400
        error_data = json.loads(response.data)
        assert error_data["code"] == INVALID_PARAM
        
        # 测试未认证访问
        response = self.client.post('/api/v3/order/test', json={"symbol": "BTCUSDT"})
        assert response.status_code == 401
        error_data = json.loads(response.data)
        assert error_data["code"] == INVALID_API_KEY_ORDER
    
    def test_cancel_order_transact_time(self, setup_server):
        """测试取消订单响应中的transactTime字段"""
        # 模拟订单取消成功
        self.matching_engine.cancel_order.return_value = True
        
        # 使用动态方法添加get_order方法到mock对象
        mock_order = MagicMock()
        mock_order.status = OrderStatus.CANCELED
        mock_order.side = "BUY"
        mock_order.remaining_quantity = Decimal("1.0")
        mock_order.price = Decimal("10000.0")
        
        # 手动添加get_order方法，而不是使用spec
        self.matching_engine.get_order = MagicMock(return_value=mock_order)
        
        # 模拟account_manager的unlock_asset方法
        self.account_manager.unlock_asset = MagicMock(return_value=True)
        
        # 测试取消订单
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.delete(
                '/api/v3/order?symbol=BTCUSDT&orderId=123',
                headers={'X-API-KEY': self.test_api_key}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # 验证transactTime字段存在
            assert "transactTime" in data
            
            # 验证transactTime是毫秒时间戳
            now = int(time.time() * 1000)
            assert abs(data["transactTime"] - now) < 1000  # 允许1秒误差 