#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件总线

统一的事件发布、订阅和分发机制
"""

import time
import queue
import threading
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future

from .event_types import Event, EventType, EventPriority


@dataclass
class EventMetadata:
    """事件元数据"""
    event_id: str
    timestamp: datetime
    priority: EventPriority
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    
    def should_retry(self) -> bool:
        """是否应该重试"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """增加重试次数"""
        self.retry_count += 1


@dataclass
class EventRecord:
    """事件记录"""
    event_id: str
    event_type: str
    event_data: Any
    metadata: EventMetadata
    created_at: datetime = field(default_factory=datetime.now)
    processed_count: int = 0
    error_count: int = 0
    last_processed: Optional[datetime] = None
    last_error: Optional[str] = None
    
    def mark_processed(self):
        """标记为已处理"""
        self.processed_count += 1
        self.last_processed = datetime.now()
    
    def mark_error(self, error_msg: str):
        """标记错误"""
        self.error_count += 1
        self.last_error = error_msg


class EventBus:
    """
    事件总线
    
    提供统一的事件发布、订阅和分发机制
    """
    
    def __init__(self, max_queue_size: int = 10000, 
                 max_workers: int = 4,
                 enable_async: bool = True):
        """
        初始化事件总线
        
        Parameters
        ----------
        max_queue_size : int, optional
            最大队列大小, by default 10000
        max_workers : int, optional
            最大工作线程数, by default 4
        enable_async : bool, optional
            是否启用异步处理, by default True
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 配置
        self.max_queue_size = max_queue_size
        self.max_workers = max_workers
        self.enable_async = enable_async
        
        # 事件队列（优先级队列）
        self._event_queue = queue.PriorityQueue(maxsize=max_queue_size)
        
        # 订阅者管理
        self._subscribers: Dict[str, List[Callable]] = {}
        self._subscriber_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 事件记录
        self._event_records: Dict[str, EventRecord] = {}
        self._max_records = 10000  # 最大记录数
        
        # 线程控制
        self._processing_thread = None
        self._stop_processing = threading.Event()
        self._pause_processing = threading.Event()
        self._pause_processing.set()  # 开始时不暂停
        
        # 异步处理器
        self._executor = ThreadPoolExecutor(max_workers=max_workers) if enable_async else None
        self._async_futures: List[Future] = []
        
        # 统计信息
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'subscribers_count': 0,
            'processing_time_total': 0.0,
            'start_time': None
        }
        
        # 线程安全锁
        self._lock = threading.Lock()
        
        self.logger.info("✅ 事件总线初始化完成")
    
    def start(self) -> bool:
        """
        启动事件总线
        
        Returns
        -------
        bool
            启动是否成功
        """
        with self._lock:
            if self._processing_thread and self._processing_thread.is_alive():
                self.logger.warning("事件总线已在运行")
                return False
            
            self._stop_processing.clear()
            self._pause_processing.set()
            
            self._processing_thread = threading.Thread(
                target=self._processing_loop,
                name="EventBus_Processor"
            )
            self._processing_thread.daemon = True
            self._processing_thread.start()
            
            self._stats['start_time'] = time.time()
            
            self.logger.info("🚀 事件总线已启动")
            return True
    
    def stop(self) -> bool:
        """
        停止事件总线
        
        Returns
        -------
        bool
            停止是否成功
        """
        with self._lock:
            if not self._processing_thread or not self._processing_thread.is_alive():
                self.logger.info("事件总线未运行")
                return True
            
            self._stop_processing.set()
            self._pause_processing.set()
            
            # 发送停止信号
            try:
                self._event_queue.put((0, time.time(), None), block=False)
            except queue.Full:
                self.logger.warning("事件队列已满，无法发送停止信号")
            
            # 等待线程结束
            if self._processing_thread:
                self._processing_thread.join(timeout=5.0)
                if self._processing_thread.is_alive():
                    self.logger.warning("事件处理线程未在超时内结束")
                else:
                    self.logger.info("✅ 事件处理线程已停止")
            
            # 关闭异步执行器
            if self._executor:
                self._executor.shutdown(wait=True)
            
            self._processing_thread = None
            
            self.logger.info("⏹️ 事件总线已停止")
            return True
    
    def pause(self) -> bool:
        """暂停事件处理"""
        self._pause_processing.clear()
        self.logger.info("⏸️ 事件处理已暂停")
        return True
    
    def resume(self) -> bool:
        """恢复事件处理"""
        self._pause_processing.set()
        self.logger.info("▶️ 事件处理已恢复")
        return True
    
    def publish(self, event: Union[Event, str], 
                event_data: Any = None,
                priority: EventPriority = EventPriority.NORMAL,
                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        发布事件
        
        Parameters
        ----------
        event : Union[Event, str]
            事件对象或事件类型字符串
        event_data : Any, optional
            事件数据（当event为字符串时使用）
        priority : EventPriority, optional
            事件优先级, by default EventPriority.NORMAL
        metadata : Optional[Dict[str, Any]], optional
            额外元数据, by default None
            
        Returns
        -------
        str
            事件ID
        """
        try:
            # 处理事件对象
            if isinstance(event, Event):
                event_obj = event
                event_type = event.event_type
                event_data = event
            else:
                event_type = event
                event_obj = Event(
                    event_type=event_type,
                    priority=priority,
                    metadata=metadata or {}
                )
            
            # 创建事件元数据
            event_metadata = EventMetadata(
                event_id=event_obj.event_id,
                timestamp=event_obj.timestamp,
                priority=priority,
                source=metadata.get('source') if metadata else None,
                correlation_id=metadata.get('correlation_id') if metadata else None
            )
            
            # 创建事件记录
            event_record = EventRecord(
                event_id=event_obj.event_id,
                event_type=event_type,
                event_data=event_data or event_obj,
                metadata=event_metadata
            )
            
            # 存储事件记录
            with self._lock:
                self._event_records[event_obj.event_id] = event_record
                self._cleanup_old_records()
                self._stats['events_published'] += 1
            
            # 将事件放入队列（优先级值越小，优先级越高）
            priority_value = priority.value
            try:
                self._event_queue.put((priority_value, time.time(), event_record), block=False)
            except queue.Full:
                self.logger.error("事件队列已满，无法发布事件")
                return ""
            
            self.logger.debug(f"📤 事件已发布: {event_type} [{event_obj.event_id}]")
            return event_obj.event_id
            
        except Exception as e:
            self.logger.error(f"发布事件失败: {e}")
            return ""
    
    def subscribe(self, event_type: str, 
                  handler: Callable[[Any, EventMetadata], None],
                  priority: EventPriority = EventPriority.NORMAL,
                  async_handler: bool = False) -> str:
        """
        订阅事件
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable[[Any, EventMetadata], None]
            事件处理函数
        priority : EventPriority, optional
            处理器优先级, by default EventPriority.NORMAL
        async_handler : bool, optional
            是否异步处理, by default False
            
        Returns
        -------
        str
            订阅ID
        """
        try:
            subscription_id = str(uuid.uuid4())[:8]
            
            with self._lock:
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = []
                
                self._subscribers[event_type].append(handler)
                
                # 存储订阅元数据
                self._subscriber_metadata[subscription_id] = {
                    'event_type': event_type,
                    'handler': handler,
                    'priority': priority,
                    'async_handler': async_handler,
                    'created_at': datetime.now(),
                    'call_count': 0,
                    'error_count': 0
                }
                
                self._stats['subscribers_count'] = len(self._subscriber_metadata)
            
            handler_name = getattr(handler, '__name__', str(handler))
            self.logger.debug(f"✅ 已订阅事件: {event_type} -> {handler_name} [{subscription_id}]")
            
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"订阅事件失败: {e}")
            return ""
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Parameters
        ----------
        subscription_id : str
            订阅ID
            
        Returns
        -------
        bool
            取消是否成功
        """
        try:
            with self._lock:
                if subscription_id not in self._subscriber_metadata:
                    self.logger.warning(f"订阅ID不存在: {subscription_id}")
                    return False
                
                metadata = self._subscriber_metadata[subscription_id]
                event_type = metadata['event_type']
                handler = metadata['handler']
                
                # 从订阅列表中移除
                if event_type in self._subscribers and handler in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(handler)
                    
                    # 如果该事件类型没有订阅者了，删除键
                    if not self._subscribers[event_type]:
                        del self._subscribers[event_type]
                
                # 删除元数据
                del self._subscriber_metadata[subscription_id]
                self._stats['subscribers_count'] = len(self._subscriber_metadata)
            
            self.logger.debug(f"✅ 已取消订阅: {subscription_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"取消订阅失败: {e}")
            return False
    
    def get_queue_size(self) -> int:
        """获取事件队列大小"""
        return self._event_queue.qsize()
    
    def get_subscriber_count(self) -> int:
        """获取订阅者数量"""
        with self._lock:
            return len(self._subscriber_metadata)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats['queue_size'] = self.get_queue_size()
            stats['subscriber_count'] = self.get_subscriber_count()
            
            # 计算运行时间
            if stats['start_time']:
                stats['uptime'] = time.time() - stats['start_time']
                
                # 计算平均处理时间
                if stats['events_processed'] > 0:
                    stats['avg_processing_time'] = stats['processing_time_total'] / stats['events_processed']
                else:
                    stats['avg_processing_time'] = 0.0
            
            return stats
    
    def _processing_loop(self):
        """事件处理循环"""
        self.logger.info("🚀 事件处理线程启动")
        
        processed_count = 0
        
        while not self._stop_processing.is_set():
            try:
                # 等待恢复（如果暂停）
                if not self._pause_processing.wait(timeout=0.1):
                    continue
                
                # 获取事件
                try:
                    priority, timestamp, event_record = self._event_queue.get(block=True, timeout=0.1)
                except queue.Empty:
                    continue
                
                # 检查停止信号
                if event_record is None or self._stop_processing.is_set():
                    break
                
                # 处理事件
                start_time = time.time()
                success = self._process_event(event_record)
                processing_time = time.time() - start_time
                
                # 更新统计
                with self._lock:
                    if success:
                        self._stats['events_processed'] += 1
                        event_record.mark_processed()
                    else:
                        self._stats['events_failed'] += 1
                    
                    self._stats['processing_time_total'] += processing_time
                
                processed_count += 1
                
                # 标记任务完成
                self._event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"事件处理循环异常: {e}", exc_info=True)
        
        self.logger.info(f"🏁 事件处理线程结束，处理事件数: {processed_count}")
    
    def _process_event(self, event_record: EventRecord) -> bool:
        """处理单个事件"""
        try:
            event_type = event_record.event_type
            event_data = event_record.event_data
            metadata = event_record.metadata
            
            # 获取订阅者
            handlers = []
            with self._lock:
                if event_type in self._subscribers:
                    handlers.extend(self._subscribers[event_type])
                
                # 通配符订阅者
                if "*" in self._subscribers:
                    handlers.extend(self._subscribers["*"])
            
            if not handlers:
                return True  # 没有处理器不算失败
            
            # 执行处理器
            success_count = 0
            for handler in handlers:
                try:
                    # 查找处理器元数据
                    handler_metadata = None
                    for sub_id, meta in self._subscriber_metadata.items():
                        if meta['handler'] == handler:
                            handler_metadata = meta
                            break
                    
                    # 执行处理器
                    if handler_metadata and handler_metadata.get('async_handler') and self._executor:
                        # 异步执行
                        future = self._executor.submit(handler, event_data, metadata)
                        self._async_futures.append(future)
                        
                        # 清理已完成的future
                        self._async_futures = [f for f in self._async_futures if not f.done()]
                    else:
                        # 同步执行
                        handler(event_data, metadata)
                    
                    success_count += 1
                    
                    # 更新处理器统计
                    if handler_metadata:
                        handler_metadata['call_count'] += 1
                    
                except Exception as e:
                    handler_name = getattr(handler, '__name__', str(handler))
                    self.logger.error(f"处理器 {handler_name} 处理事件 {event_type} 时出错: {e}")
                    
                    # 更新错误统计
                    if handler_metadata:
                        handler_metadata['error_count'] += 1
                    
                    event_record.mark_error(str(e))
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"处理事件失败: {e}", exc_info=True)
            return False
    
    def _cleanup_old_records(self):
        """清理旧的事件记录"""
        if len(self._event_records) > self._max_records:
            # 保留最新的记录
            sorted_records = sorted(
                self._event_records.items(),
                key=lambda x: x[1].created_at,
                reverse=True
            )
            
            # 保留最新的80%记录
            keep_count = int(self._max_records * 0.8)
            records_to_keep = dict(sorted_records[:keep_count])
            
            self._event_records = records_to_keep
            self.logger.debug(f"清理事件记录，保留 {keep_count} 条记录")
