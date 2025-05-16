#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试脚本 - 检查数据重放控制器与引擎管理器的集成问题
"""
import sys
import os
import pandas as pd
import numpy as np
import threading
import time
import logging
from datetime import datetime, timedelta
import traceback

# 设置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入必要的模块
from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus
from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus

def create_test_data(rows=10):
    """创建测试数据"""
    dates = pd.date_range(start=datetime.now(), periods=rows, freq='1min')
    return pd.DataFrame({
        'timestamp': dates,
        'price': np.random.rand(rows) * 100,
        'volume': np.random.randint(1000, 10000, rows)
    })

def debug_callback_issue():
    """调试回调函数问题"""
    logger.info("开始调试回调函数问题...")
    
    # 创建测试数据
    test_data = create_test_data()
    
    # 创建重放控制器
    replay_controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 记录接收到的数据
    received_data = []
    callback_called = threading.Event()
    
    # 定义回调函数
    def data_callback(data):
        logger.debug(f"回调函数被调用: {data}")
        received_data.append(data)
        callback_called.set()
    
    # 注册回调
    callback_id = replay_controller.register_callback(data_callback)
    logger.debug(f"已注册回调，ID: {callback_id}")
    
    # 启动重放
    logger.info("启动重放...")
    replay_controller.start()
    
    # 等待回调被调用
    if not callback_called.wait(timeout=3.0):
        logger.error("超时: 回调函数未被调用")
    else:
        logger.info(f"回调函数被调用了 {len(received_data)} 次")
    
    # 停止重放
    replay_controller.stop()
    
    # 检查是否正确接收到数据
    expected_count = len(test_data)
    actual_count = len(received_data)
    
    logger.info(f"预期接收 {expected_count} 条数据，实际接收 {actual_count} 条数据")
    
    if expected_count != actual_count:
        logger.error("回调问题: 数据接收不完整")
    else:
        logger.info("回调函数工作正常")

def debug_lambda_capture():
    """调试lambda表达式捕获问题"""
    logger.info("开始调试lambda表达式捕获问题...")
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine_manager.initialize()
    
    # 创建多个数据源
    sources = {}
    controllers = {}
    received = {}
    
    # 创建3个不同的数据源
    for i in range(3):
        source_name = f"source_{i}"
        sources[source_name] = create_test_data(rows=5)
        controllers[source_name] = DataFrameReplayController(
            dataframe=sources[source_name],
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST
        )
        received[source_name] = 0
    
    # 监控添加的回调函数
    callbacks = {}
    
    # 添加重放控制器
    for name, controller in controllers.items():
        # 直接使用lambda存在的问题版本
        # lambda_callback = lambda data: on_data(name, data)
        
        # 正确的捕获方式
        def create_callback(source_name):
            return lambda data: on_data(source_name, data)
        
        lambda_callback = create_callback(name)
        callbacks[name] = lambda_callback
        
        engine_manager.add_replay_controller(name, controller)
    
    # 数据处理函数
    def on_data(source, data):
        logger.debug(f"接收到来自 {source} 的数据: {data}")
        received[source] += 1
    
    # 注册事件处理器
    def event_handler(event):
        logger.debug(f"接收到事件: {event}")
        source = event.source
        if source in received:
            received[source] += 1
    
    engine_manager.register_event_handler("MARKET_DATA", event_handler)
    
    # 启动引擎
    logger.info("启动引擎...")
    engine_manager.start()
    
    # 等待处理完成
    time.sleep(3)
    
    # 停止引擎
    engine_manager.stop()
    
    # 检查每个源接收到的数据数量
    for name, count in received.items():
        expected = len(sources[name])
        logger.info(f"数据源 {name}: 预期 {expected} 个数据点, 接收到 {count} 个")
        if count != expected:
            logger.error(f"源 {name} 的数据接收不正确")

def debug_threading_issue():
    """调试线程问题"""
    logger.info("开始调试线程问题...")
    
    # 创建测试数据
    test_data = create_test_data(rows=3)
    
    # 创建重放控制器，使用步进模式更容易调试
    replay_controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column='timestamp',
        mode=ReplayMode.STEPPED
    )
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine_manager.initialize()
    
    # 添加重放控制器
    engine_manager.add_replay_controller("test", replay_controller)
    
    # 跟踪事件处理过程
    event_processed = threading.Event()
    
    # 事件处理器
    def event_handler(event):
        logger.debug(f"处理事件: {event}")
        event_processed.set()
        # 模拟处理延迟
        time.sleep(0.1)
    
    engine_manager.register_event_handler("MARKET_DATA", event_handler)
    
    # 启动引擎
    logger.info("启动引擎...")
    engine_manager.start()
    
    # 逐步测试
    for i in range(len(test_data)):
        logger.info(f"步进 {i+1}/{len(test_data)}...")
        event_processed.clear()
        replay_controller.step()
        
        # 等待事件处理
        if not event_processed.wait(timeout=2.0):
            logger.error(f"超时: 事件 {i+1} 未被处理")
            break
    
    # 停止引擎
    engine_manager.stop()
    logger.info("线程调试完成")

def debug_event_propagation():
    """调试事件传播问题"""
    logger.info("开始调试事件传播问题...")
    
    # 创建测试数据
    test_data = create_test_data()
    
    # 创建重放控制器
    replay_controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 创建引擎管理器，启用详细日志
    engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine_manager.initialize()
    
    # 添加重放控制器
    engine_manager.add_replay_controller("test", replay_controller)
    
    # 记录事件传播路径
    propagation_log = []
    
    # 直接向控制器注册回调，确认控制器正在产生数据
    replay_controller.register_callback(
        lambda data: propagation_log.append(f"Controller callback: {data}")
    )
    
    # 向引擎注册事件处理器
    engine_manager.register_event_handler(
        "MARKET_DATA", 
        lambda event: propagation_log.append(f"Engine event handler: {event}")
    )
    
    # 启动引擎
    logger.info("启动引擎...")
    engine_manager.start()
    
    # 等待处理
    time.sleep(2)
    
    # 停止引擎
    engine_manager.stop()
    
    # 检查传播日志
    controller_callbacks = sum(1 for entry in propagation_log if entry.startswith("Controller"))
    engine_handlers = sum(1 for entry in propagation_log if entry.startswith("Engine"))
    
    logger.info(f"控制器回调次数: {controller_callbacks}, 引擎处理器次数: {engine_handlers}")
    
    if controller_callbacks != len(test_data):
        logger.error(f"控制器回调次数 ({controller_callbacks}) 与预期 ({len(test_data)}) 不符")
    
    if engine_handlers != len(test_data):
        logger.error(f"引擎事件处理次数 ({engine_handlers}) 与预期 ({len(test_data)}) 不符")
    
    # 如果控制器回调正常但引擎处理器调用异常，则表明问题在事件传播路径上
    if controller_callbacks == len(test_data) and engine_handlers != len(test_data):
        logger.error("事件传播路径有问题：控制器产生数据但引擎未收到事件")

def inspect_engine_manager():
    """检查引擎管理器实现细节"""
    from qte.core.engine_manager import ReplayEngineManager
    
    # 获取源代码
    import inspect
    source = inspect.getsource(ReplayEngineManager.start)
    
    logger.info("ReplayEngineManager.start 方法源代码:")
    logger.info(source)
    
    # 分析回调注册代码
    logger.info("分析回调注册代码...")
    callback_line = None
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if "lambda data" in line and "_on_replay_data" in line:
            callback_line = line
            logger.info(f"发现回调注册代码: {line.strip()}")
            # 检查前后几行代码
            for j in range(max(0, i-2), min(len(lines), i+3)):
                if j != i:
                    logger.info(f"相关代码 {j-i:+d}: {lines[j].strip()}")
    
    if callback_line:
        logger.warning("潜在问题: lambda表达式可能没有正确捕获循环变量")
        logger.info("建议修改为: callback_id = controller.register_callback(lambda data, src=name: self._on_replay_data(src, data))")
    else:
        logger.info("未发现回调注册代码，请手动检查")

def check_event_thread_wait():
    """检查事件线程等待机制"""
    logger.info("检查事件处理线程等待机制...")
    
    # 创建测试数据
    test_data = create_test_data(rows=3)
    
    # 创建重放控制器
    replay_controller = DataFrameReplayController(
        dataframe=test_data,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    
    # 修改重放控制器的_replay_task方法，添加日志
    original_replay_task = replay_controller._replay_task
    
    def instrumented_replay_task(self):
        logger.debug("重放任务开始")
        try:
            while self._status == ReplayStatus.RUNNING:
                logger.debug("等待事件...")
                self._event.wait()
                logger.debug("事件被设置")
                
                # 剩余代码与原函数相同
                if self._status != ReplayStatus.RUNNING:
                    logger.debug("状态已更改，退出循环")
                    break
                
                data_point = self._get_next_data_point()
                logger.debug(f"获取数据点: {data_point}")
                
                if data_point is None:
                    logger.debug("没有更多数据，完成重放")
                    with self._lock:
                        self._status = ReplayStatus.COMPLETED
                    break
                
                self._control_replay_pace(data_point)
                logger.debug("控制重放节奏完成")
                
                self._notify_callbacks(data_point)
                logger.debug("通知回调完成")
                
        except Exception as e:
            logger.error(f"重放过程中发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            with self._lock:
                self._status = ReplayStatus.STOPPED
    
    # 替换方法
    replay_controller._replay_task = lambda: instrumented_replay_task(replay_controller)
    
    # 创建引擎管理器
    engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine_manager.initialize()
    
    # 添加重放控制器
    engine_manager.add_replay_controller("test", replay_controller)
    
    # 启动引擎
    logger.info("启动引擎...")
    engine_manager.start()
    
    # 等待处理
    time.sleep(2)
    
    # 停止引擎
    engine_manager.stop()
    
    # 恢复原方法
    replay_controller._replay_task = original_replay_task
    logger.info("事件线程等待机制检查完成")

if __name__ == "__main__":
    logger.info("开始调试数据重放与引擎管理器集成问题...")
    
    # 检查引擎管理器实现
    inspect_engine_manager()
    
    # 依次运行各项调试
    debug_callback_issue()
    debug_lambda_capture()
    debug_threading_issue()
    debug_event_propagation()
    check_event_thread_wait()
    
    logger.info("调试完成") 