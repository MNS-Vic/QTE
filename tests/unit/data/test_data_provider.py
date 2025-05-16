#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据提供者功能

验证从不同来源获取数据的能力
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入相关模块
from qte.core.event_loop import EventLoop
try:
    from qte.data.gm_data_provider import GmDataProvider
    from qte.data.csv_data_provider import CsvDataProvider
    HAS_DATA_PROVIDERS = True
except ImportError:
    logger.warning("无法导入数据提供者模块，部分测试将被跳过")
    HAS_DATA_PROVIDERS = False

def create_test_data_csv(output_dir, symbol="TEST.000001", days=100):
    """
    创建测试数据CSV文件
    
    Args:
        output_dir: 输出目录
        symbol: 品种代码
        days: 数据天数
        
    Returns:
        str: 生成的CSV文件路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成测试数据
    start_date = datetime.now() - timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # 生成价格数据
    np.random.seed(42)
    price = 100
    prices = [price]
    
    for i in range(1, days):
        # 添加一些趋势
        trend = 0.0003 if i < days / 2 else -0.0003
        
        # 随机波动
        random_component = np.random.normal(0, 0.01)
        
        # 价格变动
        price_change = trend + random_component
        price = price * (1 + price_change)
        prices.append(price)
    
    # 创建数据框
    data = pd.DataFrame({
        'symbol': symbol,
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.01)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.01)) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, size=days)
    })
    
    # 保存为CSV
    symbol_clean = symbol.replace('.', '_')
    csv_file = os.path.join(output_dir, f"{symbol_clean}_daily.csv")
    data.to_csv(csv_file, index=False)
    
    logger.info(f"已创建测试数据: {csv_file}")
    
    return csv_file

def test_csv_data_provider():
    """测试CSV数据提供者"""
    if not HAS_DATA_PROVIDERS:
        logger.warning("跳过CSV数据提供者测试，因为缺少必要模块")
        return
    
    logger.info("测试CSV数据提供者")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 准备测试数据
    data_dir = os.path.join("test", "data_provider", "downloaded_data")
    test_csv = create_test_data_csv(data_dir)
    
    # 创建CSV数据提供者
    provider = CsvDataProvider(data_dir=data_dir, event_loop=event_loop)
    
    # 测试获取历史数据
    symbol = "TEST.000001"
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now() - timedelta(days=10)
    
    logger.info(f"获取历史数据: {symbol}, {start_date} 到 {end_date}")
    
    # 获取历史数据
    bars = list(provider.get_historical_bars(symbol, start_date, end_date))
    
    logger.info(f"获取到 {len(bars)} 条数据")
    
    # 验证数据
    assert len(bars) > 0, "应该获取到历史数据"
    
    # 显示数据概况
    bars_df = pd.DataFrame(bars)
    logger.info(f"数据概况:\n{bars_df.describe()}")
    
    # 绘制数据
    plt.figure(figsize=(12, 6))
    plt.plot(bars_df['timestamp'], bars_df['close'], label='收盘价')
    plt.title(f"{symbol} 历史价格")
    plt.xlabel("日期")
    plt.ylabel("价格")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    
    # 保存图表
    chart_file = os.path.join(data_dir, f"{symbol.replace('.', '_')}_chart.png")
    plt.savefig(chart_file)
    logger.info(f"图表已保存至 {chart_file}")
    
    # 清理图表对象
    plt.close()
    
    logger.info("CSV数据提供者测试完成")

def test_mock_data_provider():
    """测试模拟数据提供者"""
    logger.info("测试模拟数据提供者")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 创建模拟数据提供者
    class MockDataProvider:
        def __init__(self, event_loop):
            self.event_loop = event_loop
        
        def get_historical_bars(self, symbol, start_date, end_date):
            """生成模拟历史数据"""
            days = (end_date - start_date).days + 1
            current_date = start_date
            
            for i in range(days):
                if i % 7 in [5, 6]:  # 跳过周末
                    continue
                
                # 生成随机价格
                base_price = 100 + i * 0.1  # 简单上升趋势
                random_factor = np.random.normal(0, 0.5)
                price = max(base_price + random_factor, 1.0)  # 确保价格为正
                
                # 生成OHLCV数据
                yield {
                    'symbol': symbol,
                    'timestamp': current_date,
                    'open': price * (1 - 0.005 * np.random.random()),
                    'high': price * (1 + 0.01 * np.random.random()),
                    'low': price * (1 - 0.01 * np.random.random()),
                    'close': price,
                    'volume': int(1000 * np.random.random() + 500)
                }
                
                current_date += timedelta(days=1)
    
    # 创建提供者
    provider = MockDataProvider(event_loop)
    
    # 测试获取历史数据
    symbol = "MOCK.000001"
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    logger.info(f"获取模拟历史数据: {symbol}, {start_date} 到 {end_date}")
    
    # 获取历史数据
    bars = list(provider.get_historical_bars(symbol, start_date, end_date))
    
    logger.info(f"获取到 {len(bars)} 条模拟数据")
    
    # 验证数据
    assert len(bars) > 0, "应该获取到历史数据"
    
    # 显示数据概况
    bars_df = pd.DataFrame(bars)
    
    if not bars_df.empty:
        logger.info(f"数据概况:\n{bars_df.describe()}")
        
        # 绘制数据
        plt.figure(figsize=(12, 6))
        plt.plot(bars_df['timestamp'], bars_df['close'], label='收盘价')
        plt.title(f"{symbol} 模拟历史价格")
        plt.xlabel("日期")
        plt.ylabel("价格")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        
        # 保存图表
        output_dir = os.path.join("test", "data_provider", "downloaded_data")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        chart_file = os.path.join(output_dir, f"{symbol.replace('.', '_')}_chart.png")
        plt.savefig(chart_file)
        logger.info(f"图表已保存至 {chart_file}")
        
        # 清理图表对象
        plt.close()
    
    logger.info("模拟数据提供者测试完成")

def test_gm_data_provider():
    """测试掘金数据提供者"""
    if not HAS_DATA_PROVIDERS:
        logger.warning("跳过掘金数据提供者测试，因为缺少必要模块")
        return
    
    try:
        import gm
        logger.info("测试掘金数据提供者")
        
        # 掘金API令牌，这里使用一个虚拟令牌，需要替换为实际有效的令牌
        token = "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"
        
        # 创建事件循环
        event_loop = EventLoop()
        
        # 创建掘金数据提供者
        data_dir = os.path.join("test", "data_provider", "downloaded_data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        provider = GmDataProvider(token=token, event_loop=event_loop, data_dir=data_dir)
        
        # 测试获取历史数据
        symbol = "SHSE.000001"  # 上证指数
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() - timedelta(days=1)
        
        logger.info(f"获取掘金历史数据: {symbol}, {start_date} 到 {end_date}")
        
        try:
            # 获取历史数据
            bars = list(provider.get_historical_bars(symbol, start_date, end_date))
            
            logger.info(f"获取到 {len(bars)} 条数据")
            
            # 验证数据
            if len(bars) > 0:
                # 显示数据概况
                bars_df = pd.DataFrame(bars)
                logger.info(f"数据概况:\n{bars_df.describe()}")
                
                # 绘制数据
                plt.figure(figsize=(12, 6))
                plt.plot(bars_df['timestamp'], bars_df['close'], label='收盘价')
                plt.title(f"{symbol} 历史价格")
                plt.xlabel("日期")
                plt.ylabel("价格")
                plt.grid(True)
                plt.legend()
                plt.tight_layout()
                
                # 保存图表
                chart_file = os.path.join(data_dir, f"{symbol.replace('.', '_')}_chart.png")
                plt.savefig(chart_file)
                logger.info(f"图表已保存至 {chart_file}")
                
                # 清理图表对象
                plt.close()
            else:
                logger.warning("未能获取到掘金数据")
        
        except Exception as e:
            logger.error(f"获取掘金数据时出错: {e}")
        
        logger.info("掘金数据提供者测试完成")
    
    except ImportError:
        logger.warning("跳过掘金数据提供者测试，因为缺少gm模块")

if __name__ == "__main__":
    logger.info("开始测试数据提供者")
    
    try:
        # 测试CSV数据提供者
        test_csv_data_provider()
        
        # 测试模拟数据提供者
        test_mock_data_provider()
        
        # 测试掘金数据提供者
        # test_gm_data_provider()  # 需要有效的掘金API令牌，暂时注释掉
        
        logger.info("所有数据提供者测试完成")
    
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    sys.exit(0) 