#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE框架完整工作流示例

本示例展示了使用QTE框架进行量化交易策略回测的完整流程：
1. 数据获取：从多种数据源加载股票数据
2. 策略定义：实现一个双均线交叉策略
3. 向量化回测：使用VectorEngine进行快速回测
4. 虚拟交易所交互：演示事件驱动回测与虚拟交易所的集成
5. 结果分析：生成详细的性能报告和可视化图表

作者: QTE开发团队
日期: 2024年
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import warnings

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# QTE框架核心组件导入
from qte.core.vector_engine import VectorEngine
from qte.data.data_factory import DataSourceFactory
from qte.analysis.performance_metrics import PerformanceMetrics
from qte.analysis.backtest_report import BacktestReport

# 事件驱动回测相关导入
from qte.core.event_engine import EventDrivenBacktester
from qte.core.events import MarketEvent, SignalEvent, OrderEvent, FillEvent

# 可选：虚拟交易所相关导入
try:
    from qte.exchange.virtual_exchange import VirtualExchange
    from qte.exchange.mock_exchange import MockExchange
    EXCHANGE_AVAILABLE = True
except ImportError:
    print("⚠️  虚拟交易所模块未找到，将跳过相关演示")
    EXCHANGE_AVAILABLE = False

# 忽略一些常见的警告以保持输出清洁
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)


