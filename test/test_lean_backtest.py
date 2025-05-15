#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟LEAN框架的双均线交叉策略回测脚本

LEAN框架特点：
1. 事件驱动架构：通过事件处理数据流，更符合实盘交易逻辑
2. 模块化设计：清晰的数据、策略、执行和风控模块划分
3. 实盘与回测统一接口：策略代码可无缝从回测切换到实盘
4. 多市场、多资产支持：可支持股票、期货、期权等多种资产
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# 模拟LEAN框架的模块化结构
class EventArgs:
    pass

class MarketDataEventArgs(EventArgs):
    def __init__(self, symbol, time, open_price, high, low, close, volume):
        self.Symbol = symbol
        self.Time = time
        self.Open = open_price
        self.High = high
        self.Low = low
        self.Close = close
        self.Volume = volume

class OrderEventArgs(EventArgs):
    def __init__(self, symbol, time, quantity, is_buy, price):
        self.Symbol = symbol
        self.Time = time
        self.Quantity = quantity
        self.Direction = "Buy" if is_buy else "Sell"
        self.Price = price
        self.Status = "Filled"  # 简化处理，假设订单直接成交

class Securities:
    def __init__(self):
        self.holdings = {}  # 持仓信息

    def add_security(self, symbol):
        self.holdings[symbol] = {"Quantity": 0, "AveragePrice": 0}

    def update_holding(self, symbol, quantity, price):
        if symbol not in self.holdings:
            self.add_security(symbol)

        old_quantity = self.holdings[symbol]["Quantity"]
        old_avg_price = self.holdings[symbol]["AveragePrice"]
        
        new_quantity = old_quantity + quantity
        
        if new_quantity != 0:
            if quantity > 0:  # 买入
                new_avg_price = (old_quantity * old_avg_price + quantity * price) / new_quantity
            else:  # 卖出
                new_avg_price = old_avg_price if old_quantity > 0 else 0
        else:
            new_avg_price = 0
        
        self.holdings[symbol]["Quantity"] = new_quantity
        self.holdings[symbol]["AveragePrice"] = new_avg_price

class Portfolio:
    def __init__(self, initial_capital=100000):
        self.Cash = initial_capital
        self.TotalPortfolioValue = initial_capital
        self.Securities = Securities()
        self.Transactions = []
    
    def add_transaction(self, symbol, time, quantity, price, direction):
        cost = quantity * price
        if direction == "Buy":
            self.Cash -= cost
        else:
            self.Cash += cost
        
        self.Securities.update_holding(symbol, 
                                      quantity if direction == "Buy" else -quantity, 
                                      price)
        
        self.Transactions.append({
            "Time": time,
            "Symbol": symbol,
            "Direction": direction,
            "Quantity": quantity,
            "Price": price,
            "Value": cost
        })
    
    def update_portfolio_value(self, current_prices):
        portfolio_value = self.Cash
        for symbol, holding in self.Securities.holdings.items():
            if symbol in current_prices:
                portfolio_value += holding["Quantity"] * current_prices[symbol]
        
        self.TotalPortfolioValue = portfolio_value
        return portfolio_value

