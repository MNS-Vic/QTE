import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def examine_sqlite_file(file_path):
    """
    检查SQLite文件的结构
    
    参数:
        file_path (str): SQLite文件路径
    """
    print(f"\n检查文件: {file_path}")
    
    try:
        # 连接SQLite数据库
        conn = sqlite3.connect(file_path)
        
        # 查询表结构
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 检查每个表的结构和数据
        for table in tables:
            table_name = table[0]
            print(f"\n表 {table_name} 结构:")
            
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 查询数据量
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"表中共有 {count} 条记录")
            
            # 查询示例数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_data = cursor.fetchall()
            print("示例数据:")
            for row in sample_data:
                print(f"  {row}")
        
        conn.close()
        print("文件检查完成！")
        
    except sqlite3.Error as e:
        print(f"SQLite错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

def check_all_dat_files():
    """
    查找并检查所有.dat文件
    """
    print("===== 开始检查掘金量化数据文件 =====")
    
    # 数据根目录
    data_dir = os.path.join(project_root, "myquant_data")
    
    # 递归查找所有.dat文件
    def find_dat_files(directory, depth=0, max_depth=3):
        if depth > max_depth:
            return []
        
        dat_files = []
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) and item.endswith('.dat'):
                    dat_files.append(item_path)
                elif os.path.isdir(item_path):
                    dat_files.extend(find_dat_files(item_path, depth + 1, max_depth))
        except PermissionError:
            print(f"没有权限访问目录: {directory}")
        
        return dat_files
    
    # 查找所有.dat文件
    all_dat_files = find_dat_files(data_dir)
    print(f"总共找到 {len(all_dat_files)} 个.dat文件")
    
    # 分类.dat文件
    day_bar_files = [f for f in all_dat_files if 'day_bar' in f]
    minute_bar_files = [f for f in all_dat_files if 'min' in f.lower() or 'minute' in f.lower()]
    tick_data_files = [f for f in all_dat_files if 'tick' in f.lower()]
    other_files = [f for f in all_dat_files if f not in day_bar_files + minute_bar_files + tick_data_files]
    
    print(f"日线数据文件: {len(day_bar_files)}")
    print(f"分钟线数据文件: {len(minute_bar_files)}")
    print(f"Tick数据文件: {len(tick_data_files)}")
    print(f"其他数据文件: {len(other_files)}")
    
    # 检查storage.dat
    storage_file = os.path.join(data_dir, "data", "storage.dat")
    if os.path.exists(storage_file):
        print("\n检查storage.dat文件...")
        examine_sqlite_file(storage_file)
    
    # 检查日线数据示例
    if day_bar_files:
        print("\n检查日线数据示例...")
        examine_sqlite_file(day_bar_files[0])
    
    # 检查分钟线数据示例
    if minute_bar_files:
        print("\n检查分钟线数据示例...")
        examine_sqlite_file(minute_bar_files[0])
    
    # 检查Tick数据示例
    if tick_data_files:
        print("\n检查Tick数据示例...")
        examine_sqlite_file(tick_data_files[0])

if __name__ == "__main__":
    check_all_dat_files() 