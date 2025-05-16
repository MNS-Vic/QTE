#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎管理器 - 修复版本
解决了数据重放控制器与引擎管理器集成的线程阻塞问题
"""
import os
import time
import datetime
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Any, Tuple, Callable, Type
import abc
import logging
import threading
import traceback
from enum import Enum

# 导入原始模块
from qte.core.vector_engine import VectorEngine
from qte.core.event_engine import EventDrivenBacktester
from qte.data.data_replay import ReplayMode, ReplayStatus, DataReplayInterface

# 设置日志
logger = logging.getLogger("EngineManager")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 从原始引擎管理器复制枚举和事件类
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
            处理器ID，可用于注销处理器
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
    
    实现了基本功能，可作为其他引擎管理器的基类
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
        self._handlers = {}  # 类型 -> {ID -> 处理函数}
        self._handler_id_counter = 0
        self._event_queue = []
        self._lock = threading.Lock()
        self._process_thread = None
        self._process_event = threading.Event()
        self._start_time = None
        self._end_time = None
        
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
            self._status = EngineStatus.INITIALIZED
            self._event_queue = []
            self._start_time = None
            self._end_time = None
            
            logger.info("引擎管理器已初始化")
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
            if self._status != EngineStatus.INITIALIZED and self._status != EngineStatus.STOPPED:
                logger.warning(f"引擎当前状态为 {self._status.name}，无法启动")
                return False
            
            # 启动处理线程
            self._process_event.set()
            self._process_thread = threading.Thread(target=self._process_events)
            self._process_thread.daemon = True
            self._process_thread.start()
            
            self._status = EngineStatus.RUNNING
            self._start_time = time.time()
            
            logger.info("引擎已启动")
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
                logger.warning(f"引擎当前状态为 {self._status.name}，无法暂停")
                return False
            
            self._status = EngineStatus.PAUSED
            self._process_event.clear()
            
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
                logger.warning(f"引擎当前状态为 {self._status.name}，无法恢复")
                return False
            
            self._status = EngineStatus.RUNNING
            self._process_event.set()
            
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
            if self._status == EngineStatus.STOPPED:
                logger.warning("引擎已经停止")
                return True
            
            prev_status = self._status
            self._status = EngineStatus.STOPPED
            self._process_event.set()  # 确保线程不会卡在等待
            
            if self._process_thread and self._process_thread.is_alive():
                try:
                    self._process_thread.join(timeout=2.0)
                    if self._process_thread.is_alive():
                        logger.warning("处理线程未能在2秒内结束")
                except Exception as e:
                    logger.error(f"停止处理线程时发生错误: {str(e)}")
            
            self._end_time = time.time()
            self._process_thread = None
            
            logger.info(f"引擎已从 {prev_status.name} 状态停止")
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
        try:
            with self._lock:
                if self._status not in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
                    logger.warning(f"引擎当前状态为 {self._status.name}，无法发送事件")
                    return False
                
                self._event_queue.append(event)
                
                # 如果队列中积累了太多事件，可能是处理线程卡住了
                if len(self._event_queue) > 10000:
                    logger.warning(f"事件队列过长: {len(self._event_queue)} 个事件")
                
                return True
        except Exception as e:
            logger.error(f"发送事件时发生错误: {str(e)}")
            return False
    
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
            处理器ID，可用于注销处理器
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = {}
            
            handler_id = self._handler_id_counter
            self._handler_id_counter += 1
            
            self._handlers[event_type][handler_id] = handler
            
            logger.debug(f"已注册事件处理器: 类型={event_type}, ID={handler_id}")
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
            for event_type, handlers in self._handlers.items():
                if handler_id in handlers:
                    del handlers[handler_id]
                    logger.debug(f"已注销事件处理器: 类型={event_type}, ID={handler_id}")
                    return True
            
            logger.warning(f"未找到ID为 {handler_id} 的事件处理器")
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
                "status": self._status.name,
                "event_queue_length": len(self._event_queue),
                "handler_count": sum(len(handlers) for handlers in self._handlers.values())
            }
            
            if self._start_time:
                stats["running_time"] = time.time() - self._start_time if not self._end_time else self._end_time - self._start_time
                
            return stats
    
    def _process_events(self):
        """事件处理线程的主函数"""
        logger.debug("事件处理线程已启动")
        try:
            while self._status != EngineStatus.STOPPED:
                # 等待事件，支持暂停/恢复
                # 修复：添加超时参数，防止无限等待
                event_set = self._process_event.wait(timeout=0.5)
                
                # 如果是因为超时而返回，并且引擎仍在运行，则继续等待
                if not event_set and self._status == EngineStatus.RUNNING:
                    continue
                
                # 如果引擎已停止，则退出循环
                if self._status == EngineStatus.STOPPED:
                    break
                
                # 如果引擎已暂停，则继续等待
                if self._status == EngineStatus.PAUSED:
                    continue
                
                # 从队列中取出事件并处理
                events = []
                with self._lock:
                    if self._event_queue:
                        # 一次最多处理100个事件，避免锁持有时间过长
                        events = self._event_queue[:100]
                        self._event_queue = self._event_queue[100:]
                
                for event in events:
                    self._dispatch_event(event)
                
                # 如果队列为空，稍微休息一下再检查
                if not events:
                    time.sleep(0.001)
        
        except Exception as e:
            logger.error(f"事件处理线程异常: {str(e)}")
            # 添加详细的堆栈跟踪
            logger.error(traceback.format_exc())
            with self._lock:
                self._status = EngineStatus.ERROR
        
        logger.debug("事件处理线程已退出")
    
    def _dispatch_event(self, event: EngineEvent):
        """
        分发事件到对应的处理器
        
        Parameters
        ----------
        event : EngineEvent
            要分发的事件
        """
        try:
            # 获取事件类型对应的所有处理器
            handlers = []
            with self._lock:
                if event.event_type in self._handlers:
                    handlers = list(self._handlers[event.event_type].values())
            
            # 调用所有处理器
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"事件处理器异常: {str(e)}")
                    # 添加详细的堆栈跟踪
                    logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"事件分发异常: {str(e)}")
            # 添加详细的堆栈跟踪
            logger.error(traceback.format_exc())

class ReplayEngineManager(BaseEngineManager):
    """
    数据重放引擎管理器
    
    集成了数据重放控制器，支持回测和模拟交易
    修复了以下问题：
    1. Lambda表达式捕获变量问题
    2. 线程等待无超时问题
    3. 异常处理不完善
    4. 日志记录不充分
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
                # 修复：使用嵌套函数正确捕获循环变量
                def create_callback(source_name):
                    return lambda data: self._on_replay_data(source_name, data)
                
                callback = create_callback(name)
                callback_id = controller.register_callback(callback)
                self._replay_callbacks[controller] = callback_id
                logger.debug(f"为控制器 '{name}' 注册回调，ID: {callback_id}")
            
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
            logger.debug(f"接收到来自 '{source}' 的重放数据")
            
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
                timestamp = datetime.datetime.now()  # 使用当前时间作为默认值
            
            # 应用数据转换器
            if source in self._data_converters:
                # 如果有数据转换器，使用它来创建事件
                event = self._data_converters[source](data, timestamp, symbol)
                if event:
                    logger.debug(f"使用自定义转换器创建事件: {event}")
                    self.send_event(event)
            else:
                # 默认创建市场数据事件
                event = MarketDataEvent(timestamp, symbol, data if isinstance(data, dict) else {"data": data})
                event.source = source
                logger.debug(f"创建市场数据事件: {event}")
                self.send_event(event)
        
        except Exception as e:
            logger.error(f"处理重放数据异常: {str(e)}")
            # 添加详细的堆栈跟踪
            logger.error(traceback.format_exc())
    
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