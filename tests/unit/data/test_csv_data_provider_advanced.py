#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSVDataProvider高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
import pandas as pd
import os
import tempfile
import shutil
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from pathlib import Path

from qte.core.event_loop import EventLoop
from qte.core.events import MarketEvent
from qte.data.csv_data_provider import CSVDataProvider


class TestCSVDataProviderAdvanced:
    """CSVDataProvider高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.event_loop = EventLoop()
        self.temp_dir = tempfile.mkdtemp()
        self.symbols = ["AAPL", "GOOGL"]
        
        # 创建测试CSV文件
        self._create_test_csv_files()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_csv_files(self):
        """创建测试用的CSV文件"""
        # AAPL数据
        aapl_data = {
            'timestamp': ['2023-01-01 09:00:00', '2023-01-01 09:02:00', '2023-01-01 09:04:00'],
            'open': [150.0, 151.0, 152.0],
            'high': [155.0, 156.0, 157.0],
            'low': [149.0, 150.0, 151.0],
            'close': [152.0, 153.0, 155.0],
            'volume': [1000, 1200, 1100]
        }
        aapl_df = pd.DataFrame(aapl_data)
        aapl_df.to_csv(os.path.join(self.temp_dir, "AAPL.csv"), index=False)
        
        # GOOGL数据（时间交错）
        googl_data = {
            'timestamp': ['2023-01-01 09:01:00', '2023-01-01 09:03:00', '2023-01-01 09:05:00'],
            'open': [2500.0, 2501.0, 2502.0],
            'high': [2505.0, 2506.0, 2507.0],
            'low': [2499.0, 2500.0, 2501.0],
            'close': [2502.0, 2503.0, 2505.0],
            'volume': [500, 600, 550]
        }
        googl_df = pd.DataFrame(googl_data)
        googl_df.to_csv(os.path.join(self.temp_dir, "GOOGL.csv"), index=False)
    
    def test_init_csv_data_provider(self):
        """测试CSVDataProvider初始化"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)
        
        # 验证基本属性
        assert provider.event_loop == self.event_loop
        assert provider.csv_dir_path == self.temp_dir
        assert provider.symbols == self.symbols
        
        # 验证数据加载
        assert "AAPL" in provider.data
        assert "GOOGL" in provider.data
        assert len(provider.data["AAPL"]) == 3
        assert len(provider.data["GOOGL"]) == 3
        
        # 验证数据排序
        assert len(provider.all_bars_sorted) == 6  # 3 + 3
        
        # 验证时间排序正确
        timestamps = [bar['timestamp'] for bar in provider.all_bars_sorted]
        assert timestamps == sorted(timestamps)
    
    def test_load_all_data_missing_file(self):
        """测试加载数据时文件缺失的情况"""
        # Red: 编写失败的测试
        symbols_with_missing = ["AAPL", "MISSING_SYMBOL"]
        
        with patch('builtins.print') as mock_print:
            provider = CSVDataProvider(self.event_loop, self.temp_dir, symbols_with_missing)
            
            # 验证只加载了存在的文件
            assert "AAPL" in provider.data
            assert "MISSING_SYMBOL" not in provider.data
            
            # 验证打印了警告信息
            warning_calls = [call for call in mock_print.call_args_list 
                           if "警告" in str(call) and "MISSING_SYMBOL" in str(call)]
            assert len(warning_calls) > 0
    
    def test_load_all_data_missing_columns(self):
        """测试加载数据时列缺失的情况"""
        # Red: 编写失败的测试
        # 创建缺少列的CSV文件
        invalid_data = {
            'timestamp': ['2023-01-01 09:00:00'],
            'open': [150.0],
            'high': [155.0]
            # 缺少 low, close, volume 列
        }
        invalid_df = pd.DataFrame(invalid_data)
        invalid_path = os.path.join(self.temp_dir, "INVALID.csv")
        invalid_df.to_csv(invalid_path, index=False)
        
        symbols_with_invalid = ["AAPL", "INVALID"]
        
        with patch('builtins.print') as mock_print:
            provider = CSVDataProvider(self.event_loop, self.temp_dir, symbols_with_invalid)
            
            # 验证无效文件未被加载
            assert "AAPL" in provider.data
            assert "INVALID" not in provider.data
            
            # 验证打印了警告信息
            warning_calls = [call for call in mock_print.call_args_list 
                           if "警告" in str(call) and "缺少必要列" in str(call)]
            assert len(warning_calls) > 0
    
    def test_load_all_data_file_read_error(self):
        """测试加载数据时文件读取错误的情况"""
        # Red: 编写失败的测试
        # 创建无效的CSV文件
        invalid_path = os.path.join(self.temp_dir, "CORRUPT.csv")
        with open(invalid_path, 'w') as f:
            f.write("invalid,csv,content\nwith,wrong,format")
        
        symbols_with_corrupt = ["AAPL", "CORRUPT"]
        
        with patch('builtins.print') as mock_print:
            provider = CSVDataProvider(self.event_loop, self.temp_dir, symbols_with_corrupt)
            
            # 验证损坏文件未被加载
            assert "AAPL" in provider.data
            assert "CORRUPT" not in provider.data
            
            # 验证打印了错误信息
            error_calls = [call for call in mock_print.call_args_list 
                          if "错误" in str(call) and "CORRUPT" in str(call)]
            assert len(error_calls) > 0
    
    def test_prepare_sorted_bars_empty_data(self):
        """测试准备排序数据时无数据的情况"""
        # Red: 编写失败的测试
        empty_temp_dir = tempfile.mkdtemp()
        try:
            with patch('builtins.print') as mock_print:
                provider = CSVDataProvider(self.event_loop, empty_temp_dir, ["NONEXISTENT"])
                
                # 验证没有数据被排序
                assert len(provider.all_bars_sorted) == 0
                
                # 验证打印了相应信息
                no_data_calls = [call for call in mock_print.call_args_list 
                               if "没有K线数据被加载或准备" in str(call)]
                assert len(no_data_calls) > 0
        finally:
            shutil.rmtree(empty_temp_dir, ignore_errors=True)
    
    def test_prepare_sorted_bars_datetime_conversion(self):
        """测试准备排序数据时的datetime转换"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)
        
        # 验证所有排序后的数据都有正确的datetime类型
        for bar in provider.all_bars_sorted:
            assert isinstance(bar['timestamp'], datetime)
            assert 'symbol_for_event' in bar
    
    def test_stream_market_data_all_symbols(self):
        """测试流式传输所有标的的市场数据"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)
        
        # 记录初始队列状态
        initial_queue_size = len(self.event_loop)
        
        # 流式传输数据
        events = list(provider.stream_market_data())
        
        # 验证生成了正确数量的事件
        assert len(events) == 6  # 3 AAPL + 3 GOOGL
        
        # 验证事件被添加到队列
        assert len(self.event_loop) == initial_queue_size + 6
        
        # 验证事件类型和内容
        for event in events:
            assert isinstance(event, MarketEvent)
            assert event.symbol in self.symbols
            assert event.open_price > 0
            assert event.close_price > 0
            assert event.volume > 0
        
        # 验证latest_data被更新
        assert "AAPL" in provider.latest_data
        assert "GOOGL" in provider.latest_data
        assert provider.latest_data["AAPL"]['close'] == 155.0  # 最后一条AAPL数据
        assert provider.latest_data["GOOGL"]['close'] == 2505.0  # 最后一条GOOGL数据
    
    def test_stream_market_data_specific_symbols(self):
        """测试流式传输特定标的的市场数据"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)
        
        # 只流式传输AAPL数据
        events = list(provider.stream_market_data(symbols=["AAPL"]))
        
        # 验证只生成了AAPL事件
        assert len(events) == 3
        for event in events:
            assert event.symbol == "AAPL"
        
        # 验证latest_data只包含AAPL
        assert "AAPL" in provider.latest_data
        # GOOGL可能不在latest_data中，因为没有被流式传输
    
    def test_stream_market_data_no_data(self):
        """测试流式传输时无数据的情况"""
        # Red: 编写失败的测试
        empty_temp_dir = tempfile.mkdtemp()
        try:
            with patch('builtins.print') as mock_print:
                provider = CSVDataProvider(self.event_loop, empty_temp_dir, ["NONEXISTENT"])
                
                # 流式传输应该返回空
                events = list(provider.stream_market_data())
                assert len(events) == 0
                
                # 验证打印了无数据信息
                no_data_calls = [call for call in mock_print.call_args_list 
                               if "没有数据可供流式传输" in str(call)]
                assert len(no_data_calls) > 0
        finally:
            shutil.rmtree(empty_temp_dir, ignore_errors=True)
    
    def test_stream_market_data_key_error_handling(self):
        """测试流式传输时KeyError异常处理"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)
        
        # 模拟损坏的bar_info数据
        original_bars = provider.all_bars_sorted.copy()
        provider.all_bars_sorted = [{'symbol_for_event': 'AAPL', 'timestamp': datetime.now()}]  # 缺少价格数据
        
        with patch('builtins.print') as mock_print:
            events = list(provider.stream_market_data())
            
            # 验证没有生成事件（因为数据损坏）
            assert len(events) == 0
            
            # 验证打印了错误信息
            error_calls = [call for call in mock_print.call_args_list 
                          if "错误" in str(call) and "缺少键" in str(call)]
            assert len(error_calls) > 0
        
        # 恢复原始数据
        provider.all_bars_sorted = original_bars
    
    def test_stream_market_data_value_error_handling(self):
        """测试流式传输时ValueError异常处理"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)
        
        # 模拟无效的数据类型
        original_bars = provider.all_bars_sorted.copy()
        provider.all_bars_sorted = [{
            'symbol_for_event': 'AAPL',
            'timestamp': datetime.now(),
            'open': 'invalid_price',  # 无效的价格数据
            'high': 155.0,
            'low': 149.0,
            'close': 152.0,
            'volume': 1000
        }]
        
        with patch('builtins.print') as mock_print:
            events = list(provider.stream_market_data())
            
            # 验证没有生成事件（因为数据转换失败）
            assert len(events) == 0
            
            # 验证打印了错误信息
            error_calls = [call for call in mock_print.call_args_list 
                          if "错误" in str(call) and "数据转换失败" in str(call)]
            assert len(error_calls) > 0
        
        # 恢复原始数据
        provider.all_bars_sorted = original_bars

    def test_get_latest_bar_existing_symbol(self):
        """测试获取存在标的的最新K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 流式传输一些数据
        list(provider.stream_market_data())

        # 获取最新K线
        latest_aapl = provider.get_latest_bar("AAPL")
        latest_googl = provider.get_latest_bar("GOOGL")

        # 验证返回了正确的数据
        assert latest_aapl is not None
        assert latest_aapl['close'] == 155.0
        assert 'symbol_for_event' not in latest_aapl  # 应该被移除

        assert latest_googl is not None
        assert latest_googl['close'] == 2505.0

    def test_get_latest_bar_nonexistent_symbol(self):
        """测试获取不存在标的的最新K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 获取不存在标的的最新K线
        latest_nonexistent = provider.get_latest_bar("NONEXISTENT")

        # 验证返回None
        assert latest_nonexistent is None

    def test_get_latest_bars_existing_symbol(self):
        """测试获取存在标的的最新N条K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 流式传输所有数据
        list(provider.stream_market_data())

        # 获取最新2条AAPL K线
        latest_bars = provider.get_latest_bars("AAPL", n=2)

        # 验证返回了正确数量的K线
        assert latest_bars is not None
        assert len(latest_bars) == 2

        # 验证是最新的2条数据
        assert latest_bars[-1]['close'] == 155.0  # 最新的
        assert latest_bars[-2]['close'] == 153.0  # 倒数第二新的

    def test_get_latest_bars_more_than_available(self):
        """测试获取超过可用数量的最新K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 流式传输所有数据
        list(provider.stream_market_data())

        # 尝试获取超过可用数量的K线
        latest_bars = provider.get_latest_bars("AAPL", n=10)

        # 验证返回了所有可用的K线
        assert latest_bars is not None
        assert len(latest_bars) == 3  # 只有3条可用

    def test_get_latest_bars_nonexistent_symbol(self):
        """测试获取不存在标的的最新K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 获取不存在标的的最新K线
        latest_bars = provider.get_latest_bars("NONEXISTENT", n=5)

        # 验证返回None
        assert latest_bars is None

    def test_get_latest_bars_no_streamed_data(self):
        """测试在没有流式传输数据时获取最新K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 不进行流式传输，直接获取最新K线
        latest_bars = provider.get_latest_bars("AAPL", n=2)

        # 验证返回None（因为没有latest_data）
        assert latest_bars is None

    def test_get_historical_bars_existing_symbol(self):
        """测试获取存在标的的历史K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 定义时间范围
        start_date = datetime(2023, 1, 1, 9, 0, 0)
        end_date = datetime(2023, 1, 1, 9, 3, 0)

        # 获取历史K线生成器
        hist_generator = provider.get_historical_bars("AAPL", start_date, end_date)

        # 验证返回了生成器
        assert hist_generator is not None

        # 验证生成器内容
        hist_bars = list(hist_generator)
        assert len(hist_bars) == 2  # 09:00 和 09:02 的数据
        assert hist_bars[0]['close'] == 152.0
        assert hist_bars[1]['close'] == 153.0

    def test_get_historical_bars_nonexistent_symbol(self):
        """测试获取不存在标的的历史K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        start_date = datetime(2023, 1, 1, 9, 0, 0)
        end_date = datetime(2023, 1, 1, 9, 3, 0)

        # 获取不存在标的的历史K线
        hist_generator = provider.get_historical_bars("NONEXISTENT", start_date, end_date)

        # 验证返回None
        assert hist_generator is None

    def test_get_historical_bars_no_data_in_range(self):
        """测试获取时间范围内无数据的历史K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 定义一个没有数据的时间范围
        start_date = datetime(2022, 1, 1, 9, 0, 0)
        end_date = datetime(2022, 1, 1, 9, 3, 0)

        # 获取历史K线
        hist_generator = provider.get_historical_bars("AAPL", start_date, end_date)

        # 验证返回None
        assert hist_generator is None

    def test_get_n_historical_bars_existing_symbol(self):
        """测试获取存在标的的N条历史K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 流式传输所有数据
        list(provider.stream_market_data())

        # 获取最近2条历史K线
        hist_df = provider.get_n_historical_bars("AAPL", n=2)

        # 验证返回了DataFrame
        assert hist_df is not None
        assert isinstance(hist_df, pd.DataFrame)
        assert len(hist_df) == 2

        # 验证是最新的2条数据
        assert hist_df.iloc[-1]['close'] == 155.0
        assert hist_df.iloc[-2]['close'] == 153.0

    def test_get_n_historical_bars_nonexistent_symbol(self):
        """测试获取不存在标的的N条历史K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 获取不存在标的的历史K线
        hist_df = provider.get_n_historical_bars("NONEXISTENT", n=2)

        # 验证返回None
        assert hist_df is None

    def test_get_n_historical_bars_no_streamed_data(self):
        """测试在没有流式传输数据时获取N条历史K线"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 不进行流式传输，直接获取历史K线
        hist_df = provider.get_n_historical_bars("AAPL", n=2)

        # 验证返回None（因为没有latest_data）
        assert hist_df is None

    def test_complex_streaming_scenario(self):
        """测试复杂的流式传输场景"""
        # Red: 编写失败的测试
        provider = CSVDataProvider(self.event_loop, self.temp_dir, self.symbols)

        # 验证初始状态
        assert len(provider.latest_data) == 0

        # 逐步流式传输数据
        events = []
        for event in provider.stream_market_data():
            events.append(event)

            # 在每个事件后验证latest_data状态
            if event.symbol == "AAPL":
                assert "AAPL" in provider.latest_data
                assert provider.latest_data["AAPL"]['close'] == event.close_price
            elif event.symbol == "GOOGL":
                assert "GOOGL" in provider.latest_data
                assert provider.latest_data["GOOGL"]['close'] == event.close_price

        # 验证最终状态
        assert len(events) == 6
        assert len(provider.latest_data) == 2

        # 验证事件时间顺序
        event_times = [event.timestamp for event in events]
        assert event_times == sorted(event_times)

        # 验证最终的latest_data
        assert provider.latest_data["AAPL"]['close'] == 155.0
        assert provider.latest_data["GOOGL"]['close'] == 2505.0
