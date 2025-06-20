"""
配置模式定义和验证器
"""

import logging
from typing import Dict, Any, List, Optional, Union, Type, Callable
from dataclasses import dataclass, field
from enum import Enum

from .exceptions import ConfigValidationError, ConfigSchemaError


class FieldType(Enum):
    """字段类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


@dataclass
class FieldSchema:
    """字段模式定义"""
    name: str
    type: FieldType
    required: bool = False
    default: Any = None
    description: str = ""
    
    # 验证规则
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    choices: Optional[List[Any]] = None
    
    # 嵌套模式 (用于dict和list类型)
    nested_schema: Optional['ConfigSchema'] = None
    item_type: Optional[FieldType] = None
    
    # 自定义验证器
    validator: Optional[Callable[[Any], bool]] = None
    validator_message: str = ""


class ConfigSchema:
    """
    配置模式定义
    
    定义配置的结构、类型和验证规则
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化配置模式
        
        Args:
            name: 模式名称
            description: 模式描述
        """
        self.name = name
        self.description = description
        self.fields: Dict[str, FieldSchema] = {}
        self.logger = logging.getLogger(f'{self.__class__.__name__}.{name}')
    
    def add_field(self, field: FieldSchema) -> 'ConfigSchema':
        """
        添加字段模式
        
        Args:
            field: 字段模式
            
        Returns:
            ConfigSchema: 返回自身，支持链式调用
        """
        self.fields[field.name] = field
        return self
    
    def field(self, 
              name: str,
              type: FieldType,
              required: bool = False,
              default: Any = None,
              description: str = "",
              **kwargs) -> 'ConfigSchema':
        """
        便捷方法：添加字段模式
        
        Args:
            name: 字段名
            type: 字段类型
            required: 是否必需
            default: 默认值
            description: 描述
            **kwargs: 其他验证参数
            
        Returns:
            ConfigSchema: 返回自身，支持链式调用
        """
        field_schema = FieldSchema(
            name=name,
            type=type,
            required=required,
            default=default,
            description=description,
            **kwargs
        )
        return self.add_field(field_schema)
    
    def get_field(self, name: str) -> Optional[FieldSchema]:
        """获取字段模式"""
        return self.fields.get(name)
    
    def list_fields(self) -> List[str]:
        """列出所有字段名"""
        return list(self.fields.keys())
    
    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        return [name for name, field in self.fields.items() if field.required]
    
    def get_optional_fields(self) -> List[str]:
        """获取可选字段列表"""
        return [name for name, field in self.fields.items() if not field.required]


class ConfigValidator:
    """
    配置验证器
    
    根据配置模式验证配置数据
    """
    
    def __init__(self):
        """初始化配置验证器"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 类型验证器映射
        self._type_validators = {
            FieldType.STRING: self._validate_string,
            FieldType.INTEGER: self._validate_integer,
            FieldType.FLOAT: self._validate_float,
            FieldType.BOOLEAN: self._validate_boolean,
            FieldType.LIST: self._validate_list,
            FieldType.DICT: self._validate_dict,
            FieldType.ANY: self._validate_any
        }
    
    def validate(self, data: Dict[str, Any], schema: ConfigSchema) -> Dict[str, Any]:
        """
        验证配置数据
        
        Args:
            data: 配置数据
            schema: 配置模式
            
        Returns:
            Dict[str, Any]: 验证并填充默认值后的配置数据
            
        Raises:
            ConfigValidationError: 验证失败
        """
        self.logger.info(f"🔍 开始验证配置: {schema.name}")
        
        validated_data = {}
        errors = []
        
        # 检查必需字段
        for field_name in schema.get_required_fields():
            if field_name not in data:
                errors.append(f"缺少必需字段: {field_name}")
        
        # 验证每个字段
        for field_name, field_schema in schema.fields.items():
            try:
                if field_name in data:
                    # 验证提供的值
                    validated_value = self._validate_field(data[field_name], field_schema)
                    validated_data[field_name] = validated_value
                elif field_schema.default is not None:
                    # 使用默认值
                    validated_data[field_name] = field_schema.default
                elif field_schema.required:
                    # 必需字段但未提供值
                    errors.append(f"必需字段 {field_name} 未提供值")
                
            except ConfigValidationError as e:
                errors.append(f"字段 {field_name}: {e}")
        
        # 检查未知字段
        unknown_fields = set(data.keys()) - set(schema.fields.keys())
        if unknown_fields:
            self.logger.warning(f"⚠️ 发现未知字段: {unknown_fields}")
            # 保留未知字段，但记录警告
            for field_name in unknown_fields:
                validated_data[field_name] = data[field_name]
        
        # 如果有验证错误，抛出异常
        if errors:
            error_message = "; ".join(errors)
            raise ConfigValidationError(f"配置验证失败: {error_message}")
        
        self.logger.info(f"✅ 配置验证成功: {schema.name}")
        return validated_data
    
    def _validate_field(self, value: Any, field_schema: FieldSchema) -> Any:
        """验证单个字段"""
        # 类型验证
        if field_schema.type in self._type_validators:
            validator = self._type_validators[field_schema.type]
            validated_value = validator(value, field_schema)
        else:
            raise ConfigValidationError(f"不支持的字段类型: {field_schema.type}")
        
        # 自定义验证器
        if field_schema.validator:
            if not field_schema.validator(validated_value):
                message = field_schema.validator_message or "自定义验证失败"
                raise ConfigValidationError(message, field_schema.name, validated_value)
        
        return validated_value
    
    def _validate_string(self, value: Any, field_schema: FieldSchema) -> str:
        """验证字符串类型"""
        if not isinstance(value, str):
            raise ConfigValidationError(f"期望字符串类型，得到 {type(value).__name__}")
        
        # 长度验证
        if field_schema.min_length is not None and len(value) < field_schema.min_length:
            raise ConfigValidationError(f"字符串长度不能少于 {field_schema.min_length}")
        
        if field_schema.max_length is not None and len(value) > field_schema.max_length:
            raise ConfigValidationError(f"字符串长度不能超过 {field_schema.max_length}")
        
        # 模式验证
        if field_schema.pattern:
            import re
            if not re.match(field_schema.pattern, value):
                raise ConfigValidationError(f"字符串不匹配模式: {field_schema.pattern}")
        
        # 选择验证
        if field_schema.choices and value not in field_schema.choices:
            raise ConfigValidationError(f"值必须是以下之一: {field_schema.choices}")
        
        return value
    
    def _validate_integer(self, value: Any, field_schema: FieldSchema) -> int:
        """验证整数类型"""
        if isinstance(value, bool):
            raise ConfigValidationError("布尔值不能作为整数")
        
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ConfigValidationError(f"无法转换为整数: {value}")
        
        # 范围验证
        if field_schema.min_value is not None and value < field_schema.min_value:
            raise ConfigValidationError(f"值不能小于 {field_schema.min_value}")
        
        if field_schema.max_value is not None and value > field_schema.max_value:
            raise ConfigValidationError(f"值不能大于 {field_schema.max_value}")
        
        # 选择验证
        if field_schema.choices and value not in field_schema.choices:
            raise ConfigValidationError(f"值必须是以下之一: {field_schema.choices}")
        
        return value
    
    def _validate_float(self, value: Any, field_schema: FieldSchema) -> float:
        """验证浮点数类型"""
        if isinstance(value, bool):
            raise ConfigValidationError("布尔值不能作为浮点数")
        
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ConfigValidationError(f"无法转换为浮点数: {value}")
        
        # 范围验证
        if field_schema.min_value is not None and value < field_schema.min_value:
            raise ConfigValidationError(f"值不能小于 {field_schema.min_value}")
        
        if field_schema.max_value is not None and value > field_schema.max_value:
            raise ConfigValidationError(f"值不能大于 {field_schema.max_value}")
        
        return float(value)
    
    def _validate_boolean(self, value: Any, field_schema: FieldSchema) -> bool:
        """验证布尔类型"""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ('true', 'yes', '1', 'on'):
                return True
            elif lower_value in ('false', 'no', '0', 'off'):
                return False
        
        raise ConfigValidationError(f"无法转换为布尔值: {value}")
    
    def _validate_list(self, value: Any, field_schema: FieldSchema) -> List[Any]:
        """验证列表类型"""
        if not isinstance(value, list):
            raise ConfigValidationError(f"期望列表类型，得到 {type(value).__name__}")
        
        # 长度验证
        if field_schema.min_length is not None and len(value) < field_schema.min_length:
            raise ConfigValidationError(f"列表长度不能少于 {field_schema.min_length}")
        
        if field_schema.max_length is not None and len(value) > field_schema.max_length:
            raise ConfigValidationError(f"列表长度不能超过 {field_schema.max_length}")
        
        # 元素类型验证
        if field_schema.item_type:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    item_field = FieldSchema(f"item_{i}", field_schema.item_type)
                    validated_item = self._validate_field(item, item_field)
                    validated_items.append(validated_item)
                except ConfigValidationError as e:
                    raise ConfigValidationError(f"列表元素 {i}: {e}")
            return validated_items
        
        return value
    
    def _validate_dict(self, value: Any, field_schema: FieldSchema) -> Dict[str, Any]:
        """验证字典类型"""
        if not isinstance(value, dict):
            raise ConfigValidationError(f"期望字典类型，得到 {type(value).__name__}")
        
        # 嵌套模式验证
        if field_schema.nested_schema:
            return self.validate(value, field_schema.nested_schema)
        
        return value
    
    def _validate_any(self, value: Any, field_schema: FieldSchema) -> Any:
        """验证任意类型"""
        return value
