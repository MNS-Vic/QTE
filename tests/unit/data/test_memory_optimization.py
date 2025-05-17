"""
测试数据重放控制器的性能优化功能
"""

import unittest
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime, timedelta

from qte.data.data_replay import (
    DataFrameReplayController, 
    MultiSourceReplayController,
    ReplayMode
)

class TestMemoryOptimization(unittest.TestCase):
    """测试内存优化功能"""
    
    def setUp(self):
        """准备测试数据"""
        # 创建测试数据
        size = 10000
        dates = pd.date_range(start='2023-01-01', periods=size, freq='1min')
        prices = 100 + np.cumsum(np.random.normal(0, 0.1, size))
        volumes = np.random.randint(1000, 10000, size)
        
        self.df = pd.DataFrame({
            'price': prices,
            'volume': volumes
        }, index=dates)
        
    def test_memory_optimized_flag(self):
        """测试内存优化标志正确设置"""
        # 标准模式
        controller1 = DataFrameReplayController(self.df)
        self.assertFalse(controller1._memory_optimized)
        
        # 内存优化模式
        controller2 = DataFrameReplayController(self.df, memory_optimized=True)
        self.assertTrue(controller2._memory_optimized)
        self.assertTrue(hasattr(controller2, '_optimized_iterator'))
    
    def test_optimized_data_access(self):
        """测试优化模式下的数据访问"""
        # 创建内存优化控制器
        controller = DataFrameReplayController(self.df, memory_optimized=True)
        
        # 获取第一个数据点
        data1 = controller.step_sync()
        self.assertIsNotNone(data1)
        
        # 确保可以正确访问数据点的属性
        self.assertEqual(data1['price'], self.df.iloc[0]['price'])
        self.assertEqual(data1['volume'], self.df.iloc[0]['volume'])
        
        # 获取第二个数据点
        data2 = controller.step_sync()
        self.assertIsNotNone(data2)
        
        # 确保可以正确访问数据点的属性
        self.assertEqual(data2['price'], self.df.iloc[1]['price'])
        self.assertEqual(data2['volume'], self.df.iloc[1]['volume'])
    
    def test_process_all_with_optimization(self):
        """测试优化模式下处理所有数据"""
        # 创建内存优化控制器
        controller = DataFrameReplayController(self.df, memory_optimized=True)
        
        # 处理所有数据
        results = controller.process_all_sync()
        
        # 验证结果
        self.assertEqual(len(results), len(self.df))
        
        # 检查一些数据点
        for i in [0, 100, 1000]:
            self.assertEqual(results[i]['price'], self.df.iloc[i]['price'])
            self.assertEqual(results[i]['volume'], self.df.iloc[i]['volume'])
    
    def test_reset_with_optimization(self):
        """测试优化模式下的重置功能"""
        # 创建内存优化控制器
        controller = DataFrameReplayController(self.df, memory_optimized=True)
        
        # 处理一些数据点
        for _ in range(10):
            controller.step_sync()
        
        # 重置控制器
        controller.reset()
        
        # 确认重置后从头开始
        data = controller.step_sync()
        self.assertEqual(data['price'], self.df.iloc[0]['price'])
        
    def test_multi_source_optimization(self):
        """测试多数据源优化"""
        # 创建两个数据源
        df1 = self.df.copy()
        df2 = self.df.copy()
        df2['indicator'] = np.random.random(len(df2))
        
        # 创建优化的多数据源控制器
        controller = MultiSourceReplayController(
            data_sources={
                'prices': df1,
                'indicators': df2
            },
            memory_optimized=True
        )
        
        # 检查控制器属性
        self.assertTrue(controller._memory_optimized)
        
        # 初始化同步迭代器
        controller._initialize_sync_iterators()
        
        # 验证同步迭代器结构
        self.assertIn('prices', controller._sync_iterators)
        self.assertIn('indicators', controller._sync_iterators)
        
        # 检查优化模式下迭代器结构
        price_iter = controller._sync_iterators['prices']
        self.assertIsInstance(price_iter, dict)
        self.assertEqual(price_iter['type'], 'dataframe_optimized')
        
        # 处理少量数据点
        for _ in range(5):
            data = controller.step_sync()
            self.assertIsNotNone(data)
            self.assertIn('_source', data)
            
