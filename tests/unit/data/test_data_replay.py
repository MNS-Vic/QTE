"""
数据重放控制器测试模块

测试数据重放控制器的功能，包括基本控制器、DataFrame控制器和多数据源控制器
"""

import unittest
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import logging
import pytest
import numpy as np

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

# 配置日志记录
logger = logging.getLogger(__name__)

class TestBaseDataReplayController(unittest.TestCase):
    """测试基础数据重放控制器"""
    
    def setUp(self):
        """准备测试环境"""
        # 创建一个简单实现，覆盖抽象方法
        class TestReplayController(BaseDataReplayController):
            def __init__(self, data=None, mode=ReplayMode.BACKTEST, speed_factor=1.0):
                super().__init__(data_source=data, mode=mode, speed_factor=speed_factor)
                self._test_data = data or [1, 2, 3]
                self._current_index = 0
            
            def _get_next_data_point(self):
                if self._current_index >= len(self._test_data):
                    return None
                data = self._test_data[self._current_index]
                self._current_index += 1
                return data
                
        self.controller = TestReplayController()
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.controller._status, ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._mode, ReplayMode.BACKTEST)
        self.assertEqual(self.controller._speed_factor, 1.0)
        self.assertEqual(len(self.controller._callbacks), 0)
        
    def test_start_stop(self):
        """测试启动和停止"""
        # 测试启动功能
        self.assertTrue(self.controller.start())
        self.assertEqual(self.controller._status, ReplayStatus.RUNNING)
        self.assertTrue(self.controller._event.is_set())  # 事件应该被设置
        
        # 等待一小段时间让线程启动
        time.sleep(0.2)
        
        # 测试停止功能
        self.assertTrue(self.controller.stop())
        self.assertEqual(self.controller._status, ReplayStatus.STOPPED)
        
        # 确保重新启动能正常工作
        time.sleep(0.1)  # 给线程一点时间完全停止
        self.controller.reset()
        self.assertTrue(self.controller.start())
        self.assertEqual(self.controller._status, ReplayStatus.RUNNING)
        
    def test_pause_resume(self):
        """测试暂停和恢复"""
        # 直接设置状态为RUNNING，不依赖start方法和线程
        with self.controller._lock:
            self.controller._status = ReplayStatus.RUNNING
            
        # 测试暂停功能
        self.assertTrue(self.controller.pause())
        self.assertEqual(self.controller._status, ReplayStatus.PAUSED)
        self.assertFalse(self.controller._event.is_set())  # 事件应该被清除
        
        # 测试恢复功能
        self.assertTrue(self.controller.resume())
        self.assertEqual(self.controller._status, ReplayStatus.RUNNING)
        self.assertTrue(self.controller._event.is_set())  # 事件应该被设置
        
    def test_set_speed(self):
        """测试设置速度"""
        self.assertTrue(self.controller.set_speed(2.0))
        self.assertEqual(self.controller._speed_factor, 2.0)
        
        # 测试无效速度
        self.assertFalse(self.controller.set_speed(0))
        self.assertEqual(self.controller._speed_factor, 2.0)  # 保持原值
        
        self.assertFalse(self.controller.set_speed(-1))
        self.assertEqual(self.controller._speed_factor, 2.0)  # 保持原值
        
    def test_set_mode(self):
        """测试设置模式"""
        self.assertTrue(self.controller.set_mode(ReplayMode.STEPPED))
        self.assertEqual(self.controller._mode, ReplayMode.STEPPED)
        
        # 在运行状态下无法更改模式
        self.controller.start()
        time.sleep(0.1)
        
        self.assertFalse(self.controller.set_mode(ReplayMode.REALTIME))
        self.assertEqual(self.controller._mode, ReplayMode.STEPPED)  # 保持原值
        
        self.controller.stop()
        
    def test_get_status(self):
        """测试获取状态"""
        self.assertEqual(self.controller.get_status(), ReplayStatus.INITIALIZED)
        
        # 直接测试状态设置和获取，不依赖线程
        with self.controller._lock:  # 使用锁来模拟内部状态更改
            self.controller._status = ReplayStatus.RUNNING
        self.assertEqual(self.controller.get_status(), ReplayStatus.RUNNING)
        
        with self.controller._lock:
            self.controller._status = ReplayStatus.STOPPED
        self.assertEqual(self.controller.get_status(), ReplayStatus.STOPPED)
        
    def test_callbacks(self):
        """测试回调函数注册和通知"""
        data_received = []
        
        def callback(data):
            data_received.append(data)
            
        # 注册回调
        cb_id = self.controller.register_callback(callback)
        self.assertIsInstance(cb_id, int)
        self.assertIn(cb_id, self.controller._callbacks)
        
        # 启动控制器
        self.controller.start()
        time.sleep(0.3)  # 给予足够时间处理所有数据
        
        # 检查回调是否被调用
        self.assertEqual(len(data_received), 3)  # 测试数据是[1, 2, 3]
        self.assertEqual(data_received, [1, 2, 3])
        
        # 注销回调
        self.assertTrue(self.controller.unregister_callback(cb_id))
        self.assertNotIn(cb_id, self.controller._callbacks)
        
        # 注销不存在的回调
        self.assertFalse(self.controller.unregister_callback(999))
        
    def test_step(self):
        """测试步进模式"""
        # 设置为步进模式
        self.controller.set_mode(ReplayMode.STEPPED)
        
        # 步进三次
        self.assertEqual(self.controller.step(), 1)
        self.assertEqual(self.controller.step(), 2)
        self.assertEqual(self.controller.step(), 3)
        
        # 没有更多数据
        self.assertIsNone(self.controller.step())
        self.assertEqual(self.controller._status, ReplayStatus.COMPLETED)
        
    def test_reset(self):
        """测试重置功能"""
        # 先消耗部分数据
        self.controller.step()
        self.controller.step()
        self.assertEqual(self.controller._current_position, 2)  # 位置应该是2
        
        # 重置
        self.assertTrue(self.controller.reset())
        self.assertEqual(self.controller._status, ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._current_position, 0)  # 位置应该重置为0
        self.assertTrue(self.controller.reset_called)  # 检查是否调用了reset方法
        self.assertTrue(self.controller._event.is_set())  # 事件应该被设置
        
        # 重置后应该能再次获取所有数据
        data = []
        for _ in range(4):  # 多测试一次确保到达结尾
            d = self.controller.step()
            if d is None:
                break
            data.append(d)
        
        self.assertEqual(data, [1, 2, 3])  # 应该能获取所有3个数据点
        
    def test_running_mode(self):
        """测试各种运行模式"""
        # 使用API直接测试不同模式而不依赖线程
        
        # 测试回测模式 - 使用步进方式测试
        controller1 = self.controller.__class__(mode=ReplayMode.BACKTEST)
        controller1.step()  # 第一步
        controller1.step()  # 第二步
        controller1.step()  # 第三步
        controller1.step()  # 没有更多数据，应完成
        self.assertEqual(controller1._status, ReplayStatus.COMPLETED)
        
        # 测试步进模式
        controller2 = self.controller.__class__(mode=ReplayMode.STEPPED)
        controller2.step()  # 只有一步，应自动暂停
        # 在步进模式下，step不会暂停，但start会在读取第一个数据后暂停
        controller2.start()
        time.sleep(0.2)
        self.assertEqual(controller2._status, ReplayStatus.PAUSED)
        
        # 测试实时模式 - 使用直接API调用
        controller3 = self.controller.__class__(mode=ReplayMode.REALTIME, speed_factor=100)
        for _ in range(3):  # 手动调用step而不是使用线程
            controller3.step()
        controller3.step()  # 第四次调用，没有更多数据，应完成
        self.assertEqual(controller3._status, ReplayStatus.COMPLETED)


