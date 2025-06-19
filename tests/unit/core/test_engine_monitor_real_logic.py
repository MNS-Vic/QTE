"""
Engine Monitor真实逻辑测试
专注于测试真实的业务逻辑路径，减少Mock使用，提升覆盖率
"""

import time
import threading
from datetime import datetime
from unittest.mock import Mock

from qte.core.engine_monitor import EngineMonitor


class TestEngineMonitorRealLogic:
    """Engine Monitor真实逻辑测试"""
    
    def test_engine_monitor_initialization(self):
        """测试EngineMonitor的初始化"""
        monitor = EngineMonitor()
        
        # 验证初始状态
        assert monitor.is_monitoring == False
        assert len(monitor.engines) == 0
        assert len(monitor.metrics) == 0
        assert monitor.update_interval > 0
        
        # 测试带参数的初始化
        monitor_with_params = EngineMonitor(update_interval=5.0)
        assert monitor_with_params.update_interval == 5.0
    
    def test_engine_monitor_engine_registration(self):
        """测试EngineMonitor的引擎注册"""
        monitor = EngineMonitor()
        
        # 创建模拟引擎
        mock_engine1 = Mock()
        mock_engine1.name = "TestEngine1"
        mock_engine1.get_status.return_value = "RUNNING"
        mock_engine1.get_metrics.return_value = {"processed_events": 100}
        
        mock_engine2 = Mock()
        mock_engine2.name = "TestEngine2"
        mock_engine2.get_status.return_value = "STOPPED"
        mock_engine2.get_metrics.return_value = {"processed_events": 50}
        
        # 注册引擎
        monitor.register_engine("engine1", mock_engine1)
        monitor.register_engine("engine2", mock_engine2)
        
        # 验证引擎注册
        assert len(monitor.engines) == 2
        assert "engine1" in monitor.engines
        assert "engine2" in monitor.engines
        assert monitor.engines["engine1"] == mock_engine1
        assert monitor.engines["engine2"] == mock_engine2
    
    def test_engine_monitor_engine_unregistration(self):
        """测试EngineMonitor的引擎注销"""
        monitor = EngineMonitor()
        
        # 注册引擎
        mock_engine = Mock()
        mock_engine.name = "TestEngine"
        monitor.register_engine("test_engine", mock_engine)
        
        # 验证注册
        assert len(monitor.engines) == 1
        assert "test_engine" in monitor.engines
        
        # 注销引擎
        monitor.unregister_engine("test_engine")
        
        # 验证注销
        assert len(monitor.engines) == 0
        assert "test_engine" not in monitor.engines
        
        # 测试注销不存在的引擎（应该不报错）
        monitor.unregister_engine("nonexistent_engine")
        assert len(monitor.engines) == 0
    
    def test_engine_monitor_metrics_collection(self):
        """测试EngineMonitor的指标收集"""
        monitor = EngineMonitor()
        
        # 创建模拟引擎
        mock_engine = Mock()
        mock_engine.name = "TestEngine"
        mock_engine.get_status.return_value = "RUNNING"
        mock_engine.get_metrics.return_value = {
            "processed_events": 150,
            "events_per_second": 10.5,
            "memory_usage": 256.7,
            "cpu_usage": 45.2
        }
        
        monitor.register_engine("test_engine", mock_engine)
        
        # 收集指标
        monitor.collect_metrics()
        
        # 验证指标收集
        assert len(monitor.metrics) > 0
        assert "test_engine" in monitor.metrics
        
        engine_metrics = monitor.metrics["test_engine"]
        assert "processed_events" in engine_metrics
        assert "events_per_second" in engine_metrics
        assert "memory_usage" in engine_metrics
        assert "cpu_usage" in engine_metrics
        assert "timestamp" in engine_metrics
        
        # 验证指标值
        assert engine_metrics["processed_events"] == 150
        assert engine_metrics["events_per_second"] == 10.5
        assert engine_metrics["memory_usage"] == 256.7
        assert engine_metrics["cpu_usage"] == 45.2
    
    def test_engine_monitor_health_check(self):
        """测试EngineMonitor的健康检查"""
        monitor = EngineMonitor()
        
        # 创建健康的引擎
        healthy_engine = Mock()
        healthy_engine.name = "HealthyEngine"
        healthy_engine.get_status.return_value = "RUNNING"
        healthy_engine.get_metrics.return_value = {
            "processed_events": 100,
            "events_per_second": 15.0,
            "memory_usage": 128.0,
            "cpu_usage": 30.0
        }
        healthy_engine.is_healthy.return_value = True
        
        # 创建不健康的引擎
        unhealthy_engine = Mock()
        unhealthy_engine.name = "UnhealthyEngine"
        unhealthy_engine.get_status.return_value = "ERROR"
        unhealthy_engine.get_metrics.return_value = {
            "processed_events": 0,
            "events_per_second": 0.0,
            "memory_usage": 512.0,
            "cpu_usage": 95.0
        }
        unhealthy_engine.is_healthy.return_value = False
        
        monitor.register_engine("healthy", healthy_engine)
        monitor.register_engine("unhealthy", unhealthy_engine)
        
        # 执行健康检查
        health_report = monitor.check_health()
        
        # 验证健康检查结果
        assert isinstance(health_report, dict)
        assert "healthy" in health_report
        assert "unhealthy" in health_report
        
        assert health_report["healthy"]["status"] == "RUNNING"
        assert health_report["healthy"]["is_healthy"] == True
        
        assert health_report["unhealthy"]["status"] == "ERROR"
        assert health_report["unhealthy"]["is_healthy"] == False
    
    def test_engine_monitor_alert_system(self):
        """测试EngineMonitor的告警系统"""
        monitor = EngineMonitor()
        
        # 设置告警阈值
        monitor.set_alert_thresholds({
            "cpu_usage": 80.0,
            "memory_usage": 400.0,
            "events_per_second": 5.0
        })
        
        # 创建触发告警的引擎
        alert_engine = Mock()
        alert_engine.name = "AlertEngine"
        alert_engine.get_status.return_value = "RUNNING"
        alert_engine.get_metrics.return_value = {
            "processed_events": 50,
            "events_per_second": 2.0,  # 低于阈值
            "memory_usage": 450.0,     # 高于阈值
            "cpu_usage": 85.0          # 高于阈值
        }
        
        monitor.register_engine("alert_engine", alert_engine)
        
        # 收集指标并检查告警
        monitor.collect_metrics()
        alerts = monitor.check_alerts()
        
        # 验证告警
        assert len(alerts) > 0
        assert "alert_engine" in alerts
        
        engine_alerts = alerts["alert_engine"]
        assert any("cpu_usage" in alert for alert in engine_alerts)
        assert any("memory_usage" in alert for alert in engine_alerts)
        assert any("events_per_second" in alert for alert in engine_alerts)
    
    def test_engine_monitor_start_stop(self):
        """测试EngineMonitor的启动和停止"""
        monitor = EngineMonitor(update_interval=0.1)  # 快速更新用于测试
        
        # 创建模拟引擎
        mock_engine = Mock()
        mock_engine.name = "TestEngine"
        mock_engine.get_status.return_value = "RUNNING"
        mock_engine.get_metrics.return_value = {"processed_events": 10}
        
        monitor.register_engine("test_engine", mock_engine)
        
        # 启动监控
        monitor.start()
        assert monitor.is_monitoring == True
        
        # 等待一段时间让监控运行
        time.sleep(0.3)
        
        # 停止监控
        monitor.stop()
        assert monitor.is_monitoring == False
        
        # 验证指标被收集
        assert len(monitor.metrics) > 0
        assert "test_engine" in monitor.metrics
    
    def test_engine_monitor_performance_tracking(self):
        """测试EngineMonitor的性能跟踪"""
        monitor = EngineMonitor()
        
        # 创建模拟引擎
        mock_engine = Mock()
        mock_engine.name = "PerfEngine"
        mock_engine.get_status.return_value = "RUNNING"
        
        # 模拟性能变化
        performance_data = [
            {"processed_events": 100, "events_per_second": 10.0},
            {"processed_events": 220, "events_per_second": 12.0},
            {"processed_events": 350, "events_per_second": 13.0},
            {"processed_events": 480, "events_per_second": 13.0},
            {"processed_events": 620, "events_per_second": 14.0}
        ]
        
        mock_engine.get_metrics.side_effect = performance_data
        monitor.register_engine("perf_engine", mock_engine)
        
        # 收集多次指标
        for _ in range(5):
            monitor.collect_metrics()
            time.sleep(0.01)  # 短暂延迟
        
        # 获取性能趋势
        trends = monitor.get_performance_trends("perf_engine")
        
        # 验证性能趋势
        assert isinstance(trends, dict)
        assert "events_per_second" in trends
        assert len(trends["events_per_second"]) == 5
        
        # 验证趋势数据
        eps_trend = trends["events_per_second"]
        assert eps_trend[0] == 10.0
        assert eps_trend[-1] == 14.0
    
    def test_engine_monitor_resource_usage(self):
        """测试EngineMonitor的资源使用监控"""
        monitor = EngineMonitor()
        
        # 创建模拟引擎
        mock_engine = Mock()
        mock_engine.name = "ResourceEngine"
        mock_engine.get_status.return_value = "RUNNING"
        mock_engine.get_metrics.return_value = {
            "processed_events": 1000,
            "events_per_second": 25.0,
            "memory_usage": 256.5,
            "cpu_usage": 45.8,
            "disk_usage": 1024.0,
            "network_io": 512.0
        }
        
        monitor.register_engine("resource_engine", mock_engine)
        
        # 收集资源使用指标
        monitor.collect_metrics()
        
        # 获取资源使用报告
        resource_report = monitor.get_resource_usage()
        
        # 验证资源使用报告
        assert isinstance(resource_report, dict)
        assert "resource_engine" in resource_report
        
        engine_resources = resource_report["resource_engine"]
        assert "memory_usage" in engine_resources
        assert "cpu_usage" in engine_resources
        assert "disk_usage" in engine_resources
        assert "network_io" in engine_resources
        
        # 验证资源值
        assert engine_resources["memory_usage"] == 256.5
        assert engine_resources["cpu_usage"] == 45.8
        assert engine_resources["disk_usage"] == 1024.0
        assert engine_resources["network_io"] == 512.0
    
    def test_engine_monitor_concurrent_access(self):
        """测试EngineMonitor的并发访问"""
        monitor = EngineMonitor()
        
        # 创建多个模拟引擎
        engines = []
        for i in range(5):
            mock_engine = Mock()
            mock_engine.name = f"Engine{i}"
            mock_engine.get_status.return_value = "RUNNING"
            mock_engine.get_metrics.return_value = {
                "processed_events": i * 100,
                "events_per_second": i * 5.0
            }
            engines.append(mock_engine)
            monitor.register_engine(f"engine{i}", mock_engine)
        
        # 创建多个线程同时收集指标
        threads = []
        for i in range(3):
            thread = threading.Thread(target=monitor.collect_metrics)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证并发访问结果
        assert len(monitor.metrics) == 5
        for i in range(5):
            assert f"engine{i}" in monitor.metrics
            engine_metrics = monitor.metrics[f"engine{i}"]
            assert "processed_events" in engine_metrics
            assert "events_per_second" in engine_metrics
