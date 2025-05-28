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
    """创建可视化图表"""
    print("🎨 生成可视化图表...")
    
    # 确保输出目录存在
    output_dir = "examples/visualization_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 策略概览图 (2x2布局)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('QTE框架可视化演示 - 双均线策略分析', fontsize=16, fontweight='bold')
    
    # 子图1: 价格和均线
    ax1 = axes[0, 0]
    ax1.plot(data.index, data['price'], label='价格', linewidth=1, alpha=0.8)
    ax1.plot(data.index, data['short_ma'], label='短期均线(5日)', linewidth=2)
    ax1.plot(data.index, data['long_ma'], label='长期均线(20日)', linewidth=2)
    
    # 标记买卖点
    buy_signals = data[data['signal'] == 1]
    sell_signals = data[data['signal'] == -1]
    if not buy_signals.empty:
        ax1.scatter(buy_signals.index, buy_signals['price'], 
                   marker='^', color='red', s=100, label='买入', zorder=5)
    if not sell_signals.empty:
        ax1.scatter(sell_signals.index, sell_signals['price'], 
                   marker='v', color='green', s=100, label='卖出', zorder=5)
    
    ax1.set_title('价格走势与交易信号')
    ax1.set_ylabel('价格')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    # 子图2: 资金曲线
    ax2 = axes[0, 1]
    ax2.plot(data.index, data['equity'], linewidth=2, color='blue')
    ax2.set_title('资金曲线')
    ax2.set_ylabel('资金 (¥)')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    # 添加收益率标注
    total_return_pct = metrics['total_return'] * 100
    ax2.text(0.02, 0.98, f'总收益率: {total_return_pct:.2f}%', 
             transform=ax2.transAxes, fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
             verticalalignment='top')
    
    # 子图3: 回撤分析
    ax3 = axes[1, 0]
    ax3.fill_between(data.index, 0, data['drawdown'] * 100, 
                     color='red', alpha=0.3)
    ax3.plot(data.index, data['drawdown'] * 100, color='red', linewidth=1)
    ax3.set_title('回撤分析')
    ax3.set_ylabel('回撤 (%)')
    ax3.set_xlabel('日期')
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    # 子图4: 收益分布
    ax4 = axes[1, 1]
    daily_returns = data['returns'] * 100
    returns_clean = daily_returns.dropna()
    if not returns_clean.empty:
        ax4.hist(returns_clean, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax4.axvline(returns_clean.mean(), color='red', linestyle='--', 
                    label=f'均值: {returns_clean.mean():.3f}%')
    ax4.set_title('日收益率分布')
    ax4.set_xlabel('日收益率 (%)')
    ax4.set_ylabel('频次')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/strategy_overview.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # 2. 单独的资金曲线图
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data['equity'], linewidth=2, color='blue')
    ax.set_title('资金曲线详细图', fontsize=14, fontweight='bold')
    ax.set_ylabel('资金 (¥)')
    ax.set_xlabel('日期')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # 添加统计信息
    stats_text = f"""
    初始资金: ¥{data['equity'].iloc[0]:,.0f}
    最终资金: ¥{data['equity'].iloc[-1]:,.0f}
    总收益率: {metrics['total_return']:.2%}
    年化收益率: {metrics['annual_return']:.2%}
    最大回撤: {metrics['max_drawdown']:.2%}
    夏普比率: {metrics['sharpe_ratio']:.4f}
    """
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
            verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/equity_curve.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print("✅ 图表生成完成")
    return output_dir


def generate_html_report(data, metrics, output_dir):
    """生成HTML报告"""
    print("📄 生成HTML报告...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QTE框架可视化报告演示</title>
        <style>
            body {{
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }}
            .metric-label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            .chart-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .summary-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .summary-table th, .summary-table td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            .summary-table th {{
                background-color: #3498db;
                color: white;
            }}
            .summary-table tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 QTE框架可视化报告演示</h1>
            
            <h2>📊 策略概览</h2>
            <p><strong>策略名称:</strong> 双均线策略演示</p>
            <p><strong>回测期间:</strong> {data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}</p>
            <p><strong>初始资金:</strong> ¥{data['equity'].iloc[0]:,.0f}</p>
            
            <h2>🎯 核心指标</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">总收益率</div>
                    <div class="metric-value">{metrics['total_return']:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">年化收益率</div>
                    <div class="metric-value">{metrics['annual_return']:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">最大回撤</div>
                    <div class="metric-value">{metrics['max_drawdown']:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">夏普比率</div>
                    <div class="metric-value">{metrics['sharpe_ratio']:.4f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">年化波动率</div>
                    <div class="metric-value">{metrics['volatility']:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">胜率</div>
                    <div class="metric-value">{metrics['win_rate']:.2%}</div>
                </div>
            </div>
            
            <h2>📈 策略分析图表</h2>
            <div class="chart-container">
                <h3>策略完整分析</h3>
                <img src="strategy_overview.png" alt="策略概览图">
            </div>
            
            <div class="chart-container">
                <h3>资金曲线详细图</h3>
                <img src="equity_curve.png" alt="资金曲线图">
            </div>
            
            <h2>📋 详细统计</h2>
            <table class="summary-table">
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>说明</th>
                </tr>
                <tr>
                    <td>总收益率</td>
                    <td>{metrics['total_return']:.2%}</td>
                    <td>整个回测期间的总收益率</td>
                </tr>
                <tr>
                    <td>年化收益率</td>
                    <td>{metrics['annual_return']:.2%}</td>
                    <td>年化后的收益率</td>
                </tr>
                <tr>
                    <td>年化波动率</td>
                    <td>{metrics['volatility']:.2%}</td>
                    <td>收益率的年化标准差</td>
                </tr>
                <tr>
                    <td>夏普比率</td>
                    <td>{metrics['sharpe_ratio']:.4f}</td>
                    <td>风险调整后的收益率</td>
                </tr>
                <tr>
                    <td>最大回撤</td>
                    <td>{metrics['max_drawdown']:.2%}</td>
                    <td>从峰值到谷值的最大跌幅</td>
                </tr>
                <tr>
                    <td>交易次数</td>
                    <td>{metrics['trades']}</td>
                    <td>总交易信号数量</td>
                </tr>
                <tr>
                    <td>胜率</td>
                    <td>{metrics['win_rate']:.2%}</td>
                    <td>盈利交易占比</td>
                </tr>
                <tr>
                    <td>最终资金</td>
                    <td>¥{data['equity'].iloc[-1]:,.0f}</td>
                    <td>回测结束时的资金</td>
                </tr>
            </table>
            
            <div class="footer">
                <p>📊 由QTE量化交易引擎生成 | 🕒 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>💡 这是一个演示报告，展示了QTE框架的可视化功能</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    html_path = f"{output_dir}/visualization_report.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML报告已保存: {html_path}")
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
    print(f"   📄 visualization_report.html - HTML报告")
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