class QCAlgorithm:
    def __init__(self):
        self.Portfolio = Portfolio()
        self._current_time = None
        self._symbols = []
        self._data = {}
        self._indicators = {}
        self._current_prices = {}
        self._order_events = []
        self._market_data_events = []
    
    def AddEquity(self, symbol):
        self._symbols.append(symbol)
        self.Portfolio.Securities.add_security(symbol)
    
    def SetStartDate(self, year, month, day):
        self._start_date = datetime(year, month, day)
    
    def SetEndDate(self, year, month, day):
        self._end_date = datetime(year, month, day)
    
    def SetCash(self, amount):
        self.Portfolio.Cash = amount
        self.Portfolio.TotalPortfolioValue = amount
    
    def MarketOrder(self, symbol, quantity):
        # 简化处理，假设市价单立即以当前价格成交
        if symbol not in self._current_prices:
            print(f"找不到{symbol}的市场价格，订单无法执行")
            return
        
        price = self._current_prices[symbol]
        order_event = OrderEventArgs(symbol, self._current_time, quantity, 
                                   quantity > 0, price)
        
        # 更新投资组合
        direction = "Buy" if quantity > 0 else "Sell"
        self.Portfolio.add_transaction(symbol, self._current_time, abs(quantity), 
                                     price, direction)
        
        self._order_events.append(order_event)
        return order_event
    
    def SMA(self, symbol, period):
        """简单移动平均线指标"""
        indicator_name = f"SMA_{symbol}_{period}"
        if indicator_name not in self._indicators:
            self._indicators[indicator_name] = {
                "type": "SMA",
                "symbol": symbol,
                "period": period,
                "values": [],
                "times": []
            }
        return indicator_name
    
    def GetIndicatorValue(self, indicator_name):
        """获取指标当前值"""
        if indicator_name in self._indicators and len(self._indicators[indicator_name]["values"]) > 0:
            return self._indicators[indicator_name]["values"][-1]
        return None
    
    def _update_indicators(self):
        """更新所有指标的值"""
        for name, indicator in self._indicators.items():
            if indicator["type"] == "SMA":
                symbol = indicator["symbol"]
                period = indicator["period"]
                if symbol in self._data:
                    # 获取历史价格数据
                    hist_data = [bar["Close"] for bar in self._data[symbol] 
                               if bar["Time"] <= self._current_time]
                    
                    # 计算SMA值
                    if len(hist_data) >= period:
                        sma_value = sum(hist_data[-period:]) / period
                        indicator["values"].append(sma_value)
                        indicator["times"].append(self._current_time)
    
    def _load_backtest_data(self, symbol, file_path=None):
        """加载回测数据，如果文件不存在则生成模拟数据"""
        if file_path and os.path.exists(file_path):
            # 从文件加载数据
            df = pd.read_csv(file_path, parse_dates=["Time"])
            data = []
            for _, row in df.iterrows():
                data.append({
                    "Time": row["Time"],
                    "Open": row["Open"],
                    "High": row["High"],
                    "Low": row["Low"],
                    "Close": row["Close"],
                    "Volume": row["Volume"]
                })
            return data
        else:
            # 生成模拟数据
            print(f"为{symbol}生成模拟回测数据")
            np.random.seed(42)
            data = []
            current_date = self._start_date
            
            # 模拟生成价格
            base_price = 3000  # 基础价格
            price = base_price
            while current_date <= self._end_date:
                # 跳过周末
                if current_date.weekday() < 5:  # 0-4是周一至周五
                    # 生成当日价格
                    daily_volatility = np.random.normal(0, 1) * 30  # 日波动
                    open_price = price
                    close_price = max(0, open_price + daily_volatility)
                    high_price = max(open_price, close_price) + abs(np.random.normal(0, 1) * 10)
                    low_price = min(open_price, close_price) - abs(np.random.normal(0, 1) * 10)
                    volume = int(np.random.normal(1000000, 500000))
                    
                    data.append({
                        "Time": current_date,
                        "Open": open_price,
                        "High": high_price,
                        "Low": low_price,
                        "Close": close_price,
                        "Volume": volume
                    })
                    
                    price = close_price  # 更新收盘价作为下一个交易日的基础
                
                current_date += timedelta(days=1)
            
            return data
    
    def _run_backtest(self):
        """运行回测"""
        # 加载回测数据
        for symbol in self._symbols:
            self._data[symbol] = self._load_backtest_data(symbol)
        
        # 获取所有交易日
        trading_days = sorted(list(set([bar["Time"].date() for symbol in self._data 
                                      for bar in self._data[symbol]])))
        
        # 按时间顺序处理每一天的数据
        for day in trading_days:
            day_dt = datetime.combine(day, datetime.min.time())
            self._current_time = day_dt
            
            # 更新当日价格
            for symbol in self._symbols:
                day_bars = [bar for bar in self._data[symbol] if bar["Time"].date() == day]
                if day_bars:
                    self._current_prices[symbol] = day_bars[0]["Close"]
                    
                    # 创建市场数据事件
                    bar = day_bars[0]
                    market_event = MarketDataEventArgs(
                        symbol, bar["Time"], bar["Open"], bar["High"], 
                        bar["Low"], bar["Close"], bar["Volume"]
                    )
                    self._market_data_events.append(market_event)
            
            # 更新指标
            self._update_indicators()
            
            # 运行策略逻辑
            self.OnData(EventArgs())
            
            # 更新投资组合价值
            self.Portfolio.update_portfolio_value(self._current_prices)
    
    def calculate_performance_metrics(self):
        """计算回测性能指标"""
        if not self._market_data_events:
            return {}
        
        # 提取每日投资组合价值
        dates = sorted(list(set([evt.Time.date() for evt in self._market_data_events])))
        portfolio_values = []
        
        for day in dates:
            day_dt = datetime.combine(day, datetime.min.time())
            
            # 更新当前价格
            for symbol in self._symbols:
                day_bars = [bar for bar in self._data[symbol] if bar["Time"].date() == day]
                if day_bars:
                    self._current_prices[symbol] = day_bars[0]["Close"]
            
            # 更新投资组合价值
            portfolio_value = self.Portfolio.update_portfolio_value(self._current_prices)
            portfolio_values.append(portfolio_value)
        
        # 计算收益率
        returns = pd.Series(portfolio_values).pct_change().dropna()
        
        # 计算指标
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1 if portfolio_values else 0
        annual_return = ((1 + total_return) ** (252 / len(returns)) - 1) if len(returns) > 0 else 0
        
        # 计算最大回撤
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max) - 1
        max_drawdown = drawdown.min()
        
        # 计算夏普比率 (假设无风险利率为0)
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'trading_days': len(dates),
            'trades': len(self.Portfolio.Transactions)
        }
    
    def plot_backtest_results(self):
        """绘制回测结果图表"""
        if not self._market_data_events:
            print("没有足够的数据来绘制图表")
            return
        
        # 准备数据
        dates = sorted(list(set([evt.Time.date() for evt in self._market_data_events])))
        portfolio_values = []
        symbol_prices = {symbol: [] for symbol in self._symbols}
        
        for day in dates:
            day_dt = datetime.combine(day, datetime.min.time())
            
            # 更新当前价格并记录
            for symbol in self._symbols:
                day_bars = [bar for bar in self._data[symbol] if bar["Time"].date() == day]
                if day_bars:
                    self._current_prices[symbol] = day_bars[0]["Close"]
                    symbol_prices[symbol].append(day_bars[0]["Close"])
            
            # 更新投资组合价值
            portfolio_value = self.Portfolio.update_portfolio_value(self._current_prices)
            portfolio_values.append(portfolio_value)
        
        # 绘图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # 绘制价格和投资组合价值
        ax1.plot(dates, portfolio_values, label='Portfolio Value', linewidth=2)
        
        for symbol in self._symbols:
            if len(symbol_prices[symbol]) == len(dates):  # 确保数据完整
                # 归一化价格以方便比较
                normalized_prices = np.array(symbol_prices[symbol]) / symbol_prices[symbol][0] * portfolio_values[0]
                ax1.plot(dates, normalized_prices, label=f'{symbol} (Normalized)', alpha=0.7)
        
        # 标记交易点
        for transaction in self.Portfolio.Transactions:
            marker = '^' if transaction["Direction"] == "Buy" else 'v'
            color = 'g' if transaction["Direction"] == "Buy" else 'r'
            ax1.scatter(transaction["Time"].date(), portfolio_values[dates.index(transaction["Time"].date())], 
                       s=100, marker=marker, color=color, zorder=5)
        
        ax1.set_title('LEAN Framework Backtest Results')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制指标
        for name, indicator in self._indicators.items():
            if len(indicator["values"]) > 0:
                # 转换成日期格式以匹配主图
                indicator_dates = [t.date() for t in indicator["times"]]
                # 只使用与主图日期范围重叠的部分
                valid_indices = [i for i, d in enumerate(indicator_dates) if d in dates]
                
                if valid_indices:
                    ax2.plot(
                        [indicator_dates[i] for i in valid_indices],
                        [indicator["values"][i] for i in valid_indices],
                        label=name
                    )
        
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Indicator Value')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def Initialize(self):
        """初始化策略，子类需要实现"""
        pass
    
    def OnData(self, data):
        """处理数据，子类需要实现"""
        pass

