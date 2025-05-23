#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy虚拟交易所集成示例

展示正确的数据流架构：
外部数据源 → QTE虚拟交易所 → vnpy Gateway → 策略

注意：
1. 数据获取由QTE虚拟交易所负责（从Binance API、CSV等）
2. vnpy Gateway只负责从虚拟交易所读取数据
3. 虚拟交易所运行在 localhost:5001
"""

import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from qte.vnpy.data_source import VnpyDataSource
    from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
    VNPY_AVAILABLE = True
except ImportError as e:
    print(f"vnpy集成不可用：{e}")
    VNPY_AVAILABLE = False


def check_virtual_exchange_status():
    """检查QTE虚拟交易所状态"""
    print("=== 检查QTE虚拟交易所状态 ===")
    
    try:
        # 检查REST API
        response = requests.get("http://localhost:5001/api/v3/ping", timeout=5)
        if response.status_code == 200:
            print("✅ QTE虚拟交易所REST API正常运行")
            return True
        else:
            print(f"❌ QTE虚拟交易所REST API异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接QTE虚拟交易所: {e}")
        print("请确保已运行: python start_exchange.py")
        return False


def demo_virtual_exchange_data_flow():
    """演示从虚拟交易所获取数据的完整流程"""
    print("\n=== QTE虚拟交易所数据流演示 ===")
    
    if not VNPY_AVAILABLE:
        print("❌ vnpy不可用，跳过演示")
        return
        
    if not check_virtual_exchange_status():
        print("❌ 虚拟交易所不可用，无法演示")
        return
    
    # Step 1: 直接从虚拟交易所获取数据（验证数据可用性）
    print("\n📊 Step 1: 直接从虚拟交易所获取数据")
    try:
        # 获取市场数据
        ticker_response = requests.get("http://localhost:5001/api/v3/ticker/24hr?symbol=BTCUSDT")
        if ticker_response.status_code == 200:
            ticker_data = ticker_response.json()
            print(f"✅ BTCUSDT 24h数据: 价格={ticker_data.get('lastPrice', 'N/A')}, 成交量={ticker_data.get('volume', 'N/A')}")
        
        # 获取订单簿数据
        depth_response = requests.get("http://localhost:5001/api/v3/depth?symbol=BTCUSDT&limit=5")
        if depth_response.status_code == 200:
            depth_data = depth_response.json()
            bids = depth_data.get('bids', [])
            asks = depth_data.get('asks', [])
            if bids and asks:
                print(f"✅ 订单簿: 买一={bids[0][0]}, 卖一={asks[0][0]}")
        
    except Exception as e:
        print(f"❌ 直接获取数据失败: {e}")
        return
    
    # Step 2: 通过vnpy Gateway从虚拟交易所获取数据
    print("\n🔗 Step 2: 通过vnpy Gateway从虚拟交易所获取数据")
    
    # 配置vnpy数据源连接到虚拟交易所
    gateway_settings = {
        "QTE_BINANCE_SPOT": {
            "API密钥": "qte_test_key",
            "私钥": "qte_test_secret", 
            "服务器": "QTE_MOCK",  # 明确指定连接虚拟交易所
            "代理地址": "",
            "代理端口": 0,
        }
    }
    
    # 创建vnpy数据源
    data_source = VnpyDataSource(
        gateway_names=["QTE_BINANCE_SPOT"],
        gateway_settings=gateway_settings,
        virtual_exchange_host="localhost:5001"
    )
    
    # 定义数据回调函数
    received_data = {"tick_count": 0, "contract_count": 0}
    
    def on_tick_data(tick):
        received_data["tick_count"] += 1
        print(f"🔄 收到Tick数据 #{received_data['tick_count']}: {tick.symbol} 价格:{tick.last_price}")
    
    def on_contract_data(contract):
        received_data["contract_count"] += 1
        print(f"📋 收到合约信息 #{received_data['contract_count']}: {contract.symbol}")
    
    try:
        # 连接vnpy数据源到虚拟交易所
        print("🔌 正在通过vnpy连接到QTE虚拟交易所...")
        if data_source.connect():
            print("✅ vnpy数据源已连接到QTE虚拟交易所!")
            
            # 等待合约信息加载
            print("⏳ 等待合约信息加载...")
            time.sleep(3)
            
            # 获取合约信息
            contracts = data_source.get_contracts("BINANCE")
            print(f"✅ 通过vnpy获取到 {len(contracts)} 个合约")
            
            # 显示前几个合约
            if contracts:
                for i, (symbol, contract) in enumerate(list(contracts.items())[:5]):
                    print(f"   {i+1}. {symbol}: 最小价格变动={contract.pricetick}, 最小下单量={contract.min_volume}")
            
            # 订阅实时数据
            symbols = ["BTCUSDT", "ETHUSDT"]
            print(f"\n📡 订阅实时数据: {symbols}")
            data_source.subscribe_tick_data(
                symbols=symbols,
                exchange="BINANCE", 
                callback=on_tick_data
            )
            
            # 运行一段时间接收数据
            print("🔄 正在接收实时数据，运行20秒...")
            for i in range(20):
                time.sleep(1)
                if i % 5 == 0:
                    print(f"   运行中... {i+1}/20秒，已收到 {received_data['tick_count']} 个tick数据")
            
            # 显示数据接收统计
            print(f"\n📊 数据接收统计:")
            print(f"   Tick数据: {received_data['tick_count']} 个")
            print(f"   合约信息: {len(contracts)} 个")
            
        else:
            print("❌ vnpy数据源连接失败")
            
    except Exception as e:
        print(f"❌ vnpy数据流演示出错：{e}")
    
    finally:
        # 断开连接
        data_source.disconnect()
        print("🔌 vnpy数据源已断开")


def demo_data_architecture_explanation():
    """解释数据架构"""
    print("\n" + "="*60)
    print("📚 QTE-vnpy数据架构说明")
    print("="*60)
    
    print("""
