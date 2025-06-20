#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生命周期管理器

专门负责系统生命周期管理、资源清理和状态监控
"""

import time
import threading
import atexit
from typing import Dict, List, Any, Callable, Optional
from .base_manager import BaseManager, EngineStatus
from .event_manager import EventManager
from .engine_manager import EngineManager
from .replay_manager import ReplayManager


class LifecycleManager(BaseManager):
    """
    生命周期管理器
    
    负责系统的启动、停止、资源清理和状态监控
    """
    
    def __init__(self, name: str = "LifecycleManager"):
        """
        初始化生命周期管理器
        
        Parameters
        ----------
        name : str, optional
            管理器名称
        """
        super().__init__(name)
        
        # 管理器引用
        self.event_manager: Optional[EventManager] = None
        self.engine_manager: Optional[EngineManager] = None
        self.replay_manager: Optional[ReplayManager] = None
        
        # 生命周期状态
        self._system_status = EngineStatus.INITIALIZED
        self._startup_time = None
        self._shutdown_time = None
        
        # 生命周期钩子
        self._startup_hooks: List[Callable[[], bool]] = []
        self._shutdown_hooks: List[Callable[[], bool]] = []
        self._cleanup_hooks: List[Callable[[], None]] = []
        
        # 监控线程
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self._monitor_interval = 5.0  # 监控间隔（秒）
        
        # 性能统计
        self._performance_stats = {
            "startup_time": None,
            "shutdown_time": None,
            "uptime": 0.0,
            "total_restarts": 0,
            "last_error": None,
            "error_count": 0
        }
        
        # 注册退出清理
        atexit.register(self._emergency_cleanup)
        
        self.logger.info("✅ 生命周期管理器初始化完成")
    
    def set_managers(self, event_manager: EventManager, 
                    engine_manager: EngineManager, 
                    replay_manager: ReplayManager) -> bool:
        """
        设置管理器引用
        
        Parameters
        ----------
        event_manager : EventManager
            事件管理器
        engine_manager : EngineManager
            引擎管理器
        replay_manager : ReplayManager
            重放管理器
            
        Returns
        -------
        bool
            设置是否成功
        """
        try:
            self.event_manager = event_manager
            self.engine_manager = engine_manager
            self.replay_manager = replay_manager
            
            self.logger.info("✅ 管理器引用已设置")
            return True
            
        except Exception as e:
            self.logger.error(f"设置管理器引用失败: {e}")
            return False
    
    def add_startup_hook(self, hook: Callable[[], bool]) -> bool:
        """
        添加启动钩子
        
        Parameters
        ----------
        hook : Callable[[], bool]
            启动钩子函数，返回True表示成功
            
        Returns
        -------
        bool
            添加是否成功
        """
        if not callable(hook):
            self.logger.error("启动钩子必须是可调用对象")
            return False
        
        self._startup_hooks.append(hook)
        hook_name = getattr(hook, '__name__', str(hook))
        self.logger.debug(f"✅ 已添加启动钩子: {hook_name}")
        return True
    
    def add_shutdown_hook(self, hook: Callable[[], bool]) -> bool:
        """
        添加关闭钩子
        
        Parameters
        ----------
        hook : Callable[[], bool]
            关闭钩子函数，返回True表示成功
            
        Returns
        -------
        bool
            添加是否成功
        """
        if not callable(hook):
            self.logger.error("关闭钩子必须是可调用对象")
            return False
        
        self._shutdown_hooks.append(hook)
        hook_name = getattr(hook, '__name__', str(hook))
        self.logger.debug(f"✅ 已添加关闭钩子: {hook_name}")
        return True
    
    def add_cleanup_hook(self, hook: Callable[[], None]) -> bool:
        """
        添加清理钩子
        
        Parameters
        ----------
        hook : Callable[[], None]
            清理钩子函数
            
        Returns
        -------
        bool
            添加是否成功
        """
        if not callable(hook):
            self.logger.error("清理钩子必须是可调用对象")
            return False
        
        self._cleanup_hooks.append(hook)
        hook_name = getattr(hook, '__name__', str(hook))
        self.logger.debug(f"✅ 已添加清理钩子: {hook_name}")
        return True
    
    def startup_system(self) -> bool:
        """
        启动整个系统
        
        Returns
        -------
        bool
            启动是否成功
        """
        try:
            self.logger.info("🚀 开始系统启动...")
            self._startup_time = time.time()
            
            # 执行启动钩子
            for i, hook in enumerate(self._startup_hooks):
                try:
                    hook_name = getattr(hook, '__name__', f'hook_{i}')
                    self.logger.debug(f"执行启动钩子: {hook_name}")
                    
                    if not hook():
                        self.logger.error(f"启动钩子 {hook_name} 执行失败")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"启动钩子执行异常: {e}")
                    return False
            
            # 启动事件管理器
            if self.event_manager:
                if not self.event_manager.start_processing():
                    self.logger.error("事件管理器启动失败")
                    return False
            
            # 启动引擎管理器
            if self.engine_manager:
                if not self.engine_manager.start():
                    self.logger.error("引擎管理器启动失败")
                    return False
            
            # 启动监控线程
            self._start_monitoring()
            
            self._system_status = EngineStatus.RUNNING
            self._performance_stats["startup_time"] = time.time()
            
            self.logger.info("✅ 系统启动完成")
            return True
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            self._system_status = EngineStatus.ERROR
            self._performance_stats["error_count"] += 1
            self._performance_stats["last_error"] = str(e)
            return False
    
    def shutdown_system(self) -> bool:
        """
        关闭整个系统
        
        Returns
        -------
        bool
            关闭是否成功
        """
        try:
            self.logger.info("🛑 开始系统关闭...")
            self._shutdown_time = time.time()
            
            # 停止监控
            self._stop_monitoring_thread()
            
            # 执行关闭钩子
            for i, hook in enumerate(self._shutdown_hooks):
                try:
                    hook_name = getattr(hook, '__name__', f'hook_{i}')
                    self.logger.debug(f"执行关闭钩子: {hook_name}")
                    
                    hook()  # 关闭钩子不要求返回值
                    
                except Exception as e:
                    self.logger.error(f"关闭钩子执行异常: {e}")
            
            # 停止重放管理器
            if self.replay_manager:
                self.replay_manager.stop_replay()
            
            # 停止引擎管理器
            if self.engine_manager:
                self.engine_manager.stop()
            
            # 停止事件管理器
            if self.event_manager:
                self.event_manager.stop_processing()
            
            # 执行清理钩子
            self._execute_cleanup_hooks()
            
            self._system_status = EngineStatus.STOPPED
            self._performance_stats["shutdown_time"] = time.time()
            
            # 计算运行时间
            if self._startup_time:
                self._performance_stats["uptime"] = self._shutdown_time - self._startup_time
            
            self.logger.info("✅ 系统关闭完成")
            return True
            
        except Exception as e:
            self.logger.error(f"系统关闭失败: {e}")
            self._performance_stats["error_count"] += 1
            self._performance_stats["last_error"] = str(e)
            return False
    
    def restart_system(self) -> bool:
        """
        重启系统
        
        Returns
        -------
        bool
            重启是否成功
        """
        self.logger.info("🔄 开始系统重启...")
        
        # 先关闭
        if not self.shutdown_system():
            self.logger.error("系统关闭失败，重启中止")
            return False
        
        # 等待一段时间
        time.sleep(1.0)
        
        # 再启动
        if not self.startup_system():
            self.logger.error("系统启动失败，重启失败")
            return False
        
        self._performance_stats["total_restarts"] += 1
        self.logger.info("✅ 系统重启完成")
        return True
    
    def get_system_status(self) -> EngineStatus:
        """
        获取系统状态
        
        Returns
        -------
        EngineStatus
            系统状态
        """
        return self._system_status
    
    def get_uptime(self) -> float:
        """
        获取系统运行时间
        
        Returns
        -------
        float
            运行时间（秒）
        """
        if self._startup_time and self._system_status == EngineStatus.RUNNING:
            return time.time() - self._startup_time
        elif self._startup_time and self._shutdown_time:
            return self._shutdown_time - self._startup_time
        else:
            return 0.0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        stats = self._performance_stats.copy()
        stats["current_uptime"] = self.get_uptime()
        stats["system_status"] = self._system_status.name
        
        # 添加各管理器状态
        if self.event_manager:
            stats["event_manager"] = self.event_manager.get_performance_stats()
        
        if self.engine_manager:
            stats["engine_manager"] = self.engine_manager.get_performance_stats()
        
        if self.replay_manager:
            stats["replay_manager"] = self.replay_manager.get_performance_stats()
        
        return stats
    
    def _start_monitoring(self):
        """启动监控线程"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name=f"{self.name}_Monitor"
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        self.logger.debug("📊 系统监控已启动")
    
    def _stop_monitoring_thread(self):
        """停止监控线程"""
        self._stop_monitoring.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            if self._monitor_thread.is_alive():
                self.logger.warning("监控线程未在超时内结束")
            else:
                self.logger.debug("📊 系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        self.logger.debug("🔍 系统监控线程启动")
        
        while not self._stop_monitoring.is_set():
            try:
                # 检查各管理器状态
                self._check_managers_health()
                
                # 等待下次检查
                if self._stop_monitoring.wait(timeout=self._monitor_interval):
                    break
                    
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
        
        self.logger.debug("🔍 系统监控线程结束")
    
    def _check_managers_health(self):
        """检查管理器健康状态"""
        try:
            # 检查事件管理器
            if self.event_manager:
                queue_size = self.event_manager.get_queue_size()
                if queue_size > 10000:  # 队列过大警告
                    self.logger.warning(f"事件队列过大: {queue_size}")
            
            # 检查引擎管理器
            if self.engine_manager:
                engines_info = self.engine_manager.list_engines()
                error_engines = [name for name, info in engines_info.items() 
                               if info["status"] == EngineStatus.ERROR]
                if error_engines:
                    self.logger.warning(f"发现错误状态引擎: {error_engines}")
            
        except Exception as e:
            self.logger.error(f"健康检查异常: {e}")
    
    def _execute_cleanup_hooks(self):
        """执行清理钩子"""
        for i, hook in enumerate(self._cleanup_hooks):
            try:
                hook_name = getattr(hook, '__name__', f'cleanup_hook_{i}')
                self.logger.debug(f"执行清理钩子: {hook_name}")
                hook()
            except Exception as e:
                self.logger.error(f"清理钩子执行异常: {e}")
    
    def _emergency_cleanup(self):
        """紧急清理（程序退出时调用）"""
        try:
            if self._system_status == EngineStatus.RUNNING:
                self.logger.warning("⚠️ 检测到程序异常退出，执行紧急清理...")
                self.shutdown_system()
        except Exception as e:
            # 紧急清理时不能抛出异常
            print(f"Emergency cleanup error: {e}")
