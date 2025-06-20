#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件类型定义

统一的事件类型定义，消除重复和冲突
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Union, Optional, Dict, Any


class EventType(Enum):
    """
    统一的事件类型枚举
    
    合并了原有的多个EventType定义，提供统一的事件类型
    """
    # 核心事件类型
    MARKET = "MARKET"           # 市场数据事件
    SIGNAL = "SIGNAL"           # 交易信号事件
    ORDER = "ORDER"             # 订单事件
    FILL = "FILL"               # 成交事件
    ACCOUNT = "ACCOUNT"         # 账户事件
    
    # 系统事件类型
    SYSTEM_START = "SYSTEM_START"       # 系统启动
    SYSTEM_STOP = "SYSTEM_STOP"         # 系统停止
    SYSTEM_ERROR = "SYSTEM_ERROR"       # 系统错误
    
    # 策略事件类型
    STRATEGY_START = "STRATEGY_START"   # 策略启动
    STRATEGY_STOP = "STRATEGY_STOP"     # 策略停止
    STRATEGY_ERROR = "STRATEGY_ERROR"   # 策略错误
    
    # 数据事件类型
    DATA_START = "DATA_START"           # 数据开始
    DATA_END = "DATA_END"               # 数据结束
    DATA_ERROR = "DATA_ERROR"           # 数据错误
    
    # 自定义事件类型
    CUSTOM = "CUSTOM"                   # 自定义事件
    
    # 时间事件类型
    TIME_TICK = "TIME_TICK"             # 时间滴答
    TIME_BAR = "TIME_BAR"               # 时间周期
    
    # 风控事件类型
    RISK_WARNING = "RISK_WARNING"       # 风险警告
    RISK_LIMIT = "RISK_LIMIT"           # 风险限制


class EventPriority(IntEnum):
    """
    事件优先级枚举
    
    数值越小，优先级越高
    """
    CRITICAL = 1    # 关键事件（系统错误等）
    HIGH = 2        # 高优先级（风险事件等）
    NORMAL = 3      # 普通优先级（市场数据等）
    LOW = 4         # 低优先级（日志事件等）
    BACKGROUND = 5  # 后台事件（清理任务等）


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "MKT"              # 市价单
    LIMIT = "LMT"               # 限价单
    STOP = "STOP"               # 止损单
    STOP_LIMIT = "STOP_LMT"     # 止损限价单
    TRAILING_STOP = "TRAIL"     # 跟踪止损单
    ICEBERG = "ICE"             # 冰山单
    TWAP = "TWAP"               # 时间加权平均价格单
    VWAP = "VWAP"               # 成交量加权平均价格单


class OrderDirection(Enum):
    """订单方向枚举"""
    BUY = 1     # 买入
    SELL = -1   # 卖出
    CLOSE = 0   # 平仓


@dataclass
class Event:
    """
    事件基类

    所有事件类型都应继承此类
    """
    event_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, event_type: str, timestamp: datetime = None,
                 event_id: str = None, source: Optional[str] = None,
                 priority: EventPriority = EventPriority.NORMAL,
                 metadata: Dict[str, Any] = None, **kwargs):
        """
        初始化事件

        支持向后兼容性，允许额外的关键字参数
        """
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.event_id = event_id or str(uuid.uuid4())[:8]
        self.source = source
        self.priority = priority
        self.metadata = metadata or {}

        # 向后兼容：将额外的关键字参数存储到metadata中
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
                self.metadata[key] = value

    def __post_init__(self):
        """后初始化处理"""
        # 为了向后兼容性，不自动添加时区信息
        # 如果需要时区信息，应该在创建时明确指定
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'event_id': self.event_id,
            'source': self.source,
            'priority': self.priority.value,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """从字典创建事件"""
        timestamp = datetime.fromisoformat(data['timestamp'])
        priority = EventPriority(data.get('priority', EventPriority.NORMAL.value))
        
        return cls(
            event_type=data['event_type'],
            timestamp=timestamp,
            event_id=data.get('event_id', str(uuid.uuid4())[:8]),
            source=data.get('source'),
            priority=priority,
            metadata=data.get('metadata', {})
        )
    
    def __str__(self):
        return f"{self.event_type} 事件 (ID: {self.event_id}, 时间: {self.timestamp})"


