#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy集成模块

提供QTE与vnpy框架的深度集成支持：
- 自定义Binance网关 (BinanceGateway)
- 数据源适配器 (VnpyDataSource)
- 执行处理器 (VnpyExecutionHandler)
- 策略适配器 (VnpyStrategyAdapter)
"""

__version__ = "1.0.0"
__author__ = "QTE Team"

from typing import TYPE_CHECKING

# 延迟导入以避免vnpy依赖问题
if TYPE_CHECKING:
    from .gateways.binance_spot import QTEBinanceSpotGateway
    from .gateways.binance_futures import QTEBinanceFuturesGateway
    from .data_source import VnpyDataSource
    from .execution_handler import VnpyExecutionHandler
    from .strategy_adapter import VnpyStrategyAdapter

__all__ = [
    "QTEBinanceSpotGateway",
    "QTEBinanceFuturesGateway", 
    "VnpyDataSource",
    "VnpyExecutionHandler",
    "VnpyStrategyAdapter",
]

# 模块状态管理
_vnpy_available = False

def check_vnpy_availability():
    """
    检查vnpy是否可用
    返回: (是否可用, 详细信息, 可用组件列表)
    """
    vnpy_info = {
        "available": False,
        "version": None,
        "missing_deps": [],
        "available_components": [],
        "status": "未安装"
    }
    
    try:
        import vnpy
        # 尝试获取版本信息，如果没有则使用默认值
        try:
            vnpy_info["version"] = vnpy.__version__
        except AttributeError:
            vnpy_info["version"] = "unknown"
        vnpy_info["status"] = "已安装"
        
        # 检查各个组件
        components_status = {}
        
        # 检查事件引擎 (核心组件)
        try:
            from vnpy.event import EventEngine
            components_status["event_engine"] = True
            vnpy_info["available_components"].append("EventEngine")
        except ImportError as e:
            components_status["event_engine"] = False
            vnpy_info["missing_deps"].append(f"EventEngine: {e}")
        
        # 检查交易常量 (核心组件)
        try:
            from vnpy.trader.constant import Exchange, Product, Status
            components_status["trader_constants"] = True
            vnpy_info["available_components"].append("TraderConstants")
        except ImportError as e:
            components_status["trader_constants"] = False
            vnpy_info["missing_deps"].append(f"TraderConstants: {e}")
        
        # 检查网关基类 (核心组件)
        try:
            from vnpy.trader.gateway import BaseGateway
            components_status["base_gateway"] = True
            vnpy_info["available_components"].append("BaseGateway")
        except ImportError as e:
            components_status["base_gateway"] = False
            vnpy_info["missing_deps"].append(f"BaseGateway: {e}")
        
        # 检查交易对象 (核心组件)
        try:
            from vnpy.trader.object import TickData, OrderData, TradeData
            components_status["trader_objects"] = True
            vnpy_info["available_components"].append("TraderObjects")
        except ImportError as e:
            components_status["trader_objects"] = False
            vnpy_info["missing_deps"].append(f"TraderObjects: {e}")
        
        # 检查主引擎 (可选组件，需要更多依赖)
        try:
            from vnpy.trader.engine import MainEngine
            components_status["main_engine"] = True
            vnpy_info["available_components"].append("MainEngine")
        except ImportError as e:
            components_status["main_engine"] = False
            vnpy_info["missing_deps"].append(f"MainEngine: {e}")
        
        # 如果核心组件都可用，则认为vnpy可用
        core_components = ["event_engine", "trader_constants", "base_gateway", "trader_objects"]
        if all(components_status.get(comp, False) for comp in core_components):
            vnpy_info["available"] = True
            vnpy_info["status"] = "核心组件可用"
            
            if components_status.get("main_engine", False):
                vnpy_info["status"] = "完全可用"
        else:
            vnpy_info["status"] = "核心组件缺失"
            
    except ImportError:
        vnpy_info["status"] = "未安装"
        vnpy_info["missing_deps"].append("vnpy包未安装")
    
    return vnpy_info["available"], vnpy_info

def is_vnpy_available():
    """检查vnpy是否可用的简单版本"""
    available, _ = check_vnpy_availability()
    return available

# 初始化时检查vnpy可用性
check_vnpy_availability() 