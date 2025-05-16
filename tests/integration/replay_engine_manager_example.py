"""
数据重放控制器与引擎管理器集成示例

演示如何使用数据重放控制器与引擎管理器配合工作实现策略回测
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qte.data.data_replay import (
    ReplayMode, ReplayStatus, 
    DataFrameReplayController,
    MultiSourceReplayController
)

from qte.core.engine_manager import (
    EngineType, EngineStatus, EngineEvent,
    MarketDataEvent, SignalEvent, OrderEvent, FillEvent,
    BaseEngineManager, ReplayEngineManager
)

def create_test_data(size=100, symbol="000001.SZ", start_price=100):
    """创建测试数据"""
    # 创建日期范围（每分钟一个点）
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=size, freq='1min')
    
    # 创建价格数据（模拟股票价格）
    prices = np.cumsum(np.random.normal(0, 1, size)) + start_price
    
    # 创建成交量数据
    volumes = np.abs(np.random.normal(10000, 5000, size)).astype(int)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'price': prices,
        'volume': volumes,
        'symbol': [symbol] * size
    })
    
    return df

class SimpleMovingAverageStrategy:
    """简单移动平均线策略"""
    
    def __init__(self, short_window=5, long_window=10):
        """
        初始化移动平均线策略
        
        Parameters
        ----------
        short_window : int, optional
            短期窗口长度, by default 5
        long_window : int, optional
            长期窗口长度, by default 10
        """
        self.short_window = short_window
        self.long_window = long_window
        self.prices = {}  # 股票代码 -> 价格列表
        self.positions = {}  # 股票代码 -> 当前持仓
    
    def on_market_data(self, event):
        """
        处理市场数据事件
        
        Parameters
        ----------
        event : MarketDataEvent
            市场数据事件
        
        Returns
        -------
        Optional[SignalEvent]
            如果满足交易条件则返回信号事件，否则返回None
        """
        symbol = event.symbol
        data = event.data
        timestamp = event.timestamp
        
        # 将价格添加到历史数据中
        if symbol not in self.prices:
            self.prices[symbol] = []
            self.positions[symbol] = 0
        
        self.prices[symbol].append(data['price'])
        
        # 如果数据不足以计算移动平均线，则返回
        if len(self.prices[symbol]) < self.long_window:
            return None
        
        # 计算短期和长期移动平均线
        short_ma = np.mean(self.prices[symbol][-self.short_window:])
        long_ma = np.mean(self.prices[symbol][-self.long_window:])
        
        # 生成交易信号
        signal = None
        if short_ma > long_ma and self.positions[symbol] <= 0:
            # 金叉，生成买入信号
            signal = SignalEvent(timestamp, symbol, "BUY", 1.0)
            self.positions[symbol] = 1
            print(f"[{timestamp}] 金叉信号: {symbol}, 短期MA={short_ma:.2f}, 长期MA={long_ma:.2f} -> 买入")
        elif short_ma < long_ma and self.positions[symbol] >= 0:
            # 死叉，生成卖出信号
            signal = SignalEvent(timestamp, symbol, "SELL", 1.0)
            self.positions[symbol] = -1
            print(f"[{timestamp}] 死叉信号: {symbol}, 短期MA={short_ma:.2f}, 长期MA={long_ma:.2f} -> 卖出")
        
        return signal

class SimplePortfolio:
    """简单投资组合"""
    
    def __init__(self, initial_capital=100000.0):
        """
        初始化投资组合
        
        Parameters
        ----------
        initial_capital : float, optional
            初始资金, by default 100000.0
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # 股票代码 -> 持仓数量
        self.current_prices = {}  # 股票代码 -> 当前价格
        self.trades = []  # 交易记录
        self.equity_curve = []  # 权益曲线
    
    def on_market_data(self, event):
        """
        处理市场数据事件
        
        Parameters
        ----------
        event : MarketDataEvent
            市场数据事件
        """
        symbol = event.symbol
        data = event.data
        timestamp = event.timestamp
        
        # 更新当前价格
        self.current_prices[symbol] = data['price']
        
        # 如果是新股票，初始化持仓为0
        if symbol not in self.positions:
            self.positions[symbol] = 0
        
        # 更新权益曲线
        self._update_equity_curve(timestamp)
    
    def on_signal(self, event):
        """
        处理信号事件
        
        Parameters
        ----------
        event : SignalEvent
            信号事件
            
        Returns
        -------
        Optional[OrderEvent]
            如果生成订单则返回订单事件，否则返回None
        """
        symbol = event.symbol
        signal_type = event.signal_type
        timestamp = event.timestamp
        
        # 如果没有价格数据，不能生成订单
        if symbol not in self.current_prices:
            return None
        
        # 计算订单数量
        price = self.current_prices[symbol]
        order_quantity = 0
        
        if signal_type == "BUY":
            # 简单处理：使用一半资金买入
            order_value = self.cash * 0.5
            order_quantity = int(order_value / price)
        elif signal_type == "SELL":
            # 如果有持仓，全部卖出；如果没有持仓，做空一定数量
            current_position = self.positions.get(symbol, 0)
            if current_position > 0:
                order_quantity = -current_position  # 卖出全部持仓
            else:
                order_value = self.cash * 0.25
                order_quantity = -int(order_value / price)  # 做空
        
        # 如果订单数量为0，不生成订单
        if order_quantity == 0:
            return None
        
        # 生成市价订单
        order = OrderEvent(timestamp, symbol, "MARKET", order_quantity)
        return order
    
    def on_fill(self, event):
        """
        处理成交事件
        
        Parameters
        ----------
        event : FillEvent
            成交事件
        """
        symbol = event.symbol
        quantity = event.quantity
        price = event.price
        commission = event.commission
        timestamp = event.timestamp
        
        # 更新持仓
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] += quantity
        
        # 更新现金
        cost = quantity * price + commission
        self.cash -= cost
        
        # 记录交易
        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'commission': commission,
            'cost': cost,
            'cash': self.cash
        })
        
        # 打印交易信息
        action = "买入" if quantity > 0 else "卖出"
        print(f"[{timestamp}] {action} {symbol}: {abs(quantity)} 股，价格 {price:.2f}，佣金 {commission:.2f}，剩余现金 {self.cash:.2f}")
    
    def _update_equity_curve(self, timestamp):
        """
        更新权益曲线
        
        Parameters
        ----------
        timestamp : datetime
            当前时间戳
        """
        # 计算当前持仓市值
        portfolio_value = self.cash
        for symbol, quantity in self.positions.items():
            if symbol in self.current_prices:
                portfolio_value += quantity * self.current_prices[symbol]
        
        # 添加到权益曲线
        self.equity_curve.append({
            'timestamp': timestamp,
            'portfolio_value': portfolio_value,
            'cash': self.cash
        })
    
    def get_summary(self):
        """
        获取投资组合摘要
        
        Returns
        -------
        dict
            投资组合摘要
        """
        if not self.equity_curve:
            return {
                'initial_capital': self.initial_capital,
                'final_value': self.initial_capital,
                'total_return': 0.0,
                'total_trades': 0
            }
        
        final_value = self.equity_curve[-1]['portfolio_value']
        total_return = (final_value / self.initial_capital - 1) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(self.trades)
        }

