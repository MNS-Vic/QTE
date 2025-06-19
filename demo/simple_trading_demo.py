"""
QTE简单交易演示
展示基本的量化交易流程：数据输入 → 策略执行 → 订单管理 → 回测报告
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json

try:
    from qte.core.engine_manager import ReplayEngineManager
    from qte.core.event_engine import EventDrivenBacktester
    from qte.core.events import MarketEvent, SignalEvent, OrderEvent, FillEvent
    from qte.core.time_manager import TimeManager
except ImportError as e:
    print(f"Warning: QTE core modules import failed: {e}")
    # 提供Mock类以便测试
    class MockClass:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self
        def __getattr__(self, name):
            return MockClass()

    ReplayEngineManager = MockClass
    EventDrivenBacktester = MockClass
    MarketEvent = MockClass
    SignalEvent = MockClass
    OrderEvent = MockClass
    FillEvent = MockClass
    TimeManager = MockClass

class SimpleTradeDemo:
    """简单交易演示类"""
    
    def __init__(self):
        self.logger = logging.getLogger('SimpleDemo')
        self.output_dir = Path('demo_output')
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.engine_manager = None
        self.backtester = None
        self.time_manager = TimeManager()
        
        # 演示参数
        self.initial_capital = 100000.0
        self.symbols = ['AAPL', 'GOOGL', 'MSFT']
        
    def generate_sample_data(self):
        """生成示例市场数据"""
        self.logger.info("📊 生成示例市场数据...")
        
        # 生成30天的交易数据
        start_date = datetime.now() - timedelta(days=30)
        dates = pd.date_range(start_date, periods=30, freq='D')
        
        market_data = {}
        
        for symbol in self.symbols:
            # 生成随机价格数据
            np.random.seed(hash(symbol) % 2**32)  # 确保可重复性
            
            base_price = np.random.uniform(100, 300)
            returns = np.random.normal(0.001, 0.02, len(dates))
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            # 生成OHLCV数据
            data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                high = close * np.random.uniform(1.001, 1.02)
                low = close * np.random.uniform(0.98, 0.999)
                open_price = close * np.random.uniform(0.995, 1.005)
                volume = np.random.randint(1000000, 5000000)
                
                data.append({
                    'timestamp': date,
                    'symbol': symbol,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close, 2),
                    'volume': volume
                })
            
            market_data[symbol] = data
        
        # 保存数据到文件
        data_file = self.output_dir / 'sample_market_data.json'
        with open(data_file, 'w') as f:
            json.dump(market_data, f, default=str, indent=2)
        
        self.logger.info(f"✅ 市场数据已生成: {data_file}")
        return market_data
    
    def create_simple_strategy(self):
        """创建简单的移动平均策略"""
        self.logger.info("🧠 创建简单移动平均策略...")
        
        class SimpleMAStrategy:
            def __init__(self, short_window=5, long_window=15):
                self.short_window = short_window
                self.long_window = long_window
                self.price_history = {}
                self.positions = {}
                
            def process_market_data(self, market_event):
                """处理市场数据并生成信号"""
                symbol = market_event.symbol
                price = market_event.close_price
                
                # 初始化价格历史
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                    self.positions[symbol] = 0
                
                self.price_history[symbol].append(price)
                
                # 保持历史数据长度
                if len(self.price_history[symbol]) > self.long_window:
                    self.price_history[symbol] = self.price_history[symbol][-self.long_window:]
                
                # 计算移动平均
                if len(self.price_history[symbol]) >= self.long_window:
                    short_ma = np.mean(self.price_history[symbol][-self.short_window:])
                    long_ma = np.mean(self.price_history[symbol][-self.long_window:])
                    
                    # 生成交易信号
                    current_position = self.positions[symbol]
                    
                    if short_ma > long_ma and current_position <= 0:
                        # 买入信号
                        return SignalEvent(
                            symbol=symbol,
                            timestamp=market_event.timestamp,
                            signal_type='LONG',
                            direction=1,
                            strength=1.0
                        )
                    elif short_ma < long_ma and current_position >= 0:
                        # 卖出信号
                        return SignalEvent(
                            symbol=symbol,
                            timestamp=market_event.timestamp,
                            signal_type='SHORT',
                            direction=-1,
                            strength=1.0
                        )
                
                return None
            
            def update_position(self, symbol, direction):
                """更新持仓"""
                self.positions[symbol] = direction
        
        return SimpleMAStrategy()
    
    def run_backtest(self, market_data, strategy):
        """运行回测"""
        self.logger.info("🔄 开始回测...")
        
        # 初始化回测引擎
        self.backtester = EventDrivenBacktester(initial_capital=self.initial_capital)
        
        # 模拟交易过程
        total_trades = 0
        total_pnl = 0.0
        
        for symbol in self.symbols:
            symbol_data = market_data[symbol]
            
            for data_point in symbol_data:
                # 创建市场事件
                market_event = MarketEvent(
                    symbol=data_point['symbol'],
                    timestamp=pd.to_datetime(data_point['timestamp']),
                    open_price=data_point['open'],
                    high_price=data_point['high'],
                    low_price=data_point['low'],
                    close_price=data_point['close'],
                    volume=data_point['volume']
                )
                
                # 策略处理
                signal = strategy.process_market_data(market_event)
                
                if signal:
                    # 生成订单
                    quantity = 100  # 固定数量
                    order = OrderEvent(
                        symbol=signal.symbol,
                        timestamp=signal.timestamp,
                        order_type='MARKET',
                        quantity=quantity,
                        direction=signal.direction
                    )
                    
                    # 模拟成交
                    fill = FillEvent(
                        symbol=order.symbol,
                        timestamp=order.timestamp,
                        quantity=order.quantity,
                        direction=order.direction,
                        fill_price=market_event.close_price,
                        commission=5.0  # 固定手续费
                    )
                    
                    # 更新策略持仓
                    strategy.update_position(signal.symbol, signal.direction)
                    
                    # 计算盈亏
                    pnl = quantity * market_event.close_price * signal.direction
                    total_pnl += pnl
                    total_trades += 1
                    
                    self.logger.debug(f"📈 交易: {signal.symbol} {signal.signal_type} "
                                    f"价格:{market_event.close_price:.2f} 数量:{quantity}")
                
                # 更新权益历史
                current_equity = self.initial_capital + total_pnl
                self.backtester.equity_history.append({
                    'timestamp': market_event.timestamp,
                    'equity': current_equity
                })
        
        self.logger.info(f"✅ 回测完成，总交易次数: {total_trades}")
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'final_equity': self.initial_capital + total_pnl
        }
    
    def generate_report(self, backtest_results):
        """生成回测报告"""
        self.logger.info("📋 生成回测报告...")
        
        # 计算回测指标
        results = self.backtester._calculate_results()
        
        # 合并结果
        final_results = {
            **backtest_results,
            **results
        }
        
        # 保存报告
        report_file = self.output_dir / 'simple_demo_report.json'
        with open(report_file, 'w') as f:
            json.dump(final_results, f, default=str, indent=2)
        
        # 打印摘要
        self.logger.info("📊 回测结果摘要:")
        self.logger.info(f"   初始资金: ${self.initial_capital:,.2f}")
        self.logger.info(f"   最终权益: ${final_results['final_equity']:,.2f}")
        self.logger.info(f"   总收益: ${final_results['total_pnl']:,.2f}")
        self.logger.info(f"   收益率: {(final_results['final_equity']/self.initial_capital-1)*100:.2f}%")
        self.logger.info(f"   交易次数: {final_results['total_trades']}")
        
        if 'metrics' in final_results:
            metrics = final_results['metrics']
            self.logger.info(f"   年化收益率: {metrics.get('annual_return', 0)*100:.2f}%")
            self.logger.info(f"   最大回撤: {metrics.get('max_drawdown', 0)*100:.2f}%")
            self.logger.info(f"   夏普比率: {metrics.get('sharpe_ratio', 0):.3f}")
        
        self.logger.info(f"📁 详细报告已保存: {report_file}")
        return final_results
    
    def run(self):
        """运行完整的简单演示"""
        self.logger.info("🚀 开始QTE简单交易演示...")
        
        try:
            # 1. 生成示例数据
            market_data = self.generate_sample_data()
            
            # 2. 创建交易策略
            strategy = self.create_simple_strategy()
            
            # 3. 运行回测
            backtest_results = self.run_backtest(market_data, strategy)
            
            # 4. 生成报告
            final_results = self.generate_report(backtest_results)
            
            self.logger.info("🎉 简单演示完成!")
            return final_results
            
        except Exception as e:
            self.logger.error(f"❌ 演示运行失败: {e}")
            raise
