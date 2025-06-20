"""
配置格式转换器
"""

import json
import yaml
import toml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..config_loader import ConfigLoader, ConfigFormat
from ..exceptions import ConfigFormatError, ConfigLoadError


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    source_format: ConfigFormat
    target_format: ConfigFormat
    output_file: Optional[Path] = None
    errors: list = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ConfigConverter:
    """
    配置格式转换器
    
    支持在不同配置格式之间转换：
    - YAML ↔ JSON
    - YAML ↔ TOML
    - JSON ↔ TOML
    """
    
    def __init__(self):
        """初始化配置转换器"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.loader = ConfigLoader()
        
        # 格式写入器映射
        self._format_writers = {
            ConfigFormat.YAML: self._write_yaml,
            ConfigFormat.JSON: self._write_json,
            ConfigFormat.TOML: self._write_toml
        }
    
    def convert_file(self, 
                    source_file: Path,
                    target_file: Path,
                    target_format: Optional[ConfigFormat] = None) -> ConversionResult:
        """
        转换配置文件格式
        
        Args:
            source_file: 源文件路径
            target_file: 目标文件路径
            target_format: 目标格式，None表示从文件扩展名推断
            
        Returns:
            ConversionResult: 转换结果
        """
        self.logger.info(f"🔄 开始转换配置文件: {source_file} -> {target_file}")
        
        result = ConversionResult(
            success=False,
            source_format=ConfigFormat.AUTO,
            target_format=target_format or ConfigFormat.AUTO
        )
        
        try:
            # 加载源文件
            load_result = self.loader.load(source_file)
            result.source_format = load_result.format
            
            # 确定目标格式
            if target_format is None:
                target_format = self._detect_format_from_extension(target_file)
            
            result.target_format = target_format
            
            # 验证目标格式
            if target_format not in self._format_writers:
                raise ConfigFormatError(f"不支持的目标格式: {target_format}")
            
            # 写入目标文件
            self._write_config(load_result.data, target_file, target_format)
            
            result.success = True
            result.output_file = target_file
            
            self.logger.info(f"✅ 配置转换成功: {result.source_format.value} -> {result.target_format.value}")
            
        except Exception as e:
            result.errors.append(str(e))
            self.logger.error(f"❌ 配置转换失败: {e}")
        
        return result
    
    def convert_data(self, 
                    data: Dict[str, Any],
                    source_format: ConfigFormat,
                    target_format: ConfigFormat) -> ConversionResult:
        """
        转换配置数据格式
        
        Args:
            data: 配置数据
            source_format: 源格式
            target_format: 目标格式
            
        Returns:
            ConversionResult: 转换结果
        """
        result = ConversionResult(
            success=False,
            source_format=source_format,
            target_format=target_format
        )
        
        try:
            # 验证目标格式
            if target_format not in self._format_writers:
                raise ConfigFormatError(f"不支持的目标格式: {target_format}")
            
            # 数据格式转换（主要是验证数据兼容性）
            self._validate_data_compatibility(data, target_format)
            
            result.success = True
            
            self.logger.info(f"✅ 配置数据转换验证成功: {source_format.value} -> {target_format.value}")
            
        except Exception as e:
            result.errors.append(str(e))
            self.logger.error(f"❌ 配置数据转换失败: {e}")
        
        return result
    
    def convert_string(self, 
                      content: str,
                      source_format: ConfigFormat,
                      target_format: ConfigFormat) -> tuple[bool, str, list]:
        """
        转换配置字符串格式
        
        Args:
            content: 配置内容字符串
            source_format: 源格式
            target_format: 目标格式
            
        Returns:
            tuple: (成功标志, 转换后内容, 错误列表)
        """
        errors = []
        
        try:
            # 解析源格式
            if source_format == ConfigFormat.YAML:
                data = yaml.safe_load(content)
            elif source_format == ConfigFormat.JSON:
                data = json.loads(content)
            elif source_format == ConfigFormat.TOML:
                data = toml.loads(content)
            else:
                raise ConfigFormatError(f"不支持的源格式: {source_format}")
            
            # 转换为目标格式
            if target_format == ConfigFormat.YAML:
                result_content = yaml.dump(data, default_flow_style=False, allow_unicode=True, indent=2)
            elif target_format == ConfigFormat.JSON:
                result_content = json.dumps(data, indent=2, ensure_ascii=False)
            elif target_format == ConfigFormat.TOML:
                result_content = toml.dumps(data)
            else:
                raise ConfigFormatError(f"不支持的目标格式: {target_format}")
            
            return True, result_content, errors
            
        except Exception as e:
            errors.append(str(e))
            return False, "", errors
    
    def batch_convert(self, 
                     source_dir: Path,
                     target_dir: Path,
                     source_pattern: str = "*.yaml",
                     target_format: ConfigFormat = ConfigFormat.JSON) -> Dict[str, ConversionResult]:
        """
        批量转换配置文件
        
        Args:
            source_dir: 源目录
            target_dir: 目标目录
            source_pattern: 源文件模式
            target_format: 目标格式
            
        Returns:
            Dict[str, ConversionResult]: 文件名到转换结果的映射
        """
        self.logger.info(f"🔄 开始批量转换: {source_dir} -> {target_dir}")
        
        results = {}
        source_files = list(source_dir.glob(source_pattern))
        
        if not source_files:
            self.logger.warning(f"⚠️ 未找到匹配的源文件: {source_pattern}")
            return results
        
        # 确保目标目录存在
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for source_file in source_files:
            try:
                # 生成目标文件名
                target_file = self._generate_target_filename(source_file, target_dir, target_format)
                
                # 转换文件
                result = self.convert_file(source_file, target_file, target_format)
                results[source_file.name] = result
                
            except Exception as e:
                result = ConversionResult(
                    success=False,
                    source_format=ConfigFormat.AUTO,
                    target_format=target_format,
                    errors=[str(e)]
                )
                results[source_file.name] = result
        
        success_count = sum(1 for r in results.values() if r.success)
        self.logger.info(f"✅ 批量转换完成: {success_count}/{len(results)} 成功")
        
        return results
    
    def _detect_format_from_extension(self, file_path: Path) -> ConfigFormat:
        """从文件扩展名检测格式"""
        extension = file_path.suffix.lower()
        
        if extension in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        elif extension == '.json':
            return ConfigFormat.JSON
        elif extension == '.toml':
            return ConfigFormat.TOML
        else:
            # 默认为YAML
            return ConfigFormat.YAML
    
    def _write_config(self, data: Dict[str, Any], file_path: Path, format: ConfigFormat):
        """写入配置文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        writer = self._format_writers[format]
        writer(data, file_path)
    
    def _write_yaml(self, data: Dict[str, Any], file_path: Path):
        """写入YAML格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    def _write_json(self, data: Dict[str, Any], file_path: Path):
        """写入JSON格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _write_toml(self, data: Dict[str, Any], file_path: Path):
        """写入TOML格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            toml.dump(data, f)
    
    def _validate_data_compatibility(self, data: Dict[str, Any], target_format: ConfigFormat):
        """验证数据与目标格式的兼容性"""
        if target_format == ConfigFormat.TOML:
            # TOML有一些限制，例如不支持None值
            self._validate_toml_compatibility(data)
    
    def _validate_toml_compatibility(self, data: Any, path: str = ""):
        """验证TOML兼容性"""
        if data is None:
            raise ConfigFormatError(f"TOML不支持None值: {path}")
        
        if isinstance(data, dict):
            for key, value in data.items():
                self._validate_toml_compatibility(value, f"{path}.{key}" if path else key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._validate_toml_compatibility(item, f"{path}[{i}]")
    
    def _generate_target_filename(self, source_file: Path, target_dir: Path, target_format: ConfigFormat) -> Path:
        """生成目标文件名"""
        # 移除源文件扩展名
        base_name = source_file.stem
        
        # 添加目标格式扩展名
        if target_format == ConfigFormat.YAML:
            extension = ".yaml"
        elif target_format == ConfigFormat.JSON:
            extension = ".json"
        elif target_format == ConfigFormat.TOML:
            extension = ".toml"
        else:
            extension = ".yaml"  # 默认
        
        return target_dir / f"{base_name}{extension}"
    
    def get_supported_formats(self) -> list[ConfigFormat]:
        """获取支持的格式列表"""
        return list(self._format_writers.keys())
    
    def is_format_supported(self, format: ConfigFormat) -> bool:
        """检查格式是否支持"""
        return format in self._format_writers