class SimpleExecutionHandler:
    """简单执行处理器"""
    
    def __init__(self, commission_rate=0.001):
        """
        初始化执行处理器
        
        Parameters
        ----------
        commission_rate : float, optional
            佣金率, by default 0.001 (0.1%)
        """
        self.commission_rate = commission_rate
        self.current_prices = {}
    
    def on_market_data(self, event):
        """
        处理市场数据事件
        
        Parameters
        ----------
        event : MarketDataEvent
            市场数据事件
        """
        # 更新当前价格
        self.current_prices[event.symbol] = event.data['price']
    
    def on_order(self, event):
        """
        处理订单事件
        
        Parameters
        ----------
        event : OrderEvent
            订单事件
            
        Returns
        -------
        Optional[FillEvent]
            如果订单成功执行则返回成交事件，否则返回None
        """
        symbol = event.symbol
        quantity = event.quantity
        timestamp = event.timestamp
        
        # 检查是否有价格数据
        if symbol not in self.current_prices:
            print(f"警告: 无法执行订单，没有 {symbol} 的价格数据")
            return None
        
        # 获取当前价格
        price = self.current_prices[symbol]
        
        # 计算佣金
        commission = abs(quantity * price * self.commission_rate)
        
        # 创建成交事件
        fill = FillEvent(timestamp, symbol, quantity, price, commission)
        
        return fill

