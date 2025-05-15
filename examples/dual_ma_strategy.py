#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双均线交叉策略示例 - 展示QTE框架的使用方法
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from qte.core import EngineManager, EngineType, EventType, MarketEvent, SignalEvent


class DualMaStrategy:
    """
    双均线交叉策略
    
    当短期均线上穿长期均线时买入，
    当短期均线下穿长期均线时卖出
    """
    
    def __init__(self, short_window: int = 10, long_window: int = 30):
        """
        初始化双均线策略
        
        Parameters
        ----------
        short_window : int, optional
            短期均线窗口, by default 10
        long_window : int, optional
            长期均线窗口, by default 30
        """
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号 (为向量化引擎实现)
        
        Parameters
        ----------
        data : pd.DataFrame
            价格数据
        
        Returns
        -------
        pd.DataFrame
            包含信号的数据
        """
        signals = data.copy()
        
        # 计算均线
        signals['short_ma'] = signals['close'].rolling(window=self.short_window).mean()
        signals['long_ma'] = signals['close'].rolling(window=self.long_window).mean()
        
        # 计算金叉死叉
        signals['signal'] = 0
        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1
        
        # 找出交叉点
        signals['position_change'] = signals['signal'].diff()
        signals.loc[signals['position_change'] == 2, 'signal'] = 1  # 金叉
        signals.loc[signals['position_change'] == -2, 'signal'] = -1  # 死叉
        signals.loc[signals['position_change'] == 0, 'signal'] = 0  # 无变化
        
        return signals
    
    def on_market_data(self, event: MarketEvent) -> None:
        """
        处理市场数据事件 (为事件驱动引擎实现)
        
        Parameters
        ----------
        event : MarketEvent
            市场数据事件
        """
        from qte.core import EventType
        
        # 获取最新价格数据
        current_time = event.timestamp
        current_price = event.data['close']
        symbol = event.symbol
        
        # 将数据存储到历史记录中
        if not hasattr(self, 'price_history'):
            self.price_history = {}
        
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            
        self.price_history[symbol].append({'timestamp': current_time, 'close': current_price})
        
        # 如果没有足够的历史数据，不产生信号
        if len(self.price_history[symbol]) < self.long_window:
            return
        
        # 计算最近的移动平均线
        closes = [item['close'] for item in self.price_history[symbol][-self.long_window:]]
        short_ma = np.mean(closes[-self.short_window:])
        long_ma = np.mean(closes)
        
        # 如果没有记录上一次的均线值，先创建
        if not hasattr(self, 'last_ma'):
            self.last_ma = {}
            
        if symbol not in self.last_ma:
            self.last_ma[symbol] = {'short': short_ma, 'long': long_ma}
            return
        
        # 获取上一次的均线值
        last_short_ma = self.last_ma[symbol]['short']
        last_long_ma = self.last_ma[symbol]['long']
        
        # 更新均线值
        self.last_ma[symbol]['short'] = short_ma
        self.last_ma[symbol]['long'] = long_ma
        
        # 检测金叉或死叉（短期均线穿过长期均线）
        if last_short_ma <= last_long_ma and short_ma > long_ma:
            # 金叉：产生买入信号
            self.send_signal(current_time, symbol, 1)
        elif last_short_ma >= last_long_ma and short_ma < long_ma:
            # 死叉：产生卖出信号
            self.send_signal(current_time, symbol, -1)
    
    def send_signal(self, timestamp, symbol, direction):
        """
        发送交易信号事件
        
        Parameters
        ----------
        timestamp : datetime
            时间戳
        symbol : str
            交易品种代码
        direction : int
            交易方向，1为买入，-1为卖出
        """
        # 向事件引擎添加信号事件
        if hasattr(self, 'event_engine'):
            signal_event = SignalEvent(
                timestamp=timestamp,
                symbol=symbol,
                direction=direction,
                strength=1.0
            )
            self.event_engine.put(signal_event)


def main():
    """示例主函数"""
    # 创建双均线策略
    strategy = DualMaStrategy(short_window=10, long_window=30)
    
    # 加载测试数据（如果不存在则创建模拟数据）
    data_path = "test_data/backtest_data.csv"
    if os.path.exists(data_path):
        data = pd.read_csv(data_path, index_col='date', parse_dates=True)
    else:
        # 创建模拟数据
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        # 创建一个模拟的价格序列
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        prices = np.random.randn(252).cumsum() + 100
        data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(252) * 0.01),
            'high': prices * (1 + np.random.randn(252) * 0.01 + 0.02),
            'low': prices * (1 + np.random.randn(252) * 0.01 - 0.02),
            'close': prices * (1 + np.random.randn(252) * 0.01),
            'volume': np.random.randint(100000, 1000000, 252)
        }, index=dates)
        # 保存数据
        data.to_csv(data_path)
    
    print("数据加载完成，共 {} 条记录".format(len(data)))
    
    # 创建向量化引擎管理器
    vector_manager = EngineManager(engine_type=EngineType.VECTOR)
    vector_manager.add_strategy(strategy)
    
    # 运行向量化回测
    vector_results = vector_manager.run(data)
    
    # 打印向量化回测结果
    print("\n向量化引擎回测结果:")
    for key, value in vector_results['metrics'].items():
        print(f"{key}: {value:.4f}")
    
    # 创建事件驱动引擎管理器
    event_manager = EngineManager(engine_type=EngineType.EVENT)
    event_manager.add_strategy(strategy)
    
    # 准备事件驱动引擎的数据格式
    event_data = {'default': []}
    for i, (date, row) in enumerate(data.iterrows()):
        event_data['default'].append({
            'timestamp': date,
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        })
    
    # 运行事件驱动回测
    event_results = event_manager.run(event_data)
    
    # 打印事件驱动回测结果
    print("\n事件驱动引擎回测结果:")
    for key, value in [(k, v) for k, v in event_results.items() if k not in ['equity_curve', 'transactions']]:
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    # 对比结果
    comparison = vector_manager.compare_engines(data, strategy)
    
    # 打印引擎对比结果
    print("\n引擎性能对比:")
    for engine_type, results in comparison.items():
        if results['status'] == 'success':
            print(f"\n{engine_type.upper()} 引擎:")
            print(f"总收益率: {results['total_return']:.4f}")
            print(f"年化收益率: {results['annual_return']:.4f}")
            print(f"最大回撤: {results['max_drawdown']:.4f}")
            print(f"夏普比率: {results['sharpe_ratio']:.4f}")
            print(f"执行时间: {results['execution_time']:.4f}秒")
            print(f"内存使用: {results['memory_usage']:.4f}MB")
    
    # 绘制结果
    try:
        plt.figure(figsize=(12, 8))
        
        # 绘制价格和均线
        plt.subplot(2, 1, 1)
        plt.plot(data.index, data['close'], label='价格')
        plt.plot(data.index, data['close'].rolling(window=10).mean(), label='10日均线')
        plt.plot(data.index, data['close'].rolling(window=30).mean(), label='30日均线')
        plt.title('价格和移动平均线')
        plt.legend()
        
        # 绘制向量化引擎和事件驱动引擎的资产曲线对比
        plt.subplot(2, 1, 2)
        
        vector_equity = vector_results['results']['equity']
        plt.plot(vector_equity.index, vector_equity, label='向量化引擎')
        
        event_equity = event_results['equity_curve']['equity']
        plt.plot(event_equity.index, event_equity, label='事件驱动引擎')
        
        plt.title('资产曲线对比')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('examples/dual_ma_comparison.png')
        print("\n结果图表已保存至 examples/dual_ma_comparison.png")
    except Exception as e:
        print(f"绘制图表时出错: {e}")
    

if __name__ == "__main__":
    main()