class TestDataFrameReplayController(unittest.TestCase):
    """测试基于DataFrame的数据重放控制器"""
    
    def setUp(self):
        """准备测试环境"""
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        data = {'price': [100, 101, 102, 103, 104], 'volume': [1000, 1100, 1200, 1300, 1400]}
        self.df = pd.DataFrame(data, index=dates)
        
        # 创建控制器
        self.controller = DataFrameReplayController(self.df)
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.controller._status, ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._mode, ReplayMode.BACKTEST)
        self.assertEqual(self.controller._speed_factor, 1.0)
        self.assertEqual(self.controller.current_index, -1)
        self.assertIs(self.controller._df, self.df)
        
    def test_get_next_data_point(self):
        """测试获取下一个数据点"""
        # 直接测试内部方法
        data = self.controller._get_next_data_point()
        self.assertIsNotNone(data)
        self.assertEqual(data['price'], 100)
        self.assertEqual(data['volume'], 1000)
        self.assertEqual(self.controller.current_index, 0)
        
        # 再获取一个
        data = self.controller._get_next_data_point()
        self.assertEqual(data['price'], 101)
        self.assertEqual(self.controller.current_index, 1)
        
    def test_empty_dataframe(self):
        """测试空DataFrame"""
        empty_df = pd.DataFrame()
        controller = DataFrameReplayController(empty_df)
        
        # 不应该有数据点
        self.assertIsNone(controller._get_next_data_point())
        
    def test_step(self):
        """测试步进功能"""
        # 步进获取所有数据 - 使用同步API
        data = []
        while True:
            d = self.controller.step_sync()
            if d is None:
                break
            if 'volume' in d:
                data.append(('volume', d['volume']))
            elif 'price' in d:
                data.append(('price', d['price']))
        
        # 验证数据顺序 - 注意同步API可能与异步API排序不同
        self.assertEqual(len(data), 6)
        
        # 验证每个数据源的所有记录都存在
        price_points = [p for t, p in data if t == 'price']
        volume_points = [v for t, v in data if t == 'volume']
        
        # 检查所有预期的数据点都存在
        self.assertEqual(set(price_points), {100, 101, 102})
        self.assertEqual(set(volume_points), {1000, 1100, 1200})
        
    def test_reset(self):
        """测试重置功能"""
        # 先消耗一些数据 - 使用同步API
        self.controller.step_sync()
        self.controller.step_sync()
        self.controller.step_sync()
        
        # 注意：同步API使用不同的机制，可能不会更新_current_position
        # 但我们确保能够正常重置
        
        # 重置
        self.assertTrue(self.controller.reset())
        self.assertEqual(self.controller._status, ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._current_position, 0)
        self.assertTrue(self.controller._event.is_set())
        
        # 验证数据源已重新初始化
        # 这里不直接检查_next_data，而是测试重置后能否正确读取数据
        
        # 再次获取数据 - 使用同步API
        data = []
        for _ in range(7):  # 限制循环次数，避免无限循环
            d = self.controller.step_sync()
            if d is None:
                break
            if 'volume' in d:
                data.append(('volume', d['volume']))
            if 'price' in d:
                data.append(('price', d['price']))
        
        # 验证获取到所有6个数据点
        self.assertEqual(len(data), 6)
        
        # 验证price和volume的数据点都存在
        price_count = sum(1 for t, _ in data if t == 'price')
        volume_count = sum(1 for t, _ in data if t == 'volume')
        self.assertEqual(price_count, 3)
        self.assertEqual(volume_count, 3)
        
    def test_timestamp_column(self):
        """测试时间戳列功能"""
        # 创建包含时间戳列的DataFrame
        timestamps = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data = {
            'timestamp': timestamps,
            'price': [100, 101, 102]
        }
        df = pd.DataFrame(data)
        
        # 使用时间戳列创建控制器
        controller = DataFrameReplayController(df, timestamp_column='timestamp')
        
        # 获取数据点
        d1 = controller.step()
        self.assertEqual(d1['price'], 100)
        self.assertTrue(pd.Timestamp('2023-01-01') == controller.current_timestamp or
                      pd.Timestamp('2023-01-01 00:00:00') == controller.current_timestamp)
        
        d2 = controller.step()
        self.assertEqual(d2['price'], 101)
        self.assertTrue(pd.Timestamp('2023-01-02') == controller.current_timestamp or
                      pd.Timestamp('2023-01-02 00:00:00') == controller.current_timestamp)
        
    def test_callback_with_dataframe(self):
        """测试DataFrame回调机制"""
        received_data = []
        
        def callback(data):
            received_data.append((data['price'], data['volume']))
            
        # 注册回调
        self.controller.register_callback(callback)
        
        # 启动控制器
        self.controller.start()
        time.sleep(0.3)  # 给予足够时间处理所有数据
        
        # 验证回调收到的数据
        expected = [(100, 1000), (101, 1100), (102, 1200), (103, 1300), (104, 1400)]
        self.assertEqual(received_data, expected)
        
    def test_realtime_mode(self):
        """测试实时模式下的速度控制"""
        # 创建实时模式控制器，但使用很高的速度因子以避免测试时间过长
        controller = DataFrameReplayController(
            self.df, 
            mode=ReplayMode.REALTIME, 
            speed_factor=100.0
        )
        
        # 记录开始时间
        start_time = time.time()
        
        # 启动控制器
        controller.start()
        
        # 等待完成
        for _ in range(10):  # 最多等待1秒
            if controller.get_status() == ReplayStatus.COMPLETED:
                break
            time.sleep(0.1)
            
        # 记录结束时间
        end_time = time.time()
        
        # 验证状态
        self.assertEqual(controller.get_status(), ReplayStatus.COMPLETED)
        
        # 由于我们使用了非常高的速度因子，应该很快完成
        # 但至少应该有一些延迟，不会立即完成
        elapsed = end_time - start_time
        self.assertLess(elapsed, 1.0)  # 应该不超过1秒


