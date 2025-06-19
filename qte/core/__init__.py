#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE核心模块 - 提供向量化和事件驱动回测引擎

V1架构 (原始架构，向后兼容):
- 直接依赖的引擎实现
- 紧耦合的组件设计

V2架构 (重构后的解耦架构):
- 基于接口的解耦设计
- 插件化引擎架构
- 统一的事件处理系统
- 依赖注入和服务发现
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

# V2架构 - 接口和实现 (可选导入，避免破坏现有代码)
try:
    # 接口定义
    from .interfaces import (
        IBacktestEngine,
        IEngineManager,
        IEventBus,
        IEventHandler,
        EngineCapability,
        EngineMetrics,
        BacktestResult
    )

    # 引擎实现
    from .engines import (
        VectorEngineV2,
        EngineRegistry
    )

    # 管理器实现
    from .managers import (
        EngineManagerV2,
        EventManagerV2
    )

    # V2架构可用标志
    _V2_AVAILABLE = True

except ImportError as e:
    # V2架构不可用，只使用V1架构
    _V2_AVAILABLE = False
    print(f"INFO: V2架构不可用，使用V1架构: {e}")

print(f"DEBUG: qte.core.__init__.py CLEAN VERSION executed, V2架构可用: {_V2_AVAILABLE}")

# 构建__all__列表
__all__ = [
    # V1架构 - 来自 events.py
    'Event', 'EventType', 'MarketEvent', 'SignalEvent', 'OrderEvent', 'FillEvent', 'OrderDirection', 'OrderType',
    # V1架构 - 来自 event_loop.py
    'EventLoop',
    # V1架构 - 来自 event_engine.py
    'EventDrivenBacktester', 'EventEngine',
    # V1架构 - 来自 vector_engine.py
    'VectorEngine',
    # V1架构 - 来自 engine_manager.py
    'BaseEngineManager', 'ReplayEngineManager', 'EngineType', 'EngineStatus',
    'EngineEvent', 'MarketDataEvent',
]

# 如果V2架构可用，添加到__all__中
if _V2_AVAILABLE:
    __all__.extend([
        # V2架构 - 接口
        'IBacktestEngine',
        'IEngineManager',
        'IEventBus',
        'IEventHandler',
        'EngineCapability',
        'EngineMetrics',
        'BacktestResult',

        # V2架构 - 实现
        'VectorEngineV2',
        'EngineRegistry',
        'EngineManagerV2',
        'EventManagerV2'
    ])