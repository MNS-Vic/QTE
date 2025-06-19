"""
Engine Manager边界条件测试
专门测试未覆盖的代码路径，提升覆盖率到95%+
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from qte.core.engine_manager import BaseEngineManager, ReplayEngineManager, EngineStatus, EngineType
from qte.core.events import Event, EventType


class TestEngineManagerEdgeCases:
    """Engine Manager边界条件测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.engine = BaseEngineManager()
    
    def test_register_event_handler_invalid_event_type(self):
        """测试注册处理器时event_type无效的情况 - 覆盖第478行"""
        # 测试空字符串
        result = self.engine.register_event_handler("", lambda x: None)
        assert result == -1
        
        # 测试None
        result = self.engine.register_event_handler(None, lambda x: None)
        assert result == -1
        
        # 测试非字符串类型
        result = self.engine.register_event_handler(123, lambda x: None)
        assert result == -1
    
    def test_register_event_handler_invalid_handler(self):
        """测试注册处理器时handler无效的情况 - 覆盖第482行"""
        # 测试None handler
        result = self.engine.register_event_handler("test_event", None)
        assert result == -1
        
        # 测试非可调用对象
        result = self.engine.register_event_handler("test_event", "not_callable")
        assert result == -1
        
        # 测试数字
        result = self.engine.register_event_handler("test_event", 123)
        assert result == -1
    
    def test_register_duplicate_handler(self):
        """测试注册重复处理器的情况 - 覆盖第494行"""
        def test_handler(event):
            pass
        
        # 第一次注册
        result1 = self.engine.register_event_handler("test_event", test_handler)
        assert result1 >= 0
        
        # 第二次注册相同处理器
        result2 = self.engine.register_event_handler("test_event", test_handler)
        assert result2 >= 0  # 应该返回有效ID，但不会重复添加
        
        # 验证处理器只被添加一次
        with self.engine._lock:
            assert len(self.engine._event_handlers["test_event"]) == 1
    
    def test_send_event_when_initialized_with_market_event(self):
        """测试在INITIALIZED状态下发送MARKET事件 - 覆盖第447行特殊条件"""
        # 初始化引擎但不启动
        self.engine.initialize()
        assert self.engine.get_status() == EngineStatus.INITIALIZED
        
        # 创建MARKET事件
        market_event = Event(EventType.MARKET.value, symbol="AAPL", price=150.0)

        # 应该能够发送MARKET事件
        result = self.engine.send_event(market_event)
        assert result == True

    def test_send_event_when_initialized_with_non_market_event(self):
        """测试在INITIALIZED状态下发送非MARKET事件 - 覆盖第448行"""
        # 初始化引擎但不启动
        self.engine.initialize()
        assert self.engine.get_status() == EngineStatus.INITIALIZED

        # 创建非MARKET事件
        order_event = Event(EventType.ORDER.value, symbol="AAPL", quantity=100)
        
        # 不应该能够发送非MARKET事件
        result = self.engine.send_event(order_event)
        assert result == False
    
    def test_performance_stats_with_running_engine(self):
        """测试运行中引擎的性能统计 - 覆盖第518行"""
        # 启动引擎
        self.engine.initialize()
        self.engine.start()
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 获取性能统计
        stats = self.engine.get_performance_stats()
        
        # 验证统计信息
        assert "processing_time" in stats
        assert stats["processing_time"] > 0  # 应该有处理时间
        assert stats["current_status"] == "RUNNING"
        
        # 停止引擎
        self.engine.stop()
    
    def test_stop_event_processing_queue_full_exception(self):
        """测试停止事件处理时队列满的异常 - 覆盖第400行"""
        # 启动引擎
        self.engine.initialize()
        self.engine.start()
        
        # Mock队列的put方法抛出异常
        with patch.object(self.engine._event_queue, 'put', side_effect=Exception("Queue full")):
            # 停止引擎应该能处理异常
            result = self.engine.stop()
            assert result == True
    
    def test_stop_event_processing_thread_timeout(self):
        """测试停止事件处理线程超时的情况 - 覆盖第408行"""
        # 启动引擎
        self.engine.initialize()
        self.engine.start()
        
        # Mock线程的join方法，模拟超时
        original_join = self.engine._event_processing_thread.join
        def mock_join(timeout=None):
            # 不实际join，模拟超时
            pass
        
        with patch.object(self.engine._event_processing_thread, 'join', side_effect=mock_join):
            with patch.object(self.engine._event_processing_thread, 'is_alive', return_value=True):
                # 停止引擎，应该处理线程超时情况
                result = self.engine.stop()
                assert result == True
    
    def test_dispatch_event_with_wildcard_handlers(self):
        """测试事件分发到通配符处理器 - 覆盖第667行"""
        # 先初始化引擎
        self.engine.initialize()

        # 然后注册通配符处理器（在初始化后）
        wildcard_events = []
        def wildcard_handler(event):
            wildcard_events.append(event.event_type)

        self.engine.register_event_handler("*", wildcard_handler)

        # 启动引擎
        self.engine.start()
        
        # 发送事件
        test_event = Event("any_event_type", data="test")
        self.engine.send_event(test_event)

        # 等待处理
        time.sleep(0.1)

        # 验证通配符处理器被调用
        assert len(wildcard_events) > 0
        assert "any_event_type" in wildcard_events

        # 停止引擎
        self.engine.stop()

    def test_dispatch_event_handler_exception(self):
        """测试事件处理器抛出异常的情况 - 覆盖第688行"""
        # 先初始化引擎
        self.engine.initialize()

        # 然后注册处理器（在初始化后）
        def error_handler(event):
            raise ValueError("Handler error")

        # 注册正常处理器
        normal_events = []
        def normal_handler(event):
            normal_events.append(event.event_type)

        self.engine.register_event_handler("test_event", error_handler)
        self.engine.register_event_handler("test_event", normal_handler)

        # 启动引擎
        self.engine.start()

        # 发送事件
        test_event = Event("test_event", data="test")
        self.engine.send_event(test_event)
        
        # 等待处理
        time.sleep(0.1)
        
        # 验证正常处理器仍然被调用（即使有异常）
        assert len(normal_events) > 0
        assert "test_event" in normal_events
        
        # 停止引擎
        self.engine.stop()
    
    def test_process_events_exception_handling(self):
        """测试事件处理循环中的异常处理 - 覆盖第630行"""
        # 启动引擎
        self.engine.initialize()
        self.engine.start()
        
        # Mock _dispatch_event方法抛出异常
        original_dispatch = self.engine._dispatch_event
        def mock_dispatch(event):
            if hasattr(event, 'event_type') and event.event_type == "error_event":
                raise RuntimeError("Dispatch error")
            return original_dispatch(event)
        
        with patch.object(self.engine, '_dispatch_event', side_effect=mock_dispatch):
            # 发送会导致异常的事件
            error_event = Event("error_event", data="error")
            self.engine.send_event(error_event)
            
            # 等待处理
            time.sleep(0.2)
            
            # 验证引擎状态变为ERROR
            assert self.engine.get_status() == EngineStatus.ERROR
        
        # 停止引擎
        self.engine.stop()


