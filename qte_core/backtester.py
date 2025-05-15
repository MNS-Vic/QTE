import sys
import os
# 获取当前脚本文件所在的目录 (qte_core)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (Quantitative-Backtesting-Engine)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"DEBUG: sys.path modified. Project root '{project_root}' added.")
print(f"DEBUG: Current sys.path: {sys.path}")

import time
import queue # 用于捕获 queue.Empty 异常
from datetime import datetime

from qte_core.event_loop import EventLoop
from qte_core.events import EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from qte_data.interfaces import DataProvider
from qte_strategy.interfaces import Strategy
from qte_portfolio_risk.interfaces import Portfolio
from qte_execution.interfaces import BrokerSimulator
from qte_analysis_reporting.logger import app_logger

class BE_Backtester:
    """
    基础回测编排器 (BE_Backtester)。
    负责初始化和协调回测过程中的各个组件。
    """
    def __init__(self,
                 event_loop: EventLoop,
                 data_provider: DataProvider,
                 strategy: Strategy,
                 portfolio: Portfolio,
                 broker: BrokerSimulator,
                 symbols: list[str] # 需要回测的交易品种列表
                 ):
        """
        初始化回测编排器。

        参数:
            event_loop (EventLoop): 事件循环实例。
            data_provider (DataProvider): 数据提供者实例。
            strategy (Strategy): 策略实例。
            portfolio (Portfolio): 投资组合实例。
            broker (BrokerSimulator): 模拟经纪商实例。
            symbols (list[str]): 需要进行回测的交易品种列表。
        """
        self.event_loop = event_loop
        self.data_provider = data_provider
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = broker
        self.symbols = symbols # 策略和投资组合可能也需要知道它们

        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """注册核心事件处理器到事件循环。"""
        app_logger.info("回测器：注册事件处理器...")

        # 市场数据事件 -> 策略和投资组合
        self.event_loop.register_handler(EventType.MARKET, self.strategy.on_market_event)
        self.event_loop.register_handler(EventType.MARKET, self.portfolio.update_on_market_data)

        # 信号事件 -> 投资组合 (通常由Portfolio在其__init__中自行注册)
        # BasePortfolio 已经在其 __init__ 中注册了 self.on_signal
        # 因此这里不需要重复注册，除非设计改变。
        # app_logger.info("注意：Portfolio.on_signal 应由 Portfolio 自身注册。")

        # 订单事件 -> 经纪商
        self.event_loop.register_handler(EventType.ORDER, self.broker.submit_order)

        # 成交事件 -> 投资组合
        self.event_loop.register_handler(EventType.FILL, self.portfolio.update_on_fill)
        
        app_logger.info("回测器：事件处理器注册完毕。")

    def run_backtest(self) -> None:
        """
        运行回测。
        1. 初始化策略（预加载历史数据）
        2. 数据提供者将所有历史市场事件放入队列。
        3. 事件循环处理队列中的事件，直到队列为空并且没有新的事件生成。
        4. 打印投资组合摘要。
        """
        app_logger.info(f"回测开始，针对品种: {self.symbols}。时间: {datetime.now()}")
        start_time = time.time()

        # 0. 初始化策略（预加载历史数据）
        app_logger.info("步骤 0: 初始化策略，预加载历史数据...")
        if hasattr(self.strategy, 'on_init') and callable(getattr(self.strategy, 'on_init')):
            self.strategy.on_init(self.data_provider)
        else:
            app_logger.warning("策略对象没有可调用的 on_init 方法，跳过策略初始化。")

        # 1. 数据提供者加载并流式传输所有市场数据到事件队列
        app_logger.info("步骤 1: 数据提供者开始流式传输所有市场数据...")
        market_events_count = 0
        for event in self.data_provider.stream_market_data(symbols=self.symbols):
            market_events_count += 1
            if market_events_count % 100 == 0:
                app_logger.debug(f"已加载 {market_events_count} 个市场事件")
        app_logger.info(f"数据提供者已将所有市场数据推送到事件队列，共 {market_events_count} 个事件。")

        # 2. 运行事件循环直到队列处理完毕
        app_logger.info("步骤 2: 开始主事件处理循环...")
        processed_event_count = 0
        event_type_counts = {event_type.name: 0 for event_type in EventType}
        
        while True:
            try:
                # 使用带有超时的非阻塞get_event，以允许检查队列是否真的处理完毕
                event = self.event_loop.get_event(block=True, timeout=0.01) # 短暂超时
                
                if event:
                    processed_event_count += 1
                    # 更新事件类型计数
                    if hasattr(event, 'event_type'):
                        event_type_counts[event.event_type.name] += 1
                        
                    if processed_event_count % 100 == 0:
                        app_logger.debug(f"已处理 {processed_event_count} 个事件。当前事件: {type(event).__name__} for {getattr(event, 'symbol', 'N/A')} at {getattr(event, 'timestamp', 'N/A')}")
                    
                    self.event_loop._dispatch_event(event) # 使用事件循环的内部调度逻辑
                else:
                    # Timeout 发生，并且get_event返回None，检查队列是否真的为空
                    if not self.event_loop.event_queue:
                        app_logger.info("事件队列已空，并且在超时内无新事件，判断回测事件处理完毕。")
                        break
            except queue.Empty:
                # 这个异常理论上不应该在 block=True 时发生，除非timeout非常短且队列恰好变空
                # 但作为安全措施，如果发生，也表示队列空了
                app_logger.info("事件队列报告为空 (queue.Empty)，结束事件处理循环。")
                break
            except KeyboardInterrupt:
                app_logger.warning("捕获到键盘中断，正在提前终止回测...")
                break
            except Exception as e:
                app_logger.error(f"回测主循环中发生未捕获错误: {e}", exc_info=True)
                break
        
        end_time = time.time()
        app_logger.info(f"事件处理循环结束。总共处理了 {processed_event_count} 个事件。")
        app_logger.info(f"事件类型统计: {event_type_counts}")
        app_logger.info(f"回测耗时: {end_time - start_time:.2f} 秒。")

        # 3. 打印投资组合摘要
        app_logger.info("步骤 3: 生成并打印投资组合摘要...")
        if hasattr(self.portfolio, 'print_summary') and callable(getattr(self.portfolio, 'print_summary')):
            self.portfolio.print_summary()
        else:
            app_logger.warning("投资组合对象没有可调用的 print_summary 方法。")

        app_logger.info(f"回测结束。时间: {datetime.now()}")


