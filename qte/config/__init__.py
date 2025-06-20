"""
QTE统一配置管理系统

提供统一的配置管理功能，包括：
- 配置加载和验证
- 环境隔离和继承
- 配置热更新
- 版本管理
- 类型安全
"""

from .config_manager import ConfigManager, ConfigContext
from .config_schema import ConfigSchema, ConfigValidator, FieldType, FieldSchema
from .config_loader import ConfigLoader, ConfigFormat
from .config_watcher import ConfigWatcher
from .exceptions import (
    ConfigError,
    ConfigValidationError,
    ConfigNotFoundError,
    ConfigFormatError
)

__all__ = [
    # 核心组件
    'ConfigManager',
    'ConfigContext',
    'ConfigSchema',
    'ConfigValidator',
    'FieldType',
    'FieldSchema',
    'ConfigLoader',
    'ConfigFormat',
    'ConfigWatcher',

    # 异常类
    'ConfigError',
    'ConfigValidationError',
    'ConfigNotFoundError',
    'ConfigFormatError'
]
