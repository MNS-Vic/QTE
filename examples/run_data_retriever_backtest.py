import pandas as pd
import os
import sys

# 将项目根目录添加到sys.path，以便导入qte模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from qte.core.engine_manager import EngineManager, EngineType
from strategies.traditional.dual_ma_strategy import DualMaStrategy
from qte.data import GmQuantDataRetriever, LocalCsvRetriever # 导入数据获取器

def run_backtest_with_data_retriever():
    """使用数据获取器运行双均线策略回测"""
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")

    # --- 使用 GmQuantDataRetriever (当前为模拟，从本地CSV加载) ---
    print("\n--- 测试 GmQuantDataRetriever (模拟掘金数据获取) ---")
    # 实际使用时，您可能需要提供token: retriever = GmQuantDataRetriever(token='YOUR_GM_TOKEN')
    gm_retriever = GmQuantDataRetriever() 
    
    # 掘金的symbol通常是 'SHSE.600000' 或 'SZSE.000001'。
    # 我们的 real_stock_data.csv 文件中的 'code' 列是 'sh.600000'
    # 所以，当 GmQuantDataRetriever 内部调用 LocalCsvRetriever 时，这个symbol会被用于筛选
    gm_symbol = 'sh.600000'
    gm_start_date = '2022-01-01'
    gm_end_date = '2022-01-20' # 使用一个较短的日期范围，确保在示例数据中有数据
    
    print(f"尝试使用GmQuantDataRetriever获取 {gm_symbol} 从 {gm_start_date} 到 {gm_end_date}")
    data_gm = gm_retriever.download_data(
        symbol=gm_symbol, 
        start_date=gm_start_date, 
        end_date=gm_end_date,
        # GmQuantDataRetriever内部模拟时，会固定使用 real_stock_data.csv, date_col='date', symbol_col_in_file='code'
    )

    if data_gm is None or data_gm.empty:
        print(f"未能通过GmQuantDataRetriever获取 {gm_symbol} 的数据。请检查data_retriever.py中的模拟逻辑和CSV文件。")
        return
    
    print(f"通过GmQuantDataRetriever获取数据成功 ({gm_symbol}):")
    print(data_gm.head())

    # 创建策略实例
    strategy_gm = DualMaStrategy(short_window=5, long_window=10) # 短窗口以适应小数据

    # --- 向量化回测 (使用GmQuantDataRetriever获取的数据) ---
    print("\n开始运行基于GmQuantDataRetriever数据的向量化回测...")
    manager_vector_gm = EngineManager(engine_type=EngineType.VECTOR)
    manager_vector_gm.add_strategy(strategy_gm)
    try:
        results_vector_gm = manager_vector_gm.run(data_gm.copy()) 
        print("向量化回测完成.")
        print("\n向量化回测性能指标 (GmQuantDataRetriever):")
        if results_vector_gm and 'metrics' in results_vector_gm:
            for metric, value in results_vector_gm['metrics'].items():
                print(f"{metric}: {value:.4f}")
        else:
            print("未能获取向量化回测的性能指标。")
    except Exception as e:
        print(f"向量化回测过程中发生错误: {e}")
        import traceback; traceback.print_exc()

    # --- 事件驱动回测 (使用GmQuantDataRetriever获取的数据) ---
    print("\n开始运行基于GmQuantDataRetriever数据的事件驱动回测...")
    manager_event_gm = EngineManager(engine_type=EngineType.EVENT)
    # 需要为事件驱动模式重新实例化策略，因为策略内部有状态(如prices deque)
    strategy_event_gm = DualMaStrategy(short_window=5, long_window=10)
    manager_event_gm.add_strategy(strategy_event_gm)
        
    # 为事件驱动引擎准备数据格式
    event_data_list_gm = data_gm.reset_index().to_dict('records')
    formatted_event_data_list_gm = []
    for record in event_data_list_gm:
        if 'datetime' in record:
            record['timestamp'] = record.pop('datetime')
        formatted_event_data_list_gm.append(record)
    # 对于事件驱动，symbol是字典的键
    event_data_gm = {gm_symbol: formatted_event_data_list_gm} 

    try:
        results_event_gm = manager_event_gm.run(event_data_gm)
        print("事件驱动回测完成.")
        print("\n事件驱动回测性能指标 (GmQuantDataRetriever):")
        if results_event_gm and 'metrics' in results_event_gm and isinstance(results_event_gm['metrics'], dict):
            for metric, value in results_event_gm['metrics'].items():
                if isinstance(value, float):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
        else:
            print("未能获取事件驱动回测的性能指标或指标格式不正确。")
    except Exception as e:
        print(f"事件驱动回测过程中发生错误: {e}")
        import traceback; traceback.print_exc()

    # --- (可选) 直接测试 LocalCsvRetriever ---
    # print("\n--- 测试 LocalCsvRetriever 直接调用 ---")
    # csv_retriever = LocalCsvRetriever() # base_path 默认指向 examples/test_data/
    # csv_symbol = 'sh.600000'
    # csv_start_date = '2022-01-01'
    # csv_end_date = '2022-01-15'
    # data_csv = csv_retriever.download_data(
    #     symbol=csv_symbol, 
    #     start_date=csv_start_date, 
    #     end_date=csv_end_date,
    #     file_name='real_stock_data.csv',
    #     date_col='date', 
    #     symbol_col_in_file='code',
    #     column_rename_map={'open':'open', 'high':'high', 'low':'low', 'close':'close', 'volume':'volume'} # 你的列名映射
    # )
    # if data_csv is not None:
    #     print(f"CSV Retriever ({csv_symbol}) data:")
    #     print(data_csv.head())
    #     # 在这里可以添加使用 data_csv 进行回测的逻辑
    # else:
    #     print(f"Failed to load data for {csv_symbol} using LocalCsvRetriever.")

if __name__ == "__main__":
    run_backtest_with_data_retriever() 