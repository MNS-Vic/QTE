#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟基于vnpy的事件驱动回测引擎实现双均线交叉策略

vnpy特点：
1. 事件驱动架构：核心基于事件驱动引擎，适合处理实时市场数据流
2. 模块化设计：策略、数据、执行等组件高度模块化，便于扩展和修改
3. 跨市场支持：内置多种交易接口，可对接国内外各类市场
4. 策略开发便捷：提供完整的策略模板，简化策略开发流程
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from enum import Enum
import os
import uuid
import time
import copy

# 模拟vnpy的事件驱动引擎
class Event:
    """事件对象"""
    def __init__(self, type_=None):
        self.type_ = type_
        self.dict_ = {}

class EventEngine:
    """事件驱动引擎"""
    def __init__(self):
        self.handlers = {}
        self.active = False
        self.queue = []
        
    def register(self, type_, handler):
        """注册事件处理函数"""
        if type_ not in self.handlers:
            self.handlers[type_] = []
        self.handlers[type_].append(handler)
        
    def unregister(self, type_, handler):
        """注销事件处理函数"""
        if type_ in self.handlers:
            if handler in self.handlers[type_]:
                self.handlers[type_].remove(handler)
                
    def put(self, event):
        """放入事件"""
        self.queue.append(event)
    
    def process(self):
        """处理事件"""
        if self.queue:
            event = self.queue.pop(0)
            if event.type_ in self.handlers:
                for handler in self.handlers[event.type_]:
                    handler(event)
    
    def start(self):
        """启动引擎"""
        self.active = True
        
    def stop(self):
        """停止引擎"""
        self.active = False
        self.queue = []
        
    def process_until_empty(self):
        """处理队列中所有事件"""
        while self.queue:
            self.process()

# 模拟vnpy中的常量
class Direction(Enum):
    """方向常量"""
    LONG = "多"
    SHORT = "空"

class Offset(Enum):
    """开平常量"""
    OPEN = "开"
    CLOSE = "平"

class Status(Enum):
    """状态常量"""
    SUBMITTING = "提交中"
    NOTTRADED = "未成交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    REJECTED = "拒单"

class Exchange(Enum):
    """交易所常量"""
    SSE = "SSE"       # 上交所
    SZSE = "SZSE"     # 深交所
    CFFEX = "CFFEX"   # 中金所
    SHFE = "SHFE"     # 上期所
    DCE = "DCE"       # 大商所
    CZCE = "CZCE"     # 郑商所

class Interval(Enum):
    """K线周期常量"""
    MINUTE = "1m"
    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"

class EventType(Enum):
    """事件类型常量"""
    TICK = "tick"
    BAR = "bar"
    ORDER = "order"
    TRADE = "trade"
    POSITION = "position"
    ACCOUNT = "account"
    CONTRACT = "contract"
    LOG = "log"

