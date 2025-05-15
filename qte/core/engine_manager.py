#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎管理器 - 整合向量化和事件驱动两种回测引擎
"""
import os
import time
import datetime
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Any, Tuple, Callable, Type
from qte.core.vector_engine import VectorEngine
from qte.core.event_engine import EventDrivenBacktester
from enum import Enum
import abc
import logging
import threading

# 导入数据重放相关类
from qte.data.data_replay import ReplayMode, ReplayStatus, DataReplayInterface

# 设置日志
logger = logging.getLogger("EngineManager")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
    
    def __init__(self, event_type: str, timestamp: datetime, data: Any = None):
        """
        初始化引擎事件
        
        Parameters
        ----------
        event_type : str
            事件类型
        timestamp : datetime
            事件时间戳
        data : Any, optional
            事件数据, by default None
        """
        self.event_type = event_type
        self.timestamp = timestamp
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

class SignalEvent(EngineEvent):
    """信号事件，由策略生成"""
    
    def __init__(self, timestamp: datetime, symbol: str, signal_type: str, strength: float = 1.0):
        """
        初始化信号事件
        
        Parameters
        ----------
        timestamp : datetime
            事件时间戳
        symbol : str
            交易标的代码
        signal_type : str
            信号类型，如"BUY"、"SELL"
        strength : float, optional
            信号强度, by default 1.0
        """
        super().__init__("SIGNAL", timestamp, {
            "symbol": symbol,
            "signal_type": signal_type,
            "strength": strength
        })
        self.symbol = symbol
        self.signal_type = signal_type
        self.strength = strength
        
    def __str__(self) -> str:
        return f"SignalEvent(time={self.timestamp}, symbol={self.symbol}, type={self.signal_type}, strength={self.strength})"

class OrderEvent(EngineEvent):
    """订单事件，由投资组合生成"""
    
    def __init__(self, timestamp: datetime, symbol: str, order_type: str, 
                 quantity: float, price: Optional[float] = None):
        """
        初始化订单事件
        
        Parameters
        ----------
        timestamp : datetime
            事件时间戳
        symbol : str
            交易标的代码
        order_type : str
            订单类型，如"MARKET"、"LIMIT"
        quantity : float
            数量，正数为买入，负数为卖出
        price : Optional[float], optional
            价格，对于限价单等需要指定, by default None
        """
        super().__init__("ORDER", timestamp, {
            "symbol": symbol,
            "order_type": order_type,
            "quantity": quantity,
            "price": price
        })
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.order_id = None  # 由执行系统填充
        
    def __str__(self) -> str:
        price_str = f", price={self.price}" if self.price is not None else ""
        return f"OrderEvent(time={self.timestamp}, symbol={self.symbol}, type={self.order_type}, qty={self.quantity}{price_str})"

class FillEvent(EngineEvent):
    """成交事件，由执行系统生成"""
    
    def __init__(self, timestamp: datetime, symbol: str, quantity: float, 
                 price: float, commission: float = 0.0, exchange: str = ""):
        """
        初始化成交事件
        
        Parameters
        ----------
        timestamp : datetime
            事件时间戳
        symbol : str
            交易标的代码
        quantity : float
            成交数量，正数为买入，负数为卖出
        price : float
            成交价格
        commission : float, optional
            佣金, by default 0.0
        exchange : str, optional
            交易所, by default ""
        """
        super().__init__("FILL", timestamp, {
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "commission": commission,
            "exchange": exchange
        })
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.commission = commission
        self.exchange = exchange
        self.order_id = None  # 关联的订单ID，由执行系统填充
        
    def __str__(self) -> str:
        return f"FillEvent(time={self.timestamp}, symbol={self.symbol}, qty={self.quantity}, price={self.price}, commission={self.commission})"

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
    def send_event(self, event: EngineEvent) -> bool:
        """
        发送事件到引擎
        
        Parameters
        ----------
        event : EngineEvent
            要发送的事件
            
        Returns
        -------
        bool
            发送是否成功
        """
        pass
    
    @abc.abstractmethod
    def register_event_handler(self, event_type: str, handler: Callable[[EngineEvent], None]) -> int:
        """
        注册事件处理器
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable[[EngineEvent], None]
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

