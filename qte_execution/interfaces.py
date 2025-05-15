from abc import ABC, abstractmethod
from typing import Optional, Union, List # Added Union, List

from qte_core.events import OrderEvent, FillEvent, Event, MarketEvent, OrderDirection # Added MarketEvent, OrderDirection
from qte_core.event_loop import EventLoop

class ExecutionHandler(ABC):
    """
    执行处理器的抽象基类。
    
    负责接收订单事件并执行它们，生成成交事件。
    在实盘交易中，这个类会连接到实际的交易接口。
    在回测中，它模拟订单执行并生成成交回报。
    """
    
    @abstractmethod
    def on_order(self, order: OrderEvent) -> None:
        """
        处理订单事件。
        
        参数:
            order (OrderEvent): 订单事件对象。
        """
        raise NotImplementedError


class CommissionModel(ABC):
    """
    佣金模型的抽象基类。
    """
    @abstractmethod
    def calculate_commission(self, symbol: str, quantity: Union[float, int], price: float, direction: OrderDirection) -> float:
        """
        计算给定交易的佣金。
        返回总佣金金额。
        """
        raise NotImplementedError

class SlippageModel(ABC):
    """
    滑点模型的抽象基类。
    """
    @abstractmethod
    def calculate_fill_price_with_slippage(
        self,
        symbol: str,
        quantity: Union[float, int],
        intended_price: float, # e.g., current market price for MKT, or limit price for LMT
        direction: OrderDirection,
        market_event: Optional[MarketEvent] = None # Current market conditions
    ) -> float:
        """
        计算应用滑点后的实际成交价格。
        `market_event` 可用于依赖波动率、价差或交易量的模型。
        返回调整后的成交价格。
        """
        raise NotImplementedError

class BrokerSimulator(ABC):
    """
    模拟经纪商的抽象基类。
    它处理订单执行请求并生成成交事件。
    它还集成了佣金和滑点模型。
    """

    def __init__(self, event_loop: EventLoop, commission_model: CommissionModel, slippage_model: SlippageModel):
        self.event_loop = event_loop
        self.commission_model = commission_model
        self.slippage_model = slippage_model

    @abstractmethod
    def submit_order(self, order: OrderEvent) -> None:
        """
        向模拟经纪商提交订单。
        然后，经纪商将根据当前市场数据 (通过事件时间隐式传递或显式传递)、
        其内部逻辑以及佣金/滑点模型来处理此订单。
        它最终应将一个 FillEvent (或多个用于部分成交的 FillEvent) 放入 event_loop。
        它可能还会为状态更新生成 OrderEvents (例如 ACKNOWLEDGED, REJECTED)。
        """
        raise NotImplementedError

    # Optional: Methods for order cancellation, modification, querying order status
    # @abstractmethod
    # def cancel_order(self, order_id: str) -> None:
    #     raise NotImplementedError

    # @abstractmethod
    # def modify_order(self, order_id: str, new_order_details: OrderEvent) -> None:
    #     raise NotImplementedError
        
    # @abstractmethod
    # def get_order_status(self, order_id: str) -> Optional[OrderEvent]: # or a dedicated OrderStatusEvent
    #     raise NotImplementedError 