if __name__ == '__main__':
    from qte_data.csv_data_provider import CSVDataProvider
    from qte_strategy.example_strategies import MovingAverageCrossStrategy
    from qte_portfolio_risk.base_portfolio import BasePortfolio
    from qte_execution.basic_broker import BasicBroker, FixedPercentageCommission, SimpleRandomSlippage
    
    app_logger.info("====== 开始执行 BE_Backtester 主测试 ======")

    # 1. 初始化核心组件
    event_loop_main = EventLoop()
    
    # 2. 配置数据提供者
    # 注意：CSV文件路径是相对于项目根目录的
    csv_directory = "myquant_data" 
    # test_symbols = ["TEST_SYM_A", "TEST_SYM_A"] # 使用之前创建的示例CSV文件
    test_symbols = ["TEST_SYM_A", "TEST_SYM_B"] # 使用之前创建的示例CSV文件

    try:
        data_provider_main = CSVDataProvider(
            event_loop=event_loop_main,
            csv_dir_path=csv_directory,
            symbols=test_symbols
        )
        app_logger.info(f"CSVDataProvider 初始化成功，使用目录: '{csv_directory}' 和品种: {test_symbols}")
        if not data_provider_main.all_bars_sorted:
            app_logger.error("错误：DataProvider 未能加载任何排序后的K线数据。请检查CSV文件和路径。测试无法继续。")
            exit()

    except Exception as e:
        app_logger.error(f"初始化 CSVDataProvider 失败: {e}", exc_info=True)
        exit()

    # 3. 配置策略
    # MovingAverageCrossStrategy 需要 data_provider 来获取历史数据
    strategy_main = MovingAverageCrossStrategy(
        symbols=test_symbols,
        event_loop=event_loop_main,
        short_window=5, # 示例参数
        long_window=10, # 示例参数
        data_provider=data_provider_main # 传递 data_provider
    )
    app_logger.info("MovingAverageCrossStrategy 初始化成功。")

    # 4. 配置投资组合
    # BasePortfolio 也需要 data_provider 来在生成订单时估算价格和数量
    portfolio_main = BasePortfolio(
        initial_capital=100000.0,
        event_loop=event_loop_main,
        data_provider=data_provider_main, # 传递 data_provider
        default_order_size_pct=0.10 # 使用10%的资产进行下单
    )
    app_logger.info("BasePortfolio 初始化成功。")

    # 5. 配置经纪商
    commission_model_main = FixedPercentageCommission(commission_rate=0.001) # 0.1% 佣金
    slippage_model_main = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=0.5) # 0.01价格点滑点, 50%概率
    
    broker_main = BasicBroker(
        event_loop=event_loop_main,
        commission_model=commission_model_main,
        slippage_model=slippage_model_main,
        data_provider=data_provider_main # 传递 data_provider
    )
    app_logger.info("BasicBroker 初始化成功。")

    # 6. 初始化并运行回测器
    app_logger.info("初始化 BE_Backtester...")
    backtester = BE_Backtester(
        event_loop=event_loop_main,
        data_provider=data_provider_main,
        strategy=strategy_main,
        portfolio=portfolio_main,
        broker=broker_main,
        symbols=test_symbols
    )
    app_logger.info("BE_Backtester 初始化成功。准备运行回测...")
    
    backtester.run_backtest()

    app_logger.info("====== BE_Backtester 主测试执行完毕 ======") 