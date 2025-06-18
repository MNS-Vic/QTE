#!/usr/bin/env python3
"""
Engine Manager真实业务逻辑测试
减少Mock使用，测试真实的业务逻辑路径
"""

import pytest
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch

from qte.core.engine_manager import BaseEngineManager, ReplayEngineManager, EngineStatus
from qte.core.events import MarketEvent, EventType


class TestEngineManagerRealLogic:
    """Engine Manager真实业务逻辑测试"""
    
    def test_base_engine_manager_full_lifecycle(self):
        """测试BaseEngineManager的完整生命周期"""
        engine = BaseEngineManager()

        # 1. 初始化状态检查
        # BaseEngineManager默认是INITIALIZED状态
        assert engine.get_status() == EngineStatus.INITIALIZED
        
        # 2. 注册事件处理器
        processed_events = []

        def test_handler(event):
            processed_events.append(event)

        # 使用字符串而不是枚举来注册事件处理器
        engine.register_event_handler("MARKET", test_handler)
        
        # 3. 启动引擎
        engine.start()
        assert engine.get_status() == EngineStatus.RUNNING
        
        # 4. 发送事件
        test_event = MarketEvent(
            timestamp=datetime.now(),
            symbol="TEST",
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000
        )
        
        engine.send_event(test_event)
        
        # 等待事件处理
        time.sleep(0.1)
        
        # 5. 验证事件被处理
        assert len(processed_events) == 1
        assert processed_events[0].symbol == "TEST"
        
        # 6. 暂停和恢复
        engine.pause()
        assert engine.get_status() == EngineStatus.PAUSED
        
        engine.resume()
        assert engine.get_status() == EngineStatus.RUNNING
        
        # 7. 停止引擎
        engine.stop()
        assert engine.get_status() == EngineStatus.STOPPED
    
    def test_base_engine_manager_multiple_handlers(self):
        """测试多个事件处理器"""
        engine = BaseEngineManager()
        engine.initialize()
        
        # 注册多个处理器
        handler1_events = []
        handler2_events = []
        
        def handler1(event):
            handler1_events.append(f"H1:{event.symbol}")
        
        def handler2(event):
            handler2_events.append(f"H2:{event.symbol}")
        
        engine.register_event_handler("MARKET", handler1)
        engine.register_event_handler("MARKET", handler2)
        
        engine.start()
        
        # 发送事件
        event = MarketEvent(
            timestamp=datetime.now(),
            symbol="MULTI",
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000
        )
        
        engine.send_event(event)
        time.sleep(0.1)
        
        # 验证两个处理器都被调用
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1
        assert handler1_events[0] == "H1:MULTI"
        assert handler2_events[0] == "H2:MULTI"
        
        engine.stop()
    
    def test_base_engine_manager_error_handling(self):
        """测试错误处理"""
        engine = BaseEngineManager()
        engine.initialize()
        
        # 注册一个会抛出异常的处理器
        def error_handler(event):
            raise RuntimeError("Test error")
        
        # 注册一个正常的处理器
        normal_events = []
        def normal_handler(event):
            normal_events.append(event)
        
        engine.register_event_handler("MARKET", error_handler)
        engine.register_event_handler("MARKET", normal_handler)
        
        engine.start()
        
        # 发送事件
        event = MarketEvent(
            timestamp=datetime.now(),
            symbol="ERROR_TEST",
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000
        )
        
        engine.send_event(event)
        time.sleep(0.1)
        
        # 验证正常处理器仍然工作
        assert len(normal_events) == 1
        assert normal_events[0].symbol == "ERROR_TEST"
        
        # 引擎应该仍然运行
        assert engine.get_status() == EngineStatus.RUNNING
        
        engine.stop()
    
    def test_base_engine_manager_performance_stats(self):
        """测试性能统计"""
        engine = BaseEngineManager()
        engine.initialize()
        
        # 获取初始统计
        initial_stats = engine.get_performance_stats()
        assert 'processed_events' in initial_stats
        assert 'events_per_second' in initial_stats
        assert 'start_time' in initial_stats  # 修正字段名
        assert 'processing_time' in initial_stats
        
        processed_count = []
        def counting_handler(event):
            processed_count.append(event)
        
        engine.register_event_handler("MARKET", counting_handler)
        engine.start()
        
        # 发送多个事件
        for i in range(10):
            event = MarketEvent(
                timestamp=datetime.now(),
                symbol=f"PERF{i}",
                open_price=100.0 + i,
                high_price=105.0 + i,
                low_price=95.0 + i,
                close_price=102.0 + i,
                volume=1000 + i
            )
            engine.send_event(event)
        
        time.sleep(0.2)
        
        # 获取更新后的统计
        final_stats = engine.get_performance_stats()
        assert final_stats['processed_events'] >= 10
        assert final_stats['processing_time'] >= 0  # 修正字段名
        
        engine.stop()
    
    def test_replay_engine_manager_controller_operations(self):
        """测试ReplayEngineManager的控制器操作"""
        replay_engine = ReplayEngineManager()
        replay_engine.initialize()
        
        # 创建模拟控制器
        mock_controller = Mock()
        mock_controller.start = Mock(return_value=True)
        mock_controller.pause = Mock(return_value=True)
        mock_controller.resume = Mock(return_value=True)
        mock_controller.stop = Mock(return_value=True)
        mock_controller.set_mode = Mock(return_value=True)
        mock_controller.set_speed = Mock(return_value=True)
        mock_controller.reset = Mock(return_value=True)
        mock_controller.is_running = Mock(return_value=False)
        
        # 添加控制器
        replay_engine.add_replay_controller("test_controller", mock_controller)
        
        # 测试启动
        replay_engine.start()
        mock_controller.start.assert_called_once()
        
        # 测试暂停
        replay_engine.pause()
        mock_controller.pause.assert_called_once()
        
        # 测试恢复
        replay_engine.resume()
        mock_controller.resume.assert_called_once()
        
        # 测试设置模式
        from qte.data.data_replay import ReplayMode
        replay_engine.set_replay_mode(ReplayMode.BACKTEST)
        mock_controller.set_mode.assert_called_with(ReplayMode.BACKTEST)
        
        # 测试设置速度
        replay_engine.set_replay_speed(2.0)
        mock_controller.set_speed.assert_called_with(2.0)
        
        # 测试停止
        replay_engine.stop()
        mock_controller.stop.assert_called_once()
        
        # 测试移除控制器
        replay_engine.remove_replay_controller("test_controller")
        assert "test_controller" not in replay_engine._replay_controllers
    
    def test_replay_engine_manager_data_callback(self):
        """测试ReplayEngineManager的数据回调"""
        replay_engine = ReplayEngineManager()
        replay_engine.initialize()
        
        # 注册事件处理器
        received_events = []
        def event_handler(event):
            received_events.append(event)
        
        replay_engine.register_event_handler("MARKET", event_handler)
        replay_engine.start()
        
        # 模拟数据回调
        market_data = {
            'timestamp': datetime.now(),
            'symbol': 'REPLAY_TEST',
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000
        }
        
        # 调用数据回调
        replay_engine._on_replay_data("test_source", market_data)
        
        time.sleep(0.1)
        
        # 验证事件被创建和处理
        assert len(received_events) == 1
        event = received_events[0]
        assert event.symbol == 'REPLAY_TEST'
        assert event.open_price == 100.0
        assert event.close_price == 102.0
        
        replay_engine.stop()
    
    def test_engine_manager_thread_safety(self):
        """测试引擎管理器的线程安全性"""
        engine = BaseEngineManager()
        engine.initialize()
        
        processed_events = []
        lock = threading.Lock()
        
        def thread_safe_handler(event):
            with lock:
                processed_events.append(event.symbol)
        
        engine.register_event_handler("MARKET", thread_safe_handler)
        engine.start()
        
        # 多线程发送事件
        def send_events(thread_id, count):
            for i in range(count):
                event = MarketEvent(
                    timestamp=datetime.now(),
                    symbol=f"T{thread_id}_{i}",
                    open_price=100.0,
                    high_price=105.0,
                    low_price=95.0,
                    close_price=102.0,
                    volume=1000
                )
                engine.send_event(event)
        
        # 启动多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=send_events, args=(i, 5))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        time.sleep(0.2)
        
        # 验证所有事件都被处理
        assert len(processed_events) == 15  # 3 threads * 5 events each
        
        engine.stop()
    
    def test_engine_manager_wildcard_handlers(self):
        """测试通配符事件处理器"""
        engine = BaseEngineManager()
        engine.initialize()
        
        all_events = []
        market_events = []
        
        def wildcard_handler(event):
            all_events.append(event)
        
        def market_handler(event):
            market_events.append(event)
        
        # 注册通配符处理器和特定类型处理器
        engine.register_event_handler("*", wildcard_handler)
        engine.register_event_handler("MARKET", market_handler)
        
        engine.start()
        
        # 发送市场事件
        market_event = MarketEvent(
            timestamp=datetime.now(),
            symbol="WILDCARD_TEST",
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000
        )
        
        engine.send_event(market_event)
        time.sleep(0.1)
        
        # 验证两个处理器都被调用
        assert len(all_events) == 1
        assert len(market_events) == 1
        assert all_events[0].symbol == "WILDCARD_TEST"
        assert market_events[0].symbol == "WILDCARD_TEST"
        
        engine.stop()
