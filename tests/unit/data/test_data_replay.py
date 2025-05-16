"""
数据重放控制器示例脚本

演示如何使用数据重放控制器的各种功能，包括不同模式的重放、暂停/恢复等
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qte.data import (
    ReplayMode,
    ReplayStatus,
    DataFrameReplayController,
    MultiSourceReplayController
)

def create_test_data(size=100):
    """创建测试数据"""
    # 创建日期范围（每分钟一个点）
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=size, freq='1min')
    
    # 创建价格数据（模拟股票价格）
    prices = np.cumsum(np.random.normal(0, 1, size)) + 100
    
    # 创建成交量数据
    volumes = np.abs(np.random.normal(10000, 5000, size)).astype(int)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'price': prices,
        'volume': volumes
    })
    
    return df

def basic_replay_example():
    """基本重放示例"""
    print("\n===== 基本重放示例 =====")
    
    # 创建测试数据
    df = create_test_data(10)
    print(f"测试数据预览:\n{df.head()}")
    
    # 创建重放控制器（回测模式）
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 定义回调函数
    def on_data_point(data):
        print(f"收到数据点: 时间={data['timestamp']}, 价格={data['price']:.2f}")
    
    # 注册回调
    controller.register_callback(on_data_point)
    
    # 启动重放
    print("\n启动回测模式重放...")
    controller.start()
    
    # 等待重放完成
    time.sleep(1)
    
    # 检查状态
    print(f"重放状态: {controller.get_status().name}")

def stepped_replay_example():
    """步进模式重放示例"""
    print("\n===== 步进模式重放示例 =====")
    
    # 创建测试数据
    df = create_test_data(5)
    
    # 创建重放控制器（步进模式）
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.STEPPED
    )
    
    # 手动逐步推进
    print("\n开始手动步进...")
    for i in range(len(df) + 1):  # +1 是为了测试越界情况
        data = controller.step()
        if data is not None:
            print(f"步进 {i+1}: 时间={data['timestamp']}, 价格={data['price']:.2f}")
        else:
            print(f"步进 {i+1}: 没有更多数据")
    
    # 检查状态
    print(f"重放状态: {controller.get_status().name}")

def realtime_replay_example():
    """实时模式重放示例"""
    print("\n===== 实时模式重放示例 =====")
    
    # 创建测试数据（时间间隔较短）
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=5, freq='2s')
    df = pd.DataFrame({
        'timestamp': dates,
        'price': [100, 101, 102, 101.5, 102.5],
        'volume': [10000, 12000, 9000, 11000, 13000]
    })
    
    # 创建重放控制器（实时模式）
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.REALTIME
    )
    
    # 定义回调函数
    def on_data_point(data):
        print(f"收到数据点: 时间={data['timestamp']}, 价格={data['price']:.2f}")
    
    # 注册回调
    controller.register_callback(on_data_point)
    
    # 启动重放
    print("\n启动实时模式重放...")
    start_time = time.time()
    controller.start()
    
    # 等待重放完成（大约需要8秒）
    while controller.get_status() != ReplayStatus.COMPLETED:
        time.sleep(0.1)
    
    # 计算实际耗时
    elapsed = time.time() - start_time
    print(f"重放完成，耗时: {elapsed:.2f}秒")
    print(f"重放状态: {controller.get_status().name}")

def pause_resume_example():
    """暂停和恢复示例"""
    print("\n===== 暂停和恢复示例 =====")
    
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=10, freq='1s')
    df = pd.DataFrame({
        'timestamp': dates,
        'price': np.linspace(100, 110, 10),
        'volume': [10000] * 10
    })
    
    # 创建重放控制器
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.REALTIME,
        speed_factor=0.5  # 减速播放
    )
    
    # 定义回调函数
    def on_data_point(data):
        print(f"收到数据点: 时间={data['timestamp']}, 价格={data['price']:.2f}")
    
    # 注册回调
    controller.register_callback(on_data_point)
    
    # 启动重放
    print("\n启动实时模式重放...")
    controller.start()
    
    # 等待几秒钟
    time.sleep(3)
    
    # 暂停
    print("\n暂停重放...")
    controller.pause()
    print(f"重放状态: {controller.get_status().name}")
    
    # 等待一段时间
    print("等待2秒...")
    time.sleep(2)
    
    # 恢复
    print("\n恢复重放...")
    controller.resume()
    print(f"重放状态: {controller.get_status().name}")
    
    # 等待完成
    while controller.get_status() != ReplayStatus.COMPLETED:
        time.sleep(0.1)
    
    print("\n重放完成")
    print(f"重放状态: {controller.get_status().name}")

def speed_control_example():
    """速度控制示例"""
    print("\n===== 速度控制示例 =====")
    
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=5, freq='5s')
    df = pd.DataFrame({
        'timestamp': dates,
        'price': np.linspace(100, 105, 5),
        'volume': [10000] * 5
    })
    
    # 测试不同速度因子
    for speed in [0.5, 1.0, 2.0]:
        print(f"\n== 速度因子: {speed} ==")
        
        # 创建重放控制器
        controller = DataFrameReplayController(
            dataframe=df,
            timestamp_column='timestamp',
            mode=ReplayMode.REALTIME,
            speed_factor=speed
        )
        
        # 定义回调函数
        receive_count = [0]  # 使用列表以便在闭包中修改
        def on_data_point(data):
            receive_count[0] += 1
            print(f"收到数据点 {receive_count[0]}: 时间={data['timestamp']}, 价格={data['price']:.2f}")
        
        # 注册回调
        controller.register_callback(on_data_point)
        
        # 启动重放
        print(f"开始重放，速度因子={speed}...")
        start_time = time.time()
        controller.start()
        
        # 等待重放完成
        while controller.get_status() != ReplayStatus.COMPLETED:
            time.sleep(0.1)
        
        # 计算实际耗时
        elapsed = time.time() - start_time
        print(f"重放完成，耗时: {elapsed:.2f}秒")

def multi_source_example():
    """多数据源重放示例"""
    print("\n===== 多数据源重放示例 =====")
    
    # 创建两个数据源
    # 数据源1：股票价格数据
    dates1 = pd.date_range(start='2023-01-01 09:30:00', periods=5, freq='1min')
    df1 = pd.DataFrame({
        'timestamp': dates1,
        'price': [100, 101, 102, 101, 103],
        'symbol': ['AAPL'] * 5
    })
    
    # 数据源2：市场指数数据，时间点与股票数据交错
    dates2 = pd.date_range(start='2023-01-01 09:30:30', periods=5, freq='1min')
    df2 = pd.DataFrame({
        'timestamp': dates2,
        'index_value': [1000, 1005, 1010, 1008, 1015],
        'symbol': ['SPY'] * 5
    })
    
    print(f"数据源1预览:\n{df1.head()}")
    print(f"\n数据源2预览:\n{df2.head()}")
    
    # 创建多数据源重放控制器
    controller = MultiSourceReplayController(
        data_sources={'stock': df1, 'index': df2},
        timestamp_extractors={
            'stock': lambda x: x['timestamp'],
            'index': lambda x: x['timestamp']
        },
        mode=ReplayMode.BACKTEST
    )
    
    # 定义回调函数
    def on_data_point(data):
        source = data['_source']
        if source == 'stock':
            print(f"收到股票数据: 时间={data['timestamp']}, 价格={data['price']}")
        else:
            print(f"收到指数数据: 时间={data['timestamp']}, 指数={data['index_value']}")
    
    # 注册回调
    controller.register_callback(on_data_point)
    
    # 启动重放
    print("\n启动多数据源重放...")
    controller.start()
    
    # 等待重放完成
    time.sleep(1)
    
    # 检查状态
    print(f"重放状态: {controller.get_status().name}")

if __name__ == "__main__":
    # 运行所有示例
    basic_replay_example()
    stepped_replay_example()
    realtime_replay_example()
    pause_resume_example()
    speed_control_example()
    multi_source_example()
    
    print("\n所有示例运行完成!") 