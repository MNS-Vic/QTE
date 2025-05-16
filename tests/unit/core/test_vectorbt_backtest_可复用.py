#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VectorBT风格的向量化回测测试脚本
特点：高性能、向量化操作、大规模参数优化
"""
import os
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import psutil

# 模拟VectorBT的核心向量化回测逻辑
class VectorizedBacktester:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        
    def load_data(self, file_path=None, start_date=None, end_date=None):
        """加载数据或生成模拟数据"""
        if file_path and os.path.exists(file_path):
            # 如果文件存在，直接读取
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        else:
            # 否则生成模拟数据
            print("未找到数据文件，生成模拟数据...")
            if not start_date:
                start_date = '2020-01-01'
            if not end_date:
                end_date = '2022-12-31'
                
            # 生成日期范围
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # 生成价格数据（模拟指数走势）
            np.random.seed(42)  # 保证可重复性
            price = 3000  # 起始价格
            prices = [price]
            
            # 生成随机走势
            for _ in range(1, len(date_range)):
                change_percent = np.random.normal(0, 0.01)  # 每日涨跌幅服从正态分布
                price = price * (1 + change_percent)
                prices.append(price)
                
            # 创建DataFrame
            df = pd.DataFrame(index=date_range)
            df['close'] = prices
            df['open'] = df['close'].shift(1).fillna(df['close'][0] * 0.99)
            df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.03, size=len(df)))
            df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.03, size=len(df)))
            df['volume'] = np.random.randint(1000000, 10000000, size=len(df))
            
            # 只保留交易日
            df = df[df.index.dayofweek < 5]
            
        self.data = df
        return df
    
    def calculate_signals(self, fast_ma=10, slow_ma=30):
        """计算双均线交叉信号 - 向量化方式"""
        data = self.data.copy()
        
        # 计算移动平均线
        data['fast_ma'] = data['close'].rolling(window=fast_ma).mean()
        data['slow_ma'] = data['close'].rolling(window=slow_ma).mean()
        
        # 生成交叉信号 (向量化操作)
        data['signal'] = 0  # 初始化信号为0
        
        # 金叉: 快线从下方穿过慢线
        data['golden_cross'] = (data['fast_ma'] > data['slow_ma']) & (data['fast_ma'].shift(1) <= data['slow_ma'].shift(1))
        
        # 死叉: 快线从上方穿过慢线
        data['death_cross'] = (data['fast_ma'] < data['slow_ma']) & (data['fast_ma'].shift(1) >= data['slow_ma'].shift(1))
        
        # 设置信号: 1为买入, -1为卖出
        data.loc[data['golden_cross'], 'signal'] = 1
        data.loc[data['death_cross'], 'signal'] = -1
        
        self.signals = data
        return data
    
    def backtest(self, commission_rate=0.001):
        """执行回测 - 向量化计算"""
        signals = self.signals.copy()
        
        # 计算持仓 (0表示空仓，1表示持仓)
        signals['position'] = signals['signal'].replace(to_replace=-1, value=0).fillna(0)
        signals['position'] = signals['position'].cumsum().clip(0, 1)
        signals['position'] = signals['position'].shift(1).fillna(0)  # 第二天才能交易
        
        # 计算每日收益率
        signals['returns'] = signals['close'].pct_change()
        signals['strategy_returns'] = signals['position'] * signals['returns']
        
        # 考虑交易成本 (仅在交易发生时)
        signals['trade'] = signals['position'].diff().fillna(0)
        signals['cost'] = abs(signals['trade']) * commission_rate
        signals['strategy_returns'] = signals['strategy_returns'] - signals['cost']
        
        # 计算累积收益
        signals['cum_returns'] = (1 + signals['returns']).cumprod()
        signals['cum_strategy_returns'] = (1 + signals['strategy_returns']).cumprod()
        
        # 计算回撤
        signals['cum_max'] = signals['cum_strategy_returns'].cummax()
        signals['drawdown'] = (signals['cum_max'] - signals['cum_strategy_returns']) / signals['cum_max']
        
        # 计算最终资金
        signals['equity'] = self.initial_capital * signals['cum_strategy_returns']
        
        self.results = signals
        
        # 计算策略统计
        self.calculate_statistics()
        
        return signals
    
    def calculate_statistics(self):
        """计算策略统计指标"""
        results = self.results
        
        # 总收益率
        self.total_return = results['cum_strategy_returns'].iloc[-1] - 1
        
        # 年化收益率
        days = (results.index[-1] - results.index[0]).days
        self.annual_return = (1 + self.total_return) ** (365 / days) - 1
        
        # 最大回撤
        self.max_drawdown = results['drawdown'].max()
        
        # 夏普比率 (简化版，假设无风险利率为0)
        self.sharpe_ratio = results['strategy_returns'].mean() / results['strategy_returns'].std() * (252 ** 0.5)  # 假设一年252个交易日
        
        # 交易次数
        self.trade_count = (results['trade'] != 0).sum()
        
        # 胜率 (简化计算)
        profitable_trades = (results[results['trade'] != 0]['strategy_returns'] > 0).sum()
        self.win_rate = profitable_trades / self.trade_count if self.trade_count > 0 else 0
        
    def optimize_parameters(self, fast_range=(5, 20), slow_range=(20, 60), step=1):
        """参数优化 - VectorBT的特色功能，向量化批量计算"""
        # 准备参数网格
        fast_params = range(fast_range[0], fast_range[1] + 1, step)
        slow_params = range(slow_range[0], slow_range[1] + 1, step)
        
        best_sharpe = -np.inf
        best_params = None
        results = []
        
        # 批量参数测试
        for fast in fast_params:
            for slow in slow_params:
                if fast >= slow:  # 快线周期不应大于等于慢线周期
                    continue
                
                start_time = time.time()
                
                # 计算信号
                self.calculate_signals(fast_ma=fast, slow_ma=slow)
                
                # 执行回测
                self.backtest()
                
                duration = time.time() - start_time
                
                # 记录结果
                result = {
                    'fast_ma': fast, 
                    'slow_ma': slow,
                    'total_return': self.total_return,
                    'annual_return': self.annual_return,
                    'max_drawdown': self.max_drawdown,
                    'sharpe_ratio': self.sharpe_ratio,
                    'trade_count': self.trade_count,
                    'win_rate': self.win_rate,
                    'execution_time': duration
                }
                results.append(result)
                
                # 更新最佳参数
                if self.sharpe_ratio > best_sharpe:
                    best_sharpe = self.sharpe_ratio
                    best_params = (fast, slow)
        
        # 转换为DataFrame
        self.optimization_results = pd.DataFrame(results)
        self.best_params = best_params
        
        return self.optimization_results, best_params
    
    def plot_results(self):
        """绘制回测结果图表"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 15), gridspec_kw={'height_ratios': [2, 1, 1]})
        
        # 绘制价格和均线
        ax1 = axes[0]
        ax1.plot(self.results.index, self.results['close'], label='收盘价', alpha=0.7)
        ax1.plot(self.results.index, self.results['fast_ma'], label=f"快速均线({self.results['fast_ma'].name}日)", alpha=0.8)
        ax1.plot(self.results.index, self.results['slow_ma'], label=f"慢速均线({self.results['slow_ma'].name}日)", alpha=0.8)
        
        # 标记买卖点
        buy_signals = self.results[self.results['signal'] == 1]
        sell_signals = self.results[self.results['signal'] == -1]
        ax1.scatter(buy_signals.index, buy_signals['close'], color='red', marker='^', s=100, label='买入信号')
        ax1.scatter(sell_signals.index, sell_signals['close'], color='green', marker='v', s=100, label='卖出信号')
        
        ax1.set_title('双均线交叉策略回测结果', fontsize=15)
        ax1.set_xlabel('日期')
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制资金曲线
        ax2 = axes[1]
        ax2.plot(self.results.index, self.results['equity'], label='策略资金曲线', color='blue')
        ax2.plot(self.results.index, self.initial_capital * self.results['cum_returns'], label='买入持有资金曲线', color='grey', alpha=0.5)
        ax2.set_xlabel('日期')
        ax2.set_ylabel('资金')
        ax2.legend()
        ax2.grid(True)
        
        # 绘制回撤
        ax3 = axes[2]
        ax3.fill_between(self.results.index, self.results['drawdown'], color='red', alpha=0.3)
        ax3.set_title('回撤')
        ax3.set_xlabel('日期')
        ax3.set_ylabel('回撤比例')
        ax3.grid(True)
        
        plt.tight_layout()
        plt.savefig('vectorbt_backtest_results.png', dpi=300)
        plt.show()
        
    def plot_optimization_results(self):
        """绘制参数优化热力图"""
        if not hasattr(self, 'optimization_results'):
            print("请先运行参数优化")
            return
        
        # 转换为透视表格式
        pivot_table = self.optimization_results.pivot_table(
            index='slow_ma', 
            columns='fast_ma', 
            values='sharpe_ratio'
        )
        
        plt.figure(figsize=(12, 10))
        
        # 绘制热力图
        sns.heatmap(pivot_table, annot=True, cmap='viridis', fmt='.2f')
        plt.title('参数优化结果 - 夏普比率', fontsize=15)
        plt.xlabel('快速均线周期')
        plt.ylabel('慢速均线周期')
        
        # 标记最佳参数
        best_fast, best_slow = self.best_params
        plt.plot(pivot_table.columns.get_loc(best_fast) + 0.5, 
                 pivot_table.index.get_loc(best_slow) + 0.5, 
                 'r*', markersize=20)
        
        plt.tight_layout()
        plt.savefig('vectorbt_optimization_results.png', dpi=300)
        plt.show()

