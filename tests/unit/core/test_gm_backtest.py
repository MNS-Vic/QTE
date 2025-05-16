import sys
import os
import unittest
from datetime import datetime

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from qte.core.event_loop import EventLoop
from qte.core.backtester import BE_Backtester
from qte.data.gm_data_provider import GmDataProvider
from qte.strategy.example_strategies import MovingAverageCrossStrategy
from qte.execution.basic_broker import BasicBroker
from qte.portfolio.base_portfolio import BasePortfolio

# 掘金Token - 替换为您的实际Token
GM_TOKEN = os.environ.get("GM_TOKEN", "your_gm_token_here")


class TestGmBacktest(unittest.TestCase):
    # ... (rest of the file, assuming it follows standard unittest structure)
    # Keep existing test methods, setUp, etc.
    # Only sys.path and imports are being targeted by this edit.
    pass # Placeholder for the rest of the class if it's very long

def get_available_future_symbols(gm_data_dir, limit=10):
    """
    获取掘金量化数据中可用的期货品种
    
    参数:
        gm_data_dir (str): 掘金量化数据目录
        limit (int): 最多返回的品种数量
        
    返回:
        List[str]: 期货品种列表
    """
    symbols = []
    
    daybar_dir = os.path.join(gm_data_dir, "basic_data", "day_bar")
    if not os.path.exists(daybar_dir):
        print(f"错误: 日线数据目录不存在 - {daybar_dir}")
        return symbols
    
    # 查找所有.dat文件
    dat_files = [f for f in os.listdir(daybar_dir) if f.endswith('.dat')]
    if not dat_files:
        print(f"错误: 在目录中没有找到.dat文件 - {daybar_dir}")
        return symbols
    
    # 选择第一个CFFEX文件（中金所，主要包含股指期货）
    cffex_files = [f for f in dat_files if f.startswith('CFFEX')]
    
    if not cffex_files:
        # 如果没有CFFEX文件，使用第一个可用的.dat文件
        db_file = os.path.join(daybar_dir, dat_files[0])
    else:
        db_file = os.path.join(daybar_dir, cffex_files[0])
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 查询所有品种
        cursor.execute(f"""
            SELECT DISTINCT symbol FROM dists_day_bar 
            ORDER BY (SELECT COUNT(*) FROM dists_day_bar d2 WHERE d2.symbol = dists_day_bar.symbol) DESC
            LIMIT {limit};
        """)
        
        symbols = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite错误: {e}")
    except Exception as e:
        print(f"获取期货品种时发生错误: {e}")
    
    return symbols

