#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金数据提供者调试脚本

用于诊断GmDataProvider中的问题，提供故障排除和问题分析功能
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gm_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gm_debug")

# 导入待调试的组件
from qte_data.gm_data_provider import GmDataProvider, GmDataDownloader
from qte_core.event_loop import EventLoop
from qte_core.events import MarketEvent

# 掘金量化API令牌
TOKEN = "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"

def debug_initialization():
    """调试初始化过程"""
    logger.info("=== 调试初始化 ===")
    
    try:
        # 尝试导入掘金量化SDK
        logger.info("尝试导入掘金量化SDK...")
        import gm
        from gm.api import set_token, history
        logger.info(f"掘金量化SDK版本: {gm.__version__}")
        
        # 测试Token连接
        logger.info(f"测试Token连接: {TOKEN}")
        set_token(TOKEN)
        logger.info("Token连接成功")
        
        # 创建下载器
        logger.info("创建GmDataDownloader...")
        downloader = GmDataDownloader(token=TOKEN)
        logger.info("GmDataDownloader创建成功")
        
        # 创建数据提供者
        logger.info("创建GmDataProvider...")
        provider = GmDataProvider(token=TOKEN)
        logger.info("GmDataProvider创建成功")
        
        return True, provider
    
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

def debug_data_access(provider):
    """调试数据访问功能"""
    logger.info("=== 调试数据访问 ===")
    
    try:
        # 测试参数
        symbol = "SHSE.000001"  # 上证指数
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=5)
        
        # 格式化日期为字符串
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"测试获取 {symbol} 从 {start_str} 到 {end_str} 的日线数据")
        
        # 检查下载器的内部方法
        logger.debug("测试_check_symbol方法...")
        symbol_valid = provider.downloader._check_symbol(symbol)
        logger.debug(f"符号检查结果: {symbol_valid}")
        
        # 测试下载日线数据
        logger.info("测试download_daily_data方法...")
        data = provider.downloader.download_daily_data(symbol, start_str, end_str)
        
        if data is not None and not data.empty:
            logger.info(f"成功获取到 {len(data)} 条日线数据")
            logger.debug(f"数据字段: {data.columns.tolist()}")
            logger.debug(f"数据样本:\n{data.head(2)}")
        else:
            logger.warning("未获取到日线数据")
        
        # 测试数据缓存
        logger.info("测试数据缓存功能...")
        logger.debug(f"当前缓存状态: {symbol in provider.data_cache}")
        
        # 测试历史数据接口
        logger.info("测试get_historical_bars方法...")
        bars_gen = provider.get_historical_bars(symbol, start_date, end_date)
        
        if bars_gen:
            bars = list(bars_gen)
            logger.info(f"获取到 {len(bars)} 条历史K线数据")
            if bars:
                logger.debug(f"第一条数据: {bars[0]}")
        else:
            logger.warning("get_historical_bars返回None")
        
        return True
    
    except Exception as e:
        logger.error(f"数据访问测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def debug_event_queue(provider):
    """调试事件队列功能"""
    logger.info("=== 调试事件队列 ===")
    
    try:
        # 创建新的事件循环
        event_loop = EventLoop()
        provider.event_loop = event_loop
        
        # 测试参数
        symbol = "SHSE.000001"  # 上证指数
        
        # 检查初始队列状态
        logger.debug(f"初始事件队列长度: {len(event_loop.event_queue)}")
        
        # 生成市场事件流
        logger.info(f"为 {symbol} 生成市场事件流...")
        stream = provider.stream_market_data([symbol])
        
        # 取出几个事件
        events = []
        for i, event in enumerate(stream):
            events.append(event)
            logger.debug(f"接收到事件: {event}")
            if i >= 2:  # 只取3个事件
                break
        
        # 检查队列状态
        queue_size = len(event_loop.event_queue)
        logger.info(f"事件队列长度: {queue_size}")
        
        # 检查队列内容
        if queue_size > 0:
            event = event_loop.get_next_event()
            logger.debug(f"从队列中获取的事件: {event}")
        
        return True
    
    except Exception as e:
        logger.error(f"事件队列测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def debug_file_operations(provider):
    """调试文件操作功能"""
    logger.info("=== 调试文件操作 ===")
    
    try:
        # 测试参数
        symbol = "SHSE.000001"  # 上证指数
        data_type = "daily"
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 检查文件路径生成
        logger.debug("测试_get_data_path方法...")
        file_path = provider.downloader._get_data_path(
            symbol=symbol,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date
        )
        logger.debug(f"生成的文件路径: {file_path}")
        
        # 检查文件目录是否存在
        logger.debug(f"检查目录是否存在: {file_path.parent}")
        logger.debug(f"目录存在: {file_path.parent.exists()}")
        
        # 如果有数据文件，检查其内容
        if file_path.exists():
            logger.info(f"找到数据文件: {file_path}")
            try:
                data = pd.read_csv(file_path)
                logger.info(f"文件包含 {len(data)} 条记录")
                logger.debug(f"数据字段: {data.columns.tolist()}")
            except Exception as e:
                logger.error(f"读取文件失败: {e}")
        else:
            logger.info(f"文件不存在: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"文件操作测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("开始调试掘金数据提供者")
    
    # 调试初始化
    init_success, provider = debug_initialization()
    if not init_success or provider is None:
        logger.error("初始化失败，终止调试")
        return
    
    # 调试数据访问
    data_access_success = debug_data_access(provider)
    if not data_access_success:
        logger.warning("数据访问测试失败")
    
    # 调试事件队列
    event_queue_success = debug_event_queue(provider)
    if not event_queue_success:
        logger.warning("事件队列测试失败")
    
    # 调试文件操作
    file_ops_success = debug_file_operations(provider)
    if not file_ops_success:
        logger.warning("文件操作测试失败")
    
    logger.info("调试完成")

if __name__ == "__main__":
    main() 