"""
配置验证工具
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config_loader import ConfigLoader
from ..config_schema import ConfigSchema, ConfigValidator
from ..exceptions import ConfigValidationError, ConfigLoadError


@dataclass
class ValidationIssue:
    """验证问题"""
    level: str  # 'error', 'warning', 'info'
    field: Optional[str]
    message: str
    value: Any = None


@dataclass
class ValidationReport:
    """验证报告"""
    config_name: str
    success: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_config: Optional[Dict[str, Any]] = None
    
    def add_error(self, message: str, field: str = None, value: Any = None):
        """添加错误"""
        self.issues.append(ValidationIssue("error", field, message, value))
        self.success = False
    
    def add_warning(self, message: str, field: str = None, value: Any = None):
        """添加警告"""
        self.issues.append(ValidationIssue("warning", field, message, value))
    
    def add_info(self, message: str, field: str = None, value: Any = None):
        """添加信息"""
        self.issues.append(ValidationIssue("info", field, message, value))
    
    def get_errors(self) -> List[ValidationIssue]:
        """获取错误列表"""
        return [issue for issue in self.issues if issue.level == "error"]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """获取警告列表"""
        return [issue for issue in self.issues if issue.level == "warning"]
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return any(issue.level == "error" for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return any(issue.level == "warning" for issue in self.issues)


class ConfigValidatorTool:
    """
    配置验证工具
    
    提供配置文件和配置数据的验证功能
    """
    
    def __init__(self):
        """初始化配置验证工具"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.loader = ConfigLoader()
        self.validator = ConfigValidator()
        
        # 注册的配置模式
        self._schemas: Dict[str, ConfigSchema] = {}
    
    def register_schema(self, name: str, schema: ConfigSchema):
        """
        注册配置模式
        
        Args:
            name: 模式名称
            schema: 配置模式
        """
        self._schemas[name] = schema
        self.logger.info(f"📋 注册配置模式: {name}")
    
    def validate_file(self, 
                     config_file: Path,
                     schema_name: str,
                     schema: Optional[ConfigSchema] = None) -> ValidationReport:
        """
        验证配置文件
        
        Args:
            config_file: 配置文件路径
            schema_name: 模式名称
            schema: 配置模式，None表示使用注册的模式
            
        Returns:
            ValidationReport: 验证报告
        """
        self.logger.info(f"🔍 验证配置文件: {config_file}")
        
        report = ValidationReport(config_name=str(config_file), success=True)
        
        try:
            # 加载配置文件
            load_result = self.loader.load(config_file)
            config_data = load_result.data
            
            # 获取配置模式
            if schema is None:
                if schema_name not in self._schemas:
                    report.add_error(f"未找到配置模式: {schema_name}")
                    return report
                schema = self._schemas[schema_name]
            
            # 验证配置
            validated_config = self.validator.validate(config_data, schema)
            report.validated_config = validated_config
            
            # 检查配置完整性
            self._check_config_completeness(config_data, schema, report)
            
            # 检查配置最佳实践
            self._check_best_practices(config_data, schema, report)
            
            self.logger.info(f"✅ 配置验证完成: {config_file}")
            
        except ConfigLoadError as e:
            report.add_error(f"配置加载失败: {e}")
        except ConfigValidationError as e:
            report.add_error(f"配置验证失败: {e}")
        except Exception as e:
            report.add_error(f"验证过程异常: {e}")
        
        return report
    
    def validate_data(self, 
                     config_data: Dict[str, Any],
                     schema_name: str,
                     schema: Optional[ConfigSchema] = None) -> ValidationReport:
        """
        验证配置数据
        
        Args:
            config_data: 配置数据
            schema_name: 模式名称
            schema: 配置模式，None表示使用注册的模式
            
        Returns:
            ValidationReport: 验证报告
        """
        report = ValidationReport(config_name=schema_name, success=True)
        
        try:
            # 获取配置模式
            if schema is None:
                if schema_name not in self._schemas:
                    report.add_error(f"未找到配置模式: {schema_name}")
                    return report
                schema = self._schemas[schema_name]
            
            # 验证配置
            validated_config = self.validator.validate(config_data, schema)
            report.validated_config = validated_config
            
            # 检查配置完整性
            self._check_config_completeness(config_data, schema, report)
            
            # 检查配置最佳实践
            self._check_best_practices(config_data, schema, report)
            
        except ConfigValidationError as e:
            report.add_error(f"配置验证失败: {e}")
        except Exception as e:
            report.add_error(f"验证过程异常: {e}")
        
        return report
    
    def validate_directory(self, 
                          config_dir: Path,
                          schema_mapping: Dict[str, str],
                          file_pattern: str = "*.yaml") -> Dict[str, ValidationReport]:
        """
        验证目录中的配置文件
        
        Args:
            config_dir: 配置目录
            schema_mapping: 文件名到模式名的映射
            file_pattern: 文件模式
            
        Returns:
            Dict[str, ValidationReport]: 文件名到验证报告的映射
        """
        self.logger.info(f"🔍 验证配置目录: {config_dir}")
        
        reports = {}
        config_files = list(config_dir.glob(file_pattern))
        
        if not config_files:
            self.logger.warning(f"⚠️ 未找到配置文件: {file_pattern}")
            return reports
        
        for config_file in config_files:
            file_key = config_file.stem  # 不包含扩展名的文件名
            
            if file_key in schema_mapping:
                schema_name = schema_mapping[file_key]
                report = self.validate_file(config_file, schema_name)
                reports[config_file.name] = report
            else:
                # 创建一个报告表示未找到对应的模式
                report = ValidationReport(config_name=str(config_file), success=False)
                report.add_warning(f"未找到对应的配置模式: {file_key}")
                reports[config_file.name] = report
        
        success_count = sum(1 for r in reports.values() if r.success)
        self.logger.info(f"✅ 目录验证完成: {success_count}/{len(reports)} 成功")
        
        return reports
    
    def generate_sample_config(self, schema_name: str, schema: Optional[ConfigSchema] = None) -> Dict[str, Any]:
        """
        生成示例配置
        
        Args:
            schema_name: 模式名称
            schema: 配置模式，None表示使用注册的模式
            
        Returns:
            Dict[str, Any]: 示例配置数据
        """
        if schema is None:
            if schema_name not in self._schemas:
                raise ValueError(f"未找到配置模式: {schema_name}")
            schema = self._schemas[schema_name]
        
        sample_config = {}
        
        for field_name, field_schema in schema.fields.items():
            if field_schema.default is not None:
                sample_config[field_name] = field_schema.default
            else:
                # 根据类型生成示例值
                sample_config[field_name] = self._generate_sample_value(field_schema)
        
        return sample_config
    
    def _check_config_completeness(self, config_data: Dict[str, Any], schema: ConfigSchema, report: ValidationReport):
        """检查配置完整性"""
        # 检查是否有推荐但非必需的字段缺失
        for field_name, field_schema in schema.fields.items():
            if not field_schema.required and field_name not in config_data:
                if field_schema.description:
                    report.add_info(f"可选字段 '{field_name}' 未配置: {field_schema.description}")
    
    def _check_best_practices(self, config_data: Dict[str, Any], schema: ConfigSchema, report: ValidationReport):
        """检查配置最佳实践"""
        # 检查敏感信息
        sensitive_patterns = ['password', 'secret', 'key', 'token']
        
        for key, value in config_data.items():
            if isinstance(value, str):
                key_lower = key.lower()
                if any(pattern in key_lower for pattern in sensitive_patterns):
                    if value and not value.startswith('${'):  # 不是环境变量
                        report.add_warning(f"敏感信息 '{key}' 建议使用环境变量", key, "***")
        
        # 检查数值范围的合理性
        self._check_value_reasonableness(config_data, report)
    
    def _check_value_reasonableness(self, config_data: Dict[str, Any], report: ValidationReport):
        """检查数值合理性"""
        # 检查一些常见的配置项
        if 'initial_capital' in config_data:
            capital = config_data['initial_capital']
            if isinstance(capital, (int, float)):
                if capital < 1000:
                    report.add_warning("初始资金过小，可能影响回测结果", 'initial_capital', capital)
                elif capital > 10000000:
                    report.add_warning("初始资金过大，请确认是否正确", 'initial_capital', capital)
        
        if 'commission_rate' in config_data:
            commission = config_data['commission_rate']
            if isinstance(commission, (int, float)):
                if commission > 0.01:  # 1%
                    report.add_warning("手续费率过高，请确认是否正确", 'commission_rate', commission)
    
    def _generate_sample_value(self, field_schema):
        """生成示例值"""
        from ..config_schema import FieldType
        
        if field_schema.type == FieldType.STRING:
            if field_schema.choices:
                return field_schema.choices[0]
            return "example_string"
        elif field_schema.type == FieldType.INTEGER:
            if field_schema.min_value is not None:
                return field_schema.min_value
            return 42
        elif field_schema.type == FieldType.FLOAT:
            if field_schema.min_value is not None:
                return float(field_schema.min_value)
            return 3.14
        elif field_schema.type == FieldType.BOOLEAN:
            return True
        elif field_schema.type == FieldType.LIST:
            return []
        elif field_schema.type == FieldType.DICT:
            return {}
        else:
            return None
    
    def list_schemas(self) -> List[str]:
        """列出已注册的配置模式"""
        return list(self._schemas.keys())
    
    def get_schema(self, name: str) -> Optional[ConfigSchema]:
        """获取配置模式"""
        return self._schemas.get(name)
    
    def print_report(self, report: ValidationReport):
        """打印验证报告"""
        print(f"\n📋 配置验证报告: {report.config_name}")
        print(f"状态: {'✅ 成功' if report.success else '❌ 失败'}")
        
        if report.get_errors():
            print("\n❌ 错误:")
            for issue in report.get_errors():
                field_info = f" [{issue.field}]" if issue.field else ""
                print(f"  - {issue.message}{field_info}")
        
        if report.get_warnings():
            print("\n⚠️ 警告:")
            for issue in report.get_warnings():
                field_info = f" [{issue.field}]" if issue.field else ""
                print(f"  - {issue.message}{field_info}")
        
        info_issues = [issue for issue in report.issues if issue.level == "info"]
        if info_issues:
            print("\nℹ️ 信息:")
            for issue in info_issues:
                field_info = f" [{issue.field}]" if issue.field else ""
                print(f"  - {issue.message}{field_info}")
        
        print()  # 空行