def main():
    """主函数"""
    start_time = time.time()
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # 初始内存 (MB)
    
    print("============= VectorBT风格回测引擎 - 双均线交叉策略 =============")
    
    # 初始化回测器
    backtester = VectorizedBacktester(initial_capital=100000)
    
    # 尝试加载数据，若无则生成模拟数据
    try:
        # 首先尝试读取上证指数数据
        data_path = "../data/backtest_data/daily/SHSE/000001/price.csv"
        df = backtester.load_data(data_path, '2020-01-01', '2022-12-31')
    except Exception as e:
        print(f"加载数据出错: {e}")
        # 失败则使用模拟数据
        df = backtester.load_data(start_date='2020-01-01', end_date='2022-12-31')
    
    print(f"数据加载完成，共 {len(df)} 个交易日")
    
    # 计算信号
    print("计算双均线交叉信号...")
    backtester.calculate_signals(fast_ma=10, slow_ma=30)
    
    # 执行回测
    print("执行回测...")
    results = backtester.backtest(commission_rate=0.001)
    
    # 打印回测性能指标
    print("\n============= 回测结果 =============")
    print(f"总收益率: {backtester.total_return:.2%}")
    print(f"年化收益率: {backtester.annual_return:.2%}")
    print(f"最大回撤: {backtester.max_drawdown:.2%}")
    print(f"夏普比率: {backtester.sharpe_ratio:.2f}")
    print(f"交易次数: {backtester.trade_count}")
    print(f"胜率: {backtester.win_rate:.2%}")
    
    # 参数优化示例 (小范围)
    print("\n============= 执行参数优化 =============")
    optimization_start = time.time()
    opt_results, best_params = backtester.optimize_parameters(
        fast_range=(5, 20), 
        slow_range=(20, 50), 
        step=5
    )
    optimization_time = time.time() - optimization_start
    
    print(f"参数优化完成，耗时: {optimization_time:.2f}秒")
    print(f"最佳参数: 快线={best_params[0]}, 慢线={best_params[1]}")
    print("最佳参数性能:")
    best_result = opt_results[
        (opt_results['fast_ma'] == best_params[0]) & 
        (opt_results['slow_ma'] == best_params[1])
    ].iloc[0]
    print(f"夏普比率: {best_result['sharpe_ratio']:.2f}")
    print(f"年化收益率: {best_result['annual_return']:.2%}")
    print(f"最大回撤: {best_result['max_drawdown']:.2%}")
    
    # 绘制回测结果
    try:
        # 使用最佳参数重新运行一次
        backtester.calculate_signals(fast_ma=best_params[0], slow_ma=best_params[1])
        backtester.backtest()
        backtester.plot_results()
        
        # 如果有matplotlib的高级扩展库seaborn，绘制参数优化热力图
        try:
            import seaborn as sns
            backtester.plot_optimization_results()
        except ImportError:
            print("未安装seaborn库，跳过参数优化可视化")
    except Exception as e:
        print(f"绘图过程中出错: {e}")
    
    # 计算内存使用和总耗时
    end_time = time.time()
    final_memory = process.memory_info().rss / 1024 / 1024  # 最终内存 (MB)
    
    print("\n============= 性能指标 =============")
    print(f"总耗时: {end_time - start_time:.2f}秒")
    print(f"内存使用: {final_memory - initial_memory:.2f} MB")
    print(f"参数优化耗时: {optimization_time:.2f}秒")
    print(f"平均每组参数测试耗时: {optimization_time / len(opt_results):.4f}秒")
    print("注：VectorBT核心优势在于向量化运算，真实VectorBT速度更快")

if __name__ == "__main__":
    # 检查是否已安装依赖库
    try:
        import numpy
        import pandas
        import matplotlib.pyplot
        import psutil
        # 导入可选库，用于高级可视化
        try:
            import seaborn
        except ImportError:
            print("提示: 安装seaborn可以获得更好的可视化效果")
        main()
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请安装依赖: pip install numpy pandas matplotlib psutil seaborn") 