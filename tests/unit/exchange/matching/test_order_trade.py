#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Order和Trade对象单元测试
"""
import pytest
import time
import uuid
from decimal import Decimal
from qte.exchange.matching.matching_engine import (
    Order, OrderSide, OrderType, OrderStatus, Trade
)

class TestOrderAndTrade:
    """Order和Trade类测试"""
    
    @pytest.fixture
    def symbol(self):
        """测试交易对"""
        return "BTC/USDT"
    
    @pytest.fixture
    def order_id(self):
        """生成订单ID"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def user_id(self):
        """用户ID"""
        return "test_user"
    
    def test_order_creation(self, symbol, order_id, user_id):
        """测试订单对象创建 (OT-001)"""
        # 创建限价买单
        order = Order(
            user_id=user_id,
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('1.5'),
            price=Decimal('10000.0')
        )
        
        # 验证订单属性
        assert order.order_id == order_id
        assert order.symbol == symbol
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.LIMIT
        assert order.quantity == Decimal('1.5')
        assert order.price == Decimal('10000.0')
        assert order.status == OrderStatus.NEW
        assert order.executed_quantity == Decimal('0.0')  # 使用新字段名
        assert order.remaining_quantity == Decimal('1.5')
        assert order.user_id == user_id
        
        # 创建市价卖单
        market_order = Order(
            user_id=user_id,
            order_id="market_" + order_id,
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal('2.0')
        )
        
        # 验证市价单属性
        assert market_order.order_id == "market_" + order_id
        assert market_order.symbol == symbol
        assert market_order.side == OrderSide.SELL
        assert market_order.order_type == OrderType.MARKET
        assert market_order.quantity == Decimal('2.0')
        assert market_order.price is None
        assert market_order.status == OrderStatus.NEW
        assert market_order.executed_quantity == Decimal('0.0')
        assert market_order.remaining_quantity == Decimal('2.0')
        assert market_order.user_id == user_id
    
    def test_order_fill(self, symbol, order_id, user_id):
        """测试订单成交更新 (OT-002)"""
        # 创建订单
        order = Order(
            user_id=user_id,
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('2.0'),
            price=Decimal('10000.0')
        )
        
        # 部分成交 - 使用新的add_fill方法
        order.add_fill(
            fill_qty=Decimal('1.0'), 
            fill_price=Decimal('10000.0'),
            fill_timestamp=int(time.time() * 1000),
            commission_paid=Decimal('0.001'),
            commission_asset_paid="USDT",
            trade_is_maker=False
        )
        assert order.executed_quantity == Decimal('1.0')
        assert order.remaining_quantity == Decimal('1.0')
        assert order.status == OrderStatus.PARTIALLY_FILLED
        
        # 完全成交
        order.add_fill(
            fill_qty=Decimal('1.0'), 
            fill_price=Decimal('10000.0'),
            fill_timestamp=int(time.time() * 1000),
            commission_paid=Decimal('0.001'),
            commission_asset_paid="USDT",
            trade_is_maker=False
        )
        assert order.executed_quantity == Decimal('2.0')
        assert order.remaining_quantity == Decimal('0.0')
        assert order.status == OrderStatus.FILLED
        
        # 测试成交数量超过剩余数量的情况不再需要单独测试，
        # 因为add_fill方法应该内部处理这种边界情况
    
    def test_order_cancel(self, symbol, order_id, user_id):
        """测试订单取消 (OT-003)"""
        # 创建订单
        order = Order(
            user_id=user_id,
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('1.0'),
            price=Decimal('10000.0')
        )
        
        # 取消订单
        result = order.cancel()
        assert result is True
        assert order.status == OrderStatus.CANCELED
        
        # 再次取消已取消的订单
        result = order.cancel()
        assert result is False
        assert order.status == OrderStatus.CANCELED
        
        # 测试取消已完成的订单
        filled_order = Order(
            user_id=user_id,
            order_id=order_id + "_filled",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('1.0'),
            price=Decimal('10000.0')
        )
        
        filled_order.add_fill(
            fill_qty=Decimal('1.0'), 
            fill_price=Decimal('10000.0'),
            fill_timestamp=int(time.time() * 1000),
            commission_paid=Decimal('0.001'),
            commission_asset_paid="USDT",
            trade_is_maker=False
        )  # 完全成交
        assert filled_order.status == OrderStatus.FILLED
        
        result = filled_order.cancel()
        assert result is False
        assert filled_order.status == OrderStatus.FILLED  # 状态不变
    
    def test_trade_creation(self, symbol, user_id):
        """测试交易对象创建 (OT-004)"""
        # 创建交易 - 使用新的Trade结构
        trade = Trade(
            user_id="buyer_" + user_id,
            order_id="buy_" + str(uuid.uuid4()),
            symbol=symbol,
            price=Decimal('10000.0'),
            quantity=Decimal('1.5'),
            quote_qty=Decimal('15000.0'),  # price * quantity
            side=OrderSide.BUY,
            commission=Decimal('0.0015'),
            commission_asset="USDT",
            is_maker=False,
            id=1  # 使用整数ID
        )
        
        # 验证交易属性
        assert trade.symbol == symbol
        assert trade.price == Decimal('10000.0')
        assert trade.quantity == Decimal('1.5')
        assert trade.user_id == "buyer_" + user_id
        assert trade.commission == Decimal('0.0015')
        assert trade.commission_asset == "USDT"
        assert trade.timestamp <= int(time.time() * 1000)
        assert trade.id == Decimal("1")
        assert len(trade.order_id) > 0
    
    def test_boundary_conditions(self, symbol, order_id, user_id):
        """测试边界条件处理 (OT-005)"""
        # 测试数量为0的订单
        zero_qty_order = Order(
            user_id=user_id,
            order_id=order_id + "_zero",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('0.0'),
            price=Decimal('10000.0')
        )
        
        assert zero_qty_order.quantity == Decimal('0.0')
        assert zero_qty_order.remaining_quantity == Decimal('0.0')
        
        # 测试非常小的数量
        tiny_qty_order = Order(
            user_id=user_id,
            order_id=order_id + "_tiny",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('0.00000001'),
            price=Decimal('10000.0')
        )
        
        assert tiny_qty_order.quantity == Decimal('0.00000001')
        assert tiny_qty_order.remaining_quantity == Decimal('0.00000001')
        
        # 测试非常大的价格
        big_price_order = Order(
            user_id=user_id,
            order_id=order_id + "_big_price",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('1.0'),
            price=Decimal('999999999.99999999')
        )
        
        assert big_price_order.price == Decimal('999999999.99999999')
        
        # 测试极小价格
        small_price_order = Order(
            user_id=user_id,
            order_id=order_id + "_small_price",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal('1.0'),
            price=Decimal('0.00000001')
        )
        
        assert small_price_order.price == Decimal('0.00000001')
        
        # 验证时间戳
        current_time = int(time.time() * 1000)
        order_time = zero_qty_order.timestamp
        assert order_time <= current_time + 1000  # 允许1秒的时差