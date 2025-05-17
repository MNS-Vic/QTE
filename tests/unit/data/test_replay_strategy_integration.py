"""
数据重放控制器与策略系统集成测试

此文件测试数据重放控制器与策略系统的集成，确保数据能正确传递给策略逻辑
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from qte.data.data_replay import (
    ReplayMode, 
    ReplayStatus, 
    BaseDataReplayController, 
    DataFrameReplayController, 
    MultiSourceReplayController
)

# 模拟策略组件
class MockStrategy:
    """模拟策略，用于测试与数据重放控制器的集成"""
    
    def __init__(self):
        self.received_data = []
        self.processing_complete = False
        self.last_timestamp = None
        
    def on_data(self, data):
        """接收数据的回调方法"""
        self.received_data.append(data)
        
        # 记录时间戳（如果有）
        if isinstance(data, dict) and '_timestamp' in data:
            self.last_timestamp = data['_timestamp']
        elif isinstance(data, pd.Series) and data.index.name == 'timestamp':
            self.last_timestamp = data.name
    
    def on_complete(self):
        """数据处理完成的回调方法"""
        self.processing_complete = True
        
    def reset(self):
        """重置策略状态"""
        self.received_data.clear()
        self.processing_complete = False
        self.last_timestamp = None

class TestStrategyIntegration:
    """测试数据重放控制器与策略的集成"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建模拟策略
        self.strategy = MockStrategy()
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        self.price_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        # 创建第二个数据源
        self.indicator_data = pd.DataFrame({
            'ma5': [101, 102, 103, 104, 105],
            'ma10': [99, 100, 101, 102, 103],
            'rsi': [50, 55, 60, 65, 70]
        }, index=dates)
    
    def test_dataframe_controller_with_strategy(self):
        """测试DataFrame控制器与策略集成"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 使用同步API处理所有数据
        results = controller.process_all_sync()
        
        # 验证策略接收到数据
        assert len(self.strategy.received_data) == 5
        assert self.strategy.received_data[0]['close'] == 102
        assert self.strategy.received_data[-1]['close'] == 106
        
        # 验证时间戳传递
        assert self.strategy.last_timestamp in [self.price_data.index[-1], 
                                               pd.Timestamp('2023-01-05')]
    
    def test_multi_source_controller_with_strategy(self):
        """测试多数据源控制器与策略集成"""
        # 创建多数据源控制器
        controller = MultiSourceReplayController({
            'price': self.price_data,
            'indicator': self.indicator_data
        })
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 使用同步API处理所有数据
        results = controller.process_all_sync()
        
        # 验证策略接收到数据
        assert len(self.strategy.received_data) == 10  # 5个价格数据 + 5个指标数据
        
        # 分离接收到的不同类型的数据
        price_data = [d for d in self.strategy.received_data if d.get('_source') == 'price']
        indicator_data = [d for d in self.strategy.received_data if d.get('_source') == 'indicator']
        
        assert len(price_data) == 5
        assert len(indicator_data) == 5
    
    def test_controller_with_strategy_reset(self):
        """测试控制器重置对策略的影响"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 处理部分数据
        controller.step_sync()
        controller.step_sync()
        
        # 验证策略接收到部分数据
        assert len(self.strategy.received_data) == 2
        
        # 重置控制器和策略
        controller.reset()
        self.strategy.reset()
        
        # 再次处理所有数据
        controller.process_all_sync()
        
        # 验证策略接收到完整数据
        assert len(self.strategy.received_data) == 5
    
    def test_strategy_with_event_notification(self):
        """测试事件通知机制与策略集成"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 注册数据回调和完成回调
        controller.register_callback(self.strategy.on_data)
        
        # 处理所有数据
        controller.process_all_sync()
        
        # 验证数据传递
        assert len(self.strategy.received_data) == 5
        
        # 手动调用完成回调
        self.strategy.on_complete()
        
        # 验证完成状态
        assert self.strategy.processing_complete is True
    
    def test_strategy_with_async_processing(self):
        """测试异步处理与策略集成"""
        # 创建控制器
        controller = DataFrameReplayController(
            self.price_data, 
            mode=ReplayMode.STEPPED
        )
        
        # 注册策略回调
        controller.register_callback(self.strategy.on_data)
        
        # 启动控制器但不等待完成
        controller.start()
        
        # 手动步进3次
        for _ in range(3):
            controller.step()
            time.sleep(0.1)  # 给回调一些执行时间
        
        # 停止控制器
        controller.stop()
        
        # 验证策略接收到部分数据
        assert 1 <= len(self.strategy.received_data) <= 3
        
    def test_multi_strategy_integration(self):
        """测试多策略集成"""
        # 创建两个策略
        strategy1 = MockStrategy()
        strategy2 = MockStrategy()
        
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 注册两个策略回调
        controller.register_callback(strategy1.on_data)
        controller.register_callback(strategy2.on_data)
        
        # 处理所有数据
        controller.process_all_sync()
        
        # 验证两个策略都接收到数据
        assert len(strategy1.received_data) == 5
        assert len(strategy2.received_data) == 5
        
        # 验证数据一致性
        for i in range(5):
            assert strategy1.received_data[i]['close'] == strategy2.received_data[i]['close']


if __name__ == "__main__":
    pytest.main(["-v", "test_replay_strategy_integration.py"]) 