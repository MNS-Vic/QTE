from datetime import datetime
from typing import Dict, Optional, Any, List, Union # 添加了 Union
import math # 用于处理可能的NaN值和取整

from qte_core.events import Event, FillEvent, MarketEvent, OrderEvent, SignalEvent, OrderType, OrderDirection, EventType
from qte_core.event_loop import EventLoop
from qte_portfolio_risk.interfaces import Portfolio, PositionData, PortfolioSnapshot
from qte_analysis_reporting.logger import app_logger

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

        # 为订单生成注册处理器（如果Portfolio也需要监听OrderEvent自身的状态，例如被拒绝等）
        # self.event_loop.register_handler(EventType.ORDER, self.on_order_status_update)
        # 注册信号事件处理器
        self.event_loop.register_handler(EventType.SIGNAL, self.on_signal)

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

    def on_signal(self, event: SignalEvent) -> None:
        """
        处理来自策略的信号事件，并可能生成订单事件。
        """
        app_logger.info(f"投资组合收到信号: {event.symbol} - {event.signal_type} at {event.timestamp}")
        
        # 简单的头寸管理逻辑
        symbol = event.symbol
        signal_type = event.signal_type.upper()
        # strength = event.strength # strength 暂未使用，但可以用于调整订单大小或优先级

        current_position_qty = self.positions.get(symbol, {}).get('quantity', 0.0)
        order_quantity = 0
        order_direction = None
        order_type = OrderType.MARKET # 默认为市价单

        # 确定订单数量
        if self.fixed_order_quantity is not None:
            order_quantity = self.fixed_order_quantity
        elif self.data_provider:
            latest_price = None
            latest_bar = self.data_provider.get_latest_bar(symbol)
            
            if latest_bar:
                # 尝试从多个可能的价格字段获取价格，以增强兼容性
                if 'close' in latest_bar and latest_bar['close'] > 0:
                    latest_price = latest_bar['close']
                elif 'last_price' in latest_bar and latest_bar['last_price'] > 0:
                    latest_price = latest_bar['last_price']
                elif 'price' in latest_bar and latest_bar['price'] > 0:
                    latest_price = latest_bar['price']
            
            # 如果通过尝试不同字段名仍然无法获取价格，则尝试从市场事件中获取
            if latest_price is None:
                # 从最近的市场事件中查找价格
                for event in reversed(self.event_loop.events):
                    if event.type == EventType.MARKET and event.symbol == symbol:
                        # 尝试从市场事件中获取价格
                        if hasattr(event, 'price') and event.price is not None and event.price > 0:
                            latest_price = event.price
                            break
                        elif hasattr(event, 'close_price') and event.close_price is not None and event.close_price > 0:
                            latest_price = event.close_price
                            break
                        elif hasattr(event, 'last_price') and event.last_price is not None and event.last_price > 0:
                            latest_price = event.last_price
                            break
            
            if latest_price is not None and latest_price > 0:
                total_equity = self._calculate_current_total_equity({symbol: latest_price})
                target_value = total_equity * self.default_order_size_pct
                order_quantity = math.floor(target_value / latest_price) # 向下取整确保不超过预算
            else:
                app_logger.warning(f"无法为合约 {symbol} 获取最新价格以计算订单数量，跳过信号。")
                return
        else:
            app_logger.warning(f"投资组合中未配置 data_provider，无法按百分比计算订单数量。请使用固定数量。跳过信号 '{symbol}'。")
            return
        
        if order_quantity <= 0:
            app_logger.info(f"计算得到的订单数量为 {order_quantity}，不生成订单。")
            return

        if signal_type == "LONG":
            if current_position_qty < 0: # 如果有空头仓位，先平掉
                app_logger.info(f"信号 LONG ({symbol}): 检测到空头仓位 {current_position_qty}，先平仓。")
                cover_order = OrderEvent(
                    symbol=symbol,
                    order_type=order_type,
                    direction=OrderDirection.BUY,
                    quantity=abs(current_position_qty),
                    timestamp=event.timestamp
                )
                self.event_loop.add_event(cover_order)
            # 再开多仓 (或增加多仓)
            # 为简单起见，这里假设如果已有部分多仓，我们仍然会下全部计算出的order_quantity
            # 更复杂的逻辑可以考虑只增加到目标仓位
            order_direction = OrderDirection.BUY
        elif signal_type == "SHORT":
            if current_position_qty > 0: # 如果有多头仓位，先平掉
                app_logger.info(f"信号 SHORT ({symbol}): 检测到多头仓位 {current_position_qty}，先平仓。")
                sell_order = OrderEvent(
                    symbol=symbol,
                    order_type=order_type,
                    direction=OrderDirection.SELL,
                    quantity=abs(current_position_qty),
                    timestamp=event.timestamp
                )
                self.event_loop.add_event(sell_order)
            # 再开空仓 (或增加空仓)
            order_direction = OrderDirection.SELL
        elif signal_type == "EXIT_LONG" or signal_type == "FLAT":
            if current_position_qty > 0:
                order_direction = OrderDirection.SELL
                order_quantity = current_position_qty # 平掉所有多头仓位
            else:
                app_logger.info(f"信号 EXIT_LONG/FLAT ({symbol}): 当前无多头仓位，不操作。")
                return
        elif signal_type == "EXIT_SHORT":
            if current_position_qty < 0:
                order_direction = OrderDirection.BUY
                order_quantity = abs(current_position_qty) # 平掉所有空头仓位
            else:
                app_logger.info(f"信号 EXIT_SHORT ({symbol}): 当前无空头仓位，不操作。")
                return
        else:
            app_logger.warning(f"投资组合收到未知信号类型: {signal_type} 为合约 {symbol}。")
            return

        if order_direction and order_quantity > 0:
            new_order = OrderEvent(
                symbol=symbol,
                order_type=order_type,
                direction=order_direction,
                quantity=order_quantity,
                timestamp=event.timestamp # 使用信号事件的时间戳
            )
            app_logger.info(f"投资组合为信号 {signal_type} ({symbol}) 生成订单: {new_order.direction} {new_order.quantity} @ MKT")
            self.event_loop.add_event(new_order)
        elif order_direction and order_quantity <= 0:
             app_logger.info(f"信号 {signal_type} ({symbol}): 计算的平仓数量为0或负数，不生成订单。当前持仓: {current_position_qty}")

    def update_on_fill(self, fill_event: FillEvent) -> None:
        """
        根据成交事件更新投资组合 (持仓、现金)。
        计算已实现盈亏。
        """
        symbol = fill_event.symbol
        fill_qty = fill_event.quantity
        fill_price = fill_event.fill_price
        commission = fill_event.commission
        direction_multiplier = 1 if fill_event.direction == OrderDirection.BUY else -1

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
                "realized_pnl": -commission # 初始已实现盈亏为佣金
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
                # del self.positions[symbol] # 从字典中移除已平仓位，或者标记为0
                current_pos["quantity"] = 0
                current_pos["avg_cost_price"] = 0 # 或 None
                current_pos["market_value"] = 0
                current_pos["unrealized_pnl"] = 0
            elif new_qty * current_qty >= 0: # 同方向加仓
                new_avg_cost = ((current_avg_cost * current_qty) + 
                                (direction_multiplier * fill_qty * fill_price)) / new_qty
                if direction_multiplier < 0 and current_qty < 0 : # 加空仓
                     new_avg_cost = ((current_avg_cost * abs(current_qty)) + 
                                (fill_qty * fill_price)) / abs(new_qty)
                elif direction_multiplier > 0 and current_qty > 0: # 加多仓
                    new_avg_cost = ((current_avg_cost * current_qty) + 
                                (fill_qty * fill_price)) / new_qty
                else: # 开新仓（理论上在 not current_pos 分支处理了，这里可以是错误或特殊情况）
                    app_logger.warning(f"异常持仓更新逻辑 for {symbol}")
                    new_avg_cost = fill_price

                current_pos["quantity"] = new_qty
                current_pos["avg_cost_price"] = new_avg_cost
                current_pos["realized_pnl"] -= commission # 佣金计入已实现P&L
                self.realized_pnl -= commission
            else: # 反向开仓，意味着部分平仓并可能反向开新仓 (简化处理：先平后开)
                  # 这个基础版本在on_signal中做了简化，会先发平仓单
                  # 这里假设fill是针对一个方向的，不会一个fill同时平仓又反向开仓
                app_logger.warning(f"成交事件 {fill_event.order_id} 导致合约 {symbol} 反向开仓，但基础投资组合的信号逻辑应先平仓。请检查流程。")
                # 为简化，我们只更新数量和成本，实际已实现盈亏计算会更复杂
                # 此场景下，应该认为旧仓位已平，产生已实现盈亏，然后新开仓
                # 暂时按加权平均处理，但这不完全准确反映部分平仓的P&L
                # 正确做法是在成交回报时明确是开仓还是平仓
                old_realized_pnl = (fill_price - current_avg_cost) * (-current_qty) # 假设全部旧仓位按此成交价平掉的P&L (不含佣金)
                if current_qty < 0: # 平空
                    old_realized_pnl = (current_avg_cost - fill_price) * abs(current_qty)
                else: # 平多
                    old_realized_pnl = (fill_price - current_avg_cost) * current_qty
                
                self.realized_pnl += old_realized_pnl - commission
                current_pos["realized_pnl"] += old_realized_pnl - commission
                
                current_pos["quantity"] = new_qty
                current_pos["avg_cost_price"] = fill_price # 反向开仓，成本价为当前成交价
        
        # 重新计算该合约的未实现盈亏 (基于当前持仓成本和平仓前的最后市价，或用成交价作为临时市价)
        self.update_on_market_data(MarketEvent(symbol=symbol, timestamp=fill_event.timestamp, close_price=fill_price, open_price=fill_price, high_price=fill_price, low_price=fill_price, volume=0))
        app_logger.info(f"成交处理完毕: {symbol}, 数量: {direction_multiplier * fill_qty} @ {fill_price:.2f}. 新现金: {self.current_cash:.2f}")
        app_logger.info(f"当前 {symbol} 持仓: {self.positions.get(symbol)}")

    def update_on_market_data(self, market_event: MarketEvent) -> None:
        """
        根据新的市场数据更新当前持仓的市场价值。
        计算未实现盈亏。
        """
        symbol = market_event.symbol
        if symbol in self.positions and self.positions[symbol]["quantity"] != 0:
            pos = self.positions[symbol]
            qty = pos["quantity"]
            avg_cost = pos["avg_cost_price"]
            current_price = market_event.close_price # 使用收盘价计算市值

            pos["market_value"] = qty * current_price
            pos["unrealized_pnl"] = (current_price - avg_cost) * qty
            
            # 更新总的未实现盈亏
            self.unrealized_pnl = sum(p.get("unrealized_pnl", 0.0) for p in self.positions.values() if p.get("quantity", 0) !=0)
            # app_logger.debug(f"市价更新 ({symbol}): 价格={current_price:.2f}, 市值={pos['market_value']:.2f}, 未实现P&L={pos['unrealized_pnl']:.2f}")
        # else: # 如果没有该合约持仓，或者数量为0，则不需要更新
            # pass

    def get_current_positions(self) -> Dict[str, PositionData]:
        """返回当前持仓的字典 (合约代码 -> 持仓数据)。"""
        # 返回一个副本以防止外部修改
        return {s: p.copy() for s, p in self.positions.items() if p.get("quantity", 0) != 0} 

    def get_current_holdings_value(self, symbol: Optional[str] = None) -> float:
        """
        返回当前持仓的总市值。
        如果 symbol is provided, returns value for that symbol only.
        If no symbol and no positions, returns 0.
        """
        if symbol:
            if symbol in self.positions and self.positions[symbol].get("quantity",0) != 0:
                return self.positions[symbol].get("market_value", 0.0)
            return 0.0
        else:
            total_value = 0.0
            for pos_data in self.positions.values():
                if pos_data.get("quantity",0) != 0:
                    total_value += pos_data.get("market_value", 0.0)
            return total_value

    def get_portfolio_snapshot(self, current_market_prices: Optional[Dict[str, float]] = None) -> PortfolioSnapshot:
        """
        返回投资组合当前状态的快照 (权益、现金等)。
        """
        # 如果提供了实时价格，则用实时价格更新一次所有持仓的市值和未实现盈亏
        if current_market_prices:
            for sym, price in current_market_prices.items():
                 # 创建一个临时的MarketEvent来调用update_on_market_data
                 # 注意：这可能会重复记录日志，需要考虑是否直接计算
                self.update_on_market_data(MarketEvent(symbol=sym, timestamp=datetime.utcnow(), # 时间戳可能需要同步
                                                       open_price=price, high_price=price, low_price=price, 
                                                       close_price=price, volume=0))

        total_equity = self._calculate_current_total_equity()
        return {
            "timestamp": datetime.utcnow(),
            "initial_capital": self.initial_capital,
            "current_cash": self.current_cash,
            "total_equity": total_equity, # 现金 + 总持仓市值
            "holdings_value": self.get_current_holdings_value(),
            "positions": self.get_current_positions(),
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_pnl": self.realized_pnl + self.unrealized_pnl,
            "total_commission": self.total_commission
        }

    def get_available_cash(self) -> float:
        """返回当前可用于交易的现金。"""
        # TODO: 未来可以考虑保证金占用等因素
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
            portfolio.update_on_fill(fill)
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
    portfolio.update_on_market_data(market_update_aapl_up)
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