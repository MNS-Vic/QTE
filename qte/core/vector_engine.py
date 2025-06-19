#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量化回测引擎 - 高性能数据处理和大规模回测优化
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Callable, Any


class VectorEngine:
    """
    向量化回测引擎
    
    基于Pandas和NumPy实现的高性能向量化计算引擎，
    支持快速回测、大规模参数优化和高频数据处理。
    """
    
    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.001) -> None:
        """
        初始化向量化回测引擎
        
        Parameters
        ----------
        initial_capital : float, optional
            初始资金, by default 100000.0
        commission_rate : float, optional
            交易手续费率, by default 0.001
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.data = None
        self.signals = None
        self.positions = None
        self.results = None
        self.strategies = []
        self.performance_metrics = {}
        
    def set_data(self, data: pd.DataFrame) -> None:
        """
        设置回测数据
        
        Parameters
        ----------
        data : pd.DataFrame
            回测数据，需要包含日期索引和OHLCV列
        """
        self.data = data
        if 'datetime' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
            self.data.index = pd.to_datetime(data['datetime'])
            
    def add_strategy(self, strategy: Any) -> None:
        """
        添加策略
        
        Parameters
        ----------
        strategy : Any
            策略对象，需要实现generate_signals方法
        """
        self.strategies.append(strategy)
    
    def generate_signals(self) -> pd.DataFrame:
        """
        生成交易信号
        
        针对所有添加的策略生成综合信号
        
        Returns
        -------
        pd.DataFrame
            包含交易信号的数据框
        """
        # 初始化信号
        signals = self.data.copy()
        signals['signal'] = 0
        
        # 对每个策略生成信号并进行组合
        for strategy in self.strategies:
            if hasattr(strategy, 'generate_signals'):
                strategy_signals = strategy.generate_signals(self.data)
                # 如果策略返回完整的DataFrame，提取信号列
                if isinstance(strategy_signals, pd.DataFrame) and 'signal' in strategy_signals.columns:
                    signals['signal'] += strategy_signals['signal']
                # 如果策略只返回信号Series
                elif isinstance(strategy_signals, pd.Series):
                    signals['signal'] += strategy_signals
            
        # 标准化信号: 1表示做多, -1表示做空, 0表示不操作
        signals['signal'] = signals['signal'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        
        self.signals = signals
        return signals
    
    def calculate_positions(self) -> pd.DataFrame:
        """
        计算持仓
        
        根据信号计算持仓状态
        
        Returns
        -------
        pd.DataFrame
            包含持仓信息的数据框
        """
        if self.signals is None:
            self.generate_signals()
            
        positions = self.signals.copy()
        
        # 从信号计算持仓 (0表示空仓，1表示持有多头，-1表示持有空头)
        positions['position'] = positions['signal'].replace(to_replace=-1, value=0).fillna(0)
        positions['position'] = positions['position'].cumsum().clip(0, 1)
        positions['position'] = positions['position'].shift(1).fillna(0)  # 下一个周期才能交易
        
        self.positions = positions
        return positions
    
    def calculate_returns(self) -> pd.DataFrame:
        """
        计算收益
        
        计算策略的收益率、累计收益和资金曲线
        
        Returns
        -------
        pd.DataFrame
            包含收益信息的数据框
        """
        if self.positions is None:
            self.calculate_positions()
            
        results = self.positions.copy()
        
        # 计算收益率
        results['returns'] = results['close'].pct_change()
        results['strategy_returns'] = results['position'] * results['returns']
        
        # 计算交易成本
        results['trade'] = results['position'].diff().fillna(0)
        results['cost'] = abs(results['trade']) * self.commission_rate
        results['strategy_returns'] = results['strategy_returns'] - results['cost']
        
        # 计算累积收益
        results['cum_returns'] = (1 + results['returns']).cumprod()
        results['cum_strategy_returns'] = (1 + results['strategy_returns']).cumprod()
        
        # 计算回撤
        results['cum_max'] = results['cum_strategy_returns'].cummax()
        results['drawdown'] = (results['cum_max'] - results['cum_strategy_returns']) / results['cum_max']
        
        # 计算资金曲线
        results['equity'] = self.initial_capital * results['cum_strategy_returns']
        
        self.results = results
        return results
    
    def calculate_metrics(self) -> Dict[str, float]:
        """
        计算性能指标
        
        计算策略的各项性能指标，包括收益率、最大回撤、夏普比率等
        
        Returns
        -------
        Dict[str, float]
            性能指标字典
        """
        if self.results is None:
            self.calculate_returns()
            
        results = self.results
        
        # 计算年化因子
        if isinstance(results.index, pd.DatetimeIndex):
            time_diff = (results.index[-1] - results.index[0]).days
            if time_diff <= 0:
                time_diff = 1
            annual_factor = 365 / time_diff
        else:
            annual_factor = 252  # 默认使用交易日数
            
        # 总收益率
        total_return = results['cum_strategy_returns'].iloc[-1] - 1
        
        # 年化收益率
        annual_return = (1 + total_return) ** annual_factor - 1
        
        # 最大回撤 (使用numpy处理NaN值)
        drawdown_values = results['drawdown'].values
        valid_drawdown = drawdown_values[~np.isnan(drawdown_values)]
        max_drawdown = float(np.max(valid_drawdown)) if len(valid_drawdown) > 0 else 0.0
        
        # 夏普比率 (假设无风险利率为0)
        daily_returns = results['strategy_returns']
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(annual_factor) if daily_returns.std() > 0 else 0
        
        # 索提诺比率 (使用下行波动率)
        negative_returns = daily_returns[daily_returns < 0]
        sortino_ratio = daily_returns.mean() / negative_returns.std() * np.sqrt(annual_factor) if len(negative_returns) > 0 and negative_returns.std() > 0 else 0
        
        # 交易次数 (安全计算)
        trade_mask = results['trade'] != 0
        trade_count = int(trade_mask.sum()) if 'trade' in results.columns else 0

        # 胜率 (安全计算)
        if trade_count > 0 and 'strategy_returns' in results.columns:
            # 获取有交易的行
            trade_indices = results.index[trade_mask].tolist()
            if len(trade_indices) > 0:
                trade_returns = results.loc[trade_indices, 'strategy_returns']
                winning_trades = int((trade_returns > 0).sum())
                win_rate = winning_trades / trade_count
            else:
                win_rate = 0.0
        else:
            win_rate = 0.0

        # 盈亏比 (安全计算)
        if 'strategy_returns' in results.columns:
            strategy_returns = results['strategy_returns'].dropna()
            positive_returns = strategy_returns[strategy_returns > 0]
            negative_returns = strategy_returns[strategy_returns < 0]

            avg_win = float(positive_returns.mean()) if len(positive_returns) > 0 else 0.0
            avg_loss = float(negative_returns.mean()) if len(negative_returns) > 0 else 0.0
            win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        else:
            win_loss_ratio = 0.0
        
        # 收益风险比
        return_risk_ratio = annual_return / max_drawdown if max_drawdown > 0 else float('inf')
        
        metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'trade_count': trade_count,
            'win_rate': win_rate,
            'win_loss_ratio': win_loss_ratio,
            'return_risk_ratio': return_risk_ratio
        }
        
        self.performance_metrics = metrics
        return metrics
    
    def run(self, data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        运行回测
        
        完整执行回测过程并返回结果
        
        Parameters
        ----------
        data : Optional[pd.DataFrame], optional
            回测数据，如果为None则使用已设置的数据, by default None
        
        Returns
        -------
        Dict[str, Any]
            回测结果，包含交易信号、持仓、收益和性能指标
        """
        if data is not None:
            self.set_data(data)
            
        if self.data is None:
            raise ValueError("回测数据未设置，请先调用set_data或提供数据")
            
        # 生成信号
        self.generate_signals()
        
        # 计算持仓
        self.calculate_positions()
        
        # 计算收益
        self.calculate_returns()
        
        # 计算性能指标
        self.calculate_metrics()
        
        return {
            'signals': self.signals,
            'positions': self.positions,
            'results': self.results,
            'metrics': self.performance_metrics
        }
    
    def optimize(self, param_grid: Dict[str, List[Any]], data: Optional[pd.DataFrame] = None, 
                metric: str = 'sharpe_ratio', maximize: bool = True) -> pd.DataFrame:
        """
        参数优化
        
        网格搜索优化策略参数
        
        Parameters
        ----------
        param_grid : Dict[str, List[Any]]
            参数网格，字典格式{参数名: [参数值列表]}
        data : Optional[pd.DataFrame], optional
            回测数据，如果为None则使用已设置的数据, by default None
        metric : str, optional
            优化目标指标, by default 'sharpe_ratio'
        maximize : bool, optional
            是否最大化指标, by default True
        
        Returns
        -------
        pd.DataFrame
            优化结果，包含参数组合和对应的性能指标
        """
        if data is not None:
            self.set_data(data)
            
        if self.data is None:
            raise ValueError("回测数据未设置，请先调用set_data或提供数据")
        
        # 生成参数组合
        import itertools
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        results = []
        
        # 对每个参数组合执行回测
        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            
            # 应用参数到策略
            for strategy in self.strategies:
                for param_name, param_value in param_dict.items():
                    if hasattr(strategy, param_name):
                        setattr(strategy, param_name, param_value)
            
            # 运行回测
            self.run()
            
            # 记录结果
            result = param_dict.copy()
            result.update(self.performance_metrics)
            results.append(result)
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)
        
        # 排序
        if maximize:
            results_df = results_df.sort_values(metric, ascending=False)
        else:
            results_df = results_df.sort_values(metric, ascending=True)
        
        return results_df