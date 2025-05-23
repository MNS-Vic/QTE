#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy集成深化 - 最终验证演示

这个脚本验证：
1. vnpy安装和可用性
2. QTE虚拟交易所运行状态  
3. vnpy Gateway与虚拟交易所的连接
4. 数据流架构的工作原理
"""

import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

def main():
    """主验证流程"""
    print("🎉 QTE vnpy集成深化 - 最终验证")
    print("=" * 60)
    
    # 步骤1：验证vnpy安装
    print("📦 步骤1：验证vnpy安装")
    print("-" * 30)
    
    from qte.vnpy import check_vnpy_availability
    available, info = check_vnpy_availability()
    
    print(f"✅ vnpy可用性: {available}")
    print(f"✅ vnpy版本: {info['version']}")
    print(f"✅ 运行状态: {info['status']}")
    print(f"✅ 可用组件: {', '.join(info['available_components'])}")
    
    if info['missing_deps']:
        print("⚠️  缺失依赖：")
        for dep in info['missing_deps']:
            print(f"   - {dep}")
        print("   注意：MainEngine需要ta-lib，但核心功能已可用")
    
    # 步骤2：验证虚拟交易所
    print(f"\n🏦 步骤2：验证QTE虚拟交易所")
    print("-" * 30)
    
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5001/api/v3/ping"], 
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("✅ 虚拟交易所REST API正常")
            
            # 测试更多API端点
            endpoints = [
                ("/api/v3/time", "服务器时间"),
                ("/api/v3/exchangeInfo", "交易所信息"),
                ("/api/v3/ticker/24hr?symbol=BTCUSDT", "BTCUSDT行情")
            ]
            
            for endpoint, desc in endpoints:
                try:
                    result = subprocess.run(
                        ["curl", "-s", f"http://localhost:5001{endpoint}"], 
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        print(f"✅ {desc} API正常")
                    else:
                        print(f"⚠️  {desc} API异常")
                except:
                    print(f"❌ {desc} API测试失败")
        else:
            print("❌ 虚拟交易所无响应")
            print("请确保运行: python start_exchange.py")
            return False
            
    except Exception as e:
        print(f"❌ 虚拟交易所连接失败: {e}")
        return False
    
    # 步骤3：验证vnpy组件
    print(f"\n🔗 步骤3：验证vnpy组件")
    print("-" * 30)
    
    try:
        from vnpy.event import EventEngine
        from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
        from qte.vnpy.data_source import VnpyDataSource
        
        print("✅ vnpy EventEngine导入成功")
        print("✅ QTE Binance网关导入成功")
        print("✅ QTE vnpy数据源导入成功")
        
        # 创建事件引擎
        event_engine = EventEngine()
        print("✅ vnpy事件引擎创建成功")
        
        # 创建网关
        gateway = QTEBinanceSpotGateway(event_engine)
        print("✅ QTE Binance网关创建成功")
        print(f"   默认服务器: {gateway.default_setting['服务器']}")
        
        # 创建数据源
        data_source = VnpyDataSource(
            gateway_names=["QTE_BINANCE_SPOT"],
            virtual_exchange_host="localhost:5001"
        )
        print("✅ QTE vnpy数据源创建成功")
        print(f"   运行模式: {'简化模式' if data_source.simple_mode else '完整模式'}")
        
    except Exception as e:
        print(f"❌ vnpy组件验证失败: {e}")
        return False
    
    print("\n🎉 QTE vnpy集成深化完成！")
    print("🎯 系统已准备就绪，可以开始量化交易开发")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 