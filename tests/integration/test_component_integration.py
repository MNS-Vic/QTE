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
project_root = os.path.abspath(os.path.join(current_dir, "..", "..")) # QTE project root from tests/integration
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"DEBUG SYS.PATH in test_component_integration: {sys.path}") # <--- Print sys.path

# 导入 app_logger
from qte.analysis.logger import app_logger

from qte.core.event_loop import EventLoop
from qte.core.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from qte.core.events import OrderType, OrderDirection
from qte.data.csv_data_provider import CSVDataProvider
# The following import needs careful consideration as MovingAverageCrossStrategy
# is an example strategy and not part of the core qte library.
# For now, assuming it might be moved to qte.strategy for testing purposes,
# or the test needs to add 'examples/simple_strategies' to sys.path.
# Temporarily commenting out or adjusting if it causes further issues.
# from qte.strategy.example_strategies import MovingAverageCrossStrategy
# A placeholder or a mock strategy might be better for a pure integration test.
# For now, let's assume it's accessible via qte.strategy or sys.path is adjusted elsewhere.
from qte.strategy.example_strategies import MovingAverageCrossStrategy
from qte.execution.basic_broker import BasicBroker
from qte.portfolio.base_portfolio import BasePortfolio
# from qte.execution.basic_broker import BasicBroker # 已被导入
# 引入实际的佣金和滑点模型类
from qte.execution.basic_broker import FixedPercentageCommission, SimpleRandomSlippage

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
            initial_capital=100000.0,
            data_provider=self.data_provider
        )

        # 创建佣金模型实例
        self.commission_model = FixedPercentageCommission(commission_rate=0.001) 

        # 创建滑点模型实例
        self.slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=0.1) # 示例值

        # 创建经纪商
        self.broker = BasicBroker(
            event_loop=self.event_loop,
            commission_model=self.commission_model, # 传递模型实例
            slippage_model=self.slippage_model,   # 传递模型实例
            data_provider=self.data_provider      # 传递已创建的数据提供者
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
        while len(self.event_loop) > 0: 
            _ = self.event_loop.get_next_event()
    
    def test_data_provider_to_strategy(self):
        """测试数据提供者到策略的集成"""
        # 初始化策略
        self.strategy.on_init(self.data_provider)
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass # 数据提供者应该已经将事件放入事件循环
        
        # 处理事件
        while len(self.event_loop) > 0: # 使用 len() 检查队列
            event = self.event_loop.get_next_event() # 使用正确的方法名
            if event is None: # get_next_event 在队列空时可能返回 None
                break
            if event.event_type == EventType.MARKET.value: 
                self.strategy.on_market_event(event)
            self.event_loop.dispatch_event(event) # 使用公共的 dispatch_event
        
        # 验证是否收到市场事件
        self.assertGreater(len(self.market_events), 0, "应该收到市场事件")
        
        # 验证是否生成信号
        self.assertGreater(len(self.signal_events), 0, "策略应该生成交易信号")
    
    def test_strategy_to_portfolio(self):
        """测试策略到投资组合的集成"""
        # 注册投资组合处理信号事件
        self.event_loop.register_handler(EventType.SIGNAL, self.portfolio.on_signal)
        
        # 初始化策略
        self.strategy.on_init(self.data_provider)
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理事件
        while len(self.event_loop) > 0:
            event = self.event_loop.get_next_event()
            if event is None:
                break
            if event.event_type == EventType.MARKET.value:
                self.strategy.on_market_event(event)
            self.event_loop.dispatch_event(event)
        
        # 验证是否生成订单
        self.assertGreater(len(self.order_events), 0, "投资组合应该生成订单")
    
    def test_portfolio_to_broker(self):
        """测试投资组合到经纪商的集成"""
        # 注册所有必要的处理程序
        self.event_loop.register_handler(EventType.SIGNAL, self.portfolio.on_signal)
        self.event_loop.register_handler(EventType.ORDER, self.broker.submit_order)
        self.event_loop.register_handler(EventType.MARKET, self.portfolio.on_market)
        self.event_loop.register_handler(EventType.FILL, self.portfolio.on_fill)
        
        # 初始化策略
        self.strategy.on_init(self.data_provider)
        
        # 流式传输市场数据
        for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
            pass
        
        # 处理事件
        while len(self.event_loop) > 0:
            event = self.event_loop.get_next_event()
            if event is None:
                break
            if event.event_type == EventType.MARKET.value:
                self.strategy.on_market_event(event)
            self.event_loop.dispatch_event(event)
        
        # 验证是否生成成交事件
        self.assertGreater(len(self.fill_events), 0, "经纪商应该生成成交事件")
    
    def test_full_component_chain(self):
        """测试完整组件链的集成"""
        # 注册所有必要的处理程序
        self.event_loop.register_handler(EventType.SIGNAL, self.portfolio.on_signal)
        self.event_loop.register_handler(EventType.ORDER, self.broker.submit_order)
        self.event_loop.register_handler(EventType.MARKET, self.portfolio.on_market)
        self.event_loop.register_handler(EventType.FILL, self.portfolio.on_fill)
        
        # 初始化策略
        self.strategy.on_init(self.data_provider)

        # 流式传输市场数据并处理事件的修改后逻辑
        if hasattr(self.data_provider, 'all_bars_sorted') and self.data_provider.all_bars_sorted:
            app_logger.info("DEBUG TEST: Using iterative event processing for full_component_chain.")
            for bar_info in self.data_provider.all_bars_sorted:
                symbol_from_bar = bar_info.get('symbol_for_event', bar_info.get('symbol')) 
                if symbol_from_bar != "AAPL": # 假设测试只关注AAPL
                    continue

                # 手动更新 data_provider 的 latest_data 状态，模拟 stream_market_data 的行为
                # 这样 portfolio.on_signal 中的 get_latest_bar 才能获取到价格
                current_bar_for_dp_latest_data = {k: v for k, v in bar_info.items() if k != 'symbol_for_event'}
                if hasattr(self.data_provider, 'latest_data') and isinstance(self.data_provider.latest_data, dict):
                    self.data_provider.latest_data[symbol_from_bar] = current_bar_for_dp_latest_data
                else:
                    # 如果 latest_data 属性不存在或类型不对，可能需要初始化或记录警告
                    app_logger.warning(f"DEBUG TEST: data_provider.latest_data not found or not a dict. Cannot update for {symbol_from_bar}")

                # 手动创建 MarketEvent 并放入队列
                # (确保bar_info中的字段名和类型与MarketEvent构造函数匹配)
                try:
                    market_event_to_put = MarketEvent(
                        symbol=symbol_from_bar,
                        timestamp=pd.to_datetime(bar_info['timestamp']),
                        open_price=float(bar_info['open']),
                        high_price=float(bar_info['high']),
                        low_price=float(bar_info['low']),
                        close_price=float(bar_info['close']),
                        volume=int(bar_info['volume'])
                    )
                    self.event_loop.put_event(market_event_to_put)
                except KeyError as e:
                    app_logger.error(f"DEBUG TEST: KeyError when creating MarketEvent from bar_info: {e}. Bar_info: {bar_info}")
                    continue 

                # 处理完当前事件队列中的所有事件，直到队列为空
                # app_logger.info(f"DEBUG TEST: ---- Processing events after MarketEvent for {market_event_to_put.timestamp} ----")
                while len(self.event_loop) > 0:
                    event = self.event_loop.get_next_event()
                    if event is None: 
                        # app_logger.info("DEBUG TEST: Event loop empty (event is None).")
                        break
                    
                    # app_logger.info(f"DEBUG TEST: Processing event from queue: {event.event_type} at {event.timestamp}")
                    
                    # 核心逻辑：让策略处理市场事件，让事件循环分发所有事件
                    if event.event_type == EventType.MARKET.value:
                        self.strategy.on_market_event(event)
                    
                    self.event_loop.dispatch_event(event)
                # app_logger.info(f"DEBUG TEST: ---- Finished processing events for MarketEvent at {market_event_to_put.timestamp} ----")
        else:
            # Fallback to original logic if data_provider structure is different
            app_logger.warning("DEBUG TEST: Fallback to original event processing for full_component_chain.")
            for _ in self.data_provider.stream_market_data(symbols=["AAPL"]):
                pass
            # 处理事件 (旧的循环，可能会有我们观察到的时序问题)
            while len(self.event_loop) > 0:
                event = self.event_loop.get_next_event()
                if event is None:
                    break
                if event.event_type == EventType.MARKET.value:
                    self.strategy.on_market_event(event)
                self.event_loop.dispatch_event(event)

        # 验证所有事件类型都已处理
        self.assertGreater(len(self.market_events), 0, "应该处理市场事件")
        self.assertGreater(len(self.signal_events), 0, "应该处理信号事件")
        self.assertGreater(len(self.order_events), 0, "应该处理订单事件")
        self.assertGreater(len(self.fill_events), 0, "应该处理成交事件")
        
        # 验证投资组合状态
        # 使用 get_portfolio_snapshot()['total_equity'] 获取总权益
        current_portfolio_value = self.portfolio.get_portfolio_snapshot()['total_equity']
        self.assertNotEqual(current_portfolio_value, 100000.0, "投资组合价值应该变化")      
        
        # 验证持仓
        # positions = self.portfolio.positions # 直接访问positions可能是内部字典，用get_current_positions更安全
        positions = self.portfolio.get_current_positions() 
        self.assertTrue(len(positions) > 0, "投资组合应该有持仓")
        
        # 输出结果摘要
        print("\n组件集成测试结果:")
        print(f"处理的事件数量:")
        print(f"- 市场事件: {len(self.market_events)}")
        print(f"- 信号事件: {len(self.signal_events)}")
        print(f"- 订单事件: {len(self.order_events)}")
        print(f"- 成交事件: {len(self.fill_events)}")
        print(f"\n持仓情况:")
        # 确保 positions 是通过 get_current_positions() 获取的最新状态
        final_snapshot = self.portfolio.get_portfolio_snapshot() # 获取完整的最终快照
        final_positions = final_snapshot.get("positions", {})
        if not final_positions:
            print("  无最终持仓。")
        else:
            for symbol, position in final_positions.items():
                print(f"  {symbol}: {position.get('quantity')} 股, 市值: {position.get('market_value', 0):.2f}")
        print(f"\n投资组合价值: {final_snapshot['total_equity']:.2f}")

if __name__ == "__main__":
    unittest.main() 