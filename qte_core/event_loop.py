#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件循环模块

实现事件驱动的回测系统的核心事件循环
"""

import queue
import logging
from typing import Optional, List, Callable, Any

from qte_core.events import Event

logger = logging.getLogger(__name__)

class EventLoop:
    """
    事件循环类
    
    管理事件队列和事件处理
    """
    
    def __init__(self, max_size: int = 0):
        """
        初始化事件循环
        
        Args:
            max_size: 事件队列最大长度，0表示无限制
        """
        self.event_queue = queue.Queue(maxsize=max_size)
        self.handlers = {}  # 事件处理器字典，格式为：{事件类型: [处理函数列表]}
        self.continue_backtest = True  # 是否继续回测
    
    def register_handler(self, event_type: str, handler_func: Callable[[Event], None]):
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler_func: 事件处理函数，接收一个Event参数
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        if handler_func not in self.handlers[event_type]:
            self.handlers[event_type].append(handler_func)
            logger.debug(f"已注册事件处理器: {event_type} -> {handler_func.__name__}")
    
    def unregister_handler(self, event_type: str, handler_func: Callable[[Event], None]):
        """
        注销事件处理器
        
        Args:
            event_type: 事件类型
            handler_func: 事件处理函数
        """
        if event_type in self.handlers and handler_func in self.handlers[event_type]:
            self.handlers[event_type].remove(handler_func)
            logger.debug(f"已注销事件处理器: {event_type} -> {handler_func.__name__}")
    
    def put_event(self, event: Event):
        """
        添加事件到队列
        
        Args:
            event: 事件对象
        """
        self.event_queue.put(event)
    
    def get_next_event(self) -> Optional[Event]:
        """
        获取下一个事件
        
        Returns:
            Event: 事件对象，如果队列为空则返回None
        """
        if self.event_queue.empty():
            return None
        
        return self.event_queue.get()
    
    def dispatch_event(self, event: Event) -> bool:
        """
        分发事件到对应的处理器
        
        Args:
            event: 事件对象
            
        Returns:
            bool: 是否成功处理事件
        """
        if event.event_type in self.handlers:
            for handler_func in self.handlers[event.event_type]:
                try:
                    handler_func(event)
                except Exception as e:
                    logger.error(f"处理事件时出错: {e}")
                    return False
            return True
        
        logger.warning(f"未找到事件类型 {event.event_type} 的处理器")
        return False
    
    def run(self, max_events: Optional[int] = None) -> int:
        """
        运行事件循环
        
        处理队列中的事件，直到队列为空或达到最大事件数量
        
        Args:
            max_events: 处理的最大事件数量，None表示处理所有事件
            
        Returns:
            int: 处理的事件数量
        """
        if max_events is not None and max_events <= 0:
            return 0
        
        processed = 0
        
        while self.continue_backtest:
            if max_events is not None and processed >= max_events:
                break
            
            event = self.get_next_event()
            if event is None:
                break
            
            self.dispatch_event(event)
            processed += 1
        
        return processed
    
    def stop(self):
        """停止事件循环"""
        self.continue_backtest = False
    
    def __len__(self) -> int:
        """
        获取事件队列长度
        
        Returns:
            int: 队列中的事件数量
        """
        return self.event_queue.qsize() 