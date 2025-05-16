#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析Tick数据

用于分析掘金下载的tick数据结构和内容
"""

import pandas as pd
import os
from pathlib import Path

def analyze_tick_data(file_path):
    """分析tick数据文件"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    print(f"开始分析tick数据文件: {file_path}")
    print(f"文件大小: {os.path.getsize(file_path) / 1024:.2f} KB")
    
    try:
        # 读取数据
        df = pd.read_csv(file_path)
        
        # 基本信息
        print(f"\n文件基本信息:")
        print(f"数据行数: {len(df)}")
        print(f"数据列数: {len(df.columns)}")
        print(f"列名: {list(df.columns)}")
        
        # 检查数据类型
        print(f"\n数据类型:")
        print(df.dtypes)
        
        # 转换时间列为日期时间类型
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        
        # 基本统计信息
        print(f"\n基本统计信息:")
        print(df.describe())
        
        # 时间范围
        if 'created_at' in df.columns:
            print(f"\n时间范围:")
            print(f"开始时间: {df['created_at'].min()}")
            print(f"结束时间: {df['created_at'].max()}")
            print(f"数据跨度: {df['created_at'].max() - df['created_at'].min()}")
        
        # 开盘时间段数据
        if 'created_at' in df.columns:
            morning_open = df[df['created_at'].dt.hour == 9].copy()
            if not morning_open.empty:
                print(f"\n开盘时间段(9点)数据:")
                print(f"9点数据量: {len(morning_open)}")
                if 'price' in df.columns:
                    morning_open = morning_open[morning_open['price'] > 0]  # 过滤有效价格
                    print(f"9点有效价格数据量: {len(morning_open)}")
                    if not morning_open.empty:
                        print(f"9点第一个有效报价: {morning_open.iloc[0].to_dict()}")
        
        # 价格统计
        if 'price' in df.columns:
            valid_price = df[df['price'] > 0].copy()
            if not valid_price.empty:
                print(f"\n价格统计:")
                print(f"有效价格记录数: {len(valid_price)}")
                print(f"最低价: {valid_price['price'].min()}")
                print(f"最高价: {valid_price['price'].max()}")
                print(f"收盘价(最后一笔): {valid_price.iloc[-1]['price']}")
                
                # 每小时的交易量统计
                if 'created_at' in df.columns and 'last_volume' in df.columns:
                    valid_price['hour'] = valid_price['created_at'].dt.hour
                    hour_volume = valid_price.groupby('hour')['last_volume'].sum()
                    print(f"\n每小时交易量:")
                    print(hour_volume)
        
        # 显示几个样本数据
        print(f"\n样本数据(前5行):")
        print(df.head(5))
        
        print(f"\n样本数据(开盘后前5行):")
        if 'created_at' in df.columns:
            open_time = pd.to_datetime(f"{df['created_at'].dt.date.iloc[0]} 09:30:00")
            open_data = df[df['created_at'] >= open_time].head(5)
            print(open_data)
        
        print(f"\nTick数据分析完成!")
    
    except Exception as e:
        print(f"分析数据时出错: {e}")

def main():
    """主函数"""
    tick_file = "downloaded_data/tick/SHSE/600519/SHSE_600519_2024-01-02_tick.csv"
    analyze_tick_data(tick_file)

if __name__ == "__main__":
    main() 