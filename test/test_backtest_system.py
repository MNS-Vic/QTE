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
from qte_core.events import EventType
from qte_core.backtester import BE_Backtester
from qte_data.csv_data_provider import CSVDataProvider
from qte_strategy.example_strategies import MovingAverageCrossStrategy
from qte_execution.basic_broker import BasicBroker
from qte_portfolio_risk.base_portfolio import BasePortfolio

class TestBacktestSystem(unittest.TestCase):
    """测试完整回测系统的运行"""
    
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
            symbols=["AAPL", "GOOGL"]
        )
        
        # 创建策略
        self.strategy = MovingAverageCrossStrategy(
            event_loop=self.event_loop,
            symbols=["AAPL", "GOOGL"],
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
        
        # 创建回测器
        self.backtester = BE_Backtester(
            event_loop=self.event_loop,
            data_provider=self.data_provider,
            strategy=self.strategy,
            portfolio=self.portfolio,
            broker=self.broker,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 20)
        )
        
        # 计数器
        self.event_counters = {
            EventType.MARKET: 0,
            EventType.SIGNAL: 0,
            EventType.ORDER: 0,
            EventType.FILL: 0
        }
        
        # 注册计数处理程序
        for event_type in self.event_counters.keys():
            self.event_loop.register_handler(
                event_type, 
                lambda event, et=event_type: self._count_event(event, et)
            )
    
    def _count_event(self, event, event_type):
        """计数事件"""
        self.event_counters[event_type] += 1
    
    def _prepare_test_data(self):
        """准备测试数据"""
        # 创建AAPL上升趋势数据
        self._create_test_data("AAPL", trend="up")
        
        # 创建GOOGL下降趋势数据
        self._create_test_data("GOOGL", trend="down")
    
    def _create_test_data(self, symbol, trend="up"):
        """创建测试数据"""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        
        if trend == "up":
            prices = [100 + i*2 for i in range(20)]  # 上升趋势
        else:
            prices = [140 - i*2 for i in range(20)]  # 下降趋势
            
        data = {
            'timestamp': dates,
            'open': prices,
            'high': [p + 1 for p in prices],
            'low': [p - 1 for p in prices],
            'close': [p + 0.5 if trend == "up" else p - 0.5 for p in prices],
            'volume': [1000 + i*100 for i in range(20)]
        }
        
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(self.test_data_dir, f"{symbol}.csv"), index=False)
    
    def test_backtest_initialization(self):
        """测试回测系统初始化"""
        # 验证各组件已正确初始化
        self.assertIsNotNone(self.backtester.event_loop, "事件循环应该已初始化")
        self.assertIsNotNone(self.backtester.data_provider, "数据提供者应该已初始化")
        self.assertIsNotNone(self.backtester.strategy, "策略应该已初始化")
        self.assertIsNotNone(self.backtester.portfolio, "投资组合应该已初始化")
        self.assertIsNotNone(self.backtester.broker, "经纪商应该已初始化")
        
        # 验证起止日期
        self.assertEqual(self.backtester.start_date, datetime(2023, 1, 1), "起始日期应为2023-01-01")
        self.assertEqual(self.backtester.end_date, datetime(2023, 1, 20), "结束日期应为2023-01-20")
    
    def test_backtest_run(self):
        """测试运行回测"""
        # 捕获输出
        output = StringIO()
        with redirect_stdout(output):
            # 运行回测
            self.backtester.run_backtest()
        
        # 验证事件处理
        self.assertGreater(self.event_counters[EventType.MARKET], 0, "应该处理市场事件")
        self.assertGreater(self.event_counters[EventType.SIGNAL], 0, "应该处理信号事件")
        self.assertGreater(self.event_counters[EventType.ORDER], 0, "应该处理订单事件")
        self.assertGreater(self.event_counters[EventType.FILL], 0, "应该处理成交事件")
        
        # 验证投资组合状态
        final_portfolio_value = self.portfolio.get_portfolio_value()
        self.assertNotEqual(final_portfolio_value, 100000.0, "投资组合价值应该变化")
        
        # 输出回测结果摘要
        print(f"\n回测完成！")
        print(f"处理的事件统计:")
        print(f"- 市场事件: {self.event_counters[EventType.MARKET]}")
        print(f"- 信号事件: {self.event_counters[EventType.SIGNAL]}")
        print(f"- 订单事件: {self.event_counters[EventType.ORDER]}")
        print(f"- 成交事件: {self.event_counters[EventType.FILL]}")
        print(f"\n初始资金: 100,000.00")
        print(f"最终投资组合价值: {final_portfolio_value:.2f}")
        print(f"收益: {final_portfolio_value - 100000.0:.2f}")
        print(f"收益率: {(final_portfolio_value / 100000.0 - 1) * 100:.2f}%")
    
    def test_portfolio_positions(self):
        """测试投资组合持仓"""
        # 运行回测
        self.backtester.run_backtest()
        
        # 获取持仓
        positions = self.portfolio.positions
        
        # 验证持仓
        self.assertTrue(len(positions) > 0, "投资组合应该有持仓")
        
        # 输出持仓信息
        print("\n投资组合持仓:")
        for symbol, position in positions.items():
            print(f"{symbol}: {position.quantity} 股, 市值: {position.market_value:.2f}")
    
    def test_backtest_statistics(self):
        """测试回测统计信息"""
        # 运行回测
        self.backtester.run_backtest()
        
        # 获取交易历史
        trade_history = self.portfolio.trade_history
        
        # 验证交易历史
        self.assertTrue(len(trade_history) > 0, "应该有交易历史")
        
        # 计算一些基本统计信息
        win_trades = sum(1 for trade in trade_history if trade['pnl'] > 0)
        loss_trades = sum(1 for trade in trade_history if trade['pnl'] < 0)
        total_trades = len(trade_history)
        win_rate = win_trades / total_trades if total_trades > 0 else 0
        
        # 输出统计信息
        print("\n回测统计信息:")
        print(f"总交易次数: {total_trades}")
        print(f"盈利交易: {win_trades}")
        print(f"亏损交易: {loss_trades}")
        print(f"胜率: {win_rate:.2%}")
        
        # 如果有足够的交易，验证胜率
        if total_trades > 5:
            self.assertGreaterEqual(win_rate, 0.0, "胜率应该大于或等于0")
            self.assertLessEqual(win_rate, 1.0, "胜率应该小于或等于1")

if __name__ == "__main__":
    unittest.main() 