class BaseEngineManager(EngineManagerInterface):
    """
    基础引擎管理器
    
    实现了基本的引擎管理功能
    """
    
    def __init__(self, engine_type: EngineType = EngineType.EVENT_DRIVEN):
        """
        初始化基础引擎管理器
        
        Parameters
        ----------
        engine_type : EngineType, optional
            引擎类型, by default EngineType.EVENT_DRIVEN
        """
        self._engine_type = engine_type
        self._status = EngineStatus.INITIALIZED
        self._event_handlers = {}  # 类型 -> {id: handler}
        self._handler_counter = 0
        self._lock = threading.Lock()
        self._event_queue = []
        self._event_thread = None
        self._event = threading.Event()
        self._config = {}
        self._start_time = None
        self._end_time = None
        self._processing_time = 0.0
        self._event_counts = {}  # 类型 -> 计数
    
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
        with self._lock:
            if config is not None:
                self._config.update(config)
            return True
    
    def start(self) -> bool:
        """
        启动引擎
        
        Returns
        -------
        bool
            启动是否成功
        """
        with self._lock:
            if self._status == EngineStatus.RUNNING:
                logger.warning("引擎已经在运行")
                return False
            
            self._status = EngineStatus.RUNNING
            self._event.set()  # 确保事件线程不被阻塞
            self._start_time = time.time()
            
            # 启动事件处理线程
            self._event_thread = threading.Thread(target=self._process_events)
            self._event_thread.daemon = True
            self._event_thread.start()
            
            logger.info(f"引擎已启动，类型: {self._engine_type.name}")
            return True
    
    def pause(self) -> bool:
        """
        暂停引擎
        
        Returns
        -------
        bool
            暂停是否成功
        """
        with self._lock:
            if self._status != EngineStatus.RUNNING:
                logger.warning(f"无法暂停，当前状态: {self._status.name}")
                return False
            
            self._status = EngineStatus.PAUSED
            self._event.clear()  # 暂停事件处理线程
            logger.info("引擎已暂停")
            return True
    
    def resume(self) -> bool:
        """
        恢复引擎
        
        Returns
        -------
        bool
            恢复是否成功
        """
        with self._lock:
            if self._status != EngineStatus.PAUSED:
                logger.warning(f"无法恢复，当前状态: {self._status.name}")
                return False
            
            self._status = EngineStatus.RUNNING
            self._event.set()  # 恢复事件处理线程
            logger.info("引擎已恢复")
            return True
    
    def stop(self) -> bool:
        """
        停止引擎
        
        Returns
        -------
        bool
            停止是否成功
        """
        with self._lock:
            if self._status in [EngineStatus.STOPPED, EngineStatus.COMPLETED]:
                logger.warning(f"引擎已经停止: {self._status.name}")
                return False
            
            prev_status = self._status
            self._status = EngineStatus.STOPPED
            self._event.set()  # 确保事件线程不被阻塞
            
            # 等待事件处理线程结束
            if prev_status == EngineStatus.RUNNING and self._event_thread is not None:
                self._event_thread.join(timeout=1.0)
            
            self._end_time = time.time()
            if self._start_time is not None:
                self._processing_time = self._end_time - self._start_time
            
            logger.info(f"引擎已停止，处理时间: {self._processing_time:.2f}秒")
            return True
    
    def get_status(self) -> EngineStatus:
        """
        获取引擎状态
        
        Returns
        -------
        EngineStatus
            当前引擎状态
        """
        with self._lock:
            return self._status
    
    def send_event(self, event: EngineEvent) -> bool:
        """
        发送事件到引擎
        
        Parameters
        ----------
        event : EngineEvent
            要发送的事件
        
        Returns
        -------
        bool
            发送是否成功
        """
        with self._lock:
            if self._status not in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
                logger.warning(f"无法发送事件，当前状态: {self._status.name}")
                return False
            
            self._event_queue.append(event)
            
            # 更新事件计数
            event_type = event.event_type
            self._event_counts[event_type] = self._event_counts.get(event_type, 0) + 1
            
            return True
    
    def register_event_handler(self, event_type: str, handler: Callable[[EngineEvent], None]) -> int:
        """
        注册事件处理器
        
        Parameters
        ----------
        event_type : str
            事件类型
        handler : Callable[[EngineEvent], None]
            事件处理函数
            
        Returns
        -------
        int
            处理器ID，用于注销
        """
        with self._lock:
            handler_id = self._handler_counter
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = {}
            
            self._event_handlers[event_type][handler_id] = handler
            self._handler_counter += 1
            
            return handler_id
    
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
        with self._lock:
            for event_type in self._event_handlers:
                if handler_id in self._event_handlers[event_type]:
                    del self._event_handlers[event_type][handler_id]
                    return True
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        with self._lock:
            stats = {
                "processing_time": self._processing_time,
                "event_counts": self._event_counts.copy(),
                "total_events": sum(self._event_counts.values()),
                "events_per_second": sum(self._event_counts.values()) / max(self._processing_time, 0.001)
            }
            return stats
    
    def _process_events(self):
        """事件处理线程的主函数"""
        try:
            while self._status == EngineStatus.RUNNING:
                # 等待事件，支持暂停/恢复
                self._event.wait()
                
                # 如果状态变更，则退出
                if self._status != EngineStatus.RUNNING:
                    break
                
                # 获取并处理事件
                events = []
                with self._lock:
                    if self._event_queue:
                        events = self._event_queue.copy()
                        self._event_queue.clear()
                
                # 处理事件
                for event in events:
                    self._dispatch_event(event)
                
                # 如果没有事件，短暂休眠以避免CPU过载
                if not events:
                    time.sleep(0.001)
                
        except Exception as e:
            logger.error(f"事件处理线程异常: {str(e)}")
            with self._lock:
                self._status = EngineStatus.ERROR
    
    def _dispatch_event(self, event: EngineEvent):
        """
        分发事件到对应的处理器
        
        Parameters
        ----------
        event : EngineEvent
            要分发的事件
        """
        try:
            # 获取该事件类型的所有处理器
            handlers = {}
            with self._lock:
                if event.event_type in self._event_handlers:
                    handlers = self._event_handlers[event.event_type].copy()
                
                # 获取通用处理器（处理所有类型的事件）
                if "*" in self._event_handlers:
                    handlers.update(self._event_handlers["*"])
            
            # 调用处理器
            for handler in handlers.values():
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"事件处理器异常: {str(e)}")
        except Exception as e:
            logger.error(f"事件分发异常: {str(e)}")

