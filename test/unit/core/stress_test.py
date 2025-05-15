#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压力测试 - 测试修复后版本在极端条件下的稳定性
"""
import sys
import os
import pandas as pd
import numpy as np
import time
import threading
import logging
import multiprocessing
from datetime import datetime, timedelta
import traceback
import gc
import psutil
import queue
import random
from concurrent.futures import ThreadPoolExecutor

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 尝试导入修复后的版本
try:
    from test.unit.core.engine_manager_fixed import ReplayEngineManager, EngineType, EngineStatus, EngineEvent
    from test.unit.core.data_replay_fixed import DataFrameReplayController, ReplayMode, ReplayStatus
    fixed_version_available = True
except ImportError:
    logger.warning("修复后的版本未找到，将使用原始版本")
    from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus, EngineEvent
    from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus
    fixed_version_available = False

def create_large_dataset(rows=100000):
    """创建大量测试数据"""
    logger.info(f"创建大数据集 ({rows} 行)...")
    dates = pd.date_range(start=datetime.now(), periods=rows, freq='1s')
    
    # 生成随机数据，模拟金融时间序列
    prices = 100 + np.cumsum(np.random.normal(0, 0.1, rows))
    volumes = np.random.randint(1000, 10000, rows)
    
    # 添加其他指标，增加数据量
    data = {
        'timestamp': dates,
        'price': prices,
        'volume': volumes,
        'open': prices + np.random.normal(0, 0.05, rows),
        'high': prices + np.abs(np.random.normal(0, 0.2, rows)),
        'low': prices - np.abs(np.random.normal(0, 0.2, rows)),
        'close': prices + np.random.normal(0, 0.05, rows),
        'symbol': 'TEST',
        'bid': prices - np.random.uniform(0, 0.1, rows),
        'ask': prices + np.random.uniform(0, 0.1, rows),
        'bid_volume': np.random.randint(500, 5000, rows),
        'ask_volume': np.random.randint(500, 5000, rows)
    }
    
    # 添加更多字段使数据更大
    for i in range(10):
        data[f'indicator_{i}'] = np.random.rand(rows)
        data[f'metric_{i}'] = np.random.normal(0, 1, rows)
    
    df = pd.DataFrame(data)
    logger.info(f"数据集创建完成，大小约为：{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
    return df

def create_high_frequency_dataset(rows=10000, frequency_ms=1):
    """创建高频数据集，时间间隔非常小"""
    logger.info(f"创建高频数据集 ({rows} 行，间隔 {frequency_ms} 毫秒)...")
    start_time = datetime.now()
    dates = [start_time + timedelta(milliseconds=i*frequency_ms) for i in range(rows)]
    
    df = pd.DataFrame({
        'timestamp': dates,
        'price': 100 + np.cumsum(np.random.normal(0, 0.001, rows)),
        'volume': np.random.randint(10, 100, rows),
        'symbol': 'HFT'
    })
    
    logger.info(f"高频数据集创建完成，时间跨度：{(dates[-1] - dates[0]).total_seconds():.2f} 秒")
    return df

def create_multi_source_datasets(count=5, rows_per_source=10000):
    """创建多个数据源"""
    logger.info(f"创建 {count} 个数据源...")
    datasets = {}
    
    for i in range(count):
        symbol = f"SYM{i+1}"
        dates = pd.date_range(start=datetime.now(), periods=rows_per_source, freq='1s')
        
        # 不同数据源有不同的数据特征
        base_price = 50 + random.randint(0, 100)
        volatility = 0.05 + random.random() * 0.2
        drift = -0.01 + random.random() * 0.02
        
        prices = base_price + np.cumsum(np.random.normal(drift, volatility, rows_per_source))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'price': prices,
            'volume': np.random.randint(1000, 10000, rows_per_source),
            'symbol': symbol
        })
        
        datasets[symbol] = df
    
    logger.info(f"创建了 {count} 个数据源，总行数：{count * rows_per_source}")
    return datasets

class StressTestResult:
    """压力测试结果"""
    def __init__(self, test_name):
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.total_events = 0
        self.success = False
        self.error = None
        self.peak_memory_mb = 0
        self.avg_memory_mb = 0
        self.memory_samples = []
        self.memory_sample_times = []
        self.throughput = 0
        self.event_counts_over_time = []  # 采样点的事件计数
        self.event_count_times = []  # 采样时间点
        self.pauses_detected = 0  # 检测到的长暂停次数
        self.additional_metrics = {}  # 其他度量指标
    
    def start(self):
        """开始测试"""
        self.start_time = time.time()
        self.sample_memory()
    
    def end(self, success=True, error=None):
        """结束测试"""
        self.end_time = time.time()
        self.success = success
        self.error = error
        self.sample_memory()
        
        if self.end_time > self.start_time:
            self.throughput = self.total_events / (self.end_time - self.start_time)
        
        # 计算平均内存使用
        if self.memory_samples:
            self.avg_memory_mb = sum(self.memory_samples) / len(self.memory_samples)
    
    def sample_memory(self):
        """采样当前内存使用"""
        memory_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        self.memory_samples.append(memory_mb)
        self.memory_sample_times.append(time.time())
        self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
    
    def increment_events(self, count=1):
        """增加事件计数"""
        self.total_events += count
        
        # 定期记录累计事件数
        if not self.event_count_times or time.time() - self.event_count_times[-1] >= 1.0:
            self.event_counts_over_time.append(self.total_events)
            self.event_count_times.append(time.time())
    
    def detect_pause(self, threshold_seconds=0.5):
        """检测暂停"""
        if len(self.event_count_times) < 2:
            return
        
        # 检查采样点之间的时间差
        for i in range(1, len(self.event_count_times)):
            time_diff = self.event_count_times[i] - self.event_count_times[i-1]
            if time_diff > threshold_seconds:
                self.pauses_detected += 1
    
    def get_summary(self):
        """获取结果摘要"""
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        
        summary = {
            "test_name": self.test_name,
            "success": self.success,
            "error": str(self.error) if self.error else None,
            "duration_seconds": duration,
            "total_events": self.total_events,
            "events_per_second": self.throughput,
            "peak_memory_mb": self.peak_memory_mb,
            "avg_memory_mb": self.avg_memory_mb,
            "pauses_detected": self.pauses_detected
        }
        
        # 添加其他度量指标
        summary.update(self.additional_metrics)
        
        return summary

class MemoryLeakDetector:
    """内存泄漏检测器"""
    def __init__(self, sample_interval=1.0, significant_change_mb=5.0):
        self.samples = []
        self.sample_times = []
        self.sample_interval = sample_interval
        self.significant_change_mb = significant_change_mb
        self.running = False
        self.thread = None
    
    def start(self):
        """开始监控内存"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _monitor(self):
        """内存监控线程"""
        while self.running:
            memory_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            self.samples.append(memory_mb)
            self.sample_times.append(time.time())
            time.sleep(self.sample_interval)
    
    def detect_leak(self):
        """检测内存泄漏"""
        if len(self.samples) < 10:
            return False, "样本不足"
        
        # 计算内存增长趋势
        x = np.array(range(len(self.samples)))
        y = np.array(self.samples)
        
        slope, _ = np.polyfit(x, y, 1)
        
        # 计算最后样本与最初样本的差值
        total_change = self.samples[-1] - self.samples[0]
        duration = self.sample_times[-1] - self.sample_times[0]
        
        # 判断是否存在内存泄漏
        if slope > 0.5 and total_change > self.significant_change_mb:
            return True, f"检测到内存泄漏：斜率={slope:.2f} MB/样本，总增长={total_change:.2f} MB，持续时间={duration:.2f}秒"
        
        return False, f"未检测到明显内存泄漏：斜率={slope:.2f} MB/样本，总变化={total_change:.2f} MB"

