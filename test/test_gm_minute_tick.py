import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from qte_core.event_loop import EventLoop
from qte_data.gm_data_provider import GmDataProvider

def search_and_process_data_files(data_root_dir, data_type="minute"):
    """
    搜索并处理掘金量化的数据文件
    
    参数:
        data_root_dir (str): 掘金量化数据根目录
        data_type (str): 数据类型，'minute' 或 'tick'
    """
    print(f"\n===== 搜索和处理掘金量化{data_type}数据文件 =====")
    
    # 可能包含数据的目录列表
    potential_dirs = [
        os.path.join(data_root_dir, "data"),
        os.path.join(data_root_dir, "basic_data"),
        os.path.join(data_root_dir, "base_data"),
    ]
    
    # 扩展搜索包含子目录
    extended_dirs = []
    for d in potential_dirs:
        if os.path.exists(d):
            extended_dirs.append(d)
            # 添加第一级子目录
            try:
                for subdir in os.listdir(d):
                    full_subdir = os.path.join(d, subdir)
                    if os.path.isdir(full_subdir):
                        extended_dirs.append(full_subdir)
            except PermissionError:
                print(f"无法访问目录: {d}")
    
    print(f"将在以下目录中搜索{data_type}数据文件:")
    for d in extended_dirs:
        print(f"  - {d}")
    
    # 搜索所有.dat文件
    dat_files = []
    for directory in extended_dirs:
        try:
            for file in os.listdir(directory):
                if file.endswith('.dat'):
                    # 根据数据类型筛选文件名
                    if (data_type == "minute" and ('min' in file.lower() or 'minute' in file.lower())) or \
                       (data_type == "tick" and 'tick' in file.lower()) or \
                       (file == "storage.dat"):  # storage.dat可能包含所有类型的数据
                        dat_files.append(os.path.join(directory, file))
        except PermissionError:
            print(f"无法访问目录: {directory}")
    
    print(f"找到 {len(dat_files)} 个可能包含{data_type}数据的.dat文件")
    
    # 检查每个.dat文件
    data_tables = []
    for file_path in dat_files:
        print(f"\n检查文件: {file_path}")
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # 筛选可能包含目标数据类型的表
            for table in tables:
                table_name = table[0]
                table_lower = table_name.lower()
                if (data_type == "minute" and ('min' in table_lower or 'minute' in table_lower)) or \
                   (data_type == "tick" and 'tick' in table_lower):
                    
                    print(f"发现可能的{data_type}数据表: {table_name}")
                    
                    # 检查表结构
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    
                    # 检查是否包含必要的列
                    has_symbol = 'symbol' in column_names
                    has_time = any(time_col in column_names for time_col in ['datetime', 'time', 'trade_time', 'trade_date'])
                    
                    if has_symbol and has_time:
                        # 获取记录数
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                        count = cursor.fetchone()[0]
                        
                        # 获取不同的交易品种
                        cursor.execute(f"SELECT COUNT(DISTINCT symbol) FROM {table_name};")
                        symbol_count = cursor.fetchone()[0]
                        
                        data_tables.append({
                            'file_path': file_path,
                            'table_name': table_name,
                            'column_names': column_names,
                            'record_count': count,
                            'symbol_count': symbol_count
                        })
                        
                        print(f"  - 列: {', '.join(column_names)}")
                        print(f"  - 记录数: {count}")
                        print(f"  - 交易品种数: {symbol_count}")
                        
                        # 获取样本数据
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                        sample_data = cursor.fetchall()
                        print("  - 样本数据:")
                        for row in sample_data:
                            print(f"    {row}")
            
            conn.close()
        except sqlite3.Error as e:
            print(f"处理SQLite文件时出错: {e}")
        except Exception as e:
            print(f"处理文件时出错: {e}")
    
    print(f"\n总共找到 {len(data_tables)} 个可能包含{data_type}数据的表")
    
    # 返回找到的数据表信息
    return data_tables

