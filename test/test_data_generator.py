import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import argparse

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def generate_trend_data(symbol, trend="up", volatility=0.01, start_date='2023-01-01', 
                        periods=100, base_price=100.0, trend_strength=0.002,
                        output_dir=None):
    """
    生成具有指定趋势的价格数据
    
    参数:
        symbol (str): 证券代码
        trend (str): 趋势方向，"up", "down", "flat", "volatile"
        volatility (float): 波动率
        start_date (str): 起始日期，格式为'YYYY-MM-DD'
        periods (int): 生成数据的周期数
        base_price (float): 基础价格
        trend_strength (float): 趋势强度
        output_dir (str): 输出目录，默认为项目的test_data目录
    
    返回:
        pandas.DataFrame: 生成的价格数据
    """
    # 设置默认输出目录
    if output_dir is None:
        output_dir = os.path.join(project_root, "test_data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成日期范围
    dates = pd.date_range(start=start_date, periods=periods, freq='D')
    
    # 生成随机噪声
    noise = np.random.normal(0, volatility, periods)
    
    # 基于趋势生成价格
    if trend == "up":
        # 上升趋势
        drift = np.arange(periods) * trend_strength
    elif trend == "down":
        # 下降趋势
        drift = -np.arange(periods) * trend_strength
    elif trend == "flat":
        # 平稳趋势
        drift = np.zeros(periods)
    elif trend == "volatile":
        # 高波动趋势
        drift = np.cumsum(np.random.normal(0, volatility*3, periods))
    else:
        raise ValueError(f"不支持的趋势类型: {trend}")
    
    # 计算收盘价
    close_prices = base_price * (1 + drift + noise)
    
    # 确保价格非负
    close_prices = np.maximum(close_prices, 0.01)
    
    # 生成其他价格数据 (开盘价, 最高价, 最低价)
    day_volatility = volatility / 2  # 日内波动率
    open_prices = close_prices * (1 + np.random.normal(0, day_volatility, periods))
    high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, day_volatility, periods)))
    low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, day_volatility, periods)))
    
    # 生成成交量
    volume_base = 10000
    volume = np.random.normal(volume_base, volume_base*0.2, periods).astype(int)
    volume = np.maximum(volume, 100)  # 确保成交量为正
    
    # 创建DataFrame
    data = {
        'timestamp': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volume
    }
    df = pd.DataFrame(data)
    
    # 保存到CSV文件
    output_file = os.path.join(output_dir, f"{symbol}.csv")
    df.to_csv(output_file, index=False)
    print(f"已生成{trend}趋势数据并保存到 {output_file}")
    
    return df

