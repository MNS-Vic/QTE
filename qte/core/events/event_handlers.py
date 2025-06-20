#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件处理器

插件化的事件处理器接口和基类
"""

import abc
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set, Type
from datetime import datetime

from .event_types import Event, EventType, EventPriority
from .event_bus import EventMetadata


class EventHandlerInterface(abc.ABC):
    """
    事件处理器接口
    
    定义了事件处理器必须实现的方法
    """
    
    @abc.abstractmethod
    def handle(self, event: Any, metadata: EventMetadata) -> bool:
        """
        处理事件
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            处理是否成功
        """
        pass
    
    @abc.abstractmethod
    def get_supported_event_types(self) -> List[str]:
        """
        获取支持的事件类型
        
        Returns
        -------
        List[str]
            支持的事件类型列表
        """
        pass
    
    def get_handler_name(self) -> str:
        """
        获取处理器名称
        
        Returns
        -------
        str
            处理器名称
        """
        return self.__class__.__name__
    
    def get_priority(self) -> EventPriority:
        """
        获取处理器优先级
        
        Returns
        -------
        EventPriority
            处理器优先级
        """
        return EventPriority.NORMAL
    
    def can_handle_async(self) -> bool:
        """
        是否支持异步处理
        
        Returns
        -------
        bool
            是否支持异步处理
        """
        return False
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化处理器
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数, by default None
            
        Returns
        -------
        bool
            初始化是否成功
        """
        return True
    
    def cleanup(self) -> bool:
        """
        清理处理器资源
        
        Returns
        -------
        bool
            清理是否成功
        """
        return True


