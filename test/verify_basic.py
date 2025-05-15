#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最基本的验证脚本

只测试数据重放控制器与引擎管理器的最基本功能
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime

# 确保输出立即显示
import functools
print = functools.partial(print, flush=True)

print("=== 基本验证开始 ===")

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
print(f"项目根目录: {root_dir}")

# 导入基本类
print("导入必要的类...")
from qte.data.data_replay import ReplayMode, DataFrameReplayController
from qte.core.engine_manager import EngineType, EngineStatus, ReplayEngineManager

print("创建最小测试数据...")
# 创建极简数据
dates = pd.date_range(start='2023-01-01 09:30:00', periods=3, freq='1min')
data = pd.DataFrame({
    'timestamp': dates,
    'symbol': ['000001.SZ'] * 3,
    'price': [100, 101, 102]
})
print(data)

print("\n创建数据重放控制器...")
controller = DataFrameReplayController(
    dataframe=data,
    timestamp_column='timestamp',
    mode=ReplayMode.BACKTEST
)

print("\n创建引擎管理器...")
engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
engine.initialize()

# 计数器和锁，用于线程安全的事件计数
import threading
event_count = 0
event_lock = threading.Lock()

print("\n定义事件处理器...")
def on_market_data(event):
    global event_count
    with event_lock:
        event_count += 1
    print(f"收到事件 #{event_count}: {event.timestamp} | {event.symbol} | 价格={event.data.get('price')}")

print("\n注册事件处理器...")
engine.register_event_handler("MARKET_DATA", on_market_data)

print("\n添加数据重放控制器...")
engine.add_replay_controller("test", controller)

print("\n启动引擎...")
start_time = time.time()
engine.start()

max_wait = 5  # 秒
print(f"\n最多等待 {max_wait} 秒...")

# 循环检查，直到所有事件都处理完或超时
while time.time() - start_time < max_wait:
    current_count = 0
    with event_lock:
        current_count = event_count
    
    print(f"已处理 {current_count}/{len(data)} 个事件，当前状态: {engine.get_status()}")
    
    # 如果所有事件都已处理，或者引擎已停止，则退出
    if current_count >= len(data) or engine.get_status() == EngineStatus.STOPPED:
        break
        
    time.sleep(0.5)

# 停止引擎
if engine.get_status() != EngineStatus.STOPPED:
    print("手动停止引擎...")
    engine.stop()

# 最终检查
final_count = 0
with event_lock:
    final_count = event_count

print(f"\n总共处理了 {final_count}/{len(data)} 个事件，总耗时: {time.time() - start_time:.2f} 秒")

# 评估结果
success = final_count == len(data)
print(f"\n测试{'成功' if success else '失败'}!")

# 退出码
sys.exit(0 if success else 1) 