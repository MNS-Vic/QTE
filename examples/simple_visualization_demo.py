#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QTE框架简化可视化演示

这个示例展示了基础的可视化功能，包括：
1. 模拟回测数据生成
2. 基础图表绘制
3. 性能指标计算
4. 报告输出

运行方式：
python examples/simple_visualization_demo.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def generate_demo_data():
    """生成演示数据"""
    print("📊 生成演示数据...")
    
    # 生成时间序列
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 模拟价格数据
    np.random.seed(42)
    n_days = len(dates)
    
    # 基础价格走势
    trend = np.linspace(100, 120, n_days)
    noise = np.random.normal(0, 2, n_days)
    prices = trend + noise + 5 * np.sin(np.arange(n_days) * 0.1)
    prices = np.maximum(prices, 50)
    
    # 计算移动平均线
    short_ma = pd.Series(prices).rolling(window=5).mean()
    long_ma = pd.Series(prices).rolling(window=20).mean()
    
    # 生成交易信号
    signals = np.zeros(n_days)
    positions = np.zeros(n_days)
    current_pos = 0
    
    for i in range(20, n_days):
        if short_ma.iloc[i] > long_ma.iloc[i] and current_pos <= 0:
            signals[i] = 1  # 买入
            current_pos = 1
        elif short_ma.iloc[i] < long_ma.iloc[i] and current_pos >= 0:
            signals[i] = -1  # 卖出
            current_pos = -1
        positions[i] = current_pos
    
    # 计算收益
    price_returns = np.diff(prices) / prices[:-1]
    strategy_returns = positions[1:] * price_returns
    
    # 资金曲线
    initial_capital = 100000
    cumulative_returns = np.cumprod(1 + strategy_returns)
    equity = initial_capital * np.concatenate([[1], cumulative_returns])
    
    # 回撤
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    
    # 创建DataFrame
    data = pd.DataFrame({
        'price': prices,
        'short_ma': short_ma,
        'long_ma': long_ma,
        'signal': signals,
        'position': positions,
        'equity': equity,
        'returns': np.concatenate([[0], strategy_returns]),
        'drawdown': drawdown
    }, index=dates)
    
    print(f"✅ 生成了 {len(data)} 天的数据")
    return data


def calculate_metrics(data):
    """计算基础指标"""
    print("📈 计算性能指标...")
    
    returns = data['returns'].dropna()
    equity = data['equity']
    
    # 基础指标
    total_return = (equity.iloc[-1] / equity.iloc[0] - 1)
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = annual_return / volatility if volatility > 0 else 0
    max_drawdown = data['drawdown'].min()
    
    # 交易统计
    signals = data['signal']
    trades = len(signals[signals != 0])
    winning_trades = len(returns[returns > 0])
    win_rate = winning_trades / len(returns) if len(returns) > 0 else 0
    
    metrics = {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'trades': trades,
        'win_rate': win_rate
    }
    
    print("✅ 指标计算完成")
    return metrics


