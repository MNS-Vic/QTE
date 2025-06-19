#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件驱动回测引擎 - 模拟真实市场的事件处理流程
"""
import uuid
import datetime
from queue import Queue
from enum import Enum
from typing import Dict, List, Union, Optional, Any, Callable
import pandas as pd
import numpy as np


# 定义事件类型
class EventType(Enum):
    """事件类型枚举"""
    MARKET = "市场数据"
    SIGNAL = "交易信号"
    ORDER = "订单"
    FILL = "成交"
    ACCOUNT = "账户"
    CUSTOM = "自定义"


# 基础事件类
class Event:
    """事件基类"""
    def __init__(self, event_type: EventType):
        """
        初始化事件
        
        Parameters
        ----------
        event_type : EventType
            事件类型
        """
        self.event_type = event_type
        self.timestamp = datetime.datetime.now()
        self.event_id = str(uuid.uuid4())[:8]


# 市场数据事件
class MarketEvent(Event):
    """市场数据事件，用于推送行情数据"""
    def __init__(self, timestamp: datetime.datetime, symbol: str, data: Dict[str, Any]):
        """
        初始化市场数据事件
        
        Parameters
        ----------
        timestamp : datetime.datetime
            时间戳
        symbol : str
            交易品种代码
        data : Dict[str, Any]
            市场数据，包含开高低收量等信息
        """
        super().__init__(EventType.MARKET)
        self.timestamp = timestamp
        self.symbol = symbol
        self.data = data


# 信号事件
class SignalEvent(Event):
    """信号事件，由策略生成的交易信号"""
    def __init__(self, timestamp: datetime.datetime, symbol: str, direction: int, strength: float = 1.0):
        """
        初始化信号事件
        
        Parameters
        ----------
        timestamp : datetime.datetime
            时间戳
        symbol : str
            交易品种代码
        direction : int
            交易方向，1表示买入，-1表示卖出
        strength : float, optional
            信号强度，0-1之间, by default 1.0
        """
        super().__init__(EventType.SIGNAL)
        self.timestamp = timestamp
        self.symbol = symbol
        self.direction = direction  # 1表示买入，-1表示卖出
        self.strength = strength  # 信号强度，0-1之间


# 订单类型
class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "市价单"
    LIMIT = "限价单"
    STOP = "止损单"
    STOP_LIMIT = "止损限价单"


# 订单事件
class OrderEvent(Event):
    """订单事件，由投资组合生成的订单请求"""
    def __init__(self, timestamp: datetime.datetime, symbol: str, order_type: OrderType, 
                quantity: float, direction: int, limit_price: Optional[float] = None, 
                stop_price: Optional[float] = None):
        """
        初始化订单事件
        
        Parameters
        ----------
        timestamp : datetime.datetime
            时间戳
        symbol : str
            交易品种代码
        order_type : OrderType
            订单类型
        quantity : float
            数量
        direction : int
            交易方向，1表示买入，-1表示卖出
        limit_price : Optional[float], optional
            限价, by default None
        stop_price : Optional[float], optional
            止损价, by default None
        """
        super().__init__(EventType.ORDER)
        self.timestamp = timestamp
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction  # 1表示买入，-1表示卖出
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.order_id = str(uuid.uuid4())


# 成交事件
class FillEvent(Event):
    """成交事件，由交易所返回的成交结果"""
    def __init__(self, timestamp: datetime.datetime, symbol: str, order_id: str, 
                quantity: float, direction: int, fill_price: float, 
                commission: float = 0.0):
        """
        初始化成交事件
        
        Parameters
        ----------
        timestamp : datetime.datetime
            时间戳
        symbol : str
            交易品种代码
        order_id : str
            订单ID
        quantity : float
            成交数量
        direction : int
            交易方向，1表示买入，-1表示卖出
        fill_price : float
            成交价格
        commission : float, optional
            手续费, by default 0.0
        """
        super().__init__(EventType.FILL)
        self.timestamp = timestamp
        self.symbol = symbol
        self.order_id = order_id
        self.quantity = quantity
        self.direction = direction  # 1表示买入，-1表示卖出
        self.fill_price = fill_price
        self.commission = commission


# 账户事件
class AccountEvent(Event):
    """账户事件，账户资金变动信息"""
    def __init__(self, timestamp: datetime.datetime, balance: float, 
                available: float, margin: float = 0.0):
        """
        初始化账户事件
        
        Parameters
        ----------
        timestamp : datetime.datetime
            时间戳
        balance : float
            账户总资产
        available : float
            可用资金
        margin : float, optional
            保证金, by default 0.0
        """
        super().__init__(EventType.ACCOUNT)
        self.timestamp = timestamp
        self.balance = balance
        self.available = available
        self.margin = margin


# 事件引擎
class EventEngine:
    """事件引擎，负责处理和分发各种事件"""
    def __init__(self):
        """初始化事件引擎"""
        self.queue = Queue()
        self.handlers = {event_type: [] for event_type in EventType}
    
    def register_handler(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        注册事件处理器
        
        Parameters
        ----------
        event_type : EventType
            事件类型
        handler : Callable[[Event], None]
            处理函数
        """
        if event_type in self.handlers:
            self.handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        注销事件处理器
        
        Parameters
        ----------
        event_type : EventType
            事件类型
        handler : Callable[[Event], None]
            处理函数
        """
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
    
    def put(self, event: Event) -> None:
        """
        添加事件到队列
        
        Parameters
        ----------
        event : Event
            事件对象
        """
        self.queue.put(event)
    
    def process(self) -> bool:
        """
        处理一个事件
        
        Returns
        -------
        bool
            是否处理了事件
        """
        if self.queue.empty():
            return False
        
        event = self.queue.get()
        
        if event.event_type in self.handlers:
            for handler in self.handlers[event.event_type]:
                handler(event)
        
        return True
    
    def process_all(self) -> int:
        """
        处理所有事件
        
        Returns
        -------
        int
            处理的事件数量
        """
        count = 0
        while self.process():
            count += 1
        return count
    
    def clear(self) -> None:
        """清空事件队列"""
        while not self.queue.empty():
            self.queue.get()


# 事件驱动回测引擎
class EventDrivenBacktester:
    """
    事件驱动回测引擎
    
    基于事件队列和事件驱动架构实现的高真实度回测引擎
    """
    
    def __init__(self, initial_capital: float = 100000.0, 
                commission_rate: float = 0.001, 
                slippage: float = 0.0):
        """
        初始化事件驱动回测引擎
        
        Parameters
        ----------
        initial_capital : float, optional
            初始资金, by default 100000.0
        commission_rate : float, optional
            交易手续费率, by default 0.001
        slippage : float, optional
            滑点比率, by default 0.0
        """
        self.event_engine = EventEngine()
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 回测状态
        self.data = None
        self.data_symbols = []
        self.current_date = None
        self.current_bar_index = 0
        self.is_backtest_running = False
        
        # 策略和持仓
        self.strategies = []
        self.positions = {}  # symbol -> quantity
        self.open_orders = {}  # order_id -> OrderEvent
        
        # 回测结果
        self.equity_history = []
        self.transaction_history = []
        
        # 注册事件处理器
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """注册各类事件的处理器"""
        self.event_engine.register_handler(EventType.MARKET, self._on_market_event)
        self.event_engine.register_handler(EventType.SIGNAL, self._on_signal_event)
        self.event_engine.register_handler(EventType.ORDER, self._on_order_event)
        self.event_engine.register_handler(EventType.FILL, self._on_fill_event)
    
    def _on_market_event(self, event: MarketEvent) -> None:
        """
        处理市场数据事件
        
        Parameters
        ----------
        event : MarketEvent
            市场数据事件
        """
        # 将市场数据传递给所有策略
        for strategy in self.strategies:
            strategy.on_market_data(event)
        
        # 更新当前时间
        self.current_date = event.timestamp
        
        # 记录资产状态
        self.equity_history.append({
            'timestamp': event.timestamp,
            'equity': self.calculate_equity(),
            'cash': self.current_capital
        })
    
    def _on_signal_event(self, event: SignalEvent) -> None:
        """
        处理信号事件
        
        Parameters
        ----------
        event : SignalEvent
            信号事件
        """
        # 通过投资组合逻辑转换成订单
        symbol = event.symbol
        direction = event.direction
        strength = event.strength
        
        # 获取最新价格
        market_data = self._get_latest_market_data(symbol)
        if market_data is None:
            return
        
        close_price = market_data['close']
        
        # 计算订单数量
        quantity = self._calculate_position_size(symbol, direction, strength, close_price)
        
        if quantity == 0:
            return
        
        # 创建订单
        order_type = OrderType.MARKET  # 默认使用市价单
        
        order_event = OrderEvent(
            timestamp=event.timestamp,
            symbol=symbol,
            order_type=order_type,
            quantity=abs(quantity),
            direction=1 if quantity > 0 else -1
        )
        
        # 发送订单事件
        self.event_engine.put(order_event)
    
    def _on_order_event(self, event: OrderEvent) -> None:
        """
        处理订单事件
        
        Parameters
        ----------
        event : OrderEvent
            订单事件
        """
        # 记录订单
        self.open_orders[event.order_id] = event
        
        # 执行订单（模拟交易所）
        if event.order_type == OrderType.MARKET:
            # 市价单直接成交
            self._execute_market_order(event)
        else:
            # 其他类型订单暂不处理
            pass
    
    def _on_fill_event(self, event: FillEvent) -> None:
        """
        处理成交事件
        
        Parameters
        ----------
        event : FillEvent
            成交事件
        """
        # 更新持仓
        symbol = event.symbol
        direction = event.direction
        quantity = event.quantity
        
        if symbol not in self.positions:
            self.positions[symbol] = 0
        
        # 更新持仓数量
        if direction == 1:  # 买入
            self.positions[symbol] += quantity
        else:  # 卖出
            self.positions[symbol] -= quantity
        
        # 更新资金
        cost = event.quantity * event.fill_price
        if direction == 1:  # 买入
            self.current_capital -= (cost + event.commission)
        else:  # 卖出
            self.current_capital += (cost - event.commission)
        
        # 记录交易
        transaction = {
            'timestamp': event.timestamp,
            'symbol': event.symbol,
            'direction': 'BUY' if direction == 1 else 'SELL',
            'quantity': event.quantity,
            'price': event.fill_price,
            'commission': event.commission,
            'order_id': event.order_id
        }
        
        self.transaction_history.append(transaction)
        
        # 从未完成订单中移除
        if event.order_id in self.open_orders:
            del self.open_orders[event.order_id]
    
    def _execute_market_order(self, order: OrderEvent) -> None:
        """
        执行市价单
        
        Parameters
        ----------
        order : OrderEvent
            订单事件
        """
        # 获取最新价格
        market_data = self._get_latest_market_data(order.symbol)
        if market_data is None:
            return
        
        close_price = market_data['close']
        
        # 考虑滑点
        execution_price = close_price
        if order.direction == 1:  # 买入
            execution_price *= (1 + self.slippage)
        else:  # 卖出
            execution_price *= (1 - self.slippage)
        
        # 计算佣金
        commission = order.quantity * execution_price * self.commission_rate
        
        # 创建成交事件
        fill_event = FillEvent(
            timestamp=order.timestamp,
            symbol=order.symbol,
            order_id=order.order_id,
            quantity=order.quantity,
            direction=order.direction,
            fill_price=execution_price,
            commission=commission
        )
        
        # 发送成交事件
        self.event_engine.put(fill_event)
    
    def _get_latest_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新的市场数据
        
        Parameters
        ----------
        symbol : str
            交易品种代码
        
        Returns
        -------
        Optional[Dict[str, Any]]
            市场数据字典，若不存在则返回None
        """
        if self.data is None or symbol not in self.data:
            return None
        
        if self.current_bar_index < len(self.data[symbol]):
            return self.data[symbol][self.current_bar_index]
        
        return None
    
    def _calculate_position_size(self, symbol: str, direction: int, 
                               strength: float, price: float) -> int:
        """
        计算仓位大小
        
        Parameters
        ----------
        symbol : str
            交易品种代码
        direction : int
            交易方向，1表示买入，-1表示卖出
        strength : float
            信号强度，0-1之间
        price : float
            当前价格
        
        Returns
        -------
        int
            仓位数量，正数表示买入，负数表示卖出
        """
        # 根据当前持仓计算应调整的仓位
        current_position = self.positions.get(symbol, 0)
        
        if direction == 1:  # 买入信号
            # 计算可用资金
            available_capital = self.current_capital * strength
            # 计算可买入的最大数量
            max_quantity = int(available_capital / price)
            # 如果已有空头仓位，先平仓
            if current_position < 0:
                return abs(current_position)
            # 如果资金不足，则不交易
            if available_capital <= 0 or max_quantity == 0:
                return 0
            return max_quantity
            
        elif direction == -1:  # 卖出信号
            # 如果已有多头仓位，先平仓
            if current_position > 0:
                return -current_position
            # 如果允许做空，计算做空数量
            # available_capital = self.current_capital * strength
            # max_quantity = int(available_capital / price)
            # return -max_quantity
            # 默认不做空
            return 0
        
        return 0
    
    def calculate_equity(self) -> float:
        """
        计算当前总资产
        
        Returns
        -------
        float
            总资产值
        """
        equity = self.current_capital
        
        for symbol, quantity in self.positions.items():
            market_data = self._get_latest_market_data(symbol)
            if market_data is not None:
                equity += quantity * market_data['close']
        
        return equity
    
    def add_strategy(self, strategy: Any) -> None:
        """
        添加策略
        
        Parameters
        ----------
        strategy : Any
            策略对象，需要实现on_market_data方法
        """
        self.strategies.append(strategy)
    
    def set_data(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        设置回测数据
        
        Parameters
        ----------
        data : Dict[str, List[Dict[str, Any]]]
            回测数据，格式为 {symbol: [bar_data, ...]}
            其中bar_data包含timestamp, open, high, low, close等字段
        """
        self.data = data
        self.data_symbols = list(data.keys())
    
    def run(self) -> Dict[str, Any]:
        """
        运行回测
        
        Returns
        -------
        Dict[str, Any]
            回测结果
        """
        self.is_backtest_running = True
        
        # 重置状态
        self.current_bar_index = 0
        self.current_capital = self.initial_capital
        self.positions = {}
        self.open_orders = {}
        self.equity_history = []
        self.transaction_history = []
        
        # 检查数据
        if not self.data or not self.data_symbols:
            raise ValueError("回测数据未设置")
        
        # 获取数据集长度
        data_length = min(len(self.data[symbol]) for symbol in self.data_symbols)
        
        # 主回测循环
        for i in range(data_length):
            self.current_bar_index = i
            
            # 发送市场数据事件
            for symbol in self.data_symbols:
                bar_data = self.data[symbol][i]
                market_event = MarketEvent(
                    timestamp=bar_data['timestamp'],
                    symbol=symbol,
                    data=bar_data
                )
                self.event_engine.put(market_event)
            
            # 处理所有事件直到队列为空
            self.event_engine.process_all()
        
        self.is_backtest_running = False
        
        # 计算回测结果
        results = self._calculate_results()
        
        return results
    
    def _calculate_results(self) -> Dict[str, Any]:
        """
        计算回测结果

        Returns
        -------
        Dict[str, Any]
            回测结果统计
        """
        # 处理空权益历史的情况
        if not self.equity_history:
            # 如果没有权益历史，创建一个基本的记录
            import datetime as dt
            self.equity_history = [
                {'timestamp': dt.datetime.now(), 'equity': self.current_capital}
            ]

        # 转换成DataFrame便于分析
        equity_df = pd.DataFrame(self.equity_history)

        # 检查DataFrame是否为空或缺少必要列
        if equity_df.empty or 'timestamp' not in equity_df.columns or 'equity' not in equity_df.columns:
            # 创建默认的权益曲线
            import datetime as dt
            equity_df = pd.DataFrame({
                'timestamp': [dt.datetime.now()],
                'equity': [self.current_capital]
            })

        # 使用更兼容的方式设置索引，避免pandas版本兼容性问题
        try:
            equity_df = equity_df.set_index('timestamp')
        except Exception as e:
            # 如果设置索引失败，使用默认的数字索引
            print(f"Warning: Failed to set timestamp index: {e}")
            # 确保至少有timestamp列用于后续计算
            if 'timestamp' in equity_df.columns:
                equity_df['timestamp_backup'] = equity_df['timestamp']
        
        # 计算收益率
        equity_df['return'] = equity_df['equity'].pct_change()
        
        # 计算累积收益
        equity_df['cum_return'] = (1 + equity_df['return']).cumprod()
        
        # 计算回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['peak'] - equity_df['equity']) / equity_df['peak']
        
        # 计算各种统计指标
        # 总收益率
        total_return = equity_df['equity'].iloc[-1] / self.initial_capital - 1
        
        # 年化收益率
        try:
            if hasattr(equity_df.index, 'dtype') and 'datetime' in str(equity_df.index.dtype):
                days = (equity_df.index[-1] - equity_df.index[0]).days
            else:
                # 如果索引不是datetime，使用备份的timestamp列
                if 'timestamp_backup' in equity_df.columns:
                    days = (equity_df['timestamp_backup'].iloc[-1] - equity_df['timestamp_backup'].iloc[0]).days
                else:
                    days = 1  # 默认值
        except Exception:
            days = 1  # 默认值
        annual_return = (1 + total_return) ** (365 / max(1, days)) - 1
        
        # 最大回撤 (安全处理NaN值)
        drawdown_values = equity_df['drawdown'].dropna()
        max_drawdown = float(drawdown_values.max()) if len(drawdown_values) > 0 else 0.0
        
        # 夏普比率
        sharpe_ratio = equity_df['return'].mean() / equity_df['return'].std() * np.sqrt(252) if equity_df['return'].std() > 0 else 0
        
        # 交易统计
        trade_count = len(self.transaction_history)
        
        # 胜率
        if trade_count > 0:
            from collections import defaultdict
            
            # 按订单ID分组交易
            order_trades = defaultdict(list)
            for trade in self.transaction_history:
                order_trades[trade['order_id']].append(trade)
            
            # 计算每笔交易的盈亏
            completed_trades = []
            for order_id, trades in order_trades.items():
                if len(trades) >= 2:
                    # 简化处理，假设一买一卖
                    buy_trades = [t for t in trades if t['direction'] == 'BUY']
                    sell_trades = [t for t in trades if t['direction'] == 'SELL']
                    
                    if buy_trades and sell_trades:
                        buy_cost = sum(t['price'] * t['quantity'] + t['commission'] for t in buy_trades)
                        sell_value = sum(t['price'] * t['quantity'] - t['commission'] for t in sell_trades)
                        profit = sell_value - buy_cost
                        completed_trades.append(profit)
            
            # 计算胜率
            win_count = sum(1 for p in completed_trades if p > 0)
            win_rate = win_count / len(completed_trades) if completed_trades else 0
        else:
            win_rate = 0
        
        metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            # 'trade_count': trade_count, # 这个trade_count是原始交易记录数，不是完成的交易对数
            # 'win_rate': win_rate, # 这个胜率计算需要改进
        }

        # 更准确的交易统计
        completed_trade_stats = self._calculate_trade_statistics(equity_df)
        metrics.update(completed_trade_stats)

        results = {
            'initial_capital': self.initial_capital,
            'final_equity': equity_df['equity'].iloc[-1],
            'metrics': metrics, # 将所有指标放入'metrics'键下
            'equity_curve': equity_df,
            'transactions': self.transaction_history
        }
        
        return results

    def _calculate_trade_statistics(self, equity_df: pd.DataFrame) -> Dict[str, Any]:
        """更详细地计算交易相关统计数据"""
        if not self.transaction_history:
            return {
                'trade_count': 0,
                'win_rate': 0.0,
                'avg_profit_loss_ratio': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
            }

        # 简化版交易分析：基于现金流变化近似交易
        # 注意：这是一个非常简化的版本，真实交易分析需要匹配买入和卖出操作
        # 这里的 "交易" 是指任何导致现金变动的操作（买入或卖出）
        # 胜率等指标在此简化模型下可能不完全准确，仅为示例
        
        profits = []
        current_trades = []
        last_equity = self.initial_capital
        
        # 尝试从equity_curve中推断交易点 (这是一个粗略的估计)
        # 实际中应该基于transaction_history匹配开平仓操作
        equity_changes = equity_df['equity'].diff().dropna()
        transaction_df = pd.DataFrame(self.transaction_history)
        
        # 简单的统计交易次数，不区分开平仓
        trade_count = len(transaction_df) 

        # 胜率等指标的准确计算需要更复杂的逻辑来配对买卖交易
        # 这里暂时返回0，表示这部分逻辑待完善
        # TODO: 实现更准确的交易配对和盈亏计算逻辑
        
        winning_trades_count = 0
        losing_trades_count = 0
        total_profit = 0
        total_loss = 0
        
        # 遍历交易记录进行简单分析 (这里假设每次买入后都会卖出)
        # 这只是一个非常粗略的模拟，实际的交易配对要复杂得多
        entry_price = 0
        position_active = False
        entry_timestamp = None

        trade_profits = []

        for i in range(len(self.transaction_history)):
            tx = self.transaction_history[i]
            if tx['direction'] == 'BUY' and not position_active:
                entry_price = tx['price']
                entry_timestamp = tx['timestamp']
                position_active = True
            elif tx['direction'] == 'SELL' and position_active:
                profit = (tx['price'] - entry_price) * tx['quantity'] - tx['commission'] # 简化的佣金处理，可能已在fill中扣除
                # 查找上一次买入的佣金
                prev_buy_tx = next((t for t in reversed(self.transaction_history[:i]) if t['direction'] == 'BUY' and t['symbol'] == tx['symbol']), None)
                if prev_buy_tx:
                    profit -= prev_buy_tx['commission']
                
                trade_profits.append(profit)
                position_active = False
                entry_price = 0
                entry_timestamp = None
        
        if trade_profits:
            winning_trades_count = sum(1 for p in trade_profits if p > 0)
            losing_trades_count = sum(1 for p in trade_profits if p < 0)
            total_profit = sum(p for p in trade_profits if p > 0)
            total_loss = sum(p for p in trade_profits if p < 0)

        win_rate = winning_trades_count / len(trade_profits) if trade_profits else 0.0
        avg_win = total_profit / winning_trades_count if winning_trades_count > 0 else 0.0
        avg_loss = abs(total_loss / losing_trades_count) if losing_trades_count > 0 else 0.0
        avg_profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 999999.0  # 使用大数值代替inf

        return {
            'trade_count': len(trade_profits), # 完成的交易对数量
            'win_rate': win_rate,
            'winning_trades': winning_trades_count,
            'losing_trades': losing_trades_count,
            'avg_profit_loss_ratio': avg_profit_loss_ratio
        }