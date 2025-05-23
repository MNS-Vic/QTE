#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy集成示例

展示如何使用QTE的vnpy集成功能：
1. 连接QTE模拟交易所
2. 订阅实时行情数据
3. 发送交易订单
4. 处理回报信息

运行前请确保：
1. QTE模拟交易所服务已启动
2. 已安装vnpy包
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from qte.vnpy.data_source import VnpyDataSource
    from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
    VNPY_AVAILABLE = True
except ImportError as e:
    print(f"vnpy集成不可用：{e}")
    print("请先安装vnpy：pip install vnpy")
    VNPY_AVAILABLE = False


def demo_data_source():
    """演示vnpy数据源使用"""
    print("=== QTE vnpy数据源示例 ===")
    
    if not VNPY_AVAILABLE:
        print("vnpy不可用，跳过演示")
        return
    
    # 配置网关设置
    gateway_settings = {
        "QTE_BINANCE_SPOT": {
            "API密钥": "test_api_key",
            "私钥": "test_secret_key", 
            "服务器": "QTE_MOCK",  # 使用QTE模拟服务器
            "代理地址": "",
            "代理端口": 0,
        }
    }
    
    # 创建vnpy数据源
    data_source = VnpyDataSource(
        gateway_names=["QTE_BINANCE_SPOT"],
        gateway_settings=gateway_settings
    )
    
    # 定义数据回调函数
    def on_tick_data(tick):
        print(f"收到Tick数据: {tick.symbol} 价格:{tick.last_price} 成交量:{tick.volume}")
    
    try:
        # 连接数据源
        print("正在连接vnpy数据源...")
        if data_source.connect():
            print("数据源连接成功!")
            
            # 等待合约信息加载
            time.sleep(2)
            
            # 获取合约信息
            contracts = data_source.get_contracts("BINANCE")
            print(f"获取到 {len(contracts)} 个合约")
            
            # 订阅实时数据
            symbols = ["BTCUSDT", "ETHUSDT"]
            print(f"订阅实时数据: {symbols}")
            data_source.subscribe_tick_data(
                symbols=symbols,
                exchange="BINANCE", 
                callback=on_tick_data
            )
            
            # 运行一段时间接收数据
            print("正在接收实时数据，运行30秒...")
            time.sleep(30)
            
        else:
            print("数据源连接失败")
            
    except Exception as e:
        print(f"演示过程中出错：{e}")
    
    finally:
        # 断开连接
        data_source.disconnect()
        print("数据源已断开")


def demo_gateway_connection():
    """演示网关连接测试"""
    print("\n=== QTE vnpy网关连接测试 ===")
    
    if not VNPY_AVAILABLE:
        print("vnpy不可用，跳过演示")
        return
    
    try:
        from vnpy.event import EventEngine
        from vnpy.trader.engine import MainEngine
        
        # 创建事件引擎和主引擎
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        
        # 启动事件引擎
        event_engine.start()
        
        # 添加QTE Binance网关
        main_engine.add_gateway(QTEBinanceSpotGateway)
        
        # 网关配置
        setting = {
            "API密钥": "test_api_key",
            "私钥": "test_secret_key",
            "服务器": "QTE_MOCK",  # 使用QTE模拟服务器
            "代理地址": "",
            "代理端口": 0,
        }
        
        # 连接网关
        print("正在连接QTE Binance网关...")
        main_engine.connect(setting, "QTE_BINANCE_SPOT")
        
        # 等待连接完成
        time.sleep(5)
        
        # 检查连接状态
        gateways = main_engine.get_all_gateways()
        print(f"已连接网关数量: {len(gateways)}")
        
        # 获取合约信息
        contracts = main_engine.get_all_contracts()
        print(f"获取到合约数量: {len(contracts)}")
        
        # 关闭连接
        main_engine.close()
        event_engine.stop()
        print("网关连接测试完成")
        
    except Exception as e:
        print(f"网关连接测试失败：{e}")


def demo_mock_trading():
    """演示模拟交易"""
    print("\n=== QTE模拟交易示例 ===")
    
    print("注意：此示例需要QTE模拟交易所服务运行在 localhost:5000")
    print("请先启动QTE模拟交易所：python start_exchange.py")
    
    # 这里可以添加具体的交易示例
    # 包括下单、撤单、查询等操作
    
    print("模拟交易示例完成")


def main():
    """主函数"""
    print("🚀 QTE vnpy集成演示")
    print("=" * 50)
    
    # 检查vnpy可用性
    if not VNPY_AVAILABLE:
        print("❌ vnpy未安装或不可用")
        print("请运行: pip install vnpy")
        return
    
    print("✅ vnpy可用")
    
    # 运行演示
    try:
        # 1. 数据源演示
        demo_data_source()
        
        # 2. 网关连接测试
        demo_gateway_connection()
        
        # 3. 模拟交易演示
        demo_mock_trading()
        
    except KeyboardInterrupt:
        print("\n用户中断演示")
    except Exception as e:
        print(f"演示过程中出现错误：{e}")
    
    print("\n🎉 vnpy集成演示完成!")


if __name__ == "__main__":
    main() 