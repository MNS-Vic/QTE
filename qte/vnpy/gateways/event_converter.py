#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE事件转换器

根据Creative Phase设计决策实现的事件转换机制
- 注册器模式 (选项1.3): 类型安全 + 易扩展
- 字段级精确转换 (选项2.1): 金融级精度保证
- 分层错误处理 (选项3.3): 生产级稳定性
"""

from typing import Dict, Type, Callable, Any, Optional, TypeVar, Generic
from decimal import Decimal
from datetime import datetime
import logging
from enum import Enum

from qte.vnpy import check_vnpy_availability

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.trader.object import (
        TickData, OrderData, TradeData, AccountData, ContractData,
        OrderRequest, CancelRequest, SubscribeRequest
    )
    from vnpy.trader.constant import Exchange, Product, Status, OrderType, Direction
else:
    # 模拟类型定义
    TickData = object
    OrderData = object
    TradeData = object
    AccountData = object
    ContractData = object
    OrderRequest = object
    CancelRequest = object
    SubscribeRequest = object
    Exchange = object
    Product = object
    Status = object
    OrderType = object
    Direction = object


# 类型变量
T = TypeVar('T')
U = TypeVar('U')


class ConversionError(Exception):
    """转换错误基类"""
    pass


class CriticalConversionError(ConversionError):
    """关键转换错误 - 需要立即处理"""
    pass


class WarningConversionError(ConversionError):
    """警告级转换错误 - 可以继续处理"""
    pass


class ErrorLevel(Enum):
    """错误级别枚举"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class EventConverterRegistry:
    """
    事件转换器注册表
    
    实现Creative Phase决策：注册器模式 (选项1.3)
    - 类型安全，编译时检查
    - 扩展性好，易于添加新转换器
    - 代码组织清晰
    - 性能较好
    """
    
    def __init__(self):
        self._converters: Dict[tuple, Callable] = {}
        self._logger = logging.getLogger(__name__)
        
    def register(self, source_type: Type[T], target_type: Type[U]):
        """
        注册转换器装饰器
        
        Args:
            source_type: 源类型
            target_type: 目标类型
        """
        def decorator(converter_func: Callable[[T], U]) -> Callable[[T], U]:
            key = (source_type, target_type)
            self._converters[key] = converter_func
            self._logger.info(f"注册转换器: {source_type.__name__} -> {target_type.__name__}")
            return converter_func
        return decorator
    
    def convert(self, source_obj: T, target_type: Type[U]) -> U:
        """
        执行转换
        
        Args:
            source_obj: 源对象
            target_type: 目标类型
            
        Returns:
            转换后的对象
            
        Raises:
            ConversionError: 转换失败
        """
        source_type = type(source_obj)
        key = (source_type, target_type)
        
        if key not in self._converters:
            raise CriticalConversionError(
                f"未找到转换器: {source_type.__name__} -> {target_type.__name__}"
            )
        
        converter = self._converters[key]
        
        try:
            result = converter(source_obj)
            self._logger.debug(f"转换成功: {source_type.__name__} -> {target_type.__name__}")
            return result
        except Exception as e:
            error_msg = f"转换失败: {source_type.__name__} -> {target_type.__name__}: {e}"
            self._logger.error(error_msg)
            raise CriticalConversionError(error_msg) from e
    
    def has_converter(self, source_type: Type[T], target_type: Type[U]) -> bool:
        """检查是否存在转换器"""
        return (source_type, target_type) in self._converters
    
    def list_converters(self) -> list[tuple]:
        """列出所有注册的转换器"""
        return list(self._converters.keys())


# 全局转换器注册表
converter_registry = EventConverterRegistry()


class PrecisionConverter:
    """
    精度转换器
    
    实现Creative Phase决策：字段级精确转换 (选项2.1)
    - 金融级精度保证
    - Decimal类型处理
    - 数据完整性保证
    """
    
    @staticmethod
    def to_decimal(value: Any, precision: int = 8) -> Decimal:
        """转换为Decimal类型，保证精度"""
        if value is None:
            return Decimal('0')
        
        if isinstance(value, Decimal):
            return value
        
        try:
            # 转换为字符串再转Decimal，避免浮点精度问题
            decimal_value = Decimal(str(value))
            # 量化到指定精度
            return decimal_value.quantize(Decimal('0.' + '0' * precision))
        except Exception as e:
            raise WarningConversionError(f"精度转换失败: {value} -> Decimal: {e}")
    
    @staticmethod
    def to_float(value: Any) -> float:
        """转换为float类型"""
        if value is None:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, Decimal):
            return float(value)
        
        try:
            return float(value)
        except Exception as e:
            raise WarningConversionError(f"浮点转换失败: {value} -> float: {e}")
    
    @staticmethod
    def to_int(value: Any) -> int:
        """转换为int类型"""
        if value is None:
            return 0
        
        if isinstance(value, int):
            return value
        
        try:
            return int(float(value))
        except Exception as e:
            raise WarningConversionError(f"整数转换失败: {value} -> int: {e}")


