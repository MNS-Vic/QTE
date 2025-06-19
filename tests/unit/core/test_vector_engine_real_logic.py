"""
Vector Engine真实逻辑测试
专注于测试真实的业务逻辑路径，减少Mock使用，提升覆盖率
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock

from qte.core.vector_engine import VectorEngine


class TestVectorEngineRealLogic:
    """Vector Engine真实逻辑测试"""
    
    def test_vector_engine_initialization(self):
        """测试VectorEngine的初始化"""
        engine = VectorEngine()

        # 验证初始状态
        assert engine.data is None
        assert engine.signals is None
        assert engine.positions is None
        assert engine.results is None
        assert len(engine.strategies) == 0
        assert len(engine.performance_metrics) == 0

        # 测试带参数的初始化
        engine_with_params = VectorEngine(initial_capital=50000, commission_rate=0.002)
        assert engine_with_params.initial_capital == 50000
        assert engine_with_params.commission_rate == 0.002
    
    def test_vector_engine_data_loading(self):
        """测试VectorEngine的数据加载"""
        engine = VectorEngine()

        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        test_data = pd.DataFrame({
            'datetime': dates,
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.randint(1000, 10000, 100)
        })

        # 加载数据
        engine.set_data(test_data)

        # 验证数据加载
        assert engine.data is not None
        assert len(engine.data) == 100
        assert 'datetime' in engine.data.columns
        assert 'close' in engine.data.columns
    
    def test_vector_engine_strategy_integration(self):
        """测试VectorEngine的策略集成"""
        engine = VectorEngine()

        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        prices = np.array([100 + i + np.sin(i/5) * 5 for i in range(50)])  # 趋势+波动
        test_data = pd.DataFrame({
            'datetime': dates,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 50)
        })

        engine.set_data(test_data)

        # 创建简单的策略
        class SimpleStrategy:
            def generate_signals(self, data):
                signals = pd.Series(0, index=data.index)
                # 简单的移动平均策略
                ma_short = data['close'].rolling(5).mean()
                ma_long = data['close'].rolling(10).mean()
                signals[ma_short > ma_long] = 1
                signals[ma_short < ma_long] = -1
                return signals

        strategy = SimpleStrategy()
        engine.add_strategy(strategy)

        # 验证策略添加
        assert len(engine.strategies) == 1

        # 生成信号
        signals = engine.generate_signals()
        assert signals is not None
        assert 'signal' in signals.columns
        assert len(signals) == 50
    
    def test_vector_engine_position_calculation(self):
        """测试VectorEngine的持仓计算"""
        engine = VectorEngine()

        # 创建明显的趋势数据
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        # 前15天下跌，后15天上涨
        prices = np.concatenate([
            np.linspace(110, 90, 15),  # 下跌趋势
            np.linspace(90, 120, 15)   # 上涨趋势
        ])

        test_data = pd.DataFrame({
            'datetime': dates,
            'open': prices * 0.99,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 30)
        })

        engine.set_data(test_data)

        # 创建简单策略
        class TrendStrategy:
            def generate_signals(self, data):
                signals = pd.Series(0, index=data.index)
                # 简单趋势策略：价格上涨买入，下跌卖出
                price_change = data['close'].pct_change()
                signals[price_change > 0.01] = 1  # 上涨超过1%买入
                signals[price_change < -0.01] = -1  # 下跌超过1%卖出
                return signals

        strategy = TrendStrategy()
        engine.add_strategy(strategy)

        # 计算持仓
        positions = engine.calculate_positions()

        # 验证持仓计算
        assert positions is not None
        assert 'position' in positions.columns
        assert len(positions) == 30
    
    def test_vector_engine_returns_calculation(self):
        """测试VectorEngine的收益计算"""
        engine = VectorEngine()

        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        # 创建有明显趋势的价格数据
        base_price = 100
        trend = np.linspace(0, 10, 50)  # 10%的上涨趋势
        noise = np.random.normal(0, 0.5, 50)  # 随机噪声
        prices = base_price + trend + noise

        test_data = pd.DataFrame({
            'datetime': dates,
            'open': prices * 0.999,
            'high': prices * 1.005,
            'low': prices * 0.995,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 50)
        })

        engine.set_data(test_data)

        # 添加简单策略
        class BuyHoldStrategy:
            def generate_signals(self, data):
                signals = pd.Series(1, index=data.index)  # 始终持有
                signals.iloc[0] = 1  # 第一天买入
                return signals

        strategy = BuyHoldStrategy()
        engine.add_strategy(strategy)

        # 计算收益
        results = engine.calculate_returns()

        # 验证收益计算
        assert results is not None
        assert 'returns' in results.columns
        assert 'strategy_returns' in results.columns
        assert 'cum_returns' in results.columns
        assert 'cum_strategy_returns' in results.columns
        assert 'drawdown' in results.columns
        assert 'equity' in results.columns
        assert len(results) == 50
    
    def test_vector_engine_performance_metrics(self):
        """测试VectorEngine的性能指标计算"""
        engine = VectorEngine()

        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, 30))  # 随机游走

        test_data = pd.DataFrame({
            'datetime': dates,
            'open': prices * 0.999,
            'high': prices * 1.005,
            'low': prices * 0.995,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 30)
        })

        engine.set_data(test_data)

        # 添加简单策略
        class SimpleStrategy:
            def generate_signals(self, data):
                return pd.Series(1, index=data.index)  # 始终持有

        strategy = SimpleStrategy()
        engine.add_strategy(strategy)

        # 计算性能指标
        metrics = engine.calculate_metrics()

        # 验证性能指标
        assert isinstance(metrics, dict)
        assert 'total_return' in metrics
        assert 'annual_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'trade_count' in metrics
        assert 'win_rate' in metrics

        # 验证指标的合理性
        assert isinstance(metrics['total_return'], (int, float))
        assert isinstance(metrics['sharpe_ratio'], (int, float))
        assert 0 <= metrics['win_rate'] <= 1
    
    def test_vector_engine_complete_workflow(self):
        """测试VectorEngine的完整工作流程"""
        engine = VectorEngine(initial_capital=10000, commission_rate=0.001)

        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, 100))  # 随机游走

        test_data = pd.DataFrame({
            'datetime': dates,
            'open': prices * 0.999,
            'high': prices * 1.005,
            'low': prices * 0.995,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 100)
        })

        # 创建策略
        class MovingAverageStrategy:
            def generate_signals(self, data):
                signals = pd.Series(0, index=data.index)
                ma_short = data['close'].rolling(5).mean()
                ma_long = data['close'].rolling(20).mean()
                signals[ma_short > ma_long] = 1
                signals[ma_short < ma_long] = -1
                return signals

        strategy = MovingAverageStrategy()
        engine.add_strategy(strategy)

        # 运行完整回测
        results = engine.run(test_data)

        # 验证完整结果
        assert 'signals' in results
        assert 'positions' in results
        assert 'results' in results
        assert 'metrics' in results

        # 验证各个组件
        assert results['signals'] is not None
        assert results['positions'] is not None
        assert results['results'] is not None
        assert isinstance(results['metrics'], dict)

        # 验证性能指标
        metrics = results['metrics']
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
    
    def test_vector_engine_optimization(self):
        """测试VectorEngine的参数优化"""
        engine = VectorEngine()

        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, 50))  # 随机游走

        test_data = pd.DataFrame({
            'datetime': dates,
            'open': prices * 0.999,
            'high': prices * 1.005,
            'low': prices * 0.995,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 50)
        })

        # 创建可参数化的策略
        class ParameterizedStrategy:
            def __init__(self, short_period=5, long_period=20):
                self.short_period = short_period
                self.long_period = long_period

            def generate_signals(self, data):
                signals = pd.Series(0, index=data.index)
                ma_short = data['close'].rolling(self.short_period).mean()
                ma_long = data['close'].rolling(self.long_period).mean()
                signals[ma_short > ma_long] = 1
                signals[ma_short < ma_long] = -1
                return signals

        strategy = ParameterizedStrategy()
        engine.add_strategy(strategy)

        # 定义参数网格
        param_grid = {
            'short_period': [3, 5, 7],
            'long_period': [15, 20, 25]
        }

        # 运行参数优化
        results_df = engine.optimize(param_grid, test_data, metric='sharpe_ratio')

        # 验证优化结果
        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) == 9  # 3 * 3 = 9 种组合
        assert 'short_period' in results_df.columns
        assert 'long_period' in results_df.columns
        assert 'sharpe_ratio' in results_df.columns