def create_visualizations(data, metrics):
    """创建金融专业版可视化图表"""
    print("🎨 创建金融专业版可视化图表...")
    
    # 设置金融专业版的深色主题
    plt.style.use('dark_background')
    
    # 设置全局字体和颜色
    plt.rcParams.update({
        'font.size': 10,
        'font.family': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],
        'figure.facecolor': '#0f172a',
        'axes.facecolor': '#1e293b',
        'axes.edgecolor': '#334155',
        'axes.labelcolor': '#e2e8f0',
        'xtick.color': '#94a3b8',
        'ytick.color': '#94a3b8',
        'grid.color': '#334155',
        'grid.alpha': 0.3,
        'text.color': '#e2e8f0'
    })
    
    # 专业金融配色方案
    colors = {
        'primary': '#3b82f6',
        'success': '#10b981', 
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'info': '#06b6d4',
        'accent': '#8b5cf6'
    }
    
    # 确保输出目录存在
    output_dir = "examples/visualization_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 创建策略完整分析图 (2x2 子图布局)
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.patch.set_facecolor('#0f172a')
    fig.suptitle('QTE策略完整分析 - 金融专业版', fontsize=16, fontweight='bold', color='#e2e8f0', y=0.95)
    
    # 子图1: 价格和均线
    ax1.plot(data.index, data['price'], label='价格', linewidth=1, alpha=0.8, color='#94a3b8')
    ax1.plot(data.index, data['short_ma'], label='短期均线(5日)', linewidth=2, color=colors['primary'])
    ax1.plot(data.index, data['long_ma'], label='长期均线(20日)', linewidth=2, color=colors['warning'])
    
    # 标记买卖点
    buy_signals = data[data['signal'] == 1]
    sell_signals = data[data['signal'] == -1]
    if not buy_signals.empty:
        ax1.scatter(buy_signals.index, buy_signals['price'], 
                   marker='^', color=colors['success'], s=100, label='买入', zorder=5)
    if not sell_signals.empty:
        ax1.scatter(sell_signals.index, sell_signals['price'], 
                   marker='v', color=colors['danger'], s=100, label='卖出', zorder=5)
    
    ax1.set_title('价格走势与交易信号', fontweight='bold', color='#e2e8f0', pad=20)
    ax1.set_ylabel('价格', color='#e2e8f0')
    ax1.legend(frameon=False, labelcolor='#e2e8f0')
    ax1.grid(True, alpha=0.3)
    
    # 子图2: 资金曲线
    ax2.plot(data.index, data['equity'], linewidth=2.5, color=colors['primary'], label='资金曲线')
    ax2.fill_between(data.index, data['equity'], data['equity'].min(), alpha=0.2, color=colors['primary'])
    ax2.set_title('资金曲线', fontweight='bold', color='#e2e8f0', pad=20)
    ax2.set_ylabel('资金 (¥)', color='#e2e8f0')
    ax2.grid(True, alpha=0.3)
    ax2.legend(frameon=False, labelcolor='#e2e8f0')
    
    # 子图3: 每日收益率分布
    daily_returns = data['equity'].pct_change().dropna()
    ax3.hist(daily_returns, bins=50, alpha=0.7, color=colors['info'], edgecolor='#0f172a')
    ax3.axvline(daily_returns.mean(), color=colors['success'], linestyle='--', linewidth=2, 
                label=f'均值: {daily_returns.mean():.4f}')
    ax3.set_title('每日收益率分布', fontweight='bold', color='#e2e8f0', pad=20)
    ax3.set_xlabel('每日收益率', color='#e2e8f0')
    ax3.set_ylabel('频次', color='#e2e8f0')
    ax3.grid(True, alpha=0.3)
    ax3.legend(frameon=False, labelcolor='#e2e8f0')
    
    # 子图4: 回撤分析
    rolling_max = data['equity'].expanding().max()
    drawdown = (data['equity'] - rolling_max) / rolling_max
    ax4.fill_between(data.index, drawdown, 0, alpha=0.7, color=colors['danger'], label='回撤')
    ax4.axhline(drawdown.min(), color=colors['warning'], linestyle='--', linewidth=2, 
                label=f'最大回撤: {drawdown.min():.2%}')
    ax4.set_title('回撤分析', fontweight='bold', color='#e2e8f0', pad=20)
    ax4.set_ylabel('回撤比例', color='#e2e8f0')
    ax4.grid(True, alpha=0.3)
    ax4.legend(frameon=False, labelcolor='#e2e8f0')
    
    plt.tight_layout()
    strategy_path = f"{output_dir}/strategy_overview.png"
    plt.savefig(strategy_path, dpi=300, bbox_inches='tight', facecolor='#0f172a', edgecolor='none')
    plt.close()
    
    # 2. 创建资金曲线详细图
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    fig.patch.set_facecolor('#0f172a')
    
    # 主要资金曲线
    ax.plot(data.index, data['equity'], color=colors['primary'], linewidth=3, label='资金曲线', alpha=0.9)
    
    # 添加基准线
    baseline = data['equity'].iloc[0] * (1 + 0.05) ** ((data.index - data.index[0]).days / 365.25)
    ax.plot(data.index, baseline, color=colors['warning'], linewidth=2, linestyle='--', 
            label='5%年化基准', alpha=0.7)
    
    # 填充区域
    ax.fill_between(data.index, data['equity'], baseline, 
                   where=(data['equity'] >= baseline), alpha=0.2, color=colors['success'], label='超额收益')
    ax.fill_between(data.index, data['equity'], baseline, 
                   where=(data['equity'] < baseline), alpha=0.2, color=colors['danger'], label='落后基准')
    
    # 添加重要标记点
    max_equity_idx = data['equity'].idxmax()
    max_equity_val = data['equity'].max()
    ax.scatter([max_equity_idx], [max_equity_val], color=colors['success'], s=100, zorder=5, 
              label=f'最高点: ¥{max_equity_val:,.0f}')
    
    # 最大回撤点
    rolling_max = data['equity'].expanding().max()
    drawdown = (data['equity'] - rolling_max) / rolling_max
    max_dd_idx = drawdown.idxmin()
    max_dd_val = data['equity'].loc[max_dd_idx]
    ax.scatter([max_dd_idx], [max_dd_val], color=colors['danger'], s=100, zorder=5,
              label=f'最大回撤点: ¥{max_dd_val:,.0f}')
    
    ax.set_title('QTE策略资金曲线详细分析', fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
    ax.set_xlabel('日期', color='#e2e8f0')
    ax.set_ylabel('资金 (¥)', color='#e2e8f0')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', frameon=False, labelcolor='#e2e8f0')
    
    # 格式化Y轴
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
    
    # 添加性能文本框
    textstr = f'''核心指标摘要:
总收益率: {metrics['total_return']:.2%}
年化收益: {metrics['annual_return']:.2%}
最大回撤: {metrics['max_drawdown']:.2%}
夏普比率: {metrics['sharpe_ratio']:.4f}
'''
    
    props = dict(boxstyle='round', facecolor='#1e293b', alpha=0.8, edgecolor='#334155')
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props, color='#e2e8f0')
    
    plt.tight_layout()
    equity_path = f"{output_dir}/equity_curve.png"
    plt.savefig(equity_path, dpi=300, bbox_inches='tight', facecolor='#0f172a', edgecolor='none')
    plt.close()
    
    print(f"✅ 策略分析图已保存: {strategy_path}")
    print(f"✅ 资金曲线图已保存: {equity_path}")
    
    return output_dir