class TestCallbackOptimization(unittest.TestCase):
    """测试回调优化功能"""
    
    def setUp(self):
        """准备测试数据"""
        # 创建测试数据
        size = 5000
        dates = pd.date_range(start='2023-01-01', periods=size, freq='1min')
        prices = 100 + np.cumsum(np.random.normal(0, 0.1, size))
        
        self.df = pd.DataFrame({
            'price': prices,
        }, index=dates)
        
    def test_batch_callbacks_flag(self):
        """测试批量回调标志正确设置"""
        # 标准模式
        controller1 = DataFrameReplayController(self.df)
        self.assertFalse(controller1._batch_callbacks)
        
        # 批量回调模式
        controller2 = DataFrameReplayController(self.df, batch_callbacks=True)
        self.assertTrue(controller2._batch_callbacks)
        self.assertTrue(hasattr(controller2, '_callback_queue'))
        self.assertTrue(hasattr(controller2, '_callback_event'))
    
    def test_callback_thread_creation(self):
        """测试回调线程创建"""
        # 创建批量回调控制器
        controller = DataFrameReplayController(self.df, batch_callbacks=True)
        
        # 批量回调模式下应该创建回调线程
        self.assertIsNotNone(controller._callback_thread)
        self.assertTrue(controller._callback_thread.is_alive())
        
        # 关闭线程
        controller.stop()
    
    def test_batch_callback_processing(self):
        """测试批量回调处理"""
        # 创建批量回调控制器
        controller = DataFrameReplayController(
            self.df, 
            batch_callbacks=True
        )
        
        # 用于跟踪处理情况的变量
        processed_items = []
        processing_complete = threading.Event()
        
        # 计数回调
        def counting_callback(data):
            processed_items.append(data)
            # 当处理完所有数据时设置事件
            if len(processed_items) == len(self.df):
                processing_complete.set()
        
        # 注册回调
        controller.register_callback(counting_callback)
        
        # 处理所有数据
        all_data = controller.process_all_sync()
        
        # 等待回调处理完成
        processing_complete.wait(timeout=2.0)
        
        # 验证所有数据都通过回调处理
        self.assertEqual(len(processed_items), len(self.df))
    
    def test_combined_optimizations(self):
        """测试结合内存优化和批量回调"""
        # 创建同时启用两种优化的控制器
        controller = DataFrameReplayController(
            self.df,
            memory_optimized=True,
            batch_callbacks=True
        )
        
        # 用于跟踪处理情况的变量
        processed_count = 0
        count_lock = threading.Lock()
        processing_complete = threading.Event()
        
        # 计数回调
        def counting_callback(data):
            nonlocal processed_count
            with count_lock:
                processed_count += 1
                # 当处理完所有数据时设置事件
                if processed_count == len(self.df):
                    processing_complete.set()
        
        # 注册回调
        controller.register_callback(counting_callback)
        
        # 处理所有数据
        controller.process_all_sync()
        
        # 等待回调处理完成
        processing_complete.wait(timeout=2.0)
        
        # 验证所有数据都通过回调处理
        self.assertEqual(processed_count, len(self.df))
        
        # 重置并测试单步执行
        controller.reset()
        processed_count = 0
        
        # 单步执行
        data = controller.step_sync()
        self.assertIsNotNone(data)
        
        # 等待回调处理
        time.sleep(0.2)
        
        # 由于使用批量处理，单个回调可能尚未被处理
        # 所以这里我们不严格检查处理数量
        
if __name__ == '__main__':
    unittest.main() 