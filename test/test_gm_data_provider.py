#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金数据提供者单元测试

用于测试掘金量化数据提供者(GmDataProvider)的各项功能
"""

import os
import sys
import unittest
from datetime import datetime, timedelta
import pandas as pd

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入待测试的模块
from qte_data.gm_data_provider import GmDataProvider, GmDataDownloader
from qte_core.event_loop import EventLoop
from qte_core.events import MarketEvent

# 掘金量化API令牌（使用默认测试令牌）
TOKEN = "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"


class TestGmDataProvider(unittest.TestCase):
    """测试掘金数据提供者类"""
    
    @classmethod
    def setUpClass(cls):
        """在所有测试前设置环境"""
        # 创建事件循环和数据提供者
        cls.event_loop = EventLoop()
        data_dir = os.path.join(current_dir, "data_provider", "downloaded_data")
        cls.provider = GmDataProvider(token=TOKEN, event_loop=cls.event_loop, data_dir=data_dir)
        
        # 测试数据参数
        cls.test_symbol = "SHSE.000001"  # 上证指数
        cls.test_date = datetime.now() - timedelta(days=5)
        cls.start_date = cls.test_date - timedelta(days=5)
        cls.end_date = cls.test_date
    
    def test_downloader_initialization(self):
        """测试下载器初始化"""
        downloader = GmDataDownloader(token=TOKEN)
        self.assertIsNotNone(downloader)
        self.assertEqual(downloader.token, TOKEN)
    
    def test_provider_initialization(self):
        """测试提供者初始化"""
        self.assertIsNotNone(self.provider)
        self.assertIsNotNone(self.provider.downloader)
        self.assertEqual(self.provider.event_loop, self.event_loop)
    
    def test_get_historical_bars(self):
        """测试获取历史K线数据"""
        bars_gen = self.provider.get_historical_bars(
            self.test_symbol, 
            self.start_date, 
            self.end_date
        )
        
        # 验证数据生成器
        self.assertIsNotNone(bars_gen, "历史K线数据生成器不应为None")
        
        # 获取数据
        bars = list(bars_gen)
        
        # 由于可能是非交易日，我们只检查基本结构
        if bars:
            first_bar = bars[0]
            self.assertIn('timestamp', first_bar)
            self.assertIn('open', first_bar)
            self.assertIn('high', first_bar)
            self.assertIn('low', first_bar)
            self.assertIn('close', first_bar)
            self.assertIn('volume', first_bar)
    
    def test_get_latest_bar(self):
        """测试获取最新K线数据"""
        # 先确保有历史数据
        self.provider.get_historical_bars(
            self.test_symbol, 
            self.start_date,
            self.end_date
        )
        
        # 获取最新K线
        latest_bar = self.provider.get_latest_bar(self.test_symbol)
        
        # 由于缓存行为，这里应该能获取到数据
        self.assertIsNotNone(latest_bar)
        self.assertIn('timestamp', latest_bar)
        self.assertIn('close', latest_bar)
    
    def test_get_latest_bars(self):
        """测试获取多个最新K线数据"""
        # 先确保有历史数据
        self.provider.get_historical_bars(
            self.test_symbol, 
            self.start_date,
            self.end_date
        )
        
        # 获取最新的3条K线
        bars = self.provider.get_latest_bars(self.test_symbol, 3)
        
        # 检查结果
        self.assertIsNotNone(bars)
        if bars:
            self.assertLessEqual(len(bars), 3)
            for bar in bars:
                self.assertIn('timestamp', bar)
                self.assertIn('close', bar)
    
    def test_stream_market_data(self):
        """测试市场数据流"""
        # 使用一个简单的列表，只测试功能
        symbols = [self.test_symbol]
        
        # 获取市场数据流
        stream = self.provider.stream_market_data(symbols)
        self.assertIsNotNone(stream)
        
        # 获取前3个事件
        events = []
        for i, event in enumerate(stream):
            events.append(event)
            if i >= 2:  # 只取3个事件用于测试
                break
        
        # 检查事件队列
        queue_size = self.provider.event_loop.event_queue.qsize() if hasattr(self.provider.event_loop.event_queue, 'qsize') else len(self.provider.event_loop.event_queue)
        self.assertTrue(queue_size > 0)
        
        # 检查事件类型
        if events:
            for event in events:
                self.assertTrue(
                    isinstance(event, MarketEvent) or 
                    ('last_price' in event or 'price' in event)  # Tick数据
                )
    
    def test_get_minute_bar_generator(self):
        """测试获取分钟线数据生成器"""
        # 使用一个工作日进行测试
        test_day = self.test_date
        start = datetime(test_day.year, test_day.month, test_day.day, 9, 30)
        end = datetime(test_day.year, test_day.month, test_day.day, 15, 0)
        
        # 获取分钟线数据
        bars_gen = self.provider.get_minute_bar_generator(
            symbol=self.test_symbol, 
            minutes=1, 
            start_date=start, 
            end_date=end
        )
        
        # 数据可能不存在，如果存在则验证
        if bars_gen:
            bars = list(bars_gen)
            if bars:
                self.assertIn('timestamp', bars[0])
                self.assertIn('close', bars[0])
    
    def test_event_queue_operations(self):
        """测试事件队列操作"""
        # 清空事件队列
        while not self.event_loop.event_queue.empty():
            self.event_loop.event_queue.get()
        
        # 流式获取市场数据，应该会添加事件到队列
        symbols = [self.test_symbol]
        stream = self.provider.stream_market_data(symbols)
        next(stream)  # 获取第一个事件
        
        # 检查事件队列长度
        queue_size = len(self.event_loop.event_queue)
        self.assertTrue(queue_size > 0)


if __name__ == "__main__":
    unittest.main() 