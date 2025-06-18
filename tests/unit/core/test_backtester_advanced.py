#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BE_Backtester高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
import time
import queue
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, call

from qte.core.event_loop import EventLoop
from qte.core.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from qte.core.backtester import BE_Backtester


class TestBEBacktesterAdvanced:
    """BE_Backtester高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.event_loop = EventLoop()
        self.mock_data_provider = Mock()
        self.mock_strategy = Mock()
        self.mock_portfolio = Mock()
        self.mock_broker = Mock()
        self.symbols = ["AAPL", "GOOGL"]
        
        # 创建回测器实例
        self.backtester = BE_Backtester(
            event_loop=self.event_loop,
            data_provider=self.mock_data_provider,
            strategy=self.mock_strategy,
            portfolio=self.mock_portfolio,
            broker=self.mock_broker,
            symbols=self.symbols
        )
    
    def test_init_backtester(self):
        """测试回测器初始化"""
        # Red: 编写失败的测试
        assert self.backtester.event_loop == self.event_loop
        assert self.backtester.data_provider == self.mock_data_provider
        assert self.backtester.strategy == self.mock_strategy
        assert self.backtester.portfolio == self.mock_portfolio
        assert self.backtester.broker == self.mock_broker
        assert self.backtester.symbols == self.symbols
    
    def test_register_event_handlers(self):
        """测试事件处理器注册"""
        # Red: 编写失败的测试
        # 验证事件处理器被正确注册
        handlers = self.event_loop.handlers

        # 验证MARKET事件处理器
        assert "MARKET" in handlers
        market_handlers = handlers["MARKET"]
        assert self.mock_strategy.on_market_event in market_handlers
        assert self.mock_portfolio.update_on_market_data in market_handlers

        # 验证ORDER事件处理器
        assert "ORDER" in handlers
        order_handlers = handlers["ORDER"]
        assert self.mock_broker.submit_order in order_handlers

        # 验证FILL事件处理器
        assert "FILL" in handlers
        fill_handlers = handlers["FILL"]
        assert self.mock_portfolio.update_on_fill in fill_handlers
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_with_strategy_init(self, mock_logger):
        """测试运行回测 - 策略有on_init方法"""
        # Red: 编写失败的测试
        # 设置策略有on_init方法
        self.mock_strategy.on_init = Mock()
        
        # 设置数据提供者返回空的市场事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # 设置投资组合有print_summary方法
        self.mock_portfolio.print_summary = Mock()
        
        # 运行回测
        self.backtester.run_backtest()
        
        # 验证策略初始化被调用
        self.mock_strategy.on_init.assert_called_once_with(self.mock_data_provider)
        
        # 验证数据流式传输被调用
        self.mock_data_provider.stream_market_data.assert_called_once_with(symbols=self.symbols)
        
        # 验证投资组合摘要被调用
        self.mock_portfolio.print_summary.assert_called_once()
        
        # 验证日志记录
        assert mock_logger.info.call_count >= 5  # 至少有开始、步骤0、1、2、3、结束的日志
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_without_strategy_init(self, mock_logger):
        """测试运行回测 - 策略没有on_init方法"""
        # Red: 编写失败的测试
        # 确保策略没有on_init方法
        if hasattr(self.mock_strategy, 'on_init'):
            delattr(self.mock_strategy, 'on_init')
        
        # 设置数据提供者返回空的市场事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # 设置投资组合有print_summary方法
        self.mock_portfolio.print_summary = Mock()
        
        # 运行回测
        self.backtester.run_backtest()
        
        # 验证警告日志被记录
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "策略对象没有可调用的 on_init 方法" in str(call)]
        assert len(warning_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_without_portfolio_summary(self, mock_logger):
        """测试运行回测 - 投资组合没有print_summary方法"""
        # Red: 编写失败的测试
        # 确保投资组合没有print_summary方法
        if hasattr(self.mock_portfolio, 'print_summary'):
            delattr(self.mock_portfolio, 'print_summary')
        
        # 设置数据提供者返回空的市场事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # 运行回测
        self.backtester.run_backtest()
        
        # 验证警告日志被记录
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "投资组合对象没有可调用的 print_summary 方法" in str(call)]
        assert len(warning_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_with_market_events(self, mock_logger):
        """测试运行回测 - 处理市场事件"""
        # Red: 编写失败的测试
        # 创建测试市场事件
        market_events = [
            MarketEvent(
                symbol="AAPL",
                timestamp=datetime.now(timezone.utc),
                open_price=150.0,
                high_price=155.0,
                low_price=149.0,
                close_price=152.0,
                volume=1000
            ),
            MarketEvent(
                symbol="GOOGL",
                timestamp=datetime.now(timezone.utc),
                open_price=2500.0,
                high_price=2505.0,
                low_price=2499.0,
                close_price=2502.0,
                volume=500
            )
        ]
        
        # 设置数据提供者返回市场事件
        self.mock_data_provider.stream_market_data.return_value = market_events
        
        # 运行回测
        self.backtester.run_backtest()
        
        # 验证事件计数日志
        info_calls = [call for call in mock_logger.info.call_args_list 
                     if "共 2 个事件" in str(call)]
        assert len(info_calls) > 0
        
        # 验证事件处理日志
        processed_calls = [call for call in mock_logger.info.call_args_list 
                          if "总共处理了" in str(call) and "个事件" in str(call)]
        assert len(processed_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_with_large_dataset(self, mock_logger):
        """测试运行回测 - 大数据集处理"""
        # Red: 编写失败的测试
        # 创建大量市场事件
        market_events = []
        for i in range(150):  # 150个事件
            market_events.append(
                MarketEvent(
                    symbol="AAPL",
                    timestamp=datetime.now(timezone.utc),
                    open_price=150.0 + i,
                    high_price=155.0 + i,
                    low_price=149.0 + i,
                    close_price=152.0 + i,
                    volume=1000
                )
            )

        # 设置数据提供者返回大量市场事件
        self.mock_data_provider.stream_market_data.return_value = market_events

        # 运行回测
        self.backtester.run_backtest()

        # 验证数据加载信息日志
        info_calls = [call for call in mock_logger.info.call_args_list
                     if "共 150 个事件" in str(call)]
        assert len(info_calls) > 0

        # 验证事件处理完成日志
        process_complete_calls = [call for call in mock_logger.info.call_args_list
                                 if "总共处理了" in str(call) and "个事件" in str(call)]
        assert len(process_complete_calls) > 0

        # 验证回测耗时日志
        timing_calls = [call for call in mock_logger.info.call_args_list
                       if "回测耗时" in str(call)]
        assert len(timing_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_keyboard_interrupt(self, mock_logger):
        """测试运行回测 - 键盘中断处理"""
        # Red: 编写失败的测试
        # 设置数据提供者返回空事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # Mock event_loop.get_next_event 抛出KeyboardInterrupt
        with patch.object(self.event_loop, 'get_next_event', side_effect=KeyboardInterrupt("Test interrupt")):
            # 运行回测
            self.backtester.run_backtest()
            
            # 验证键盘中断警告日志
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                            if "捕获到键盘中断" in str(call)]
            assert len(warning_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_general_exception(self, mock_logger):
        """测试运行回测 - 一般异常处理"""
        # Red: 编写失败的测试
        # 设置数据提供者返回空事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # Mock event_loop.get_next_event 抛出一般异常
        with patch.object(self.event_loop, 'get_next_event', side_effect=Exception("Test exception")):
            # 运行回测
            self.backtester.run_backtest()
            
            # 验证错误日志
            error_calls = [call for call in mock_logger.error.call_args_list 
                          if "回测主循环中发生未捕获错误" in str(call)]
            assert len(error_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_queue_empty_exception(self, mock_logger):
        """测试运行回测 - 队列空异常处理"""
        # Red: 编写失败的测试
        # 设置数据提供者返回空事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # Mock event_loop.get_next_event 抛出queue.Empty异常
        with patch.object(self.event_loop, 'get_next_event', side_effect=queue.Empty("Test queue empty")):
            # 运行回测
            self.backtester.run_backtest()
            
            # 验证队列空信息日志
            info_calls = [call for call in mock_logger.info.call_args_list 
                         if "事件队列报告为空" in str(call)]
            assert len(info_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_event_type_counting(self, mock_logger):
        """测试运行回测 - 事件类型计数"""
        # Red: 编写失败的测试
        # 创建不同类型的事件
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            open_price=150.0,
            high_price=155.0,
            low_price=149.0,
            close_price=152.0,
            volume=1000
        )
        
        signal_event = SignalEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            signal_type="LONG",
            direction=1,
            strength=1.0
        )
        
        # 设置数据提供者返回市场事件
        self.mock_data_provider.stream_market_data.return_value = [market_event]
        
        # 手动添加信号事件到队列
        self.event_loop.put_event(signal_event)
        
        # 运行回测
        self.backtester.run_backtest()
        
        # 验证事件类型统计日志
        stats_calls = [call for call in mock_logger.info.call_args_list 
                      if "事件类型统计" in str(call)]
        assert len(stats_calls) > 0
    
    @patch('qte.core.backtester.app_logger')
    def test_run_backtest_timing_measurement(self, mock_logger):
        """测试运行回测 - 时间测量"""
        # Red: 编写失败的测试
        # 设置数据提供者返回空事件
        self.mock_data_provider.stream_market_data.return_value = []
        
        # 运行回测
        start_time = time.time()
        self.backtester.run_backtest()
        end_time = time.time()
        
        # 验证时间测量日志
        timing_calls = [call for call in mock_logger.info.call_args_list 
                       if "回测耗时" in str(call) and "秒" in str(call)]
        assert len(timing_calls) > 0
        
        # 验证实际耗时合理
        actual_duration = end_time - start_time
        assert actual_duration < 5.0  # 应该在5秒内完成
    
    def test_run_backtest_complete_flow(self):
        """测试运行回测 - 完整流程"""
        # Red: 编写失败的测试
        # 创建测试事件
        market_event = MarketEvent(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            open_price=150.0,
            high_price=155.0,
            low_price=149.0,
            close_price=152.0,
            volume=1000
        )

        # 设置数据提供者返回市场事件
        self.mock_data_provider.stream_market_data.return_value = [market_event]

        # 设置投资组合有print_summary方法
        self.mock_portfolio.print_summary = Mock()

        # 运行回测（应该不抛出异常）
        self.backtester.run_backtest()

        # 验证数据提供者被调用
        self.mock_data_provider.stream_market_data.assert_called_once_with(symbols=self.symbols)

        # 验证投资组合摘要被调用
        self.mock_portfolio.print_summary.assert_called_once()

        # 验证回测完成（没有异常）
        assert True
