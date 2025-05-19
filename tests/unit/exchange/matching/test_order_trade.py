#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Order和Trade对象单元测试
"""
import pytest
import time
import uuid
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
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.5,
            price=10000.0,
            user_id=user_id
        )
        
        # 验证订单属性
        assert order.order_id == order_id
        assert order.symbol == symbol
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.LIMIT
        assert order.quantity == 1.5
        assert order.price == 10000.0
        assert order.status == OrderStatus.NEW
        assert order.filled_quantity == 0.0
        assert order.remaining_quantity == 1.5
        assert order.user_id == user_id
        
        # 创建市价卖单
        market_order = Order(
            order_id="market_" + order_id,
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=2.0,
            user_id=user_id
        )
        
        # 验证市价单属性
        assert market_order.order_id == "market_" + order_id
        assert market_order.symbol == symbol
        assert market_order.side == OrderSide.SELL
        assert market_order.order_type == OrderType.MARKET
        assert market_order.quantity == 2.0
        assert market_order.price is None
        assert market_order.status == OrderStatus.NEW
        assert market_order.filled_quantity == 0.0
        assert market_order.remaining_quantity == 2.0
        assert market_order.user_id == user_id
    
    def test_order_fill(self, symbol, order_id, user_id):
        """测试订单成交更新 (OT-002)"""
        # 创建订单
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=2.0,
            price=10000.0,
            user_id=user_id
        )
        
        # 部分成交
        result = order.fill(1.0, 10000.0)
        assert result is False  # 未完全成交
        assert order.filled_quantity == 1.0
        assert order.remaining_quantity == 1.0
        assert order.status == OrderStatus.PARTIALLY_FILLED
        
        # 完全成交
        result = order.fill(1.0, 10000.0)
        assert result is True  # 完全成交
        assert order.filled_quantity == 2.0
        assert order.remaining_quantity == 0.0
        assert order.status == OrderStatus.FILLED
        
        # 测试成交数量超过剩余数量
        order = Order(
            order_id=order_id + "_2",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=10000.0,
            user_id=user_id
        )
        
        order.fill(1.5, 10000.0)  # 超过剩余数量
        assert order.filled_quantity == 1.0
        assert order.remaining_quantity == 0.0
        assert order.status == OrderStatus.FILLED
    
    def test_order_cancel(self, symbol, order_id, user_id):
        """测试订单取消 (OT-003)"""
        # 创建订单
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=10000.0,
            user_id=user_id
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
            order_id=order_id + "_filled",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=10000.0,
            user_id=user_id
        )
        
        filled_order.fill(1.0, 10000.0)  # 完全成交
        assert filled_order.status == OrderStatus.FILLED
        
        result = filled_order.cancel()
        assert result is False
        assert filled_order.status == OrderStatus.FILLED  # 状态不变
    
    def test_trade_creation(self, symbol, user_id):
        """测试交易对象创建 (OT-004)"""
        # 创建交易
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            buy_order_id="buy_" + str(uuid.uuid4()),
            sell_order_id="sell_" + str(uuid.uuid4()),
            price=10000.0,
            quantity=1.5,
            buyer_user_id="buyer_" + user_id,
            seller_user_id="seller_" + user_id,
            fee=0.001,
            fee_asset="USDT"
        )
        
        # 验证交易属性
        assert trade.symbol == symbol
        assert trade.price == 10000.0
        assert trade.quantity == 1.5
        assert trade.buyer_user_id == "buyer_" + user_id
        assert trade.seller_user_id == "seller_" + user_id
        assert trade.fee == 0.001
        assert trade.fee_asset == "USDT"
        assert trade.timestamp <= time.time()
        assert len(trade.trade_id) > 0
        assert len(trade.buy_order_id) > 0
        assert len(trade.sell_order_id) > 0
    
    def test_boundary_conditions(self, symbol, order_id, user_id):
        """测试边界条件处理 (OT-005)"""
        # 测试数量为0的订单
        zero_qty_order = Order(
            order_id=order_id + "_zero",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.0,
            price=10000.0,
            user_id=user_id
        )
        
        assert zero_qty_order.remaining_quantity == 0.0
        
        # 测试负数量的填充
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=10000.0,
            user_id=user_id
        )
        
        result = order.fill(-0.5, 10000.0)
        assert result is False
        assert order.filled_quantity == 0.0  # 不应变化
        assert order.remaining_quantity == 1.0  # 不应变化
        
        # 测试零数量的填充
        result = order.fill(0.0, 10000.0)
        assert result is False
        assert order.filled_quantity == 0.0
        assert order.remaining_quantity == 1.0