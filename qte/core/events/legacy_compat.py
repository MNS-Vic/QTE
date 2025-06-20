#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向后兼容性接口

提供与原有事件系统的兼容性，确保现有代码无需修改
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from queue import Queue

from .event_types import Event as NewEvent, EventType, EventPriority
from .event_bus import EventBus
from .event_handlers import EventHandler


class LegacyEvent:
    """
    兼容原有Event类的接口
    
    提供与原有Event类相同的接口，内部使用新的Event实现
    """
    
    def __init__(self, event_type: str, timestamp: Optional[datetime] = None, **kwargs):
        """
        初始化兼容事件
        
        Parameters
        ----------
        event_type : str
            事件类型
        timestamp : Optional[datetime], optional
            事件时间戳, by default None
        **kwargs
            额外属性
        """
        # 创建新的Event实例
        self._new_event = NewEvent(
            event_type=event_type,
            timestamp=timestamp,
            metadata=kwargs
        )
        
        # 设置额外属性（兼容原有行为）
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @property
    def event_type(self) -> str:
        """获取事件类型"""
        return self._new_event.event_type
    
    @event_type.setter
    def event_type(self, value: str):
        """设置事件类型"""
        self._new_event.event_type = value
    
    @property
    def timestamp(self) -> datetime:
        """获取时间戳"""
        return self._new_event.timestamp
    
    @timestamp.setter
    def timestamp(self, value: datetime):
        """设置时间戳"""
        self._new_event.timestamp = value
    
    @property
    def event_id(self) -> str:
        """获取事件ID"""
        return self._new_event.event_id
    
    def get_new_event(self) -> NewEvent:
        """获取内部的新Event实例"""
        return self._new_event
    
    def __str__(self):
        return str(self._new_event)


