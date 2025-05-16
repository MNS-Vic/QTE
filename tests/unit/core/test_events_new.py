"""
核心事件系统单元测试（重新实现）
测试Events基础类、市场事件、信号事件、订单事件和成交事件
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
import inspect

# 导入要测试的模块
from qte.core.events import (
    Event, EventType, MarketEvent, SignalEvent, 
    OrderEvent, FillEvent, OrderDirection, OrderType
)

class TestEventBase:
    """测试基础事件类"""
    
    def setup_method(self):
        """测试前设置"""
        self.timestamp = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    def test_event_initialization_with_timestamp(self):
        """测试提供时间戳初始化事件"""
        event = Event(event_type="TEST", timestamp=self.timestamp)
        
        assert event.event_type == "TEST"
        assert event.timestamp == self.timestamp
    
    def test_event_initialization_without_timestamp(self):
        """测试不提供时间戳初始化事件"""
        event = Event(event_type="TEST")
        
        assert event.event_type == "TEST"
        assert isinstance(event.timestamp, datetime)
        assert event.timestamp.tzinfo is not None  # 应该有时区信息
    
    def test_event_string_representation(self):
        """测试事件的字符串表示"""
        event = Event(event_type="TEST", timestamp=self.timestamp)
        string_repr = str(event)
        
        assert "TEST" in string_repr
        assert str(self.timestamp) in string_repr
    
    def test_event_additional_attributes(self):
        """测试事件的额外属性"""
        event = Event(event_type="TEST", timestamp=self.timestamp, extra_field="value")
        
        assert hasattr(event, "extra_field")
        assert event.extra_field == "value"

class TestEventType:
    """测试事件类型枚举"""
    
    def test_event_type_values(self):
        """测试事件类型枚举值"""
        assert EventType.MARKET.value == "MARKET"
        assert EventType.SIGNAL.value == "SIGNAL"
        assert EventType.ORDER.value == "ORDER"
        assert EventType.FILL.value == "FILL"
    
    def test_event_type_comparison(self):
        """测试事件类型比较"""
        assert EventType.MARKET != EventType.SIGNAL
        assert EventType.ORDER != EventType.FILL
        
        # 与字符串值比较
        assert EventType.MARKET.value == "MARKET"

class TestMarketEvent:
    """测试市场事件类"""
    
    def setup_method(self):
        """测试前设置"""
        self.symbol = "000001.XSHE"
        self.timestamp = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.open_price = 10.0
        self.high_price = 11.0
        self.low_price = 9.5
        self.close_price = 10.5
        self.volume = 1000
    
    def test_market_event_initialization(self):
        """测试市场事件初始化"""
        market_event = MarketEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume
        )
        
        assert market_event.event_type == "MARKET"
        assert market_event.symbol == self.symbol
        assert market_event.timestamp == self.timestamp
        assert market_event.open_price == self.open_price
        assert market_event.high_price == self.high_price
        assert market_event.low_price == self.low_price
        assert market_event.close_price == self.close_price
        assert market_event.volume == self.volume
        assert market_event.additional_data == {}
    
    def test_market_event_with_additional_data(self):
        """测试带有额外数据的市场事件"""
        additional_data = {"vwap": 10.2, "turnover": 50000}
        
        market_event = MarketEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
            additional_data=additional_data
        )
        
        assert market_event.additional_data == additional_data
        assert market_event.additional_data["vwap"] == 10.2
        assert market_event.additional_data["turnover"] == 50000
    
    def test_market_event_string_representation(self):
        """测试市场事件的字符串表示"""
        market_event = MarketEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume
        )
        
        string_repr = str(market_event)
        assert "MARKET" in string_repr
        assert self.symbol in string_repr
        assert str(self.close_price) in string_repr

class TestSignalEvent:
    """测试信号事件类"""
    
    def setup_method(self):
        """测试前设置"""
        self.symbol = "000001.XSHE"
        self.timestamp = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    def test_signal_event_long(self):
        """测试多头信号事件"""
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type="LONG",
            direction=1,
            strength=0.8
        )
        
        assert signal_event.event_type == "SIGNAL"
        assert signal_event.symbol == self.symbol
        assert signal_event.timestamp == self.timestamp
        assert signal_event.signal_type == "LONG"
        assert signal_event.direction == 1
        assert signal_event.strength == 0.8
        assert signal_event.additional_data == {}
    
    def test_signal_event_short(self):
        """测试空头信号事件"""
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type="SHORT",
            direction=-1,
            strength=0.5
        )
        
        assert signal_event.event_type == "SIGNAL"
        assert signal_event.symbol == self.symbol
        assert signal_event.signal_type == "SHORT"
        assert signal_event.direction == -1
        assert signal_event.strength == 0.5
    
    def test_signal_event_exit(self):
        """测试平仓信号事件"""
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type="EXIT",
            direction=0,
            strength=1.0
        )
        
        assert signal_event.event_type == "SIGNAL"
        assert signal_event.symbol == self.symbol
        assert signal_event.signal_type == "EXIT"
        assert signal_event.direction == 0
        assert signal_event.strength == 1.0
    
    def test_signal_event_with_additional_data(self):
        """测试带有额外数据的信号事件"""
        additional_data = {"indicator_value": 1.5, "confidence": 0.9}
        
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type="LONG",
            direction=1,
            strength=0.8,
            additional_data=additional_data
        )
        
        assert signal_event.additional_data == additional_data
        assert signal_event.additional_data["indicator_value"] == 1.5
        assert signal_event.additional_data["confidence"] == 0.9
    
    def test_signal_event_string_representation(self):
        """测试信号事件的字符串表示"""
        signal_event = SignalEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            signal_type="LONG",
            direction=1,
            strength=0.8
        )
        
        string_repr = str(signal_event)
        assert "SIGNAL" in string_repr
        assert self.symbol in string_repr
        assert "LONG" in string_repr

class TestOrderEvent:
    """测试订单事件类"""
    
    def setup_method(self):
        """测试前设置"""
        self.symbol = "000001.XSHE"
        self.timestamp = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.quantity = 100
        self.price = 10.5
        self.order_id = "test_order_1"
    
    def test_order_direction_enum(self):
        """测试订单方向枚举"""
        assert OrderDirection.BUY.value == 1
        assert OrderDirection.SELL.value == -1
    
    def test_order_type_enum(self):
        """测试订单类型枚举"""
        assert OrderType.MARKET.value == "MKT"
        assert OrderType.LIMIT.value == "LMT"
        assert OrderType.STOP.value == "STOP"
        assert OrderType.STOP_LIMIT.value == "STOP_LMT"
    
    def test_order_event_with_enum_direction(self):
        """测试使用枚举方向的订单事件"""
        # 测试BUY方向
        buy_order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.MARKET,
            quantity=self.quantity,
            direction=OrderDirection.BUY,
            price=self.price,
            order_id=self.order_id
        )
        
        assert buy_order.event_type == "ORDER"
        assert buy_order.symbol == self.symbol
        assert buy_order.timestamp == self.timestamp
        assert buy_order.order_type == "MKT"
        assert buy_order.quantity == self.quantity
        assert buy_order.direction == 1
        assert buy_order.original_direction_enum == OrderDirection.BUY
        assert buy_order.price == self.price
        assert buy_order.order_id == self.order_id
        
        # 测试SELL方向
        sell_order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.LIMIT,
            quantity=self.quantity,
            direction=OrderDirection.SELL,
            price=self.price,
            order_id=self.order_id
        )
        
        assert sell_order.order_type == "LMT"
        assert sell_order.direction == -1
        assert sell_order.original_direction_enum == OrderDirection.SELL
    
    def test_order_event_with_int_direction(self):
        """测试使用整数方向的订单事件"""
        # 测试买入方向 (1)
        buy_order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.MARKET,
            quantity=self.quantity,
            direction=1,
            price=self.price,
            order_id=self.order_id
        )
        
        assert buy_order.direction == 1
        assert buy_order.original_direction_enum == OrderDirection.BUY
        
        # 测试卖出方向 (-1)
        sell_order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.LIMIT,
            quantity=self.quantity,
            direction=-1,
            price=self.price,
            order_id=self.order_id
        )
        
        assert sell_order.direction == -1
        assert sell_order.original_direction_enum == OrderDirection.SELL
    
    def test_order_event_with_string_order_type(self):
        """测试使用字符串订单类型的订单事件"""
        order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type="STOP",
            quantity=self.quantity,
            direction=1,
            price=self.price,
            order_id=self.order_id
        )
        
        assert order.order_type == "STOP"
    
    def test_order_event_without_optional_fields(self):
        """测试不提供可选字段的订单事件"""
        order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.MARKET,
            quantity=self.quantity,
            direction=1
        )
        
        assert order.price is None
        assert order.order_id is None
        assert order.additional_data == {}
    
    def test_order_event_with_additional_data(self):
        """测试带有额外数据的订单事件"""
        additional_data = {"priority": "high", "strategy_id": "trend_001"}
        
        order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.MARKET,
            quantity=self.quantity,
            direction=1,
            additional_data=additional_data
        )
        
        assert order.additional_data == additional_data
        assert order.additional_data["priority"] == "high"
        assert order.additional_data["strategy_id"] == "trend_001"
    
    def test_order_event_string_representation(self):
        """测试订单事件的字符串表示"""
        order = OrderEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            order_type=OrderType.MARKET,
            quantity=self.quantity,
            direction=1,
            price=self.price
        )
        
        string_repr = str(order)
        assert "ORDER" in string_repr
        assert self.symbol in string_repr
        assert "MKT" in string_repr
        assert str(self.quantity) in string_repr

class TestFillEvent:
    """测试成交事件类"""
    
    def setup_method(self):
        """测试前设置"""
        self.symbol = "000001.XSHE"
        self.timestamp = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.quantity = 100
        self.fill_price = 10.5
        self.commission = 5.0
        self.order_id = "test_order_1"
    
    def test_fill_event_with_enum_direction(self):
        """测试使用枚举方向的成交事件"""
        # 测试BUY方向
        buy_fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=OrderDirection.BUY,
            fill_price=self.fill_price,
            commission=self.commission,
            order_id=self.order_id
        )
        
        assert buy_fill.event_type == "FILL"
        assert buy_fill.symbol == self.symbol
        assert buy_fill.timestamp == self.timestamp
        assert buy_fill.quantity == self.quantity
        assert buy_fill.direction == 1
        assert buy_fill.original_direction_enum == OrderDirection.BUY
        assert buy_fill.fill_price == self.fill_price
        assert buy_fill.commission == self.commission
        assert buy_fill.order_id == self.order_id
        
        # 测试SELL方向
        sell_fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=OrderDirection.SELL,
            fill_price=self.fill_price,
            commission=self.commission,
            order_id=self.order_id
        )
        
        assert sell_fill.direction == -1
        assert sell_fill.original_direction_enum == OrderDirection.SELL
    
    def test_fill_event_with_int_direction(self):
        """测试使用整数方向的成交事件"""
        # 测试买入方向 (1)
        buy_fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=1,
            fill_price=self.fill_price,
            commission=self.commission,
            order_id=self.order_id
        )
        
        assert buy_fill.direction == 1
        assert buy_fill.original_direction_enum == OrderDirection.BUY
        
        # 测试卖出方向 (-1)
        sell_fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=-1,
            fill_price=self.fill_price,
            commission=self.commission,
            order_id=self.order_id
        )
        
        assert sell_fill.direction == -1
        assert sell_fill.original_direction_enum == OrderDirection.SELL
    
    def test_fill_event_with_additional_fields(self):
        """测试带有额外字段的成交事件"""
        fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=1,
            fill_price=self.fill_price,
            commission=self.commission,
            order_id=self.order_id,
            exchange="SSE",
            slippage=0.01
        )
        
        assert fill.exchange == "SSE"
        assert fill.slippage == 0.01
    
    def test_fill_event_without_optional_fields(self):
        """测试不提供可选字段的成交事件"""
        fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=1,
            fill_price=self.fill_price
        )
        
        assert fill.commission == 0.0
        assert fill.order_id is None
        assert fill.exchange is None
        assert fill.slippage is None
        assert fill.additional_data == {}
    
    def test_fill_event_with_additional_data(self):
        """测试带有额外数据的成交事件"""
        additional_data = {"broker_id": "broker_001", "execution_time": 0.05}
        
        fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=1,
            fill_price=self.fill_price,
            additional_data=additional_data
        )
        
        assert fill.additional_data == additional_data
        assert fill.additional_data["broker_id"] == "broker_001"
        assert fill.additional_data["execution_time"] == 0.05
    
    def test_fill_event_string_representation(self):
        """测试成交事件的字符串表示"""
        fill = FillEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            quantity=self.quantity,
            direction=1,
            fill_price=self.fill_price,
            commission=self.commission
        )
        
        string_repr = str(fill)
        assert "FILL" in string_repr
        assert self.symbol in string_repr
        assert str(self.quantity) in string_repr
        assert str(self.fill_price) in string_repr


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 