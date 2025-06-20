#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE事件系统模块

重构后的事件系统架构，按功能解耦：
- event_types: 事件类型定义和枚举
- event_bus: 事件总线和分发机制
- event_handlers: 事件处理器基类和接口
- event_registry: 事件注册器和插件管理
- event_plugins: 插件化事件处理器
"""

# 导入事件类型和枚举
from .event_types import (
    EventType,
    EventPriority,
    Event,
    MarketEvent,
    SignalEvent,
    OrderEvent,
    FillEvent,
    AccountEvent,
    OrderType,
    OrderDirection
)

# 导入事件总线
from .event_bus import (
    EventBus,
    EventMetadata,
    EventRecord
)

# 导入事件处理器
from .event_handlers import (
    EventHandler,
    AsyncEventHandler,
    EventHandlerInterface,
    HandlerRegistry
)

# 导入事件注册器
from .event_registry import (
    EventRegistry,
    PluginManager,
    EventPlugin
)

# 导入兼容性接口（向后兼容）
from .legacy_compat import (
    LegacyEventEngine,
    LegacyEvent,
    create_legacy_event
)

__all__ = [
    # 事件类型和枚举
    'EventType',
    'EventPriority', 
    'Event',
    'MarketEvent',
    'SignalEvent',
    'OrderEvent',
    'FillEvent',
    'AccountEvent',
    'OrderType',
    'OrderDirection',
    
    # 事件总线
    'EventBus',
    'EventMetadata',
    'EventRecord',
    
    # 事件处理器
    'EventHandler',
    'AsyncEventHandler',
    'EventHandlerInterface',
    'HandlerRegistry',
    
    # 事件注册器
    'EventRegistry',
    'PluginManager',
    'EventPlugin',
    
    # 兼容性接口
    'LegacyEventEngine',
    'LegacyEvent',
    'create_legacy_event'
]
