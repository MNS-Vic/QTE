"""
事件管理器 V2 - 统一的事件处理系统

提供统一的事件发布、订阅和处理机制，支持优先级、异步处理等高级特性
"""

import logging
import threading
import queue
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from ..interfaces.event_interface import (
    IEventBus, 
    IEventHandler, 
    EventPriority, 
    EventMetadata
)


@dataclass
class Subscription:
    """订阅信息"""
    subscription_id: str
    event_type: str
    handler: Union[IEventHandler, Callable]
    priority: EventPriority
    created_at: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    error_count: int = 0
    last_called: Optional[datetime] = None


@dataclass
class EventRecord:
    """事件记录"""
    event_id: str
    event_type: str
    event_data: Any
    metadata: EventMetadata
    published_at: datetime = field(default_factory=datetime.now)
    processed_count: int = 0
    error_count: int = 0


class EventManagerV2(IEventBus):
    """
    事件管理器 V2
    
    实现了IEventBus接口，提供统一的事件处理系统：
    - 事件发布和订阅
    - 优先级处理
    - 异步事件处理
    - 事件统计和监控
    """
    
    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        """
        初始化事件管理器
        
        Args:
            max_workers: 最大工作线程数
            queue_size: 事件队列大小
        """
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 事件队列
        self._event_queue = queue.PriorityQueue(maxsize=queue_size)
        
        # 订阅管理
        self._subscriptions: Dict[str, Subscription] = {}
        self._event_handlers: Dict[str, List[str]] = {}  # event_type -> subscription_ids
        
        # 事件记录
        self._event_records: Dict[str, EventRecord] = {}
        self._max_records = 10000  # 最大记录数
        
        # 线程管理
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._processing_thread = None
        self._running = False
        self._lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'subscriptions_created': 0,
            'handlers_executed': 0
        }
        
        self.logger.info(f"🔧 事件管理器V2初始化完成，工作线程数: {max_workers}")
    
    def start(self) -> bool:
        """
        启动事件总线
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if self._running:
                self.logger.warning("⚠️ 事件总线已经在运行")
                return True
            
            self._running = True
            
            # 启动事件处理线程
            self._processing_thread = threading.Thread(
                target=self._process_events,
                name="EventProcessor",
                daemon=True
            )
            self._processing_thread.start()
            
            self.logger.info("🚀 事件总线已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 事件总线启动失败: {e}")
            return False
    
    def stop(self) -> bool:
        """
        停止事件总线
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if not self._running:
                self.logger.warning("⚠️ 事件总线未在运行")
                return True
            
            self._running = False
            
            # 等待处理线程结束
            if self._processing_thread and self._processing_thread.is_alive():
                self._processing_thread.join(timeout=5.0)
            
            # 关闭线程池
            self._executor.shutdown(wait=True)
            
            self.logger.info("🔒 事件总线已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 事件总线停止失败: {e}")
            return False
    
    def publish(self, event_type: str, event_data: Any, 
                priority: EventPriority = EventPriority.NORMAL,
                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            priority: 事件优先级
            metadata: 额外的元数据
            
        Returns:
            str: 事件ID
        """
        try:
            # 生成事件ID
            event_id = str(uuid.uuid4())
            
            # 创建事件元数据
            event_metadata = EventMetadata(
                event_id=event_id,
                timestamp=datetime.now(),
                priority=priority,
                source=metadata.get('source') if metadata else None,
                correlation_id=metadata.get('correlation_id') if metadata else None
            )
            
            # 创建事件记录
            event_record = EventRecord(
                event_id=event_id,
                event_type=event_type,
                event_data=event_data,
                metadata=event_metadata
            )
            
            # 存储事件记录
            with self._lock:
                self._event_records[event_id] = event_record
                self._cleanup_old_records()
                self._stats['events_published'] += 1
            
            # 将事件放入队列
            # 优先级值越小，优先级越高
            priority_value = 5 - priority.value
            self._event_queue.put((priority_value, time.time(), event_record))
            
            self.logger.debug(f"📤 事件已发布: {event_type} [{event_id}]")
            return event_id
            
        except Exception as e:
            self.logger.error(f"❌ 事件发布失败: {e}")
            return ""
    
    def subscribe(self, event_type: str, handler: Union[IEventHandler, Callable],
                 priority: EventPriority = EventPriority.NORMAL) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            priority: 处理器优先级
            
        Returns:
            str: 订阅ID
        """
        try:
            # 生成订阅ID
            subscription_id = str(uuid.uuid4())
            
            # 创建订阅信息
            subscription = Subscription(
                subscription_id=subscription_id,
                event_type=event_type,
                handler=handler,
                priority=priority
            )
            
            with self._lock:
                # 存储订阅
                self._subscriptions[subscription_id] = subscription
                
                # 更新事件处理器映射
                if event_type not in self._event_handlers:
                    self._event_handlers[event_type] = []
                self._event_handlers[event_type].append(subscription_id)
                
                # 按优先级排序
                self._event_handlers[event_type].sort(
                    key=lambda sid: self._subscriptions[sid].priority.value,
                    reverse=True  # 高优先级在前
                )
                
                self._stats['subscriptions_created'] += 1
            
            handler_name = handler.__class__.__name__ if hasattr(handler, '__class__') else str(handler)
            self.logger.info(f"📝 事件订阅成功: {event_type} -> {handler_name} [{subscription_id}]")
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"❌ 事件订阅失败: {e}")
            return ""
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 取消是否成功
        """
        try:
            with self._lock:
                if subscription_id not in self._subscriptions:
                    return False
                
                subscription = self._subscriptions[subscription_id]
                event_type = subscription.event_type
                
                # 从订阅列表中移除
                del self._subscriptions[subscription_id]
                
                # 从事件处理器映射中移除
                if event_type in self._event_handlers:
                    if subscription_id in self._event_handlers[event_type]:
                        self._event_handlers[event_type].remove(subscription_id)
                    
                    # 如果没有处理器了，删除事件类型
                    if not self._event_handlers[event_type]:
                        del self._event_handlers[event_type]
            
            self.logger.info(f"🗑️ 取消订阅成功: [{subscription_id}]")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 取消订阅失败: {e}")
            return False
    
    def _process_events(self):
        """事件处理主循环"""
        self.logger.info("🔄 事件处理线程已启动")
        
        while self._running:
            try:
                # 从队列获取事件，超时1秒
                try:
                    priority, timestamp, event_record = self._event_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 处理事件
                self._handle_event(event_record)
                
                # 标记任务完成
                self._event_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"❌ 事件处理异常: {e}")
        
        self.logger.info("🔒 事件处理线程已停止")
    
    def _handle_event(self, event_record: EventRecord):
        """
        处理单个事件
        
        Args:
            event_record: 事件记录
        """
        event_type = event_record.event_type
        event_data = event_record.event_data
        metadata = event_record.metadata
        
        try:
            with self._lock:
                # 获取事件处理器
                handler_ids = self._event_handlers.get(event_type, [])
                if not handler_ids:
                    self.logger.debug(f"📭 没有找到事件处理器: {event_type}")
                    return
                
                # 复制处理器列表，避免在处理过程中被修改
                handler_ids = handler_ids.copy()
            
            # 处理每个处理器
            for handler_id in handler_ids:
                try:
                    subscription = self._subscriptions.get(handler_id)
                    if not subscription:
                        continue
                    
                    # 执行处理器
                    self._execute_handler(subscription, event_data, metadata)
                    
                    # 更新统计
                    with self._lock:
                        subscription.call_count += 1
                        subscription.last_called = datetime.now()
                        self._stats['handlers_executed'] += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ 处理器执行失败: {handler_id}, 错误: {e}")
                    
                    # 更新错误统计
                    with self._lock:
                        if handler_id in self._subscriptions:
                            self._subscriptions[handler_id].error_count += 1
                        event_record.error_count += 1
                        self._stats['events_failed'] += 1
            
            # 更新事件处理统计
            with self._lock:
                event_record.processed_count += 1
                self._stats['events_processed'] += 1
            
        except Exception as e:
            self.logger.error(f"❌ 事件处理失败: {event_type}, 错误: {e}")
    
    def _execute_handler(self, subscription: Subscription, event_data: Any, metadata: EventMetadata):
        """
        执行事件处理器
        
        Args:
            subscription: 订阅信息
            event_data: 事件数据
            metadata: 事件元数据
        """
        handler = subscription.handler
        
        if isinstance(handler, IEventHandler):
            # 使用IEventHandler接口
            handler.handle(event_data, metadata)
        elif callable(handler):
            # 使用可调用对象
            handler(event_data, metadata)
        else:
            raise ValueError(f"无效的事件处理器类型: {type(handler)}")
    
    def _cleanup_old_records(self):
        """清理旧的事件记录"""
        if len(self._event_records) > self._max_records:
            # 按时间排序，删除最旧的记录
            sorted_records = sorted(
                self._event_records.items(),
                key=lambda x: x[1].published_at
            )
            
            # 删除最旧的20%记录
            records_to_delete = int(self._max_records * 0.2)
            for i in range(records_to_delete):
                event_id, _ = sorted_records[i]
                del self._event_records[event_id]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取事件总线统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            return {
                'running': self._running,
                'queue_size': self._event_queue.qsize(),
                'total_subscriptions': len(self._subscriptions),
                'event_types_count': len(self._event_handlers),
                'event_records_count': len(self._event_records),
                'stats': self._stats.copy()
            }
    
    def get_event_types(self) -> List[str]:
        """
        获取所有已注册的事件类型
        
        Returns:
            List[str]: 事件类型列表
        """
        with self._lock:
            return list(self._event_handlers.keys())
    
    def get_subscribers_count(self, event_type: str) -> int:
        """
        获取指定事件类型的订阅者数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 订阅者数量
        """
        with self._lock:
            return len(self._event_handlers.get(event_type, []))
    
    def clear_all(self) -> bool:
        """
        清空所有事件和订阅
        
        Returns:
            bool: 清空是否成功
        """
        try:
            with self._lock:
                self._subscriptions.clear()
                self._event_handlers.clear()
                self._event_records.clear()
                
                # 清空队列
                while not self._event_queue.empty():
                    try:
                        self._event_queue.get_nowait()
                    except queue.Empty:
                        break
                
                # 重置统计
                self._stats = {
                    'events_published': 0,
                    'events_processed': 0,
                    'events_failed': 0,
                    'subscriptions_created': 0,
                    'handlers_executed': 0
                }
            
            self.logger.info("🧹 事件总线已清空")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 事件总线清空失败: {e}")
            return False
