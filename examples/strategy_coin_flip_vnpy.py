#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抛硬币交易策略 - vnpy集成版本

策略逻辑：
1. 通过vnpy Gateway从QTE虚拟交易所获取实时价格
2. 随机50%概率做多或做空  
3. 达到3%回撤时平仓（加密货币合理止损）
4. 通过vnpy Gateway向虚拟交易所发送订单

正确的架构：外部数据源 → QTE虚拟交易所 → vnpy Gateway → Strategy
"""

import sys
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# QTE和vnpy相关导入
from qte.vnpy import check_vnpy_availability
from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.event import EventEngine, Event
    from vnpy.trader.object import (
        TickData, OrderData, TradeData, AccountData, ContractData,
        OrderRequest, CancelRequest, SubscribeRequest
    )
    from vnpy.trader.constant import Exchange, OrderType, Direction, Status
    from vnpy.trader.event import (
        EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT, EVENT_CONTRACT
    )
else:
    print("❌ vnpy不可用，无法运行策略")
    sys.exit(1)

@dataclass 
class Position:
    """策略持仓信息"""
    symbol: str
    direction: Direction  # Direction.LONG 或 Direction.SHORT
    volume: float
    entry_price: float
    entry_time: datetime
    vnpy_order_id: str = ""  # vnpy订单ID
    unrealized_pnl: float = 0.0
    
    def update_pnl(self, current_price: float):
        """更新未实现盈亏"""
        if self.direction == Direction.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.volume
        else:  # Direction.SHORT
            self.unrealized_pnl = (self.entry_price - current_price) * self.volume

@dataclass
class StrategyTrade:
    """策略交易记录"""
    symbol: str
    direction: Direction
    volume: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    drawdown_pct: float

class CoinFlipVnpyStrategy:
    """抛硬币交易策略 - vnpy版本"""
    
    def __init__(self, 
                 symbols: List[str] = None,
                 initial_capital: float = 100000.0,
                 position_size: float = 0.1,  # 10%仓位
                 drawdown_threshold: float = 0.03,  # 3%回撤平仓
                 gateway_name: str = "QTE_BINANCE_SPOT",
                 virtual_exchange_host: str = "localhost:5001"):
        """
        初始化策略
        
        Args:
            symbols: 交易标的列表
            initial_capital: 初始资金
            position_size: 单次开仓仓位比例
            drawdown_threshold: 回撤阈值
            gateway_name: vnpy网关名称
            virtual_exchange_host: 虚拟交易所地址
        """
        if symbols is None:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_size = position_size
        self.drawdown_threshold = drawdown_threshold
        self.gateway_name = gateway_name
        self.virtual_exchange_host = virtual_exchange_host
        
        # 策略状态
        self.positions: Dict[str, Position] = {}
        self.trades: List[StrategyTrade] = []
        self.last_prices: Dict[str, float] = {}
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}
        
        # vnpy组件
        self.event_engine: Optional[EventEngine] = None
        self.gateway: Optional[QTEBinanceSpotGateway] = None
        self.running = False
        
        # 交易控制
        self.order_count = 0
        self.pending_orders: Dict[str, str] = {}  # vnpy_order_id -> symbol
        self.last_trade_time: Dict[str, datetime] = {}  # 防止过于频繁交易
        self.min_trade_interval = 60  # 最小交易间隔（秒）
        
        # 随机种子
        random.seed(42)
        
        print(f"🎲 抛硬币策略初始化（vnpy版本）")
        print(f"   交易标的: {self.symbols}")
        print(f"   初始资金: {self.initial_capital:,.2f}")
        print(f"   仓位大小: {self.position_size:.1%}")
        print(f"   回撤阈值: {self.drawdown_threshold:.1%}")
        print(f"   虚拟交易所: {self.virtual_exchange_host}")
    
    def init_vnpy(self):
        """初始化vnpy组件"""
        print("🔧 初始化vnpy组件...")
        
        # 创建事件引擎
        self.event_engine = EventEngine()
        
        # 创建网关
        self.gateway = QTEBinanceSpotGateway(self.event_engine, self.gateway_name)
        
        # 注册事件处理器
        self._register_event_handlers()
        
        # 连接虚拟交易所
        gateway_setting = {
            "API密钥": "demo_api_key",  # 虚拟交易所的演示密钥
            "私钥": "demo_secret_key",
            "服务器": "QTE_MOCK",  # 连接QTE虚拟交易所
            "代理地址": "",
            "代理端口": 0,
        }
        
        print(f"🔗 连接虚拟交易所: {self.virtual_exchange_host}")
        self.gateway.connect(gateway_setting)
        
        # 等待连接建立
        time.sleep(2)
        
        # 订阅行情
        for symbol in self.symbols:
            req = SubscribeRequest(
                symbol=symbol,
                exchange=Exchange.OTC  # 使用OTC交易所
            )
            self.gateway.subscribe(req)
            print(f"📊 订阅行情: {symbol}")
        
        print("✅ vnpy组件初始化完成")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        self.event_engine.register(EVENT_TICK, self._on_tick)
        self.event_engine.register(EVENT_ORDER, self._on_order)
        self.event_engine.register(EVENT_TRADE, self._on_trade)
        self.event_engine.register(EVENT_ACCOUNT, self._on_account)
        self.event_engine.register(EVENT_CONTRACT, self._on_contract)
    
    def _on_tick(self, event: Event):
        """处理行情事件"""
        tick: TickData = event.data
        symbol = tick.symbol
        price = tick.last_price
        
        # 更新最新价格
        self.last_prices[symbol] = price
        
        # 更新持仓盈亏
        if symbol in self.positions:
            position = self.positions[symbol]
            position.update_pnl(price)
            
            # 检查是否需要平仓
            if self._should_close_position(position, price):
                self._close_position(position, price)
        
        # 检查是否需要开仓
        elif self._should_open_position(symbol):
            self._try_open_position(symbol, price)
    
    def _on_order(self, event: Event):
        """处理订单事件"""
        order: OrderData = event.data
        print(f"📋 订单更新: {order.symbol} {order.direction.value} {order.volume} @ {order.price} 状态: {order.status.value}")
        
        # 如果订单被拒绝，清理pending状态
        if order.status in [Status.REJECTED, Status.CANCELLED]:
            if order.orderid in self.pending_orders:
                del self.pending_orders[order.orderid]
    
    def _on_trade(self, event: Event):
        """处理成交事件"""
        trade: TradeData = event.data
        symbol = trade.symbol
        
        print(f"✅ 成交: {symbol} {trade.direction.value} {trade.volume} @ {trade.price}")
        
        # 更新持仓信息
        if symbol in self.positions:
            # 平仓成交
            position = self.positions[symbol]
            if ((position.direction == Direction.LONG and trade.direction == Direction.SHORT) or 
                (position.direction == Direction.SHORT and trade.direction == Direction.LONG)):
                
                # 计算盈亏
                pnl = position.unrealized_pnl
                self.current_capital += pnl
                
                # 记录交易
                strategy_trade = StrategyTrade(
                    symbol=symbol,
                    direction=position.direction,
                    volume=position.volume,
                    entry_price=position.entry_price,
                    exit_price=trade.price,
                    entry_time=position.entry_time,
                    exit_time=datetime.now(),
                    pnl=pnl,
                    drawdown_pct=abs(trade.price - position.entry_price) / position.entry_price
                )
                self.trades.append(strategy_trade)
                
                print(f"📉 平仓完成: {symbol} 盈亏: {pnl:+.2f}")
                del self.positions[symbol]
        else:
            # 开仓成交
            position = Position(
                symbol=symbol,
                direction=trade.direction,
                volume=trade.volume,
                entry_price=trade.price,
                entry_time=datetime.now(),
                vnpy_order_id=trade.orderid
            )
            self.positions[symbol] = position
            print(f"📈 开仓完成: {symbol} {trade.direction.value} {trade.volume} @ {trade.price}")
        
        # 清理pending状态
        if trade.orderid in self.pending_orders:
            del self.pending_orders[trade.orderid]
    
    def _on_account(self, event: Event):
        """处理账户事件"""
        account: AccountData = event.data
        self.accounts[account.accountid] = account
        # print(f"💰 账户更新: {account.accountid} 余额: {account.balance}")
    
    def _on_contract(self, event: Event):
        """处理合约事件"""
        contract: ContractData = event.data
        self.contracts[contract.symbol] = contract
        print(f"📄 合约信息: {contract.symbol}")
    
    def flip_coin(self) -> Direction:
        """抛硬币决定交易方向"""
        return Direction.LONG if random.random() > 0.5 else Direction.SHORT
    
    def _should_open_position(self, symbol: str) -> bool:
        """判断是否应该开仓"""
        # 如果已有持仓，不再开仓
        if symbol in self.positions:
            return False
        
        # 如果有pending订单，不开仓
        for order_id, pending_symbol in self.pending_orders.items():
            if pending_symbol == symbol:
                return False
        
        # 检查交易间隔
        if symbol in self.last_trade_time:
            time_diff = (datetime.now() - self.last_trade_time[symbol]).seconds
            if time_diff < self.min_trade_interval:
                return False
        
        # 简单策略：随机开仓（可以加入更多条件）
        return random.random() > 0.7  # 30%概率开仓，避免过于频繁
    
    def _should_close_position(self, position: Position, current_price: float) -> bool:
        """判断是否应该平仓"""
        # 计算回撤比例
        if position.direction == Direction.LONG:
            drawdown = (position.entry_price - current_price) / position.entry_price
        else:  # SHORT
            drawdown = (current_price - position.entry_price) / position.entry_price
        
        # 如果回撤超过阈值，平仓
        return drawdown >= self.drawdown_threshold
    
    def _try_open_position(self, symbol: str, price: float):
        """尝试开仓"""
        try:
            direction = self.flip_coin()
            
            # 计算仓位大小
            position_value = self.current_capital * self.position_size
            volume = position_value / price
            
            # 创建订单请求
            req = OrderRequest(
                symbol=symbol,
                exchange=Exchange.OTC,
                direction=direction,
                type=OrderType.MARKET,  # 市价单
                volume=volume,
                price=price,  # 市价单价格可以为0，但这里提供参考价格
                reference=f"coinflip_{self.order_count}"
            )
            
            # 发送订单
            order_id = self.gateway.send_order(req)
            if order_id:
                self.pending_orders[order_id] = symbol
                self.last_trade_time[symbol] = datetime.now()
                self.order_count += 1
                print(f"📤 发送开仓订单: {symbol} {direction.value} {volume:.4f} @ {price:.2f}")
            else:
                print(f"❌ 开仓订单发送失败: {symbol}")
                
        except Exception as e:
            print(f"❌ 开仓失败: {e}")
    
    def _close_position(self, position: Position, price: float):
        """平仓"""
        try:
            # 平仓方向与持仓方向相反
            close_direction = Direction.SHORT if position.direction == Direction.LONG else Direction.LONG
            
            # 创建平仓订单
            req = OrderRequest(
                symbol=position.symbol,
                exchange=Exchange.OTC,
                direction=close_direction,
                type=OrderType.MARKET,
                volume=position.volume,
                price=price,
                reference=f"coinflip_close_{self.order_count}"
            )
            
            # 发送订单
            order_id = self.gateway.send_order(req)
            if order_id:
                self.pending_orders[order_id] = position.symbol
                self.order_count += 1
                print(f"📤 发送平仓订单: {position.symbol} {close_direction.value} {position.volume:.4f} @ {price:.2f}")
            else:
                print(f"❌ 平仓订单发送失败: {position.symbol}")
                
        except Exception as e:
            print(f"❌ 平仓失败: {e}")
    
    def start(self):
        """启动策略"""
        print("🚀 启动抛硬币策略...")
        
        # 初始化vnpy
        self.init_vnpy()
        
        # 启动事件引擎
        self.event_engine.start()
        self.running = True
        
        print("✅ 策略已启动，开始监控市场...")
        print("📊 实时状态更新:")
        print("-" * 60)
        
        try:
            # 定期打印状态
            while self.running:
                time.sleep(10)  # 每10秒打印一次状态
                self._print_status()
                
        except KeyboardInterrupt:
            print("\\n🛑 收到中断信号，正在停止策略...")
            self.stop()
    
    def stop(self):
        """停止策略"""
        self.running = False
        
        # 平掉所有持仓
        for symbol, position in list(self.positions.items()):
            if symbol in self.last_prices:
                self._close_position(position, self.last_prices[symbol])
        
        # 等待所有订单处理完成
        time.sleep(3)
        
        # 停止vnpy组件
        if self.gateway:
            self.gateway.close()
        if self.event_engine:
            self.event_engine.stop()
        
        print("✅ 策略已停止")
        self._print_final_results()
    
    def _print_status(self):
        """打印实时状态"""
        print(f"\\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 当前资金: {self.current_capital:,.2f}")
        print(f"📊 最新价格: {', '.join([f'{s}:{p:.2f}' for s, p in self.last_prices.items()])}")
        print(f"📈 持仓数量: {len(self.positions)}")
        
        for symbol, position in self.positions.items():
            if symbol in self.last_prices:
                position.update_pnl(self.last_prices[symbol])
                print(f"   {symbol}: {position.direction.value} {position.volume:.4f} @ {position.entry_price:.2f} PnL: {position.unrealized_pnl:+.2f}")
        
        print(f"📋 总交易数: {len(self.trades)}")
        if self.trades:
            winning_trades = len([t for t in self.trades if t.pnl > 0])
            win_rate = winning_trades / len(self.trades)
            print(f"🎯 胜率: {win_rate:.1%}")
    
    def _print_final_results(self):
        """打印最终结果"""
        print("\\n" + "=" * 60)
        print("📊 策略运行结果")
        print("=" * 60)
        
        total_trades = len(self.trades)
        if total_trades == 0:
            print("❌ 无交易记录")
            return
        
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades
        
        total_pnl = sum(t.pnl for t in self.trades)
        avg_win = sum(t.pnl for t in self.trades if t.pnl > 0) / max(winning_trades, 1)
        avg_loss = sum(t.pnl for t in self.trades if t.pnl < 0) / max(losing_trades, 1)
        
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        
        print(f"💰 最终资金: {self.current_capital:,.2f}")
        print(f"📈 总收益: {total_pnl:+,.2f}")
        print(f"📊 总收益率: {total_return:+.2%}")
        print(f"🎯 总交易次数: {total_trades}")
        print(f"✅ 盈利交易: {winning_trades} ({win_rate:.1%})")
        print(f"❌ 亏损交易: {losing_trades}")
        
        if winning_trades > 0:
            print(f"💚 平均盈利: {avg_win:+.2f}")
        if losing_trades > 0:
            print(f"💔 平均亏损: {avg_loss:+.2f}")
        
        # 显示最近交易
        if self.trades:
            print(f"\\n📋 最近 {min(5, len(self.trades))} 笔交易:")
            for trade in self.trades[-5:]:
                print(f"   {trade.symbol} {trade.direction.value} {trade.pnl:+.2f} "
                      f"({trade.entry_time.strftime('%H:%M:%S')} -> {trade.exit_time.strftime('%H:%M:%S')})")

def main():
    """主函数"""
    print("🎲 抛硬币交易策略演示（vnpy集成版本）")
    print("=" * 60)
    
    # 检查vnpy可用性
    if not VNPY_AVAILABLE:
        print(f"❌ vnpy不可用: {VNPY_INFO}")
        return
    
    # 创建策略实例
    strategy = CoinFlipVnpyStrategy(
        symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
        initial_capital=100000.0,
        position_size=0.1,  # 10%仓位
        drawdown_threshold=0.03,  # 3%回撤
        gateway_name="QTE_BINANCE_SPOT",
        virtual_exchange_host="localhost:5001"
    )
    
    try:
        # 启动策略（会一直运行直到按Ctrl+C）
        strategy.start()
    except KeyboardInterrupt:
        print("\\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 策略运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        strategy.stop()

if __name__ == "__main__":
    main() 