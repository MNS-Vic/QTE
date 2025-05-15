import pandas as pd
from collections import deque

# 尝试从qte.core.event_engine导入事件类，如果失败则定义桩代码
# 这使得策略文件本身可以独立运行或被其他非QTE环境有限地引用
try:
    from qte.core.event_engine import Event, EventType, SignalEvent, MarketEvent
except ImportError:
    # 如果直接运行策略文件或在没有完整qte环境时，提供桩定义
    class Event:
        pass
    class EventType:
        SIGNAL = "SIGNAL"
        MARKET = "MARKET"
    class SignalEvent(Event):
        def __init__(self, timestamp, symbol, direction, strength=1.0):
            self.timestamp = timestamp
            self.symbol = symbol
            self.direction = direction
            self.strength = strength
            self.event_type = EventType.SIGNAL
    class MarketEvent(Event):
        pass # 简化定义

class DualMaStrategy:
    def __init__(self, short_window: int = 5, long_window: int = 20):
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"DualMA({self.short_window},{self.long_window})"
        
        # 事件驱动模式所需属性
        self.event_engine = None
        self.prices = deque(maxlen=self.long_window) # 存储最近的收盘价
        self.current_signal_state = 0 # 0: 无信号/平仓, 1: 看多, -1: 看空
        self.data_initialized = False

    def set_event_engine(self, event_engine: 'EventEngine'):
        """注入事件引擎实例"""
        self.event_engine = event_engine

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号 (向量化模式)
        """
        if 'close' not in data.columns:
            raise ValueError("数据中必须包含'close'列")

        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0

        signals['short_ma'] = data['close'].rolling(window=self.short_window, min_periods=1).mean()
        signals['long_ma'] = data['close'].rolling(window=self.long_window, min_periods=1).mean()

        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1
        
        return signals[['signal']]

    def on_market_data(self, market_event: 'MarketEvent') -> None:
        """
        处理市场数据事件 (事件驱动模式)
        """
        if not self.event_engine:
            # print("警告: DualMaStrategy 未设置 event_engine，无法在事件驱动模式下发送信号。")
            return

        if not hasattr(market_event, 'data') or 'close' not in market_event.data:
            # print(f"警告: MarketEvent缺少数据或收盘价: {market_event}")
            return
        
        current_close = market_event.data['close']
        self.prices.append(current_close)

        if len(self.prices) < self.long_window:
            # 数据不足以计算长周期均线
            if not self.data_initialized and len(self.prices) >= self.short_window:
                 # 至少可以计算一次短均线，可以认为数据开始就绪
                 pass # 可以选择在此处进行一些初始化，但通常等待长均线
            return 
        
        self.data_initialized = True # 确认有足够数据计算所有指标

        # 计算均线
        short_ma_values = list(self.prices)[-self.short_window:]
        short_ma = sum(short_ma_values) / len(short_ma_values)
        
        long_ma_values = list(self.prices) # deque已保证长度不超过long_window
        long_ma = sum(long_ma_values) / len(long_ma_values)

        new_signal_state = self.current_signal_state

        # 均线交叉判断
        if short_ma > long_ma:
            if self.current_signal_state <= 0: # 从无信号/空头到多头
                new_signal_state = 1
                # print(f"{market_event.timestamp} - {market_event.symbol}: BUY signal (short_ma={short_ma:.2f}, long_ma={long_ma:.2f})")
                sig_event = SignalEvent(timestamp=market_event.timestamp, 
                                        symbol=market_event.symbol, 
                                        direction=1, # 买入
                                        strength=1.0)
                self.event_engine.put(sig_event)
        elif short_ma < long_ma:
            if self.current_signal_state >= 0: # 从无信号/多头到空头
                new_signal_state = -1
                # print(f"{market_event.timestamp} - {market_event.symbol}: SELL signal (short_ma={short_ma:.2f}, long_ma={long_ma:.2f})")
                sig_event = SignalEvent(timestamp=market_event.timestamp, 
                                        symbol=market_event.symbol, 
                                        direction=-1, # 卖出
                                        strength=1.0)
                self.event_engine.put(sig_event)
        # else: # 均线相等或未交叉，保持当前信号状态或根据需求平仓
            # 如果需要严格的均线粘合即平仓逻辑，可以在此处理
            # pass 
            
        self.current_signal_state = new_signal_state 