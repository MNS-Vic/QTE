"""
预定义配置模式

提供QTE系统各个模块的标准配置模式定义
"""

from .demo_schema import DemoConfigSchema
from .engine_schema import EngineConfigSchema
from .trading_schema import TradingConfigSchema
from .system_schema import SystemConfigSchema

__all__ = [
    'DemoConfigSchema',
    'EngineConfigSchema', 
    'TradingConfigSchema',
    'SystemConfigSchema'
]
