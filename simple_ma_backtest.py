#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版移动平均线交叉策略回测

直接在脚本中实现回测逻辑，不依赖于test模块
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

# 导入策略和数据提供者
try:
    from strategy.strategyA.ma_cross_strategy import MACrossStrategy
    from qte_data.gm_data_provider import GmDataProvider
    from qte_core.event_loop import EventLoop
except ImportError as e:
    logger.error(f"导入模块出错: {e}")
    logger.error("请确保已安装所有依赖，并且当前目录是项目根目录")
    sys.exit(1)

# 掘金量化API令牌
TOKEN = "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"


class SimpleBacktester:
    """
    简单回测器类
    """
    
    def __init__(self, strategy, initial_capital=100000.0):
        """
        初始化回测器
        
        Args:
            strategy: 交易策略
            initial_capital: 初始资金
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        
        # 回测结果
        self.equity = [initial_capital]  # 账户净值
        self.returns = []  # 收益率
        self.positions = []  # 持仓记录
        self.trades = []  # 交易记录
        
        # 当前持仓状态
        self.current_position = 0
        self.current_cash = initial_capital
        self.current_shares = 0
        
        # 记录价格数据
        self.price_data = []
        
        # 当前净值
        self.current_equity = initial_capital
    
    def run(self, price_data):
        """
        运行回测
        
        Args:
            price_data: 历史价格数据DataFrame，必须包含timestamp和close列
            
        Returns:
            dict: 回测结果
        """
        logger.info(f"开始回测，数据点数: {len(price_data)}")
        
        # 记录历史价格
        self.price_data = price_data.to_dict('records')
        
        # 遍历所有K线数据
        for i, bar in enumerate(self.price_data):
            # 调用策略处理K线
            signal = self.strategy.on_bar(bar)
            
            # 处理交易信号
            self._process_signal(bar, signal)
            
            # 更新净值
            self._update_equity(bar)
            
            # 输出进度
            if i % 50 == 0 and i > 0:
                logger.info(f"回测进度: {i}/{len(self.price_data)}")
        
        # 计算回测指标
        return self._calculate_metrics()
    
    def _process_signal(self, bar, signal):
        """
        处理交易信号
        
        Args:
            bar: 当前K线数据
            signal: 交易信号
        """
        action = signal['action']
        position = signal['position']
        
        # 无交易信号
        if action == 'HOLD':
            return
        
        # 记录交易
        trade = {
            'timestamp': bar['timestamp'],
            'price': bar['close'],
            'action': action,
            'position': position
        }
        
        # 执行交易
        if action == 'BUY':
            # 如果当前是空头，先平仓
            if self.current_position < 0:
                self.current_cash += self.current_shares * bar['close']
                trade['shares'] = self.current_shares
                self.current_shares = 0
            
            # 做多
            shares_to_buy = self.current_cash / bar['close']
            self.current_shares = shares_to_buy
            self.current_cash = 0
            self.current_position = 1
            
            trade['shares'] = shares_to_buy
        
        elif action == 'SELL':
            # 如果当前是多头，先平仓
            if self.current_position > 0:
                self.current_cash += self.current_shares * bar['close']
                trade['shares'] = -self.current_shares
                self.current_shares = 0
            
            # 做空
            shares_to_sell = self.current_cash / bar['close']
            self.current_shares = -shares_to_sell
            self.current_cash = 0
            self.current_position = -1
            
            trade['shares'] = -shares_to_sell
        
        elif action == 'CLOSE':
            # 平仓
            if self.current_position != 0:
                self.current_cash += abs(self.current_shares) * bar['close']
                
                # 记录平仓的股数，保持正负号
                trade['shares'] = -self.current_shares
                
                self.current_shares = 0
                self.current_position = 0
        
        # 记录交易
        self.trades.append(trade)
        
        # 记录持仓
        self.positions.append({
            'timestamp': bar['timestamp'],
            'position': self.current_position,
            'shares': self.current_shares,
            'cash': self.current_cash
        })
    
    def _update_equity(self, bar):
        """
        更新账户净值
        
        Args:
            bar: 当前K线数据
        """
        # 计算当前净值
        if self.current_position == 0:
            current_equity = self.current_cash
        else:
            current_equity = self.current_cash + self.current_shares * bar['close']
        
        # 记录净值
        self.equity.append(current_equity)
        
        # 计算收益率
        if len(self.equity) > 1:
            daily_return = (current_equity - self.equity[-2]) / self.equity[-2]
            self.returns.append(daily_return)
        
        # 更新当前净值
        self.current_equity = current_equity
    
    def _calculate_metrics(self):
        """
        计算回测指标
        
        Returns:
            dict: 回测指标
        """
        # 转换为DataFrame
        price_df = pd.DataFrame(self.price_data)
        
        # 无交易数据
        if not self.trades:
            logger.warning("回测期间没有产生任何交易信号")
            return {
                'total_return': 0,
                'annual_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'equity_curve': self.equity,
                'price_data': price_df,
                'trades': []
            }
        
        # 计算总收益率
        total_return = (self.equity[-1] - self.initial_capital) / self.initial_capital
        
        # 计算年化收益率
        days = (self.price_data[-1]['timestamp'] - self.price_data[0]['timestamp']).days
        annual_return = total_return * (365 / max(days, 1))
        
        # 计算最大回撤
        equity_series = pd.Series(self.equity)
        max_drawdown = ((equity_series.cummax() - equity_series) / equity_series.cummax()).max()
        
        # 计算夏普比率
        if self.returns:
            returns_series = pd.Series(self.returns)
            sharpe_ratio = (returns_series.mean() * 252) / (returns_series.std() * np.sqrt(252))
        else:
            sharpe_ratio = 0
        
        # 交易记录
        trades_df = pd.DataFrame(self.trades)
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'equity_curve': self.equity,
            'price_data': price_df,
            'trades': trades_df
        }
    
    def plot_results(self, results=None):
        """
        绘制回测结果图表
        
        Args:
            results: 回测结果，如果为None则使用当前结果
        """
        if results is None:
            # 使用当前结果
            equity_curve = self.equity
            price_data = pd.DataFrame(self.price_data)
            trades = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        else:
            equity_curve = results['equity_curve']
            price_data = results['price_data']
            trades = results['trades']
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 绘制价格和信号
        ax1.plot(price_data['timestamp'], price_data['close'], label='Close Price')
        
        # 计算移动平均线
        if len(price_data) >= self.strategy.long_window:
            price_data['short_ma'] = price_data['close'].rolling(window=self.strategy.short_window).mean()
            price_data['long_ma'] = price_data['close'].rolling(window=self.strategy.long_window).mean()
            
            ax1.plot(price_data['timestamp'], price_data['short_ma'], 
                    label=f'Short MA ({self.strategy.short_window})', alpha=0.7)
            ax1.plot(price_data['timestamp'], price_data['long_ma'], 
                    label=f'Long MA ({self.strategy.long_window})', alpha=0.7)
        
        # 标记交易
        if not trades.empty:
            # 买入信号
            buy_trades = trades[trades['action'] == 'BUY']
            if not buy_trades.empty:
                ax1.scatter(buy_trades['timestamp'], buy_trades['price'], 
                          marker='^', color='g', label='Buy', s=100)
            
            # 卖出信号
            sell_trades = trades[trades['action'] == 'SELL']
            if not sell_trades.empty:
                ax1.scatter(sell_trades['timestamp'], sell_trades['price'], 
                          marker='v', color='r', label='Sell', s=100)
            
            # 平仓信号
            close_trades = trades[trades['action'] == 'CLOSE']
            if not close_trades.empty:
                ax1.scatter(close_trades['timestamp'], close_trades['price'], 
                          marker='o', color='blue', label='Close', s=80)
        
        ax1.set_title('Price Chart with Signals')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制净值曲线
        ax2.plot(price_data['timestamp'], equity_curve[1:], label='Equity', color='purple')
        ax2.set_title('Equity Curve')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Equity')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()


def generate_random_data(start_date, end_date, seed=42):
    """
    生成随机价格数据用于测试
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        seed: 随机数种子
        
    Returns:
        DataFrame: 包含OHLCV数据的DataFrame
    """
    # 设置随机种子
    np.random.seed(seed)
    
    # 创建日期范围（仅工作日）
    all_dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # 生成随机价格
    price = 100  # 初始价格
    prices = [price]
    
    for _ in range(1, len(all_dates)):
        movement = np.random.normal(0, 1)  # 每天价格变动百分比
        price = price * (1 + movement/100)
        prices.append(price)
    
    # 创建OHLCV数据
    data = pd.DataFrame({
        'timestamp': all_dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.01)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.01)) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, size=len(all_dates))
    })
    
    return data


def run_backtest_on_symbol(symbol, start_date, end_date, short_window=5, long_window=20):
    """
    在指定品种上运行回测
    
    Args:
        symbol: 交易品种代码
        start_date: 回测开始日期
        end_date: 回测结束日期
        short_window: 短期均线周期
        long_window: 长期均线周期
        
    Returns:
        dict: 回测结果
    """
    # 创建事件循环
    event_loop = EventLoop()
    
    # 创建数据提供者
    data_dir = os.path.join("test", "data", "backtest_data")
    provider = GmDataProvider(token=TOKEN, event_loop=event_loop, data_dir=data_dir)
    
    try:
        # 获取历史数据
        logger.info(f"尝试从掘金数据提供者获取 {symbol} 从 {start_date} 到 {end_date} 的数据")
        bars_gen = provider.get_historical_bars(symbol, start_date, end_date)
        
        if bars_gen:
            # 转换为DataFrame
            bars = list(bars_gen)
            df = pd.DataFrame(bars)
            logger.info(f"成功获取 {len(df)} 条历史数据")
        else:
            logger.warning(f"无法从掘金获取数据，将使用模拟数据")
            df = generate_random_data(start_date, end_date)
            logger.info(f"生成了 {len(df)} 条模拟数据")
    
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        logger.warning("将使用模拟数据进行回测")
        df = generate_random_data(start_date, end_date)
        logger.info(f"生成了 {len(df)} 条模拟数据")
    
    # 创建策略
    strategy = MACrossStrategy(short_window=short_window, long_window=long_window)
    
    # 创建回测器
    backtester = SimpleBacktester(strategy)
    
    # 运行回测
    results = backtester.run(df)
    
    # 打印回测结果
    logger.info("\n===== 回测结果 =====")
    logger.info(f"总收益率: {results['total_return']:.2%}")
    logger.info(f"年化收益率: {results['annual_return']:.2%}")
    logger.info(f"最大回撤: {results['max_drawdown']:.2%}")
    logger.info(f"夏普比率: {results['sharpe_ratio']:.2f}")
    
    # 统计交易
    if isinstance(results['trades'], pd.DataFrame) and not results['trades'].empty:
        buy_trades = results['trades'][results['trades']['action'] == 'BUY']
        sell_trades = results['trades'][results['trades']['action'] == 'SELL']
        close_trades = results['trades'][results['trades']['action'] == 'CLOSE']
        
        logger.info(f"交易次数: {len(results['trades'])}")
        logger.info(f"买入次数: {len(buy_trades)}")
        logger.info(f"卖出次数: {len(sell_trades)}")
        logger.info(f"平仓次数: {len(close_trades)}")
    
    # 绘制回测结果
    backtester.plot_results(results)
    
    return results


def main():
    """主函数"""
    logger.info("===== 移动平均线交叉策略回测 =====")
    
    # 定义回测参数
    symbol = "SHSE.000001"  # 上证指数
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    short_window = 5
    long_window = 20
    
    logger.info("回测参数:")
    logger.info(f"交易品种: {symbol}")
    logger.info(f"回测周期: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"短期均线: {short_window}日")
    logger.info(f"长期均线: {long_window}日")
    
    try:
        # 运行回测
        run_backtest_on_symbol(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            short_window=short_window,
            long_window=long_window
        )
        
    except Exception as e:
        logger.error(f"回测过程出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    logger.info("\n回测完成")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 