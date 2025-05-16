from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd

# Attempt to import OrderDirection from a plausible location
# Assuming events.py is in qte.core
try:
    from qte.core.events import OrderDirection
except ImportError:
    # Fallback if qte.core.events is not found or OrderDirection is not there
    # This allows the code to be written, but it will fail at runtime if OrderDirection is truly missing
    print("Warning: Could not import OrderDirection from qte.core.events. Using a placeholder.")
    from enum import Enum
    class OrderDirection(Enum):
        BUY = "BUY"
        SELL = "SELL"

@dataclass
class Trade:
    """记录单笔交易的详情"""
    timestamp: datetime
    quantity: float
    price: float
    commission: float
    direction: OrderDirection # BUY or SELL

@dataclass
class Position:
    """
    表示一个交易品种的持仓信息。
    """
    symbol: str
    quantity: float = 0.0  # 当前持仓数量 (正为多头, 负为空头)
    average_cost: float = 0.0  # 平均持仓成本
    market_value: float = 0.0  # 当前市值
    unrealized_pnl: float = 0.0  # 未实现盈亏
    realized_pnl: float = 0.0  # 已实现盈亏
    last_price: float = 0.0 # 最新市场价格
    last_update_time: Optional[datetime] = None # 最后更新时间
    
    trades: List[Trade] = field(default_factory=list) # 详细的交易记录
    position_history: List[Dict[str, Any]] = field(default_factory=list)  # 持仓历史记录
    _last_trade: Optional[Trade] = None  # 最后一笔交易，用于记录历史

    def update_market_value(self, current_price: float, timestamp: Optional[datetime] = None) -> None:
        """根据当前市场价格更新市值和未实现盈亏"""
        self.last_price = current_price
        self.market_value = self.quantity * current_price
        if self.quantity != 0:
            # 对于空头，成本高于现价是盈利
            if self.quantity > 0: # 多头
                self.unrealized_pnl = (current_price - self.average_cost) * self.quantity
            else: # 空头
                self.unrealized_pnl = (self.average_cost - current_price) * abs(self.quantity)
        else:
            self.unrealized_pnl = 0.0
        self.last_update_time = timestamp if timestamp else datetime.now()
        
        # 记录持仓历史，如果有最近的交易记录
        if self._last_trade:
            self._record_position_snapshot(current_price)

    def add_trade(self, trade: Trade) -> None:
        """
        记录一笔交易，并更新持仓状态 (数量, 平均成本, 已实现盈亏)。
        """
        self.trades.append(trade)
        self._last_trade = trade  # 保存当前交易用于历史记录
        
        # 记录交易前的总成本和总数量，方便计算平均成本变化
        # 注意：这里的实现逻辑是为了简化，实际的平均成本计算可能更复杂，尤其涉及部分平仓和先进先出等规则
        
        current_total_value_before_trade = self.average_cost * self.quantity
        
        # 处理已实现盈亏 (只在平仓时计算)
        # 简化逻辑：当交易方向与现有持仓方向相反时，认为是平仓操作
        is_closing_trade = (self.quantity > 0 and trade.direction == OrderDirection.SELL) or \
                           (self.quantity < 0 and trade.direction == OrderDirection.BUY)

        if is_closing_trade:
            closed_quantity = min(abs(self.quantity), trade.quantity)
            if self.quantity > 0: # 平多仓
                self.realized_pnl += (trade.price - self.average_cost) * closed_quantity
            else: # 平空仓 (self.quantity < 0)
                self.realized_pnl += (self.average_cost - trade.price) * closed_quantity
        
        # 更新数量
        if trade.direction == OrderDirection.BUY:
            new_quantity = self.quantity + trade.quantity
            if self.quantity >= 0: # 多头加仓或开多仓
                if new_quantity != 0: # 避免除以零
                    self.average_cost = (current_total_value_before_trade + trade.price * trade.quantity) / new_quantity
                else: # 刚好平仓，成本归零 (理论上加仓不会直接到0，除非原仓位是负数且数量一致)
                    self.average_cost = 0.0
            else: # 空头减仓(买入平空)或反手开多
                if new_quantity == 0: # 完全平空
                    self.average_cost = 0.0
                elif new_quantity > 0 : # 反手开多
                    self.average_cost = trade.price # 新的多头持仓成本为当前交易价格
                # else: # 部分平空，平均成本不变 (此简化逻辑下)
                #     pass
        else: # trade.direction == OrderDirection.SELL
            new_quantity = self.quantity - trade.quantity
            if self.quantity <= 0: # 空头加仓或开空仓
                if new_quantity != 0: # 避免除以零 (注意quantity是负数，所以current_total_value_before_trade也是负值或0)
                     self.average_cost = (current_total_value_before_trade - trade.price * trade.quantity) / new_quantity
                else:
                    self.average_cost = 0.0
            else: # 多头减仓(卖出平多)或反手开空
                if new_quantity == 0: # 完全平多
                    self.average_cost = 0.0
                elif new_quantity < 0: # 反手开空
                    self.average_cost = trade.price # 新的空头持仓成本为当前交易价格
                # else: # 部分平多，平均成本不变
                #     pass
        
        self.quantity = new_quantity
        if self.quantity == 0: # 确保完全平仓后成本为0
            self.average_cost = 0.0
            
        # 更新市值和未实现盈亏
        self.update_market_value(trade.price, trade.timestamp)
        
        # 加上手续费到已实现盈亏
        self.realized_pnl -= trade.commission

    def _record_position_snapshot(self, current_price: float) -> None:
        """记录当前持仓状态快照到历史记录"""
        if not self._last_trade:
            return
            
        history_entry = {
            'timestamp': self.last_update_time,
            'quantity': self.quantity,
            'average_cost': self.average_cost,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'last_price': current_price,
            'trade_direction': self._last_trade.direction,
            'trade_quantity': self._last_trade.quantity,
            'trade_price': self._last_trade.price,
            'trade_commission': self._last_trade.commission
        }
        
        # 只有在position_history为空或者当前记录和上一条记录不同时才添加
        if not self.position_history or self.position_history[-1]['last_price'] != current_price:
            self.position_history.append(history_entry)

    def get_position_history(self) -> pd.DataFrame:
        """
        获取持仓历史记录，返回一个DataFrame，包含每次交易后的持仓状态
        
        Returns:
            pd.DataFrame: 包含以下列的DataFrame:
                - timestamp: 交易时间
                - quantity: 交易后的持仓数量
                - average_cost: 交易后的平均成本
                - market_value: 交易后的市值
                - unrealized_pnl: 交易后的未实现盈亏
                - realized_pnl: 交易后的已实现盈亏
                - last_price: 交易时的市场价格
                - trade_direction: 交易方向 (BUY/SELL)
                - trade_quantity: 交易数量
                - trade_price: 交易价格
                - trade_commission: 交易佣金
        """
        if not self.position_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.position_history)

    def __repr__(self) -> str:
        return (
            f"Position(symbol=\'{self.symbol}\', quantity={self.quantity}, "
            f"avg_cost={self.average_cost:.2f}, market_val={self.market_value:.2f}, "
            f"unreal_pnl={self.unrealized_pnl:.2f}, real_pnl={self.realized_pnl:.2f}, "
            f"last_price={self.last_price:.2f})"
        ) 