@dataclass
class MarketEvent(Event):
    """
    市场数据事件

    当收到新的市场数据时产生此事件
    """
    symbol: str = ""
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    volume: int = 0
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, symbol: str = "", open_price: float = 0.0,
                 high_price: float = 0.0, low_price: float = 0.0,
                 close_price: float = 0.0, volume: int = 0,
                 timestamp: datetime = None, additional_data: Dict[str, Any] = None):
        super().__init__(
            event_type=EventType.MARKET.value,
            timestamp=timestamp,
            priority=EventPriority.NORMAL
        )
        self.symbol = symbol
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.additional_data = additional_data or {}
    
    def get_ohlcv(self) -> Dict[str, float]:
        """获取OHLCV数据"""
        return {
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume
        }
    
    def __str__(self):
        return (f"MARKET 市场事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"收盘价: {self.close_price:.2f})")


@dataclass
class SignalEvent(Event):
    """
    信号事件

    当策略产生交易信号时生成此事件
    """
    symbol: str = ""
    signal_type: str = ""
    direction: int = 0
    strength: float = 1.0
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, symbol: str = "", signal_type: str = "",
                 direction: int = 0, strength: float = 1.0,
                 timestamp: datetime = None, additional_data: Dict[str, Any] = None):
        super().__init__(
            event_type=EventType.SIGNAL.value,
            timestamp=timestamp,
            priority=EventPriority.NORMAL
        )
        self.symbol = symbol
        self.signal_type = signal_type
        self.direction = direction
        self.strength = strength
        self.additional_data = additional_data or {}
    
    def is_long_signal(self) -> bool:
        """是否为多头信号"""
        return self.direction > 0
    
    def is_short_signal(self) -> bool:
        """是否为空头信号"""
        return self.direction < 0
    
    def is_close_signal(self) -> bool:
        """是否为平仓信号"""
        return self.direction == 0
    
    def __str__(self):
        direction_str = "多头" if self.direction > 0 else "空头" if self.direction < 0 else "平仓"
        return (f"SIGNAL 信号事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"类型: {self.signal_type}, 方向: {direction_str}, 强度: {self.strength:.2f})")


@dataclass
class OrderEvent(Event):
    """
    订单事件

    当投资组合管理器决定下单时生成此事件
    """
    symbol: str = ""
    order_type: Union[str, OrderType] = OrderType.MARKET
    quantity: float = 0.0
    direction: Union[int, OrderDirection] = OrderDirection.BUY
    price: Optional[float] = None
    order_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, symbol: str = "", order_type: Union[str, OrderType] = OrderType.MARKET,
                 quantity: float = 0.0, direction: Union[int, OrderDirection] = OrderDirection.BUY,
                 price: Optional[float] = None, order_id: Optional[str] = None,
                 timestamp: datetime = None, additional_data: Dict[str, Any] = None):
        super().__init__(
            event_type=EventType.ORDER.value,
            timestamp=timestamp,
            priority=EventPriority.NORMAL
        )
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.additional_data = additional_data or {}

        # 处理order_type
        if isinstance(order_type, OrderType):
            self.order_type = order_type.value
        else:
            self.order_type = order_type

        # 处理direction - 保持向后兼容性
        if isinstance(direction, OrderDirection):
            self.direction = direction.value  # 存储为整数以保持兼容性
            self._direction_int = direction.value
            self.original_direction_enum = direction
        elif isinstance(direction, int):
            self.direction = direction  # 直接存储整数
            self._direction_int = direction
            if direction == 1:
                self.original_direction_enum = OrderDirection.BUY
            elif direction == -1:
                self.original_direction_enum = OrderDirection.SELL
            else:
                self.original_direction_enum = OrderDirection.CLOSE

        # 处理订单ID - 只有明确传入None时才不生成
        self.order_id = order_id
        if order_id is None and hasattr(self, '_auto_generate_order_id'):
            self.order_id = f"ORD_{self.event_id}"
    
    @property
    def direction_int(self) -> int:
        """返回整数表示的方向"""
        return getattr(self, '_direction_int', 0)
    
    def is_buy_order(self) -> bool:
        """是否为买单"""
        return self.direction_int > 0
    
    def is_sell_order(self) -> bool:
        """是否为卖单"""
        return self.direction_int < 0
    
    def __str__(self):
        direction_str = "买入" if self.direction_int > 0 else "卖出" if self.direction_int < 0 else "平仓"
        price_str = f", 价格: {self.price:.2f}" if self.price is not None else ""
        return (f"ORDER 订单事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"类型: {self.order_type}, 方向: {direction_str}, 数量: {self.quantity}{price_str})")