class TestReplayEngineManagerEdgeCases:
    """Replay Engine Manager边界条件测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.replay_engine = ReplayEngineManager()
    
    def test_add_duplicate_replay_controller(self):
        """测试添加重复的重放控制器 - 覆盖第804行"""
        # 创建Mock控制器
        mock_controller = Mock()
        
        # 第一次添加
        result1 = self.replay_engine.add_replay_controller("test_controller", mock_controller)
        assert result1 == True
        
        # 第二次添加相同名称的控制器
        result2 = self.replay_engine.add_replay_controller("test_controller", mock_controller)
        assert result2 == False
    
    def test_remove_nonexistent_replay_controller(self):
        """测试移除不存在的重放控制器 - 覆盖第835行"""
        # 尝试移除不存在的控制器
        result = self.replay_engine.remove_replay_controller("nonexistent")
        assert result == False
    
    def test_remove_replay_controller_callback_error(self):
        """测试移除重放控制器时回调注销错误 - 覆盖第844行"""
        # 创建Mock控制器
        mock_controller = Mock()
        mock_controller.unregister_callback.side_effect = Exception("Unregister error")
        
        # 添加控制器
        self.replay_engine.add_replay_controller("test_controller", mock_controller)
        
        # 手动添加回调记录（模拟已注册状态）
        with self.replay_engine._lock:
            self.replay_engine._replay_callbacks[mock_controller] = 123
        
        # 移除控制器，应该处理注销回调时的异常
        result = self.replay_engine.remove_replay_controller("test_controller")
        assert result == True
    
    def test_start_with_no_controllers(self):
        """测试启动时没有重放控制器的情况 - 覆盖第895行"""
        # 初始化但不添加任何控制器
        self.replay_engine.initialize()
        
        # 启动应该成功，但会有警告
        result = self.replay_engine.start()
        assert result == True
        
        # 停止引擎
        self.replay_engine.stop()
    
    def test_start_with_callback_cleanup_error(self):
        """测试启动时清理旧回调出错的情况 - 覆盖第889行"""
        # 创建Mock控制器
        mock_controller = Mock()
        mock_controller.unregister_callback.side_effect = Exception("Cleanup error")
        
        # 手动添加回调记录
        with self.replay_engine._lock:
            self.replay_engine._replay_callbacks[mock_controller] = 123
        
        # 初始化并启动
        self.replay_engine.initialize()
        result = self.replay_engine.start()
        
        # 应该能处理清理错误并成功启动
        assert result == True
        
        # 停止引擎
        self.replay_engine.stop()
