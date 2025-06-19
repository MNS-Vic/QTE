"""
Event Engine真实逻辑测试
专注于测试真实的业务逻辑路径，减少Mock使用，提升覆盖率
"""

import time
import threading
import queue
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

from qte.core.event_engine import (
    EventEngine, EventDrivenBacktester, EventType,
    MarketEvent, SignalEvent, OrderEvent, FillEvent, OrderType
)


class TestEventEngineRealLogic:
    """Event Engine真实逻辑测试"""
    
    def test_event_engine_full_lifecycle(self):
        """测试EventEngine的完整生命周期"""
        engine = EventEngine()

        # 1. 初始状态验证
        assert engine.queue.empty()
        # EventEngine初始化时会为所有EventType创建空列表
        assert len(engine.handlers) == len(EventType)
        
        # 2. 注册多个处理器
        processed_events = []
        
        def market_handler(event):
            processed_events.append(('market', event))
        
        def signal_handler(event):
            processed_events.append(('signal', event))
        
        def order_handler(event):
            processed_events.append(('order', event))
        
        engine.register_handler(EventType.MARKET, market_handler)
        engine.register_handler(EventType.SIGNAL, signal_handler)
        engine.register_handler(EventType.ORDER, order_handler)
        
        # 3. 验证处理器注册
        assert EventType.MARKET in engine.handlers
        assert EventType.SIGNAL in engine.handlers
        assert EventType.ORDER in engine.handlers
        assert len(engine.handlers[EventType.MARKET]) == 1
        
        # 4. 添加事件到队列
        market_event = MarketEvent(
            timestamp=datetime.now(),
            symbol="AAPL",
            data={
                'open': 150.0,
                'high': 155.0,
                'low': 148.0,
                'close': 152.0,
                'volume': 1000
            }
        )

        signal_event = SignalEvent(
            timestamp=datetime.now(),
            symbol="AAPL",
            direction=1,
            strength=0.8
        )

        order_event = OrderEvent(
            timestamp=datetime.now(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=100,
            direction=1
        )
        
        engine.put(market_event)
        engine.put(signal_event)
        engine.put(order_event)
        
        # 5. 处理所有事件
        engine.process_all()
        
        # 6. 验证事件处理结果
        assert len(processed_events) == 3
        assert processed_events[0][0] == 'market'
        assert processed_events[1][0] == 'signal'
        assert processed_events[2][0] == 'order'
        assert processed_events[0][1].symbol == "AAPL"
        assert processed_events[1][1].direction == 1
        assert processed_events[2][1].quantity == 100
        
        # 7. 验证队列为空
        assert engine.queue.empty()
    
    def test_event_engine_error_handling(self):
        """测试EventEngine的错误处理"""
        engine = EventEngine()

        # 注册一个会抛出异常的处理器
        def error_handler(event):
            raise RuntimeError("Test error")

        # 注册一个正常的处理器
        processed_events = []
        def normal_handler(event):
            processed_events.append(event)

        engine.register_handler(EventType.MARKET, error_handler)
        engine.register_handler(EventType.MARKET, normal_handler)

        # 添加事件
        market_event = MarketEvent(
            timestamp=datetime.now(),
            symbol="AAPL",
            data={
                'open': 150.0,
                'high': 155.0,
                'low': 148.0,
                'close': 152.0,
                'volume': 1000
            }
        )

        engine.put(market_event)

        # 处理事件（EventEngine当前实现不捕获异常，所以会抛出）
        # 我们测试异常确实被抛出
        try:
            engine.process_all()
            # 如果没有异常，说明错误处理器没有被调用
            assert False, "Expected RuntimeError to be raised"
        except RuntimeError as e:
            assert str(e) == "Test error"
            # 验证事件确实被处理了（虽然抛出了异常）
            assert engine.queue.empty()
    
    def test_event_engine_handler_management(self):
        """测试EventEngine的处理器管理"""
        engine = EventEngine()
        
        # 测试注册和注销处理器
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        # 注册处理器
        engine.register_handler(EventType.MARKET, handler1)
        engine.register_handler(EventType.MARKET, handler2)
        
        assert len(engine.handlers[EventType.MARKET]) == 2
        
        # 注销处理器
        engine.unregister_handler(EventType.MARKET, handler1)
        assert len(engine.handlers[EventType.MARKET]) == 1
        assert handler2 in engine.handlers[EventType.MARKET]
        
        # 注销不存在的处理器（应该不报错）
        def non_existent_handler(event):
            pass
        
        engine.unregister_handler(EventType.MARKET, non_existent_handler)
        assert len(engine.handlers[EventType.MARKET]) == 1
        
        # 注销所有处理器
        engine.unregister_handler(EventType.MARKET, handler2)
        assert EventType.MARKET not in engine.handlers or len(engine.handlers[EventType.MARKET]) == 0
    
    def test_event_engine_queue_operations(self):
        """测试EventEngine的队列操作"""
        engine = EventEngine()
        
        # 测试空队列处理
        engine.process_all()  # 应该不报错
        
        # 测试单个事件处理
        processed_events = []
        def handler(event):
            processed_events.append(event)
        
        engine.register_handler(EventType.MARKET, handler)
        
        market_event = MarketEvent(
            timestamp=datetime.now(),
            symbol="AAPL",
            data={
                'open': 150.0,
                'high': 155.0,
                'low': 148.0,
                'close': 152.0,
                'volume': 1000
            }
        )
        
        engine.put(market_event)
        assert not engine.queue.empty()
        
        # 处理单个事件
        engine.process()
        assert len(processed_events) == 1
        assert engine.queue.empty()
        
        # 测试清空队列
        engine.put(market_event)
        engine.put(market_event)
        assert engine.queue.qsize() == 2
        
        engine.clear()
        assert engine.queue.empty()
    
    def test_event_driven_backtester_real_logic(self):
        """测试EventDrivenBacktester的真实逻辑"""
        # 创建backtester（使用实际的构造函数参数）
        backtester = EventDrivenBacktester(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage=0.0
        )
        
        # 测试基本功能
        # 1. 验证初始状态
        assert backtester.initial_capital == 100000.0
        assert backtester.current_capital == 100000.0
        assert backtester.commission_rate == 0.001
        assert backtester.slippage == 0.0
        assert len(backtester.strategies) == 0
        assert len(backtester.positions) == 0
        assert len(backtester.open_orders) == 0

        # 2. 测试添加策略
        mock_strategy = Mock()
        mock_strategy.on_market_data = Mock()
        backtester.add_strategy(mock_strategy)
        assert len(backtester.strategies) == 1

        # 3. 测试设置数据
        test_data = {
            'AAPL': [
                {
                    'timestamp': datetime.now(),
                    'open': 150.0,
                    'high': 155.0,
                    'low': 148.0,
                    'close': 152.0,
                    'volume': 1000
                }
            ]
        }
        backtester.set_data(test_data)
        assert backtester.data == test_data
        assert backtester.data_symbols == ['AAPL']

        # 4. 测试计算权益
        initial_equity = backtester.calculate_equity()
        assert initial_equity == 100000.0

        # 5. 测试事件处理器注册
        assert EventType.MARKET in backtester.event_engine.handlers
        assert EventType.SIGNAL in backtester.event_engine.handlers
        assert EventType.ORDER in backtester.event_engine.handlers
        assert EventType.FILL in backtester.event_engine.handlers
