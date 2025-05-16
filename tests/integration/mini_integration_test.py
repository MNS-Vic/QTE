#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版集成测试 - 数据重放控制器与引擎管理器
"""
import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
import threading

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 打印调试信息
print("=== 集成测试开始 ===")

# 导入核心类
print("\n导入模块...")
from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus, MarketDataEvent
from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus

print("\n创建测试数据...")
# 创建测试数据
dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
data = pd.DataFrame({
    'price': [100, 101, 102, 103, 104],
    'volume': [1000, 1100, 1200, 1300, 1400],
    'symbol': ['TEST'] * 5
}, index=dates)
data.index.name = 'timestamp'
print(data)

print("\n创建事件计数器...")
# 创建事件计数器
event_count = 0
event_lock = threading.Lock()

# 定义事件处理函数
def on_market_data(event):
    global event_count
    with event_lock:
        event_count += 1
    print(f"收到事件 #{event_count}: {event.timestamp} | {event.symbol} | 数据: {event.data}")

print("\n创建数据重放控制器...")
# 创建数据重放控制器
controller = DataFrameReplayController(
    dataframe=data,
    timestamp_column=None,  # 使用索引作为时间戳
    mode=ReplayMode.BACKTEST,
    speed_factor=1.0
)

print("\n创建引擎管理器...")
# 创建引擎管理器
engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
engine.initialize()

print("\n注册事件处理器...")
# 注册事件处理器
handler_id = engine.register_event_handler("MARKET_DATA", on_market_data)
print(f"处理器ID: {handler_id}")

print("\n添加重放控制器...")
# 添加重放控制器
engine.add_replay_controller("test", controller, "TEST")

print("\n启动引擎...")
# 启动引擎
engine.start()

print("\n等待数据处理...")
# 等待处理完成
start_time = time.time()
max_wait = 5.0  # 最多等待5秒

while time.time() - start_time < max_wait:
    # 获取当前计数
    with event_lock:
        current_count = event_count
    
    # 获取引擎状态
    status = engine.get_status()
    print(f"已处理 {current_count}/{len(data)} 个事件，引擎状态: {status.name}")
    
    # 如果处理完成或引擎已停止，则退出
    if current_count >= len(data) or status == EngineStatus.COMPLETED or status == EngineStatus.STOPPED:
        break
    
    # 短暂等待
    time.sleep(0.5)

print("\n停止引擎...")
# 停止引擎
engine.stop()

# 检查结果
with event_lock:
    final_count = event_count

print(f"\n测试结果: 处理了 {final_count}/{len(data)} 个事件")
print(f"测试{'成功' if final_count == len(data) else '失败'}")

# 获取性能统计
stats = engine.get_performance_stats()
print(f"\n性能统计: {stats}")

print("\n=== 集成测试结束 ===")