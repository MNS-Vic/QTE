"""
数据重放控制器单元测试

测试数据重放控制器的基本功能和边缘情况
"""

import unittest
import time
import threading
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qte.data.data_replay import (
    ReplayMode, ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController,
    MultiSourceReplayController
)

class TestBaseDataReplayController(unittest.TestCase):
    """测试基础数据重放控制器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建一个具体的BaseDataReplayController子类用于测试
        class ConcreteReplayController(BaseDataReplayController):
            def __init__(self, data=None, mode=ReplayMode.BACKTEST, speed_factor=1.0):
                super().__init__(data_source=data, mode=mode, speed_factor=speed_factor)
                self.data = data or []
                self.current_index = 0
                
            def _get_next_data_point(self):
                if self.current_index < len(self.data):
                    data_point = self.data[self.current_index]
                    self.current_index += 1
                    return data_point
                return None
        
        self.test_data = [{'value': i} for i in range(5)]
        self.controller = ConcreteReplayController(data=self.test_data)
    
    def test_initialization(self):
        """测试初始化状态"""
        self.assertEqual(self.controller.get_status(), ReplayStatus.INITIALIZED)
        
    def test_start_stop(self):
        """测试启动和停止"""
        # 启动
        self.controller.start()
        self.assertEqual(self.controller.get_status(), ReplayStatus.RUNNING)
        
        # 等待一小段时间让线程运行
        time.sleep(0.1)
        
        # 停止
        self.controller.stop()
        self.assertEqual(self.controller.get_status(), ReplayStatus.STOPPED)
    
    def test_pause_resume(self):
        """测试暂停和恢复"""
        # 启动
        self.controller.start()
        self.assertEqual(self.controller.get_status(), ReplayStatus.RUNNING)
        
        # 暂停
        self.controller.pause()
        self.assertEqual(self.controller.get_status(), ReplayStatus.PAUSED)
        
        # 恢复
        self.controller.resume()
        self.assertEqual(self.controller.get_status(), ReplayStatus.RUNNING)
        
        # 停止清理
        self.controller.stop()
    
    def test_step(self):
        """测试手动步进"""
        # 确保处于初始状态
        self.assertEqual(self.controller.get_status(), ReplayStatus.INITIALIZED)
        
        # 逐步执行并验证数据
        for i in range(len(self.test_data)):
            data = self.controller.step()
            self.assertEqual(data['value'], i)
        
        # 所有数据处理完毕后应返回None
        data = self.controller.step()
        self.assertIsNone(data)
        self.assertEqual(self.controller.get_status(), ReplayStatus.COMPLETED)
    
    def test_set_mode(self):
        """测试设置模式"""
        # 初始模式应为BACKTEST
        self.assertEqual(self.controller._mode, ReplayMode.BACKTEST)
        
        # 设置为实时模式
        result = self.controller.set_mode(ReplayMode.REALTIME)
        self.assertTrue(result)
        self.assertEqual(self.controller._mode, ReplayMode.REALTIME)
        
        # 启动控制器
        self.controller.start()
        
        # 已启动状态下无法更改模式
        result = self.controller.set_mode(ReplayMode.STEPPED)
        self.assertFalse(result)
        self.assertEqual(self.controller._mode, ReplayMode.REALTIME)
        
        # 停止清理
        self.controller.stop()
    
    def test_set_speed(self):
        """测试设置速度"""
        # 默认速度应为1.0
        self.assertEqual(self.controller._speed_factor, 1.0)
        
        # 设置有效速度
        result = self.controller.set_speed(2.0)
        self.assertTrue(result)
        self.assertEqual(self.controller._speed_factor, 2.0)
        
        # 设置无效速度
        result = self.controller.set_speed(0)
        self.assertFalse(result)
        self.assertEqual(self.controller._speed_factor, 2.0)
        
        result = self.controller.set_speed(-1.0)
        self.assertFalse(result)
        self.assertEqual(self.controller._speed_factor, 2.0)
    
    def test_callbacks(self):
        """测试回调函数机制"""
        # 创建模拟回调
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        # 注册回调
        cb_id1 = self.controller.register_callback(callback1)
        cb_id2 = self.controller.register_callback(callback2)
        
        # 启动重放
        self.controller.start()
        
        # 等待重放完成
        time.sleep(0.2)
        
        # 验证回调被调用
        self.assertEqual(callback1.call_count, len(self.test_data))
        self.assertEqual(callback2.call_count, len(self.test_data))
        
        # 注销第一个回调
        result = self.controller.unregister_callback(cb_id1)
        self.assertTrue(result)
        
        # 重置并再次启动
        self.controller.reset()
        self.controller.start()
        
        # 等待重放完成
        time.sleep(0.2)
        
        # 第一个回调不再增加调用次数，第二个继续增加
        self.assertEqual(callback1.call_count, len(self.test_data))
        self.assertEqual(callback2.call_count, len(self.test_data) * 2)
        
        # 停止清理
        self.controller.stop()
    
    def test_reset(self):
        """测试重置功能"""
        # 启动并运行一段时间
        self.controller.start()
        time.sleep(0.1)
        
        # 重置
        result = self.controller.reset()
        self.assertTrue(result)
        self.assertEqual(self.controller.get_status(), ReplayStatus.INITIALIZED)
        self.assertEqual(self.controller._current_position, 0)
        
        # 确认可以重新启动并处理所有数据
        for i in range(len(self.test_data)):
            data = self.controller.step()
            self.assertEqual(data['value'], i)


class TestDataFrameReplayController(unittest.TestCase):
    """测试基于DataFrame的数据重放控制器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建测试数据，包含时间戳列
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'price': [100, 101, 99, 102, 103],
            'volume': [1000, 1200, 900, 1100, 1300]
        })
        
        # 创建控制器
        self.controller = DataFrameReplayController(
            dataframe=self.df,
            timestamp_column='timestamp'
        )
    
    def test_initialization(self):
        """测试初始化"""
        # 验证DataFrame和时间戳列正确设置
        self.assertEqual(self.controller._df.shape, self.df.shape)
        self.assertEqual(self.controller._timestamp_column, 'timestamp')
        self.assertEqual(self.controller.get_status(), ReplayStatus.INITIALIZED)
    
    def test_step_through_all_data(self):
        """测试逐步处理所有数据"""
        for i in range(len(self.df)):
            data = self.controller.step()
            self.assertIsNotNone(data)
            self.assertEqual(data['price'], self.df.iloc[i]['price'])
            self.assertEqual(data['volume'], self.df.iloc[i]['volume'])
        
        # 所有数据处理完毕后应返回None
        data = self.controller.step()
        self.assertIsNone(data)
        self.assertEqual(self.controller.get_status(), ReplayStatus.COMPLETED)
    
    def test_with_datetime_index(self):
        """测试使用日期时间索引的DataFrame"""
        # 创建以日期为索引的DataFrame
        df_indexed = self.df.set_index('timestamp')
        
        # 创建控制器
        controller = DataFrameReplayController(dataframe=df_indexed)
        
        # 测试步进
        for i in range(len(df_indexed)):
            data = controller.step()
            self.assertIsNotNone(data)
            self.assertEqual(data['price'], df_indexed.iloc[i]['price'])
    
    def test_calculate_delay(self):
        """测试延迟计算功能"""
        # 创建时间间隔更大的DataFrame
        dates = [
            datetime(2023, 1, 1, 10, 0, 0),
            datetime(2023, 1, 1, 10, 0, 10),  # 10秒后
            datetime(2023, 1, 1, 10, 0, 30),  # 再过20秒
        ]
        df = pd.DataFrame({
            'timestamp': dates,
            'value': [1, 2, 3]
        })
        
        controller = DataFrameReplayController(
            dataframe=df,
            timestamp_column='timestamp',
            mode=ReplayMode.REALTIME
        )
        
        # 第一步没有延迟
        data1 = controller.step()
        self.assertEqual(data1['value'], 1)
        
        # 捕获_calculate_delay的调用
        with patch.object(controller, '_calculate_delay', wraps=controller._calculate_delay) as mock_calc:
            data2 = controller.step()
            self.assertEqual(data2['value'], 2)
            # 验证延迟计算被调用，第二个数据点应该计算出约10秒延迟
            mock_calc.assert_called_once()
            delay = mock_calc.return_value
            self.assertAlmostEqual(delay, 10.0, delta=0.1)


