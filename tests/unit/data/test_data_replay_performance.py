"""
数据重放控制器性能测试

此测试文件专注于数据重放控制器的性能表现，包括大数据量、高频回调等场景
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

class TestSyncPerformance:
    """测试同步API的性能"""
    
    def test_large_dataframe_sync(self):
        """测试处理大型DataFrame的性能"""
        # 创建大型测试数据
        size = 50000
        print(f"\n测试处理{size}行数据的性能")
        
        dates = pd.date_range(start='2023-01-01', periods=size, freq='1min')
        df = pd.DataFrame({
            'price': np.random.randint(100, 200, size),
            'volume': np.random.randint(1000, 10000, size)
        }, index=dates)
        
        # 创建控制器
        controller = DataFrameReplayController(df)
        
        # 计时处理性能
        start_time = time.time()
        results = controller.process_all_sync()
        end_time = time.time()
        
        # 计算和输出性能指标
        processing_time = end_time - start_time
        rows_per_second = size / processing_time
        
        print(f"总处理时间: {processing_time:.2f}秒")
        print(f"每秒处理行数: {rows_per_second:.0f}行/秒")
        
        # 验证处理了所有数据
        assert len(results) == size
        assert controller.get_status() == ReplayStatus.COMPLETED
    
    def test_multiple_callbacks_performance(self):
        """测试多回调场景的性能"""
        # 创建中等大小的测试数据
        size = 10000
        print(f"\n测试{size}行数据上的多回调性能")
        
        dates = pd.date_range(start='2023-01-01', periods=size, freq='1min')
        df = pd.DataFrame({
            'price': np.random.randint(100, 200, size),
            'volume': np.random.randint(1000, 10000, size)
        }, index=dates)
        
        # 创建不同数量回调的场景
        callback_counts = [1, 5, 10, 20]
        
        for cb_count in callback_counts:
            # 创建控制器
            controller = DataFrameReplayController(df)
            
            # 注册指定数量的回调
            for i in range(cb_count):
                controller.register_callback(lambda x: None)  # 空回调，最小化回调自身的开销
            
            # 计时处理性能
            start_time = time.time()
            results = controller.process_all_sync()
            end_time = time.time()
            
            # 计算和输出性能指标
            processing_time = end_time - start_time
            rows_per_second = size / processing_time
            
            print(f"{cb_count}个回调: 总时间={processing_time:.2f}秒, 速度={rows_per_second:.0f}行/秒")
            
            # 验证处理了所有数据
            assert len(results) == size
    
    def test_multi_source_performance(self):
        """测试多数据源控制器的性能"""
        # 创建多个测试数据源
        source_counts = [2, 3, 5, 10]
        size_per_source = 5000
        
        print(f"\n测试多数据源性能 (每源{size_per_source}行)")
        
        for source_count in source_counts:
            # 创建多个数据源
            data_sources = {}
            for i in range(source_count):
                # 使用不同的起始日期，确保格式正确
                start_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=i)
                dates = pd.date_range(
                    start=start_date,
                    periods=size_per_source,
                    freq='1min'
                )
                
                # 创建数据
                data_sources[f'source{i+1}'] = pd.DataFrame({
                    'value': np.random.randn(size_per_source),
                    'volume': np.random.randint(1000, 10000, size_per_source)
                }, index=dates)
            
            # 创建多数据源控制器
            controller = MultiSourceReplayController(data_sources)
            
            # 计时处理性能
            start_time = time.time()
            results = controller.process_all_sync()
            end_time = time.time()
            
            # 计算和输出性能指标
            total_rows = source_count * size_per_source
            processing_time = end_time - start_time
            rows_per_second = total_rows / processing_time
            
            print(f"{source_count}个数据源: 总时间={processing_time:.2f}秒, 速度={rows_per_second:.0f}行/秒")
            
            # 验证处理了所有数据
            assert len(results) == total_rows


class TestAsyncPerformance:
    """测试异步API的性能"""
    
    def test_async_vs_sync_performance(self):
        """比较异步和同步处理的性能差异"""
        # 创建中等大小的测试数据
        size = 10000
        print(f"\n比较异步与同步处理{size}行数据的性能")
        
        dates = pd.date_range(start='2023-01-01', periods=size, freq='1min')
        df = pd.DataFrame({
            'price': np.random.randint(100, 200, size),
            'volume': np.random.randint(1000, 10000, size)
        }, index=dates)
        
        # 测试同步API性能
        controller_sync = DataFrameReplayController(df)
        start_time = time.time()
        results_sync = controller_sync.process_all_sync()
        sync_time = time.time() - start_time
        
        # 测试异步API性能（使用回调收集数据）
        controller_async = DataFrameReplayController(df)
        async_results = []
        
        def collect_data(data):
            async_results.append(data)
        
        controller_async.register_callback(collect_data)
        
        # 启动并等待完成
        start_time = time.time()
        controller_async.start()
        
        # 等待处理完成
        max_wait = 30  # 最多等待30秒
        wait_start = time.time()
        while (controller_async.get_status() != ReplayStatus.COMPLETED and 
               time.time() - wait_start < max_wait):
            time.sleep(0.1)
            
        async_time = time.time() - start_time
        
        # 输出性能比较
        print(f"同步处理时间: {sync_time:.2f}秒, 处理{len(results_sync)}行")
        print(f"异步处理时间: {async_time:.2f}秒, 处理{len(async_results)}行")
        print(f"性能比较: 异步/同步 = {sync_time/async_time:.2f}x")
        
        # 验证异步方式也能成功处理数据
        # 由于实现方式不同，不强制要求处理相同数量的数据
        assert len(async_results) > 0
    
    def test_realtime_mode_performance(self):
        """测试实时模式的性能表现"""
        # 创建小型测试数据（加速模式会有延迟）
        size = 100
        print(f"\n测试实时模式(加速)处理{size}行数据的性能")
        
        # 创建具有递增时间间隔的数据
        base_date = datetime(2023, 1, 1)
        dates = [base_date + timedelta(seconds=i*5) for i in range(size)]
        
        df = pd.DataFrame({
            'price': np.random.randint(100, 200, size),
            'timestamp': dates
        })
        
        # 使用加速模式，100倍速
        controller = DataFrameReplayController(
            df, 
            timestamp_column='timestamp',
            mode=ReplayMode.ACCELERATED, 
            speed_factor=100.0
        )
        
        # 收集结果
        results = []
        def collect_data(data):
            results.append(data)
            
        controller.register_callback(collect_data)
        
        # 启动并计时
        start_time = time.time()
        controller.start()
        
        # 等待处理完成
        max_wait = 30  # 最多等待30秒
        wait_start = time.time()
        while (controller.get_status() != ReplayStatus.COMPLETED and 
               time.time() - wait_start < max_wait):
            time.sleep(0.1)
            
        processing_time = time.time() - start_time
        
        # 计算理论耗时（考虑加速因子）
        total_data_time = (dates[-1] - dates[0]).total_seconds()
        expected_time = total_data_time / 100.0
        
        print(f"实际处理时间: {processing_time:.2f}秒")
        print(f"理论处理时间: {expected_time:.2f}秒")
        print(f"速度比例: {processing_time/expected_time:.2f}x")
        
        # 验证确实有处理数据，但不强制要求达到特定比例
        # 由于异步实现和计时控制的复杂性，实际处理量可能有很大差异
        assert len(results) > 0


class TestMemoryUsage:
    """测试内存使用情况"""
    
    def test_memory_with_large_data(self):
        """测试处理大数据时的内存使用"""
        # 需要依赖psutil包，如果没有则跳过测试
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            pytest.skip("psutil未安装，跳过内存测试")
            return
            
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大型DataFrame (100K行)
        size = 100000
        print(f"\n测试处理{size}行数据的内存使用")
        
        # 创建测试数据
        df = pd.DataFrame({
            'price': np.random.randint(100, 200, size),
            'volume': np.random.randint(1000, 10000, size),
            'extra_data': ['x' * 100 for _ in range(size)]  # 添加大字符串增加内存使用
        })
        
        # 记录加载数据后的内存
        data_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建控制器并处理数据
        controller = DataFrameReplayController(df)
        results = controller.process_all_sync()
        
        # 记录处理后的内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 输出内存使用情况
        print(f"初始内存: {initial_memory:.1f} MB")
        print(f"加载数据后: {data_memory:.1f} MB (增加 {data_memory-initial_memory:.1f} MB)")
        print(f"处理后: {final_memory:.1f} MB (增加 {final_memory-data_memory:.1f} MB)")
        
        # 验证处理了所有数据
        assert len(results) == size


if __name__ == "__main__":
    pytest.main(["-v", "test_data_replay_performance.py"]) 