#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件系统核心功能测试

提供一个简单的示例，展示如何使用QTE的事件处理系统
"""

import os
import sys
import logging
from datetime import datetime
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"已添加项目路径: {project_root}")

# 导入需要的组件
from qte import (
    BaseEngineManager, EngineType, EngineStatus,
    Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
)

# 全局计数器，用于统计接收到的事件
event_counters = {
    "MARKET": 0,
    "SIGNAL": 0,
    "ORDER": 0,
    "FILL": 0
}

def market_handler(event):
    """市场事件处理函数"""
    event_counters["MARKET"] += 1
    logger.info(f"市场事件处理器接收到事件 #{event_counters['MARKET']}: {event}")
    
    # 根据市场数据生成交易信号
    if event.close_price > 3000.0:
        signal = SignalEvent(
            symbol=event.symbol,
            timestamp=datetime.now(),
            signal_type="LONG",
            direction=1,
            strength=1.0
        )
        logger.info(f"生成做多信号: {signal}")
        # 在真实应用中，我们会将这个信号发送到引擎
        return signal
    return None

def signal_handler(event):
    """信号事件处理函数"""
    event_counters["SIGNAL"] += 1
    logger.info(f"信号事件处理器接收到事件 #{event_counters['SIGNAL']}: {event}")
    
    # 根据信号生成订单
    order = OrderEvent(
        symbol=event.symbol,
        timestamp=datetime.now(),
        order_type="MARKET",
        quantity=100.0,
        direction=event.direction
    )
    logger.info(f"生成市场订单: {order}")
    # 在真实应用中，我们会将这个订单发送到引擎
    return order

def order_handler(event):
    """订单事件处理函数"""
    event_counters["ORDER"] += 1
    logger.info(f"订单事件处理器接收到事件 #{event_counters['ORDER']}: {event}")
    
    # 模拟订单执行
    fill = FillEvent(
        symbol=event.symbol,
        timestamp=datetime.now(),
        quantity=event.quantity,
        direction=event.direction,
        fill_price=3020.0,
        commission=event.quantity * 3020.0 * 0.0003
    )
    logger.info(f"生成成交事件: {fill}")
    # 在真实应用中，我们会将这个成交事件发送到引擎
    return fill

def fill_handler(event):
    """成交事件处理函数"""
    event_counters["FILL"] += 1
    logger.info(f"成交事件处理器接收到事件 #{event_counters['FILL']}: {event}")
    logger.info(f"交易完成: 方向={'多头' if event.direction > 0 else '空头'}, "
               f"数量={event.quantity}, 价格={event.fill_price:.2f}, "
               f"手续费={event.commission:.2f}")

def test_event_handlers():
    """测试事件处理器链"""
    logger.info("===== 测试事件处理器链 =====")
    
    # 创建一个市场事件
    market_event = MarketEvent(
        symbol="SHSE.000001",
        timestamp=datetime.now(),
        open_price=3000.0,
        high_price=3050.0,
        low_price=2980.0,
        close_price=3020.0,
        volume=10000
    )
    logger.info(f"创建市场事件: {market_event}")
    
    # 手动调用事件处理链
    signal_event = market_handler(market_event)
    if signal_event:
        order_event = signal_handler(signal_event)
        if order_event:
            fill_event = order_handler(order_event)
            if fill_event:
                fill_handler(fill_event)
    
    logger.info(f"事件处理计数: {event_counters}")
    logger.info("===== 测试完成 =====")

def test_engine_manager():
    """测试引擎管理器的事件处理"""
    logger.info("===== 测试引擎管理器事件处理 =====")
    
    # 重置计数器
    for key in event_counters:
        event_counters[key] = 0
    
    # 创建引擎管理器
    manager = BaseEngineManager(engine_type=EngineType.EVENT_DRIVEN)
    logger.info(f"创建引擎管理器: {manager.__class__.__name__}")
    
    # 初始化引擎管理器
    success = manager.initialize()
    logger.info(f"引擎管理器初始化: {'成功' if success else '失败'}")
    
    # 注册事件处理器
    manager.register_event_handler(EventType.MARKET.value, market_handler)
    manager.register_event_handler(EventType.SIGNAL.value, signal_handler)
    manager.register_event_handler(EventType.ORDER.value, order_handler)
    manager.register_event_handler(EventType.FILL.value, fill_handler)
    logger.info("已注册所有事件处理器")
    
    # 启动引擎管理器
    success = manager.start()
    logger.info(f"引擎管理器启动: {'成功' if success else '失败'}")
    
    # 给事件处理线程一点时间启动
    time.sleep(1)
    
    # 创建一系列市场事件
    for i in range(3):
        market_event = MarketEvent(
            symbol=f"SHSE.00000{i+1}",
            timestamp=datetime.now(),
            open_price=3000.0 + i * 10,
            high_price=3050.0 + i * 10,
            low_price=2980.0 + i * 10,
            close_price=3020.0 + i * 10,
            volume=10000 + i * 1000
        )
        logger.info(f"发送市场事件 #{i+1}: {market_event}")
        manager.send_event(market_event)
        time.sleep(0.1)  # 给事件处理一点时间
    
    # 给事件处理一些时间
    time.sleep(3)
    
    # 检查性能统计
    stats = manager.get_performance_stats()
    logger.info(f"性能统计: {stats}")
    
    # 停止引擎管理器
    success = manager.stop()
    logger.info(f"引擎管理器停止: {'成功' if success else '失败'}")
    
    logger.info(f"事件处理计数: {event_counters}")
    logger.info("===== 测试完成 =====")

if __name__ == "__main__":
    test_event_handlers()
    test_engine_manager() 