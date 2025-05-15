import sys
import os
import io
from contextlib import redirect_stdout
import time
from datetime import datetime

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已添加项目路径: {project_root}")

from qte_core.event_loop import EventLoop
from qte_data.csv_data_provider import CSVDataProvider
from qte_strategy.example_strategies import MovingAverageCrossStrategy
from qte_portfolio_risk.base_portfolio import BasePortfolio
from qte_execution.basic_broker import BasicBroker, FixedPercentageCommission, SimpleRandomSlippage
from qte_core.backtester import BE_Backtester

# 首先确保我们有测试数据
from test_backtest_data import generate_test_data

def run_improved_backtest():
    """
    运行改进后的回测，使用新生成的测试数据和优化后的组件。
    """
    # 确保生成测试数据
    test_a_path, test_b_path = generate_test_data()
    
    # 设置回测参数
    symbols = ["TEST_SYM_A", "TEST_SYM_B"]
    data_dir = os.path.join(project_root, "myquant_data")
    initial_capital = 100000.0  # 10万初始资金
    
    print("\n===== 开始优化后的回测测试 =====")
    start_time = time.time()
    
    # 1. 初始化组件
    print("\n1. 初始化组件")
    # 事件循环
    event_loop = EventLoop()
    print("  ✓ 事件循环初始化完成")
    
    # 数据提供者
    data_provider = CSVDataProvider(
        event_loop=event_loop,
        csv_dir_path=data_dir,
        symbols=symbols
    )
    print(f"  ✓ 数据提供者初始化完成，加载了 {len(data_provider.all_bars_sorted)} 条市场数据")
    
    # 策略
    strategy = MovingAverageCrossStrategy(
        symbols=symbols,
        event_loop=event_loop,
        short_window=5,
        long_window=15,
        data_provider=data_provider,
        name="改进MA交叉策略"
    )
    print("  ✓ 策略初始化完成")
    
    # 投资组合
    portfolio = BasePortfolio(
        initial_capital=initial_capital,
        event_loop=event_loop,
        data_provider=data_provider,
        default_order_size_pct=0.05  # 每次交易使用5%的资金
    )
    print("  ✓ 投资组合初始化完成")
    
    # 经纪商
    commission_model = FixedPercentageCommission(commission_rate=0.001)  # 0.1%佣金
    slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=0.5)  # 1%滑点，50%概率
    broker = BasicBroker(
        event_loop=event_loop,
        commission_model=commission_model,
        slippage_model=slippage_model,
        data_provider=data_provider
    )
    print("  ✓ 经纪商初始化完成")
    
    # 2. 初始化回测器
    print("\n2. 初始化回测器")
    backtester = BE_Backtester(
        event_loop=event_loop,
        data_provider=data_provider,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker,
        symbols=symbols
    )
    print("  ✓ 回测器初始化完成")
    
    # 3. 运行回测
    print("\n3. 开始运行回测")
    # 捕获输出，避免太多日志混淆输出
    f = io.StringIO()
    with redirect_stdout(f):
        backtester.run_backtest()
    
    # 4. 显示结果
    end_time = time.time()
    print(f"\n4. 回测完成，耗时: {end_time - start_time:.2f} 秒")
    
    # 计算回测结果
    final_equity = portfolio.current_equity
    profit_loss = final_equity - initial_capital
    profit_loss_pct = (profit_loss / initial_capital) * 100
    
    print("\n===== 回测结果摘要 =====")
    print(f"初始资金: {initial_capital:.2f}")
    print(f"最终资产: {final_equity:.2f}")
    print(f"盈亏: {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
    
    # 交易统计
    print("\n交易统计:")
    order_count = 0
    fill_count = 0
    for event_type, count in backtester.event_loop._handlers.items():
        if event_type.name == "ORDER":
            order_count = len(count)
        elif event_type.name == "FILL":
            fill_count = len(count)
    
    print(f"处理的订单数量: {order_count}")
    print(f"成交数量: {fill_count}")
    
    # 获取持仓信息
    print("\n最终持仓:")
    for symbol, position in portfolio.positions.items():
        if position.quantity != 0:
            print(f"  {symbol}: {position.quantity} 股，成本价: {position.average_cost:.2f}")
    
    if not portfolio.positions:
        print("  无持仓")
    
    print("\n===== 回测测试结束 =====")

if __name__ == "__main__":
    run_improved_backtest() 