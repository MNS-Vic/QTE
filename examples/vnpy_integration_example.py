#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE vnpy集成完整示例

演示如何使用QTE的vnpy集成功能进行量化交易开发。
包括Gateway连接、订单管理、行情订阅、事件处理等完整流程。
"""

import time
import threading
from typing import Dict, List
from qte.vnpy import check_vnpy_availability, is_vnpy_available

# 检查vnpy可用性
if not is_vnpy_available():
    print("错误: vnpy不可用，请先安装: pip install vnpy")
    exit(1)

from vnpy.event import EventEngine, Event
from vnpy.trader.object import (
    TickData, OrderData, TradeData, AccountData, ContractData,
    OrderRequest, CancelRequest, SubscribeRequest
)
from vnpy.trader.constant import (
    Exchange, Product, Status, OrderType, Direction, Offset
)
from vnpy.trader.event import (
    EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, 
    EVENT_CONTRACT, EVENT_LOG
)
from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
from qte.vnpy.data_source import VnpyDataSource


class QTEVnpyTradingBot:
    """QTE vnpy交易机器人示例"""
    
    def __init__(self):
        """初始化交易机器人"""
        self.event_engine = EventEngine()
        self.gateway = None
        self.data_source = None
        
        # 交易状态
        self.connected = False
        self.contracts: Dict[str, ContractData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.positions: Dict[str, float] = {}
        self.account_balance = 0.0
        
        # 交易参数
        self.target_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        self.order_size = 0.001  # 每次交易数量
        self.price_threshold = 0.01  # 价格变动阈值
        
        print("QTE vnpy交易机器人初始化完成")

    def start(self):
        """启动交易机器人"""
        print("启动交易机器人...")
        
        # 启动事件引擎
        self.event_engine.start()
        print("事件引擎已启动")
        
        # 注册事件处理器
        self._register_event_handlers()
        print("事件处理器已注册")
        
        # 创建Gateway
        self.gateway = QTEBinanceSpotGateway(self.event_engine, "TRADING_BOT_GATEWAY")
        print("Gateway已创建")
        
        # 连接Gateway
        self._connect_gateway()
        
        # 创建数据源
        self.data_source = VnpyDataSource()
        data_source_connected = self.data_source.connect()
        print(f"数据源连接: {'成功' if data_source_connected else '失败'}")

    def stop(self):
        """停止交易机器人"""
        print("停止交易机器人...")
        
        if self.gateway:
            self.gateway.close()
            print("Gateway已关闭")
        
        self.event_engine.stop()
        print("事件引擎已停止")
        
        print("交易机器人已停止")

    def _register_event_handlers(self):
        """注册事件处理器"""
        self.event_engine.register(EVENT_TICK, self._on_tick)
        self.event_engine.register(EVENT_ORDER, self._on_order)
        self.event_engine.register(EVENT_TRADE, self._on_trade)
        self.event_engine.register(EVENT_ACCOUNT, self._on_account)
        self.event_engine.register(EVENT_CONTRACT, self._on_contract)
        self.event_engine.register(EVENT_LOG, self._on_log)

    def _connect_gateway(self):
        """连接Gateway"""
        setting = {
            "API密钥": "demo_api_key",
            "私钥": "demo_secret_key",
            "服务器": "QTE_MOCK",  # 使用QTE模拟交易所
            "代理地址": "",
            "代理端口": "0"
        }
        
        print("连接Gateway...")
        self.gateway.connect(setting)
        
        # 等待连接完成
        time.sleep(1.0)
        
        if self.gateway.connect_status:
            self.connected = True
            print("Gateway连接成功")
            
            # 订阅目标交易对行情
            self._subscribe_market_data()
        else:
            print("Gateway连接失败")

    def _subscribe_market_data(self):
        """订阅行情数据"""
        print("订阅行情数据...")
        
        for symbol in self.target_symbols:
            sub_req = SubscribeRequest(
                symbol=symbol,
                exchange=Exchange.OTC
            )
            self.gateway.subscribe(sub_req)
            print(f"已订阅 {symbol} 行情")

    def _on_tick(self, event: Event):
        """处理行情数据"""
        tick: TickData = event.data
        print(f"行情更新: {tick.symbol} 最新价: {tick.last_price}")
        
        # 简单的交易策略示例
        self._simple_trading_strategy(tick)

    def _on_order(self, event: Event):
        """处理订单更新"""
        order: OrderData = event.data
        self.orders[order.vt_orderid] = order
        
        print(f"订单更新: {order.vt_orderid} {order.symbol} "
              f"{order.direction.value} {order.volume}@{order.price} "
              f"状态: {order.status.value}")

    def _on_trade(self, event: Event):
        """处理成交回报"""
        trade: TradeData = event.data
        
        print(f"成交回报: {trade.vt_tradeid} {trade.symbol} "
              f"{trade.direction.value} {trade.volume}@{trade.price}")
        
        # 更新持仓
        if trade.symbol not in self.positions:
            self.positions[trade.symbol] = 0.0
        
        if trade.direction == Direction.LONG:
            self.positions[trade.symbol] += trade.volume
        else:
            self.positions[trade.symbol] -= trade.volume

    def _on_account(self, event: Event):
        """处理账户更新"""
        account: AccountData = event.data
        self.account_balance = account.balance
        
        print(f"账户更新: {account.accountid} 余额: {account.balance}")

    def _on_contract(self, event: Event):
        """处理合约信息"""
        contract: ContractData = event.data
        self.contracts[contract.vt_symbol] = contract
        
        print(f"合约信息: {contract.symbol} {contract.name}")

    def _on_log(self, event: Event):
        """处理日志信息"""
        log_data = event.data
        print(f"[LOG] {log_data}")

    def _simple_trading_strategy(self, tick: TickData):
        """简单的交易策略示例"""
        if not self.connected:
            return
        
        symbol = tick.symbol
        price = tick.last_price
        
        # 获取当前持仓
        current_position = self.positions.get(symbol, 0.0)
        
        # 简单策略：价格上涨买入，价格下跌卖出
        # 这里只是示例，实际策略会更复杂
        
        if current_position == 0.0:
            # 无持仓时，随机买入
            if hash(symbol) % 100 < 10:  # 10%概率买入
                self._place_order(symbol, Direction.LONG, self.order_size, price)
        
        elif current_position > 0.0:
            # 有多头持仓时，考虑卖出
            if hash(symbol + str(int(price))) % 100 < 5:  # 5%概率卖出
                self._place_order(symbol, Direction.SHORT, min(current_position, self.order_size), price)

    def _place_order(self, symbol: str, direction: Direction, volume: float, price: float):
        """下单"""
        order_req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.OTC,
            direction=direction,
            type=OrderType.LIMIT,
            volume=volume,
            price=price,
            offset=Offset.NONE,
            reference=f"bot_order_{int(time.time())}"
        )
        
        vt_orderid = self.gateway.send_order(order_req)
        print(f"下单: {vt_orderid} {symbol} {direction.value} {volume}@{price}")
        
        return vt_orderid

    def get_status(self) -> Dict:
        """获取机器人状态"""
        return {
            "connected": self.connected,
            "contracts_count": len(self.contracts),
            "orders_count": len(self.orders),
            "positions": self.positions.copy(),
            "account_balance": self.account_balance
        }

    def run_demo(self, duration: int = 30):
        """运行演示"""
        print(f"开始运行演示，持续 {duration} 秒...")
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # 定期查询账户
            if int(time.time()) % 10 == 0:
                self.gateway.query_account()
            
            # 显示状态
            if int(time.time()) % 5 == 0:
                status = self.get_status()
                print(f"状态: 连接={status['connected']}, "
                      f"合约={status['contracts_count']}, "
                      f"订单={status['orders_count']}, "
                      f"持仓={len(status['positions'])}")
            
            time.sleep(1)
        
        print("演示结束")


def main():
    """主函数"""
    print("=== QTE vnpy集成示例 ===")
    
    # 检查vnpy可用性
    available, info = check_vnpy_availability()
    print(f"vnpy可用性: {available}")
    print(f"vnpy版本: {info['version']}")
    print(f"可用组件: {info['available_components']}")
    
    if not available:
        print("vnpy不可用，退出演示")
        return
    
    # 创建交易机器人
    bot = QTEVnpyTradingBot()
    
    try:
        # 启动机器人
        bot.start()
        
        # 等待连接稳定
        time.sleep(2)
        
        # 运行演示
        bot.run_demo(duration=30)
        
    except KeyboardInterrupt:
        print("\n用户中断演示")
    
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
    
    finally:
        # 停止机器人
        bot.stop()
    
    print("演示完成")


if __name__ == "__main__":
    main()
