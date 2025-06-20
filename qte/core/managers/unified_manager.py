#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一管理器

提供向后兼容的统一管理器接口，内部使用重构后的专门管理器
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable
from qte.core.events import Event as CoreEvent
from qte.data.data_replay import DataReplayInterface, ReplayMode, ReplayStatus

from .base_manager import EngineManagerInterface, EngineType, EngineStatus
from .event_manager import EventManager
from .engine_manager import EngineManager
from .replay_manager import ReplayManager
from .lifecycle_manager import LifecycleManager


class BaseEngineManager(EngineManagerInterface):
    """
    基础引擎管理器（向后兼容）
    
    内部使用重构后的专门管理器，提供与原始接口兼容的API
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
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 创建专门管理器
        self.event_manager = EventManager()
        self.engine_manager = EngineManager(self.event_manager)
        self.lifecycle_manager = LifecycleManager()
        
        # 设置管理器引用
        self.lifecycle_manager.set_managers(
            self.event_manager,
            self.engine_manager,
            None  # replay_manager在子类中设置
        )
        
        # 兼容性属性
        self._status = EngineStatus.INITIALIZED
        self._config = {}
        self._performance_stats = {"processed_events": 0, "start_time": None, "end_time": None}
        
        self.logger.info(f"✅ 基础引擎管理器初始化完成 (类型: {engine_type.name})")
    
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
        try:
            self._config = config or {}
            
            # 初始化各管理器
            if not self.event_manager.initialize(config):
                return False
            
            if not self.engine_manager.initialize(config):
                return False
            
            if not self.lifecycle_manager.initialize(config):
                return False
            
            self._status = EngineStatus.INITIALIZED
            self.logger.info("✅ 引擎管理器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False
    
    def start(self) -> bool:
        """
        启动引擎
        
        Returns
        -------
        bool
            启动是否成功
        """
        try:
            # 启动事件处理
            if not self.event_manager.start_processing():
                return False
            
            self._status = EngineStatus.RUNNING
            self._performance_stats["start_time"] = time.time()
            
            self.logger.info("🚀 引擎已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            self._status = EngineStatus.ERROR
            return False
    
    def pause(self) -> bool:
        """
        暂停引擎
        
        Returns
        -------
        bool
            暂停是否成功
        """
        try:
            if self._status != EngineStatus.RUNNING:
                self.logger.warning(f"引擎未运行，无法暂停 (状态: {self._status.name})")
                return False
            
            self.event_manager.pause_processing()
            self._status = EngineStatus.PAUSED
            
            self.logger.info("⏸️ 引擎已暂停")
            return True
            
        except Exception as e:
            self.logger.error(f"暂停失败: {e}")
            return False
    
    def resume(self) -> bool:
        """
        恢复引擎
        
        Returns
        -------
        bool
            恢复是否成功
        """
        try:
            if self._status != EngineStatus.PAUSED:
                self.logger.warning(f"引擎未暂停，无法恢复 (状态: {self._status.name})")
                return False
            
            self.event_manager.resume_processing()
            self._status = EngineStatus.RUNNING
            
            self.logger.info("▶️ 引擎已恢复")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复失败: {e}")
            return False
    
    def stop(self) -> bool:
        """
        停止引擎
        
        Returns
        -------
        bool
            停止是否成功
        """
        try:
            if self._status not in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
                self.logger.info(f"引擎未运行，无需停止 (状态: {self._status.name})")
                return True
            
            # 停止事件处理
            self.event_manager.stop_processing()
            
            self._status = EngineStatus.STOPPED
            self._performance_stats["end_time"] = time.time()
            
            self.logger.info("⏹️ 引擎已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止失败: {e}")
            return False
    
    def get_status(self) -> EngineStatus:
        """
        获取引擎状态
        
        Returns
        -------
        EngineStatus
            当前引擎状态
        """
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
        return self.event_manager.send_event(event)
    
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
        return self.event_manager.register_event_handler(event_type, handler)
    
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
        # 注意：当前EventManager不支持通过ID注销，这是一个已知限制
        self.logger.warning("通过handler_id注销处理器暂不支持")
        return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        # 合并各管理器的统计信息
        stats = self._performance_stats.copy()
        
        # 添加事件管理器统计
        event_stats = self.event_manager.get_performance_stats()
        stats.update({
            "processed_events": event_stats.get("processed_events", 0),
            "events_per_second": event_stats.get("events_per_second", 0),
            "queue_size": event_stats.get("queue_size", 0),
            "handler_count": event_stats.get("handler_count", 0)
        })
        
        # 计算处理时间
        start_time = stats.get("start_time")
        end_time = stats.get("end_time")
        
        if start_time:
            if end_time:
                processing_time = end_time - start_time
            elif self._status == EngineStatus.RUNNING:
                processing_time = time.time() - start_time
            else:
                processing_time = 0
            
            stats["processing_time"] = processing_time
            stats["current_status"] = self._status.name
        
        return stats


class ReplayEngineManager(BaseEngineManager):
    """
    数据重放引擎管理器（向后兼容）
    
    在BaseEngineManager基础上添加数据重放功能
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
        
        # 创建重放管理器
        self.replay_manager = ReplayManager(self.event_manager)
        
        # 更新生命周期管理器引用
        self.lifecycle_manager.set_managers(
            self.event_manager,
            self.engine_manager,
            self.replay_manager
        )
        
        # 兼容性属性
        self._replay_controllers: Dict[str, Dict[str, Any]] = {}
        self._replay_callbacks: Dict[DataReplayInterface, int] = {}
        self._symbol_mapping: Dict[str, Optional[str]] = {}
        self._data_converters: Dict[str, Optional[Callable]] = {}
        
        self.logger.info("✅ 数据重放引擎管理器初始化完成")
    
    def add_replay_controller(self, name: str, controller: DataReplayInterface, 
                              symbol: Optional[str] = None,
                              data_converter: Optional[Callable] = None) -> bool:
        """
        添加数据重放控制器
        
        Parameters
        ----------
        name : str
            控制器名称
        controller : DataReplayInterface
            数据重放控制器实例
        symbol : Optional[str], optional
            关联的交易标的代码
        data_converter : Optional[Callable], optional
            数据转换函数
            
        Returns
        -------
        bool
            添加是否成功
        """
        try:
            if name in self._replay_controllers:
                self.logger.warning(f"重放控制器 '{name}' 已存在")
                return False
            
            # 存储控制器信息（兼容性）
            self._replay_controllers[name] = {
                "controller": controller,
                "symbol": symbol,
                "converter": data_converter
            }
            
            if symbol:
                self._symbol_mapping[name] = symbol
            
            if data_converter:
                self._data_converters[name] = data_converter
            
            # 注册数据回调
            def data_callback(source_name: str, data: Dict[str, Any]):
                return self._on_replay_data(source_name, data)
            
            self.replay_manager.register_data_callback(name, data_callback)
            
            self.logger.info(f"✅ 已添加重放控制器: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加重放控制器失败: {e}")
            return False
    
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
        try:
            if name not in self._replay_controllers:
                self.logger.warning(f"重放控制器 '{name}' 不存在")
                return False
            
            # 清理兼容性数据
            del self._replay_controllers[name]
            
            if name in self._symbol_mapping:
                del self._symbol_mapping[name]
            
            if name in self._data_converters:
                del self._data_converters[name]
            
            self.logger.info(f"✅ 已移除重放控制器: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除重放控制器失败: {e}")
            return False
    
    def start(self) -> bool:
        """
        启动引擎和所有重放控制器
        
        Returns
        -------
        bool
            启动是否成功
        """
        # 先启动基础引擎
        if not super().start():
            return False
        
        try:
            # 启动重放管理器
            if self._replay_controllers:
                self.replay_manager.start_replay()
            
            self.logger.info("🚀 重放引擎管理器已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动重放功能失败: {e}")
            return False
    
    def stop(self) -> bool:
        """
        停止引擎和所有重放控制器
        
        Returns
        -------
        bool
            停止是否成功
        """
        try:
            # 停止重放管理器
            self.replay_manager.stop_replay()
            
            # 停止基础引擎
            return super().stop()
            
        except Exception as e:
            self.logger.error(f"停止重放功能失败: {e}")
            return False
    
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
        try:
            success = True
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
                if not controller.set_mode(mode):
                    self.logger.warning(f"无法设置控制器 '{name}' 的模式: {mode.name}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置重放模式失败: {e}")
            return False
    
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
        try:
            # 设置重放管理器速度
            config = {"speed_multiplier": speed_factor}
            self.replay_manager.set_replay_config(config)
            
            # 设置各控制器速度（兼容性）
            success = True
            for name, controller_info in self._replay_controllers.items():
                controller = controller_info["controller"]
                if hasattr(controller, 'set_speed'):
                    if not controller.set_speed(speed_factor):
                        self.logger.warning(f"无法设置控制器 '{name}' 的速度: {speed_factor}")
                        success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置重放速度失败: {e}")
            return False
    
    def _on_replay_data(self, source: str, data: Any):
        """
        数据重放回调（兼容性方法）
        
        Parameters
        ----------
        source : str
            数据源标识
        data : Any
            重放数据
        """
        try:
            # 这个方法主要用于兼容性，实际处理由ReplayManager完成
            self.logger.debug(f"收到重放数据: {source}")
            
        except Exception as e:
            self.logger.error(f"处理重放数据失败: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        stats = super().get_performance_stats()
        
        # 添加重放管理器统计
        if self.replay_manager:
            replay_stats = self.replay_manager.get_performance_stats()
            stats["replay_manager"] = replay_stats
        
        # 添加重放控制器状态（兼容性）
        replay_controller_stats = {}
        for name, controller_info in self._replay_controllers.items():
            controller = controller_info["controller"]
            if hasattr(controller, 'get_status'):
                replay_controller_stats[name] = {
                    "status": controller.get_status().name
                }
        
        stats["replay_controllers"] = replay_controller_stats
        
        return stats
