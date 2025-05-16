#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试引擎管理器的事件处理功能

验证引擎管理器能否正确处理事件
"""

import os
import sys
import logging
from datetime import datetime
import time
import threading

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已添加项目路径: {project_root}")

# 使用直接导入，避免子模块导入问题
import qte
from qte.core.engine_manager import BaseEngineManager, EngineType, EngineStatus
from qte import Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent

def event_handler(event):
    """事件处理函数"""
    print(f"【事件处理器】收到事件: {event}")
    
def test_engine_manager_events():
    """测试引擎管理器的事件处理功能"""
    print("===== 测试引擎管理器事件处理 =====")
    
    # 创建引擎管理器
    manager = BaseEngineManager(engine_type=EngineType.EVENT_DRIVEN)
    print(f"已创建引擎管理器，类型: {manager._engine_type.name}")
    
    # 初始化引擎管理器
    success = manager.initialize()
    print(f"引擎管理器初始化: {'成功' if success else '失败'}")
    
    # 注册事件处理器
    for event_type in [EventType.MARKET.value, EventType.SIGNAL.value, EventType.ORDER.value, EventType.FILL.value]:
        handler_id = manager.register_event_handler(event_type, event_handler)
        print(f"已注册 {event_type} 事件处理器，ID: {handler_id}")
    
    # 启动引擎管理器
    success = manager.start()
    print(f"引擎管理器启动: {'成功' if success else '失败'}")
    print(f"当前状态: {manager.get_status().name}")
    
    # 等待事件处理线程启动
    time.sleep(2)
    
    # 创建并发送事件
    market_event = MarketEvent(
        symbol="SHSE.000001",
        timestamp=datetime.now(),
        open_price=3000.0,
        high_price=3050.0,
        low_price=2980.0,
        close_price=3020.0,
        volume=10000
    )
    print(f"准备发送市场事件: {market_event}")
    
    success = manager.send_event(market_event)
    print(f"市场事件发送: {'成功' if success else '失败'}")
    
    # 等待事件处理
    time.sleep(5)
    
    # 检查性能统计
    stats = manager.get_performance_stats()
    print(f"性能统计: {stats}")
    
    # 停止引擎管理器
    success = manager.stop()
    print(f"引擎管理器停止: {'成功' if success else '失败'}")
    print(f"当前状态: {manager.get_status().name}")
    
    # 最终性能统计
    stats = manager.get_performance_stats()
    print(f"最终性能统计: {stats}")
    
    print("===== 测试完成 =====")

if __name__ == "__main__":
    test_engine_manager_events() 