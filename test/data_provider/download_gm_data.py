#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金行情数据下载工具

用于从掘金量化平台下载行情数据，支持tick级、分钟级、日线级数据
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 尝试导入掘金量化的库
try:
    from gm.api import *
except ImportError:
    print("错误: 未找到掘金量化API，请确保已正确安装掘金量化Python SDK")
    print("可通过以下命令安装: pip install gm")
    sys.exit(1)


class GoldenMineDataDownloader:
    """掘金数据下载类"""

    def __init__(self, token=None, output_dir="downloaded_data"):
        """
        初始化下载器
        
        Args:
            token: 掘金量化Token
            output_dir: 数据保存目录
        """
        self.token = token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 已初始化标记
        self.initialized = False
        
    def initialize(self):
        """初始化API连接"""
        if not self.initialized:
            if not self.token:
                raise ValueError("Token未设置，请提供掘金量化Token")
            
            try:
                # 设置token
                set_token(self.token)
                self.initialized = True
                print(f"掘金API连接初始化成功，Token: {self.token}")
            except Exception as e:
                raise RuntimeError(f"掘金API连接初始化失败: {e}")
    
    def check_symbol(self, symbol):
        """
        检查标的代码格式是否正确
        
        Args:
            symbol: 标的代码，如SHSE.600000
            
        Returns:
            bool: 格式是否正确
        """
        if not symbol or '.' not in symbol:
            print(f"警告: 标的代码 {symbol} 格式不正确。应为 '交易所.代码' 格式，如 'SHSE.600000'")
            return False
        return True
    
    def download_tick_data(self, symbol, start_date, end_date=None):
        """
        下载tick级别数据
        
        Args:
            symbol: 标的代码，如SHSE.600000
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            
        Returns:
            DataFrame: tick数据
        """
        self.initialize()
        
        if not self.check_symbol(symbol):
            return None
        
        # 解析日期
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date) if end_date else datetime.now()
        
        # 创建输出目录
        exchange, code = symbol.split('.')
        output_dir = self.output_dir / "tick" / exchange / code
        output_dir.mkdir(exist_ok=True, parents=True)
        
        print(f"开始下载 {symbol} 的tick数据，时间范围: {start_date} 到 {end_date or datetime.now().strftime('%Y-%m-%d')}")
        
        # 由于tick数据量大，按天下载并保存
        current_date = start
        all_data = []
        
        while current_date <= end:
            current_date_str = current_date.strftime('%Y-%m-%d')
            next_date = current_date + timedelta(days=1)
            next_date_str = next_date.strftime('%Y-%m-%d')
            
            try:
                print(f"下载 {symbol} 在 {current_date_str} 的tick数据...")
                
                # 查询当天的tick数据
                data = history(
                    symbol=symbol,
                    frequency='tick',
                    start_time=f"{current_date_str} 00:00:00",
                    end_time=f"{current_date_str} 23:59:59",
                    fields='last_price,created_at,trade_date,volume,position,last_volume,bid_price,bid_volume,ask_price,ask_volume',
                    df=True
                )
                
                if data is not None and not data.empty:
                    print(f"获取到 {len(data)} 条tick记录")
                    
                    # 保存当天数据到CSV
                    output_file = output_dir / f"{symbol.replace('.', '_')}_{current_date_str}_tick.csv"
                    data.to_csv(output_file, index=False)
                    print(f"数据已保存到 {output_file}")
                    
                    all_data.append(data)
                else:
                    print(f"未获取到 {symbol} 在 {current_date_str} 的tick数据")
            
            except Exception as e:
                print(f"下载 {symbol} 在 {current_date_str} 的tick数据时出错: {e}")
            
            # 移动到下一天
            current_date = next_date
        
        # 如果需要合并所有数据
        if all_data:
            all_data_df = pd.concat(all_data, ignore_index=True)
            return all_data_df
        
        return None
    
    def download_bar_data(self, symbol, frequency, start_date, end_date=None, adjust=None):
        """
        下载K线数据（分钟线或日线）
        
        Args:
            symbol: 标的代码，如SHSE.600000
            frequency: 频率，如'60s'为分钟线，'1d'为日线
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            adjust: 复权方式，None为不复权，ADJUST_PREV为前复权，ADJUST_POST为后复权
            
        Returns:
            DataFrame: K线数据
        """
        self.initialize()
        
        if not self.check_symbol(symbol):
            return None
        
        # 解析日期
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        
        # 确定数据类型目录
        if frequency in ['1d', 'daily', '1dm']:
            data_type = "daily"
        else:
            # 将频率转换为分钟
            if frequency.endswith('s'):
                minutes = int(frequency[:-1]) // 60
                data_type = f"{minutes}min"
            elif frequency.endswith('m'):
                minutes = int(frequency[:-1])
                data_type = f"{minutes}min"
            else:
                data_type = frequency
        
        # 创建输出目录
        exchange, code = symbol.split('.')
        output_dir = self.output_dir / data_type / exchange / code
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # 复权设置
        adjust_text = ""
        adjust_end_time = end_date
        
        if adjust == ADJUST_PREV:
            adjust_text = "前复权"
        elif adjust == ADJUST_POST:
            adjust_text = "后复权"
        else:
            adjust_text = "不复权"
            adjust = None
        
        print(f"开始下载 {symbol} 的{data_type}数据，时间范围: {start_date} 到 {end_date}，复权方式: {adjust_text}")
        
        try:
            # 查询K线数据
            data = history(
                symbol=symbol,
                frequency=frequency,
                start_time=f"{start_date} 00:00:00",
                end_time=f"{end_date} 23:59:59",
                fields='open,high,low,close,volume,amount,position,bob,eob',
                adjust=adjust,
                adjust_end_time=adjust_end_time if adjust else None,
                df=True
            )
            
            if data is not None and not data.empty:
                print(f"获取到 {len(data)} 条{data_type}记录")
                
                # 保存数据到CSV
                adjust_suffix = ""
                if adjust == ADJUST_PREV:
                    adjust_suffix = "_前复权"
                elif adjust == ADJUST_POST:
                    adjust_suffix = "_后复权"
                
                output_file = output_dir / f"{symbol.replace('.', '_')}_{start_date}_to_{end_date}_{data_type}{adjust_suffix}.csv"
                data.to_csv(output_file, index=False)
                print(f"数据已保存到 {output_file}")
                
                return data
            else:
                print(f"未获取到 {symbol} 在 {start_date} 到 {end_date} 的{data_type}数据")
        
        except Exception as e:
            print(f"下载 {symbol} 的{data_type}数据时出错: {e}")
        
        return None
    
    def download_daily_data(self, symbol, start_date, end_date=None, adjust=None):
        """
        下载日线级别数据
        
        Args:
            symbol: 标的代码，如SHSE.600000
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            adjust: 复权方式，None为不复权，ADJUST_PREV为前复权，ADJUST_POST为后复权
            
        Returns:
            DataFrame: 日线数据
        """
        return self.download_bar_data(symbol, '1d', start_date, end_date, adjust)
    
    def download_minute_data(self, symbol, minutes, start_date, end_date=None, adjust=None):
        """
        下载分钟线级别数据
        
        Args:
            symbol: 标的代码，如SHSE.600000
            minutes: 分钟数，如1为1分钟线，5为5分钟线
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            adjust: 复权方式，None为不复权，ADJUST_PREV为前复权，ADJUST_POST为后复权
            
        Returns:
            DataFrame: 分钟线数据
        """
        frequency = f"{minutes * 60}s"
        return self.download_bar_data(symbol, frequency, start_date, end_date, adjust)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='掘金行情数据下载工具')
    
    # 基本参数
    parser.add_argument('--token', type=str, required=False, help='掘金量化Token')
    parser.add_argument('--output-dir', type=str, default='downloaded_data', help='数据保存目录')
    parser.add_argument('--symbol', type=str, required=True, help='标的代码，如SHSE.600000')
    
    # 时间范围
    parser.add_argument('--start-date', type=str, required=True, help='开始日期，格式为YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, help='结束日期，格式为YYYY-MM-DD，默认为当天')
    
    # 数据类型
    data_type_group = parser.add_mutually_exclusive_group(required=True)
    data_type_group.add_argument('--tick', action='store_true', help='下载tick数据')
    data_type_group.add_argument('--minute', type=int, help='下载分钟线数据，参数为分钟数，如1为1分钟线，5为5分钟线')
    data_type_group.add_argument('--daily', action='store_true', help='下载日线数据')
    
    # 复权方式
    adjust_group = parser.add_mutually_exclusive_group()
    adjust_group.add_argument('--no-adjust', action='store_true', help='不复权（默认）')
    adjust_group.add_argument('--pre-adjust', action='store_true', help='前复权')
    adjust_group.add_argument('--post-adjust', action='store_true', help='后复权')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 如果未提供token，使用默认token
    token = args.token or "d6e3ba1ba79d0af43300589d35af32bdf9e5800b"
    
    # 创建下载器
    downloader = GoldenMineDataDownloader(token=token, output_dir=args.output_dir)
    
    # 处理复权方式
    adjust = None
    if args.pre_adjust:
        adjust = ADJUST_PREV
    elif args.post_adjust:
        adjust = ADJUST_POST
    
    try:
        # 根据数据类型下载数据
        if args.tick:
            downloader.download_tick_data(args.symbol, args.start_date, args.end_date)
        elif args.minute is not None:
            downloader.download_minute_data(args.symbol, args.minute, args.start_date, args.end_date, adjust)
        elif args.daily:
            downloader.download_daily_data(args.symbol, args.start_date, args.end_date, adjust)
    
    except Exception as e:
        print(f"数据下载过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 