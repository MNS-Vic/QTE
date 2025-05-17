"""
数据重放控制器性能优化示例

此示例展示如何使用内存优化和回调批处理来提高数据重放性能
"""

import pandas as pd
import numpy as np
import time
import logging
import threading
import queue
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("performance_test")

# 导入数据重放模块
from qte.data.data_replay import (
    DataFrameReplayController, 
    MultiSourceReplayController,
    ReplayMode
)

def create_test_data(size=100000):
    """创建测试数据集"""
    logger.info(f"创建测试数据集 ({size:,}行)")
    
    # 创建日期索引
    dates = pd.date_range(start='2023-01-01', periods=size, freq='1min')
    
    # 创建价格数据 (模拟随机游走)
    prices = 100 + np.cumsum(np.random.normal(0, 0.1, size))
    volumes = np.random.randint(1000, 10000, size)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'price': prices,
        'volume': volumes
    }, index=dates)
    
    logger.info(f"测试数据集创建完成，大小: {df.memory_usage().sum() / (1024*1024):.2f} MB")
    return df

def test_standard_mode(df):
    """测试标准模式性能"""
    logger.info("测试 - 标准模式")
    
    start_time = time.time()
    
    # 创建标准控制器
    controller = DataFrameReplayController(df)
    
    # 记录处理数据
    processed_count = 0
    
    # 简单计数回调
    def counter_callback(data):
        nonlocal processed_count
        processed_count += 1
    
    # 注册回调
    controller.register_callback(counter_callback)
    
    # 处理所有数据
    all_data = controller.process_all_sync()
    
    elapsed = time.time() - start_time
    logger.info(f"标准模式处理耗时: {elapsed:.4f}秒")
    logger.info(f"处理了 {processed_count:,} 条数据")
    logger.info(f"处理速度: {processed_count/elapsed:.2f} 条/秒")
    
    return elapsed

def test_memory_optimized(df):
    """测试内存优化模式性能"""
    logger.info("测试 - 内存优化模式")
    
    start_time = time.time()
    
    # 创建内存优化控制器
    controller = DataFrameReplayController(
        df, 
        memory_optimized=True
    )
    
    # 记录处理数据
    processed_count = 0
    
    # 简单计数回调
    def counter_callback(data):
        nonlocal processed_count
        processed_count += 1
    
    # 注册回调
    controller.register_callback(counter_callback)
    
    # 处理所有数据
    all_data = controller.process_all_sync()
    
    elapsed = time.time() - start_time
    logger.info(f"内存优化模式处理耗时: {elapsed:.4f}秒")
    logger.info(f"处理了 {processed_count:,} 条数据")
    logger.info(f"处理速度: {processed_count/elapsed:.2f} 条/秒")
    
    return elapsed

def test_batch_callbacks(df):
    """测试批量回调处理性能"""
    logger.info("测试 - 批量回调处理")
    
    start_time = time.time()
    
    # 创建启用批量回调的控制器
    controller = DataFrameReplayController(
        df, 
        batch_callbacks=True
    )
    
    # 记录处理数据
    processed_count = 0
    
    # 互斥锁，避免多线程计数冲突
    count_lock = threading.Lock()
    
    # 简单计数回调
    def counter_callback(data):
        nonlocal processed_count
        with count_lock:
            processed_count += 1
    
    # 注册回调
    controller.register_callback(counter_callback)
    
    # 处理所有数据
    all_data = controller.process_all_sync()
    
    # 等待回调处理完成
    time.sleep(0.5)
    
    elapsed = time.time() - start_time
    logger.info(f"批量回调模式处理耗时: {elapsed:.4f}秒")
    logger.info(f"处理了 {processed_count:,} 条数据")
    logger.info(f"处理速度: {processed_count/elapsed:.2f} 条/秒")
    
    return elapsed

def test_combined_optimizations(df):
    """测试综合优化 (内存优化 + 批量回调)"""
    logger.info("测试 - 内存优化+批量回调")
    
    start_time = time.time()
    
    # 创建综合优化控制器
    controller = DataFrameReplayController(
        df, 
        memory_optimized=True,
        batch_callbacks=True
    )
    
    # 记录处理数据
    processed_count = 0
    
    # 互斥锁，避免多线程计数冲突
    count_lock = threading.Lock()
    
    # 简单计数回调
    def counter_callback(data):
        nonlocal processed_count
        with count_lock:
            processed_count += 1
    
    # 注册回调
    controller.register_callback(counter_callback)
    
    # 处理所有数据
    all_data = controller.process_all_sync()
    
    # 等待回调处理完成
    time.sleep(0.5)
    
    elapsed = time.time() - start_time
    logger.info(f"综合优化模式处理耗时: {elapsed:.4f}秒")
    logger.info(f"处理了 {processed_count:,} 条数据")
    logger.info(f"处理速度: {processed_count/elapsed:.2f} 条/秒")
    
    return elapsed