class ReplayEngineManager(BaseEngineManager):
    """
    数据重放引擎管理器
    
    集成了数据重放控制器，支持回测和模拟交易
    """
    
    def __init__(self, engine_type: EngineType = EngineType.EVENT_DRIVEN):
        """
        初始化数据重放引擎管理器
        
        Parameters
        ----------
        engine_type : EngineType, optional
            引擎类型, by default EngineType.EVENT_DRIVEN
        """
        super().__init__(engine_type)
        self._replay_controllers = {}  # 名称 -> 控制器
        self._replay_callbacks = {}    # 控制器 -> 回调ID
        self._symbol_mapping = {}      # 数据源标识 -> 标的代码
        self._data_converters = {}     # 数据源标识 -> 转换函数
    
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
        result = super().initialize(config)
        
        # 读取配置中的重放控制器
        if config and "replay_controllers" in config:
            for name, controller_config in config["replay_controllers"].items():
                controller = controller_config.get("controller")
                if controller and isinstance(controller, DataReplayInterface):
                    self.add_replay_controller(
                        name, 
                        controller, 
                        controller_config.get("symbol"),
                        controller_config.get("converter")
                    )
        
        return result
    
    def add_replay_controller(self, name: str, controller: DataReplayInterface, 
                              symbol: Optional[str] = None,
                              data_converter: Optional[Callable] = None) -> bool:
        """
        添加数据重放控制器
        
        Parameters
        ----------
        name : str
            控制器名称，用于标识不同的数据源
        controller : DataReplayInterface
            数据重放控制器实例
        symbol : Optional[str], optional
            关联的交易标的代码，如果为None则使用数据点中的信息, by default None
        data_converter : Optional[Callable], optional
            数据转换函数，用于将重放数据转换为引擎事件, by default None
            
        Returns
        -------
        bool
            添加是否成功
        """
        with self._lock:
            if name in self._replay_controllers:
                logger.warning(f"重放控制器 '{name}' 已存在")
                return False
            
            self._replay_controllers[name] = controller
            self._symbol_mapping[name] = symbol
            
            if data_converter is not None:
                self._data_converters[name] = data_converter
            
            logger.info(f"已添加重放控制器: {name}")
            return True
    
    def remove_replay_controller(self, name: str) -> bool:
        """
        移除数据重放控制器
        
        Parameters
        ----------
        name : str
            控制器名称
            
        Returns
        -------
        bool
            移除是否成功
        """
        with self._lock:
            if name not in self._replay_controllers:
                logger.warning(f"重放控制器 '{name}' 不存在")
                return False
            
            controller = self._replay_controllers[name]
            
            # 注销回调
            if controller in self._replay_callbacks:
                controller.unregister_callback(self._replay_callbacks[controller])
                del self._replay_callbacks[controller]
            
            del self._replay_controllers[name]
            
            if name in self._symbol_mapping:
                del self._symbol_mapping[name]
                
            if name in self._data_converters:
                del self._data_converters[name]
            
            logger.info(f"已移除重放控制器: {name}")
            return True
    
    def start(self) -> bool:
        """
        启动引擎和所有重放控制器
        
        Returns
        -------
        bool
            启动是否成功
        """
        with self._lock:
            # 先启动引擎
            if not super().start():
                return False
            
            # 为所有控制器注册回调
            for name, controller in self._replay_controllers.items():
                callback_id = controller.register_callback(
                    lambda data, src=name: self._on_replay_data(src, data)
                )
                self._replay_callbacks[controller] = callback_id
            
            # 启动所有控制器
            for name, controller in self._replay_controllers.items():
                controller.start()
                logger.info(f"已启动重放控制器: {name}")
            
            return True
    
    def pause(self) -> bool:
        """
        暂停引擎和所有重放控制器
        
        Returns
        -------
        bool
            暂停是否成功
        """
        with self._lock:
            # 暂停所有控制器
            for name, controller in self._replay_controllers.items():
                controller.pause()
                logger.info(f"已暂停重放控制器: {name}")
            
            # 暂停引擎
            return super().pause()
    
    def resume(self) -> bool:
        """
        恢复引擎和所有重放控制器
        
        Returns
        -------
        bool
            恢复是否成功
        """
        with self._lock:
            # 先恢复引擎
            if not super().resume():
                return False
            
            # 恢复所有控制器
            for name, controller in self._replay_controllers.items():
                controller.resume()
                logger.info(f"已恢复重放控制器: {name}")
            
            return True
    
    def stop(self) -> bool:
        """
        停止引擎和所有重放控制器
        
        Returns
        -------
        bool
            停止是否成功
        """
        with self._lock:
            # 停止所有控制器
            for name, controller in self._replay_controllers.items():
                controller.stop()
                logger.info(f"已停止重放控制器: {name}")
            
            # 停止引擎
            return super().stop()
    
    def set_replay_mode(self, mode: ReplayMode) -> bool:
        """
        设置所有重放控制器的模式
        
        Parameters
        ----------
        mode : ReplayMode
            重放模式
        
        Returns
        -------
        bool
            设置是否成功
        """
        with self._lock:
            success = True
            for name, controller in self._replay_controllers.items():
                if not controller.set_mode(mode):
                    logger.warning(f"无法设置控制器 '{name}' 的模式: {mode.name}")
                    success = False
            
            return success
    
    def set_replay_speed(self, speed_factor: float) -> bool:
        """
        设置所有重放控制器的速度
        
        Parameters
        ----------
        speed_factor : float
            速度因子
            
        Returns
        -------
        bool
            设置是否成功
        """
        with self._lock:
            success = True
            for name, controller in self._replay_controllers.items():
                if not controller.set_speed(speed_factor):
                    logger.warning(f"无法设置控制器 '{name}' 的速度: {speed_factor}")
                    success = False
            
            return success
    
    def _on_replay_data(self, source: str, data: Any):
        """
        数据重放回调
        
        Parameters
        ----------
        source : str
            数据源标识
        data : Any
            重放数据
        """
        try:
            # 获取关联的标的代码
            symbol = self._symbol_mapping.get(source)
            if symbol is None:
                # 尝试从数据中获取标的代码
                if isinstance(data, dict) and "symbol" in data:
                    symbol = data["symbol"]
                elif hasattr(data, "symbol"):
                    symbol = data.symbol
                else:
                    symbol = source  # 使用数据源标识作为标的代码
            
            # 获取时间戳
            timestamp = None
            if isinstance(data, dict) and "timestamp" in data:
                timestamp = data["timestamp"]
            elif hasattr(data, "timestamp"):
                timestamp = data.timestamp
            elif isinstance(data, dict) and "time" in data:
                timestamp = data["time"]
            elif hasattr(data, "time"):
                timestamp = data.time
            elif isinstance(data, dict) and "date" in data:
                timestamp = data["date"]
            elif hasattr(data, "date"):
                timestamp = data.date
            
            if timestamp is None:
                timestamp = datetime.now()  # 使用当前时间作为默认值
            
            # 应用数据转换器
            if source in self._data_converters:
                # 如果有数据转换器，使用它来创建事件
                event = self._data_converters[source](data, timestamp, symbol)
                if event:
                    self.send_event(event)
            else:
                # 默认创建市场数据事件
                event = MarketDataEvent(timestamp, symbol, data if isinstance(data, dict) else {"data": data})
                event.source = source
                self.send_event(event)
        
        except Exception as e:
            logger.error(f"处理重放数据异常: {str(e)}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        stats = super().get_performance_stats()
        
        # 添加重放控制器的状态
        replay_stats = {}
        with self._lock:
            for name, controller in self._replay_controllers.items():
                replay_stats[name] = {
                    "status": controller.get_status().name
                }
        
        stats["replay_controllers"] = replay_stats
        return stats