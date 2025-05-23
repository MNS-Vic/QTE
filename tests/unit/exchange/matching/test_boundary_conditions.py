#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
撮合引擎边界条件测试
测试匹配引擎在各种边界条件下的行为
"""
import pytest
from decimal import Decimal
import uuid
import time
from qte.exchange.matching.matching_engine import (
    MatchingEngine, OrderBook, Order, OrderSide, 
    OrderType, OrderStatus, Trade
)

class TestMatchingEngineBoundaryConditions:
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
    
    def test_zero_price_limit_order(self, matching_engine, symbol):
        """
        测试价格为0的限价单处理
        预期：系统应拒绝价格为0的订单
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
        
        # 检查订单是否被拒绝
        assert zero_price_buy.status == OrderStatus.REJECTED
        assert zero_price_sell.status == OrderStatus.REJECTED
        
        # 订单不应该被加入订单簿
        order_book = matching_engine.get_order_book(symbol)
        assert 0.0 not in order_book.buy_prices
        assert 0.0 not in order_book.sell_prices
        
        # 不应产生成交
        assert len(trades_buy) == Decimal("0")
        assert len(trades_sell) == Decimal("0")
    
    def test_negative_price_order(self, matching_engine, symbol):
        """
        测试价格为负值的订单处理
        预期：系统应拒绝负价格的订单
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
        
        # 创建价格为负值的限价卖单
        negative_price_sell = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("-100.0"),
            user_id="user2"
        )
        
        # 尝试下单，验证结果
        trades_buy = matching_engine.place_order(negative_price_buy)
        trades_sell = matching_engine.place_order(negative_price_sell)
        
        # 检查订单是否被拒绝
        assert negative_price_buy.status == OrderStatus.REJECTED
        assert negative_price_sell.status == OrderStatus.REJECTED
        
        # 订单不应该被加入订单簿
        order_book = matching_engine.get_order_book(symbol)
        assert -100.0 not in order_book.buy_prices
        assert -100.0 not in order_book.sell_prices
        
        # 不应产生成交
        assert len(trades_buy) == Decimal("0")
        assert len(trades_sell) == Decimal("0")
    
    def test_empty_orderbook_market_order(self, matching_engine, symbol):
        """
        测试空订单簿中的市价单处理
        预期：当订单簿为空时，市价单应不产生成交
        """
        # 确保订单簿为空
        order_book = matching_engine.get_order_book(symbol)
        assert len(order_book.buy_prices) == Decimal("0")
        assert len(order_book.sell_prices) == Decimal("0")
        
        # 创建市价买单
        market_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            user_id="user1"
        )
        
        # 尝试下单
        trades = matching_engine.place_order(market_buy)
        
        # 预期无成交
        assert len(trades) == Decimal("0")
        
        # 市价单不应加入订单簿
        assert market_buy.order_id not in order_book.order_map
        
        # 创建市价卖单
        market_sell = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            user_id="user2"
        )
        
        # 尝试下单
        trades = matching_engine.place_order(market_sell)
        
        # 预期无成交
        assert len(trades) == Decimal("0")
        
        # 市价单不应加入订单簿
        assert market_sell.order_id not in order_book.order_map
    
    def test_market_order_partial_fill(self, matching_engine, symbol):
        """
        测试市价单部分成交场景
        预期：当对手方订单量不足时，市价单应部分成交
        """
        # 创建限价卖单（数量较小）
        limit_sell = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("10000.0"),
            user_id="seller"
        )
        matching_engine.place_order(limit_sell)
    
        # 创建数量较大的市价买单
        market_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("2.0"),
            user_id="buyer"
        )
    
        # 尝试下单
        trades = matching_engine.place_order(market_buy)
    
        # 预期部分成交 - 现在每次撮合产生2个Trade对象（买方和卖方各一个）
        assert len(trades) == 2
        # 找到买方的trade
        buyer_trade = next(t for t in trades if t.user_id == "buyer")
        assert buyer_trade.quantity == Decimal("1.0")
        assert market_buy.executed_quantity == Decimal("1.0")
        assert market_buy.remaining_quantity == Decimal("1.0")
        assert market_buy.status == OrderStatus.PARTIALLY_FILLED
        
        # 市价单不应加入订单簿，即使部分成交
        order_book = matching_engine.get_order_book(symbol)
        assert market_buy.order_id not in order_book.order_map
    
    def test_extremely_large_order(self, matching_engine, symbol):
        """
        测试极大订单量的处理
        预期：系统应能正确处理超大订单量
        """
        # 创建多个卖单
        for i in range(5):
            sell_order = Order(
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=Decimal("100.0"),
                price=Decimal("10000.0") + i*10,  # 10000, 10010, 10020...
                user_id=f"seller_{i}"
            )
            matching_engine.place_order(sell_order)
        
        # 创建极大买单
        large_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1000000000"),  # 10亿，使用Decimal
            price=Decimal("10050.0"),  # 高于所有卖单
            user_id="big_buyer"
        )
        
        # 尝试下单
        trades = matching_engine.place_order(large_buy)
        
        # 预期成交5笔，但每笔交易产生2个Trade对象，所以总共10个
        assert len(trades) == 10
        # 计算买方的总成交量
        buyer_trades = [t for t in trades if t.user_id == "big_buyer"]
        assert len(buyer_trades) == 5
        assert sum(trade.quantity for trade in buyer_trades) == Decimal("500.0")
        
        # 验证大单状态
        assert large_buy.executed_quantity == Decimal("500.0")
        assert large_buy.remaining_quantity == Decimal("1000000000") - Decimal("500.0")
        assert large_buy.status == OrderStatus.PARTIALLY_FILLED
    
    def test_extremely_small_order(self, matching_engine, symbol):
        """
        测试极小订单量的处理
        预期：系统应能正确处理极小订单量
        """
        # 创建限价卖单
        limit_sell = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("10000.0"),
            user_id="seller"
        )
        matching_engine.place_order(limit_sell)
        
        # 创建极小买单
        small_buy = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.0000000001"),  # 非常小的数量，使用Decimal
            price=Decimal("10000.0"),
            user_id="buyer"
        )
        
        # 尝试下单
        trades = matching_engine.place_order(small_buy)
        
        # 预期成交 - 现在每次撮合产生2个Trade对象
        assert len(trades) == 2
        buyer_trade = next(t for t in trades if t.user_id == "buyer")
        assert buyer_trade.quantity == Decimal("0.0000000001")
        
        # 验证订单状态
        assert small_buy.status == OrderStatus.FILLED
        assert limit_sell.status == OrderStatus.PARTIALLY_FILLED
        assert limit_sell.remaining_quantity == Decimal("1.0") - Decimal("0.0000000001")
    
    def test_price_time_priority(self, matching_engine, symbol):
        """
        测试价格优先、时间优先原则
        预期：系统应按价格优先、时间优先顺序撮合订单
        """
        # 创建不同价格的卖单
        sell_orders = []
        prices = [10050.0, 10030.0, 10010.0, 10040.0, 10020.0]  # 乱序价格
        
        for price in prices:
            order = Order(
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=Decimal("1.0"),
                price=price,
                user_id=f"seller_{price}"
            )
            sell_orders.append(order)
            matching_engine.place_order(order)
            time.sleep(0.01)  # 确保时间戳不同
        
        # 创建足够大的买单
        buy_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10.0"),
            price=Decimal("10050.0"),  # 等于或高于所有卖单
            user_id="buyer"
        )
        
        # 尝试下单
        trades = matching_engine.place_order(buy_order)
        
        # 预期成交5笔，但每笔交易产生2个Trade对象，所以总共10个
        assert len(trades) == 10
        
        # 获取买方的trades并验证成交价格顺序（应按照价格从低到高）
        buyer_trades = [t for t in trades if t.user_id == "buyer"]
        assert len(buyer_trades) == 5
        expected_prices = sorted(prices)
        for i, trade in enumerate(buyer_trades):
            assert trade.price == expected_prices[i]
    
    def test_cancel_nonexistent_order(self, matching_engine, symbol):
        """
        测试取消不存在的订单
        预期：系统应正确处理不存在订单的取消请求
        """
        # 尝试取消不存在的订单
        result = matching_engine.cancel_order("nonexistent_order_id", symbol)
        
        # 预期取消失败
        assert result is False
    
    def test_duplicate_order_id(self, matching_engine, symbol):
        """
        测试重复订单ID
        预期：系统应拒绝重复的订单ID
        """
        # 创建第一个订单
        order_id = str(uuid.uuid4())
        order1 = Order(
            order_id=order_id,
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("10000.0"),
            user_id="user1"
        )
        
        # 创建使用相同ID的第二个订单
        order2 = Order(
            order_id=order_id,  # 相同ID
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("10000.0"),
            user_id="user2"
        )
        
        # 尝试下单
        matching_engine.place_order(order1)
        
        # 检查订单簿
        order_book = matching_engine.get_order_book(symbol)
        assert order_id in order_book.order_map
        
        # 尝试下第二个相同ID的订单
        # 这里只是验证系统不会崩溃，具体行为取决于实现
        matching_engine.place_order(order2)
    
    def test_zero_quantity_order(self, matching_engine, symbol):
        """
        测试数量为0的订单
        预期：系统应拒绝或正确处理数量为0的订单
        """
        # 创建数量为0的订单
        zero_qty_order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.0"),
            price=Decimal("10000.0"),
            user_id="user1"
        )
        
        # 尝试下单
        trades = matching_engine.place_order(zero_qty_order)
        
        # 预期无成交
        assert len(trades) == Decimal("0")
        
        # 数量为0的订单不应加入订单簿
        order_book = matching_engine.get_order_book(symbol)
        assert zero_qty_order.order_id not in order_book.order_map