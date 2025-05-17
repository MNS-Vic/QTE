"""
简单执行处理器测试
测试订单执行和成交回报功能
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pandas as pd

from qte.core.events import OrderEvent, FillEvent, EventType, OrderDirection, OrderType
from qte.core.event_loop import EventLoop
from qte.execution.simple_execution_handler import SimpleExecutionHandler

class TestSimpleExecutionHandler:
    """测试简单执行处理器"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环的模拟对象
        self.mock_event_loop = MagicMock(spec=EventLoop)
        
        # 创建执行处理器
        self.execution_handler = SimpleExecutionHandler(
            event_loop=self.mock_event_loop,
            commission_rate=0.0003  # 万分之三佣金
        )
        
        # 设置一些测试用的价格
        self.execution_handler.latest_prices = {
            "000001": 10.0,
            "600000": 20.0
        }
    
    def test_initialization(self):
        """测试初始化功能"""
        assert self.execution_handler.commission_rate == 0.0003
        assert isinstance(self.execution_handler.latest_prices, dict)
        
        # 验证事件处理器注册
        self.mock_event_loop.register_handler.assert_any_call(EventType.ORDER, self.execution_handler.on_order)
        self.mock_event_loop.register_handler.assert_any_call(EventType.MARKET, self.execution_handler.on_market)
    
    def test_on_market_update_price(self):
        """测试市场事件更新价格"""
        # 创建市场事件
        market_event = MagicMock()
        market_event.symbol = "000002"
        market_event.price = 15.0
        
        # 处理市场事件
        self.execution_handler.on_market(market_event)
        
        # 验证价格更新
        assert self.execution_handler.latest_prices["000002"] == 15.0
    
    def test_on_market_use_close_price(self):
        """测试市场事件使用收盘价"""
        # 创建市场事件（没有price字段，只有close_price）
        market_event = MagicMock()
        market_event.symbol = "000003"
        market_event.price = None
        market_event.close_price = 25.0
        
        # 处理市场事件
        self.execution_handler.on_market(market_event)
        
        # 验证价格更新
        assert self.execution_handler.latest_prices["000003"] == 25.0
    
    def test_on_market_ignore_zero_price(self):
        """测试市场事件忽略零价格"""
        # 创建市场事件（价格为0）
        market_event = MagicMock()
        market_event.symbol = "000004"
        market_event.price = 0.0
        market_event.close_price = 0.0
        
        # 处理市场事件
        self.execution_handler.on_market(market_event)
        
        # 验证价格未更新
        assert "000004" not in self.execution_handler.latest_prices
    
    def test_on_order_buy(self):
        """测试处理买入订单"""
        # 创建买入订单事件
        order_event = OrderEvent(
            order_id="test_buy_1",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 处理订单
        self.execution_handler.on_order(order_event)
        
        # 验证成交事件
        self.mock_event_loop.put_event.assert_called_once()
        fill_event = self.mock_event_loop.put_event.call_args[0][0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id == "test_buy_1"
        assert fill_event.symbol == "000001"
        assert fill_event.direction == 1  # OrderDirection.BUY的值
        assert fill_event.quantity == 100
        assert fill_event.fill_price == 10.0
        assert fill_event.commission == pytest.approx(10.0 * 100 * 0.0003)
    
    def test_on_order_sell(self):
        """测试处理卖出订单"""
        # 创建卖出订单事件
        order_event = OrderEvent(
            order_id="test_sell_1",
            symbol="600000",
            timestamp=datetime.now(),
            direction=OrderDirection.SELL,
            quantity=50,
            order_type=OrderType.MARKET
        )
        
        # 处理订单
        self.execution_handler.on_order(order_event)
        
        # 验证成交事件
        self.mock_event_loop.put_event.assert_called_once()
        fill_event = self.mock_event_loop.put_event.call_args[0][0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id == "test_sell_1"
        assert fill_event.symbol == "600000"
        assert fill_event.direction == -1  # OrderDirection.SELL的值
        assert fill_event.quantity == 50
        assert fill_event.fill_price == 20.0
        assert fill_event.commission == pytest.approx(20.0 * 50 * 0.0003)
    
    def test_on_order_no_price(self):
        """测试处理没有价格的订单"""
        # 创建订单事件（标的没有价格）
        order_event = OrderEvent(
            order_id="test_no_price",
            symbol="000099",  # 未知标的
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 处理订单
        self.execution_handler.on_order(order_event)
        
        # 验证没有生成成交事件
        self.mock_event_loop.put_event.assert_not_called()
    
    def test_get_fill_price(self):
        """测试获取成交价格"""
        # 测试已知标的
        price = self.execution_handler._get_fill_price("000001")
        assert price == 10.0
        
        # 测试未知标的
        price = self.execution_handler._get_fill_price("unknown")
        assert price == 0.0
    
    def test_calculate_commission(self):
        """测试计算佣金"""
        commission = self.execution_handler._calculate_commission(100, 10.0)
        assert commission == pytest.approx(100 * 10.0 * 0.0003)
        
        # 测试负数数量（应该取绝对值）
        commission = self.execution_handler._calculate_commission(-50, 20.0)
        assert commission == pytest.approx(50 * 20.0 * 0.0003)
    
    def test_on_order_generates_unique_id(self):
        """测试处理没有订单ID的订单"""
        # 创建没有订单ID的订单事件
        order_event = OrderEvent(
            order_id=None,
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 处理订单
        self.execution_handler.on_order(order_event)
        
        # 验证成交事件生成了唯一ID
        self.mock_event_loop.put_event.assert_called_once()
        fill_event = self.mock_event_loop.put_event.call_args[0][0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id is not None
        assert fill_event.order_id.startswith("simfill_")
    
    # 以下是集成测试（可选，因为需要更多的模拟）
    
    def test_integration_with_event_loop(self):
        """测试与事件循环的集成"""
        # 使用真实事件循环而不是模拟
        real_event_loop = EventLoop()
        
        # 创建执行处理器
        execution_handler = SimpleExecutionHandler(
            event_loop=real_event_loop,
            commission_rate=0.0003
        )
        
        # 设置价格
        execution_handler.latest_prices = {"000001": 10.0}
        
        # 创建一个接收成交事件的处理器
        fill_events = []
        
        def on_fill(event):
            fill_events.append(event)
        
        # 注册成交事件处理器
        real_event_loop.register_handler(EventType.FILL, on_fill)
        
        # 创建订单事件
        order_event = OrderEvent(
            order_id="test_integration",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 添加订单事件到事件循环
        real_event_loop.put_event(order_event)
        
        # 模拟事件循环处理事件
        # 处理所有事件队列中的事件
        while not real_event_loop.event_queue.empty():
            real_event_loop._process_next_event()
        
        # 验证成交事件
        assert len(fill_events) == 1
        fill_event = fill_events[0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id == "test_integration"
        assert fill_event.symbol == "000001"
        assert fill_event.direction == 1  # OrderDirection.BUY的值
        assert fill_event.quantity == 100
        assert fill_event.fill_price == 10.0
        assert fill_event.commission == pytest.approx(10.0 * 100 * 0.0003) 