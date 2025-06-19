"""
QTE核心引擎实现模块

提供各种回测引擎的具体实现，包括向量化引擎、事件驱动引擎等
"""

from .vector_engine_v2 import VectorEngineV2
from .engine_registry import EngineRegistry

# 注意：EventEngineV2 暂未实现，将在后续版本中添加
# from .event_engine_v2 import EventEngineV2

__all__ = [
    'VectorEngineV2',
    'EngineRegistry'
    # 'EventEngineV2'  # 暂未实现
]