def test_data_provider_with_found_data(data_tables, data_type="minute"):
    """
    使用找到的数据表测试数据提供者
    
    参数:
        data_tables (List[Dict]): 数据表信息列表
        data_type (str): 数据类型，'minute' 或 'tick'
    """
    if not data_tables:
        print(f"未找到{data_type}数据表，无法测试数据提供者")
        return
    
    print(f"\n===== 使用找到的{data_type}数据测试GmDataProvider =====")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 掘金量化数据目录
    gm_data_dir = os.path.join(project_root, "myquant_data")
    
    # 获取可用的交易品种列表
    all_symbols = set()
    for table_info in data_tables:
        try:
            conn = sqlite3.connect(table_info['file_path'])
            cursor = conn.cursor()
            cursor.execute(f"SELECT DISTINCT symbol FROM {table_info['table_name']} LIMIT 100;")
            symbols = [row[0] for row in cursor.fetchall()]
            all_symbols.update(symbols)
            conn.close()
        except Exception as e:
            print(f"获取交易品种时出错: {e}")
    
    symbols_list = list(all_symbols)
    if not symbols_list:
        print(f"未找到交易品种，无法测试数据提供者")
        return
    
    # 限制测试的品种数量
    test_symbols = symbols_list[:5]
    print(f"使用以下交易品种进行测试: {test_symbols}")
    
    # 创建数据提供者
    data_provider = GmDataProvider(
        event_loop=event_loop,
        gm_data_dir=gm_data_dir,
        symbols=test_symbols,
        use_csv_cache=True,
        data_type=data_type
    )
    
    # 检查是否加载了数据
    loaded_symbols = list(data_provider.data.keys())
    print(f"成功加载数据的交易品种: {loaded_symbols}")
    
    if not loaded_symbols:
        print(f"未能加载任何{data_type}数据，测试结束")
        return
    
    # 测试流式数据
    test_symbol = loaded_symbols[0]
    print(f"\n测试流式传输 {test_symbol} 的{data_type}数据...")
    
    event_count = 0
    max_events = 10
    
    for event in data_provider.stream_market_data([test_symbol]):
        event_count += 1
        
        if data_type == "minute":
            print(f"接收到K线事件 {event_count}: {event.symbol} 于 {event.timestamp}, OHLC: {event.open_price}/{event.high_price}/{event.low_price}/{event.close_price}, 成交量: {event.volume}")
        else:  # tick
            print(f"接收到Tick事件 {event_count}: {event['symbol']} 于 {event['timestamp']}, 价格: {event['price']}, 成交量: {event.get('volume', 'N/A')}")
        
        if event_count >= max_events:
            break
    
    # 测试获取最新数据
    print(f"\n测试获取 {test_symbol} 的最新{data_type}数据...")
    latest_data = data_provider.get_latest_bar(test_symbol)
    if latest_data:
        if data_type == "minute":
            print(f"最新K线: 时间 {latest_data['timestamp']}, 收盘价 {latest_data['close']}")
        else:  # tick
            print(f"最新Tick: 时间 {latest_data['timestamp']}, 价格 {latest_data.get('price', latest_data.get('close', 'N/A'))}")
    else:
        print(f"未能获取 {test_symbol} 的最新{data_type}数据")
    
    # 测试获取历史数据
    if test_symbol in data_provider.data:
        df = data_provider.data[test_symbol]
        if not df.empty:
            # 选取数据中间的一个时间范围
            all_timestamps = sorted(df['timestamp'].unique())
            if len(all_timestamps) > 2:
                start_idx = len(all_timestamps) // 3
                end_idx = start_idx * 2
                start_date = all_timestamps[start_idx]
                end_date = all_timestamps[end_idx]
                
                print(f"\n测试获取 {test_symbol} 从 {start_date} 到 {end_date} 的历史{data_type}数据...")
                historical_data = data_provider.get_historical_bars(test_symbol, start_date, end_date)
                
                if historical_data:
                    data_list = list(historical_data)
                    print(f"获取到 {len(data_list)} 条历史数据")
                    if data_list:
                        first_item = data_list[0]
                        last_item = data_list[-1]
                        if data_type == "minute":
                            print(f"第一条: 时间 {first_item['timestamp']}, 收盘价 {first_item['close']}")
                            print(f"最后一条: 时间 {last_item['timestamp']}, 收盘价 {last_item['close']}")
                        else:  # tick
                            print(f"第一条: 时间 {first_item['timestamp']}, 价格 {first_item.get('price', first_item.get('close', 'N/A'))}")
                            print(f"最后一条: 时间 {last_item['timestamp']}, 价格 {last_item.get('price', last_item.get('close', 'N/A'))}")
                else:
                    print(f"未能获取 {test_symbol} 的历史{data_type}数据")

