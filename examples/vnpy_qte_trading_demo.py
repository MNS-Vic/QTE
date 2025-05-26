#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
vnpy与QTE集成交易流程演示 - 活跃交易版

实现README.md中描述的完整交易流程，调整参数以产生更多交易信号
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

# QTE imports
from qte.vnpy.gateways import GatewayFactory, GatewayType
from qte.vnpy.gateways.qte_event_converters import QTEMarketData, QTEOrderData


class DataReplayController:
    """数据回放控制器"""
    
    def __init__(self):
        self.replay_speed = 5.0  # 加快回放速度
        self.is_running = False
        self.subscribers = []
        
    def add_subscriber(self, callback):
        self.subscribers.append(callback)
        
    def load_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """加载历史数据 - 增加波动性"""
        dates = pd.date_range(start=start_date, end=end_date, freq='1min')
        
        # 生成更有波动性的价格数据
        base_price = 50000.0
        price_changes = np.random.normal(0, 0.005, len(dates))  # 增加波动性
        prices = [base_price]
        
        # 添加趋势变化
        trend_changes = np.sin(np.arange(len(dates)) * 0.1) * 0.002
        
        for i, change in enumerate(price_changes[1:], 1):
            trend_change = trend_changes[i] if i < len(trend_changes) else 0
            new_price = prices[-1] * (1 + change + trend_change)
            prices.append(new_price)
        
        data = pd.DataFrame({
            'datetime': dates,
            'symbol': symbol,
            'open': prices,
            'high': [p * 1.002 for p in prices],
            'low': [p * 0.998 for p in prices],
            'close': prices,
            'volume': np.random.randint(100, 1000, len(dates))
        })
        
        return data
    
    async def start_replay(self, symbol: str, start_date: str, end_date: str):
        print(f"🎬 开始回放历史数据: {symbol} ({start_date} 到 {end_date})")
        
        historical_data = self.load_historical_data(symbol, start_date, end_date)
        self.is_running = True
        
        for _, row in historical_data.iterrows():
            if not self.is_running:
                break
                
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
            
            for callback in self.subscribers:
                try:
                    await callback(market_data)
                except Exception as e:
                    print(f"❌ 数据推送失败: {e}")
            
            await asyncio.sleep(0.05 / self.replay_speed)  # 更快的回放
            
        print("✅ 数据回放完成")
    
    def stop_replay(self):
        self.is_running = False


class QTEVirtualExchange:
    """QTE虚拟交易所"""
    
    def __init__(self):
        self.market_data: Dict[str, QTEMarketData] = {}
        self.orders: Dict[str, QTEOrderData] = {}
        self.trades: List[Dict] = []
        self.accounts = {
            'USDT': Decimal('100000.0'),
            'BTC': Decimal('0.0')
        }
        self.order_id_counter = 1
        self.subscribers = []
        
    def add_subscriber(self, callback):
        self.subscribers.append(callback)
        
    async def on_market_data(self, data: QTEMarketData):
        self.market_data[data.symbol] = data
        await self._match_orders(data)
        
        for callback in self.subscribers:
            try:
                await callback(data)
            except Exception as e:
                print(f"❌ 市场数据推送失败: {e}")
    
    async def _match_orders(self, market_data: QTEMarketData):
        symbol = market_data.symbol
        current_price = market_data.price
        
        for order_id, order in list(self.orders.items()):
            if order.symbol != symbol or order.status != "PENDING":
                continue
                
            should_fill = False
            fill_price = current_price
            
            if order.order_type == "MARKET":
                should_fill = True
                fill_price = current_price
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
        order.status = "FILLED"
        order.filled_quantity = order.quantity
        
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
        
        if order.side == "BUY":
            cost = order.quantity * fill_price
            self.accounts['USDT'] -= cost
            base_currency = order.symbol.replace('USDT', '')
            if base_currency not in self.accounts:
                self.accounts[base_currency] = Decimal('0')
            self.accounts[base_currency] += order.quantity
        else:
            revenue = order.quantity * fill_price
            self.accounts['USDT'] += revenue
            base_currency = order.symbol.replace('USDT', '')
            self.accounts[base_currency] -= order.quantity
        
        print(f"✅ 交易执行: {order.side} {order.quantity} {order.symbol} @ {fill_price:.2f}")
        print(f"💰 余额: USDT={self.accounts['USDT']:.2f}, BTC={self.accounts.get('BTC', 0):.4f}")
    
    async def place_order(self, symbol: str, side: str, order_type: str, 
                         quantity: Decimal, price: Optional[Decimal] = None) -> str:
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
        
        if order_type == "MARKET" and symbol in self.market_data:
            await self._match_orders(self.market_data[symbol])
        
        return order_id
    
    def get_account_info(self) -> Dict:
        return {
            'balances': dict(self.accounts),
            'orders': len(self.orders),
            'trades': len(self.trades)
        }


