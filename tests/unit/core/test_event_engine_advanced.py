#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EventEngine高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
import datetime
from unittest.mock import Mock, patch
from queue import Queue

from qte.core.event_engine import (
    EventType, Event, MarketEvent, SignalEvent, OrderEvent, FillEvent, 
    AccountEvent, OrderType, EventEngine, EventDrivenBacktester
)


class TestEventEngineAdvanced:
    """EventEngine高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.engine = EventEngine()
    
    def test_event_base_class(self):
        """测试事件基类"""
        # Red: 编写失败的测试
        event = Event(EventType.CUSTOM)
        
        # 验证事件属性
        assert event.event_type == EventType.CUSTOM
        assert isinstance(event.timestamp, datetime.datetime)
        assert isinstance(event.event_id, str)
        assert len(event.event_id) == 8  # UUID前8位
    
    def test_market_event(self):
        """测试市场数据事件"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        data = {
            'open': 150.0,
            'high': 155.0,
            'low': 149.0,
            'close': 152.0,
            'volume': 1000000
        }
        
        event = MarketEvent(timestamp, symbol, data)
        
        # 验证事件属性
        assert event.event_type == EventType.MARKET
        assert event.timestamp == timestamp
        assert event.symbol == symbol
        assert event.data == data
    
    def test_signal_event(self):
        """测试信号事件"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        direction = 1
        strength = 0.8
        
        event = SignalEvent(timestamp, symbol, direction, strength)
        
        # 验证事件属性
        assert event.event_type == EventType.SIGNAL
        assert event.timestamp == timestamp
        assert event.symbol == symbol
        assert event.direction == direction
        assert event.strength == strength
    
    def test_signal_event_default_strength(self):
        """测试信号事件默认强度"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        direction = -1
        
        event = SignalEvent(timestamp, symbol, direction)
        
        # 验证默认强度
        assert event.strength == 1.0
    
    def test_order_event(self):
        """测试订单事件"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_type = OrderType.LIMIT
        quantity = 100.0
        direction = 1
        limit_price = 150.0
        stop_price = 145.0
        
        event = OrderEvent(timestamp, symbol, order_type, quantity, direction, limit_price, stop_price)
        
        # 验证事件属性
        assert event.event_type == EventType.ORDER
        assert event.timestamp == timestamp
        assert event.symbol == symbol
        assert event.order_type == order_type
        assert event.quantity == quantity
        assert event.direction == direction
        assert event.limit_price == limit_price
        assert event.stop_price == stop_price
        assert isinstance(event.order_id, str)
    
    def test_order_event_optional_params(self):
        """测试订单事件可选参数"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_type = OrderType.MARKET
        quantity = 100.0
        direction = -1
        
        event = OrderEvent(timestamp, symbol, order_type, quantity, direction)
        
        # 验证可选参数默认值
        assert event.limit_price is None
        assert event.stop_price is None
    
    def test_fill_event(self):
        """测试成交事件"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_id = "order_123"
        quantity = 100.0
        direction = 1
        fill_price = 151.0
        commission = 1.5
        
        event = FillEvent(timestamp, symbol, order_id, quantity, direction, fill_price, commission)
        
        # 验证事件属性
        assert event.event_type == EventType.FILL
        assert event.timestamp == timestamp
        assert event.symbol == symbol
        assert event.order_id == order_id
        assert event.quantity == quantity
        assert event.direction == direction
        assert event.fill_price == fill_price
        assert event.commission == commission
    
    def test_fill_event_default_commission(self):
        """测试成交事件默认佣金"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_id = "order_123"
        quantity = 100.0
        direction = -1
        fill_price = 151.0
        
        event = FillEvent(timestamp, symbol, order_id, quantity, direction, fill_price)
        
        # 验证默认佣金
        assert event.commission == 0.0
    
    def test_account_event(self):
        """测试账户事件"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        balance = 100000.0
        available = 95000.0
        margin = 5000.0
        
        event = AccountEvent(timestamp, balance, available, margin)
        
        # 验证事件属性
        assert event.event_type == EventType.ACCOUNT
        assert event.timestamp == timestamp
        assert event.balance == balance
        assert event.available == available
        assert event.margin == margin
    
    def test_account_event_default_margin(self):
        """测试账户事件默认保证金"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        balance = 100000.0
        available = 100000.0
        
        event = AccountEvent(timestamp, balance, available)
        
        # 验证默认保证金
        assert event.margin == 0.0
    
    def test_event_engine_init(self):
        """测试事件引擎初始化"""
        # Red: 编写失败的测试
        engine = EventEngine()
        
        # 验证初始化状态
        assert isinstance(engine.queue, Queue)
        assert isinstance(engine.handlers, dict)
        assert len(engine.handlers) == len(EventType)
        
        # 验证每个事件类型都有处理器列表
        for event_type in EventType:
            assert event_type in engine.handlers
            assert isinstance(engine.handlers[event_type], list)
            assert len(engine.handlers[event_type]) == 0
    
    def test_register_handler(self):
        """测试注册事件处理器"""
        # Red: 编写失败的测试
        handler = Mock()
        
        # 注册处理器
        self.engine.register_handler(EventType.MARKET, handler)
        
        # 验证处理器被注册
        assert handler in self.engine.handlers[EventType.MARKET]
        assert len(self.engine.handlers[EventType.MARKET]) == 1
    
    def test_register_multiple_handlers(self):
        """测试注册多个事件处理器"""
        # Red: 编写失败的测试
        handler1 = Mock()
        handler2 = Mock()
        
        # 注册多个处理器
        self.engine.register_handler(EventType.MARKET, handler1)
        self.engine.register_handler(EventType.MARKET, handler2)
        
        # 验证多个处理器被注册
        assert handler1 in self.engine.handlers[EventType.MARKET]
        assert handler2 in self.engine.handlers[EventType.MARKET]
        assert len(self.engine.handlers[EventType.MARKET]) == 2
    
    def test_unregister_handler(self):
        """测试注销事件处理器"""
        # Red: 编写失败的测试
        handler = Mock()
        
        # 先注册处理器
        self.engine.register_handler(EventType.SIGNAL, handler)
        assert handler in self.engine.handlers[EventType.SIGNAL]
        
        # 注销处理器
        self.engine.unregister_handler(EventType.SIGNAL, handler)
        
        # 验证处理器被注销
        assert handler not in self.engine.handlers[EventType.SIGNAL]
        assert len(self.engine.handlers[EventType.SIGNAL]) == 0
    
    def test_unregister_nonexistent_handler(self):
        """测试注销不存在的处理器"""
        # Red: 编写失败的测试
        handler = Mock()
        
        # 尝试注销不存在的处理器（应该不抛出异常）
        self.engine.unregister_handler(EventType.ORDER, handler)
        
        # 验证没有异常抛出
        assert len(self.engine.handlers[EventType.ORDER]) == 0
    
    def test_put_event(self):
        """测试添加事件到队列"""
        # Red: 编写失败的测试
        event = Event(EventType.CUSTOM)
        
        # 添加事件
        self.engine.put(event)
        
        # 验证事件被添加到队列
        assert not self.engine.queue.empty()
        assert self.engine.queue.qsize() == 1
    
    def test_process_empty_queue(self):
        """测试处理空队列"""
        # Red: 编写失败的测试
        # 处理空队列
        result = self.engine.process()
        
        # 验证返回False
        assert result is False
    
    def test_process_single_event(self):
        """测试处理单个事件"""
        # Red: 编写失败的测试
        handler = Mock()
        event = Event(EventType.CUSTOM)
        
        # 注册处理器并添加事件
        self.engine.register_handler(EventType.CUSTOM, handler)
        self.engine.put(event)
        
        # 处理事件
        result = self.engine.process()
        
        # 验证事件被处理
        assert result is True
        assert handler.called
        handler.assert_called_once_with(event)
        assert self.engine.queue.empty()
    
    def test_process_multiple_handlers(self):
        """测试处理多个处理器"""
        # Red: 编写失败的测试
        handler1 = Mock()
        handler2 = Mock()
        event = Event(EventType.MARKET)
        
        # 注册多个处理器并添加事件
        self.engine.register_handler(EventType.MARKET, handler1)
        self.engine.register_handler(EventType.MARKET, handler2)
        self.engine.put(event)
        
        # 处理事件
        result = self.engine.process()
        
        # 验证所有处理器都被调用
        assert result is True
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
    
    def test_process_all_events(self):
        """测试处理所有事件"""
        # Red: 编写失败的测试
        handler = Mock()
        event1 = Event(EventType.SIGNAL)
        event2 = Event(EventType.SIGNAL)
        event3 = Event(EventType.SIGNAL)
        
        # 注册处理器并添加多个事件
        self.engine.register_handler(EventType.SIGNAL, handler)
        self.engine.put(event1)
        self.engine.put(event2)
        self.engine.put(event3)
        
        # 处理所有事件
        count = self.engine.process_all()
        
        # 验证所有事件被处理
        assert count == 3
        assert handler.call_count == 3
        assert self.engine.queue.empty()
    
    def test_clear_queue(self):
        """测试清空事件队列"""
        # Red: 编写失败的测试
        event1 = Event(EventType.ORDER)
        event2 = Event(EventType.FILL)
        
        # 添加事件
        self.engine.put(event1)
        self.engine.put(event2)
        assert self.engine.queue.qsize() == 2
        
        # 清空队列
        self.engine.clear()
        
        # 验证队列被清空
        assert self.engine.queue.empty()
        assert self.engine.queue.qsize() == 0


