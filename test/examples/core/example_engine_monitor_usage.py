#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎监控系统使用示例

演示如何在实际应用中使用引擎监控系统，包括：
1. 基本监控设置
2. 自动恢复配置
3. 警报系统集成
4. 性能数据可视化
"""

import os
import sys
import time
import logging
import threading
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EngineMonitorExample")

# 导入引擎监控系统
from test.unit.core.engine_monitor import EngineMonitor, MonitorConfig, HealthStatus

# 导入核心组件（如果可用）
try:
    from qte.core.engine_manager import ReplayEngineManager, EngineType
    from qte.data.data_replay import (
        DataFrameReplayController, 
        MultiSourceReplayController,
        ReplayMode
    )
    
    USING_REAL_COMPONENTS = True
except ImportError:
    logger.warning("无法导入实际组件，将使用模拟组件进行演示")
    USING_REAL_COMPONENTS = False
    
    # 导入模拟组件
    from test.unit.core.test_engine_monitor import MockEngine, MockController

def create_demo_data():
    """创建演示数据"""
    # 创建两个不同的价格数据集
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='1min')
    
    # 股票A数据
    df_a = pd.DataFrame({
        'timestamp': dates,
        'open': 100 + 0.1 * (dates.dayofyear - dates[0].dayofyear) + 2 * pd.np.random.randn(len(dates)),
        'high': 0,
        'low': 0,
        'close': 0,
        'volume': 10000 + 5000 * pd.np.random.rand(len(dates))
    })
    df_a['high'] = df_a['open'] + 0.5 + 0.5 * pd.np.random.rand(len(dates))
    df_a['low'] = df_a['open'] - 0.5 - 0.5 * pd.np.random.rand(len(dates))
    df_a['close'] = df_a['low'] + (df_a['high'] - df_a['low']) * pd.np.random.rand(len(dates))
    
    # 股票B数据
    df_b = pd.DataFrame({
        'timestamp': dates,
        'open': 50 - 0.05 * (dates.dayofyear - dates[0].dayofyear) + 1.5 * pd.np.random.randn(len(dates)),
        'high': 0,
        'low': 0,
        'close': 0,
        'volume': 5000 + 2500 * pd.np.random.rand(len(dates))
    })
    df_b['high'] = df_b['open'] + 0.3 + 0.3 * pd.np.random.rand(len(dates))
    df_b['low'] = df_b['open'] - 0.3 - 0.3 * pd.np.random.rand(len(dates))
    df_b['close'] = df_b['low'] + (df_b['high'] - df_b['low']) * pd.np.random.rand(len(dates))
    
    return df_a, df_b

def setup_with_real_components():
    """使用实际组件设置引擎监控系统"""
    logger.info("使用实际组件设置引擎监控系统")
    
    # 创建演示数据
    df_a, df_b = create_demo_data()
    
    # 创建重放控制器
    controller_a = DataFrameReplayController(
        dataframe=df_a,
        timestamp_column='timestamp',
        mode=ReplayMode.ACCELERATED,
        speed_factor=10.0  # 10倍速
    )
    
    controller_b = DataFrameReplayController(
        dataframe=df_b,
        timestamp_column='timestamp',
        mode=ReplayMode.ACCELERATED,
        speed_factor=10.0  # 10倍速
    )
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(engine_type=EngineType.VECTORIZED)
    
    # 添加重放控制器到引擎管理器
    engine_manager.add_replay_controller("stock_a", controller_a, symbol="STOCK_A")
    engine_manager.add_replay_controller("stock_b", controller_b, symbol="STOCK_B")
    
    # 初始化引擎管理器
    engine_manager.initialize()
    
    # 创建监控配置
    config = MonitorConfig()
    config.interval = 0.5  # 每0.5秒检查一次
    config.auto_recovery = True  # 启用自动恢复
    config.enable_alerts = True  # 启用警报
    
    # 创建引擎监控系统
    monitor = EngineMonitor(config)
    
    # 注册被监控的组件
    monitor.register_engine_manager(engine_manager)
    monitor.register_replay_controller("stock_a", controller_a)
    monitor.register_replay_controller("stock_b", controller_b)
    
    return engine_manager, monitor

def setup_with_mock_components():
    """使用模拟组件设置引擎监控系统"""
    logger.info("使用模拟组件设置引擎监控系统")
    
    # 创建模拟引擎
    engine = MockEngine()
    
    # 创建模拟控制器
    controller_a = MockController("stock_a")
    controller_b = MockController("stock_b")
    
    # 创建监控配置
    config = MonitorConfig()
    config.interval = 0.5  # 每0.5秒检查一次
    config.auto_recovery = True  # 启用自动恢复
    config.enable_alerts = True  # 启用警报
    
    # 创建引擎监控系统
    monitor = EngineMonitor(config)
    
    # 注册被监控的组件
    monitor.register_engine_manager(engine)
    monitor.register_replay_controller("stock_a", controller_a)
    monitor.register_replay_controller("stock_b", controller_b)
    
    return engine, monitor

def setup_alert_system(monitor):
    """设置警报系统"""
    logger.info("设置警报系统")
    
    # 创建警报日志文件
    alert_log_file = os.path.join(project_root, "test", "examples", "core", "engine_alerts.log")
    alert_handler = logging.FileHandler(alert_log_file, mode='w')
    alert_handler.setFormatter(logging.Formatter('%(asctime)s - ALERT - %(message)s'))
    
    alert_logger = logging.getLogger("EngineAlerts")
    alert_logger.addHandler(alert_handler)
    alert_logger.setLevel(logging.WARNING)
    
    # 注册警报回调
    def on_alert(message, details):
        alert_logger.warning(message)
        
        # 在这里可以添加更多警报渠道，如：
        # - 发送邮件
        # - 发送短信
        # - 推送到监控平台
        # - 触发声音警报
        # - 更新UI状态
        
        issues = details.get('issues', [])
        if issues and any("停滞" in issue for issue in issues):
            logger.warning("检测到停滞问题，可能需要人工干预")
    
    monitor.register_alert_callback(on_alert)
    logger.info(f"警报将记录到: {alert_log_file}")
    
    return alert_logger

def visualize_health_trend(monitor):
    """可视化健康趋势"""
    # 获取健康趋势数据
    trend_data = monitor.get_health_trend(hours=1)
    
    if len(trend_data) == 0:
        logger.warning("没有足够的健康数据进行可视化")
        return None
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制健康状态
    status_map = {
        'EXCELLENT': 1,
        'GOOD': 2,
        'FAIR': 3,
        'WARNING': 4,
        'CRITICAL': 5
    }
    
    if 'status' in trend_data.columns:
        status_values = trend_data['status'].map(status_map)
        plt.subplot(3, 1, 1)
        plt.title('系统健康状态')
        plt.plot(trend_data.index, status_values, 'o-', label='健康状态')
        plt.yticks(list(status_map.values()), list(status_map.keys()))
        plt.grid(True)
        plt.legend()
    
    # 绘制CPU使用率
    cpu_cols = [col for col in trend_data.columns if 'cpu_usage' in col]
    if cpu_cols:
        plt.subplot(3, 1, 2)
        plt.title('CPU使用率')
        for col in cpu_cols:
            plt.plot(trend_data.index, trend_data[col], label=col)
        plt.grid(True)
        plt.legend()
    
    # 绘制内存使用率
    mem_cols = [col for col in trend_data.columns if 'memory_usage' in col]
    if mem_cols:
        plt.subplot(3, 1, 3)
        plt.title('内存使用率')
        for col in mem_cols:
            plt.plot(trend_data.index, trend_data[col], label=col)
        plt.grid(True)
        plt.legend()
    
    plt.tight_layout()
    
    # 保存图表
    plot_file = os.path.join(project_root, "test", "examples", "core", "health_trend.png")
    plt.savefig(plot_file)
    plt.close()
    
    logger.info(f"健康趋势图已保存到: {plot_file}")
    return plot_file

def simulate_abnormal_conditions(engine, controllers=None):
    """模拟异常情况"""
    if not controllers:
        controllers = {}
    
    logger.info("模拟异常情况...")
    
    # 模拟一个控制器停滞
    if "stock_a" in controllers:
        logger.info("模拟控制器 'stock_a' 停滞")
        controller = controllers["stock_a"]
        
        if hasattr(controller, 'last_activity_time'):
            # 设置最后活动时间为10分钟前
            controller.last_activity_time = time.time() - 600
    
    # 模拟引擎错误
    if USING_REAL_COMPONENTS:
        logger.info("无法直接模拟实际引擎的错误状态，跳过")
    else:
        logger.info("模拟引擎错误状态")
        engine.status = MockEngineStatus.ERROR
    
    # 模拟回调错误
    if "stock_b" in controllers:
        logger.info("模拟控制器 'stock_b' 回调错误")
        controller = controllers["stock_b"]
        
        if hasattr(controller, 'callback_errors'):
            controller.callback_errors = 10

def run_example():
    """运行示例"""
    logger.info("启动引擎监控系统示例")
    
    # 根据可用组件设置监控
    if USING_REAL_COMPONENTS:
        engine, monitor = setup_with_real_components()
        controllers = {
            "stock_a": engine._replay_controllers.get("stock_a"),
            "stock_b": engine._replay_controllers.get("stock_b")
        }
    else:
        engine, monitor = setup_with_mock_components()
        controllers = {
            "stock_a": monitor._replay_controllers.get("stock_a"),
            "stock_b": monitor._replay_controllers.get("stock_b")
        }
    
    # 设置警报系统
    alert_logger = setup_alert_system(monitor)
    
    # 定义状态回调
    def status_callback(status, details):
        status_name = status.name
        issues = details.get('issues', [])
        issue_count = len(issues)
        
        logger.info(f"状态更新: {status_name}, 问题数: {issue_count}")
        
        # 打印重要资源使用情况
        resources = details.get('resources', {})
        for resource_type, metrics in resources.items():
            if resource_type.name in ['CPU', 'MEMORY']:
                logger.info(f"资源 {resource_type.name}: {metrics}")
    
    # 注册状态回调
    monitor.register_status_callback(status_callback)
    
    # 启动监控
    logger.info("启动监控")
    monitor.start_monitoring()
    
    # 如果使用实际组件，启动引擎
    if USING_REAL_COMPONENTS:
        logger.info("启动引擎")
        engine.start()
    
    # 运行一段时间，收集正常数据
    logger.info("收集正常运行数据...")
    time.sleep(5)
    
    # 可视化初始健康趋势
    visualize_health_trend(monitor)
    
    # 模拟异常情况
    simulate_abnormal_conditions(engine, controllers)
    
    # 再运行一段时间，让监控系统检测并处理异常
    logger.info("等待异常检测和处理...")
    time.sleep(5)
    
    # 可视化异常后的健康趋势
    visualize_health_trend(monitor)
    
    # 如果使用实际组件，停止引擎
    if USING_REAL_COMPONENTS:
        logger.info("停止引擎")
        engine.stop()
    
    # 停止监控
    logger.info("停止监控")
    monitor.stop_monitoring()
    
    logger.info("示例运行完成")

if __name__ == "__main__":
    run_example() 