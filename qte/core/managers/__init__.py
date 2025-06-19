"""
QTE核心管理器模块

提供各种管理器的实现，包括引擎管理器、事件管理器等
"""

from .engine_manager_v2 import EngineManagerV2
from .event_manager_v2 import EventManagerV2

__all__ = [
    'EngineManagerV2',
    'EventManagerV2'
]
