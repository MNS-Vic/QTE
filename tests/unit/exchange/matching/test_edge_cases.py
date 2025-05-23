#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
撮合引擎边界条件测试
测试极端情况下的撮合引擎行为
"""
import pytest
from decimal import Decimal
import uuid
import time
from qte.exchange.matching.matching_engine import (
    MatchingEngine, OrderBook, Order, OrderSide, 
    OrderType, OrderStatus, Trade
)

class TestMatchingEngineEdgeCases:
    """撮合引擎边界条件测试类"""
    
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
    
    def test_zero_price_order(self, matching_engine, symbol):
        """
        测试价格为0的订单处理
        预期：价格为0的限价单应该被拒绝或不生成成交
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
        
        # 创建价格为0的限价卖单
        zero_price_sell = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("0.0"),
            user_id="user2"
        )
        
        # 尝试下单，验证结果
        trades_buy = matching_engine.place_order(zero_price_buy)
        trades_sell = matching_engine.place_order(zero_price_sell)
        
        # 检查是否产生成交（应该不会成交）
        assert len(trades_buy) == Decimal("0")
        assert len(trades_sell) == Decimal("0")
        
        # 检查订单是否被拒绝
        assert zero_price_buy.status == OrderStatus.REJECTED
        assert zero_price_sell.status == OrderStatus.REJECTED
        
        # 检查订单不应该在订单簿中
        order_book = matching_engine.get_order_book(symbol)
        assert 0.0 not in order_book.buy_prices
        assert 0.0 not in order_book.sell_prices
    
    def test_market_order_empty_book(self, matching_engine, symbol):
        """
        测试市价单在空订单簿情况下的处理
        预期：市价单应该被拒绝或保持未成交状态
        """
        # 创建市价买单
        market_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            user_id="user1"
        )
        
        # 创建市价卖单
        market_sell = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            user_id="user2"
        )
        
        # 确保订单簿为空
        order_book = matching_engine.get_order_book(symbol)
        assert len(order_book.buy_prices) == Decimal("0")
        assert len(order_book.sell_prices) == Decimal("0")
        
        # 尝试下市价单
        trades_buy = matching_engine.place_order(market_buy)
        trades_sell = matching_engine.place_order(market_sell)
        
        # 检查是否产生成交（应该不会成交）
        assert len(trades_buy) == Decimal("0")
        assert len(trades_sell) == Decimal("0")
        
        # 市价单不应该被加入订单簿
        assert market_buy.order_id not in order_book.order_map
        assert market_sell.order_id not in order_book.order_map
    
    def test_extremely_large_order(self, matching_engine, symbol):
        """
        测试极大订单量的处理
        预期：系统应能正确处理大订单量而不崩溃
        """
        # 创建普通卖单作为对手方
        sell_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1000.0"),
            price=Decimal("10000.0"),
            user_id="user2"
        )
        matching_engine.place_order(sell_order)
        
        # 创建极大买单量
        large_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1000000000.0"),  # 10亿数量
            price=Decimal("10000.0"),
            user_id="user1"
        )
        
        # 下单并验证系统不崩溃
        trades = matching_engine.place_order(large_buy)
        
        # 应该只成交对手方的可用数量
        assert len(trades) == 2
        assert trades[0].quantity == Decimal("1000.0")
        assert large_buy.executed_quantity == Decimal("1000.0")
        assert large_buy.remaining_quantity == Decimal("1000000000.0") - Decimal("1000.0")
        assert large_buy.status == OrderStatus.PARTIALLY_FILLED
    
    def test_multiple_price_levels(self, matching_engine, symbol):
        """
        测试多价位撮合
        预期：大单应按价格优先顺序逐层撮合
        """
        # 创建多个不同价格的卖单
        sell_orders = []
        prices = [10000.0, 10010.0, 10020.0, 10030.0, 10040.0]
        
        for price in prices:
            sell_order = Order(
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=Decimal("1.0"),
                price=price,
                user_id=f"seller_{price}"
            )
            sell_orders.append(sell_order)
            matching_engine.place_order(sell_order)
        
        # 创建足够大的买单覆盖所有卖单
        buy_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10.0"),
            price=Decimal("10050.0"),  # 高于所有卖单价格
            user_id="big_buyer"
        )
        
        # 下单并验证撮合结果
        trades = matching_engine.place_order(buy_order)
        
        # 应该产生5笔成交，按价格从低到高撮合
        assert len(trades) == 10
        
        # 验证成交价格按从低到高顺序
        # 过滤出买方的Trade进行验证
        buyer_trades = [t for t in trades if t.user_id == "big_buyer"]
        for i, trade in enumerate(buyer_trades):
            assert trade.price == prices[i]
            assert trade.quantity == Decimal("1.0")
        
        # 验证买单状态
        assert buy_order.executed_quantity == Decimal("5.0")
        assert buy_order.remaining_quantity == Decimal("5.0")
        assert buy_order.status == OrderStatus.PARTIALLY_FILLED
    
    def test_cancel_partially_filled_order(self, matching_engine, symbol):
        """
        测试取消部分成交订单
        预期：部分成交订单可以被取消，取消后剩余数量不再参与撮合
        """
        # 创建卖单
        sell_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("2.0"),
            price=Decimal("10000.0"),
            user_id="seller"
        )
        matching_engine.place_order(sell_order)
        
        # 创建一个只能部分成交的买单
        buy_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("10000.0"),
            user_id="buyer"
        )
        
        # 下单并验证部分成交
        trades = matching_engine.place_order(buy_order)
        assert len(trades) == 2
        assert trades[0].quantity == Decimal("1.0")
        assert sell_order.executed_quantity == Decimal("1.0")
        assert sell_order.remaining_quantity == Decimal("1.0")
        assert sell_order.status == OrderStatus.PARTIALLY_FILLED
        
        # 取消部分成交的卖单
        result = matching_engine.cancel_order(sell_order.order_id, symbol)
        assert result is True
        assert sell_order.status == OrderStatus.CANCELED
        
        # 再次尝试成交
        buy_order2 = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("10000.0"),
            user_id="buyer2"
        )
        
        trades2 = matching_engine.place_order(buy_order2)
        assert len(trades2) == Decimal("0")  # 不应该有成交
    
    def test_same_price_time_priority(self, matching_engine, symbol):
        """
        测试同价格时间优先
        预期：同价格订单应按时间先后顺序成交
        """
        # 创建多个相同价格的卖单
        sell_orders = []
        
        for i in range(5):
            sell_order = Order(
                order_id=f"sell_{i}",
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=Decimal("1.0"),
                price=Decimal("10000.0"),
                user_id=f"seller_{i}"
            )
            sell_orders.append(sell_order)
            matching_engine.place_order(sell_order)
            time.sleep(0.01)  # 确保时间戳不同
        
        # 创建足够大的买单覆盖所有卖单
        buy_order = Order(
            order_id="buy_all",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("5.0"),
            price=Decimal("10000.0"),
            user_id="buyer"
        )
        
        # 下单并验证撮合结果
        trades = matching_engine.place_order(buy_order)
        
        # 应该产生5笔成交，按时间从早到晚撮合
        assert len(trades) == 10
        
        # 验证成交顺序与挂单顺序一致
        # 过滤出买方的Trade进行验证
        buyer_trades = [t for t in trades if t.user_id == "big_buyer"]
        for i, trade in enumerate(buyer_trades):
            assert trade.order_id == f"sell_{i}" or trade.order_id == "buy_all"
            assert trade.seller_user_id == f"seller_{i}"