def generate_multi_asset_data(symbols, correlations=None, volatilities=None, trends=None,
                             start_date='2023-01-01', periods=100, base_prices=None,
                             output_dir=None):
    """
    生成多资产的相关数据
    
    参数:
        symbols (list): 证券代码列表
        correlations (dict): 资产间的相关系数, 格式为 {(symbol1, symbol2): corr}
        volatilities (dict): 各资产的波动率, 格式为 {symbol: vol}
        trends (dict): 各资产的趋势, 格式为 {symbol: trend}
        start_date (str): 起始日期
        periods (int): 周期数
        base_prices (dict): 各资产的基础价格, 格式为 {symbol: price}
        output_dir (str): 输出目录
        
    返回:
        dict: 各资产的DataFrame，格式为 {symbol: df}
    """
    # 设置默认参数
    if correlations is None:
        correlations = {}
    if volatilities is None:
        volatilities = {s: 0.01 for s in symbols}
    if trends is None:
        trends = {s: "flat" for s in symbols}
    if base_prices is None:
        base_prices = {s: 100.0 for s in symbols}
    
    # 设置默认输出目录
    if output_dir is None:
        output_dir = os.path.join(project_root, "test_data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成日期范围
    dates = pd.date_range(start=start_date, periods=periods, freq='D')
    
    # 生成随机成分
    random_components = {}
    for symbol in symbols:
        random_components[symbol] = np.random.normal(0, volatilities.get(symbol, 0.01), periods)
    
    # 应用相关性
    for (sym1, sym2), corr in correlations.items():
        if sym1 in symbols and sym2 in symbols:
            # 计算相关成分
            common_component = np.random.normal(0, np.sqrt(volatilities.get(sym1, 0.01) * volatilities.get(sym2, 0.01)), periods)
            
            # 结合独立成分和共同成分
            random_components[sym1] = np.sqrt(1 - corr**2) * random_components[sym1] + corr * common_component
            random_components[sym2] = np.sqrt(1 - corr**2) * random_components[sym2] + corr * common_component
    
    # 生成各资产的数据
    dfs = {}
    for symbol in symbols:
        # 基于趋势生成价格
        trend = trends.get(symbol, "flat")
        base_price = base_prices.get(symbol, 100.0)
        volatility = volatilities.get(symbol, 0.01)
        
        if trend == "up":
            drift = np.arange(periods) * 0.002
        elif trend == "down":
            drift = -np.arange(periods) * 0.002
        elif trend == "flat":
            drift = np.zeros(periods)
        elif trend == "volatile":
            drift = np.cumsum(np.random.normal(0, volatility*3, periods))
        else:
            drift = np.zeros(periods)
        
        # 计算收盘价
        close_prices = base_price * (1 + drift + random_components[symbol])
        close_prices = np.maximum(close_prices, 0.01)  # 确保价格非负
        
        # 生成其他价格数据
        day_volatility = volatility / 2
        open_prices = close_prices * (1 + np.random.normal(0, day_volatility, periods))
        high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, day_volatility, periods)))
        low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, day_volatility, periods)))
        
        # 生成成交量
        volume_base = 10000
        volume = np.random.normal(volume_base, volume_base*0.2, periods).astype(int)
        volume = np.maximum(volume, 100)
        
        # 创建DataFrame
        data = {
            'timestamp': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume
        }
        df = pd.DataFrame(data)
        
        # 保存到CSV文件
        output_file = os.path.join(output_dir, f"{symbol}.csv")
        df.to_csv(output_file, index=False)
        print(f"已生成{symbol}数据并保存到 {output_file}")
        
        dfs[symbol] = df
    
    return dfs

def plot_data(dfs, output_file=None):
    """
    绘制生成的数据
    
    参数:
        dfs (dict): 各资产的DataFrame，格式为 {symbol: df}
        output_file (str): 输出文件路径，如果为None则显示图表
    """
    plt.figure(figsize=(12, 8))
    
    # 绘制收盘价
    for symbol, df in dfs.items():
        plt.subplot(2, 1, 1)
        plt.plot(df['timestamp'], df['close'], label=f"{symbol} Close")
    plt.title('Closing Prices')
    plt.legend()
    plt.grid(True)
    
    # 绘制成交量
    for symbol, df in dfs.items():
        plt.subplot(2, 1, 2)
        plt.bar(df['timestamp'], df['volume'], alpha=0.5, label=f"{symbol} Volume")
    plt.title('Trading Volume')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        print(f"已保存图表到 {output_file}")
    else:
        plt.show()

def main():
    """主函数，用于命令行调用"""
    parser = argparse.ArgumentParser(description='生成回测测试数据')
    parser.add_argument('--symbol', type=str, default='TEST', help='证券代码')
    parser.add_argument('--trend', type=str, default='up', choices=['up', 'down', 'flat', 'volatile'], help='趋势方向')
    parser.add_argument('--volatility', type=float, default=0.01, help='波动率')
    parser.add_argument('--start_date', type=str, default='2023-01-01', help='起始日期，格式为YYYY-MM-DD')
    parser.add_argument('--periods', type=int, default=100, help='生成数据的周期数')
    parser.add_argument('--base_price', type=float, default=100.0, help='基础价格')
    parser.add_argument('--output_dir', type=str, help='输出目录')
    parser.add_argument('--plot', action='store_true', help='是否绘制图表')
    
    args = parser.parse_args()
    
    # 生成数据
    df = generate_trend_data(
        symbol=args.symbol,
        trend=args.trend,
        volatility=args.volatility,
        start_date=args.start_date,
        periods=args.periods,
        base_price=args.base_price,
        output_dir=args.output_dir
    )
    
    # 绘制图表
    if args.plot:
        plot_data({args.symbol: df})

if __name__ == "__main__":
    main() 