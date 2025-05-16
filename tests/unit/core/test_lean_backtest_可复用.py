#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QuantConnect LEAN风格的事件驱动回测测试脚本
特点：模块化架构、事件驱动设计、高真实度回测
"""
import os
import datetime
import time
import queue
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pytz
from enum import Enum
import uuid

# 定义事件类型
class EventType(Enum):
    MARKET_DATA = 1
    SIGNAL = 2
    ORDER = 3
    FILL = 4
    CUSTOM = 5

# 基础事件类
class Event:
    """事件基类"""
    def __init__(self, event_type):
        self.event_type = event_type
        self.timestamp = datetime.datetime.now()

# 市场数据事件
class MarketDataEvent(Event):
    """市场数据事件"""
    def __init__(self, timestamp, symbol, open_price, high_price, low_price, close_price, volume):
        super().__init__(EventType.MARKET_DATA)
        self.timestamp = timestamp
        self.symbol = symbol
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume

# 信号事件
class SignalEvent(Event):
    """信号事件"""
    def __init__(self, timestamp, symbol, signal_type, strength=1.0):
        super().__init__(EventType.SIGNAL)
        self.timestamp = timestamp
        self.symbol = symbol
        self.signal_type = signal_type  # 'LONG', 'SHORT', 'EXIT'
        self.strength = strength  # 信号强度，1.0表示满仓

# 订单事件
class OrderEvent(Event):
    """订单事件"""
    def __init__(self, timestamp, symbol, order_type, quantity, direction):
        super().__init__(EventType.ORDER)
        self.timestamp = timestamp
        self.symbol = symbol
        self.order_type = order_type  # 'MARKET', 'LIMIT', 'STOP'
        self.quantity = quantity
        self.direction = direction  # 'BUY', 'SELL'
        self.order_id = str(uuid.uuid4())[:8]  # 生成唯一订单ID

# 成交事件
class FillEvent(Event):
    """成交事件"""
    def __init__(self, timestamp, symbol, quantity, direction, fill_price, commission=0.0):
        super().__init__(EventType.FILL)
        self.timestamp = timestamp
        self.symbol = symbol
        self.quantity = quantity
        self.direction = direction
        self.fill_price = fill_price
        self.commission = commission

# 事件队列
class EventQueue:
    """事件队列类"""
    def __init__(self):
        self.queue = queue.Queue()
    
    def add_event(self, event):
        """添加事件到队列"""
        self.queue.put(event)
    
    def get_next_event(self):
        """获取下一个事件"""
        if self.queue.empty():
            return None
        return self.queue.get()
    
    def is_empty(self):
        """检查队列是否为空"""
        return self.queue.empty()

# 数据处理和事件生成
class DataHandler:
    """数据处理器基类"""
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.symbols = []
        self.latest_data = {}
        self.continue_backtest = True
    
    def get_latest_data(self, symbol, n=1):
        """获取最新的n条数据"""
        pass
    
    def update_data(self):
        """更新数据"""
        pass

# CSV数据处理器
class CSVDataHandler(DataHandler):
    """CSV数据处理器"""
    def __init__(self, event_queue, csv_dir, symbol_list, start_date, end_date=None):
        super().__init__(event_queue)
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.symbols = symbol_list
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.datetime.now()
        
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.data_index = 0
        
        self._load_and_process_csv_files()
    
    def _load_and_process_csv_files(self):
        """加载并处理CSV文件数据"""
        combined_index = None
        for symbol in self.symbol_list:
            file_path = os.path.join(self.csv_dir, f"{symbol}/price.csv")
            
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                df = df.sort_index()  # 确保按日期排序
                # 重命名列确保统一
                df = df.rename(columns={c: c.lower() for c in df.columns})
                if 'datetime' in df.columns:
                    df.index = pd.to_datetime(df['datetime'])
                    df = df.drop(columns=['datetime'])
                
                # 过滤日期范围
                mask = (df.index >= self.start_date) & (df.index <= self.end_date)
                df = df.loc[mask]
                
                # 确保至少有open, high, low, close, volume列
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col not in df.columns:
                        if col == 'volume':
                            df[col] = 0
                        else:
                            # 使用close填充缺失的价格列
                            df[col] = df['close'] if 'close' in df.columns else 0
                
                self.symbol_data[symbol] = df
                if combined_index is None:
                    combined_index = df.index
                else:
                    combined_index = combined_index.union(df.index)
            else:
                print(f"警告: 找不到{file_path}，生成模拟数据")
                # 生成模拟数据
                dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
                dates = dates[dates.dayofweek < 5]  # 仅保留工作日
                
                np.random.seed(42 + len(symbol))  # 确保每个模拟数据集不同
                price = 100.0  # 初始价格
                prices = [price]
                
                # 生成随机价格序列
                for _ in range(1, len(dates)):
                    price = price * (1 + np.random.normal(0, 0.01))
                    prices.append(price)
                
                # 创建DataFrame
                df = pd.DataFrame(index=dates)
                df['close'] = prices
                df['open'] = df['close'].shift(1).fillna(prices[0] * 0.99)
                df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.02, size=len(df)))
                df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.02, size=len(df)))
                df['volume'] = np.random.randint(100000, 1000000, size=len(df))
                
                self.symbol_data[symbol] = df
                if combined_index is None:
                    combined_index = df.index
                else:
                    combined_index = combined_index.union(df.index)
        
        # 确保所有数据使用相同的索引，以便正确对齐
        self.all_dates = sorted(combined_index)
    
    def get_latest_data(self, symbol, n=1):
        """获取最新的n条数据"""
        if symbol not in self.latest_symbol_data:
            return None
        
        try:
            return self.latest_symbol_data[symbol][-n:]
        except IndexError:
            return self.latest_symbol_data[symbol]
    
    def update_data(self):
        """更新数据并生成市场数据事件"""
        if self.data_index >= len(self.all_dates):
            self.continue_backtest = False
            return
        
        # 获取当前日期
        current_date = self.all_dates[self.data_index]
        self.data_index += 1
        
        # 为每个交易品种更新并生成事件
        for symbol in self.symbol_list:
            if symbol in self.symbol_data and current_date in self.symbol_data[symbol].index:
                symbol_df = self.symbol_data[symbol]
                
                # 获取当前日期的数据
                bar = symbol_df.loc[current_date]
                
                # 创建市场数据事件
                bar_event = MarketDataEvent(
                    timestamp=current_date,
                    symbol=symbol,
                    open_price=bar['open'],
                    high_price=bar['high'],
                    low_price=bar['low'],
                    close_price=bar['close'],
                    volume=bar['volume']
                )
                
                # 添加事件到队列
                self.event_queue.add_event(bar_event)
                
                # 更新最新数据
                if symbol not in self.latest_symbol_data:
                    self.latest_symbol_data[symbol] = []
                
                self.latest_symbol_data[symbol].append(bar_event)

# 策略基类
class Strategy:
    """策略基类"""
    def __init__(self, data_handler, event_queue):
        self.data_handler = data_handler
        self.event_queue = event_queue
        self.current_positions = {}  # 当前持仓
        
        for symbol in self.data_handler.symbols:
            self.current_positions[symbol] = 0
    
    def calculate_signals(self, event):
        """计算交易信号 - 由子类实现"""
        raise NotImplementedError("calculate_signals() 方法必须由子类实现!")

# 具体策略实现: 双均线交叉策略
class MovingAverageCrossStrategy(Strategy):
    """双均线交叉策略"""
    def __init__(self, data_handler, event_queue, short_window=10, long_window=30):
        super().__init__(data_handler, event_queue)
        self.short_window = short_window
        self.long_window = long_window
        self.bought = {}  # 记录持仓状态：1为持有多头，-1为持有空头，0为未持仓
        
        for symbol in self.data_handler.symbols:
            self.bought[symbol] = 0
    
    def calculate_signals(self, event):
        """计算双均线交叉信号"""
        if event.event_type == EventType.MARKET_DATA:
            symbol = event.symbol
            latest_data = self.data_handler.get_latest_data(symbol, n=self.long_window+1)
            
            if latest_data is None or len(latest_data) < self.long_window:
                return  # 数据不足以计算均线
            
            # 获取收盘价序列
            closes = [bar.close for bar in latest_data]
            
            # 计算短期和长期简单移动平均线
            short_sma = sum(closes[-self.short_window:]) / self.short_window
            long_sma = sum(closes[-self.long_window:]) / self.long_window
            
            # 当前收盘价
            current_close = closes[-1]
            
            # 信号逻辑
            # 空仓状态下，短期均线上穿长期均线，开多仓
            if short_sma > long_sma and self.bought[symbol] <= 0:
                # 如果当前持有空头，先平仓
                if self.bought[symbol] < 0:
                    exit_signal = SignalEvent(
                        timestamp=event.timestamp,
                        symbol=symbol,
                        signal_type="EXIT",
                        strength=1.0
                    )
                    self.event_queue.add_event(exit_signal)
                
                # 发出多头信号
                signal = SignalEvent(
                    timestamp=event.timestamp,
                    symbol=symbol,
                    signal_type="LONG",
                    strength=1.0
                )
                self.event_queue.add_event(signal)
                self.bought[symbol] = 1
            
            # 持多仓状态下，短期均线下穿长期均线，平多仓
            elif short_sma < long_sma and self.bought[symbol] >= 0:
                # 如果当前持有多头，先平仓
                if self.bought[symbol] > 0:
                    exit_signal = SignalEvent(
                        timestamp=event.timestamp,
                        symbol=symbol,
                        signal_type="EXIT",
                        strength=1.0
                    )
                    self.event_queue.add_event(exit_signal)
                
                # 目前我们不做空，只平仓
                self.bought[symbol] = 0

# 投资组合管理类
class Portfolio:
    """投资组合管理类"""
    def __init__(self, data_handler, event_queue, initial_capital=100000.0):
        self.data_handler = data_handler
        self.event_queue = event_queue
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.equity = initial_capital
        
        # 持仓记录
        self.positions = {}  # symbol -> quantity
        self.holdings = {}   # symbol -> market value
        
        # 交易记录
        self.transactions = []
        
        # 资金曲线和绩效指标
        self.equity_curve = []
        self.daily_returns = []
        self.timestamps = []
        
        # 初始化持仓
        for symbol in self.data_handler.symbols:
            self.positions[symbol] = 0
            self.holdings[symbol] = 0.0
    
    def update_signal(self, event):
        """处理信号事件，生成订单"""
        if event.event_type == EventType.SIGNAL:
            symbol = event.symbol
            signal_type = event.signal_type
            strength = event.strength
            
            # 获取最新市场数据
            market_data = self.data_handler.get_latest_data(symbol, n=1)
            if market_data is None or len(market_data) == 0:
                return
            
            current_price = market_data[-1].close
            
            # 计算订单数量 (简化版本：假设全仓操作，不考虑资产分配)
            order_size = self._calculate_order_size(symbol, signal_type, strength, current_price)
            
            if order_size == 0:
                return
            
            # 创建订单事件
            direction = "BUY" if order_size > 0 else "SELL"
            
            order = OrderEvent(
                timestamp=event.timestamp,
                symbol=symbol,
                order_type="MARKET",
                quantity=abs(order_size),
                direction=direction
            )
            
            self.event_queue.add_event(order)
    
    def _calculate_order_size(self, symbol, signal_type, strength, current_price):
        """计算订单大小"""
        if signal_type == "EXIT":
            # 平仓
            return -self.positions[symbol]  # 返回负的持仓数量，表示平仓
        
        # 计算可用资金
        available_capital = self.current_capital * strength
        
        # 计算可买入数量（简化版本，不考虑手续费和滑点）
        if signal_type == "LONG":
            # 买入信号，计算买入数量
            shares = int(available_capital / current_price)
            return shares
        elif signal_type == "SHORT":
            # 卖出信号，如果允许做空
            shares = int(available_capital / current_price)
            return -shares
        
        return 0
    
    def update_fill(self, event):
        """处理成交事件，更新持仓"""
        if event.event_type == EventType.FILL:
            self._update_positions_from_fill(event)
            self._update_holdings_from_fill(event)
            
            # 记录交易
            transaction = {
                'timestamp': event.timestamp,
                'symbol': event.symbol,
                'direction': event.direction,
                'quantity': event.quantity,
                'price': event.fill_price,
                'commission': event.commission,
                'value': event.quantity * event.fill_price,
                'total_cost': event.quantity * event.fill_price + event.commission
            }
            self.transactions.append(transaction)
            
            # 更新资金
            if event.direction == "BUY":
                self.current_capital -= (event.quantity * event.fill_price + event.commission)
            else:  # "SELL"
                self.current_capital += (event.quantity * event.fill_price - event.commission)
    
    def _update_positions_from_fill(self, fill):
        """根据成交事件更新持仓数量"""
        symbol = fill.symbol
        # 更新持仓数量
        if fill.direction == "BUY":
            self.positions[symbol] += fill.quantity
        else:  # "SELL"
            self.positions[symbol] -= fill.quantity
    
    def _update_holdings_from_fill(self, fill):
        """根据成交事件更新持仓市值"""
        symbol = fill.symbol
        # 更新持仓市值
        cost = fill.quantity * fill.fill_price
        
        if fill.direction == "BUY":
            self.holdings[symbol] += cost
        else:  # "SELL"
            self.holdings[symbol] -= cost
    
    def update_timeindex(self, market_data_event):
        """根据最新市场数据更新投资组合状态"""
        symbol = market_data_event.symbol
        latest_price = market_data_event.close
        
        # 更新持仓市值
        self.holdings[symbol] = self.positions[symbol] * latest_price
        
        # 计算当前总资产
        total_holdings = sum(self.holdings.values())
        self.equity = self.current_capital + total_holdings
        
        # 更新资金曲线
        self.equity_curve.append(self.equity)
        self.timestamps.append(market_data_event.timestamp)
        
        # 计算每日收益率
        if len(self.equity_curve) > 1:
            daily_return = self.equity_curve[-1] / self.equity_curve[-2] - 1
            self.daily_returns.append(daily_return)
        else:
            self.daily_returns.append(0.0)
    
    def get_performance_stats(self):
        """计算绩效统计指标"""
        returns = pd.Series(self.daily_returns)
        equity_curve = pd.Series(self.equity_curve, index=self.timestamps)
        
        # 总收益率
        total_return = (self.equity / self.initial_capital) - 1
        
        # 年化收益率
        num_days = (self.timestamps[-1] - self.timestamps[0]).days
        annualized_return = (1 + total_return) ** (365 / num_days) - 1 if num_days > 0 else 0
        
        # 最大回撤
        running_max = pd.Series(equity_curve).cummax()
        drawdown = (running_max - equity_curve) / running_max
        max_drawdown = drawdown.max()
        
        # 夏普比率 (简化版，假设无风险收益率=0)
        sharpe_ratio = returns.mean() / returns.std() * (252 ** 0.5) if len(returns) > 1 and returns.std() > 0 else 0
        
        # 交易次数
        num_trades = len(self.transactions)
        
        # 胜率 (盈利交易数量 / 总交易数量)
        if num_trades > 0:
            profit_trades = sum(1 for t in self.transactions if 
                                (t['direction'] == 'BUY' and self.holdings[t['symbol']] > t['value']) or
                                (t['direction'] == 'SELL' and self.holdings[t['symbol']] < t['value']))
            win_rate = profit_trades / num_trades
        else:
            win_rate = 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'equity_curve': equity_curve
        }

# 执行引擎类
class ExecutionHandler:
    """执行引擎负责处理订单并生成成交事件"""
    def __init__(self, event_queue):
        self.event_queue = event_queue
    
    def execute_order(self, event):
        """处理订单，生成成交事件"""
        if event.event_type == EventType.ORDER:
            # 获取最新数据
            latest_price = None
            # 在实际情况下，我们需要从数据源获取最新价格，这里简化为直接使用订单中的价格
            
            # 简化处理：假设所有订单都能立即以市价成交
            fill_event = FillEvent(
                timestamp=event.timestamp,
                symbol=event.symbol,
                quantity=event.quantity,
                direction=event.direction,
                fill_price=latest_price if latest_price else 0.0,
                commission=self._calculate_commission(event)
            )
            
            self.event_queue.add_event(fill_event)
    
    def _calculate_commission(self, order_event):
        """计算交易佣金"""
        # 简化计算：假设佣金为交易额的0.1%
        # 实际应用中，佣金计算可能更复杂，涉及固定费用、阶梯费率等
        return 0.001 * order_event.quantity * (order_event.fill_price if hasattr(order_event, 'fill_price') else 0.0)

# 模拟交易所
class Exchange:
    """模拟交易所，提供市价查询和订单撮合功能"""
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.last_prices = {}  # symbol -> last_price
    
    def get_latest_price(self, symbol):
        """获取最新市价"""
        market_data = self.data_handler.get_latest_data(symbol, n=1)
        if market_data is None or len(market_data) == 0:
            return None
        
        last_price = market_data[-1].close
        self.last_prices[symbol] = last_price
        return last_price
    
    def execute_market_order(self, order_event):
        """执行市价单"""
        # 获取最新价格
        price = self.get_latest_price(order_event.symbol)
        if price is None:
            return None  # 无法获取价格，不能执行订单
        
        # 计算佣金 (简化：按交易额的0.1%)
        commission = 0.001 * order_event.quantity * price
        
        # 创建成交事件
        fill_event = FillEvent(
            timestamp=order_event.timestamp,
            symbol=order_event.symbol,
            quantity=order_event.quantity,
            direction=order_event.direction,
            fill_price=price,
            commission=commission
        )
        
        return fill_event

# 回测引擎
class Backtest:
    """回测引擎 - 协调数据、策略、投资组合和执行"""
    def __init__(self, symbol_list, initial_capital, start_date, end_date, data_dir, strategy_class, strategy_params={}):
        """
        初始化回测
        
        Parameters:
        -----------
        symbol_list: 股票代码列表
        initial_capital: 初始资金
        start_date: 回测开始日期
        end_date: 回测结束日期
        data_dir: 数据目录
        strategy_class: 策略类
        strategy_params: 策略参数字典
        """
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        self.data_dir = data_dir
        self.strategy_class = strategy_class
        self.strategy_params = strategy_params
        
        # 创建事件队列
        self.events = EventQueue()
        
        # 创建数据处理器
        self.data_handler = CSVDataHandler(self.events, self.data_dir, self.symbol_list, self.start_date, self.end_date)
        
        # 创建策略
        self.strategy = self.strategy_class(self.data_handler, self.events, **self.strategy_params)
        
        # 创建投资组合
        self.portfolio = Portfolio(self.data_handler, self.events, self.initial_capital)
        
        # 创建交易所
        self.exchange = Exchange(self.data_handler)
        
        # 性能跟踪
        self.start_time = None
        self.end_time = None
        self.event_counts = {
            EventType.MARKET_DATA: 0,
            EventType.SIGNAL: 0,
            EventType.ORDER: 0,
            EventType.FILL: 0
        }
    
    def run_backtest(self):
        """运行回测主循环"""
        self.start_time = time.time()
        
        while True:
            # 检查数据源是否已经枯竭
            if not self.data_handler.continue_backtest:
                break
            
            # 获取新的市场数据
            self.data_handler.update_data()
            
            # 处理事件队列中的所有事件
            while not self.events.is_empty():
                event = self.events.get_next_event()
                
                # 统计事件数量
                if event.event_type in self.event_counts:
                    self.event_counts[event.event_type] += 1
                
                # 根据事件类型分发处理
                if event.event_type == EventType.MARKET_DATA:
                    self.strategy.calculate_signals(event)
                    self.portfolio.update_timeindex(event)
                    
                elif event.event_type == EventType.SIGNAL:
                    self.portfolio.update_signal(event)
                    
                elif event.event_type == EventType.ORDER:
                    # 通过交易所执行订单
                    fill_event = self.exchange.execute_market_order(event)
                    if fill_event:
                        self.events.add_event(fill_event)
                    
                elif event.event_type == EventType.FILL:
                    self.portfolio.update_fill(event)
        
        self.end_time = time.time()
        
        # 计算性能统计
        performance_stats = self.portfolio.get_performance_stats()
        performance_stats['execution_time'] = self.end_time - self.start_time
        performance_stats['events_processed'] = sum(self.event_counts.values())
        
        return performance_stats
    
    def plot_results(self):
        """绘制回测结果"""
        performance = self.portfolio.get_performance_stats()
        equity_curve = performance['equity_curve']
        
        plt.figure(figsize=(14, 10))
        
        # 绘制资金曲线
        plt.subplot(2, 1, 1)
        plt.plot(equity_curve.index, equity_curve.values, linewidth=2)
        plt.title('资金曲线')
        plt.xlabel('日期')
        plt.ylabel('资产价值')
        plt.grid(True)
        
        # 绘制回撤
        plt.subplot(2, 1, 2)
        running_max = equity_curve.cummax()
        drawdown = (running_max - equity_curve) / running_max
        plt.fill_between(drawdown.index, drawdown.values, color='red', alpha=0.3)
        plt.title('回撤')
        plt.xlabel('日期')
        plt.ylabel('回撤比例')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig('lean_backtest_results.png', dpi=300)
        plt.show()
        
        # 打印统计数据
        print("\n============= 回测统计 =============")
        print(f"总收益率: {performance['total_return']:.2%}")
        print(f"年化收益率: {performance['annualized_return']:.2%}")
        print(f"最大回撤: {performance['max_drawdown']:.2%}")
        print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
        print(f"交易次数: {performance['num_trades']}")
        print(f"胜率: {performance['win_rate']:.2%}")
        print(f"\n执行时间: {self.end_time - self.start_time:.2f} 秒")
        print(f"处理事件数: {sum(self.event_counts.values())}")
        for event_type, count in self.event_counts.items():
            print(f"  {event_type.name}: {count}")

def main():
    """主函数"""
    print("============= LEAN风格事件驱动回测引擎 - 双均线交叉策略 =============")
    
    # 设置参数
    symbol_list = ['000001']  # 上证指数
    initial_capital = 100000.0
    start_date = '2020-01-01'
    end_date = '2022-12-31'
    data_dir = "../data/backtest_data/daily/SHSE"
    
    # 策略参数
    strategy_params = {
        'short_window': 10,
        'long_window': 30
    }
    
    # 创建回测实例
    backtest = Backtest(
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        data_dir=data_dir,
        strategy_class=MovingAverageCrossStrategy,
        strategy_params=strategy_params
    )
    
    # 运行回测
    print("开始回测...")
    performance = backtest.run_backtest()
    
    # 绘制结果
    try:
        backtest.plot_results()
    except Exception as e:
        print(f"绘图出错: {e}")
    
    # 打印结果摘要
    print("\n============= 回测结果摘要 =============")
    print(f"总收益率: {performance['total_return']:.2%}")
    print(f"年化收益率: {performance['annualized_return']:.2%}")
    print(f"最大回撤: {performance['max_drawdown']:.2%}")
    print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
    print(f"交易次数: {performance['num_trades']}")
    
    print("\n============= 性能指标 =============")
    print(f"执行时间: {performance['execution_time']:.2f} 秒")
    print(f"处理事件总数: {performance['events_processed']}")
    print("注: LEAN框架的核心优势在于模块化设计和事件驱动架构，而非原始性能")

if __name__ == "__main__":
    main() 