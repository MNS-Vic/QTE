from collections import deque
from typing import Dict, Any, Optional, List
import pandas as pd # 用于计算移动平均线
import numpy as np
from datetime import datetime, timedelta

from qte.core.events import MarketEvent, SignalEvent, EventType
from qte.data.interfaces import DataProvider # 策略可能需要直接查询历史数据进行初始化
from qte.core.event_loop import EventLoop
from .interfaces import Strategy # Assuming Strategy is in the same package (qte.strategy)
from qte.analysis.logger import app_logger

class MovingAverageCrossStrategy(Strategy):
    """
    一个简单的移动平均线交叉策略。

    当短期移动平均线从下方上穿长期移动平均线时，产生买入信号。
    当短期移动平均线从上方下穿长期移动平均线时，产生卖出信号。
    """
    def __init__(self, 
                 symbols: List[str], 
                 event_loop: EventLoop, # 直接传递事件循环实例
                 short_window: int = 10, 
                 long_window: int = 30,
                 params: Optional[Dict[str, Any]] = None,
                 data_provider: Optional[DataProvider] = None,
                 name: str = "MovingAverageCross"):
        """
        初始化移动平均线交叉策略。

        参数:
            symbols (List[str]): 此策略交易或监控的合约代码列表。
            event_loop (EventLoop): 事件循环实例，用于发送信号。
            short_window (int): 短期移动平均线的周期。
            long_window (int): 长期移动平均线的周期。
            params (Optional[Dict[str, Any]]): 其他可选参数。
            data_provider (Optional[DataProvider]): 数据提供者实例，可选。
            name (str): 策略名称，默认为"MovingAverageCross"。
        """
        super().__init__(name, symbols, params)
        self.event_loop = event_loop
        self.short_window = short_window
        self.long_window = long_window
        self.data_provider = data_provider

        if short_window >= long_window:
            raise ValueError("短期窗口必须小于长期窗口。")

        # 每个 symbol 的数据和状态
        self.prices: Dict[str, deque] = {symbol: deque(maxlen=self.long_window) for symbol in self.symbols}
        self.short_sma: Dict[str, Optional[float]] = {symbol: None for symbol in self.symbols}
        self.long_sma: Dict[str, Optional[float]] = {symbol: None for symbol in self.symbols}
        # 用于检测交叉的状态，存储前一个bar的短期SMA是否高于长期SMA
        self.was_short_above_long: Dict[str, Optional[bool]] = {symbol: None for symbol in self.symbols}
        
        app_logger.info(f"策略 '{self.name}' 已初始化，监控合约: {self.symbols}, 短期窗口: {short_window}, 长期窗口: {long_window}")

    def on_init(self, data_provider: DataProvider) -> None:
        """
        策略初始化，预加载一些历史数据来填充初始窗口。
        这样在回测开始时就能有足够的数据计算移动平均线，无需等待填充。
        
        参数:
            data_provider (DataProvider): 数据提供者实例
        """
        app_logger.info(f"策略 '{self.name}' on_init 被调用，预加载历史数据...")
        
        if not data_provider:
            app_logger.warning(f"策略 '{self.name}' on_init: 没有提供data_provider，无法预加载数据。")
            return
        
        # 如果我们在初始化时已存储了data_provider引用，可以重用它
        if self.data_provider is None:
            self.data_provider = data_provider
        
        current_time = datetime.now()
        for symbol in self.symbols:
            try:
                # 使用改进后的get_historical_bars方法
                # 获取足够长的历史数据来填充长期移动平均线窗口
                # 假设30天的数据足够（实际项目中可能需要更多）
                start_date = current_time - timedelta(days=30)
                end_date = current_time
                
                # 使用新的接口获取历史数据
                bars_gen = data_provider.get_historical_bars(symbol, start_date, end_date)
                
                if bars_gen:
                    # 将生成器转换为列表
                    bars = list(bars_gen)
                    
                    if len(bars) >= self.long_window:
                        # 预填充价格队列
                        initial_prices = [bar['close'] for bar in bars[-self.long_window:]]
                        self.prices[symbol] = deque(initial_prices, maxlen=self.long_window)
                        
                        # 预计算移动平均线
                        prices_series = pd.Series(initial_prices)
                        if len(prices_series) >= self.short_window:
                            self.short_sma[symbol] = prices_series.rolling(window=self.short_window).mean().iloc[-1]
                        if len(prices_series) >= self.long_window:
                            self.long_sma[symbol] = prices_series.rolling(window=self.long_window).mean().iloc[-1]
                            
                            # 设置初始交叉状态
                            if self.short_sma[symbol] is not None and self.long_sma[symbol] is not None:
                                self.was_short_above_long[symbol] = self.short_sma[symbol] > self.long_sma[symbol]
                                
                        app_logger.info(f"策略 '{self.name}' 为 {symbol} 预加载了 {len(initial_prices)} 条历史数据")
                    else:
                        app_logger.warning(f"策略 '{self.name}' on_init: {symbol} 历史数据不足，需要 {self.long_window} 条，实际获得 {len(bars)} 条")
                else:
                    app_logger.warning(f"策略 '{self.name}' on_init: 未能获取 {symbol} 的历史数据")
            except Exception as e:
                app_logger.error(f"策略 '{self.name}' on_init: 预加载 {symbol} 的历史数据时出错: {e}")
        
        app_logger.info(f"策略 '{self.name}' 初始化完成。")

    def on_bar(self, event: MarketEvent) -> None:
        """
        处理新的市场K线数据。
        """
        print(f"DEBUG STRATEGY ({self.name} - {event.symbol}): on_bar received event at {event.timestamp} with close price {event.close_price}") # DEBUG print

        if event.symbol not in self.symbols:
            print(f"DEBUG STRATEGY ({self.name} - {event.symbol}): Symbol not in strategy symbols {self.symbols}. Skipping.") # DEBUG print
            return # 不是此策略关注的合约

        self.prices[event.symbol].append(event.close_price)
        print(f"DEBUG STRATEGY ({self.name} - {event.symbol}): Appended price. Queue length = {len(self.prices[event.symbol])}, long_window = {self.long_window}") # DEBUG print

        # 检查是否有足够的数据来计算MA
        if len(self.prices[event.symbol]) < self.long_window:
            print(f"DEBUG STRATEGY ({self.name} - {event.symbol}): Data insufficient for MA. Returning from on_bar.") # DEBUG print
            # app_logger.debug(f"策略 '{self.name}' ({event.symbol}): 数据不足 ({len(self.prices[event.symbol])}/{self.long_window}) 以计算MA。")
            return

        # 计算移动平均线
        print(f"DEBUG STRATEGY ({self.name} - {event.symbol}): Data sufficient for MA. Proceeding to calculate.") # DEBUG print
        current_prices = list(self.prices[event.symbol])
        self.short_sma[event.symbol] = pd.Series(current_prices).rolling(window=self.short_window).mean().iloc[-1]
        self.long_sma[event.symbol] = pd.Series(current_prices).rolling(window=self.long_window).mean().iloc[-1]

        # app_logger.debug(f"策略 '{self.name}' ({event.symbol}): Close={event.close_price}, ShortSMA={self.short_sma[event.symbol]:.2f}, LongSMA={self.long_sma[event.symbol]:.2f}")

        # 检查信号
        self._check_signal(event)

    def _check_signal(self, event: MarketEvent) -> None:
        """
        检查移动平均线交叉并生成信号。
        """
        symbol = event.symbol
        short_sma = self.short_sma[symbol]
        long_sma = self.long_sma[symbol]

        # DEBUG print for MA values
        print(f"DEBUG STRATEGY ({self.name} - {symbol} @ {event.timestamp}): Close={event.close_price:.2f}, ShortSMA={short_sma if short_sma is None else short_sma:.2f}, LongSMA={long_sma if long_sma is None else long_sma:.2f}")

        if short_sma is None or long_sma is None:
            print(f"DEBUG STRATEGY ({self.name} - {symbol}): MA not ready (short: {short_sma}, long: {long_sma}).")
            return # MA尚未计算

        current_short_above_long = short_sma > long_sma
        print(f"DEBUG STRATEGY ({self.name} - {symbol}): current_short_above_long = {current_short_above_long}. was_short_above_long = {self.was_short_above_long[symbol]}")

        if self.was_short_above_long[symbol] is None:
            # 第一次有足够数据，只记录状态
            self.was_short_above_long[symbol] = current_short_above_long
            print(f"DEBUG STRATEGY ({self.name} - {symbol}): Initialized was_short_above_long to {current_short_above_long}")
            return

        # 检查交叉
        if not self.was_short_above_long[symbol] and current_short_above_long: # 金叉: 短期上穿长期
            signal_type = "LONG"
            app_logger.info(f"策略 '{self.name}' ({symbol}): 金叉信号! ShortSMA={short_sma:.2f}, LongSMA={long_sma:.2f}")
            print(f"DEBUG STRATEGY ({self.name} - {symbol}): 金叉信号! Triggering LONG.") # DEBUG print for signal
            signal = SignalEvent(symbol=symbol, signal_type=signal_type, direction=1, strength=1.0, timestamp=event.timestamp) # direction 1 for LONG
            self.event_loop.put_event(signal)
        elif self.was_short_above_long[symbol] and not current_short_above_long: # 死叉: 短期下穿长期
            signal_type = "SHORT"
            app_logger.info(f"策略 '{self.name}' ({symbol}): 死叉信号! ShortSMA={short_sma:.2f}, LongSMA={long_sma:.2f}")
            print(f"DEBUG STRATEGY ({self.name} - {symbol}): 死叉信号! Triggering SHORT.") # DEBUG print for signal
            signal = SignalEvent(symbol=symbol, signal_type=signal_type, direction=-1, strength=1.0, timestamp=event.timestamp) # direction -1 for SHORT
            self.event_loop.put_event(signal)
        
        # 更新前一状态
        self.was_short_above_long[symbol] = current_short_above_long

    def on_market_event(self, event: MarketEvent) -> None:
        """
        处理市场事件，实际是调用on_bar方法。
        这是为了与回测器的事件处理接口一致。
        """
        # print(f"DEBUG STRATEGY ({self.name}): on_market_event for {event.symbol} at {event.timestamp} Price: {event.close_price}") # Optional: Print when event is received by strategy
        self.on_bar(event)

