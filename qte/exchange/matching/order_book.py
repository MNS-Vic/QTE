#!/usr/bin/env python3
"""
简单的订单簿模块

提供基本的订单簿功能以支持virtual_exchange
"""

import logging
from typing import List, Optional, Tuple, Dict
from decimal import Decimal

logger = logging.getLogger(__name__)


class OrderBook:
    """简单的订单簿实现
    
    为virtual_exchange提供基本的订单簿功能
    """
    
    def __init__(self, symbol: str):
        """初始化订单簿
        
        Args:
            symbol: 交易标的
        """
        self.symbol = symbol
        self.bids: List[Tuple[Decimal, Decimal]] = []  # [(价格, 数量), ...]
        self.asks: List[Tuple[Decimal, Decimal]] = []  # [(价格, 数量), ...]
        self.orders: Dict[str, dict] = {}  # 订单ID -> 订单数据
        
        logger.debug(f"订单簿 {symbol} 初始化完成")
    
    def add_order(self, order_id: str, side: str, price: Decimal, quantity: Decimal) -> None:
        """添加订单到订单簿
        
        Args:
            order_id: 订单ID
            side: 买卖方向 ('BUY' 或 'SELL')
            price: 价格
            quantity: 数量
        """
        order = {
            'order_id': order_id,
            'side': side,
            'price': price,
            'quantity': quantity,
            'remaining_quantity': quantity
        }
        
        self.orders[order_id] = order
        
        if side == 'BUY':
            self.bids.append((price, quantity))
            self.bids.sort(key=lambda x: x[0], reverse=True)  # 按价格降序排列
        else:
            self.asks.append((price, quantity))
            self.asks.sort(key=lambda x: x[0])  # 按价格升序排列
    
    def remove_order(self, order_id: str) -> bool:
        """从订单簿移除订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功移除
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders.pop(order_id)
        price = order['price']
        quantity = order['remaining_quantity']
        
        if order['side'] == 'BUY':
            try:
                self.bids.remove((price, quantity))
            except ValueError:
                pass
        else:
            try:
                self.asks.remove((price, quantity))
            except ValueError:
                pass
        
        return True
    
    def get_depth(self, limit: int = 10) -> Dict[str, List[List]]:
        """获取订单簿深度
        
        Args:
            limit: 返回的档位数量
            
        Returns:
            包含bids和asks的字典
        """
        return {
            'bids': [[str(price), str(qty)] for price, qty in self.bids[:limit]],
            'asks': [[str(price), str(qty)] for price, qty in self.asks[:limit]]
        }
    
    def get_best_bid(self) -> Optional[Decimal]:
        """获取最佳买价
        
        Returns:
            最佳买价，如果没有买单返回None
        """
        return self.bids[0][0] if self.bids else None
    
    def get_best_ask(self) -> Optional[Decimal]:
        """获取最佳卖价
        
        Returns:
            最佳卖价，如果没有卖单返回None
        """
        return self.asks[0][0] if self.asks else None
    
    def check_triggers(self, current_price: float) -> List[dict]:
        """检查价格触发的订单
        
        Args:
            current_price: 当前市场价格
            
        Returns:
            被触发的订单列表
        """
        triggered_orders = []
        
        # 简单实现：检查限价单是否可以成交
        for order_id, order in self.orders.items():
            if order['side'] == 'BUY' and current_price <= float(order['price']):
                triggered_orders.append(order)
            elif order['side'] == 'SELL' and current_price >= float(order['price']):
                triggered_orders.append(order)
        
        return triggered_orders
    
    def get_spread(self) -> Optional[Decimal]:
        """获取买卖价差
        
        Returns:
            价差，如果买卖盘都为空返回None
        """
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return best_ask - best_bid
        
        return None
    
    def is_empty(self) -> bool:
        """检查订单簿是否为空
        
        Returns:
            是否为空
        """
        return len(self.bids) == 0 and len(self.asks) == 0
    
    def get_statistics(self) -> dict:
        """获取订单簿统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'symbol': self.symbol,
            'total_orders': len(self.orders),
            'bid_levels': len(self.bids),
            'ask_levels': len(self.asks),
            'best_bid': str(self.get_best_bid()) if self.get_best_bid() else None,
            'best_ask': str(self.get_best_ask()) if self.get_best_ask() else None,
            'spread': str(self.get_spread()) if self.get_spread() else None
        } 