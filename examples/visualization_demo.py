#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTE框架可视化报告演示示例

这个示例展示了QTE框架完整的可视化报告功能，包括：
1. 回测数据生成
2. 性能指标计算  
3. 多种图表生成
4. HTML/PDF报告输出
5. 交易分析可视化

运行方式：
python examples/visualization_demo.py
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qte.analysis.backtest_report import BacktestReport
from qte.analysis.performance_metrics import PerformanceMetrics


def generate_sample_data():
    """
    生成示例回测数据
    
    模拟一个双均线策略的回测结果
    """
    print("📊 正在生成示例回测数据...")
    
    # 生成时间序列 (1年的交易日)
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 模拟价格数据 (带趋势和波动)
    np.random.seed(42)  # 确保结果可重现
    n_days = len(dates)
    
    # 生成基础价格走势
    trend = np.linspace(100, 120, n_days)  # 上升趋势
    noise = np.random.normal(0, 2, n_days)  # 随机波动
    prices = trend + noise + 5 * np.sin(np.arange(n_days) * 0.1)  # 加入周期性
    
    # 确保价格为正数
    prices = np.maximum(prices, 50)
    
    # 生成交易信号 (简单双均线策略)
    short_ma = pd.Series(prices).rolling(window=5).mean()
    long_ma = pd.Series(prices).rolling(window=20).mean()
    
    # 生成交易信号
    signals = np.zeros(n_days)
    positions = np.zeros(n_days)
    current_position = 0
    
    for i in range(20, n_days):  # 从第20天开始，确保长均线有效
        if short_ma.iloc[i] > long_ma.iloc[i] and current_position <= 0:
            signals[i] = 1  # 买入信号
            current_position = 1
        elif short_ma.iloc[i] < long_ma.iloc[i] and current_position >= 0:
            signals[i] = -1  # 卖出信号
            current_position = -1
        
        positions[i] = current_position
    
    # 计算策略收益
    price_returns = np.diff(prices) / prices[:-1]
    strategy_returns = positions[1:] * price_returns
    
    # 计算累计收益和资金曲线
    initial_capital = 100000
    cumulative_returns = np.cumprod(1 + strategy_returns)
    equity = initial_capital * np.concatenate([[1], cumulative_returns])
    
    # 计算回撤
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    
    # 创建结果DataFrame
    results = pd.DataFrame({
        'price': prices,
        'short_ma': short_ma,
        'long_ma': long_ma,
        'signal': signals,
        'position': positions,
        'equity': equity,
        'strategy_returns': np.concatenate([[0], strategy_returns]),
        'drawdown': drawdown
    }, index=dates)
    
    # 生成交易记录
    trades = []
    trade_id = 1
    entry_price = None
    entry_date = None
    
    for i, (date, row) in enumerate(results.iterrows()):
        if row['signal'] == 1 and entry_price is None:  # 开仓
            entry_price = row['price']
            entry_date = date
        elif row['signal'] == -1 and entry_price is not None:  # 平仓
            exit_price = row['price']
            exit_date = date
            pnl = (exit_price - entry_price) / entry_price * initial_capital * 0.1  # 假设10%仓位
            
            trades.append({
                'trade_id': trade_id,
                'symbol': 'DEMO.001',
                'direction': 'LONG',
                'quantity': 1000,
                'entry_time': entry_date,
                'entry_price': entry_price,
                'exit_time': exit_date,
                'exit_price': exit_price,
                'pnl': pnl,
                'commission': abs(pnl) * 0.001,  # 0.1% 手续费
                'datetime': exit_date,
                'price': exit_price,
                'drawdown_pct': results.loc[exit_date, 'drawdown']
            })
            
            trade_id += 1
            entry_price = None
            entry_date = None
    
    print(f"✅ 生成了 {len(results)} 天的回测数据")
    print(f"✅ 生成了 {len(trades)} 笔交易记录")
    
    return results, trades


