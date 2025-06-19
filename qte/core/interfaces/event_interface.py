"""
事件系统接口定义

定义了统一的事件处理接口，支持不同的事件总线实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EventMetadata:
    """事件元数据"""
    event_id: str
    timestamp: datetime
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def should_retry(self) -> bool:
        """判断是否应该重试"""
        return self.retry_count < self.max_retries


class IEventHandler(ABC):
    """
    事件处理器接口
    
    定义了事件处理器的基本接口
    """
    
    @abstractmethod
    def handle(self, event: Any, metadata: EventMetadata) -> bool:
        """
        处理事件
        
        Args:
            event: 事件对象
            metadata: 事件元数据
            
        Returns:
            bool: 处理是否成功
        """
        pass
    
    @abstractmethod
    def get_supported_event_types(self) -> List[str]:
        """
        获取支持的事件类型
        
        Returns:
            List[str]: 支持的事件类型列表
        """
        pass
    
    def get_handler_name(self) -> str:
        """
        获取处理器名称
        
        Returns:
            str: 处理器名称
        """
        return self.__class__.__name__
    
    def get_priority(self) -> EventPriority:
        """
        获取处理器优先级
        
        Returns:
            EventPriority: 处理器优先级
        """
        return EventPriority.NORMAL
    
    def can_handle_async(self) -> bool:
        """
        是否支持异步处理
        
        Returns:
            bool: 是否支持异步处理
        """
        return False


class IEventSubscriber(ABC):
    """
    事件订阅者接口
    
    定义了事件订阅的基本接口
    """
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Union[IEventHandler, Callable]) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器或处理函数
            
        Returns:
            str: 订阅ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 取消是否成功
        """
        pass
    
    @abstractmethod
    def unsubscribe_all(self, event_type: Optional[str] = None) -> int:
        """
        取消所有订阅
        
        Args:
            event_type: 事件类型，None表示取消所有类型的订阅
            
        Returns:
            int: 取消的订阅数量
        """
        pass


class IEventBus(ABC):
    """
    事件总线接口
    
    定义了事件发布、订阅和处理的统一接口
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 取消是否成功
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        启动事件总线
        
        Returns:
            bool: 启动是否成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        停止事件总线
        
        Returns:
            bool: 停止是否成功
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取事件总线统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    # 可选的高级接口
    def publish_batch(self, events: List[Dict[str, Any]]) -> List[str]:
        """
        批量发布事件
        
        Args:
            events: 事件列表，每个事件包含type、data等字段
            
        Returns:
            List[str]: 事件ID列表
        """
        event_ids = []
        for event in events:
            event_id = self.publish(
                event_type=event.get('type'),
                event_data=event.get('data'),
                priority=event.get('priority', EventPriority.NORMAL),
                metadata=event.get('metadata')
            )
            event_ids.append(event_id)
        return event_ids
    
    def get_event_types(self) -> List[str]:
        """
        获取所有已注册的事件类型
        
        Returns:
            List[str]: 事件类型列表
        """
        return []
    
    def get_subscribers_count(self, event_type: str) -> int:
        """
        获取指定事件类型的订阅者数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 订阅者数量
        """
        return 0
    
    def clear_all(self) -> bool:
        """
        清空所有事件和订阅
        
        Returns:
            bool: 清空是否成功
        """
        return True
