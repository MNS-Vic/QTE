"""
事件循环单元测试（重新实现）
测试EventLoop类的事件队列管理、事件处理器注册和事件分发功能
"""
import pytest
from unittest.mock import MagicMock, call, patch
from datetime import datetime
import logging
import queue

# 导入要测试的模块
from qte.core.event_loop import EventLoop
from qte.core.events import Event, EventType, MarketEvent

class TestEventLoopNew:
    """测试事件循环类（重新实现）"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建事件循环实例
        self.event_loop = EventLoop(max_size=10)
        
        # 创建模拟事件和事件处理器
        self.test_timestamp = datetime(2023, 1, 1, 10, 0, 0)
        self.test_event = Event(event_type="TEST", timestamp=self.test_timestamp)
        self.mock_handler = MagicMock()
    
    def teardown_method(self):
        """测试后清理"""
        self.event_loop = None
        self.mock_handler = None
    
    def test_initialization(self):
        """测试事件循环初始化"""
        assert self.event_loop.continue_backtest is True
        assert len(self.event_loop.handlers) == 0
        assert self.event_loop.event_queue.maxsize == 10
        assert self.event_loop.event_queue.qsize() == 0
    
    def test_get_handler_name_with_name(self):
        """测试获取有__name__属性的处理器名称"""
        def sample_handler(event):
            pass
        
        name = self.event_loop._get_handler_name(sample_handler)
        assert name == "sample_handler"
    
    def test_get_handler_name_without_name(self):
        """测试获取没有__name__属性的处理器名称"""
        # 创建一个没有__name__属性的对象
        class HandlerWithoutName:
            def __call__(self, event):
                pass
            
            def __str__(self):
                return "<mock_handler>"
        
        handler = HandlerWithoutName()
        
        # 确认该对象确实没有__name__属性
        assert not hasattr(handler, "__name__")
        
        # 测试_get_handler_name方法
        name = self.event_loop._get_handler_name(handler)
        assert name == "<mock_handler>"
    
    def test_register_handler_with_string(self):
        """测试使用字符串事件类型注册处理器"""
        self.event_loop.register_handler("TEST", self.mock_handler)
        
        assert "TEST" in self.event_loop.handlers
        assert self.mock_handler in self.event_loop.handlers["TEST"]
        assert len(self.event_loop.handlers["TEST"]) == 1
    
    def test_register_handler_with_enum(self):
        """测试使用枚举事件类型注册处理器"""
        self.event_loop.register_handler(EventType.MARKET, self.mock_handler)
        
        assert EventType.MARKET.value in self.event_loop.handlers
        assert self.mock_handler in self.event_loop.handlers[EventType.MARKET.value]
    
    def test_register_handler_invalid_type(self):
        """测试使用无效的事件类型注册处理器"""
        with patch.object(logging.getLogger("qte.core.event_loop"), "error") as mock_error:
            self.event_loop.register_handler(123, self.mock_handler)  # 使用数字作为事件类型
            mock_error.assert_called_once()
            assert 123 not in self.event_loop.handlers
    
    def test_register_multiple_handlers(self):
        """测试为一个事件类型注册多个处理器"""
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        
        self.event_loop.register_handler("TEST", mock_handler1)
        self.event_loop.register_handler("TEST", mock_handler2)
        
        assert len(self.event_loop.handlers["TEST"]) == 2
        assert mock_handler1 in self.event_loop.handlers["TEST"]
        assert mock_handler2 in self.event_loop.handlers["TEST"]
    
    def test_register_same_handler_twice(self):
        """测试重复注册同一个处理器"""
        self.event_loop.register_handler("TEST", self.mock_handler)
        self.event_loop.register_handler("TEST", self.mock_handler)
        
        # 同一个处理器只应该被注册一次
        assert len(self.event_loop.handlers["TEST"]) == 1
    
    def test_unregister_handler(self):
        """测试注销事件处理器"""
        # 先注册处理器
        self.event_loop.register_handler("TEST", self.mock_handler)
        assert len(self.event_loop.handlers["TEST"]) == 1
        
        # 注销处理器
        self.event_loop.unregister_handler("TEST", self.mock_handler)
        assert len(self.event_loop.handlers["TEST"]) == 0
    
    def test_unregister_handler_invalid_type(self):
        """测试使用无效的事件类型注销处理器"""
        with patch.object(logging.getLogger("qte.core.event_loop"), "error") as mock_error:
            self.event_loop.unregister_handler(123, self.mock_handler)  # 使用数字作为事件类型
            mock_error.assert_called_once()
    
    def test_unregister_nonexistent_handler(self):
        """测试注销不存在的处理器"""
        # 注册一个处理器
        mock_handler1 = MagicMock()
        self.event_loop.register_handler("TEST", mock_handler1)
        
        # 尝试注销一个未注册的处理器
        mock_handler2 = MagicMock()
        self.event_loop.unregister_handler("TEST", mock_handler2)
        
        # 确认原有处理器仍然存在
        assert len(self.event_loop.handlers["TEST"]) == 1
        assert mock_handler1 in self.event_loop.handlers["TEST"]
    
    def test_put_event(self):
        """测试添加事件到队列"""
        self.event_loop.put_event(self.test_event)
        
        assert self.event_loop.event_queue.qsize() == 1
        assert not self.event_loop.event_queue.empty()
    
    def test_put_event_full_queue(self):
        """测试向已满队列添加事件"""
        # 创建最大容量为1的事件循环
        small_event_loop = EventLoop(max_size=1)
        
        # 添加一个事件，填满队列
        small_event_loop.put_event(self.test_event)
        
        # 再添加一个事件，应该阻塞或引发异常
        # 使用非阻塞方式测试
        with pytest.raises(queue.Full):
            # 使用原始队列的put_nowait方法测试，避免阻塞测试进程
            small_event_loop.event_queue.put_nowait(self.test_event)
    
    def test_get_next_event(self):
        """测试获取下一个事件"""
        # 先添加事件
        self.event_loop.put_event(self.test_event)
        
        # 获取事件
        event = self.event_loop.get_next_event()
        
        assert event is self.test_event
        assert self.event_loop.event_queue.empty()
    
    def test_get_next_event_empty_queue(self):
        """测试从空队列获取事件"""
        event = self.event_loop.get_next_event()
        
        assert event is None
    
    def test_dispatch_event_with_handler(self):
        """测试分发事件到处理器"""
        # 注册处理器
        self.event_loop.register_handler("TEST", self.mock_handler)
        
        # 分发事件
        result = self.event_loop.dispatch_event(self.test_event)
        
        assert result is True
        self.mock_handler.assert_called_once_with(self.test_event)
    
    def test_dispatch_event_without_handler(self):
        """测试分发事件但没有对应处理器"""
        # 注册一个不匹配的处理器
        self.event_loop.register_handler("OTHER", self.mock_handler)
        
        # 分发事件
        with patch.object(logging.getLogger("qte.core.event_loop"), "warning") as mock_warning:
            result = self.event_loop.dispatch_event(self.test_event)
            mock_warning.assert_called_once()
        
        assert result is False
        self.mock_handler.assert_not_called()
    
    def test_dispatch_event_with_multiple_handlers(self):
        """测试分发事件到多个处理器"""
        # 创建多个处理器
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        
        # 注册处理器
        self.event_loop.register_handler("TEST", mock_handler1)
        self.event_loop.register_handler("TEST", mock_handler2)
        
        # 分发事件
        result = self.event_loop.dispatch_event(self.test_event)
        
        assert result is True
        mock_handler1.assert_called_once_with(self.test_event)
        mock_handler2.assert_called_once_with(self.test_event)
    
    def test_dispatch_event_handler_raises_exception(self):
        """测试处理器抛出异常的情况"""
        # 创建一个会抛出异常的处理器
        def handler_with_exception(event):
            raise ValueError("Test exception")
        
        # 注册处理器
        self.event_loop.register_handler("TEST", handler_with_exception)
        
        # 分发事件
        with patch.object(logging.getLogger("qte.core.event_loop"), "error") as mock_error:
            result = self.event_loop.dispatch_event(self.test_event)
            mock_error.assert_called_once()
        
        assert result is False
    
    def test_run_process_all_events(self):
        """测试运行事件循环处理所有事件"""
        # 注册处理器
        self.event_loop.register_handler("TEST", self.mock_handler)
        
        # 添加多个事件
        for i in range(5):
            event = Event(event_type="TEST", timestamp=self.test_timestamp)
            self.event_loop.put_event(event)
        
        # 运行事件循环
        processed = self.event_loop.run()
        
        assert processed == 5
        assert self.mock_handler.call_count == 5
        assert self.event_loop.event_queue.empty()
    
    def test_run_with_max_events(self):
        """测试运行事件循环处理指定数量的事件"""
        # 注册处理器
        self.event_loop.register_handler("TEST", self.mock_handler)
        
        # 添加多个事件
        for i in range(5):
            event = Event(event_type="TEST", timestamp=self.test_timestamp)
            self.event_loop.put_event(event)
        
        # 运行事件循环，只处理3个事件
        processed = self.event_loop.run(max_events=3)
        
        assert processed == 3
        assert self.mock_handler.call_count == 3
        assert self.event_loop.event_queue.qsize() == 2
    
    def test_run_with_invalid_max_events(self):
        """测试运行事件循环并提供无效的max_events参数"""
        # 添加事件
        self.event_loop.put_event(self.test_event)
        
        # 运行事件循环，提供无效的max_events
        processed = self.event_loop.run(max_events=0)
        
        assert processed == 0
        assert self.event_loop.event_queue.qsize() == 1
    
    def test_stop_event_loop(self):
        """测试停止事件循环"""
        # 注册处理器
        self.event_loop.register_handler("TEST", self.mock_handler)
        
        # 添加多个事件
        for i in range(5):
            event = Event(event_type="TEST", timestamp=self.test_timestamp)
            self.event_loop.put_event(event)
        
        # 停止事件循环
        self.event_loop.stop()
        
        # 运行事件循环
        processed = self.event_loop.run()
        
        assert processed == 0
        assert self.mock_handler.call_count == 0
        assert self.event_loop.event_queue.qsize() == 5
    
    def test_len_operator(self):
        """测试__len__方法（获取队列长度）"""
        # 添加多个事件
        for i in range(3):
            event = Event(event_type="TEST", timestamp=self.test_timestamp)
            self.event_loop.put_event(event)
        
        assert len(self.event_loop) == 3


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 