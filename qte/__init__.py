#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE - 量化回测引擎

一个高性能的量化回测框架，支持向量化和事件驱动两种回测方式，以及机器学习集成。
"""

print(f"DEBUG: qte.__init__.py TOP LEVEL executed") # 添加一个打印语句确认执行

# 恢复对 qte.core 的导入
from qte.core import (
    VectorEngine, EventDrivenBacktester, EventLoop, 
    BaseEngineManager, ReplayEngineManager, EngineType, EngineStatus,
    Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent, 
    OrderDirection, OrderType,
    EngineEvent, MarketDataEvent  # 添加引擎事件类的导出
)

# 暂时保持对 qte.ml 的导入注释掉
# from qte.ml import FeatureGenerator, ModelManager

__version__ = "0.1.0"

__all__ = [
    'VectorEngine',
    'EventDrivenBacktester',
    'EventLoop',
    'BaseEngineManager',
    'ReplayEngineManager',
    'EngineType',
    'EngineStatus',
    'Event', 'EventType', 'MarketEvent', 'SignalEvent', 'OrderEvent', 'FillEvent',
    'OrderDirection', 'OrderType',
    'EngineEvent', 'MarketDataEvent',  # 添加到__all__中
    # 'FeatureGenerator',
    # 'ModelManager'
]