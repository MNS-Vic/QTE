"""
完整策略流程集成测试
测试从数据获取到信号生成、订单执行和结果分析的完整流程
"""
import pytest
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 测试所需的模块导入
try:
    from qte.core import Engine
    from qte.data.sources import DataSource
    from qte.strategy import Strategy
    from qte.portfolio import Portfolio
    from qte.execution import Executor
    from qte.analysis import Analyzer
except ImportError:
    # 如果不能导入，标记整个模块跳过
    pytest.skip("无法导入QTE核心模块，跳过策略流程集成测试", allow_module_level=True)


class TestStrategyFlow:
    """测试完整的策略执行流程"""
    
    @pytest.fixture(autouse=True)
    def setup(self, data_dir, configure_logging):
        """测试前设置"""
        self.logger = configure_logging
        self.logger.info("开始策略流程集成测试")
        
        # 初始化组件
        self.engine = Engine()
        self.data_source = DataSource()
        self.strategy = Strategy()
        self.portfolio = Portfolio()
        self.executor = Executor()
        self.analyzer = Analyzer()
        
        # 设置测试数据路径
        self.data_path = os.path.join(data_dir, 'sample')
        
        # 设置测试参数
        self.start_date = '2023-01-01'
        self.end_date = '2023-01-31'
        self.symbols = ['000001.XSHE']  # 使用示例股票代码
        
        # 配置组件连接
        self.engine.set_data_source(self.data_source)
        self.engine.set_strategy(self.strategy)
        self.engine.set_portfolio(self.portfolio)
        self.engine.set_executor(self.executor)
        self.engine.set_analyzer(self.analyzer)
        
        yield
        
        # 测试后清理
        self.logger.info("策略流程集成测试结束")
        self.engine = None
        self.data_source = None
        self.strategy = None
        self.portfolio = None
        self.executor = None
        self.analyzer = None
    
    def test_data_loading(self):
        """测试数据加载功能"""
        # 设置数据源
        self.data_source.set_data_path(self.data_path)
        
        # 加载数据
        data = self.data_source.load_data(
            symbols=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
            frequency='daily'
        )
        
        # 验证数据加载结果
        assert data is not None
        assert not data.empty
        assert all(symbol in data['symbol'].unique() for symbol in self.symbols)
        
        # 验证数据时间范围
        min_date = data.index.min().strftime('%Y-%m-%d')
        max_date = data.index.max().strftime('%Y-%m-%d')
        
        # 数据可能没有覆盖完整的请求范围，所以检查它至少包含一些数据
        assert min_date <= self.end_date
        assert max_date >= self.start_date
    
    def test_strategy_signal_generation(self):
        """测试策略信号生成"""
        # 准备测试数据
        dates = pd.date_range(start=self.start_date, end=self.end_date)
        prices = np.random.normal(100, 5, size=len(dates))
        volumes = np.random.randint(1000, 10000, size=len(dates))
        
        # 创建模拟K线数据
        data = pd.DataFrame({
            'symbol': self.symbols[0],
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices * (1 + 0.01 * np.random.randn(len(dates))),
            'volume': volumes
        }, index=dates)
        
        # 设置一个简单的移动平均策略
        self.strategy.set_parameters(
            short_window=5,
            long_window=10
        )
        
        # 生成信号
        signals = self.strategy.generate_signals(data)
        
        # 验证信号生成结果
        assert signals is not None
        assert not signals.empty
        assert 'signal' in signals.columns
        assert signals['symbol'].unique()[0] == self.symbols[0]
    
    def test_portfolio_order_generation(self):
        """测试投资组合订单生成"""
        # 准备测试信号
        dates = pd.date_range(start=self.start_date, end=self.end_date)
        signals = pd.DataFrame({
            'symbol': self.symbols[0],
            'signal': np.random.choice([-1, 0, 1], size=len(dates)),
            'price': np.random.normal(100, 5, size=len(dates))
        }, index=dates)
        
        # 设置投资组合参数
        self.portfolio.set_parameters(
            initial_capital=100000,
            position_size=0.1  # 每个信号使用10%的资金
        )
        
        # 生成订单
        orders = self.portfolio.generate_orders(signals)
        
        # 验证订单生成结果
        assert orders is not None
        assert not orders.empty
        assert 'symbol' in orders.columns
        assert 'quantity' in orders.columns
        assert 'direction' in orders.columns
        assert 'order_price' in orders.columns
    
    def test_order_execution(self):
        """测试订单执行"""
        # 准备测试订单
        dates = pd.date_range(start=self.start_date, end=self.end_date)
        test_orders = pd.DataFrame({
            'symbol': self.symbols[0],
            'quantity': np.random.randint(10, 100, size=len(dates)),
            'direction': np.random.choice(['BUY', 'SELL'], size=len(dates)),
            'order_price': np.random.normal(100, 5, size=len(dates))
        }, index=dates)
        
        # 设置执行器参数
        self.executor.set_parameters(
            commission_rate=0.001,
            slippage=0.001
        )
        
        # 执行订单
        executions = self.executor.execute_orders(test_orders)
        
        # 验证执行结果
        assert executions is not None
        assert not executions.empty
        assert 'symbol' in executions.columns
        assert 'quantity' in executions.columns
        assert 'direction' in executions.columns
        assert 'execution_price' in executions.columns
        assert 'commission' in executions.columns
    
    def test_analysis(self):
        """测试回测结果分析"""
        # 准备测试执行记录
        dates = pd.date_range(start=self.start_date, end=self.end_date)
        executions = pd.DataFrame({
            'symbol': self.symbols[0],
            'quantity': np.random.randint(10, 100, size=len(dates)),
            'direction': np.random.choice(['BUY', 'SELL'], size=len(dates)),
            'execution_price': np.random.normal(100, 5, size=len(dates)),
            'commission': np.random.uniform(1, 10, size=len(dates))
        }, index=dates)
        
        # 添加价格数据用于计算收益
        price_data = pd.DataFrame({
            'symbol': self.symbols[0],
            'close': np.random.normal(100, 5, size=len(dates) + 30)  # 额外添加30天价格便于计算收益
        }, index=pd.date_range(start=self.start_date, periods=len(dates) + 30))
        
        # 设置分析器参数
        self.analyzer.set_parameters(
            benchmark='000300.XSHG',
            risk_free_rate=0.03
        )
        
        # 进行分析
        results = self.analyzer.analyze(executions, price_data)
        
        # 验证分析结果
        assert results is not None
        assert 'total_return' in results
        assert 'sharpe_ratio' in results
        assert 'max_drawdown' in results
        assert 'win_rate' in results
    
    def test_end_to_end_flow(self):
        """测试完整策略执行流程"""
        # 设置执行参数
        params = {
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': 100000,
            'frequency': 'daily'
        }
        
        # 运行完整回测流程
        try:
            results = self.engine.run_backtest(params)
            
            # 验证结果
            assert results is not None
            assert 'performance' in results
            assert 'trades' in results
            assert 'equity_curve' in results
            
            # 检查关键指标
            performance = results['performance']
            assert 'total_return' in performance
            assert 'sharpe_ratio' in performance
            assert 'max_drawdown' in performance
            
        except Exception as e:
            self.logger.error(f"完整策略流程测试失败: {str(e)}")
            pytest.fail(f"完整策略流程测试失败: {str(e)}")


