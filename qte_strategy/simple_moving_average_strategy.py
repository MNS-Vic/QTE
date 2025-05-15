from collections import deque
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime

from qte_core.events import MarketEvent, SignalEvent
from qte_core.event_loop import EventLoop
from qte_strategy.interfaces import Strategy
from qte_data.interfaces import DataProvider
from qte_analysis_reporting.logger import app_logger

class SimpleMovingAverageStrategy(Strategy):
    """
    简单移动平均线策略，用于测试掘金量化数据。
    
    当短期移动平均线从下方上穿长期移动平均线时，产生买入信号。
    当短期移动平均线从上方下穿长期移动平均线时，产生卖出信号。
    """
    def __init__(self, 
                 event_loop: EventLoop,
                 data_provider: DataProvider,
                 symbols: List[str],
                 short_window: int = 5, 
                 long_window: int = 20,
                 params: Optional[Dict[str, Any]] = None,
                 name: str = "SimpleMovingAverage"):
        """
        初始化简单移动平均线策略。
        
        参数:
            event_loop (EventLoop): 事件循环实例，用于发送信号。
            data_provider (DataProvider): 数据提供者实例。
            symbols (List[str]): 此策略交易或监控的合约代码列表。
            short_window (int): 短期移动平均线的周期。
            long_window (int): 长期移动平均线的周期。
            params (Optional[Dict[str, Any]]): 其他可选参数。
            name (str): 策略名称，默认为"SimpleMovingAverage"。
        """
        super().__init__(name, symbols, params)
        self.event_loop = event_loop
        self.data_provider = data_provider
        self.short_window = short_window
        self.long_window = long_window
        
        # 每个 symbol 的数据和状态
        self.prices: Dict[str, deque] = {symbol: deque(maxlen=self.long_window) for symbol in self.symbols}
        self.short_sma: Dict[str, Optional[float]] = {symbol: None for symbol in self.symbols}
        self.long_sma: Dict[str, Optional[float]] = {symbol: None for symbol in self.symbols}
        # 用于检测交叉的状态，存储前一个bar的短期SMA是否高于长期SMA
        self.was_short_above_long: Dict[str, Optional[bool]] = {symbol: None for symbol in self.symbols}
        
        app_logger.info(f"策略 '{self.name}' 已初始化，监控合约: {self.symbols}, 短期窗口: {short_window}, 长期窗口: {long_window}")

    def on_init(self, data_provider: DataProvider, event_loop: Optional[EventLoop] = None) -> None:
        """
        策略初始化方法，满足接口要求。
        
        参数:
            data_provider (DataProvider): 数据提供者实例。
            event_loop (Optional[EventLoop]): 事件循环实例。
        """
        # 如果在初始化时已传入，我们不需要再次存储
        if self.data_provider is None:
            self.data_provider = data_provider
        
        if event_loop is not None and self.event_loop is None:
            self.event_loop = event_loop
        
        app_logger.info(f"策略 '{self.name}' 初始化完成。")
    
    def on_bar(self, event: MarketEvent) -> None:
        """
        处理K线数据事件。
        
        参数:
            event (MarketEvent): K线数据事件。
        """
        # 实际上就是调用on_market_event
        self.on_market_event(event)
    
    def on_market_event(self, event: MarketEvent) -> None:
        """
        处理市场事件，更新价格数据并检查交易信号。
        """
        if event.symbol not in self.symbols:
            return  # 不是此策略关注的合约
        
        # 获取价格，优先使用price字段，如果没有则使用close_price
        price = getattr(event, 'price', None)
        if price is None or price <= 0:
            price = event.close_price
        
        self.prices[event.symbol].append(price)
        
        # 检查是否有足够的数据来计算移动平均线
        if len(self.prices[event.symbol]) < self.long_window:
            return
        
        # 计算移动平均线
        current_prices = list(self.prices[event.symbol])
        self.short_sma[event.symbol] = pd.Series(current_prices).rolling(window=self.short_window).mean().iloc[-1]
        self.long_sma[event.symbol] = pd.Series(current_prices).rolling(window=self.long_window).mean().iloc[-1]
        
        # 检查信号
        self._check_signal(event)
    
    def _check_signal(self, event: MarketEvent) -> None:
        """
        检查移动平均线交叉并生成信号。
        """
        symbol = event.symbol
        short_sma = self.short_sma[symbol]
        long_sma = self.long_sma[symbol]
        
        if short_sma is None or long_sma is None:
            return  # MA尚未计算
        
        current_short_above_long = short_sma > long_sma
        
        if self.was_short_above_long[symbol] is None:
            # 第一次有足够数据，只记录状态
            self.was_short_above_long[symbol] = current_short_above_long
            return
        
        # 检查交叉
        if not self.was_short_above_long[symbol] and current_short_above_long:  # 金叉: 短期上穿长期
            signal_type = "LONG"
            app_logger.info(f"策略 '{self.name}' ({symbol}): 金叉信号! ShortSMA={short_sma:.2f}, LongSMA={long_sma:.2f}")
            signal = SignalEvent(symbol=symbol, signal_type=signal_type, strength=1.0, timestamp=event.timestamp)
            self.event_loop.add_event(signal)
        elif self.was_short_above_long[symbol] and not current_short_above_long:  # 死叉: 短期下穿长期
            signal_type = "SHORT"
            app_logger.info(f"策略 '{self.name}' ({symbol}): 死叉信号! ShortSMA={short_sma:.2f}, LongSMA={long_sma:.2f}")
            signal = SignalEvent(symbol=symbol, signal_type=signal_type, strength=1.0, timestamp=event.timestamp)
            self.event_loop.add_event(signal)
        
        # 更新前一状态
        self.was_short_above_long[symbol] = current_short_above_long 