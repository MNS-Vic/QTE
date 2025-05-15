import pandas as pd
import os
import sys

# 将项目根目录添加到sys.path，以便导入qte模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from qte.core.engine_manager import EngineManager, EngineType
from strategies.traditional.dual_ma_strategy import DualMaStrategy

def run_real_data_backtest():
    """使用真实数据运行双均线策略回测"""
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")

    # 真实数据文件路径 (假设在 examples/test_data/real_stock_data.csv)
    data_file_path = os.path.join(project_root, "examples", "test_data", "real_stock_data.csv")
    print(f"尝试加载真实数据文件: {data_file_path}")

    if not os.path.exists(data_file_path):
        print(f"错误: 真实数据文件未找到于 {data_file_path}")
        return

    # 加载数据
    try:
        raw_data = pd.read_csv(data_file_path)
    except Exception as e:
        print(f"加载真实数据时发生错误: {e}")
        return

    print("真实数据原始表头:", raw_data.columns.tolist())
    print(raw_data.head())

    # 数据预处理
    # 1. 重命名列以匹配框架要求 (datetime, open, high, low, close, volume)
    #    假设真实数据CSV有 'date', 'code', 'open', 'high', 'low', 'close', 'volume' 列
    data = raw_data.rename(columns={
        'date': 'datetime', # 将 'date' 重命名为 'datetime'
        # 如果您的列名不同，请在此处添加更多映射
        # 'your_open_col': 'open',
        # 'your_high_col': 'high',
        # 'your_low_col': 'low',
        # 'your_close_col': 'close',
        # 'your_volume_col': 'volume'
    })

    # 2. 确保datetime列被正确解析为日期时间对象并设为索引
    if 'datetime' in data.columns:
        data['datetime'] = pd.to_datetime(data['datetime'])
        data.set_index('datetime', inplace=True)
    else:
        print("错误: 数据中缺少'datetime'列 (或未能正确重命名)")
        return
    
    # 3. 确保必要的 OHLCV 列存在
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        print(f"错误: 数据中缺少以下必要列: {missing_cols}")
        return

    # 4. 按时间排序 (如果数据未排序)
    data.sort_index(inplace=True)

    # (可选) 筛选特定股票代码和时间段
    # if 'code' in data.columns:
    #     data = data[data['code'] == 'sh.600000'] # 假设我们只回测这只股票
    # data = data.loc['2022-01-01':'2023-01-01'] # 假设回测特定时间段
        
    print("预处理后的数据加载成功:")
    print(data.head())

    # 创建策略实例
    strategy = DualMaStrategy(short_window=10, long_window=30) # 可以调整参数

    # --- 向量化回测 ---
    print("\n开始运行基于真实数据的向量化回测...")
    manager_vector = EngineManager(engine_type=EngineType.VECTOR)
    manager_vector.add_strategy(strategy)
    try:
        results_vector = manager_vector.run(data.copy()) 
        print("向量化回测完成.")
        print("\n向量化回测性能指标:")
        if results_vector and 'metrics' in results_vector:
            for metric, value in results_vector['metrics'].items():
                print(f"{metric}: {value:.4f}")
        else:
            print("未能获取向量化回测的性能指标。")
        # 更多输出可以取消注释
        # print("\n向量化回测信号:"); print(results_vector['signals'].head())
        # print("\n向量化回测持仓:"); print(results_vector['positions'].head())
        # print("\n向量化回测逐日结果:"); print(results_vector['results'].head())
    except Exception as e:
        print(f"向量化回测过程中发生错误: {e}")
        import traceback; traceback.print_exc()

    # --- 事件驱动回测 ---
    print("\n开始运行基于真实数据的事件驱动回测...")
    manager_event = EngineManager(engine_type=EngineType.EVENT)
    manager_event.add_strategy(strategy) # DualMaStrategy 已适配事件驱动
    
    # 为事件驱动引擎准备数据格式: Dict[str, List[Dict]]
    # 假设我们使用 'code' 列作为 symbol，如果不存在，则用默认值
    symbol_name = data['code'].iloc[0] if 'code' in data.columns and not data['code'].empty else 'REAL_STOCK'
    event_data_list = data.reset_index().to_dict('records')
    formatted_event_data_list = []
    for record in event_data_list:
        if 'datetime' in record: # reset_index后，datetime是普通列
            record['timestamp'] = record.pop('datetime')
        formatted_event_data_list.append(record)
    event_data = {symbol_name: formatted_event_data_list}

    try:
        results_event = manager_event.run(event_data)
        print("事件驱动回测完成.")
        print("\n事件驱动回测性能指标:")
        if results_event and 'metrics' in results_event and isinstance(results_event['metrics'], dict):
            for metric, value in results_event['metrics'].items():
                if isinstance(value, float):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
        else:
            print("未能获取事件驱动回测的性能指标或指标格式不正确。")
        # 更多输出可以取消注释
        # print("\n事件驱动回测资产曲线:"); print(results_event['equity_curve'].head())
        # print("\n事件驱动回测交易记录:"); print(results_event['transactions'][:5])
    except Exception as e:
        print(f"事件驱动回测过程中发生错误: {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    # 替换为新的函数名，或者保留旧的并修改其内容
    # run_backtest() # 这是旧的测试数据回测
    run_real_data_backtest() # 这是新的真实数据回测 