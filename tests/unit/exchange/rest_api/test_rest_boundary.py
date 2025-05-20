#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REST API服务器边界条件测试
测试REST API服务器在各种边界和异常情况下的行为
"""
import pytest
import json
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock

from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.matching.matching_engine import OrderSide, OrderType, OrderStatus

class TestRESTBoundary:
    """测试REST API服务器边界条件"""
    
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
    
    def test_rest001_authentication_enhanced(self, setup_server):
        """
        测试REST-001：增强的API认证方法
        验证API认证过程中的各种边界情况处理
        """
        # 1. 测试请求头中没有API密钥的情况
        response = self.client.get('/api/v1/account')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "msg" in data
        assert "API-key is required" in data["msg"]
        
        # 2. 测试无效的API密钥
        response = self.client.get(
            '/api/v1/account',
            headers={'X-API-KEY': 'invalid_key'}
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "msg" in data
        assert "Invalid API-key" in data["msg"]
        
        # 3. 测试有效的API密钥
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.get(
                '/api/v1/account',
                headers={'X-API-KEY': self.test_api_key}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "balances" in data
    
    def test_rest001_authentication_logs(self, setup_server):
        """
        测试REST-001：API认证日志
        验证API认证过程是否正确记录日志
        """
        # 使用mock捕获日志
        with patch('qte.exchange.rest_api.rest_server.logger') as mock_logger:
            # 测试成功认证
            with patch.object(self.server, 'get_user_id_from_api_key', return_value=self.test_user_id):
                self.server._authenticate(self.test_api_key)
                # 验证有成功的日志记录 - 使用any_call检查是否被调用
                assert mock_logger.debug.call_count > 0
                assert any("认证成功" in str(call) for call in mock_logger.debug.call_args_list)
            
            # 重置mock
            mock_logger.reset_mock()
            
            # 测试认证失败 - 使用无效的API密钥格式
            self.server._authenticate('invalid_key')
            # 验证有失败的日志记录
            assert mock_logger.warning.call_count > 0
            assert any("无效的API密钥" in str(call) for call in mock_logger.warning.call_args_list)
    
    def test_rest002_async_error_handling_comprehensive(self, setup_server):
        """
        测试REST-002：综合异步错误处理
        验证在下单过程的不同阶段出现异常时是否能正确处理
        """
        # 1. 模拟匹配引擎抛出异常
        self.matching_engine.place_order.side_effect = Exception("模拟的引擎异常")
        self.account_manager.lock_funds_for_order.return_value = True
        
        # 请求数据
        request_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": "1.0",
            "price": "10000.0"
        }
        
        # 发送请求
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v1/order',
                data=json.dumps(request_data),
                content_type='application/json',
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证结果 - 应该返回错误响应
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "msg" in data
            assert "创建订单失败" in data["msg"]
            
            # 验证资金解锁是否被调用
            self.account_manager.unlock_funds_for_order.assert_called_once()
            
        # 2. 模拟账户管理器在解锁资金时抛出异常
        self.matching_engine.place_order.side_effect = Exception("模拟的引擎异常")
        self.account_manager.lock_funds_for_order.return_value = True
        self.account_manager.unlock_funds_for_order.side_effect = Exception("模拟的解锁异常")
        self.account_manager.unlock_funds_for_order.reset_mock()
        
        # 发送请求
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            with patch('qte.exchange.rest_api.rest_server.logger') as mock_logger:
                response = self.client.post(
                    '/api/v1/order',
                    data=json.dumps(request_data),
                    content_type='application/json',
                    headers={'X-API-KEY': self.test_api_key}
                )
                
                # 验证结果 - 应该仍然返回错误响应，但不会因为解锁资金异常而崩溃
                assert response.status_code == 400
                data = json.loads(response.data)
                assert "msg" in data
                
                # 验证解锁资金异常被记录
                mock_logger.error.assert_any_call("解锁资金失败")
    
    def test_request_validation_comprehensive(self, setup_server):
        """
        测试请求参数验证
        验证各种无效的请求参数是否被正确检测和处理
        """
        # 准备各种无效的请求数据
        invalid_requests = [
            # 缺少必要参数
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                # 缺少type参数
                "quantity": "1.0",
                "price": "10000.0"
            },
            # 无效的订单类型
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "INVALID_TYPE",
                "quantity": "1.0",
                "price": "10000.0"
            },
            # 无效的订单方向
            {
                "symbol": "BTCUSDT",
                "side": "INVALID_SIDE",
                "type": "LIMIT",
                "quantity": "1.0",
                "price": "10000.0"
            },
            # 无效的数量格式
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "invalid_qty",
                "price": "10000.0"
            },
            # 无效的价格格式
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "1.0",
                "price": "invalid_price"
            },
            # 市价单提供了价格
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": "1.0",
                "price": "10000.0"  # 市价单不应提供价格
            },
            # 限价单没有提供价格
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "LIMIT",
                "quantity": "1.0"
                # 缺少price参数
            }
        ]
        
        # 测试每个无效请求
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            for request_data in invalid_requests:
                response = self.client.post(
                    '/api/v1/order',
                    data=json.dumps(request_data),
                    content_type='application/json',
                    headers={'X-API-KEY': self.test_api_key}
                )
                
                # 验证结果 - 应该返回错误响应
                assert response.status_code == 400
                data = json.loads(response.data)
                assert "msg" in data
    
    def test_rest002_funds_handling(self, setup_server):
        """
        测试REST-002：资金处理边界情况
        验证在资金不足、锁定失败等情况下的处理
        """
        # 设置模拟资金锁定失败
        self.account_manager.lock_funds_for_order.return_value = False
        
        # 准备请求数据
        request_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": "1.0",
            "price": "10000.0"
        }
        
        # 发送请求
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v1/order',
                data=json.dumps(request_data),
                content_type='application/json',
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证结果 - 应该返回资金不足错误
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "msg" in data
            assert "资金不足" in data["msg"]
            
            # 验证解锁资金不应被调用（因为锁定就失败了）
            self.account_manager.unlock_funds_for_order.assert_not_called()
    
    def test_order_cancellation_boundary(self, setup_server):
        """
        测试订单取消的边界情况
        """
        # 1. the test for missing symbol parameter
        response = self.client.delete(
            '/api/v1/order',
            headers={'X-API-KEY': self.test_api_key}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "msg" in data
        
        # 2. test for missing orderId
        response = self.client.delete(
            '/api/v1/order?symbol=BTCUSDT',
            headers={'X-API-KEY': self.test_api_key}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "msg" in data
        
        # 3. test cancelling a non-existent order
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            self.matching_engine.cancel_order.return_value = False
            response = self.client.delete(
                '/api/v1/order?symbol=BTCUSDT&orderId=non_existent_id',
                headers={'X-API-KEY': self.test_api_key}
            )
            # Accept either 400 or 404 status code based on the implementation
            assert response.status_code in (400, 404)
            data = json.loads(response.data)
            assert "msg" in data
            
        # 4. test successful order cancellation
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            self.matching_engine.cancel_order.return_value = True
            response = self.client.delete(
                '/api/v1/order?symbol=BTCUSDT&orderId=test_order_id',
                headers={'X-API-KEY': self.test_api_key}
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get("status") == "CANCELED"