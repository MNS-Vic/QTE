#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件管理器

专门负责事件处理、分发和队列管理
"""

import time
import queue
import threading
import logging
from typing import Dict, List, Callable, Any
from qte.core.events import Event as CoreEvent, EventType
from .base_manager import BaseManager, EngineStatus


class EventManager(BaseManager):
    """
    事件管理器
    
    负责事件队列管理、事件分发和处理器注册
    """
    
    def __init__(self, name: str = "EventManager"):
        """
        初始化事件管理器
        
        Parameters
        ----------
        name : str, optional
            管理器名称
        """
        super().__init__(name)
        
        # 事件队列和处理
        self._event_queue = queue.Queue()
        self._event_handlers: Dict[str, List[Callable[[CoreEvent], None]]] = {}
        self._handler_id_counter = 0
        
        # 线程控制
        self._event_processing_thread = None
        self._stop_event_processing = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 开始时不暂停
        
        # 性能统计
        self._performance_stats = {
            "processed_events": 0,
            "start_time": None,
            "end_time": None,
            "failed_events": 0,
            "handler_errors": 0
        }
        
        # 线程安全锁
        self._lock = threading.Lock()
        
        self.logger.info("✅ 事件管理器初始化完成")
    
    def start_processing(self) -> bool:
        """
        启动事件处理
        
        Returns
        -------
        bool
            启动是否成功
        """
        with self._lock:
            if self._event_processing_thread and self._event_processing_thread.is_alive():
                self.logger.warning("事件处理线程已在运行")
                return False
            
            self._stop_event_processing.clear()
            self._pause_event.set()
            
            self._event_processing_thread = threading.Thread(
                target=self._process_events,
                name=f"{self.name}_EventProcessor"
            )
            self._event_processing_thread.daemon = True
            self._event_processing_thread.start()
            
            if self._performance_stats.get("start_time") is None:
                self._performance_stats["start_time"] = time.time()
            
            thread_id = self._event_processing_thread.ident
            self.logger.info(f"✅ 事件处理线程已启动 (ID: {thread_id})")
            return True
    
    def stop_processing(self) -> bool:
        """
        停止事件处理
        
        Returns
        -------
        bool
            停止是否成功
        """
        with self._lock:
            if not self._event_processing_thread or not self._event_processing_thread.is_alive():
                self.logger.info("事件处理线程未运行")
                return True
            
            self._stop_event_processing.set()
            self._pause_event.set()
            
            # 发送停止信号
            try:
                self._event_queue.put(None, block=True, timeout=0.5)
            except queue.Full:
                self.logger.warning("事件队列已满，无法发送停止信号")
            
            # 等待线程结束
            if self._event_processing_thread:
                self._event_processing_thread.join(timeout=3.0)
                if self._event_processing_thread.is_alive():
                    self.logger.warning("事件处理线程未在超时内结束")
                else:
                    self.logger.info("✅ 事件处理线程已停止")
            
            self._event_processing_thread = None
            
            if self._performance_stats.get("end_time") is None:
                self._performance_stats["end_time"] = time.time()
            
            return True
    
    def pause_processing(self) -> bool:
        """
        暂停事件处理
        
        Returns
        -------
        bool
            暂停是否成功
        """
        self._pause_event.clear()
        self.logger.info("⏸️ 事件处理已暂停")
        return True
    
    def resume_processing(self) -> bool:
        """
        恢复事件处理
        
        Returns
        -------
        bool
            恢复是否成功
        """
        self._pause_event.set()
        self.logger.info("▶️ 事件处理已恢复")
        return True
    
    def send_event(self, event: CoreEvent) -> bool:
        """
        发送事件到队列
        
        Parameters
        ----------
        event : CoreEvent
            要发送的事件
            
        Returns
        -------
        bool
            发送是否成功
        """
        try:
            self._event_queue.put(event)
            return True
        except Exception as e:
            self.logger.error(f"发送事件失败: {e}")
            return False
    
    def register_event_handler(self, event_type: str, handler: Callable[[CoreEvent], None]) -> int:
        """
        注册事件处理器
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable[[CoreEvent], None]
            事件处理函数
            
        Returns
        -------
        int
            处理器ID
        """
        with self._lock:
            if not isinstance(event_type, str) or not event_type:
                self.logger.error("事件类型必须是非空字符串")
                return -1
            
            if not callable(handler):
                self.logger.error("处理器必须是可调用对象")
                return -1
            
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            
            if handler not in self._event_handlers[event_type]:
                self._event_handlers[event_type].append(handler)
                handler_id = self._handler_id_counter
                self._handler_id_counter += 1
                
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.debug(f"✅ 已注册事件处理器: {event_type} -> {handler_name}")
                return handler_id
            else:
                self.logger.debug(f"处理器已存在: {event_type}")
                return self._handler_id_counter - 1
    
    def unregister_event_handler(self, event_type: str, handler: Callable[[CoreEvent], None]) -> bool:
        """
        注销事件处理器
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable[[CoreEvent], None]
            事件处理函数
            
        Returns
        -------
        bool
            注销是否成功
        """
        with self._lock:
            if event_type in self._event_handlers:
                if handler in self._event_handlers[event_type]:
                    self._event_handlers[event_type].remove(handler)
                    handler_name = getattr(handler, '__name__', str(handler))
                    self.logger.debug(f"✅ 已注销事件处理器: {event_type} -> {handler_name}")
                    return True
            
            self.logger.warning(f"未找到要注销的处理器: {event_type}")
            return False
    
    def get_queue_size(self) -> int:
        """获取事件队列大小"""
        return self._event_queue.qsize()
    
    def get_handler_count(self) -> int:
        """获取处理器总数"""
        with self._lock:
            return sum(len(handlers) for handlers in self._event_handlers.values())
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        with self._lock:
            stats = self._performance_stats.copy()
            
            # 计算处理时间
            start_time = stats.get("start_time")
            end_time = stats.get("end_time")
            
            if start_time:
                if end_time:
                    processing_time = end_time - start_time
                else:
                    processing_time = time.time() - start_time
                
                stats["processing_time"] = processing_time
                stats["events_per_second"] = stats["processed_events"] / max(processing_time, 0.000001)
            
            stats["queue_size"] = self.get_queue_size()
            stats["handler_count"] = self.get_handler_count()
            
            return stats
    
    def _process_events(self):
        """
        事件处理循环，在单独线程中运行
        """
        thread_name = threading.current_thread().name
        thread_id = threading.get_ident()
        
        self.logger.info(f"🚀 事件处理线程启动: {thread_name} (ID: {thread_id})")
        
        processed_in_session = 0
        last_progress_time = time.time()
        progress_interval = 5.0  # 每5秒输出一次进度
        
        while not self._stop_event_processing.is_set():
            try:
                # 周期性输出进度
                current_time = time.time()
                if (current_time - last_progress_time) >= progress_interval:
                    queue_size = self.get_queue_size()
                    self.logger.debug(f"📊 事件处理进度: 已处理={processed_in_session}, 队列大小={queue_size}")
                    last_progress_time = current_time
                
                # 等待恢复（如果暂停）
                if not self._pause_event.wait(timeout=0.1):
                    continue
                
                # 检查停止信号
                if self._stop_event_processing.is_set():
                    break
                
                # 获取事件
                try:
                    event = self._event_queue.get(block=True, timeout=0.1)
                except queue.Empty:
                    continue
                
                # 检查停止信号
                if event is None or self._stop_event_processing.is_set():
                    break
                
                # 分发事件
                dispatch_start = time.time()
                success = self._dispatch_event(event)
                dispatch_time = time.time() - dispatch_start
                
                # 更新统计
                with self._lock:
                    self._performance_stats["processed_events"] += 1
                    if not success:
                        self._performance_stats["failed_events"] += 1
                
                processed_in_session += 1
                
                # 标记任务完成
                self._event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"事件处理循环异常: {e}", exc_info=True)
                with self._lock:
                    self._performance_stats["handler_errors"] += 1
        
        self.logger.info(f"🏁 事件处理线程结束: 本次处理={processed_in_session}, 总处理={self._performance_stats['processed_events']}")
    
    def _dispatch_event(self, event: CoreEvent) -> bool:
        """
        分发事件到处理器
        
        Parameters
        ----------
        event : CoreEvent
            要分发的事件
            
        Returns
        -------
        bool
            分发是否成功
        """
        try:
            event_type = getattr(event, 'event_type', 'Unknown')
            
            handlers_to_call = []
            with self._lock:
                # 获取特定类型的处理器
                if event_type in self._event_handlers:
                    handlers_to_call.extend(self._event_handlers[event_type])
                
                # 获取通配符处理器
                if "*" in self._event_handlers:
                    handlers_to_call.extend(self._event_handlers["*"])
            
            if not handlers_to_call:
                return True  # 没有处理器不算失败
            
            # 调用所有处理器
            success_count = 0
            for handler in handlers_to_call:
                try:
                    handler(event)
                    success_count += 1
                except Exception as e:
                    handler_name = getattr(handler, '__name__', str(handler))
                    self.logger.error(f"处理器 {handler_name} 处理事件 {event_type} 时出错: {e}")
                    with self._lock:
                        self._performance_stats["handler_errors"] += 1
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"事件分发异常: {e}", exc_info=True)
            return False
