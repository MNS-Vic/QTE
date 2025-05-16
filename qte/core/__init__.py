#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE核心模块 - 提供向量化和事件驱动回测引擎
"""

# 从各子模块按需导出真正需要作为 qte.core.xxx 形式访问的API
# 避免不必要的重复导出或导出内部类

# 从 events.py (这是事件定义的权威来源)
from .events import Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent, OrderDirection, OrderType

# 从 event_loop.py
from .event_loop import EventLoop

# 从 event_engine.py (只导出引擎本身，事件已从events导出)
# 假设 event_engine.py 至少定义了 EventDrivenBacktester 和 EventEngine
# 如果 AccountEvent 定义在 event_engine.py 并且需要导出，则在此处添加
from .event_engine import EventDrivenBacktester, EventEngine 
# from .event_engine import AccountEvent # 如果存在且需要

# 从 vector_engine.py
from .vector_engine import VectorEngine

# 从 engine_manager.py (导出管理器、相关枚举及EngineEvent类)
from .engine_manager import BaseEngineManager, ReplayEngineManager, EngineType, EngineStatus
from .engine_manager import EngineEvent, MarketDataEvent  # 添加对EngineEvent和MarketDataEvent的导出

print(f"DEBUG: qte.core.__init__.py CLEAN VERSION executed")

__all__ = [
    # 来自 events.py
    'Event', 'EventType', 'MarketEvent', 'SignalEvent', 'OrderEvent', 'FillEvent', 'OrderDirection', 'OrderType',
    # 来自 event_loop.py
    'EventLoop',
    # 来自 event_engine.py
    'EventDrivenBacktester', 'EventEngine',
    # 'AccountEvent', # 如果导出
    # 来自 vector_engine.py
    'VectorEngine',
    # 来自 engine_manager.py
    'BaseEngineManager', 'ReplayEngineManager', 'EngineType', 'EngineStatus',
    'EngineEvent', 'MarketDataEvent',  # 添加到__all__中
]