def create_dummy_data(data_type="minute"):
    """
    创建虚拟的分钟线或tick数据用于测试
    
    参数:
        data_type (str): 数据类型，'minute' 或 'tick'
    """
    print(f"\n===== 创建虚拟{data_type}数据 =====")
    
    # 输出目录
    output_dir = os.path.join(project_root, "myquant_data", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试用的交易品种
    symbols = ["SHFE.au", "CFFEX.IF", "DCE.m"]
    
    # 创建SQLite数据库
    db_path = os.path.join(output_dir, f"dummy_{data_type}_data.dat")
    
    try:
        # 删除已存在的文件
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # 创建新数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表
        if data_type == "minute":
            table_name = "minute_bars"
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    datetime TIMESTAMP,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER
                )
            ''')
        else:  # tick
            table_name = "tick_data"
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    datetime TIMESTAMP,
                    price REAL,
                    volume INTEGER,
                    bid_price REAL,
                    bid_volume INTEGER,
                    ask_price REAL,
                    ask_volume INTEGER
                )
            ''')
        
        # 为每个交易品种生成数据
        for symbol in symbols:
            # 生成时间范围
            start_time = datetime(2024, 1, 1, 9, 0, 0)
            
            # 分钟线数据的时间间隔为1分钟
            # Tick数据的时间间隔可以更短，比如几秒钟
            interval = timedelta(minutes=1) if data_type == "minute" else timedelta(seconds=5)
            
            # 生成数据点
            num_data_points = 1000 if data_type == "minute" else 2000
            
            base_price = 100.0  # 基础价格
            daily_volatility = 0.02  # 每日波动率
            
            data_records = []
            current_time = start_time
            current_price = base_price
            
            for i in range(num_data_points):
                # 生成价格变动
                price_change = current_price * daily_volatility * (0.5 - np.random.random())
                current_price += price_change
                
                if data_type == "minute":
                    # 生成OHLC数据
                    open_price = current_price
                    high_price = current_price * (1 + 0.005 * np.random.random())
                    low_price = current_price * (1 - 0.005 * np.random.random())
                    close_price = current_price + price_change
                    volume = int(1000 * np.random.random())
                    
                    data_records.append((
                        symbol,
                        current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    ))
                else:  # tick
                    # 生成tick数据
                    price = current_price
                    volume = int(100 * np.random.random())
                    bid_price = price * (1 - 0.001)
                    bid_volume = int(50 * np.random.random())
                    ask_price = price * (1 + 0.001)
                    ask_volume = int(50 * np.random.random())
                    
                    data_records.append((
                        symbol,
                        current_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                        price,
                        volume,
                        bid_price,
                        bid_volume,
                        ask_price,
                        ask_volume
                    ))
                
                # 增加时间
                current_time += interval
            
            # 插入数据
            if data_type == "minute":
                cursor.executemany(
                    f"INSERT INTO {table_name} (symbol, datetime, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    data_records
                )
            else:  # tick
                cursor.executemany(
                    f"INSERT INTO {table_name} (symbol, datetime, price, volume, bid_price, bid_volume, ask_price, ask_volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    data_records
                )
            
            print(f"为交易品种 {symbol} 生成了 {len(data_records)} 条{data_type}数据")
        
        # 提交事务并关闭连接
        conn.commit()
        conn.close()
        
        print(f"虚拟{data_type}数据已保存到: {db_path}")
        return db_path
    
    except Exception as e:
        print(f"创建虚拟数据时出错: {e}")
        return None

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description=f"测试掘金量化{sys.argv[0].split('_')[-1].split('.')[0]}数据获取功能")
    parser.add_argument('--search', action='store_true', help='搜索数据文件')
    parser.add_argument('--create', action='store_true', help='创建虚拟数据')
    parser.add_argument('--test', action='store_true', help='测试数据提供者')
    parser.add_argument('--minute', action='store_true', help='处理分钟线数据')
    parser.add_argument('--tick', action='store_true', help='处理tick数据')
    
    args = parser.parse_args()
    
    # 如果没有指定参数，则执行所有操作
    if not any([args.search, args.create, args.test]):
        args.search = args.create = args.test = True
    
    # 如果没有指定数据类型，则默认为分钟线数据
    if not any([args.minute, args.tick]):
        args.minute = True
    
    # 掘金量化数据目录
    gm_data_dir = os.path.join(project_root, "myquant_data")
    
    # 处理分钟线数据
    if args.minute:
        print("\n========== 处理分钟线数据 ==========")
        
        # 搜索数据文件
        minute_tables = []
        if args.search:
            minute_tables = search_and_process_data_files(gm_data_dir, "minute")
        
        # 如果没有找到数据且需要创建虚拟数据
        if not minute_tables and args.create:
            dummy_db_path = create_dummy_data("minute")
            if dummy_db_path:
                # 重新搜索，包括新创建的虚拟数据
                minute_tables = search_and_process_data_files(gm_data_dir, "minute")
        
        # 测试数据提供者
        if args.test:
            test_data_provider_with_found_data(minute_tables, "minute")
    
    # 处理tick数据
    if args.tick:
        print("\n========== 处理Tick数据 ==========")
        
        # 搜索数据文件
        tick_tables = []
        if args.search:
            tick_tables = search_and_process_data_files(gm_data_dir, "tick")
        
        # 如果没有找到数据且需要创建虚拟数据
        if not tick_tables and args.create:
            dummy_db_path = create_dummy_data("tick")
            if dummy_db_path:
                # 重新搜索，包括新创建的虚拟数据
                tick_tables = search_and_process_data_files(gm_data_dir, "tick")
        
        # 测试数据提供者
        if args.test:
            test_data_provider_with_found_data(tick_tables, "tick")

if __name__ == "__main__":
    main() 