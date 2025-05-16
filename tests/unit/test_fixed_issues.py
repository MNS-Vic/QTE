import sys
import os
import io
from contextlib import redirect_stdout

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.abspath(os.path.join(current_dir, "..", "..")) # QTE project root from tests/unit
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已添加项目路径: {project_root}")

from datetime import datetime
import pandas as pd
from qte.core.events import EventType, Event, MarketEvent, SignalEvent, OrderEvent, FillEvent
from qte.core.events import OrderType, OrderDirection
from qte.core.event_loop import EventLoop
from qte.data.csv_data_provider import CSVDataProvider
from qte.strategy.example_strategies import MovingAverageCrossStrategy

def capture_output(func):
    """用于捕获函数执行期间的标准输出的装饰器"""
    def wrapper(*args, **kwargs):
        f = io.StringIO()
        with redirect_stdout(f):
            result = func(*args, **kwargs)
        output = f.getvalue()
        return result, output
    return wrapper

def test_fixed_issues():
    """
    测试所有修复的问题
    
    1. dataclass继承问题（non-default argument follows default argument）
    2. CSVDataProvider与DataProvider接口不匹配
    3. MovingAverageCrossStrategy构造函数缺少data_provider参数
    4. EventLoop类中deque没有empty方法的问题
    """
    print("\n===== 测试修复的问题 =====")
    
    # 1. 测试事件类
    print("\n1. 测试事件类 (修复 dataclass 继承问题):")
    try:
        # 创建基类事件
        base_event = Event(event_type=EventType.MARKET)
        print("  ✓ Event 创建成功")
        
        # 创建MarketEvent
        market_event = MarketEvent(
            symbol="AAPL",
            open_price=150.0,
            high_price=152.0,
            low_price=149.0,
            close_price=151.5,
            volume=10000
        )
        print("  ✓ MarketEvent 创建成功")
        
        # 创建其他事件类
        signal_event = SignalEvent(symbol="AAPL", signal_type="LONG")
        order_event = OrderEvent(
            symbol="AAPL", 
            order_type=OrderType.MARKET, 
            direction=OrderDirection.BUY, 
            quantity=100
        )
        fill_event = FillEvent(
            order_id="order123",
            symbol="AAPL",
            direction=OrderDirection.BUY,
            quantity=100,
            fill_price=151.0
        )
        print("  ✓ 所有事件类创建成功")
    except Exception as e:
        print(f"  ✗ 事件类创建失败: {e}")
        return
    
    # 2. 测试CSVDataProvider与接口一致性
    print("\n2. 测试CSVDataProvider (修复接口不匹配):")
    try:
        # 创建测试目录和数据
        test_data_dir = os.path.join(project_root, "test_data")
        os.makedirs(test_data_dir, exist_ok=True)
        
        # 创建测试数据
        sym_data = {
            'timestamp': pd.date_range(start='2023-01-01', periods=3, freq='D'),
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [102, 103, 104],
            'volume': [1000, 1100, 1200]
        }
        sym_df = pd.DataFrame(sym_data)
        sym_file = os.path.join(test_data_dir, "TEST.csv")
        sym_df.to_csv(sym_file, index=False)
        
        # 创建事件循环
        event_loop = EventLoop()
        
        # 使用装饰器捕获输出
        @capture_output
        def create_and_test_data_provider():
            # 创建数据提供者
            data_provider = CSVDataProvider(
                event_loop=event_loop,
                csv_dir_path=test_data_dir,
                symbols=["TEST"]
            )
            
            # 测试stream_market_data方法
            for _ in data_provider.stream_market_data(symbols=["TEST"]):
                pass  # 生成器会自动将事件放入队列
            
            # 测试get_latest_bar方法
            latest_bar = data_provider.get_latest_bar("TEST")
            
            # 测试get_latest_bars方法
            latest_bars = data_provider.get_latest_bars("TEST", n=2)
            
            # 测试get_historical_bars方法
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 1, 3)
            historical_bars_gen = data_provider.get_historical_bars("TEST", start_date, end_date)
            if historical_bars_gen:
                historical_bars = list(historical_bars_gen)
            
            return data_provider

        # 执行函数并捕获输出
        data_provider, provider_output = create_and_test_data_provider()
        
        print("  ✓ CSVDataProvider 创建成功")
        print("  ✓ stream_market_data 方法调用成功")
        if data_provider.get_latest_bar("TEST"):
            print("  ✓ get_latest_bar 方法调用成功")
        if data_provider.get_latest_bars("TEST", n=2):
            print("  ✓ get_latest_bars 方法调用成功")
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 3)
        historical_bars_gen = data_provider.get_historical_bars("TEST", start_date, end_date)
        if historical_bars_gen:
            print("  ✓ get_historical_bars 方法调用成功")
    except Exception as e:
        print(f"  ✗ CSVDataProvider 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 测试MovingAverageCrossStrategy构造函数
    print("\n3. 测试MovingAverageCrossStrategy (修复构造函数):")
    try:
        # 使用装饰器捕获输出
        @capture_output
        def create_and_test_strategy():
            # 创建策略
            strategy = MovingAverageCrossStrategy(
                symbols=["TEST"],
                event_loop=event_loop,
                short_window=3,
                long_window=5,
                data_provider=data_provider  # 这个参数原来缺失
            )
            
            # 测试on_market_event方法
            market_event = MarketEvent(
                symbol="TEST",
                timestamp=datetime.now(),
                open_price=100,
                high_price=105,
                low_price=95,
                close_price=102,
                volume=1000
            )
            strategy.on_market_event(market_event)
            
            return strategy, market_event
        
        # 执行函数并捕获输出
        result, strategy_output = create_and_test_strategy()
        strategy, market_event = result
        
        print("  ✓ MovingAverageCrossStrategy 创建成功")
        print("  ✓ on_market_event 方法调用成功")
    except Exception as e:
        print(f"  ✗ MovingAverageCrossStrategy 测试失败: {e}")
        return
    
    # 4. 测试EventLoop中的deque问题
    print("\n4. 测试EventLoop (修复deque没有empty方法的问题):")
    try:
        # 创建事件循环
        event_loop = EventLoop()
        
        # 添加事件
        event_loop.add_event(market_event)
        print("  ✓ 事件添加成功")
        
        # 获取事件
        event = event_loop.get_event(block=False)
        if event:
            print("  ✓ 事件获取成功")
        
        # 检查队列是否为空
        if not event_loop.event_queue:
            print("  ✓ 队列为空检查成功")
    except Exception as e:
        print(f"  ✗ EventLoop 测试失败: {e}")
        return
    
    print("\n✅ 所有修复都已成功验证!")

if __name__ == "__main__":
    test_fixed_issues() 