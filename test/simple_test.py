#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试脚本

快速测试数据重放控制器与引擎管理器的集成
"""
import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"已添加项目根目录到 Python 路径: {project_root}")

# 导入必要的模块
from qte.core.engine_manager import ReplayEngineManager, EngineType
from qte.data.data_replay import DataFrameReplayController, ReplayMode

def create_test_data(rows=20):
    """创建测试数据"""
    # 创建时间索引
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=rows)
    date_range = pd.date_range(start=start_time, end=end_time, periods=rows)
    
    # 模拟价格数据
    prices = 100 + np.cumsum(np.random.normal(0, 1, rows))
    volumes = np.random.randint(1000, 10000, rows)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'price': prices,
        'volume': volumes,
        'symbol': 'TEST'
    }, index=date_range)
    
    df.index.name = 'timestamp'
    return df

def on_market_data(event):
    """市场数据事件处理器"""
    logger.info(f"收到市场数据: {event}")

def main():
    """主函数"""
    logger.info("启动简单测试...")
    
    # 创建测试数据
    test_data = create_test_data()
    
    # 创建数据重放控制器
    controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column=None,  # 使用索引作为时间戳
        mode=ReplayMode.BACKTEST,
        speed_factor=1.0
    )
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(engine_type=EngineType.EVENT_DRIVEN)
    
    # 初始化引擎管理器
    engine_manager.initialize()
    
    # 添加重放控制器
    engine_manager.add_replay_controller(
        name="test_data",
        controller=controller,
        symbol="TEST"
    )
    
    # 注册事件处理器
    engine_manager.register_event_handler("MARKET_DATA", on_market_data)
    
    # 启动引擎
    logger.info("启动引擎...")
    engine_manager.start()
    
    # 等待数据处理完成
    time.sleep(1.0)
    
    # 打印性能统计
    stats = engine_manager.get_performance_stats()
    logger.info(f"引擎性能统计: {stats}")
    
    # 停止引擎
    logger.info("停止引擎...")
    engine_manager.stop()
    
    logger.info("测试完成")

if __name__ == "__main__":
    main()