def test_multi_source_optimized():
    """测试多数据源内存优化"""
    logger.info("测试 - 多数据源内存优化")
    
    # 创建多个测试数据集
    prices_df = create_test_data(50000)
    volumes_df = create_test_data(80000)
    indicators_df = create_test_data(30000)
    
    start_time = time.time()
    
    # 创建优化的多数据源控制器
    controller = MultiSourceReplayController(
        data_sources={
            'prices': prices_df,
            'volumes': volumes_df,
            'indicators': indicators_df
        },
        memory_optimized=True,
    )
    
    # 记录处理数据
    processed_count = 0
    
    # 简单计数回调
    def counter_callback(data):
        nonlocal processed_count
        processed_count += 1
    
    # 注册回调
    controller.register_callback(counter_callback)
    
    # 处理所有数据
    all_data = controller.process_all_sync()
    
    elapsed = time.time() - start_time
    logger.info(f"多数据源优化模式处理耗时: {elapsed:.4f}秒")
    logger.info(f"处理了 {processed_count:,} 条数据")
    logger.info(f"处理速度: {processed_count/elapsed:.2f} 条/秒")
    
    return elapsed

def test_optimized_callback_design():
    """测试优化的回调设计模式"""
    logger.info("测试 - 优化的回调设计模式")
    
    # 创建测试数据
    df = create_test_data(50000)
    
    start_time = time.time()
    
    # 创建处理队列和线程
    processing_queue = queue.Queue()
    processed_count = 0
    should_exit = False
    
    # 处理线程
    def processing_worker():
        nonlocal processed_count
        while not should_exit:
            try:
                # 尝试从队列获取数据，超时0.1秒
                batch = processing_queue.get(timeout=0.1)
                
                # 处理数据（实际应用中会有更复杂的逻辑）
                processed_count += len(batch)
                
                # 标记任务完成
                processing_queue.task_done()
            except queue.Empty:
                # 队列为空，等待下一次循环
                continue
    
    # 启动处理线程
    worker_thread = threading.Thread(target=processing_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    # 数据收集器
    batch_size = 100
    collected_data = []
    
    # 优化的批量回调
    def batch_callback(data):
        collected_data.append(data)
        
        # 达到批处理阈值，放入处理队列
        if len(collected_data) >= batch_size:
            processing_queue.put(collected_data[:])
            collected_data.clear()
    
    # 创建控制器
    controller = DataFrameReplayController(df)
    controller.register_callback(batch_callback)
    
    # 处理所有数据
    all_data = controller.process_all_sync()
    
    # 确保最后一批数据也被处理
    if collected_data:
        processing_queue.put(collected_data[:])
        collected_data.clear()
    
    # 等待队列处理完成
    processing_queue.join()
    
    # 准备退出
    should_exit = True
    worker_thread.join(timeout=1.0)
    
    elapsed = time.time() - start_time
    logger.info(f"优化回调设计模式处理耗时: {elapsed:.4f}秒")
    logger.info(f"处理了 {processed_count:,} 条数据")
    logger.info(f"处理速度: {processed_count/elapsed:.2f} 条/秒")
    
    return elapsed

def run_all_tests():
    """运行所有测试并对比结果"""
    logger.info("开始性能测试")
    
    # 创建测试数据
    test_size = 100000  # 默认10万行，可根据需要调整
    df = create_test_data(test_size)
    
    # 运行各种测试
    standard_time = test_standard_mode(df)
    memory_time = test_memory_optimized(df)
    batch_time = test_batch_callbacks(df)
    combined_time = test_combined_optimizations(df)
    
    # 计算性能提升
    memory_improvement = (standard_time - memory_time) / standard_time * 100
    batch_improvement = (standard_time - batch_time) / standard_time * 100
    combined_improvement = (standard_time - combined_time) / standard_time * 100
    
    # 输出对比结果
    logger.info("\n=== 性能对比结果 ===")
    logger.info(f"标准模式:              {standard_time:.2f}秒")
    logger.info(f"内存优化模式:           {memory_time:.2f}秒 (提升{memory_improvement:.1f}%)")
    logger.info(f"批量回调处理:           {batch_time:.2f}秒 (提升{batch_improvement:.1f}%)")
    logger.info(f"内存优化+批量回调:       {combined_time:.2f}秒 (提升{combined_improvement:.1f}%)")
    
    # 测试多数据源优化
    logger.info("\n=== 附加测试 ===")
    multi_time = test_multi_source_optimized()
    optimized_callback_time = test_optimized_callback_design()
    
    logger.info("\n性能测试完成")

if __name__ == "__main__":
    run_all_tests() 