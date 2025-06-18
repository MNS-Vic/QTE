#!/usr/bin/env python3
"""
BE_Backtester覆盖率提升专用测试
专门设计来覆盖BE_Backtester中未被测试的代码路径
"""

import pytest
import queue
import time
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from qte.core.backtester import BE_Backtester
from qte.core.events import EventType, MarketEvent


class TestBEBacktesterCoverage:
    """BE_Backtester覆盖率提升测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建Mock组件，使用MagicMock来支持魔术方法
        self.mock_event_loop = MagicMock()
        self.mock_data_provider = Mock()
        self.mock_strategy = Mock()
        self.mock_portfolio = Mock()
        self.mock_broker = Mock()
        self.symbols = ['TEST_SYMBOL']
    
    def test_backtester_initialization_and_event_registration(self):
        """测试backtester初始化和事件注册"""
        # 创建backtester
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 验证属性设置
        assert backtester.event_loop == self.mock_event_loop
        assert backtester.data_provider == self.mock_data_provider
        assert backtester.strategy == self.mock_strategy
        assert backtester.portfolio == self.mock_portfolio
        assert backtester.broker == self.mock_broker
        assert backtester.symbols == self.symbols
        
        # 验证事件处理器注册
        expected_calls = [
            (EventType.MARKET, self.mock_strategy.on_market_event),
            (EventType.MARKET, self.mock_portfolio.update_on_market_data),
            (EventType.ORDER, self.mock_broker.submit_order),
            (EventType.FILL, self.mock_portfolio.update_on_fill)
        ]
        
        assert self.mock_event_loop.register_handler.call_count == 4
    
    def test_run_backtest_with_strategy_without_on_init(self):
        """测试策略没有on_init方法的情况"""
        # 策略没有on_init方法
        strategy_without_init = Mock()
        del strategy_without_init.on_init  # 删除on_init属性
        
        # 设置数据提供者返回空事件列表
        self.mock_data_provider.stream_market_data.return_value = []
        self.mock_event_loop.get_next_event.return_value = None
        self.mock_event_loop.__len__.return_value = 0
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=strategy_without_init,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证数据提供者被调用
        self.mock_data_provider.stream_market_data.assert_called_once_with(symbols=self.symbols)
    
    def test_run_backtest_with_events_processing(self):
        """测试事件处理循环"""
        # 创建模拟事件
        mock_event1 = Mock()
        mock_event1.event_type = EventType.MARKET
        mock_event1.symbol = 'TEST'
        mock_event1.timestamp = datetime.now()
        
        mock_event2 = Mock()
        mock_event2.event_type = EventType.ORDER
        mock_event2.symbol = 'TEST'
        mock_event2.timestamp = datetime.now()
        
        # 设置事件循环返回事件序列
        self.mock_event_loop.get_next_event.side_effect = [mock_event1, mock_event2, None]
        self.mock_event_loop.__len__.side_effect = [2, 1, 0]  # 队列长度递减
        
        # 设置数据提供者返回一些事件
        self.mock_data_provider.stream_market_data.return_value = [mock_event1, mock_event2]
        
        # 设置策略有on_init方法
        self.mock_strategy.on_init = Mock()
        
        # 设置投资组合有print_summary方法
        self.mock_portfolio.print_summary = Mock()
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证策略初始化被调用
        self.mock_strategy.on_init.assert_called_once_with(self.mock_data_provider)
        
        # 验证事件分发被调用
        assert self.mock_event_loop.dispatch_event.call_count == 2
        
        # 验证投资组合摘要被调用
        self.mock_portfolio.print_summary.assert_called_once()
    
    def test_run_backtest_with_queue_empty_exception(self):
        """测试队列空异常处理"""
        # 设置事件循环抛出queue.Empty异常
        self.mock_event_loop.get_next_event.side_effect = queue.Empty()
        self.mock_data_provider.stream_market_data.return_value = []
        self.mock_strategy.on_init = Mock()
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测，应该正常处理异常
        backtester.run_backtest()
        
        # 验证策略初始化被调用
        self.mock_strategy.on_init.assert_called_once()
    
    def test_run_backtest_with_keyboard_interrupt(self):
        """测试键盘中断处理"""
        # 设置事件循环抛出KeyboardInterrupt
        self.mock_event_loop.get_next_event.side_effect = KeyboardInterrupt()
        self.mock_data_provider.stream_market_data.return_value = []
        self.mock_strategy.on_init = Mock()
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测，应该正常处理中断
        backtester.run_backtest()
        
        # 验证策略初始化被调用
        self.mock_strategy.on_init.assert_called_once()
    
    def test_run_backtest_with_general_exception(self):
        """测试一般异常处理"""
        # 设置事件循环抛出一般异常
        self.mock_event_loop.get_next_event.side_effect = RuntimeError("Test error")
        self.mock_data_provider.stream_market_data.return_value = []
        self.mock_strategy.on_init = Mock()
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测，应该正常处理异常
        backtester.run_backtest()
        
        # 验证策略初始化被调用
        self.mock_strategy.on_init.assert_called_once()
    
    def test_run_backtest_without_portfolio_print_summary(self):
        """测试投资组合没有print_summary方法的情况"""
        # 投资组合没有print_summary方法
        portfolio_without_summary = Mock()
        del portfolio_without_summary.print_summary
        
        self.mock_data_provider.stream_market_data.return_value = []
        self.mock_event_loop.get_next_event.return_value = None
        self.mock_event_loop.__len__.return_value = 0
        self.mock_strategy.on_init = Mock()
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=portfolio_without_summary,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证策略初始化被调用
        self.mock_strategy.on_init.assert_called_once()
    
    def test_run_backtest_with_event_progress_logging(self):
        """测试事件处理进度日志"""
        # 创建大量事件来触发进度日志
        events = []
        for i in range(150):  # 超过100个事件来触发进度日志
            event = Mock()
            event.event_type = EventType.MARKET
            event.symbol = f'TEST{i}'
            event.timestamp = datetime.now()
            events.append(event)
        
        # 设置数据提供者返回大量事件
        self.mock_data_provider.stream_market_data.return_value = events
        
        # 设置事件循环返回事件然后结束
        self.mock_event_loop.get_next_event.side_effect = events + [None]
        self.mock_event_loop.__len__.side_effect = list(range(len(events), -1, -1))
        
        self.mock_strategy.on_init = Mock()
        self.mock_portfolio.print_summary = Mock()
        
        backtester = BE_Backtester(
            event_loop=self.mock_event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证所有事件都被分发
        assert self.mock_event_loop.dispatch_event.call_count == len(events)
