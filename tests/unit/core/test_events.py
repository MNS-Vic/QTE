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

def test_events():
    """测试所有事件类是否能正确实例化"""
    # 基础事件测试
    try:
        # 创建基类事件，需要提供event_type
        base_event = Event(event_type=EventType.MARKET)
        print(f"基类事件创建成功: {base_event}")
        
        # 子类事件测试
        # 测试MarketEvent
        market_event = MarketEvent(
            symbol="AAPL",
            open_price=150.0,
            high_price=152.0,
            low_price=149.0,
            close_price=151.5,
            volume=10000
        )
        print(f"市场事件创建成功: {market_event}")
        
        # 测试SignalEvent
        signal_event = SignalEvent(
            symbol="AAPL",
            signal_type="LONG"
        )
        print(f"信号事件创建成功: {signal_event}")
        
        # 测试OrderEvent
        order_event = OrderEvent(
            symbol="AAPL",
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100
        )
        print(f"订单事件创建成功: {order_event}")
        
        # 测试FillEvent
        fill_event = FillEvent(
            order_id="order123",
            symbol="AAPL",
            direction=OrderDirection.BUY,
            quantity=100,
            fill_price=151.0
        )
        print(f"成交事件创建成功: {fill_event}")
        
        print("所有事件测试通过，修复成功！")
    except Exception as e:
        print(f"测试失败，错误信息: {e}")

if __name__ == "__main__":
    test_events() 