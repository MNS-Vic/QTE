#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据重放控制器与引擎管理器的集成
"""
import unittest
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus, EngineEvent
from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus

class TestReplayEngineIntegration(unittest.TestCase):
    """测试数据重放控制器与引擎管理器的集成"""
    
    def setUp(self):
        """测试前准备工作"""
        # 创建测试数据
        dates = pd.date_range(start=datetime.now(), periods=10, freq='1min')
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.rand(10) * 100,
            'high': np.random.rand(10) * 100 + 10,
            'low': np.random.rand(10) * 80,
            'close': np.random.rand(10) * 90 + 5,
            'volume': np.random.randint(1000, 10000, 10)
        })
        
        # 创建引擎管理器
        self.engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        self.engine_manager.initialize()
        
        # 创建数据重放控制器
        self.replay_controller = DataFrameReplayController(
            dataframe=self.test_data,
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST
        )
        
        # 接收到的事件计数
        self.received_events = 0
        self.events_lock = threading.Lock()
        
    def test_basic_integration(self):
        """测试基本集成功能"""
        # 注册事件处理器
        self.engine_manager.register_event_handler(
            "MARKET_DATA", 
            self._on_market_data
        )
        
        # 添加重放控制器
        result = self.engine_manager.add_replay_controller(
            "test_data", 
            self.replay_controller,
            symbol="TEST"
        )
        self.assertTrue(result, "添加重放控制器失败")
        
        # 启动引擎
        result = self.engine_manager.start()
        self.assertTrue(result, "启动引擎失败")
        
        # 等待数据处理完成
        max_wait = 5  # 最多等待5秒
        wait_time = 0
        check_interval = 0.1
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # 如果接收到所有事件或引擎完成则退出等待
            if self.received_events >= len(self.test_data) or self.engine_manager.get_status() == EngineStatus.COMPLETED:
                break
        
        # 停止引擎
        self.engine_manager.stop()
        
        # 验证是否接收到所有事件
        self.assertEqual(self.received_events, len(self.test_data), 
                          f"接收到 {self.received_events} 个事件，预期 {len(self.test_data)} 个")
    
    def test_callback_with_lambda(self):
        """测试使用lambda回调的正确性"""
        # 使用列表存储接收到的数据
        received_data = []
        
        # 直接向数据重放控制器注册回调
        self.replay_controller.register_callback(
            lambda data: received_data.append(data)
        )
        
        # 启动重放控制器
        self.replay_controller.start()
        
        # 等待重放完成
        max_wait = 5  # 最多等待5秒
        wait_time = 0
        check_interval = 0.1
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            if self.replay_controller.get_status() == ReplayStatus.COMPLETED:
                break
        
        # 停止重放
        self.replay_controller.stop()
        
        # 验证是否接收到所有数据
        self.assertEqual(len(received_data), len(self.test_data), 
                          f"接收到 {len(received_data)} 个数据点，预期 {len(self.test_data)} 个")
    
    def test_multiple_controllers(self):
        """测试多数据源集成"""
        # 创建第二个测试数据集
        dates2 = pd.date_range(start=datetime.now(), periods=5, freq='2min')
        test_data2 = pd.DataFrame({
            'timestamp': dates2,
            'price': np.random.rand(5) * 200,
            'quantity': np.random.randint(100, 500, 5)
        })
        
        # 创建第二个重放控制器
        replay_controller2 = DataFrameReplayController(
            dataframe=test_data2,
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST
        )
        
        # 添加两个重放控制器
        self.engine_manager.add_replay_controller("data1", self.replay_controller, symbol="SYM1")
        self.engine_manager.add_replay_controller("data2", replay_controller2, symbol="SYM2")
        
        # 接收到的数据计数
        received_count = {"data1": 0, "data2": 0}
        
        # 注册事件处理器
        def event_handler(event):
            if event.source == "data1":
                received_count["data1"] += 1
            elif event.source == "data2":
                received_count["data2"] += 1
        
        self.engine_manager.register_event_handler("MARKET_DATA", event_handler)
        
        # 启动引擎
        self.engine_manager.start()
        
        # 等待数据处理完成
        time.sleep(3)
        
        # 停止引擎
        self.engine_manager.stop()
        
        # 验证是否接收到所有事件
        self.assertEqual(received_count["data1"], len(self.test_data), 
                          f"数据源1: 接收到 {received_count['data1']} 个事件，预期 {len(self.test_data)} 个")
        self.assertEqual(received_count["data2"], len(test_data2), 
                          f"数据源2: 接收到 {received_count['data2']} 个事件，预期 {len(test_data2)} 个")
    
    def _on_market_data(self, event):
        """市场数据事件处理函数"""
        with self.events_lock:
            self.received_events += 1

if __name__ == "__main__":
    unittest.main()