def calculate_performance_metrics(results):
    """计算性能指标"""
    print("📈 正在计算性能指标...")
    
    metrics_calculator = PerformanceMetrics()
    metrics_calculator.set_results(results)
    
    # 计算所有指标
    metrics = metrics_calculator.calculate_all()
    
    print("✅ 性能指标计算完成")
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'rate' in key or 'ratio' in key:
                print(f"   {key}: {value:.4f}")
            else:
                print(f"   {key}: {value:.2%}")
        else:
            print(f"   {key}: {value}")
    
    return metrics


def generate_visualization_report(results, trades, metrics):
    """生成可视化报告"""
    print("🎨 正在生成可视化报告...")
    
    # 创建报告生成器
    report = BacktestReport(
        strategy_name="双均线策略演示",
        results=results,
        metrics=metrics,
        trades=trades,
        initial_capital=100000.0
    )
    
    # 确保输出目录存在
    output_dir = "examples/visualization_output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("📊 生成各种图表...")
    
    # 1. 生成资金曲线图
    print("   - 资金曲线图")
    equity_fig = report.plot_equity_curve()
    equity_fig.savefig(f"{output_dir}/equity_curve.png", dpi=300, bbox_inches='tight')
    plt.close(equity_fig)
    
    # 2. 生成回撤分析图
    print("   - 回撤分析图")
    drawdown_fig = report.plot_drawdown()
    drawdown_fig.savefig(f"{output_dir}/drawdown_analysis.png", dpi=300, bbox_inches='tight')
    plt.close(drawdown_fig)
    
    # 3. 生成月度收益热图
    print("   - 月度收益热图")
    monthly_fig = report.plot_monthly_returns()
    monthly_fig.savefig(f"{output_dir}/monthly_returns.png", dpi=300, bbox_inches='tight')
    plt.close(monthly_fig)
    
    # 4. 生成收益分布图
    print("   - 收益分布图")
    dist_fig = report.plot_return_distribution()
    dist_fig.savefig(f"{output_dir}/return_distribution.png", dpi=300, bbox_inches='tight')
    plt.close(dist_fig)
    
    # 5. 生成策略概览图
    print("   - 策略概览图")
    create_strategy_overview(results, output_dir)
    
    # 6. 生成HTML报告
    print("📄 生成HTML报告...")
    html_path = f"{output_dir}/backtest_report.html"
    report.save_report_html(html_path)
    
    # 7. 生成完整报告包
    print("📦 生成完整报告包...")
    report_files = report.generate_full_report(f"{output_dir}/full_report")
    
    print("✅ 可视化报告生成完成！")
    print(f"\n📁 输出文件位置: {os.path.abspath(output_dir)}")
    print("\n📋 生成的文件:")
    print("   📊 图表文件:")
    print("      - equity_curve.png (资金曲线)")
    print("      - drawdown_analysis.png (回撤分析)")
    print("      - monthly_returns.png (月度收益热图)")
    print("      - return_distribution.png (收益分布)")
    print("      - strategy_overview.png (策略概览)")
    print("   📄 报告文件:")
    print("      - backtest_report.html (HTML报告)")
    print("   📦 完整报告包:")
    for file_path in report_files:
        print(f"      - {os.path.basename(file_path)}")
    
    return output_dir