# 模拟vnpy中的数据结构
class BarData:
    """K线数据对象"""
    def __init__(
        self,
        symbol: str = "",
        exchange: Exchange = None,
        datetime: datetime = None,
        interval: Interval = None,
        open_price: float = 0.0,
        high_price: float = 0.0,
        low_price: float = 0.0,
        close_price: float = 0.0,
        volume: float = 0.0,
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.datetime = datetime
        self.interval = interval
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.gateway_name = "BACKTEST"

class OrderData:
    """委托订单数据"""
    def __init__(
        self,
        symbol: str = "",
        exchange: Exchange = None,
        orderid: str = "",
        type: str = "限价",
        direction: Direction = None,
        offset: Offset = None,
        price: float = 0.0,
        volume: float = 0.0,
        traded: float = 0.0,
        status: Status = Status.SUBMITTING,
        datetime: datetime = None,
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.orderid = orderid
        self.type = type
        self.direction = direction
        self.offset = offset
        self.price = price
        self.volume = volume
        self.traded = traded
        self.status = status
        self.datetime = datetime
        self.gateway_name = "BACKTEST"

class TradeData:
    """成交数据"""
    def __init__(
        self,
        symbol: str = "",
        exchange: Exchange = None,
        orderid: str = "",
        tradeid: str = "",
        direction: Direction = None,
        offset: Offset = None,
        price: float = 0.0,
        volume: float = 0.0,
        datetime: datetime = None,
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.orderid = orderid
        self.tradeid = tradeid
        self.direction = direction
        self.offset = offset
        self.price = price
        self.volume = volume
        self.datetime = datetime
        self.gateway_name = "BACKTEST"

class PositionData:
    """持仓数据"""
    def __init__(
        self,
        symbol: str = "",
        exchange: Exchange = None,
        direction: Direction = None,
        volume: float = 0.0,
        frozen: float = 0.0,
        price: float = 0.0,
        pnl: float = 0.0,
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.direction = direction
        self.volume = volume
        self.frozen = frozen
        self.price = price
        self.pnl = pnl
        self.gateway_name = "BACKTEST"

class AccountData:
    """账户数据"""
    def __init__(
        self,
        accountid: str = "",
        balance: float = 0.0,
        frozen: float = 0.0,
    ):
        self.accountid = accountid
        self.balance = balance
        self.frozen = frozen
        self.gateway_name = "BACKTEST"

# 模拟vnpy回测引擎组件
class BacktestingEngine:
    """回测引擎"""
    def __init__(self):
        self.gateway_name = "BACKTEST"
        self.start_dt = None
        self.end_dt = None
        self.capital = 1_000_000
        self.rates = {"SSE": 0.0001}
        self.slippages = {"SSE": 0.0}
        self.size = {"000001": 1}
        self.pricetick = {"000001": 0.01}
        
        self.daily_results = []
        self.daily_df = None
        
        self.event_engine = EventEngine()
        self.strategy = None
        
        self.current_dt = None
        self.bars = {}
        self.trades = []
        self.orders = {}
        
        self.accounts = {}
        self.positions = {}
        
        self.bar_data = []
        
    def set_parameters(
        self,
        start_dt: datetime,
        end_dt: datetime,
        capital: float = 1_000_000,
    ):
        """设置回测参数"""
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.capital = capital
        
    def add_strategy(self, strategy_class, setting={}):
        """添加策略类实例"""
        self.strategy = strategy_class(self, setting)
        
    def load_data(self, symbol, exchange, interval, file_path=None):
        """加载回测数据，如果文件不存在则生成模拟数据"""
        if file_path and os.path.exists(file_path):
            # 从文件加载数据
            df = pd.read_csv(file_path, parse_dates=["datetime"])
            for _, row in df.iterrows():
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=row["datetime"],
                    interval=interval,
                    open_price=row["open"],
                    high_price=row["high"],
                    low_price=row["low"],
                    close_price=row["close"],
                    volume=row["volume"]
                )
                self.bar_data.append(bar)
            
            print(f"从文件加载了 {len(self.bar_data)} 条历史数据")
            
        else:
            # 生成模拟数据
            print(f"为 {symbol} 生成模拟回测数据")
            np.random.seed(42)
            
            start = self.start_dt
            end = self.end_dt
            
            # 模拟生成价格
            base_price = 3000  # 基础价格
            price = base_price
            current_date = start
            
            while current_date <= end:
                # 跳过周末
                if current_date.weekday() < 5:  # 0-4是周一至周五
                    # 生成当日价格
                    daily_volatility = np.random.normal(0, 1) * 30  # 日波动
                    open_price = price
                    close_price = max(0, open_price + daily_volatility)
                    high_price = max(open_price, close_price) + abs(np.random.normal(0, 1) * 10)
                    low_price = min(open_price, close_price) - abs(np.random.normal(0, 1) * 10)
                    volume = int(np.random.normal(1000000, 500000))
                    
                    bar = BarData(
                        symbol=symbol,
                        exchange=exchange,
                        datetime=current_date,
                        interval=interval,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        volume=volume
                    )
                    self.bar_data.append(bar)
                    
                    price = close_price  # 更新收盘价作为下一个交易日的基础
                
                current_date += timedelta(days=1)
            
            print(f"生成了 {len(self.bar_data)} 条模拟数据")
    
    def init_backtesting(self):
        """初始化回测相关数据结构"""
        self.current_dt = self.start_dt
        
        # 初始化账户
        account = AccountData(
            accountid="BACKTEST",
            balance=self.capital,
            frozen=0.0
        )
        self.accounts["BACKTEST"] = account
        
        # 初始化持仓
        if self.bar_data:
            symbols = set([bar.symbol for bar in self.bar_data])
            for symbol in symbols:
                for direction in [Direction.LONG, Direction.SHORT]:
                    position = PositionData(
                        symbol=symbol,
                        exchange=Exchange.SSE,
                        direction=direction,
                        volume=0,
                        frozen=0,
                        price=0,
                        pnl=0
                    )
                    key = f"{symbol}_{direction.value}"
                    self.positions[key] = position
    
    def run_backtesting(self):
        """运行回测"""
        self.init_backtesting()
        
        # 初始化策略
        self.strategy.on_init()
        
        # 逐日运行回测
        day_bars = {}
        day_dates = sorted(list(set([bar.datetime.date() for bar in self.bar_data])))
        
        for i, day in enumerate(day_dates):
            self.current_dt = datetime.combine(day, datetime.min.time())
            
            # 获取当日所有K线
            day_bars_data = [bar for bar in self.bar_data if bar.datetime.date() == day]
            for bar in day_bars_data:
                self.bars[bar.symbol] = bar
                
                # 创建事件
                event = Event(EventType.BAR.value)
                event.dict_["data"] = bar
                
                # 推送事件
                self.event_engine.put(event)
                
                # 处理事件引擎队列中的所有事件
                self.event_engine.process_until_empty()
            
            # 每日收盘更新投资组合
            self.update_daily_results()
        
        # 生成回测结果
        self.calculate_result()
        
    def send_order(self, symbol, exchange, direction, offset, price, volume):
        """发送委托"""
        orderid = str(uuid.uuid4())
        
        order = OrderData(
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            status=Status.SUBMITTING,
            datetime=self.current_dt
        )
        
        self.orders[orderid] = order
        
        # 创建委托事件
        event = Event(EventType.ORDER.value)
        event.dict_["data"] = order
        self.event_engine.put(event)
        
        # 立即执行成交（回测不考虑延迟）
        self.trade_order(order)
        
        return orderid
    
    def trade_order(self, order):
        """委托成交"""
        # 生成成交ID
        tradeid = str(uuid.uuid4())
        
        # 计算成交价格（考虑滑点）
        slippage = self.slippages.get(order.exchange.value, 0)
        if order.direction == Direction.LONG:
            trade_price = order.price + slippage
        else:
            trade_price = order.price - slippage
        
        # 创建成交对象
        trade = TradeData(
            symbol=order.symbol,
            exchange=order.exchange,
            orderid=order.orderid,
            tradeid=tradeid,
            direction=order.direction,
            offset=order.offset,
            price=trade_price,
            volume=order.volume,
            datetime=self.current_dt
        )
        
        # 更新订单状态
        order.traded = order.volume
        order.status = Status.ALLTRADED
        
        # 创建成交事件
        event = Event(EventType.TRADE.value)
        event.dict_["data"] = trade
        self.event_engine.put(event)
        
        # 更新持仓
        self.update_position(trade)
        
        # 更新账户余额
        self.update_account(trade)
        
        # 记录成交
        self.trades.append(trade)
    
    def update_position(self, trade):
        """更新持仓"""
        # 更新方向持仓
        key = f"{trade.symbol}_{trade.direction.value}"
        
        if key not in self.positions:
            position = PositionData(
                symbol=trade.symbol,
                exchange=trade.exchange,
                direction=trade.direction,
                volume=0,
                frozen=0,
                price=0,
                pnl=0
            )
            self.positions[key] = position
        else:
            position = self.positions[key]
        
        # 计算新的持仓成本和数量
        cost = position.price * position.volume
        
        if trade.offset == Offset.OPEN:
            cost += trade.price * trade.volume
            position.volume += trade.volume
        else:
            position.volume -= trade.volume
        
        if position.volume:
            position.price = cost / position.volume
        else:
            position.price = 0
    
    def update_account(self, trade):
        """更新账户"""
        # 计算手续费
        rate = self.rates.get(trade.exchange.value, 0)
        commission = trade.price * trade.volume * rate
        
        # 计算损益
        if trade.direction == Direction.LONG:
            if trade.offset == Offset.OPEN:
                self.accounts["BACKTEST"].balance -= trade.price * trade.volume
            else:
                pos_key = f"{trade.symbol}_{Direction.LONG.value}"
                pos_price = self.positions[pos_key].price
                profit = (trade.price - pos_price) * trade.volume
                self.accounts["BACKTEST"].balance += trade.price * trade.volume + profit
        else:
            if trade.offset == Offset.OPEN:
                self.accounts["BACKTEST"].balance -= trade.price * trade.volume
            else:
                pos_key = f"{trade.symbol}_{Direction.SHORT.value}"
                pos_price = self.positions[pos_key].price
                profit = (pos_price - trade.price) * trade.volume
                self.accounts["BACKTEST"].balance += trade.price * trade.volume + profit
        
        # 扣减手续费
        self.accounts["BACKTEST"].balance -= commission
    
    def update_daily_results(self):
        """更新每日回测结果"""
        # 计算当日结算价
        settle_price = {}
        for symbol, bar in self.bars.items():
            settle_price[symbol] = bar.close_price
        
        # 计算持仓盈亏
        for key, position in self.positions.items():
            symbol, direction = key.split("_")
            if position.volume and symbol in settle_price:
                if direction == Direction.LONG.value:
                    position.pnl = (settle_price[symbol] - position.price) * position.volume
                else:
                    position.pnl = (position.price - settle_price[symbol]) * position.volume
        
        # 计算账户总资产
        balance = self.accounts["BACKTEST"].balance
        for key, position in self.positions.items():
            symbol, direction = key.split("_")
            if symbol in settle_price:
                balance += position.volume * settle_price[symbol]
        
        # 记录每日结果
        daily_result = {
            "date": self.current_dt.date(),
            "balance": balance,
        }
        self.daily_results.append(daily_result)
    
    def calculate_result(self):
        """计算回测结果"""
        # 创建DataFrame保存每日结果
        self.daily_df = pd.DataFrame(self.daily_results)
        
        # 计算日收益率
        self.daily_df["return"] = self.daily_df["balance"].pct_change().fillna(0)
        
        # 计算累计收益率
        self.daily_df["return_cum"] = (1 + self.daily_df["return"]).cumprod() - 1
        
        # 计算年化收益率
        annual_days = 252  # 交易日
        total_days = len(self.daily_df)
        if total_days:
            annual_return = (1 + self.daily_df["return_cum"].iloc[-1]) ** (annual_days / total_days) - 1
        else:
            annual_return = 0
        
        # 计算最大回撤
        drawdown = (self.daily_df["return_cum"] + 1) / (self.daily_df["return_cum"] + 1).cummax() - 1
        max_drawdown = drawdown.min()
        
        # 计算夏普比率（假设无风险收益率为0）
        if self.daily_df["return"].std() != 0:
            sharpe_ratio = (self.daily_df["return"].mean()) / self.daily_df["return"].std() * (annual_days ** 0.5)
        else:
            sharpe_ratio = 0
        
        self.result_dict = {
            "start_date": self.start_dt.date(),
            "end_date": self.end_dt.date(),
            "total_days": total_days,
            "profit_days": (self.daily_df["return"] > 0).sum(),
            "loss_days": (self.daily_df["return"] < 0).sum(),
            "start_balance": self.capital,
            "end_balance": self.daily_df["balance"].iloc[-1] if not self.daily_df.empty else self.capital,
            "total_return": self.daily_df["return_cum"].iloc[-1] if not self.daily_df.empty else 0,
            "annual_return": annual_return,
            "max_drawdown": abs(max_drawdown),
            "sharpe_ratio": sharpe_ratio,
            "total_trades": len(self.trades),
        }
        
        return self.result_dict
    
    def show_results(self):
        """显示回测结果"""
        if not hasattr(self, "result_dict"):
            print("请先运行回测")
            return
        
        print("\n====== vnpy回测结果汇总 ======")
        print(f"开始日期: {self.result_dict['start_date']}")
        print(f"结束日期: {self.result_dict['end_date']}")
        print(f"总交易日: {self.result_dict['total_days']}")
        print(f"盈利天数: {self.result_dict['profit_days']}")
        print(f"亏损天数: {self.result_dict['loss_days']}")
        print(f"初始资金: {self.result_dict['start_balance']:.2f}")
        print(f"结束资金: {self.result_dict['end_balance']:.2f}")
        print(f"总收益率: {self.result_dict['total_return']:.4f}")
        print(f"年化收益率: {self.result_dict['annual_return']:.4f}")
        print(f"最大回撤: {self.result_dict['max_drawdown']:.4f}")
        print(f"夏普比率: {self.result_dict['sharpe_ratio']:.4f}")
        print(f"总成交笔数: {self.result_dict['total_trades']}")
    
    def plot_results(self):
        """绘制回测结果"""
        if self.daily_df is None or self.daily_df.empty:
            print("没有足够的数据来绘制图表")
            return
        
        # 创建图表
        fig = plt.figure(figsize=(10, 12))
        
        # 资金曲线
        ax1 = fig.add_subplot(3, 1, 1)
        ax1.set_title("资金曲线")
        ax1.plot(self.daily_df["date"], self.daily_df["balance"])
        ax1.grid(True)
        
        # 收益率曲线
        ax2 = fig.add_subplot(3, 1, 2)
        ax2.set_title("收益率曲线")
        ax2.plot(self.daily_df["date"], self.daily_df["return_cum"] * 100)
        ax2.grid(True)
        
        # 每日收益率
        ax3 = fig.add_subplot(3, 1, 3)
        ax3.set_title("每日收益率")
        ax3.bar(self.daily_df["date"], self.daily_df["return"] * 100)
        ax3.grid(True)
        
        plt.tight_layout()
        plt.show()

class CtaTemplate:
    """CTA策略模板"""
    def __init__(self, engine, setting={}):
        self.engine = engine
        self.trading = True
        
        # 读取交易参数
        for name, value in setting.items():
            setattr(self, name, value)
            
        # 注册事件处理函数
        self.engine.event_engine.register(EventType.BAR.value, self.process_bar_event)
        self.engine.event_engine.register(EventType.ORDER.value, self.process_order_event)
        self.engine.event_engine.register(EventType.TRADE.value, self.process_trade_event)
        
        # 指标缓存
        self.indicators = {}
        self.bar_window = {}
    
    def process_bar_event(self, event):
        """处理K线事件"""
        bar = event.dict_["data"]
        
        # 缓存K线数据用于计算指标
        if bar.symbol not in self.bar_window:
            self.bar_window[bar.symbol] = []
        
        self.bar_window[bar.symbol].append(bar)
        
        # 调用K线更新函数
        self.on_bar(bar)
    
    def process_order_event(self, event):
        """处理委托事件"""
        order = event.dict_["data"]
        self.on_order(order)
    
    def process_trade_event(self, event):
        """处理成交事件"""
        trade = event.dict_["data"]
        self.on_trade(trade)
    
    def on_init(self):
        """策略初始化"""
        pass
    
    def on_bar(self, bar):
        """K线更新"""
        pass
    
    def on_order(self, order):
        """委托更新"""
        pass
    
    def on_trade(self, trade):
        """成交更新"""
        pass
    
    def buy(self, price, volume, symbol=None, exchange=None, stop=False):
        """买入开仓"""
        if not symbol:
            if hasattr(self, "symbol"):
                symbol = self.symbol
            else:
                return ""
        
        if not exchange:
            if hasattr(self, "exchange"):
                exchange = self.exchange
            else:
                exchange = Exchange.SSE
                
        return self.engine.send_order(symbol, exchange, Direction.LONG, Offset.OPEN, price, volume)
    
    def sell(self, price, volume, symbol=None, exchange=None, stop=False):
        """卖出平仓"""
        if not symbol:
            if hasattr(self, "symbol"):
                symbol = self.symbol
            else:
                return ""
        
        if not exchange:
            if hasattr(self, "exchange"):
                exchange = self.exchange
            else:
                exchange = Exchange.SSE
                
        return self.engine.send_order(symbol, exchange, Direction.SHORT, Offset.CLOSE, price, volume)
    
    def calculate_ma(self, symbol, n):
        """计算简单移动平均线"""
        if symbol not in self.bar_window:
            return None
        
        bars = self.bar_window[symbol]
        if len(bars) < n:
            return None
        
        ma_value = sum(bar.close_price for bar in bars[-n:]) / n
        return ma_value

# 实现双均线交叉策略
class MACrossStrategy(CtaTemplate):
    """双均线交叉策略"""
    def __init__(self, engine, setting={}):
        super().__init__(engine, setting)
        
        # 默认参数
        self.symbol = "000001"
        self.exchange = Exchange.SSE
        self.fast_window = 10
        self.slow_window = 30
        
        # 覆盖默认参数
        for name, value in setting.items():
            setattr(self, name, value)
        
        # 辅助变量
        self.fast_ma0 = 0.0
        self.fast_ma1 = 0.0
        self.slow_ma0 = 0.0
        self.slow_ma1 = 0.0
        
        self.pos = 0  # 当前持仓
        self.traded = False  # 当天是否已经交易
    
    def on_init(self):
        """策略初始化"""
        print("策略初始化")
        print(f"策略参数: 快线={self.fast_window}, 慢线={self.slow_window}")
    
    def on_bar(self, bar):
        """K线更新"""
        if bar.symbol != self.symbol:
            return
        
        # 计算快速和慢速移动平均线
        self.fast_ma0 = self.fast_ma1
        self.slow_ma0 = self.slow_ma1
        
        self.fast_ma1 = self.calculate_ma(self.symbol, self.fast_window)
        self.slow_ma1 = self.calculate_ma(self.symbol, self.slow_window)
        
        # 确保两条均线都有值
        if not self.fast_ma1 or not self.slow_ma1:
            return
        
        # 交叉信号检测
        cross_over = (self.fast_ma0 <= self.slow_ma0 and self.fast_ma1 > self.slow_ma1)
        cross_below = (self.fast_ma0 >= self.slow_ma0 and self.fast_ma1 < self.slow_ma1)
        
        # 金叉买入
        if cross_over and self.pos == 0:
            # 计算购买数量
            account = self.engine.accounts["BACKTEST"]
            price = bar.close_price
            
            # 计算可买数量
            available_balance = account.balance * 0.95  # 使用95%的资金
            volume = int(available_balance / price)
            
            if volume > 0:
                # 发出买入信号
                self.buy(price, volume)
                print(f"{bar.datetime.date()}: 买入 {volume} 股 {self.symbol} @ {price:.2f}")
        
        # 死叉卖出
        elif cross_below and self.pos > 0:
            # 发出卖出信号
            self.sell(bar.close_price, self.pos)
            print(f"{bar.datetime.date()}: 卖出 {self.pos} 股 {self.symbol} @ {bar.close_price:.2f}")
    
    def on_trade(self, trade):
        """成交更新"""
        if trade.direction == Direction.LONG:
            self.pos += trade.volume
        else:
            self.pos -= trade.volume

def test_vnpy_backtest():
    """
    使用vnpy风格回测引擎测试双均线交叉策略
    """
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置回测参数
    start = datetime(2020, 1, 1)
    end = datetime(2022, 12, 31)
    engine.set_parameters(start, end, 100000)
    
    # 添加策略
    setting = {
        "symbol": "000001",
        "exchange": Exchange.SSE,
        "fast_window": 10,
        "slow_window": 30,
    }
    engine.add_strategy(MACrossStrategy, setting)
    
    # 加载历史数据
    engine.load_data("000001", Exchange.SSE, Interval.DAILY)
    
    # 运行回测
    engine.run_backtesting()
    
    # 显示回测结果
    engine.show_results()
    
    # 绘制回测图表
    try:
        engine.plot_results()
    except Exception as e:
        print(f"无法绘制图表: {e}")
    
    return engine

if __name__ == "__main__":
    engine = test_vnpy_backtest() 