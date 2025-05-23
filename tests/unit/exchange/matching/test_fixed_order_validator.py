#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试订单验证器
"""
import pytest
from decimal import Decimal

from qte.exchange.matching.matching_engine import Order, OrderSide, OrderType, OrderStatus
from qte.exchange.matching.order_validator import OrderValidator

class TestOrderValidator:
    """订单验证器测试类"""
    
    @pytest.fixture
    def validator(self):
        """设置测试环境"""
        return OrderValidator()
    
    def test_validate_limit_order(self, validator):
        """测试验证限价单"""
        # 创建一个有效的限价单
        order = Order(
            order_id="test_order_1",
            user_id="test_user",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("10000.0"),
            quantity=Decimal("1.5")
        )
        
        # 验证订单
        is_valid, errors = validator.validate_order(order)
        
        # 断言
        assert is_valid is True
        assert errors == []
    
    def test_validate_market_order(self, validator):
        """测试验证市价单"""
        # 创建一个有效的市价单
        order = Order(
            order_id="test_order_2",
            user_id="test_user",
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.5")
        )
        
        # 验证订单
        is_valid, errors = validator.validate_order(order)
        
        # 断言
        assert is_valid is True
        assert errors == []
    
    def test_validate_invalid_price(self, validator):
        """测试验证无效价格"""
        # 创建一个价格无效的限价单
        order = Order(
            order_id="test_order_3",
            user_id="test_user",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("-100.0"),  # 负价格
            quantity=Decimal("1.5")
        )
        
        # 直接测试价格验证方法
        is_valid, reason = validator.validate_order_price(Decimal("-100.0"))
        
        # 断言
        assert is_valid is False
        assert "价格必须大于零" in reason
        
    def test_validate_invalid_quantity(self, validator):
        """测试验证无效数量"""
        # 创建一个数量无效的限价单
        order = Order(
            order_id="test_order_4",
            user_id="test_user",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("10000.0"),
            quantity=Decimal("0")  # 零数量
        )
        
        # 验证订单
        is_valid, errors = validator.validate_order(order)
        
        # 断言
        assert is_valid is False
        assert errors is not None
        assert len(errors) > 0
        assert any("订单数量必须大于0" in err for err in errors)
        assert order.status == OrderStatus.REJECTED
        
    def test_validate_missing_symbol(self, validator):
        """测试缺少交易对信息"""
        # 创建一个缺少交易对的订单
        order = Order(
            order_id="test_order_5",
            user_id="test_user",
            symbol="",  # 空交易对
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("10000.0"),
            quantity=Decimal("1.5")
        )
        
        # 验证订单
        is_valid, errors = validator.validate_order(order)
        
        # 断言
        assert is_valid is False
        assert errors is not None
        assert len(errors) > 0
        assert any("订单必须指定交易对" in err for err in errors)
        assert order.status == OrderStatus.REJECTED
        
    def test_validate_limit_order_without_price(self, validator):
        """测试无价格的限价单"""
        # 创建一个没有价格的限价单
        order = Order(
            order_id="test_order_6",
            user_id="test_user",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=None,  # 无价格
            quantity=Decimal("1.5")
        )
        
        # 验证订单
        is_valid, errors = validator.validate_order(order)
        
        # 断言
        assert is_valid is False
        assert errors is not None
        assert len(errors) > 0
        assert any("限价单必须指定价格" in err for err in errors)
        assert order.status == OrderStatus.REJECTED
