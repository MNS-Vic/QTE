#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多数据源重放演示

这个脚本展示了如何使用多数据源重放控制器与引擎管理器一起工作
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
    DataFrameReplayController,
    MultiSourceReplayController
)

def create_sample_data(symbol, rows=100, freq='1min', volatility=0.01):
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
        change_pct = random.uniform(-volatility, volatility)
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

def create_market_indicator_data(rows=100, freq='1min'):
    """创建市场指标数据"""
    logger.info(f"创建 {rows} 行市场指标数据")
    
    # 创建时间索引
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=rows)
    date_range = pd.date_range(start=start_time, end=end_time, periods=rows)
    
    # 生成指标数据
    market_index = [10000]
    for i in range(1, rows):
        change_pct = random.uniform(-0.005, 0.005)
        new_index = market_index[-1] * (1 + change_pct)
        market_index.append(new_index)
    
    volatility = [random.uniform(0.5, 2.0) for _ in range(rows)]
    pe_ratio = [random.uniform(10, 30) for _ in range(rows)]
    
    # 创建DataFrame
    df = pd.DataFrame({
        'market_index': market_index,
        'volatility': volatility,
        'pe_ratio': pe_ratio
    }, index=date_range)
    
    df.index.name = 'timestamp'
    
    logger.info(f"市场指标数据创建完成，形状: {df.shape}")
    return df

def create_news_events(rows=20):
    """创建新闻事件数据"""
    logger.info(f"创建 {rows} 条新闻事件数据")
    
    # 创建时间索引 (新闻事件比交易数据少)
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=100)
    
    # 随机选择时间点
    timestamps = [start_time + timedelta(minutes=random.randint(0, 100)) for _ in range(rows)]
    timestamps.sort()
    
    # 生成新闻标题和影响
    news_titles = [
        "市场震荡加剧",
        "央行降息25个基点",
        "上市公司财报普遍向好",
        "贸易政策调整",
        "重大技术突破",
        "国际政治局势紧张",
        "市场监管政策收紧",
        "行业龙头公司重组",
        "宏观经济数据超预期",
        "重大资产并购完成"
    ]
    
    titles = [random.choice(news_titles) for _ in range(rows)]
    impacts = [random.uniform(-5, 5) for _ in range(rows)]  # 负值表示负面影响
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'title': titles,
        'impact': impacts
    })
    
    logger.info(f"新闻事件数据创建完成，形状: {df.shape}")
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

# 转换函数：将市场指标数据转换为事件
def convert_market_indicator(data, timestamp, symbol):
    """将市场指标数据转换为事件"""
    event = MarketDataEvent(timestamp, "MARKET_INDEX", data)
    event.market_data_type = "INDICATOR"
    return event

# 转换函数：将新闻事件转换为引擎事件
def convert_news_event(data, timestamp, symbol):
    """将新闻事件转换为自定义事件类型"""
    event_data = {
        "title": data.get("title", ""),
        "impact": data.get("impact", 0)
    }
    event = EngineEvent("NEWS", timestamp, event_data)
    return event

# 事件处理器
def handle_market_data(event, counter):
    """处理市场数据事件"""
    counter.count("MARKET_DATA")
    if random.random() < 0.1:  # 10%的概率打印日志
        logger.info(f"收到市场数据: {event}, 源: {event.source}")

def handle_news_event(event, counter):
    """处理新闻事件"""
    counter.count("NEWS")
    logger.info(f"收到新闻事件: {event.event_type}, 数据: {event.data}")

def run_demo(mode=ReplayMode.ACCELERATED, speed_factor=5.0, duration=10):
    """运行多数据源演示"""
    logger.info(f"开始多数据源演示，模式: {mode.name}, 速度: {speed_factor}x, 持续: {duration}秒")
    
    # 创建事件计数器
    counter = EventCounter()
    
    # 创建样本数据
    stock_data_1 = create_sample_data("000001.XSHE", rows=300, freq='1s', volatility=0.01)
    stock_data_2 = create_sample_data("600000.XSHG", rows=300, freq='1s', volatility=0.02)
    market_data = create_market_indicator_data(rows=150, freq='2s')
    news_data = create_news_events(rows=20)
    
    # 创建单独的数据重放控制器
    controller_1 = DataFrameReplayController(
        dataframe=stock_data_1,
        timestamp_column=None,  # 使用索引作为时间戳
        mode=mode,
        speed_factor=speed_factor
    )
    
    controller_2 = DataFrameReplayController(
        dataframe=stock_data_2,
        timestamp_column=None,  # 使用索引作为时间戳
        mode=mode,
        speed_factor=speed_factor
    )
    
    # 创建多数据源重放控制器
    multi_source_data = {
        "market_index": market_data,
        "news": news_data
    }
    
    # 时间戳提取函数
    timestamp_extractors = {
        "news": lambda data: data.get("timestamp", datetime.now())
    }
    
    multi_controller = MultiSourceReplayController(
        data_sources=multi_source_data,
        timestamp_extractors=timestamp_extractors,
        mode=mode,
        speed_factor=speed_factor
    )
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(engine_type=EngineType.EVENT_DRIVEN)
    
    # 初始化引擎管理器
    engine_manager.initialize()
    
    # 添加重放控制器
    engine_manager.add_replay_controller(
        name="stock_1",
        controller=controller_1,
        symbol="000001.XSHE"
    )
    
    engine_manager.add_replay_controller(
        name="stock_2",
        controller=controller_2,
        symbol="600000.XSHG"
    )
    
    engine_manager.add_replay_controller(
        name="market_index",
        controller=multi_controller,
        symbol=None,  # 将使用数据源标识
        data_converter=lambda data, timestamp, symbol: (
            convert_market_indicator(data, timestamp, symbol) 
            if symbol == "market_index" 
            else convert_news_event(data, timestamp, symbol)
        )
    )
    
    # 注册事件处理器
    engine_manager.register_event_handler(
        "MARKET_DATA", 
        lambda event: handle_market_data(event, counter)
    )
    
    engine_manager.register_event_handler(
        "NEWS", 
        lambda event: handle_news_event(event, counter)
    )
    
    # 启动引擎
    engine_manager.start()
    
    try:
        # 运行指定时间
        start_time = time.time()
        while time.time() - start_time < duration:
            time.sleep(1.0)
            
            # 打印实时状态
            if int(time.time() - start_time) % 2 == 0:
                logger.info(f"已运行 {time.time() - start_time:.1f} 秒")
                logger.info(f"事件计数: {counter.get_counts()}")
                
                # 获取性能统计
                stats = engine_manager.get_performance_stats()
                logger.info(f"引擎状态: {stats.get('replay_controllers', {})}")
        
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
    # 运行多数据源演示
    run_demo(mode=ReplayMode.BACKTEST, speed_factor=1.0, duration=5)
    run_demo(mode=ReplayMode.ACCELERATED, speed_factor=3.0, duration=8)