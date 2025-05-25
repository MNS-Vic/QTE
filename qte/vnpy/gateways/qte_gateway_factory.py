#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE Gateway工厂模式实现

根据Creative Phase设计决策实现的Gateway工厂模式
支持多种Gateway类型的创建和管理
"""

from typing import Dict, Type, Optional, Any
from enum import Enum
import logging

from qte.vnpy import check_vnpy_availability

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.event import EventEngine
    from vnpy.trader.gateway import BaseGateway
else:
    BaseGateway = object
    EventEngine = object


class GatewayType(Enum):
    """Gateway类型枚举"""
    QTE_BINANCE = "QTE_BINANCE"
    QTE_MOCK = "QTE_MOCK"
    # 预留未来扩展
    QTE_OKEX = "QTE_OKEX"
    QTE_HUOBI = "QTE_HUOBI"


class GatewayFactory:
    """
    Gateway工厂类
    
    实现Creative Phase决策：工厂模式 (选项1.2)
    - 支持多种Gateway类型
    - 便于单元测试和依赖注入
    - 符合开闭原则，易于扩展
    - 实例管理灵活
    """
    
    _gateway_classes: Dict[GatewayType, Type[BaseGateway]] = {}
    _instances: Dict[str, BaseGateway] = {}
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def register_gateway(cls, gateway_type: GatewayType, gateway_class: Type[BaseGateway]):
        """注册Gateway类型"""
        cls._gateway_classes[gateway_type] = gateway_class
        cls._logger.info(f"注册Gateway类型: {gateway_type.value} -> {gateway_class.__name__}")
    
    @classmethod
    def create_gateway(
        cls, 
        gateway_type: GatewayType, 
        event_engine: EventEngine,
        gateway_name: Optional[str] = None,
        **kwargs
    ) -> BaseGateway:
        """
        创建Gateway实例
        
        Args:
            gateway_type: Gateway类型
            event_engine: vnpy事件引擎
            gateway_name: Gateway名称（可选）
            **kwargs: 额外参数
            
        Returns:
            Gateway实例
            
        Raises:
            ValueError: 未注册的Gateway类型
            ImportError: vnpy不可用
        """
        if not VNPY_AVAILABLE:
            raise ImportError(f"vnpy核心组件不可用：{VNPY_INFO['missing_deps']}")
        
        if gateway_type not in cls._gateway_classes:
            available_types = list(cls._gateway_classes.keys())
            raise ValueError(
                f"未注册的Gateway类型: {gateway_type}. "
                f"可用类型: {[t.value for t in available_types]}"
            )
        
        gateway_class = cls._gateway_classes[gateway_type]
        
        # 生成实例键
        instance_key = f"{gateway_type.value}_{gateway_name or 'default'}"
        
        # 检查是否已存在实例（可选的单例行为）
        if instance_key in cls._instances:
            cls._logger.warning(f"Gateway实例已存在: {instance_key}")
            return cls._instances[instance_key]
        
        # 创建新实例
        try:
            gateway = gateway_class(event_engine, gateway_name, **kwargs)
            cls._instances[instance_key] = gateway
            cls._logger.info(f"创建Gateway实例: {instance_key}")
            return gateway
        except Exception as e:
            cls._logger.error(f"创建Gateway失败: {e}")
            raise
    
    @classmethod
    def get_gateway(cls, gateway_type: GatewayType, gateway_name: Optional[str] = None) -> Optional[BaseGateway]:
        """获取已创建的Gateway实例"""
        instance_key = f"{gateway_type.value}_{gateway_name or 'default'}"
        return cls._instances.get(instance_key)
    
    @classmethod
    def remove_gateway(cls, gateway_type: GatewayType, gateway_name: Optional[str] = None) -> bool:
        """移除Gateway实例"""
        instance_key = f"{gateway_type.value}_{gateway_name or 'default'}"
        if instance_key in cls._instances:
            gateway = cls._instances.pop(instance_key)
            try:
                gateway.close()
            except Exception as e:
                cls._logger.error(f"关闭Gateway时出错: {e}")
            cls._logger.info(f"移除Gateway实例: {instance_key}")
            return True
        return False
    
    @classmethod
    def list_gateways(cls) -> Dict[str, BaseGateway]:
        """列出所有Gateway实例"""
        return cls._instances.copy()
    
    @classmethod
    def list_available_types(cls) -> list[GatewayType]:
        """列出可用的Gateway类型"""
        return list(cls._gateway_classes.keys())
    
    @classmethod
    def clear_all(cls):
        """清理所有Gateway实例"""
        for instance_key, gateway in cls._instances.items():
            try:
                gateway.close()
            except Exception as e:
                cls._logger.error(f"关闭Gateway {instance_key} 时出错: {e}")
        cls._instances.clear()
        cls._logger.info("已清理所有Gateway实例")


# 便捷函数
def create_qte_gateway(
    event_engine: EventEngine,
    gateway_name: Optional[str] = None,
    **kwargs
) -> BaseGateway:
    """创建QTE Binance Gateway的便捷函数"""
    return GatewayFactory.create_gateway(
        GatewayType.QTE_BINANCE,
        event_engine,
        gateway_name,
        **kwargs
    )


def create_mock_gateway(
    event_engine: EventEngine,
    gateway_name: Optional[str] = None,
    **kwargs
) -> BaseGateway:
    """创建QTE Mock Gateway的便捷函数"""
    return GatewayFactory.create_gateway(
        GatewayType.QTE_MOCK,
        event_engine,
        gateway_name,
        **kwargs
    ) 