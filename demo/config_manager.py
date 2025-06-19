"""
QTE演示系统配置管理器
提供统一的配置加载、验证、默认值处理机制
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
import copy


@dataclass
class DemoConfig:
    """演示配置数据类"""
    
    # 全局配置
    global_config: Dict[str, Any] = field(default_factory=dict)
    
    # 各演示模式配置
    simple_config: Dict[str, Any] = field(default_factory=dict)
    advanced_config: Dict[str, Any] = field(default_factory=dict)
    exchange_config: Dict[str, Any] = field(default_factory=dict)
    ml_config: Dict[str, Any] = field(default_factory=dict)
    vnpy_config: Dict[str, Any] = field(default_factory=dict)
    datasource_config: Dict[str, Any] = field(default_factory=dict)
    report_config: Dict[str, Any] = field(default_factory=dict)
    comprehensive_config: Dict[str, Any] = field(default_factory=dict)
    test_config: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger('ConfigManager')
        self.config_file = config_file or 'demo_config.yaml'
        self.config_dir = Path('demo_config')
        self.config_path = self.config_dir / self.config_file
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = self._get_default_config()
        
        # 当前配置
        self.config = DemoConfig()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'global': {
                'initial_capital': 100000.0,
                'test_symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'],
                'test_period_days': 30,
                'data_frequency': '1d',
                'timezone': 'UTC',
                'random_seed': 42,
                'log_level': 'INFO',
                'output_dir': 'demo_output',
                'reports_dir': 'demo_reports',
                'data_dir': 'demo_data'
            },
            'simple': {
                'strategy_type': 'moving_average',
                'short_window': 10,
                'long_window': 30,
                'commission': 0.001,
                'slippage': 0.0001
            },
            'advanced': {
                'strategies': ['momentum', 'mean_reversion'],
                'risk_management': {
                    'max_position_size': 0.1,
                    'stop_loss': 0.05,
                    'take_profit': 0.1
                },
                'portfolio': {
                    'rebalance_frequency': 'weekly',
                    'max_weights': 0.2
                }
            },
            'exchange': {
                'rest_port': 5001,
                'websocket_port': 8766,
                'matching_engine': {
                    'tick_size': 0.01,
                    'lot_size': 1.0
                },
                'market_data': {
                    'update_frequency': 1.0,
                    'price_volatility': 0.02
                }
            },
            'ml': {
                'models': ['random_forest', 'gradient_boosting'],
                'features': {
                    'technical_indicators': True,
                    'price_features': True,
                    'volume_features': True,
                    'lookback_periods': [5, 10, 20]
                },
                'training': {
                    'test_size': 0.2,
                    'cv_folds': 5,
                    'random_state': 42
                }
            },
            'vnpy': {
                'gateway_name': 'QTE_GATEWAY',
                'event_engine': {
                    'timer_interval': 1.0,
                    'max_queue_size': 1000
                },
                'trading': {
                    'order_timeout': 30,
                    'max_orders_per_second': 10
                }
            },
            'datasource': {
                'sources': ['local_csv', 'gm_quant', 'binance_api'],
                'performance_test': {
                    'timeout': 30,
                    'retry_count': 3
                },
                'quality_check': {
                    'missing_data_threshold': 0.05,
                    'outlier_std_threshold': 3.0
                }
            },
            'report': {
                'theme': 'dark',
                'charts': ['trades_comparison', 'returns_curve', 'coverage_radar'],
                'export_formats': ['html', 'json'],
                'interactive': True
            },
            'comprehensive': {
                'run_all_demos': True,
                'continue_on_error': True,
                'generate_summary': True,
                'timeout_per_demo': 300
            },
            'test': {
                'test_suites': ['data_generation', 'strategy_function', 'risk_management', 'config_loading'],
                'cleanup_after_test': True,
                'verbose_output': True
            }
        }
    
    def create_default_config_file(self) -> bool:
        """创建默认配置文件"""
        try:
            self.logger.info(f"📝 创建默认配置文件: {self.config_path}")
            
            # 添加配置文件说明
            config_with_comments = {
                '_description': 'QTE演示系统配置文件',
                '_version': '1.0.0',
                '_created': 'auto-generated',
                '_usage': '使用 --config 参数指定配置文件，或修改此默认配置',
                **self.default_config
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_with_comments, f, default_flow_style=False, 
                         allow_unicode=True, indent=2, sort_keys=False)
            
            self.logger.info(f"✅ 默认配置文件已创建: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建配置文件失败: {e}")
            return False
    
    def load_config(self, config_file: Optional[str] = None) -> DemoConfig:
        """加载配置文件"""
        if config_file:
            config_path = Path(config_file)
        else:
            config_path = self.config_path
        
        try:
            # 如果配置文件不存在，创建默认配置
            if not config_path.exists():
                self.logger.info(f"📄 配置文件不存在，创建默认配置: {config_path}")
                if config_path == self.config_path:
                    self.create_default_config_file()
                else:
                    # 如果是自定义路径，复制默认配置
                    config_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(self.default_config, f, default_flow_style=False, 
                                 allow_unicode=True, indent=2)
            
            # 加载配置文件
            self.logger.info(f"📖 加载配置文件: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f) or {}
            
            # 合并默认配置和加载的配置
            merged_config = self._merge_configs(self.default_config, loaded_config)
            
            # 验证配置
            validated_config = self._validate_config(merged_config)
            
            # 应用环境变量覆盖
            final_config = self._apply_env_overrides(validated_config)
            
            # 创建配置对象
            self.config = DemoConfig(
                global_config=final_config.get('global', {}),
                simple_config=final_config.get('simple', {}),
                advanced_config=final_config.get('advanced', {}),
                exchange_config=final_config.get('exchange', {}),
                ml_config=final_config.get('ml', {}),
                vnpy_config=final_config.get('vnpy', {}),
                datasource_config=final_config.get('datasource', {}),
                report_config=final_config.get('report', {}),
                comprehensive_config=final_config.get('comprehensive', {}),
                test_config=final_config.get('test', {})
            )
            
            self.logger.info("✅ 配置加载完成")
            return self.config
            
        except Exception as e:
            self.logger.error(f"❌ 配置加载失败: {e}")
            self.logger.info("🔄 使用默认配置")
            
            # 使用默认配置
            self.config = DemoConfig(
                global_config=self.default_config.get('global', {}),
                simple_config=self.default_config.get('simple', {}),
                advanced_config=self.default_config.get('advanced', {}),
                exchange_config=self.default_config.get('exchange', {}),
                ml_config=self.default_config.get('ml', {}),
                vnpy_config=self.default_config.get('vnpy', {}),
                datasource_config=self.default_config.get('datasource', {}),
                report_config=self.default_config.get('report', {}),
                comprehensive_config=self.default_config.get('comprehensive', {}),
                test_config=self.default_config.get('test', {})
            )
            
            return self.config

    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置字典"""
        merged = copy.deepcopy(default)

        for key, value in loaded.items():
            if key.startswith('_'):  # 跳过元数据字段
                continue

            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置参数"""
        validated = copy.deepcopy(config)

        try:
            # 验证全局配置
            global_config = validated.get('global', {})

            # 验证初始资金
            if 'initial_capital' in global_config:
                capital = global_config['initial_capital']
                if not isinstance(capital, (int, float)) or capital <= 0:
                    self.logger.warning(f"⚠️ 无效的初始资金: {capital}，使用默认值")
                    global_config['initial_capital'] = self.default_config['global']['initial_capital']

            # 验证测试周期
            if 'test_period_days' in global_config:
                days = global_config['test_period_days']
                if not isinstance(days, int) or days <= 0:
                    self.logger.warning(f"⚠️ 无效的测试周期: {days}，使用默认值")
                    global_config['test_period_days'] = self.default_config['global']['test_period_days']

            # 验证测试标的
            if 'test_symbols' in global_config:
                symbols = global_config['test_symbols']
                if not isinstance(symbols, list) or len(symbols) == 0:
                    self.logger.warning(f"⚠️ 无效的测试标的: {symbols}，使用默认值")
                    global_config['test_symbols'] = self.default_config['global']['test_symbols']

            # 验证交易所配置
            exchange_config = validated.get('exchange', {})
            if 'rest_port' in exchange_config:
                port = exchange_config['rest_port']
                if not isinstance(port, int) or port < 1024 or port > 65535:
                    self.logger.warning(f"⚠️ 无效的REST端口: {port}，使用默认值")
                    exchange_config['rest_port'] = self.default_config['exchange']['rest_port']

            if 'websocket_port' in exchange_config:
                port = exchange_config['websocket_port']
                if not isinstance(port, int) or port < 1024 or port > 65535:
                    self.logger.warning(f"⚠️ 无效的WebSocket端口: {port}，使用默认值")
                    exchange_config['websocket_port'] = self.default_config['exchange']['websocket_port']

            # 验证ML配置
            ml_config = validated.get('ml', {})
            if 'training' in ml_config and 'test_size' in ml_config['training']:
                test_size = ml_config['training']['test_size']
                if not isinstance(test_size, (int, float)) or test_size <= 0 or test_size >= 1:
                    self.logger.warning(f"⚠️ 无效的测试集比例: {test_size}，使用默认值")
                    ml_config['training']['test_size'] = self.default_config['ml']['training']['test_size']

            self.logger.info("✅ 配置验证完成")

        except Exception as e:
            self.logger.error(f"❌ 配置验证失败: {e}")

        return validated

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        overridden = copy.deepcopy(config)

        try:
            # 支持的环境变量映射
            env_mappings = {
                'QTE_INITIAL_CAPITAL': ('global', 'initial_capital', float),
                'QTE_TEST_PERIOD_DAYS': ('global', 'test_period_days', int),
                'QTE_LOG_LEVEL': ('global', 'log_level', str),
                'QTE_REST_PORT': ('exchange', 'rest_port', int),
                'QTE_WEBSOCKET_PORT': ('exchange', 'websocket_port', int),
                'QTE_OUTPUT_DIR': ('global', 'output_dir', str),
                'QTE_REPORTS_DIR': ('global', 'reports_dir', str),
                'QTE_DATA_DIR': ('global', 'data_dir', str)
            }

            for env_var, (section, key, value_type) in env_mappings.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    try:
                        # 类型转换
                        if value_type == bool:
                            converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            converted_value = value_type(env_value)

                        # 应用覆盖
                        if section not in overridden:
                            overridden[section] = {}
                        overridden[section][key] = converted_value

                        self.logger.info(f"🔧 环境变量覆盖: {env_var} = {converted_value}")

                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"⚠️ 环境变量类型转换失败: {env_var} = {env_value}, {e}")

        except Exception as e:
            self.logger.error(f"❌ 环境变量覆盖失败: {e}")

        return overridden

    def get_demo_config(self, demo_mode: str) -> Dict[str, Any]:
        """获取指定演示模式的配置"""
        # 获取全局配置
        global_config = self.config.global_config.copy()

        # 获取演示模式特定配置
        demo_configs = {
            'simple': self.config.simple_config,
            'advanced': self.config.advanced_config,
            'exchange': self.config.exchange_config,
            'ml': self.config.ml_config,
            'vnpy': self.config.vnpy_config,
            'datasource': self.config.datasource_config,
            'report': self.config.report_config,
            'all': self.config.comprehensive_config,
            'comprehensive': self.config.comprehensive_config,
            'test': self.config.test_config
        }

        demo_specific_config = demo_configs.get(demo_mode, {}).copy()

        # 合并全局配置和演示特定配置
        merged_config = {**global_config, **demo_specific_config}

        return merged_config

    def update_config(self, section: str, key: str, value: Any) -> bool:
        """更新配置值"""
        try:
            config_attrs = {
                'global': 'global_config',
                'simple': 'simple_config',
                'advanced': 'advanced_config',
                'exchange': 'exchange_config',
                'ml': 'ml_config',
                'vnpy': 'vnpy_config',
                'datasource': 'datasource_config',
                'report': 'report_config',
                'comprehensive': 'comprehensive_config',
                'test': 'test_config'
            }

            if section in config_attrs:
                config_dict = getattr(self.config, config_attrs[section])
                config_dict[key] = value
                self.logger.info(f"🔧 配置已更新: {section}.{key} = {value}")
                return True
            else:
                self.logger.warning(f"⚠️ 未知的配置段: {section}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 配置更新失败: {e}")
            return False

    def save_config(self, config_file: Optional[str] = None) -> bool:
        """保存当前配置到文件"""
        if config_file:
            config_path = Path(config_file)
        else:
            config_path = self.config_path

        try:
            # 构建配置字典
            config_dict = {
                '_description': 'QTE演示系统配置文件',
                '_version': '1.0.0',
                '_last_updated': 'auto-saved',
                'global': self.config.global_config,
                'simple': self.config.simple_config,
                'advanced': self.config.advanced_config,
                'exchange': self.config.exchange_config,
                'ml': self.config.ml_config,
                'vnpy': self.config.vnpy_config,
                'datasource': self.config.datasource_config,
                'report': self.config.report_config,
                'comprehensive': self.config.comprehensive_config,
                'test': self.config.test_config
            }

            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False,
                         allow_unicode=True, indent=2, sort_keys=False)

            self.logger.info(f"✅ 配置已保存: {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 配置保存失败: {e}")
            return False


# 全局配置管理器实例
_config_manager = None

def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None or config_file is not None:
        _config_manager = ConfigManager(config_file)
        _config_manager.load_config()
    return _config_manager

def get_demo_config(demo_mode: str, config_file: Optional[str] = None) -> Dict[str, Any]:
    """获取演示模式配置的便捷函数"""
    manager = get_config_manager(config_file)
    return manager.get_demo_config(demo_mode)
