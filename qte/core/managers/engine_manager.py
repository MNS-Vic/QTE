#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎管理器

专门负责回测引擎的管理、配置和执行控制
"""

import logging
from typing import Dict, List, Any, Optional, Type
from qte.core.events import Event as CoreEvent
from .base_manager import BaseManager, EngineManagerInterface, EngineType, EngineStatus
from .event_manager import EventManager


class EngineManager(BaseManager, EngineManagerInterface):
    """
    引擎管理器
    
    负责回测引擎的创建、配置、启动和监控
    """
    
    def __init__(self, event_manager: EventManager, name: str = "EngineManager"):
        """
        初始化引擎管理器
        
        Parameters
        ----------
        event_manager : EventManager
            事件管理器实例
        name : str, optional
            管理器名称
        """
        super().__init__(name)
        
        self.event_manager = event_manager
        
        # 引擎注册表
        self._engine_registry: Dict[str, Type] = {}
        self._active_engines: Dict[str, Any] = {}
        self._engine_configs: Dict[str, Dict[str, Any]] = {}
        
        # 引擎状态
        self._engine_status: Dict[str, EngineStatus] = {}
        self._primary_engine: Optional[str] = None
        
        # 性能统计
        self._performance_stats = {
            "engines_created": 0,
            "engines_started": 0,
            "engines_completed": 0,
            "engines_failed": 0,
            "total_events_processed": 0
        }
        
        self.logger.info("✅ 引擎管理器初始化完成")
    
    def register_engine_type(self, engine_name: str, engine_class: Type) -> bool:
        """
        注册引擎类型
        
        Parameters
        ----------
        engine_name : str
            引擎名称
        engine_class : Type
            引擎类
            
        Returns
        -------
        bool
            注册是否成功
        """
        try:
            if not isinstance(engine_name, str) or not engine_name:
                self.logger.error("引擎名称必须是非空字符串")
                return False
            
            if not hasattr(engine_class, 'run_backtest'):
                self.logger.error(f"引擎类 {engine_class} 必须实现 run_backtest 方法")
                return False
            
            self._engine_registry[engine_name] = engine_class
            self.logger.info(f"✅ 已注册引擎类型: {engine_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册引擎类型失败: {e}")
            return False
    
    def create_engine(self, engine_name: str, engine_type: str, config: Dict[str, Any] = None) -> bool:
        """
        创建引擎实例
        
        Parameters
        ----------
        engine_name : str
            引擎实例名称
        engine_type : str
            引擎类型名称
        config : Dict[str, Any], optional
            引擎配置
            
        Returns
        -------
        bool
            创建是否成功
        """
        try:
            if engine_type not in self._engine_registry:
                self.logger.error(f"未知的引擎类型: {engine_type}")
                return False
            
            if engine_name in self._active_engines:
                self.logger.warning(f"引擎 {engine_name} 已存在")
                return False
            
            # 创建引擎实例
            engine_class = self._engine_registry[engine_type]
            engine_instance = engine_class()
            
            # 初始化引擎
            engine_config = config or {}
            if hasattr(engine_instance, 'initialize'):
                init_success = engine_instance.initialize(engine_config)
                if not init_success:
                    self.logger.error(f"引擎 {engine_name} 初始化失败")
                    return False
            
            # 注册引擎
            self._active_engines[engine_name] = engine_instance
            self._engine_configs[engine_name] = engine_config
            self._engine_status[engine_name] = EngineStatus.INITIALIZED
            
            # 设置为主引擎（如果是第一个）
            if self._primary_engine is None:
                self._primary_engine = engine_name
            
            self._performance_stats["engines_created"] += 1
            
            self.logger.info(f"✅ 已创建引擎: {engine_name} (类型: {engine_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"创建引擎失败: {e}")
            return False
    
    def start_engine(self, engine_name: str = None) -> bool:
        """
        启动引擎
        
        Parameters
        ----------
        engine_name : str, optional
            引擎名称，如果为None则启动主引擎
            
        Returns
        -------
        bool
            启动是否成功
        """
        target_engine = engine_name or self._primary_engine
        
        if not target_engine:
            self.logger.error("没有可启动的引擎")
            return False
        
        if target_engine not in self._active_engines:
            self.logger.error(f"引擎 {target_engine} 不存在")
            return False
        
        try:
            engine = self._active_engines[target_engine]
            
            # 检查引擎状态
            current_status = self._engine_status.get(target_engine, EngineStatus.INITIALIZED)
            if current_status == EngineStatus.RUNNING:
                self.logger.warning(f"引擎 {target_engine} 已在运行")
                return True
            
            # 启动引擎
            if hasattr(engine, 'start'):
                start_success = engine.start()
                if start_success:
                    self._engine_status[target_engine] = EngineStatus.RUNNING
                    self._performance_stats["engines_started"] += 1
                    self.logger.info(f"🚀 引擎 {target_engine} 已启动")
                    return True
                else:
                    self._engine_status[target_engine] = EngineStatus.ERROR
                    self.logger.error(f"引擎 {target_engine} 启动失败")
                    return False
            else:
                self.logger.warning(f"引擎 {target_engine} 不支持启动操作")
                return False
                
        except Exception as e:
            self._engine_status[target_engine] = EngineStatus.ERROR
            self.logger.error(f"启动引擎失败: {e}")
            return False
    
    def stop_engine(self, engine_name: str = None) -> bool:
        """
        停止引擎
        
        Parameters
        ----------
        engine_name : str, optional
            引擎名称，如果为None则停止主引擎
            
        Returns
        -------
        bool
            停止是否成功
        """
        target_engine = engine_name or self._primary_engine
        
        if not target_engine or target_engine not in self._active_engines:
            self.logger.error(f"引擎 {target_engine} 不存在")
            return False
        
        try:
            engine = self._active_engines[target_engine]
            
            # 停止引擎
            if hasattr(engine, 'stop'):
                stop_success = engine.stop()
                if stop_success:
                    self._engine_status[target_engine] = EngineStatus.STOPPED
                    self.logger.info(f"⏹️ 引擎 {target_engine} 已停止")
                    return True
                else:
                    self.logger.error(f"引擎 {target_engine} 停止失败")
                    return False
            else:
                # 如果没有stop方法，直接标记为停止
                self._engine_status[target_engine] = EngineStatus.STOPPED
                self.logger.info(f"⏹️ 引擎 {target_engine} 已标记为停止")
                return True
                
        except Exception as e:
            self.logger.error(f"停止引擎失败: {e}")
            return False
    
    def pause_engine(self, engine_name: str = None) -> bool:
        """
        暂停引擎
        
        Parameters
        ----------
        engine_name : str, optional
            引擎名称，如果为None则暂停主引擎
            
        Returns
        -------
        bool
            暂停是否成功
        """
        target_engine = engine_name or self._primary_engine
        
        if not target_engine or target_engine not in self._active_engines:
            self.logger.error(f"引擎 {target_engine} 不存在")
            return False
        
        try:
            engine = self._active_engines[target_engine]
            
            if hasattr(engine, 'pause'):
                pause_success = engine.pause()
                if pause_success:
                    self._engine_status[target_engine] = EngineStatus.PAUSED
                    self.logger.info(f"⏸️ 引擎 {target_engine} 已暂停")
                    return True
            
            self.logger.warning(f"引擎 {target_engine} 不支持暂停操作")
            return False
            
        except Exception as e:
            self.logger.error(f"暂停引擎失败: {e}")
            return False
    
    def resume_engine(self, engine_name: str = None) -> bool:
        """
        恢复引擎
        
        Parameters
        ----------
        engine_name : str, optional
            引擎名称，如果为None则恢复主引擎
            
        Returns
        -------
        bool
            恢复是否成功
        """
        target_engine = engine_name or self._primary_engine
        
        if not target_engine or target_engine not in self._active_engines:
            self.logger.error(f"引擎 {target_engine} 不存在")
            return False
        
        try:
            engine = self._active_engines[target_engine]
            
            if hasattr(engine, 'resume'):
                resume_success = engine.resume()
                if resume_success:
                    self._engine_status[target_engine] = EngineStatus.RUNNING
                    self.logger.info(f"▶️ 引擎 {target_engine} 已恢复")
                    return True
            
            self.logger.warning(f"引擎 {target_engine} 不支持恢复操作")
            return False
            
        except Exception as e:
            self.logger.error(f"恢复引擎失败: {e}")
            return False
    
    def get_engine(self, engine_name: str) -> Optional[Any]:
        """
        获取引擎实例
        
        Parameters
        ----------
        engine_name : str
            引擎名称
            
        Returns
        -------
        Optional[Any]
            引擎实例，如果不存在返回None
        """
        return self._active_engines.get(engine_name)
    
    def get_primary_engine(self) -> Optional[Any]:
        """
        获取主引擎实例
        
        Returns
        -------
        Optional[Any]
            主引擎实例，如果不存在返回None
        """
        if self._primary_engine:
            return self._active_engines.get(self._primary_engine)
        return None
    
    def set_primary_engine(self, engine_name: str) -> bool:
        """
        设置主引擎
        
        Parameters
        ----------
        engine_name : str
            引擎名称
            
        Returns
        -------
        bool
            设置是否成功
        """
        if engine_name not in self._active_engines:
            self.logger.error(f"引擎 {engine_name} 不存在")
            return False
        
        self._primary_engine = engine_name
        self.logger.info(f"✅ 已设置主引擎: {engine_name}")
        return True
    
    def list_engines(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有引擎
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            引擎信息字典
        """
        engines_info = {}
        
        for engine_name in self._active_engines:
            engines_info[engine_name] = {
                "status": self._engine_status.get(engine_name, EngineStatus.INITIALIZED),
                "config": self._engine_configs.get(engine_name, {}),
                "is_primary": engine_name == self._primary_engine
            }
        
        return engines_info
    
    # 实现EngineManagerInterface的抽象方法
    def start(self) -> bool:
        """启动主引擎"""
        return self.start_engine()
    
    def pause(self) -> bool:
        """暂停主引擎"""
        return self.pause_engine()
    
    def resume(self) -> bool:
        """恢复主引擎"""
        return self.resume_engine()
    
    def stop(self) -> bool:
        """停止主引擎"""
        return self.stop_engine()
    
    def get_status(self) -> EngineStatus:
        """获取主引擎状态"""
        if self._primary_engine:
            return self._engine_status.get(self._primary_engine, EngineStatus.INITIALIZED)
        return EngineStatus.INITIALIZED
    
    def send_event(self, event: CoreEvent) -> bool:
        """发送事件到事件管理器"""
        return self.event_manager.send_event(event)
    
    def register_event_handler(self, event_type: str, handler) -> int:
        """注册事件处理器"""
        return self.event_manager.register_event_handler(event_type, handler)
    
    def unregister_event_handler(self, handler_id: int) -> bool:
        """注销事件处理器"""
        # 注意：这里需要修改EventManager的接口来支持handler_id
        self.logger.warning("unregister_event_handler 需要EventManager支持handler_id")
        return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        stats = self._performance_stats.copy()
        
        # 添加引擎状态统计
        status_counts = {}
        for status in self._engine_status.values():
            status_name = status.name
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        stats["engine_status_counts"] = status_counts
        stats["total_engines"] = len(self._active_engines)
        stats["primary_engine"] = self._primary_engine
        
        return stats
