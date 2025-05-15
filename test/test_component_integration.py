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
from qte_core.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from qte_core.events import OrderType, OrderDirection
from qte_data.csv_data_provider import CSVDataProvider
from qte_strategy.example_strategies import MovingAverageCrossStrategy
from qte_execution.basic_broker import BasicBroker
from qte_portfolio_risk.base_portfolio import BasePortfolio

class TestComponentIntegration(unittest.TestCase):
    """测试各组件之间的集成"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        # 创建测试数据目录
        self.test_data_dir = os.path.join(project_root, "test_data")
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # 准备测试数据
        self._prepare_test_data()
        
        # 创建事件循环
        self.event_loop = EventLoop()
        
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
        
        # 创建投资组合
        self.portfolio = BasePortfolio(
            event_loop=self.event_loop,
            initial_capital=100000.0
        )
        
        # 创建经纪商
        self.broker = BasicBroker(
            event_loop=self.event_loop,
            commission_rate=0.001  # 0.1%
        )
        
        # 记录收到的事件
        self.market_events = []
        self.signal_events = []
        self.order_events = []
        self.fill_events = []
        
        # 定义事件处理函数
        def market_handler(event):
            self.market_events.append(event)
            
        def signal_handler(event):
            self.signal_events.append(event)
            
        def order_handler(event):
            self.order_events.append(event)
            
        def fill_handler(event):
            self.fill_events.append(event)
        
        # 注册事件处理函数
        self.event_loop.register_handler(EventType.MARKET, market_handler)
        self.event_loop.register_handler(EventType.SIGNAL, signal_handler)
        self.event_loop.register_handler(EventType.ORDER, order_handler)
        self.event_loop.register_handler(EventType.FILL, fill_handler)
    
    def _prepare_test_data(self):
        """准备测试数据"""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        
        # 创建一个波动的价格序列，能触发交易信号
        prices = [
            100.0, 101.0, 102.0, 103.0, 104.0,  # 上涨
            105.0, 104.0, 103.0, 102.0, 101.0,  # 下跌
            100.0, 99.0, 98.0, 97.0, 96.0,      # 继续下跌
            95.0, 96.0, 97.0, 98.0, 99.0        # 回升
        ]
        
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
    
    def test_data_provider_to_strategy(self):
        """测试数据提供者到策略的集成"""
        # 初始化策略
        self.strategy.on_init()
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理事件
        while self.event_loop.event_queue:
            event = self.event_loop.get_event()
            if event.event_type == EventType.MARKET:
                self.strategy.on_market_event(event)
            self.event_loop._dispatch_event(event)
        
        # 验证是否收到市场事件
        self.assertGreater(len(self.market_events), 0, "应该收到市场事件")
        
        # 验证是否生成信号
        self.assertGreater(len(self.signal_events), 0, "策略应该生成交易信号")
    
    def test_strategy_to_portfolio(self):
        """测试策略到投资组合的集成"""
        # 注册投资组合处理信号事件
        self.event_loop.register_handler(EventType.SIGNAL, self.portfolio.on_signal)
        
        # 初始化策略
        self.strategy.on_init()
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理事件
        while self.event_loop.event_queue:
            event = self.event_loop.get_event()
            if event.event_type == EventType.MARKET:
                self.strategy.on_market_event(event)
            self.event_loop._dispatch_event(event)
        
        # 验证是否生成订单
        self.assertGreater(len(self.order_events), 0, "投资组合应该生成订单")
    
    def test_portfolio_to_broker(self):
        """测试投资组合到经纪商的集成"""
        # 注册所有必要的处理程序
        self.event_loop.register_handler(EventType.SIGNAL, self.portfolio.on_signal)
        self.event_loop.register_handler(EventType.ORDER, self.broker.on_order)
        self.event_loop.register_handler(EventType.MARKET, self.portfolio.on_market)
        self.event_loop.register_handler(EventType.FILL, self.portfolio.on_fill)
        
        # 初始化策略
        self.strategy.on_init()
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理事件
        while self.event_loop.event_queue:
            event = self.event_loop.get_event()
            if event.event_type == EventType.MARKET:
                self.strategy.on_market_event(event)
            self.event_loop._dispatch_event(event)
        
        # 验证是否生成成交事件
        self.assertGreater(len(self.fill_events), 0, "经纪商应该生成成交事件")
    
    def test_full_component_chain(self):
        """测试完整组件链的集成"""
        # 注册所有必要的处理程序
        self.event_loop.register_handler(EventType.SIGNAL, self.portfolio.on_signal)
        self.event_loop.register_handler(EventType.ORDER, self.broker.on_order)
        self.event_loop.register_handler(EventType.MARKET, self.portfolio.on_market)
        self.event_loop.register_handler(EventType.FILL, self.portfolio.on_fill)
        
        # 初始化策略
        self.strategy.on_init()
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理事件
        while self.event_loop.event_queue:
            event = self.event_loop.get_event()
            if event.event_type == EventType.MARKET:
                self.strategy.on_market_event(event)
            self.event_loop._dispatch_event(event)
        
        # 验证所有事件类型都已处理
        self.assertGreater(len(self.market_events), 0, "应该处理市场事件")
        self.assertGreater(len(self.signal_events), 0, "应该处理信号事件")
        self.assertGreater(len(self.order_events), 0, "应该处理订单事件")
        self.assertGreater(len(self.fill_events), 0, "应该处理成交事件")
        
        # 验证投资组合状态
        self.assertNotEqual(self.portfolio.get_portfolio_value(), 100000.0, "投资组合价值应该变化")
        
        # 验证持仓
        positions = self.portfolio.positions
        self.assertTrue(len(positions) > 0, "投资组合应该有持仓")
        
        # 输出结果摘要
        print("\n组件集成测试结果:")
        print(f"处理的事件数量:")
        print(f"- 市场事件: {len(self.market_events)}")
        print(f"- 信号事件: {len(self.signal_events)}")
        print(f"- 订单事件: {len(self.order_events)}")
        print(f"- 成交事件: {len(self.fill_events)}")
        print(f"\n持仓情况:")
        for symbol, position in positions.items():
            print(f"{symbol}: {position.quantity} 股, 市值: {position.market_value:.2f}")
        print(f"\n投资组合价值: {self.portfolio.get_portfolio_value():.2f}")

if __name__ == "__main__":
    unittest.main() 