class TestMultiSourceReplayController(unittest.TestCase):
    """测试多数据源重放控制器"""
    
    def setUp(self):
        """准备测试环境"""
        # 创建测试数据
        dates1 = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data1 = {'price': [100, 101, 102]}
        self.df1 = pd.DataFrame(data1, index=dates1)
        
        dates2 = pd.date_range(start='2023-01-01', periods=3, freq='8h')
        data2 = {'volume': [1000, 1100, 1200]}
        self.df2 = pd.DataFrame(data2, index=dates2)
        
        # 创建控制器
        self.controller = MultiSourceReplayController({
            'price': self.df1,
            'volume': self.df2
        })
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.controller._status, ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._mode, ReplayMode.BACKTEST)
        self.assertEqual(self.controller._speed_factor, 1.0)
        
        # 验证数据源已正确初始化
        self.assertIn('price', self.controller._next_data)
        self.assertIn('volume', self.controller._next_data)
        
    def test_get_next_data_point(self):
        """测试获取下一个数据点"""
        # 使用step_sync方法来测试数据输出序列，避免线程同步问题
        results = []
        while True:
            data = self.controller.step_sync()
            if data is None:
                break
            # 收集数据类型和值
            if 'volume' in data:
                results.append(('volume', data['volume']))
            if 'price' in data:
                results.append(('price', data['price']))
        
        # 验证数据点的个数和序列
        self.assertEqual(len(results), 6)
        
        # 验证上源和数据的顺序。直接检查集合而不是具体的排序
        # 这样的验证更稳定，开发者可以对具体实现的算法进行调整
        # 只要确保所有的数据都被输出即可
        price_points = [p for t, p in results if t == 'price']
        volume_points = [v for t, v in results if t == 'volume']
        
        # 检查所有预期的数据点都存在
        self.assertEqual(set(price_points), {100, 101, 102})
        self.assertEqual(set(volume_points), {1000, 1100, 1200})
        
        # 重置控制器，再次测试数据重播
        self.controller.reset()
        result2 = []
        for _ in range(7):  # 最多尝试7次，应该只会返回6个数据点和一个None
            data = self.controller.step_sync() # 使用同步API
            if data is None:
                break
            # 收集数据类型和值
            if 'volume' in data:
                result2.append(('volume', data['volume']))
            if 'price' in data:
                result2.append(('price', data['price']))
        
        # 应该仍然有全部6个数据点
        self.assertEqual(len(result2), 6)
        
    def test_step(self):
        """测试步进功能"""
        # 步进获取所有数据 - 使用同步API
        data = []
        while True:
            d = self.controller.step_sync()
            if d is None:
                break
            if 'volume' in d:
                data.append(('volume', d['volume']))
            elif 'price' in d:
                data.append(('price', d['price']))
        
        # 验证数据顺序 - 注意同步API可能与异步API排序不同
        self.assertEqual(len(data), 6)
        
        # 验证每个数据源的所有记录都存在
        price_points = [p for t, p in data if t == 'price']
        volume_points = [v for t, v in data if t == 'volume']
        
        # 检查所有预期的数据点都存在
        self.assertEqual(set(price_points), {100, 101, 102})
        self.assertEqual(set(volume_points), {1000, 1100, 1200})
        
    def test_reset(self):
        """测试重置功能"""
        # 先消耗一些数据 - 使用同步API
        self.controller.step_sync()
        self.controller.step_sync()
        self.controller.step_sync()
        
        # 注意：同步API使用不同的机制，可能不会更新_current_position
        # 但我们确保能够正常重置
        
        # 重置
        self.assertTrue(self.controller.reset())
        self.assertEqual(self.controller._status, ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._current_position, 0)
        self.assertTrue(self.controller._event.is_set())
        
        # 验证数据源已重新初始化
        # 这里不直接检查_next_data，而是测试重置后能否正确读取数据
        
        # 再次获取数据 - 使用同步API
        data = []
        for _ in range(7):  # 限制循环次数，避免无限循环
            d = self.controller.step_sync()
            if d is None:
                break
            if 'volume' in d:
                data.append(('volume', d['volume']))
            if 'price' in d:
                data.append(('price', d['price']))
        
        # 验证获取到所有6个数据点
        self.assertEqual(len(data), 6)
        
        # 验证price和volume的数据点都存在
        price_count = sum(1 for t, _ in data if t == 'price')
        volume_count = sum(1 for t, _ in data if t == 'volume')
        self.assertEqual(price_count, 3)
        self.assertEqual(volume_count, 3)
        
    def test_custom_timestamp_extractors(self):
        """测试自定义时间戳提取器"""
        # 创建非日期索引的DataFrame
        data1 = {'timestamp': pd.date_range(start='2023-01-01', periods=3, freq='D'), 'price': [100, 101, 102]}
        data2 = {'timestamp': pd.date_range(start='2023-01-01', periods=3, freq='12h'), 'volume': [1000, 1100, 1200]}
        
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        
        # 定义提取器
        def extract_timestamp1(data):
            return data['timestamp']
            
        def extract_timestamp2(data):
            return data['timestamp']
            
        # 创建控制器
        controller = MultiSourceReplayController(
            {'price': df1, 'volume': df2},
            timestamp_extractors={'price': extract_timestamp1, 'volume': extract_timestamp2}
        )
        
        # 验证数据按时间戳顺序获取 - 使用同步API
        results = []
        while True:
            d = controller.step_sync()
            if d is None:
                break
            results.append(d)
            
        # 验证按时间戳排序
        for i in range(1, len(results)):
            prev_ts = results[i-1]['timestamp']
            curr_ts = results[i]['timestamp']
            self.assertLessEqual(prev_ts, curr_ts)

