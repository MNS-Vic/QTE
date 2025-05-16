import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import pytest

# 这个是我们要实现的类，现在还不存在
from qte.analysis.performance_metrics import PerformanceMetrics


class TestPerformanceMetrics(unittest.TestCase):
    """测试性能指标计算类"""

    def setUp(self):
        """设置测试环境"""
        # 创建样本回测结果数据
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # 创建价格数据
        np.random.seed(42)  # 确保结果可重现
        price = 100.0
        prices = []
        for _ in range(len(dates)):
            change = np.random.normal(0, 1) / 100  # 每日涨跌幅
            price *= (1 + change)
            prices.append(price)
        
        # 创建策略信号 (-1, 0, 1)
        signals = np.random.choice([-1, 0, 1], size=len(dates))
        
        # 创建测试数据DataFrame
        self.test_data = pd.DataFrame({
            'close': prices,
            'position': signals,
        }, index=dates)
        
        # 计算回测结果
        self.test_data['returns'] = self.test_data['close'].pct_change().fillna(0)
        self.test_data['strategy_returns'] = self.test_data['position'] * self.test_data['returns']
        
        # 模拟交易成本
        self.test_data['trade'] = self.test_data['position'].diff().fillna(0)
        commission_rate = 0.001
        self.test_data['cost'] = abs(self.test_data['trade']) * commission_rate
        self.test_data['strategy_returns'] = self.test_data['strategy_returns'] - self.test_data['cost']
        
        # 计算累积收益
        self.test_data['cum_returns'] = (1 + self.test_data['returns']).cumprod()
        self.test_data['cum_strategy_returns'] = (1 + self.test_data['strategy_returns']).cumprod()
        
        # 计算回撤
        self.test_data['cum_max'] = self.test_data['cum_strategy_returns'].cummax()
        self.test_data['drawdown'] = (self.test_data['cum_max'] - self.test_data['cum_strategy_returns']) / self.test_data['cum_max']
        
        # 创建性能指标计算对象
        self.metrics = PerformanceMetrics()
    
    def test_total_return(self):
        """测试总收益率计算"""
        self.metrics.set_results(self.test_data)
        total_return = self.metrics.calculate_total_return()
        
        # 手动计算总收益率
        expected_total_return = self.test_data['cum_strategy_returns'].iloc[-1] - 1
        
        self.assertAlmostEqual(total_return, expected_total_return, delta=1e-10)
    
    def test_annual_return(self):
        """测试年化收益率计算"""
        self.metrics.set_results(self.test_data)
        annual_return = self.metrics.calculate_annual_return()
        
        # 手动计算年化收益率
        time_diff = (self.test_data.index[-1] - self.test_data.index[0]).days
        annual_factor = 365 / time_diff
        expected_annual_return = (1 + self.test_data['cum_strategy_returns'].iloc[-1] - 1) ** annual_factor - 1
        
        self.assertAlmostEqual(annual_return, expected_annual_return, delta=1e-10)
    
    def test_max_drawdown(self):
        """测试最大回撤计算"""
        self.metrics.set_results(self.test_data)
        max_drawdown = self.metrics.calculate_max_drawdown()
        
        # 手动计算最大回撤
        expected_max_drawdown = self.test_data['drawdown'].max()
        
        self.assertAlmostEqual(max_drawdown, expected_max_drawdown, delta=1e-10)
    
    def test_sharpe_ratio(self):
        """测试夏普比率计算"""
        self.metrics.set_results(self.test_data)
        sharpe_ratio = self.metrics.calculate_sharpe_ratio()
        
        # 手动计算夏普比率
        daily_returns = self.test_data['strategy_returns']
        time_diff = (self.test_data.index[-1] - self.test_data.index[0]).days
        annual_factor = 365 / time_diff
        expected_sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(annual_factor) if daily_returns.std() > 0 else 0
        
        self.assertAlmostEqual(sharpe_ratio, expected_sharpe_ratio, delta=1e-10)
    
    def test_sortino_ratio(self):
        """测试索提诺比率计算"""
        self.metrics.set_results(self.test_data)
        sortino_ratio = self.metrics.calculate_sortino_ratio()
        
        # 手动计算索提诺比率
        daily_returns = self.test_data['strategy_returns']
        negative_returns = daily_returns[daily_returns < 0]
        time_diff = (self.test_data.index[-1] - self.test_data.index[0]).days
        annual_factor = 365 / time_diff
        expected_sortino_ratio = daily_returns.mean() / negative_returns.std() * np.sqrt(annual_factor) if len(negative_returns) > 0 and negative_returns.std() > 0 else 0
        
        self.assertAlmostEqual(sortino_ratio, expected_sortino_ratio, delta=1e-10)
    
    def test_win_rate(self):
        """测试胜率计算"""
        self.metrics.set_results(self.test_data)
        win_rate = self.metrics.calculate_win_rate()
        
        # 手动计算胜率
        trade_count = (self.test_data['trade'] != 0).sum()
        winning_trades = (self.test_data[self.test_data['trade'] != 0]['strategy_returns'] > 0).sum()
        expected_win_rate = winning_trades / trade_count if trade_count > 0 else 0
        
        self.assertAlmostEqual(win_rate, expected_win_rate, delta=1e-10)
    
    def test_win_loss_ratio(self):
        """测试盈亏比计算"""
        self.metrics.set_results(self.test_data)
        win_loss_ratio = self.metrics.calculate_win_loss_ratio()
        
        # 手动计算盈亏比
        avg_win = self.test_data['strategy_returns'][self.test_data['strategy_returns'] > 0].mean() if len(self.test_data['strategy_returns'][self.test_data['strategy_returns'] > 0]) > 0 else 0
        avg_loss = self.test_data['strategy_returns'][self.test_data['strategy_returns'] < 0].mean() if len(self.test_data['strategy_returns'][self.test_data['strategy_returns'] < 0]) > 0 else 0
        expected_win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # 处理无穷大的情况
        if expected_win_loss_ratio == float('inf'):
            self.assertEqual(win_loss_ratio, float('inf'))
        else:
            self.assertAlmostEqual(win_loss_ratio, expected_win_loss_ratio, delta=1e-10)
    
    def test_return_risk_ratio(self):
        """测试收益风险比计算"""
        self.metrics.set_results(self.test_data)
        return_risk_ratio = self.metrics.calculate_return_risk_ratio()
        
        # 手动计算收益风险比
        time_diff = (self.test_data.index[-1] - self.test_data.index[0]).days
        annual_factor = 365 / time_diff
        annual_return = (1 + self.test_data['cum_strategy_returns'].iloc[-1] - 1) ** annual_factor - 1
        max_drawdown = self.test_data['drawdown'].max()
        expected_return_risk_ratio = annual_return / max_drawdown if max_drawdown > 0 else float('inf')
        
        # 处理无穷大的情况
        if expected_return_risk_ratio == float('inf'):
            self.assertEqual(return_risk_ratio, float('inf'))
        else:
            self.assertAlmostEqual(return_risk_ratio, expected_return_risk_ratio, delta=1e-10)
    
    def test_calculate_all_metrics(self):
        """测试一次性计算所有指标"""
        self.metrics.set_results(self.test_data)
        all_metrics = self.metrics.calculate_all()
        
        # 验证所有指标是否都已计算
        expected_metrics = [
            'total_return', 'annual_return', 'max_drawdown', 
            'sharpe_ratio', 'sortino_ratio', 'trade_count',
            'win_rate', 'win_loss_ratio', 'return_risk_ratio'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, all_metrics)
    
    def test_no_data_exception(self):
        """测试在没有设置数据的情况下是否会抛出异常"""
        metrics = PerformanceMetrics()  # 创建一个新的对象，不设置数据
        
        with self.assertRaises(ValueError):
            metrics.calculate_all()


if __name__ == '__main__':
    unittest.main() 