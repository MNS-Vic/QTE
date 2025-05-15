#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据重放调试脚本

提供详细的日志输出和强制停止机制
"""
import sys
import os
import logging
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import signal

# 设置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置模块日志级别
logging.getLogger("qte.core.engine_manager").setLevel(logging.DEBUG)
logging.getLogger("qte.data.data_replay").setLevel(logging.DEBUG)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"已添加项目根目录到 Python 路径: {project_root}")

# 导入必要的模块
from qte.core.engine_manager import (
    ReplayEngineManager, 
    EngineType, 
    EngineStatus,
    MarketDataEvent,
    SignalEvent
)
from qte.data.data_replay import (
    ReplayMode,
    ReplayStatus,
    DataFrameReplayController
)

# 全局变量，用于跟踪事件
event_counter = {}
event_lock = threading.Lock()
last_event_time = None

def create_test_data():
    """创建测试数据"""
    # 创建时间索引
    rows = 50
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

def on_event(event):
    """通用事件处理器"""
    global last_event_time
    
    with event_lock:
        event_type = event.event_type
        if event_type not in event_counter:
            event_counter[event_type] = 0
        event_counter[event_type] += 1
        last_event_time = datetime.now()
    
    logger.info(f"收到事件: {event}, 类型: {event_type}")

def on_market_data(event):
    """市场数据事件处理器"""
    if isinstance(event, MarketDataEvent):
        with event_lock:
            if "MARKET_DATA" not in event_counter:
                event_counter["MARKET_DATA"] = 0
            event_counter["MARKET_DATA"] += 1
            
        logger.info(f"收到市场数据: 符号={event.symbol}, 时间戳={event.timestamp}")
        
        # 30%的概率生成信号
        if np.random.random() < 0.3:
            signal_event = SignalEvent(
                timestamp=event.timestamp,
                symbol=event.symbol,
                signal_type="BUY" if np.random.random() > 0.5 else "SELL",
                strength=np.random.random()
            )
            return signal_event
    
    return None

def print_stats():
    """打印统计信息"""
    with event_lock:
        logger.info(f"事件计数: {event_counter}")
        logger.info(f"最后一个事件时间: {last_event_time}")

def signal_handler(signum, frame):
    """信号处理器，用于强制退出"""
    logger.warning(f"收到信号 {signum}，强制退出")
    print_stats()
    sys.exit(0)

def main():
    """主函数"""
    logger.info("启动数据重放调试...")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    
    # 创建测试数据
    test_data = create_test_data()
    
    # 创建数据重放控制器
    controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column=None,  # 使用索引作为时间戳
        mode=ReplayMode.ACCELERATED,
        speed_factor=2.0
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
    market_data_handler_id = engine_manager.register_event_handler(
        "MARKET_DATA", 
        lambda event: on_market_data(event)
    )
    
    signal_handler_id = engine_manager.register_event_handler(
        "SIGNAL", 
        lambda event: on_event(event)
    )
    
    # 设置超时强制退出
    def force_stop():
        logger.warning("超时，强制停止")
        engine_manager.stop()
        print_stats()
    
    timeout = threading.Timer(15.0, force_stop)
    timeout.start()
    
    try:
        # 启动引擎
        logger.info("启动引擎...")
        engine_manager.start()
        
        # 等待一段时间
        start_time = time.time()
        max_duration = 10.0  # 最长运行10秒
        
        while time.time() - start_time < max_duration:
            time.sleep(1.0)
            logger.info(f"运行中，已经过 {time.time() - start_time:.1f} 秒")
            
            # 每2秒打印一次状态
            if int(time.time() - start_time) % 2 == 0:
                print_stats()
                
                # 获取引擎状态
                status = engine_manager.get_status()
                logger.info(f"引擎状态: {status.name}")
                
                # 获取性能统计
                stats = engine_manager.get_performance_stats()
                logger.info(f"引擎性能: {stats}")
        
    except Exception as e:
        logger.error(f"发生异常: {str(e)}")
    finally:
        # 取消超时
        timeout.cancel()
        
        # 停止引擎
        logger.info("停止引擎...")
        engine_manager.stop()
        
        # 打印最终统计
        print_stats()
        
        logger.info("调试完成")

if __name__ == "__main__":
    main()