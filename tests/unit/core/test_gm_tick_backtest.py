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
from qte.strategy.example_strategies import MovingAverageCrossStrategy # Or other appropriate strategy
from qte.execution.basic_broker import BasicBroker
from qte.portfolio.base_portfolio import BasePortfolio

# 掘金Token
GM_TOKEN = os.environ.get("GM_TOKEN", "your_gm_token_here")

class TestGmTickBacktest(unittest.TestCase):
    # ... (rest of the file)
    pass

def ensure_dummy_tick_data_exists():
    """
    确保虚拟Tick数据存在，如果不存在则创建
    
    返回:
        str: 数据文件路径
    """
    # 输出目录
    output_dir = os.path.join(project_root, "myquant_data", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试用的交易品种
    symbols = ["SHFE.au", "CFFEX.IF", "DCE.m"]
    
    # 创建SQLite数据库
    db_path = os.path.join(output_dir, "dummy_tick_data.dat")
    
    # 如果文件已存在且不为空，直接返回
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        print(f"虚拟Tick数据文件已存在: {db_path}")
        return db_path
    
    print("创建虚拟Tick数据...")
    
    try:
        # 创建新数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表
        table_name = "tick_data"
        cursor.execute(f'''
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                datetime TIMESTAMP,
                price REAL,
                volume INTEGER,
                bid_price REAL,
                bid_volume INTEGER,
                ask_price REAL,
                ask_volume INTEGER
            )
        ''')
        
        # 为每个交易品种生成数据
        for symbol in symbols:
            # 生成时间范围
            start_time = datetime(2024, 1, 1, 9, 0, 0)
            
            # Tick数据的时间间隔为5秒
            interval = timedelta(seconds=5)
            
            # 生成数据点
            num_data_points = 2000
            
            base_price = 100.0  # 基础价格
            intraday_volatility = 0.01  # 日内波动率
            
            data_records = []
            current_time = start_time
            current_price = base_price
            
            for i in range(num_data_points):
                # 生成价格变动
                price_change = current_price * intraday_volatility * (0.5 - np.random.random())
                current_price += price_change
                
                # 生成买卖价
                bid_price = current_price * (1 - 0.001 * np.random.random())
                ask_price = current_price * (1 + 0.001 * np.random.random())
                
                # 生成成交量和买卖量
                volume = int(100 * np.random.random())
                bid_volume = int(50 * np.random.random())
                ask_volume = int(50 * np.random.random())
                
                data_records.append((
                    symbol,
                    current_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    current_price,
                    volume,
                    bid_price,
                    bid_volume,
                    ask_price,
                    ask_volume
                ))
                
                # 增加时间
                current_time += interval
            
            # 插入数据
            cursor.executemany(
                f"INSERT INTO {table_name} (symbol, datetime, price, volume, bid_price, bid_volume, ask_price, ask_volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                data_records
            )
            
            print(f"为交易品种 {symbol} 生成了 {len(data_records)} 条Tick数据")
        
        # 提交事务并关闭连接
        conn.commit()
        conn.close()
        
        print(f"虚拟Tick数据已保存到: {db_path}")
        return db_path
    
    except Exception as e:
        print(f"创建虚拟Tick数据时出错: {e}")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass
        return None

def get_available_symbols(data_file, table_name="tick_data", limit=3):
    """
    获取数据文件中可用的交易品种
    
    参数:
        data_file (str): 数据文件路径
        table_name (str): 表名
        limit (int): 最多返回的品种数量
        
    返回:
        List[str]: 交易品种列表
    """
    try:
        conn = sqlite3.connect(data_file)
        cursor = conn.cursor()
        
        # 查询所有交易品种
        cursor.execute(f"SELECT DISTINCT symbol FROM {table_name} LIMIT {limit};")
        symbols = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return symbols
    except Exception as e:
        print(f"获取交易品种时出错: {e}")
        return []

def run_tick_data_backtest():
    """
    使用Tick数据进行回测
    """
    print("\n===== 使用掘金量化Tick数据进行回测 =====")
    
    # 确保虚拟数据存在
    data_file = ensure_dummy_tick_data_exists()
    if not data_file:
        print("创建虚拟数据失败，无法进行回测")
        return
    
    # 数据目录
    gm_data_dir = os.path.join(project_root, "myquant_data")
    
    # 获取可用的交易品种
    symbols = get_available_symbols(data_file)
    
    if not symbols:
        print("未找到可用的交易品种，无法进行回测")
        return
    
    print(f"选择以下交易品种进行回测: {symbols}")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 创建数据提供者
    data_provider = GmDataProvider(
        event_loop=event_loop,
        gm_data_dir=gm_data_dir,
        symbols=symbols,
        use_csv_cache=True,
        data_type="tick"  # 使用Tick数据
    )
    
    # 如果没有加载到数据，终止回测
    if not data_provider.data:
        print("未找到Tick数据，无法进行回测")
        return
    
    # 创建策略
    strategy = SimpleTickStrategy(
        event_loop=event_loop,
        symbols=symbols,
        data_provider=data_provider,
        price_threshold=0.1,  # 价格阈值
        position_size=10  # 每次交易的数量
    )
    
    # 创建投资组合
    portfolio = BasePortfolio(
        event_loop=event_loop,
        initial_capital=1000000.0,  # 100万初始资金
        data_provider=data_provider
    )
    
    # 创建经纪商（针对Tick交易调整佣金和滑点）
    commission_model = FixedPercentageCommission(commission_rate=0.0001)  # 0.01%佣金
    slippage_model = SimpleRandomSlippage(slippage_points=0.002, slippage_chance=0.5)  # 0.2点滑点，50%概率
    
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
    
    # 捕获标准输出以便查看详细日志
    output = StringIO()
    with redirect_stdout(output):
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
    
    # 打印详细回测日志的摘要
    log_lines = output.getvalue().split('\n')
    trade_lines = [line for line in log_lines if "交易" in line or "TRADE" in line or "ORDER" in line]
    if trade_lines:
        print("\n回测过程中的交易记录摘要:")
        for i, line in enumerate(trade_lines[:10]):
            print(line)
        if len(trade_lines) > 10:
            print(f"... 及其他 {len(trade_lines) - 10} 条交易记录")
    
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
    
    # 计算交易统计数据
    if hasattr(portfolio, 'trade_history') and portfolio.trade_history:
        trades = portfolio.trade_history
        num_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
        losing_trades = sum(1 for trade in trades if trade.get('profit', 0) < 0)
        win_rate = winning_trades / num_trades if num_trades > 0 else 0
        
        print("\n交易统计:")
        print(f"总交易次数: {num_trades}")
        print(f"盈利交易: {winning_trades}")
        print(f"亏损交易: {losing_trades}")
        print(f"胜率: {win_rate:.2f}")

if __name__ == "__main__":
    run_tick_data_backtest() 