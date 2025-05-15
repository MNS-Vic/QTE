#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单移动平均线交叉策略

使用短期和长期移动平均线的交叉来产生交易信号
- 当短期均线上穿长期均线时做多
- 当短期均线下穿长期均线时做空
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MACrossStrategy:
    """
    移动平均线交叉策略
    """

    def __init__(self, short_window=5, long_window=20):
        """
        初始化策略参数

        Args:
            short_window: 短期均线周期
            long_window: 长期均线周期
        """
        self.short_window = short_window
        self.long_window = long_window
        
        # 当前持仓状态: 1表示多头，-1表示空头，0表示空仓
        self.position = 0
        
        # 历史数据缓存
        self.price_history = []
        
        # 信号记录
        self.signals = []
    
    def calculate_signals(self, price_data):
        """
        根据价格数据计算交易信号

        Args:
            price_data: 包含价格数据的DataFrame，必须包含'close'列
            
        Returns:
            DataFrame: 包含交易信号的DataFrame
        """
        # 确保数据足够计算指标
        if len(price_data) < self.long_window:
            return None
        
        # 复制数据，避免修改原始数据
        data = price_data.copy()
        
        # 计算短期和长期移动平均线
        data['short_ma'] = data['close'].rolling(window=self.short_window).mean()
        data['long_ma'] = data['close'].rolling(window=self.long_window).mean()
        
        # 计算金叉和死叉信号
        # 金叉：短期均线上穿长期均线
        # 死叉：短期均线下穿长期均线
        data['signal'] = 0
        data['position'] = 0
        
        # 计算金叉和死叉 - 修复SettingWithCopyWarning
        signals = np.zeros(len(data))
        positions = np.zeros(len(data))
        
        for i in range(1, len(data)):
            if pd.notna(data['short_ma'].iloc[i]) and pd.notna(data['long_ma'].iloc[i]):
                # 上一个周期
                prev_short = data['short_ma'].iloc[i-1]
                prev_long = data['long_ma'].iloc[i-1]
                
                # 当前周期
                curr_short = data['short_ma'].iloc[i]
                curr_long = data['long_ma'].iloc[i]
                
                # 金叉信号
                if prev_short <= prev_long and curr_short > curr_long:
                    signals[i] = 1
                
                # 死叉信号
                elif prev_short >= prev_long and curr_short < curr_long:
                    signals[i] = -1
        
        # 计算持仓
        position = 0
        for i in range(len(data)):
            if signals[i] == 1:  # 金叉信号
                position = 1  # 做多
            elif signals[i] == -1:  # 死叉信号
                position = -1  # 做空
            
            positions[i] = position
        
        # 一次性赋值，避免SettingWithCopyWarning
        data['signal'] = signals
        data['position'] = positions
        
        return data
    
    def on_bar(self, bar):
        """
        处理新的K线数据

        Args:
            bar: K线数据，必须包含timestamp和close价格
            
        Returns:
            dict: 交易信号，包含action和position
        """
        # 将新数据添加到历史数据中
        self.price_history.append({
            'timestamp': bar['timestamp'],
            'close': bar['close'],
            'high': bar.get('high', bar['close']),
            'low': bar.get('low', bar['close']),
            'open': bar.get('open', bar['close']),
            'volume': bar.get('volume', 0)
        })
        
        # 转换为DataFrame
        df = pd.DataFrame(self.price_history)
        
        # 确保有足够的数据来计算信号
        if len(df) < self.long_window:
            return {'action': 'HOLD', 'position': 0}
        
        # 计算信号
        signal_data = self.calculate_signals(df)
        
        # 如果无法计算信号
        if signal_data is None:
            return {'action': 'HOLD', 'position': 0}
        
        # 获取最新的持仓状态
        current_position = signal_data['position'].iloc[-1]
        
        # 如果持仓状态改变，产生交易信号
        if current_position != self.position:
            if current_position == 1:  # 多头信号
                signal = {'action': 'BUY', 'position': 1}
            elif current_position == -1:  # 空头信号
                signal = {'action': 'SELL', 'position': -1}
            else:  # 平仓信号
                signal = {'action': 'CLOSE', 'position': 0}
            
            # 更新持仓状态
            self.position = current_position
            
            # 记录信号
            self.signals.append({
                'timestamp': bar['timestamp'],
                'price': bar['close'],
                'action': signal['action'],
                'position': signal['position']
            })
            
            return signal
        
        # 无交易信号
        return {'action': 'HOLD', 'position': self.position}

# 测试函数
def test_strategy():
    """测试移动平均线交叉策略"""
    import matplotlib.pyplot as plt
    
    # 创建策略实例
    strategy = MACrossStrategy(short_window=5, long_window=20)
    
    # 生成模拟数据
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(60)]
    
    # 使用随机游走生成价格
    np.random.seed(42)  # 设置随机种子，确保结果可重复
    price = 100  # 初始价格
    prices = [price]
    
    for _ in range(1, len(dates)):
        movement = np.random.normal(0, 1)  # 每天的价格变动百分比
        price = price * (1 + movement/100)
        prices.append(price)
    
    # 创建数据框
    data = pd.DataFrame({
        'timestamp': dates,
        'close': prices
    })
    
    # 计算信号
    signal_data = strategy.calculate_signals(data)
    
    if signal_data is not None:
        # 绘制结果
        plt.figure(figsize=(12, 6))
        plt.plot(signal_data['timestamp'], signal_data['close'], label='Close Price')
        plt.plot(signal_data['timestamp'], signal_data['short_ma'], label=f'Short MA ({strategy.short_window})')
        plt.plot(signal_data['timestamp'], signal_data['long_ma'], label=f'Long MA ({strategy.long_window})')
        
        # 标记买入信号
        buy_signals = signal_data[signal_data['signal'] == 1]
        plt.scatter(buy_signals['timestamp'], buy_signals['close'], marker='^', color='g', label='Buy Signal')
        
        # 标记卖出信号
        sell_signals = signal_data[signal_data['signal'] == -1]
        plt.scatter(sell_signals['timestamp'], sell_signals['close'], marker='v', color='r', label='Sell Signal')
        
        plt.legend()
        plt.title('MA Cross Strategy Backtest')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True)
        plt.show()
        
        print(f"生成了{len(buy_signals)}个买入信号和{len(sell_signals)}个卖出信号")
    else:
        print("数据不足以计算信号")

if __name__ == "__main__":
    test_strategy() 