class DirectionConverter:
    """方向转换器"""
    
    # QTE到vnpy方向映射
    QTE_TO_VNPY_DIRECTION = {
        "BUY": Direction.LONG if VNPY_AVAILABLE else "LONG",
        "SELL": Direction.SHORT if VNPY_AVAILABLE else "SHORT",
        "LONG": Direction.LONG if VNPY_AVAILABLE else "LONG",
        "SHORT": Direction.SHORT if VNPY_AVAILABLE else "SHORT",
    }
    
    # vnpy到QTE方向映射
    VNPY_TO_QTE_DIRECTION = {
        Direction.LONG if VNPY_AVAILABLE else "LONG": "BUY",
        Direction.SHORT if VNPY_AVAILABLE else "SHORT": "SELL",
    }
    
    @classmethod
    def qte_to_vnpy(cls, qte_direction: str):
        """QTE方向转vnpy方向"""
        if qte_direction not in cls.QTE_TO_VNPY_DIRECTION:
            raise WarningConversionError(f"未知的QTE方向: {qte_direction}")
        return cls.QTE_TO_VNPY_DIRECTION[qte_direction]
    
    @classmethod
    def vnpy_to_qte(cls, vnpy_direction) -> str:
        """vnpy方向转QTE方向"""
        if vnpy_direction not in cls.VNPY_TO_QTE_DIRECTION:
            raise WarningConversionError(f"未知的vnpy方向: {vnpy_direction}")
        return cls.VNPY_TO_QTE_DIRECTION[vnpy_direction]


class OrderTypeConverter:
    """订单类型转换器"""
    
    # QTE到vnpy订单类型映射
    QTE_TO_VNPY_ORDER_TYPE = {
        "MARKET": OrderType.MARKET if VNPY_AVAILABLE else "MARKET",
        "LIMIT": OrderType.LIMIT if VNPY_AVAILABLE else "LIMIT",
        "STOP": OrderType.STOP if VNPY_AVAILABLE else "STOP",
        "STOP_MARKET": OrderType.STOP if VNPY_AVAILABLE else "STOP",
    }
    
    # vnpy到QTE订单类型映射
    VNPY_TO_QTE_ORDER_TYPE = {
        OrderType.MARKET if VNPY_AVAILABLE else "MARKET": "MARKET",
        OrderType.LIMIT if VNPY_AVAILABLE else "LIMIT": "LIMIT",
        OrderType.STOP if VNPY_AVAILABLE else "STOP": "STOP",
    }
    
    @classmethod
    def qte_to_vnpy(cls, qte_type: str):
        """QTE订单类型转vnpy类型"""
        if qte_type not in cls.QTE_TO_VNPY_ORDER_TYPE:
            raise WarningConversionError(f"未知的QTE订单类型: {qte_type}")
        return cls.QTE_TO_VNPY_ORDER_TYPE[qte_type]
    
    @classmethod
    def vnpy_to_qte(cls, vnpy_type) -> str:
        """vnpy订单类型转QTE类型"""
        if vnpy_type not in cls.VNPY_TO_QTE_ORDER_TYPE:
            raise WarningConversionError(f"未知的vnpy订单类型: {vnpy_type}")
        return cls.VNPY_TO_QTE_ORDER_TYPE[vnpy_type]


class StatusConverter:
    """状态转换器"""
    
    # QTE到vnpy状态映射
    QTE_TO_VNPY_STATUS = {
        "NEW": Status.SUBMITTING if VNPY_AVAILABLE else "SUBMITTING",
        "PARTIALLY_FILLED": Status.PARTTRADED if VNPY_AVAILABLE else "PARTTRADED",
        "FILLED": Status.ALLTRADED if VNPY_AVAILABLE else "ALLTRADED",
        "CANCELED": Status.CANCELLED if VNPY_AVAILABLE else "CANCELLED",
        "REJECTED": Status.REJECTED if VNPY_AVAILABLE else "REJECTED",
        "EXPIRED": Status.CANCELLED if VNPY_AVAILABLE else "CANCELLED",
    }
    
    @classmethod
    def qte_to_vnpy(cls, qte_status: str):
        """QTE状态转vnpy状态"""
        if qte_status not in cls.QTE_TO_VNPY_STATUS:
            raise WarningConversionError(f"未知的QTE状态: {qte_status}")
        return cls.QTE_TO_VNPY_STATUS[qte_status]


# 分层错误处理器
class LayeredErrorHandler:
    """
    分层错误处理器
    
    实现Creative Phase决策：分层错误处理 (选项3.3)
    - 生产级稳定性
    - 分级错误处理
    - 调试友好
    """
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._error_counts = {level: 0 for level in ErrorLevel}
    
    def handle_error(self, error: ConversionError, context: str = "") -> bool:
        """
        处理转换错误
        
        Args:
            error: 转换错误
            context: 错误上下文
            
        Returns:
            是否可以继续处理
        """
        if isinstance(error, CriticalConversionError):
            return self._handle_critical_error(error, context)
        elif isinstance(error, WarningConversionError):
            return self._handle_warning_error(error, context)
        else:
            return self._handle_info_error(error, context)
    
    def _handle_critical_error(self, error: CriticalConversionError, context: str) -> bool:
        """处理关键错误"""
        self._error_counts[ErrorLevel.CRITICAL] += 1
        self._logger.critical(f"关键转换错误 [{context}]: {error}")
        # 关键错误不能继续处理
        return False
    
    def _handle_warning_error(self, error: WarningConversionError, context: str) -> bool:
        """处理警告错误"""
        self._error_counts[ErrorLevel.WARNING] += 1
        self._logger.warning(f"警告转换错误 [{context}]: {error}")
        # 警告错误可以继续处理
        return True
    
    def _handle_info_error(self, error: ConversionError, context: str) -> bool:
        """处理信息错误"""
        self._error_counts[ErrorLevel.INFO] += 1
        self._logger.info(f"信息转换错误 [{context}]: {error}")
        # 信息错误可以继续处理
        return True
    
    def get_error_stats(self) -> Dict[ErrorLevel, int]:
        """获取错误统计"""
        return self._error_counts.copy()
    
    def reset_stats(self):
        """重置错误统计"""
        self._error_counts = {level: 0 for level in ErrorLevel}


# 全局错误处理器
error_handler = LayeredErrorHandler() 