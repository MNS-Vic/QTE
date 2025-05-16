#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据重放控制器与引擎管理器的集成
"""
import unittest
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys

# 配置更详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("replay_test_debug.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TestReplay")

from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus, EngineEvent
from qte.data.data_replay import DataFrameReplayController, ReplayMode, ReplayStatus

class TestReplayEngineIntegration(unittest.TestCase):
    """测试数据重放控制器与引擎管理器的集成"""
    
    def setUp(self):
        """测试前准备工作 - 只使用1行数据"""
        # 创建测试数据 - 只有1行
        dates = pd.date_range(start=datetime.now(), periods=1, freq='1min')
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': [100.0],
            'high': [105.0],
            'low': [95.0],
            'close': [102.0],
            'volume': [1000]
        })
        
        # 创建引擎管理器
        self.engine_manager = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        self.engine_manager.initialize()
        
        # 创建数据重放控制器
        self.replay_controller = DataFrameReplayController(
            dataframe=self.test_data,
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST
        )
        
        # 接收到的事件计数
        self.received_events = 0
        self.events_lock = threading.Lock()
        
    def test_basic_integration(self):
        """测试基本集成功能 - 极简版本"""
        print("\n====== 开始极简版本测试 ======")
        logger.info("\n====== 开始极简版本测试 ======")
        
        # 修改为极简测试数据 - 只用1行
        dates = pd.date_range(start=datetime.now(), periods=1, freq='1min')
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [1000]
        })
        print(f"测试数据: {len(self.test_data)}行")
        logger.info(f"测试数据: {len(self.test_data)}行")
        
        # 重新创建控制器
        self.replay_controller = DataFrameReplayController(
            dataframe=self.test_data,
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST
        )
        
        # 注册事件处理器
        print("1. 注册事件处理器...")
        logger.info("1. 注册事件处理器...")
        handler_id = self.engine_manager.register_event_handler(
            "MARKET", 
            self._on_market_data
        )
        logger.info(f"   事件处理器注册完成，ID: {handler_id}")
        
        # 添加重放控制器
        print("2. 添加重放控制器...")
        logger.info("2. 添加重放控制器...")
        add_result = self.engine_manager.add_replay_controller(
            "test_data", 
            self.replay_controller,
            symbol="TEST"
        )
        logger.info(f"   重放控制器添加结果: {add_result}")
        
        # 启动引擎
        print("3. 启动引擎...")
        logger.info("3. 启动引擎...")
        # 记录启动前状态
        if hasattr(self.engine_manager, '_event_processing_thread'):
            thread = self.engine_manager._event_processing_thread
            thread_status = f"存在={thread.is_alive() if thread else False}, ID={thread.ident if thread else 'N/A'}"
            logger.info(f"   启动前事件线程状态: {thread_status}")
        
        # 实际启动
        start_time = time.time()
        start_result = self.engine_manager.start()
        start_elapsed = time.time() - start_time
        logger.info(f"   引擎启动结果: {start_result}, 耗时: {start_elapsed:.4f}秒")
        
        # 检查启动后状态
        logger.info(f"4. 检查状态 - 引擎: {self.engine_manager.get_status().name}, 控制器: {self.replay_controller.get_status().name}")
        print(f"4. 检查状态 - 引擎: {self.engine_manager.get_status().name}, 控制器: {self.replay_controller.get_status().name}")
        
        if hasattr(self.engine_manager, '_event_processing_thread'):
            thread = self.engine_manager._event_processing_thread
            if thread:
                thread_status = f"存在={thread.is_alive()}, ID={thread.ident}, 名称={thread.name}"
                print(f"5. 事件线程: {thread_status}")
                logger.info(f"5. 事件线程: {thread_status}")
            else:
                print("5. 事件线程: 不存在")
                logger.info("5. 事件线程: 不存在")
        
        # 输出所有线程
        logger.info("当前活跃线程:")
        for thread in threading.enumerate():
            logger.info(f"  - {thread.name} (ID: {thread.ident})")
        
        # 等待处理（更详细）
        print("6. 等待处理...")
        logger.info("6. 等待处理...")
        
        max_wait = 15  # 最多等待15秒
        check_interval = 0.5  # 每0.5秒检查一次
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            with self.events_lock:
                current_received = self.received_events
            
            print(f"   等待中... 时间={wait_time:.1f}秒, 已接收: {current_received}/{len(self.test_data)} 个事件")
            logger.info(f"   等待中... 时间={wait_time:.1f}秒, 已接收: {current_received}/{len(self.test_data)} 个事件")
            logger.info(f"   引擎状态: {self.engine_manager.get_status().name}, 控制器状态: {self.replay_controller.get_status().name}")
            
            # 获取性能统计
            stats = self.engine_manager.get_performance_stats()
            logger.info(f"   引擎统计: 已处理事件={stats.get('processed_events', 0)}, 状态={stats.get('current_status', 'Unknown')}")
            
            # 如果收到所有事件，提前退出
            if current_received >= len(self.test_data):
                print(f"   已收到所有事件，提前结束等待，用时: {wait_time:.1f}秒")
                logger.info(f"   已收到所有事件，提前结束等待，用时: {wait_time:.1f}秒")
                break
        
        # 输出事件处理线程最终状态
        if hasattr(self.engine_manager, '_event_processing_thread'):
            thread = self.engine_manager._event_processing_thread
            if thread:
                logger.info(f"   事件处理线程状态: 存在={thread.is_alive()}, ID={thread.ident}")
            else:
                logger.info("   事件处理线程不存在")
                
        # 停止引擎
        print("7. 停止引擎...")
        logger.info("7. 停止引擎...")
        stop_result = self.engine_manager.stop()
        logger.info(f"   引擎停止结果: {stop_result}")
        
        # 结果验证
        with self.events_lock:
            final_count = self.received_events
        
        print(f"8. 最终结果: {final_count}/{len(self.test_data)} 个事件")
        logger.info(f"8. 最终结果: {final_count}/{len(self.test_data)} 个事件")
        
        self.assertEqual(final_count, len(self.test_data), 
                         f"接收: {final_count}, 预期: {len(self.test_data)}")
        
        print("====== 测试完成 ======")
        logger.info("====== 测试完成 ======")
    
    def test_callback_with_lambda(self):
        """测试使用lambda回调的正确性"""
        print("\n====== 开始Lambda回调测试 ======")
        
        # 使用列表存储接收到的数据
        received_data = []
        
        # 直接向数据重放控制器注册回调
        print("注册Lambda回调...")
        callback_id = self.replay_controller.register_callback(
            lambda data: received_data.append(data)
        )
        print(f"回调ID: {callback_id}")
        
        # 启动重放控制器
        print("启动重放控制器...")
        result = self.replay_controller.start()
        print(f"启动控制器结果: {result}")
        print(f"控制器状态: {self.replay_controller.get_status().name}")
        
        # 等待重放完成
        max_wait = 10  # 最多等待10秒
        wait_time = 0
        check_interval = 0.5
        
        print("等待数据处理...")
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            print(f"等待中... 已接收数据: {len(received_data)}/{len(self.test_data)}")
            print(f"控制器状态: {self.replay_controller.get_status().name}")
            
            if self.replay_controller.get_status() == ReplayStatus.COMPLETED:
                print("控制器已完成，退出等待")
                break
        
        # 停止重放
        print("停止重放控制器...")
        self.replay_controller.stop()
        print(f"停止后控制器状态: {self.replay_controller.get_status().name}")
        
        # 输出接收到的部分数据
        if received_data:
            print(f"接收到的第一个数据点: {received_data[0]}")
            if len(received_data) > 1:
                print(f"接收到的最后一个数据点: {received_data[-1]}")
        
        # 验证是否接收到所有数据
        print(f"最终结果: 接收 {len(received_data)} 个数据点，预期 {len(self.test_data)} 个")
        self.assertEqual(len(received_data), len(self.test_data), 
                          f"接收到 {len(received_data)} 个数据点，预期 {len(self.test_data)} 个")
        
        print("====== 测试完成 ======")
    
    def test_multiple_controllers(self):
        """测试多数据源集成"""
        # 创建第二个测试数据集
        dates2 = pd.date_range(start=datetime.now(), periods=5, freq='2min')
        test_data2 = pd.DataFrame({
            'timestamp': dates2,
            'price': np.random.rand(5) * 200,
            'quantity': np.random.randint(100, 500, 5)
        })
        
        # 创建第二个重放控制器
        replay_controller2 = DataFrameReplayController(
            dataframe=test_data2,
            timestamp_column='timestamp',
            mode=ReplayMode.BACKTEST
        )
        
        # 添加两个重放控制器
        self.engine_manager.add_replay_controller("data1", self.replay_controller, symbol="SYM1")
        self.engine_manager.add_replay_controller("data2", replay_controller2, symbol="SYM2")
        
        # 接收到的数据计数
        received_count = {"data1": 0, "data2": 0}
        
        # 注册事件处理器
        def event_handler(event):
            if event.source == "data1":
                received_count["data1"] += 1
            elif event.source == "data2":
                received_count["data2"] += 1
        
        self.engine_manager.register_event_handler("MARKET_DATA", event_handler)
        
        # 启动引擎
        self.engine_manager.start()
        
        # 等待数据处理完成
        time.sleep(3)
        
        # 停止引擎
        self.engine_manager.stop()
        
        # 验证是否接收到所有事件
        self.assertEqual(received_count["data1"], len(self.test_data), 
                          f"数据源1: 接收到 {received_count['data1']} 个事件，预期 {len(self.test_data)} 个")
        self.assertEqual(received_count["data2"], len(test_data2), 
                          f"数据源2: 接收到 {received_count['data2']} 个事件，预期 {len(test_data2)} 个")
    
    def _on_market_data(self, event):
        """市场数据事件处理函数 - 增强版"""
        with self.events_lock:
            self.received_events += 1
            event_count = self.received_events
            
        # 获取事件属性
        event_type = getattr(event, 'event_type', 'Unknown')
        event_symbol = getattr(event, 'symbol', 'N/A')
        
        print(f"√ 收到事件 #{event_count}: {event_type}, 标的={event_symbol}")
        logger.info(f"√ 收到事件 #{event_count}: 类型={event_type}, 标的={event_symbol}, 详情={event}")
        
        # 输出事件详细属性
        logger.debug(f"  事件详情: 字段={dir(event)}")

if __name__ == "__main__":
    unittest.main()