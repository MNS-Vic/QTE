"""
执行模块集成测试
测试执行处理器、经纪商与事件循环的集成功能
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from qte.core.events import OrderEvent, FillEvent, MarketEvent, EventType, OrderDirection, OrderType
from qte.core.event_loop import EventLoop
from qte.execution.simple_execution_handler import SimpleExecutionHandler
from qte.execution.basic_broker import BasicBroker, FixedPercentageCommission, SimpleRandomSlippage

class TestExecutionIntegration:
    """测试执行处理器与事件循环的集成"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环
        self.event_loop = EventLoop()
        
        # 创建回调队列并注册回调，必须在创建执行处理器前完成
        self.fill_events = []
        self.event_loop.register_handler(EventType.FILL, self.on_fill)
        
        # 创建简单执行处理器
        self.execution_handler = SimpleExecutionHandler(
            event_loop=self.event_loop,
            commission_rate=0.0003  # 万分之三佣金
        )
        
        # 设置测试数据
        self.test_price = 10.0
        self.test_symbol = "000001"
        
        # 设置最新价格
        self.execution_handler.latest_prices = {self.test_symbol: self.test_price}
    
    def on_fill(self, event):
        """处理成交事件"""
        self.fill_events.append(event)
    
    def test_market_data_to_order_to_fill(self):
        """测试市场数据 -> 订单 -> 成交的完整流程"""
        # 创建市场事件
        market_event = MarketEvent(
            symbol=self.test_symbol,
            timestamp=datetime.now(),
            open_price=9.8,
            high_price=10.2,
            low_price=9.7,
            close_price=10.1,
            volume=10000
        )
        
        # 添加市场事件到事件循环
        self.event_loop.put_event(market_event)
        
        # 处理市场事件
        self.event_loop.run(max_events=1)
        
        # 验证最新价格已更新
        assert self.execution_handler.latest_prices[self.test_symbol] == 10.1
        
        # 创建订单事件
        order_event = OrderEvent(
            order_id="test_integration_order",
            symbol=self.test_symbol,
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 添加订单事件到事件循环
        self.event_loop.put_event(order_event)
        
        # 处理所有事件，包括ORDER事件和由其产生的FILL事件
        self.event_loop.run()
        
        # 验证成交事件
        assert len(self.fill_events) == 1
        fill_event = self.fill_events[0]
        
        assert isinstance(fill_event, FillEvent)
        assert fill_event.order_id == "test_integration_order"
        assert fill_event.symbol == self.test_symbol
        assert fill_event.direction == 1  # OrderDirection.BUY的值
        assert fill_event.quantity == 100
        assert fill_event.fill_price == 10.1
        assert fill_event.commission == pytest.approx(10.1 * 100 * 0.0003)
    
    def test_multiple_orders_and_fills(self):
        """测试多个订单和成交事件"""
        # 创建多个订单事件
        order1 = OrderEvent(
            order_id="test_multi_order_1",
            symbol=self.test_symbol,
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        order2 = OrderEvent(
            order_id="test_multi_order_2",
            symbol=self.test_symbol,
            timestamp=datetime.now() + timedelta(seconds=1),
            direction=OrderDirection.SELL,
            quantity=50,
            order_type=OrderType.MARKET
        )
        
        # 添加订单事件到事件循环
        self.event_loop.put_event(order1)
        self.event_loop.put_event(order2)
        
        # 处理所有事件
        self.event_loop.run()
        
        # 验证成交事件
        assert len(self.fill_events) == 2
        
        # 验证第一个成交事件
        fill1 = self.fill_events[0]
        assert fill1.order_id == "test_multi_order_1"
        assert fill1.direction == 1  # 买入
        assert fill1.quantity == 100
        
        # 验证第二个成交事件
        fill2 = self.fill_events[1]
        assert fill2.order_id == "test_multi_order_2"
        assert fill2.direction == -1  # 卖出
        assert fill2.quantity == 50
    
    def test_market_price_update_affects_fills(self):
        """测试市场价格更新影响成交价格"""
        # 创建市场事件序列
        market_events = [
            MarketEvent(
                symbol=self.test_symbol,
                timestamp=datetime.now(),
                open_price=9.8,
                high_price=10.2,
                low_price=9.7,
                close_price=10.0,
                volume=10000
            ),
            MarketEvent(
                symbol=self.test_symbol,
                timestamp=datetime.now() + timedelta(seconds=1),
                open_price=10.0,
                high_price=10.5,
                low_price=9.9,
                close_price=10.3,
                volume=12000
            ),
            MarketEvent(
                symbol=self.test_symbol,
                timestamp=datetime.now() + timedelta(seconds=2),
                open_price=10.3,
                high_price=10.4,
                low_price=10.1,
                close_price=10.2,
                volume=11000
            )
        ]
        
        # 添加市场事件到事件循环
        for event in market_events:
            self.event_loop.put_event(event)
        
        # 处理所有市场事件
        self.event_loop.run(max_events=3)
        
        # 创建订单事件
        orders = [
            OrderEvent(
                order_id="test_price_update_1",
                symbol=self.test_symbol,
                timestamp=datetime.now() + timedelta(seconds=3),
                direction=OrderDirection.BUY,
                quantity=100,
                order_type=OrderType.MARKET
            ),
            OrderEvent(
                order_id="test_price_update_2",
                symbol=self.test_symbol,
                timestamp=datetime.now() + timedelta(seconds=4),
                direction=OrderDirection.SELL,
                quantity=50,
                order_type=OrderType.MARKET
            )
        ]
        
        # 分别添加订单并处理
        self.event_loop.put_event(orders[0])
        self.event_loop.run()  # 处理所有事件，包括ORDER事件和由其产生的FILL事件
        
        # 验证第一个成交事件使用了最后一个市场价格
        assert len(self.fill_events) == 1
        assert self.fill_events[0].fill_price == 10.2
        
        # 添加新的市场事件
        new_market_event = MarketEvent(
            symbol=self.test_symbol,
            timestamp=datetime.now() + timedelta(seconds=5),
            open_price=10.2,
            high_price=10.6,
            low_price=10.2,
            close_price=10.5,
            volume=13000
        )
        
        self.event_loop.put_event(new_market_event)
        self.event_loop.run(max_events=1)
        
        # 添加第二个订单
        self.event_loop.put_event(orders[1])
        self.event_loop.run()  # 处理所有事件，包括ORDER事件和由其产生的FILL事件
        
        # 验证第二个成交事件使用了更新后的市场价格
        assert len(self.fill_events) == 2
        assert self.fill_events[1].fill_price == 10.5


class TestBrokerIntegration:
    """测试经纪商与事件循环的集成"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环
        self.event_loop = EventLoop()
        
        # 创建回调队列并注册回调，必须在创建经纪商前完成
        self.fill_events = []
        self.event_loop.register_handler(EventType.FILL, self.on_fill)
        
        # 创建佣金和滑点模型
        self.commission_model = FixedPercentageCommission(commission_rate=0.001)
        self.slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=1.0)
        
        # 创建模拟数据提供者
        class MockDataProvider:
            def __init__(self):
                self.latest_bars = {
                    "000001": {
                        'datetime': datetime.now(),
                        'symbol': '000001',
                        'open': 10.0,
                        'high': 10.2,
                        'low': 9.8,
                        'close': 10.0,
                        'volume': 10000
                    }
                }
                
            def get_latest_bar(self, symbol):
                return self.latest_bars.get(symbol)
                
            def update_bar(self, symbol, price):
                if symbol in self.latest_bars:
                    self.latest_bars[symbol]['close'] = price
        
        self.data_provider = MockDataProvider()
        
        # 创建经纪商
        self.broker = BasicBroker(
            event_loop=self.event_loop,
            commission_model=self.commission_model,
            slippage_model=self.slippage_model,
            data_provider=self.data_provider
        )
    
    def on_fill(self, event):
        """处理成交事件"""
        self.fill_events.append(event)
    
    def test_broker_order_processing(self):
        """测试经纪商订单处理"""
        # 创建市价买单
        order = OrderEvent(
            order_id="test_broker_order",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # 提交订单到经纪商
        self.broker.submit_order(order)
        
        # 处理事件循环
        self.event_loop.run()
        
        # 验证成交事件
        assert len(self.fill_events) == 1
        fill_event = self.fill_events[0]
        
        assert fill_event.order_id == "test_broker_order"
        assert fill_event.symbol == "000001"
        assert fill_event.direction == 1  # 买入
        assert fill_event.quantity == 100
        # 买入滑点应使价格变化
        assert fill_event.fill_price == pytest.approx(9.99)  # 修正期望值
        assert fill_event.commission == pytest.approx(100 * 9.99 * 0.001)
        assert fill_event.slippage == pytest.approx(0.01)
    
    def test_broker_with_changing_prices(self):
        """测试价格变化对经纪商的影响"""
        # 提交第一个订单
        order1 = OrderEvent(
            order_id="test_broker_price_1",
            symbol="000001",
            timestamp=datetime.now(),
            direction=OrderDirection.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        self.broker.submit_order(order1)
        self.event_loop.run()
        
        # 更新价格
        self.data_provider.update_bar("000001", 10.5)
        
        # 提交第二个订单
        order2 = OrderEvent(
            order_id="test_broker_price_2",
            symbol="000001",
            timestamp=datetime.now() + timedelta(seconds=1),
            direction=OrderDirection.SELL,
            quantity=50,
            order_type=OrderType.MARKET
        )
        
        self.broker.submit_order(order2)
        self.event_loop.run()
        
        # 验证成交事件
        assert len(self.fill_events) == 2
        
        # 验证第一个成交事件
        fill1 = self.fill_events[0]
        assert fill1.fill_price == pytest.approx(9.99)  # 修正期望值
        
        # 验证第二个成交事件
        fill2 = self.fill_events[1]
        assert fill2.fill_price == pytest.approx(10.49)  # 10.5 - 0.01 (卖出滑点)
        
    def test_broker_with_multiple_orders(self):
        """测试经纪商处理多个订单"""
        # 创建多个订单
        orders = [
            OrderEvent(
                order_id=f"test_broker_multi_{i}",
                symbol="000001",
                timestamp=datetime.now() + timedelta(milliseconds=i*100),
                direction=OrderDirection.BUY if i % 2 == 0 else OrderDirection.SELL,
                quantity=100 - i*10,
                order_type=OrderType.MARKET
            )
            for i in range(5)
        ]
        
        # 提交所有订单
        for order in orders:
            self.broker.submit_order(order)
        
        # 处理事件循环
        self.event_loop.run()
        
        # 验证成交事件
        assert len(self.fill_events) == 5
        
        # 验证所有成交事件
        for i, fill in enumerate(self.fill_events):
            assert fill.order_id == f"test_broker_multi_{i}"
            assert fill.quantity == 100 - i*10
            if i % 2 == 0:
                assert fill.direction == 1  # 买入
                assert fill.fill_price == pytest.approx(9.99)  # 修正期望值
            else:
                assert fill.direction == -1  # 卖出
                assert fill.fill_price == pytest.approx(9.99)  # 修正期望值 