def run_large_data_stress_test(rows=100000, run_time=30):
    """大数据量压力测试"""
    test_result = StressTestResult("大数据量测试")
    logger.info(f"开始大数据量压力测试 ({rows} 行)...")
    
    try:
        # 创建大数据集
        test_data = create_large_dataset(rows=rows)
        
        # 创建引擎管理器
        engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        engine_manager.initialize()
        
        # 创建重放控制器
        replay_controller = DataFrameReplayController(
            dataframe=test_data,
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST  # 使用回测模式最快速度播放
        )
        
        # 添加重放控制器
        engine_manager.add_replay_controller("test", replay_controller)
        
        # 创建内存泄漏检测器
        leak_detector = MemoryLeakDetector()
        leak_detector.start()
        
        # 注册事件处理器
        def event_handler(event):
            test_result.increment_events()
            # 每1000个事件采样一次内存
            if test_result.total_events % 1000 == 0:
                test_result.sample_memory()
        
        engine_manager.register_event_handler("MARKET_DATA", event_handler)
        
        # 开始测试
        test_result.start()
        engine_manager.start()
        
        # 运行指定时间
        start_time = time.time()
        while time.time() - start_time < run_time:
            time.sleep(0.1)
            test_result.sample_memory()
            
            # 如果引擎已经停止了，提前退出
            if engine_manager.get_status() != EngineStatus.RUNNING:
                logger.info("引擎已停止运行，测试提前结束")
                break
        
        # 停止测试
        engine_manager.stop()
        leak_detector.stop()
        
        # 检测内存泄漏
        has_leak, leak_message = leak_detector.detect_leak()
        test_result.additional_metrics["memory_leak_detected"] = has_leak
        test_result.additional_metrics["memory_leak_message"] = leak_message
        
        if has_leak:
            logger.warning(leak_message)
        else:
            logger.info(leak_message)
        
        test_result.end(success=True)
        
        # 清理资源
        engine_manager = None
        replay_controller = None
        test_data = None
        gc.collect()
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        test_result.end(success=False, error=e)
    
    logger.info(f"大数据量测试完成: 处理了 {test_result.total_events} 个事件，"
               f"吞吐量 {test_result.throughput:.2f} 事件/秒")
    
    return test_result