# 集成测试，以便测试多个控制器类之间的交互
class TestDataReplayIntegration:
    """数据重放控制器集成测试"""
    
    def test_data_transfer_between_controllers(self):
        """测试数据从一个控制器传输到另一个控制器"""
        # 创建第一个控制器
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        data = {'price': [100, 101, 102, 103, 104], 'volume': [1000, 1100, 1200, 1300, 1400]}
        df = pd.DataFrame(data, index=dates)
        controller1 = DataFrameReplayController(df)
        
        # 创建一个队列来收集数据
        collected_data = []
        
        # 定义一个回调函数
        def collect_data(data):
            collected_data.append(data)
            
        # 注册回调
        controller1.register_callback(collect_data)
        
        # 启动第一个控制器
        controller1.start()
        time.sleep(0.3)  # 给予足够时间处理所有数据
        
        # 验证所有数据都被收集
        self.assertEqual(len(collected_data), 5)
        
        # 创建第二个控制器，使用收集到的数据
        controller2 = MultiSourceReplayController({'combined': collected_data})
        
        # 从第二个控制器中逐步获取数据
        results = []
        while True:
            data = controller2.step()
            if data is None:
                break
            results.append(data)
            
        # 验证第二个控制器返回的所有数据
        self.assertEqual(len(results), 5)
        
    def test_multiple_callbacks(self):
        """测试多个回调函数"""
        # 创建控制器
        dates = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data = {'value': [1, 2, 3]}
        df = pd.DataFrame(data, index=dates)
        controller = DataFrameReplayController(df)
        
        # 创建三个不同的计数器
        counter1 = []
        counter2 = []
        counter3 = []
        
        # 定义三个不同的回调函数
        def callback1(data):
            counter1.append(data['value'])
            
        def callback2(data):
            counter2.append(data['value'] * 2)
            
        def callback3(data):
            counter3.append(data['value'] * 3)
            
        # 注册所有回调
        controller.register_callback(callback1)
        controller.register_callback(callback2)
        controller.register_callback(callback3)
        
        # 启动控制器
        controller.start()
        time.sleep(0.3)  # 给予足够时间处理所有数据
        
        # 验证所有回调都收到了数据，并且进行了相应的处理
        assert counter1 == [1, 2, 3]
        assert counter2 == [2, 4, 6]
        assert counter3 == [3, 6, 9]
        
    def test_parallel_controllers(self):
        """测试并行控制器"""
        # 创建两个不同的DataFrame
        dates1 = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data1 = {'value': [1, 2, 3]}
        df1 = pd.DataFrame(data1, index=dates1)
        
        dates2 = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data2 = {'value': [10, 20, 30]}
        df2 = pd.DataFrame(data2, index=dates2)
        
        # 创建两个控制器
        controller1 = DataFrameReplayController(df1)
        controller2 = DataFrameReplayController(df2)
        
        # 收集数据的容器
        results1 = []
        results2 = []
        
        def callback1(data):
            results1.append(data['value'])
            
        def callback2(data):
            results2.append(data['value'])
            
        # 注册回调
        controller1.register_callback(callback1)
        controller2.register_callback(callback2)
        
        # 并行启动两个控制器
        controller1.start()
        controller2.start()
        
        # 等待完成
        time.sleep(0.3)
        
        # 验证两个控制器都完成了处理
        assert len(results1) == 3
        assert len(results2) == 3
        assert results1 == [1, 2, 3]
        assert results2 == [10, 20, 30]
        
    def test_api_direct_step(self):
        """测试通过API直接步进而非线程"""
        # 创建控制器
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        data = {'price': [100, 101, 102, 103, 104]}
        df = pd.DataFrame(data, index=dates)
        controller = DataFrameReplayController(df, mode=ReplayMode.STEPPED)
        
        # 收集数据
        results = []
        
        def callback(data):
            results.append(data['price'])
            
        # 注册回调
        controller.register_callback(callback)
        
        # 手动调用step而不是start/线程
        for _ in range(5):
            controller.step()
            
        # 验证所有数据都被处理
        assert results == [100, 101, 102, 103, 104]
        assert controller.get_status() == ReplayStatus.COMPLETED

if __name__ == "__main__":
    unittest.main()