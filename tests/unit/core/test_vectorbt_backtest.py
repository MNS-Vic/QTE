#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于vectorbt实现的简单双均线交叉策略回测脚本

vectorbt作为一个高性能的量化回测库，通过向量化操作和numba加速，
能够高效地处理大量数据和多参数优化。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import vectorbt as vbt

def test_ma_crossover_strategy():
    """
    测试双均线交叉策略
    
    使用vectorbt进行简单的双均线交叉策略回测，并输出结果
    """
    # 设置回测期间
    start_date = '2020-01-01'
    end_date = '2022-12-31'
    
    # 下载上证指数数据
    symbol = '000001.XSHG'  # 上证指数
    try:
        price = vbt.YFData.download('000001.SS', start=start_date, end=end_date).get('Close')
        print(f"成功获取上证指数数据，共 {len(price)} 条记录")
    except Exception as e:
        print(f"获取数据失败: {e}")
        # 如果获取失败，使用随机生成的数据作为备选
        np.random.seed(42)
        index = pd.date_range(start=start_date, end=end_date, freq='B')
        price = pd.Series(np.random.randint(2800, 3600, size=len(index)) + 
                        np.random.random(size=len(index)) * 100, 
                        index=index)
        print(f"使用随机生成的数据进行测试，共 {len(price)} 条记录")
    
    # 计算各种窗口大小的移动平均线
    fast_windows = [5, 10, 15]
    slow_windows = [20, 30, 50]
    
    # 计算快速移动平均线
    fast_ma = vbt.MA.run(price, fast_windows, short_name='fast')
    # 计算慢速移动平均线
    slow_ma = vbt.MA.run(price, slow_windows, short_name='slow')
    
    # 生成交易信号：当快线上穿慢线时买入，当快线下穿慢线时卖出
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    
    # 运行回测
    pf = vbt.Portfolio.from_signals(price, entries, exits, 
                                  fees=0.001, # 设置手续费为0.1%
                                  freq='1D')  # 日频数据
    
    # 输出回测结果
    print("\n====== 回测结果汇总 ======")
    print(f"总收益率：\n{pf.total_return()}")
    print(f"\n年化收益率：\n{pf.annual_return()}")
    print(f"\n夏普比率：\n{pf.sharpe_ratio()}")
    print(f"\n最大回撤：\n{pf.max_drawdown()}")
    
    # 找出表现最好的参数组合
    best_idx = pf.sharpe_ratio().idxmax()
    if isinstance(best_idx, tuple):
        best_fast, best_slow = best_idx
        print(f"\n最佳参数组合 - 快线: {best_fast}, 慢线: {best_slow}")
        print(f"该参数组合的夏普比率: {pf.sharpe_ratio().loc[best_idx]:.4f}")
        print(f"该参数组合的总收益率: {pf.total_return().loc[best_idx]:.4f}")
    else:
        print("\n无法确定最佳参数组合")
    
    # 绘制回测结果
    try:
        pf.plot().show()
    except Exception as e:
        print(f"无法绘制图表: {e}")
    
    return pf

if __name__ == "__main__":
    pf = test_ma_crossover_strategy() 