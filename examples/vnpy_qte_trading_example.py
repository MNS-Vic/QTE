#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
vnpy与QTE集成交易流程完整实例

实现README.md中描述的完整交易流程：
历史数据 -> DataReplayController -> QTE虚拟交易所 -> vnpy Gateway -> 交易策略
"""

import sys
import time
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# vnpy imports
from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import (
    TickData, OrderData, TradeData, AccountData, ContractData,
    OrderRequest, CancelRequest, SubscribeRequest
)
from vnpy.trader.constant import Direction, OrderType, Status, Exchange, Product
from vnpy.trader.gateway import BaseGateway

# QTE imports
from qte.vnpy.gateways import GatewayFactory, GatewayType
from qte.vnpy.gateways.qte_event_converters import QTEMarketData, QTEOrderData
from qte.core.engine import VectorEngine
from qte.data.sources.base import BaseDataSource


class DataReplayController:
    """
    数据回放控制器
    
    负责按时间顺序推送历史数据到QTE虚拟交易所
    """
    
    def __init__(self, data_source: BaseDataSource):
        self.data_source = data_source
        self.current_time = None
        self.replay_speed = 1.0  # 回放速度倍数
        self.is_running = False
        self.subscribers = []
        
    def add_subscriber(self, callback):
        """添加数据订阅者"""
        self.subscribers.append(callback)
        
    def load_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """加载历史数据"""
        # 模拟历史数据
        dates = pd.date_range(start=start_date, end=end_date, freq='1min')
        
        # 生成模拟价格数据
        base_price = 50000.0
        price_changes = np.random.normal(0, 0.001, len(dates))
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        data = pd.DataFrame({
            'datetime': dates,
            'symbol': symbol,
            'open': prices,
            'high': [p * 1.001 for p in prices],
            'low': [p * 0.999 for p in prices],
            'close': prices,
            'volume': np.random.randint(100, 1000, len(dates))
        })
        
        return data
    
    async def start_replay(self, symbol: str, start_date: str, end_date: str):
        """开始数据回放"""
        print(f"🎬 开始回放历史数据: {symbol} ({start_date} 到 {end_date})")
        
        # 加载历史数据
        historical_data = self.load_historical_data(symbol, start_date, end_date)
        self.is_running = True
        
        for _, row in historical_data.iterrows():
            if not self.is_running:
                break
                
            # 创建市场数据
            market_data = QTEMarketData(
                symbol=row['symbol'],
                price=Decimal(str(row['close'])),
                volume=Decimal(str(row['volume'])),
                timestamp=row['datetime'],
                bid_price=Decimal(str(row['close'] * 0.9999)),
                ask_price=Decimal(str(row['close'] * 1.0001)),
                bid_volume=Decimal(str(row['volume'] * 0.3)),
                ask_volume=Decimal(str(row['volume'] * 0.3))
            )
            
            # 推送数据给订阅者
            for callback in self.subscribers:
                try:
                    await callback(market_data)
                except Exception as e:
                    print(f"❌ 数据推送失败: {e}")
            
            # 控制回放速度
            await asyncio.sleep(0.1 / self.replay_speed)
            
        print("✅ 数据回放完成")
    
    def stop_replay(self):
        """停止数据回放"""
        self.is_running = False


class QTEVirtualExchange:
    """
    QTE虚拟交易所
    
    接收历史数据，进行订单撮合，更新市场数据
    """
    
    def __init__(self):
        self.market_data: Dict[str, QTEMarketData] = {}
        self.orders: Dict[str, QTEOrderData] = {}
        self.trades: List[Dict] = []
        self.accounts = {
            'USDT': Decimal('100000.0'),  # 初始资金
            'BTC': Decimal('0.0')
        }
        self.order_id_counter = 1
        self.subscribers = []
        
    def add_subscriber(self, callback):
        """添加市场数据订阅者"""
        self.subscribers.append(callback)
        
    async def on_market_data(self, data: QTEMarketData):
        """处理市场数据更新"""
        self.market_data[data.symbol] = data
        
        # 检查是否有订单可以成交
        await self._match_orders(data)
        
        # 推送市场数据给订阅者
        for callback in self.subscribers:
            try:
                await callback(data)
            except Exception as e:
                print(f"❌ 市场数据推送失败: {e}")
    
    async def _match_orders(self, market_data: QTEMarketData):
        """订单撮合引擎"""
        symbol = market_data.symbol
        current_price = market_data.price
        
        # 检查所有未成交订单
        for order_id, order in list(self.orders.items()):
            if order.symbol != symbol or order.status != "PENDING":
                continue
                
            should_fill = False
            fill_price = current_price
            
            # 市价单立即成交
            if order.order_type == "MARKET":
                should_fill = True
                fill_price = current_price
            
            # 限价单条件成交
            elif order.order_type == "LIMIT":
                if order.side == "BUY" and current_price <= order.price:
                    should_fill = True
                    fill_price = order.price
                elif order.side == "SELL" and current_price >= order.price:
                    should_fill = True
                    fill_price = order.price
            
            if should_fill:
                await self._execute_trade(order, fill_price)
    
    async def _execute_trade(self, order: QTEOrderData, fill_price: Decimal):
        """执行交易"""
        # 更新订单状态
        order.status = "FILLED"
        order.filled_quantity = order.quantity
        
        # 记录成交
        trade = {
            'trade_id': f"T{len(self.trades) + 1}",
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'price': fill_price,
            'timestamp': datetime.now()
        }
        self.trades.append(trade)
        
        # 更新账户余额
        if order.side == "BUY":
            cost = order.quantity * fill_price
            self.accounts['USDT'] -= cost
            base_currency = order.symbol.replace('USDT', '')
            if base_currency not in self.accounts:
                self.accounts[base_currency] = Decimal('0')
            self.accounts[base_currency] += order.quantity
        else:  # SELL
            revenue = order.quantity * fill_price
            self.accounts['USDT'] += revenue
            base_currency = order.symbol.replace('USDT', '')
            self.accounts[base_currency] -= order.quantity
        
        print(f"✅ 交易执行: {order.side} {order.quantity} {order.symbol} @ {fill_price}")
        print(f"💰 账户余额: {dict(self.accounts)}")
    
    async def place_order(self, symbol: str, side: str, order_type: str, 
                         quantity: Decimal, price: Optional[Decimal] = None) -> str:
        """下单"""
        order_id = f"O{self.order_id_counter}"
        self.order_id_counter += 1
        
        order = QTEOrderData(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price or Decimal('0'),
            status="PENDING",
            filled_quantity=Decimal('0'),
            timestamp=datetime.now()
        )
        
        self.orders[order_id] = order
        print(f"📝 订单提交: {side} {quantity} {symbol} @ {price or 'MARKET'}")
        
        # 如果是市价单，立即尝试撮合
        if order_type == "MARKET" and symbol in self.market_data:
            await self._match_orders(self.market_data[symbol])
        
        return order_id
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        return {
            'balances': dict(self.accounts),
            'orders': len(self.orders),
            'trades': len(self.trades)
        }


class SimpleStrategy:
    """
    简单交易策略
    
    基于移动平均线的交易策略
    """
    
    def __init__(self, exchange: QTEVirtualExchange):
        self.exchange = exchange
        self.price_history = []
        self.position = Decimal('0')  # 当前持仓
        self.last_signal = None
        
    async def on_market_data(self, data: QTEMarketData):
        """处理市场数据"""
        self.price_history.append(float(data.price))
        
        # 保持最近50个价格点
        if len(self.price_history) > 50:
            self.price_history.pop(0)
        
        # 需要足够的历史数据才能计算信号
        if len(self.price_history) < 20:
            return
        
        # 计算移动平均线
        short_ma = np.mean(self.price_history[-5:])  # 5周期短期均线
        long_ma = np.mean(self.price_history[-20:])  # 20周期长期均线
        
        current_price = float(data.price)
        
        # 生成交易信号
        signal = None
        if short_ma > long_ma and self.last_signal != 'BUY':
            signal = 'BUY'
        elif short_ma < long_ma and self.last_signal != 'SELL':
            signal = 'SELL'
        
        if signal:
            await self._execute_signal(signal, data.symbol, current_price)
            self.last_signal = signal
    
    async def _execute_signal(self, signal: str, symbol: str, current_price: float):
        """执行交易信号"""
        quantity = Decimal('0.1')  # 固定交易数量
        
        if signal == 'BUY' and self.position <= 0:
            # 买入信号且当前无多头持仓
            await self.exchange.place_order(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity
            )
            self.position += quantity
            print(f"📈 策略信号: 买入 {quantity} {symbol} @ {current_price}")
            
        elif signal == 'SELL' and self.position > 0:
            # 卖出信号且当前有多头持仓
            sell_quantity = min(quantity, self.position)
            await self.exchange.place_order(
                symbol=symbol,
                side="SELL",
                order_type="MARKET",
                quantity=sell_quantity
            )
            self.position -= sell_quantity
            print(f"📉 策略信号: 卖出 {sell_quantity} {symbol} @ {current_price}")


class VnpyGatewayBridge:
    """
    vnpy Gateway桥接器
    
    连接QTE虚拟交易所和vnpy系统
    """
    
    def __init__(self, exchange: QTEVirtualExchange, event_engine: EventEngine):
        self.exchange = exchange
        self.event_engine = event_engine
        self.gateway = None
        
    def setup_gateway(self):
        """设置Gateway"""
        try:
            # 创建QTE Gateway
            factory = GatewayFactory()
            self.gateway = factory.create_gateway(
                GatewayType.QTE_BINANCE,
                event_engine=self.event_engine,
                gateway_name="QTE_VIRTUAL"
            )
            print("✅ vnpy Gateway桥接器设置成功")
            return True
        except Exception as e:
            print(f"❌ vnpy Gateway桥接器设置失败: {e}")
            return False
    
    async def on_market_data(self, data: QTEMarketData):
        """处理来自QTE的市场数据，转发给vnpy"""
        if not self.gateway:
            return
            
        try:
            # 转换为vnpy TickData格式
            tick = TickData(
                symbol=data.symbol,
                exchange=Exchange.OTC,
                datetime=data.timestamp,
                name=data.symbol,
                volume=float(data.volume),
                turnover=float(data.price * data.volume),
                open_interest=0,
                last_price=float(data.price),
                last_volume=float(data.volume),
                limit_up=0,
                limit_down=0,
                open_price=float(data.price),
                high_price=float(data.price),
                low_price=float(data.price),
                pre_close=float(data.price),
                bid_price_1=float(data.bid_price),
                ask_price_1=float(data.ask_price),
                bid_volume_1=float(data.bid_volume),
                ask_volume_1=float(data.ask_volume),
                gateway_name="QTE_VIRTUAL"
            )
            
            # 发送到vnpy事件系统
            self.event_engine.put(Event(type="eTick", data=tick))
            
        except Exception as e:
            print(f"❌ 市场数据转换失败: {e}")


async def main():
    """主函数 - 运行完整的交易流程"""
    print("🚀 启动vnpy与QTE集成交易流程演示")
    print("=" * 60)
    
    # 1. 创建事件引擎
    print("1️⃣ 创建vnpy事件引擎...")
    event_engine = EventEngine()
    
    # 2. 创建QTE虚拟交易所
    print("2️⃣ 创建QTE虚拟交易所...")
    exchange = QTEVirtualExchange()
    
    # 3. 创建数据回放控制器
    print("3️⃣ 创建数据回放控制器...")
    data_controller = DataReplayController(data_source=None)
    
    # 4. 创建交易策略
    print("4️⃣ 创建简单交易策略...")
    strategy = SimpleStrategy(exchange)
    
    # 5. 创建vnpy Gateway桥接器
    print("5️⃣ 创建vnpy Gateway桥接器...")
    gateway_bridge = VnpyGatewayBridge(exchange, event_engine)
    gateway_bridge.setup_gateway()
    
    # 6. 连接数据流
    print("6️⃣ 连接数据流...")
    data_controller.add_subscriber(exchange.on_market_data)
    exchange.add_subscriber(strategy.on_market_data)
    exchange.add_subscriber(gateway_bridge.on_market_data)
    
    # 7. 显示初始账户状态
    print("7️⃣ 初始账户状态:")
    account_info = exchange.get_account_info()
    print(f"   💰 余额: {account_info['balances']}")
    print(f"   📝 订单: {account_info['orders']}")
    print(f"   💼 交易: {account_info['trades']}")
    
    print("\n" + "=" * 60)
    print("🎬 开始交易流程演示...")
    print("=" * 60)
    
    # 8. 开始数据回放和交易
    try:
        # 设置回放参数
        symbol = "BTCUSDT"
        start_date = "2024-01-01 09:00:00"
        end_date = "2024-01-01 12:00:00"
        
        # 启动数据回放
        await data_controller.start_replay(symbol, start_date, end_date)
        
        # 等待一段时间让所有异步操作完成
        await asyncio.sleep(2)
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断交易流程")
    except Exception as e:
        print(f"\n❌ 交易流程异常: {e}")
    finally:
        # 9. 清理资源
        print("\n" + "=" * 60)
        print("🧹 清理资源...")
        data_controller.stop_replay()
        event_engine.stop()
        
        # 10. 显示最终结果
        print("📊 最终交易结果:")
        final_account = exchange.get_account_info()
        print(f"   💰 最终余额: {final_account['balances']}")
        print(f"   📝 总订单数: {final_account['orders']}")
        print(f"   💼 总交易数: {final_account['trades']}")
        
        # 计算收益
        if exchange.trades:
            print(f"   📈 交易记录:")
            for trade in exchange.trades[-5:]:  # 显示最后5笔交易
                print(f"      {trade['side']} {trade['quantity']} {trade['symbol']} @ {trade['price']}")
        
        print("✅ 交易流程演示完成")


if __name__ == "__main__":
    # 检查vnpy可用性
    try:
        from vnpy.event import EventEngine
        print("✅ vnpy可用，开始演示")
        asyncio.run(main())
    except ImportError:
        print("❌ vnpy不可用，请先安装vnpy")
        print("💡 安装命令: pip install vnpy")
        sys.exit(1) 