@dataclass
class FillEvent(Event):
    """
    成交事件

    当订单被执行并成交时生成此事件
    """
    symbol: str = ""
    quantity: float = 0.0
    direction: Union[int, OrderDirection] = OrderDirection.BUY
    fill_price: float = 0.0
    commission: float = 0.0
    order_id: Optional[str] = None
    exchange: Optional[str] = None
    slippage: Optional[float] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, symbol: str = "", quantity: float = 0.0,
                 direction: Union[int, OrderDirection] = OrderDirection.BUY,
                 fill_price: float = 0.0, commission: float = 0.0,
                 order_id: Optional[str] = None, exchange: Optional[str] = None,
                 slippage: Optional[float] = None, timestamp: datetime = None,
                 additional_data: Dict[str, Any] = None):
        super().__init__(
            event_type=EventType.FILL.value,
            timestamp=timestamp,
            priority=EventPriority.NORMAL
        )
        self.symbol = symbol
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.order_id = order_id
        self.exchange = exchange
        self.slippage = slippage
        self.additional_data = additional_data or {}

        # 处理direction - 保持向后兼容性
        if isinstance(direction, OrderDirection):
            self.direction = direction.value  # 存储为整数以保持兼容性
            self._direction_int = direction.value
            self.original_direction_enum = direction
        elif isinstance(direction, int):
            self.direction = direction  # 直接存储整数
            self._direction_int = direction
            if direction == 1:
                self.original_direction_enum = OrderDirection.BUY
            elif direction == -1:
                self.original_direction_enum = OrderDirection.SELL
            else:
                self.original_direction_enum = OrderDirection.CLOSE
    
    @property
    def direction_int(self) -> int:
        """返回整数表示的方向"""
        return getattr(self, '_direction_int', 0)
    
    def get_total_cost(self) -> float:
        """获取总成本（包含手续费）"""
        return self.quantity * self.fill_price + self.commission
    
    def get_net_amount(self) -> float:
        """获取净金额（买入为负，卖出为正）"""
        total_cost = self.get_total_cost()
        return total_cost if self.direction_int < 0 else -total_cost
    
    def __str__(self):
        direction_str = "买入" if self.direction_int > 0 else "卖出" if self.direction_int < 0 else "平仓"
        return (f"FILL 成交事件 (品种: {self.symbol}, 时间: {self.timestamp}, "
                f"方向: {direction_str}, 数量: {self.quantity}, 价格: {self.fill_price:.2f}, "
                f"手续费: {self.commission:.2f})")


@dataclass
class AccountEvent(Event):
    """
    账户事件

    账户资金变动信息
    """
    balance: float = 0.0
    available: float = 0.0
    margin: float = 0.0
    equity: float = 0.0
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, balance: float = 0.0, available: float = 0.0,
                 margin: float = 0.0, equity: float = 0.0,
                 timestamp: datetime = None, additional_data: Dict[str, Any] = None):
        super().__init__(
            event_type=EventType.ACCOUNT.value,
            timestamp=timestamp,
            priority=EventPriority.NORMAL
        )
        self.balance = balance
        self.available = available
        self.margin = margin
        self.equity = equity if equity > 0.0 else balance  # 如果equity未设置，默认等于balance
        self.additional_data = additional_data or {}
    
    def get_margin_ratio(self) -> float:
        """获取保证金比例"""
        if self.equity <= 0:
            return 0.0
        return self.margin / self.equity
    
    def get_available_ratio(self) -> float:
        """获取可用资金比例"""
        if self.balance <= 0:
            return 0.0
        return self.available / self.balance
    
    def __str__(self):
        return (f"ACCOUNT 账户事件 (时间: {self.timestamp}, "
                f"余额: {self.balance:.2f}, 可用: {self.available:.2f}, "
                f"保证金: {self.margin:.2f})")
