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
from datetime import datetime
from qte.core.vector_engine import VectorEngine
from qte.core.event_engine import EventDrivenBacktester
from enum import Enum
import abc
import logging
import threading
import queue

# 导入数据重放相关类
from qte.data.data_replay import ReplayMode, ReplayStatus, DataReplayInterface
# 导入核心事件定义
from qte.core.events import Event as CoreEvent, EventType, MarketEvent as CoreMarketEvent, SignalEvent as CoreSignalEvent, OrderEvent as CoreOrderEvent, FillEvent as CoreFillEvent, OrderDirection, OrderType
from datetime import datetime

# 设置日志
logger = logging.getLogger("EngineManager")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

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

class BaseEngineManager(EngineManagerInterface):
    """
    引擎管理器基类
    
    实现了基本的引擎控制、事件处理和监控功能
    """
    
    def __init__(self, engine_type: EngineType = EngineType.EVENT_DRIVEN):
        """
        初始化引擎管理器基类
        
        Parameters
        ----------
        engine_type : EngineType, optional
            引擎类型, by default EngineType.EVENT_DRIVEN
        """
        self._engine_type = engine_type
        self._status = EngineStatus.INITIALIZED
        self._config = {}
        self._event_queue = queue.Queue()
        self._event_handlers: Dict[str, List[Callable[[CoreEvent], None]]] = {} # Store list of handlers directly
        self._handler_id_counter = 0 # Used to generate unique IDs if needed, but not for direct unsubscription by ID here
        self._event_processing_thread = None
        self._stop_event_processing = threading.Event()
        self._pause_event = threading.Event() 
        self._pause_event.set() # Start in non-paused state (wait() will not block)
        self._performance_stats = {"processed_events": 0, "start_time": None, "end_time": None}
        self._lock = threading.Lock()
    
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
            if self._status in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
                logger.warning(f"引擎 ({self.__class__.__name__}) 正在运行或暂停，无法在当前状态 {self._status.name} 下初始化。请先停止引擎。")
                return False
            
            self._config = config if config is not None else {}
            self._status = EngineStatus.INITIALIZED
            self._event_queue = queue.Queue()
            self._event_handlers = {}
            self._handler_id_counter = 0
            self._stop_event_processing.clear()
            self._pause_event.set()
            self._performance_stats = {"processed_events": 0, "start_time": None, "end_time": None}
            self._event_processing_thread = None 
            logger.info(f"引擎 ({self.__class__.__name__}) 已初始化。配置: {self._config}")
            return True
    
    def start(self) -> bool:
        logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): Entered start() method.")
        with self._lock:
            if self._status == EngineStatus.RUNNING:
                logger.warning(f"引擎 ({self.__class__.__name__}) 已经在运行")
                return False
            
            if self._status not in [EngineStatus.INITIALIZED, EngineStatus.STOPPED, EngineStatus.PAUSED]:
                 logger.warning(f"引擎 ({self.__class__.__name__}) 无法从当前状态 {self._status.name} 启动。请先初始化或重置。")
                 return False 

            self._status = EngineStatus.RUNNING # Set status to RUNNING
            self._stop_event_processing.clear() 
            self._pause_event.set() 
            
            logger.info(f"引擎 ({self.__class__.__name__}) 已设置为RUNNING。类型: {self._engine_type.name}")
            
            # 确保事件处理线程启动 - 删除之前可能的注释标记，确保此代码始终执行
            print(f"【启动事件处理线程】正在为 {self.__class__.__name__} 启动事件处理线程...")
            logger.info(f"【启动事件处理线程】正在为 {self.__class__.__name__} 启动事件处理线程...")
            
            if self._event_processing_thread is None or not self._event_processing_thread.is_alive():
                logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): Starting _event_processing_thread.")
                self._event_processing_thread = threading.Thread(target=self._process_events, name=f"{self.__class__.__name__}_EventProcessor")
                self._event_processing_thread.daemon = True
                self._event_processing_thread.start()
                thread_id = self._event_processing_thread.ident if self._event_processing_thread else 'N/A'
                print(f"【事件处理线程已启动】线程ID: {thread_id}")
                logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): _event_processing_thread started (Thread ID: {thread_id}).")
            else:
                thread_id = self._event_processing_thread.ident if self._event_processing_thread else 'N/A'
                print(f"【事件处理线程已运行】线程ID: {thread_id}")
                logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): _event_processing_thread already running (Thread ID: {thread_id}).")
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
                logger.warning(f"引擎 ({self.__class__.__name__}) 未在运行，无法暂停。当前状态: {self._status.name}")
                return False
            
            self._status = EngineStatus.PAUSED
            self._pause_event.clear() 
            logger.info(f"引擎 ({self.__class__.__name__}) 已暂停。")
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
                logger.warning(f"引擎 ({self.__class__.__name__}) 未暂停，无法恢复。当前状态: {self._status.name}")
                return False
        logger.info(f"引擎 ({self.__class__.__name__}) 正在从暂停状态恢复...")
        return self.start()
    
    def stop(self) -> bool:
        """
        停止引擎管理器
        
        Returns
        -------
        bool
            停止是否成功
        """
        with self._lock:
            if self._status not in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
                logger.info(f"引擎 ({self.__class__.__name__}) 未在运行或暂停，无需停止。当前状态: {self._status.name}")
                return False

            logger.info(f"开始停止引擎 ({self.__class__.__name__})...")
            original_status = self._status
            self._status = EngineStatus.STOPPED
            self._stop_event_processing.set() 
            self._pause_event.set() 

            try:
                self._event_queue.put(None, block=True, timeout=0.5) 
                logger.debug(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 已向事件队列发送None以唤醒处理线程。")
            except queue.Full:
                logger.warning(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 尝试向事件队列发送None失败，队列已满。")
            except Exception as e: 
                logger.error(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 向事件队列发送None时发生错误: {e}")

            if self._event_processing_thread and self._event_processing_thread.is_alive():
                logger.debug(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 等待事件处理线程 (ID: {self._event_processing_thread.ident}) 结束...")
                self._event_processing_thread.join(timeout=3.0) 
                if self._event_processing_thread.is_alive():
                    logger.warning(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 事件处理线程 (ID: {self._event_processing_thread.ident}) 在超时后仍未结束。")
                else:
                    logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 事件处理线程 (ID: {self._event_processing_thread.ident}) 已成功停止。")
            else:
                logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): 事件处理线程不存在或已停止。")
            
            self._event_processing_thread = None 

            if self._performance_stats.get("start_time") is not None and self._performance_stats.get("end_time") is None:
                 self._performance_stats["end_time"] = time.time()
            logger.info(f"引擎 ({self.__class__.__name__}) 已停止。原状态: {original_status.name}")
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
        if self._status not in [EngineStatus.RUNNING, EngineStatus.PAUSED] and not (self._status == EngineStatus.INITIALIZED and event.event_type == EventType.MARKET.value): 
            logger.warning(f"引擎 ({self.__class__.__name__}) 未运行/暂停 (状态: {self._status.name})，无法发送事件类型 '{event.event_type}'。")
            return False
        try:
            self._event_queue.put(event)
            return True
        except Exception as e:
            logger.error(f"发送事件到队列时出错 ({self.__class__.__name__}): {e}", exc_info=True)
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
            处理器ID，用于注销
        """
        with self._lock:
            handler_id = self._handler_id_counter
            key_to_register = event_type 
            
            if not isinstance(key_to_register, str): 
                 logger.error(f"注册处理器时event_type必须是字符串，得到: {type(key_to_register)}")
                 return -1 

            if key_to_register not in self._event_handlers:
                self._event_handlers[key_to_register] = []
            
            if handler not in self._event_handlers[key_to_register]: 
                self._event_handlers[key_to_register].append(handler) 
                self._handler_id_counter += 1 
                logger.debug(f"已注册事件处理器: {key_to_register} -> {handler.__name__}")
            else:
                logger.debug(f"事件处理器 {handler.__name__} 已为事件类型 {key_to_register} 注册。")
            return handler_id 
    
    def unregister_event_handler(self, handler_id: int) -> bool: 
        logger.warning(f"Unregistering by handler_id ({handler_id}) is not robustly supported. Please unregister by (event_type, handler_func)." )
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
            processing_time = 0
            start_time = self._performance_stats.get("start_time")
            end_time = self._performance_stats.get("end_time")

            if end_time and start_time:
                processing_time = end_time - start_time
            elif start_time and self._status == EngineStatus.RUNNING: 
                processing_time = time.time() - start_time
                
            stats = {
                "processed_events": self._performance_stats.get("processed_events", 0),
                "start_time": start_time,
                "end_time": end_time,
                "current_status": self._status.name,
                "processing_time": processing_time,
                "events_per_second": self._performance_stats.get("processed_events", 0) / max(processing_time, 0.000001)
            }
            return stats
    
    def _process_events(self):
        """
        事件处理循环，在单独线程中运行
        """
        thread_name = threading.current_thread().name
        thread_id = threading.get_ident()
        print(f"【事件处理启动】引擎名称={self.__class__.__name__}, 线程名称={thread_name}, 线程ID={thread_id}")
        logger.debug(f"【事件处理启动】引擎名称={self.__class__.__name__}, 线程名称={thread_name}, 线程ID={thread_id}")
        
        processed_in_session = 0
        last_progress_time = time.time()
        progress_interval = 0.5  # 每0.5秒输出一次进度
        
        with self._lock: 
            if self._performance_stats.get("start_time") is None and self._status == EngineStatus.RUNNING:
                 self._performance_stats["start_time"] = time.time()
                 logger.debug(f"【事件处理】记录启动时间: {self._performance_stats['start_time']}")

        while not self._stop_event_processing.is_set():
            try:
                # 周期性输出进度状态，而不是按处理次数
                current_time = time.time()
                if (current_time - last_progress_time) >= progress_interval:
                    queue_size = self._event_queue.qsize() if hasattr(self._event_queue, 'qsize') else "未知"
                    runtime = current_time - self._performance_stats.get('start_time', current_time)
                    print(f"【事件处理进度】已处理={processed_in_session}, 队列大小={queue_size}, 状态={self._status.name}, 运行时间={runtime:.1f}秒")
                    logger.debug(f"【事件处理进度】已处理={processed_in_session}, 队列大小={queue_size}, 状态={self._status.name}")
                    last_progress_time = current_time
                
                # 等待恢复，如果处于暂停状态
                resumed_from_pause = self._pause_event.wait(timeout=0.1) 
                
                if self._stop_event_processing.is_set(): 
                    print(f"【事件处理终止】检测到停止信号，退出循环")
                    logger.debug(f"【事件处理终止】检测到停止信号，退出循环")
                    break
                
                if not resumed_from_pause: 
                    if self._status == EngineStatus.PAUSED:
                        print(f"【事件处理暂停】引擎已暂停，等待恢复...")
                        logger.debug(f"【事件处理暂停】引擎已暂停，等待恢复...")
                        continue 
                
                # 尝试从队列获取事件
                try:
                    event = self._event_queue.get(block=True, timeout=0.1)
                    if event:
                        event_type = getattr(event, 'event_type', 'Unknown')
                        event_symbol = getattr(event, 'symbol', 'N/A')
                        print(f"【获取事件】类型={event_type}, 标的={event_symbol}")
                        logger.debug(f"【获取事件】类型={event_type}, 标的={event_symbol}")
                except queue.Empty:
                    # 不再每次都打印队列为空的信息，减少噪音
                    continue
                except Exception as e:
                    print(f"【事件处理错误】从队列获取事件时出错: {str(e)}")
                    logger.error(f"【事件处理错误】从队列获取事件时出错: {str(e)}", exc_info=True)
                    continue
                
                # 检查是否收到None结束信号
                if event is None: 
                    print(f"【事件处理终止】收到None结束信号，退出循环")
                    logger.debug(f"【事件处理终止】收到None结束信号，退出循环")
                    break 
                
                # 再次检查是否应该停止处理
                if self._stop_event_processing.is_set(): 
                    print(f"【事件处理终止】在获取事件'{type(event).__name__}'后检测到停止信号，退出循环")
                    logger.debug(f"【事件处理终止】在获取事件'{type(event).__name__}'后检测到停止信号，退出循环")
                    break

                # 分发事件到处理器
                event_type = getattr(event, 'event_type', 'Unknown')
                event_symbol = getattr(event, 'symbol', 'N/A')
                print(f"【分发事件】类型={event_type}, 标的={event_symbol}")
                logger.debug(f"【分发事件】类型={event_type}, 标的={event_symbol}")
                
                # 记录处理时间
                dispatch_start = time.time()
                dispatch_result = self._dispatch_event(event)
                dispatch_time = time.time() - dispatch_start
                
                print(f"【分发完成】类型={event_type}, 结果={dispatch_result}, 耗时={dispatch_time:.4f}秒")
                logger.debug(f"【分发完成】类型={event_type}, 结果={dispatch_result}, 耗时={dispatch_time:.4f}秒")
                
                # 更新性能统计和计数器
                with self._lock: 
                    self._performance_stats["processed_events"] = self._performance_stats.get("processed_events", 0) + 1
                processed_in_session += 1
                
                # 标记任务完成
                self._event_queue.task_done() 

            except queue.Empty: 
                if self._stop_event_processing.is_set(): 
                    print(f"DEBUG ENGINE_MGR ({thread_name}): Queue empty and stop event set, breaking loop.")
                    logger.debug(f"DEBUG ENGINE_MGR ({thread_name}): Queue empty and stop event set, breaking loop.")
                    break
                continue 
            except Exception as e:
                print(f"事件处理循环 ({thread_name}) 中发生错误: {e}")
                logger.error(f"事件处理循环 ({thread_name}) 中发生错误: {e}", exc_info=True)
                with self._lock: 
                    self._status = EngineStatus.ERROR 
                self._stop_event_processing.set() 
                break 
        
        print(f"DEBUG ENGINE_MGR ({thread_name}): _process_events thread loop finished. Processed in this session: {processed_in_session}, Total processed overall: {self._performance_stats.get('processed_events', 0)}")
        logger.info(f"DEBUG ENGINE_MGR ({thread_name}): _process_events thread loop finished. Processed in this session: {processed_in_session}, Total processed overall: {self._performance_stats.get('processed_events', 0)}")
    
    def _dispatch_event(self, event: CoreEvent):
        """
        分发事件到对应的处理器
        
        Parameters
        ----------
        event : CoreEvent
            要分发的事件
        """
        try:
            event_type = getattr(event, 'event_type', 'Unknown')
            event_symbol = getattr(event, 'symbol', 'N/A')
            logger.debug(f"【事件分发开始】类型={event_type}, 标的={event_symbol}")
            
            handlers_to_call = []
            with self._lock:
                registered_types = list(self._event_handlers.keys())
                logger.debug(f"【事件分发】已注册的处理器类型: {registered_types}")
                
                if event_type in self._event_handlers:
                    handlers = self._event_handlers[event_type]
                    handlers_to_call.extend(handlers)
                    logger.debug(f"【事件分发】找到 {len(handlers)} 个匹配事件类型 {event_type} 的处理器")
                else:
                    logger.debug(f"【事件分发】未找到事件类型 {event_type} 的处理器")
                
                if "*" in self._event_handlers:
                    handlers = self._event_handlers["*"]
                    handlers_to_call.extend(handlers)
                    logger.debug(f"【事件分发】找到 {len(handlers)} 个通配符处理器")
            
            if not handlers_to_call:
                logger.debug(f"【事件分发】未找到任何处理器来处理事件类型 {event_type}")
                return False 

            logger.debug(f"【事件分发】准备调用 {len(handlers_to_call)} 个处理器")
            
            handler_results = []
            for i, handler_func in enumerate(handlers_to_call):
                handler_name = getattr(handler_func, '__name__', str(handler_func))
                handler_start = time.time()
                try:
                    logger.debug(f"【处理器调用】开始处理器 #{i+1}: {handler_name}")
                    handler_func(event)
                    handler_time = time.time() - handler_start
                    logger.debug(f"【处理器完成】处理器 {handler_name} 成功处理事件，耗时: {handler_time:.4f}秒")
                    handler_results.append(True)
                except Exception as e:
                    handler_time = time.time() - handler_start
                    print(f"【处理器错误】处理器 {handler_name} 处理事件时出错: {str(e)}")
                    logger.error(f"【处理器错误】处理器 {handler_name} 处理事件 {event_type} 时出错: {str(e)}, 耗时: {handler_time:.4f}秒", exc_info=True)
                    handler_results.append(False)
            
            success_count = sum(1 for result in handler_results if result)
            logger.debug(f"【事件分发完成】事件类型: {event_type}, 成功处理: {success_count}/{len(handlers_to_call)}")
            return success_count > 0  # 至少有一个处理器成功则返回True
        
        except Exception as e:
            print(f"【事件分发错误】事件分发过程中出错: {str(e)}")
            logger.error(f"【事件分发错误】事件分发过程中出错: {str(e)}", exc_info=True)
            return False

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
        self._replay_controllers: Dict[str, Dict[str, Any]] = {}  # name -> {'controller': DataReplayInterface, 'symbol': Optional[str], 'converter': Optional[Callable]}
        self._replay_callbacks: Dict[DataReplayInterface, int] = {} # controller_instance -> callback_id
        self._symbol_mapping: Dict[str, Optional[str]] = {}      # source_name -> symbol (largely redundant with _replay_controllers storage)
        self._data_converters: Dict[str, Optional[Callable]] = {} # source_name -> converter (largely redundant)
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化引擎管理器，并重置ReplayEngineManager的特定状态。
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数, by default None
            
        Returns
        -------
        bool
            初始化是否成功
        """
        with self._lock: # Ensure thread safety for initialization
            if not super().initialize(config):
                logger.error(f"DEBUG REPLAY_EM ({self.__class__.__name__}): BaseEngineManager initialization failed.")
                return False 
            
            # Reset ReplayEngineManager specific state
            self._replay_controllers = {} 
            self._replay_callbacks = {}   
            self._symbol_mapping = {} # Kept for compatibility if _on_replay_data uses it, but primarily info is in _replay_controllers
            self._data_converters = {} # Kept for compatibility 
            
            logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): ReplayEngineManager specific state reset during initialize.")

            # Original logic for loading controllers from config
            if config and "replay_controllers" in config:
                logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Loading replay controllers from config...")
                for name, controller_config in config["replay_controllers"].items():
                    controller = controller_config.get("controller")
                    if controller and isinstance(controller, DataReplayInterface):
                        logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Adding controller '{name}' from config.")
                        # Call the public add_replay_controller method to ensure all logic (like logging) is applied
                        self.add_replay_controller(
                            name, 
                            controller, 
                            controller_config.get("symbol"),
                            controller_config.get("converter")
                        )
                    else:
                        logger.warning(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Controller '{name}' in config is invalid or missing.")
            
            # BaseEngineManager.initialize should set status to INITIALIZED.
            # If we need to re-affirm, self._status = EngineStatus.INITIALIZED
            logger.info(f"ReplayEngineManager ({self.__class__.__name__}) 已初始化。")
        return True
    
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
            
            self._replay_controllers[name] = {"controller": controller, "symbol": symbol, "converter": data_converter}
            
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
            
            controller = self._replay_controllers[name]["controller"]
            
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
            print(f"DEBUG REPLAY_EM: 启动引擎，当前状态: {self._status.name}")
            logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Entering start() method. Current status: {self._status.name}")
            
            if not super().start(): 
                print(f"DEBUG REPLAY_EM: 基础引擎管理器启动失败")
                logger.error(f"DEBUG REPLAY_EM ({self.__class__.__name__}): BaseEngineManager (super) start() failed.")
                return False
            
            print(f"DEBUG REPLAY_EM: 基础引擎管理器启动成功，准备注册控制器回调")
            logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): BaseEngineManager started successfully. Registering controller callbacks...")

            # 清理之前的回调（避免重复）
            for ctrl in list(self._replay_callbacks.keys()):
                try:
                    callback_id = self._replay_callbacks[ctrl]
                    print(f"DEBUG REPLAY_EM: 注销控制器的旧回调 ID: {callback_id}")
                    ctrl.unregister_callback(callback_id)
                except Exception as e:
                    print(f"DEBUG REPLAY_EM: 注销旧回调时出错: {e}")
            self._replay_callbacks = {}

            # 为所有控制器注册回调
            if not self._replay_controllers:
                print(f"DEBUG REPLAY_EM: 没有重放控制器可以启动")
                logger.warning(f"DEBUG REPLAY_EM ({self.__class__.__name__}): No replay controllers added to start.")
            else:
                print(f"DEBUG REPLAY_EM: 发现 {len(self._replay_controllers)} 个重放控制器")
                for name, controller_info in self._replay_controllers.items():
                    rc = controller_info['controller']
                    print(f"DEBUG REPLAY_EM: 为控制器 '{name}' 注册回调")
                    logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Registering callback for controller '{name}' (Instance: {rc})")
                    try:
                        # 创建并测试回调函数
                        def make_callback(src_name):
                            def callback_func(data):
                                print(f"DEBUG REPLAY_EM: 控制器 '{src_name}' 回调被触发，数据: {str(data)[:100]}...")
                                return self._on_replay_data(src_name, data)
                            return callback_func
                        
                        callback_func = make_callback(name)
                        callback_id = rc.register_callback(callback_func)
                        self._replay_callbacks[rc] = callback_id 
                        print(f"DEBUG REPLAY_EM: 成功为控制器 '{name}' 注册回调，ID: {callback_id}")
                        logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Callback registered for '{name}' with ID {callback_id}.")
                    except Exception as e:
                        print(f"DEBUG REPLAY_EM: 为控制器 '{name}' 注册回调时出错: {e}")
                        logger.error(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Error registering callback for '{name}': {e}", exc_info=True)
                        return False
            
            print(f"DEBUG REPLAY_EM: 已注册完所有控制器回调，现在启动控制器")
            logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Controller callbacks registered. Starting controllers...")

            # 启动所有控制器
            if not self._replay_controllers:
                print(f"DEBUG REPLAY_EM: 没有控制器需要启动")
                logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): No controllers to start explicitly in ReplayEngineManager.start().")
            else:
                print(f"DEBUG REPLAY_EM: 开始启动 {len(self._replay_controllers)} 个控制器")
                for name, controller_info in self._replay_controllers.items():
                    rc = controller_info['controller']
                    
                    # 重置控制器，确保从头开始
                    try:
                        if hasattr(rc, 'reset') and callable(rc.reset):
                            print(f"DEBUG REPLAY_EM: 重置控制器 '{name}'")
                            rc.reset()
                    except Exception as e:
                        print(f"DEBUG REPLAY_EM: 重置控制器 '{name}' 时出错: {e}")
                    
                    if rc.get_status() != ReplayStatus.RUNNING:
                        print(f"DEBUG REPLAY_EM: 启动控制器 '{name}'，当前状态: {rc.get_status().name}")
                        logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Attempting to start controller '{name}'. Current status: {rc.get_status().name}")
                        result = rc.start()
                        if not result: 
                            print(f"DEBUG REPLAY_EM: 启动控制器 '{name}' 失败")
                            logger.error(f"启动数据重放控制器 '{name}' 失败")
                        else:
                            print(f"DEBUG REPLAY_EM: 成功启动控制器 '{name}'，新状态: {rc.get_status().name}")
                            logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Successfully started controller '{name}'. New status: {rc.get_status().name}")
                    else:
                        print(f"DEBUG REPLAY_EM: 控制器 '{name}' 已经在运行中")
                        logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): Controller '{name}' already running.")
            
            # 查看是否有成功启动的控制器
            running_controllers = [
                name for name, info in self._replay_controllers.items() 
                if info['controller'].get_status() == ReplayStatus.RUNNING
            ]
            print(f"DEBUG REPLAY_EM: 成功启动的控制器: {running_controllers}")
            
            if not running_controllers and self._replay_controllers:
                print(f"DEBUG REPLAY_EM: 警告 - 没有控制器处于运行状态")
                logger.warning(f"DEBUG REPLAY_EM ({self.__class__.__name__}): No replay controllers are in RUNNING state after start attempts. Engine might complete prematurely if no data is pushed.")
            
            print(f"DEBUG REPLAY_EM: 引擎启动完成，状态: {self._status.name}，控制器数量: {len(self._replay_controllers)}")
            logger.info(f"DEBUG REPLAY_EM ({self.__class__.__name__}): ReplayEngineManager start() method finished successfully.")
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
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
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
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
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
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
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
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
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
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
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
            重放数据 (通常是一个包含OHLCV等数据的字典)
        """
        print(f"DEBUG REPLAY_DATA: 收到来自源 '{source}' 的数据回调。数据: {str(data)[:100]}...")
        logger.info(f"DEBUG ENGINE_MGR ({self.__class__.__name__}): _on_replay_data called by source '{source}'. Data: {str(data)[:100]}...") 
        try:
            # 获取标的代码
            symbol_from_data = data.get('symbol', self._symbol_mapping.get(source, source))
            print(f"DEBUG REPLAY_DATA: 使用标的代码: {symbol_from_data}")
            
            # 处理时间戳
            ts_data = data.get('timestamp')
            print(f"DEBUG REPLAY_DATA: 原始时间戳: {ts_data}, 类型: {type(ts_data)}")
            
            if isinstance(ts_data, str):
                timestamp_from_data = pd.to_datetime(ts_data)
                print(f"DEBUG REPLAY_DATA: 字符串时间戳转换为: {timestamp_from_data}")
            elif isinstance(ts_data, datetime):
                timestamp_from_data = ts_data
                print(f"DEBUG REPLAY_DATA: 使用原始datetime时间戳: {timestamp_from_data}")
            else: # Fallback or raise error
                print(f"DEBUG REPLAY_DATA: 时间戳类型无法识别，使用当前时间")
                logger.warning(f"Timestamp from replay source '{source}' is not a recognized type (str/datetime): {ts_data}. Using current time.")
                timestamp_from_data = datetime.now()
                print(f"DEBUG REPLAY_DATA: 使用当前时间: {timestamp_from_data}")

            # 创建事件
            engine_event = None
            print(f"DEBUG REPLAY_DATA: 准备创建事件") 
            
            # 检查是否有数据转换器
            if source in self._data_converters and callable(self._data_converters[source]):
                print(f"DEBUG REPLAY_DATA: 使用数据转换器处理源 '{source}' 的数据")
                logger.debug(f"DEBUG ENGINE_MGR: Using data_converter for source '{source}'.")
                try:
                    engine_event = self._data_converters[source](data, timestamp_from_data, symbol_from_data)
                    print(f"DEBUG REPLAY_DATA: 数据转换器返回事件类型: {type(engine_event)}")
                    if not isinstance(engine_event, CoreEvent):
                        print(f"DEBUG REPLAY_DATA: 错误 - 数据转换器未返回有效事件对象，而是 {type(engine_event)}")
                        logger.error(f"Data converter for source '{source}' did not return a CoreEvent instance. Got: {type(engine_event)}")
                        return
                except Exception as e:
                    print(f"DEBUG REPLAY_DATA: 调用数据转换器时出错: {e}")
                    return
            else:
                # 创建标准市场事件
                print(f"DEBUG REPLAY_DATA: 无数据转换器，创建标准市场事件")
                logger.debug(f"DEBUG ENGINE_MGR: No data_converter for source '{source}', creating CoreMarketEvent.")
                try:
                    # 检查数据完整性
                    required_fields = ['open', 'high', 'low', 'close', 'volume']
                    for field in required_fields:
                        if field not in data:
                            print(f"DEBUG REPLAY_DATA: 错误 - 数据缺少必需字段 '{field}'")
                            return
                    
                    # 创建事件对象
                    print(f"DEBUG REPLAY_DATA: 创建市场事件对象，字段: {required_fields}")
                    engine_event = CoreMarketEvent(
                        symbol=symbol_from_data,
                        timestamp=timestamp_from_data,
                        open_price=float(data['open']),
                        high_price=float(data['high']),
                        low_price=float(data['low']),
                        close_price=float(data['close']),
                        volume=int(data['volume'])
                    )
                    print(f"DEBUG REPLAY_DATA: 成功创建市场事件: {engine_event.event_type} 标的={symbol_from_data} 时间={timestamp_from_data}")
                    logger.debug(f"DEBUG ENGINE_MGR: Successfully created CoreMarketEvent for '{symbol_from_data}' at {timestamp_from_data}.")
                except KeyError as e:
                    print(f"DEBUG REPLAY_DATA: 数据源 '{source}' 缺少字段 '{e}'")
                    logger.error(f"Data from replay source '{source}' is missing key '{e}' for MarketEvent creation. Data: {data}")
                    return
                except ValueError as e:
                    print(f"DEBUG REPLAY_DATA: 转换数据源 '{source}' 的值时出错: {e}")
                    logger.error(f"ValueError during MarketEvent creation for source '{source}': {e}. Data: {data}")
                    return
                except Exception as e:
                    print(f"DEBUG REPLAY_DATA: 创建市场事件时发生意外错误: {e}")
                    return
            
            # 检查事件创建结果
            if engine_event is None: 
                print(f"DEBUG REPLAY_DATA: 错误 - 创建事件失败")
                logger.error(f"DEBUG ENGINE_MGR: engine_event is None after creation attempt for source '{source}'. This should not happen.")
                return

            # 添加来源信息到事件
            print(f"DEBUG REPLAY_DATA: 为事件添加来源信息: {source}")
            if not hasattr(engine_event, 'additional_data') or engine_event.additional_data is None:
                engine_event.additional_data = {}
            engine_event.additional_data['_source_replay_controller'] = source
            
            # 发送事件到队列
            print(f"DEBUG REPLAY_DATA: 发送事件 {engine_event.event_type} 标的={getattr(engine_event, 'symbol', 'N/A')} 到事件队列")
            logger.debug(f"DEBUG ENGINE_MGR: Sending event to event_queue: {engine_event.event_type} for {getattr(engine_event, 'symbol', 'N/A')}")
            result = self.send_event(engine_event)
            print(f"DEBUG REPLAY_DATA: 事件发送结果: {result}")
            
            return result
        except Exception as e:
            print(f"DEBUG REPLAY_DATA: 处理重放数据时发生异常: {e}")
            logger.error(f"处理来自数据源 '{source}' 的重放数据时发生异常: {e}", exc_info=True)
            return False
    
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
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
                replay_stats[name] = {
                    "status": controller.get_status().name
                }
        
        stats["replay_controllers"] = replay_stats
        return stats