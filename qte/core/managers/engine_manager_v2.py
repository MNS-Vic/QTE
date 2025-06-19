"""
引擎管理器 V2 - 基于接口的重构版本

提供统一的引擎管理功能，支持多种引擎类型的创建、配置和调度
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from ..interfaces.engine_interface import IBacktestEngine, IEngineManager, BacktestResult
from ..engines.engine_registry import EngineRegistry, register_builtin_engines


@dataclass
class BacktestTask:
    """回测任务"""
    task_id: str
    engine_type: str
    config: Dict[str, Any]
    data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]
    strategies: List[Any]
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[BacktestResult] = None
    error: Optional[str] = None


class EngineManagerV2(IEngineManager):
    """
    引擎管理器 V2
    
    基于接口的重构版本，提供统一的引擎管理功能：
    - 引擎注册和发现
    - 引擎实例创建和管理
    - 回测任务调度和执行
    - 性能监控和资源管理
    """
    
    def __init__(self):
        """初始化引擎管理器"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 引擎注册表
        self._registry = EngineRegistry()
        
        # 活动引擎实例
        self._active_engines: Dict[str, IBacktestEngine] = {}
        
        # 回测任务
        self._tasks: Dict[str, BacktestTask] = {}
        self._task_counter = 0
        
        # 管理器状态
        self._initialized = False
        
        # 注册内置引擎
        register_builtin_engines()
        
        self.logger.info("🔧 引擎管理器V2初始化完成")
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化管理器
        
        Args:
            config: 管理器配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            self._config = config.copy()
            self._initialized = True
            
            self.logger.info("✅ 引擎管理器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 引擎管理器初始化失败: {e}")
            return False
    
    def register_engine(self, engine_type: str, engine_class: type) -> bool:
        """
        注册引擎类型
        
        Args:
            engine_type: 引擎类型标识
            engine_class: 引擎类
            
        Returns:
            bool: 注册是否成功
        """
        return self._registry.register_engine(engine_type, engine_class)
    
    def create_engine(self, engine_type: str, config: Dict[str, Any]) -> Optional[IBacktestEngine]:
        """
        创建引擎实例
        
        Args:
            engine_type: 引擎类型
            config: 引擎配置
            
        Returns:
            Optional[IBacktestEngine]: 引擎实例，失败时返回None
        """
        try:
            engine = self._registry.create_engine(engine_type, config)
            
            if engine:
                # 生成引擎实例ID
                instance_id = f"{engine_type}_{int(time.time() * 1000)}"
                self._active_engines[instance_id] = engine
                
                self.logger.info(f"✅ 引擎实例创建成功: {instance_id}")
                return engine
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 引擎实例创建失败: {e}")
            return None
    
    def get_available_engines(self) -> List[str]:
        """
        获取可用的引擎类型
        
        Returns:
            List[str]: 可用引擎类型列表
        """
        return self._registry.get_available_engines()
    
    def get_engine_info(self, engine_type: str) -> Dict[str, Any]:
        """
        获取引擎信息
        
        Args:
            engine_type: 引擎类型
            
        Returns:
            Dict[str, Any]: 引擎信息
        """
        return self._registry.get_engine_info(engine_type)
    
    def submit_backtest_task(self, 
                           engine_type: str,
                           config: Dict[str, Any],
                           data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
                           strategies: List[Any]) -> str:
        """
        提交回测任务
        
        Args:
            engine_type: 引擎类型
            config: 引擎配置
            data: 回测数据
            strategies: 交易策略列表
            
        Returns:
            str: 任务ID
        """
        try:
            # 生成任务ID
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{int(time.time())}"
            
            # 创建任务
            task = BacktestTask(
                task_id=task_id,
                engine_type=engine_type,
                config=config,
                data=data,
                strategies=strategies
            )
            
            self._tasks[task_id] = task
            
            self.logger.info(f"📋 回测任务已提交: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"❌ 回测任务提交失败: {e}")
            return ""
    
    def execute_backtest_task(self, task_id: str) -> BacktestResult:
        """
        执行回测任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            BacktestResult: 回测结果
        """
        if task_id not in self._tasks:
            result = BacktestResult()
            result.add_error(f"任务不存在: {task_id}")
            return result
        
        task = self._tasks[task_id]
        
        try:
            # 更新任务状态
            task.status = "running"
            task.started_at = datetime.now()
            
            self.logger.info(f"🚀 开始执行回测任务: {task_id}")
            
            # 创建引擎实例
            engine = self.create_engine(task.engine_type, task.config)
            if not engine:
                raise Exception(f"无法创建引擎: {task.engine_type}")
            
            # 设置数据
            if not engine.set_data(task.data):
                raise Exception("数据设置失败")
            
            # 添加策略
            for strategy in task.strategies:
                if not engine.add_strategy(strategy):
                    raise Exception(f"策略添加失败: {strategy.__class__.__name__}")
            
            # 执行回测
            result = engine.run_backtest()
            
            # 更新任务状态
            task.status = "completed" if result.success else "failed"
            task.completed_at = datetime.now()
            task.result = result
            
            # 清理引擎资源
            engine.cleanup()
            
            self.logger.info(f"🎉 回测任务执行完成: {task_id}")
            return result
            
        except Exception as e:
            # 更新任务状态
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error = str(e)
            
            # 创建失败结果
            result = BacktestResult()
            result.add_error(str(e))
            task.result = result
            
            self.logger.error(f"❌ 回测任务执行失败: {task_id}, 错误: {e}")
            return result
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        if task_id not in self._tasks:
            return {'error': f'任务不存在: {task_id}'}
        
        task = self._tasks[task_id]
        
        return {
            'task_id': task.task_id,
            'engine_type': task.engine_type,
            'status': task.status,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error': task.error,
            'has_result': task.result is not None
        }
    
    def get_task_result(self, task_id: str) -> Optional[BacktestResult]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[BacktestResult]: 回测结果
        """
        if task_id not in self._tasks:
            return None
        
        return self._tasks[task_id].result
    
    def list_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status_filter: 状态过滤器
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        tasks = []
        
        for task in self._tasks.values():
            if status_filter is None or task.status == status_filter:
                tasks.append(self.get_task_status(task.task_id))
        
        return tasks
    
    def cleanup_completed_tasks(self, keep_recent: int = 10) -> int:
        """
        清理已完成的任务
        
        Args:
            keep_recent: 保留最近的任务数量
            
        Returns:
            int: 清理的任务数量
        """
        completed_tasks = [
            task for task in self._tasks.values()
            if task.status in ['completed', 'failed']
        ]
        
        # 按完成时间排序，保留最近的任务
        completed_tasks.sort(key=lambda x: x.completed_at or datetime.min, reverse=True)
        
        tasks_to_remove = completed_tasks[keep_recent:]
        removed_count = 0
        
        for task in tasks_to_remove:
            if task.task_id in self._tasks:
                del self._tasks[task.task_id]
                removed_count += 1
        
        if removed_count > 0:
            self.logger.info(f"🧹 清理了 {removed_count} 个已完成的任务")
        
        return removed_count
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """
        获取管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        task_status_count = {}
        for task in self._tasks.values():
            task_status_count[task.status] = task_status_count.get(task.status, 0) + 1
        
        return {
            'total_tasks': len(self._tasks),
            'active_engines': len(self._active_engines),
            'available_engine_types': len(self.get_available_engines()),
            'task_status_distribution': task_status_count,
            'engine_registry_stats': self._registry.get_engine_statistics()
        }
    
    def shutdown(self) -> bool:
        """
        关闭管理器
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 清理活动引擎
            for engine in self._active_engines.values():
                try:
                    engine.cleanup()
                except Exception as e:
                    self.logger.warning(f"引擎清理时发生异常: {e}")
            
            self._active_engines.clear()
            self._tasks.clear()
            self._initialized = False
            
            self.logger.info("🔒 引擎管理器已关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 引擎管理器关闭失败: {e}")
            return False
