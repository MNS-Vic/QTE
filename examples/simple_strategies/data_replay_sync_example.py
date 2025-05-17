"""
数据重放控制器同步API使用示例

此示例脚本演示了如何使用数据重放控制器的同步API进行数据处理
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入数据重放模块
from qte.data.data_replay import (
    DataFrameReplayController, 
    MultiSourceReplayController,
    ReplayMode
)

def dataframe_sync_example():
    """DataFrame控制器同步API示例"""
    print("\n===== DataFrame控制器同步API示例 =====")
    
    # 创建示例数据
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    data = {
        'price': [100, 101, 102, 103, 104], 
        'volume': [1000, 1100, 1200, 1300, 1400]
    }
    df = pd.DataFrame(data, index=dates)
    
    print(f"样本数据:\n{df}")
    
    # 创建控制器
    controller = DataFrameReplayController(df)
    
    # 方法1: 使用step_sync逐个获取数据点
    print("\n使用step_sync逐个获取数据点:")
    
    results = []
    while True:
        data_point = controller.step_sync()
        if data_point is None:
            break
        date_str = data_point.name.strftime('%Y-%m-%d')
        print(f"  时间: {date_str}, 价格: {data_point['price']}, 成交量: {data_point['volume']}")
        results.append(data_point)
    
    print(f"获取的数据点数量: {len(results)}")
    
    # 重置控制器
    controller.reset()
    
    # 方法2: 使用process_all_sync一次获取所有数据
    print("\n使用process_all_sync一次获取所有数据:")
    all_data = controller.process_all_sync()
    for i, data_point in enumerate(all_data):
        date_str = data_point.name.strftime('%Y-%m-%d')
        print(f"  第{i+1}条: 时间: {date_str}, 价格: {data_point['price']}")
    
    print(f"获取的数据点数量: {len(all_data)}")
    
    return df

def multisource_sync_example():
    """多数据源控制器同步API示例"""
    print("\n===== 多数据源控制器同步API示例 =====")
    
    # 创建价格数据(按天)
    price_dates = pd.date_range(start='2023-01-01', periods=3, freq='D')
    price_data = {'price': [100, 101, 102]}
    price_df = pd.DataFrame(price_data, index=price_dates)
    
    # 创建成交量数据(按半天)
    volume_dates = pd.date_range(start='2023-01-01', periods=6, freq='12h')
    volume_data = {'volume': [1000, 1100, 1200, 1300, 1400, 1500]}
    volume_df = pd.DataFrame(volume_data, index=volume_dates)
    
    print("价格数据:")
    print(price_df)
    print("\n成交量数据:")
    print(volume_df)
    
    # 创建多数据源控制器
    controller = MultiSourceReplayController({
        'price': price_df,
        'volume': volume_df
    })
    
    # 方法1: 使用step_sync逐个处理
    print("\n使用step_sync逐个处理:")
    results = []
    
    while True:
        data = controller.step_sync()
        if data is None:
            break
        
        source = data.get('_source', 'unknown')
        timestamp = data.get('_timestamp')
        
        if timestamp:
            time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        else:
            time_str = "无时间戳"
            
        if source == 'price' and 'price' in data:
            print(f"  数据: 来源={source}, 时间={time_str}, 价格={data['price']}")
        elif source == 'volume' and 'volume' in data:
            print(f"  数据: 来源={source}, 时间={time_str}, 成交量={data['volume']}")
            
        results.append(data)
    
    print(f"获取的数据点数量: {len(results)}")
    
    # 重置控制器
    controller.reset()
    
    # 方法2: 使用process_all_sync一次处理所有数据
    print("\n使用process_all_sync处理所有数据:")
    all_data = controller.process_all_sync()
    
    for i, data in enumerate(all_data):
        source = data.get('_source', 'unknown')
        timestamp = data.get('_timestamp')
        
        if timestamp:
            time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        else:
            time_str = "无时间戳"
            
        if source == 'price' and 'price' in data:
            print(f"  第{i+1}条: 来源={source}, 时间={time_str}, 价格={data['price']}")
        elif source == 'volume' and 'volume' in data:
            print(f"  第{i+1}条: 来源={source}, 时间={time_str}, 成交量={data['volume']}")
    
    print(f"获取的数据点数量: {len(all_data)}")

def sync_vs_async_example(df):
    """同步与异步API的比较示例"""
    print("\n===== 同步与异步API比较 =====")
    
    # 创建控制器
    controller = DataFrameReplayController(df.copy())
    
    # 同步API - 数据收集
    print("\n同步API:")
    sync_results = []
    while True:
        data = controller.step_sync()
        if data is None:
            break
        sync_results.append(data)
    
    print(f"  获取到 {len(sync_results)} 个数据点")
    
    # 异步API - 回调方式
    print("\n异步API:")
    async_results = []
    
    def collect_data(data):
        async_results.append(data)
    
    # 重置控制器
    controller.reset()
    
    # 注册回调并启动
    controller.register_callback(collect_data)
    controller.start()
    
    # 等待处理完成
    import time
    max_wait = 3  # 最多等待3秒
    for _ in range(30):
        if controller.get_status().is_completed:
            break
        time.sleep(0.1)
    
    print(f"  获取到 {len(async_results)} 个数据点")
    
    # 比较结果
    if len(sync_results) == len(async_results):
        print("\n结果比较: 同步和异步API获取的数据点数量相同")
    else:
        print(f"\n结果比较: 不同! 同步={len(sync_results)}, 异步={len(async_results)}")

if __name__ == "__main__":
    # 运行DataFrame控制器示例
    df = dataframe_sync_example()
    
    # 运行多数据源控制器示例
    multisource_sync_example()
    
    # 比较同步与异步API
    sync_vs_async_example(df)
    
    print("\n===== 示例完成 =====")