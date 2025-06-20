"""
配置迁移工具 - 帮助从旧配置格式迁移到新格式
"""

import logging
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from ..config_loader import ConfigLoader
from ..config_schema import ConfigSchema, ConfigValidator
from ..exceptions import ConfigError, ConfigValidationError


@dataclass
class MigrationRule:
    """迁移规则"""
    source_key: str
    target_key: str
    transformer: Optional[Callable[[Any], Any]] = None
    required: bool = False
    description: str = ""


@dataclass
class MigrationResult:
    """迁移结果"""
    success: bool
    migrated_config: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
    migration_info: Dict[str, Any]
    source_format: Optional[str] = None
    target_format: Optional[str] = None


class ConfigMigrator:
    """
    配置迁移工具
    
    帮助从旧的配置格式迁移到新的统一配置格式
    """
    
    def __init__(self):
        """初始化配置迁移器"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.loader = ConfigLoader()
        self.validator = ConfigValidator()
        
        # 预定义的迁移规则
        self._migration_rules: Dict[str, List[MigrationRule]] = {}
        self._setup_builtin_rules()
    
    def _setup_builtin_rules(self):
        """设置内置迁移规则"""
        # 演示配置迁移规则
        demo_rules = [
            MigrationRule("initial_capital", "initial_capital", description="初始资金"),
            MigrationRule("commission", "commission_rate", description="手续费率"),
            MigrationRule("symbols", "test_symbols", description="测试标的"),
            MigrationRule("period", "test_period_days", description="测试周期"),
            MigrationRule("strategy", "strategy_type", description="策略类型"),
            MigrationRule("short_ma", "short_window", description="短期窗口"),
            MigrationRule("long_ma", "long_window", description="长期窗口"),
            MigrationRule("output", "output_dir", description="输出目录"),
            MigrationRule("verbose", "verbose", description="详细输出"),
        ]
        self._migration_rules["demo"] = demo_rules
        
        # 引擎配置迁移规则
        engine_rules = [
            MigrationRule("engine", "engine_type", description="引擎类型"),
            MigrationRule("workers", "max_workers", description="工作线程数"),
            MigrationRule("batch_size", "vectorized_batch_size", description="批处理大小"),
            MigrationRule("parallel", "enable_parallel_processing", description="并行处理"),
            MigrationRule("memory_limit", "memory_limit_mb", description="内存限制"),
            MigrationRule("timeout", "event_processing_timeout", description="处理超时"),
        ]
        self._migration_rules["engine"] = engine_rules
        
        # 交易配置迁移规则
        trading_rules = [
            MigrationRule("mode", "trading_mode", description="交易模式"),
            MigrationRule("order_type", "default_order_type", description="订单类型"),
            MigrationRule("risk", "max_portfolio_risk", description="组合风险"),
            MigrationRule("position_size", "max_single_position_risk", description="持仓风险"),
            MigrationRule("stop_loss", "enable_stop_loss", description="止损"),
            MigrationRule("take_profit", "enable_take_profit", description="止盈"),
        ]
        self._migration_rules["trading"] = trading_rules
    
    def register_migration_rules(self, config_type: str, rules: List[MigrationRule]):
        """
        注册迁移规则
        
        Args:
            config_type: 配置类型
            rules: 迁移规则列表
        """
        self._migration_rules[config_type] = rules
        self.logger.info(f"📝 注册迁移规则: {config_type}, 规则数: {len(rules)}")
    
    def migrate_file(self, 
                    source_file: Path,
                    target_file: Path,
                    config_type: str,
                    target_schema: Optional[ConfigSchema] = None) -> MigrationResult:
        """
        迁移配置文件
        
        Args:
            source_file: 源配置文件
            target_file: 目标配置文件
            config_type: 配置类型
            target_schema: 目标配置模式
            
        Returns:
            MigrationResult: 迁移结果
        """
        self.logger.info(f"🔄 开始迁移配置文件: {source_file} -> {target_file}")
        
        result = MigrationResult(
            success=False,
            migrated_config={},
            warnings=[],
            errors=[],
            migration_info={
                'source_file': str(source_file),
                'target_file': str(target_file),
                'config_type': config_type,
                'migration_time': datetime.now().isoformat()
            }
        )
        
        try:
            # 加载源配置
            load_result = self.loader.load(source_file)
            source_config = load_result.data
            result.source_format = load_result.format.value

            # 设置目标格式
            if target_file.suffix.lower() in ['.yaml', '.yml']:
                result.target_format = 'yaml'
            elif target_file.suffix.lower() == '.json':
                result.target_format = 'json'
            else:
                result.target_format = 'yaml'

            # 执行迁移
            migrated_config = self._migrate_config(source_config, config_type, result)
            
            # 验证迁移后的配置
            if target_schema:
                try:
                    migrated_config = self.validator.validate(migrated_config, target_schema)
                except ConfigValidationError as e:
                    result.errors.append(f"迁移后配置验证失败: {e}")
                    return result
            
            # 保存迁移后的配置
            self._save_migrated_config(migrated_config, target_file)
            
            result.success = True
            result.migrated_config = migrated_config
            
            self.logger.info(f"✅ 配置迁移成功: {source_file}")
            
        except Exception as e:
            result.errors.append(f"迁移失败: {e}")
            self.logger.error(f"❌ 配置迁移失败: {e}")
        
        return result
    
    def migrate_config(self, 
                      source_config: Dict[str, Any],
                      config_type: str,
                      target_schema: Optional[ConfigSchema] = None) -> MigrationResult:
        """
        迁移配置数据
        
        Args:
            source_config: 源配置数据
            config_type: 配置类型
            target_schema: 目标配置模式
            
        Returns:
            MigrationResult: 迁移结果
        """
        result = MigrationResult(
            success=False,
            migrated_config={},
            warnings=[],
            errors=[],
            migration_info={
                'config_type': config_type,
                'migration_time': datetime.now().isoformat()
            }
        )
        
        try:
            # 执行迁移
            migrated_config = self._migrate_config(source_config, config_type, result)
            
            # 验证迁移后的配置
            if target_schema:
                try:
                    migrated_config = self.validator.validate(migrated_config, target_schema)
                except ConfigValidationError as e:
                    result.errors.append(f"迁移后配置验证失败: {e}")
                    return result
            
            result.success = True
            result.migrated_config = migrated_config
            
        except Exception as e:
            result.errors.append(f"迁移失败: {e}")
        
        return result
    

    
    def _migrate_config(self, 
                       source_config: Dict[str, Any], 
                       config_type: str,
                       result: MigrationResult) -> Dict[str, Any]:
        """执行配置迁移"""
        if config_type not in self._migration_rules:
            raise ConfigError(f"未找到配置类型 {config_type} 的迁移规则")
        
        rules = self._migration_rules[config_type]
        migrated_config = {}
        
        # 应用迁移规则
        for rule in rules:
            try:
                value = self._extract_value(source_config, rule.source_key)
                
                if value is not None:
                    # 应用转换器
                    if rule.transformer:
                        value = rule.transformer(value)
                    
                    # 设置目标值
                    self._set_nested_value(migrated_config, rule.target_key, value)
                    
                elif rule.required:
                    result.errors.append(f"缺少必需的配置项: {rule.source_key}")
                else:
                    result.warnings.append(f"未找到配置项: {rule.source_key}")
                    
            except Exception as e:
                result.errors.append(f"迁移规则 {rule.source_key} -> {rule.target_key} 失败: {e}")
        
        # 复制未匹配的配置项
        unmatched_keys = self._find_unmatched_keys(source_config, rules)
        for key in unmatched_keys:
            value = source_config[key]
            migrated_config[key] = value
            result.warnings.append(f"未匹配的配置项已保留: {key}")
        
        return migrated_config
    
    def _extract_value(self, config: Dict[str, Any], key: str) -> Any:
        """提取配置值，支持嵌套键"""
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """设置嵌套配置值"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _find_unmatched_keys(self, source_config: Dict[str, Any], rules: List[MigrationRule]) -> List[str]:
        """查找未匹配的配置键"""
        rule_keys = {rule.source_key.split('.')[0] for rule in rules}
        source_keys = set(source_config.keys())
        return list(source_keys - rule_keys)
    
    def _save_migrated_config(self, config: Dict[str, Any], target_file: Path):
        """保存迁移后的配置"""
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据文件扩展名选择格式
        if target_file.suffix.lower() in ['.yaml', '.yml']:
            with open(target_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        elif target_file.suffix.lower() == '.json':
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        else:
            # 默认使用YAML格式
            with open(target_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    def list_migration_types(self) -> List[str]:
        """列出可用的迁移类型"""
        return list(self._migration_rules.keys())
    
    def get_migration_rules(self, config_type: str) -> List[MigrationRule]:
        """获取指定类型的迁移规则"""
        return self._migration_rules.get(config_type, [])
    
    def validate_migration_rules(self, config_type: str) -> List[str]:
        """验证迁移规则"""
        errors = []
        
        if config_type not in self._migration_rules:
            errors.append(f"未找到配置类型: {config_type}")
            return errors
        
        rules = self._migration_rules[config_type]
        
        # 检查重复的目标键
        target_keys = [rule.target_key for rule in rules]
        duplicates = [key for key in target_keys if target_keys.count(key) > 1]
        
        if duplicates:
            errors.append(f"发现重复的目标键: {duplicates}")
        
        # 检查规则的有效性
        for rule in rules:
            if not rule.source_key:
                errors.append("发现空的源键")
            if not rule.target_key:
                errors.append("发现空的目标键")
        
        return errors


# 便捷函数
def migrate_demo_config(source_file: Path, target_file: Path) -> MigrationResult:
    """迁移演示配置的便捷函数"""
    from ..schemas.demo_schema import DemoConfigSchema

    migrator = ConfigMigrator()
    return migrator.migrate_file(source_file, target_file, "demo", DemoConfigSchema)


def migrate_engine_config(source_file: Path, target_file: Path) -> MigrationResult:
    """迁移引擎配置的便捷函数"""
    from ..schemas.engine_schema import EngineConfigSchema

    migrator = ConfigMigrator()
    return migrator.migrate_file(source_file, target_file, "engine", EngineConfigSchema)


def migrate_trading_config(source_file: Path, target_file: Path) -> MigrationResult:
    """迁移交易配置的便捷函数"""
    from ..schemas.trading_schema import TradingConfigSchema

    migrator = ConfigMigrator()
    return migrator.migrate_file(source_file, target_file, "trading", TradingConfigSchema)
