import sys
import os
import unittest
from io import StringIO
from contextlib import redirect_stdout
import pandas as pd
from datetime import datetime, timedelta

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from qte_core.event_loop import EventLoop
from qte_core.events import EventType, MarketEvent, SignalEvent
from qte_strategy.example_strategies import MovingAverageCrossStrategy
from qte_data.csv_data_provider import CSVDataProvider

class TestStrategyIntegration(unittest.TestCase):
    """测试策略与事件系统的集成"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        # 创建事件循环
        self.event_loop = EventLoop()
        
        # 创建测试数据目录
        self.test_data_dir = os.path.join(project_root, "test_data")
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # 准备测试数据
        self._prepare_test_data()
        
        # 创建数据提供者
        self.data_provider = CSVDataProvider(
            event_loop=self.event_loop,
            csv_dir_path=self.test_data_dir,
            symbols=["AAPL"]
        )
        
        # 创建策略
        self.strategy = MovingAverageCrossStrategy(
            event_loop=self.event_loop,
            symbols=["AAPL"],
            short_window=3,
            long_window=5,
            data_provider=self.data_provider
        )
        
        # 收集信号事件
        self.signal_events = []
        
        def signal_handler(event):
            self.signal_events.append(event)
            
        # 注册信号处理程序
        self.event_loop.register_handler(EventType.SIGNAL, signal_handler)
    
    def _prepare_test_data(self):
        """准备测试数据"""
        # 创建上升趋势数据
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        prices = [100 + i*2 for i in range(20)]  # 创建上升趋势
        
        data = {
            'timestamp': dates,
            'open': prices,
            'high': [p + 1 for p in prices],
            'low': [p - 1 for p in prices],
            'close': [p + 0.5 for p in prices],
            'volume': [1000 + i*100 for i in range(20)]
        }
        
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(self.test_data_dir, "AAPL.csv"), index=False)
    
    def tearDown(self):
        """每个测试后的清理工作"""
        # 清空事件队列
        while self.event_loop.event_queue:
            _ = self.event_loop.get_event(block=False)
    
    def test_strategy_initialization(self):
        """测试策略初始化"""
        # 调用策略的初始化方法
        self.strategy.on_init()
        
        # 验证策略的数据窗口已初始化
        self.assertTrue(hasattr(self.strategy, '_data_windows'), "策略应该有_data_windows属性")
        self.assertIn("AAPL", self.strategy._data_windows, "AAPL应该在数据窗口中")
        
        # 验证历史数据已预加载
        self.assertGreater(len(self.strategy._data_windows["AAPL"]), 0, "数据窗口应该包含数据")
    
    def test_strategy_market_response(self):
        """测试策略对市场事件的响应"""
        # 调用策略的初始化方法
        self.strategy.on_init()
        
        # 创建并分发一个市场事件
        market_event = MarketEvent(
            symbol="AAPL",
            open_price=150.0,
            high_price=152.0,
            low_price=149.0,
            close_price=151.5,
            volume=10000
        )
        
        # 测试策略处理市场事件
        output = StringIO()
        with redirect_stdout(output):
            self.strategy.on_market_event(market_event)
        
        # 验证数据窗口是否更新
        self.assertIn(151.5, [bar['close'] for bar in self.strategy._data_windows["AAPL"]], 
                     "数据窗口应该包含最新的收盘价")
    
    def test_strategy_signal_generation(self):
        """测试策略生成交易信号"""
        # 首先初始化策略
        self.strategy.on_init()
        
        # 现在流式传输所有市场数据来触发信号生成
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理所有事件
        while self.event_loop.event_queue:
            event = self.event_loop.get_event()
            if event.event_type == EventType.MARKET:
                self.strategy.on_market_event(event)
            self.event_loop._dispatch_event(event)
        
        # 验证是否生成了信号
        self.assertGreater(len(self.signal_events), 0, "策略应该生成至少一个交易信号")
        
        # 验证信号类型
        for signal in self.signal_events:
            self.assertEqual(signal.event_type, EventType.SIGNAL, "事件类型应该是SIGNAL")
            self.assertEqual(signal.symbol, "AAPL", "信号的股票代码应该是AAPL")
            self.assertIn(signal.signal_type, ["LONG", "EXIT"], "信号类型应该是LONG或EXIT")
    
    def test_full_strategy_workflow(self):
        """测试完整的策略工作流程"""
        # 初始化策略
        output = StringIO()
        with redirect_stdout(output):
            self.strategy.on_init()
        
        # 获取系统开始状态
        initial_position = self.strategy.get_position("AAPL")
        
        # 运行事件循环
        for _ in range(5):  # 限制迭代次数，避免无限循环
            # 生成一批市场数据
            for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
                pass
                
            # 处理所有事件
            while self.event_loop.event_queue:
                event = self.event_loop.get_event()
                self.event_loop._dispatch_event(event)
        
        # 验证是否生成了信号
        self.assertGreater(len(self.signal_events), 0, "应该生成至少一个交易信号")
        
        # 输出结果摘要
        print(f"\n生成的信号数量: {len(self.signal_events)}")
        for i, signal in enumerate(self.signal_events[:5], 1):
            print(f"信号 {i}: {signal.symbol} {signal.signal_type} 于 {signal.timestamp}")
        
        if len(self.signal_events) > 5:
            print(f"... 及其他 {len(self.signal_events) - 5} 个信号")

if __name__ == "__main__":
    unittest.main() 