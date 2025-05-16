#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终验证脚本

用于验证数据重放控制器与引擎管理器的集成功能
"""
import sys
import os
import logging
import time
import threading
import pandas as pd
from datetime import datetime, timedelta
import random

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"已添加项目根目录到 Python 路径: {project_root}")

# 导入必要的模块
from qte.core.engine_manager import (
    ReplayEngineManager, 
    EngineType, 
    EngineStatus,
    EngineEvent,
    MarketDataEvent
)
from qte.data.data_replay import (
    ReplayMode,
    ReplayStatus,
    DataFrameReplayController,
    MultiSourceReplayController
)

def create_sample_data(rows=50):
    """创建样本数据"""
    # 创建时间索引
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=rows)
    date_range = pd.date_range(start=start_time, end=end_time, periods=rows)
    
    # 模拟价格数据
    prices = [100]
    for i in range(1, rows):
        # 生成一个随机变化率 (-1% 到 +1%)
        change_pct = random.uniform(-0.01, 0.01)
        new_price = prices[-1] * (1 + change_pct)
        prices.append(new_price)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'price': prices,
        'volume': [random.randint(1000, 10000) for _ in range(rows)],
        'symbol': 'TEST'
    }, index=date_range)
    
    df.index.name = 'timestamp'
    return df

class EventCounter:
    """线程安全的事件计数器"""
    def __init__(self):
        self.counts = {}
        self.lock = threading.Lock()
        self.last_event = None
        self.last_event_time = None
    
    def count(self, event_type, event=None):
        with self.lock:
            if event_type not in self.counts:
                self.counts[event_type] = 0
            self.counts[event_type] += 1
            if event:
                self.last_event = event
                self.last_event_time = datetime.now()
    
    def get_counts(self):
        with self.lock:
            return self.counts.copy()
    
    def get_last_event(self):
        with self.lock:
            return self.last_event, self.last_event_time

def handle_event(event, counter):
    """通用事件处理器"""
    counter.count(event.event_type, event)
    logger.info(f"收到事件: {event}, 类型: {event.event_type}")

def test_all_modes():
    """测试所有重放模式"""
    for mode in [ReplayMode.BACKTEST, ReplayMode.STEPPED, ReplayMode.ACCELERATED, ReplayMode.REALTIME]:
        logger.info(f"\n===== 测试模式: {mode.name} =====")
        
        # 速度因子
        speed_factor = 1.0
        if mode == ReplayMode.ACCELERATED:
            speed_factor = 5.0
        
        # 运行时间
        duration = 2.0
        if mode == ReplayMode.REALTIME:
            duration = 5.0
        elif mode == ReplayMode.STEPPED:
            duration = 0  # 步进模式不需要等待
        
        # 创建事件计数器
        counter = EventCounter()
        
        # 创建样本数据
        sample_data = create_sample_data(rows=50)
        
        # 创建数据重放控制器
        controller = DataFrameReplayController(
            dataframe=sample_data,
            timestamp_column=None,
            mode=mode,
            speed_factor=speed_factor
        )
        
        # 创建引擎管理器
        engine_manager = ReplayEngineManager(engine_type=EngineType.EVENT_DRIVEN)
        
        # 初始化引擎管理器
        engine_manager.initialize()
        
        # 添加重放控制器
        engine_manager.add_replay_controller(
            name="test_data",
            controller=controller,
            symbol="TEST"
        )
        
        # 注册事件处理器
        engine_manager.register_event_handler("*", lambda event: handle_event(event, counter))
        
        # 启动引擎
        engine_manager.start()
        
        start_time = time.time()
        
        try:
            if mode == ReplayMode.STEPPED:
                # 步进模式需要手动推进
                for _ in range(10):  # 只步进10次
                    controller.step()
                    time.sleep(0.1)
            else:
                # 其他模式等待指定时间
                time.sleep(duration)
        finally:
            # 停止引擎
            engine_manager.stop()
            
            # 打印统计信息
            elapsed = time.time() - start_time
            counts = counter.get_counts()
            logger.info(f"模式 {mode.name} 测试完成，用时: {elapsed:.2f}秒")
            logger.info(f"事件计数: {counts}")
            
            last_event, last_time = counter.get_last_event()
            if last_event:
                logger.info(f"最后一个事件: {last_event}, 接收时间: {last_time}")
            
            # 输出引擎统计
            stats = engine_manager.get_performance_stats()
            logger.info(f"引擎性能: {stats}")
            
            # 如果是回测模式，应该处理所有数据
            if mode == ReplayMode.BACKTEST:
                assert "MARKET_DATA" in counts, "未收到市场数据事件"
                # 可能有些事件在统计前未处理完，所以不做精确比对
                logger.info(f"回测模式接收到 {counts.get('MARKET_DATA', 0)} 个事件，数据集大小: {len(sample_data)}")

def main():
    """主函数"""
    logger.info("开始验证数据重放控制器与引擎管理器的集成...")
    
    # 导入测试
    test_imports()
    
    # 测试所有模式
    test_all_modes()
    
    logger.info("验证完成")

def test_imports():
    """测试导入"""
    try:
        from qte import BaseEngineManager, ReplayEngineManager, EngineType
        logger.info("导入 BaseEngineManager, ReplayEngineManager, EngineType 成功")
        
        # 测试各个方法
        engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        assert isinstance(engine, ReplayEngineManager)
        assert isinstance(engine, BaseEngineManager)
        logger.info("创建 ReplayEngineManager 实例成功")
        
        return True
    except ImportError as e:
        logger.error(f"导入错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"其他错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()