class EventHandler(EventHandlerInterface):
    """
    事件处理器基类
    
    提供事件处理器的基础实现
    """
    
    def __init__(self, name: str = None, 
                 supported_events: List[str] = None,
                 priority: EventPriority = EventPriority.NORMAL):
        """
        初始化事件处理器
        
        Parameters
        ----------
        name : str, optional
            处理器名称, by default None
        supported_events : List[str], optional
            支持的事件类型, by default None
        priority : EventPriority, optional
            处理器优先级, by default EventPriority.NORMAL
        """
        self.name = name or self.__class__.__name__
        self.supported_events = supported_events or []
        self.priority = priority
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 处理统计
        self.stats = {
            'events_handled': 0,
            'events_failed': 0,
            'last_handled': None,
            'created_at': datetime.now()
        }
        
        self._initialized = False
        self._config = {}
    
    def handle(self, event: Any, metadata: EventMetadata) -> bool:
        """
        处理事件
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            处理是否成功
        """
        try:
            # 检查是否支持该事件类型
            if not self._can_handle_event(event, metadata):
                return True  # 不支持的事件类型不算失败
            
            # 调用具体的处理逻辑
            success = self._handle_event(event, metadata)
            
            # 更新统计
            if success:
                self.stats['events_handled'] += 1
                self.stats['last_handled'] = datetime.now()
            else:
                self.stats['events_failed'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"处理事件失败: {e}", exc_info=True)
            self.stats['events_failed'] += 1
            return False
    
    def _can_handle_event(self, event: Any, metadata: EventMetadata) -> bool:
        """
        检查是否可以处理该事件
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            是否可以处理
        """
        if not self.supported_events:
            return True  # 如果没有指定支持的事件类型，则处理所有事件
        
        # 获取事件类型
        event_type = getattr(event, 'event_type', None)
        if event_type is None:
            event_type = metadata.event_id  # 使用元数据中的事件ID作为类型
        
        return event_type in self.supported_events or "*" in self.supported_events
    
    def _handle_event(self, event: Any, metadata: EventMetadata) -> bool:
        """
        具体的事件处理逻辑（子类重写）
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            处理是否成功
        """
        # 默认实现：记录日志
        self.logger.debug(f"处理事件: {getattr(event, 'event_type', 'Unknown')} [{metadata.event_id}]")
        return True
    
    def get_supported_event_types(self) -> List[str]:
        """获取支持的事件类型"""
        return self.supported_events.copy()
    
    def get_handler_name(self) -> str:
        """获取处理器名称"""
        return self.name
    
    def get_priority(self) -> EventPriority:
        """获取处理器优先级"""
        return self.priority
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化处理器
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数, by default None
            
        Returns
        -------
        bool
            初始化是否成功
        """
        try:
            self._config = config or {}
            self._initialized = True
            self.logger.info(f"✅ 事件处理器 {self.name} 已初始化")
            return True
        except Exception as e:
            self.logger.error(f"初始化事件处理器失败: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        清理处理器资源
        
        Returns
        -------
        bool
            清理是否成功
        """
        try:
            self._initialized = False
            self.logger.info(f"✅ 事件处理器 {self.name} 已清理")
            return True
        except Exception as e:
            self.logger.error(f"清理事件处理器失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        stats = self.stats.copy()
        stats['name'] = self.name
        stats['priority'] = self.priority.name
        stats['supported_events'] = self.supported_events
        stats['initialized'] = self._initialized
        return stats


class AsyncEventHandler(EventHandler):
    """
    异步事件处理器
    
    支持异步事件处理的处理器基类
    """
    
    def __init__(self, name: str = None, 
                 supported_events: List[str] = None,
                 priority: EventPriority = EventPriority.NORMAL):
        """
        初始化异步事件处理器
        
        Parameters
        ----------
        name : str, optional
            处理器名称, by default None
        supported_events : List[str], optional
            支持的事件类型, by default None
        priority : EventPriority, optional
            处理器优先级, by default EventPriority.NORMAL
        """
        super().__init__(name, supported_events, priority)
        self._loop = None
    
    def can_handle_async(self) -> bool:
        """是否支持异步处理"""
        return True
    
    async def handle_async(self, event: Any, metadata: EventMetadata) -> bool:
        """
        异步处理事件
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            处理是否成功
        """
        try:
            # 检查是否支持该事件类型
            if not self._can_handle_event(event, metadata):
                return True
            
            # 调用异步处理逻辑
            success = await self._handle_event_async(event, metadata)
            
            # 更新统计
            if success:
                self.stats['events_handled'] += 1
                self.stats['last_handled'] = datetime.now()
            else:
                self.stats['events_failed'] += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"异步处理事件失败: {e}", exc_info=True)
            self.stats['events_failed'] += 1
            return False
    
    async def _handle_event_async(self, event: Any, metadata: EventMetadata) -> bool:
        """
        具体的异步事件处理逻辑（子类重写）
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            处理是否成功
        """
        # 默认实现：异步记录日志
        await asyncio.sleep(0)  # 让出控制权
        self.logger.debug(f"异步处理事件: {getattr(event, 'event_type', 'Unknown')} [{metadata.event_id}]")
        return True
    
    def _handle_event(self, event: Any, metadata: EventMetadata) -> bool:
        """
        同步处理事件（转换为异步调用）
        
        Parameters
        ----------
        event : Any
            事件对象
        metadata : EventMetadata
            事件元数据
            
        Returns
        -------
        bool
            处理是否成功
        """
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 运行异步处理
            return loop.run_until_complete(self.handle_async(event, metadata))
            
        except Exception as e:
            self.logger.error(f"异步事件处理转换失败: {e}")
            return False


