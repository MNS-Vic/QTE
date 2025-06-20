"""
向量化回测引擎 V2 - 基于接口的重构版本

实现了IBacktestEngine接口，提供高性能的向量化回测功能
"""

import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Any
from datetime import datetime

from ..interfaces.engine_interface import (
    IBacktestEngine,
    EngineCapability,
    EngineMetrics,
    BacktestResult
)

# 导入性能优化模块
try:
    from qte.performance.numba_accelerators import (
        fast_position_calculation,
        fast_returns_calculation,
        fast_drawdown_calculation,
        fast_sharpe_ratio,
        NUMBA_AVAILABLE
    )
    from qte.performance.memory_optimizers import optimize_dataframe_memory
    PERFORMANCE_OPTIMIZED = True
except ImportError:
    NUMBA_AVAILABLE = False
    PERFORMANCE_OPTIMIZED = False
    logging.getLogger(__name__).warning("⚠️ 性能优化模块不可用，使用标准实现")


class VectorEngineV2(IBacktestEngine):
    """
    向量化回测引擎 V2
    
    基于Pandas和NumPy实现的高性能向量化计算引擎，
    支持快速回测、大规模参数优化和高频数据处理。
    
    实现了IBacktestEngine接口，提供统一的引擎访问方式。
    """
    
    def __init__(self):
        """初始化向量化引擎"""
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # 引擎状态
        self._initialized = False
        self._config = {}
        
        # 数据和结果
        self._data = None
        self._strategies = []
        self._signals = None
        self._positions = None
        self._results = None
        
        # 性能指标
        self._metrics = EngineMetrics()
        
        # 引擎参数
        self._initial_capital = 100000.0
        self._commission_rate = 0.001
        
        self.logger.info("🔧 向量化引擎V2初始化完成")
    
    def get_engine_type(self) -> str:
        """获取引擎类型"""
        return "vectorized_v2"
    
    def get_capabilities(self) -> List[EngineCapability]:
        """获取引擎能力"""
        return [
            EngineCapability.VECTORIZED_COMPUTATION,
            EngineCapability.MULTI_ASSET_SUPPORT,
            EngineCapability.HIGH_FREQUENCY_DATA,
            EngineCapability.PARALLEL_PROCESSING,
            EngineCapability.CUSTOM_STRATEGIES
        ]
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化引擎
        
        Args:
            config: 引擎配置参数
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            self._config = config.copy()
            
            # 设置引擎参数
            self._initial_capital = config.get('initial_capital', 100000.0)
            self._commission_rate = config.get('commission_rate', 0.001)
            
            # 重置状态
            self._data = None
            self._strategies = []
            self._signals = None
            self._positions = None
            self._results = None
            self._metrics = EngineMetrics()
            
            self._initialized = True
            self.logger.info(f"✅ 向量化引擎初始化成功，初始资金: ${self._initial_capital:,.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 向量化引擎初始化失败: {e}")
            return False
    
    def set_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> bool:
        """
        设置回测数据
        
        Args:
            data: 回测数据
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if isinstance(data, dict):
                # 多资产数据，合并为单个DataFrame
                combined_data = []
                for symbol, df in data.items():
                    df_copy = df.copy()
                    df_copy['symbol'] = symbol
                    combined_data.append(df_copy)
                self._data = pd.concat(combined_data, ignore_index=True)
            else:
                # 单资产数据
                self._data = data.copy()
            
            # 确保数据包含必要的列
            required_columns = ['close']
            missing_columns = [col for col in required_columns if col not in self._data.columns]
            
            if missing_columns:
                self.logger.error(f"❌ 数据缺少必要列: {missing_columns}")
                return False

            # 内存优化
            if PERFORMANCE_OPTIMIZED and len(self._data) > 10000:
                try:
                    original_memory = self._data.memory_usage(deep=True).sum()
                    self._data = optimize_dataframe_memory(self._data, inplace=True)
                    optimized_memory = self._data.memory_usage(deep=True).sum()
                    reduction = (original_memory - optimized_memory) / original_memory * 100
                    self.logger.info(f"✅ 内存优化完成，减少 {reduction:.1f}%")
                except Exception as e:
                    self.logger.warning(f"内存优化失败: {e}")

            self.logger.info(f"✅ 数据设置成功，数据点数: {len(self._data)}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据设置失败: {e}")
            return False
    
    def add_strategy(self, strategy: Any) -> bool:
        """
        添加交易策略
        
        Args:
            strategy: 交易策略对象
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 验证策略是否有必要的方法
            if not hasattr(strategy, 'generate_signals'):
                self.logger.error("❌ 策略必须实现generate_signals方法")
                return False
            
            self._strategies.append(strategy)
            self.logger.info(f"✅ 策略添加成功: {strategy.__class__.__name__}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 策略添加失败: {e}")
            return False
    
    def run_backtest(self, **kwargs) -> BacktestResult:
        """
        运行回测
        
        Args:
            **kwargs: 回测参数
            
        Returns:
            BacktestResult: 回测结果
        """
        start_time = time.time()
        result = BacktestResult(start_time=datetime.now())
        
        try:
            if not self._initialized:
                result.add_error("引擎未初始化")
                return result
            
            if self._data is None:
                result.add_error("未设置回测数据")
                return result
            
            if not self._strategies:
                result.add_error("未添加交易策略")
                return result
            
            self.logger.info("🚀 开始向量化回测...")
            
            # 1. 生成交易信号
            self._generate_signals()
            
            # 2. 计算持仓
            self._calculate_positions()
            
            # 3. 计算收益
            self._calculate_returns()
            
            # 4. 计算性能指标
            self._calculate_performance_metrics()
            
            # 设置结果
            result.success = True
            result.signals = self._signals
            result.positions = self._positions
            result.portfolio = self._results
            result.performance_metrics = self._get_performance_dict()
            
            # 更新引擎指标
            end_time = time.time()
            self._metrics.execution_time = end_time - start_time
            self._metrics.events_processed = len(self._data) if self._data is not None else 0
            self._metrics.throughput = self._metrics.events_processed / self._metrics.execution_time if self._metrics.execution_time > 0 else 0
            
            result.metrics = self._metrics
            result.end_time = datetime.now()
            
            self.logger.info(f"🎉 向量化回测完成，耗时: {self._metrics.execution_time:.2f}秒")
            
        except Exception as e:
            self.logger.error(f"❌ 回测执行失败: {e}")
            result.add_error(str(e))
            result.success = False
        
        return result
    
    def _generate_signals(self):
        """生成交易信号"""
        if self._data is None or not self._strategies:
            return
        
        # 为每个策略生成信号
        all_signals = []
        
        for strategy in self._strategies:
            try:
                signals = strategy.generate_signals(self._data)
                if signals is not None:
                    all_signals.append(signals)
            except Exception as e:
                self.logger.error(f"策略 {strategy.__class__.__name__} 信号生成失败: {e}")
        
        if all_signals:
            # 合并所有信号
            self._signals = pd.concat(all_signals, ignore_index=True)
        else:
            # 创建空信号DataFrame
            self._signals = pd.DataFrame(columns=['timestamp', 'symbol', 'signal'])
    
    def _calculate_positions(self):
        """计算持仓 - 性能优化版本"""
        if self._signals is None:
            return

        # 简化的持仓计算
        positions = self._signals.copy()

        if 'signal' in positions.columns:
            signals = positions['signal'].fillna(0).values

            # 使用Numba加速的持仓计算
            if PERFORMANCE_OPTIMIZED:
                try:
                    position_values = fast_position_calculation(signals)
                    positions['position'] = position_values
                    self.logger.debug("✅ 使用Numba加速持仓计算")
                except Exception as e:
                    self.logger.warning(f"Numba持仓计算失败，使用标准方法: {e}")
                    # 回退到标准方法
                    positions['position'] = positions['signal'].fillna(0).cumsum().clip(-1, 1)
            else:
                # 标准方法
                positions['position'] = positions['signal'].fillna(0).cumsum().clip(-1, 1)
        else:
            positions['position'] = 0

        self._positions = positions
    
    def _calculate_returns(self):
        """计算收益 - 性能优化版本"""
        if self._positions is None or self._data is None:
            return

        # 合并持仓和价格数据
        if 'timestamp' in self._data.columns and 'timestamp' in self._positions.columns:
            merged = pd.merge(self._positions, self._data, on='timestamp', how='left')
        else:
            merged = self._positions.copy()
            if 'close' in self._data.columns:
                merged['close'] = self._data['close']

        # 计算收益
        if 'position' in merged.columns and 'close' in merged.columns:
            prices = merged['close'].values
            positions = merged['position'].values

            # 使用Numba加速的收益计算
            if PERFORMANCE_OPTIMIZED and len(prices) > 1000:  # 对大数据集使用优化
                try:
                    returns, cum_returns, equity = fast_returns_calculation(
                        prices, positions, self._commission_rate
                    )
                    merged['returns'] = returns
                    merged['cumulative_returns'] = cum_returns
                    merged['equity'] = self._initial_capital * equity
                    self.logger.debug("✅ 使用Numba加速收益计算")
                except Exception as e:
                    self.logger.warning(f"Numba收益计算失败，使用标准方法: {e}")
                    # 回退到标准方法
                    merged['returns'] = merged['close'].pct_change() * merged['position'].shift(1)
                    merged['cumulative_returns'] = (1 + merged['returns'].fillna(0)).cumprod()
                    merged['equity'] = self._initial_capital * merged['cumulative_returns']
            else:
                # 标准方法
                merged['returns'] = merged['close'].pct_change() * merged['position'].shift(1)
                merged['cumulative_returns'] = (1 + merged['returns'].fillna(0)).cumprod()
                merged['equity'] = self._initial_capital * merged['cumulative_returns']
        else:
            merged['returns'] = 0
            merged['cumulative_returns'] = 1
            merged['equity'] = self._initial_capital

        self._results = merged
    
    def _calculate_performance_metrics(self):
        """计算性能指标 - 性能优化版本"""
        if self._results is None:
            return

        # 基本性能指标计算
        if 'returns' in self._results.columns:
            returns = self._results['returns'].dropna()

            if len(returns) > 0:
                total_return = self._results['cumulative_returns'].iloc[-1] - 1
                annual_return = (1 + total_return) ** (252 / len(returns)) - 1
                volatility = returns.std() * np.sqrt(252)

                # 使用Numba加速的夏普比率计算
                if PERFORMANCE_OPTIMIZED:
                    try:
                        sharpe_ratio = fast_sharpe_ratio(returns.values)
                        self.logger.debug("✅ 使用Numba加速夏普比率计算")
                    except Exception as e:
                        self.logger.warning(f"Numba夏普比率计算失败，使用标准方法: {e}")
                        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
                else:
                    sharpe_ratio = annual_return / volatility if volatility > 0 else 0

                # 使用Numba加速的回撤计算
                equity = self._results['equity'].values
                if PERFORMANCE_OPTIMIZED:
                    try:
                        drawdowns, max_drawdown = fast_drawdown_calculation(equity)
                        self.logger.debug("✅ 使用Numba加速回撤计算")
                    except Exception as e:
                        self.logger.warning(f"Numba回撤计算失败，使用标准方法: {e}")
                        # 标准方法
                        equity_series = self._results['equity']
                        peak = equity_series.expanding().max()
                        drawdown = (equity_series - peak) / peak
                        max_drawdown = drawdown.min()
                else:
                    # 标准方法
                    equity_series = self._results['equity']
                    peak = equity_series.expanding().max()
                    drawdown = (equity_series - peak) / peak
                    max_drawdown = drawdown.min()

                self._performance_metrics = {
                    'total_return': total_return,
                    'annual_return': annual_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'total_trades': len(self._positions) if self._positions is not None else 0
                }
    
    def _get_performance_dict(self) -> Dict[str, Any]:
        """获取性能指标字典"""
        return getattr(self, '_performance_metrics', {})
    
    def get_metrics(self) -> EngineMetrics:
        """获取引擎性能指标"""
        return self._metrics
    
    def reset(self) -> bool:
        """重置引擎状态"""
        try:
            self._data = None
            self._strategies = []
            self._signals = None
            self._positions = None
            self._results = None
            self._metrics = EngineMetrics()
            
            self.logger.info("🔄 引擎状态已重置")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 引擎重置失败: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理引擎资源"""
        try:
            self.reset()
            self._initialized = False
            self._config = {}
            
            self.logger.info("🧹 引擎资源已清理")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 引擎清理失败: {e}")
            return False
    
    def get_status(self) -> str:
        """获取引擎状态"""
        if not self._initialized:
            return "未初始化"
        elif self._data is None:
            return "已初始化，等待数据"
        elif not self._strategies:
            return "已设置数据，等待策略"
        else:
            return "就绪"
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置参数"""
        errors = []
        
        # 验证初始资金
        initial_capital = config.get('initial_capital', 0)
        if initial_capital <= 0:
            errors.append("初始资金必须大于0")
        
        # 验证手续费率
        commission_rate = config.get('commission_rate', 0)
        if commission_rate < 0 or commission_rate > 1:
            errors.append("手续费率必须在0-1之间")
        
        return errors
