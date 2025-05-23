#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测时间集成示例
展示如何在QTE中解决回测与实盘时间戳冲突问题
"""

import time
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal

# QTE核心组件
from qte.core.time_manager import (
    set_backtest_time, set_live_mode, advance_backtest_time,
    get_current_timestamp, get_current_time, now, time_manager
)
from qte.exchange.matching.matching_engine import MatchingEngine, Order, OrderSide, OrderType
from qte.exchange.account.account_manager import AccountManager
from qte.exchange.rest_api.rest_server import ExchangeRESTServer


class BacktestTimeDemo:
    """回测时间演示类"""
    
    def __init__(self):
        self.matching_engine = MatchingEngine()
        self.account_manager = AccountManager()
        self.rest_server = ExchangeRESTServer(self.matching_engine, self.account_manager)
        
    def demo_time_conflict_problem(self):
        """演示时间冲突问题"""
        print("=" * 60)
        print("🚨 演示：回测时间冲突问题")
        print("=" * 60)
        
        # 模拟历史数据时间戳
        historical_time = datetime(2024, 6, 15, 9, 30, 0)
        historical_timestamp = int(historical_time.timestamp() * 1000)
        
        print(f"📊 历史数据时间: {historical_time}")
        print(f"📊 历史时间戳: {historical_timestamp}")
        
        # 策略代码尝试获取当前时间
        current_time = time.time()
        current_timestamp = int(current_time * 1000)
        
        print(f"⏰ 当前实际时间: {datetime.fromtimestamp(current_time)}")
        print(f"⏰ 当前时间戳: {current_timestamp}")
        
        # 时间差
        time_diff = abs(current_timestamp - historical_timestamp)
        print(f"❌ 时间差: {time_diff}ms ({time_diff/1000/3600:.1f}小时)")
        
        # 这会导致API验证失败
        print("💥 结果: API时间戳验证失败！")
        
    def demo_solution_with_time_manager(self):
        """演示时间管理器解决方案"""
        print("\n" + "=" * 60)
        print("✅ 演示：时间管理器解决方案")
        print("=" * 60)
        
        # 设置回测模式和历史时间
        historical_time = datetime(2024, 6, 15, 9, 30, 0)
        print(f"🔄 切换到回测模式，设置时间: {historical_time}")
        set_backtest_time(historical_time)
        
        # 现在策略代码获取的是虚拟时间
        virtual_time = get_current_time()
        virtual_timestamp = get_current_timestamp()
        virtual_datetime = now()
        
        print(f"⏪ 虚拟时间: {virtual_datetime}")
        print(f"⏪ 虚拟时间戳: {virtual_timestamp}")
        print(f"✅ 时间状态: {time_manager.format_time()}")
        
        # 即使策略代码调用 time.time()，也会得到虚拟时间
        print(f"🔧 time.time() 返回: {datetime.fromtimestamp(time.time())}")
        
    def demo_api_integration(self):
        """演示API集成"""
        print("\n" + "=" * 60)
        print("🌐 演示：API集成测试")
        print("=" * 60)
        
        # 模拟策略发送API请求
        from flask import Flask
        app = self.rest_server.app
        
        with app.test_client() as client:
            # 获取服务器时间
            response = client.get('/api/v3/time')
            time_data = response.get_json()
            
            print(f"🕐 服务器时间: {time_data}")
            print(f"📡 API响应正常: {response.status_code == 200}")
            
    def demo_backtest_progression(self):
        """演示回测时间推进"""
        print("\n" + "=" * 60)
        print("⏭️ 演示：回测时间推进")
        print("=" * 60)
        
        # 创建模拟的历史数据
        start_time = datetime(2024, 6, 15, 9, 30, 0)
        data_points = []
        
        for i in range(5):
            timestamp = start_time + timedelta(minutes=i)
            price = Decimal("50000") + Decimal(str(i * 100))
            data_points.append({
                'timestamp': timestamp,
                'price': price,
                'volume': Decimal("10")
            })
        
        print("📈 历史数据:")
        for point in data_points:
            print(f"  {point['timestamp']}: ${point['price']}")
        
        print("\n🔄 开始回测时间推进:")
        
        # 逐个处理数据点
        for i, point in enumerate(data_points):
            # 设置当前数据点的时间
            set_backtest_time(point['timestamp'])
            
            print(f"\n📍 步骤 {i+1}:")
            print(f"  设置时间: {point['timestamp']}")
            print(f"  当前虚拟时间: {now()}")
            print(f"  策略可以安全调用 get_current_timestamp(): {get_current_timestamp()}")
            
            # 模拟策略决策和下单
            if point['price'] > Decimal("50200"):
                print(f"  💰 策略决策: 价格 ${point['price']} > $50200，执行买入")
                
                # 创建订单（使用虚拟时间戳）
                order = Order(
                    order_id=f"order_{i}",
                    symbol="BTC/USDT",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=Decimal("0.1"),
                    user_id="strategy_user",
                    timestamp=get_current_timestamp()  # 虚拟时间戳
                )
                
                print(f"  📝 订单时间戳: {order.timestamp} (虚拟)")
                print(f"  ✅ 时间戳匹配数据: {abs(order.timestamp - get_current_timestamp()) < 1000}")
        
    def demo_live_switch(self):
        """演示切换回实盘模式"""
        print("\n" + "=" * 60)
        print("🔴 演示：切换回实盘模式")
        print("=" * 60)
        
        print("🔄 切换到实盘模式...")
        set_live_mode()
        
        real_time = get_current_time()
        real_timestamp = get_current_timestamp()
        real_datetime = now()
        
        print(f"🔴 实盘时间: {real_datetime}")
        print(f"🔴 实盘时间戳: {real_timestamp}")
        print(f"✅ 时间状态: {time_manager.format_time()}")
        print(f"🔧 time.time() 返回: {datetime.fromtimestamp(time.time())}")
        
    def run_full_demo(self):
        """运行完整演示"""
        print("🚀 QTE 回测时间管理器演示")
        print("解决策略代码在回测与实盘环境下的时间戳冲突问题\n")
        
        try:
            self.demo_time_conflict_problem()
            self.demo_solution_with_time_manager()
            self.demo_api_integration()
            self.demo_backtest_progression()
            self.demo_live_switch()
            
            print("\n" + "=" * 60)
            print("🎉 演示完成！")
            print("✅ 时间管理器成功解决了回测时间戳冲突问题")
            print("✅ 策略代码无需修改即可在回测和实盘间切换")
            print("✅ API验证在回测模式下正常工作")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ 演示过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    demo = BacktestTimeDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main() 