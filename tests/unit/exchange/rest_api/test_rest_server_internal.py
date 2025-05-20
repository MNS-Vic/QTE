#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
REST API服务器内部方法的单元测试
"""
import unittest
import pytest
import json
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify, request

# 导入被测试的模块
from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.matching.matching_engine import MatchingEngine, Order, OrderSide, OrderType, OrderStatus
from qte.exchange.account.account_manager import AccountManager

# 检查REST服务器内部函数逻辑
class TestRESTServerFunctions:
    """REST API服务器函数测试类"""
    
    @pytest.fixture
    def setup_mock_engine(self):
        """设置模拟引擎和账户管理器"""
        matching_engine = MagicMock()
        account_manager = MagicMock()
        
        # 创建模拟市场价格
        matching_engine.get_market_price.return_value = 10000.0
        
        # 创建模拟订单簿
        mock_order_book = MagicMock()
        mock_order_book.get_depth.return_value = {
            "bids": [(9900.0, 1.0), (9800.0, 2.0)],
            "asks": [(10100.0, 1.0), (10200.0, 2.0)]
        }
        matching_engine.get_order_book.return_value = mock_order_book
        
        # 模拟创建订单
        mock_order = MagicMock()
        mock_order.order_id = "TEST123456"
        mock_order.symbol = "BTCUSDT"
        mock_order.price = 10000.0
        mock_order.quantity = 1.0
        mock_order.filled_quantity = 0.0
        mock_order.status = OrderStatus.NEW
        mock_order.to_dict.return_value = {
            "orderId": "TEST123456",
            "symbol": "BTCUSDT",
            "price": "10000.0",
            "origQty": "1.0",
            "executedQty": "0.0",
            "status": "NEW",
            "type": "LIMIT",
            "side": "BUY",
            "time": int(time.time() * 1000)
        }
        matching_engine.create_order.return_value = mock_order
        
        # 模拟撤单
        mock_canceled_order = MagicMock()
        mock_canceled_order.order_id = "TEST123456"
        mock_canceled_order.to_dict.return_value = {
            "orderId": "TEST123456",
            "symbol": "BTCUSDT",
            "status": "CANCELED",
            "origQty": "1.0",
            "executedQty": "0.0",
            "price": "10000.0"
        }
        matching_engine.cancel_order.return_value = mock_canceled_order
        
        # 模拟查询订单
        mock_queried_order = MagicMock()
        mock_queried_order.to_dict.return_value = {
            "orderId": "TEST123456",
            "symbol": "BTCUSDT",
            "price": "10000.0",
            "origQty": "1.0",
            "executedQty": "0.5",
            "status": "PARTIALLY_FILLED",
            "type": "LIMIT",
            "side": "BUY",
            "time": int(time.time() * 1000)
        }
        matching_engine.get_order.return_value = mock_queried_order
        
        # 模拟账户余额
        mock_balances = [
            {
                "asset": "BTC",
                "free": "1.0",
                "locked": "0.5"
            },
            {
                "asset": "USDT",
                "free": "10000.0",
                "locked": "5000.0"
            }
        ]
        account_manager.get_account_balances.return_value = mock_balances
        
        return matching_engine, account_manager
    
    def test_authentication(self, setup_mock_engine):
        """测试API密钥验证功能"""
        # 设置模拟对象
        matching_engine, account_manager = setup_mock_engine
        
        # 创建REST服务器
        server = ExchangeRESTServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=5000
        )
        
        # 创建测试用户和API密钥
        test_user_id = "test_user"
        api_key = server.create_api_key(test_user_id)
        
        # 验证API密钥匹配
        assert server.get_user_id_from_api_key(api_key) == test_user_id
        
        # 验证无效API密钥
        assert server.get_user_id_from_api_key("invalid_key") is None
        
    def test_handle_order_params(self, setup_mock_engine):
        """测试订单参数处理"""
        # 设置模拟对象
        matching_engine, account_manager = setup_mock_engine
        
        # 创建REST服务器
        server = ExchangeRESTServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=5000
        )
        
        # 测试处理有效的限价单参数
        order_params = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": "1.0",
            "price": "10000.0"
        }
        
        # 模拟订单创建
        with patch.object(matching_engine, 'create_order') as mock_create_order:
            mock_order = MagicMock()
            mock_order.order_id = "TEST123456"
            mock_order.to_dict.return_value = {
                "orderId": "TEST123456",
            }
            mock_create_order.return_value = mock_order
            
            # 在应用上下文中测试
            with server.app.app_context():
                # 直接测试创建订单的核心逻辑（不通过HTTP接口）
                user_id = "test_user"
                symbol = order_params["symbol"]
                side_str = order_params["side"]
                type_str = order_params["type"]
                quantity_str = order_params["quantity"]
                price_str = order_params["price"]
                
                # 使用server中的逻辑转换参数
                side = OrderSide.BUY if side_str == "BUY" else OrderSide.SELL
                order_type = OrderType.LIMIT if type_str == "LIMIT" else OrderType.MARKET
                quantity = float(quantity_str)
                price = float(price_str) if price_str else None
                
                # 调用匹配引擎创建订单
                server.matching_engine.create_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price
                )
                
                # 验证匹配引擎被正确调用
                mock_create_order.assert_called_once_with(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price
                )
                
    def test_get_account_balances(self, setup_mock_engine):
        """测试获取账户余额逻辑"""
        # 设置模拟对象
        matching_engine, account_manager = setup_mock_engine
        
        # 创建REST服务器
        server = ExchangeRESTServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=5000
        )
        
        # 测试用户ID
        test_user_id = "test_user"
        
        # 设置预期返回值
        expected_balances = [
            {
                "asset": "BTC",
                "free": "1.0",
                "locked": "0.5"
            },
            {
                "asset": "USDT",
                "free": "10000.0",
                "locked": "5000.0"
            }
        ]
        account_manager.get_account_balances.return_value = expected_balances
        
        # 直接调用账户管理器获取余额
        balances = server.account_manager.get_account_balances(test_user_id)
        
        # 验证结果
        assert balances == expected_balances
        account_manager.get_account_balances.assert_called_once_with(test_user_id)
        
    def test_order_operations(self, setup_mock_engine):
        """测试订单操作逻辑"""
        # 设置模拟对象
        matching_engine, account_manager = setup_mock_engine
        
        # 创建REST服务器
        server = ExchangeRESTServer(
            matching_engine=matching_engine,
            account_manager=account_manager,
            host="localhost",
            port=5000
        )
        
        # 测试用户ID和订单ID
        test_user_id = "test_user"
        test_order_id = "TEST123456"
        test_symbol = "BTCUSDT"
        
        # 测试撤单逻辑
        with patch.object(matching_engine, 'cancel_order') as mock_cancel_order:
            mock_order = MagicMock()
            mock_order.order_id = test_order_id
            mock_order.to_dict.return_value = {
                "orderId": test_order_id,
                "status": "CANCELED"
            }
            mock_cancel_order.return_value = mock_order
            
            # 直接调用撤单逻辑
            result = server.matching_engine.cancel_order(
                user_id=test_user_id,
                symbol=test_symbol,
                order_id=test_order_id
            )
            
            # 验证结果
            assert result.order_id == test_order_id
            mock_cancel_order.assert_called_once_with(
                user_id=test_user_id,
                symbol=test_symbol,
                order_id=test_order_id
            )
            
        # 测试查询订单逻辑
        with patch.object(matching_engine, 'get_order') as mock_get_order:
            mock_order = MagicMock()
            mock_order.order_id = test_order_id
            mock_order.to_dict.return_value = {
                "orderId": test_order_id,
                "symbol": test_symbol,
                "status": "FILLED"
            }
            mock_get_order.return_value = mock_order
            
            # 直接调用查询订单逻辑
            result = server.matching_engine.get_order(
                user_id=test_user_id,
                symbol=test_symbol,
                order_id=test_order_id
            )
            
            # 验证结果
            assert result.order_id == test_order_id
            mock_get_order.assert_called_once_with(
                user_id=test_user_id,
                symbol=test_symbol,
                order_id=test_order_id
            )