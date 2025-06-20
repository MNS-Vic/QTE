#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE核心管理器模块

重构后的引擎管理器架构，按单一职责原则拆分：
- BaseManager: 基础管理器接口和通用功能
- EngineManager: 纯引擎管理功能
- ReplayManager: 数据重放管理功能
- EventManager: 事件处理管理功能
- LifecycleManager: 生命周期管理功能
"""

# 导入基础接口和枚举
from .base_manager import (
    EngineManagerInterface,
    EngineType,
    EngineStatus,
    EngineEvent,
    MarketDataEvent,
    BaseManager
)

# 导入具体管理器实现
from .engine_manager import EngineManager
from .replay_manager import ReplayManager
from .event_manager import EventManager
from .lifecycle_manager import LifecycleManager

# 导入统一的管理器（向后兼容）
from .unified_manager import (
    BaseEngineManager,
    ReplayEngineManager
)

# 导入V2管理器（保持兼容性）
try:
    from .engine_manager_v2 import EngineManagerV2
    from .event_manager_v2 import EventManagerV2
    _V2_AVAILABLE = True
except ImportError:
    _V2_AVAILABLE = False

__all__ = [
    # 基础接口和枚举
    'EngineManagerInterface',
    'EngineType',
    'EngineStatus',
    'EngineEvent',
    'MarketDataEvent',
    'BaseManager',

    # 专门管理器
    'EngineManager',
    'ReplayManager',
    'EventManager',
    'LifecycleManager',

    # 统一管理器（向后兼容）
    'BaseEngineManager',
    'ReplayEngineManager'
]

# 如果V2管理器可用，添加到导出列表
if _V2_AVAILABLE:
    __all__.extend([
        'EngineManagerV2',
        'EventManagerV2'
    ])
