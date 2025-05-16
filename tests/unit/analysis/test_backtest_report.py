import unittest
import os
import sys
import tempfile
import shutil
from unittest import mock

# 设置matplotlib后端 - 必须在导入matplotlib之前设置
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免在测试环境中弹出图形窗口

# 设置环境变量来禁用GUI相关的功能
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import pandas as pd
import numpy as np
from datetime import datetime, timezone
import matplotlib.pyplot as plt

# 这个是我们要实现的类，现在还不存在
from qte.analysis.backtest_report import BacktestReport
from qte.analysis.performance_metrics import PerformanceMetrics


class TestBacktestReport(unittest.TestCase):
    """测试回测报告生成功能"""

    def setUp(self):
        """设置测试环境"""
        try:
            # 确保matplotlib使用非交互式后端
            if plt.get_backend() != 'agg':
                plt.switch_backend('agg')
                
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
                'open': [p * 0.99 for p in prices],  # 简单模拟开盘价
                'high': [p * 1.02 for p in prices],  # 简单模拟最高价
                'low': [p * 0.98 for p in prices],   # 简单模拟最低价
                'volume': np.random.randint(1000, 100000, size=len(dates)),  # 模拟成交量
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
            
            # 计算资金曲线
            initial_capital = 100000.0
            self.test_data['equity'] = initial_capital * self.test_data['cum_strategy_returns']
            
            # 创建性能指标计算对象并计算指标
            metrics = PerformanceMetrics()
            metrics.set_results(self.test_data)
            self.metrics_dict = metrics.calculate_all()
            
            # 模拟交易记录
            self.trades = []
            for i in range(1, len(self.test_data)):
                if self.test_data['trade'].iloc[i] != 0:
                    trade = {
                        'datetime': self.test_data.index[i],
                        'symbol': 'AAPL',
                        'direction': 'BUY' if self.test_data['trade'].iloc[i] > 0 else 'SELL',
                        'quantity': abs(self.test_data['trade'].iloc[i]) * 100,  # 假设每单位信号对应100股
                        'price': self.test_data['close'].iloc[i],
                        'commission': self.test_data['cost'].iloc[i] * initial_capital,
                        'pnl': self.test_data['strategy_returns'].iloc[i] * initial_capital,
                    }
                    self.trades.append(trade)
            
            # 创建回测报告对象
            self.report = BacktestReport(
                strategy_name='测试策略',
                results=self.test_data,
                metrics=self.metrics_dict,
                trades=self.trades,
                initial_capital=initial_capital
            )
            
            # 创建临时目录用于保存报告
            self.temp_dir = tempfile.mkdtemp()
        except Exception as e:
            self.fail(f"setUp失败: {str(e)}")
    
    def tearDown(self):
        """清理测试环境"""
        # 关闭所有打开的图形
        try:
            plt.close('all')
        except Exception as e:
            print(f"关闭图形时出错: {e}")
        
        # 安全删除临时目录及其内容
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"清理临时目录时出错: {e}")
    
    def test_report_initialization(self):
        """测试报告对象初始化"""
        self.assertEqual(self.report.strategy_name, '测试策略')
        self.assertIs(self.report.results, self.test_data)
        self.assertIs(self.report.metrics, self.metrics_dict)
        self.assertEqual(len(self.report.trades), len(self.trades))
        self.assertEqual(self.report.initial_capital, 100000.0)
    
    def test_generate_performance_summary(self):
        """测试生成性能摘要"""
        summary = self.report.generate_performance_summary()
        
        # 检查关键指标是否包含在摘要中
        self.assertIn('总收益率', summary)
        self.assertIn('年化收益率', summary)
        self.assertIn('最大回撤', summary)
        self.assertIn('夏普比率', summary)
        self.assertIn('胜率', summary)
    
    @mock.patch('qte.analysis.backtest_report.plt.subplots')
    def test_plot_equity_curve(self, mock_subplots):
        """测试绘制资金曲线"""
        # 模拟figure和axes
        mock_fig = mock.MagicMock()
        mock_ax = mock.MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        # 调用函数
        fig = self.report.plot_equity_curve()
        
        # 验证函数被调用
        mock_subplots.assert_called_once()
        self.assertIsNotNone(fig)
    
    @mock.patch('qte.analysis.backtest_report.plt.subplots')
    def test_plot_drawdown(self, mock_subplots):
        """测试绘制回撤曲线"""
        # 模拟figure和axes
        mock_fig = mock.MagicMock()
        mock_ax = mock.MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        # 调用函数
        fig = self.report.plot_drawdown()
        
        # 验证函数被调用
        mock_subplots.assert_called_once()
        self.assertIsNotNone(fig)
    
    @mock.patch('qte.analysis.backtest_report.plt.subplots')
    def test_plot_monthly_returns(self, mock_subplots):
        """测试绘制月度收益热图"""
        # 简化测试，不再使用复杂的mock结构
        try:
            # 模拟figure和axes
            mock_fig = mock.MagicMock()
            mock_ax = mock.MagicMock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            # 直接调用方法，允许使用真实的数据处理逻辑
            fig = self.report.plot_monthly_returns()
            
            # 验证结果
            self.assertIsNotNone(fig)
        except Exception as e:
            self.fail(f"测试plot_monthly_returns失败: {str(e)}")
    
    @mock.patch('qte.analysis.backtest_report.plt.subplots')
    def test_plot_return_distribution(self, mock_subplots):
        """测试绘制收益分布图"""
        try:
            # 模拟figure和axes
            mock_fig = mock.MagicMock()
            mock_ax1 = mock.MagicMock()
            mock_ax2 = mock.MagicMock()
            mock_subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
            
            # 使用适当的mock替换，避免复杂的处理链
            with mock.patch('qte.analysis.backtest_report.sns.histplot'):
                with mock.patch('scipy.stats.probplot'):
                    # 直接调用方法
                    fig = self.report.plot_return_distribution()
                    
                    # 验证结果
                    self.assertIsNotNone(fig)
        except Exception as e:
            self.fail(f"测试plot_return_distribution失败: {str(e)}")
    
    def test_generate_trade_analysis(self):
        """测试生成交易分析"""
        # 创建简化的测试交易记录，减少复杂性和潜在的递归问题
        test_trades = [
            {
                'datetime': datetime(2023, 1, 2),
                'symbol': 'AAPL',
                'direction': 'BUY',
                'quantity': 100,
                'price': 150.0,
                'commission': 1.5,
                'pnl': 100.0,
            },
            {
                'datetime': datetime(2023, 1, 3),
                'symbol': 'AAPL',
                'direction': 'SELL',
                'quantity': 100,
                'price': 155.0,
                'commission': 1.5,
                'pnl': -50.0,
            }
        ]
        
        # 创建具有简单交易记录的报告对象
        try:
            report = BacktestReport(
                strategy_name='简化测试策略',
                results=self.test_data,
                metrics=self.metrics_dict,
                trades=test_trades,
                initial_capital=100000.0
            )
            
            # 直接调用方法
            trade_analysis = report.generate_trade_analysis()
            
            # 检查是否包含基本交易统计信息
            self.assertIn('总交易次数', trade_analysis)
            self.assertEqual(trade_analysis['总交易次数'], 2)
            self.assertIn('盈利交易次数', trade_analysis)
            self.assertEqual(trade_analysis['盈利交易次数'], 1)
            self.assertIn('亏损交易次数', trade_analysis)
            self.assertEqual(trade_analysis['亏损交易次数'], 1)
            
        except Exception as e:
            self.fail(f"测试生成交易分析失败: {str(e)}")
    
    def test_generate_trade_analysis_no_trades(self):
        """测试没有交易记录时的交易分析"""
        # 创建无交易记录的报告对象
        report = BacktestReport(
            strategy_name='无交易测试策略',
            results=self.test_data,
            metrics=self.metrics_dict,
            trades=[],
            initial_capital=100000.0
        )
        
        trade_analysis = report.generate_trade_analysis()
        
        # 检查无交易情况的处理
        self.assertIn('总交易次数', trade_analysis)
        self.assertEqual(trade_analysis['总交易次数'], 0)
        self.assertIn('无交易记录', trade_analysis)
        self.assertTrue(trade_analysis['无交易记录'])
    
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_equity_curve')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_drawdown')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_monthly_returns')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_return_distribution')
    def test_save_report_html(self, mock_return_dist, mock_monthly, mock_drawdown, mock_equity):
        """测试保存HTML报告"""
        # 创建一个简单的测试报告对象
        test_trades = [
            {
                'datetime': datetime(2023, 1, 2),
                'symbol': 'AAPL',
                'direction': 'BUY',
                'quantity': 100,
                'price': 150.0,
                'commission': 1.5,
                'pnl': 100.0,
            }
        ]
        
        report = BacktestReport(
            strategy_name='测试策略',
            results=self.test_data,
            metrics=self.metrics_dict,
            trades=test_trades,
            initial_capital=100000.0
        )
        
        # 设置模拟对象返回值
        mock_fig = mock.MagicMock()
        mock_fig.savefig = mock.MagicMock()
        mock_equity.return_value = mock_fig
        mock_drawdown.return_value = mock_fig
        mock_monthly.return_value = mock_fig
        mock_return_dist.return_value = mock_fig
        
        # 调用函数
        html_file = os.path.join(self.temp_dir, 'backtest_report.html')
        report.save_report_html(html_file)
        
        # 验证文件是否创建
        self.assertTrue(os.path.exists(html_file))
        self.assertTrue(os.path.getsize(html_file) > 0)
        
        # 验证文件内容
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('测试策略', content)
            self.assertIn('性能指标', content)
    
    def test_save_report_pdf(self):
        """测试保存PDF报告"""
        # 跳过测试，因为依赖外部工具
        self.skipTest("PDF导出功能需要安装pdfkit和wkhtmltopdf")
    
    @mock.patch('qte.analysis.backtest_report.BacktestReport.save_report_html')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_equity_curve')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_drawdown')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_monthly_returns')
    @mock.patch('qte.analysis.backtest_report.BacktestReport.plot_return_distribution')
    def test_generate_full_report(self, mock_return_dist, mock_monthly, mock_drawdown, mock_equity, mock_save_html):
        """测试生成完整报告"""
        # 创建一个简单的测试报告对象
        test_trades = [
            {
                'datetime': datetime(2023, 1, 2),
                'symbol': 'AAPL',
                'direction': 'BUY',
                'quantity': 100,
                'price': 150.0,
                'commission': 1.5,
                'pnl': 100.0,
            }
        ]
        
        report = BacktestReport(
            strategy_name='测试策略',
            results=self.test_data,
            metrics=self.metrics_dict,
            trades=test_trades,
            initial_capital=100000.0
        )
        
        # 设置模拟对象返回值
        mock_fig = mock.MagicMock()
        mock_fig.savefig = mock.MagicMock()
        mock_equity.return_value = mock_fig
        mock_drawdown.return_value = mock_fig
        mock_monthly.return_value = mock_fig
        mock_return_dist.return_value = mock_fig
        
        # 创建测试目录
        report_dir = os.path.join(self.temp_dir, 'full_report')
        os.makedirs(report_dir, exist_ok=True)
        
        # 调用函数
        report_files = report.generate_full_report(report_dir)
        
        # 验证结果
        self.assertIsInstance(report_files, list)
        self.assertTrue(len(report_files) > 0)


if __name__ == '__main__':
    unittest.main() 