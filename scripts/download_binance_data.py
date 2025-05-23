#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
币安数据下载脚本

批量下载币安交易对的历史数据并存储为CSV
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from qte.data.sources.binance_api import BinanceApiSource

def download_popular_pairs():
    """下载热门交易对数据"""
    print("🚀 开始下载币安热门交易对数据")
    print("="*60)
    
    # 初始化币安数据源
    binance_source = BinanceApiSource(
        data_dir="data/binance",
        use_cache=True
    )
    
    # 连接API
    if not binance_source.connect():
        print("❌ 无法连接到币安API")
        return
    
    # 获取热门交易对
    popular_symbols = binance_source.get_popular_symbols(base_currency='USDT', limit=15)
    print(f"📊 将下载 {len(popular_symbols)} 个热门交易对的数据")
    print(f"   交易对: {', '.join(popular_symbols)}")
    print()
    
    # 设置时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1年历史数据
    
    print(f"📅 时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print()
    
    # 下载数据
    success_count = 0
    for i, symbol in enumerate(popular_symbols, 1):
        print(f"[{i}/{len(popular_symbols)}] 下载 {symbol} 数据...")
        
        try:
            # 下载日线数据
            daily_data = binance_source.get_bars(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                frequency='1d'
            )
            
            if daily_data is not None and not daily_data.empty:
                print(f"   ✅ 成功: {len(daily_data)} 条日线数据")
                success_count += 1
            else:
                print(f"   ❌ 失败: 无数据")
                
            # 下载1小时数据（最近30天）
            hour_start = end_date - timedelta(days=30)
            hour_data = binance_source.get_bars(
                symbol=symbol,
                start_date=hour_start,
                end_date=end_date,
                frequency='1h'
            )
            
            if hour_data is not None and not hour_data.empty:
                print(f"   ✅ 成功: {len(hour_data)} 条1小时数据")
            else:
                print(f"   ⚠️  1小时数据无法获取")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        print()
    
    print("="*60)
    print(f"📈 下载完成! 成功下载 {success_count}/{len(popular_symbols)} 个交易对的数据")
    print(f"💾 数据保存在: {os.path.abspath('data/binance')}")

def download_specific_symbols(symbols: List[str], days: int = 365):
    """
    下载指定交易对的数据
    
    Parameters
    ----------
    symbols : List[str]
        交易对列表
    days : int, optional
        历史数据天数, by default 365
    """
    print(f"🚀 开始下载指定交易对数据: {', '.join(symbols)}")
    print("="*60)
    
    # 初始化币安数据源
    binance_source = BinanceApiSource(
        data_dir="data/binance",
        use_cache=True
    )
    
    # 连接API
    if not binance_source.connect():
        print("❌ 无法连接到币安API")
        return
    
    # 设置时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"📅 时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print()
    
    # 下载数据
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] 下载 {symbol} 数据...")
        
        try:
            data = binance_source.get_bars(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                frequency='1d'
            )
            
            if data is not None and not data.empty:
                print(f"   ✅ 成功: {len(data)} 条数据")
            else:
                print(f"   ❌ 失败: 无数据")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        print()
    
    print("="*60)
    print(f"💾 数据保存在: {os.path.abspath('data/binance')}")

def list_available_data():
    """列出已下载的数据"""
    data_dir = "data/binance"
    
    if not os.path.exists(data_dir):
        print("📂 数据目录不存在")
        return
    
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("📂 数据目录为空")
        return
    
    print("📊 已下载的数据文件:")
    print("="*60)
    
    for file in sorted(csv_files):
        file_path = os.path.join(data_dir, file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"   📄 {file} ({file_size:.1f} KB)")
    
    print(f"\n💾 总计 {len(csv_files)} 个文件")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='币安数据下载工具')
    parser.add_argument('--action', choices=['popular', 'custom', 'list'], 
                       default='popular', help='操作类型')
    parser.add_argument('--symbols', nargs='+', 
                       help='指定下载的交易对（用于custom模式）')
    parser.add_argument('--days', type=int, default=365, 
                       help='历史数据天数')
    
    args = parser.parse_args()
    
    if args.action == 'popular':
        download_popular_pairs()
    elif args.action == 'custom':
        if not args.symbols:
            print("❌ custom模式需要指定--symbols参数")
            return
        download_specific_symbols(args.symbols, args.days)
    elif args.action == 'list':
        list_available_data()

if __name__ == "__main__":
    main() 