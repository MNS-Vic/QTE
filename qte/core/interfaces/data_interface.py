"""
数据接口定义

定义了数据提供者和数据处理器的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Iterator
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import pandas as pd


class DataFormat(Enum):
    """数据格式枚举"""
    OHLCV = "ohlcv"  # 开高低收成交量
    TICK = "tick"  # 逐笔数据
    ORDER_BOOK = "order_book"  # 订单簿
    TRADE = "trade"  # 成交数据
    CUSTOM = "custom"  # 自定义格式


class DataQuality(Enum):
    """数据质量等级"""
    HIGH = "high"  # 高质量，无缺失，已清洗
    MEDIUM = "medium"  # 中等质量，少量缺失
    LOW = "low"  # 低质量，存在缺失或异常
    UNKNOWN = "unknown"  # 未知质量


@dataclass
class DataMetadata:
    """数据元数据"""
    symbol: str
    data_format: DataFormat
    start_time: datetime
    end_time: datetime
    frequency: str  # 如 '1min', '1h', '1d'
    quality: DataQuality = DataQuality.UNKNOWN
    source: Optional[str] = None
    record_count: int = 0
    missing_count: int = 0
    
    def get_quality_score(self) -> float:
        """
        获取数据质量分数
        
        Returns:
            float: 质量分数 (0-1)
        """
        if self.record_count == 0:
            return 0.0
        
        completeness = 1.0 - (self.missing_count / self.record_count)
        
        quality_weights = {
            DataQuality.HIGH: 1.0,
            DataQuality.MEDIUM: 0.8,
            DataQuality.LOW: 0.5,
            DataQuality.UNKNOWN: 0.3
        }
        
        return completeness * quality_weights.get(self.quality, 0.3)


class IDataProvider(ABC):
    """
    数据提供者接口
    
    定义了数据获取的统一接口
    """
    
    @abstractmethod
    def get_data(self, symbol: str, start_time: datetime, end_time: datetime,
                frequency: str = '1d', data_format: DataFormat = DataFormat.OHLCV) -> pd.DataFrame:
        """
        获取数据
        
        Args:
            symbol: 交易标的
            start_time: 开始时间
            end_time: 结束时间
            frequency: 数据频率
            data_format: 数据格式
            
        Returns:
            pd.DataFrame: 数据
        """
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """
        获取可用的交易标的列表
        
        Returns:
            List[str]: 标的列表
        """
        pass
    
    @abstractmethod
    def get_data_metadata(self, symbol: str) -> DataMetadata:
        """
        获取数据元数据
        
        Args:
            symbol: 交易标的
            
        Returns:
            DataMetadata: 数据元数据
        """
        pass
    
    @abstractmethod
    def is_available(self, symbol: str, start_time: datetime, end_time: datetime) -> bool:
        """
        检查数据是否可用
        
        Args:
            symbol: 交易标的
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            bool: 数据是否可用
        """
        pass
    
    def get_supported_formats(self) -> List[DataFormat]:
        """
        获取支持的数据格式
        
        Returns:
            List[DataFormat]: 支持的格式列表
        """
        return [DataFormat.OHLCV]
    
    def get_supported_frequencies(self) -> List[str]:
        """
        获取支持的数据频率
        
        Returns:
            List[str]: 支持的频率列表
        """
        return ['1d', '1h', '1min']
    
    def validate_request(self, symbol: str, start_time: datetime, 
                        end_time: datetime, frequency: str) -> List[str]:
        """
        验证数据请求
        
        Args:
            symbol: 交易标的
            start_time: 开始时间
            end_time: 结束时间
            frequency: 数据频率
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not symbol:
            errors.append("交易标的不能为空")
        
        if start_time >= end_time:
            errors.append("开始时间必须早于结束时间")
        
        if frequency not in self.get_supported_frequencies():
            errors.append(f"不支持的数据频率: {frequency}")
        
        return errors


class IDataProcessor(ABC):
    """
    数据处理器接口
    
    定义了数据处理和清洗的统一接口
    """
    
    @abstractmethod
    def process(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        处理数据
        
        Args:
            data: 原始数据
            config: 处理配置
            
        Returns:
            pd.DataFrame: 处理后的数据
        """
        pass
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> List[str]:
        """
        验证数据质量
        
        Args:
            data: 数据
            
        Returns:
            List[str]: 验证问题列表
        """
        pass
    
    @abstractmethod
    def get_processor_name(self) -> str:
        """
        获取处理器名称
        
        Returns:
            str: 处理器名称
        """
        pass
    
    def get_supported_formats(self) -> List[DataFormat]:
        """
        获取支持的数据格式
        
        Returns:
            List[DataFormat]: 支持的格式列表
        """
        return [DataFormat.OHLCV]
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {}
    
    def estimate_processing_time(self, data_size: int) -> float:
        """
        估算处理时间
        
        Args:
            data_size: 数据大小（行数）
            
        Returns:
            float: 估算的处理时间（秒）
        """
        # 默认估算：每1000行数据需要0.1秒
        return (data_size / 1000) * 0.1