def generate_html_report(data, metrics, output_dir):
    """生成金融专业版HTML报告"""
    print("📄 生成金融专业版HTML报告...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QTE量化框架 - 金融专业报告</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0a0e1a;
                color: #e2e8f0;
                line-height: 1.7;
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 32px 24px;
            }}
            
            .header {{
                background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #7c3aed 100%);
                padding: 48px 40px;
                border-radius: 20px;
                text-align: center;
                margin-bottom: 40px;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
                opacity: 0.3;
            }}
            
            .header h1 {{
                font-size: 3rem;
                font-weight: 700;
                color: white;
                margin-bottom: 16px;
                letter-spacing: -0.02em;
                position: relative;
                z-index: 1;
            }}
            
            .header .subtitle {{
                font-size: 1.25rem;
                color: #e0e7ff;
                font-weight: 300;
                position: relative;
                z-index: 1;
            }}
            
            .strategy-info {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 16px;
                padding: 32px;
                margin: 32px 0;
                border: 1px solid #334155;
            }}
            
            .strategy-info h2 {{
                color: #f1f5f9;
                font-size: 1.5rem;
                margin-bottom: 20px;
                border-bottom: 2px solid #3b82f6;
                padding-bottom: 12px;
            }}
            
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            
            .info-item {{
                background: #0f172a;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #1e293b;
            }}
            
            .info-label {{
                color: #94a3b8;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 8px;
            }}
            
            .info-value {{
                color: #f1f5f9;
                font-size: 1.1rem;
                font-weight: 600;
            }}
            
            .dashboard {{
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 32px;
                margin: 40px 0;
            }}
            
            .main-metrics {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 16px;
                padding: 32px;
                border: 1px solid #334155;
            }}
            
            .side-metrics {{
                display: flex;
                flex-direction: column;
                gap: 20px;
            }}
            
            .metric-large {{
                text-align: center;
                padding: 32px;
                border-bottom: 1px solid #475569;
            }}
            
            .metric-large:last-child {{
                border-bottom: none;
            }}
            
            .metric-large .value {{
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 12px;
                background: linear-gradient(135deg, #06b6d4, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .metric-large .label {{
                font-size: 1rem;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 600;
            }}
            
            .metric-small {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                padding: 24px;
                border-radius: 12px;
                border: 1px solid #334155;
                text-align: center;
            }}
            
            .metric-small .value {{
                font-size: 1.75rem;
                font-weight: 700;
                color: #06b6d4;
                margin-bottom: 8px;
            }}
            
            .metric-small .label {{
                font-size: 0.875rem;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            
            .section {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 16px;
                padding: 40px;
                margin: 32px 0;
                border: 1px solid #334155;
            }}
            
            .section-title {{
                font-size: 1.75rem;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 32px;
                border-bottom: 2px solid #3b82f6;
                padding-bottom: 16px;
            }}
            
            .chart-container {{
                background: #0f172a;
                padding: 24px;
                border-radius: 12px;
                border: 1px solid #1e293b;
                text-align: center;
            }}
            
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            
            .financial-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 24px 0;
                background: #0f172a;
                border-radius: 8px;
                overflow: hidden;
            }}
            
            .financial-table th {{
                background: linear-gradient(135deg, #1e3a8a, #3730a3);
                color: white;
                font-weight: 700;
                padding: 20px 16px;
                text-align: left;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }}
            
            .financial-table td {{
                padding: 16px;
                border-bottom: 1px solid #1e293b;
                font-size: 0.95rem;
                color: #e2e8f0;
            }}
            
            .financial-table tbody tr:hover {{
                background: #1e293b;
            }}
            
            .trend-up {{ 
                color: #10b981; 
                font-weight: 600;
            }}
            
            .trend-down {{ 
                color: #ef4444; 
                font-weight: 600;
            }}
            
            .neutral {{ 
                color: #06b6d4; 
                font-weight: 600;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 60px;
                padding: 32px;
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 16px;
                border: 1px solid #334155;
            }}
            
            .footer p {{
                color: #94a3b8;
                font-size: 0.875rem;
                margin: 8px 0;
            }}
            
            @media (max-width: 1024px) {{
                .dashboard {{
                    grid-template-columns: 1fr;
                }}
            }}
            
            @media (max-width: 768px) {{
                .header h1 {{ font-size: 2.5rem; }}
                .container {{ padding: 20px 16px; }}
                .section {{ padding: 24px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Professional Trading Analytics</h1>
                <p class="subtitle">QTE量化交易引擎 · 专业级金融分析报告</p>
            </div>
            
            <div class="strategy-info">
                <h2>策略概览信息</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">策略名称</div>
                        <div class="info-value">双均线策略演示</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">回测期间</div>
                        <div class="info-value">{data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">初始资金</div>
                        <div class="info-value">¥{data['equity'].iloc[0]:,.0f}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">最终资金</div>
                        <div class="info-value">¥{data['equity'].iloc[-1]:,.0f}</div>
                    </div>
                </div>
            </div>
            
            <div class="dashboard">
                <div class="main-metrics">
                    <div class="metric-large">
                        <div class="value {'trend-up' if metrics['total_return'] > 0 else 'trend-down'}">{metrics['total_return']:+.2%}</div>
                        <div class="label">Total Return</div>
                    </div>
                    <div class="metric-large">
                        <div class="value {'trend-up' if metrics['annual_return'] > 0 else 'trend-down'}">{metrics['annual_return']:+.2%}</div>
                        <div class="label">Annualized Return</div>
                    </div>
                    <div class="metric-large">
                        <div class="value trend-down">{metrics['max_drawdown']:.2%}</div>
                        <div class="label">Maximum Drawdown</div>
                    </div>
                </div>
                
                <div class="side-metrics">
                    <div class="metric-small">
                        <div class="value neutral">{metrics['sharpe_ratio']:.2f}</div>
                        <div class="label">Sharpe Ratio</div>
                    </div>
                    <div class="metric-small">
                        <div class="value">{metrics['volatility']:.1%}</div>
                        <div class="label">Volatility</div>
                    </div>
                    <div class="metric-small">
                        <div class="value {'trend-up' if metrics['win_rate'] > 0.5 else 'neutral'}">{metrics['win_rate']:.1%}</div>
                        <div class="label">Win Rate</div>
                    </div>
                    <div class="metric-small">
                        <div class="value">{metrics['trades']}</div>
                        <div class="label">Total Trades</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Strategy Performance Overview</h2>
                <div class="chart-container">
                    <img src="strategy_overview.png" alt="Strategy Performance">
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Equity Curve Analysis</h2>
                <div class="chart-container">
                    <img src="equity_curve.png" alt="Equity Curve">
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Detailed Performance Metrics</h2>
                <table class="financial-table">
                    <thead>
                        <tr>
                            <th>指标名称</th>
                            <th>数值</th>
                            <th>基准</th>
                            <th>评级</th>
                            <th>说明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>总收益率</td>
                            <td class="{'trend-up' if metrics['total_return'] > 0 else 'trend-down'}">{metrics['total_return']:+.2%}</td>
                            <td>15%</td>
                            <td>{'🟢 优秀' if metrics['total_return'] > 0.15 else '🟡 良好' if metrics['total_return'] > 0.05 else '🔴 较差'}</td>
                            <td>策略整体盈利能力</td>
                        </tr>
                        <tr>
                            <td>年化收益率</td>
                            <td class="{'trend-up' if metrics['annual_return'] > 0 else 'trend-down'}">{metrics['annual_return']:+.2%}</td>
                            <td>12%</td>
                            <td>{'🟢 优秀' if metrics['annual_return'] > 0.12 else '🟡 良好' if metrics['annual_return'] > 0.08 else '🔴 较差'}</td>
                            <td>年化后的收益表现</td>
                        </tr>
                        <tr>
                            <td>最大回撤</td>
                            <td class="trend-down">{metrics['max_drawdown']:.2%}</td>
                            <td>-10%</td>
                            <td>{'🟢 优秀' if metrics['max_drawdown'] > -0.1 else '🟡 良好' if metrics['max_drawdown'] > -0.2 else '🔴 较差'}</td>
                            <td>风险控制能力</td>
                        </tr>
                        <tr>
                            <td>夏普比率</td>
                            <td class="neutral">{metrics['sharpe_ratio']:.4f}</td>
                            <td>1.5</td>
                            <td>{'🟢 优秀' if metrics['sharpe_ratio'] > 1.5 else '🟡 良好' if metrics['sharpe_ratio'] > 1.0 else '🔴 较差'}</td>
                            <td>风险调整后收益</td>
                        </tr>
                        <tr>
                            <td>年化波动率</td>
                            <td class="neutral">{metrics['volatility']:.2%}</td>
                            <td>15%</td>
                            <td>{'🟢 优秀' if metrics['volatility'] < 0.15 else '🟡 中等' if metrics['volatility'] < 0.25 else '🔴 较高'}</td>
                            <td>收益稳定性</td>
                        </tr>
                        <tr>
                            <td>胜率</td>
                            <td class="{'trend-up' if metrics['win_rate'] > 0.5 else 'neutral'}">{metrics['win_rate']:.2%}</td>
                            <td>55%</td>
                            <td>{'🟢 优秀' if metrics['win_rate'] > 0.6 else '🟡 良好' if metrics['win_rate'] > 0.5 else '🔴 较差'}</td>
                            <td>交易成功率</td>
                        </tr>
                        <tr>
                            <td>交易次数</td>
                            <td class="neutral">{metrics['trades']}</td>
                            <td>100-200</td>
                            <td>{'🟢 适中' if 100 <= metrics['trades'] <= 200 else '🟡 偏多' if metrics['trades'] > 200 else '🟡 偏少'}</td>
                            <td>交易频率</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p><strong>QTE Quantitative Trading Engine</strong></p>
                <p>Professional Financial Analytics Report</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    html_path = f"{output_dir}/financial_pro_report.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ 金融专业版HTML报告已保存: {html_path}")
    return html_path


def print_summary(data, metrics, output_dir):
    """打印汇总信息"""
    print("\n" + "="*60)
    print("📊 QTE框架可视化演示 - 汇总报告")
    print("="*60)
    
    print(f"\n📅 回测期间: {data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"📈 策略名称: 双均线策略演示")
    print(f"💰 初始资金: ¥{data['equity'].iloc[0]:,.0f}")
    print(f"💼 最终资金: ¥{data['equity'].iloc[-1]:,.0f}")
    
    print(f"\n🎯 核心指标:")
    print(f"   总收益率: {metrics['total_return']:.2%}")
    print(f"   年化收益率: {metrics['annual_return']:.2%}")
    print(f"   年化波动率: {metrics['volatility']:.2%}")
    print(f"   夏普比率: {metrics['sharpe_ratio']:.4f}")
    print(f"   最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"   胜率: {metrics['win_rate']:.2%}")
    
    print(f"\n📁 输出文件:")
    print(f"   📊 strategy_overview.png - 策略完整分析图")
    print(f"   📈 equity_curve.png - 资金曲线详细图")
    print(f"   📄 financial_pro_report.html - 金融专业版HTML报告")
    print(f"\n📂 输出目录: {os.path.abspath(output_dir)}")


def main():
    """主函数"""
    print("🚀 QTE框架可视化演示")
    print("="*50)
    
    try:
        # 1. 生成演示数据
        data = generate_demo_data()
        
        # 2. 计算指标
        metrics = calculate_metrics(data)
        
        # 3. 创建可视化
        output_dir = create_visualizations(data, metrics)
        
        # 4. 生成HTML报告
        html_path = generate_html_report(data, metrics, output_dir)
        
        # 5. 打印汇总
        print_summary(data, metrics, output_dir)
        
        print(f"\n🎉 演示完成！")
        print(f"\n💡 查看结果:")
        print(f"   🌐 打开 {html_path} 查看完整报告")
        print(f"   📊 查看 {output_dir} 目录中的图片文件")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 