def run_high_frequency_stress_test(rows=50000, frequency_ms=1, run_time=30):
    """高频数据压力测试"""
    test_result = StressTestResult("高频数据测试")
    logger.info(f"开始高频数据压力测试 (频率: {frequency_ms}ms)...")
    
    try:
        # 创建高频数据集
        test_data = create_high_frequency_dataset(rows=rows, frequency_ms=frequency_ms)
        
        # 创建引擎管理器
        engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        engine_manager.initialize()
        
        # 创建重放控制器，使用实时模式
        replay_controller = DataFrameReplayController(
            dataframe=test_data,
            timestamp_column='timestamp',
            mode=ReplayMode.REALTIME  # 使用实时模式测试高频处理能力
        )
        
        # 添加重放控制器
        engine_manager.add_replay_controller("test", replay_controller)
        
        # 事件处理计数和上一个事件的时间
        event_times = []
        event_lock = threading.Lock()
        
        # 注册事件处理器
        def event_handler(event):
            with event_lock:
                test_result.increment_events()
                event_times.append(time.time())
                
                # 每1000个事件采样一次内存
                if test_result.total_events % 1000 == 0:
                    test_result.sample_memory()
        
        engine_manager.register_event_handler("MARKET_DATA", event_handler)
        
        # 开始测试
        test_result.start()
        engine_manager.start()
        
        # 运行指定时间
        start_time = time.time()
        while time.time() - start_time < run_time:
            time.sleep(0.1)
            test_result.sample_memory()
            
            # 计算时间差，检测处理是否跟上
            with event_lock:
                if len(event_times) >= 2:
                    # 计算事件间隔
                    intervals = [event_times[i] - event_times[i-1] for i in range(1, len(event_times))]
                    
                    # 检测是否有长暂停
                    for interval in intervals:
                        if interval > 0.1:  # 100ms以上视为暂停
                            test_result.pauses_detected += 1
                    
                    # 清空已处理的事件时间
                    event_times.clear()
            
            # 如果引擎已经停止了，提前退出
            if engine_manager.get_status() != EngineStatus.RUNNING:
                logger.info("引擎已停止运行，测试提前结束")
                break
        
        # 停止测试
        engine_manager.stop()
        test_result.end(success=True)
        
        # 清理资源
        engine_manager = None
        replay_controller = None
        test_data = None
        gc.collect()
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        test_result.end(success=False, error=e)
    
    logger.info(f"高频数据测试完成: 处理了 {test_result.total_events} 个事件，"
               f"吞吐量 {test_result.throughput:.2f} 事件/秒，"
               f"检测到 {test_result.pauses_detected} 次处理暂停")
    
    return test_result