class TestMultiSourceReplayController(unittest.TestCase):
    """测试多数据源重放控制器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建两个测试数据源
        dates1 = pd.date_range(start='2023-01-01 10:00:00', periods=3, freq='10S')
        self.df1 = pd.DataFrame({
            'timestamp': dates1,
            'price': [100, 101, 102],
            'source': ['df1'] * 3
        })
        
        dates2 = pd.date_range(start='2023-01-01 10:00:05', periods=3, freq='10S')
        self.df2 = pd.DataFrame({
            'timestamp': dates2,
            'price': [200, 201, 202],
            'source': ['df2'] * 3
        })
        
        # 创建控制器
        self.controller = MultiSourceReplayController(
            data_sources={'df1': self.df1, 'df2': self.df2},
            timestamp_extractors={'df1': lambda x: x['timestamp'], 'df2': lambda x: x['timestamp']}
        )
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.controller._data_sources), 2)
        self.assertEqual(len(self.controller._iterators), 2)
        self.assertEqual(len(self.controller._current_data_points), 2)
        self.assertEqual(self.controller.get_status(), ReplayStatus.INITIALIZED)
    
    def test_timestamp_order(self):
        """测试数据点按时间戳顺序处理"""
        # 预期的处理顺序：df1[0], df2[0], df1[1], df2[1], df1[2], df2[2]
        expected_sources = ['df1', 'df2', 'df1', 'df2', 'df1', 'df2']
        expected_prices = [100, 200, 101, 201, 102, 202]
        
        for i in range(6):  # 两个数据源各3个点
            data = self.controller.step()
            self.assertIsNotNone(data)
            self.assertEqual(data['_source'], expected_sources[i])
            self.assertEqual(data['price'], expected_prices[i])
        
        # 所有数据处理完毕后应返回None
        data = self.controller.step()
        self.assertIsNone(data)
        self.assertEqual(self.controller.get_status(), ReplayStatus.COMPLETED)
    
    def test_uneven_data_sources(self):
        """测试数据源长度不一致的情况"""
        # 创建不等长的数据源
        dates1 = pd.date_range(start='2023-01-01 10:00:00', periods=2, freq='10S')
        df1 = pd.DataFrame({
            'timestamp': dates1,
            'price': [100, 101],
            'source': ['df1'] * 2
        })
        
        dates2 = pd.date_range(start='2023-01-01 10:00:05', periods=4, freq='10S')
        df2 = pd.DataFrame({
            'timestamp': dates2,
            'price': [200, 201, 202, 203],
            'source': ['df2'] * 4
        })
        
        controller = MultiSourceReplayController(
            data_sources={'df1': df1, 'df2': df2},
            timestamp_extractors={'df1': lambda x: x['timestamp'], 'df2': lambda x: x['timestamp']}
        )
        
        # 应该按时间顺序处理完所有数据点
        expected_sources = ['df1', 'df2', 'df1', 'df2', 'df2', 'df2']
        expected_prices = [100, 200, 101, 201, 202, 203]
        
        for i in range(6):
            data = controller.step()
            self.assertIsNotNone(data)
            self.assertEqual(data['_source'], expected_sources[i])
            self.assertEqual(data['price'], expected_prices[i])
        
        # 所有数据处理完毕后应返回None
        data = controller.step()
        self.assertIsNone(data)
    
    def test_timestamp_extraction_fallback(self):
        """测试时间戳提取的备选方案"""
        # 创建没有明确时间戳列的DataFrame，但有日期时间索引
        df1 = self.df1.set_index('timestamp')
        df2 = self.df2.set_index('timestamp')
        
        # 不提供时间戳提取器
        controller = MultiSourceReplayController(
            data_sources={'df1': df1, 'df2': df2}
        )
        
        # 尝试处理第一个数据点
        data = controller.step()
        self.assertIsNotNone(data)
        # 应该根据索引找到时间戳并正确排序
        # 第一个应该是df1的第一条记录
        self.assertEqual(data['price'], 100)
    
    def test_missing_timestamps(self):
        """测试缺失时间戳的情况"""
        # 创建没有时间戳的DataFrame
        df1 = pd.DataFrame({
            'price': [100, 101, 102],
            'source': ['df1'] * 3
        })
        
        df2 = pd.DataFrame({
            'price': [200, 201, 202],
            'source': ['df2'] * 3
        })
        
        controller = MultiSourceReplayController(
            data_sources={'df1': df1, 'df2': df2}
        )
        
        # 应该仍然能处理数据，但可能顺序不一定按时间
        data_points = []
        for _ in range(6):
            data = controller.step()
            self.assertIsNotNone(data)
            data_points.append(data['price'])
        
        # 确认所有数据点都被处理
        self.assertCountEqual(data_points, [100, 101, 102, 200, 201, 202])


if __name__ == '__main__':
    unittest.main() 