class TestMultipleStrategyFlow:
    """测试多策略并行执行流程"""
    
    @pytest.fixture(autouse=True)
    def setup(self, data_dir, configure_logging):
        """测试前设置"""
        self.logger = configure_logging
        self.logger.info("开始多策略流程集成测试")
        
        # 初始化引擎
        self.engine = Engine()
        
        # 创建多个测试策略
        self.strategies = {
            'ma_cross': Strategy(name='ma_cross'),
            'rsi': Strategy(name='rsi'),
            'momentum': Strategy(name='momentum')
        }
        
        # 设置测试数据路径
        self.data_path = os.path.join(data_dir, 'sample')
        
        # 设置测试参数
        self.start_date = '2023-01-01'
        self.end_date = '2023-01-31'
        self.symbols = ['000001.XSHE', '000002.XSHE']
        
        yield
        
        # 测试后清理
        self.logger.info("多策略流程集成测试结束")
        self.engine = None
        self.strategies = None
    
    def test_multiple_strategy_execution(self):
        """测试多个策略并行执行"""
        # 注册多个策略到引擎
        for name, strategy in self.strategies.items():
            # 配置策略(设置不同参数以产生不同信号)
            if name == 'ma_cross':
                strategy.set_parameters(short_window=5, long_window=10)
            elif name == 'rsi':
                strategy.set_parameters(rsi_period=14, overbought=70, oversold=30)
            elif name == 'momentum':
                strategy.set_parameters(momentum_period=20)
            
            # 注册策略
            self.engine.register_strategy(strategy)
        
        # 设置执行参数
        params = {
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': 100000,
            'frequency': 'daily'
        }
        
        # 运行多策略回测
        try:
            results = self.engine.run_multi_strategy_backtest(params)
            
            # 验证结果
            assert results is not None
            assert len(results) == len(self.strategies)
            
            # 检查每个策略的结果
            for name, strategy_result in results.items():
                assert 'performance' in strategy_result
                assert 'trades' in strategy_result
                assert 'equity_curve' in strategy_result
                
                # 验证策略名称
                assert name in self.strategies.keys()
            
        except Exception as e:
            self.logger.error(f"多策略流程测试失败: {str(e)}")
            pytest.fail(f"多策略流程测试失败: {str(e)}")
    
    def test_strategy_comparison(self):
        """测试策略对比分析"""
        # 先运行多策略回测获取结果
        params = {
            'symbols': self.symbols,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': 100000,
            'frequency': 'daily'
        }
        
        # 生成多策略回测的模拟结果
        strategy_results = {}
        for name in self.strategies.keys():
            # 创建一些模拟性能数据
            performance = {
                'total_return': np.random.uniform(0.05, 0.2),
                'sharpe_ratio': np.random.uniform(0.5, 2.0),
                'max_drawdown': np.random.uniform(0.05, 0.15),
                'volatility': np.random.uniform(0.1, 0.2),
                'win_rate': np.random.uniform(0.4, 0.6)
            }
            
            # 创建模拟权益曲线
            dates = pd.date_range(start=self.start_date, end=self.end_date)
            equity = 100000 * (1 + np.cumsum(np.random.normal(0.001, 0.01, size=len(dates))))
            equity_curve = pd.Series(equity, index=dates)
            
            strategy_results[name] = {
                'performance': performance,
                'equity_curve': equity_curve
            }
        
        # 进行策略对比分析
        try:
            comparison = self.engine.compare_strategies(strategy_results)
            
            # 验证对比结果
            assert comparison is not None
            assert 'performance_comparison' in comparison
            assert 'correlation_matrix' in comparison
            
            # 检查性能对比表
            perf_comparison = comparison['performance_comparison']
            assert all(name in perf_comparison.index for name in self.strategies.keys())
            assert 'total_return' in perf_comparison.columns
            assert 'sharpe_ratio' in perf_comparison.columns
            assert 'max_drawdown' in perf_comparison.columns
            
        except Exception as e:
            self.logger.error(f"策略对比分析测试失败: {str(e)}")
            pytest.fail(f"策略对比分析测试失败: {str(e)}") 