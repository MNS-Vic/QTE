from datetime import datetime, timezone
from typing import Dict, Optional, Any, List, Union # 添加了 Union
import math # 用于处理可能的NaN值和取整
import random # 用于生成 order_id
import pandas as pd

from qte.core.events import Event, FillEvent, MarketEvent, OrderEvent, SignalEvent, OrderType, OrderDirection, EventType
from qte.core.event_loop import EventLoop
from .interfaces import Portfolio, PositionData, PortfolioSnapshot
from qte.analysis.logger import app_logger
from .position import Position

class BasePortfolio(Portfolio):
    """
    一个基础的投资组合实现，处理信号、订单和成交事件，管理持仓和现金。
    """
    def __init__(self, 
                 initial_capital: float, 
                 event_loop: EventLoop, 
                 # 允许传入一个用于获取当前价格的DataProvider引用，以便在生成订单时估算成本
                 data_provider: Optional[Any] = None, # 避免循环导入，使用Any，实际应为DataProvider
                 default_order_size_pct: float = 0.02, # 默认使用当前资产组合价值的2%进行下单
                 fixed_order_quantity: Optional[float] = None # 或者使用固定数量下单
                 ):
        """
        初始化基础投资组合。

        参数:
            initial_capital (float): 初始资本。
            event_loop (EventLoop): 事件循环实例，用于发送订单事件。
            data_provider (Optional[DataProvider]): 数据提供者，用于获取当前价格以进行头寸调整。
            default_order_size_pct (float): 默认订单规模占总资产的百分比 (例如0.02代表2%)。
            fixed_order_quantity (Optional[float]): 如果提供，则使用固定的数量下单，忽略百分比。
        """
        super().__init__(initial_capital)
        self.event_loop = event_loop
        self.data_provider = data_provider 
        self.default_order_size_pct = default_order_size_pct
        self.fixed_order_quantity = fixed_order_quantity

        self.positions: Dict[str, PositionData] = {}
        # self.current_cash 继承自父类
        self.realized_pnl: float = 0.0
        self.unrealized_pnl: float = 0.0
        self.total_commission: float = 0.0
        
        # 投资组合历史记录
        self.portfolio_history: List[Dict[str, Any]] = []

        # 为订单生成注册处理器（如果Portfolio也需要监听OrderEvent自身的状态，例如被拒绝等）
        # self.event_loop.register_handler(EventType.ORDER, self.on_order_status_update)
        # 注册信号事件处理器
        self.event_loop.register_handler(EventType.SIGNAL, self.on_signal)
        
        # 记录初始状态
        self._record_portfolio_snapshot(datetime.now(timezone.utc))

        app_logger.info(f"基础投资组合已初始化，初始资金: {initial_capital:.2f}")

    def _calculate_current_total_equity(self, current_market_prices: Optional[Dict[str, float]] = None) -> float:
        """
        计算当前总权益 (现金 + 所有持仓的市场价值)。
        如果提供了 current_market_prices，则使用这些价格；否则，尝试从持仓数据中获取。
        """
        holdings_value = 0.0
        for symbol, position in self.positions.items():
            market_value = position.get('market_value', 0.0)
            if current_market_prices and symbol in current_market_prices:
                market_value = position.get('quantity', 0) * current_market_prices[symbol]
            holdings_value += market_value
        return self.current_cash + holdings_value
    
    def _record_portfolio_snapshot(self, timestamp: datetime) -> None:
        """记录当前投资组合状态到历史记录"""
        holdings_value = sum(position.get('market_value', 0.0) for position in self.positions.values())
        
        snapshot = {
            'timestamp': timestamp,
            'total_equity': self.current_cash + holdings_value,
            'cash': self.current_cash,
            'holdings_value': holdings_value,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'positions_count': len(self.positions)
        }
        
        self.portfolio_history.append(snapshot)

    def on_signal(self, event: SignalEvent) -> None:
        """
        处理来自策略的信号事件，并可能生成订单事件。
        采用目标仓位导向的逻辑。
        """
        app_logger.info(f"DEBUG PORTFOLIO (on_signal entry): For Signal {event.symbol} {event.signal_type}. Current self.positions snapshot: {self.positions}")
        
        current_position_qty = self.positions.get(event.symbol, {}).get('quantity', 0.0)
        app_logger.info(f"DEBUG PORTFOLIO (on_signal entry): For {event.symbol}, calculated current_position_qty = {current_position_qty}")

        app_logger.info(f"投资组合收到信号: {event.symbol} - {event.signal_type.upper()} at {event.timestamp}") 
        
        symbol = event.symbol
        signal_type = event.signal_type.upper()
        # event.direction (来自SignalEvent) 是整数: 1 for LONG, -1 for SHORT, 0 for FLAT/EXIT
        # event.strength 暂未使用

        # 1. 确定此信号建议的单次理想交易规模 (abs_trade_size)
        abs_suggested_trade_size = 0
        if self.fixed_order_quantity is not None:
            abs_suggested_trade_size = self.fixed_order_quantity
        elif self.data_provider:
            latest_price = None
            latest_bar = self.data_provider.get_latest_bar(symbol)
            if latest_bar:
                if 'close' in latest_bar and latest_bar['close'] > 0:
                    latest_price = latest_bar['close']
                elif 'last_price' in latest_bar and latest_bar['last_price'] > 0:
                    latest_price = latest_bar['last_price']
                elif 'price' in latest_bar and latest_bar['price'] > 0:
                    latest_price = latest_bar['price']
            
            if latest_price is not None and latest_price > 0:
                total_equity = self._calculate_current_total_equity({symbol: latest_price})
                target_value_for_trade = total_equity * self.default_order_size_pct
                abs_suggested_trade_size = math.floor(target_value_for_trade / latest_price)
            else:
                app_logger.warning(f"信号 {signal_type} ({symbol}): 无法获取最新价格计算订单规模，跳过信号。")
                return
        else:
            app_logger.warning(f"信号 {signal_type} ({symbol}): Portfolio 未配置 data_provider 且无固定数量，无法计算订单规模，跳过信号。")
            return
        
        if abs_suggested_trade_size <= 0:
            app_logger.info(f"信号 {signal_type} ({symbol}): 计算的建议交易规模为 {abs_suggested_trade_size}，不生成订单。")
            return

        # 2. 根据信号类型确定目标仓位 (target_position_qty)
        target_position_qty = current_position_qty # 默认目标是维持当前仓位，除非信号指示改变

        if signal_type == "LONG": # 信号希望建立或增加多头到 abs_suggested_trade_size
            target_position_qty = abs_suggested_trade_size
        elif signal_type == "SHORT": # 信号希望建立或增加空头到 -abs_suggested_trade_size
            target_position_qty = -abs_suggested_trade_size
        elif signal_type == "EXIT_LONG" or (signal_type == "FLAT" and current_position_qty > 0):
            # 如果是平多仓信号，或当前是多头时的FLAT信号，目标是0
            target_position_qty = 0
        elif signal_type == "EXIT_SHORT" or (signal_type == "FLAT" and current_position_qty < 0):
            # 如果是平空仓信号，或当前是空头时的FLAT信号，目标是0
            target_position_qty = 0
        elif signal_type == "FLAT" and current_position_qty == 0:
            app_logger.info(f"信号 FLAT ({symbol}): 当前无持仓，无需操作。")
            return # 已经是FLAT状态，无需操作
        else:
            app_logger.warning(f"投资组合收到未知或不适用的信号类型: {signal_type} ({symbol}) 对于当前仓位 {current_position_qty}。")
            return

        # 3. 计算实际需要下单的数量和方向以达到目标仓位
        order_qty_to_reach_target = target_position_qty - current_position_qty
        
        app_logger.info(f"DEBUG PORTFOLIO (on_signal): Symbol={symbol}, Signal={signal_type}, CurrQty={current_position_qty}, TargetQty={target_position_qty}, OrderToPlace={order_qty_to_reach_target}")

        if abs(order_qty_to_reach_target) < 1e-6: # 如果变化太小或为0，不操作
            app_logger.info(f"信号 {signal_type} ({symbol}): 目标仓位与当前仓位 ({current_position_qty}) 相同或调整量过小，无需操作。")
            return

        order_direction_enum = OrderDirection.BUY if order_qty_to_reach_target > 0 else OrderDirection.SELL
        final_order_abs_quantity = abs(order_qty_to_reach_target)

        # 创建订单
        order_to_send = OrderEvent(
            symbol=symbol,
            order_type=OrderType.MARKET, # 默认为市价单
            direction=order_direction_enum,
            quantity=final_order_abs_quantity,
            timestamp=event.timestamp,
            order_id=f"po_adj_{symbol}_{int(event.timestamp.timestamp()*1000)}_{random.randint(1000,9999)}"
        )
        app_logger.info(f"投资组合为信号 {signal_type} ({symbol}) 生成目标导向订单: {order_to_send.direction} {order_to_send.quantity} @ {order_to_send.order_type} ID: {order_to_send.order_id}")
        self.event_loop.put_event(order_to_send)
        
        # 记录投资组合快照
        self._record_portfolio_snapshot(event.timestamp)

    def on_fill(self, fill_event: FillEvent) -> None:
        """
        根据成交事件更新投资组合 (持仓、现金)。
        计算已实现盈亏。
        """
        app_logger.info(f"DEBUG PORTFOLIO (on_fill entry): Received FillEvent. Direction: {fill_event.direction}, OrderID: {fill_event.order_id}, Qty: {fill_event.quantity}, Price: {fill_event.fill_price}")

        symbol = fill_event.symbol
        fill_qty = fill_event.quantity
        fill_price = fill_event.fill_price
        commission = fill_event.commission
        
        direction_multiplier = fill_event.direction 
        app_logger.info(f"DEBUG PORTFOLIO (on_fill mid): direction_multiplier = {direction_multiplier} (from fill_event.direction = {fill_event.direction}) for OrderID: {fill_event.order_id}")

        self.current_cash -= (direction_multiplier * fill_qty * fill_price) + commission
        self.total_commission += commission

        # 更新持仓
        current_pos = self.positions.get(symbol)
        if not current_pos: # 新建仓位
            self.positions[symbol] = {
                "quantity": direction_multiplier * fill_qty,
                "avg_cost_price": fill_price,
                "market_value": direction_multiplier * fill_qty * fill_price, # 初始市值
                "unrealized_pnl": 0.0,
                "realized_pnl": -commission, # 初始已实现盈亏为佣金
                "last_known_price": fill_price
            }
        else: # 更新现有仓位
            current_qty = current_pos["quantity"]
            current_avg_cost = current_pos["avg_cost_price"]
            
            new_qty = current_qty + (direction_multiplier * fill_qty)

            if new_qty == 0: # 仓位被平掉
                realized_pnl_trade = (fill_price - current_avg_cost) * (-current_qty) - commission # 如果是卖出平多仓，-current_qty是正数
                                    # (current_avg_cost - fill_price) * current_qty - commission # 如果是买入平空仓，current_qty是负数
                if current_qty < 0 : # 平空仓
                    realized_pnl_trade = (current_avg_cost - fill_price) * abs(current_qty) - commission
                else: # 平多仓
                    realized_pnl_trade = (fill_price - current_avg_cost) * current_qty - commission
                
                self.realized_pnl += realized_pnl_trade
                current_pos["realized_pnl"] += realized_pnl_trade
                current_pos["quantity"] = 0
                current_pos["avg_cost_price"] = 0
                current_pos["market_value"] = 0
                current_pos["unrealized_pnl"] = 0
                current_pos["last_known_price"] = fill_price
            elif (current_qty > 0 and new_qty > 0) or (current_qty < 0 and new_qty < 0): # 加仓或减仓 (不改变仓位方向)
                if abs(new_qty) < abs(current_qty): # 减仓 (部分平仓)
                    # 计算平仓部分的已实现盈亏
                    closed_quantity = abs(current_qty) - abs(new_qty)
                    if current_qty > 0: # 减多头
                        realized_pnl_trade = (fill_price - current_avg_cost) * closed_quantity - commission
                    else: # 减空头
                        realized_pnl_trade = (current_avg_cost - fill_price) * closed_quantity - commission
                    
                    self.realized_pnl += realized_pnl_trade
                    current_pos["realized_pnl"] += realized_pnl_trade
                else: # 加仓
                    # 简化的加权平均成本计算
                    if current_qty > 0: # 加多头
                        current_pos["avg_cost_price"] = (current_qty * current_avg_cost + fill_qty * fill_price) / new_qty
                    else: # 加空头
                        current_pos["avg_cost_price"] = (current_qty * current_avg_cost - fill_qty * fill_price) / new_qty
                
                # 更新持仓
                current_pos["quantity"] = new_qty
                current_pos["market_value"] = new_qty * fill_price
                current_pos["unrealized_pnl"] = (fill_price - current_pos["avg_cost_price"]) * new_qty if new_qty > 0 else (current_pos["avg_cost_price"] - fill_price) * abs(new_qty)
                current_pos["last_known_price"] = fill_price
            else: # 反向交易 (多变空或空变多)
                # 先平仓，获取全部已实现盈亏
                if current_qty > 0: # 平多开空
                    realized_pnl_trade = (fill_price - current_avg_cost) * current_qty
                else: # 平空开多  
                    realized_pnl_trade = (current_avg_cost - fill_price) * abs(current_qty)
                
                # 佣金
                realized_pnl_trade -= commission
                
                # 更新总体盈亏
                self.realized_pnl += realized_pnl_trade
                current_pos["realized_pnl"] += realized_pnl_trade
                
                # 设置新仓位
                current_pos["quantity"] = new_qty
                current_pos["avg_cost_price"] = fill_price # 简化：新的反向仓位的平均成本就是当前成交价
                current_pos["market_value"] = new_qty * fill_price
                current_pos["unrealized_pnl"] = 0.0 # 刚开的新仓位，未实现盈亏为0
                current_pos["last_known_price"] = fill_price
        
        app_logger.info(f"DEBUG PORTFOLIO (on_fill before log): Logging with direction_multiplier = {direction_multiplier}, fill_qty = {fill_qty} for OrderID: {fill_event.order_id}")
        app_logger.info(f"成交处理完毕: {symbol}, 数量: {fill_qty} @ {fill_price:.2f}. 新现金: {self.current_cash:.2f}")
        app_logger.info(f"当前 {symbol} 持仓: {self.positions[symbol]}")
        app_logger.info(f"DEBUG PORTFOLIO (on_fill exit): self.positions AFTER update: {self.positions}")
        
        # 记录投资组合快照
        self._record_portfolio_snapshot(fill_event.timestamp)

    def on_market(self, market_event: MarketEvent) -> None:
        """
        根据市场事件更新持仓市值和未实现盈亏。
        """
        symbol = market_event.symbol
        close_price = market_event.close_price
        
        if symbol in self.positions:
            position = self.positions[symbol]
            quantity = position["quantity"]
            avg_cost = position["avg_cost_price"]
            
            # 更新市值和未实现盈亏
            position["market_value"] = quantity * close_price
            if quantity > 0:  # 多头
                position["unrealized_pnl"] = (close_price - avg_cost) * quantity
            elif quantity < 0:  # 空头
                position["unrealized_pnl"] = (avg_cost - close_price) * abs(quantity)
            
            position["last_known_price"] = close_price
            
            # 更新投资组合未实现盈亏 (总计所有持仓)
            self.unrealized_pnl = sum(pos.get("unrealized_pnl", 0.0) for pos in self.positions.values())
            
            # 记录投资组合快照
            self._record_portfolio_snapshot(market_event.timestamp)

    def get_current_positions(self) -> Dict[str, PositionData]:
        """获取当前持仓状态"""
        return self.positions

    def get_current_holdings_value(self, symbol: Optional[str] = None) -> float:
        """
        获取当前持仓市值。
        如果提供symbol，则返回该symbol的市值；否则返回所有持仓的总市值。
        """
        if symbol:
            return self.positions.get(symbol, {}).get("market_value", 0.0)
        else:
            return sum(position.get("market_value", 0.0) for position in self.positions.values())

    def get_portfolio_snapshot(self, current_market_prices: Optional[Dict[str, float]] = None) -> PortfolioSnapshot:
        """
        获取当前投资组合状态的快照。
        
        参数:
            current_market_prices: 可选的当前市场价格字典 {symbol: price}，用于更新市值计算
            
        返回:
            包含投资组合状态的字典
        """
        # 计算持仓总价值
        holdings_value = 0.0
        for symbol, position in self.positions.items():
            price = current_market_prices.get(symbol, position.get('last_known_price', 0.0)) if current_market_prices else position.get('market_value', 0.0) / position.get('quantity', 1.0) if position.get('quantity', 0.0) != 0 else 0.0
            qty = position.get('quantity', 0.0)
            holdings_value += qty * price
            
        # 更新未实现盈亏总额
        unrealized_pnl = sum(pos.get('unrealized_pnl', 0.0) for pos in self.positions.values())
        
        # 计算总权益
        total_equity = self.current_cash + holdings_value
        
        # 返回快照
        return {
            "timestamp": datetime.now(timezone.utc),
            "total_equity": total_equity,
            "cash": self.current_cash,
            "holdings_value": holdings_value,
            "positions": {symbol: dict(pos) for symbol, pos in self.positions.items()},
            "total_unrealized_pnl": unrealized_pnl,
            "total_realized_pnl": self.realized_pnl,
            "total_commission": self.total_commission
        }
    
    def get_portfolio_history(self) -> pd.DataFrame:
        """
        获取投资组合历史记录，返回一个DataFrame，包含投资组合随时间的状态变化
        
        返回:
            pd.DataFrame: 包含以下列的DataFrame:
                - timestamp: 记录时间
                - total_equity: 总权益
                - cash: 现金
                - holdings_value: 持仓市值
                - realized_pnl: 已实现盈亏
                - unrealized_pnl: 未实现盈亏
                - positions_count: 持仓数量
        """
        if not self.portfolio_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.portfolio_history)

    def get_available_cash(self) -> float:
        """获取当前可用现金"""
        return self.current_cash

    def print_summary(self) -> None:
        """打印投资组合的回测摘要。"""
        app_logger.info("\n--- 投资组合回测摘要 ---")
        # 在获取快照前，确保所有持仓的最新市值和未实现盈亏已基于最新数据更新
        # 如果data_provider可用，可以尝试获取所有持仓的最新价格并更新
        # 但在回测结束时，MarketEvents应该已经处理完毕，这里的snapshot应该反映最终状态
        final_snapshot = self.get_portfolio_snapshot()

        app_logger.info(f"初始资本: {self.initial_capital:,.2f}")
        app_logger.info(f"最终总权益: {final_snapshot['total_equity']:,.2f}")
        
        total_pnl = final_snapshot['total_pnl']
        return_pct = (total_pnl / self.initial_capital) * 100 if self.initial_capital != 0 else 0
        app_logger.info(f"总盈亏 (P&L): {total_pnl:,.2f} ({return_pct:.2f}%)")
        app_logger.info(f"  已实现盈亏: {final_snapshot['realized_pnl']:,.2f}")
        app_logger.info(f"  未实现盈亏: {final_snapshot['unrealized_pnl']:,.2f}")
        app_logger.info(f"总佣金支出: {final_snapshot['total_commission']:,.2f}")
        
        # TODO: 添加更多指标，如夏普比率、最大回撤、交易次数等。
        # 交易次数需要一种计数方式，例如统计开仓或平仓的次数。

        app_logger.info("\n最终持仓:")
        current_positions = final_snapshot.get("positions", {})
        if not current_positions or all(p.get("quantity", 0) == 0 for p in current_positions.values()):
            app_logger.info("  无持仓。")
        else:
            for symbol, pos_data in current_positions.items():
                if pos_data.get("quantity", 0) != 0: # 仅显示实际有数量的持仓
                    app_logger.info(
                        f"  {symbol}: "
                        f"数量={pos_data.get('quantity')}, "
                        f"均价={pos_data.get('avg_cost_price', 0):.2f}, "
                        f"市值={pos_data.get('market_value', 0):.2f}, "
                        f"未实现P&L={pos_data.get('unrealized_pnl', 0):.2f}"
                    )
        app_logger.info("--- 摘要结束 ---")

