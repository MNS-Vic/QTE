"""
QTE核心接口模块 - 定义核心组件的抽象接口

这个模块提供了QTE系统中各个核心组件的抽象接口定义，
实现了依赖倒置原则，降低了组件间的耦合度。
"""

from .engine_interface import (
    IBacktestEngine,
    IEngineManager,
    EngineCapability,
    EngineMetrics,
    BacktestResult
)

from .event_interface import (
    IEventBus,
    IEventHandler,
    IEventSubscriber,
    EventPriority
)

from .data_interface import (
    IDataProvider,
    IDataProcessor,
    DataFormat,
    DataQuality
)

__all__ = [
    # 引擎接口
    'IBacktestEngine',
    'IEngineManager', 
    'EngineCapability',
    'EngineMetrics',
    'BacktestResult',
    
    # 事件接口
    'IEventBus',
    'IEventHandler',
    'IEventSubscriber',
    'EventPriority',
    
    # 数据接口
    'IDataProvider',
    'IDataProcessor',
    'DataFormat',
    'DataQuality'
]
