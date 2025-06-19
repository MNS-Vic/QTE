"""
QTE虚拟交易所演示
展示完整的虚拟交易所功能：订单撮合、账户管理、实时数据推送
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
import threading
from decimal import Decimal

try:
    from qte.exchange.virtual_exchange import VirtualExchange
    from qte.exchange.mock_exchange import MockExchange
    from qte.exchange.matching.matching_engine import Order, OrderSide, OrderType
    from qte.data.data_replay import DataFrameReplayController, ReplayMode
    from qte.core.time_manager import TimeManager
    EXCHANGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Virtual Exchange modules import failed: {e}")
    EXCHANGE_AVAILABLE = False
    
    # 提供Mock类
    class MockClass:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self
        def __getattr__(self, name):
            return MockClass()
    
    VirtualExchange = MockClass
    MockExchange = MockClass
    Order = MockClass
    OrderSide = MockClass
    OrderType = MockClass
    DataFrameReplayController = MockClass
    ReplayMode = MockClass
    TimeManager = MockClass


class VirtualExchangeDemo:
    """虚拟交易所演示类"""
    
    def __init__(self):
        self.logger = logging.getLogger('VirtualExchangeDemo')
        self.output_dir = Path('demo_output')
        self.output_dir.mkdir(exist_ok=True)
        
        # 虚拟交易所组件
        self.virtual_exchange = None
        self.mock_exchange = None
        self.replay_controller = None
        
        # 演示参数
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        self.initial_balance = 100000.0
        
        # 交易记录
        self.orders = []
        self.trades = []
        self.market_events = []
        
    def check_exchange_availability(self):
        """检查虚拟交易所可用性"""
        if not EXCHANGE_AVAILABLE:
            self.logger.error("❌ 虚拟交易所模块不可用")
            return False
        
        self.logger.info("✅ 虚拟交易所模块可用")
        return True
    
    def setup_virtual_exchange(self):
        """设置虚拟交易所"""
        self.logger.info("🏛️ 设置虚拟交易所...")
        
        try:
            # 创建虚拟交易所
            self.virtual_exchange = VirtualExchange(
                exchange_id="demo_exchange",
                enable_market_data=True,
                enable_data_replay=True
            )
            
            # 创建用户账户
            user_id = "demo_user"
            account = self.virtual_exchange.account_manager.create_account(
                user_id=user_id,
                name="Demo User"
            )

            # 充值初始资金
            account.deposit("USDT", Decimal(str(self.initial_balance)))
            
            # 注册事件监听器
            self.virtual_exchange.add_event_listener(self.on_exchange_event)
            
            self.logger.info("✅ 虚拟交易所设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 虚拟交易所设置失败: {e}")
            return False
    
    def setup_mock_exchange(self):
        """设置Mock交易所（REST API服务器）"""
        self.logger.info("🌐 设置Mock交易所服务器...")
        
        try:
            # 创建Mock交易所
            self.mock_exchange = MockExchange(
                rest_host="localhost",
                rest_port=5001,
                ws_host="localhost", 
                ws_port=8766
            )
            
            # 注册交易对
            for symbol in self.symbols:
                # 解析交易对
                if symbol.endswith('USDT'):
                    base_asset = symbol[:-4]
                    quote_asset = 'USDT'
                else:
                    # 简单解析，实际应该更复杂
                    base_asset = symbol[:3]
                    quote_asset = symbol[3:]

                self.mock_exchange.register_symbol(symbol, base_asset, quote_asset)
            
            # 创建用户账户
            user_id = "demo_user"
            account = self.mock_exchange.account_manager.create_account(
                user_id=user_id,
                name="Demo User"
            )

            # 充值初始资金
            account.deposit("USDT", Decimal(str(self.initial_balance)))
            
            self.logger.info("✅ Mock交易所设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Mock交易所设置失败: {e}")
            return False
    
    def generate_market_data(self):
        """生成市场数据用于回放"""
        self.logger.info("📊 生成市场数据...")
        
        # 生成7天的分钟级数据
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        market_data = {}
        
        for symbol in self.symbols:
            # 设置不同的基础价格
            base_prices = {
                'BTCUSDT': 45000.0,
                'ETHUSDT': 3000.0,
                'ADAUSDT': 0.5
            }
            
            base_price = base_prices.get(symbol, 100.0)
            
            # 生成时间序列
            time_range = pd.date_range(start_time, end_time, freq='1min')
            
            # 生成价格数据（随机游走）
            np.random.seed(hash(symbol) % 2**32)
            returns = np.random.normal(0, 0.001, len(time_range))
            prices = [base_price]
            
            for ret in returns[1:]:
                new_price = prices[-1] * (1 + ret)
                prices.append(max(new_price, 0.01))  # 防止负价格
            
            # 构造DataFrame
            data = []
            for i, (timestamp, close) in enumerate(zip(time_range, prices)):
                high = close * np.random.uniform(1.0001, 1.005)
                low = close * np.random.uniform(0.995, 0.9999)
                open_price = close * np.random.uniform(0.998, 1.002)
                volume = np.random.uniform(1000, 10000)
                
                data.append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'open': round(open_price, 4),
                    'high': round(high, 4),
                    'low': round(low, 4),
                    'close': round(close, 4),
                    'volume': round(volume, 2)
                })
            
            market_data[symbol] = pd.DataFrame(data)
        
        # 保存数据
        data_file = self.output_dir / 'virtual_exchange_market_data.json'
        combined_data = {}
        for symbol, df in market_data.items():
            combined_data[symbol] = df.to_dict('records')
        
        with open(data_file, 'w') as f:
            json.dump(combined_data, f, default=str, indent=2)
        
        self.logger.info(f"✅ 市场数据已生成: {data_file}")
        return market_data
    
    def setup_data_replay(self, market_data):
        """设置数据回放"""
        self.logger.info("🔄 设置数据回放...")
        
        try:
            # 合并所有数据并按时间排序
            all_data = []
            for symbol, df in market_data.items():
                for _, row in df.iterrows():
                    all_data.append(row.to_dict())
            
            # 按时间戳排序
            all_data.sort(key=lambda x: x['timestamp'])
            
            # 创建DataFrame
            combined_df = pd.DataFrame(all_data)
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            
            # 创建回放控制器
            self.replay_controller = DataFrameReplayController(
                dataframe=combined_df,
                timestamp_column='timestamp',
                mode=ReplayMode.BACKTEST,  # 使用回测模式，速度最快
                speed_factor=100.0  # 100倍速回放
            )
            
            # 注册回调
            self.replay_controller.register_callback(self.on_market_data)
            
            self.logger.info("✅ 数据回放设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据回放设置失败: {e}")
            return False
    
    def on_market_data(self, timestamp, data):
        """处理市场数据回调"""
        try:
            symbol = data['symbol']
            
            # 记录市场事件
            self.market_events.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'price': data['close'],
                'volume': data['volume']
            })
            
            # 更新虚拟交易所市场数据
            if self.virtual_exchange:
                self.virtual_exchange._on_replay_data(timestamp, symbol, data)
            
            # 简单的交易策略：价格突破
            self.execute_simple_strategy(symbol, data)
            
        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")
    
    def execute_simple_strategy(self, symbol, data):
        """执行简单交易策略"""
        try:
            # 简单的动量策略
            if len(self.market_events) < 10:
                return
            
            # 获取最近的价格
            recent_events = [e for e in self.market_events[-10:] if e['symbol'] == symbol]
            if len(recent_events) < 5:
                return
            
            current_price = data['close']
            avg_price = sum(e['price'] for e in recent_events[-5:]) / 5
            
            # 价格上涨超过1%，买入
            if current_price > avg_price * 1.01:
                self.place_buy_order(symbol, current_price, 0.1)
            
            # 价格下跌超过1%，卖出
            elif current_price < avg_price * 0.99:
                self.place_sell_order(symbol, current_price, 0.1)
                
        except Exception as e:
            self.logger.error(f"执行策略失败: {e}")
    
    def place_buy_order(self, symbol, price, quantity):
        """下买单"""
        try:
            if self.virtual_exchange:
                order_id = self.virtual_exchange.create_order(
                    user_id="demo_user",
                    symbol=symbol,
                    side="BUY",
                    order_type="LIMIT",
                    quantity=quantity,
                    price=price
                )
                
                if order_id:
                    self.orders.append({
                        'order_id': order_id,
                        'symbol': symbol,
                        'side': 'BUY',
                        'quantity': quantity,
                        'price': price,
                        'timestamp': datetime.now()
                    })
                    
                    self.logger.debug(f"📈 买单已下: {symbol} {quantity}@{price}")
                    
        except Exception as e:
            self.logger.error(f"下买单失败: {e}")
    
    def place_sell_order(self, symbol, price, quantity):
        """下卖单"""
        try:
            if self.virtual_exchange:
                order_id = self.virtual_exchange.create_order(
                    user_id="demo_user",
                    symbol=symbol,
                    side="SELL",
                    order_type="LIMIT",
                    quantity=quantity,
                    price=price
                )
                
                if order_id:
                    self.orders.append({
                        'order_id': order_id,
                        'symbol': symbol,
                        'side': 'SELL',
                        'quantity': quantity,
                        'price': price,
                        'timestamp': datetime.now()
                    })
                    
                    self.logger.debug(f"📉 卖单已下: {symbol} {quantity}@{price}")
                    
        except Exception as e:
            self.logger.error(f"下卖单失败: {e}")
    
    def on_exchange_event(self, event):
        """处理交易所事件"""
        try:
            if event.event_type == "TRADE":
                trade_data = event.data
                self.trades.append(trade_data)
                self.logger.info(f"💰 成交: {trade_data}")
                
            elif event.event_type == "ORDER_UPDATE":
                order_data = event.data
                self.logger.debug(f"📋 订单更新: {order_data}")
                
        except Exception as e:
            self.logger.error(f"处理交易所事件失败: {e}")
    
    def start_exchange_servers(self):
        """启动交易所服务器"""
        self.logger.info("🚀 启动交易所服务器...")
        
        try:
            if self.mock_exchange:
                # 在后台线程启动服务器
                server_thread = threading.Thread(
                    target=self.mock_exchange.start,
                    daemon=True
                )
                server_thread.start()
                
                # 等待服务器启动
                time.sleep(2)
                self.logger.info("✅ 交易所服务器已启动")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 启动交易所服务器失败: {e}")
            return False
    
    def run_demo(self):
        """运行虚拟交易所演示"""
        self.logger.info("🚀 开始虚拟交易所演示...")
        
        try:
            # 1. 检查可用性
            if not self.check_exchange_availability():
                return None
            
            # 2. 设置虚拟交易所
            if not self.setup_virtual_exchange():
                return None
            
            # 3. 设置Mock交易所
            if not self.setup_mock_exchange():
                return None
            
            # 4. 启动服务器
            if not self.start_exchange_servers():
                return None
            
            # 5. 生成市场数据
            market_data = self.generate_market_data()
            
            # 6. 设置数据回放
            if not self.setup_data_replay(market_data):
                return None
            
            # 7. 开始回放
            self.logger.info("🔄 开始数据回放...")
            self.replay_controller.start()
            
            # 等待回放完成
            while self.replay_controller.is_running():
                time.sleep(1)
            
            # 8. 生成报告
            results = self.generate_report()
            
            self.logger.info("🎉 虚拟交易所演示完成!")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 虚拟交易所演示失败: {e}")
            return None
    
    def generate_report(self):
        """生成演示报告"""
        self.logger.info("📋 生成虚拟交易所演示报告...")
        
        # 统计结果
        results = {
            'market_events_count': len(self.market_events),
            'orders_count': len(self.orders),
            'trades_count': len(self.trades),
            'symbols_traded': list(set(order['symbol'] for order in self.orders)),
            'total_volume': sum(trade.get('quantity', 0) for trade in self.trades),
            'demo_duration': '7 days (100x speed)',
            'exchange_features_demonstrated': [
                '实时市场数据处理',
                '订单撮合引擎',
                '账户管理系统',
                '事件驱动架构',
                'REST API服务器',
                '数据回放功能'
            ]
        }
        
        # 保存详细报告
        report_file = self.output_dir / 'virtual_exchange_demo_report.json'
        detailed_report = {
            'summary': results,
            'market_events': self.market_events[-100:],  # 最后100个事件
            'orders': self.orders,
            'trades': self.trades
        }
        
        with open(report_file, 'w') as f:
            json.dump(detailed_report, f, default=str, indent=2)
        
        # 打印摘要
        self.logger.info("📊 虚拟交易所演示结果摘要:")
        self.logger.info(f"   市场事件数: {results['market_events_count']}")
        self.logger.info(f"   订单数: {results['orders_count']}")
        self.logger.info(f"   成交数: {results['trades_count']}")
        self.logger.info(f"   交易标的: {results['symbols_traded']}")
        self.logger.info(f"   总成交量: {results['total_volume']}")
        self.logger.info(f"📁 详细报告已保存: {report_file}")
        
        return results


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    demo = VirtualExchangeDemo()
    results = demo.run_demo()