# 示例用法 (可以稍后移至测试或示例脚本)
if __name__ == '__main__':
    test_event_loop = EventLoop()
    
    # 模拟一个 DataProvider 来提供最新价格
    class MockDataProvider:
        def get_latest_bar(self, symbol: str) -> Optional[BarData]:
            if symbol == "AAPL":
                return {"datetime": datetime.utcnow(), "symbol": "AAPL", "open": 150, "high": 151, "low": 149, "close": 150.5, "volume": 1000}
            if symbol == "GOOG":
                return {"datetime": datetime.utcnow(), "symbol": "GOOG", "open": 2700, "high": 2701, "low": 2699, "close": 2700.5, "volume": 500}
            return None

    mock_dp = MockDataProvider()
    portfolio = BasePortfolio(initial_capital=100000.0, event_loop=test_event_loop, data_provider=mock_dp, default_order_size_pct=0.1)

    def order_handler(event: OrderEvent):
        app_logger.info(f"测试订单处理器收到订单: {event.symbol} {event.direction} {event.quantity} @ {event.order_type}")
        # 模拟成交
        fill_ts = event.timestamp + timedelta(seconds=1)
        if event.symbol == "AAPL":
            fill_price = 150.6 if event.direction == OrderDirection.BUY else 150.4
            commission = 1.0
        elif event.symbol == "GOOG":
            fill_price = 2701.0 if event.direction == OrderDirection.BUY else 2700.0
            commission = 1.5
        else:
            fill_price = 0
            commission = 0
        
        if fill_price > 0:
            fill = FillEvent(
                order_id=event.order_id or str(datetime.utcnow().timestamp()), # 模拟一个order_id
                symbol=event.symbol,
                timestamp=fill_ts,
                direction=event.direction,
                quantity=event.quantity,
                fill_price=fill_price,
                commission=commission
            )
            app_logger.info(f"模拟成交: {fill.symbol} {fill.direction} {fill.quantity} @ {fill.fill_price} (Comm: {fill.commission})")
            portfolio.on_fill(fill)
        else:
            app_logger.warning(f"无法为 {event.symbol} 模拟成交，价格为0。")

    test_event_loop.register_handler(EventType.ORDER, order_handler)

    app_logger.info("\n--- Portfolio 测试开始 ---")
    start_snapshot = portfolio.get_portfolio_snapshot()
    app_logger.info(f"初始 Portfolio 快照: {start_snapshot}")

    # 1. 模拟买入 AAPL 的信号
    app_logger.info("\n1. 模拟买入 AAPL 的信号")
    signal_buy_aapl = SignalEvent(symbol="AAPL", signal_type="LONG", timestamp=datetime.utcnow())
    portfolio.on_signal(signal_buy_aapl) # 直接调用on_signal, 因为它已经注册为处理器
    # test_event_loop.add_event(signal_buy_aapl) # 或者通过事件循环添加，让循环处理
    # 模拟处理事件 (在实际系统中会由事件循环驱动)
    # while test_event_loop.event_queue:
    #     evt = test_event_loop.event_queue.popleft()
    #     if isinstance(evt, OrderEvent): order_handler(evt)
    #     # if isinstance(evt, SignalEvent): portfolio.on_signal(evt) # 如果没注册on_signal为处理器

    snapshot_after_aapl_buy = portfolio.get_portfolio_snapshot({"AAPL": 151.0}) # 提供市价更新
    app_logger.info(f"买入 AAPL 后 Portfolio 快照 (市价151.0): {snapshot_after_aapl_buy}")
    assert snapshot_after_aapl_buy["positions"]["AAPL"]["quantity"] > 0
    assert snapshot_after_aapl_buy["current_cash"] < initial_capital

    # 2. 模拟市场价格上涨
    app_logger.info("\n2. 模拟 AAPL 市场价格上涨")
    market_update_aapl_up = MarketEvent(symbol="AAPL", timestamp=datetime.utcnow(), close_price=155.0, open_price=151, high_price=156, low_price=151, volume=0)
    portfolio.on_market(market_update_aapl_up)
    snapshot_aapl_up = portfolio.get_portfolio_snapshot()
    app_logger.info(f"AAPL 价格上涨后 Portfolio 快照: {snapshot_aapl_up}")
    assert snapshot_aapl_up["positions"]["AAPL"]["unrealized_pnl"] > 0

    # 3. 模拟卖出 GOOG 的信号 (假设允许裸空)
    app_logger.info("\n3. 模拟卖出 GOOG 的信号 (裸空)")
    signal_sell_goog = SignalEvent(symbol="GOOG", signal_type="SHORT", timestamp=datetime.utcnow())
    portfolio.on_signal(signal_sell_goog)
    snapshot_after_goog_sell = portfolio.get_portfolio_snapshot({"AAPL": 155.0, "GOOG": 2690.0})
    app_logger.info(f"卖出 GOOG 后 Portfolio 快照 (市价 GOOG:2690): {snapshot_after_goog_sell}")
    assert snapshot_after_goog_sell["positions"]["GOOG"]["quantity"] < 0

    # 4. 模拟平掉 AAPL 的多头仓位
    app_logger.info("\n4. 模拟平掉 AAPL 的多头仓位")
    signal_exit_aapl = SignalEvent(symbol="AAPL", signal_type="EXIT_LONG", timestamp=datetime.utcnow())
    portfolio.on_signal(signal_exit_aapl)
    snapshot_after_aapl_exit = portfolio.get_portfolio_snapshot({"GOOG": 2690.0})
    app_logger.info(f"平掉 AAPL 多头仓位后 Portfolio 快照: {snapshot_after_aapl_exit}")
    assert "AAPL" not in snapshot_after_aapl_exit["positions"] or snapshot_after_aapl_exit["positions"]["AAPL"]["quantity"] == 0
    assert snapshot_after_aapl_exit["realized_pnl"] != start_snapshot["realized_pnl"]

    # 5. 模拟买入平掉 GOOG 的空头仓位
    app_logger.info("\n5. 模拟买入平掉 GOOG 的空头仓位")
    signal_exit_goog = SignalEvent(symbol="GOOG", signal_type="EXIT_SHORT", timestamp=datetime.utcnow())
    portfolio.on_signal(signal_exit_goog)
    snapshot_after_goog_exit = portfolio.get_portfolio_snapshot()
    app_logger.info(f"平掉 GOOG 空头仓位后 Portfolio 快照: {snapshot_after_goog_exit}")
    assert "GOOG" not in snapshot_after_goog_exit["positions"] or snapshot_after_goog_exit["positions"]["GOOG"]["quantity"] == 0

    app_logger.info("\n--- Portfolio 测试结束 ---") 