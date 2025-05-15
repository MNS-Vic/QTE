#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据重放控制器与引擎管理器集成演示

这个脚本展示了如何使用数据重放控制器与引擎管理器一起工作
"""
import sys
import os
import logging
import time
import threading
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

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
from qte.core.engine_manager import (
    ReplayEngineManager, 
    EngineType, 
    EngineStatus,
    MarketDataEvent,
    SignalEvent,
    OrderEvent,
    FillEvent
)
from qte.data.data_replay import (
    ReplayMode,
    ReplayStatus,
    DataFrameReplayController
)

def create_sample_data(symbol, rows=100, freq='1min'):
    """创建样本数据"""
    logger.info(f"为 {symbol} 创建 {rows} 行样本数据，频率: {freq}")
    
    # 创建时间索引
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=rows)
    date_range = pd.date_range(start=start_time, end=end_time, periods=rows)
    
    # 模拟价格数据
    initial_price = random.uniform(100, 1000)
    
    # 生成随机价格
    prices = [initial_price]
    for i in range(1, rows):
        # 生成一个随机变化率 (-1% 到 +1%)
        change_pct = random.uniform(-0.01, 0.01)
        new_price = prices[-1] * (1 + change_pct)
        prices.append(new_price)
    
    # 生成随机量
    volumes = [random.randint(1000, 10000) for _ in range(rows)]
    
    # 创建DataFrame
    df = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + random.uniform(0, 0.005)) for p in prices],
        'low': [p * (1 - random.uniform(0, 0.005)) for p in prices],
        'close': [p * (1 + random.uniform(-0.003, 0.003)) for p in prices],
        'volume': volumes,
        'symbol': symbol
    }, index=date_range)
    
    df.index.name = 'timestamp'
    
    logger.info(f"样本数据创建完成，形状: {df.shape}")
    return df

# 事件计数器 (线程安全)
class EventCounter:
    def __init__(self):
        self.counts = {}
        self.lock = threading.Lock()
    
    def count(self, event_type):
        with self.lock:
            if event_type not in self.counts:
                self.counts[event_type] = 0
            self.counts[event_type] += 1
    
    def get_counts(self):
        with self.lock:
            return self.counts.copy()

# 事件处理器
def handle_market_data(event, counter):
    counter.count("MARKET_DATA")
    if random.random() < 0.1:  # 10%的概率生成信号
        logger.info(f"收到市场数据: {event}")

def handle_signal(event, counter):
    counter.count("SIGNAL")
    logger.info(f"收到信号: {event}")

def handle_order(event, counter):
    counter.count("ORDER")
    logger.info(f"收到订单: {event}")

def handle_fill(event, counter):
    counter.count("FILL")
    logger.info(f"收到成交: {event}")

def generate_signals(engine_manager, event, counter):
    """根据市场数据生成信号"""
    if isinstance(event, MarketDataEvent):
        # 简单策略：随机生成信号
        if random.random() < 0.3:  # 30%的概率生成信号
            signal_type = random.choice(["BUY", "SELL"])
            strength = random.uniform(0.5, 1.0)
            
            signal_event = SignalEvent(
                timestamp=event.timestamp,
                symbol=event.symbol,
                signal_type=signal_type,
                strength=strength
            )
            
            engine_manager.send_event(signal_event)
            counter.count("SIGNAL_GENERATED")

def process_signals(engine_manager, event, counter):
    """处理信号并生成订单"""
    if isinstance(event, SignalEvent):
        # 根据信号生成订单
        quantity = random.randint(100, 1000)
        if event.signal_type == "SELL":
            quantity = -quantity
        
        order_event = OrderEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            order_type="MARKET",
            quantity=quantity
        )
        
        engine_manager.send_event(order_event)
        counter.count("ORDER_GENERATED")

def execute_orders(engine_manager, event, counter):
    """执行订单并生成成交"""
    if isinstance(event, OrderEvent):
        # 模拟执行订单
        price = random.uniform(90, 110)  # 模拟价格
        commission = abs(event.quantity) * price * 0.001  # 0.1%佣金
        
        fill_event = FillEvent(
            timestamp=event.timestamp,
            symbol=event.symbol,
            quantity=event.quantity,
            price=price,
            commission=commission,
            exchange="DEMO"
        )
        
        engine_manager.send_event(fill_event)
        counter.count("FILL_GENERATED")

def run_demo(mode=ReplayMode.ACCELERATED, speed_factor=5.0, duration=10):
    """运行演示"""
    logger.info(f"开始演示，模式: {mode.name}, 速度: {speed_factor}x, 持续时间: {duration}秒")
    
    # 创建事件计数器
    counter = EventCounter()
    
    # 创建样本数据
    sample_data = create_sample_data("000001.XSHE", rows=300, freq='1s')
    
    # 创建数据重放控制器
    controller = DataFrameReplayController(
        dataframe=sample_data,
        timestamp_column=None,  # 使用索引作为时间戳
        mode=mode,
        speed_factor=speed_factor
    )
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(engine_type=EngineType.EVENT_DRIVEN)
    
    # 初始化引擎管理器
    engine_manager.initialize()
    
    # 添加重放控制器
    engine_manager.add_replay_controller(
        name="demo_data",
        controller=controller,
        symbol="000001.XSHE"
    )
    
    # 注册事件处理器
    engine_manager.register_event_handler(
        "MARKET_DATA", 
        lambda event: handle_market_data(event, counter)
    )
    
    engine_manager.register_event_handler(
        "SIGNAL", 
        lambda event: handle_signal(event, counter)
    )
    
    engine_manager.register_event_handler(
        "ORDER", 
        lambda event: handle_order(event, counter)
    )
    
    engine_manager.register_event_handler(
        "FILL", 
        lambda event: handle_fill(event, counter)
    )
    
    # 注册策略处理器
    engine_manager.register_event_handler(
        "MARKET_DATA", 
        lambda event: generate_signals(engine_manager, event, counter)
    )
    
    engine_manager.register_event_handler(
        "SIGNAL", 
        lambda event: process_signals(engine_manager, event, counter)
    )
    
    engine_manager.register_event_handler(
        "ORDER", 
        lambda event: execute_orders(engine_manager, event, counter)
    )
    
    # 启动引擎
    engine_manager.start()
    
    try:
        # 运行指定时间
        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(0.5)
            
            # 打印实时状态
            if int((time.time() - start_time) * 2) % 4 == 0:
                logger.info(f"已运行 {time.time() - start_time:.1f} 秒, 事件计数: {counter.get_counts()}")
                
                # 获取性能统计
                stats = engine_manager.get_performance_stats()
                logger.info(f"引擎性能: {stats}")
        
    except KeyboardInterrupt:
        logger.info("用户中断演示")
    finally:
        # 停止引擎
        engine_manager.stop()
        
        # 打印最终统计
        logger.info("演示完成")
        logger.info(f"事件计数: {counter.get_counts()}")
        
        # 获取性能统计
        stats = engine_manager.get_performance_stats()
        logger.info(f"引擎性能: {stats}")

if __name__ == "__main__":
    # 运行三种模式的演示
    run_demo(mode=ReplayMode.BACKTEST, speed_factor=1.0, duration=5)
    run_demo(mode=ReplayMode.ACCELERATED, speed_factor=2.0, duration=10)
    run_demo(mode=ReplayMode.REALTIME, speed_factor=1.0, duration=15)