def run_multi_source_stress_test(source_count=5, rows_per_source=10000, run_time=30):
    """多数据源压力测试"""
    test_result = StressTestResult("多数据源测试")
    logger.info(f"开始多数据源压力测试 ({source_count} 个数据源)...")
    
    try:
        # 创建多个数据源
        datasets = create_multi_source_datasets(count=source_count, rows_per_source=rows_per_source)
        
        # 创建引擎管理器
        engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        engine_manager.initialize()
        
        # 为每个数据源创建重放控制器
        for symbol, df in datasets.items():
            replay_controller = DataFrameReplayController(
                dataframe=df,
                timestamp_column='timestamp',
                mode=ReplayMode.BACKTEST
            )
            
            # 添加重放控制器
            engine_manager.add_replay_controller(symbol, replay_controller)
        
        # 统计每个数据源的事件
        source_counts = {symbol: 0 for symbol in datasets.keys()}
        source_lock = threading.Lock()
        
        # 注册事件处理器
        def event_handler(event):
            test_result.increment_events()
            
            # 记录来源
            source = event.source
            with source_lock:
                if source in source_counts:
                    source_counts[source] += 1
            
            # 每1000个事件采样一次内存
            if test_result.total_events % 1000 == 0:
                test_result.sample_memory()
        
        engine_manager.register_event_handler("MARKET_DATA", event_handler)
        
        # 开始测试
        test_result.start()
        engine_manager.start()
        
        # 运行指定时间
        start_time = time.time()
        while time.time() - start_time < run_time:
            time.sleep(0.1)
            test_result.sample_memory()
            
            # 如果引擎已经停止了，提前退出
            if engine_manager.get_status() != EngineStatus.RUNNING:
                logger.info("引擎已停止运行，测试提前结束")
                break
        
        # 停止测试
        engine_manager.stop()
        test_result.end(success=True)
        
        # 添加每个数据源的计数到结果中
        for symbol, count in source_counts.items():
            test_result.additional_metrics[f"source_{symbol}_count"] = count
        
        # 检查数据源平衡性
        if source_counts:
            max_count = max(source_counts.values())
            min_count = min(source_counts.values())
            imbalance = (max_count - min_count) / max(1, max_count) * 100
            test_result.additional_metrics["source_imbalance_percent"] = imbalance
            
            logger.info(f"数据源平衡性: 最大={max_count}, 最小={min_count}, 不平衡率={imbalance:.2f}%")
        
        # 清理资源
        engine_manager = None
        datasets = None
        gc.collect()
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        test_result.end(success=False, error=e)
    
    logger.info(f"多数据源测试完成: 处理了 {test_result.total_events} 个事件，"
               f"吞吐量 {test_result.throughput:.2f} 事件/秒")
    
    return test_result

def run_memory_leak_test(iterations=10, rows=5000, gc_frequency=2):
    """内存泄漏专项测试"""
    test_result = StressTestResult("内存泄漏测试")
    logger.info(f"开始内存泄漏专项测试 ({iterations} 次迭代)...")
    
    leak_detector = MemoryLeakDetector(sample_interval=0.5)
    leak_detector.start()
    
    try:
        test_result.start()
        
        # 多次创建和销毁引擎管理器和重放控制器
        for i in range(iterations):
            logger.info(f"内存泄漏测试迭代 {i+1}/{iterations}")
            
            # 创建测试数据
            test_data = create_large_dataset(rows=rows)
            
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
                test_result.increment_events()
            
            engine_manager.register_event_handler("MARKET_DATA", event_handler)
            
            # 启动引擎
            engine_manager.start()
            
            # 运行一小段时间
            time.sleep(2)
            
            # 停止引擎
            engine_manager.stop()
            
            # 记录内存使用
            test_result.sample_memory()
            
            # 清理资源
            engine_manager = None
            replay_controller = None
            test_data = None
            
            # 定期强制垃圾回收
            if i % gc_frequency == 0:
                gc.collect()
        
        leak_detector.stop()
        
        # 检测内存泄漏
        has_leak, leak_message = leak_detector.detect_leak()
        test_result.additional_metrics["memory_leak_detected"] = has_leak
        test_result.additional_metrics["memory_leak_message"] = leak_message
        
        if has_leak:
            logger.warning(leak_message)
        else:
            logger.info(leak_message)
        
        test_result.end(success=True)
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        test_result.end(success=False, error=e)
        leak_detector.stop()
    
    logger.info(f"内存泄漏测试完成: 峰值内存使用 {test_result.peak_memory_mb:.2f} MB")
    
    return test_result

