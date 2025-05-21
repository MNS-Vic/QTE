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
from qte.exchange.matching.matching_engine import MatchingEngine, OrderStatus, OrderSide
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
        mock_order.side = OrderSide.BUY
        mock_order.order_id = "123"
        mock_order.symbol = "BTCUSDT"
        mock_order.user_id = self.test_user_id
        mock_order.remaining_quantity = Decimal("1.0")
        mock_order.price = Decimal("10000.0")
        
        # 手动添加get_order方法，而不是使用spec
        self.matching_engine.get_order = MagicMock(return_value=mock_order)
        
        # 模拟account_manager方法
        self.account_manager.unlock_funds_for_order = MagicMock(return_value=True)
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
    
    def test_quote_order_qty_market_buy(self, setup_server):
        """测试报价金额市价买单功能"""
        # 模拟account_manager的lock_funds_for_order方法
        self.account_manager.lock_funds_for_order.return_value = True
        
        # 模拟matching_engine的place_order方法
        self.matching_engine.place_order.return_value = True
        
        # 创建mock订单对象
        mock_order_dict = {
            "orderId": "test_order_id",
            "clientOrderId": "test_client_order_id",
            "symbol": "BTCUSDT",
            "price": None,
            "origQty": "0",
            "executedQty": "0",
            "status": "NEW",
            "type": "MARKET",
            "side": "BUY",
            "time": int(time.time() * 1000),
            "origQuoteOrderQty": "1000.00000000"
        }
        
        # 测试创建报价金额市价买单
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            # 在mock对象上添加to_dict方法
            self.matching_engine.place_order.side_effect = lambda order: setattr(order, 'to_dict', lambda: mock_order_dict) or True
            
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "quoteOrderQty": "1000"  # 使用报价金额下单
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # 验证响应包含origQuoteOrderQty字段
            assert "origQuoteOrderQty" in data
            assert data["origQuoteOrderQty"] == "1000.00000000"
            
            # 验证account_manager方法调用
            self.account_manager.lock_funds_for_order.assert_called_once()
            args, kwargs = self.account_manager.lock_funds_for_order.call_args
            assert kwargs["is_quote_order"] is True
            assert kwargs["amount"] == Decimal("1000")
    
    def test_self_trade_prevention_mode(self, setup_server):
        """测试自成交保护功能"""
        # 模拟account_manager的lock_funds_for_order方法
        self.account_manager.lock_funds_for_order.return_value = True
        
        # 模拟matching_engine的place_order方法
        self.matching_engine.place_order.return_value = True
        
        # 创建mock订单对象
        mock_order_dict = {
            "orderId": "test_order_id",
            "clientOrderId": "test_client_order_id",
            "symbol": "BTCUSDT",
            "price": "10000.00000000",
            "origQty": "1.00000000",
            "executedQty": "0",
            "status": "NEW",
            "type": "LIMIT",
            "side": "BUY",
            "time": int(time.time() * 1000),
            "selfTradePreventionMode": "EXPIRE_TAKER"  # 自成交保护模式
        }
        
        # 测试创建带有自成交保护的订单
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            # 在mock对象上添加to_dict方法
            self.matching_engine.place_order.side_effect = lambda order: setattr(order, 'to_dict', lambda: mock_order_dict) or True
            
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "1.0",
                    "price": "10000",
                    "selfTradePreventionMode": "EXPIRE_TAKER"  # 设置自成交保护模式
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # 验证响应包含selfTradePreventionMode字段
            assert "selfTradePreventionMode" in data
            assert data["selfTradePreventionMode"] == "EXPIRE_TAKER"
            
            # 验证order对象创建时的参数
            args, kwargs = self.matching_engine.place_order.call_args
            order = args[0]
            assert order.self_trade_prevention_mode == "EXPIRE_TAKER"
            
        # 测试使用无效的自成交保护模式
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "1.0",
                    "price": "10000",
                    "selfTradePreventionMode": "INVALID_MODE"  # 无效的模式
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 400
            error_data = json.loads(response.data)
            assert error_data["code"] == INVALID_PARAM
    
    def test_market_order_liquidity_insufficient(self, setup_server):
        """测试使用quoteOrderQty的市价单流动性不足处理"""
        # 模拟account_manager的lock_funds_for_order方法
        self.account_manager.lock_funds_for_order.return_value = True
        
        # 创建mock订单对象 - 部分成交且过期
        mock_order_dict = {
            "orderId": "test_order_id",
            "clientOrderId": "test_client_order_id",
            "symbol": "BTCUSDT",
            "price": None,
            "origQty": "0.5",
            "executedQty": "0.5",
            "status": "EXPIRED",  # 因流动性不足而过期
            "type": "MARKET",
            "side": "BUY",
            "time": int(time.time() * 1000),
            "origQuoteOrderQty": "1000.00000000"
        }
        
        # 模拟撮合引擎处理 - 返回部分成交的订单
        def mock_place_order(order):
            # 设置部分成交状态
            order.filled_quantity = 0.5
            order.remaining_quantity = 0.0
            order.status = OrderStatus.EXPIRED
            return setattr(order, 'to_dict', lambda: mock_order_dict) or True
            
        self.matching_engine.place_order.side_effect = mock_place_order
        
        # 测试下单
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "quoteOrderQty": "1000"  # 使用报价金额下单
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # 验证订单状态为EXPIRED
            assert data["status"] == "EXPIRED"
            # 验证部分成交量
            assert data["executedQty"] == "0.5"
    
    def test_cancel_restrictions(self, setup_server):
        """测试取消订单限制功能"""
        # 模拟订单对象
        class MockOrder:
            def __init__(self, status, user_id, side):
                self.order_id = "test_order_id"
                self.status = status
                self.user_id = user_id
                self.side = side
                self.remaining_quantity = Decimal("1.0")
                self.price = Decimal("10000.0")
                self.symbol = "BTCUSDT"
        
        # 模拟不同状态的订单
        new_order = MockOrder(OrderStatus.NEW, self.test_user_id, OrderSide.BUY)
        partially_filled_order = MockOrder(OrderStatus.PARTIALLY_FILLED, self.test_user_id, OrderSide.BUY)
        
        # 设置需要的mock方法
        self.matching_engine.get_order = MagicMock()
        self.matching_engine.cancel_order = MagicMock(return_value=True)
        # 只测试取消订单限制功能，不需要实际执行资金解锁逻辑
        self.account_manager.unlock_funds_for_order = MagicMock(return_value=True)
        
        # 测试只允许取消NEW状态的订单
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            # 模拟返回PARTIALLY_FILLED状态的订单
            self.matching_engine.get_order.return_value = partially_filled_order
            
            # 测试ONLY_NEW限制 - 应该被拒绝
            response = self.client.delete(
                '/api/v3/order?symbol=BTCUSDT&orderId=123&cancelRestrictions=ONLY_NEW',
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 400
            error_data = json.loads(response.data)
            assert error_data["code"] == CANCEL_REJECTED
            
        # 测试无效的限制值
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.delete(
                '/api/v3/order?symbol=BTCUSDT&orderId=123&cancelRestrictions=INVALID_VALUE',
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 400
            error_data = json.loads(response.data)
            assert error_data["code"] == INVALID_PARAM
    
    def test_price_match_feature(self, setup_server):
        """测试价格匹配功能"""
        # 模拟account_manager的lock_funds_for_order方法
        self.account_manager.lock_funds_for_order.return_value = True
        
        # 创建mock订单对象
        mock_order_dict = {
            "orderId": "test_order_id",
            "clientOrderId": "test_client_order_id",
            "symbol": "BTCUSDT",
            "price": "10000.00000000",  # 匹配后的价格
            "origQty": "1.00000000",
            "executedQty": "0",
            "status": "NEW",
            "type": "LIMIT",
            "side": "BUY",
            "time": int(time.time() * 1000),
            "priceMatch": "OPPONENT"  # 价格匹配模式
        }
        
        # 模拟匹配引擎处理
        def mock_place_order(order):
            # 设置匹配后的价格
            order.price = 10000.0
            return setattr(order, 'to_dict', lambda: mock_order_dict) or True
            
        self.matching_engine.place_order.side_effect = mock_place_order
        
        # 测试创建带有价格匹配的限价单
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "1.0",
                    "priceMatch": "OPPONENT"  # 使用对手价
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 打印详细的错误信息
            if response.status_code != 200:
                print(f"Error response ({response.status_code}):", response.data)
                error_data = json.loads(response.data)
                print(f"Error code: {error_data.get('code')}")
                print(f"Error message: {error_data.get('msg')}")
            
            # 验证响应
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # 验证响应包含priceMatch字段
            assert "priceMatch" in data
            assert data["priceMatch"] == "OPPONENT"
            
            # 验证订单已获得匹配价格
            assert data["price"] == "10000.00000000"
            
            # 验证order对象创建时的参数
            args, kwargs = self.matching_engine.place_order.call_args
            order = args[0]
            assert order.price_match == "OPPONENT"
            
        # 测试使用无效的价格匹配模式
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "1.0",
                    "priceMatch": "INVALID_MODE"  # 无效的模式
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 400
            error_data = json.loads(response.data)
            assert error_data["code"] == INVALID_PARAM
            
        # 测试同时提供价格和价格匹配（应该被拒绝）
        with patch.object(self.server, '_authenticate', return_value=self.test_user_id):
            response = self.client.post(
                '/api/v3/order',
                json={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": "1.0",
                    "price": "9500",
                    "priceMatch": "OPPONENT"  # 不能同时使用价格和价格匹配
                },
                headers={'X-API-KEY': self.test_api_key}
            )
            
            # 验证响应
            assert response.status_code == 400
            error_data = json.loads(response.data)
            assert error_data["code"] == INVALID_PARAM 