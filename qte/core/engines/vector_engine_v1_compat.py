#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V1向量引擎兼容层

提供与原始vector_engine.py完全兼容的接口，内部使用V2引擎实现
"""

import logging
import warnings
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from .vector_engine_v2 import VectorEngineV2
from qte.core.interfaces.engine_interface import BacktestResult


class VectorEngineV1Compat:
    """
    V1向量引擎兼容层
    
    提供与原始VectorEngine完全兼容的接口，内部使用V2引擎实现
    确保现有V1代码无需修改即可运行
    """
    
    def __init__(self):
        """初始化V1兼容引擎"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 内部使用V2引擎
        self._v2_engine = VectorEngineV2()
        
        # V1兼容性状态
        self._initialized = False
        self._data = None
        self._strategies = []
        self._initial_capital = 100000.0
        self._commission = 0.001
        
        # V1特有属性（兼容性）
        self.portfolio_value = self._initial_capital
        self.positions = {}
        self.trades = []
        self.signals = []
        
        # 统计信息
        self._compat_stats = {
            "v1_method_calls": 0,
            "deprecated_warnings": 0,
            "compatibility_mode": "v1_full"
        }
        
        self.logger.info("✅ V1兼容向量引擎初始化完成")
    
    def initialize(self, initial_capital: float = 100000.0, 
                  commission: float = 0.001, **kwargs) -> bool:
        """
        初始化引擎（V1兼容接口）
        
        Parameters
        ----------
        initial_capital : float, optional
            初始资金, by default 100000.0
        commission : float, optional
            手续费率, by default 0.001
        **kwargs
            其他参数
            
        Returns
        -------
        bool
            初始化是否成功
        """
        try:
            self._initial_capital = initial_capital
            self._commission = commission
            self.portfolio_value = initial_capital
            
            # 转换为V2配置格式
            v2_config = {
                'initial_capital': initial_capital,
                'commission': commission,
                'compatibility_mode': 'v1',
                **kwargs
            }
            
            # 使用V2引擎初始化
            success = self._v2_engine.initialize(v2_config)
            
            if success:
                self._initialized = True
                self.logger.info("✅ V1兼容引擎初始化成功 (资金: %.2f)" % initial_capital)
            else:
                self.logger.error("❌ V1兼容引擎初始化失败")
            
            self._compat_stats["v1_method_calls"] += 1
            return success
            
        except Exception as e:
            self.logger.error(f"V1兼容引擎初始化失败: {e}")
            return False
    
    def set_data(self, data: pd.DataFrame) -> bool:
        """
        设置回测数据（V1兼容接口）
        
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
            self._data = data
            
            # 使用V2引擎设置数据
            success = self._v2_engine.set_data(data)
            
            if success:
                self.logger.info("✅ 数据设置成功 (%d 行)" % len(data))
            else:
                self.logger.error("❌ 数据设置失败")
            
            self._compat_stats["v1_method_calls"] += 1
            return success
            
        except Exception as e:
            self.logger.error(f"设置数据失败: {e}")
            return False
    
    def add_strategy(self, strategy: Any) -> bool:
        """
        添加策略（V1兼容接口）
        
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
            self._strategies.append(strategy)
            
            # 使用V2引擎添加策略
            success = self._v2_engine.add_strategy(strategy)
            
            if success:
                self.logger.info("✅ 策略添加成功: %s" % strategy.__class__.__name__)
            else:
                self.logger.error("❌ 策略添加失败: %s" % strategy.__class__.__name__)
            
            self._compat_stats["v1_method_calls"] += 1
            return success
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    def run_backtest(self) -> Dict[str, Any]:
        """
        运行回测（V1兼容接口）
        
        Returns
        -------
        Dict[str, Any]
            回测结果（V1格式）
        """
        try:
            if not self._initialized:
                self.logger.error("引擎未初始化")
                return {"success": False, "error": "引擎未初始化"}
            
            # 使用V2引擎运行回测
            v2_result = self._v2_engine.run_backtest()
            
            # 转换为V1格式结果
            v1_result = self._convert_v2_to_v1_result(v2_result)
            
            # 更新V1兼容属性
            self._update_v1_attributes(v1_result)
            
            self._compat_stats["v1_method_calls"] += 1
            
            if v1_result.get("success", False):
                self.logger.info("✅ V1兼容回测完成")
            else:
                self.logger.error("❌ V1兼容回测失败")
            
            return v1_result
            
        except Exception as e:
            self.logger.error(f"运行回测失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "portfolio_value": self.portfolio_value,
                "total_return": 0.0,
                "sharpe_ratio": 0.0
            }
    
    def _convert_v2_to_v1_result(self, v2_result: BacktestResult) -> Dict[str, Any]:
        """
        将V2结果转换为V1格式
        
        Parameters
        ----------
        v2_result : BacktestResult
            V2引擎结果
            
        Returns
        -------
        Dict[str, Any]
            V1格式结果
        """
        try:
            if not v2_result.success:
                return {
                    "success": False,
                    "error": "; ".join(v2_result.errors),
                    "portfolio_value": self.portfolio_value,
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0
                }
            
            # 提取V2结果中的关键指标
            metrics = v2_result.metrics or {}

            # 处理EngineMetrics对象
            if hasattr(metrics, '__dict__'):
                metrics_dict = metrics.__dict__
            else:
                metrics_dict = metrics if isinstance(metrics, dict) else {}

            # 构建V1格式结果
            v1_result = {
                "success": True,
                "portfolio_value": metrics_dict.get("final_portfolio_value", self.portfolio_value),
                "total_return": metrics_dict.get("total_return", 0.0),
                "sharpe_ratio": metrics_dict.get("sharpe_ratio", 0.0),
                "max_drawdown": metrics_dict.get("max_drawdown", 0.0),
                "win_rate": metrics_dict.get("win_rate", 0.0),
                "profit_factor": metrics_dict.get("profit_factor", 1.0),
                
                # V1特有字段
                "trades": getattr(v2_result, 'trades', []),
                "signals": getattr(v2_result, 'signals', []),
                "positions": self._convert_positions_to_dict(getattr(v2_result, 'positions', None)),
                "equity_curve": getattr(v2_result, 'equity_curve', []),
                
                # 兼容性信息
                "engine_version": "v1_compat",
                "v2_engine_used": True,
                "compat_stats": self._compat_stats
            }
            
            return v1_result
            
        except Exception as e:
            self.logger.error(f"转换V2结果到V1格式失败: {e}")
            return {
                "success": False,
                "error": f"结果转换失败: {e}",
                "portfolio_value": self.portfolio_value
            }
    
    def _update_v1_attributes(self, result: Dict[str, Any]):
        """
        更新V1兼容属性
        
        Parameters
        ----------
        result : Dict[str, Any]
            回测结果
        """
        try:
            if result.get("success", False):
                self.portfolio_value = result.get("portfolio_value", self.portfolio_value)
                self.trades = result.get("trades", [])
                self.signals = result.get("signals", [])
                positions_data = result.get("positions", {})
                self.positions = positions_data if isinstance(positions_data, dict) else {}
                
        except Exception as e:
            self.logger.error("更新V1属性失败: %s" % str(e))

    def _convert_positions_to_dict(self, positions_data) -> Dict[str, Any]:
        """
        将持仓数据转换为V1格式的字典

        Parameters
        ----------
        positions_data : Any
            持仓数据（可能是DataFrame或其他格式）

        Returns
        -------
        Dict[str, Any]
            V1格式的持仓字典
        """
        try:
            if positions_data is None:
                return {}

            # 如果是DataFrame，转换为字典
            if hasattr(positions_data, 'to_dict'):
                return positions_data.to_dict('records')

            # 如果已经是字典，直接返回
            if isinstance(positions_data, dict):
                return positions_data

            # 如果是列表，转换为字典
            if isinstance(positions_data, list):
                return {'positions': positions_data}

            # 其他情况，返回空字典
            return {}

        except Exception as e:
            self.logger.error("转换持仓数据失败: %s" % str(e))
            return {}

    # V1兼容性方法
    def set_initial_capital(self, capital: float):
        """V1方法：设置初始资金"""
        self._initial_capital = capital
        self.portfolio_value = capital
        self._compat_stats["v1_method_calls"] += 1
        self.logger.debug("设置初始资金: %.2f" % capital)
    
    def set_commission(self, commission: float):
        """V1方法：设置手续费"""
        self._commission = commission
        self._compat_stats["v1_method_calls"] += 1
        self.logger.debug("设置手续费: %.4f" % commission)
    
    def get_portfolio_value(self) -> float:
        """V1方法：获取组合价值"""
        self._compat_stats["v1_method_calls"] += 1
        return self.portfolio_value
    
    def get_total_return(self) -> float:
        """V1方法：获取总收益率"""
        self._compat_stats["v1_method_calls"] += 1
        if self._initial_capital > 0:
            return (self.portfolio_value - self._initial_capital) / self._initial_capital
        return 0.0
    
    def get_positions(self) -> Dict[str, Any]:
        """V1方法：获取持仓"""
        self._compat_stats["v1_method_calls"] += 1
        if isinstance(self.positions, dict):
            return self.positions.copy()
        else:
            return {}
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """V1方法：获取交易记录"""
        self._compat_stats["v1_method_calls"] += 1
        return self.trades.copy()
    
    def get_signals(self) -> List[Dict[str, Any]]:
        """V1方法：获取信号记录"""
        self._compat_stats["v1_method_calls"] += 1
        return self.signals.copy()
    
    def reset(self):
        """V1方法：重置引擎"""
        self.portfolio_value = self._initial_capital
        self.positions = {}
        self.trades = []
        self.signals = []
        self._strategies = []
        self._data = None
        self._initialized = False
        self._compat_stats["v1_method_calls"] += 1
        self.logger.info("✅ V1兼容引擎已重置")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取兼容性统计信息"""
        return {
            "compatibility_stats": self._compat_stats,
            "v2_engine_metrics": self._v2_engine.get_metrics() if hasattr(self._v2_engine, 'get_metrics') else {},
            "v1_attributes": {
                "portfolio_value": self.portfolio_value,
                "initial_capital": self._initial_capital,
                "commission": self._commission,
                "strategies_count": len(self._strategies),
                "data_rows": len(self._data) if self._data is not None else 0
            }
        }
    
    # 属性访问兼容性
    def __getattr__(self, name: str):
        """提供V1属性访问兼容性"""
        # 尝试从V2引擎获取属性
        if hasattr(self._v2_engine, name):
            warnings.warn(
                f"访问属性 '{name}' 可能不是V1标准API",
                DeprecationWarning,
                stacklevel=2
            )
            self._compat_stats["deprecated_warnings"] += 1
            return getattr(self._v2_engine, name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
