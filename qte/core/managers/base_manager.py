#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础管理器接口和通用功能

定义了所有管理器的基础接口和通用枚举类型
"""

import abc
import logging
from enum import Enum
from datetime import datetime
from typing import Dict, List, Union, Optional, Any, Callable
from qte.core.events import Event as CoreEvent


class EngineType(Enum):
    """引擎类型枚举"""
    EVENT_DRIVEN = 1   # 事件驱动引擎
    VECTORIZED = 2     # 向量化引擎
    HYBRID = 3         # 混合引擎


class EngineStatus(Enum):
    """引擎状态枚举"""
    INITIALIZED = 1    # 已初始化
    RUNNING = 2        # 运行中
    PAUSED = 3         # 已暂停
    STOPPED = 4        # 已停止
    COMPLETED = 5      # 已完成
    ERROR = 6          # 错误状态


class EngineEvent:
    """引擎事件基类"""
    
    def __init__(self, event_type: str, timestamp: datetime = None, data: Any = None):
        """
        初始化引擎事件
        
        Parameters
        ----------
        event_type : str
            事件类型
        timestamp : datetime, optional
            事件时间戳，默认为当前时间
        data : Any, optional
            事件数据
        """
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now()
        self.data = data
        self.source = None  # 事件来源，可由发送者设置
        
    def __str__(self) -> str:
        return f"EngineEvent(type={self.event_type}, time={self.timestamp}, source={self.source})"


class MarketDataEvent(EngineEvent):
    """市场数据事件"""
    
    def __init__(self, timestamp: datetime, symbol: str, data: Dict[str, Any]):
        """
        初始化市场数据事件
        
        Parameters
        ----------
        timestamp : datetime
            事件时间戳
        symbol : str
            交易标的代码
        data : Dict[str, Any]
            市场数据，包含价格、交易量等信息
        """
        super().__init__("MARKET_DATA", timestamp, data)
        self.symbol = symbol
        
    def __str__(self) -> str:
        return f"MarketDataEvent(time={self.timestamp}, symbol={self.symbol})"


class EngineManagerInterface(abc.ABC):
    """
    引擎管理器接口类
    
    定义了引擎管理器必须实现的方法
    """
    
    @abc.abstractmethod
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化引擎管理器
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数, by default None
            
        Returns
        -------
        bool
            初始化是否成功
        """
        pass
    
    @abc.abstractmethod
    def start(self) -> bool:
        """
        启动引擎
        
        Returns
        -------
        bool
            启动是否成功
        """
        pass
    
    @abc.abstractmethod
    def pause(self) -> bool:
        """
        暂停引擎
        
        Returns
        -------
        bool
            暂停是否成功
        """
        pass
    
    @abc.abstractmethod
    def resume(self) -> bool:
        """
        恢复引擎
        
        Returns
        -------
        bool
            恢复是否成功
        """
        pass
    
    @abc.abstractmethod
    def stop(self) -> bool:
        """
        停止引擎
        
        Returns
        -------
        bool
            停止是否成功
        """
        pass
    
    @abc.abstractmethod
    def get_status(self) -> EngineStatus:
        """
        获取引擎状态
        
        Returns
        -------
        EngineStatus
            当前引擎状态
        """
        pass
    
    @abc.abstractmethod
    def send_event(self, event: CoreEvent) -> bool:
        """
        发送事件到引擎
        
        Parameters
        ----------
        event : CoreEvent
            要发送的事件
            
        Returns
        -------
        bool
            发送是否成功
        """
        pass
    
    @abc.abstractmethod
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
            处理器ID，用于注销
        """
        pass
    
    @abc.abstractmethod
    def unregister_event_handler(self, handler_id: int) -> bool:
        """
        注销事件处理器
        
        Parameters
        ----------
        handler_id : int
            处理器ID
            
        Returns
        -------
        bool
            注销是否成功
        """
        pass
    
    @abc.abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        pass


class BaseManager:
    """
    基础管理器类
    
    提供所有管理器的通用功能
    """
    
    def __init__(self, name: str = None):
        """
        初始化基础管理器
        
        Parameters
        ----------
        name : str, optional
            管理器名称
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self._initialized = False
        self._config = {}
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化管理器
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数
            
        Returns
        -------
        bool
            初始化是否成功
        """
        self._config = config or {}
        self._initialized = True
        self.logger.info(f"{self.name} 已初始化")
        return True
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置参数
        
        Parameters
        ----------
        config : Dict[str, Any]
            配置参数
            
        Returns
        -------
        bool
            配置是否有效
        """
        # 子类可以重写此方法进行具体验证
        return True
