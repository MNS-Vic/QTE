#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金数据提供者调试脚本

用于详细检查GmDataProvider的运行情况
"""

import os
import sys
import traceback
from datetime import datetime, timedelta
import logging

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("debug_gm_provider.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    # 尝试导入必要的模块
    logger.info("导入必要的模块")
    from qte_core.event_loop import EventLoop
    from qte_data.gm_data_provider import GmDataProvider
    
    # 测试函数
    def test_event_loop():
        """测试事件循环的基本功能"""
        logger.info("测试事件循环的基本功能")
        try:
            event_loop = EventLoop()
            logger.info(f"事件循环创建成功: {event_loop}")
            logger.info(f"事件队列类型: {type(event_loop.event_queue)}")
            logger.info(f"事件队列长度: {len(event_loop.event_queue)}")
            return event_loop
        except Exception as e:
            logger.error(f"事件循环测试失败: {e}")
            traceback.print_exc()
            return None
    
    def test_gm_provider_init():
        """测试GmDataProvider的初始化"""
        logger.info("测试GmDataProvider的初始化")
        try:
            token = "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"
            event_loop = EventLoop()
            data_dir = os.path.join(current_dir, "data", "gm_data")
            os.makedirs(data_dir, exist_ok=True)
            
            provider = GmDataProvider(token=token, event_loop=event_loop, data_dir=data_dir)
            logger.info(f"GmDataProvider创建成功: {provider}")
            logger.info(f"下载器: {provider.downloader}")
            logger.info(f"事件循环: {provider.event_loop}")
            logger.info(f"数据目录: {provider.downloader.data_dir}")
            return provider
        except Exception as e:
            logger.error(f"GmDataProvider初始化测试失败: {e}")
            traceback.print_exc()
            return None
    
    def test_download_data(provider):
        """测试下载数据功能"""
        logger.info("测试下载数据功能")
        try:
            # 测试参数
            symbol = "SHSE.000001"  # 上证指数
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=3)  # 只测试3天数据
            
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"尝试下载 {symbol} 从 {start_str} 到 {end_str} 的日线数据")
            
            # 直接使用下载器下载数据
            df = provider.downloader.download_daily_data(symbol, start_str, end_str)
            
            if df is not None and not df.empty:
                logger.info(f"成功下载数据，共 {len(df)} 条记录")
                logger.info(f"数据列: {df.columns.tolist()}")
                logger.info(f"第一条记录: {df.iloc[0].to_dict()}")
                return True
            else:
                logger.warning(f"未能下载 {symbol} 的数据")
                return False
        except Exception as e:
            logger.error(f"下载数据测试失败: {e}")
            traceback.print_exc()
            return False
    
    def test_historical_bars(provider):
        """测试获取历史K线功能"""
        logger.info("测试获取历史K线功能")
        try:
            # 测试参数
            symbol = "SHSE.000001"  # 上证指数
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date - timedelta(days=3)  # 只测试3天数据
            
            logger.info(f"尝试获取 {symbol} 从 {start_date} 到 {end_date} 的历史K线")
            
            # 获取历史K线生成器
            bars_gen = provider.get_historical_bars(symbol, start_date, end_date)
            
            if bars_gen:
                logger.info("成功获取历史K线生成器")
                
                # 提取所有K线数据
                bars = []
                try:
                    for bar in bars_gen:
                        bars.append(bar)
                except Exception as e:
                    logger.error(f"遍历历史K线生成器时出错: {e}")
                    traceback.print_exc()
                
                if bars:
                    logger.info(f"成功获取 {len(bars)} 条历史K线")
                    logger.info(f"第一条K线: {bars[0]}")
                    return True
                else:
                    logger.warning("历史K线生成器未返回任何数据")
                    return False
            else:
                logger.warning(f"未能获取 {symbol} 的历史K线生成器")
                return False
        except Exception as e:
            logger.error(f"获取历史K线测试失败: {e}")
            traceback.print_exc()
            return False
    
    def test_market_event_stream(provider):
        """测试市场事件流功能"""
        logger.info("测试市场事件流功能")
        try:
            # 测试参数
            symbols = ["SHSE.000001", "SHSE.600519"]  # 上证指数和贵州茅台
            
            logger.info(f"尝试创建市场事件流，包含品种: {', '.join(symbols)}")
            
            # 创建市场事件流
            events_gen = provider.stream_market_data(symbols)
            
            if events_gen:
                logger.info("成功创建市场事件流")
                
                # 提取部分事件
                events = []
                try:
                    for i, event in enumerate(events_gen):
                        events.append(event)
                        logger.info(f"事件 {i+1}: {event.symbol} 于 {event.timestamp}, 收盘价: {getattr(event, 'close_price', 'N/A')}")
                        if i >= 4:  # 只取5条
                            break
                except Exception as e:
                    logger.error(f"遍历市场事件流时出错: {e}")
                    traceback.print_exc()
                
                if events:
                    logger.info(f"成功获取 {len(events)} 个市场事件")
                    # 检查事件队列
                    if provider.event_loop:
                        logger.info(f"事件队列中的事件数量: {len(provider.event_loop.event_queue)}")
                    return True
                else:
                    logger.warning("市场事件流未返回任何事件")
                    return False
            else:
                logger.warning("未能创建市场事件流")
                return False
        except Exception as e:
            logger.error(f"市场事件流测试失败: {e}")
            traceback.print_exc()
            return False

    # 执行测试
    logger.info("==== 开始执行调试测试 ====")
    
    # 测试事件循环
    event_loop_ok = test_event_loop()
    
    # 测试GmDataProvider初始化
    provider = test_gm_provider_init()
    
    if provider:
        # 测试下载数据
        download_ok = test_download_data(provider)
        
        # 测试获取历史K线
        hist_bars_ok = test_historical_bars(provider)
        
        # 测试市场事件流
        market_event_ok = test_market_event_stream(provider)
        
        # 测试结果汇总
        logger.info("==== 测试结果汇总 ====")
        logger.info(f"事件循环测试: {'成功' if event_loop_ok else '失败'}")
        logger.info(f"GmDataProvider初始化测试: {'成功' if provider else '失败'}")
        logger.info(f"下载数据测试: {'成功' if download_ok else '失败'}")
        logger.info(f"获取历史K线测试: {'成功' if hist_bars_ok else '失败'}")
        logger.info(f"市场事件流测试: {'成功' if market_event_ok else '失败'}")
    else:
        logger.error("GmDataProvider初始化失败，无法继续测试")

except Exception as e:
    logger.error(f"调试脚本执行过程中出错: {e}")
    traceback.print_exc()

logger.info("调试测试完成") 