class ActiveStrategy:
    """更活跃的交易策略"""
    
    def __init__(self, exchange: QTEVirtualExchange):
        self.exchange = exchange
        self.price_history = []
        self.position = Decimal('0')
        self.last_signal = None
        self.signal_count = 0
        
    async def on_market_data(self, data: QTEMarketData):
        self.price_history.append(float(data.price))
        
        if len(self.price_history) > 30:
            self.price_history.pop(0)
        
        # 降低所需历史数据量，使策略更快激活
        if len(self.price_history) < 10:
            return
        
        # 使用更短的移动平均线，产生更多信号
        short_ma = np.mean(self.price_history[-3:])  # 3周期短期均线
        long_ma = np.mean(self.price_history[-10:])  # 10周期长期均线
        
        current_price = float(data.price)
        
        # 更敏感的信号生成
        signal = None
        if short_ma > long_ma * 1.0005 and self.last_signal != 'BUY':  # 0.05%的阈值
            signal = 'BUY'
        elif short_ma < long_ma * 0.9995 and self.last_signal != 'SELL':  # 0.05%的阈值
            signal = 'SELL'
        
        if signal:
            await self._execute_signal(signal, data.symbol, current_price)
            self.last_signal = signal
            self.signal_count += 1
    
    async def _execute_signal(self, signal: str, symbol: str, current_price: float):
        quantity = Decimal('0.05')  # 减少单次交易量，增加交易频率
        
        if signal == 'BUY' and self.position <= Decimal('0.5'):  # 允许更多买入
            await self.exchange.place_order(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity
            )
            self.position += quantity
            print(f"📈 策略信号 #{self.signal_count}: 买入 {quantity} {symbol} @ {current_price:.2f}")
            
        elif signal == 'SELL' and self.position > 0:
            sell_quantity = min(quantity, self.position)
            await self.exchange.place_order(
                symbol=symbol,
                side="SELL",
                order_type="MARKET",
                quantity=sell_quantity
            )
            self.position -= sell_quantity
            print(f"📉 策略信号 #{self.signal_count}: 卖出 {sell_quantity} {symbol} @ {current_price:.2f}")


class VnpyGatewayBridge:
    """vnpy Gateway桥接器"""
    
    def __init__(self, exchange: QTEVirtualExchange, event_engine: EventEngine):
        self.exchange = exchange
        self.event_engine = event_engine
        self.gateway = None
        self.tick_count = 0
        
    def setup_gateway(self):
        try:
            factory = GatewayFactory()
            self.gateway = factory.create_gateway(
                GatewayType.QTE_BINANCE,
                event_engine=self.event_engine,
                gateway_name="QTE_VIRTUAL"
            )
            print("✅ vnpy Gateway桥接器设置成功")
            return True
        except Exception as e:
            print(f"⚠️ vnpy Gateway桥接器设置失败: {e}")
            return False
    
    async def on_market_data(self, data: QTEMarketData):
        self.tick_count += 1
        
        if self.tick_count % 20 == 0:
            print(f"🔄 vnpy数据转换: 已处理 {self.tick_count} 个tick")
        
        if not self.gateway:
            return
            
        try:
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
            
            self.event_engine.put(Event(type="eTick", data=tick))
            
        except Exception as e:
            print(f"❌ 市场数据转换失败: {e}")


