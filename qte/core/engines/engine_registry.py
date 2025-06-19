"""
引擎注册表 - 管理和创建回测引擎实例

提供统一的引擎注册、发现和创建机制，支持插件化的引擎扩展
"""

import logging
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from ..interfaces.engine_interface import IBacktestEngine, IEngineManager


@dataclass
class EngineInfo:
    """引擎信息"""
    engine_type: str
    engine_class: Type[IBacktestEngine]
    description: str
    capabilities: List[str]
    version: str = "1.0.0"
    author: str = "QTE Team"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'engine_type': self.engine_type,
            'class_name': self.engine_class.__name__,
            'description': self.description,
            'capabilities': self.capabilities,
            'version': self.version,
            'author': self.author
        }


class EngineRegistry(IEngineManager):
    """
    引擎注册表
    
    实现了IEngineManager接口，提供引擎的注册、发现和创建功能。
    支持插件化的引擎扩展和动态引擎加载。
    """
    
    _instance = None
    _engines: Dict[str, EngineInfo] = {}
    _logger = logging.getLogger('EngineRegistry')
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(EngineRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register_engine(cls, engine_type: str, engine_class: Type[IBacktestEngine],
                       description: str = "", capabilities: Optional[List[str]] = None,
                       version: str = "1.0.0", author: str = "QTE Team") -> bool:
        """
        注册引擎类型
        
        Args:
            engine_type: 引擎类型标识
            engine_class: 引擎类
            description: 引擎描述
            capabilities: 引擎能力列表
            version: 版本号
            author: 作者
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 验证引擎类是否实现了IBacktestEngine接口
            if not issubclass(engine_class, IBacktestEngine):
                cls._logger.error(f"❌ 引擎类 {engine_class.__name__} 必须实现IBacktestEngine接口")
                return False
            
            # 获取引擎能力
            if capabilities is None:
                try:
                    # 尝试从引擎类获取能力信息
                    temp_instance = engine_class()
                    capabilities = [cap.value for cap in temp_instance.get_capabilities()]
                except Exception:
                    capabilities = []
            
            # 创建引擎信息
            engine_info = EngineInfo(
                engine_type=engine_type,
                engine_class=engine_class,
                description=description or f"{engine_class.__name__} 回测引擎",
                capabilities=capabilities,
                version=version,
                author=author
            )
            
            # 注册引擎
            cls._engines[engine_type] = engine_info
            cls._logger.info(f"📝 引擎注册成功: {engine_type} -> {engine_class.__name__}")
            return True
            
        except Exception as e:
            cls._logger.error(f"❌ 引擎注册失败: {e}")
            return False
    
    @classmethod
    def create_engine(cls, engine_type: str, config: Dict[str, Any]) -> Optional[IBacktestEngine]:
        """
        创建引擎实例
        
        Args:
            engine_type: 引擎类型
            config: 引擎配置
            
        Returns:
            Optional[IBacktestEngine]: 引擎实例，失败时返回None
        """
        try:
            if engine_type not in cls._engines:
                cls._logger.error(f"❌ 未知的引擎类型: {engine_type}")
                return None
            
            engine_info = cls._engines[engine_type]
            engine_class = engine_info.engine_class
            
            # 创建引擎实例
            engine = engine_class()
            
            # 初始化引擎
            if not engine.initialize(config):
                cls._logger.error(f"❌ 引擎初始化失败: {engine_type}")
                return None
            
            cls._logger.info(f"✅ 引擎创建成功: {engine_type}")
            return engine
            
        except Exception as e:
            cls._logger.error(f"❌ 引擎创建失败: {e}")
            return None
    
    @classmethod
    def get_available_engines(cls) -> List[str]:
        """
        获取可用的引擎类型
        
        Returns:
            List[str]: 可用引擎类型列表
        """
        return list(cls._engines.keys())
    
    @classmethod
    def get_engine_info(cls, engine_type: str) -> Dict[str, Any]:
        """
        获取引擎信息
        
        Args:
            engine_type: 引擎类型
            
        Returns:
            Dict[str, Any]: 引擎信息
        """
        if engine_type not in cls._engines:
            return {}
        
        return cls._engines[engine_type].to_dict()
    
    @classmethod
    def get_all_engines_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        获取所有引擎信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有引擎信息
        """
        return {
            engine_type: engine_info.to_dict()
            for engine_type, engine_info in cls._engines.items()
        }
    
    @classmethod
    def unregister_engine(cls, engine_type: str) -> bool:
        """
        注销引擎
        
        Args:
            engine_type: 引擎类型
            
        Returns:
            bool: 注销是否成功
        """
        if engine_type in cls._engines:
            del cls._engines[engine_type]
            cls._logger.info(f"🗑️ 引擎注销成功: {engine_type}")
            return True
        return False
    
    @classmethod
    def clear_all(cls) -> bool:
        """
        清空所有注册的引擎
        
        Returns:
            bool: 清空是否成功
        """
        cls._engines.clear()
        cls._logger.info("🧹 所有引擎已清空")
        return True
    
    @classmethod
    def validate_engine_config(cls, engine_type: str, config: Dict[str, Any]) -> List[str]:
        """
        验证引擎配置
        
        Args:
            engine_type: 引擎类型
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表
        """
        if engine_type not in cls._engines:
            return [f"未知的引擎类型: {engine_type}"]
        
        try:
            engine_info = cls._engines[engine_type]
            engine_class = engine_info.engine_class
            
            # 创建临时实例进行验证
            temp_engine = engine_class()
            return temp_engine.validate_config(config)
            
        except Exception as e:
            return [f"配置验证失败: {e}"]
    
    @classmethod
    def find_engines_by_capability(cls, capability: str) -> List[str]:
        """
        根据能力查找引擎
        
        Args:
            capability: 引擎能力
            
        Returns:
            List[str]: 支持该能力的引擎类型列表
        """
        matching_engines = []
        
        for engine_type, engine_info in cls._engines.items():
            if capability in engine_info.capabilities:
                matching_engines.append(engine_type)
        
        return matching_engines
    
    @classmethod
    def get_engine_statistics(cls) -> Dict[str, Any]:
        """
        获取引擎注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_engines = len(cls._engines)
        capabilities_count = {}
        
        for engine_info in cls._engines.values():
            for capability in engine_info.capabilities:
                capabilities_count[capability] = capabilities_count.get(capability, 0) + 1
        
        return {
            'total_engines': total_engines,
            'engine_types': list(cls._engines.keys()),
            'capabilities_distribution': capabilities_count,
            'most_common_capability': max(capabilities_count.items(), key=lambda x: x[1])[0] if capabilities_count else None
        }


# 自动注册内置引擎
def register_builtin_engines():
    """注册内置引擎"""
    try:
        # 注册向量化引擎V2
        from .vector_engine_v2 import VectorEngineV2
        EngineRegistry.register_engine(
            engine_type="vectorized_v2",
            engine_class=VectorEngineV2,
            description="高性能向量化回测引擎，支持快速回测和参数优化",
            version="2.0.0"
        )
        
        # 可以在这里注册更多内置引擎
        # from .event_engine_v2 import EventEngineV2
        # EngineRegistry.register_engine(
        #     engine_type="event_driven_v2",
        #     engine_class=EventEngineV2,
        #     description="事件驱动回测引擎，支持高精度模拟和实时处理",
        #     version="2.0.0"
        # )
        
        logging.getLogger('EngineRegistry').info("✅ 内置引擎注册完成")
        
    except Exception as e:
        logging.getLogger('EngineRegistry').error(f"❌ 内置引擎注册失败: {e}")


# 便捷函数
def get_engine(engine_type: str, config: Dict[str, Any]) -> Optional[IBacktestEngine]:
    """
    便捷函数：获取引擎实例
    
    Args:
        engine_type: 引擎类型
        config: 引擎配置
        
    Returns:
        Optional[IBacktestEngine]: 引擎实例
    """
    return EngineRegistry.create_engine(engine_type, config)


def list_engines() -> List[str]:
    """
    便捷函数：列出可用引擎
    
    Returns:
        List[str]: 可用引擎类型列表
    """
    return EngineRegistry.get_available_engines()


def get_engine_capabilities(engine_type: str) -> List[str]:
    """
    便捷函数：获取引擎能力
    
    Args:
        engine_type: 引擎类型
        
    Returns:
        List[str]: 引擎能力列表
    """
    info = EngineRegistry.get_engine_info(engine_type)
    return info.get('capabilities', [])
