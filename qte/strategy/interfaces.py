from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List # Added List
import pandas as pd

# Assuming these modules will exist with the specified classes
from qte.core.events import MarketEvent, SignalEvent, OrderEvent, FillEvent 
# Forward declaration or type alias if qte_data.interfaces causes circular import during linting
# For now, direct import assuming it's resolvable by Python path later.
from qte.data.interfaces import DataProvider 
from qte.core.event_loop import EventLoop 

class Strategy(ABC):
    """
    所有交易策略的抽象基类。
    策略接收市场数据并生成交易信号。
    它们还可以对自己的订单和成交事件做出反应。
    """

    def __init__(self, name: str, symbols: List[str], params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.symbols = symbols # List of symbols this strategy trades or monitors
        self.params = params if params is not None else {}
        # self.event_loop_ref: Optional[EventLoop] = None 
        # self.data_provider_ref: Optional[DataProvider] = None
        # These might be injected by the BacktestCoordinator or StrategyLoader

    @abstractmethod
    def on_init(self, data_provider: DataProvider, event_loop: EventLoop) -> None:
        """
        在回测开始时或策略初始化时调用一次。
        用于设置初始状态、加载指标的历史数据等。
        如果策略需要直接推送 SignalEvents，则可以存储 event_loop。
        """
        # Example: 
        # self.data_provider_ref = data_provider
        # self.event_loop_ref = event_loop
        raise NotImplementedError

    @abstractmethod
    def on_bar(self, event: MarketEvent) -> None:
        """
        为订阅的合约代码的每个新的市场K线柱/数据事件调用。
        这是核心策略逻辑所在的位置。
        应生成信号并通过 self.event_loop_ref.add_event(SignalEvent(...)) 将其放入 event_loop。
        """
        raise NotImplementedError

    # Optional event handlers for strategies that need to react to their own orders/fills
    def on_order_status(self, event: OrderEvent) -> None:
        """
        (可选) 当此策略发出的订单有更新时调用。
        """
        pass # Default implementation does nothing

    def on_fill(self, event: FillEvent) -> None:
        """
        (可选) 当此策略的订单被成交时调用。
        """
        pass # Default implementation does nothing

    # Optional: on_tick for tick-based strategies
    # @abstractmethod
    # def on_tick(self, event: TickData) -> None:
    #     raise NotImplementedError

    # Optional: on_shutdown or similar for cleanup
    # def on_shutdown(self) -> None:
    #     pass 