#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
币安API兼容性测试

测试REST API与币安API的兼容性
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from decimal import Decimal

from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.matching.matching_engine import MatchingEngine, OrderStatus
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.rest_api.error_codes import *

class TestBinanceCompatibility:
    """测试币安API兼容性"""
    
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
    
    def test_v3_endpoints(self, setup_server):
        """测试v3 API端点是否可访问"""
        # 测试ping端点
        response = self.client.get('/api/v3/ping')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"
        
        # 测试time端点
        response = self.client.get('/api/v3/time')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "serverTime" in data
    
    def test_binance_error_format(self, setup_server):
        """测试币安风格的错误响应格式"""
        # 缺少API密钥的错误
        response = self.client.get('/api/v3/account')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "code" in data
        assert "msg" in data
        assert "success" not in data  # 不应包含success字段
        assert data["code"] == INVALID_API_KEY_ORDER  # 应使用币安错误码
        
        # 参数验证错误
        response = self.client.get('/api/v3/depth')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "code" in data
        assert "msg" in data
        assert "success" not in data
    
    def test_timestamp_validation(self, setup_server):
        """测试时间戳验证逻辑"""
        import time
        
        # 当前时间
        now = int(time.time() * 1000)
        
        # 过期时间戳（2017年之前）
        response = self.client.post(
            '/api/v3/order',
            json={
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "1.0",
                "price": "10000",
                "timestamp": 1483228700000  # 2017年以前
            },
            headers={'X-API-KEY': self.test_api_key}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["code"] == INVALID_TIMESTAMP
        
        # 未来时间戳（当前时间+20秒）
        response = self.client.post(
            '/api/v3/order',
            json={
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "1.0",
                "price": "10000",
                "timestamp": now + 20000  # 未来时间戳
            },
            headers={'X-API-KEY': self.test_api_key}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["code"] == INVALID_TIMESTAMP
    
    def test_avg_price_endpoint(self, setup_server):
        """测试新增的平均价格端点"""
        # 模拟市场价格
        self.matching_engine.get_market_price.return_value = Decimal("10000.0")
        
        # 测试avgPrice端点
        response = self.client.get('/api/v3/avgPrice?symbol=BTCUSDT')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "mins" in data
        assert "price" in data
        assert data["price"] == "10000.0"
        assert "closeTime" in data  # 2023-12-04新增字段
    
    def test_commission_endpoint(self, setup_server):
        """测试佣金信息端点"""
        # 模拟用户认证
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.get(
                '/api/v3/account/commission',
                headers={'X-API-KEY': self.test_api_key}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "standardCommission" in data
            assert "taxCommission" in data
            assert "discount" in data
    
    def test_omit_zero_balances(self, setup_server):
        """测试隐藏零余额功能"""
        # 模拟账户和余额
        mock_account = MagicMock()
        mock_account.get_account_snapshot.return_value = {
            "balances": {
                "BTC": {"free": Decimal("1.0"), "locked": Decimal("0.0")},
                "ETH": {"free": Decimal("0.0"), "locked": Decimal("0.0")},
                "USDT": {"free": Decimal("1000.0"), "locked": Decimal("500.0")}
            }
        }
        
        self.account_manager.get_account.return_value = mock_account
        
        # 测试不隐藏零余额（默认）
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.get(
                '/api/v3/account',
                headers={'X-API-KEY': self.test_api_key}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data["balances"]) == 3  # 应显示所有3个资产
            
        # 测试隐藏零余额
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.get(
                '/api/v3/account?omitZeroBalances=true',
                headers={'X-API-KEY': self.test_api_key}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data["balances"]) == 2  # 应只显示BTC和USDT
            
            # 验证ETH（零余额）被排除
            asset_symbols = [balance["asset"] for balance in data["balances"]]
            assert "BTC" in asset_symbols
            assert "USDT" in asset_symbols
            assert "ETH" not in asset_symbols 