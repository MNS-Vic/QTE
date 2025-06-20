#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一向量引擎

V1/V2架构统一后的向量引擎实现，提供：
- V2的高性能实现
- V1的兼容性接口
- 自动性能优化
- 渐进式迁移支持
"""

import logging
import warnings
from typing import Dict, List, Any

from .vector_engine_v2 import VectorEngineV2
from qte.core.interfaces.engine_interface import IBacktestEngine, BacktestResult

# 尝试导入性能优化模块
try:
    from qte.performance.numba_accelerators import NUMBA_AVAILABLE
except ImportError:
    NUMBA_AVAILABLE = False


class UnifiedVectorEngine(IBacktestEngine):
    """
    统一向量引擎
    
    集成V1和V2架构的优点，提供统一的接口和最佳性能
    """
    
    def __init__(self, compatibility_mode: str = "auto"):
        """
        初始化统一向量引擎
        
        Parameters
        ----------
        compatibility_mode : str, optional
            兼容性模式:
            - "auto": 自动选择最佳实现
            - "v1": 强制使用V1兼容模式
            - "v2": 强制使用V2高性能模式
            - "hybrid": 混合模式，根据数据规模自动切换
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.compatibility_mode = compatibility_mode
        
        # 内部使用V2引擎作为核心实现
        self._v2_engine = VectorEngineV2()
        
        # 兼容性状态
        self._v1_compatibility_enabled = False
        self._performance_mode = "v2"  # v1, v2, hybrid
        
        # 统计信息
        self._stats = {
            "engine_version": "unified",
            "performance_mode": self._performance_mode,
            "numba_available": NUMBA_AVAILABLE,
            "v1_calls": 0,
            "v2_calls": 0,
            "auto_switches": 0
        }
        
        # 根据兼容性模式初始化
        self._initialize_compatibility_mode()
        
        self.logger.info("✅ 统一向量引擎初始化完成 (模式: %s)", compatibility_mode)
    
    def _initialize_compatibility_mode(self):
        """初始化兼容性模式"""
        if self.compatibility_mode == "v1":
            self._v1_compatibility_enabled = True
            self._performance_mode = "v1"
            self.logger.info("启用V1兼容模式")
        elif self.compatibility_mode == "v2":
            self._v1_compatibility_enabled = False
            self._performance_mode = "v2"
            self.logger.info("启用V2高性能模式")
        elif self.compatibility_mode == "hybrid":
            self._v1_compatibility_enabled = True
            self._performance_mode = "hybrid"
            self.logger.info("启用混合模式")
        else:  # auto
            # 自动选择最佳模式
            if NUMBA_AVAILABLE:
                self._performance_mode = "v2"
                self.logger.info("自动选择V2高性能模式 (Numba可用)")
            else:
                self._performance_mode = "v1"
                self._v1_compatibility_enabled = True
                self.logger.info("自动选择V1兼容模式 (Numba不可用)")
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化引擎
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数
            
        Returns
        -------
        bool
            初始化是否成功
        """
        try:
            config = config or {}
            
            # 检查是否有V1特定的配置
            v1_specific_keys = ['old_api_param', 'legacy_mode', 'v1_compatibility']
            has_v1_config = any(key in config for key in v1_specific_keys)
            
            if has_v1_config and not self._v1_compatibility_enabled:
                self.logger.warning("检测到V1配置参数，启用V1兼容模式")
                self._v1_compatibility_enabled = True
                self._performance_mode = "v1"
            
            # 使用V2引擎进行初始化
            success = self._v2_engine.initialize(config)
            
            if success:
                self.logger.info("✅ 统一向量引擎初始化成功")
            else:
                self.logger.error("❌ 统一向量引擎初始化失败")
            
            return success
            
        except Exception as e:
            self.logger.error("初始化统一向量引擎失败: %s", e)
            return False
    
    def set_data(self, data) -> bool:
        """
        设置回测数据
        
        Parameters
        ----------
        data : pd.DataFrame
            回测数据
            
        Returns
        -------
        bool
            设置是否成功
        """
        try:
            # 根据数据规模自动调整性能模式
            if self._performance_mode == "hybrid":
                self._auto_adjust_performance_mode(data)
            
            # 使用V2引擎设置数据
            return self._v2_engine.set_data(data)
            
        except Exception as e:
            self.logger.error("设置数据失败: %s", e)
            return False
    
    def add_strategy(self, strategy: Any) -> bool:
        """
        添加策略
        
        Parameters
        ----------
        strategy : Any
            策略对象
            
        Returns
        -------
        bool
            添加是否成功
        """
        try:
            # 检查策略是否使用V1 API
            if self._is_v1_strategy(strategy):
                if not self._v1_compatibility_enabled:
                    self.logger.warning("检测到V1策略，启用V1兼容模式")
                    self._v1_compatibility_enabled = True
                
                self._stats["v1_calls"] += 1
                # 可以在这里添加V1策略适配逻辑
            else:
                self._stats["v2_calls"] += 1
            
            # 使用V2引擎添加策略
            return self._v2_engine.add_strategy(strategy)
            
        except Exception as e:
            self.logger.error("添加策略失败: %s", e)
            return False
    
    def run_backtest(self) -> BacktestResult:
        """
        运行回测
        
        Returns
        -------
        BacktestResult
            回测结果
        """
        try:
            # 记录性能模式使用情况
            if self._performance_mode == "v1":
                self._stats["v1_calls"] += 1
            elif self._performance_mode == "v2":
                self._stats["v2_calls"] += 1
            
            # 使用V2引擎运行回测
            result = self._v2_engine.run_backtest()
            
            # 添加统一引擎的统计信息
            if result.success and hasattr(result, 'metadata'):
                result.metadata.update({
                    'unified_engine_stats': self._stats,
                    'performance_mode': self._performance_mode,
                    'compatibility_mode': self.compatibility_mode
                })
            
            return result
            
        except Exception as e:
            self.logger.error("运行回测失败: %s", e)
            return BacktestResult(
                success=False,
                errors=["统一引擎回测失败: %s" % str(e)]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取引擎指标

        Returns
        -------
        Dict[str, Any]
            引擎指标
        """
        try:
            # 获取V2引擎指标
            v2_metrics = self._v2_engine.get_metrics()

            # 添加统一引擎特有的指标
            unified_metrics = {
                'unified_engine_version': '2.0.0',
                'compatibility_mode': self.compatibility_mode,
                'performance_mode': self._performance_mode,
                'v1_compatibility_enabled': self._v1_compatibility_enabled,
                'stats': self._stats
            }

            # 合并指标
            if hasattr(v2_metrics, '__dict__'):
                # 如果是EngineMetrics对象，转换为字典
                metrics_dict = v2_metrics.__dict__.copy()
            else:
                metrics_dict = v2_metrics.copy() if isinstance(v2_metrics, dict) else {}

            metrics_dict.update(unified_metrics)

            return metrics_dict

        except Exception as e:
            self.logger.error("获取引擎指标失败: %s", e)
            return {'error': str(e)}

    # 实现抽象方法
    def get_engine_type(self) -> str:
        """获取引擎类型"""
        return "unified_vector"

    def get_capabilities(self) -> List[str]:
        """获取引擎能力"""
        return [
            "vectorized_backtest",
            "v1_compatibility",
            "v2_performance",
            "auto_optimization",
            "hybrid_mode"
        ]

    def reset(self) -> bool:
        """重置引擎状态"""
        try:
            success = self._v2_engine.reset()

            # 重置统一引擎状态
            self._stats = {
                "engine_version": "unified",
                "performance_mode": self._performance_mode,
                "numba_available": NUMBA_AVAILABLE,
                "v1_calls": 0,
                "v2_calls": 0,
                "auto_switches": 0
            }

            self.logger.info("✅ 统一引擎已重置")
            return success

        except Exception as e:
            self.logger.error("重置统一引擎失败: %s", e)
            return False

    def cleanup(self) -> bool:
        """清理引擎资源"""
        try:
            success = self._v2_engine.cleanup()

            # 清理统一引擎资源
            self._stats.clear()

            self.logger.info("✅ 统一引擎资源已清理")
            return success

        except Exception as e:
            self.logger.error("清理统一引擎资源失败: %s", e)
            return False
    
    def _auto_adjust_performance_mode(self, data):
        """
        根据数据规模自动调整性能模式
        
        Parameters
        ----------
        data : pd.DataFrame
            数据
        """
        try:
            data_size = len(data)
            
            # 根据数据规模选择性能模式
            if data_size > 50000 and NUMBA_AVAILABLE:
                if self._performance_mode != "v2":
                    self._performance_mode = "v2"
                    self._stats["auto_switches"] += 1
                    self.logger.info(f"大数据集({data_size}行)，自动切换到V2高性能模式")
            elif data_size <= 10000:
                if self._performance_mode != "v1":
                    self._performance_mode = "v1"
                    self._stats["auto_switches"] += 1
                    self.logger.info(f"小数据集({data_size}行)，自动切换到V1兼容模式")
            
        except Exception as e:
            self.logger.error("自动调整性能模式失败: %s", e)
    
    def _is_v1_strategy(self, strategy: Any) -> bool:
        """
        检查策略是否使用V1 API
        
        Parameters
        ----------
        strategy : Any
            策略对象
            
        Returns
        -------
        bool
            是否为V1策略
        """
        try:
            # 检查V1特有的方法或属性
            v1_indicators = [
                'generate_signals',  # V1常用方法名
                'old_api_method',    # 假设的V1方法
                'legacy_attribute'   # 假设的V1属性
            ]
            
            for indicator in v1_indicators:
                if hasattr(strategy, indicator):
                    return True
            
            # 检查策略类名是否包含V1标识
            class_name = strategy.__class__.__name__.lower()
            if 'v1' in class_name or 'legacy' in class_name or 'old' in class_name:
                return True
            
            return False
            
        except Exception:
            # 如果检查失败，默认认为是V2策略
            return False
    
    # V1兼容性方法
    def set_initial_capital(self, capital: float):
        """V1兼容方法：设置初始资金"""
        if self._v1_compatibility_enabled:
            warnings.warn(
                "set_initial_capital 是V1 API，建议使用 initialize({'initial_capital': capital})",
                DeprecationWarning,
                stacklevel=2
            )
            return self.initialize({'initial_capital': capital})
        else:
            raise AttributeError("V1兼容性未启用，请使用 initialize() 方法")
    
    def get_portfolio_value(self) -> float:
        """V1兼容方法：获取组合价值"""
        if self._v1_compatibility_enabled:
            warnings.warn(
                "get_portfolio_value 是V1 API，建议使用 get_metrics()['portfolio_value']",
                DeprecationWarning,
                stacklevel=2
            )
            metrics = self.get_metrics()
            return metrics.get('portfolio_value', 0.0)
        else:
            raise AttributeError("V1兼容性未启用，请使用 get_metrics() 方法")
    
    # 属性访问兼容性
    def __getattr__(self, name: str):
        """提供V1属性访问兼容性"""
        if self._v1_compatibility_enabled:
            # 尝试从V2引擎获取属性
            if hasattr(self._v2_engine, name):
                warnings.warn(
                    f"直接访问属性 '{name}' 是V1行为，建议使用相应的方法",
                    DeprecationWarning,
                    stacklevel=2
                )
                return getattr(self._v2_engine, name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
