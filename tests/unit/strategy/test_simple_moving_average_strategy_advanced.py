#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SimpleMovingAverageStrategy高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
from collections import deque
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from qte.core.event_loop import EventLoop
from qte.core.events import MarketEvent, SignalEvent
from qte.strategy.simple_moving_average_strategy import SimpleMovingAverageStrategy


class TestSimpleMovingAverageStrategyAdvanced:
    """SimpleMovingAverageStrategy高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.event_loop = EventLoop()
        self.mock_data_provider = Mock()
        self.symbols = ["AAPL", "GOOGL"]
        self.short_window = 5
        self.long_window = 20
        
        # 创建策略实例
        self.strategy = SimpleMovingAverageStrategy(
            event_loop=self.event_loop,
            data_provider=self.mock_data_provider,
            symbols=self.symbols,
            short_window=self.short_window,
            long_window=self.long_window,
            name="TestSMAStrategy"
        )
    
    def test_init_strategy(self):
        """测试策略初始化"""
        # Red: 编写失败的测试
        assert self.strategy.name == "TestSMAStrategy"
        assert self.strategy.symbols == self.symbols
        assert self.strategy.short_window == self.short_window
        assert self.strategy.long_window == self.long_window
        assert self.strategy.event_loop == self.event_loop
        assert self.strategy.data_provider == self.mock_data_provider
        
        # 验证每个symbol的数据结构初始化
        for symbol in self.symbols:
            assert symbol in self.strategy.prices
            assert isinstance(self.strategy.prices[symbol], deque)
            assert self.strategy.prices[symbol].maxlen == self.long_window
            assert self.strategy.short_sma[symbol] is None
            assert self.strategy.long_sma[symbol] is None
            assert self.strategy.was_short_above_long[symbol] is None
    
    def test_on_init_with_none_data_provider(self):
        """测试on_init方法 - 数据提供者为None的情况"""
        # Red: 编写失败的测试
        # 创建没有数据提供者的策略
        strategy_no_provider = SimpleMovingAverageStrategy(
            event_loop=self.event_loop,
            data_provider=None,
            symbols=["AAPL"],
            short_window=5,
            long_window=20
        )
        
        # 调用on_init设置数据提供者
        new_data_provider = Mock()
        strategy_no_provider.on_init(new_data_provider)
        
        # 验证数据提供者被设置
        assert strategy_no_provider.data_provider == new_data_provider
    
    def test_on_init_with_none_event_loop(self):
        """测试on_init方法 - 事件循环为None的情况"""
        # Red: 编写失败的测试
        # 创建没有事件循环的策略
        strategy_no_loop = SimpleMovingAverageStrategy(
            event_loop=None,
            data_provider=self.mock_data_provider,
            symbols=["AAPL"],
            short_window=5,
            long_window=20
        )
        
        # 调用on_init设置事件循环
        new_event_loop = EventLoop()
        strategy_no_loop.on_init(self.mock_data_provider, new_event_loop)
        
        # 验证事件循环被设置
        assert strategy_no_loop.event_loop == new_event_loop
    
    def test_on_init_with_existing_providers(self):
        """测试on_init方法 - 已有数据提供者和事件循环的情况"""
        # Red: 编写失败的测试
        original_provider = self.strategy.data_provider
        original_loop = self.strategy.event_loop
        
        # 调用on_init，不应该覆盖现有的提供者
        new_provider = Mock()
        new_loop = EventLoop()
        self.strategy.on_init(new_provider, new_loop)
        
        # 验证原有的提供者和循环没有被覆盖
        assert self.strategy.data_provider == original_provider
        assert self.strategy.event_loop == original_loop
    
    def test_on_bar_delegates_to_on_market_event(self):
        """测试on_bar方法委托给on_market_event"""
        # Red: 编写失败的测试
        # 创建市场事件
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=150.0,
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )
        
        # Mock on_market_event方法
        self.strategy.on_market_event = Mock()
        
        # 调用on_bar
        self.strategy.on_bar(market_event)
        
        # 验证on_market_event被调用
        self.strategy.on_market_event.assert_called_once_with(market_event)
    
    def test_on_market_event_ignore_unknown_symbol(self):
        """测试on_market_event忽略未知标的"""
        # Red: 编写失败的测试
        # 创建未知标的的市场事件
        market_event = MarketEvent(
            symbol="UNKNOWN",
            timestamp=datetime.now(timezone.utc),
            close_price=150.0,
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )
        
        # 记录初始状态
        initial_queue_size = len(self.event_loop)
        
        # 处理事件
        self.strategy.on_market_event(market_event)
        
        # 验证没有处理（队列大小不变）
        assert len(self.event_loop) == initial_queue_size
        assert "UNKNOWN" not in self.strategy.prices
    
    def test_on_market_event_use_price_field(self):
        """测试on_market_event使用price字段"""
        # Red: 编写失败的测试
        # 创建有price字段的市场事件
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=150.0,
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )
        # 手动添加price字段
        market_event.price = 155.0
        
        # 处理事件
        self.strategy.on_market_event(market_event)
        
        # 验证使用了price字段而不是close_price
        assert self.strategy.prices["AAPL"][-1] == 155.0
    
    def test_on_market_event_use_close_price_when_no_price(self):
        """测试on_market_event在没有price字段时使用close_price"""
        # Red: 编写失败的测试
        # 创建没有price字段的市场事件
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=150.0,
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )
        
        # 处理事件
        self.strategy.on_market_event(market_event)
        
        # 验证使用了close_price
        assert self.strategy.prices["AAPL"][-1] == 150.0
    
    def test_on_market_event_use_close_price_when_invalid_price(self):
        """测试on_market_event在price无效时使用close_price"""
        # Red: 编写失败的测试
        # 创建有无效price字段的市场事件
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=150.0,
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )
        # 设置无效price
        market_event.price = 0.0
        
        # 处理事件
        self.strategy.on_market_event(market_event)
        
        # 验证使用了close_price而不是无效的price
        assert self.strategy.prices["AAPL"][-1] == 150.0
    
    def test_on_market_event_insufficient_data(self):
        """测试on_market_event数据不足时不计算信号"""
        # Red: 编写失败的测试
        # 添加少于long_window的数据
        for i in range(self.long_window - 1):
            market_event = MarketEvent(
                symbol="AAPL",
                timestamp=datetime.now(timezone.utc),
                close_price=150.0 + i,
                open_price=149.0,
                high_price=151.0,
                low_price=148.0,
                volume=1000000
            )
            self.strategy.on_market_event(market_event)
        
        # 验证移动平均线未计算
        assert self.strategy.short_sma["AAPL"] is None
        assert self.strategy.long_sma["AAPL"] is None
        assert self.strategy.was_short_above_long["AAPL"] is None
        
        # 验证没有生成信号
        assert len(self.event_loop) == 0
    
    def test_on_market_event_sufficient_data_calculates_sma(self):
        """测试on_market_event数据充足时计算移动平均线"""
        # Red: 编写失败的测试
        # 添加足够的数据
        prices = [100.0 + i for i in range(self.long_window)]
        for i, price in enumerate(prices):
            market_event = MarketEvent(
                symbol="AAPL",
                timestamp=datetime.now(timezone.utc),
                close_price=price,
                open_price=price - 1,
                high_price=price + 1,
                low_price=price - 2,
                volume=1000000
            )
            self.strategy.on_market_event(market_event)
        
        # 验证移动平均线被计算
        assert self.strategy.short_sma["AAPL"] is not None
        assert self.strategy.long_sma["AAPL"] is not None
        assert self.strategy.was_short_above_long["AAPL"] is not None
        
        # 验证移动平均线计算正确
        # 短期SMA应该是最后5个价格的平均值
        expected_short_sma = sum(prices[-self.short_window:]) / self.short_window
        assert abs(self.strategy.short_sma["AAPL"] - expected_short_sma) < 0.01
        
        # 长期SMA应该是所有20个价格的平均值
        expected_long_sma = sum(prices) / self.long_window
        assert abs(self.strategy.long_sma["AAPL"] - expected_long_sma) < 0.01
    
    def test_check_signal_no_sma_calculated(self):
        """测试_check_signal在移动平均线未计算时不生成信号"""
        # Red: 编写失败的测试
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=150.0,
            open_price=149.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )
        
        # 直接调用_check_signal（SMA为None）
        initial_queue_size = len(self.event_loop)
        self.strategy._check_signal(market_event)
        
        # 验证没有生成信号
        assert len(self.event_loop) == initial_queue_size
    
    def test_check_signal_first_time_only_records_state(self):
        """测试_check_signal第一次只记录状态不生成信号"""
        # Red: 编写失败的测试
        # 设置移动平均线值
        self.strategy.short_sma["AAPL"] = 155.0
        self.strategy.long_sma["AAPL"] = 150.0
        
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=155.0,
            open_price=154.0,
            high_price=156.0,
            low_price=153.0,
            volume=1000000
        )
        
        # 第一次调用_check_signal
        initial_queue_size = len(self.event_loop)
        self.strategy._check_signal(market_event)
        
        # 验证状态被记录但没有生成信号
        assert self.strategy.was_short_above_long["AAPL"] is True  # 短期>长期
        assert len(self.event_loop) == initial_queue_size

    def test_check_signal_golden_cross_generates_long_signal(self):
        """测试_check_signal金叉生成LONG信号"""
        # Red: 编写失败的测试
        # 设置初始状态：短期在长期下方
        self.strategy.short_sma["AAPL"] = 149.0
        self.strategy.long_sma["AAPL"] = 150.0
        self.strategy.was_short_above_long["AAPL"] = False

        # 更新为金叉状态：短期上穿长期
        self.strategy.short_sma["AAPL"] = 151.0
        self.strategy.long_sma["AAPL"] = 150.0

        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=151.0,
            open_price=150.0,
            high_price=152.0,
            low_price=149.0,
            volume=1000000
        )

        # 调用_check_signal
        initial_queue_size = len(self.event_loop)
        self.strategy._check_signal(market_event)

        # 验证生成了LONG信号
        assert len(self.event_loop) == initial_queue_size + 1
        signal_event = self.event_loop.get_next_event()
        assert isinstance(signal_event, SignalEvent)
        assert signal_event.symbol == "AAPL"
        assert signal_event.signal_type == "LONG"
        assert signal_event.strength == 1.0

        # 验证状态更新
        assert self.strategy.was_short_above_long["AAPL"] is True

    def test_check_signal_death_cross_generates_short_signal(self):
        """测试_check_signal死叉生成SHORT信号"""
        # Red: 编写失败的测试
        # 设置初始状态：短期在长期上方
        self.strategy.short_sma["AAPL"] = 151.0
        self.strategy.long_sma["AAPL"] = 150.0
        self.strategy.was_short_above_long["AAPL"] = True

        # 更新为死叉状态：短期下穿长期
        self.strategy.short_sma["AAPL"] = 149.0
        self.strategy.long_sma["AAPL"] = 150.0

        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=149.0,
            open_price=150.0,
            high_price=151.0,
            low_price=148.0,
            volume=1000000
        )

        # 调用_check_signal
        initial_queue_size = len(self.event_loop)
        self.strategy._check_signal(market_event)

        # 验证生成了SHORT信号
        assert len(self.event_loop) == initial_queue_size + 1
        signal_event = self.event_loop.get_next_event()
        assert isinstance(signal_event, SignalEvent)
        assert signal_event.symbol == "AAPL"
        assert signal_event.signal_type == "SHORT"
        assert signal_event.strength == 1.0

        # 验证状态更新
        assert self.strategy.was_short_above_long["AAPL"] is False

    def test_check_signal_no_cross_no_signal(self):
        """测试_check_signal无交叉时不生成信号"""
        # Red: 编写失败的测试
        # 设置状态：短期持续在长期上方
        self.strategy.short_sma["AAPL"] = 151.0
        self.strategy.long_sma["AAPL"] = 150.0
        self.strategy.was_short_above_long["AAPL"] = True

        # 更新但仍保持短期在长期上方
        self.strategy.short_sma["AAPL"] = 152.0
        self.strategy.long_sma["AAPL"] = 150.5

        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=152.0,
            open_price=151.0,
            high_price=153.0,
            low_price=150.0,
            volume=1000000
        )

        # 调用_check_signal
        initial_queue_size = len(self.event_loop)
        self.strategy._check_signal(market_event)

        # 验证没有生成信号
        assert len(self.event_loop) == initial_queue_size

        # 验证状态更新
        assert self.strategy.was_short_above_long["AAPL"] is True