def simple_ma_backtest():
    """使用移动平均线策略进行回测"""
    print("\n===== 移动平均线策略回测 =====")
    
    # 创建测试数据
    df1 = create_test_data(size=100, symbol="000001.SZ", start_price=100)
    df2 = create_test_data(size=100, symbol="000002.SZ", start_price=50)
    
    print(f"数据预览:\n{df1.head()}")
    
    # 创建数据重放控制器
    controller1 = DataFrameReplayController(
        dataframe=df1,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    controller2 = DataFrameReplayController(
        dataframe=df2,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 创建引擎管理器
    engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine.initialize()
    
    # 添加重放控制器
    engine.add_replay_controller("data1", controller1)
    engine.add_replay_controller("data2", controller2)
    
    # 创建策略、投资组合和执行处理器
    strategy = SimpleMovingAverageStrategy(short_window=5, long_window=20)
    portfolio = SimplePortfolio(initial_capital=100000.0)
    execution = SimpleExecutionHandler(commission_rate=0.001)
    
    # 注册事件处理器
    engine.register_event_handler("MARKET_DATA", strategy.on_market_data)
    engine.register_event_handler("MARKET_DATA", portfolio.on_market_data)
    engine.register_event_handler("MARKET_DATA", execution.on_market_data)
    
    # 注册信号处理器
    def on_strategy_signal(event):
        if isinstance(event, SignalEvent):
            order = portfolio.on_signal(event)
            if order:
                engine.send_event(order)
    
    engine.register_event_handler("SIGNAL", on_strategy_signal)
    
    # 注册订单处理器
    def on_order(event):
        if isinstance(event, OrderEvent):
            fill = execution.on_order(event)
            if fill:
                engine.send_event(fill)
    
    engine.register_event_handler("ORDER", on_order)
    
    # 注册成交处理器
    engine.register_event_handler("FILL", portfolio.on_fill)
    
    # 启动回测
    print("\n开始回测...")
    start_time = time.time()
    engine.start()
    
    # 等待回测完成
    while engine.get_status() != EngineStatus.COMPLETED:
        time.sleep(0.1)
        
        # 如果超过10秒还未完成，主动停止
        if time.time() - start_time > 10:
            print("回测时间过长，主动停止")
            engine.stop()
            break
    
    # 输出回测结果
    summary = portfolio.get_summary()
    print("\n回测完成！")
    print(f"初始资金: {summary['initial_capital']:.2f}")
    print(f"最终价值: {summary['final_value']:.2f}")
    print(f"总收益率: {summary['total_return']:.2f}%")
    print(f"总交易次数: {summary['total_trades']}")
    
    # 返回结果数据便于进一步分析
    return {
        'portfolio': portfolio,
        'equity_curve': pd.DataFrame(portfolio.equity_curve),
        'trades': pd.DataFrame(portfolio.trades) if portfolio.trades else None
    }

def realtime_simulation():
    """模拟实时交易"""
    print("\n===== 模拟实时交易 =====")
    
    # 创建更小的测试数据集
    df = create_test_data(size=20, symbol="000001.SZ", start_price=100)
    print(f"数据预览:\n{df.head()}")
    
    # 创建数据重放控制器，设置为实时模式
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.REALTIME,
        speed_factor=2.0  # 加速2倍
    )
    
    # 创建引擎管理器
    engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine.initialize()
    
    # 添加重放控制器
    engine.add_replay_controller("realtime_data", controller)
    
    # 创建策略、投资组合和执行处理器
    strategy = SimpleMovingAverageStrategy(short_window=3, long_window=10)
    portfolio = SimplePortfolio(initial_capital=100000.0)
    execution = SimpleExecutionHandler()
    
    # 注册事件处理器
    engine.register_event_handler("MARKET_DATA", lambda e: print(f"市场数据: {e.timestamp}, {e.symbol}, 价格={e.data['price']:.2f}"))
    engine.register_event_handler("MARKET_DATA", strategy.on_market_data)
    engine.register_event_handler("MARKET_DATA", portfolio.on_market_data)
    engine.register_event_handler("MARKET_DATA", execution.on_market_data)
    
    # 注册信号处理器
    def on_strategy_signal(event):
        if isinstance(event, SignalEvent):
            order = portfolio.on_signal(event)
            if order:
                engine.send_event(order)
    
    engine.register_event_handler("SIGNAL", on_strategy_signal)
    
    # 注册订单处理器
    def on_order(event):
        if isinstance(event, OrderEvent):
            fill = execution.on_order(event)
            if fill:
                engine.send_event(fill)
    
    engine.register_event_handler("ORDER", on_order)
    
    # 注册成交处理器
    engine.register_event_handler("FILL", portfolio.on_fill)
    
    # 启动模拟
    print("\n开始模拟实时交易...")
    print("（每个数据点之间按实时时间比例延迟）")
    engine.start()
    
    # 等待模拟完成
    try:
        while engine.get_status() == EngineStatus.RUNNING:
            time.sleep(0.5)
            
            # 演示暂停/恢复功能
            if len(portfolio.equity_curve) == 10:
                print("\n(暂停模拟...)")
                engine.pause()
                time.sleep(2)
                print("(恢复模拟...)")
                engine.resume()
    except KeyboardInterrupt:
        print("\n用户中断，停止模拟")
        engine.stop()
    
    # 输出模拟结果
    summary = portfolio.get_summary()
    print("\n模拟完成！")
    print(f"初始资金: {summary['initial_capital']:.2f}")
    print(f"最终价值: {summary['final_value']:.2f}")
    print(f"总收益率: {summary['total_return']:.2f}%")
    print(f"总交易次数: {summary['total_trades']}")

def multi_source_demo():
    """多数据源协同示例"""
    print("\n===== 多数据源协同示例 =====")
    
    # 创建股票数据
    stock_df = create_test_data(size=50, symbol="000001.SZ", start_price=100)
    
    # 创建指数数据
    index_dates = pd.date_range(start='2023-01-01 09:30:00', periods=50, freq='1min')
    index_df = pd.DataFrame({
        'timestamp': index_dates,
        'index_price': np.cumsum(np.random.normal(0, 0.5, 50)) + 1000,
        'symbol': ['INDEX'] * 50
    })
    
    # 创建另一数据源：成交量数据
    volume_dates = pd.date_range(start='2023-01-01 09:30:30', periods=25, freq='2min')
    volume_df = pd.DataFrame({
        'timestamp': volume_dates,
        'market_volume': np.abs(np.random.normal(1000000, 500000, 25)).astype(int),
        'symbol': ['VOLUME'] * 25
    })
    
    print(f"股票数据:\n{stock_df.head()}")
    print(f"\n指数数据:\n{index_df.head()}")
    print(f"\n成交量数据:\n{volume_df.head()}")
    
    # 使用多数据源控制器
    controller = MultiSourceReplayController(
        data_sources={
            'stock': stock_df,
            'index': index_df,
            'volume': volume_df
        },
        timestamp_extractors={
            'stock': lambda x: x['timestamp'],
            'index': lambda x: x['timestamp'],
            'volume': lambda x: x['timestamp']
        },
        mode=ReplayMode.BACKTEST
    )
    
    # 创建引擎管理器
    engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine.initialize()
    
    # 添加重放控制器
    engine.add_replay_controller(
        "multi_source", 
        controller,
        data_converter=lambda data, timestamp, symbol: 
            MarketDataEvent(timestamp, data.get('symbol', data.get('_source', 'unknown')), data)
    )
    
    # 注册处理器
    def on_data(event):
        source = event.source
        data = event.data
        if source == 'stock':
            print(f"股票数据: {event.timestamp}, 价格={data['price']:.2f}")
        elif source == 'index':
            print(f"指数数据: {event.timestamp}, 指数={data['index_price']:.2f}")
        elif source == 'volume':
            print(f"成交量数据: {event.timestamp}, 成交量={data['market_volume']:,}")
    
    engine.register_event_handler("MARKET_DATA", on_data)
    
    # 启动重放
    print("\n开始多数据源重放...")
    engine.start()
    
    # 等待重放完成
    start_time = time.time()
    while engine.get_status() == EngineStatus.RUNNING:
        time.sleep(0.1)
        # 超时保护
        if time.time() - start_time > 10:
            engine.stop()
            break
    
    print("\n多数据源重放完成！")

if __name__ == "__main__":
    print("==== 数据重放控制器与引擎管理器集成示例 ====")
    
    # 运行移动平均线回测
    simple_ma_backtest()
    
    # 运行实时模拟
    realtime_simulation()
    
    # 运行多数据源示例
    multi_source_demo()
    
    print("\n所有示例运行完成！") 