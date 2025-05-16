from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Union, Optional, Dict, Any

class EventType(Enum):
    """
    表示事件的类型。
    """
    MARKET = "MARKET"  # 新的市场数据 (例如，一个新的K线柱)
    SIGNAL = "SIGNAL"  # 策略生成的交易信号
    ORDER = "ORDER"    # 请求下单
    FILL = "FILL"      # 订单已被填充 (部分或全部)
    # E.g., TIME_TICK, ORDER_STATUS, SENTIMENT, etc. # 根据需要添加其他事件类型，例如：时间事件、订单状态事件、情绪事件等。

@dataclass
class Event:
    """
    事件基类
    
    所有事件类型都应继承此类
    """
    
    def __init__(self, event_type: str, timestamp: Optional[datetime] = None, **kwargs):
        """
        初始化事件
        
        Args:
            event_type: 事件类型
            timestamp: 事件时间戳，如果为None则使用当前时间
            **kwargs: 额外的属性
        """
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now(timezone.utc)
        
        # 添加额外属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return f"{self.event_type} 事件 (时间: {self.timestamp})"

@dataclass
class MarketEvent(Event):
    """
    市场事件，表示市场数据更新
    
    当收到新的市场数据时产生此事件
    """
    
    def __init__(self, symbol: str, timestamp: datetime, 
                 open_price: float, high_price: float, 
                 low_price: float, close_price: float, 
                 volume: int, additional_data: Dict[str, Any] = None):
        """
        初始化市场事件
        
        Args:
            symbol: 交易品种代码
            timestamp: 事件时间戳
            open_price: 开盘价
            high_price: 最高价
            low_price: 最低价
            close_price: 收盘价
            volume: 成交量
            additional_data: 额外数据
        """
        super().__init__("MARKET", timestamp)
        self.symbol = symbol
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.additional_data = additional_data or {}
    
    def __str__(self):
        return (f"MARKET 市场事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"收盘价: {self.close_price:.2f})")

@dataclass
class SignalEvent(Event):
    """
    信号事件，表示交易信号
    
    当策略产生交易信号时生成此事件
    """
    
    def __init__(self, symbol: str, timestamp: datetime, 
                 signal_type: str, direction: int, 
                 strength: float = 1.0, additional_data: Dict[str, Any] = None):
        """
        初始化信号事件
        
        Args:
            symbol: 交易品种代码
            timestamp: 事件时间戳
            signal_type: 信号类型，如'LONG'、'SHORT'、'EXIT'
            direction: 方向，1表示做多，-1表示做空，0表示平仓
            strength: 信号强度，用于确定头寸规模
            additional_data: 额外数据
        """
        super().__init__("SIGNAL", timestamp)
        self.symbol = symbol
        self.signal_type = signal_type
        self.direction = direction
        self.strength = strength
        self.additional_data = additional_data or {}
    
    def __str__(self):
        direction_str = "多头" if self.direction > 0 else "空头" if self.direction < 0 else "平仓"
        return (f"SIGNAL 信号事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"类型: {self.signal_type}, 方向: {direction_str}, 强度: {self.strength:.2f})")