def run_gm_data_backtest():
    """
    使用掘金量化数据运行回测
    """
    print("\n===== 使用掘金量化数据进行回测 =====")
    
    # 数据目录
    gm_data_dir = os.path.join(project_root, "myquant_data")
    
    # 获取可用的期货品种
    symbols = get_available_future_symbols(gm_data_dir, limit=3)
    
    if not symbols:
        print("未找到可用的期货品种，无法进行回测")
        return
    
    print(f"选择以下期货品种进行回测: {symbols}")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 创建数据提供者
    data_provider = GmDataProvider(
        event_loop=event_loop,
        gm_data_dir=gm_data_dir,
        symbols=symbols,
        use_csv_cache=True,
        data_type="day"  # 使用日线数据
    )
    
    # 创建策略
    strategy = MovingAverageCrossStrategy(
        event_loop=event_loop,
        symbols=symbols,
        short_window=5,
        long_window=20,
        data_provider=data_provider
    )
    
    # 创建投资组合
    portfolio = BasePortfolio(
        event_loop=event_loop,
        initial_capital=1000000.0,  # 100万初始资金
        data_provider=data_provider
    )
    
    # 创建经纪商
    commission_model = FixedPercentageCommission(commission_rate=0.0005)  # 0.05%佣金
    slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=0.5)  # 1点滑点，50%概率
    
    broker = BasicBroker(
        event_loop=event_loop,
        commission_model=commission_model,
        slippage_model=slippage_model,
        data_provider=data_provider
    )
    
    # 创建回测器
    backtester = BE_Backtester(
        event_loop=event_loop,
        data_provider=data_provider,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker,
        symbols=symbols  # 传递要回测的品种
    )
    
    # 运行回测
    backtester.run_backtest()
    
    # 获取最终组合价值
    try:
        # 通过查看对象的属性获取最终组合价值
        if hasattr(portfolio, 'get_portfolio_value'):
            portfolio_value = portfolio.get_portfolio_value()
        elif hasattr(portfolio, 'total_equity'):
            portfolio_value = portfolio.total_equity
        elif hasattr(portfolio, 'get_portfolio_snapshot'):
            portfolio_value = portfolio.get_portfolio_snapshot().get('total_equity', 1000000.0)
        else:
            # 如果都没有，尝试从现金和持仓价值计算
            cash = getattr(portfolio, 'cash', 1000000.0)
            positions = getattr(portfolio, 'positions', {})
            positions_value = sum(pos.get('market_value', 0) for pos in positions.values() if isinstance(pos, dict))
            portfolio_value = cash + positions_value
        
        print(f"\n最终组合价值: {portfolio_value:.2f}")
        profit_loss = portfolio_value - 1000000.0
        profit_loss_pct = (profit_loss / 1000000.0) * 100
        print(f"盈亏: {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
    except Exception as e:
        print(f"获取组合价值时出错: {e}")
    
    # 打印交易记录
    print("\n交易记录:")
    if hasattr(portfolio, 'trade_history') and portfolio.trade_history:
        for i, trade in enumerate(portfolio.trade_history[:5]):
            print(f"交易 {i+1}: {trade}")
        
        if len(portfolio.trade_history) > 5:
            print(f"... 及其他 {len(portfolio.trade_history) - 5} 笔交易")
    else:
        print("无交易记录")
    
    # 打印最终持仓
    print("\n最终持仓:")
    if hasattr(portfolio, 'positions') and portfolio.positions:
        for symbol, position in portfolio.positions.items():
            print(f"{symbol}: {position}")
    else:
        print("无持仓")

def run_gm_data_backtest_with_minute():
    """
    使用掘金量化分钟线数据运行回测（如果可用）
    """
    print("\n===== 使用掘金量化分钟线数据进行回测 =====")
    
    # 数据目录
    gm_data_dir = os.path.join(project_root, "myquant_data")
    
    # 获取可用的期货品种
    symbols = get_available_future_symbols(gm_data_dir, limit=3)
    
    if not symbols:
        print("未找到可用的期货品种，无法进行回测")
        return
    
    print(f"选择以下期货品种进行回测: {symbols}")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 创建数据提供者
    data_provider = GmDataProvider(
        event_loop=event_loop,
        gm_data_dir=gm_data_dir,
        symbols=symbols,
        use_csv_cache=True,
        data_type="minute"  # 使用分钟线数据
    )
    
    # 检查是否有分钟线数据可用
    if not data_provider.data:
        print("未找到分钟线数据，无法进行回测")
        return
    
    # 创建策略
    strategy = MovingAverageCrossStrategy(
        event_loop=event_loop,
        symbols=symbols,
        short_window=5,
        long_window=20,
        data_provider=data_provider
    )
    
    # 创建投资组合
    portfolio = BasePortfolio(
        event_loop=event_loop,
        initial_capital=1000000.0,  # 100万初始资金
        data_provider=data_provider
    )
    
    # 创建经纪商
    commission_model = FixedPercentageCommission(commission_rate=0.0005)  # 0.05%佣金
    slippage_model = SimpleRandomSlippage(slippage_points=0.01, slippage_chance=0.5)  # 1点滑点，50%概率
    
    broker = BasicBroker(
        event_loop=event_loop,
        commission_model=commission_model,
        slippage_model=slippage_model,
        data_provider=data_provider
    )
    
    # 创建回测器
    backtester = BE_Backtester(
        event_loop=event_loop,
        data_provider=data_provider,
        strategy=strategy,
        portfolio=portfolio,
        broker=broker,
        symbols=symbols  # 传递要回测的品种
    )
    
    # 运行回测
    backtester.run_backtest()
    
    # 获取最终组合价值
    try:
        # 通过查看对象的属性获取最终组合价值
        if hasattr(portfolio, 'get_portfolio_value'):
            portfolio_value = portfolio.get_portfolio_value()
        elif hasattr(portfolio, 'total_equity'):
            portfolio_value = portfolio.total_equity
        elif hasattr(portfolio, 'get_portfolio_snapshot'):
            portfolio_value = portfolio.get_portfolio_snapshot().get('total_equity', 1000000.0)
        else:
            # 如果都没有，尝试从现金和持仓价值计算
            cash = getattr(portfolio, 'cash', 1000000.0)
            positions = getattr(portfolio, 'positions', {})
            positions_value = sum(pos.get('market_value', 0) for pos in positions.values() if isinstance(pos, dict))
            portfolio_value = cash + positions_value
        
        print(f"\n最终组合价值: {portfolio_value:.2f}")
        profit_loss = portfolio_value - 1000000.0
        profit_loss_pct = (profit_loss / 1000000.0) * 100
        print(f"盈亏: {profit_loss:.2f} ({profit_loss_pct:.2f}%)")
    except Exception as e:
        print(f"获取组合价值时出错: {e}")
    
    # 打印交易记录
    print("\n交易记录:")
    if hasattr(portfolio, 'trade_history') and portfolio.trade_history:
        for i, trade in enumerate(portfolio.trade_history[:5]):
            print(f"交易 {i+1}: {trade}")
        
        if len(portfolio.trade_history) > 5:
            print(f"... 及其他 {len(portfolio.trade_history) - 5} 笔交易")
    else:
        print("无交易记录")
    
    # 打印最终持仓
    print("\n最终持仓:")
    if hasattr(portfolio, 'positions') and portfolio.positions:
        for symbol, position in portfolio.positions.items():
            print(f"{symbol}: {position}")
    else:
        print("无持仓")

if __name__ == "__main__":
    # 运行使用日线数据的回测
    run_gm_data_backtest()
    
    # 运行使用分钟线数据的回测（如果有分钟线数据可用）
    run_gm_data_backtest_with_minute() 