class TestEventDrivenBacktesterAdvanced:
    """EventDrivenBacktester高级功能测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.backtester = EventDrivenBacktester(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage=0.001
        )

    def test_backtester_init(self):
        """测试回测引擎初始化"""
        # Red: 编写失败的测试
        backtester = EventDrivenBacktester(
            initial_capital=50000.0,
            commission_rate=0.002,
            slippage=0.005
        )

        # 验证初始化参数
        assert backtester.initial_capital == 50000.0
        assert backtester.current_capital == 50000.0
        assert backtester.commission_rate == 0.002
        assert backtester.slippage == 0.005

        # 验证初始状态
        assert isinstance(backtester.event_engine, EventEngine)
        assert backtester.data is None
        assert backtester.data_symbols == []
        assert backtester.current_date is None
        assert backtester.current_bar_index == 0
        assert backtester.is_backtest_running is False

        # 验证集合初始化
        assert isinstance(backtester.strategies, list)
        assert isinstance(backtester.positions, dict)
        assert isinstance(backtester.open_orders, dict)
        assert isinstance(backtester.equity_history, list)
        assert isinstance(backtester.transaction_history, list)

        assert len(backtester.strategies) == 0
        assert len(backtester.positions) == 0
        assert len(backtester.open_orders) == 0
        assert len(backtester.equity_history) == 0
        assert len(backtester.transaction_history) == 0

    def test_register_handlers(self):
        """测试事件处理器注册"""
        # Red: 编写失败的测试
        # 验证处理器已注册
        market_handlers = self.backtester.event_engine.handlers[EventType.MARKET]
        signal_handlers = self.backtester.event_engine.handlers[EventType.SIGNAL]
        order_handlers = self.backtester.event_engine.handlers[EventType.ORDER]
        fill_handlers = self.backtester.event_engine.handlers[EventType.FILL]

        assert len(market_handlers) == 1
        assert len(signal_handlers) == 1
        assert len(order_handlers) == 1
        assert len(fill_handlers) == 1

    def test_on_market_event(self):
        """测试市场数据事件处理"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        data = {'close': 150.0, 'volume': 1000}

        # Mock策略
        mock_strategy = Mock()
        self.backtester.strategies.append(mock_strategy)

        # Mock计算权益方法
        with patch.object(self.backtester, 'calculate_equity', return_value=105000.0):
            # 创建并处理市场事件
            event = MarketEvent(timestamp, symbol, data)
            self.backtester._on_market_event(event)

            # 验证策略被调用
            mock_strategy.on_market_data.assert_called_once_with(event)

            # 验证当前时间更新
            assert self.backtester.current_date == timestamp

            # 验证权益历史记录
            assert len(self.backtester.equity_history) == 1
            equity_record = self.backtester.equity_history[0]
            assert equity_record['timestamp'] == timestamp
            assert equity_record['equity'] == 105000.0
            assert equity_record['cash'] == 100000.0

    def test_on_signal_event_no_market_data(self):
        """测试信号事件处理 - 无市场数据"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        direction = 1
        strength = 0.8

        # Mock获取市场数据返回None
        with patch.object(self.backtester, '_get_latest_market_data', return_value=None):
            # 创建并处理信号事件
            event = SignalEvent(timestamp, symbol, direction, strength)
            self.backtester._on_signal_event(event)

            # 验证没有订单生成
            assert len(self.backtester.open_orders) == 0

    def test_on_signal_event_zero_quantity(self):
        """测试信号事件处理 - 零数量"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        direction = 1
        strength = 0.8

        # Mock获取市场数据和计算仓位大小
        with patch.object(self.backtester, '_get_latest_market_data', return_value={'close': 150.0}), \
             patch.object(self.backtester, '_calculate_position_size', return_value=0):

            # 创建并处理信号事件
            event = SignalEvent(timestamp, symbol, direction, strength)
            self.backtester._on_signal_event(event)

            # 验证没有订单生成
            assert len(self.backtester.open_orders) == 0

    def test_on_signal_event_success(self):
        """测试信号事件处理 - 成功"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        direction = 1
        strength = 0.8

        # Mock获取市场数据和计算仓位大小
        with patch.object(self.backtester, '_get_latest_market_data', return_value={'close': 150.0}), \
             patch.object(self.backtester, '_calculate_position_size', return_value=100):

            # Mock事件引擎put方法
            with patch.object(self.backtester.event_engine, 'put') as mock_put:
                # 创建并处理信号事件
                event = SignalEvent(timestamp, symbol, direction, strength)
                self.backtester._on_signal_event(event)

                # 验证订单事件被发送
                mock_put.assert_called_once()
                order_event = mock_put.call_args[0][0]
                assert isinstance(order_event, OrderEvent)
                assert order_event.symbol == symbol
                assert order_event.order_type == OrderType.MARKET
                assert order_event.quantity == 100
                assert order_event.direction == 1

    def test_on_order_event_market_order(self):
        """测试订单事件处理 - 市价单"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_type = OrderType.MARKET
        quantity = 100.0
        direction = 1

        # Mock执行市价单方法
        with patch.object(self.backtester, '_execute_market_order') as mock_execute:
            # 创建并处理订单事件
            event = OrderEvent(timestamp, symbol, order_type, quantity, direction)
            self.backtester._on_order_event(event)

            # 验证订单被记录
            assert event.order_id in self.backtester.open_orders
            assert self.backtester.open_orders[event.order_id] == event

            # 验证市价单被执行
            mock_execute.assert_called_once_with(event)

    def test_on_order_event_limit_order(self):
        """测试订单事件处理 - 限价单"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_type = OrderType.LIMIT
        quantity = 100.0
        direction = 1
        limit_price = 150.0

        # 创建并处理订单事件
        event = OrderEvent(timestamp, symbol, order_type, quantity, direction, limit_price)
        self.backtester._on_order_event(event)

        # 验证订单被记录但不执行
        assert event.order_id in self.backtester.open_orders
        assert self.backtester.open_orders[event.order_id] == event

    def test_on_fill_event_buy(self):
        """测试成交事件处理 - 买入"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_id = "order_123"
        quantity = 100.0
        direction = 1  # 买入
        fill_price = 150.0
        commission = 15.0

        # 添加订单到未完成订单
        mock_order = Mock()
        self.backtester.open_orders[order_id] = mock_order

        # 创建并处理成交事件
        event = FillEvent(timestamp, symbol, order_id, quantity, direction, fill_price, commission)
        self.backtester._on_fill_event(event)

        # 验证持仓更新
        assert symbol in self.backtester.positions
        assert self.backtester.positions[symbol] == 100.0

        # 验证资金更新
        expected_capital = 100000.0 - (100.0 * 150.0 + 15.0)  # 初始资金 - (成交金额 + 佣金)
        assert self.backtester.current_capital == expected_capital

        # 验证交易记录
        assert len(self.backtester.transaction_history) == 1
        transaction = self.backtester.transaction_history[0]
        assert transaction['symbol'] == symbol
        assert transaction['direction'] == 'BUY'
        assert transaction['quantity'] == quantity
        assert transaction['price'] == fill_price
        assert transaction['commission'] == commission

        # 验证订单从未完成订单中移除
        assert order_id not in self.backtester.open_orders

    def test_on_fill_event_sell(self):
        """测试成交事件处理 - 卖出"""
        # Red: 编写失败的测试
        timestamp = datetime.datetime.now()
        symbol = "AAPL"
        order_id = "order_456"
        quantity = 50.0
        direction = -1  # 卖出
        fill_price = 155.0
        commission = 7.75

        # 设置初始持仓
        self.backtester.positions[symbol] = 100.0

        # 添加订单到未完成订单
        mock_order = Mock()
        self.backtester.open_orders[order_id] = mock_order

        # 创建并处理成交事件
        event = FillEvent(timestamp, symbol, order_id, quantity, direction, fill_price, commission)
        self.backtester._on_fill_event(event)

        # 验证持仓更新
        assert self.backtester.positions[symbol] == 50.0  # 100 - 50

        # 验证资金更新
        expected_capital = 100000.0 + (50.0 * 155.0 - 7.75)  # 初始资金 + (成交金额 - 佣金)
        assert self.backtester.current_capital == expected_capital

        # 验证交易记录
        assert len(self.backtester.transaction_history) == 1
        transaction = self.backtester.transaction_history[0]
        assert transaction['direction'] == 'SELL'
