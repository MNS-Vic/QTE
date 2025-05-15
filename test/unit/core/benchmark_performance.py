#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能基准测试 - 测试修复前后的性能差异
"""
import sys
import os
import pandas as pd
import numpy as np
import time
import threading
import logging
from datetime import datetime, timedelta
import traceback
import gc
import psutil
import statistics

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入必要的模块
from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus
from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus

# 尝试导入修复后的版本
try:
    from test.unit.core.engine_manager_fixed import ReplayEngineManager as FixedReplayEngineManager
    from test.unit.core.data_replay_fixed import DataFrameReplayController as FixedDataFrameReplayController
    fixed_version_available = True
except ImportError:
    logger.warning("修复后的版本未找到，仅测试原始版本")
    fixed_version_available = False

def create_test_data(rows=1000):
    """创建大量测试数据"""
    dates = pd.date_range(start=datetime.now(), periods=rows, freq='1min')
    return pd.DataFrame({
        'timestamp': dates,
        'price': np.random.rand(rows) * 100,
        'volume': np.random.randint(1000, 10000, rows),
        'symbol': 'TEST',
        'extra_data1': np.random.rand(rows),
        'extra_data2': np.random.rand(rows),
        'extra_data3': np.random.rand(rows)
    })

def measure_memory_usage():
    """测量当前进程的内存使用"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)  # 转换为MB

class PerformanceTracker:
    """性能跟踪器"""
    def __init__(self, name):
        self.name = name
        self.event_count = 0
        self.start_time = None
        self.end_time = None
        self.event_times = []
        self.start_memory = 0
        self.end_memory = 0
        self.lock = threading.Lock()
    
    def start(self):
        """开始跟踪"""
        self.start_time = time.time()
        self.start_memory = measure_memory_usage()
    
    def record_event(self):
        """记录事件"""
        with self.lock:
            self.event_count += 1
            self.event_times.append(time.time())
    
    def stop(self):
        """停止跟踪"""
        self.end_time = time.time()
        self.end_memory = measure_memory_usage()
    
    def get_stats(self):
        """获取统计信息"""
        if self.start_time is None or self.end_time is None:
            return {"error": "未开始或未结束跟踪"}
        
        total_time = self.end_time - self.start_time
        events_per_second = self.event_count / total_time if total_time > 0 else 0
        memory_delta = self.end_memory - self.start_memory
        
        # 计算事件间隔统计
        intervals = []
        for i in range(1, len(self.event_times)):
            intervals.append(self.event_times[i] - self.event_times[i-1])
        
        interval_stats = {
            "mean": statistics.mean(intervals) if intervals else 0,
            "median": statistics.median(intervals) if intervals else 0,
            "min": min(intervals) if intervals else 0,
            "max": max(intervals) if intervals else 0,
            "stdev": statistics.stdev(intervals) if len(intervals) > 1 else 0
        }
        
        return {
            "name": self.name,
            "total_time": total_time,
            "event_count": self.event_count,
            "events_per_second": events_per_second,
            "start_memory_mb": self.start_memory,
            "end_memory_mb": self.end_memory,
            "memory_delta_mb": memory_delta,
            "interval_stats": interval_stats
        }

def benchmark_original_version(data_size=1000, max_time=10):
    """测试原始版本的性能"""
    logger.info(f"开始测试原始版本 (数据量: {data_size})")
    
    # 创建测试数据
    test_data = create_test_data(rows=data_size)
    
    # 创建性能跟踪器
    tracker = PerformanceTracker("原始版本")
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine_manager.initialize()
    
    # 创建重放控制器
    replay_controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 添加重放控制器
    engine_manager.add_replay_controller("test", replay_controller)
    
    # 注册事件处理器
    def event_handler(event):
        tracker.record_event()
    
    engine_manager.register_event_handler("MARKET_DATA", event_handler)
    
    # 开始测试
    tracker.start()
    engine_manager.start()
    
    # 运行一段时间或直到处理完所有数据
    start_time = time.time()
    while time.time() - start_time < max_time:
        if engine_manager.get_status() != EngineStatus.RUNNING:
            break
        time.sleep(0.1)
    
    # 停止测试
    engine_manager.stop()
    tracker.stop()
    
    # 清理资源
    engine_manager = None
    replay_controller = None
    gc.collect()
    
    return tracker.get_stats()

