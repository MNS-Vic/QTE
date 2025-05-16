#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试引擎事件系统

验证可以正确导入和使用EngineEvent类
"""

import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已添加项目路径: {project_root}")

# 导入需要测试的类
from qte import EngineEvent, MarketDataEvent

def test_engine_event():
    """测试EngineEvent类的创建和使用"""
    print("===== 测试引擎事件类 =====")
    
    # 创建一个EngineEvent实例
    event = EngineEvent(
        event_type="TEST_EVENT",
        timestamp=datetime.now(),
        data={"test": "data"}
    )
    print(f"创建的引擎事件: {event}")
    
    # 验证EngineEvent的属性
    print(f"事件类型: {event.event_type}")
    print(f"时间戳: {event.timestamp}")
    print(f"数据: {event.data}")
    
    # 创建一个MarketDataEvent实例
    market_data = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="SHSE.000001",
        data={"price": 3020.0, "volume": 10000}
    )
    print(f"创建的市场数据事件: {market_data}")
    
    # 验证MarketDataEvent的属性
    print(f"事件类型: {market_data.event_type}")
    print(f"时间戳: {market_data.timestamp}")
    print(f"品种: {market_data.symbol}")
    print(f"数据: {market_data.data}")
    
    print("===== 测试完成 =====")

if __name__ == "__main__":
    test_engine_event() 