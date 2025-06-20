"""
QTE统一引擎架构

V1/V2架构统一后的引擎模块，提供：
- 统一的引擎接口
- 向后兼容的V1 API
- 高性能的V2实现
- 渐进式迁移支持
"""

# V2引擎（当前实现）
from .vector_engine_v2 import VectorEngineV2
from .engine_registry import EngineRegistry

# 统一引擎接口（新增）
try:
    from .unified_vector_engine import UnifiedVectorEngine
    _UNIFIED_AVAILABLE = True
except ImportError:
    _UNIFIED_AVAILABLE = False

# V1兼容层（新增）
try:
    from .vector_engine_v1_compat import VectorEngineV1Compat
    _V1_COMPAT_AVAILABLE = True
except ImportError:
    _V1_COMPAT_AVAILABLE = False

# 引擎工厂（新增）
try:
    from .engine_factory import EngineFactory, create_engine
    _FACTORY_AVAILABLE = True
except ImportError:
    _FACTORY_AVAILABLE = False

# 迁移工具（新增）
try:
    from .migration_tools import V1ToV2Migrator, check_compatibility
    _MIGRATION_AVAILABLE = True
except ImportError:
    _MIGRATION_AVAILABLE = False

# 基础导出
__all__ = [
    'VectorEngineV2',
    'EngineRegistry'
]

# 添加统一架构组件
if _UNIFIED_AVAILABLE:
    __all__.append('UnifiedVectorEngine')

if _V1_COMPAT_AVAILABLE:
    __all__.append('VectorEngineV1Compat')

if _FACTORY_AVAILABLE:
    __all__.extend(['EngineFactory', 'create_engine'])

if _MIGRATION_AVAILABLE:
    __all__.extend(['V1ToV2Migrator', 'check_compatibility'])

# 版本信息
__version__ = "2.0.0"
__architecture__ = "unified"

# 默认引擎类型
if _UNIFIED_AVAILABLE:
    DEFAULT_ENGINE = UnifiedVectorEngine
else:
    DEFAULT_ENGINE = VectorEngineV2
