from typing import Dict, Any
from datetime import datetime
import logging

from qte.core.events import OrderEvent, FillEvent, EventType
from qte.core.event_loop import EventLoop
from .interfaces import ExecutionHandler
from qte.analysis.logger import app_logger

logger = logging.getLogger(__name__)

class SimpleExecutionHandler(ExecutionHandler):
    """
    简单的执行处理器，模拟订单执行和成交回报。
    
    这个简化版的执行处理器假设所有订单都能立即以当前市场价格成交，没有滑点、延迟或拒绝。
    用于回测和模拟交易环境。
    """
    
    def __init__(self, event_loop: EventLoop, commission_rate: float = 0.0003):
        """
        初始化简单执行处理器。
        
        参数:
            event_loop (EventLoop): 事件循环实例，用于发送成交事件。
            commission_rate (float): 佣金费率，默认为万分之三(0.0003)。
        """
        super().__init__()
        self.event_loop = event_loop
        self.commission_rate = commission_rate
        
        # 最近一个市场价格缓存，用于模拟成交价格
        self.latest_prices: Dict[str, float] = {}
        
        # 注册处理器
        self.event_loop.register_handler(EventType.ORDER, self.on_order)
        self.event_loop.register_handler(EventType.MARKET, self.on_market)
        
        app_logger.info(f"简单执行处理器已初始化，佣金费率: {commission_rate}")
    
    def on_market(self, event) -> None:
        """
        处理市场事件，更新最新价格缓存。
        
        参数:
            event: 市场事件对象。
        """
        # 更新最新价格缓存
        symbol = event.symbol
        # 优先使用price字段，如果没有则使用close_price
        price = getattr(event, 'price', None)
        if price is None or price <= 0:
            price = event.close_price
        
        if price > 0:
            self.latest_prices[symbol] = price
    
    def on_order(self, order: OrderEvent) -> None:
        """
        处理订单事件，生成成交事件。
        
        参数:
            order (OrderEvent): 订单事件对象。
        """
        app_logger.info(f"收到订单: {order.symbol} {order.direction} {order.quantity} @ {order.order_type}")
        
        # 获取成交价格
        fill_price = self._get_fill_price(order.symbol)
        if fill_price <= 0:
            app_logger.warning(f"无法为 {order.symbol} 获取有效的成交价格，订单未成交")
            return
        
        # 计算佣金
        commission = self._calculate_commission(order.quantity, fill_price)
        
        # 创建成交事件
        fill_event = FillEvent(
            order_id=order.order_id or f"simfill_{datetime.now().timestamp()}",
            symbol=order.symbol,
            timestamp=order.timestamp,
            direction=order.direction,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission
        )
        
        app_logger.info(f"订单成交: {fill_event.symbol} {fill_event.direction} {fill_event.quantity} @ {fill_event.fill_price} (佣金: {fill_event.commission:.2f})")
        
        # 发送成交事件
        self.event_loop.put_event(fill_event)
    
    def _get_fill_price(self, symbol: str) -> float:
        """
        获取成交价格。在实际场景中，这应该考虑订单类型、市场深度、滑点等因素。
        在这个简化版中，我们简单地使用最新市场价格。
        
        参数:
            symbol (str): 交易品种代码。
            
        返回:
            float: 成交价格。
        """
        return self.latest_prices.get(symbol, 0.0)
    
    def _calculate_commission(self, quantity: int, price: float) -> float:
        """
        计算佣金。
        
        参数:
            quantity (int): 成交数量。
            price (float): 成交价格。
            
        返回:
            float: 佣金金额。
        """
        return abs(quantity) * price * self.commission_rate 