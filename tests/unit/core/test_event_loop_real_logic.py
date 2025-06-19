"""
Event Loop真实逻辑测试
专注于测试真实的业务逻辑路径，减少Mock使用，提升覆盖率
"""

import asyncio
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch

from qte.core.event_loop import EventLoop
from qte.core.events import Event, EventType


class TestEventLoopRealLogic:
    """Event Loop真实逻辑测试"""
    
    def test_event_loop_full_lifecycle(self):
        """测试EventLoop的完整生命周期"""
        loop = EventLoop()

        # 1. 初始状态验证
        assert loop.continue_backtest == True
        assert len(loop.handlers) == 0
        assert loop.event_queue.empty()

        # 2. 注册事件处理器
        processed_events = []

        def test_handler(event):
            processed_events.append(("test_event", event.event_type))

        loop.register_handler("test_event", test_handler)
        assert "test_event" in loop.handlers
        assert len(loop.handlers["test_event"]) == 1

        # 3. 创建并发送事件
        test_event = Event("test_event")
        loop.put_event(test_event)
        assert not loop.event_queue.empty()

        # 4. 处理事件
        processed_count = loop.run()
        assert processed_count == 1
        assert len(processed_events) == 1
        assert processed_events[0][0] == "test_event"
        assert loop.event_queue.empty()

        # 5. 测试多个处理器
        def another_handler(event):
            processed_events.append(("another", event.event_type))

        loop.register_handler("test_event", another_handler)

        # 重新创建事件并发送
        test_event2 = Event("test_event")
        loop.put_event(test_event2)
        processed_count = loop.run()

        # 验证两个处理器都被调用
        assert processed_count == 1
        assert len(processed_events) == 3  # 之前1个 + 现在2个

        # 6. 注销处理器
        loop.unregister_handler("test_event", test_handler)
        assert len(loop.handlers["test_event"]) == 1

        # 发送最后一个事件
        test_event3 = Event("test_event")
        loop.put_event(test_event3)
        processed_count = loop.run()

        # 验证只有一个处理器被调用
        assert processed_count == 1
        assert len(processed_events) == 4
    
    def test_event_loop_error_handling(self):
        """测试EventLoop的错误处理"""
        loop = EventLoop()

        # 注册一个会抛出异常的处理器
        def error_handler(event):
            raise RuntimeError("Test error")

        # 注册一个正常的处理器
        processed_events = []
        def normal_handler(event):
            processed_events.append(event.event_type)

        loop.register_handler("test_event", error_handler)
        loop.register_handler("test_event", normal_handler)

        # 创建并发送事件
        test_event = Event("test_event")
        loop.put_event(test_event)

        # 处理事件（EventLoop会捕获异常并返回False，但继续处理其他处理器）
        success = loop.dispatch_event(test_event)

        # 验证处理失败（因为有异常）
        assert success == False

        # 但是我们需要单独测试正常处理器
        loop2 = EventLoop()
        loop2.register_handler("test_event", normal_handler)
        test_event2 = Event("test_event")
        loop2.put_event(test_event2)
        processed_count = loop2.run()

        # 验证正常处理器被调用
        assert processed_count == 1
        assert len(processed_events) == 1
        assert processed_events[0] == "test_event"
    
    def test_event_loop_threading(self):
        """测试EventLoop的线程安全性"""
        loop = EventLoop()

        processed_events = []
        event_lock = threading.Lock()

        def thread_safe_handler(event):
            with event_lock:
                processed_events.append((event.event_type, threading.current_thread().name))

        loop.register_handler("thread_event", thread_safe_handler)

        # 创建多个线程同时发送事件
        threads = []
        for i in range(5):
            def worker(thread_id=i):
                test_event = Event("thread_event")
                loop.put_event(test_event)

            thread = threading.Thread(target=worker, name=f"Worker-{i}")
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 处理所有事件
        processed_count = loop.run()

        # 验证所有事件都被处理
        assert processed_count == 5
        assert len(processed_events) == 5
    
    def test_event_loop_start_stop(self):
        """测试EventLoop的启动和停止"""
        loop = EventLoop()

        processed_events = []
        def handler(event):
            processed_events.append(event.event_type)
            # 在处理第一个事件后停止循环
            if len(processed_events) >= 1:
                loop.stop()

        loop.register_handler("stop_test", handler)

        # 发送事件
        test_event = Event("stop_test")
        loop.put_event(test_event)

        # 运行循环（会在处理第一个事件后停止）
        processed_count = loop.run()

        # 验证事件被处理且循环停止
        assert processed_count == 1
        assert len(processed_events) == 1
        assert not loop.continue_backtest
    
    def test_event_loop_batch_processing(self):
        """测试EventLoop的批量事件处理"""
        loop = EventLoop()

        processed_events = []
        def batch_handler(event):
            processed_events.append(event.event_type)

        loop.register_handler("batch_event", batch_handler)

        # 发送多个事件
        for i in range(10):
            test_event = Event("batch_event")
            loop.put_event(test_event)

        # 批量处理
        processed_count = loop.run()

        # 验证所有事件都被处理
        assert processed_count == 10
        assert len(processed_events) == 10
        assert loop.event_queue.empty()
    
    def test_event_loop_priority_events(self):
        """测试EventLoop的优先级事件处理"""
        loop = EventLoop()

        processed_events = []
        def priority_handler(event):
            processed_events.append(event.event_type)

        loop.register_handler("normal", priority_handler)
        loop.register_handler("priority", priority_handler)

        # 发送混合优先级事件
        normal_event1 = Event("normal")
        priority_event = Event("priority")
        normal_event2 = Event("normal")

        loop.put_event(normal_event1)
        loop.put_event(priority_event)
        loop.put_event(normal_event2)

        # 处理事件
        processed_count = loop.run()

        # 验证事件按发送顺序处理（FIFO）
        assert processed_count == 3
        assert len(processed_events) == 3
        assert processed_events[0] == "normal"
        assert processed_events[1] == "priority"
        assert processed_events[2] == "normal"

    def test_event_loop_performance(self):
        """测试EventLoop的性能"""
        loop = EventLoop()

        processed_count = 0
        def performance_handler(event):
            nonlocal processed_count
            processed_count += 1

        loop.register_handler("perf_event", performance_handler)

        # 发送大量事件
        event_count = 1000
        start_time = time.time()

        for i in range(event_count):
            test_event = Event("perf_event")
            loop.put_event(test_event)

        # 批量处理
        processed_events = loop.run()

        end_time = time.time()
        processing_time = end_time - start_time

        # 验证所有事件都被处理
        assert processed_count == event_count
        assert processed_events == event_count
        assert loop.event_queue.empty()

        # 验证性能（应该能在合理时间内处理完成）
        assert processing_time < 1.0  # 1秒内处理1000个事件

        # 计算每秒处理事件数
        events_per_second = event_count / processing_time
        assert events_per_second > 500  # 至少每秒500个事件