🏗️ 正确的数据流架构:

1️⃣ 外部数据源 (多种来源)
   ├── 真实Binance API (实时数据)
   ├── 预下载的历史数据 (CSV文件)
   ├── 其他交易所API
   └── 模拟数据生成器
           ↓
2️⃣ QTE虚拟交易所 (localhost:5001)
   ├── 统一数据接口 (REST API)
   ├── WebSocket推送服务
   ├── 订单簿维护
   └── 交易撮合引擎
           ↓
3️⃣ vnpy Gateway接口
   ├── QTEBinanceSpotGateway
   ├── 标准vnpy接口实现
   └── 事件驱动架构
           ↓
4️⃣ QTE策略层
   ├── 策略逻辑
   ├── 风险管理
   └── 交易执行

🔑 关键职责分工:
   • 虚拟交易所: 负责数据获取、存储、推送
   • vnpy Gateway: 负责从虚拟交易所读取数据
   • 策略层: 负责交易决策和执行

✅ 这样的设计优势:
   • 数据源灵活切换 (实时/历史/模拟)
   • 统一的接口标准
   • 便于回测和实盘切换
   • 降低策略与数据源耦合
    """)


def main():
    """主函数"""
    print("🚀 QTE vnpy虚拟交易所集成演示")
    print("=" * 60)
    
    # 检查vnpy可用性
    if not VNPY_AVAILABLE:
        print("❌ vnpy未安装或不可用")
        print("请运行: pip install vnpy")
        return
    
    print("✅ vnpy可用")
    
    # 运行演示
    try:
        # 1. 检查虚拟交易所状态
        virtual_exchange_ok = check_virtual_exchange_status()
        
        # 2. 演示数据流
        if virtual_exchange_ok:
            demo_virtual_exchange_data_flow()
        else:
            print("\n⚠️  无法连接到虚拟交易所，跳过数据流演示")
            print("请确保QTE虚拟交易所正在运行: python start_exchange.py")
        
        # 3. 解释架构
        demo_data_architecture_explanation()
        
    except KeyboardInterrupt:
        print("\n👋 用户中断演示")
    except Exception as e:
        print(f"❌ 演示过程中出现错误：{e}")
    
    print("\n🎉 vnpy虚拟交易所集成演示完成!")


if __name__ == "__main__":
    main() 