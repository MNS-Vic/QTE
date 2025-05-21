#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试价格匹配功能 - 对手价与同向价逻辑
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

from qte.exchange.matching.matching_engine import MatchingEngine, Order, OrderSide, OrderType, OrderStatus, OrderBook, Trade


class TestPriceMatching:
    """测试价格匹配功能的各种模式"""
    
    @pytest.fixture
    def matching_engine(self):
        """创建撮合引擎"""
        return MatchingEngine()
    
    @pytest.fixture
    def symbol(self):
        """交易对"""
        return "BTCUSDT"
    
    @pytest.fixture
    def setup_order_book(self, matching_engine, symbol):
        """设置有深度的订单簿"""
        # 获取订单簿
        order_book = matching_engine.get_order_book(symbol)
        
        # 添加卖单，价格从10000到10100，每价格档位1个订单
        for i in range(10):
            price = 10000 + i * 10
            order = Order(
                order_id=f"sell_{i}",
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=1.0,
                price=price,
                user_id="seller"
            )
            order_book.add_order(order)
        
        # 添加买单，价格从9900到9990，每价格档位1个订单
        for i in range(10):
            price = 9990 - i * 10
            order = Order(
                order_id=f"buy_{i}",
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=1.0,
                price=price,
                user_id="buyer"
            )
            order_book.add_order(order)
            
        return order_book
    
    def test_opponent_price_match_buy(self, matching_engine, symbol, setup_order_book):
        """测试买单对手价匹配（卖一价）"""
        # 创建使用对手价的买单
        buy_order = Order(
            order_id="test_buy",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="OPPONENT"  # 使用对手价
        )
        
        # 调用价格匹配方法
        matched_price = matching_engine._apply_price_match(buy_order, setup_order_book)
        
        # 验证匹配后的价格是卖一价 10000
        assert matched_price == 10000
        
        # 使用匹配后的价格更新订单并下单
        buy_order.price = matched_price
        trades = matching_engine.place_order(buy_order)
        
        # 验证成交
        assert len(trades) == 1
        assert trades[0].price == 10000
        assert trades[0].quantity == 0.5
        assert trades[0].buy_order_id == "test_buy"
        assert trades[0].sell_order_id == "sell_0"
    
    def test_opponent_price_match_sell(self, matching_engine, symbol, setup_order_book):
        """测试卖单对手价匹配（买一价）"""
        # 创建使用对手价的卖单
        sell_order = Order(
            order_id="test_sell",
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="OPPONENT"  # 使用对手价
        )
        
        # 调用价格匹配方法
        matched_price = matching_engine._apply_price_match(sell_order, setup_order_book)
        
        # 验证匹配后的价格是买一价 9990
        assert matched_price == 9990
        
        # 使用匹配后的价格更新订单并下单
        sell_order.price = matched_price
        trades = matching_engine.place_order(sell_order)
        
        # 验证成交
        assert len(trades) == 1
        assert trades[0].price == 9990
        assert trades[0].quantity == 0.5
        assert trades[0].buy_order_id == "buy_0"
        assert trades[0].sell_order_id == "test_sell"
    
    def test_queue_price_match_buy(self, matching_engine, symbol, setup_order_book):
        """测试买单同向价匹配（买一价）"""
        # 创建使用同向价的买单
        buy_order = Order(
            order_id="test_buy_queue",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="QUEUE"  # 使用同向价
        )
        
        # 调用价格匹配方法
        matched_price = matching_engine._apply_price_match(buy_order, setup_order_book)
        
        # 验证匹配后的价格是买一价 9990
        assert matched_price == 9990
        
        # 使用匹配后的价格更新订单并下单
        buy_order.price = matched_price
        
        # 此时不应该成交，因为同向价不够高
        trades = matching_engine.place_order(buy_order)
        assert len(trades) == 0
        
        # 验证订单被添加到买单中
        order_book = matching_engine.get_order_book(symbol)
        assert buy_order.order_id in order_book.order_map
        assert buy_order.price == 9990
    
    def test_queue_price_match_sell(self, matching_engine, symbol, setup_order_book):
        """测试卖单同向价匹配（卖一价）"""
        # 创建使用同向价的卖单
        sell_order = Order(
            order_id="test_sell_queue",
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="QUEUE"  # 使用同向价
        )
        
        # 调用价格匹配方法
        matched_price = matching_engine._apply_price_match(sell_order, setup_order_book)
        
        # 验证匹配后的价格是卖一价 10000
        assert matched_price == 10000
        
        # 使用匹配后的价格更新订单并下单
        sell_order.price = matched_price
        
        # 此时不应该成交，因为同向价不够低
        trades = matching_engine.place_order(sell_order)
        assert len(trades) == 0
        
        # 验证订单被添加到卖单中
        order_book = matching_engine.get_order_book(symbol)
        assert sell_order.order_id in order_book.order_map
        assert sell_order.price == 10000
    
    def test_opponent_5_price_match(self, matching_engine, symbol, setup_order_book):
        """测试对手5档价格匹配"""
        # 创建使用对手5档价的买单
        buy_order = Order(
            order_id="test_buy_opponent5",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="OPPONENT_5"  # 使用对手5档价
        )
        
        # 调用价格匹配方法
        matched_price = matching_engine._apply_price_match(buy_order, setup_order_book)
        
        # 验证匹配后的价格是卖5档价 (10000 + 4*10 = 10040)
        assert matched_price == 10040
        
        # 使用匹配后的价格更新订单并下单
        buy_order.price = matched_price
        trades = matching_engine.place_order(buy_order)
        
        # 应该会匹配到卖一档，因为买单价格高于卖一价
        assert len(trades) == 1
        assert trades[0].price == 10000  # 成交价是卖一价，不是匹配价
        assert trades[0].quantity == 0.5
    
    def test_queue_10_price_match(self, matching_engine, symbol, setup_order_book):
        """测试同向10档价格匹配"""
        # 创建使用同向10档价的卖单
        sell_order = Order(
            order_id="test_sell_queue10",
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="QUEUE_10"  # 使用同向10档价
        )
        
        # 实际上我们的卖盘有10个档位，所以第10档的价格是10090
        matched_price = matching_engine._apply_price_match(sell_order, setup_order_book)
        assert matched_price == 10090
        
        # 测试超出档位的情况，比如请求第11档
        sell_order.price_match = "QUEUE_11"
        matched_price = matching_engine._apply_price_match(sell_order, setup_order_book)
        assert matched_price is None
    
    def test_empty_orderbook_price_match(self, matching_engine, symbol):
        """测试空订单簿时的价格匹配"""
        # 创建空的订单簿
        order_book = matching_engine.get_order_book(symbol)
        
        # 创建使用对手价的买单
        buy_order = Order(
            order_id="test_buy_empty",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="OPPONENT"  # 使用对手价
        )
        
        # 尝试匹配价格，应该返回None
        matched_price = matching_engine._apply_price_match(buy_order, order_book)
        assert matched_price is None
    
    def test_invalid_price_match_mode(self, matching_engine, symbol, setup_order_book):
        """测试无效的价格匹配模式"""
        # 创建使用无效匹配模式的买单
        buy_order = Order(
            order_id="test_buy_invalid",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="INVALID_MODE"  # 无效的匹配模式
        )
        
        # 尝试匹配价格，应该返回None
        matched_price = matching_engine._apply_price_match(buy_order, setup_order_book)
        assert matched_price is None
    
    def test_place_order_with_price_match(self, matching_engine, symbol, setup_order_book):
        """测试在place_order中应用价格匹配"""
        # 保存原始方法
        original_apply_price_match = matching_engine._apply_price_match
        original_validate_order = matching_engine.validate_order
        
        # Mock相关方法
        matching_engine._apply_price_match = MagicMock(return_value=10000)
        matching_engine.validate_order = MagicMock(return_value=True)
        
        # 创建买单
        buy_order = Order(
            order_id="test_buy_place",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=None,  # 不指定价格
            user_id="test_user",
            price_match="OPPONENT"  # 使用对手价
        )
        
        # 下单
        matching_engine.place_order(buy_order)
        
        # 验证调用了价格匹配方法
        matching_engine._apply_price_match.assert_called_once()
        
        # 恢复原始方法
        matching_engine._apply_price_match = original_apply_price_match
        matching_engine.validate_order = original_validate_order 