def benchmark_fixed_version(data_size=1000, max_time=10):
    """测试修复版本的性能"""
    if not fixed_version_available:
        return {"error": "修复版本不可用"}
    
    logger.info(f"开始测试修复版本 (数据量: {data_size})")
    
    # 创建测试数据
    test_data = create_test_data(rows=data_size)
    
    # 创建性能跟踪器
    tracker = PerformanceTracker("修复版本")
    
    # 创建引擎管理器
    engine_manager = FixedReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine_manager.initialize()
    
    # 创建重放控制器
    replay_controller = FixedDataFrameReplayController(
        dataframe=test_data,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 添加重放控制器
    engine_manager.add_replay_controller("test", replay_controller)
    
    # 注册事件处理器
    def event_handler(event):
        tracker.record_event()
    
    engine_manager.register_event_handler("MARKET_DATA", event_handler)
    
    # 开始测试
    tracker.start()
    engine_manager.start()
    
    # 运行一段时间或直到处理完所有数据
    start_time = time.time()
    while time.time() - start_time < max_time:
        if engine_manager.get_status() != EngineStatus.RUNNING:
            break
        time.sleep(0.1)
    
    # 停止测试
    engine_manager.stop()
    tracker.stop()
    
    # 清理资源
    engine_manager = None
    replay_controller = None
    gc.collect()
    
    return tracker.get_stats()

def compare_results(original_stats, fixed_stats):
    """比较结果并输出报告"""
    if "error" in original_stats or "error" in fixed_stats:
        if "error" in original_stats:
            logger.error(f"原始版本测试失败: {original_stats['error']}")
        if "error" in fixed_stats:
            logger.error(f"修复版本测试失败: {fixed_stats['error']}")
        return
    
    # 计算差异
    time_diff = fixed_stats["total_time"] - original_stats["total_time"]
    time_percent = (time_diff / original_stats["total_time"]) * 100 if original_stats["total_time"] > 0 else 0
    
    throughput_diff = fixed_stats["events_per_second"] - original_stats["events_per_second"]
    throughput_percent = (throughput_diff / original_stats["events_per_second"]) * 100 if original_stats["events_per_second"] > 0 else 0
    
    memory_diff = fixed_stats["memory_delta_mb"] - original_stats["memory_delta_mb"]
    
    # 打印报告
    logger.info("\n性能比较报告:")
    logger.info(f"{'指标':<20} {'原始版本':<15} {'修复版本':<15} {'差异':<15} {'变化百分比':<15}")
    logger.info("-" * 80)
    logger.info(f"{'总时间 (秒)':<20} {original_stats['total_time']:<15.3f} {fixed_stats['total_time']:<15.3f} {time_diff:<+15.3f} {time_percent:<+15.2f}%")
    logger.info(f"{'事件数量':<20} {original_stats['event_count']:<15d} {fixed_stats['event_count']:<15d} {fixed_stats['event_count'] - original_stats['event_count']:<+15d} {((fixed_stats['event_count'] - original_stats['event_count']) / original_stats['event_count'] * 100) if original_stats['event_count'] > 0 else 0:<+15.2f}%")
    logger.info(f"{'吞吐量 (事件/秒)':<20} {original_stats['events_per_second']:<15.2f} {fixed_stats['events_per_second']:<15.2f} {throughput_diff:<+15.2f} {throughput_percent:<+15.2f}%")
    logger.info(f"{'内存使用增长 (MB)':<20} {original_stats['memory_delta_mb']:<15.2f} {fixed_stats['memory_delta_mb']:<15.2f} {memory_diff:<+15.2f} {'N/A':<15}")
    
    # 事件间隔统计
    logger.info("\n事件间隔统计 (秒):")
    logger.info(f"{'统计量':<20} {'原始版本':<15} {'修复版本':<15} {'差异':<15}")
    logger.info("-" * 65)
    for stat in ["mean", "median", "min", "max", "stdev"]:
        orig_val = original_stats["interval_stats"][stat]
        fixed_val = fixed_stats["interval_stats"][stat]
        diff = fixed_val - orig_val
        logger.info(f"{stat:<20} {orig_val:<15.6f} {fixed_val:<15.6f} {diff:<+15.6f}")
    
    # 总结
    logger.info("\n性能总结:")
    if throughput_percent > 5:
        logger.info(f"修复版本的性能提升明显，吞吐量增加了 {throughput_percent:.2f}%")
    elif throughput_percent > -5:
        logger.info(f"修复版本的性能基本不变，吞吐量变化了 {throughput_percent:.2f}%")
    else:
        logger.info(f"修复版本的性能有所下降，吞吐量减少了 {-throughput_percent:.2f}%")
    
    if memory_diff > 1:
        logger.info(f"修复版本的内存使用增加了 {memory_diff:.2f} MB")
    elif memory_diff < -1:
        logger.info(f"修复版本的内存使用减少了 {-memory_diff:.2f} MB")
    else:
        logger.info("修复版本的内存使用基本不变")

def run_benchmark(data_sizes=[100, 1000, 10000], max_time=10):
    """运行所有基准测试"""
    results = {
        "original": {},
        "fixed": {}
    }
    
    for size in data_sizes:
        logger.info(f"\n开始测试数据量: {size}")
        
        # 测试原始版本
        original_stats = benchmark_original_version(data_size=size, max_time=max_time)
        results["original"][size] = original_stats
        
        # 给系统一些时间恢复
        time.sleep(1)
        
        # 测试修复版本
        if fixed_version_available:
            fixed_stats = benchmark_fixed_version(data_size=size, max_time=max_time)
            results["fixed"][size] = fixed_stats
            
            # 比较结果
            compare_results(original_stats, fixed_stats)
        
        # 给系统一些时间恢复
        time.sleep(1)
    
    return results

if __name__ == "__main__":
    logger.info("开始性能基准测试...")
    
    # 运行基准测试
    data_sizes = [100, 1000, 5000]
    results = run_benchmark(data_sizes=data_sizes, max_time=20)
    
    logger.info("\n性能基准测试完成") 