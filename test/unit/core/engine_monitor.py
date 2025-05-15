#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎监控系统

用于监控引擎和数据重放控制器的健康状态，
检测线程阻塞、内存泄漏等问题，并在发现问题时
自动采取修复措施。
"""

import os
import sys
import time
import logging
import threading
import traceback
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入核心组件
try:
    from qte.core.engine_manager import ReplayEngineManager, EngineStatus
    from qte.data.data_replay import BaseDataReplayController, ReplayStatus
except ImportError:
    # 如果在测试环境中无法导入
    class EngineStatus(Enum):
        INITIALIZED = 1
        RUNNING = 2
        PAUSED = 3
        STOPPED = 4
        COMPLETED = 5
        ERROR = 6
    
    class ReplayStatus(Enum):
        INITIALIZED = 1
        RUNNING = 2
        PAUSED = 3
        STOPPED = 4
        COMPLETED = 5

# 设置日志
logger = logging.getLogger("EngineMonitor")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class HealthStatus(Enum):
    """健康状态枚举"""
    EXCELLENT = 1   # 极佳：系统运行完美
    GOOD = 2        # 良好：系统运行正常，性能指标在预期范围内
    FAIR = 3        # 一般：有轻微问题但不影响正常运行
    WARNING = 4     # 警告：存在潜在问题，需要关注
    CRITICAL = 5    # 严重：存在严重问题，需要立即处理

class ResourceType(Enum):
    """资源类型枚举"""
    CPU = 1         # CPU使用率
    MEMORY = 2      # 内存使用
    THREAD = 3      # 线程状态
    EVENT_QUEUE = 4 # 事件队列
    IO = 5          # I/O操作
    CALLBACK = 6    # 回调执行

class MonitorConfig:
    """监控配置"""
    def __init__(self):
        # 监控间隔（秒）
        self.interval = 1.0
        
        # 健康检查阈值
        self.cpu_warning_threshold = 80.0  # CPU使用率警告阈值（%）
        self.cpu_critical_threshold = 95.0  # CPU使用率严重阈值（%）
        self.memory_warning_threshold = 80.0  # 内存使用警告阈值（%）
        self.memory_critical_threshold = 95.0  # 内存使用严重阈值（%）
        self.thread_stall_timeout = 5.0  # 线程停滞超时（秒）
        self.queue_warning_size = 1000  # 队列警告大小
        self.queue_critical_size = 5000  # 队列严重大小
        self.callback_error_threshold = 5  # 回调错误阈值
        
        # 自动修复设置
        self.auto_recovery = True  # 是否自动修复
        self.max_recovery_attempts = 3  # 最大修复尝试次数
        self.recovery_cooldown = 60.0  # 修复冷却时间（秒）
        
        # 警报设置
        self.enable_alerts = True  # 是否启用警报
        self.alert_cooldown = 300.0  # 警报冷却时间（秒）

class EngineMonitor:
    """引擎监控系统"""
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        """
        初始化引擎监控系统
        
        Parameters
        ----------
        config : Optional[MonitorConfig], optional
            监控配置, by default None
        """
        self.config = config if config is not None else MonitorConfig()
        
        # 状态信息
        self._running = False
        self._monitor_thread = None
        self._lock = threading.Lock()
        
        # 监控目标
        self._engine_manager = None
        self._replay_controllers = {}
        
        # 统计信息
        self._health_history = []
        self._resource_usage = {}
        self._recovery_attempts = {}
        self._last_alert_time = {}
        self._last_recovery_time = {}
        
        # 回调函数
        self._status_callbacks = {}
        self._alert_callbacks = {}
        self._recovery_callbacks = {}
        self._callback_counter = 0
        
        # 进程监控
        self._process = psutil.Process()
        
        logger.info("引擎监控系统已初始化")
    
    def register_engine_manager(self, manager: Any) -> bool:
        """
        注册引擎管理器
        
        Parameters
        ----------
        manager : Any
            引擎管理器实例
            
        Returns
        -------
        bool
            是否成功注册
        """
        with self._lock:
            if not hasattr(manager, 'get_status'):
                logger.error("引擎管理器必须实现 get_status 方法")
                return False
            
            self._engine_manager = manager
            logger.info("已注册引擎管理器")
            return True
    
    def register_replay_controller(self, name: str, controller: Any) -> bool:
        """
        注册数据重放控制器
        
        Parameters
        ----------
        name : str
            控制器名称
        controller : Any
            控制器实例
            
        Returns
        -------
        bool
            是否成功注册
        """
        with self._lock:
            if not hasattr(controller, 'get_status'):
                logger.error(f"控制器 '{name}' 必须实现 get_status 方法")
                return False
            
            self._replay_controllers[name] = controller
            logger.info(f"已注册重放控制器: {name}")
            return True
    
    def start_monitoring(self) -> bool:
        """
        启动监控
        
        Returns
        -------
        bool
            是否成功启动
        """
        with self._lock:
            if self._running:
                logger.warning("监控已经在运行中")
                return False
            
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitoring_task)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            
            logger.info("监控已启动")
            return True
    
    def stop_monitoring(self) -> bool:
        """
        停止监控
        
        Returns
        -------
        bool
            是否成功停止
        """
        with self._lock:
            if not self._running:
                logger.warning("监控未在运行")
                return False
            
            self._running = False
            
            if self._monitor_thread is not None:
                self._monitor_thread.join(timeout=2.0)
            
            logger.info("监控已停止")
            return True
    
    def get_health_status(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        获取当前健康状态
        
        Returns
        -------
        Tuple[HealthStatus, Dict[str, Any]]
            健康状态和详细信息
        """
        with self._lock:
            if not self._health_history:
                return HealthStatus.FAIR, {"message": "尚未收集健康数据"}
            
            return self._health_history[-1]
    
    def get_resource_usage(self) -> Dict[ResourceType, Dict[str, Any]]:
        """
        获取资源使用情况
        
        Returns
        -------
        Dict[ResourceType, Dict[str, Any]]
            各类资源的使用情况
        """
        with self._lock:
            return self._resource_usage.copy()
    
    def get_health_trend(self, hours: float = 1.0) -> pd.DataFrame:
        """
        获取健康趋势数据
        
        Parameters
        ----------
        hours : float, optional
            获取最近几小时的数据, by default 1.0
            
        Returns
        -------
        pd.DataFrame
            健康趋势数据
        """
        with self._lock:
            if not self._health_history:
                return pd.DataFrame()
            
            # 转换为DataFrame
            data = []
            for status, details in self._health_history:
                record = {
                    'timestamp': details.get('timestamp', datetime.now()),
                    'status': status.name
                }
                
                # 添加资源使用情况
                if 'resources' in details:
                    for resource_type, metrics in details['resources'].items():
                        for metric_name, value in metrics.items():
                            record[f"{resource_type.name.lower()}_{metric_name}"] = value
                
                data.append(record)
            
            df = pd.DataFrame(data)
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
                
                # 过滤最近的数据
                cutoff = datetime.now() - timedelta(hours=hours)
                df = df[df.index >= cutoff]
            
            return df
    
    def register_status_callback(self, callback: Callable[[HealthStatus, Dict[str, Any]], None]) -> int:
        """
        注册状态回调
        
        Parameters
        ----------
        callback : Callable[[HealthStatus, Dict[str, Any]], None]
            回调函数，接收健康状态和详细信息
            
        Returns
        -------
        int
            回调ID
        """
        with self._lock:
            self._callback_counter += 1
            self._status_callbacks[self._callback_counter] = callback
            return self._callback_counter
    
    def register_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> int:
        """
        注册警报回调
        
        Parameters
        ----------
        callback : Callable[[str, Dict[str, Any]], None]
            回调函数，接收警报消息和详细信息
            
        Returns
        -------
        int
            回调ID
        """
        with self._lock:
            self._callback_counter += 1
            self._alert_callbacks[self._callback_counter] = callback
            return self._callback_counter
    
    def unregister_callback(self, callback_id: int) -> bool:
        """
        注销回调
        
        Parameters
        ----------
        callback_id : int
            回调ID
            
        Returns
        -------
        bool
            是否成功注销
        """
        with self._lock:
            removed = False
            
            if callback_id in self._status_callbacks:
                del self._status_callbacks[callback_id]
                removed = True
                
            if callback_id in self._alert_callbacks:
                del self._alert_callbacks[callback_id]
                removed = True
                
            if callback_id in self._recovery_callbacks:
                del self._recovery_callbacks[callback_id]
                removed = True
                
            return removed
    
    def _monitoring_task(self):
        """监控线程的主任务"""
        logger.info("监控任务开始")
        
        while self._running:
            try:
                # 收集健康数据
                health_status, details = self._check_health()
                
                with self._lock:
                    # 更新历史记录
                    self._health_history.append((health_status, details))
                    # 只保留最近1000条记录
                    if len(self._health_history) > 1000:
                        self._health_history = self._health_history[-1000:]
                
                # 触发状态回调
                self._notify_status_callbacks(health_status, details)
                
                # 检查是否需要触发警报
                if health_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    self._handle_health_issue(health_status, details)
                
            except Exception as e:
                logger.error(f"监控任务异常: {str(e)}")
                logger.error(traceback.format_exc())
            
            # 等待下一个监控周期
            time.sleep(self.config.interval)
        
        logger.info("监控任务结束")
    
    def _check_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        检查系统健康状态
        
        Returns
        -------
        Tuple[HealthStatus, Dict[str, Any]]
            健康状态和详细信息
        """
        timestamp = datetime.now()
        resource_data = {}
        issues = []
        
        # ===== 检查CPU使用率 =====
        try:
            cpu_percent = self._process.cpu_percent()
            resource_data[ResourceType.CPU] = {
                'usage_percent': cpu_percent
            }
            
            if cpu_percent >= self.config.cpu_critical_threshold:
                issues.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            elif cpu_percent >= self.config.cpu_warning_threshold:
                issues.append(f"CPU使用率较高: {cpu_percent:.1f}%")
        except Exception as e:
            logger.error(f"检查CPU使用率异常: {str(e)}")
        
        # ===== 检查内存使用 =====
        try:
            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()
            resource_data[ResourceType.MEMORY] = {
                'usage_percent': memory_percent,
                'rss': memory_info.rss,
                'vms': memory_info.vms
            }
            
            if memory_percent >= self.config.memory_critical_threshold:
                issues.append(f"内存使用率过高: {memory_percent:.1f}%")
            elif memory_percent >= self.config.memory_warning_threshold:
                issues.append(f"内存使用率较高: {memory_percent:.1f}%")
        except Exception as e:
            logger.error(f"检查内存使用异常: {str(e)}")
        
        # ===== 检查引擎状态 =====
        engine_status = None
        if self._engine_manager is not None:
            try:
                engine_status = self._engine_manager.get_status()
                engine_stats = {}
                
                # 如果引擎有性能统计方法
                if hasattr(self._engine_manager, 'get_performance_stats'):
                    engine_stats = self._engine_manager.get_performance_stats()
                
                resource_data[ResourceType.EVENT_QUEUE] = {
                    'engine_status': engine_status.name,
                    **engine_stats
                }
                
                if engine_status == EngineStatus.ERROR:
                    issues.append("引擎处于错误状态")
            except Exception as e:
                logger.error(f"检查引擎状态异常: {str(e)}")
                issues.append(f"无法获取引擎状态: {str(e)}")
        
        # ===== 检查重放控制器 =====
        controller_issues = []
        for name, controller in self._replay_controllers.items():
            try:
                controller_status = controller.get_status()
                controller_data = {
                    'status': controller_status.name
                }
                
                # 如果控制器有健康统计方法
                if hasattr(controller, 'get_health_stats'):
                    controller_data.update(controller.get_health_stats())
                
                # 记录回调错误
                if 'callback_errors' in controller_data and controller_data['callback_errors'] > self.config.callback_error_threshold:
                    controller_issues.append(f"控制器 '{name}' 回调错误过多: {controller_data['callback_errors']}")
                
                # 检查活动时间
                if 'last_activity_time' in controller_data and 'idle_time' in controller_data:
                    if controller_status == ReplayStatus.RUNNING and controller_data['idle_time'] > self.config.thread_stall_timeout:
                        controller_issues.append(f"控制器 '{name}' 可能已停滞: {controller_data['idle_time']:.1f}秒无活动")
                
                if ResourceType.CALLBACK not in resource_data:
                    resource_data[ResourceType.CALLBACK] = {}
                
                resource_data[ResourceType.CALLBACK][name] = controller_data
            
            except Exception as e:
                logger.error(f"检查控制器 '{name}' 状态异常: {str(e)}")
                controller_issues.append(f"无法获取控制器 '{name}' 状态: {str(e)}")
        
        issues.extend(controller_issues)
        
        # ===== 检查线程状态 =====
        try:
            thread_count = threading.active_count()
            resource_data[ResourceType.THREAD] = {
                'count': thread_count
            }
            
            # 如果线程数过多可能有问题
            if thread_count > 100:  # 根据具体应用调整阈值
                issues.append(f"活跃线程数过多: {thread_count}")
        except Exception as e:
            logger.error(f"检查线程状态异常: {str(e)}")
        
        # ===== 获取IO使用情况 =====
        try:
            io_counters = self._process.io_counters()
            resource_data[ResourceType.IO] = {
                'read_count': io_counters.read_count,
                'write_count': io_counters.write_count,
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes
            }
        except Exception as e:
            logger.error(f"获取IO使用情况异常: {str(e)}")
        
        # ===== 确定健康状态 =====
        health_status = HealthStatus.EXCELLENT
        
        if controller_issues:
            # 如果有控制器问题，至少是警告级别
            health_status = HealthStatus.WARNING
        
        if issues and not controller_issues:
            # 资源使用高但无控制器问题，视为一般状态
            health_status = HealthStatus.FAIR
        
        if engine_status == EngineStatus.ERROR or len(issues) >= 3:
            # 引擎错误或多个问题，视为严重状态
            health_status = HealthStatus.CRITICAL
        
        # 根据控制器问题的数量调整状态
        if len(controller_issues) >= 3:
            health_status = HealthStatus.CRITICAL
        
        # 保存资源使用情况
        with self._lock:
            self._resource_usage = resource_data
        
        # 返回健康状态和详细信息
        return health_status, {
            'timestamp': timestamp,
            'status': health_status.name,
            'resources': resource_data,
            'issues': issues
        }
    
    def _handle_health_issue(self, status: HealthStatus, details: Dict[str, Any]):
        """
        处理健康问题
        
        Parameters
        ----------
        status : HealthStatus
            健康状态
        details : Dict[str, Any]
            详细信息
        """
        issues = details.get('issues', [])
        issue_key = '-'.join(sorted(issues))  # 用排序后的问题列表作为键
        current_time = time.time()
        
        # 检查是否可以发送警报
        should_alert = (self.config.enable_alerts and 
                        (issue_key not in self._last_alert_time or 
                         current_time - self._last_alert_time.get(issue_key, 0) > self.config.alert_cooldown))
        
        if should_alert:
            # 更新最后警报时间
            self._last_alert_time[issue_key] = current_time
            
            # 构建警报消息
            message = f"健康状态: {status.name}\n"
            if issues:
                message += "问题:\n" + "\n".join([f"- {issue}" for issue in issues])
            
            # 触发警报回调
            self._notify_alert_callbacks(message, details)
        
        # 检查是否需要自动修复
        if (self.config.auto_recovery and status == HealthStatus.CRITICAL and 
            (issue_key not in self._last_recovery_time or 
             current_time - self._last_recovery_time.get(issue_key, 0) > self.config.recovery_cooldown)):
            
            # 检查修复尝试次数
            attempts = self._recovery_attempts.get(issue_key, 0)
            if attempts < self.config.max_recovery_attempts:
                # 增加尝试次数
                self._recovery_attempts[issue_key] = attempts + 1
                self._last_recovery_time[issue_key] = current_time
                
                # 尝试自动修复
                self._attempt_recovery(issues, details)
    
    def _attempt_recovery(self, issues: List[str], details: Dict[str, Any]):
        """
        尝试自动修复
        
        Parameters
        ----------
        issues : List[str]
            问题列表
        details : Dict[str, Any]
            详细信息
        """
        logger.info("尝试自动修复...")
        
        # 存储已恢复的问题
        recovered_issues = []
        
        # 检查控制器停滞问题
        for issue in issues:
            if "控制器" in issue and "可能已停滞" in issue:
                controller_name = issue.split("'")[1]
                if controller_name in self._replay_controllers:
                    controller = self._replay_controllers[controller_name]
                    
                    try:
                        # 尝试暂停并恢复控制器
                        logger.info(f"尝试重启控制器: {controller_name}")
                        controller.pause()
                        time.sleep(0.5)
                        controller.resume()
                        recovered_issues.append(issue)
                    except Exception as e:
                        logger.error(f"重启控制器 '{controller_name}' 失败: {str(e)}")
        
        # 检查CPU/内存使用过高问题
        high_resource_usage = any("CPU使用率过高" in issue or "内存使用率过高" in issue for issue in issues)
        if high_resource_usage and self._engine_manager is not None:
            try:
                # 降低引擎速度
                if hasattr(self._engine_manager, 'set_replay_speed'):
                    logger.info("尝试降低重放速度以减轻系统负载")
                    self._engine_manager.set_replay_speed(0.5)  # 降至半速
                    recovered_issues.append("已降低重放速度以减轻系统负载")
            except Exception as e:
                logger.error(f"降低重放速度失败: {str(e)}")
        
        # 如果引擎处于错误状态，尝试重启
        resources = details.get('resources', {})
        if (ResourceType.EVENT_QUEUE in resources and 
            resources[ResourceType.EVENT_QUEUE].get('engine_status') == EngineStatus.ERROR.name):
            
            try:
                if self._engine_manager is not None:
                    logger.info("尝试重启引擎")
                    self._engine_manager.stop()
                    time.sleep(1.0)
                    self._engine_manager.start()
                    recovered_issues.append("已重启引擎")
            except Exception as e:
                logger.error(f"重启引擎失败: {str(e)}")
        
        # 汇报恢复结果
        if recovered_issues:
            message = "自动恢复操作:\n" + "\n".join([f"- {issue}" for issue in recovered_issues])
            logger.info(message)
            
            # 触发恢复回调
            for callback in self._recovery_callbacks.values():
                try:
                    callback(recovered_issues, details)
                except Exception as e:
                    logger.error(f"执行恢复回调时出错: {str(e)}")
    
    def _notify_status_callbacks(self, status: HealthStatus, details: Dict[str, Any]):
        """
        通知状态回调
        
        Parameters
        ----------
        status : HealthStatus
            健康状态
        details : Dict[str, Any]
            详细信息
        """
        for callback in self._status_callbacks.values():
            try:
                callback(status, details)
            except Exception as e:
                logger.error(f"执行状态回调时出错: {str(e)}")
    
    def _notify_alert_callbacks(self, message: str, details: Dict[str, Any]):
        """
        通知警报回调
        
        Parameters
        ----------
        message : str
            警报消息
        details : Dict[str, Any]
            详细信息
        """
        logger.warning(f"健康警报: {message}")
        
        for callback in self._alert_callbacks.values():
            try:
                callback(message, details)
            except Exception as e:
                logger.error(f"执行警报回调时出错: {str(e)}")


if __name__ == "__main__":
    # 简单的使用示例
    monitor = EngineMonitor()
    
    # 注册状态回调
    def on_status_change(status, details):
        print(f"状态变更: {status.name}")
        if 'issues' in details and details['issues']:
            print("问题:")
            for issue in details['issues']:
                print(f"- {issue}")
    
    monitor.register_status_callback(on_status_change)
    
    # 注册警报回调
    def on_alert(message, details):
        print(f"警报: {message}")
    
    monitor.register_alert_callback(on_alert)
    
    # 启动监控
    monitor.start_monitoring()
    
    # 运行一段时间
    try:
        print("监控系统已启动，按Ctrl+C退出...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("正在停止监控...")
        monitor.stop_monitoring()
        print("监控已停止") 