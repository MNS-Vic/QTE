#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
超简化版测试脚本 - 确保能看到完整执行结果
"""
import os
import sys
import time
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 立即输出打印内容
import functools
print = functools.partial(print, flush=True)

print("=== 测试开始 ===")

# 导入核心类
print("导入模块...")
from qte.core.engine_manager import ReplayEngineManager, EngineType
from qte.data.data_replay import DataFrameReplayController, ReplayMode

# 创建极简数据
print("创建极简数据...")
data = pd.DataFrame({
    'price': [100, 101, 102],
    'volume': [1000, 1100, 1200],
    'symbol': ['TEST'] * 3
}, index=pd.date_range('2023-01-01', periods=3))
data.index.name = 'timestamp'
print(data)

# 创建事件计数器
event_count = 0

# 定义事件处理函数
def on_market_data(event):
    global event_count
    event_count += 1
    print(f"收到事件 #{event_count}: {event.symbol} | 价格={event.data.get('price')}")

# 创建数据重放控制器
print("创建数据重放控制器...")
controller = DataFrameReplayController(
    dataframe=data,
    timestamp_column=None,  # 使用索引作为时间戳
    mode=ReplayMode.BACKTEST,
    speed_factor=1.0
)

# 创建引擎管理器
print("创建引擎管理器...")
engine = ReplayEngineManager()
engine.initialize()

# 注册事件处理器
print("注册事件处理器...")
engine.register_event_handler("MARKET_DATA", on_market_data)

# 添加重放控制器
print("添加重放控制器...")
engine.add_replay_controller("test", controller, "TEST")

# 设置超时强制退出
def force_exit():
    print("超时强制退出!")
    os._exit(0)  # 强制退出

import threading
timer = threading.Timer(5.0, force_exit)
timer.daemon = True
timer.start()

# 启动引擎
print("启动引擎...")
engine.start()

# 等待极短时间
print("等待数据处理...")
time.sleep(1)  # 仅等待1秒

# 停止引擎
print("停止引擎...")
engine.stop()

# 取消超时
timer.cancel()

# 打印结果
print(f"总共处理了 {event_count}/{len(data)} 个事件")
print(f"测试{'成功' if event_count == len(data) else '失败'}")

# 退出
print("=== 测试结束 ===")