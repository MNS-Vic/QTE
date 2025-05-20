#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试订单验证模块
"""
import pytest
import uuid

from qte.exchange.matching.matching_engine import (
    Order, OrderSide, OrderType, OrderStatus
)
from qte.exchange.matching.order_validator import OrderValidator

class TestOrderValidator:
    """测试订单验证器类"""
    
    def test_validate_order_valid(self):
        """测试有效订单的验证"""
        # 创建有效的限价买单
        valid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(valid_order)
        
        # 验证结果
        assert is_valid is True
        assert len(errors) == 0
        assert valid_order.status == OrderStatus.NEW
    
    def test_validate_order_missing_symbol(self):
        """测试缺少交易对的订单验证"""
        # 创建缺少交易对的订单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="",  # 空交易对
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "订单必须指定交易对" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_order_zero_quantity(self):
        """测试零数量订单的验证"""
        # 创建零数量的订单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.0,  # 零数量
            price=50000.0,
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "订单数量必须大于0" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_order_negative_quantity(self):
        """测试负数量订单的验证"""
        # 创建负数量的订单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=-1.0,  # 负数量
            price=50000.0,
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "订单数量必须大于0" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_limit_order_missing_price(self):
        """测试缺少价格的限价单验证"""
        # 创建缺少价格的限价单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=None,  # 缺少价格
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "限价单必须指定价格" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_limit_order_zero_price(self):
        """测试零价格限价单验证"""
        # 创建零价格的限价单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=0.0,  # 零价格
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "限价单价格必须大于0" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_limit_order_negative_price(self):
        """测试负价格限价单验证"""
        # 创建负价格的限价单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=-1.0,  # 负价格
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "限价单价格必须大于0" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_market_order(self):
        """测试市价单验证"""
        # 创建有效的市价单
        valid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0,
            price=None,  # 市价单价格可以是None
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(valid_order)
        
        # 验证结果
        assert is_valid is True
        assert len(errors) == 0
        assert valid_order.status == OrderStatus.NEW
    
    def test_validate_stop_order_missing_stop_price(self):
        """测试缺少触发价格的止损单验证"""
        # 创建缺少触发价格的止损单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=1.0,
            price=None,
            stop_price=None,  # 缺少触发价格
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "止损单必须指定触发价格" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_validate_stop_limit_order(self):
        """测试止损限价单验证"""
        # 创建有效的止损限价单
        valid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=1.0,
            price=45000.0,  # 限价
            stop_price=46000.0,  # 触发价格
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(valid_order)
        
        # 验证结果
        assert is_valid is True
        assert len(errors) == 0
        assert valid_order.status == OrderStatus.NEW
    
    def test_validate_stop_limit_order_missing_price(self):
        """测试缺少限价的止损限价单验证"""
        # 创建缺少限价的止损限价单
        invalid_order = Order(
            order_id=str(uuid.uuid4()),
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=1.0,
            price=None,  # 缺少限价
            stop_price=46000.0,
            user_id="test_user"
        )
        
        # 验证订单
        is_valid, errors = OrderValidator.validate_order(invalid_order)
        
        # 验证结果
        assert is_valid is False
        assert len(errors) == 1
        assert "止损限价单必须同时指定触发价格和限价" in errors[0]
        assert invalid_order.status == OrderStatus.REJECTED
    
    def test_check_price_precision(self):
        """测试价格精度检查"""
        # 定义价格精度配置
        price_precision = {
            "BTC/USDT": 2,  # 最多2位小数
            "ETH/USDT": 3   # 最多3位小数
        }
        
        # 测试符合精度要求的价格
        valid_result, valid_error = OrderValidator.check_price_precision(
            price=1234.56,
            symbol="BTC/USDT",
            price_precision=price_precision
        )
        assert valid_result is True
        assert valid_error is None
        
        # 测试超出精度要求的价格
        invalid_result, invalid_error = OrderValidator.check_price_precision(
            price=1234.567,
            symbol="BTC/USDT",
            price_precision=price_precision
        )
        assert invalid_result is False
        assert "价格精度超过限制" in invalid_error
        
        # 测试未配置精度的交易对
        unconfigured_result, unconfigured_error = OrderValidator.check_price_precision(
            price=1234.5678,
            symbol="XRP/USDT",
            price_precision=price_precision
        )
        assert unconfigured_result is True
        assert unconfigured_error is None
    
    def test_check_quantity_precision(self):
        """测试数量精度检查"""
        # 定义数量精度配置
        quantity_precision = {
            "BTC/USDT": 6,  # 最多6位小数
            "ETH/USDT": 4   # 最多4位小数
        }
        
        # 测试符合精度要求的数量
        valid_result, valid_error = OrderValidator.check_quantity_precision(
            quantity=1.123456,
            symbol="BTC/USDT",
            quantity_precision=quantity_precision
        )
        assert valid_result is True
        assert valid_error is None
        
        # 测试超出精度要求的数量
        invalid_result, invalid_error = OrderValidator.check_quantity_precision(
            quantity=1.12345,
            symbol="ETH/USDT",
            quantity_precision=quantity_precision
        )
        assert invalid_result is False
        assert "数量精度超过限制" in invalid_error
    
    def test_check_min_order_size(self):
        """测试最小订单金额检查"""
        # 定义最小订单金额配置
        min_notional = {
            "BTC/USDT": 10.0,  # 最小10 USDT
            "ETH/USDT": 5.0    # 最小5 USDT
        }
        
        # 测试符合最小金额要求的订单
        valid_result, valid_error = OrderValidator.check_min_order_size(
            price=100.0,
            quantity=0.2,
            symbol="BTC/USDT",
            min_notional=min_notional
        )
        assert valid_result is True
        assert valid_error is None
        
        # 测试低于最小金额要求的订单
        invalid_result, invalid_error = OrderValidator.check_min_order_size(
            price=100.0,
            quantity=0.05,
            symbol="BTC/USDT",
            min_notional=min_notional
        )
        assert invalid_result is False
        assert "订单金额" in invalid_error
        assert "小于最小要求" in invalid_error