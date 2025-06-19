"""
回测引擎接口定义

定义了回测引擎的统一接口，支持不同类型的回测引擎实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import pandas as pd


class EngineCapability(Enum):
    """引擎能力枚举"""
    VECTORIZED_COMPUTATION = "vectorized_computation"  # 向量化计算
    EVENT_DRIVEN_SIMULATION = "event_driven_simulation"  # 事件驱动模拟
    REAL_TIME_PROCESSING = "real_time_processing"  # 实时处理
    MULTI_ASSET_SUPPORT = "multi_asset_support"  # 多资产支持
    HIGH_FREQUENCY_DATA = "high_frequency_data"  # 高频数据支持
    PARALLEL_PROCESSING = "parallel_processing"  # 并行处理
    CUSTOM_STRATEGIES = "custom_strategies"  # 自定义策略
    RISK_MANAGEMENT = "risk_management"  # 风险管理


@dataclass
class EngineMetrics:
    """引擎性能指标"""
    execution_time: float = 0.0  # 执行时间(秒)
    memory_usage: float = 0.0  # 内存使用(MB)
    cpu_usage: float = 0.0  # CPU使用率(%)
    events_processed: int = 0  # 处理的事件数量
    throughput: float = 0.0  # 吞吐量(事件/秒)
    error_count: int = 0  # 错误数量
    warning_count: int = 0  # 警告数量
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'events_processed': self.events_processed,
            'throughput': self.throughput,
            'error_count': self.error_count,
            'warning_count': self.warning_count
        }


@dataclass
class BacktestResult:
    """回测结果统一格式"""
    success: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metrics: EngineMetrics = field(default_factory=EngineMetrics)
    
    # 交易结果
    signals: Optional[pd.DataFrame] = None
    positions: Optional[pd.DataFrame] = None
    trades: Optional[pd.DataFrame] = None
    portfolio: Optional[pd.DataFrame] = None
    
    # 性能指标
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 错误和警告
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 额外数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.metrics.error_count += 1
    
    def add_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)
        self.metrics.warning_count += 1
    
    def is_successful(self) -> bool:
        """判断回测是否成功"""
        return self.success and len(self.errors) == 0


class IBacktestEngine(ABC):
    """
    回测引擎接口
    
    定义了所有回测引擎必须实现的基本接口，
    支持向量化引擎、事件驱动引擎等不同实现。
    """
    
    @abstractmethod
    def get_engine_type(self) -> str:
        """
        获取引擎类型
        
        Returns:
            str: 引擎类型标识
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[EngineCapability]:
        """
        获取引擎能力
        
        Returns:
            List[EngineCapability]: 引擎支持的能力列表
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化引擎
        
        Args:
            config: 引擎配置参数
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def set_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> bool:
        """
        设置回测数据
        
        Args:
            data: 回测数据，可以是单个DataFrame或多个DataFrame的字典
            
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def add_strategy(self, strategy: Any) -> bool:
        """
        添加交易策略
        
        Args:
            strategy: 交易策略对象
            
        Returns:
            bool: 添加是否成功
        """
        pass
    
    @abstractmethod
    def run_backtest(self, **kwargs) -> BacktestResult:
        """
        运行回测
        
        Args:
            **kwargs: 回测参数
            
        Returns:
            BacktestResult: 回测结果
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> EngineMetrics:
        """
        获取引擎性能指标
        
        Returns:
            EngineMetrics: 性能指标
        """
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """
        重置引擎状态
        
        Returns:
            bool: 重置是否成功
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """
        清理引擎资源
        
        Returns:
            bool: 清理是否成功
        """
        pass
    
    # 可选的高级接口
    def supports_capability(self, capability: EngineCapability) -> bool:
        """
        检查是否支持特定能力
        
        Args:
            capability: 要检查的能力
            
        Returns:
            bool: 是否支持该能力
        """
        return capability in self.get_capabilities()
    
    def get_status(self) -> str:
        """
        获取引擎状态
        
        Returns:
            str: 引擎状态描述
        """
        return "unknown"
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        验证配置参数
        
        Args:
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        return []


class IEngineManager(ABC):
    """
    引擎管理器接口
    
    负责管理多个回测引擎，提供统一的引擎访问和调度接口。
    """
    
    @abstractmethod
    def register_engine(self, engine_type: str, engine_class: type) -> bool:
        """
        注册引擎类型
        
        Args:
            engine_type: 引擎类型标识
            engine_class: 引擎类
            
        Returns:
            bool: 注册是否成功
        """
        pass
    
    @abstractmethod
    def create_engine(self, engine_type: str, config: Dict[str, Any]) -> Optional[IBacktestEngine]:
        """
        创建引擎实例
        
        Args:
            engine_type: 引擎类型
            config: 引擎配置
            
        Returns:
            Optional[IBacktestEngine]: 引擎实例，失败时返回None
        """
        pass
    
    @abstractmethod
    def get_available_engines(self) -> List[str]:
        """
        获取可用的引擎类型
        
        Returns:
            List[str]: 可用引擎类型列表
        """
        pass
    
    @abstractmethod
    def get_engine_info(self, engine_type: str) -> Dict[str, Any]:
        """
        获取引擎信息
        
        Args:
            engine_type: 引擎类型
            
        Returns:
            Dict[str, Any]: 引擎信息
        """
        pass
