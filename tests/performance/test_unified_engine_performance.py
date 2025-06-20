#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一引擎性能基准测试

测试V1/V2架构统一后的性能表现和对比
"""

import time
import pytest
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta

# 导入统一架构引擎
try:
    from qte.core.engines import (
        UnifiedVectorEngine, VectorEngineV2, VectorEngineV1Compat,
        create_engine
    )
    _UNIFIED_ENGINES_AVAILABLE = True
    print("✅ 统一引擎模块导入成功")
except ImportError as e:
    _UNIFIED_ENGINES_AVAILABLE = False
    print(f"❌ 统一引擎模块导入失败: {e}")


class SimpleStrategy:
    """简单测试策略"""
    
    def __init__(self, short_window: int = 10, long_window: int = 30):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        signals = data.copy()
        
        # 计算移动平均线
        signals['short_ma'] = signals['close'].rolling(window=self.short_window).mean()
        signals['long_ma'] = signals['close'].rolling(window=self.long_window).mean()
        
        # 生成信号
        signals['signal'] = 0
        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1
        
        return signals


def create_test_data(size: int, seed: int = 42) -> pd.DataFrame:
    """创建测试数据"""
    np.random.seed(seed)
    
    # 生成日期序列
    start_date = datetime(2020, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(size)]
    
    # 生成价格数据
    returns = np.random.normal(0.001, 0.02, size)
    prices = 100 * np.exp(np.cumsum(returns))
    
    # 创建OHLCV数据
    data = pd.DataFrame({
        'datetime': dates,
        'open': prices * (1 + np.random.normal(0, 0.001, size)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.005, size))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.005, size))),
        'close': prices,
        'volume': np.random.randint(1000, 10000, size)
    })
    
    return data


def measure_engine_performance(engine_factory, data_size: int, iterations: int = 3) -> Dict[str, Any]:
    """
    测量引擎性能
    
    Parameters
    ----------
    engine_factory : callable
        引擎创建函数
    data_size : int
        数据大小
    iterations : int
        迭代次数
        
    Returns
    -------
    Dict[str, Any]
        性能测试结果
    """
    times = []
    success_count = 0
    errors = []
    
    for i in range(iterations):
        try:
            # 创建测试数据和策略
            data = create_test_data(data_size, seed=42 + i)
            strategy = SimpleStrategy()
            
            # 创建引擎
            engine = engine_factory()
            
            # 配置引擎
            if hasattr(engine, 'initialize'):
                if 'V1Compat' in str(type(engine)):
                    engine.initialize(100000, 0.001)
                else:
                    engine.initialize({
                        'initial_capital': 100000,
                        'commission_rate': 0.001
                    })
            
            # 测量执行时间
            start_time = time.time()
            
            # 设置数据和策略
            engine.set_data(data)
            engine.add_strategy(strategy)
            
            # 运行回测
            result = engine.run_backtest()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 检查结果
            if hasattr(result, 'success'):
                success = result.success
            else:
                success = result.get('success', False)
            
            if success:
                times.append(execution_time)
                success_count += 1
            else:
                errors.append(f"Iteration {i}: 回测失败")
            
            # 清理资源
            if hasattr(engine, 'cleanup'):
                engine.cleanup()
                
        except Exception as e:
            errors.append(f"Iteration {i}: {str(e)}")
    
    # 计算统计信息
    if times:
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        std_time = np.std(times)
        throughput = data_size / avg_time
    else:
        avg_time = min_time = max_time = std_time = throughput = 0
    
    return {
        'data_size': data_size,
        'iterations': iterations,
        'success_count': success_count,
        'success_rate': success_count / iterations if iterations > 0 else 0,
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'std_time': std_time,
        'throughput': throughput,
        'errors': errors
    }


@pytest.mark.performance
@pytest.mark.skipif(not _UNIFIED_ENGINES_AVAILABLE, reason="统一引擎模块不可用")
class TestUnifiedEnginePerformance:
    """统一引擎性能测试类"""
    
    def test_unified_engine_basic_performance(self):
        """测试统一引擎基本性能"""
        engine_factory = lambda: UnifiedVectorEngine(compatibility_mode='auto')
        result = measure_engine_performance(engine_factory, 500, 2)
        
        # 验证性能指标
        assert result['success_rate'] >= 0.5, "成功率过低"
        assert result['avg_time'] < 10.0, "执行时间过长"
        assert result['throughput'] > 50, "吞吐量过低"
    
    def test_compatibility_modes_performance(self):
        """测试不同兼容性模式的性能"""
        modes = ['auto', 'v1', 'v2', 'hybrid']
        results = {}
        
        for mode in modes:
            engine_factory = lambda m=mode: UnifiedVectorEngine(compatibility_mode=m)
            result = measure_engine_performance(engine_factory, 300, 1)
            results[mode] = result
            
            # 基本性能要求
            assert result['success_rate'] > 0, f"模式 {mode} 完全失败"
            assert result['avg_time'] < 15.0, f"模式 {mode} 执行时间过长"
        
        # 打印性能对比
        print("\n兼容性模式性能对比:")
        for mode, result in results.items():
            print(f"  {mode}: {result['avg_time']:.3f}s, 吞吐量: {result['throughput']:.0f} 行/秒")
    
    def test_engine_comparison(self):
        """测试不同引擎的性能对比"""
        engines = {
            'UnifiedAuto': lambda: UnifiedVectorEngine(compatibility_mode='auto'),
            'UnifiedV2': lambda: UnifiedVectorEngine(compatibility_mode='v2'),
            'V2Direct': lambda: VectorEngineV2(),
            'V1Compat': lambda: VectorEngineV1Compat(),
        }
        
        data_size = 1000
        results = {}
        
        for name, factory in engines.items():
            result = measure_engine_performance(factory, data_size, 1)
            results[name] = result
            
            # 基本要求
            assert result['success_rate'] > 0, f"引擎 {name} 完全失败"
        
        # 性能对比分析
        print(f"\n引擎性能对比 (数据大小: {data_size}):")
        sorted_results = sorted(results.items(), key=lambda x: x[1]['avg_time'])
        
        for i, (name, result) in enumerate(sorted_results, 1):
            print(f"  {i}. {name}: {result['avg_time']:.3f}s, "
                  f"吞吐量: {result['throughput']:.0f} 行/秒, "
                  f"成功率: {result['success_rate']:.1%}")
    
    def test_scalability(self):
        """测试可扩展性"""
        data_sizes = [100, 500, 1000, 2000]
        engine_factory = lambda: UnifiedVectorEngine(compatibility_mode='auto')
        
        results = []
        for size in data_sizes:
            result = measure_engine_performance(engine_factory, size, 1)
            results.append((size, result))
            
            # 基本要求
            assert result['success_rate'] > 0, f"数据大小 {size} 测试失败"
            assert result['avg_time'] < size * 0.01, f"数据大小 {size} 性能过差"  # 100行/秒最低要求
        
        # 分析可扩展性
        print("\n可扩展性测试结果:")
        for size, result in results:
            print(f"  {size} 行: {result['avg_time']:.3f}s, "
                  f"吞吐量: {result['throughput']:.0f} 行/秒")
    
    def test_factory_performance(self):
        """测试引擎工厂性能"""
        factory_configs = [
            ('auto', {}),
            ('unified', {'compatibility_mode': 'auto'}),
            ('v2', {'high_performance': True}),
            ('v1', {'legacy_mode': True}),
        ]
        
        for engine_type, config in factory_configs:
            engine_factory = lambda: create_engine(engine_type, config)
            result = measure_engine_performance(engine_factory, 200, 1)
            
            # 验证工厂创建的引擎性能
            assert result['success_rate'] > 0, f"工厂引擎 {engine_type} 失败"
            assert result['avg_time'] < 5.0, f"工厂引擎 {engine_type} 性能过差"
            
            print(f"工厂引擎 {engine_type}: {result['avg_time']:.3f}s")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建多个引擎实例
        engines = []
        for i in range(5):
            engine = UnifiedVectorEngine(compatibility_mode='auto')
            engine.initialize({'initial_capital': 100000})
            engines.append(engine)
        
        # 运行一些操作
        data = create_test_data(500)
        strategy = SimpleStrategy()
        
        for engine in engines:
            engine.set_data(data)
            engine.add_strategy(strategy)
        
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # 清理
        for engine in engines:
            if hasattr(engine, 'cleanup'):
                engine.cleanup()
        
        print(f"内存使用测试: 初始 {initial_memory:.1f}MB, "
              f"峰值 {current_memory:.1f}MB, "
              f"增加 {memory_increase:.1f}MB")
        
        # 内存使用不应该过高
        assert memory_increase < 100, "内存使用过高"
    
    def test_concurrent_performance(self):
        """测试并发性能"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def run_engine_test():
            try:
                engine = UnifiedVectorEngine(compatibility_mode='auto')
                engine.initialize({'initial_capital': 100000})
                
                data = create_test_data(200)
                strategy = SimpleStrategy()
                
                start_time = time.time()
                engine.set_data(data)
                engine.add_strategy(strategy)
                result = engine.run_backtest()
                end_time = time.time()
                
                success = result.success if hasattr(result, 'success') else result.get('success', False)
                results_queue.put({
                    'success': success,
                    'time': end_time - start_time
                })
                
                if hasattr(engine, 'cleanup'):
                    engine.cleanup()
                    
            except Exception as e:
                results_queue.put({'error': str(e)})
        
        # 启动多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_engine_test)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # 验证并发性能
        success_count = sum(1 for r in results if r.get('success', False))
        error_count = sum(1 for r in results if 'error' in r)
        
        print(f"并发测试结果: 成功 {success_count}, 错误 {error_count}")
        
        assert success_count >= 2, "并发测试成功率过低"
        assert error_count <= 1, "并发测试错误过多"


