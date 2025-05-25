#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy Gateway使用示例

演示如何使用新的QTE Gateway系统
包含工厂模式创建、事件处理、订单交易等功能
"""

import time
import asyncio
from datetime import datetime

from qte.vnpy import check_vnpy_availability
from qte.vnpy.gateways import (
    GatewayFactory, GatewayType, create_qte_gateway,
    get_conversion_stats
)

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.event import EventEngine
    from vnpy.trader.object import OrderRequest, SubscribeRequest
    from vnpy.trader.constant import Direction, OrderType, Exchange
else:
    print("vnpy不可用，使用模拟模式")
    EventEngine = object
    OrderRequest = object
    SubscribeRequest = object
    Direction = object
    OrderType = object
    Exchange = object


class QTEGatewayExample:
    """QTE Gateway使用示例"""
    
    def __init__(self):
        self.event_engine = None
        self.gateway = None
        
    def setup(self):
        """初始化设置"""
        print("=== QTE vnpy Gateway示例 ===")
        print(f"vnpy可用性: {VNPY_AVAILABLE}")
        
        if not VNPY_AVAILABLE:
            print(f"缺失组件: {VNPY_INFO['missing_deps']}")
            print("将使用模拟模式演示")
            return False
        
        # 创建事件引擎
        self.event_engine = EventEngine()
        print("✅ 事件引擎已创建")
        
        return True
    
    def create_gateway_with_factory(self):
        """使用工厂模式创建Gateway"""
        print("\n--- 使用工厂模式创建Gateway ---")
        
        try:
            # 方法1：使用工厂类
            self.gateway = GatewayFactory.create_gateway(
                GatewayType.QTE_BINANCE,
                self.event_engine,
                "QTE_DEMO"
            )
            print("✅ 使用GatewayFactory创建成功")
            
            # 方法2：使用便捷函数
            # gateway2 = create_qte_gateway(self.event_engine, "QTE_DEMO2")
            # print("✅ 使用便捷函数创建成功")
            
            # 显示可用的Gateway类型
            available_types = GatewayFactory.list_available_types()
            print(f"可用Gateway类型: {[t.value for t in available_types]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Gateway创建失败: {e}")
            return False
    
    def connect_gateway(self):
        """连接Gateway"""
        print("\n--- 连接Gateway ---")
        
        # Gateway配置
        gateway_setting = {
            "API密钥": "demo_api_key",
            "私钥": "demo_secret_key",
            "服务器": "QTE_MOCK",  # 连接QTE虚拟交易所
            "重连次数": 3,
            "重连延迟": 2.0,
            "健康检查间隔": 30,
        }
        
        try:
            self.gateway.connect(gateway_setting)
            print("✅ Gateway连接请求已发送")
            
            # 等待连接建立
            print("等待连接建立...")
            time.sleep(3)
            
            # 检查连接状态
            stats = self.gateway.get_gateway_stats()
            print(f"连接状态: {stats['connect_status']}")
            print(f"登录状态: {stats['login_status']}")
            print(f"服务器类型: {stats['server_type']}")
            
            return stats['connect_status']
            
        except Exception as e:
            print(f"❌ Gateway连接失败: {e}")
            return False
    
    def subscribe_market_data(self):
        """订阅市场数据"""
        print("\n--- 订阅市场数据 ---")
        
        try:
            # 创建订阅请求
            subscribe_req = SubscribeRequest(
                symbol="BTCUSDT",
                exchange=Exchange.OTC
            )
            
            # 订阅行情
            self.gateway.subscribe(subscribe_req)
            print("✅ 行情订阅请求已发送")
            
            # 等待数据推送
            print("等待行情数据...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ 行情订阅失败: {e}")
            return False
    
    def send_test_order(self):
        """发送测试订单"""
        print("\n--- 发送测试订单 ---")
        
        try:
            # 创建订单请求
            order_req = OrderRequest(
                symbol="BTCUSDT",
                exchange=Exchange.OTC,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=0.001,
                price=50000.0,
                reference="test_order"
            )
            
            # 发送订单
            orderid = self.gateway.send_order(order_req)
            
            if orderid:
                print(f"✅ 订单发送成功，订单ID: {orderid}")
                
                # 等待订单回报
                time.sleep(2)
                
                return orderid
            else:
                print("❌ 订单发送失败")
                return None
                
        except Exception as e:
            print(f"❌ 发送订单异常: {e}")
            return None
    
    def show_conversion_stats(self):
        """显示转换统计信息"""
        print("\n--- 事件转换统计 ---")
        
        try:
            stats = get_conversion_stats()
            print(f"注册转换器数量: {stats['registered_converters']}")
            print("转换器列表:")
            for converter in stats['converter_list']:
                print(f"  - {converter}")
            
            error_stats = stats['error_stats']
            print(f"错误统计: {error_stats}")
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
    
    def show_gateway_stats(self):
        """显示Gateway统计信息"""
        print("\n--- Gateway统计信息 ---")
        
        try:
            stats = self.gateway.get_gateway_stats()
            
            print(f"Gateway名称: {stats['gateway_name']}")
            print(f"连接状态: {stats['connect_status']}")
            print(f"登录状态: {stats['login_status']}")
            print(f"服务器类型: {stats['server_type']}")
            print(f"订阅品种数: {stats['subscribed_symbols']}")
            print(f"缓存订单数: {stats['cached_orders']}")
            print(f"缓存合约数: {stats['cached_contracts']}")
            
            if 'connection_stats' in stats:
                conn_stats = stats['connection_stats']
                print(f"连接次数: {conn_stats['total_connections']}")
                print(f"断开次数: {conn_stats['total_disconnections']}")
                print(f"重连次数: {conn_stats['total_reconnections']}")
                print(f"运行时间: {conn_stats.get('uptime_seconds', 0):.1f}秒")
            
        except Exception as e:
            print(f"❌ 获取Gateway统计失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        print("\n--- 清理资源 ---")
        
        try:
            if self.gateway:
                self.gateway.close()
                print("✅ Gateway已关闭")
            
            if self.event_engine:
                self.event_engine.stop()
                print("✅ 事件引擎已停止")
            
            # 清理工厂中的实例
            GatewayFactory.clear_all()
            print("✅ 工厂实例已清理")
            
        except Exception as e:
            print(f"❌ 清理资源失败: {e}")
    
    def run_demo(self):
        """运行完整演示"""
        print("开始QTE Gateway演示...")
        
        # 1. 初始化
        if not self.setup():
            print("初始化失败，退出演示")
            return
        
        # 2. 创建Gateway
        if not self.create_gateway_with_factory():
            print("Gateway创建失败，退出演示")
            return
        
        # 3. 连接Gateway
        if not self.connect_gateway():
            print("Gateway连接失败，继续其他演示")
        
        # 4. 订阅行情
        self.subscribe_market_data()
        
        # 5. 发送测试订单
        self.send_test_order()
        
        # 6. 显示统计信息
        self.show_conversion_stats()
        self.show_gateway_stats()
        
        # 7. 清理资源
        self.cleanup()
        
        print("\n=== 演示完成 ===")


def main():
    """主函数"""
    demo = QTEGatewayExample()
    demo.run_demo()


if __name__ == "__main__":
    main() 