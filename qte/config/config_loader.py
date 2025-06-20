"""
配置加载器 - 支持多种格式的配置文件加载
"""

import json
import yaml
import toml
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass

from .exceptions import ConfigLoadError, ConfigFormatError, ConfigNotFoundError


class ConfigFormat(Enum):
    """配置文件格式枚举"""
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    INI = "ini"
    AUTO = "auto"  # 自动检测


@dataclass
class LoadResult:
    """配置加载结果"""
    data: Dict[str, Any]
    format: ConfigFormat
    source: str
    metadata: Dict[str, Any]


class ConfigLoader:
    """
    配置加载器
    
    支持多种配置文件格式的加载，包括：
    - YAML (.yaml, .yml)
    - JSON (.json)
    - TOML (.toml)
    - 自动格式检测
    - 环境变量替换
    - 配置合并
    """
    
    def __init__(self):
        """初始化配置加载器"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 格式处理器映射
        self._format_handlers = {
            ConfigFormat.YAML: self._load_yaml,
            ConfigFormat.JSON: self._load_json,
            ConfigFormat.TOML: self._load_toml
        }
        
        # 文件扩展名到格式的映射
        self._extension_mapping = {
            '.yaml': ConfigFormat.YAML,
            '.yml': ConfigFormat.YAML,
            '.json': ConfigFormat.JSON,
            '.toml': ConfigFormat.TOML
        }
    
    def load(self, 
             config_path: Union[str, Path], 
             format: ConfigFormat = ConfigFormat.AUTO,
             encoding: str = 'utf-8',
             expand_vars: bool = True) -> LoadResult:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            format: 配置文件格式，AUTO表示自动检测
            encoding: 文件编码
            expand_vars: 是否展开环境变量
            
        Returns:
            LoadResult: 加载结果
            
        Raises:
            ConfigNotFoundError: 配置文件不存在
            ConfigFormatError: 配置格式错误
            ConfigLoadError: 配置加载失败
        """
        config_path = Path(config_path)
        
        # 检查文件是否存在
        if not config_path.exists():
            raise ConfigNotFoundError(str(config_path))
        
        # 自动检测格式
        if format == ConfigFormat.AUTO:
            format = self._detect_format(config_path)
        
        try:
            self.logger.info(f"📖 加载配置文件: {config_path} (格式: {format.value})")
            
            # 读取文件内容
            with open(config_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 环境变量替换
            if expand_vars:
                content = self._expand_environment_variables(content)
            
            # 根据格式解析内容
            if format not in self._format_handlers:
                raise ConfigFormatError(f"不支持的配置格式: {format}")
            
            handler = self._format_handlers[format]
            data = handler(content, config_path)
            
            # 创建加载结果
            result = LoadResult(
                data=data,
                format=format,
                source=str(config_path),
                metadata={
                    'file_size': config_path.stat().st_size,
                    'modified_time': config_path.stat().st_mtime,
                    'encoding': encoding,
                    'expand_vars': expand_vars
                }
            )
            
            self.logger.info(f"✅ 配置加载成功，数据项数: {len(data)}")
            return result
            
        except Exception as e:
            if isinstance(e, (ConfigNotFoundError, ConfigFormatError)):
                raise
            else:
                raise ConfigLoadError(f"配置加载失败: {e}", str(config_path), e)
    
    def load_multiple(self, 
                     config_paths: List[Union[str, Path]],
                     merge_strategy: str = 'deep') -> LoadResult:
        """
        加载多个配置文件并合并
        
        Args:
            config_paths: 配置文件路径列表
            merge_strategy: 合并策略 ('shallow', 'deep', 'override')
            
        Returns:
            LoadResult: 合并后的加载结果
        """
        if not config_paths:
            raise ConfigLoadError("配置文件路径列表不能为空")
        
        merged_data = {}
        sources = []
        formats = []
        
        for config_path in config_paths:
            try:
                result = self.load(config_path)
                merged_data = self._merge_configs(merged_data, result.data, merge_strategy)
                sources.append(result.source)
                formats.append(result.format.value)
            except ConfigNotFoundError:
                self.logger.warning(f"⚠️ 配置文件不存在，跳过: {config_path}")
                continue
        
        if not sources:
            raise ConfigLoadError("没有成功加载任何配置文件")
        
        return LoadResult(
            data=merged_data,
            format=ConfigFormat.AUTO,  # 多文件合并
            source=f"merged({', '.join(sources)})",
            metadata={
                'source_count': len(sources),
                'sources': sources,
                'formats': formats,
                'merge_strategy': merge_strategy
            }
        )
    
    def _detect_format(self, config_path: Path) -> ConfigFormat:
        """自动检测配置文件格式"""
        extension = config_path.suffix.lower()
        
        if extension in self._extension_mapping:
            return self._extension_mapping[extension]
        
        # 如果无法从扩展名检测，尝试从内容检测
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 简单的内容检测
            if content.startswith('{') and content.endswith('}'):
                return ConfigFormat.JSON
            elif '=' in content and '[' in content:
                return ConfigFormat.TOML
            else:
                return ConfigFormat.YAML  # 默认为YAML
                
        except Exception:
            return ConfigFormat.YAML  # 默认为YAML
    
    def _load_yaml(self, content: str, config_path: Path) -> Dict[str, Any]:
        """加载YAML格式配置"""
        try:
            data = yaml.safe_load(content)
            return data if data is not None else {}
        except yaml.YAMLError as e:
            raise ConfigFormatError(f"YAML解析失败: {e}", "yaml")
    
    def _load_json(self, content: str, config_path: Path) -> Dict[str, Any]:
        """加载JSON格式配置"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ConfigFormatError(f"JSON解析失败: {e}", "json")
    
    def _load_toml(self, content: str, config_path: Path) -> Dict[str, Any]:
        """加载TOML格式配置"""
        try:
            return toml.loads(content)
        except toml.TomlDecodeError as e:
            raise ConfigFormatError(f"TOML解析失败: {e}", "toml")
    
    def _expand_environment_variables(self, content: str) -> str:
        """展开环境变量"""
        import os
        import re
        
        # 匹配 ${VAR_NAME} 或 $VAR_NAME 格式的环境变量
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))
        
        # 替换 ${VAR_NAME} 格式
        content = re.sub(r'\$\{([^}]+)\}', replace_var, content)
        
        # 替换 $VAR_NAME 格式 (单词边界)
        content = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, content)
        
        return content
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """合并配置字典"""
        if strategy == 'override':
            # 完全覆盖
            return override.copy()
        elif strategy == 'shallow':
            # 浅合并
            result = base.copy()
            result.update(override)
            return result
        elif strategy == 'deep':
            # 深度合并
            return self._deep_merge(base, override)
        else:
            raise ConfigLoadError(f"不支持的合并策略: {strategy}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
