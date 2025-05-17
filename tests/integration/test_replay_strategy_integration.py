"""
数据重放控制器与策略集成测试

测试数据重放控制器与策略引擎的集成功能，确保数据能够正确传递给策略
"""

import unittest
import pandas as pd 
import numpy as np
from datetime import datetime, timedelta

from qte.data.data_replay import (
    ReplayMode,
    ReplayStatus,
    DataFrameReplayController
)

class SimpleStrategy:
    """简单测试策略，用于记录接收到的数据点"""
    
    def __init__(self):
        self.received_data = []
        self.processed_values = []
        
    def on_data(self, data):
        """数据回调处理函数"""
        self.received_data.append(data)
        if 'close' in data:
            self.processed_values.append(data['close'])
            
    def get_positions(self):
        """获取模拟持仓"""
        # 简单策略：当价格高于均值时做多
        if len(self.processed_values) < 2:
            return 0
        
        avg = sum(self.processed_values) / len(self.processed_values)
        last_price = self.processed_values[-1]
        
        return 1 if last_price > avg else -1

class TestReplayStrategyIntegration(unittest.TestCase):
    """测试数据重放控制器与策略的集成"""
    
    def test_strategy_data_flow(self):
        """测试数据流从重放控制器到策略"""
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        data = {
            'open': [100, 101, 99, 102, 104],
            'high': [103, 104, 101, 105, 107],
            'low': [98, 98, 97, 100, 102],
            'close': [101, 102, 98, 104, 105],
            'volume': [1000, 1100, 900, 1200, 1300]
        }
        df = pd.DataFrame(data, index=dates)
        
        # 创建控制器和策略
        controller = DataFrameReplayController(df)
        strategy = SimpleStrategy()
        
        # 连接控制器和策略
        controller.register_callback(strategy.on_data)
        
        # 使用同步API处理所有数据
        controller.process_all_sync()
        
        # 验证策略接收到所有数据点
        self.assertEqual(len(strategy.received_data), 5)
        
        # 验证接收的数据内容
        self.assertEqual(strategy.received_data[0]['close'], 101)
        self.assertEqual(strategy.received_data[-1]['close'], 105)
        
        # 验证策略逻辑
        self.assertEqual(len(strategy.processed_values), 5)
        self.assertEqual(strategy.processed_values, [101, 102, 98, 104, 105])
        
    def test_real_time_execution(self):
        """测试实时模式的执行"""
        # 创建简短的测试数据
        dates = pd.date_range(start='2023-01-01', periods=3, freq='D')
        data = {
            'price': [100, 102, 101]
        }
        df = pd.DataFrame(data, index=dates)
        
        # 创建实时模式控制器，使用超高速因子加速测试
        controller = DataFrameReplayController(df, mode=ReplayMode.REALTIME, speed_factor=1000)
        
        # 记录数据接收时间
        received_times = []
        
        def time_callback(data):
            received_times.append(datetime.now())
        
        # 注册回调
        controller.register_callback(time_callback)
        
        # 处理数据
        controller.process_all_sync()
        
        # 验证收到了所有数据点
        self.assertEqual(len(received_times), 3)
        
    def test_multiple_strategies(self):
        """测试多个策略同时订阅数据"""
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=4, freq='D')
        data = {
            'close': [100, 102, 101, 103]
        }
        df = pd.DataFrame(data, index=dates)
        
        # 创建控制器和多个策略
        controller = DataFrameReplayController(df)
        strategy1 = SimpleStrategy()
        strategy2 = SimpleStrategy()
        
        # 连接控制器和策略
        controller.register_callback(strategy1.on_data)
        controller.register_callback(strategy2.on_data)
        
        # 处理所有数据
        controller.process_all_sync()
        
        # 验证两个策略都接收到所有数据
        self.assertEqual(len(strategy1.received_data), 4)
        self.assertEqual(len(strategy2.received_data), 4)
        
        # 验证数据内容一致
        for i in range(4):
            self.assertEqual(strategy1.received_data[i]['close'], 
                           strategy2.received_data[i]['close'])

if __name__ == '__main__':
    unittest.main()