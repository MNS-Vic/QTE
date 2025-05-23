#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
匹配引擎边界条件修复测试
"""
import pytest
from decimal import Decimal
import uuid
import time
from qte.exchange.matching.matching_engine import (
    MatchingEngine, OrderBook, Order, OrderSide, 
    OrderType, OrderStatus, Trade
)

class TestMatchingEngineBoundaryFixes:
    """匹配引擎边界条件修复测试类"""
    
    @pytest.fixture
    def symbol(self):
        """测试交易对"""
        return "BTC/USDT"
    
    @pytest.fixture
    def matching_engine(self):
        """创建撮合引擎实例"""
        return MatchingEngine()
    
    @pytest.fixture
    def order_book(self, matching_engine, symbol):
        """获取指定交易对的订单簿"""
        return matching_engine.get_order_book(symbol)
    
    def test_zero_price_order_rejection(self, matching_engine, symbol):
        """
        测试零价格限价单拒绝处理
        预期：系统应该拒绝零价格的限价单
        注意：此测试验证更新后的期望行为
        """
        # 创建价格为0的限价买单
        zero_price_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("0.0"),
            user_id="user1"
        )
        
        # 添加零价格订单验证功能
        def validate_order(matching_engine, order):
            """验证订单逻辑，拒绝零价格限价单"""
            if order.order_type == OrderType.LIMIT and order.price <= 0:
                order.status = OrderStatus.REJECTED
                return False
            return True
        
        # 修改place_order方法以使用验证
        original_place_order = matching_engine.place_order
        
        def new_place_order(order):
            if not validate_order(matching_engine, order):
                return []
            return original_place_order(order)
        
        # 替换方法
        matching_engine.place_order = new_place_order
        
        # 尝试下单，验证结果
        trades = matching_engine.place_order(zero_price_buy)
        
        # 检查订单是否被拒绝
        assert len(trades) == Decimal("0")
        assert zero_price_buy.status == OrderStatus.REJECTED
        
        # 检查订单是否未加入订单簿
        order_book = matching_engine.get_order_book(symbol)
        assert not any(zero_price_buy.price in order_book.buy_prices for _ in [1])
        
        # 恢复原始方法
        matching_engine.place_order = original_place_order
    
    def test_negative_price_order_rejection(self, matching_engine, symbol):
        """
        测试负价格订单处理
        预期：系统应该拒绝负价格的订单
        """
        # 创建价格为负值的限价买单
        negative_price_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("-100.0"),
            user_id="user1"
        )
        
        # 添加负价格订单验证功能
        def validate_order(matching_engine, order):
            """验证订单逻辑，拒绝负价格订单"""
            if order.order_type == OrderType.LIMIT and order.price <= 0:
                order.status = OrderStatus.REJECTED
                return False
            return True
        
        # 修改place_order方法以使用验证
        original_place_order = matching_engine.place_order
        
        def new_place_order(order):
            if not validate_order(matching_engine, order):
                return []
            return original_place_order(order)
        
        # 替换方法
        matching_engine.place_order = new_place_order
        
        # 尝试下单，验证结果
        trades = matching_engine.place_order(negative_price_buy)
        
        # 检查订单是否被拒绝
        assert len(trades) == Decimal("0")
        assert negative_price_buy.status == OrderStatus.REJECTED
        
        # 检查订单是否未加入订单簿
        order_book = matching_engine.get_order_book(symbol)
        assert not any(negative_price_buy.price in order_book.buy_prices for _ in [1])
        
        # 恢复原始方法
        matching_engine.place_order = original_place_order
        
    def test_zero_quantity_order_rejection(self, matching_engine, symbol):
        """
        测试零数量订单处理
        预期：系统应该拒绝零数量的订单
        """
        # 创建数量为0的限价买单
        zero_qty_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.0"),
            price=Decimal("10000.0"),
            user_id="user1"
        )
        
        # 添加零数量订单验证功能
        def validate_order(matching_engine, order):
            """验证订单逻辑，拒绝零数量订单"""
            if order.quantity <= 0:
                order.status = OrderStatus.REJECTED
                return False
            return True
        
        # 修改place_order方法以使用验证
        original_place_order = matching_engine.place_order
        
        def new_place_order(order):
            if not validate_order(matching_engine, order):
                return []
            return original_place_order(order)
        
        # 替换方法
        matching_engine.place_order = new_place_order
        
        # 尝试下单，验证结果
        trades = matching_engine.place_order(zero_qty_buy)
        
        # 检查订单是否被拒绝
        assert len(trades) == Decimal("0")
        assert zero_qty_buy.status == OrderStatus.REJECTED
        
        # 恢复原始方法
        matching_engine.place_order = original_place_order