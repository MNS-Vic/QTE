#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据重放控制器和引擎管理器简单集成演示
"""

import os
import sys
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# 导入必要的模块
from qte.data.data_replay import (
    ReplayMode, ReplayStatus, 
    DataFrameReplayController
)

from qte.core.engine_manager import (
    EngineType, EngineStatus,
    EngineEvent, MarketDataEvent,
    ReplayEngineManager
)

# 创建测试数据
def create_test_data(size=10, symbol="TEST_SYMBOL"):
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=size, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'price': np.random.normal(100, 5, size),
        'volume': np.random.randint(1000, 2000, size),
        'symbol': [symbol] * size
    })
    return df

def main():
    """主函数"""
    print("开始数据重放引擎演示...")
    
    # 创建测试数据
    df = create_test_data()
    print(f"测试数据:\n{df.head()}")
    
    # 创建数据重放控制器
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    print("成功创建数据重放控制器")
    
    # 创建引擎管理器
    engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    print("成功创建引擎管理器")
    
    # 初始化引擎
    engine.initialize()
    print("成功初始化引擎")
    
    # 添加数据重放控制器
    engine.add_replay_controller("test_data", controller)
    print("成功添加数据重放控制器到引擎")
    
    # 注册事件处理器
    def on_market_data(event):
        print(f"收到市场数据: 时间={event.timestamp}, 标的={event.symbol}, 价格={event.data.get('price', 'N/A')}")
    
    engine.register_event_handler("MARKET_DATA", on_market_data)
    print("成功注册事件处理器")
    
    # 启动引擎
    print("\n启动引擎...")
    engine.start()
    
    # 等待数据处理完成
    time.sleep(1)
    
    # 停止引擎
    print("\n停止引擎...")
    engine.stop()
    
    # 获取性能统计
    stats = engine.get_performance_stats()
    print(f"\n性能统计:\n{stats}")
    
    print("\n演示完成!")
    
if __name__ == "__main__":
    main() 