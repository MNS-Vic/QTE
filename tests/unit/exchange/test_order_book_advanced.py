#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OrderBook高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from qte.exchange.matching.order_book import OrderBook


class TestOrderBookAdvanced:
    """OrderBook高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.order_book = OrderBook("BTCUSDT")
    
    def test_init_order_book(self):
        """测试订单簿初始化"""
        # Red: 编写失败的测试
        assert self.order_book.symbol == "BTCUSDT"
        assert self.order_book.bids == []
        assert self.order_book.asks == []
        assert self.order_book.orders == {}
        assert self.order_book.is_empty() is True
    
    def test_add_buy_order(self):
        """测试添加买单"""
        # Red: 编写失败的测试
        order_id = "buy_order_1"
        price = Decimal("50000.00")
        quantity = Decimal("1.5")
        
        self.order_book.add_order(order_id, "BUY", price, quantity)
        
        # 验证订单被添加到orders字典
        assert order_id in self.order_book.orders
        order = self.order_book.orders[order_id]
        assert order['order_id'] == order_id
        assert order['side'] == "BUY"
        assert order['price'] == price
        assert order['quantity'] == quantity
        assert order['remaining_quantity'] == quantity
        
        # 验证买单被添加到bids列表
        assert len(self.order_book.bids) == 1
        assert self.order_book.bids[0] == (price, quantity)
        
        # 验证asks列表仍为空
        assert len(self.order_book.asks) == 0
        
        # 验证最佳买价
        assert self.order_book.get_best_bid() == price
        assert self.order_book.get_best_ask() is None
    
    def test_add_sell_order(self):
        """测试添加卖单"""
        # Red: 编写失败的测试
        order_id = "sell_order_1"
        price = Decimal("51000.00")
        quantity = Decimal("2.0")
        
        self.order_book.add_order(order_id, "SELL", price, quantity)
        
        # 验证订单被添加到orders字典
        assert order_id in self.order_book.orders
        order = self.order_book.orders[order_id]
        assert order['side'] == "SELL"
        
        # 验证卖单被添加到asks列表
        assert len(self.order_book.asks) == 1
        assert self.order_book.asks[0] == (price, quantity)
        
        # 验证bids列表仍为空
        assert len(self.order_book.bids) == 0
        
        # 验证最佳卖价
        assert self.order_book.get_best_ask() == price
        assert self.order_book.get_best_bid() is None
    
    def test_add_multiple_buy_orders_sorting(self):
        """测试添加多个买单的价格排序"""
        # Red: 编写失败的测试
        # 添加不同价格的买单
        orders = [
            ("buy_1", Decimal("50000.00"), Decimal("1.0")),
            ("buy_2", Decimal("50500.00"), Decimal("0.5")),  # 更高价格
            ("buy_3", Decimal("49500.00"), Decimal("2.0")),  # 更低价格
        ]
        
        for order_id, price, quantity in orders:
            self.order_book.add_order(order_id, "BUY", price, quantity)
        
        # 验证买单按价格降序排列（最高价在前）
        assert len(self.order_book.bids) == 3
        assert self.order_book.bids[0][0] == Decimal("50500.00")  # 最高价
        assert self.order_book.bids[1][0] == Decimal("50000.00")  # 中间价
        assert self.order_book.bids[2][0] == Decimal("49500.00")  # 最低价
        
        # 验证最佳买价是最高价
        assert self.order_book.get_best_bid() == Decimal("50500.00")
    
    def test_add_multiple_sell_orders_sorting(self):
        """测试添加多个卖单的价格排序"""
        # Red: 编写失败的测试
        # 添加不同价格的卖单
        orders = [
            ("sell_1", Decimal("51000.00"), Decimal("1.0")),
            ("sell_2", Decimal("50500.00"), Decimal("0.5")),  # 更低价格
            ("sell_3", Decimal("51500.00"), Decimal("2.0")),  # 更高价格
        ]
        
        for order_id, price, quantity in orders:
            self.order_book.add_order(order_id, "SELL", price, quantity)
        
        # 验证卖单按价格升序排列（最低价在前）
        assert len(self.order_book.asks) == 3
        assert self.order_book.asks[0][0] == Decimal("50500.00")  # 最低价
        assert self.order_book.asks[1][0] == Decimal("51000.00")  # 中间价
        assert self.order_book.asks[2][0] == Decimal("51500.00")  # 最高价
        
        # 验证最佳卖价是最低价
        assert self.order_book.get_best_ask() == Decimal("50500.00")
    
    def test_remove_existing_order(self):
        """测试移除存在的订单"""
        # Red: 编写失败的测试
        # 先添加一个买单
        order_id = "buy_order_1"
        price = Decimal("50000.00")
        quantity = Decimal("1.5")
        
        self.order_book.add_order(order_id, "BUY", price, quantity)
        assert order_id in self.order_book.orders
        assert len(self.order_book.bids) == 1
        
        # 移除订单
        result = self.order_book.remove_order(order_id)
        
        # 验证移除成功
        assert result is True
        assert order_id not in self.order_book.orders
        assert len(self.order_book.bids) == 0
        assert self.order_book.get_best_bid() is None
    
    def test_remove_nonexistent_order(self):
        """测试移除不存在的订单"""
        # Red: 编写失败的测试
        result = self.order_book.remove_order("nonexistent_order")
        
        # 验证移除失败
        assert result is False
    
    def test_remove_order_with_value_error(self):
        """测试移除订单时处理ValueError异常"""
        # Red: 编写失败的测试
        # 先添加订单
        order_id = "buy_order_1"
        price = Decimal("50000.00")
        quantity = Decimal("1.5")
        
        self.order_book.add_order(order_id, "BUY", price, quantity)
        
        # 手动修改bids列表，模拟数据不一致的情况
        self.order_book.bids.clear()
        
        # 移除订单应该仍然成功（捕获ValueError）
        result = self.order_book.remove_order(order_id)
        assert result is True
        assert order_id not in self.order_book.orders
    
    def test_get_depth_with_orders(self):
        """测试获取订单簿深度 - 有订单情况"""
        # Red: 编写失败的测试
        # 添加多个买卖单
        buy_orders = [
            ("buy_1", Decimal("50000.00"), Decimal("1.0")),
            ("buy_2", Decimal("49500.00"), Decimal("2.0")),
        ]
        sell_orders = [
            ("sell_1", Decimal("51000.00"), Decimal("1.5")),
            ("sell_2", Decimal("51500.00"), Decimal("0.8")),
        ]
        
        for order_id, price, quantity in buy_orders:
            self.order_book.add_order(order_id, "BUY", price, quantity)
        
        for order_id, price, quantity in sell_orders:
            self.order_book.add_order(order_id, "SELL", price, quantity)
        
        # 获取深度
        depth = self.order_book.get_depth(limit=5)
        
        # 验证深度结构
        assert 'bids' in depth
        assert 'asks' in depth
        assert len(depth['bids']) == 2
        assert len(depth['asks']) == 2
        
        # 验证买单深度（按价格降序）
        assert depth['bids'][0] == ["50000.00", "1.0"]  # 最高买价
        assert depth['bids'][1] == ["49500.00", "2.0"]
        
        # 验证卖单深度（按价格升序）
        assert depth['asks'][0] == ["51000.00", "1.5"]  # 最低卖价
        assert depth['asks'][1] == ["51500.00", "0.8"]
    
    def test_get_depth_with_limit(self):
        """测试获取订单簿深度 - 限制档位数量"""
        # Red: 编写失败的测试
        # 添加多个买单
        for i in range(5):
            order_id = f"buy_{i}"
            price = Decimal(f"{50000 - i * 100}.00")
            quantity = Decimal("1.0")
            self.order_book.add_order(order_id, "BUY", price, quantity)
        
        # 获取限制为2档的深度
        depth = self.order_book.get_depth(limit=2)
        
        # 验证只返回2档
        assert len(depth['bids']) == 2
        assert len(depth['asks']) == 0
        
        # 验证返回的是最佳的2档
        assert depth['bids'][0] == ["50000.00", "1.0"]
        assert depth['bids'][1] == ["49900.00", "1.0"]
    
    def test_get_depth_empty_order_book(self):
        """测试获取空订单簿的深度"""
        # Red: 编写失败的测试
        depth = self.order_book.get_depth()
        
        # 验证空深度
        assert depth['bids'] == []
        assert depth['asks'] == []
    
    def test_check_triggers_buy_orders(self):
        """测试检查买单触发"""
        # Red: 编写失败的测试
        # 添加买单
        self.order_book.add_order("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0"))
        self.order_book.add_order("buy_2", "BUY", Decimal("49000.00"), Decimal("2.0"))

        # 当前价格为49500，应该触发价格>=49500的买单
        triggered = self.order_book.check_triggers(49500.0)

        # 验证只有buy_1被触发（49500 <= 50000）
        assert len(triggered) == 1
        assert triggered[0]['order_id'] == "buy_1"
        assert triggered[0]['side'] == "BUY"
    
    def test_check_triggers_sell_orders(self):
        """测试检查卖单触发"""
        # Red: 编写失败的测试
        # 添加卖单
        self.order_book.add_order("sell_1", "SELL", Decimal("51000.00"), Decimal("1.0"))
        self.order_book.add_order("sell_2", "SELL", Decimal("52000.00"), Decimal("2.0"))
        
        # 当前价格为51500，应该触发价格<=51500的卖单
        triggered = self.order_book.check_triggers(51500.0)
        
        # 验证只有sell_1被触发（51000 <= 51500）
        assert len(triggered) == 1
        assert triggered[0]['order_id'] == "sell_1"
        assert triggered[0]['side'] == "SELL"
    
    def test_check_triggers_no_triggers(self):
        """测试检查触发 - 无触发情况"""
        # Red: 编写失败的测试
        # 添加订单
        self.order_book.add_order("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0"))
        self.order_book.add_order("sell_1", "SELL", Decimal("51000.00"), Decimal("1.0"))
        
        # 当前价格在买卖价之间，不应触发任何订单
        triggered = self.order_book.check_triggers(50500.0)
        
        # 验证无触发
        assert len(triggered) == 0
    
    def test_get_spread_with_orders(self):
        """测试获取价差 - 有买卖单情况"""
        # Red: 编写失败的测试
        # 添加买卖单
        self.order_book.add_order("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0"))
        self.order_book.add_order("sell_1", "SELL", Decimal("51000.00"), Decimal("1.0"))
        
        # 获取价差
        spread = self.order_book.get_spread()
        
        # 验证价差计算
        expected_spread = Decimal("51000.00") - Decimal("50000.00")
        assert spread == expected_spread
        assert spread == Decimal("1000.00")
    
    def test_get_spread_no_bids(self):
        """测试获取价差 - 无买单情况"""
        # Red: 编写失败的测试
        # 只添加卖单
        self.order_book.add_order("sell_1", "SELL", Decimal("51000.00"), Decimal("1.0"))
        
        # 获取价差
        spread = self.order_book.get_spread()
        
        # 验证无价差
        assert spread is None
    
    def test_get_spread_no_asks(self):
        """测试获取价差 - 无卖单情况"""
        # Red: 编写失败的测试
        # 只添加买单
        self.order_book.add_order("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0"))
        
        # 获取价差
        spread = self.order_book.get_spread()
        
        # 验证无价差
        assert spread is None
    
    def test_get_spread_empty_order_book(self):
        """测试获取价差 - 空订单簿情况"""
        # Red: 编写失败的测试
        spread = self.order_book.get_spread()
        
        # 验证无价差
        assert spread is None
    
    def test_is_empty_true(self):
        """测试订单簿为空的判断"""
        # Red: 编写失败的测试
        assert self.order_book.is_empty() is True
    
    def test_is_empty_false_with_bids(self):
        """测试订单簿非空的判断 - 有买单"""
        # Red: 编写失败的测试
        self.order_book.add_order("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0"))
        assert self.order_book.is_empty() is False
    
    def test_is_empty_false_with_asks(self):
        """测试订单簿非空的判断 - 有卖单"""
        # Red: 编写失败的测试
        self.order_book.add_order("sell_1", "SELL", Decimal("51000.00"), Decimal("1.0"))
        assert self.order_book.is_empty() is False

    def test_get_statistics_empty_order_book(self):
        """测试获取空订单簿统计信息"""
        # Red: 编写失败的测试
        stats = self.order_book.get_statistics()

        # 验证统计信息
        assert stats['symbol'] == "BTCUSDT"
        assert stats['total_orders'] == 0
        assert stats['bid_levels'] == 0
        assert stats['ask_levels'] == 0
        assert stats['best_bid'] is None
        assert stats['best_ask'] is None
        assert stats['spread'] is None

    def test_get_statistics_with_orders(self):
        """测试获取有订单的订单簿统计信息"""
        # Red: 编写失败的测试
        # 添加多个订单
        self.order_book.add_order("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0"))
        self.order_book.add_order("buy_2", "BUY", Decimal("49500.00"), Decimal("2.0"))
        self.order_book.add_order("sell_1", "SELL", Decimal("51000.00"), Decimal("1.5"))

        stats = self.order_book.get_statistics()

        # 验证统计信息
        assert stats['symbol'] == "BTCUSDT"
        assert stats['total_orders'] == 3
        assert stats['bid_levels'] == 2
        assert stats['ask_levels'] == 1
        assert stats['best_bid'] == "50000.00"
        assert stats['best_ask'] == "51000.00"
        assert stats['spread'] == "1000.00"

    def test_get_best_bid_empty(self):
        """测试获取最佳买价 - 空订单簿"""
        # Red: 编写失败的测试
        assert self.order_book.get_best_bid() is None

    def test_get_best_ask_empty(self):
        """测试获取最佳卖价 - 空订单簿"""
        # Red: 编写失败的测试
        assert self.order_book.get_best_ask() is None

    def test_complex_order_management_scenario(self):
        """测试复杂的订单管理场景"""
        # Red: 编写失败的测试
        # 场景：添加多个订单，然后移除部分订单，验证状态

        # 第一步：添加多个买卖单
        orders_to_add = [
            ("buy_1", "BUY", Decimal("50000.00"), Decimal("1.0")),
            ("buy_2", "BUY", Decimal("49500.00"), Decimal("2.0")),
            ("buy_3", "BUY", Decimal("49000.00"), Decimal("1.5")),
            ("sell_1", "SELL", Decimal("51000.00"), Decimal("1.0")),
            ("sell_2", "SELL", Decimal("51500.00"), Decimal("2.0")),
            ("sell_3", "SELL", Decimal("52000.00"), Decimal("0.5")),
        ]

        for order_id, side, price, quantity in orders_to_add:
            self.order_book.add_order(order_id, side, price, quantity)

        # 验证初始状态
        assert len(self.order_book.orders) == 6
        assert len(self.order_book.bids) == 3
        assert len(self.order_book.asks) == 3
        assert self.order_book.get_best_bid() == Decimal("50000.00")
        assert self.order_book.get_best_ask() == Decimal("51000.00")
        assert self.order_book.get_spread() == Decimal("1000.00")

        # 第二步：移除最佳买单
        result = self.order_book.remove_order("buy_1")
        assert result is True
        assert len(self.order_book.orders) == 5
        assert len(self.order_book.bids) == 2
        assert self.order_book.get_best_bid() == Decimal("49500.00")  # 新的最佳买价

        # 第三步：移除最佳卖单
        result = self.order_book.remove_order("sell_1")
        assert result is True
        assert len(self.order_book.orders) == 4
        assert len(self.order_book.asks) == 2
        assert self.order_book.get_best_ask() == Decimal("51500.00")  # 新的最佳卖价

        # 第四步：验证新的价差
        new_spread = self.order_book.get_spread()
        expected_spread = Decimal("51500.00") - Decimal("49500.00")
        assert new_spread == expected_spread
        assert new_spread == Decimal("2000.00")

        # 第五步：检查触发条件
        # 价格为49000时，应该触发buy_2和buy_3（49000 <= 49500 和 49000 <= 49000）
        triggered = self.order_book.check_triggers(49000.0)
        assert len(triggered) == 2
        triggered_ids = [order['order_id'] for order in triggered]
        assert "buy_2" in triggered_ids
        assert "buy_3" in triggered_ids

        # 第六步：获取深度信息
        depth = self.order_book.get_depth(limit=3)
        assert len(depth['bids']) == 2
        assert len(depth['asks']) == 2
        assert depth['bids'][0] == ["49500.00", "2.0"]  # 最佳买价
        assert depth['asks'][0] == ["51500.00", "2.0"]  # 最佳卖价

        # 第七步：获取最终统计信息
        final_stats = self.order_book.get_statistics()
        assert final_stats['total_orders'] == 4
        assert final_stats['bid_levels'] == 2
        assert final_stats['ask_levels'] == 2
        assert final_stats['best_bid'] == "49500.00"
        assert final_stats['best_ask'] == "51500.00"
        assert final_stats['spread'] == "2000.00"

    def test_edge_case_same_price_multiple_orders(self):
        """测试边界情况 - 相同价格的多个订单"""
        # Red: 编写失败的测试
        # 添加相同价格的多个买单
        price = Decimal("50000.00")
        self.order_book.add_order("buy_1", "BUY", price, Decimal("1.0"))
        self.order_book.add_order("buy_2", "BUY", price, Decimal("2.0"))
        self.order_book.add_order("buy_3", "BUY", price, Decimal("0.5"))

        # 验证所有订单都被添加
        assert len(self.order_book.orders) == 3
        assert len(self.order_book.bids) == 3

        # 验证所有订单都有相同的最佳买价
        assert self.order_book.get_best_bid() == price

        # 验证深度显示所有相同价格的订单
        depth = self.order_book.get_depth()
        assert len(depth['bids']) == 3
        for bid in depth['bids']:
            assert bid[0] == "50000.00"

        # 移除一个订单
        result = self.order_book.remove_order("buy_2")
        assert result is True
        assert len(self.order_book.orders) == 2
        assert len(self.order_book.bids) == 2

        # 最佳买价应该仍然是相同价格
        assert self.order_book.get_best_bid() == price

    def test_edge_case_decimal_precision(self):
        """测试边界情况 - Decimal精度处理"""
        # Red: 编写失败的测试
        # 使用高精度的Decimal价格
        high_precision_price = Decimal("50000.123456789")
        quantity = Decimal("1.987654321")

        self.order_book.add_order("precise_order", "BUY", high_precision_price, quantity)

        # 验证精度被保持
        order = self.order_book.orders["precise_order"]
        assert order['price'] == high_precision_price
        assert order['quantity'] == quantity

        # 验证最佳买价保持精度
        assert self.order_book.get_best_bid() == high_precision_price

        # 验证深度信息中的字符串转换
        depth = self.order_book.get_depth()
        assert depth['bids'][0][0] == str(high_precision_price)
        assert depth['bids'][0][1] == str(quantity)

        # 验证统计信息中的字符串转换
        stats = self.order_book.get_statistics()
        assert stats['best_bid'] == str(high_precision_price)
