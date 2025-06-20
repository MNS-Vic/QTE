"""
配置管理器 - 统一的配置管理核心
"""

import os
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .config_loader import ConfigLoader, LoadResult
from .config_schema import ConfigSchema, ConfigValidator
from .exceptions import (
    ConfigError, 
    ConfigValidationError, 
    ConfigNotFoundError,
    ConfigEnvironmentError
)


@dataclass
class ConfigContext:
    """配置上下文"""
    environment: str = "development"
    config_dir: Optional[Path] = None
    override_values: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.config_dir is None:
            # 默认配置目录
            self.config_dir = Path.cwd() / "config"
        elif isinstance(self.config_dir, str):
            self.config_dir = Path(self.config_dir)


class ConfigManager:
    """
    统一配置管理器
    
    提供统一的配置管理功能：
    - 多环境配置支持
    - 配置验证和类型安全
    - 配置热更新
    - 配置继承和覆盖
    - 环境变量集成
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 核心组件
        self._loader = ConfigLoader()
        self._validator = ConfigValidator()
        
        # 配置存储
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._schemas: Dict[str, ConfigSchema] = {}
        self._contexts: Dict[str, ConfigContext] = {}
        
        # 配置监听器
        self._change_listeners: List[Callable[[str, Dict[str, Any]], None]] = []
        
        # 默认上下文
        self._default_context = ConfigContext()
        
        # 初始化标志
        self._initialized = True
        
        self.logger.info("🔧 配置管理器初始化完成")
    
    def set_default_context(self, context: ConfigContext):
        """设置默认配置上下文"""
        self._default_context = context
        self.logger.info(f"📝 设置默认配置上下文: {context.environment}")
    
    def register_schema(self, name: str, schema: ConfigSchema):
        """
        注册配置模式
        
        Args:
            name: 配置名称
            schema: 配置模式
        """
        self._schemas[name] = schema
        self.logger.info(f"📋 注册配置模式: {name}")
    
    def load_config(self, 
                   name: str,
                   config_files: Optional[List[Union[str, Path]]] = None,
                   context: Optional[ConfigContext] = None,
                   validate: bool = True) -> Dict[str, Any]:
        """
        加载配置
        
        Args:
            name: 配置名称
            config_files: 配置文件列表，None表示使用默认文件
            context: 配置上下文，None表示使用默认上下文
            validate: 是否验证配置
            
        Returns:
            Dict[str, Any]: 配置数据
            
        Raises:
            ConfigNotFoundError: 配置文件不存在
            ConfigValidationError: 配置验证失败
        """
        context = context or self._default_context
        
        self.logger.info(f"📖 加载配置: {name} (环境: {context.environment})")
        
        # 确定配置文件列表
        if config_files is None:
            config_files = self._get_default_config_files(name, context)
        
        # 加载配置文件
        try:
            if len(config_files) == 1:
                load_result = self._loader.load(config_files[0])
            else:
                load_result = self._loader.load_multiple(config_files, merge_strategy='deep')
            
            config_data = load_result.data
            
        except Exception as e:
            raise ConfigError(f"配置加载失败: {e}")
        
        # 应用环境变量覆盖
        config_data = self._apply_environment_overrides(config_data, name, context)
        
        # 应用上下文覆盖
        if context.override_values:
            config_data = self._deep_merge(config_data, context.override_values)
        
        # 配置验证
        if validate and name in self._schemas:
            schema = self._schemas[name]
            config_data = self._validator.validate(config_data, schema)
        
        # 存储配置
        self._configs[name] = config_data
        self._contexts[name] = context
        
        # 通知监听器
        self._notify_change_listeners(name, config_data)
        
        self.logger.info(f"✅ 配置加载成功: {name}")
        return config_data
    
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取已加载的配置
        
        Args:
            name: 配置名称
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据，未加载时返回None
        """
        return self._configs.get(name)
    
    def get_config_value(self, name: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            name: 配置名称
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        config = self.get_config(name)
        if config is None:
            return default
        
        # 支持嵌套键访问
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_config_value(self, name: str, key: str, value: Any):
        """
        设置配置值
        
        Args:
            name: 配置名称
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        if name not in self._configs:
            self._configs[name] = {}
        
        config = self._configs[name]
        
        # 支持嵌套键设置
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        # 通知监听器
        self._notify_change_listeners(name, config)
    
    def reload_config(self, name: str) -> Dict[str, Any]:
        """
        重新加载配置
        
        Args:
            name: 配置名称
            
        Returns:
            Dict[str, Any]: 重新加载的配置数据
        """
        if name not in self._contexts:
            raise ConfigError(f"配置 {name} 未加载，无法重新加载")
        
        context = self._contexts[name]
        return self.load_config(name, context=context)
    
    def list_configs(self) -> List[str]:
        """列出所有已加载的配置"""
        return list(self._configs.keys())
    
    def add_change_listener(self, listener: Callable[[str, Dict[str, Any]], None]):
        """
        添加配置变更监听器
        
        Args:
            listener: 监听器函数，接收配置名称和配置数据
        """
        self._change_listeners.append(listener)
        self.logger.info("📡 添加配置变更监听器")
    
    def remove_change_listener(self, listener: Callable[[str, Dict[str, Any]], None]):
        """移除配置变更监听器"""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
            self.logger.info("🗑️ 移除配置变更监听器")
    
    def _get_default_config_files(self, name: str, context: ConfigContext) -> List[Path]:
        """获取默认配置文件列表"""
        config_dir = context.config_dir
        files = []
        
        # 基础配置文件
        base_file = config_dir / f"{name}.yaml"
        if base_file.exists():
            files.append(base_file)
        
        # 环境特定配置文件
        env_file = config_dir / f"{name}.{context.environment}.yaml"
        if env_file.exists():
            files.append(env_file)
        
        # 本地配置文件 (通常不提交到版本控制)
        local_file = config_dir / f"{name}.local.yaml"
        if local_file.exists():
            files.append(local_file)
        
        if not files:
            raise ConfigNotFoundError(f"未找到配置文件: {name}")
        
        return files
    
    def _apply_environment_overrides(self, config_data: Dict[str, Any], name: str, context: ConfigContext) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        # 查找以 QTE_{NAME}_ 开头的环境变量
        prefix = f"QTE_{name.upper()}_"
        overrides = {}

        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                # 移除前缀并转换为配置键
                config_key_raw = env_key[len(prefix):]

                # 智能转换配置键：
                # 1. 如果包含双下划线，则转换为嵌套结构 (DATABASE__HOST -> database.host)
                # 2. 否则保持下划线格式 (API_KEY -> api_key)
                if '__' in config_key_raw:
                    config_key = config_key_raw.lower().replace('__', '.')
                else:
                    config_key = config_key_raw.lower()

                # 尝试类型转换
                try:
                    # 尝试解析为JSON
                    import json
                    parsed_value = json.loads(env_value)
                except json.JSONDecodeError:
                    # 作为字符串处理
                    parsed_value = env_value

                # 设置嵌套值
                self._set_nested_value(overrides, config_key, parsed_value)

        if overrides:
            config_data = self._deep_merge(config_data, overrides)
            self.logger.info(f"🌍 应用环境变量覆盖: {list(overrides.keys())}")

        return config_data
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """设置嵌套值"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _notify_change_listeners(self, name: str, config_data: Dict[str, Any]):
        """通知配置变更监听器"""
        for listener in self._change_listeners:
            try:
                listener(name, config_data)
            except Exception as e:
                self.logger.error(f"❌ 配置变更监听器执行失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取配置管理器统计信息"""
        return {
            'loaded_configs': len(self._configs),
            'registered_schemas': len(self._schemas),
            'change_listeners': len(self._change_listeners),
            'config_names': list(self._configs.keys()),
            'schema_names': list(self._schemas.keys())
        }
