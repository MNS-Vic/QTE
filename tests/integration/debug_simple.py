#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试简化版测试 - 着重检查事件循环是否正常工作
"""
import os
import sys
import time
import pandas as pd
from datetime import datetime
import threading

# 确保输出立即显示
import functools
print = functools.partial(print, flush=True)

print("=== 调试开始 ===")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置更详细的日志级别
import logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 导入核心类
print("导入模块...")
from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus
from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus

# 极简数据
print("创建极简数据...")
data = pd.DataFrame({
    'price': [100],
    'volume': [1000],
    'symbol': ['TEST']
}, index=pd.date_range('2023-01-01', periods=1))
data.index.name = 'timestamp'
print(data)

# 事件处理函数
def on_market_data(event):
    print(f"收到市场数据事件: {event}")
    return True

# 创建引擎和控制器
print("创建引擎和控制器...")
engine = ReplayEngineManager()
engine.initialize()

controller = DataFrameReplayController(
    dataframe=data,
    timestamp_column=None,
    mode=ReplayMode.BACKTEST,
    speed_factor=1.0
)

# 注册事件处理器
print("注册事件处理器...")
engine.register_event_handler("MARKET_DATA", on_market_data)

# 添加重放控制器
print("添加重放控制器...")
engine.add_replay_controller("test", controller, "TEST")

# 状态检查线程
def check_status():
    while True:
        status = engine.get_status()
        controller_status = controller.get_status() if hasattr(controller, 'get_status') else "未知"
        print(f"引擎状态: {status}, 控制器状态: {controller_status}")
        time.sleep(1)
        if status == EngineStatus.STOPPED or status == EngineStatus.COMPLETED:
            break

status_thread = threading.Thread(target=check_status)
status_thread.daemon = True

# 超时强制退出
def force_exit():
    print("超时强制退出!")
    # 尝试正常停止引擎
    try:
        engine.stop()
        print("引擎已停止")
    except:
        pass
    os._exit(0)  # 强制退出

timer = threading.Timer(10.0, force_exit)
timer.daemon = True

# 启动监控和定时器
print("启动监控...")
status_thread.start()
timer.start()

# 启动引擎
print("启动引擎...")
try:
    engine.start()
    print("引擎启动成功")
except Exception as e:
    print(f"引擎启动异常: {e}")

# 等待一段时间
print("等待引擎运行...")
time.sleep(3)

# 尝试手动步进一次
try:
    print("尝试手动步进...")
    if hasattr(controller, 'step'):
        result = controller.step()
        print(f"步进结果: {result}")
except Exception as e:
    print(f"步进异常: {e}")

# 停止引擎
print("停止引擎...")
engine.stop()

# 取消超时
timer.cancel()

# 获取性能统计
try:
    stats = engine.get_performance_stats()
    print(f"性能统计: {stats}")
except Exception as e:
    print(f"获取性能统计异常: {e}")

print("=== 调试结束 ===")