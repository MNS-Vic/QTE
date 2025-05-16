import pandas as pd
import numpy as np
from typing import Dict, Any, Union, Optional
from datetime import datetime, timezone

class PerformanceMetrics:
    """
    量化交易性能指标计算类
    
    用于计算量化交易策略的各项性能指标，包括总收益率、年化收益率、
    最大回撤、夏普比率、索提诺比率、胜率、盈亏比等。
    """
    
    def __init__(self):
        """初始化性能指标计算类"""
        self.results = None
        self.annual_factor = 252  # 默认年化因子，可根据数据周期调整
    
    def set_results(self, results: pd.DataFrame) -> None:
        """
        设置回测结果数据
        
        Parameters
        ----------
        results : pd.DataFrame
            回测结果数据，包含策略收益等信息
        """
        self.results = results
        
        # 计算年化因子
        if isinstance(results.index, pd.DatetimeIndex):
            time_diff = (results.index[-1] - results.index[0]).days
            if time_diff <= 0:
                time_diff = 1
            self.annual_factor = 365 / time_diff
    
    def calculate_total_return(self) -> float:
        """
        计算总收益率
        
        Returns
        -------
        float
            总收益率
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        return self.results['cum_strategy_returns'].iloc[-1] - 1
    
    def calculate_annual_return(self) -> float:
        """
        计算年化收益率
        
        Returns
        -------
        float
            年化收益率
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        total_return = self.calculate_total_return()
        annual_return = (1 + total_return) ** self.annual_factor - 1
        
        return annual_return
    
    def calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns
        -------
        float
            最大回撤
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        return self.results['drawdown'].max()
    
    def calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率
        
        假设无风险利率为0
        
        Returns
        -------
        float
            夏普比率
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        daily_returns = self.results['strategy_returns']
        if daily_returns.std() > 0:
            return daily_returns.mean() / daily_returns.std() * np.sqrt(self.annual_factor)
        else:
            return 0
    
    def calculate_sortino_ratio(self) -> float:
        """
        计算索提诺比率
        
        使用下行波动率代替标准差
        
        Returns
        -------
        float
            索提诺比率
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        daily_returns = self.results['strategy_returns']
        negative_returns = daily_returns[daily_returns < 0]
        
        if len(negative_returns) > 0 and negative_returns.std() > 0:
            return daily_returns.mean() / negative_returns.std() * np.sqrt(self.annual_factor)
        else:
            return 0
    
    def calculate_trade_count(self) -> int:
        """
        计算交易次数
        
        Returns
        -------
        int
            交易次数
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        return (self.results['trade'] != 0).sum()
    
    def calculate_win_rate(self) -> float:
        """
        计算胜率
        
        Returns
        -------
        float
            胜率
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        trade_count = self.calculate_trade_count()
        if trade_count > 0:
            winning_trades = (self.results[self.results['trade'] != 0]['strategy_returns'] > 0).sum()
            return winning_trades / trade_count
        else:
            return 0
    
    def calculate_win_loss_ratio(self) -> float:
        """
        计算盈亏比
        
        Returns
        -------
        float
            盈亏比
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        avg_win = self.results['strategy_returns'][self.results['strategy_returns'] > 0].mean() if len(self.results['strategy_returns'][self.results['strategy_returns'] > 0]) > 0 else 0
        avg_loss = self.results['strategy_returns'][self.results['strategy_returns'] < 0].mean() if len(self.results['strategy_returns'][self.results['strategy_returns'] < 0]) > 0 else 0
        
        if avg_loss != 0:
            return abs(avg_win / avg_loss)
        else:
            return float('inf')
    
    def calculate_return_risk_ratio(self) -> float:
        """
        计算收益风险比
        
        Returns
        -------
        float
            收益风险比
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        annual_return = self.calculate_annual_return()
        max_drawdown = self.calculate_max_drawdown()
        
        if max_drawdown > 0:
            return annual_return / max_drawdown
        else:
            return float('inf')
    
    def calculate_all(self) -> Dict[str, Any]:
        """
        计算所有性能指标
        
        Returns
        -------
        Dict[str, Any]
            所有性能指标的字典
        """
        if self.results is None:
            raise ValueError("请先设置回测结果数据")
            
        metrics = {
            'total_return': self.calculate_total_return(),
            'annual_return': self.calculate_annual_return(),
            'max_drawdown': self.calculate_max_drawdown(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'trade_count': self.calculate_trade_count(),
            'win_rate': self.calculate_win_rate(),
            'win_loss_ratio': self.calculate_win_loss_ratio(),
            'return_risk_ratio': self.calculate_return_risk_ratio()
        }
        
        return metrics 