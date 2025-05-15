#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试事件循环和事件处理

验证事件驱动架构的基本功能
"""

import os
import sys
import logging
from datetime import datetime
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入核心组件
from qte_core.event_loop import EventLoop
from qte_core.events import MarketEvent, SignalEvent, OrderEvent, FillEvent

def test_event_loop_basics():
    """测试事件循环的基本功能"""
    logger.info("测试事件循环基本功能")
    
    # 创建事件循环
    event_loop = EventLoop()
    logger.info("已创建事件循环")
    
    # 创建事件
    market_event = MarketEvent(
        symbol="SHSE.000001",
        timestamp=datetime.now(),
        open_price=3000.0,
        high_price=3050.0,
        low_price=2980.0,
        close_price=3020.0,
        volume=10000
    )
    
    signal_event = SignalEvent(
        symbol="SHSE.000001",
        timestamp=datetime.now(),
        signal_type="LONG",
        direction=1,
        strength=1.0
    )
    
    # 定义处理函数
    events_received = []
    
    def market_handler(event):
        logger.info(f"收到市场事件: {event}")
        events_received.append(("MARKET", event))
    
    def signal_handler(event):
        logger.info(f"收到信号事件: {event}")
        events_received.append(("SIGNAL", event))
    
    # 注册处理函数
    event_loop.register_handler("MARKET", market_handler)
    event_loop.register_handler("SIGNAL", signal_handler)
    
    # 添加事件
    event_loop.put_event(market_event)
    event_loop.put_event(signal_event)
    
    # 运行事件循环
    processed = event_loop.run()
    logger.info(f"事件循环处理了 {processed} 个事件")
    
    # 验证结果
    assert len(events_received) == 2, f"期望接收2个事件，实际接收{len(events_received)}个"
    assert events_received[0][0] == "MARKET", f"第一个事件应该是市场事件，实际是{events_received[0][0]}"
    assert events_received[1][0] == "SIGNAL", f"第二个事件应该是信号事件，实际是{events_received[1][0]}"
    
    logger.info("事件循环基本功能测试通过")

def test_event_chain():
    """测试事件链式处理"""
    logger.info("测试事件链式处理")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 事件链: 市场事件 -> 信号事件 -> 订单事件 -> 成交事件
    def market_handler(event):
        logger.info(f"处理市场事件: {event}")
        # 基于市场事件创建信号事件
        if event.close_price > 3000:
            signal = SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                signal_type="LONG",
                direction=1,
                strength=1.0
            )
            logger.info(f"市场价格高于3000，生成做多信号")
            event_loop.put_event(signal)
        else:
            signal = SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                signal_type="SHORT",
                direction=-1,
                strength=1.0
            )
            logger.info(f"市场价格低于或等于3000，生成做空信号")
            event_loop.put_event(signal)
    
    def signal_handler(event):
        logger.info(f"处理信号事件: {event}")
        # 基于信号事件创建订单事件
        order = OrderEvent(
            symbol=event.symbol,
            timestamp=event.timestamp,
            order_type="MARKET",
            quantity=100.0,
            direction=event.direction
        )
        logger.info(f"基于信号生成订单")
        event_loop.put_event(order)
    
    def order_handler(event):
        logger.info(f"处理订单事件: {event}")
        # 基于订单事件创建成交事件
        fill = FillEvent(
            symbol=event.symbol,
            timestamp=event.timestamp,
            quantity=event.quantity,
            direction=event.direction,
            fill_price=3010.0,
            commission=event.quantity * 3010.0 * 0.0003  # 模拟手续费
        )
        logger.info(f"订单已成交")
        event_loop.put_event(fill)
    
    def fill_handler(event):
        logger.info(f"处理成交事件: {event}")
        # 记录成交
        logger.info(f"成交记录: 品种={event.symbol}, 数量={event.quantity}, "
                   f"方向={event.direction}, 价格={event.fill_price}, "
                   f"手续费={event.commission}")
    
    # 注册处理函数
    event_loop.register_handler("MARKET", market_handler)
    event_loop.register_handler("SIGNAL", signal_handler)
    event_loop.register_handler("ORDER", order_handler)
    event_loop.register_handler("FILL", fill_handler)
    
    # 创建初始市场事件
    market_event_1 = MarketEvent(
        symbol="SHSE.000001",
        timestamp=datetime.now(),
        open_price=3000.0,
        high_price=3050.0,
        low_price=2980.0,
        close_price=3020.0,  # 高于3000，应生成做多信号
        volume=10000
    )
    
    market_event_2 = MarketEvent(
        symbol="SHSE.000001",
        timestamp=datetime.now(),
        open_price=2950.0,
        high_price=3000.0,
        low_price=2900.0,
        close_price=2980.0,  # 低于3000，应生成做空信号
        volume=12000
    )
    
    # 添加事件
    event_loop.put_event(market_event_1)
    
    # 运行事件循环
    processed_1 = event_loop.run()
    logger.info(f"第一轮事件循环处理了 {processed_1} 个事件")
    
    # 添加第二个事件
    event_loop.put_event(market_event_2)
    
    # 再次运行事件循环
    processed_2 = event_loop.run()
    logger.info(f"第二轮事件循环处理了 {processed_2} 个事件")
    
    # 验证结果
    assert processed_1 == 4, f"第一轮应处理4个事件(市场->信号->订单->成交)，实际处理{processed_1}个"
    assert processed_2 == 4, f"第二轮应处理4个事件(市场->信号->订单->成交)，实际处理{processed_2}个"
    
    logger.info("事件链式处理测试通过")

def test_event_loop_performance():
    """测试事件循环性能"""
    logger.info("测试事件循环性能")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 计数器
    counter = {'count': 0}
    
    # 简单处理函数
    def simple_handler(event):
        counter['count'] += 1
    
    # 注册处理函数
    event_loop.register_handler("MARKET", simple_handler)
    
    # 创建大量事件
    num_events = 10000
    logger.info(f"创建 {num_events} 个市场事件")
    
    for i in range(num_events):
        event = MarketEvent(
            symbol="SHSE.000001",
            timestamp=datetime.now(),
            open_price=3000.0,
            high_price=3050.0,
            low_price=2980.0,
            close_price=3020.0,
            volume=10000
        )
        event_loop.put_event(event)
    
    # 测量处理时间
    start_time = time.time()
    processed = event_loop.run()
    elapsed = time.time() - start_time
    
    # 输出性能指标
    logger.info(f"处理 {processed} 个事件耗时 {elapsed:.4f} 秒")
    logger.info(f"平均每秒处理 {processed/elapsed:.2f} 个事件")
    
    # 验证结果
    assert counter['count'] == num_events, f"应处理 {num_events} 个事件，实际处理 {counter['count']} 个"
    
    logger.info("事件循环性能测试通过")

if __name__ == "__main__":
    logger.info("开始测试事件循环")
    
    try:
        # 运行基本功能测试
        test_event_loop_basics()
        
        # 运行事件链测试
        test_event_chain()
        
        # 运行性能测试
        test_event_loop_performance()
        
        logger.info("所有测试通过")
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    sys.exit(0) 