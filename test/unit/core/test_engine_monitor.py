#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试引擎监控系统的功能
"""

import os
import sys
import time
import unittest
import threading
from enum import Enum
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入被测试的模块
from test.unit.core.engine_monitor import (
    EngineMonitor, 
    MonitorConfig, 
    HealthStatus,
    ResourceType
)

# 模拟引擎状态和重放状态
class MockEngineStatus(Enum):
    INITIALIZED = 1
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4
    COMPLETED = 5
    ERROR = 6

class MockReplayStatus(Enum):
    INITIALIZED = 1
    RUNNING = 2
    PAUSED = 3
    STOPPED = 4
    COMPLETED = 5

class MockEngine:
    """模拟引擎管理器"""
    
    def __init__(self):
        self.status = MockEngineStatus.INITIALIZED
        self.replay_speed = 1.0
        self.start_called = False
        self.stop_called = False
    
    def get_status(self):
        return self.status
    
    def get_performance_stats(self):
        return {
            'event_count': 100,
            'queue_size': 20,
            'processing_time': 0.05
        }
    
    def start(self):
        self.start_called = True
        self.status = MockEngineStatus.RUNNING
        return True
    
    def stop(self):
        self.stop_called = True
        self.status = MockEngineStatus.STOPPED
        return True
    
    def set_replay_speed(self, speed):
        self.replay_speed = speed
        return True

class MockController:
    """模拟数据重放控制器"""
    
    def __init__(self, name):
        self.name = name
        self.status = MockReplayStatus.INITIALIZED
        self.last_activity_time = time.time()
        self.callback_errors = 0
        self.pause_called = False
        self.resume_called = False
    
    def get_status(self):
        return self.status
    
    def get_health_stats(self):
        return {
            'last_activity_time': self.last_activity_time,
            'idle_time': time.time() - self.last_activity_time,
            'callback_errors': self.callback_errors,
            'data_points_processed': 500
        }
    
    def pause(self):
        self.pause_called = True
        self.status = MockReplayStatus.PAUSED
        return True
    
    def resume(self):
        self.resume_called = True
        self.status = MockReplayStatus.RUNNING
        return True

class TestEngineMonitor(unittest.TestCase):
    """测试引擎监控系统"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建一个自定义配置，使用较短的间隔以加速测试
        config = MonitorConfig()
        config.interval = 0.1  # 每0.1秒检查一次
        config.thread_stall_timeout = 0.5  # 0.5秒无活动视为停滞
        config.callback_error_threshold = 3  # 3个回调错误触发警告
        
        # 使用这个配置创建监控器
        self.monitor = EngineMonitor(config)
        
        # 创建模拟对象
        self.engine = MockEngine()
        self.controller1 = MockController("controller1")
        self.controller2 = MockController("controller2")
        
        # 注册模拟对象
        self.monitor.register_engine_manager(self.engine)
        self.monitor.register_replay_controller("controller1", self.controller1)
        self.monitor.register_replay_controller("controller2", self.controller2)
        
        # 记录回调调用
        self.status_calls = []
        self.alert_calls = []
        
        # 注册回调
        self.monitor.register_status_callback(
            lambda status, details: self.status_calls.append((status, details))
        )
        self.monitor.register_alert_callback(
            lambda msg, details: self.alert_calls.append((msg, details))
        )
    
    def tearDown(self):
        """每个测试后的清理"""
        # 确保停止监控
        if hasattr(self, 'monitor'):
            self.monitor.stop_monitoring()
    
    def test_basic_monitoring(self):
        """测试基本监控功能"""
        # 启动监控
        self.assertTrue(self.monitor.start_monitoring())
        
        # 运行几个周期
        time.sleep(0.5)
        
        # 停止监控
        self.assertTrue(self.monitor.stop_monitoring())
        
        # 验证收集了健康数据
        status, details = self.monitor.get_health_status()
        self.assertIsInstance(status, HealthStatus)
        self.assertIn('resources', details)
        self.assertIn('timestamp', details)
        
        # 验证资源数据已收集
        resources = self.monitor.get_resource_usage()
        self.assertIn(ResourceType.CPU, resources)
        self.assertIn(ResourceType.MEMORY, resources)
        
        # 验证健康趋势数据已生成
        trend_data = self.monitor.get_health_trend()
        self.assertGreater(len(trend_data), 0)
        
        # 验证回调被触发
        self.assertGreater(len(self.status_calls), 0)
    
    def test_engine_error_detection(self):
        """测试引擎错误检测"""
        # 启动监控
        self.monitor.start_monitoring()
        
        # 将引擎状态设置为错误
        self.engine.status = MockEngineStatus.ERROR
        
        # 等待几个监控周期
        time.sleep(0.5)
        
        # 获取最新状态
        status, details = self.monitor.get_health_status()
        
        # 验证检测到了错误状态
        self.assertEqual(status, HealthStatus.CRITICAL)
        self.assertTrue(any("引擎处于错误状态" in issue for issue in details.get('issues', [])))
        
        # 验证发送了警报
        self.assertTrue(any("引擎处于错误状态" in msg for msg, _ in self.alert_calls))
    
    def test_controller_stall_detection(self):
        """测试控制器停滞检测"""
        # 设置控制器状态为运行中
        self.controller1.status = MockReplayStatus.RUNNING
        # 设置最后活动时间为1分钟前（远超过超时阈值）
        self.controller1.last_activity_time = time.time() - 60
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 等待几个监控周期
        time.sleep(0.5)
        
        # 获取最新状态
        status, details = self.monitor.get_health_status()
        
        # 验证检测到了控制器停滞
        self.assertIn(HealthStatus.WARNING, [status, HealthStatus.CRITICAL])  # 可能是WARNING或CRITICAL
        self.assertTrue(any("可能已停滞" in issue and "controller1" in issue for issue in details.get('issues', [])))
    
    def test_callback_error_detection(self):
        """测试回调错误检测"""
        # 设置控制器回调错误数量
        self.controller2.callback_errors = 10  # 超过阈值
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 等待几个监控周期
        time.sleep(0.5)
        
        # 获取最新状态
        status, details = self.monitor.get_health_status()
        
        # 验证检测到了回调错误
        self.assertIn(HealthStatus.WARNING, [status, HealthStatus.CRITICAL])  # 可能是WARNING或CRITICAL
        self.assertTrue(any("回调错误过多" in issue and "controller2" in issue for issue in details.get('issues', [])))
    
    def test_auto_recovery(self):
        """测试自动恢复功能"""
        # 启用自动恢复
        self.monitor.config.auto_recovery = True
        
        # 设置控制器状态为运行中但已停滞
        self.controller1.status = MockReplayStatus.RUNNING
        self.controller1.last_activity_time = time.time() - 60
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 等待足够长的时间以触发恢复操作
        time.sleep(1.0)
        
        # 验证恢复操作已执行
        self.assertTrue(self.controller1.pause_called)
        self.assertTrue(self.controller1.resume_called)
    
    def test_engine_restart_recovery(self):
        """测试引擎重启恢复功能"""
        # 启用自动恢复
        self.monitor.config.auto_recovery = True
        
        # 设置引擎状态为错误
        self.engine.status = MockEngineStatus.ERROR
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 等待足够长的时间以触发恢复操作
        time.sleep(1.0)
        
        # 验证引擎重启操作已执行
        self.assertTrue(self.engine.stop_called)
        self.assertTrue(self.engine.start_called)

if __name__ == "__main__":
    unittest.main() 