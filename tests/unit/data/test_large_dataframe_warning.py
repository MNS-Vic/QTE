"""
测试数据重放控制器对大型数据集的警告情况

此测试文件专门测试数据重放控制器在处理超大数据集时的警告和性能调优
"""

import pandas as pd
import pytest
import numpy as np
from datetime import datetime, timedelta
import time
import logging

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

class TestLargeDatasetWarnings:
    """测试处理大型数据集时的警告和行为"""
    
    def setup_method(self):
        """设置测试环境，捕获日志"""
        # 配置日志捕获
        self.log_capture = []
        
        class LogHandler(logging.Handler):
            def __init__(self, log_list):
                super().__init__()
                self.log_list = log_list
                
            def emit(self, record):
                self.log_list.append(record.getMessage())
        
        # 添加自定义处理器到数据重放控制器的日志器
        self.handler = LogHandler(self.log_capture)
        self.logger = logging.getLogger("DataReplayController")
        self.logger.addHandler(self.handler)
        self.original_level = self.logger.level
        self.logger.setLevel(logging.DEBUG)
    
    def teardown_method(self):
        """清理测试环境"""
        # 恢复日志配置
        self.logger.removeHandler(self.handler)
        self.logger.setLevel(self.original_level)
    
    def test_large_dataframe_warning(self):
        """测试大型DataFrame的警告"""
        # 创建一个大型DataFrame (超过100,000行)
        size = 150000
        df = pd.DataFrame({
            'price': np.random.randn(size),
            'volume': np.random.randint(1000, 10000, size)
        })
        
        # 创建控制器，应该发出警告
        controller = DataFrameReplayController(df)
        
        # 检查是否有警告消息
        warning_logs = [log for log in self.log_capture if "大型数据集" in log or "large dataset" in log]
        assert len(warning_logs) > 0, "应该对大型数据集发出警告"
        
        # 测试性能是否可接受
        start_time = time.time()
        # 只处理前1000个数据点以节省测试时间
        for i in range(1000):
            data = controller.step_sync()
            assert data is not None
        
        elapsed = time.time() - start_time
        proc_per_sec = 1000 / elapsed
        
        print(f"\n处理1000个数据点耗时: {elapsed:.4f}秒")
        print(f"每秒处理数据点: {proc_per_sec:.2f}")
        
        # 确保性能在合理范围内
        assert proc_per_sec > 1000, "处理速度应超过每秒1000条"
    
    def test_multi_source_large_data_warning(self):
        """测试多数据源中有大型数据集的情况"""
        # 创建一个正常大小的数据源和一个大型数据源
        size_normal = 10000
        size_large = 120000
        
        # 正常大小的数据源
        df_normal = pd.DataFrame({
            'value': np.random.randn(size_normal),
            'volume': np.random.randint(1000, 10000, size_normal)
        })
        
        # 大型数据源
        df_large = pd.DataFrame({
            'value': np.random.randn(size_large),
            'volume': np.random.randint(1000, 10000, size_large)
        })
        
        # 创建多数据源控制器
        controller = MultiSourceReplayController({
            'normal': df_normal,
            'large': df_large
        })
        
        # 检查是否有大型数据源警告
        source_warning_logs = [log for log in self.log_capture if "个大型数据源" in log or "large source" in log]
        assert len(source_warning_logs) > 0, "应该对大型数据源发出警告"
        
        # 检查是否指明了哪个数据源较大 - 在日志中查找数据源名称
        large_source_mentioned = False
        for log in self.log_capture:
            if "个大型数据源" in log and "large" in log:
                large_source_mentioned = True
                break
        
        assert large_source_mentioned, "应该指出具体哪个数据源较大"
        
        # 测试多数据源处理的性能
        start_time = time.time()
        # 只处理前1000个数据点
        count = 0
        while count < 1000:
            data = controller.step_sync()
            if data is None:
                break
            count += 1
        
        elapsed = time.time() - start_time
        proc_per_sec = count / elapsed
        
        print(f"\n多数据源处理{count}个数据点耗时: {elapsed:.4f}秒")
        print(f"每秒处理数据点: {proc_per_sec:.2f}")
        
        # 确保多数据源处理性能在合理范围内
        assert proc_per_sec > 500, "多数据源处理速度应超过每秒500条"
    
    def test_memory_optimization(self):
        """测试内存优化选项"""
        # 创建大型DataFrame
        size = 120000
        df = pd.DataFrame({
            'price': np.random.randn(size),
            'volume': np.random.randint(1000, 10000, size)
        })
        
        # 使用memory_optimized=True创建控制器
        controller = DataFrameReplayController(df, memory_optimized=True)
        
        # 检查是否有内存优化的日志
        mem_logs = [log for log in self.log_capture if "memory" in log or "内存" in log]
        assert len(mem_logs) > 0, "应该有内存优化相关的日志"
        
        # 测试处理性能
        start_time = time.time()
        # 只处理前1000个数据点
        for i in range(1000):
            data = controller.step_sync()
            assert data is not None
        
        elapsed = time.time() - start_time
        proc_per_sec = 1000 / elapsed
        
        print(f"\n内存优化模式处理1000个数据点耗时: {elapsed:.4f}秒")
        print(f"每秒处理数据点: {proc_per_sec:.2f}")
        
        # 在内存优化模式下，性能可能会略低，但仍应保持在合理范围内
        assert proc_per_sec > 500, "内存优化模式下处理速度应超过每秒500条"

# 运行测试时添加verbosity
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 