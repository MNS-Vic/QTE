"""
演示工厂 - 负责创建和管理演示实例
"""

import logging
from typing import Dict, Any, Optional, Type
from pathlib import Path

from .framework import DemoFramework, DemoContext, DemoResult
from .framework.services import ServiceRegistry, register_builtin_services, get_demo_services
from .implementations.simple_demo_v2 import SimpleDemoV2


class DemoFactory:
    """
    演示工厂 - 负责创建和配置演示实例
    
    提供统一的演示创建接口，支持：
    - 演示类型注册和发现
    - 服务依赖注入
    - 配置管理
    - 向后兼容
    """
    
    _demo_registry: Dict[str, Type[DemoFramework]] = {}
    _logger = logging.getLogger('DemoFactory')
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """初始化工厂"""
        if cls._initialized:
            return
        
        cls._logger.info("🏭 初始化演示工厂...")
        
        # 注册内置服务
        register_builtin_services()
        
        # 注册内置演示类型
        cls._register_builtin_demos()
        
        cls._initialized = True
        cls._logger.info("✅ 演示工厂初始化完成")
    
    @classmethod
    def _register_builtin_demos(cls):
        """注册内置演示类型"""
        cls.register_demo('simple_v2', SimpleDemoV2)
        # 可以在这里注册更多演示类型
        # cls.register_demo('advanced_v2', AdvancedDemoV2)
        # cls.register_demo('ml_v2', MLDemoV2)
    
    @classmethod
    def register_demo(cls, name: str, demo_class: Type[DemoFramework]):
        """
        注册演示类型
        
        Args:
            name: 演示名称
            demo_class: 演示类
        """
        if not issubclass(demo_class, DemoFramework):
            raise ValueError(f"演示类必须继承自DemoFramework: {demo_class}")
        
        cls._demo_registry[name] = demo_class
        cls._logger.info(f"📝 注册演示类型: {name} -> {demo_class.__name__}")
    
    @classmethod
    def create_demo(cls, 
                   demo_type: str,
                   config: Dict[str, Any],
                   demo_name: Optional[str] = None,
                   output_dir: Optional[str] = None) -> DemoFramework:
        """
        创建演示实例
        
        Args:
            demo_type: 演示类型
            config: 配置字典
            demo_name: 演示名称
            output_dir: 输出目录
            
        Returns:
            演示实例
            
        Raises:
            ValueError: 当演示类型不存在时
        """
        cls.initialize()
        
        if demo_type not in cls._demo_registry:
            available_types = list(cls._demo_registry.keys())
            raise ValueError(f"未知的演示类型: {demo_type}，可用类型: {available_types}")
        
        # 准备演示上下文
        demo_name = demo_name or demo_type
        output_dir = Path(output_dir or 'demo_output')
        
        context = DemoContext(
            demo_name=demo_name,
            output_dir=output_dir,
            config=config
        )
        
        # 获取演示所需的服务
        try:
            services = get_demo_services(config)
            cls._logger.info(f"🔧 为演示 {demo_name} 准备服务: {list(services.keys())}")
        except Exception as e:
            cls._logger.error(f"❌ 服务准备失败: {e}")
            raise
        
        # 创建演示实例
        demo_class = cls._demo_registry[demo_type]
        demo_instance = demo_class(context, services)
        
        cls._logger.info(f"✅ 演示实例创建成功: {demo_type} -> {demo_name}")
        return demo_instance
    
    @classmethod
    def list_available_demos(cls) -> Dict[str, Dict[str, Any]]:
        """列出可用的演示类型"""
        cls.initialize()
        
        demo_info = {}
        for name, demo_class in cls._demo_registry.items():
            info = {
                'name': name,
                'class': demo_class.__name__,
                'description': demo_class.__doc__ or "无描述"
            }
            
            # 如果演示类有get_demo_info方法，获取详细信息
            if hasattr(demo_class, 'get_demo_info'):
                try:
                    # 创建临时实例获取信息
                    temp_context = DemoContext(
                        demo_name="temp",
                        output_dir=Path("temp"),
                        config={}
                    )
                    temp_instance = demo_class(temp_context, {})
                    detailed_info = temp_instance.get_demo_info()
                    info.update(detailed_info)
                except Exception:
                    pass  # 忽略错误，使用基本信息
            
            demo_info[name] = info
        
        return demo_info
    
    @classmethod
    def run_demo(cls,
                demo_type: str,
                config: Dict[str, Any],
                demo_name: Optional[str] = None,
                output_dir: Optional[str] = None) -> DemoResult:
        """
        创建并运行演示
        
        Args:
            demo_type: 演示类型
            config: 配置字典
            demo_name: 演示名称
            output_dir: 输出目录
            
        Returns:
            演示结果
        """
        cls._logger.info(f"🚀 运行演示: {demo_type}")
        
        # 创建演示实例
        demo = cls.create_demo(demo_type, config, demo_name, output_dir)
        
        # 运行演示
        result = demo.run()
        
        cls._logger.info(f"🏁 演示运行完成: {demo_type}, 状态: {result.status}")
        return result


# 向后兼容函数

def run_simple_demo_v2(config: Optional[Dict[str, Any]] = None) -> DemoResult:
    """
    运行简单演示 V2 (向后兼容函数)
    
    Args:
        config: 配置字典
        
    Returns:
        演示结果
    """
    # 使用默认配置
    default_config = {
        'initial_capital': 100000.0,
        'test_symbols': ['AAPL', 'GOOGL', 'MSFT'],
        'test_period_days': 30,
        'strategy_type': 'moving_average',
        'short_window': 5,
        'long_window': 15,
        'commission': 0.001,
        'slippage': 0.0001,
        'output_dir': 'demo_output',
        'reports_dir': 'demo_reports'
    }
    
    # 合并用户配置
    final_config = {**default_config, **(config or {})}
    
    return DemoFactory.run_demo(
        demo_type='simple_v2',
        config=final_config,
        demo_name='simple'
    )


def create_demo_with_config(demo_type: str, config_manager: Any) -> DemoFramework:
    """
    使用配置管理器创建演示
    
    Args:
        demo_type: 演示类型
        config_manager: 配置管理器实例
        
    Returns:
        演示实例
    """
    # 获取演示配置
    config = config_manager.get_demo_config(demo_type)
    
    return DemoFactory.create_demo(
        demo_type=f"{demo_type}_v2",  # 使用V2版本
        config=config,
        demo_name=demo_type
    )


# 便捷函数

def get_available_demo_types() -> list:
    """获取可用的演示类型列表"""
    return list(DemoFactory.list_available_demos().keys())


def get_demo_info(demo_type: str) -> Dict[str, Any]:
    """获取指定演示类型的信息"""
    available_demos = DemoFactory.list_available_demos()
    return available_demos.get(demo_type, {})


def validate_demo_config(demo_type: str, config: Dict[str, Any]) -> bool:
    """
    验证演示配置
    
    Args:
        demo_type: 演示类型
        config: 配置字典
        
    Returns:
        验证是否通过
    """
    try:
        # 尝试创建演示实例来验证配置
        demo = DemoFactory.create_demo(demo_type, config, "validation_test")
        return demo.validate_prerequisites()
    except Exception:
        return False