class DualMovingAverageStrategy:
    """
    双均线交叉策略
    
    当短期均线上穿长期均线时产生买入信号
    当短期均线下穿长期均线时产生卖出信号
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        初始化策略参数
        
        Parameters
        ----------
        short_window : int
            短期均线周期
        long_window : int  
            长期均线周期
        """
        self.short_window = short_window
        self.long_window = long_window
        
        if short_window >= long_window:
            raise ValueError("短期均线周期必须小于长期均线周期")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号（用于向量化回测）
        
        Parameters
        ----------
        data : pd.DataFrame
            包含OHLCV数据的DataFrame
            
        Returns
        -------
        pd.DataFrame
            包含交易信号的DataFrame
        """
        if 'close' not in data.columns:
            raise ValueError("数据中必须包含'close'列")
        
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        
        # 计算移动平均线
        signals['short_mavg'] = data['close'].rolling(
            window=self.short_window, min_periods=1
        ).mean()
        signals['long_mavg'] = data['close'].rolling(
            window=self.long_window, min_periods=1
        ).mean()
        
        # 生成交易信号
        # 1: 买入, -1: 卖出, 0: 无操作
        signals.loc[signals['short_mavg'] > signals['long_mavg'], 'signal'] = 1.0
        signals.loc[signals['short_mavg'] < signals['long_mavg'], 'signal'] = -1.0
        
        print(f"✅ 策略信号生成完成，总共{len(signals)}个交易日")
        return signals[['signal']]


def prepare_sample_data(save_path: str, num_days: int = 500) -> pd.DataFrame:
    """
    准备示例数据
    
    如果数据文件不存在，则生成模拟的股票价格数据
    
    Parameters
    ----------
    save_path : str
        数据保存路径
    num_days : int
        生成数据的天数
        
    Returns
    -------
    pd.DataFrame
        OHLCV格式的股票数据
    """
    if os.path.exists(save_path):
        print(f"📊 从 {save_path} 加载已有数据...")
        try:
            data = pd.read_csv(save_path, index_col=0, parse_dates=True)
            return data
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
    
    print(f"📊 生成 {num_days} 天的模拟股票数据...")
    
    # 生成时间序列
    dates = pd.date_range(start='2022-01-01', periods=num_days, freq='B')
    
    # 生成价格数据（带趋势的随机游走）
    np.random.seed(42)
    
    # 基础价格趋势
    trend = np.linspace(100, 130, num_days)
    
    # 添加随机波动和周期性成分
    volatility = np.random.normal(0, 2, num_days)
    seasonal = 5 * np.sin(np.arange(num_days) * 2 * np.pi / 252)  # 年度周期
    
    close_prices = trend + volatility + seasonal
    close_prices = np.maximum(close_prices, 50)  # 避免负价格
    
    # 生成OHLC数据
    data = pd.DataFrame(index=dates)
    data['close'] = close_prices
    
    # 生成其他价格数据
    daily_ranges = np.random.uniform(0.5, 3.0, num_days)
    data['high'] = data['close'] + daily_ranges * np.random.uniform(0.3, 0.7, num_days)
    data['low'] = data['close'] - daily_ranges * np.random.uniform(0.3, 0.7, num_days)
    data['open'] = data['low'] + (data['high'] - data['low']) * np.random.uniform(0.2, 0.8, num_days)
    
    # 生成成交量
    data['volume'] = np.random.randint(100000, 2000000, num_days)
    
    # 确保OHLC逻辑正确
    data['high'] = data[['high', 'open', 'close']].max(axis=1)
    data['low'] = data[['low', 'open', 'close']].min(axis=1)
    
    # 保存数据
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    data.to_csv(save_path)
    print(f"✅ 模拟数据已保存到 {save_path}")
    
    return data


def load_data_from_sources():
    """
    演示从不同数据源加载数据
    
    Returns
    -------
    pd.DataFrame
        加载的股票数据
    """
    print("\n" + "="*60)
    print("📊 数据获取演示")
    print("="*60)
    
    # 方法1: 直接加载示例数据
    data_dir = os.path.join("examples", "tutorials", "sample_data")
    sample_file = os.path.join(data_dir, "sample_stock_data.csv")
    
    data = prepare_sample_data(sample_file, num_days=500)
    
    # 方法2: 使用DataSourceFactory（如果需要从其他源加载）
    # try:
    #     csv_source = DataSourceFactory.create('csv', base_path=data_dir)
    #     if csv_source:
    #         data = csv_source.get_bars('SAMPLE_STOCK')
    # except Exception as e:
    #     print(f"⚠️  DataSourceFactory加载失败: {e}")
    
    print(f"📈 数据概况:")
    print(f"   时间范围: {data.index[0].date()} 至 {data.index[-1].date()}")
    print(f"   总交易日: {len(data)}")
    print(f"   价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
    
    return data


def run_vectorized_backtest(data: pd.DataFrame, strategy: DualMovingAverageStrategy):
    """
    运行向量化回测
    
    Parameters
    ----------
    data : pd.DataFrame
        历史价格数据
    strategy : DualMovingAverageStrategy
        交易策略
        
    Returns
    -------
    dict
        回测结果
    """
    print("\n" + "="*60)
    print("🚀 向量化回测演示")
    print("="*60)
    
    # 创建回测引擎
    engine = VectorEngine(
        initial_capital=100000.0,  # 初始资金10万
        commission_rate=0.001      # 手续费0.1%
    )
    
    # 设置数据和策略
    engine.set_data(data)
    engine.add_strategy(strategy)
    
    # 运行回测
    print("🔄 正在运行向量化回测...")
    results = engine.run()
    
    print("✅ 向量化回测完成")
    
    return results


def demonstrate_virtual_exchange(data: pd.DataFrame, strategy: DualMovingAverageStrategy):
    """
    演示虚拟交易所集成
    
    Parameters
    ----------
    data : pd.DataFrame
        历史价格数据
    strategy : DualMovingAverageStrategy
        交易策略
    """
    print("\n" + "="*60)
    print("🏦 虚拟交易所演示")
    print("="*60)
    
    if not EXCHANGE_AVAILABLE:
        print("⚠️  虚拟交易所模块不可用，跳过此部分演示")
        return
    
    print("💡 这部分展示了策略信号如何与虚拟交易所交互")
    print("   在事件驱动回测中，策略会：")
    print("   1. 接收市场数据事件")
    print("   2. 生成交易信号")
    print("   3. 发送订单到虚拟交易所")
    print("   4. 接收成交回报")
    print("   5. 更新持仓和账户状态")
    
    # 这里可以添加具体的虚拟交易所演示代码
    # 由于时间关系，先提供概念性演示
    print("\n📋 虚拟交易所主要功能:")
    print("   • 订单匹配引擎")
    print("   • 账户管理系统") 
    print("   • 风险控制模块")
    print("   • 实时行情推送")
    print("   • WebSocket/REST API接口")


def analyze_results(results: Dict[str, Any], daily_results: pd.DataFrame):
    """
    分析回测结果
    
    Parameters
    ----------
    results : dict
        回测结果汇总
    daily_results : pd.DataFrame
        每日详细结果
    """
    print("\n" + "="*60)
    print("📊 结果分析")
    print("="*60)
    
    metrics = results.get('metrics', {})
    
    # 打印核心指标
    print("📈 核心性能指标:")
    key_metrics = [
        ('总收益率', 'total_return', '{:.2%}'),
        ('年化收益率', 'annual_return', '{:.2%}'),
        ('最大回撤', 'max_drawdown', '{:.2%}'),
        ('夏普比率', 'sharpe_ratio', '{:.3f}'),
        ('索提诺比率', 'sortino_ratio', '{:.3f}'),
        ('交易次数', 'trade_count', '{:.0f}'),
        ('胜率', 'win_rate', '{:.2%}'),
        ('盈亏比', 'win_loss_ratio', '{:.3f}')
    ]
    
    for name, key, fmt in key_metrics:
        value = metrics.get(key, 0)
        if key in ['win_loss_ratio'] and value == float('inf'):
            print(f"   {name}: ∞")
        else:
            print(f"   {name}: {fmt.format(value)}")
    
    # 资金曲线信息
    if daily_results is not None and 'equity' in daily_results.columns:
        initial_capital = daily_results['equity'].iloc[0]
        final_capital = daily_results['equity'].iloc[-1]
        print(f"\n💰 资金变化:")
        print(f"   初始资金: ¥{initial_capital:,.2f}")
        print(f"   最终资金: ¥{final_capital:,.2f}")
        print(f"   绝对收益: ¥{final_capital - initial_capital:,.2f}")


def generate_detailed_report(results: Dict[str, Any], daily_results: pd.DataFrame, 
                           strategy: DualMovingAverageStrategy):
    """
    生成详细的回测报告
    
    Parameters
    ----------
    results : dict
        回测结果
    daily_results : pd.DataFrame
        每日详细结果
    strategy : DualMovingAverageStrategy
        策略对象
    """
    print("\n" + "="*60)
    print("📋 生成详细报告")
    print("="*60)
    
    try:
        # 创建报告生成器
        report = BacktestReport(
            strategy_name=f"双均线策略({strategy.short_window},{strategy.long_window})",
            results=daily_results,
            metrics=results.get('metrics', {}),
            trades=[],  # 可以从results中提取交易记录
            initial_capital=100000.0
        )
        
        # 生成报告目录
        report_dir = os.path.join("examples", "tutorials", "backtest_reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # 生成完整报告
        report_files = report.generate_full_report(report_dir)
        
        print("✅ 详细报告生成完成:")
        for file_path in report_files:
            print(f"   📄 {os.path.basename(file_path)}")
        
        print(f"\n📁 报告保存位置: {report_dir}")
        
    except Exception as e:
        print(f"⚠️  报告生成失败: {e}")
        print("💡 提示: 可能需要安装matplotlib等依赖包")


def main():
    """
    主函数 - 运行完整的工作流演示
    """
    print("🎯 QTE框架完整工作流演示")
    print("=" * 80)
    print("本示例将演示从数据获取到结果分析的完整量化交易流程")
    
    try:
        # 1. 数据获取
        data = load_data_from_sources()
        
        # 2. 策略定义
        strategy = DualMovingAverageStrategy(short_window=20, long_window=50)
        print(f"\n📋 策略配置:")
        print(f"   策略类型: 双均线交叉策略")
        print(f"   短期均线: {strategy.short_window}日")
        print(f"   长期均线: {strategy.long_window}日")
        
        # 3. 向量化回测
        backtest_results = run_vectorized_backtest(data, strategy)
        daily_results = backtest_results.get('results')
        
        # 4. 虚拟交易所演示
        demonstrate_virtual_exchange(data, strategy)
        
        # 5. 结果分析
        analyze_results(backtest_results, daily_results)
        
        # 6. 生成详细报告
        generate_detailed_report(backtest_results, daily_results, strategy)
        
        print("\n" + "="*80)
        print("🎉 完整工作流演示结束")
        print("="*80)
        print("💡 后续步骤建议:")
        print("   • 尝试调整策略参数进行优化")
        print("   • 使用真实的历史数据进行回测")
        print("   • 集成更多技术指标和策略")
        print("   • 进行风险管理和资金管理")
        print("   • 连接实盘交易接口")
        
    except Exception as e:
        print(f"\n❌ 运行过程中发生错误: {e}")
        print("💡 请检查QTE框架是否正确安装和配置")


if __name__ == "__main__":
    main() 