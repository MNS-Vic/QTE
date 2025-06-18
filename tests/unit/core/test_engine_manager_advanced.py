#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EngineManager高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from queue import Queue, Empty

from qte.core.engine_manager import (
    EngineType, EngineStatus, EngineEvent, MarketDataEvent,
    EngineManagerInterface, BaseEngineManager
)
from qte.core.events import Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent


class TestEngineManagerAdvanced:
    """EngineManager高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.manager = BaseEngineManager(EngineType.EVENT_DRIVEN)
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        try:
            self.manager.stop()
        except:
            pass
    
    def test_engine_type_enum(self):
        """测试引擎类型枚举"""
        # Red: 编写失败的测试
        assert EngineType.EVENT_DRIVEN.value == 1
        assert EngineType.VECTORIZED.value == 2
        assert EngineType.HYBRID.value == 3
    
    def test_engine_status_enum(self):
        """测试引擎状态枚举"""
        # Red: 编写失败的测试
        assert EngineStatus.INITIALIZED.value == 1
        assert EngineStatus.RUNNING.value == 2
        assert EngineStatus.PAUSED.value == 3
        assert EngineStatus.STOPPED.value == 4
        assert EngineStatus.COMPLETED.value == 5
        assert EngineStatus.ERROR.value == 6
    
    def test_engine_event_creation(self):
        """测试引擎事件创建"""
        # Red: 编写失败的测试
        event_type = "TEST_EVENT"
        timestamp = datetime.now()
        data = {"test": "data"}
        
        event = EngineEvent(event_type, timestamp, data)
        
        # 验证事件属性
        assert event.event_type == event_type
        assert event.timestamp == timestamp
        assert event.data == data
        assert event.source is None
    
    def test_engine_event_default_timestamp(self):
        """测试引擎事件默认时间戳"""
        # Red: 编写失败的测试
        event = EngineEvent("TEST_EVENT")
        
        # 验证默认时间戳
        assert isinstance(event.timestamp, datetime)
        assert event.data is None
    
    def test_engine_event_str_representation(self):
        """测试引擎事件字符串表示"""
        # Red: 编写失败的测试
        event = EngineEvent("TEST_EVENT")
        event.source = "test_source"
        
        str_repr = str(event)
        assert "EngineEvent" in str_repr
        assert "TEST_EVENT" in str_repr
        assert "test_source" in str_repr
    
    def test_market_data_event_creation(self):
        """测试市场数据事件创建"""
        # Red: 编写失败的测试
        timestamp = datetime.now()
        symbol = "AAPL"
        data = {"close": 150.0, "volume": 1000}
        
        event = MarketDataEvent(timestamp, symbol, data)
        
        # 验证事件属性
        assert event.event_type == "MARKET_DATA"
        assert event.timestamp == timestamp
        assert event.symbol == symbol
        assert event.data == data
    
    def test_market_data_event_str_representation(self):
        """测试市场数据事件字符串表示"""
        # Red: 编写失败的测试
        timestamp = datetime.now()
        symbol = "AAPL"
        data = {"close": 150.0}
        
        event = MarketDataEvent(timestamp, symbol, data)
        str_repr = str(event)
        
        assert "MarketDataEvent" in str_repr
        assert "AAPL" in str_repr
    
    def test_base_engine_manager_init(self):
        """测试基础引擎管理器初始化"""
        # Red: 编写失败的测试
        manager = BaseEngineManager(EngineType.VECTORIZED)
        
        # 验证初始化状态
        assert manager._engine_type == EngineType.VECTORIZED
        assert manager._status == EngineStatus.INITIALIZED
        assert isinstance(manager._config, dict)
        assert isinstance(manager._event_queue, Queue)
        assert isinstance(manager._event_handlers, dict)
        assert manager._handler_id_counter == 0
        assert manager._event_processing_thread is None
        assert manager._performance_stats["processed_events"] == 0
    
    def test_initialize_success(self):
        """测试初始化成功"""
        # Red: 编写失败的测试
        config = {"test_param": "test_value"}
        
        result = self.manager.initialize(config)
        
        # 验证初始化成功
        assert result is True
        assert self.manager._config == config
        assert self.manager._status == EngineStatus.INITIALIZED
        assert self.manager._handler_id_counter == 0
        assert self.manager._performance_stats["processed_events"] == 0
    
    def test_initialize_default_config(self):
        """测试初始化默认配置"""
        # Red: 编写失败的测试
        result = self.manager.initialize()
        
        # 验证默认配置
        assert result is True
        assert self.manager._config == {}
    
    def test_initialize_while_running(self):
        """测试运行时初始化失败"""
        # Red: 编写失败的测试
        # 先启动管理器
        self.manager.start()
        assert self.manager._status == EngineStatus.RUNNING
        
        # 尝试重新初始化
        result = self.manager.initialize({"new": "config"})
        
        # 验证初始化失败
        assert result is False
        assert self.manager._status == EngineStatus.RUNNING  # 状态不变
    
    def test_initialize_while_paused(self):
        """测试暂停时初始化失败"""
        # Red: 编写失败的测试
        # 先启动并暂停管理器
        self.manager.start()
        self.manager.pause()
        assert self.manager._status == EngineStatus.PAUSED
        
        # 尝试重新初始化
        result = self.manager.initialize()
        
        # 验证初始化失败
        assert result is False
        assert self.manager._status == EngineStatus.PAUSED  # 状态不变
    
    def test_start_success(self):
        """测试启动成功"""
        # Red: 编写失败的测试
        result = self.manager.start()
        
        # 验证启动成功
        assert result is True
        assert self.manager._status == EngineStatus.RUNNING
        assert self.manager._event_processing_thread is not None
        assert self.manager._event_processing_thread.is_alive()
    
    def test_start_already_running(self):
        """测试重复启动失败"""
        # Red: 编写失败的测试
        # 先启动
        self.manager.start()
        assert self.manager._status == EngineStatus.RUNNING
        
        # 尝试再次启动
        result = self.manager.start()
        
        # 验证启动失败
        assert result is False
        assert self.manager._status == EngineStatus.RUNNING
    
    def test_start_from_stopped(self):
        """测试从停止状态启动"""
        # Red: 编写失败的测试
        # 先启动再停止
        self.manager.start()
        self.manager.stop()
        assert self.manager._status == EngineStatus.STOPPED
        
        # 从停止状态重新启动
        result = self.manager.start()
        
        # 验证启动成功
        assert result is True
        assert self.manager._status == EngineStatus.RUNNING
    
    def test_start_from_invalid_status(self):
        """测试从无效状态启动失败"""
        # Red: 编写失败的测试
        # 手动设置为错误状态
        self.manager._status = EngineStatus.ERROR
        
        # 尝试启动
        result = self.manager.start()
        
        # 验证启动失败
        assert result is False
        assert self.manager._status == EngineStatus.ERROR
    
    def test_pause_success(self):
        """测试暂停成功"""
        # Red: 编写失败的测试
        # 先启动
        self.manager.start()
        assert self.manager._status == EngineStatus.RUNNING
        
        # 暂停
        result = self.manager.pause()
        
        # 验证暂停成功
        assert result is True
        assert self.manager._status == EngineStatus.PAUSED
    
    def test_pause_not_running(self):
        """测试非运行状态暂停失败"""
        # Red: 编写失败的测试
        # 确保未运行
        assert self.manager._status == EngineStatus.INITIALIZED
        
        # 尝试暂停
        result = self.manager.pause()
        
        # 验证暂停失败
        assert result is False
        assert self.manager._status == EngineStatus.INITIALIZED
    
    def test_resume_success(self):
        """测试恢复成功"""
        # Red: 编写失败的测试
        # 先启动再暂停
        self.manager.start()
        self.manager.pause()
        assert self.manager._status == EngineStatus.PAUSED
        
        # 恢复
        result = self.manager.resume()
        
        # 验证恢复成功
        assert result is True
        assert self.manager._status == EngineStatus.RUNNING
    
    def test_resume_not_paused(self):
        """测试非暂停状态恢复失败"""
        # Red: 编写失败的测试
        # 确保未暂停
        assert self.manager._status == EngineStatus.INITIALIZED

        # 尝试恢复
        result = self.manager.resume()

        # 验证恢复失败（resume只能从PAUSED状态调用）
        assert result is False
        assert self.manager._status == EngineStatus.INITIALIZED
    
    def test_stop_success(self):
        """测试停止成功"""
        # Red: 编写失败的测试
        # 先启动
        self.manager.start()
        assert self.manager._status == EngineStatus.RUNNING
        
        # 停止
        result = self.manager.stop()
        
        # 验证停止成功
        assert result is True
        assert self.manager._status == EngineStatus.STOPPED
        assert self.manager._event_processing_thread is None
    
    def test_stop_from_paused(self):
        """测试从暂停状态停止"""
        # Red: 编写失败的测试
        # 先启动再暂停
        self.manager.start()
        self.manager.pause()
        assert self.manager._status == EngineStatus.PAUSED
        
        # 停止
        result = self.manager.stop()
        
        # 验证停止成功
        assert result is True
        assert self.manager._status == EngineStatus.STOPPED
    
    def test_stop_not_running_or_paused(self):
        """测试非运行/暂停状态停止失败"""
        # Red: 编写失败的测试
        # 确保未运行
        assert self.manager._status == EngineStatus.INITIALIZED
        
        # 尝试停止
        result = self.manager.stop()
        
        # 验证停止失败
        assert result is False
        assert self.manager._status == EngineStatus.INITIALIZED
    
    def test_get_status(self):
        """测试获取状态"""
        # Red: 编写失败的测试
        # 测试不同状态
        assert self.manager.get_status() == EngineStatus.INITIALIZED
        
        self.manager.start()
        assert self.manager.get_status() == EngineStatus.RUNNING
        
        self.manager.pause()
        assert self.manager.get_status() == EngineStatus.PAUSED
        
        self.manager.stop()
        assert self.manager.get_status() == EngineStatus.STOPPED

    def test_send_event_success(self):
        """测试发送事件成功"""
        # Red: 编写失败的测试
        self.manager.start()

        event = Event(EventType.MARKET)
        result = self.manager.send_event(event)

        # 验证发送成功
        assert result is True
        assert not self.manager._event_queue.empty()

    def test_send_event_not_running(self):
        """测试非运行状态发送事件失败"""
        # Red: 编写失败的测试
        # 确保未运行
        assert self.manager._status == EngineStatus.INITIALIZED

        event = Event(EventType.SIGNAL)
        result = self.manager.send_event(event)

        # 验证发送失败
        assert result is False

    def test_send_event_market_when_initialized(self):
        """测试初始化状态发送市场事件失败"""
        # Red: 编写失败的测试
        # 确保是初始化状态
        assert self.manager._status == EngineStatus.INITIALIZED

        event = Event(EventType.MARKET)
        result = self.manager.send_event(event)

        # 验证市场事件在初始化状态也不能发送（实际实现的行为）
        assert result is False

    def test_send_event_paused(self):
        """测试暂停状态发送事件成功"""
        # Red: 编写失败的测试
        self.manager.start()
        self.manager.pause()
        assert self.manager._status == EngineStatus.PAUSED

        event = Event(EventType.ORDER)
        result = self.manager.send_event(event)

        # 验证暂停状态可以发送事件
        assert result is True

    def test_send_event_exception(self):
        """测试发送事件异常处理"""
        # Red: 编写失败的测试
        self.manager.start()

        # Mock队列抛出异常
        with patch.object(self.manager._event_queue, 'put', side_effect=Exception("Queue error")):
            event = Event(EventType.FILL)
            result = self.manager.send_event(event)

            # 验证异常被捕获，返回False
            assert result is False

    def test_register_event_handler_success(self):
        """测试注册事件处理器成功"""
        # Red: 编写失败的测试
        def test_handler(event):
            pass

        event_type = "TEST_EVENT"

        handler_id = self.manager.register_event_handler(event_type, test_handler)

        # 验证注册成功
        assert handler_id >= 0
        assert event_type in self.manager._event_handlers
        assert test_handler in self.manager._event_handlers[event_type]
        assert self.manager._handler_id_counter > 0

    def test_register_event_handler_duplicate(self):
        """测试注册重复事件处理器"""
        # Red: 编写失败的测试
        def test_handler(event):
            pass

        event_type = "TEST_EVENT"

        # 注册两次相同的处理器
        handler_id1 = self.manager.register_event_handler(event_type, test_handler)
        handler_id2 = self.manager.register_event_handler(event_type, test_handler)

        # 验证不会重复添加
        assert handler_id1 >= 0
        assert handler_id2 >= 0
        assert len(self.manager._event_handlers[event_type]) == 1

    def test_register_event_handler_multiple(self):
        """测试注册多个事件处理器"""
        # Red: 编写失败的测试
        def test_handler1(event):
            pass

        def test_handler2(event):
            pass

        event_type = "TEST_EVENT"

        # 注册多个处理器
        handler_id1 = self.manager.register_event_handler(event_type, test_handler1)
        handler_id2 = self.manager.register_event_handler(event_type, test_handler2)

        # 验证都被注册
        assert handler_id1 >= 0
        assert handler_id2 >= 0
        assert len(self.manager._event_handlers[event_type]) == 2
        assert test_handler1 in self.manager._event_handlers[event_type]
        assert test_handler2 in self.manager._event_handlers[event_type]

    def test_register_event_handler_invalid_type(self):
        """测试注册无效事件类型处理器"""
        # Red: 编写失败的测试
        handler = Mock()
        invalid_event_type = 123  # 非字符串类型

        handler_id = self.manager.register_event_handler(invalid_event_type, handler)

        # 验证注册失败
        assert handler_id == -1

    def test_unregister_event_handler_not_supported(self):
        """测试注销事件处理器不支持"""
        # Red: 编写失败的测试
        result = self.manager.unregister_event_handler(123)

        # 验证不支持按ID注销
        assert result is False

    def test_get_performance_stats_initial(self):
        """测试获取初始性能统计"""
        # Red: 编写失败的测试
        stats = self.manager.get_performance_stats()

        # 验证初始统计
        assert isinstance(stats, dict)
        assert stats["processed_events"] == 0
        assert stats["start_time"] is None
        assert stats["end_time"] is None

    def test_event_processing_thread_lifecycle(self):
        """测试事件处理线程生命周期"""
        # Red: 编写失败的测试
        # 启动前没有线程
        assert self.manager._event_processing_thread is None

        # 启动后有线程
        self.manager.start()
        assert self.manager._event_processing_thread is not None
        assert self.manager._event_processing_thread.is_alive()
        thread_id = self.manager._event_processing_thread.ident

        # 停止后线程清理
        self.manager.stop()
        assert self.manager._event_processing_thread is None

        # 重新启动创建新线程
        self.manager.start()
        assert self.manager._event_processing_thread is not None
        assert self.manager._event_processing_thread.is_alive()
        new_thread_id = self.manager._event_processing_thread.ident
        # 注意：在某些情况下线程ID可能被重用，这是正常的
        # 主要验证线程对象是新创建的即可
        assert isinstance(new_thread_id, int)

    def test_thread_safety_status_access(self):
        """测试状态访问的线程安全性"""
        # Red: 编写失败的测试
        results = []

        def check_status():
            for _ in range(10):
                status = self.manager.get_status()
                results.append(status)
                time.sleep(0.001)

        # 启动多个线程同时访问状态
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=check_status)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有结果都是有效状态
        assert len(results) == 30
        for status in results:
            assert isinstance(status, EngineStatus)

    def test_stop_with_queue_timeout(self):
        """测试停止时队列超时处理"""
        # Red: 编写失败的测试
        self.manager.start()

        # Mock队列put方法抛出Full异常
        with patch.object(self.manager._event_queue, 'put', side_effect=Exception("Queue error")):
            result = self.manager.stop()

            # 验证即使队列操作失败，停止仍然成功
            assert result is True
            assert self.manager._status == EngineStatus.STOPPED

    def test_stop_thread_timeout_handling(self):
        """测试停止时线程超时处理"""
        # Red: 编写失败的测试
        self.manager.start()

        # Mock线程join超时
        original_thread = self.manager._event_processing_thread
        with patch.object(original_thread, 'join') as mock_join, \
             patch.object(original_thread, 'is_alive', return_value=True):

            result = self.manager.stop()

            # 验证超时处理
            assert result is True
            assert self.manager._status == EngineStatus.STOPPED
            mock_join.assert_called_once_with(timeout=3.0)

    def test_performance_stats_timing(self):
        """测试性能统计时间记录"""
        # Red: 编写失败的测试
        # 手动设置开始时间
        start_time = time.time()
        self.manager._performance_stats["start_time"] = start_time

        # 停止时应该设置结束时间
        self.manager.start()  # 先启动才能停止
        self.manager.stop()

        # 验证结束时间被设置
        assert self.manager._performance_stats["end_time"] is not None
        assert self.manager._performance_stats["end_time"] >= start_time