class LegacyEventEngine:
    """
    兼容原有EventEngine的接口
    
    提供与原有EventEngine相同的接口，内部使用新的事件系统
    """
    
    def __init__(self):
        """初始化兼容事件引擎"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 创建新的事件系统组件
        self.event_bus = EventBus()
        
        # 兼容性存储
        self._legacy_handlers: Dict[str, List[Callable]] = {}
        self._handler_subscriptions: Dict[str, List[str]] = {}
        
        # 模拟原有的队列接口
        self._queue = Queue()
        
        # 启动事件总线
        self.event_bus.start()
        
        self.logger.info("✅ 兼容事件引擎初始化完成")
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        注册事件处理器（兼容原有接口）
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable
            处理函数
        """
        try:
            # 存储到兼容性列表
            if event_type not in self._legacy_handlers:
                self._legacy_handlers[event_type] = []
                self._handler_subscriptions[event_type] = []
            
            if handler not in self._legacy_handlers[event_type]:
                self._legacy_handlers[event_type].append(handler)
                
                # 创建包装器处理器
                def handler_wrapper(event_data, metadata):
                    try:
                        # 转换为兼容事件对象
                        if hasattr(event_data, '_new_event'):
                            # 已经是LegacyEvent
                            legacy_event = event_data
                        elif isinstance(event_data, NewEvent):
                            # 新Event，转换为LegacyEvent
                            legacy_event = create_legacy_event(event_data)
                        else:
                            # 其他数据，创建LegacyEvent
                            legacy_event = LegacyEvent(event_type, metadata.timestamp)
                            for key, value in event_data.__dict__.items():
                                setattr(legacy_event, key, value)
                        
                        # 调用原有处理器
                        handler(legacy_event)
                        return True
                        
                    except Exception as e:
                        self.logger.error(f"兼容处理器执行失败: {e}")
                        return False
                
                # 订阅到新事件总线
                subscription_id = self.event_bus.subscribe(
                    event_type=event_type,
                    handler=handler_wrapper,
                    priority=EventPriority.NORMAL
                )
                
                self._handler_subscriptions[event_type].append(subscription_id)
            
            handler_name = getattr(handler, '__name__', str(handler))
            self.logger.debug(f"✅ 已注册兼容事件处理器: {event_type} -> {handler_name}")
            
        except Exception as e:
            self.logger.error(f"注册兼容事件处理器失败: {e}")
    
    def unregister_handler(self, event_type: str, handler: Callable) -> None:
        """
        注销事件处理器（兼容原有接口）
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable
            处理函数
        """
        try:
            if event_type in self._legacy_handlers:
                if handler in self._legacy_handlers[event_type]:
                    # 找到处理器的索引
                    handler_index = self._legacy_handlers[event_type].index(handler)
                    
                    # 取消订阅
                    if (event_type in self._handler_subscriptions and 
                        handler_index < len(self._handler_subscriptions[event_type])):
                        subscription_id = self._handler_subscriptions[event_type][handler_index]
                        self.event_bus.unsubscribe(subscription_id)
                        del self._handler_subscriptions[event_type][handler_index]
                    
                    # 从兼容性列表移除
                    self._legacy_handlers[event_type].remove(handler)
                    
                    handler_name = getattr(handler, '__name__', str(handler))
                    self.logger.debug(f"✅ 已注销兼容事件处理器: {event_type} -> {handler_name}")
            
        except Exception as e:
            self.logger.error(f"注销兼容事件处理器失败: {e}")
    
    def put(self, event: Union[LegacyEvent, NewEvent, Any]) -> None:
        """
        添加事件到队列（兼容原有接口）
        
        Parameters
        ----------
        event : Union[LegacyEvent, NewEvent, Any]
            事件对象
        """
        try:
            # 转换为新Event并发布
            if isinstance(event, LegacyEvent):
                new_event = event.get_new_event()
            elif isinstance(event, NewEvent):
                new_event = event
            else:
                # 尝试从对象属性创建事件
                event_type = getattr(event, 'event_type', 'UNKNOWN')
                timestamp = getattr(event, 'timestamp', None)
                
                new_event = NewEvent(
                    event_type=event_type,
                    timestamp=timestamp
                )
                
                # 复制其他属性到metadata
                for attr_name in dir(event):
                    if not attr_name.startswith('_') and attr_name not in ['event_type', 'timestamp']:
                        attr_value = getattr(event, attr_name)
                        if not callable(attr_value):
                            new_event.metadata[attr_name] = attr_value
            
            # 发布到新事件总线
            event_id = self.event_bus.publish(new_event)
            
            # 同时添加到兼容队列（用于process方法）
            self._queue.put(event)
            
            self.logger.debug(f"✅ 已发布兼容事件: {new_event.event_type} [{event_id}]")
            
        except Exception as e:
            self.logger.error(f"发布兼容事件失败: {e}")
    
    def process(self) -> bool:
        """
        处理一个事件（兼容原有接口）
        
        Returns
        -------
        bool
            是否处理了事件
        """
        try:
            if self._queue.empty():
                return False
            
            # 从兼容队列获取事件
            event = self._queue.get()
            
            # 事件已经通过put方法发布到新事件总线
            # 这里只是为了兼容原有的process接口
            return True
            
        except Exception as e:
            self.logger.error(f"处理兼容事件失败: {e}")
            return False
    
    def process_all(self) -> int:
        """
        处理所有事件（兼容原有接口）
        
        Returns
        -------
        int
            处理的事件数量
        """
        count = 0
        while self.process():
            count += 1
        return count
    
    def clear(self) -> None:
        """清空事件队列（兼容原有接口）"""
        while not self._queue.empty():
            self._queue.get()
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.event_bus.get_stats()
        stats['legacy_handlers'] = sum(len(handlers) for handlers in self._legacy_handlers.values())
        stats['queue_size'] = self.get_queue_size()
        return stats
    
    def shutdown(self):
        """关闭事件引擎"""
        try:
            # 清理所有处理器
            for event_type in list(self._legacy_handlers.keys()):
                handlers = self._legacy_handlers[event_type].copy()
                for handler in handlers:
                    self.unregister_handler(event_type, handler)
            
            # 停止事件总线
            self.event_bus.stop()
            
            self.logger.info("✅ 兼容事件引擎已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭兼容事件引擎失败: {e}")


def create_legacy_event(new_event: NewEvent) -> LegacyEvent:
    """
    从新Event创建兼容Event
    
    Parameters
    ----------
    new_event : NewEvent
        新的Event实例
        
    Returns
    -------
    LegacyEvent
        兼容的Event实例
    """
    # 创建兼容事件
    legacy_event = LegacyEvent(
        event_type=new_event.event_type,
        timestamp=new_event.timestamp
    )
    
    # 复制metadata中的属性
    for key, value in new_event.metadata.items():
        setattr(legacy_event, key, value)
    
    # 设置内部的新Event引用
    legacy_event._new_event = new_event
    
    return legacy_event


def create_new_event_from_legacy(legacy_event: LegacyEvent) -> NewEvent:
    """
    从兼容Event创建新Event
    
    Parameters
    ----------
    legacy_event : LegacyEvent
        兼容的Event实例
        
    Returns
    -------
    NewEvent
        新的Event实例
    """
    if hasattr(legacy_event, '_new_event'):
        return legacy_event._new_event
    
    # 创建新事件
    metadata = {}
    
    # 复制属性到metadata
    for attr_name in dir(legacy_event):
        if not attr_name.startswith('_') and attr_name not in ['event_type', 'timestamp']:
            attr_value = getattr(legacy_event, attr_name)
            if not callable(attr_value):
                metadata[attr_name] = attr_value
    
    new_event = NewEvent(
        event_type=legacy_event.event_type,
        timestamp=legacy_event.timestamp,
        metadata=metadata
    )
    
    return new_event


# 兼容性别名
Event = LegacyEvent
EventEngine = LegacyEventEngine
