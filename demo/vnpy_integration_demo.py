"""
QTE vnpy集成演示
展示QTE与vnpy框架的完整集成：Gateway、订单管理、交易执行
确保回测环境与实盘交易环境的一致性
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
import threading
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

try:
    from qte.vnpy import check_vnpy_availability, is_vnpy_available
    from qte.vnpy.gateways import GatewayFactory, GatewayType, create_qte_gateway
    from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
    from qte.vnpy.data_source import VnpyDataSource
    from qte.exchange.virtual_exchange import VirtualExchange
    from qte.exchange.mock_exchange import MockExchange
    VNPY_INTEGRATION_AVAILABLE = True
    
    # 尝试导入vnpy核心组件
    try:
        from vnpy.event import EventEngine, Event
        from vnpy.trader.object import (
            TickData, OrderData, TradeData, AccountData, ContractData,
            OrderRequest, CancelRequest, SubscribeRequest
        )
        from vnpy.trader.constant import (
            Exchange, Product, Status, OrderType, Direction, Offset
        )
        from vnpy.trader.event import (
            EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_CONTRACT
        )
        VNPY_CORE_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: vnpy core modules import failed: {e}")
        VNPY_CORE_AVAILABLE = False
        
        # 提供Mock类
        class MockClass:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, *args, **kwargs):
                return self
            def __getattr__(self, name):
                return MockClass()
        
        EventEngine = MockClass
        Event = MockClass
        TickData = MockClass
        OrderData = MockClass
        TradeData = MockClass
        AccountData = MockClass
        ContractData = MockClass
        OrderRequest = MockClass
        CancelRequest = MockClass
        SubscribeRequest = MockClass
        Exchange = MockClass
        Product = MockClass
        Status = MockClass
        OrderType = MockClass
        Direction = MockClass
        Offset = MockClass
        EVENT_TICK = "EVENT_TICK"
        EVENT_ORDER = "EVENT_ORDER"
        EVENT_TRADE = "EVENT_TRADE"
        EVENT_ACCOUNT = "EVENT_ACCOUNT"
        EVENT_CONTRACT = "EVENT_CONTRACT"
        
except ImportError as e:
    print(f"Warning: QTE vnpy integration modules import failed: {e}")
    VNPY_INTEGRATION_AVAILABLE = False
    VNPY_CORE_AVAILABLE = False
    
    # 提供Mock类
    class MockClass:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self
        def __getattr__(self, name):
            return MockClass()
    
    # Mock所有类
    GatewayFactory = MockClass
    GatewayType = MockClass
    create_qte_gateway = MockClass
    QTEBinanceSpotGateway = MockClass
    VnpyDataSource = MockClass
    VirtualExchange = MockClass
    MockExchange = MockClass
    EventEngine = MockClass
    Event = MockClass


class VnpyIntegrationDemo:
    """vnpy集成演示类"""
    
    def __init__(self):
        self.logger = logging.getLogger('VnpyIntegrationDemo')
        self.output_dir = Path('demo_output')
        self.output_dir.mkdir(exist_ok=True)
        
        # vnpy组件
        self.event_engine = None
        self.gateway = None
        self.data_source = None
        
        # QTE组件
        self.virtual_exchange = None
        self.mock_exchange = None
        
        # 演示参数
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        self.initial_balance = 100000.0
        
        # 交易记录
        self.orders = []
        self.trades = []
        self.market_data = []
        self.events_received = []
        
    def check_vnpy_availability(self):
        """检查vnpy可用性"""
        if not VNPY_INTEGRATION_AVAILABLE:
            self.logger.warning("⚠️ QTE vnpy集成模块不可用，使用演示模式")
            return "demo_mode"

        if not VNPY_CORE_AVAILABLE:
            self.logger.warning("⚠️ vnpy核心模块不可用，使用演示模式")
            self.logger.info("💡 演示模式将展示QTE vnpy集成架构和接口设计")
            return "demo_mode"

        # 使用QTE的vnpy可用性检查
        available, info = check_vnpy_availability()

        if available:
            self.logger.info("✅ vnpy集成环境可用")
            self.logger.info(f"   vnpy版本: {info.get('version', 'Unknown')}")
            self.logger.info(f"   可用组件: {len(info.get('available_components', []))}")
            return "full_mode"
        else:
            self.logger.warning("⚠️ vnpy环境不完整，使用演示模式")
            self.logger.info(f"   缺失依赖: {info.get('missing_deps', [])}")
            self.logger.info("💡 演示模式将展示QTE vnpy集成架构和接口设计")
            return "demo_mode"
    
    def setup_vnpy_components(self):
        """设置vnpy组件"""
        self.logger.info("🔧 设置vnpy组件...")
        
        try:
            # 1. 创建vnpy事件引擎
            self.event_engine = EventEngine()
            self.event_engine.start()
            self.logger.info("✅ vnpy事件引擎已启动")
            
            # 2. 注册事件监听器
            self.register_event_handlers()
            
            # 3. 创建QTE Gateway
            self.gateway = QTEBinanceSpotGateway(
                event_engine=self.event_engine,
                gateway_name="QTE_DEMO_GATEWAY"
            )
            self.logger.info("✅ QTE Gateway已创建")
            
            # 4. 创建vnpy数据源
            self.data_source = VnpyDataSource(
                gateway_names=["QTE_DEMO_GATEWAY"],
                virtual_exchange_host="localhost:5001"
            )
            self.logger.info("✅ vnpy数据源已创建")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ vnpy组件设置失败: {e}")
            return False
    
    def setup_qte_backend(self):
        """设置QTE后端交易所"""
        self.logger.info("🏛️ 设置QTE后端交易所...")
        
        try:
            # 1. 创建虚拟交易所
            self.virtual_exchange = VirtualExchange(
                exchange_id="vnpy_demo_exchange",
                enable_market_data=True,
                enable_data_replay=True
            )
            
            # 2. 创建用户账户
            account = self.virtual_exchange.account_manager.create_account(
                user_id="vnpy_demo_user",
                name="vnpy Demo User"
            )
            
            # 3. 充值初始资金
            from decimal import Decimal
            account.deposit("USDT", Decimal(str(self.initial_balance)))
            
            # 4. 创建Mock交易所（REST API服务器）
            self.mock_exchange = MockExchange(
                rest_host="localhost",
                rest_port=5001,
                ws_host="localhost",
                ws_port=8766
            )
            
            # 5. 注册交易对
            for symbol in self.symbols:
                if symbol.endswith('USDT'):
                    base_asset = symbol[:-4]
                    quote_asset = 'USDT'
                else:
                    base_asset = symbol[:3]
                    quote_asset = symbol[3:]
                
                self.mock_exchange.register_symbol(symbol, base_asset, quote_asset)
            
            # 6. 启动服务器
            server_thread = threading.Thread(
                target=self.mock_exchange.start,
                daemon=True
            )
            server_thread.start()
            time.sleep(2)  # 等待服务器启动
            
            self.logger.info("✅ QTE后端交易所已启动")
            self.logger.info("   REST API: localhost:5001")
            self.logger.info("   WebSocket: localhost:8766")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ QTE后端设置失败: {e}")
            return False
    
    def register_event_handlers(self):
        """注册vnpy事件处理器"""
        self.logger.info("📡 注册vnpy事件处理器...")
        
        # 注册各种事件的处理器
        self.event_engine.register(EVENT_TICK, self.on_tick)
        self.event_engine.register(EVENT_ORDER, self.on_order)
        self.event_engine.register(EVENT_TRADE, self.on_trade)
        self.event_engine.register(EVENT_ACCOUNT, self.on_account)
        self.event_engine.register(EVENT_CONTRACT, self.on_contract)
        
        self.logger.info("✅ 事件处理器注册完成")
    
    def on_tick(self, event: Event):
        """处理Tick数据事件"""
        tick = event.data
        self.market_data.append({
            'timestamp': datetime.now(),
            'symbol': tick.symbol,
            'last_price': tick.last_price,
            'volume': tick.volume,
            'event_type': 'TICK'
        })
        self.events_received.append('TICK')
        self.logger.debug(f"📊 收到Tick: {tick.symbol} @ {tick.last_price}")
    
    def on_order(self, event: Event):
        """处理订单事件"""
        order = event.data
        self.orders.append({
            'timestamp': datetime.now(),
            'orderid': order.orderid,
            'symbol': order.symbol,
            'direction': order.direction.value if hasattr(order.direction, 'value') else str(order.direction),
            'volume': order.volume,
            'price': order.price,
            'status': order.status.value if hasattr(order.status, 'value') else str(order.status),
            'event_type': 'ORDER'
        })
        self.events_received.append('ORDER')
        self.logger.info(f"📋 订单更新: {order.orderid} - {order.status}")
    
    def on_trade(self, event: Event):
        """处理成交事件"""
        trade = event.data
        self.trades.append({
            'timestamp': datetime.now(),
            'tradeid': trade.tradeid,
            'orderid': trade.orderid,
            'symbol': trade.symbol,
            'direction': trade.direction.value if hasattr(trade.direction, 'value') else str(trade.direction),
            'volume': trade.volume,
            'price': trade.price,
            'event_type': 'TRADE'
        })
        self.events_received.append('TRADE')
        self.logger.info(f"💰 成交记录: {trade.tradeid} - {trade.volume}@{trade.price}")
    
    def on_account(self, event: Event):
        """处理账户事件"""
        account = event.data
        self.events_received.append('ACCOUNT')
        self.logger.info(f"💳 账户更新: {account.accountid} - 余额: {account.balance}")
    
    def on_contract(self, event: Event):
        """处理合约事件"""
        contract = event.data
        self.events_received.append('CONTRACT')
        self.logger.info(f"📜 合约信息: {contract.symbol}")
    
    def connect_gateway(self):
        """连接Gateway到QTE交易所"""
        self.logger.info("🔗 连接Gateway到QTE交易所...")
        
        try:
            # Gateway连接配置
            setting = {
                "API密钥": "demo_api_key",
                "私钥": "demo_secret_key",
                "服务器": "QTE_MOCK",  # 连接到QTE模拟交易所
                "代理地址": "",
                "代理端口": 0,
            }
            
            # 连接Gateway
            self.gateway.connect(setting)
            
            # 等待连接建立
            time.sleep(3)
            
            self.logger.info("✅ Gateway连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Gateway连接失败: {e}")
            return False
    
    def demonstrate_trading_workflow(self):
        """演示完整的交易流程"""
        self.logger.info("💼 演示vnpy交易流程...")
        
        try:
            # 1. 订阅市场数据
            self.logger.info("📊 订阅市场数据...")
            for symbol in self.symbols:
                req = SubscribeRequest(
                    symbol=symbol,
                    exchange=Exchange.OTC
                )
                self.gateway.subscribe(req)
            
            time.sleep(2)  # 等待数据订阅
            
            # 2. 查询账户信息
            self.logger.info("💳 查询账户信息...")
            self.gateway.query_account()
            
            # 3. 查询持仓信息
            self.logger.info("📊 查询持仓信息...")
            self.gateway.query_position()
            
            # 4. 下单演示
            self.logger.info("📋 演示下单流程...")
            
            # 创建买单
            buy_order = OrderRequest(
                symbol="BTCUSDT",
                exchange=Exchange.OTC,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=0.001,
                price=45000.0,
                offset=Offset.NONE,
                reference="vnpy_demo_buy"
            )
            
            # 发送订单
            order_id = self.gateway.send_order(buy_order)
            self.logger.info(f"📤 买单已发送: {order_id}")
            
            time.sleep(2)  # 等待订单处理
            
            # 创建卖单
            sell_order = OrderRequest(
                symbol="ETHUSDT",
                exchange=Exchange.OTC,
                direction=Direction.SHORT,
                type=OrderType.LIMIT,
                volume=0.01,
                price=3000.0,
                offset=Offset.NONE,
                reference="vnpy_demo_sell"
            )
            
            # 发送订单
            order_id = self.gateway.send_order(sell_order)
            self.logger.info(f"📤 卖单已发送: {order_id}")
            
            time.sleep(3)  # 等待订单处理和成交
            
            self.logger.info("✅ 交易流程演示完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 交易流程演示失败: {e}")
            return False
    
    def generate_integration_report(self):
        """生成vnpy集成演示报告"""
        self.logger.info("📋 生成vnpy集成演示报告...")
        
        # 统计事件数量
        event_stats = {}
        for event_type in ['TICK', 'ORDER', 'TRADE', 'ACCOUNT', 'CONTRACT']:
            event_stats[event_type] = self.events_received.count(event_type)
        
        # 生成报告
        report = {
            'demo_type': 'vnpy Integration Demo',
            'vnpy_availability': {
                'integration_available': VNPY_INTEGRATION_AVAILABLE,
                'core_available': VNPY_CORE_AVAILABLE,
                'gateway_connected': self.gateway is not None,
                'event_engine_running': self.event_engine is not None
            },
            'trading_statistics': {
                'symbols_subscribed': len(self.symbols),
                'orders_sent': len(self.orders),
                'trades_executed': len(self.trades),
                'market_data_received': len(self.market_data),
                'total_events': len(self.events_received)
            },
            'event_statistics': event_stats,
            'integration_features_demonstrated': [
                'vnpy事件引擎集成',
                'QTE Gateway创建和连接',
                'vnpy标准订单接口',
                '市场数据订阅和推送',
                '订单生命周期管理',
                '成交数据处理',
                '账户和持仓查询',
                'QTE虚拟交易所后端'
            ],
            'backend_services': {
                'virtual_exchange': self.virtual_exchange is not None,
                'mock_exchange_rest': 'localhost:5001',
                'mock_exchange_ws': 'localhost:8766',
                'initial_balance': self.initial_balance
            }
        }
        
        # 保存详细报告
        report_file = self.output_dir / 'vnpy_integration_demo_report.json'
        detailed_report = {
            'summary': report,
            'orders': self.orders,
            'trades': self.trades,
            'market_data': self.market_data[-50:],  # 最后50条市场数据
            'events_timeline': self.events_received[-100:]  # 最后100个事件
        }
        
        with open(report_file, 'w') as f:
            json.dump(detailed_report, f, default=str, indent=2)
        
        # 打印摘要
        self.logger.info("📊 vnpy集成演示结果摘要:")
        self.logger.info(f"   订阅标的: {report['trading_statistics']['symbols_subscribed']} 个")
        self.logger.info(f"   发送订单: {report['trading_statistics']['orders_sent']} 个")
        self.logger.info(f"   执行成交: {report['trading_statistics']['trades_executed']} 个")
        self.logger.info(f"   接收事件: {report['trading_statistics']['total_events']} 个")
        self.logger.info(f"   初始资金: ${report['backend_services']['initial_balance']:,.2f}")
        self.logger.info(f"📁 详细报告已保存: {report_file}")
        
        return report

    def cleanup(self):
        """清理资源"""
        self.logger.info("🧹 清理vnpy集成演示资源...")

        try:
            # 关闭Gateway
            if self.gateway:
                self.gateway.close()
                self.logger.info("✅ Gateway已关闭")

            # 停止事件引擎
            if self.event_engine:
                self.event_engine.stop()
                self.logger.info("✅ 事件引擎已停止")

            # 停止交易所服务器
            if self.mock_exchange:
                self.mock_exchange.stop()
                self.logger.info("✅ Mock交易所已停止")

        except Exception as e:
            self.logger.error(f"❌ 资源清理失败: {e}")

    def run_demo_mode(self):
        """运行演示模式（不依赖vnpy）"""
        self.logger.info("🎭 运行vnpy集成架构演示模式...")

        # 演示QTE vnpy集成架构
        self.logger.info("🏗️ QTE vnpy集成架构展示:")
        self.logger.info("   ├── qte.vnpy.gateways - Gateway工厂和实现")
        self.logger.info("   ├── qte.vnpy.data_source - vnpy数据源适配器")
        self.logger.info("   ├── qte.vnpy.event_converters - 事件转换器")
        self.logger.info("   └── qte.vnpy.strategy_adapters - 策略适配器")

        # 模拟Gateway创建
        self.logger.info("🔧 模拟Gateway创建过程...")
        self.logger.info("   ✅ QTEBinanceSpotGateway - 币安现货Gateway")
        self.logger.info("   ✅ 事件引擎集成 - vnpy EventEngine适配")
        self.logger.info("   ✅ 订单接口标准化 - vnpy OrderRequest兼容")

        # 模拟交易流程
        self.logger.info("💼 模拟vnpy标准交易流程...")

        # 模拟订单
        demo_orders = [
            {"symbol": "BTCUSDT", "direction": "LONG", "volume": 0.001, "price": 45000.0},
            {"symbol": "ETHUSDT", "direction": "SHORT", "volume": 0.01, "price": 3000.0}
        ]

        for i, order in enumerate(demo_orders, 1):
            self.logger.info(f"   📋 模拟订单 {i}: {order['symbol']} {order['direction']} {order['volume']}@{order['price']}")
            self.orders.append({
                'timestamp': datetime.now(),
                'orderid': f"demo_order_{i}",
                'symbol': order['symbol'],
                'direction': order['direction'],
                'volume': order['volume'],
                'price': order['price'],
                'status': 'SUBMITTED',
                'event_type': 'ORDER'
            })

            # 模拟成交
            self.trades.append({
                'timestamp': datetime.now(),
                'tradeid': f"demo_trade_{i}",
                'orderid': f"demo_order_{i}",
                'symbol': order['symbol'],
                'direction': order['direction'],
                'volume': order['volume'],
                'price': order['price'],
                'event_type': 'TRADE'
            })

            self.logger.info(f"   💰 模拟成交 {i}: {order['volume']}@{order['price']}")

        # 模拟市场数据
        self.logger.info("📊 模拟市场数据订阅...")
        for symbol in self.symbols:
            price = np.random.uniform(1000, 50000)
            self.market_data.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'last_price': price,
                'volume': np.random.uniform(1000, 10000),
                'event_type': 'TICK'
            })
            self.logger.info(f"   📈 {symbol}: ${price:.2f}")

        # 模拟事件统计
        self.events_received = ['TICK'] * len(self.symbols) + ['ORDER'] * len(demo_orders) + ['TRADE'] * len(demo_orders)

        return True

    def run_demo(self):
        """运行完整的vnpy集成演示"""
        self.logger.info("🚀 开始vnpy集成演示...")

        try:
            # 1. 检查vnpy可用性
            mode = self.check_vnpy_availability()

            if mode == "demo_mode":
                # 运行演示模式
                if not self.run_demo_mode():
                    return None
            else:
                # 运行完整模式
                # 2. 设置QTE后端交易所
                if not self.setup_qte_backend():
                    return None

                # 3. 设置vnpy组件
                if not self.setup_vnpy_components():
                    return None

                # 4. 连接Gateway
                if not self.connect_gateway():
                    return None

                # 5. 演示交易流程
                if not self.demonstrate_trading_workflow():
                    return None

            # 6. 生成报告
            report = self.generate_integration_report()

            self.logger.info("🎉 vnpy集成演示完成!")
            return report

        except Exception as e:
            self.logger.error(f"❌ vnpy集成演示失败: {e}")
            return None

        finally:
            # 清理资源
            self.cleanup()


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行演示
    demo = VnpyIntegrationDemo()
    results = demo.run_demo()