# 示例用法 (可以稍后移至测试或示例脚本)
if __name__ == '__main__':
    from qte.core.event_loop import EventLoop
    from qte.core.events import MarketEvent
    from datetime import datetime, timedelta

    app_logger.info("\n--- 测试 MovingAverageCrossStrategy ---")
    event_loop_test = EventLoop() # 创建一个测试用的事件循环
    
    # 模拟一个简单的事件处理器来打印信号
    def signal_printer(event: SignalEvent):
        app_logger.info(f"测试信号接收: {event.symbol} - {event.signal_type} at {event.timestamp}")
    event_loop_test.register_handler(EventType.SIGNAL, signal_printer)

    # 初始化策略
    # 注意: 现实中，event_loop 通常由回测引擎或交易系统管理和注入
    strategy_test = MovingAverageCrossStrategy(
        name="SMACrossTest", 
        symbols=["TEST_AAPL"], 
        event_loop=event_loop_test,
        short_window=3, 
        long_window=5
    )
    
    # 模拟市场数据流
    prices_aapl = [10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 9, 10, 11]
    current_time = datetime(2023,1,1)

    app_logger.info("开始模拟市场数据馈送...")
    for i, price in enumerate(prices_aapl):
        current_time += timedelta(minutes=1)
        market_event = MarketEvent(
            symbol="TEST_AAPL", 
            timestamp=current_time,
            open_price=price-0.1, 
            high_price=price+0.1, 
            low_price=price-0.2, 
            close_price=price, 
            volume=1000
        )
        app_logger.debug(f"馈送市场数据: {market_event.symbol} Close={market_event.close_price} at {market_event.timestamp}")
        strategy_test.on_bar(market_event) # 直接调用 on_bar 进行测试
        
        # 模拟事件循环处理 (在实际系统中，这会异步发生)
        # 为简单起见，我们在这里同步处理一下队列中的信号事件
        if event_loop_test.event_queue: # 检查是否有事件
            while event_loop_test.event_queue: # 处理所有累积的事件
                 queued_event = event_loop_test.event_queue.popleft()
                 if isinstance(queued_event, SignalEvent):
                     signal_printer(queued_event)
                 # 忽略其他可能的事件类型，因为我们只注册了信号处理器

    app_logger.info("移动平均线交叉策略测试结束。") 
# 为了向后兼容，提供SimpleMovingAverageStrategy别名
SimpleMovingAverageStrategy = MovingAverageCrossStrategy
