#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复重放引擎管理器的线程阻塞问题
"""
import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入引擎管理器
from qte.core.engine_manager import ReplayEngineManager

def fix_lambda_capture_issue():
    """
    修复lambda表达式捕获变量问题
    
    在ReplayEngineManager的start方法中，为重放控制器注册回调时，
    使用lambda表达式没有正确捕获循环变量，导致所有控制器都使用了最后一个循环变量。
    """
    logger.info("修复 lambda 表达式捕获问题...")
    
    # 获取原始方法
    original_start = ReplayEngineManager.start
    
    # 修改后的方法
    def fixed_start(self) -> bool:
        """
        启动引擎和所有重放控制器
        
        Returns
        -------
        bool
            启动是否成功
        """
        with self._lock:
            # 先启动引擎
            if not super(ReplayEngineManager, self).start():
                return False
            
            # 为所有控制器注册回调
            for name, controller in self._replay_controllers.items():
                # 修复: 使用嵌套函数正确捕获循环变量
                def create_callback(source_name):
                    return lambda data: self._on_replay_data(source_name, data)
                
                callback = create_callback(name)
                callback_id = controller.register_callback(callback)
                self._replay_callbacks[controller] = callback_id
            
            # 启动所有控制器
            for name, controller in self._replay_controllers.items():
                controller.start()
                logger.info(f"已启动重放控制器: {name}")
            
            return True
    
    # 替换方法
    ReplayEngineManager.start = fixed_start
    logger.info("已修复 lambda 表达式捕获问题")
    return original_start

def fix_thread_wait_issue():
    """
    修复线程等待问题
    
    在BaseDataReplayController的_replay_task方法中，使用event.wait()方法时没有设置超时时间，
    如果引擎管理器没有正确地设置事件，线程可能会无限等待。
    """
    logger.info("修复线程等待问题...")
    
    # 导入数据重放控制器
    from qte.data.data_replay import BaseDataReplayController, ReplayStatus
    
    # 获取原始方法
    original_replay_task = BaseDataReplayController._replay_task
    
    # 修改后的方法
    def fixed_replay_task(self):
        """重放线程的主任务函数"""
        try:
            while self._status == ReplayStatus.RUNNING:
                # 修复: 添加超时参数，防止无限等待
                event_set = self._event.wait(timeout=0.5)
                
                # 检查是否由于超时返回
                if not event_set and self._status == ReplayStatus.RUNNING:
                    continue
                
                # 如果状态变更，则退出
                if self._status != ReplayStatus.RUNNING:
                    break
                
                # 获取下一个数据点
                data_point = self._get_next_data_point()
                if data_point is None:
                    with self._lock:
                        self._status = ReplayStatus.COMPLETED
                    logger.info("重放已完成所有数据")
                    break
                
                # 根据模式和速度控制重放节奏
                self._control_replay_pace(data_point)
                
                # 触发回调
                self._notify_callbacks(data_point)
                
        except Exception as e:
            logger.error(f"重放过程中发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            with self._lock:
                self._status = ReplayStatus.STOPPED
    
    # 替换方法
    BaseDataReplayController._replay_task = fixed_replay_task
    logger.info("已修复线程等待问题")
    return original_replay_task

def fix_exception_handling():
    """
    改进异常处理
    
    增强异常处理，添加详细的堆栈跟踪，便于定位问题
    """
    logger.info("改进异常处理...")
    
    # 导入引擎管理器和数据重放控制器
    from qte.core.engine_manager import ReplayEngineManager
    from qte.data.data_replay import BaseDataReplayController
    
    # 获取原始方法
    original_on_replay_data = ReplayEngineManager._on_replay_data
    
    # 修改后的方法
    def fixed_on_replay_data(self, source, data):
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
            # 原方法的实现
            original_on_replay_data(self, source, data)
        except Exception as e:
            logger.error(f"处理重放数据异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # 替换方法
    ReplayEngineManager._on_replay_data = fixed_on_replay_data
    logger.info("已改进异常处理")
    return original_on_replay_data

def add_debug_logging():
    """
    添加调试日志
    
    在关键方法中添加更详细的日志，帮助跟踪执行流程
    """
    logger.info("添加调试日志...")
    
    # 导入相关类
    from qte.core.engine_manager import ReplayEngineManager
    from qte.data.data_replay import BaseDataReplayController
    
    # 存储原始方法
    originals = {}
    
    # ----- 增强引擎管理器的日志 -----
    # start方法
    originals['engine_start'] = ReplayEngineManager.start
    def enhanced_engine_start(self) -> bool:
        logger.debug("引擎管理器启动开始...")
        result = originals['engine_start'](self)
        logger.debug(f"引擎管理器启动{'成功' if result else '失败'}")
        return result
    ReplayEngineManager.start = enhanced_engine_start
    
    # _on_replay_data方法
    originals['on_replay_data'] = ReplayEngineManager._on_replay_data
    def enhanced_on_replay_data(self, source, data):
        logger.debug(f"接收来自 '{source}' 的重放数据")
        originals['on_replay_data'](self, source, data)
        logger.debug(f"完成处理 '{source}' 的重放数据")
    ReplayEngineManager._on_replay_data = enhanced_on_replay_data
    
    # ----- 增强重放控制器的日志 -----
    # _replay_task方法
    originals['replay_task'] = BaseDataReplayController._replay_task
    def enhanced_replay_task(self):
        logger.debug("重放任务开始...")
        originals['replay_task'](self)
        logger.debug("重放任务结束")
    BaseDataReplayController._replay_task = enhanced_replay_task
    
    # _notify_callbacks方法
    originals['notify_callbacks'] = BaseDataReplayController._notify_callbacks
    def enhanced_notify_callbacks(self, data_point):
        logger.debug(f"开始通知回调: {len(self._callbacks)} 个回调")
        originals['notify_callbacks'](self, data_point)
        logger.debug("完成通知回调")
    BaseDataReplayController._notify_callbacks = enhanced_notify_callbacks
    
    logger.info("已添加调试日志")
    return originals

def apply_all_fixes():
    """应用所有修复"""
    logger.info("开始应用所有修复...")
    
    # 存储原始方法以便恢复
    original_methods = {}
    
    try:
        # 修复lambda捕获问题
        original_methods['lambda_fix'] = fix_lambda_capture_issue()
        
        # 修复线程等待问题
        original_methods['thread_wait_fix'] = fix_thread_wait_issue()
        
        # 改进异常处理
        original_methods['exception_fix'] = fix_exception_handling()
        
        # 添加调试日志
        original_methods['logging_fix'] = add_debug_logging()
        
        logger.info("已成功应用所有修复")
        return original_methods
    
    except Exception as e:
        logger.error(f"应用修复时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 恢复已应用的修复
        restore_fixes(original_methods)
        return None

def restore_fixes(original_methods):
    """恢复原始方法"""
    logger.info("恢复原始方法...")
    
    if 'lambda_fix' in original_methods:
        from qte.core.engine_manager import ReplayEngineManager
        ReplayEngineManager.start = original_methods['lambda_fix']
    
    if 'thread_wait_fix' in original_methods:
        from qte.data.data_replay import BaseDataReplayController
        BaseDataReplayController._replay_task = original_methods['thread_wait_fix']
    
    if 'exception_fix' in original_methods:
        from qte.core.engine_manager import ReplayEngineManager
        ReplayEngineManager._on_replay_data = original_methods['exception_fix']
    
    if 'logging_fix' in original_methods and isinstance(original_methods['logging_fix'], dict):
        from qte.core.engine_manager import ReplayEngineManager
        from qte.data.data_replay import BaseDataReplayController
        
        if 'engine_start' in original_methods['logging_fix']:
            ReplayEngineManager.start = original_methods['logging_fix']['engine_start']
        
        if 'on_replay_data' in original_methods['logging_fix']:
            ReplayEngineManager._on_replay_data = original_methods['logging_fix']['on_replay_data']
        
        if 'replay_task' in original_methods['logging_fix']:
            BaseDataReplayController._replay_task = original_methods['logging_fix']['replay_task']
        
        if 'notify_callbacks' in original_methods['logging_fix']:
            BaseDataReplayController._notify_callbacks = original_methods['logging_fix']['notify_callbacks']
    
    logger.info("已恢复原始方法")

if __name__ == "__main__":
    logger.info("开始修复数据重放与引擎管理器集成问题...")
    
    # 应用所有修复
    original_methods = apply_all_fixes()
    
    if original_methods:
        logger.info("所有修复已成功应用，可以进行测试")
        
        # 这里可以添加测试代码
        
        # 恢复原始方法
        # restore_fixes(original_methods)
    else:
        logger.error("修复应用失败") 