class OrderType(Enum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STOP"  # 修改为STOP而不是STP
    STOP_LIMIT = "STOP_LMT"
    # Add more specific order types if needed # 如果需要，添加更具体的订单类型

class OrderDirection(Enum):
    BUY = 1  # 修改为整数值1
    SELL = -1  # 修改为整数值-1

@dataclass
class OrderEvent(Event):
    """
    订单事件，表示交易订单
    
    当投资组合管理器决定下单时生成此事件
    """
    symbol: str 
    order_type: Union[str, OrderType]
    quantity: float
    # direction: int # 将在 __init__ 中处理
    price: Optional[float] = None
    order_id: Optional[str] = field(default=None) # 添加字段并设默认值
    additional_data: Dict[str, Any] = field(default_factory=dict)
    # 内部使用的数值方向，和可能的原始枚举方向
    _direction_int: int = field(init=False, repr=False)
    original_direction_enum: Optional[OrderDirection] = field(init=False, default=None, repr=False)
    
    def __init__(self, symbol: str, timestamp: datetime, 
                 order_type: Union[str, OrderType], 
                 quantity: float, 
                 direction: Union[int, OrderDirection],
                 price: Optional[float] = None, 
                 order_id: Optional[str] = None,
                 additional_data: Optional[Dict[str, Any]] = None):
        """
        初始化订单事件
        
        Args:
            symbol: 交易品种代码
            timestamp: 事件时间戳
            order_type: 订单类型，如'MARKET'、'LIMIT' (或OrderType枚举)
            quantity: 数量
            direction: 方向 (OrderDirection枚举, 或整数 1 for BUY, -1 for SELL)
            price: 价格，对于限价单有效
            order_id: 可选的订单ID
            additional_data: 额外数据
        """
        super().__init__("ORDER", timestamp)
        self.symbol = symbol
        self.order_type = order_type.value if isinstance(order_type, OrderType) else order_type
        self.quantity = quantity
        self.price = price
        
        if isinstance(direction, OrderDirection):
            self.original_direction_enum = direction
            self._direction_int = direction.value
        elif isinstance(direction, int):
            self._direction_int = direction
            if direction == 1:
                self.original_direction_enum = OrderDirection.BUY
            elif direction == -1:
                self.original_direction_enum = OrderDirection.SELL
            else:
                self.original_direction_enum = None # Or raise error for invalid int
        else:
            raise TypeError(f"OrderEvent direction must be int or OrderDirection enum, got {type(direction)}")

        self.order_id = order_id # 如果为None，则保持为None，让Broker处理
        self.additional_data = additional_data or {}
    
    @property
    def direction(self) -> int:
        """返回整数表示的方向 (1 for BUY, -1 for SELL)"""
        return self._direction_int

    def __str__(self):
        direction_str = "多头" if self.direction > 0 else "空头" if self.direction < 0 else "平仓"
        price_str = f", 价格: {self.price:.2f}" if self.price is not None else ""
        oid_str = f", ID: {self.order_id}" if self.order_id else ""
        return (f"ORDER 订单事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"类型: {self.order_type}, 方向: {direction_str}, 数量: {self.quantity}{price_str}{oid_str})")

@dataclass
class FillEvent(Event):
    """
    成交事件，表示订单成交
    
    当订单被执行并成交时生成此事件
    """
    symbol: str
    # timestamp: datetime # 已在 Event 基类中
    quantity: float 
    # direction: int # 将在 __init__ 中处理并通过属性访问
    fill_price: float
    commission: float = 0.0
    order_id: Optional[str] = None # 添加 order_id 字段
    exchange: Optional[str] = None # 保留已有的 exchange
    slippage: Optional[float] = None # 保留已有的 slippage
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    _direction_int: int = field(init=False, repr=False)
    original_direction_enum: Optional[OrderDirection] = field(init=False, default=None, repr=False)
    
    def __init__(self, symbol: str, timestamp: datetime, 
                 quantity: float, 
                 direction: Union[int, OrderDirection],
                 fill_price: float,
                 commission: float = 0.0, 
                 order_id: Optional[str] = None, # 添加 order_id 参数
                 exchange: Optional[str] = None, 
                 slippage: Optional[float] = None,
                 additional_data: Optional[Dict[str, Any]] = None):
        """
        初始化成交事件
        
        Args:
            symbol: 交易品种代码
            timestamp: 事件时间戳
            quantity: 成交数量
            direction: 方向 (OrderDirection 枚举或整数 1 for BUY, -1 for SELL)
            fill_price: 成交价格
            commission: 手续费
            order_id: 关联的订单ID
            exchange: 交易所
            slippage: 滑点
            additional_data: 额外数据
        """
        super().__init__("FILL", timestamp)
        self.symbol = symbol
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.order_id = order_id
        self.exchange = exchange
        self.slippage = slippage
        self.additional_data = additional_data or {}
    
        if isinstance(direction, OrderDirection):
            self.original_direction_enum = direction
            self._direction_int = direction.value
        elif isinstance(direction, int):
            self._direction_int = direction
            if direction == 1:
                self.original_direction_enum = OrderDirection.BUY
            elif direction == -1:
                self.original_direction_enum = OrderDirection.SELL
            else: # 包括0或其他整数
                self.original_direction_enum = None 
        else:
            raise TypeError(f"FillEvent direction must be int or OrderDirection enum, got {type(direction)}")

    @property
    def direction(self) -> int:
        """返回整数表示的方向 (1 for BUY, -1 for SELL)"""
        return self._direction_int

    def __str__(self):
        direction_str = "多头" if self.direction > 0 else "空头" if self.direction < 0 else "平仓"
        return (f"FILL 成交事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"方向: {direction_str}, 数量: {self.quantity}, 价格: {self.fill_price:.2f}, "
                f"手续费: {self.commission:.2f})")
