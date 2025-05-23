#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抛硬币交易策略示例

策略逻辑：
1. 随机50%概率做多或做空
2. 达到1%回撤时平仓
3. 循环往复

使用QTE框架和vnpy集成，获取真实历史数据进行回测
"""

import sys
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from qte.data.sources.gm_quant import GmQuantSource
from qte.data.sources.local_csv import LocalCsvSource
from qte.data.sources.binance_api import BinanceApiSource
from qte.vnpy.data_source import VnpyDataSource
from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
from vnpy.event import EventEngine

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    
    def update_pnl(self, current_price: float):
        """更新未实现盈亏"""
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:  # short
            self.unrealized_pnl = (self.entry_price - current_price) * self.size

@dataclass
class Trade:
    """交易记录"""
    symbol: str
    side: str
    size: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    drawdown_pct: float

class CoinFlipStrategy:
    """抛硬币交易策略"""
    
    def __init__(self, 
                 symbols: List[str] = None,
                 initial_capital: float = 100000.0,
                 position_size: float = 0.1,  # 10%仓位
                 drawdown_threshold: float = 0.01,  # 1%回撤平仓
                 data_source: str = 'binance'):  # 默认使用币安
        """
        初始化策略
        
        Args:
            symbols: 交易标的列表
            initial_capital: 初始资金
            position_size: 单次开仓仓位比例
            drawdown_threshold: 回撤阈值
            data_source: 数据源类型 ('gm', 'vnpy', 'binance', 'mock')
        """
        # 根据数据源类型设置默认标的
        if symbols is None:
            if data_source == 'binance':
                symbols = ['BTCUSDT', 'ETHUSDT']  # 币安交易对
            else:
                symbols = ['SHSE.600000']  # 股票代码
        
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size = position_size
        self.drawdown_threshold = drawdown_threshold
        self.data_source_type = data_source
        
        # 交易状态
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
        # 数据源
        self.data_source = None
        self.price_data: Dict[str, pd.DataFrame] = {}
        
        # 随机种子
        random.seed(42)
        np.random.seed(42)
        
        print(f"🎲 抛硬币策略初始化")
        print(f"   交易标的: {self.symbols}")
        print(f"   初始资金: {self.initial_capital:,.2f}")
        print(f"   仓位大小: {self.position_size:.1%}")
        print(f"   回撤阈值: {self.drawdown_threshold:.1%}")
        print(f"   数据源: {self.data_source_type}")
    
    def setup_data_source(self):
        """设置数据源"""
        if self.data_source_type == 'gm':
            print("🔗 使用掘金数据源...")
            try:
                from gm.api import set_token
                self.data_source = GmQuantSource()
                print("ℹ️  注意：需要设置掘金Token才能获取真实数据")
            except ImportError:
                print("❌ 掘金API包未安装，切换到币安数据源")
                self.data_source_type = 'binance'
                self.setup_data_source()
                return
                
        elif self.data_source_type == 'vnpy':
            print("🔗 使用vnpy数据源...")
            try:
                event_engine = EventEngine()
                self.data_source = VnpyDataSource(
                    gateway_names=["QTE_BINANCE_SPOT"],
                    virtual_exchange_host="localhost:5001"
                )
            except ImportError:
                print("❌ vnpy包未安装，切换到币安数据源")
                self.data_source_type = 'binance'
                self.setup_data_source()
                return
                
        elif self.data_source_type == 'binance':
            print("🔗 使用币安数据源...")
            self.data_source = BinanceApiSource(
                data_dir="data/binance",
                use_cache=True
            )
            if not self.data_source.connect():
                print("❌ 币安API连接失败，切换到模拟数据")
                self.data_source_type = 'mock'
                self.data_source = None
            
        else:
            print("🔗 使用模拟数据...")
            self.data_source = None
    
    def load_data(self, start_date: str, end_date: str):
        """加载历史数据"""
        print(f"📊 加载历史数据: {start_date} 到 {end_date}")
        
        for symbol in self.symbols:
            try:
                if self.data_source and self.data_source_type in ['gm', 'vnpy', 'binance']:
                    # 从真实数据源获取数据
                    df = self.data_source.get_bars(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        frequency='1d'
                    )
                    if df is not None and not df.empty:
                        self.price_data[symbol] = df
                        print(f"   ✅ {symbol}: {len(df)} 条数据")
                    else:
                        print(f"   ❌ {symbol}: 无数据，生成模拟数据")
                        self.price_data[symbol] = self._generate_mock_data(symbol, start_date, end_date)
                else:
                    # 生成模拟数据
                    print(f"   🎲 {symbol}: 生成模拟数据")
                    self.price_data[symbol] = self._generate_mock_data(symbol, start_date, end_date)
                    
            except Exception as e:
                print(f"   ❌ {symbol}: 数据加载失败 - {e}")
                # 生成模拟数据作为备选
                self.price_data[symbol] = self._generate_mock_data(symbol, start_date, end_date)
    
    def _generate_mock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟价格数据"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 根据交易对类型设置初始价格
        if 'BTC' in symbol.upper():
            initial_price = 50000.0  # BTC起始价格
        elif 'ETH' in symbol.upper():
            initial_price = 3000.0   # ETH起始价格
        else:
            initial_price = 100.0    # 其他资产起始价格
        
        # 模拟价格走势：随机游走
        np.random.seed(hash(symbol) % 2**32)
        price = initial_price
        prices = []
        
        for _ in dates:
            # 随机变动-3%到+3%
            change = np.random.normal(0, 0.03)
            price *= (1 + change)
            prices.append(price)
        
        # 生成OHLC数据
        df = pd.DataFrame(index=dates)
        df['close'] = prices
        df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.02, len(df)))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.02, len(df)))
        df['volume'] = np.random.uniform(1000, 50000, len(df))
        
        return df
    
    def flip_coin(self) -> str:
        """抛硬币决定交易方向"""
        return 'long' if random.random() > 0.5 else 'short'
    
    def should_open_position(self, symbol: str) -> bool:
        """判断是否应该开仓"""
        # 如果已有持仓，不再开仓
        if symbol in self.positions:
            return False
        
        # 简单策略：总是有开仓信号（由抛硬币决定方向）
        return True
    
    def should_close_position(self, symbol: str, current_price: float) -> bool:
        """判断是否应该平仓"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        position.update_pnl(current_price)
        
        # 计算回撤比例
        if position.side == 'long':
            drawdown = (position.entry_price - current_price) / position.entry_price
        else:  # short
            drawdown = (current_price - position.entry_price) / position.entry_price
        
        # 如果回撤超过阈值，平仓
        return drawdown >= self.drawdown_threshold
    
    def open_position(self, symbol: str, side: str, price: float, timestamp: datetime):
        """开仓"""
        position_value = self.current_capital * self.position_size
        size = position_value / price
        
        self.positions[symbol] = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            entry_time=timestamp
        )
        
        print(f"📈 开仓: {symbol} {side.upper()} {size:.2f}股 @ {price:.2f} ({timestamp.strftime('%Y-%m-%d')})")
    
    def close_position(self, symbol: str, price: float, timestamp: datetime):
        """平仓"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.update_pnl(price)
        
        # 计算盈亏
        pnl = position.unrealized_pnl
        self.current_capital += pnl
        
        # 计算回撤
        if position.side == 'long':
            drawdown_pct = (position.entry_price - price) / position.entry_price
        else:
            drawdown_pct = (price - position.entry_price) / position.entry_price
        
        # 记录交易
        trade = Trade(
            symbol=symbol,
            side=position.side,
            size=position.size,
            entry_price=position.entry_price,
            exit_price=price,
            entry_time=position.entry_time,
            exit_time=timestamp,
            pnl=pnl,
            drawdown_pct=drawdown_pct
        )
        self.trades.append(trade)
        
        print(f"📉 平仓: {symbol} {position.side.upper()} {position.size:.2f}股 @ {price:.2f} "
              f"盈亏: {pnl:+.2f} 回撤: {drawdown_pct:.2%} ({timestamp.strftime('%Y-%m-%d')})")
        
        # 删除持仓
        del self.positions[symbol]
    
    def update_equity_curve(self, timestamp: datetime):
        """更新资金曲线"""
        total_unrealized_pnl = 0
        for symbol, position in self.positions.items():
            if symbol in self.price_data:
                # 获取当前价格
                current_data = self.price_data[symbol]
                if timestamp in current_data.index:
                    current_price_data = current_data.loc[timestamp, 'close']
                    if hasattr(current_price_data, 'iloc'):
                        current_price = current_price_data.iloc[0]
                    else:
                        current_price = current_price_data
                    position.update_pnl(current_price)
                    total_unrealized_pnl += position.unrealized_pnl
        
        total_equity = self.current_capital + total_unrealized_pnl
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'capital': self.current_capital,
            'unrealized_pnl': total_unrealized_pnl,
            'total_equity': total_equity,
            'positions': len(self.positions)
        })
    
    def run_backtest(self, start_date: str, end_date: str):
        """运行回测"""
        print("\n" + "="*60)
        print(f"🚀 开始回测: {start_date} 到 {end_date}")
        print("="*60)
        
        # 设置数据源
        self.setup_data_source()
        
        # 加载数据
        self.load_data(start_date, end_date)
        
        if not self.price_data:
            print("❌ 无可用数据，回测终止")
            return
        
        # 获取所有交易日
        all_dates = set()
        for df in self.price_data.values():
            all_dates.update(df.index)
        all_dates = sorted(all_dates)
        
        print(f"📅 回测期间: {len(all_dates)} 个交易日")
        print(f"💰 初始资金: {self.initial_capital:,.2f}")
        print()
        
        # 逐日回测
        for i, current_date in enumerate(all_dates):
            # 更新资金曲线
            self.update_equity_curve(current_date)
            
            # 处理每个标的
            for symbol in self.symbols:
                if symbol not in self.price_data:
                    continue
                
                df = self.price_data[symbol]
                if current_date not in df.index:
                    continue
                
                # 确保获取标量值
                current_price_data = df.loc[current_date, 'close']
                if hasattr(current_price_data, 'iloc'):
                    current_price = current_price_data.iloc[0]  # 如果是Series，取第一个值
                else:
                    current_price = current_price_data
                
                # 检查是否需要平仓
                if self.should_close_position(symbol, current_price):
                    self.close_position(symbol, current_price, current_date)
                
                # 检查是否需要开仓
                elif self.should_open_position(symbol):
                    side = self.flip_coin()  # 抛硬币决定方向
                    self.open_position(symbol, side, current_price, current_date)
        
        # 强制平掉所有剩余持仓
        final_date = all_dates[-1]
        for symbol in list(self.positions.keys()):
            if symbol in self.price_data:
                df = self.price_data[symbol]
                if final_date in df.index:
                    final_price_data = df.loc[final_date, 'close']
                    if hasattr(final_price_data, 'iloc'):
                        final_price = final_price_data.iloc[0]
                    else:
                        final_price = final_price_data
                    self.close_position(symbol, final_price, final_date)
        
        # 最终更新资金曲线
        self.update_equity_curve(final_date)
        
        print("\n" + "="*60)
        print("📊 回测结果")
        print("="*60)
        self.print_results()
    
    def print_results(self):
        """打印回测结果"""
        if not self.equity_curve:
            print("❌ 无回测数据")
            return
        
        # 基本统计
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = total_trades - winning_trades
        
        if total_trades > 0:
            win_rate = winning_trades / total_trades
            avg_win = np.mean([t.pnl for t in self.trades if t.pnl > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean([t.pnl for t in self.trades if t.pnl < 0]) if losing_trades > 0 else 0
            total_pnl = sum(t.pnl for t in self.trades)
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            total_pnl = 0
        
        # 资金曲线分析
        equity_series = [e['total_equity'] for e in self.equity_curve]
        final_equity = equity_series[-1]
        max_equity = max(equity_series)
        max_drawdown = (max_equity - min(equity_series)) / max_equity if max_equity > 0 else 0
        
        # 收益率
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        print(f"💰 最终资金: {final_equity:,.2f}")
        print(f"📈 总收益率: {total_return:+.2%}")
        print(f"💸 最大回撤: {max_drawdown:.2%}")
        print(f"🎯 总交易次数: {total_trades}")
        print(f"✅ 盈利交易: {winning_trades} ({win_rate:.1%})")
        print(f"❌ 亏损交易: {losing_trades}")
        
        if winning_trades > 0:
            print(f"💚 平均盈利: {avg_win:+.2f}")
        if losing_trades > 0:
            print(f"💔 平均亏损: {avg_loss:+.2f}")
        
        # 显示最近几笔交易
        if self.trades:
            print(f"\n📋 最近 {min(5, len(self.trades))} 笔交易:")
            for trade in self.trades[-5:]:
                print(f"   {trade.entry_time.strftime('%Y-%m-%d')} -> {trade.exit_time.strftime('%Y-%m-%d')}: "
                      f"{trade.symbol} {trade.side.upper()} {trade.pnl:+.2f} (回撤:{trade.drawdown_pct:.2%})")
    
    def plot_results(self):
        """绘制结果（可选）"""
        try:
            import matplotlib.pyplot as plt
            
            if not self.equity_curve:
                print("❌ 无数据可绘制")
                return
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # 资金曲线
            dates = [e['timestamp'] for e in self.equity_curve]
            equity = [e['total_equity'] for e in self.equity_curve]
            
            ax1.plot(dates, equity, 'b-', linewidth=2, label='总资产')
            ax1.axhline(y=self.initial_capital, color='r', linestyle='--', label='初始资金')
            ax1.set_title('资金曲线')
            ax1.set_ylabel('资金')
            ax1.legend()
            ax1.grid(True)
            
            # 持仓数量
            positions = [e['positions'] for e in self.equity_curve]
            ax2.plot(dates, positions, 'g-', linewidth=2, label='持仓数')
            ax2.set_title('持仓数量')
            ax2.set_ylabel('持仓数')
            ax2.set_xlabel('日期')
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            print("📊 提示: 安装matplotlib可以查看图表: pip install matplotlib")

def main():
    """主函数"""
    print("🎲 抛硬币交易策略演示")
    print("="*60)
    
    # 创建策略实例
    strategy = CoinFlipStrategy(
        symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],  # 币安热门交易对
        initial_capital=100000.0,
        position_size=0.2,  # 20%仓位
        drawdown_threshold=0.01,  # 1%回撤
        data_source='binance'  # 使用币安数据源
    )
    
    # 运行回测
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    strategy.run_backtest(start_date, end_date)
    
    # 绘制结果
    strategy.plot_results()

if __name__ == "__main__":
    main() 