#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy Gateway模块

根据Creative Phase设计决策实现的完整Gateway系统
包含工厂模式、智能连接管理、事件转换等核心组件
"""

from qte.vnpy import check_vnpy_availability

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

# 导出核心组件
from .qte_gateway_factory import GatewayFactory, GatewayType, create_qte_gateway, create_mock_gateway
from .event_converter import (
    EventConverterRegistry, PrecisionConverter, DirectionConverter,
    OrderTypeConverter, StatusConverter, LayeredErrorHandler,
    ConversionError, CriticalConversionError, WarningConversionError
)
from .qte_event_converters import (
    safe_convert, batch_convert, get_conversion_stats,
    QTEMarketData, QTEOrderData, QTETradeData, QTEAccountData
)
from .connection_manager import (
    SmartConnectionManager, ConnectionConfig, ConnectionState, ConnectionType,
    create_connection_manager
)
from .qte_binance_gateway import QTEBinanceGateway

# 兼容性导入（保持向后兼容）
try:
    from .binance_spot import QTEBinanceSpotGateway
except ImportError:
    QTEBinanceSpotGateway = None

__all__ = [
    # 工厂模式
    "GatewayFactory",
    "GatewayType", 
    "create_qte_gateway",
    "create_mock_gateway",
    
    # 事件转换
    "EventConverterRegistry",
    "PrecisionConverter",
    "DirectionConverter", 
    "OrderTypeConverter",
    "StatusConverter",
    "LayeredErrorHandler",
    "ConversionError",
    "CriticalConversionError",
    "WarningConversionError",
    "safe_convert",
    "batch_convert",
    "get_conversion_stats",
    
    # QTE数据类型
    "QTEMarketData",
    "QTEOrderData", 
    "QTETradeData",
    "QTEAccountData",
    
    # 连接管理
    "SmartConnectionManager",
    "ConnectionConfig",
    "ConnectionState",
    "ConnectionType",
    "create_connection_manager",
    
    # Gateway实现
    "QTEBinanceGateway",
    "QTEBinanceSpotGateway",  # 兼容性
]

# 模块信息
__version__ = "1.0.0"
__author__ = "QTE Team"
__description__ = "QTE vnpy Gateway - 基于Creative Phase设计决策的完整实现" 