def run_long_runtime_test(duration_minutes=5, data_size=10000):
    """长时间运行测试"""
    test_result = StressTestResult("长时间运行测试")
    logger.info(f"开始长时间运行测试 (持续 {duration_minutes} 分钟)...")
    
    try:
        # 创建测试数据
        test_data = create_large_dataset(rows=data_size)
        
        # 创建引擎管理器
        engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        engine_manager.initialize()
        
        # 使用步进模式，可以控制数据重放速度
        replay_controller = DataFrameReplayController(
            dataframe=test_data,
            timestamp_column='timestamp',
            mode=ReplayMode.STEPPED
        )
        
        # 添加重放控制器
        engine_manager.add_replay_controller("test", replay_controller)
        
        # 统计事件间隔
        last_event_time = [time.time()]
        
        # 注册事件处理器
        def event_handler(event):
            current_time = time.time()
            interval = current_time - last_event_time[0]
            last_event_time[0] = current_time
            
            test_result.increment_events()
            
            # 检测处理间隔过长
            if interval > 0.5:  # 500ms以上视为暂停
                test_result.pauses_detected += 1
            
            # 每500个事件采样一次内存
            if test_result.total_events % 500 == 0:
                test_result.sample_memory()
        
        engine_manager.register_event_handler("MARKET_DATA", event_handler)
        
        # 开始测试
        test_result.start()
        engine_manager.start()
        
        # 创建一个线程池用于步进操作
        with ThreadPoolExecutor(max_workers=1) as executor:
            # 长时间运行
            end_time = time.time() + duration_minutes * 60
            
            while time.time() < end_time:
                # 步进
                executor.submit(replay_controller.step)
                
                # 模拟间隔不均匀的数据到达
                sleep_time = random.uniform(0.01, 0.2)
                time.sleep(sleep_time)
                
                # 定期采样内存
                if random.random() < 0.05:  # 5%的概率
                    test_result.sample_memory()
                
                # 如果已处理完所有数据，重置重放控制器
                if replay_controller.get_status() == ReplayStatus.COMPLETED:
                    logger.info("重置重放控制器以继续测试")
                    replay_controller.reset()
                    time.sleep(0.5)  # 给一点时间重置
                    replay_controller.start()
        
        # 停止测试
        engine_manager.stop()
        test_result.end(success=True)
        
        # 清理资源
        engine_manager = None
        replay_controller = None
        test_data = None
        gc.collect()
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        test_result.end(success=False, error=e)
    
    # 计算稳定性指标
    stability_score = 100 - (test_result.pauses_detected / max(1, test_result.total_events / 1000) * 100)
    test_result.additional_metrics["stability_score"] = min(100, max(0, stability_score))
    
    logger.info(f"长时间运行测试完成: 处理了 {test_result.total_events} 个事件，"
               f"持续时间 {(test_result.end_time - test_result.start_time)/60:.1f} 分钟，"
               f"稳定性评分 {test_result.additional_metrics['stability_score']:.2f}%")
    
    return test_result

def print_test_summary(test_results):
    """打印测试摘要"""
    logger.info("\n" + "="*80)
    logger.info("压力测试摘要")
    logger.info("="*80)
    
    for test_name, result in test_results.items():
        logger.info(f"\n{test_name}:")
        logger.info("-" * len(test_name))
        
        summary = result.get_summary()
        
        logger.info(f"状态: {'成功' if summary['success'] else '失败'}")
        if not summary['success'] and summary['error']:
            logger.info(f"错误: {summary['error']}")
        
        logger.info(f"持续时间: {summary['duration_seconds']:.2f} 秒")
        logger.info(f"处理事件数: {summary['total_events']}")
        logger.info(f"吞吐量: {summary['events_per_second']:.2f} 事件/秒")
        logger.info(f"峰值内存: {summary['peak_memory_mb']:.2f} MB")
        logger.info(f"平均内存: {summary['avg_memory_mb']:.2f} MB")
        logger.info(f"检测到的暂停: {summary['pauses_detected']}")
        
        # 打印其他指标
        for key, value in summary.items():
            if key not in ["test_name", "success", "error", "duration_seconds", "total_events", 
                          "events_per_second", "peak_memory_mb", "avg_memory_mb", "pauses_detected"]:
                logger.info(f"{key}: {value}")
    
    logger.info("\n" + "="*80)

if __name__ == "__main__":
    logger.info("开始压力测试...")
    
    if not fixed_version_available:
        logger.warning("未找到修复版本，将使用原始版本进行测试")
    
    # 存储所有测试结果
    test_results = {}
    
    # 1. 大数据量测试
    test_results["大数据量测试"] = run_large_data_stress_test(rows=50000, run_time=30)
    
    # 2. 高频数据测试
    test_results["高频数据测试"] = run_high_frequency_stress_test(rows=20000, frequency_ms=5, run_time=30)
    
    # 3. 多数据源测试
    test_results["多数据源测试"] = run_multi_source_stress_test(source_count=5, rows_per_source=5000, run_time=30)
    
    # 4. 内存泄漏测试
    test_results["内存泄漏测试"] = run_memory_leak_test(iterations=5, rows=5000)
    
    # 5. 长时间运行测试 (减少时间以免测试时间过长)
    test_results["长时间运行测试"] = run_long_runtime_test(duration_minutes=2, data_size=5000)
    
    # 打印测试摘要
    print_test_summary(test_results)
    
    logger.info("压力测试完成") 