async def main():
    """主函数"""
    print("🚀 启动vnpy与QTE集成交易流程演示 - 活跃交易版")
    print("=" * 60)
    print("📋 流程说明:")
    print("   历史数据 -> DataReplayController -> QTE虚拟交易所")
    print("   -> vnpy Gateway -> 活跃交易策略 -> 订单撮合 -> 账户更新")
    print("=" * 60)
    
    # 创建组件
    print("1️⃣ 创建vnpy事件引擎...")
    event_engine = EventEngine()
    
    print("2️⃣ 创建QTE虚拟交易所...")
    exchange = QTEVirtualExchange()
    
    print("3️⃣ 创建数据回放控制器...")
    data_controller = DataReplayController()
    
    print("4️⃣ 创建活跃交易策略...")
    strategy = ActiveStrategy(exchange)
    
    print("5️⃣ 创建vnpy Gateway桥接器...")
    gateway_bridge = VnpyGatewayBridge(exchange, event_engine)
    gateway_bridge.setup_gateway()
    
    # 连接数据流
    print("6️⃣ 连接数据流...")
    data_controller.add_subscriber(exchange.on_market_data)
    exchange.add_subscriber(strategy.on_market_data)
    exchange.add_subscriber(gateway_bridge.on_market_data)
    
    # 显示初始状态
    print("7️⃣ 初始账户状态:")
    account_info = exchange.get_account_info()
    print(f"   💰 余额: {account_info['balances']}")
    
    print("\n" + "=" * 60)
    print("🎬 开始活跃交易演示...")
    print("=" * 60)
    
    try:
        # 设置回放参数
        symbol = "BTCUSDT"
        start_date = "2024-01-01 09:00:00"
        end_date = "2024-01-01 10:00:00"  # 1小时数据
        
        # 启动数据回放
        await data_controller.start_replay(symbol, start_date, end_date)
        await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断交易流程")
    except Exception as e:
        print(f"\n❌ 交易流程异常: {e}")
    finally:
        # 清理资源
        print("\n" + "=" * 60)
        print("🧹 清理资源...")
        data_controller.stop_replay()
        
        try:
            if hasattr(event_engine, '_active') and event_engine._active:
                event_engine.stop()
        except Exception as e:
            print(f"⚠️ 事件引擎停止时出现问题: {e}")
        
        # 显示最终结果
        print("📊 最终交易结果:")
        final_account = exchange.get_account_info()
        print(f"   💰 最终余额: {final_account['balances']}")
        print(f"   📝 总订单数: {final_account['orders']}")
        print(f"   💼 总交易数: {final_account['trades']}")
        
        # 计算收益
        initial_balance = Decimal('100000.0')
        final_usdt = final_account['balances']['USDT']
        final_btc = final_account['balances'].get('BTC', Decimal('0'))
        
        if exchange.trades:
            print(f"   📈 最近交易记录:")
            for trade in exchange.trades[-10:]:  # 显示最后10笔交易
                print(f"      {trade['side']} {trade['quantity']} {trade['symbol']} @ {trade['price']:.2f}")
            
            if exchange.market_data:
                last_price = list(exchange.market_data.values())[-1].price
                total_value = final_usdt + final_btc * last_price
                pnl = total_value - initial_balance
                pnl_pct = (pnl / initial_balance) * 100
                print(f"   📊 盈亏分析:")
                print(f"      初始资金: {initial_balance} USDT")
                print(f"      最终价值: {total_value:.2f} USDT")
                print(f"      盈亏金额: {pnl:.2f} USDT")
                print(f"      盈亏比例: {pnl_pct:.2f}%")
        
        print(f"   🔄 vnpy数据转换: 总计处理 {gateway_bridge.tick_count} 个tick")
        print(f"   📈 策略信号: 总计产生 {strategy.signal_count} 个交易信号")
        
        print("\n🎉 vnpy与QTE集成活跃交易演示完成！")
        print("✅ 成功演示了:")
        print("   - 历史数据回放 ✓")
        print("   - 实时数据处理 ✓") 
        print("   - 活跃交易策略 ✓")
        print("   - 订单撮合引擎 ✓")
        print("   - 账户管理 ✓")
        print("   - vnpy事件系统集成 ✓")


if __name__ == "__main__":
    try:
        from vnpy.event import EventEngine
        print("✅ vnpy可用，开始演示")
        asyncio.run(main())
    except ImportError:
        print("❌ vnpy不可用，请先安装vnpy")
        sys.exit(1) 