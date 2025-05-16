import sys
import os

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已添加项目路径: {project_root}")

from qte.core.events import EventType, Event, MarketEvent, SignalEvent, OrderEvent, FillEvent
from qte.core.events import OrderType, OrderDirection
from datetime import datetime

# 创建一个日志文件
log_file = os.path.join(project_root, "event_test_results.log")
with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"事件测试开始: {datetime.now()}\n")
    f.write("="*50 + "\n")
    
    try:
        # 1. 测试基础事件
        base_event = Event(event_type=EventType.MARKET)
        f.write("1. 基础事件测试通过\n")
        
        # 2. 测试市场事件
        market_event = MarketEvent(
            symbol="AAPL",
            open_price=150.0,
            high_price=152.0,
            low_price=149.0,
            close_price=151.5,
            volume=10000
        )
        f.write("2. 市场事件测试通过\n")
        
        # 3. 测试信号事件
        signal_event = SignalEvent(
            symbol="AAPL",
            signal_type="LONG",
            strength=0.8,
            target_quantity=100
        )
        f.write("3. 信号事件测试通过\n")
        
        # 4. 测试订单事件
        # 市价单
        market_order = OrderEvent(
            symbol="AAPL",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        f.write("4.1. 市价单测试通过\n")
        
        # 限价单
        limit_order = OrderEvent(
            symbol="GOOGL",
            order_type=OrderType.LIMIT,
            direction=OrderDirection.SELL,
            quantity=50,
            limit_price=2500.0
        )
        f.write("4.2. 限价单测试通过\n")
        
        # 5. 测试成交事件
        fill_event = FillEvent(
            order_id="order123",
            symbol="AAPL",
            direction=OrderDirection.BUY,
            quantity=100,
            fill_price=151.0,
            commission=1.5,
            slippage=0.25
        )
        f.write("5. 成交事件测试通过\n")
        
        # 所有测试通过
        f.write("\n所有事件测试通过，修复成功！\n")
        
    except Exception as e:
        f.write(f"\n测试失败: {e}\n")
    
    f.write("\n" + "="*50 + "\n")
    f.write(f"测试结束: {datetime.now()}")

print(f"测试完成，结果已写入文件: {log_file}")

# 输出测试结果
print("\n测试结果:")
with open(log_file, "r", encoding="utf-8") as f:
    print(f.read()) 