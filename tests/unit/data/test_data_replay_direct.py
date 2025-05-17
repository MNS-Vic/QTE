"""
数据重放控制器直接测试

此测试文件使用直接API调用而不是线程，避免因线程同步导致的测试不稳定问题
"""

import unittest
import pandas as pd
import pytest
from datetime import datetime, timedelta
import time

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

class MockController(BaseDataReplayController):
    """测试用的简单控制器实现，不依赖线程"""
    
    def __init__(self, data=None, mode=ReplayMode.BACKTEST, speed_factor=1.0):
        super().__init__(data_source=data, mode=mode, speed_factor=speed_factor)
        self._test_data = data or [1, 2, 3]
        self._current_index = 0
    
    def _get_next_data_point(self):
        """直接返回下一个数据点，不依赖线程"""
        if self._current_index >= len(self._test_data):
            return None
        data = self._test_data[self._current_index]
        self._current_index += 1
        return data
    
    def start_sync(self):
        """同步启动，不创建线程"""
        # 更新状态但不启动线程
        with self._lock:
            self._status = ReplayStatus.RUNNING
            self._event.set()
        return True
    
    def process_all(self):
        """同步处理所有数据点"""
        results = []
        while True:
            data = self.step()
            if data is None:
                break
            results.append(data)
        return results

class TestReplayControllerDirect:
    """直接测试重放控制器API，不依赖线程"""
    
    def test_basic_controller_api(self):
        """测试基本控制器API"""
        controller = MockController()
        
        # 测试初始状态
        assert controller.get_status() == ReplayStatus.INITIALIZED
        
        # 测试同步启动
        assert controller.start_sync()
        assert controller.get_status() == ReplayStatus.RUNNING
        
        # 测试步进
        data_points = []
        for _ in range(4):  # 应该只有3个数据点加上1个None
            dp = controller.step()
            data_points.append(dp)
            
        # 检查数据点和最终状态
        assert data_points[0:3] == [1, 2, 3]
        assert data_points[3] is None
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 测试重置
        assert controller.reset()
        assert controller.get_status() == ReplayStatus.INITIALIZED
        
        # 重置后再次获取所有数据点
        data2 = controller.process_all()
        assert data2 == [1, 2, 3]
    
    def test_dataframe_controller(self):
        """测试DataFrame控制器"""
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data = {'price': [100, 101, 102], 'volume': [1000, 1100, 1200]}
        df = pd.DataFrame(data, index=dates)
        
        controller = DataFrameReplayController(df)
        
        # 手动调用步进收集数据
        results = []
        for _ in range(4):  # 应该有3个数据点加上1个None
            data = controller.step()
            if data is None:
                break
            results.append((data['price'], data['volume']))
        
        # 验证数据
        expected = [(100, 1000), (101, 1100), (102, 1200)]
        assert results == expected
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 测试重置功能
        assert controller.reset()
        assert controller.get_status() == ReplayStatus.INITIALIZED
        
        # 重置后再次收集数据
        reset_results = []
        for _ in range(4):
            data = controller.step()
            if data is None:
                break
            reset_results.append((data['price'], data['volume']))
            
        assert reset_results == expected
    
    def test_timestamp_column(self):
        """测试时间戳列"""
        # 创建包含时间戳列的DataFrame
        timestamps = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data = {
            'timestamp': timestamps,
            'price': [100, 101, 102]
        }
        df = pd.DataFrame(data)
        
        # 使用时间戳列创建控制器
        controller = DataFrameReplayController(df, timestamp_column='timestamp')
        
        # 手动获取数据点
        d1 = controller.step()
        assert d1['price'] == 100
        assert d1['timestamp'] in [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-01 00:00:00')]
        
        d2 = controller.step()
        assert d2['price'] == 101
        assert d2['timestamp'] in [pd.Timestamp('2023-01-02'), pd.Timestamp('2023-01-02 00:00:00')]
    
    def test_multi_source_controller(self):
        """测试多数据源控制器"""
        # 创建测试数据
        dates1 = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data1 = {'price': [100, 101, 102]}
        df1 = pd.DataFrame(data1, index=dates1)
        
        dates2 = pd.date_range(start='2023-01-01', periods=3, freq='8h')
        data2 = {'volume': [1000, 1100, 1200]}
        df2 = pd.DataFrame(data2, index=dates2)
        
        # 创建控制器
        controller = MultiSourceReplayController({
            'price': df1,
            'volume': df2
        })
        
        # 使用同步API收集所有数据
        results = []
        for _ in range(7):  # 应该有6个数据点和一个None
            data = controller.step_sync()
            if data is None:
                break
            
            # 收集数据点信息
            if 'price' in data:
                results.append(('price', data['price']))
            if 'volume' in data:
                results.append(('volume', data['volume']))
        
        # 验证收集到6个数据点
        assert len(results) == 6
        
        # 验证price和volume的数据点都存在
        price_values = [p for t, p in results if t == 'price']
        volume_values = [v for t, v in results if t == 'volume']
        
        assert set(price_values) == {100, 101, 102}
        assert set(volume_values) == {1000, 1100, 1200}
        
        # 测试重置
        assert controller.reset()
        
        # 重置后再次收集数据 - 使用同步API
        reset_results = []
        for _ in range(7):
            data = controller.step_sync()
            if data is None:
                break
            
            if 'price' in data:
                reset_results.append(('price', data['price']))
            if 'volume' in data:
                reset_results.append(('volume', data['volume']))
        
        # 验证重置后仍能收集到6个数据点
        assert len(reset_results) == 6
    
    def test_callback_mechanism(self):
        """测试回调机制"""
        # 使用简单控制器测试回调
        controller = MockController([10, 20, 30])
        
        # 创建三个独立的回调计数器
        counter1 = []
        counter2 = []
        counter3 = []
        
        # 注册三个回调函数
        controller.register_callback(lambda x: counter1.append(x))
        controller.register_callback(lambda x: counter2.append(x * 2))
        controller.register_callback(lambda x: counter3.append(x * 3))
        
        # 手动调用step处理所有数据
        controller.process_all()
        
        # 验证所有回调都收到了数据
        assert counter1 == [10, 20, 30]
        assert counter2 == [20, 40, 60]
        assert counter3 == [30, 60, 90]
        
    def test_mode_behaviors(self):
        """测试不同模式的行为"""
        # 步进模式测试
        stepped_controller = MockController(mode=ReplayMode.STEPPED)
        stepped_controller.start()
        
        # 启动后，步进模式从step方法中获取数据
        data = stepped_controller.step()
        assert data == 1
        
        # 回测模式测试 - 使用手动API
        backtest_controller = MockController(mode=ReplayMode.BACKTEST)
        results = backtest_controller.process_all()
        assert results == [1, 2, 3]
        assert backtest_controller.get_status() == ReplayStatus.COMPLETED

if __name__ == "__main__":
    pytest.main(["-v", "test_data_replay_direct.py"])