# 实现双均线交叉策略
class MACrossoverStrategy(QCAlgorithm):
    def Initialize(self):
        # 设置回测参数
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2022, 12, 31)
        self.SetCash(100000)
        
        # 添加交易标的
        self.symbol = '000001.XSHG'
        self.AddEquity(self.symbol)
        
        # 添加指标
        self.fast_ma = self.SMA(self.symbol, 10)
        self.slow_ma = self.SMA(self.symbol, 30)
        
        # 策略状态
        self.previous_fast = None
        self.previous_slow = None
        self.is_invested = False
    
    def OnData(self, data):
        # 获取当前移动平均线值
        fast_ma_value = self.GetIndicatorValue(self.fast_ma)
        slow_ma_value = self.GetIndicatorValue(self.slow_ma)
        
        # 确保两条移动平均线都有值
        if fast_ma_value is None or slow_ma_value is None:
            return
        
        # 存储之前的值用于交叉判断
        if self.previous_fast is not None and self.previous_slow is not None:
            # 检查金叉（快线上穿慢线）
            if self.previous_fast <= self.previous_slow and fast_ma_value > slow_ma_value:
                if not self.is_invested:
                    # 计算购买数量
                    price = self._current_prices.get(self.symbol, 0)
                    if price > 0:
                        shares_to_buy = int(self.Portfolio.Cash * 0.95 / price)  # 使用95%的现金
                        if shares_to_buy > 0:
                            self.MarketOrder(self.symbol, shares_to_buy)
                            self.is_invested = True
                            print(f"{self._current_time.date()}: 买入 {shares_to_buy} 股 {self.symbol} @ {price:.2f}")
            
            # 检查死叉（快线下穿慢线）
            elif self.previous_fast >= self.previous_slow and fast_ma_value < slow_ma_value:
                if self.is_invested:
                    # 卖出全部持仓
                    holdings = self.Portfolio.Securities.holdings.get(self.symbol, {}).get("Quantity", 0)
                    if holdings > 0:
                        price = self._current_prices.get(self.symbol, 0)
                        self.MarketOrder(self.symbol, -holdings)
                        self.is_invested = False
                        print(f"{self._current_time.date()}: 卖出 {holdings} 股 {self.symbol} @ {price:.2f}")
        
        # 更新之前的值
        self.previous_fast = fast_ma_value
        self.previous_slow = slow_ma_value

def test_lean_backtest():
    """
    使用LEAN框架风格测试双均线交叉策略
    """
    # 创建策略实例
    strategy = MACrossoverStrategy()
    
    # 初始化策略
    strategy.Initialize()
    
    # 运行回测
    strategy._run_backtest()
    
    # 计算和输出绩效指标
    metrics = strategy.calculate_performance_metrics()
    
    print("\n====== LEAN Framework 回测结果 ======")
    print(f"总收益率: {metrics['total_return']:.4f}")
    print(f"年化收益率: {metrics['annual_return']:.4f}")
    print(f"夏普比率: {metrics['sharpe_ratio']:.4f}")
    print(f"最大回撤: {metrics['max_drawdown']:.4f}")
    print(f"交易天数: {metrics['trading_days']}")
    print(f"交易次数: {metrics['trades']}")
    
    # 绘制回测结果
    try:
        strategy.plot_backtest_results()
    except Exception as e:
        print(f"无法绘制图表: {e}")
    
    return strategy

if __name__ == "__main__":
    strategy = test_lean_backtest() 