class HandlerRegistry:
    """
    处理器注册表
    
    管理事件处理器的注册、查找和生命周期
    """
    
    def __init__(self):
        """初始化处理器注册表"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 处理器存储
        self._handlers: Dict[str, EventHandlerInterface] = {}
        self._handlers_by_type: Dict[str, List[str]] = {}
        self._handler_classes: Dict[str, Type[EventHandlerInterface]] = {}
        
        # 统计信息
        self._stats = {
            'registered_handlers': 0,
            'active_handlers': 0,
            'handler_calls': 0,
            'handler_errors': 0
        }
        
        self.logger.info("✅ 处理器注册表初始化完成")
    
    def register_handler(self, handler: EventHandlerInterface, 
                        handler_id: str = None) -> str:
        """
        注册事件处理器
        
        Parameters
        ----------
        handler : EventHandlerInterface
            事件处理器实例
        handler_id : str, optional
            处理器ID, by default None
            
        Returns
        -------
        str
            处理器ID
        """
        try:
            if handler_id is None:
                handler_id = f"{handler.get_handler_name()}_{len(self._handlers)}"
            
            if handler_id in self._handlers:
                self.logger.warning(f"处理器ID已存在: {handler_id}")
                return handler_id
            
            # 注册处理器
            self._handlers[handler_id] = handler
            
            # 按事件类型索引
            supported_types = handler.get_supported_event_types()
            for event_type in supported_types:
                if event_type not in self._handlers_by_type:
                    self._handlers_by_type[event_type] = []
                self._handlers_by_type[event_type].append(handler_id)
            
            # 更新统计
            self._stats['registered_handlers'] += 1
            self._stats['active_handlers'] = len(self._handlers)
            
            self.logger.info(f"✅ 已注册事件处理器: {handler.get_handler_name()} [{handler_id}]")
            return handler_id
            
        except Exception as e:
            self.logger.error(f"注册事件处理器失败: {e}")
            return ""
    
    def unregister_handler(self, handler_id: str) -> bool:
        """
        注销事件处理器
        
        Parameters
        ----------
        handler_id : str
            处理器ID
            
        Returns
        -------
        bool
            注销是否成功
        """
        try:
            if handler_id not in self._handlers:
                self.logger.warning(f"处理器ID不存在: {handler_id}")
                return False
            
            handler = self._handlers[handler_id]
            
            # 从事件类型索引中移除
            supported_types = handler.get_supported_event_types()
            for event_type in supported_types:
                if event_type in self._handlers_by_type:
                    if handler_id in self._handlers_by_type[event_type]:
                        self._handlers_by_type[event_type].remove(handler_id)
                    
                    # 如果该事件类型没有处理器了，删除键
                    if not self._handlers_by_type[event_type]:
                        del self._handlers_by_type[event_type]
            
            # 清理处理器
            handler.cleanup()
            
            # 从注册表中移除
            del self._handlers[handler_id]
            
            # 更新统计
            self._stats['active_handlers'] = len(self._handlers)
            
            self.logger.info(f"✅ 已注销事件处理器: {handler.get_handler_name()} [{handler_id}]")
            return True
            
        except Exception as e:
            self.logger.error(f"注销事件处理器失败: {e}")
            return False
    
    def get_handlers_for_event(self, event_type: str) -> List[EventHandlerInterface]:
        """
        获取处理指定事件类型的处理器
        
        Parameters
        ----------
        event_type : str
            事件类型
            
        Returns
        -------
        List[EventHandlerInterface]
            处理器列表
        """
        handlers = []
        
        # 获取特定事件类型的处理器
        if event_type in self._handlers_by_type:
            for handler_id in self._handlers_by_type[event_type]:
                if handler_id in self._handlers:
                    handlers.append(self._handlers[handler_id])
        
        # 获取通配符处理器
        if "*" in self._handlers_by_type:
            for handler_id in self._handlers_by_type["*"]:
                if handler_id in self._handlers:
                    handlers.append(self._handlers[handler_id])
        
        # 按优先级排序
        handlers.sort(key=lambda h: h.get_priority().value)
        
        return handlers
    
    def get_handler(self, handler_id: str) -> Optional[EventHandlerInterface]:
        """
        获取指定ID的处理器
        
        Parameters
        ----------
        handler_id : str
            处理器ID
            
        Returns
        -------
        Optional[EventHandlerInterface]
            处理器实例，如果不存在返回None
        """
        return self._handlers.get(handler_id)
    
    def list_handlers(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有处理器
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            处理器信息字典
        """
        handlers_info = {}
        
        for handler_id, handler in self._handlers.items():
            handlers_info[handler_id] = {
                'name': handler.get_handler_name(),
                'priority': handler.get_priority().name,
                'supported_events': handler.get_supported_event_types(),
                'can_async': handler.can_handle_async(),
                'stats': getattr(handler, 'stats', {}) if hasattr(handler, 'stats') else {}
            }
        
        return handlers_info
    
    def get_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        return self._stats.copy()
    
    def cleanup_all(self) -> bool:
        """清理所有处理器"""
        try:
            handler_ids = list(self._handlers.keys())
            for handler_id in handler_ids:
                self.unregister_handler(handler_id)
            
            self.logger.info("✅ 已清理所有事件处理器")
            return True
            
        except Exception as e:
            self.logger.error(f"清理所有处理器失败: {e}")
            return False
