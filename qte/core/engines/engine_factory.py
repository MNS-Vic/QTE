#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引擎工厂

提供统一的引擎创建和管理接口，支持V1/V2架构的无缝切换
"""

import logging
from typing import Dict, Any, Optional, Type, Union
from enum import Enum

from .unified_vector_engine import UnifiedVectorEngine
from .vector_engine_v2 import VectorEngineV2
from .vector_engine_v1_compat import VectorEngineV1Compat
from qte.core.interfaces.engine_interface import IBacktestEngine


class EngineType(Enum):
    """引擎类型枚举"""
    UNIFIED = "unified"           # 统一引擎（推荐）
    V2_PERFORMANCE = "v2"         # V2高性能引擎
    V1_COMPATIBLE = "v1"          # V1兼容引擎
    AUTO = "auto"                 # 自动选择


class EngineFactory:
    """
    引擎工厂
    
    提供统一的引擎创建接口，根据需求自动选择最适合的引擎实现
    """
    
    def __init__(self):
        """初始化引擎工厂"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 引擎注册表
        self._engine_registry = {
            EngineType.UNIFIED: UnifiedVectorEngine,
            EngineType.V2_PERFORMANCE: VectorEngineV2,
            EngineType.V1_COMPATIBLE: VectorEngineV1Compat
        }
        
        # 工厂统计
        self._stats = {
            "engines_created": 0,
            "engine_type_usage": {
                "unified": 0,
                "v2": 0,
                "v1": 0,
                "auto": 0
            },
            "auto_selections": {
                "unified": 0,
                "v2": 0,
                "v1": 0
            }
        }
        
        self.logger.info("✅ 引擎工厂初始化完成")
    
    def create_engine(self, 
                     engine_type: Union[str, EngineType] = EngineType.AUTO,
                     config: Optional[Dict[str, Any]] = None,
                     **kwargs) -> Optional[IBacktestEngine]:
        """
        创建引擎实例
        
        Parameters
        ----------
        engine_type : Union[str, EngineType], optional
            引擎类型, by default EngineType.AUTO
        config : Optional[Dict[str, Any]], optional
            引擎配置, by default None
        **kwargs
            额外配置参数
            
        Returns
        -------
        Optional[IBacktestEngine]
            引擎实例，失败时返回None
        """
        try:
            # 标准化引擎类型
            if isinstance(engine_type, str):
                engine_type = EngineType(engine_type.lower())
            
            # 合并配置
            final_config = config or {}
            final_config.update(kwargs)
            
            # 自动选择引擎类型
            if engine_type == EngineType.AUTO:
                engine_type = self._auto_select_engine_type(final_config)
                self._stats["engine_type_usage"]["auto"] += 1
                self._stats["auto_selections"][engine_type.value] += 1
            else:
                self._stats["engine_type_usage"][engine_type.value] += 1
            
            # 创建引擎实例
            engine_class = self._engine_registry.get(engine_type)
            if not engine_class:
                self.logger.error("不支持的引擎类型: %s", engine_type)
                return None
            
            # 实例化引擎
            if engine_type == EngineType.UNIFIED:
                # 统一引擎需要兼容性模式参数
                compatibility_mode = final_config.get('compatibility_mode', 'auto')
                engine = engine_class(compatibility_mode=compatibility_mode)
            else:
                engine = engine_class()

            # 初始化引擎
            if final_config:
                if engine_type == EngineType.V1_COMPATIBLE:
                    # V1兼容引擎使用不同的初始化参数
                    initial_capital = final_config.get('initial_capital', 100000)
                    commission = final_config.get('commission_rate', 0.001)
                    success = engine.initialize(initial_capital, commission)
                else:
                    success = engine.initialize(final_config)

                if not success:
                    self.logger.error("引擎初始化失败: %s", engine_type.value)
                    return None
            
            self._stats["engines_created"] += 1
            self.logger.info("✅ 引擎创建成功: %s", engine_type.value)
            
            return engine
            
        except Exception as e:
            self.logger.error("创建引擎失败: %s", e)
            return None
    
    def _auto_select_engine_type(self, config: Dict[str, Any]) -> EngineType:
        """
        自动选择引擎类型
        
        Parameters
        ----------
        config : Dict[str, Any]
            配置参数
            
        Returns
        -------
        EngineType
            选择的引擎类型
        """
        try:
            # 检查是否有V1特定配置
            v1_indicators = [
                'old_api_param', 'legacy_mode', 'v1_compatibility',
                'use_v1_api', 'compatibility_required'
            ]
            
            has_v1_config = any(key in config for key in v1_indicators)
            if has_v1_config:
                self.logger.info("检测到V1配置，选择V1兼容引擎")
                return EngineType.V1_COMPATIBLE
            
            # 检查是否明确要求高性能
            performance_indicators = [
                'high_performance', 'use_numba', 'large_dataset',
                'performance_critical', 'v2_only'
            ]
            
            needs_performance = any(key in config for key in performance_indicators)
            if needs_performance:
                self.logger.info("检测到性能需求，选择V2高性能引擎")
                return EngineType.V2_PERFORMANCE
            
            # 检查数据规模
            data_size_hint = config.get('data_size', 0)
            if data_size_hint > 100000:
                self.logger.info(f"大数据集({data_size_hint}行)，选择V2高性能引擎")
                return EngineType.V2_PERFORMANCE
            elif data_size_hint > 0 and data_size_hint < 10000:
                self.logger.info(f"小数据集({data_size_hint}行)，选择统一引擎")
                return EngineType.UNIFIED
            
            # 默认选择统一引擎
            self.logger.info("默认选择统一引擎")
            return EngineType.UNIFIED
            
        except Exception as e:
            self.logger.error("自动选择引擎类型失败: %s", e)
            return EngineType.UNIFIED
    
    def get_available_engines(self) -> Dict[str, str]:
        """
        获取可用的引擎类型
        
        Returns
        -------
        Dict[str, str]
            引擎类型和描述的映射
        """
        return {
            "unified": "统一引擎 - V1/V2架构统一，自动优化",
            "v2": "V2高性能引擎 - 基于接口的高性能实现",
            "v1": "V1兼容引擎 - 完全兼容原始API",
            "auto": "自动选择 - 根据配置自动选择最佳引擎"
        }
    
    def get_engine_recommendations(self, use_case: str) -> EngineType:
        """
        根据使用场景推荐引擎类型
        
        Parameters
        ----------
        use_case : str
            使用场景
            
        Returns
        -------
        EngineType
            推荐的引擎类型
        """
        recommendations = {
            "legacy_code": EngineType.V1_COMPATIBLE,
            "high_performance": EngineType.V2_PERFORMANCE,
            "large_dataset": EngineType.V2_PERFORMANCE,
            "small_dataset": EngineType.UNIFIED,
            "production": EngineType.UNIFIED,
            "development": EngineType.UNIFIED,
            "migration": EngineType.UNIFIED,
            "compatibility": EngineType.V1_COMPATIBLE
        }
        
        return recommendations.get(use_case.lower(), EngineType.UNIFIED)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工厂统计信息"""
        return self._stats.copy()
    
    def register_engine(self, engine_type: EngineType, engine_class: Type[IBacktestEngine]):
        """
        注册自定义引擎类型
        
        Parameters
        ----------
        engine_type : EngineType
            引擎类型
        engine_class : Type[IBacktestEngine]
            引擎类
        """
        try:
            self._engine_registry[engine_type] = engine_class
            self.logger.info("✅ 自定义引擎注册成功: %s", engine_type.value)
            
        except Exception as e:
            self.logger.error("注册自定义引擎失败: %s", e)


# 全局工厂实例
_global_factory = EngineFactory()


def create_engine(engine_type: Union[str, EngineType] = EngineType.AUTO,
                 config: Optional[Dict[str, Any]] = None,
                 **kwargs) -> Optional[IBacktestEngine]:
    """
    创建引擎实例（便捷函数）
    
    Parameters
    ----------
    engine_type : Union[str, EngineType], optional
        引擎类型, by default EngineType.AUTO
    config : Optional[Dict[str, Any]], optional
        引擎配置, by default None
    **kwargs
        额外配置参数
        
    Returns
    -------
    Optional[IBacktestEngine]
        引擎实例，失败时返回None
    """
    return _global_factory.create_engine(engine_type, config, **kwargs)


def get_available_engines() -> Dict[str, str]:
    """获取可用的引擎类型"""
    return _global_factory.get_available_engines()


def get_engine_recommendations(use_case: str) -> EngineType:
    """根据使用场景推荐引擎类型"""
    return _global_factory.get_engine_recommendations(use_case)


def get_factory_stats() -> Dict[str, Any]:
    """获取工厂统计信息"""
    return _global_factory.get_stats()
