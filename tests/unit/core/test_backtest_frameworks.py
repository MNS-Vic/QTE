#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
比较不同量化回测框架的性能和特点

本脚本测试和对比多个流行的量化回测框架，包括：
1. vectorbt - 基于向量化操作的高性能回测框架
2. LEAN - QuantConnect开发的专业级事件驱动回测引擎
3. vnpy - 国内流行的事件驱动量化交易平台

通过相同的测试场景，比较各框架的运行速度、内存占用、易用性和功能特点
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time
import psutil
import os
import traceback
import sys
import gc
from functools import wraps

# 添加当前目录到路径，以导入其他测试模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 性能测量装饰器
def measure_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 记录开始时间
        start_time = time.time()
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        
        # 记录开始内存
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录结束时间和内存
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 计算性能指标
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            # 返回结果和性能指标
            return {
                'result': result,
                'execution_time': execution_time,
                'memory_used': memory_used,
                'success': True,
                'error': None
            }
        except Exception as e:
            # 记录异常信息
            end_time = time.time()
            execution_time = end_time - start_time
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            
            return {
                'result': None,
                'execution_time': execution_time,
                'memory_used': 0,
                'success': False,
                'error': error_msg,
                'traceback': error_traceback
            }
        finally:
            # 强制垃圾回收以避免内存泄漏
            gc.collect()
    
    return wrapper

# 测试vectorbt的双均线策略回测
@measure_performance
def test_vectorbt():
    """运行vectorbt的双均线交叉策略回测"""
    from test.test_vectorbt_backtest import test_ma_crossover_strategy
    return test_ma_crossover_strategy()

# 测试LEAN风格的双均线策略回测
@measure_performance
def test_lean():
    """运行LEAN风格的双均线交叉策略回测"""
    from test.test_lean_backtest import test_lean_backtest
    return test_lean_backtest()

# 测试vnpy风格的双均线策略回测
@measure_performance
def test_vnpy():
    """运行vnpy风格的双均线交叉策略回测"""
    from test.test_vnpy_backtest import test_vnpy_backtest
    return test_vnpy_backtest()

def format_performance(perf_data):
    """格式化性能测试结果"""
    if perf_data['success']:
        return {
            'execution_time': f"{perf_data['execution_time']:.4f} 秒",
            'memory_used': f"{perf_data['memory_used']:.2f} MB",
            'success': '✓',
            'error': '无'
        }
    else:
        return {
            'execution_time': f"{perf_data['execution_time']:.4f} 秒",
            'memory_used': 'N/A',
            'success': '✗',
            'error': perf_data['error']
        }

def compare_frameworks():
    """比较不同回测框架的性能"""
    print("正在对比各回测框架的性能，请稍等...")
    
    # 运行各框架测试
    print("\n运行 vectorbt 回测...")
    vectorbt_perf = test_vectorbt()
    
    print("\n运行 LEAN风格 回测...")
    lean_perf = test_lean()
    
    print("\n运行 vnpy风格 回测...")
    vnpy_perf = test_vnpy()
    
    # 格式化结果
    vectorbt_result = format_performance(vectorbt_perf)
    lean_result = format_performance(lean_perf)
    vnpy_result = format_performance(vnpy_perf)
    
    # 创建比较表格
    comparison = pd.DataFrame({
        'vectorbt': vectorbt_result,
        'LEAN风格': lean_result,
        'vnpy风格': vnpy_result
    }).T
    
    # 显示结果
    print("\n\n========== 回测框架性能对比 ==========")
    print(comparison)
    
    # 展示各框架特点对比
    print("\n\n========== 回测框架特点对比 ==========")
    features = pd.DataFrame({
        'vectorbt': {
            '架构模式': '向量化操作',
            '运行速度': '极快',
            '内存占用': '中等',
            '上手难度': '中等',
            '实盘支持': '需要额外开发',
            '参数优化': '原生内置、速度极快',
            '多资产支持': '支持',
            '图表可视化': '高级交互式图表',
            '适用场景': '海量参数优化、高频策略'
        },
        'LEAN': {
            '架构模式': '事件驱动',
            '运行速度': '中等',
            '内存占用': '中等',
            '上手难度': '较高',
            '实盘支持': '原生支持',
            '参数优化': '支持但速度较慢',
            '多资产支持': '全面支持多市场多资产',
            '图表可视化': '完整的可视化报告',
            '适用场景': '专业量化策略、实盘交易'
        },
        'vnpy': {
            '架构模式': '事件驱动',
            '运行速度': '中等',
            '内存占用': '较低',
            '上手难度': '中等',
            '实盘支持': '原生支持多种接口',
            '参数优化': '支持',
            '多资产支持': '支持国内外多市场',
            '图表可视化': '基础图表',
            '适用场景': '国内市场策略实盘交易'
        }
    }).T
    
    print(features)
    
    # 绘制执行时间对比图
    try:
        frameworks = ['vectorbt', 'LEAN', 'vnpy']
        exec_times = [
            vectorbt_perf['execution_time'] if vectorbt_perf['success'] else 0,
            lean_perf['execution_time'] if lean_perf['success'] else 0,
            vnpy_perf['execution_time'] if vnpy_perf['success'] else 0
        ]
        
        plt.figure(figsize=(10, 6))
        plt.bar(frameworks, exec_times, color=['#5DA5DA', '#FAA43A', '#60BD68'])
        plt.title('不同回测框架执行时间对比')
        plt.ylabel('执行时间 (秒)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 在柱状图上添加具体数值
        for i, v in enumerate(exec_times):
            plt.text(i, v + 0.1, f'{v:.2f}秒', ha='center')
        
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"无法绘制对比图表: {e}")
    
    return {
        'vectorbt': vectorbt_perf,
        'lean': lean_perf,
        'vnpy': vnpy_perf
    }

def recommend_framework():
    """根据不同需求场景，推荐最适合的回测框架"""
    print("\n\n========== 回测框架选择建议 ==========")
    
    recommendations = {
        '大规模参数优化': 'vectorbt - 基于向量化操作，可以同时处理数百万种参数组合，是参数优化的最佳选择',
        '策略开发与研究': 'LEAN或vnpy - 事件驱动架构更符合实际交易逻辑，便于策略研发',
        '高频量化策略': 'vectorbt或LEAN - vectorbt速度极快，LEAN可细粒度控制交易执行',
        '国内市场实盘': 'vnpy - 支持最全面的国内交易接口，对A股、期货等支持完善',
        '国际市场实盘': 'LEAN - 支持多种国际市场和经纪商',
        '量化教学与入门': 'vnpy或vectorbt - vnpy文档全面、中文支持好；vectorbt简洁易懂',
        '机构级专业应用': 'LEAN - 架构专业，支持分布式部署，适合专业机构',
        '快速验证交易想法': 'vectorbt - 极快的回测速度，便于快速验证想法'
    }
    
    for scenario, recommendation in recommendations.items():
        print(f"【{scenario}】\n推荐: {recommendation}\n")
    
    print("最终建议:")
    print("1. 如果您需要大规模参数优化和验证交易想法，选择 vectorbt")
    print("2. 如果您需要完整的策略开发、回测到实盘一体化解决方案，选择 vnpy")
    print("3. 如果您需要专业级架构和跨市场支持，选择 LEAN")
    print("4. 理想的工作流：用vectorbt快速验证想法和优化参数，然后用vnpy/LEAN实现完整策略并实盘")

if __name__ == "__main__":
    # 运行对比测试
    perf_results = compare_frameworks()
    
    # 提供框架选择建议
    recommend_framework() 