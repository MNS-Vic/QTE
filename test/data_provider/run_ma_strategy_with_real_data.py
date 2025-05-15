import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime

# 将项目根目录添加到sys.path，以便导入qte模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from qte.core.engine_manager import EngineManager, EngineType
from strategies.traditional.dual_ma_strategy import DualMaStrategy
from qte.data.sources.gm_quant import GmQuantSource
from qte.data.data_source_manager import get_data_source_manager

def run_ma_backtest_with_real_data():
    """使用掘金数据源的真实数据运行移动平均线策略回测"""
    
    print("=" * 60)
    print("使用掘金数据源的真实数据运行移动平均线策略回测")
    print("=" * 60)
    
    # 初始化掘金数据源
    token = os.environ.get('GM_TOKEN', 'd6e3ba1ba79d0af43300589d35af32bdf9e5800b')
    gm_source = GmQuantSource(token=token)
    
    # 连接掘金API
    if not gm_source.connect():
        print("连接掘金API失败，无法继续测试")
        return
        
    # 获取数据源管理器并注册掘金数据源
    dsm = get_data_source_manager()
    dsm.register_source('gm', gm_source, make_default=True)
    
    # 配置回测参数
    symbol = 'SHSE.600000'  # 浦发银行
    start_date = '2022-01-01'
    end_date = '2022-12-31'
    short_window = 5
    long_window = 20
    
    print(f"\n获取 {symbol} 从 {start_date} 到 {end_date} 的日线数据...")
    
    # 获取股票数据
    data = dsm.get_bars(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        frequency='1d'
    )
    
    if data is None or data.empty:
        print(f"获取 {symbol} 的数据失败，无法继续回测")
        return
        
    print(f"成功获取 {len(data)} 条数据")
    print("\n数据预览:")
    print(data.head())
    
    # 创建策略实例
    strategy = DualMaStrategy(short_window=short_window, long_window=long_window)
    
    # --- 向量化回测 ---
    print("\n" + "=" * 60)
    print(f"开始运行向量化回测 (短均线={short_window}, 长均线={long_window})...")
    
    # 创建向量化引擎管理器
    manager_vector = EngineManager(engine_type=EngineType.VECTOR)
    manager_vector.add_strategy(strategy)
    
    # 运行回测
    results_vector = manager_vector.run(data.copy())
    
    if not results_vector or 'metrics' not in results_vector:
        print("向量化回测未返回有效结果")
    else:
        print("\n向量化回测性能指标:")
        for metric, value in results_vector['metrics'].items():
            print(f"  {metric}: {value:.4f}")
            
        # 获取策略生成的信号
        signals = results_vector.get('signals', None)
        if signals is not None:
            # 绘制价格和信号
            plt.figure(figsize=(12, 6))
            plt.plot(data.index, data['close'], label='收盘价')
            plt.plot(signals.index, signals['short_ma'], label=f'{short_window}日均线')
            plt.plot(signals.index, signals['long_ma'], label=f'{long_window}日均线')
            
            # 标记买入信号
            buy_signals = signals[signals['signal'] == 1].index
            sell_signals = signals[signals['signal'] == -1].index
            
            plt.scatter(buy_signals, data.loc[buy_signals, 'close'], 
                       marker='^', color='g', s=100, label='买入信号')
            plt.scatter(sell_signals, data.loc[sell_signals, 'close'], 
                       marker='v', color='r', s=100, label='卖出信号')
            
            plt.title(f'{symbol} 移动平均线策略 ({short_window}/{long_window}) - 向量化回测')
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.legend()
            plt.grid(True)
            
            # 保存图表
            plt.savefig(f'test/data_provider/ma_strategy_vector_{symbol.replace(".", "_")}.png')
            print(f"\n向量化回测结果图表已保存到: test/data_provider/ma_strategy_vector_{symbol.replace('.', '_')}.png")
    
    # --- 事件驱动回测 ---
    print("\n" + "=" * 60)
    print(f"开始运行事件驱动回测 (短均线={short_window}, 长均线={long_window})...")
    
    # 需要为事件驱动模式重新实例化策略，因为策略内部有状态
    strategy_event = DualMaStrategy(short_window=short_window, long_window=long_window)
    
    # 创建事件驱动引擎管理器
    manager_event = EngineManager(engine_type=EngineType.EVENT)
    manager_event.add_strategy(strategy_event)
    
    # 为事件驱动引擎准备数据格式
    event_data = data.reset_index().to_dict('records')
    formatted_event_data = []
    
    for record in event_data:
        if 'datetime' in record:
            record['timestamp'] = record.pop('datetime')
        formatted_event_data.append(record)
    
    # 对于事件驱动，symbol是字典的键
    event_data_dict = {symbol: formatted_event_data}
    
    # 运行回测
    results_event = manager_event.run(event_data_dict)
    
    if not results_event or 'metrics' not in results_event:
        print("事件驱动回测未返回有效结果")
    else:
        print("\n事件驱动回测性能指标:")
        for metric, value in results_event['metrics'].items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.4f}")
            else:
                print(f"  {metric}: {value}")
        
        # 事件驱动引擎通常不会返回信号序列，因此这里不绘制图表
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    run_ma_backtest_with_real_data() 