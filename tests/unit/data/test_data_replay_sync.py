"""
数据重放控制器同步API测试

此测试文件专门测试数据重放控制器的同步API功能，包括step_sync和process_all_sync方法
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

class TestSyncAPI:
    """测试数据重放控制器的同步API功能"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        self.price_data = pd.DataFrame({
            'price': [100, 102, 101, 103, 105],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        # 创建第二个数据源
        self.indicator_data = pd.DataFrame({
            'ma5': [99, 100, 101, 102, 103],
            'rsi': [50, 55, 60, 65, 70]
        }, index=dates)
    
    def test_dataframe_step_sync(self):
        """测试DataFrame控制器的step_sync方法"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 验证初始状态
        assert controller.get_status() == ReplayStatus.INITIALIZED
        
        # 逐步获取数据
        data_points = []
        while True:
            data = controller.step_sync()
            if data is None:
                break
            data_points.append(data)
        
        # 验证获取了所有数据
        assert len(data_points) == 5
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 验证数据内容
        assert data_points[0]['price'] == 100
        assert data_points[-1]['price'] == 105
    
    def test_dataframe_process_all_sync(self):
        """测试DataFrame控制器的process_all_sync方法"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 一次性处理所有数据
        results = controller.process_all_sync()
        
        # 验证获取了所有数据
        assert len(results) == 5
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 验证数据内容
        assert results[0]['price'] == 100
        assert results[-1]['price'] == 105
    
    def test_multisource_step_sync(self):
        """测试多数据源控制器的step_sync方法"""
        # 创建多数据源控制器
        controller = MultiSourceReplayController({
            'price': self.price_data,
            'indicator': self.indicator_data
        })
        
        # 逐步获取数据
        data_points = []
        while True:
            data = controller.step_sync()
            if data is None:
                break
            data_points.append(data)
        
        # 验证获取了所有数据
        assert len(data_points) == 10  # 5个价格数据 + 5个指标数据
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 分离不同数据源的数据
        price_data = [d for d in data_points if d.get('_source') == 'price']
        indicator_data = [d for d in data_points if d.get('_source') == 'indicator']
        
        assert len(price_data) == 5
        assert len(indicator_data) == 5
    
    def test_multisource_process_all_sync(self):
        """测试多数据源控制器的process_all_sync方法"""
        # 创建多数据源控制器
        controller = MultiSourceReplayController({
            'price': self.price_data,
            'indicator': self.indicator_data
        })
        
        # 一次性处理所有数据
        results = controller.process_all_sync()
        
        # 验证获取了所有数据
        assert len(results) == 10  # 5个价格数据 + 5个指标数据
        assert controller.get_status() == ReplayStatus.COMPLETED
        
        # 分离不同数据源的数据
        price_data = [d for d in results if d.get('_source') == 'price']
        indicator_data = [d for d in results if d.get('_source') == 'indicator']
        
        assert len(price_data) == 5
        assert len(indicator_data) == 5
    
    def test_sync_api_with_reset(self):
        """测试重置后使用同步API"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 处理部分数据
        data1 = controller.step_sync()
        data2 = controller.step_sync()
        
        assert data1['price'] == 100
        assert data2['price'] == 102
        
        # 重置控制器
        controller.reset()
        assert controller.get_status() == ReplayStatus.INITIALIZED
        
        # 再次处理所有数据
        results = controller.process_all_sync()
        
        # 验证获取了所有数据
        assert len(results) == 5
        assert results[0]['price'] == 100
    
    def test_sync_api_with_callbacks(self):
        """测试同步API下回调的执行"""
        # 创建控制器
        controller = DataFrameReplayController(self.price_data)
        
        # 创建回调记录
        callback_data = []
        def test_callback(data):
            callback_data.append(data)
        
        # 注册回调
        controller.register_callback(test_callback)
        
        # 使用step_sync逐步处理
        while controller.step_sync() is not None:
            pass
        
        # 验证回调被执行
        assert len(callback_data) == 5
        assert callback_data[0]['price'] == 100
        assert callback_data[-1]['price'] == 105
        
        # 重置并测试process_all_sync
        controller.reset()
        callback_data.clear()
        
        controller.process_all_sync()
        
        # 验证回调被执行
        assert len(callback_data) == 5
    
    def test_sync_api_thread_safety(self):
        """测试同步API的线程安全性"""
        # 创建一个更大的数据集，以便异步处理不会立即完成
        size = 100
        df = pd.DataFrame({
            'price': [100 + i for i in range(size)],
            'volume': [1000 + i * 100 for i in range(size)]
        })
        
        # 创建控制器，使用STEPPED模式避免异步自动完成
        controller = DataFrameReplayController(df, mode=ReplayMode.STEPPED)
        
        # 步进获取第一个数据点
        data1 = controller.step_sync()
        assert data1['price'] == 100
        
        # 在STEPPED模式下启动异步处理（会暂停在第一步）
        controller.start()
        
        # 继续使用同步API
        controller.reset()  # 重置控制器
        
        # 再次获取第一个数据点，此时不应受异步影响
        data1 = controller.step_sync()
        assert data1['price'] == 100
        
        # 获取第二个数据点
        data2 = controller.step_sync()
        assert data2['price'] == 101
        
        # 停止异步处理
        controller.stop()
        
        # 最后验证process_all_sync功能
        controller.reset()
        results = controller.process_all_sync()
        assert len(results) == size
    
    def test_mixed_sync_async_usage(self):
        """测试混合使用同步和异步API"""
        # 创建控制器
        controller = DataFrameReplayController(
            self.price_data,
            mode=ReplayMode.STEPPED
        )
        
        # 记录数据
        all_data = []
        
        # 注册回调
        controller.register_callback(lambda x: all_data.append(x))
        
        # 先使用异步API
        controller.start()
        time.sleep(0.1)  # 给异步处理一些时间
        
        # 停止异步处理
        controller.stop()
        
        # 切换到同步API继续处理
        controller.reset()
        all_data.clear()
        
        results = controller.process_all_sync()
        
        # 验证同步API处理了所有数据
        assert len(results) == 5
        assert len(all_data) == 5
    
    def test_sync_api_performance(self):
        """测试同步API的基本性能"""
        # 创建较大的测试数据
        size = 1000
        df = pd.DataFrame({
            'price': np.random.randn(size),
            'volume': np.random.randint(1000, 10000, size)
        })
        
        # 创建控制器
        controller = DataFrameReplayController(df)
        
        # 计时process_all_sync
        start_time = time.time()
        results = controller.process_all_sync()
        process_all_time = time.time() - start_time
        
        # 重置并计时step_sync
        controller.reset()
        start_time = time.time()
        while controller.step_sync() is not None:
            pass
        step_sync_time = time.time() - start_time
        
        # 验证处理了所有数据
        assert len(results) == size
        
        # 比较两种方法的性能
        # process_all_sync应该略快，但这主要是参考而非严格测试
        print(f"process_all_sync: {process_all_time:.4f}秒, step_sync: {step_sync_time:.4f}秒")


if __name__ == "__main__":
    pytest.main(["-v", "test_data_replay_sync.py"])