def main():
    """运行性能基准测试"""
    if not _UNIFIED_ENGINES_AVAILABLE:
        print("❌ 统一引擎模块不可用，跳过性能测试")
        return
    
    print("🚀 开始统一引擎性能基准测试")
    print("=" * 50)
    
    # 运行基本性能测试
    print("\n1. 基本性能测试")
    engine_factory = lambda: UnifiedVectorEngine(compatibility_mode='auto')
    result = measure_engine_performance(engine_factory, 1000, 3)
    
    print(f"平均时间: {result['avg_time']:.3f}s")
    print(f"吞吐量: {result['throughput']:.0f} 行/秒")
    print(f"成功率: {result['success_rate']:.1%}")
    
    # 引擎对比测试
    print("\n2. 引擎对比测试")
    engines = {
        'UnifiedAuto': lambda: UnifiedVectorEngine(compatibility_mode='auto'),
        'V2Engine': lambda: VectorEngineV2(),
        'V1Compat': lambda: VectorEngineV1Compat(),
    }
    
    for name, factory in engines.items():
        result = measure_engine_performance(factory, 500, 1)
        print(f"{name}: {result['avg_time']:.3f}s, {result['throughput']:.0f} 行/秒")
    
    print("\n🎉 性能基准测试完成！")


if __name__ == "__main__":
    main()