def create_strategy_overview(results, output_dir):
    """创建策略概览图"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('双均线策略完整分析', fontsize=16, fontweight='bold')
    
    # 子图1: 价格和均线
    ax1 = axes[0, 0]
    ax1.plot(results.index, results['price'], label='价格', linewidth=1, alpha=0.8)
    ax1.plot(results.index, results['short_ma'], label='短期均线(5日)', linewidth=2)
    ax1.plot(results.index, results['long_ma'], label='长期均线(20日)', linewidth=2)
    
    # 标记买卖点
    buy_signals = results[results['signal'] == 1]
    sell_signals = results[results['signal'] == -1]
    ax1.scatter(buy_signals.index, buy_signals['price'], 
               marker='^', color='red', s=100, label='买入', zorder=5)
    ax1.scatter(sell_signals.index, sell_signals['price'], 
               marker='v', color='green', s=100, label='卖出', zorder=5)
    
    ax1.set_title('价格走势与交易信号')
    ax1.set_ylabel('价格')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 子图2: 资金曲线
    ax2 = axes[0, 1]
    ax2.plot(results.index, results['equity'], linewidth=2, color='blue')
    ax2.set_title('资金曲线')
    ax2.set_ylabel('资金')
    ax2.grid(True, alpha=0.3)
    
    # 添加收益率标注
    total_return = (results['equity'].iloc[-1] / results['equity'].iloc[0] - 1) * 100
    ax2.text(0.02, 0.98, f'总收益率: {total_return:.2f}%', 
             transform=ax2.transAxes, fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
             verticalalignment='top')
    
    # 子图3: 回撤分析
    ax3 = axes[1, 0]
    ax3.fill_between(results.index, 0, results['drawdown'] * 100, 
                     color='red', alpha=0.3)
    ax3.plot(results.index, results['drawdown'] * 100, color='red', linewidth=1)
    ax3.set_title('回撤分析')
    ax3.set_ylabel('回撤 (%)')
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.3)
    
    # 子图4: 收益分布
    ax4 = axes[1, 1]
    daily_returns = results['strategy_returns'] * 100
    ax4.hist(daily_returns.dropna(), bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    ax4.axvline(daily_returns.mean(), color='red', linestyle='--', 
                label=f'均值: {daily_returns.mean():.3f}%')
    ax4.set_title('日收益率分布')
    ax4.set_xlabel('日收益率 (%)')
    ax4.set_ylabel('频次')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/strategy_overview.png", dpi=300, bbox_inches='tight')
    plt.close(fig)


def print_summary_stats(results, trades, metrics):
    """打印汇总统计信息"""
    print("\n" + "="*60)
    print("📊 QTE框架可视化报告演示 - 汇总统计")
    print("="*60)
    
    print(f"\n📅 回测期间: {results.index[0].strftime('%Y-%m-%d')} 至 {results.index[-1].strftime('%Y-%m-%d')}")
    print(f"📈 策略名称: 双均线策略演示")
    print(f"💰 初始资金: ¥100,000")
    print(f"💼 最终资金: ¥{results['equity'].iloc[-1]:,.2f}")
    
    print(f"\n🎯 核心指标:")
    print(f"   总收益率: {metrics['total_return']:.2%}")
    print(f"   年化收益率: {metrics['annual_return']:.2%}")
    print(f"   最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"   夏普比率: {metrics['sharpe_ratio']:.4f}")
    print(f"   索提诺比率: {metrics['sortino_ratio']:.4f}")
    
    print(f"\n📊 交易统计:")
    print(f"   交易次数: {len(trades)}")
    print(f"   胜率: {metrics['win_rate']:.2%}")
    print(f"   盈亏比: {metrics['win_loss_ratio']:.4f}")
    
    if trades:
        total_pnl = sum(trade['pnl'] for trade in trades)
        avg_pnl = total_pnl / len(trades)
        print(f"   总盈亏: ¥{total_pnl:,.2f}")
        print(f"   平均每笔: ¥{avg_pnl:,.2f}")


def main():
    """主函数"""
    print("🚀 QTE框架可视化报告演示")
    print("="*50)
    
    try:
        # 1. 生成示例数据
        results, trades = generate_sample_data()
        
        # 2. 计算性能指标
        metrics = calculate_performance_metrics(results)
        
        # 3. 生成可视化报告
        output_dir = generate_visualization_report(results, trades, metrics)
        
        # 4. 打印汇总统计
        print_summary_stats(results, trades, metrics)
        
        print(f"\n🎉 演示完成！请查看输出目录: {os.path.abspath(output_dir)}")
        print("\n💡 提示:")
        print("   - 打开 backtest_report.html 查看完整的HTML报告")
        print("   - 查看各个PNG图片文件了解不同的可视化效果")
        print("   - full_report/ 目录包含了所有生成的文件")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 