#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
移动平均线交叉策略测试

测试MA交叉策略的功能和性能
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, "..", "..")) # QTE project root from tests/unit
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入策略和相关模块
from qte.strategy.example_strategies import MovingAverageCrossStrategy # Corrected import
from qte.core.event_loop import EventLoop # Adjusted import

def generate_test_data(days=100, volatility=0.01, trend=0.0001, seed=42):
    """
    生成测试数据
    
    Args:
        days: 数据天数
        volatility: 波动率
        trend: 趋势强度
        seed: 随机种子
        
    Returns:
        DataFrame: 价格数据
    """
    # 设置随机种子
    np.random.seed(seed)
    
    # 生成日期
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # 生成价格
    price = 100
    prices = [price]
    
    for i in range(1, days):
        # 添加一些趋势和季节性
        if i < days / 2:
            trend_component = trend  # 上升趋势
        else:
            trend_component = -trend  # 下降趋势
            
        # 添加周期性波动
        cyclic_component = 0.0005 * np.sin(i / 10)
        
        # 随机波动
        random_component = np.random.normal(0, volatility)
        
        # 价格变动
        price_change = trend_component + cyclic_component + random_component
        price = price * (1 + price_change)
        
        prices.append(price)
    
    # 创建数据框
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, volatility)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, volatility)) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, size=days)
    })
    
    return data

def test_ma_cross_strategy():
    """测试移动平均线交叉策略"""
    logger.info("开始测试移动平均线交叉策略")
    
    # 生成测试数据
    data = generate_test_data(days=200, volatility=0.015, trend=0.0003)
    logger.info(f"生成了{len(data)}天的测试数据")
    
    # 创建策略
    short_window = 10
    long_window = 30
    strategy = MovingAverageCrossStrategy(short_window=short_window, long_window=long_window)
    logger.info(f"创建了移动平均线交叉策略，短期均线={short_window}天，长期均线={long_window}天")
    
    # 计算信号
    signal_data = strategy.calculate_signals(data)
    
    if signal_data is None:
        logger.error("无法计算交易信号")
        return
    
    # 统计信号
    buy_signals = signal_data[signal_data['signal'] == 1]
    sell_signals = signal_data[signal_data['signal'] == -1]
    
    logger.info(f"策略生成了{len(buy_signals)}个买入信号和{len(sell_signals)}个卖出信号")
    
    # 绘制结果
    plt.figure(figsize=(14, 7))
    plt.subplot(2, 1, 1)
    plt.plot(signal_data['timestamp'], signal_data['close'], label='价格', alpha=0.5)
    plt.plot(signal_data['timestamp'], signal_data['short_ma'], label=f'短期均线({short_window}日)')
    plt.plot(signal_data['timestamp'], signal_data['long_ma'], label=f'长期均线({long_window}日)')
    
    # 标记买入和卖出信号
    plt.scatter(buy_signals['timestamp'], buy_signals['close'], marker='^', color='g', s=100, label='买入信号')
    plt.scatter(sell_signals['timestamp'], sell_signals['close'], marker='v', color='r', s=100, label='卖出信号')
    
    plt.title('移动平均线交叉策略测试')
    plt.ylabel('价格')
    plt.grid(True)
    plt.legend()
    
    # 计算收益
    signal_data['position_diff'] = signal_data['position'].diff().fillna(0)
    signal_data['returns'] = signal_data['close'].pct_change()
    signal_data['strategy_returns'] = signal_data['position'].shift(1) * signal_data['returns']
    
    cumulative_returns = (1 + signal_data['returns']).cumprod()
    cumulative_strategy_returns = (1 + signal_data['strategy_returns']).cumprod()
    
    # 绘制收益曲线
    plt.subplot(2, 1, 2)
    plt.plot(signal_data['timestamp'], cumulative_returns - 1, label='买入持有收益')
    plt.plot(signal_data['timestamp'], cumulative_strategy_returns - 1, label='策略收益')
    plt.xlabel('日期')
    plt.ylabel('累计收益率')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    # 计算性能指标
    strategy_return = cumulative_strategy_returns.iloc[-1] - 1
    buy_hold_return = cumulative_returns.iloc[-1] - 1
    excess_return = strategy_return - buy_hold_return
    
    # 年化收益和波动率
    annual_return = strategy_return * (252 / len(signal_data))
    annual_volatility = signal_data['strategy_returns'].std() * np.sqrt(252)
    sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
    
    # 最大回撤
    rolling_max = cumulative_strategy_returns.cummax()
    drawdown = (cumulative_strategy_returns - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    # 输出结果
    logger.info("\n===== 策略性能 =====")
    logger.info(f"策略收益率: {strategy_return:.2%}")
    logger.info(f"买入持有收益率: {buy_hold_return:.2%}")
    logger.info(f"超额收益率: {excess_return:.2%}")
    logger.info(f"年化收益率: {annual_return:.2%}")
    logger.info(f"年化波动率: {annual_volatility:.2%}")
    logger.info(f"夏普比率: {sharpe_ratio:.2f}")
    logger.info(f"最大回撤: {max_drawdown:.2%}")
    logger.info(f"胜率: {(signal_data['strategy_returns'] > 0).mean():.2%}")
    
    # 显示详细交易记录
    logger.info("\n===== 交易记录 =====")
    trades = pd.concat([
        signal_data[signal_data['signal'] == 1][['timestamp', 'close']].assign(type='买入'),
        signal_data[signal_data['signal'] == -1][['timestamp', 'close']].assign(type='卖出')
    ]).sort_values('timestamp')
    
    trades['序号'] = range(1, len(trades) + 1)
    trades.columns = ['交易时间', '交易价格', '交易类型', '序号']
    trades = trades[['序号', '交易时间', '交易类型', '交易价格']]
    
    print(trades)
    
    return {
        'strategy': strategy,
        'signal_data': signal_data,
        'trades': trades,
        'metrics': {
            'strategy_return': strategy_return,
            'buy_hold_return': buy_hold_return,
            'excess_return': excess_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
    }

def test_strategy_with_real_data():
    """使用真实数据测试策略"""
    # 尝试加载真实数据
    data_dir = os.path.join("data", "backtest", "backtest_data") # Adjusted path
    data_file = os.path.join(data_dir, "SHSE.000001_daily_2023.csv")
    
    if os.path.exists(data_file):
        logger.info(f"加载真实数据: {data_file}")
        data = pd.read_csv(data_file, parse_dates=['timestamp'])
        
        # 创建策略
        short_window = 5
        long_window = 20
        strategy = MovingAverageCrossStrategy(short_window=short_window, long_window=long_window)
        
        # 计算信号并回测
        # 这里可以复用上面的回测逻辑
        # ...
    else:
        logger.warning(f"真实数据文件不存在: {data_file}")

if __name__ == "__main__":
    # 测试模拟数据
    test_results = test_ma_cross_strategy()
    
    # 测试真实数据
    # test_strategy_with_real_data() 