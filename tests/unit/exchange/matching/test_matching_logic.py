#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
撮合引擎逻辑单元测试
"""
import pytest
import time
import uuid
from qte.exchange.matching.matching_engine import (
    MatchingEngine, OrderBook, Order, OrderSide, 
    OrderType, OrderStatus, Trade
)

class TestMatchingLogic:
    """撮合引擎测试类"""
    
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
    
    @pytest.fixture
    def limit_buy_order(self, symbol):
        """创建限价买单"""
        return Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=10000.0,
            user_id="user1"
        )
    
    @pytest.fixture
    def limit_sell_order(self, symbol):
        """创建限价卖单"""
        return Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=10000.0,
            user_id="user2"
        )
    
    @pytest.fixture
    def market_buy_order(self, symbol):
        """创建市价买单"""
        return Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0,
            user_id="user1"
        )
    
    @pytest.fixture
    def market_sell_order(self, symbol):
        """创建市价卖单"""
        return Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=1.0,
            user_id="user2"
        )
    
    def test_matching_engine_init(self, matching_engine):
        """测试撮合引擎初始化 (ML-001)"""
        assert matching_engine.order_books == {}
        assert matching_engine.trades == []
        assert matching_engine.trade_listeners == []
    
    def test_limit_buy_order_matching(self, matching_engine, symbol, limit_sell_order, limit_buy_order):
        """测试限价买单撮合 (ML-002)"""
        # 先放入卖单
        matching_engine.place_order(limit_sell_order)
        
        # 再放入买单进行撮合
        trades = matching_engine.place_order(limit_buy_order)
        
        # 应该产生一笔成交
        assert len(trades) == 1
        trade = trades[0]
        
        # 验证成交信息
        assert trade.symbol == symbol
        assert trade.buy_order_id == limit_buy_order.order_id
        assert trade.sell_order_id == limit_sell_order.order_id
        assert trade.price == limit_sell_order.price
        assert trade.quantity == limit_buy_order.quantity
        assert trade.buyer_user_id == limit_buy_order.user_id
        assert trade.seller_user_id == limit_sell_order.user_id
        
        # 验证订单状态
        assert limit_buy_order.status == OrderStatus.FILLED
        assert limit_sell_order.status == OrderStatus.FILLED