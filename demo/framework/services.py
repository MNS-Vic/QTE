"""
服务注册表和依赖注入机制
"""

import logging
from typing import Dict, Any, Callable, Optional, Type, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .exceptions import ServiceNotFoundError, ServiceInitializationError

T = TypeVar('T')


@dataclass
class ServiceDefinition:
    """服务定义"""
    name: str
    factory: Callable[..., Any]
    singleton: bool = True
    dependencies: Optional[list] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceFactory(ABC):
    """服务工厂抽象基类"""
    
    @abstractmethod
    def create_service(self, config: Dict[str, Any], **kwargs) -> Any:
        """创建服务实例"""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """获取服务名称"""
        pass


class ServiceRegistry:
    """
    服务注册表 - 管理演示所需的服务依赖
    
    提供依赖注入功能，支持：
    - 服务注册和发现
    - 单例模式
    - 依赖解析
    - 延迟初始化
    """
    
    _instance = None
    _services: Dict[str, ServiceDefinition] = {}
    _instances: Dict[str, Any] = {}
    _logger = logging.getLogger('ServiceRegistry')
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register_service(cls, 
                        name: str, 
                        factory: Callable[..., Any], 
                        singleton: bool = True,
                        dependencies: Optional[list] = None) -> None:
        """
        注册服务
        
        Args:
            name: 服务名称
            factory: 服务工厂函数
            singleton: 是否单例
            dependencies: 依赖的其他服务列表
        """
        cls._services[name] = ServiceDefinition(
            name=name,
            factory=factory,
            singleton=singleton,
            dependencies=dependencies or []
        )
        cls._logger.info(f"📝 注册服务: {name} (单例: {singleton})")
    
    @classmethod
    def register_factory(cls, factory: ServiceFactory) -> None:
        """
        注册服务工厂
        
        Args:
            factory: 服务工厂实例
        """
        name = factory.get_service_name()
        cls.register_service(name, factory.create_service, singleton=True)
    
    @classmethod
    def get_service(cls, name: str, config: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            config: 配置参数
            **kwargs: 额外参数
            
        Returns:
            服务实例
            
        Raises:
            ServiceNotFoundError: 服务未找到
            ServiceInitializationError: 服务初始化失败
        """
        if name not in cls._services:
            raise ServiceNotFoundError(name)
        
        service_def = cls._services[name]
        
        # 如果是单例且已经创建，直接返回
        if service_def.singleton and name in cls._instances:
            return cls._instances[name]
        
        try:
            # 解析依赖
            dependencies = {}
            for dep_name in service_def.dependencies:
                dependencies[dep_name] = cls.get_service(dep_name, config, **kwargs)
            
            # 创建服务实例
            cls._logger.debug(f"🔧 创建服务实例: {name}")
            
            # 准备参数
            factory_kwargs = {**kwargs, **dependencies}
            if config:
                factory_kwargs['config'] = config
            
            instance = service_def.factory(**factory_kwargs)
            
            # 如果是单例，缓存实例
            if service_def.singleton:
                cls._instances[name] = instance
            
            cls._logger.debug(f"✅ 服务创建成功: {name}")
            return instance
            
        except Exception as e:
            cls._logger.error(f"❌ 服务创建失败: {name}, 错误: {e}")
            raise ServiceInitializationError(name, e)
    
    @classmethod
    def get_services(cls, service_names: list, config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        批量获取服务
        
        Args:
            service_names: 服务名称列表
            config: 配置参数
            **kwargs: 额外参数
            
        Returns:
            服务字典
        """
        services = {}
        for name in service_names:
            services[name] = cls.get_service(name, config, **kwargs)
        return services
    
    @classmethod
    def has_service(cls, name: str) -> bool:
        """检查服务是否已注册"""
        return name in cls._services
    
    @classmethod
    def list_services(cls) -> list:
        """列出所有已注册的服务"""
        return list(cls._services.keys())
    
    @classmethod
    def clear_instances(cls) -> None:
        """清空所有服务实例 (主要用于测试)"""
        cls._instances.clear()
        cls._logger.info("🧹 清空所有服务实例")
    
    @classmethod
    def unregister_service(cls, name: str) -> None:
        """注销服务"""
        if name in cls._services:
            del cls._services[name]
        if name in cls._instances:
            del cls._instances[name]
        cls._logger.info(f"🗑️ 注销服务: {name}")


# 内置服务工厂

class DataGeneratorFactory(ServiceFactory):
    """数据生成器工厂"""
    
    def create_service(self, config: Dict[str, Any], **kwargs) -> Any:
        """创建数据生成器服务"""
        from ..services.data_generator import DataGeneratorService
        return DataGeneratorService(config)
    
    def get_service_name(self) -> str:
        return "data_generator"


class StrategyEngineFactory(ServiceFactory):
    """策略引擎工厂"""
    
    def create_service(self, config: Dict[str, Any], **kwargs) -> Any:
        """创建策略引擎服务"""
        from ..services.strategy_engine import StrategyEngineService
        return StrategyEngineService(config)
    
    def get_service_name(self) -> str:
        return "strategy_engine"


class BacktesterFactory(ServiceFactory):
    """回测器工厂"""
    
    def create_service(self, config: Dict[str, Any], **kwargs) -> Any:
        """创建回测器服务"""
        from ..services.backtester import BacktesterService
        return BacktesterService(config)
    
    def get_service_name(self) -> str:
        return "backtester"


class ReportGeneratorFactory(ServiceFactory):
    """报告生成器工厂"""
    
    def create_service(self, config: Dict[str, Any], **kwargs) -> Any:
        """创建报告生成器服务"""
        from ..services.report_generator import ReportGeneratorService
        return ReportGeneratorService(config)
    
    def get_service_name(self) -> str:
        return "report_generator"


# 自动注册内置服务
def register_builtin_services():
    """注册内置服务"""
    ServiceRegistry.register_factory(DataGeneratorFactory())
    ServiceRegistry.register_factory(StrategyEngineFactory())
    ServiceRegistry.register_factory(BacktesterFactory())
    ServiceRegistry.register_factory(ReportGeneratorFactory())


# 便捷函数
def get_demo_services(config: Dict[str, Any], required_services: Optional[list] = None) -> Dict[str, Any]:
    """
    获取演示所需的服务
    
    Args:
        config: 配置字典
        required_services: 必需的服务列表，如果为None则返回所有可用服务
        
    Returns:
        服务字典
    """
    if required_services is None:
        required_services = ['data_generator', 'strategy_engine', 'backtester', 'report_generator']
    
    return ServiceRegistry.get_services(required_services, config)
