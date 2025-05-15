#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎监控系统高级测试

测试监控系统在以下场景下的性能和稳定性：
1. 高负载条件（大量数据、多控制器）
2. 长时间运行
3. 错误注入和恢复
4. 资源限制条件
5. 并发操作

这个脚本可以作为压力测试和稳定性测试工具使用。
"""

import os
import sys
import time
import random
import threading
import logging
import argparse
import gc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, "test", "performance", "advanced_testing.log"), mode='w')
    ]
)
logger = logging.getLogger("AdvancedTesting")

# 导入引擎监控系统
from test.unit.core.engine_monitor import EngineMonitor, MonitorConfig, HealthStatus, ResourceType

# 导入测试工具
from test.unit.core.test_engine_monitor import MockEngine, MockController, MockEngineStatus, MockReplayStatus

class HighLoadTestingEnvironment:
    """高负载测试环境"""
    
    def __init__(self, controller_count=10, data_points=1000, update_interval=0.1):
        """
        初始化高负载测试环境
        
        Parameters
        ----------
        controller_count : int, optional
            控制器数量, by default 10
        data_points : int, optional
            每个控制器的数据点数, by default 1000
        update_interval : float, optional
            更新间隔(秒), by default 0.1
        """
        self.controller_count = controller_count
        self.data_points = data_points
        self.update_interval = update_interval
        
        self.engine = None
        self.controllers = {}
        self.controller_threads = {}
        self.monitor = None
        self.running = False
        self.performance_data = []
        
        # 创建监控配置
        self.config = MonitorConfig()
        self.config.interval = 0.5
        self.config.thread_stall_timeout = 2.0
        self.config.auto_recovery = True
        
        logger.info(f"初始化高负载测试环境: {controller_count}个控制器, {data_points}个数据点/控制器")
    
    def setup(self):
        """设置测试环境"""
        logger.info("设置测试环境...")
        
        # 创建引擎
        self.engine = MockEngine()
        
        # 创建监控系统
        self.monitor = EngineMonitor(self.config)
        self.monitor.register_engine_manager(self.engine)
        
        # 创建并注册多个控制器
        for i in range(self.controller_count):
            controller_name = f"controller_{i}"
            controller = MockController(controller_name)
            controller.status = MockReplayStatus.RUNNING
            
            self.controllers[controller_name] = controller
            self.monitor.register_replay_controller(controller_name, controller)
        
        # 注册性能数据收集回调
        self.monitor.register_status_callback(self._collect_performance_data)
        
        logger.info(f"测试环境已设置: {len(self.controllers)}个控制器")
    
    def start(self):
        """启动测试环境"""
        logger.info("启动测试环境...")
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 启动控制器模拟线程
        self.running = True
        for name, controller in self.controllers.items():
            thread = threading.Thread(
                target=self._simulate_controller_activity,
                args=(name, controller),
                name=f"Sim-{name}"
            )
            thread.daemon = True
            thread.start()
            self.controller_threads[name] = thread
        
        # 启动引擎
        self.engine.status = MockEngineStatus.RUNNING
        logger.info("测试环境已启动")
    
    def stop(self):
        """停止测试环境"""
        logger.info("停止测试环境...")
        
        # 停止控制器模拟
        self.running = False
        
        # 等待所有控制器线程结束
        for name, thread in self.controller_threads.items():
            thread.join(timeout=2.0)
            logger.info(f"控制器线程 {name} 已停止")
        
        # 停止监控
        self.monitor.stop_monitoring()
        
        # 停止引擎
        self.engine.status = MockEngineStatus.STOPPED
        
        logger.info("测试环境已停止")
    
    def _simulate_controller_activity(self, name, controller):
        """
        模拟控制器活动
        
        Parameters
        ----------
        name : str
            控制器名称
        controller : MockController
            控制器对象
        """
        logger.info(f"开始模拟控制器 {name} 活动")
        data_point = 0
        error_count = 0
        
        while self.running and data_point < self.data_points:
            # 更新控制器状态
            controller.last_activity_time = time.time()
            
            # 随机生成一些回调错误
            if random.random() < 0.01:  # 1%的概率产生错误
                error_count += 1
                controller.callback_errors = error_count
            
            # 每100个点记录一次
            if data_point % 100 == 0:
                logger.debug(f"控制器 {name}: 处理数据点 {data_point}/{self.data_points}")
            
            data_point += 1
            time.sleep(self.update_interval)
        
        logger.info(f"控制器 {name} 活动模拟完成: {data_point}个数据点, {error_count}个错误")
    
    def _collect_performance_data(self, status, details):
        """
        收集性能数据
        
        Parameters
        ----------
        status : HealthStatus
            健康状态
        details : dict
            详细信息
        """
        # 记录时间戳、健康状态和资源使用情况
        record = {
            'timestamp': datetime.now(),
            'status': status.name,
            'issues_count': len(details.get('issues', []))
        }
        
        # 添加资源使用情况
        resources = details.get('resources', {})
        for resource_type, metrics in resources.items():
            if isinstance(resource_type, ResourceType):
                resource_name = resource_type.name
                
                if resource_name == 'CPU' and 'usage_percent' in metrics:
                    record['cpu_usage'] = metrics['usage_percent']
                    
                if resource_name == 'MEMORY' and 'usage_percent' in metrics:
                    record['memory_usage'] = metrics['usage_percent']
                    
                if resource_name == 'THREAD' and 'count' in metrics:
                    record['thread_count'] = metrics['count']
        
        self.performance_data.append(record)
    
    def get_performance_summary(self):
        """
        获取性能摘要
        
        Returns
        -------
        dict
            性能摘要
        """
        if not self.performance_data:
            return {"message": "没有性能数据"}
        
        # 转换为DataFrame便于分析
        df = pd.DataFrame(self.performance_data)
        
        # 计算摘要统计
        summary = {}
        
        if 'cpu_usage' in df.columns:
            summary['cpu_usage_avg'] = df['cpu_usage'].mean()
            summary['cpu_usage_max'] = df['cpu_usage'].max()
            
        if 'memory_usage' in df.columns:
            summary['memory_usage_avg'] = df['memory_usage'].mean()
            summary['memory_usage_max'] = df['memory_usage'].max()
            
        if 'thread_count' in df.columns:
            summary['thread_count_avg'] = df['thread_count'].mean()
            summary['thread_count_max'] = df['thread_count'].max()
        
        if 'issues_count' in df.columns:
            summary['total_issues'] = df['issues_count'].sum()
            summary['max_issues'] = df['issues_count'].max()
        
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            for status_name, count in status_counts.items():
                summary[f'status_{status_name}'] = count
        
        return summary
    
    def plot_performance_data(self, save_path=None):
        """
        绘制性能数据图表
        
        Parameters
        ----------
        save_path : str, optional
            保存路径, by default None
            
        Returns
        -------
        str
            保存的文件路径
        """
        if not self.performance_data:
            logger.warning("没有性能数据可绘制")
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(self.performance_data)
        df.set_index('timestamp', inplace=True)
        
        # 创建图表
        plt.figure(figsize=(12, 10))
        
        # 健康状态转换为数值
        status_map = {
            'EXCELLENT': 1,
            'GOOD': 2,
            'FAIR': 3,
            'WARNING': 4,
            'CRITICAL': 5
        }
        
        # 绘制健康状态
        if 'status' in df.columns:
            plt.subplot(4, 1, 1)
            plt.title('健康状态')
            status_values = df['status'].map(status_map)
            plt.plot(df.index, status_values, 'o-')
            plt.yticks(list(status_map.values()), list(status_map.keys()))
            plt.grid(True)
        
        # 绘制问题数量
        if 'issues_count' in df.columns:
            plt.subplot(4, 1, 2)
            plt.title('问题数量')
            plt.plot(df.index, df['issues_count'])
            plt.grid(True)
        
        # 绘制CPU使用率
        if 'cpu_usage' in df.columns:
            plt.subplot(4, 1, 3)
            plt.title('CPU使用率 (%)')
            plt.plot(df.index, df['cpu_usage'])
            plt.grid(True)
        
        # 绘制内存使用率
        if 'memory_usage' in df.columns:
            plt.subplot(4, 1, 4)
            plt.title('内存使用率 (%)')
            plt.plot(df.index, df['memory_usage'])
            plt.grid(True)
        
        plt.tight_layout()
        
        # 保存图表
        if save_path is None:
            save_path = os.path.join(project_root, "test", "performance", "high_load_performance.png")
        
        plt.savefig(save_path)
        plt.close()
        
        logger.info(f"性能图表已保存到: {save_path}")
        return save_path


class ErrorInjectionTest:
    """错误注入测试"""
    
    def __init__(self, env):
        """
        初始化错误注入测试
        
        Parameters
        ----------
        env : HighLoadTestingEnvironment
            测试环境
        """
        self.env = env
        self.recovery_events = []
        
        # 注册恢复回调
        self.env.monitor._recovery_callbacks[1] = self._on_recovery
    
    def _on_recovery(self, recovered_issues, details):
        """
        恢复事件回调
        
        Parameters
        ----------
        recovered_issues : list
            已恢复的问题
        details : dict
            详细信息
        """
        event = {
            'timestamp': datetime.now(),
            'recovered_issues': recovered_issues,
            'details': details
        }
        self.recovery_events.append(event)
        logger.info(f"记录恢复事件: {len(recovered_issues)}个问题已恢复")
    
    def inject_controller_stall(self, controller_name=None):
        """
        注入控制器停滞错误
        
        Parameters
        ----------
        controller_name : str, optional
            控制器名称, by default None (随机选择)
        
        Returns
        -------
        str
            受影响的控制器名称
        """
        # 如果没有指定控制器，随机选择一个
        if controller_name is None:
            controller_name = random.choice(list(self.env.controllers.keys()))
        
        controller = self.env.controllers.get(controller_name)
        if controller is None:
            logger.warning(f"控制器 {controller_name} 不存在")
            return None
        
        # 设置最后活动时间为10分钟前
        controller.last_activity_time = time.time() - 600
        logger.info(f"已注入控制器停滞错误: {controller_name}")
        
        return controller_name
    
    def inject_callback_errors(self, controller_name=None, error_count=10):
        """
        注入回调错误
        
        Parameters
        ----------
        controller_name : str, optional
            控制器名称, by default None (随机选择)
        error_count : int, optional
            错误数量, by default 10
            
        Returns
        -------
        str
            受影响的控制器名称
        """
        # 如果没有指定控制器，随机选择一个
        if controller_name is None:
            controller_name = random.choice(list(self.env.controllers.keys()))
        
        controller = self.env.controllers.get(controller_name)
        if controller is None:
            logger.warning(f"控制器 {controller_name} 不存在")
            return None
        
        # 设置回调错误
        controller.callback_errors = error_count
        logger.info(f"已注入回调错误: {controller_name}, {error_count}个错误")
        
        return controller_name
    
    def inject_engine_error(self):
        """
        注入引擎错误
        
        Returns
        -------
        bool
            是否成功
        """
        if self.env.engine is None:
            logger.warning("引擎不存在")
            return False
        
        # 设置引擎状态为错误
        self.env.engine.status = MockEngineStatus.ERROR
        logger.info("已注入引擎错误")
        
        return True
    
    def get_recovery_stats(self):
        """
        获取恢复统计
        
        Returns
        -------
        dict
            恢复统计
        """
        if not self.recovery_events:
            return {"message": "没有恢复事件"}
        
        # 计算统计
        stats = {
            'total_recovery_events': len(self.recovery_events),
            'total_issues_recovered': sum(len(e['recovered_issues']) for e in self.recovery_events),
            'first_recovery_time': self.recovery_events[0]['timestamp'] if self.recovery_events else None,
            'last_recovery_time': self.recovery_events[-1]['timestamp'] if self.recovery_events else None
        }
        
        # 按类型统计恢复的问题
        issue_types = {}
        for event in self.recovery_events:
            for issue in event['recovered_issues']:
                issue_type = 'unknown'
                if '控制器' in issue and '停滞' in issue:
                    issue_type = 'controller_stall'
                elif '引擎' in issue:
                    issue_type = 'engine_error'
                elif '回调错误' in issue:
                    issue_type = 'callback_error'
                elif 'CPU' in issue or '内存' in issue:
                    issue_type = 'resource_usage'
                
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        stats['issue_types'] = issue_types
        
        return stats


def run_high_load_test(controller_count=10, data_points=1000, duration=30):
    """
    运行高负载测试
    
    Parameters
    ----------
    controller_count : int, optional
        控制器数量, by default 10
    data_points : int, optional
        每个控制器的数据点数, by default 1000
    duration : int, optional
        测试持续时间(秒), by default 30
        
    Returns
    -------
    tuple
        (测试环境, 性能摘要, 图表路径)
    """
    logger.info(f"开始高负载测试: {controller_count}个控制器, {data_points}个数据点, {duration}秒")
    
    # 创建测试环境
    env = HighLoadTestingEnvironment(
        controller_count=controller_count,
        data_points=data_points,
        update_interval=duration / data_points  # 调整更新间隔以适应持续时间
    )
    
    try:
        # 设置测试环境
        env.setup()
        
        # 启动测试环境
        env.start()
        
        # 运行指定时间
        logger.info(f"测试运行中，将持续{duration}秒...")
        time.sleep(duration)
        
        # 获取性能摘要
        summary = env.get_performance_summary()
        logger.info(f"性能摘要: {summary}")
        
        # 绘制性能图表
        plot_path = env.plot_performance_data()
        
        return env, summary, plot_path
        
    finally:
        # 停止测试环境
        env.stop()
        
        # 清理资源
        gc.collect()
        
        logger.info("高负载测试完成")


def run_error_injection_test(controller_count=5, duration=30):
    """
    运行错误注入测试
    
    Parameters
    ----------
    controller_count : int, optional
        控制器数量, by default 5
    duration : int, optional
        测试持续时间(秒), by default 30
        
    Returns
    -------
    tuple
        (测试环境, 错误注入测试, 恢复统计)
    """
    logger.info(f"开始错误注入测试: {controller_count}个控制器, {duration}秒")
    
    # 创建测试环境
    env = HighLoadTestingEnvironment(
        controller_count=controller_count,
        data_points=10000,  # 设置足够大的数据点数
        update_interval=0.1
    )
    
    try:
        # 设置测试环境
        env.setup()
        
        # 创建错误注入测试
        error_test = ErrorInjectionTest(env)
        
        # 启动测试环境
        env.start()
        
        # 等待系统稳定
        logger.info("等待系统稳定...")
        time.sleep(5)
        
        # 注入错误
        logger.info("开始注入错误...")
        
        # 注入控制器停滞
        stalled_controller = error_test.inject_controller_stall()
        
        # 等待一段时间，让监控系统检测到问题
        time.sleep(5)
        
        # 注入回调错误
        error_controller = error_test.inject_callback_errors()
        
        # 等待一段时间
        time.sleep(5)
        
        # 注入引擎错误
        error_test.inject_engine_error()
        
        # 等待系统进行恢复
        logger.info("等待系统恢复...")
        time.sleep(10)
        
        # 获取恢复统计
        recovery_stats = error_test.get_recovery_stats()
        logger.info(f"恢复统计: {recovery_stats}")
        
        # 再运行一段时间
        remaining_time = duration - 25  # 已经用了25秒左右
        if remaining_time > 0:
            logger.info(f"继续运行{remaining_time}秒...")
            time.sleep(remaining_time)
        
        # 绘制性能图表
        plot_path = env.plot_performance_data(
            save_path=os.path.join(project_root, "test", "performance", "error_injection_performance.png")
        )
        
        return env, error_test, recovery_stats
        
    finally:
        # 停止测试环境
        env.stop()
        
        # 清理资源
        gc.collect()
        
        logger.info("错误注入测试完成")


def run_concurrent_operations_test(controller_count=5, thread_count=3, duration=30):
    """
    运行并发操作测试
    
    Parameters
    ----------
    controller_count : int, optional
        控制器数量, by default 5
    thread_count : int, optional
        并发线程数, by default 3
    duration : int, optional
        测试持续时间(秒), by default 30
        
    Returns
    -------
    tuple
        (测试环境, 操作统计)
    """
    logger.info(f"开始并发操作测试: {controller_count}个控制器, {thread_count}个线程, {duration}秒")
    
    # 创建测试环境
    env = HighLoadTestingEnvironment(
        controller_count=controller_count,
        data_points=10000,  # 设置足够大的数据点数
        update_interval=0.1
    )
    
    # 操作统计
    operations_stats = {
        'total_operations': 0,
        'successful_operations': 0,
        'failed_operations': 0,
        'operation_types': {}
    }
    
    # 操作锁
    stats_lock = threading.Lock()
    
    # 定义并发操作函数
    def concurrent_operation(thread_id):
        """
        并发操作函数
        
        Parameters
        ----------
        thread_id : int
            线程ID
        """
        logger.info(f"线程 {thread_id} 开始执行操作")
        
        operations = 0
        successes = 0
        failures = 0
        op_types = {}
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # 随机选择一个操作
            operation = random.choice([
                'get_health_status',
                'get_resource_usage',
                'get_health_trend',
                'register_callback',
                'unregister_callback'
            ])
            
            try:
                if operation == 'get_health_status':
                    status, details = env.monitor.get_health_status()
                    
                elif operation == 'get_resource_usage':
                    resources = env.monitor.get_resource_usage()
                    
                elif operation == 'get_health_trend':
                    trend = env.monitor.get_health_trend(hours=0.1)
                    
                elif operation == 'register_callback':
                    callback_id = env.monitor.register_status_callback(lambda s, d: None)
                    
                elif operation == 'unregister_callback':
                    # 随机ID，有时会失败
                    callback_id = random.randint(1, 100)
                    env.monitor.unregister_callback(callback_id)
                
                successes += 1
                
            except Exception as e:
                logger.error(f"线程 {thread_id} 操作 {operation} 失败: {e}")
                failures += 1
            
            operations += 1
            op_types[operation] = op_types.get(operation, 0) + 1
            
            # 随机暂停一段时间
            time.sleep(random.uniform(0.01, 0.2))
        
        # 更新全局统计
        with stats_lock:
            operations_stats['total_operations'] += operations
            operations_stats['successful_operations'] += successes
            operations_stats['failed_operations'] += failures
            
            for op_type, count in op_types.items():
                operations_stats['operation_types'][op_type] = \
                    operations_stats['operation_types'].get(op_type, 0) + count
        
        logger.info(f"线程 {thread_id} 完成: {operations}个操作, {successes}成功, {failures}失败")
    
    try:
        # 设置测试环境
        env.setup()
        
        # 启动测试环境
        env.start()
        
        # 等待系统稳定
        logger.info("等待系统稳定...")
        time.sleep(3)
        
        # 启动并发操作线程
        logger.info(f"启动{thread_count}个并发操作线程...")
        threads = []
        for i in range(thread_count):
            thread = threading.Thread(
                target=concurrent_operation,
                args=(i,),
                name=f"Concurrent-{i}"
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        logger.info("所有并发操作线程已完成")
        logger.info(f"操作统计: {operations_stats}")
        
        # 绘制性能图表
        plot_path = env.plot_performance_data(
            save_path=os.path.join(project_root, "test", "performance", "concurrent_operations_performance.png")
        )
        
        return env, operations_stats
        
    finally:
        # 停止测试环境
        env.stop()
        
        # 清理资源
        gc.collect()
        
        logger.info("并发操作测试完成")


def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行所有测试...")
    
    results = {}
    
    # 运行高负载测试
    logger.info("=== 运行高负载测试 ===")
    _, high_load_summary, high_load_plot = run_high_load_test(
        controller_count=20,
        data_points=500,
        duration=20
    )
    results['high_load_test'] = {
        'summary': high_load_summary,
        'plot': high_load_plot
    }
    
    # 运行错误注入测试
    logger.info("=== 运行错误注入测试 ===")
    _, _, recovery_stats = run_error_injection_test(
        controller_count=10,
        duration=20
    )
    results['error_injection_test'] = {
        'recovery_stats': recovery_stats
    }
    
    # 运行并发操作测试
    logger.info("=== 运行并发操作测试 ===")
    _, operations_stats = run_concurrent_operations_test(
        controller_count=10,
        thread_count=5,
        duration=20
    )
    results['concurrent_operations_test'] = {
        'operations_stats': operations_stats
    }
    
    logger.info("所有测试完成")
    return results


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="引擎监控系统高级测试")
    parser.add_argument('--test', choices=['high-load', 'error-injection', 'concurrent', 'all'],
                        default='all', help="要运行的测试类型")
    parser.add_argument('--controllers', type=int, default=10, help="控制器数量")
    parser.add_argument('--duration', type=int, default=30, help="测试持续时间(秒)")
    parser.add_argument('--data-points', type=int, default=1000, help="每个控制器的数据点数")
    parser.add_argument('--threads', type=int, default=3, help="并发线程数")
    
    args = parser.parse_args()
    
    if args.test == 'high-load':
        run_high_load_test(
            controller_count=args.controllers,
            data_points=args.data_points,
            duration=args.duration
        )
    elif args.test == 'error-injection':
        run_error_injection_test(
            controller_count=args.controllers,
            duration=args.duration
        )
    elif args.test == 'concurrent':
        run_concurrent_operations_test(
            controller_count=args.controllers,
            thread_count=args.threads,
            duration=args.duration
        )
    else:
        run_all_tests() 