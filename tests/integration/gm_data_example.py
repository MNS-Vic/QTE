#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金数据提供者使用示例

演示如何使用掘金数据提供者下载和访问各类市场数据
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import logging

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入回测系统相关模块
from qte_core.event_loop import EventLoop
from qte_data.gm_data_provider import GmDataProvider

# 掘金量化API令牌
TOKEN = "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"  # 示例Token，请替换为自己的Token

def example_daily_data():
    """演示如何获取日线数据"""
    logger.info("=== 日线数据示例 ===")
    
    # 初始化事件循环和数据提供者
    event_loop = EventLoop()
    data_dir = os.path.join(current_dir, "downloaded_data")
    provider = GmDataProvider(token=TOKEN, event_loop=event_loop, data_dir=data_dir)
    
    # 测试参数
    symbol = "SHSE.000001"  # 上证指数
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=10)
    
    logger.info(f"下载 {symbol} 从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 的日线数据")
    
    # 获取历史数据
    bars_gen = provider.get_historical_bars(symbol, start_date, end_date)
    
    if bars_gen:
        logger.info("日线数据样本:")
        for i, bar in enumerate(bars_gen):
            logger.info(f"  {bar['timestamp']} - 开:{bar['open']:.2f} 高:{bar['high']:.2f} 低:{bar['low']:.2f} 收:{bar['close']:.2f} 量:{bar['volume']}")
            if i >= 4:  # 只显示前5条
                break
    else:
        logger.warning(f"未能获取 {symbol} 的日线数据")
    
    # 获取最新K线
    latest_bar = provider.get_latest_bar(symbol)
    if latest_bar:
        logger.info(f"最新K线: {latest_bar['timestamp']} 收盘价: {latest_bar['close']:.2f}")
    
    return provider  # 返回提供者实例便于复用

def example_minute_data(provider=None):
    """演示如何获取分钟线数据"""
    logger.info("\n=== 分钟线数据示例 ===")
    
    if provider is None:
        # 初始化事件循环和数据提供者
        event_loop = EventLoop()
        data_dir = os.path.join(current_dir, "downloaded_data")
        provider = GmDataProvider(token=TOKEN, event_loop=event_loop, data_dir=data_dir)
    
    # 测试参数
    symbol = "SHSE.600519"  # 贵州茅台
    
    # 指定一个交易日
    test_date = datetime(2023, 1, 10)
    start = datetime(test_date.year, test_date.month, test_date.day, 9, 30)
    end = datetime(test_date.year, test_date.month, test_date.day, 15, 0)
    
    logger.info(f"下载 {symbol} 在 {test_date.strftime('%Y-%m-%d')} 的1分钟线数据")
    
    # 获取分钟线数据
    bars_gen = provider.get_minute_bar_generator(symbol, 1, start, end)
    
    if bars_gen:
        logger.info("分钟线数据样本:")
        for i, bar in enumerate(bars_gen):
            logger.info(f"  {bar['timestamp']} - 收:{bar['close']:.2f}")
            if i >= 4:  # 只显示前5条
                break
        logger.info("  ...")
    else:
        logger.warning(f"未能获取 {symbol} 的分钟线数据")
    
    return provider  # 返回提供者实例便于复用

def example_tick_data(provider=None):
    """演示如何获取Tick数据"""
    logger.info("\n=== Tick数据示例 ===")
    
    if provider is None:
        # 初始化事件循环和数据提供者
        event_loop = EventLoop()
        data_dir = os.path.join(current_dir, "downloaded_data")
        provider = GmDataProvider(token=TOKEN, event_loop=event_loop, data_dir=data_dir)
    
    # 测试参数
    symbol = "SHSE.600519"  # 贵州茅台
    
    # 指定一个交易日
    test_date = datetime(2023, 1, 10)
    start = datetime(test_date.year, test_date.month, test_date.day, 9, 30)
    end = datetime(test_date.year, test_date.month, test_date.day, 10, 0)  # 只获取30分钟
    
    logger.info(f"下载 {symbol} 在 {test_date.strftime('%Y-%m-%d')} 9:30-10:00 的Tick数据")
    
    # 获取Tick数据
    ticks_gen = provider.get_tick_generator(symbol, start, end)
    
    if ticks_gen:
        logger.info("Tick数据样本:")
        for i, tick in enumerate(ticks_gen):
            # 打印时间和价格
            time_str = tick['timestamp'].strftime("%H:%M:%S.%f")[:-3]
            price = tick.get('price', tick.get('last_price', 0))
            volume = tick.get('last_volume', 0)
            logger.info(f"  {time_str} - 价格:{price:.2f} 量:{volume}")
            if i >= 9:  # 只显示前10条
                break
        logger.info("  ...")
    else:
        logger.warning(f"未能获取 {symbol} 的Tick数据")
    
    return provider  # 返回提供者实例便于复用

def example_market_event_stream(provider=None):
    """演示如何生成市场事件流"""
    logger.info("\n=== 市场事件流示例 ===")
    
    if provider is None:
        # 初始化事件循环和数据提供者
        event_loop = EventLoop()
        data_dir = os.path.join(current_dir, "downloaded_data")
        provider = GmDataProvider(token=TOKEN, event_loop=event_loop, data_dir=data_dir)
    
    # 测试多个股票
    symbols = ["SHSE.000001", "SHSE.600519"]  # 上证指数和贵州茅台
    
    logger.info(f"生成市场事件流，包含品种: {', '.join(symbols)}")
    
    # 创建市场事件流
    events_gen = provider.stream_market_data(symbols)
    
    if events_gen:
        logger.info("市场事件样本:")
        for i, event in enumerate(events_gen):
            logger.info(f"  {event.timestamp} - {event.symbol} 开:{event.open_price:.2f} 收:{event.close_price:.2f}")
            if i >= 9:  # 只取10条
                break
        logger.info("  ...")
        
        # 检查事件队列
        queue_size = provider.event_loop.event_queue.qsize() if hasattr(provider.event_loop.event_queue, 'qsize') else len(provider.event_loop.event_queue)
        logger.info(f"事件队列中的事件数量: {queue_size}")
    else:
        logger.warning("未能创建市场事件流")

def main():
    """主函数"""
    logger.info("掘金数据提供者示例开始")
    
    # 初始化一个提供者并在各个示例中复用
    provider = example_daily_data()
    example_minute_data(provider)
    example_tick_data(provider)
    example_market_event_stream(provider)
    
    logger.info("\n示例结束")

if __name__ == "__main__":
    main() 