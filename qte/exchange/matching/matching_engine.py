#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
撮合引擎 - 负责订单匹配和交易生成
"""
import time
import uuid
import bisect
import logging
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("MatchingEngine")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    """订单类型"""
    LIMIT = "LIMIT"        # 限价单
    MARKET = "MARKET"      # 市价单
    STOP = "STOP"          # 止损单
    STOP_LIMIT = "STOP_LIMIT"  # 止损限价单

class OrderStatus(Enum):
    """订单状态"""
    NEW = "NEW"            # 新订单
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # 部分成交
    FILLED = "FILLED"      # 完全成交
    CANCELED = "CANCELED"  # 已取消
    REJECTED = "REJECTED"  # 已拒绝
    EXPIRED = "EXPIRED"    # 已过期
    EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH"  # 因自成交保护而过期

@dataclass
class Order:
    """订单类"""
    order_id: str                      # 订单ID
    symbol: str                        # 交易对
    side: OrderSide                    # 订单方向
    order_type: OrderType              # 订单类型
    quantity: float                    # 数量
    price: Optional[float] = None      # 价格（市价单为None）
    stop_price: Optional[float] = None # 触发价格（止损单）
    timestamp: float = field(default_factory=time.time)  # 订单时间戳
    status: OrderStatus = OrderStatus.NEW  # 订单状态
    filled_quantity: float = 0.0       # 已成交数量
    remaining_quantity: float = 0.0    # 剩余数量
    user_id: str = ""                  # 用户ID
    client_order_id: Optional[str] = None  # 客户端订单ID
    quote_order_qty: Optional[float] = None  # 报价金额（用于反向市价单）
    self_trade_prevention_mode: str = "NONE"  # 自成交保护模式: NONE, EXPIRE_TAKER, EXPIRE_MAKER, EXPIRE_BOTH
    price_match: str = "NONE"          # 价格匹配模式: NONE, OPPONENT, OPPONENT_5, QUEUE, QUEUE_5等
    
    def __post_init__(self):
        """初始化后设置剩余数量"""
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.quantity
    
    def fill(self, fill_quantity: float, fill_price: float) -> bool:
        """
        订单成交更新
        
        Parameters
        ----------
        fill_quantity : float
            成交数量
        fill_price : float
            成交价格
            
        Returns
        -------
        bool
            是否完全成交
        """
        if fill_quantity <= 0:
            return False
            
        if fill_quantity > self.remaining_quantity:
            logger.warning(f"成交数量 {fill_quantity} 大于剩余数量 {self.remaining_quantity}")
            fill_quantity = self.remaining_quantity
            
        self.filled_quantity += fill_quantity
        self.remaining_quantity -= fill_quantity
        
        previous_status = self.status
        
        if self.remaining_quantity <= 0:
            self.status = OrderStatus.FILLED
            logger.info(f"订单 {self.order_id} 已完全成交")
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
            logger.info(f"订单 {self.order_id} 部分成交: {fill_quantity}@{fill_price}")
            
        return self.status == OrderStatus.FILLED
    
    def cancel(self) -> bool:
        """
        取消订单
        
        Returns
        -------
        bool
            是否成功取消
        """
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            logger.warning(f"订单 {self.order_id} 状态为 {self.status}，无法取消")
            return False
            
        self.status = OrderStatus.CANCELED
        logger.info(f"订单 {self.order_id} 已取消")
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """
        将订单转换为字典，用于API响应
        
        Returns
        -------
        Dict[str, Any]
            订单信息字典
        """
        # 计算或使用原始报价金额
        orig_quote_order_qty = None
        if self.quote_order_qty is not None:
            # 如果设置了quote_order_qty，直接使用
            orig_quote_order_qty = str(round(float(self.quote_order_qty), 8))
        elif self.price is not None and self.quantity > 0:
            # 否则根据价格和数量计算
            orig_quote_order_qty = str(round(float(self.price) * float(self.quantity), 8))
            
        result = {
            "orderId": self.order_id,
            "clientOrderId": self.client_order_id,
            "symbol": self.symbol,
            "price": str(self.price) if self.price is not None else None,
            "origQty": str(self.quantity),
            "executedQty": str(self.filled_quantity),
            "status": self.status.value,
            "type": self.order_type.value,
            "side": self.side.value,
            "time": int(self.timestamp * 1000),  # 毫秒时间戳
            "origQuoteOrderQty": orig_quote_order_qty,  # 原始报价金额
            "selfTradePreventionMode": self.self_trade_prevention_mode  # 自成交保护模式
        }
        
        # 只有在非NONE模式下才添加priceMatch字段
        if self.price_match != "NONE":
            result["priceMatch"] = self.price_match
            
        return result

@dataclass
class Trade:
    """交易类，表示一次成交"""
    trade_id: str                  # 交易ID
    symbol: str                    # 交易对
    buy_order_id: str              # 买方订单ID
    sell_order_id: str             # 卖方订单ID
    price: float                   # 成交价格
    quantity: float                # 成交数量
    timestamp: float = field(default_factory=time.time)  # 成交时间戳
    buyer_user_id: Optional[str] = None  # 买方用户ID
    seller_user_id: Optional[str] = None  # 卖方用户ID
    fee: Optional[float] = None    # 手续费
    fee_asset: Optional[str] = None  # 手续费资产

class OrderBook:
    """订单簿类，管理买卖订单"""
    
    def __init__(self, symbol: str):
        """
        初始化订单簿
        
        Parameters
        ----------
        symbol : str
            交易对名称
        """
        self.symbol = symbol
        self.buy_orders: Dict[float, List[Order]] = {}  # 买单，按价格分组
        self.sell_orders: Dict[float, List[Order]] = {}  # 卖单，按价格分组
        self.order_map: Dict[str, Order] = {}  # 订单ID到订单对象的映射
        
        # 排序的价格列表，用于快速访问买卖盘
        self.buy_prices: List[float] = []  # 买价，降序排列
        self.sell_prices: List[float] = []  # 卖价，升序排列
        
        logger.info(f"订单簿已创建: {symbol}")
    
    def add_order(self, order: Order) -> bool:
        """
        添加订单到订单簿
        
        Parameters
        ----------
        order : Order
            订单对象
            
        Returns
        -------
        bool
            是否成功添加
        """
        if order.order_id in self.order_map:
            logger.warning(f"订单 {order.order_id} 已存在")
            return False
            
        # 市价单直接进行撮合，不加入订单簿
        if order.order_type == OrderType.MARKET:
            logger.info(f"市价单 {order.order_id} 直接进行撮合")
            return True
            
        self.order_map[order.order_id] = order
        
        # 按买卖方向分别处理
        if order.side == OrderSide.BUY:
            if order.price not in self.buy_orders:
                self.buy_orders[order.price] = []
                # 更新排序的价格列表（降序）- 使用二分查找确定插入位置
                # 对于买单，我们希望按照价格从高到低排序
                pos = self._find_buy_position(order.price)
                self.buy_prices.insert(pos, order.price)
            self.buy_orders[order.price].append(order)
            logger.info(f"买单 {order.order_id} 加入订单簿: {order.quantity}@{order.price}")
        else:
            if order.price not in self.sell_orders:
                self.sell_orders[order.price] = []
                # 更新排序的价格列表（升序）- 使用bisect库高效插入
                bisect.insort_left(self.sell_prices, order.price)
            self.sell_orders[order.price].append(order)
            logger.info(f"卖单 {order.order_id} 加入订单簿: {order.quantity}@{order.price}")
            
        return True
    
    def _find_buy_position(self, price: float) -> int:
        """
        使用二分查找确定买价在降序列表中的插入位置
        
        Parameters
        ----------
        price : float
            要插入的价格
            
        Returns
        -------
        int
            应该插入的位置索引
        """
        left, right = 0, len(self.buy_prices)
        while left < right:
            mid = (left + right) // 2
            if self.buy_prices[mid] > price:
                left = mid + 1
            else:
                right = mid
        return left
    
    def remove_order(self, order_id: str) -> Optional[Order]:
        """
        从订单簿中移除订单
        
        Parameters
        ----------
        order_id : str
            订单ID
            
        Returns
        -------
        Optional[Order]
            移除的订单，如不存在则返回None
        """
        if order_id not in self.order_map:
            logger.warning(f"订单 {order_id} 不存在")
            return None
            
        order = self.order_map[order_id]
        del self.order_map[order_id]
        
        if order.side == OrderSide.BUY:
            orders = self.buy_orders.get(order.price, [])
            orders = [o for o in orders if o.order_id != order_id]
            if not orders:
                del self.buy_orders[order.price]
                self.buy_prices.remove(order.price)
            else:
                self.buy_orders[order.price] = orders
        else:
            orders = self.sell_orders.get(order.price, [])
            orders = [o for o in orders if o.order_id != order_id]
            if not orders:
                del self.sell_orders[order.price]
                self.sell_prices.remove(order.price)
            else:
                self.sell_orders[order.price] = orders
                
        logger.info(f"订单 {order_id} 已移除")
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单
        
        Parameters
        ----------
        order_id : str
            订单ID
            
        Returns
        -------
        Optional[Order]
            订单对象，如不存在则返回None
        """
        return self.order_map.get(order_id)
    
    def get_best_bid(self) -> Optional[float]:
        """
        获取最高买价
        
        Returns
        -------
        Optional[float]
            最高买价，无买单时返回None
        """
        return self.buy_prices[0] if self.buy_prices else None
    
    def get_best_ask(self) -> Optional[float]:
        """
        获取最低卖价
        
        Returns
        -------
        Optional[float]
            最低卖价，无卖单时返回None
        """
        return self.sell_prices[0] if self.sell_prices else None
    
    def get_depth(self, levels: int = 10) -> Dict[str, List[List[float]]]:
        """
        获取订单簿深度
        
        Parameters
        ----------
        levels : int, optional
            返回的层级数, by default 10
            
        Returns
        -------
        Dict[str, List[List[float]]]
            订单簿深度，格式为 {'bids': [[price, quantity], ...], 'asks': [[price, quantity], ...]}
        """
        bids = []
        asks = []
        
        # 获取买单深度
        for price in self.buy_prices[:levels]:
            quantity = sum(order.remaining_quantity for order in self.buy_orders[price])
            bids.append([price, quantity])
            
        # 获取卖单深度
        for price in self.sell_prices[:levels]:
            quantity = sum(order.remaining_quantity for order in self.sell_orders[price])
            asks.append([price, quantity])
            
        return {'bids': bids, 'asks': asks}
            
class MatchingEngine:
    """撮合引擎，负责订单匹配和交易生成"""
    
    def __init__(self):
        """初始化撮合引擎"""
        self.order_books: Dict[str, OrderBook] = {}  # 交易对 -> 订单簿
        self.trades: List[Trade] = []  # 成交记录
        self.trade_listeners = []  # 成交监听器
        self.order_listeners = []  # 订单状态更新监听器
        
        logger.info("撮合引擎已初始化")
    
    def get_order_book(self, symbol: str) -> OrderBook:
        """
        获取指定交易对的订单簿，不存在则创建
        
        Parameters
        ----------
        symbol : str
            交易对
            
        Returns
        -------
        OrderBook
            订单簿对象
        """
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
        return self.order_books[symbol]
    
    def validate_order(self, order: Order) -> bool:
        """
        验证订单有效性
        
        Parameters
        ----------
        order : Order
            订单对象
            
        Returns
        -------
        bool
            订单是否有效
        """
        # 基础验证
        if not order.symbol:
            logger.warning("订单缺少交易对信息")
            order.status = OrderStatus.REJECTED
            return False
        
        # 验证数量
        if order.quantity <= 0:
            logger.warning(f"订单数量必须大于零: {order.quantity}")
            order.status = OrderStatus.REJECTED
            return False
            
        # 验证价格（限价单）
        if order.order_type == OrderType.LIMIT and order.price is None:
            # 如果是带有价格匹配模式的订单，先不验证价格
            if order.price_match != "NONE":
                # 在place_order方法中会先进行价格匹配，然后再次验证
                return True
                
            logger.warning(f"限价单必须提供价格")
            order.status = OrderStatus.REJECTED
            return False
            
        # 拒绝负价格或零价格的订单
        if order.order_type == OrderType.LIMIT and order.price <= 0:
            logger.warning(f"限价单价格必须大于零: {order.price}")
            order.status = OrderStatus.REJECTED
            return False
            
        return True
    
    def place_order(self, order: Order) -> List[Trade]:
        """
        下单并尝试撮合
        
        Parameters
        ----------
        order : Order
            订单对象
            
        Returns
        -------
        List[Trade]
            生成的交易列表
        """
        logger.info(f"收到订单: {order.order_id}, {order.side.value}, {order.quantity}@{order.price}")
        
        # 是否需要价格匹配
        needs_price_match = (order.order_type == OrderType.LIMIT and 
                           order.price is None and 
                           order.price_match != "NONE")
        
        # 验证订单，但允许带有price_match的限价单暂时不提供价格
        if not needs_price_match and not self.validate_order(order):
            # 通知订单被拒绝
            self._notify_order_update(order, "REJECTED")
            return []
            
        # 如果是需要价格匹配的限价单，先处理价格匹配
        if needs_price_match:
            # 获取订单簿
            order_book = self.get_order_book(order.symbol)
            
            # 检查订单簿深度是否足够进行价格匹配
            if (order.side == OrderSide.BUY and not order_book.sell_prices and order.price_match.startswith("OPPONENT")) or \
               (order.side == OrderSide.SELL and not order_book.buy_prices and order.price_match.startswith("OPPONENT")) or \
               (order.side == OrderSide.BUY and not order_book.buy_prices and order.price_match.startswith("QUEUE")) or \
               (order.side == OrderSide.SELL and not order_book.sell_prices and order.price_match.startswith("QUEUE")):
                logger.warning(f"订单簿不足，无法应用价格匹配: {order.order_id}, 匹配模式 {order.price_match}, {order.side.value}")
                order.status = OrderStatus.REJECTED
                self._notify_order_update(order, "REJECTED")
                return []
                
            matched_price = self._apply_price_match(order, order_book)
            
            if matched_price:
                order.price = matched_price
                logger.info(f"价格匹配成功: {order.order_id}, 匹配模式 {order.price_match}, 匹配价格 {matched_price}")
                
                # 匹配价格后再次验证订单
                if not self.validate_order(order):
                    self._notify_order_update(order, "REJECTED")
                    return []
            else:
                # 提供更详细的拒绝原因
                if order.price_match.startswith("OPPONENT"):
                    side_desc = "卖盘" if order.side == OrderSide.BUY else "买盘"
                    depth_desc = order.price_match.split("_")[1] if "_" in order.price_match else "1"
                    logger.warning(f"价格匹配失败: {order.order_id}, 匹配模式 {order.price_match}, 原因: {side_desc}深度不足 {depth_desc} 档")
                elif order.price_match.startswith("QUEUE"):
                    side_desc = "买盘" if order.side == OrderSide.BUY else "卖盘"
                    depth_desc = order.price_match.split("_")[1] if "_" in order.price_match else "1"
                    logger.warning(f"价格匹配失败: {order.order_id}, 匹配模式 {order.price_match}, 原因: {side_desc}深度不足 {depth_desc} 档")
                else:
                    logger.warning(f"价格匹配失败: {order.order_id}, 匹配模式 {order.price_match}, 原因: 未知匹配模式")
                
                order.status = OrderStatus.REJECTED
                self._notify_order_update(order, "REJECTED")
                return []
        
        # 获取订单簿
        order_book = self.get_order_book(order.symbol)
        
        # 订单状态通知 - 新订单
        self._notify_order_update(order, "NEW")
        
        # 尝试撮合
        trades = self._match_order(order, order_book)
        
        # 如果订单未完全成交且非市价单，则加入订单簿
        if order.remaining_quantity > 0:
            if order.order_type == OrderType.MARKET:
                # 市价单流动性不足处理
                # 如果是使用quoteOrderQty的市价单且部分成交，应将状态设为EXPIRED
                if order.quote_order_qty is not None and order.filled_quantity > 0:
                    order.status = OrderStatus.EXPIRED
                    logger.info(f"市价单 {order.order_id} 因流动性不足而过期，已成交: {order.filled_quantity}")
                    self._notify_order_update(order, "EXPIRED")
            else:
                # 非市价单加入订单簿
                order_book.add_order(order)
        elif order.status == OrderStatus.FILLED:
            # 订单完全成交
            self._notify_order_update(order, "FILLED")
            
        return trades
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        取消订单
        
        Parameters
        ----------
        order_id : str
            订单ID
        symbol : str
            交易对
            
        Returns
        -------
        bool
            是否成功取消
        """
        order_book = self.get_order_book(symbol)
        order = order_book.get_order(order_id)
        
        if not order:
            logger.warning(f"订单 {order_id} 不存在")
            return False
            
        # 从订单簿移除
        order_book.remove_order(order_id)
        
        # 更新订单状态
        order.cancel()
        
        # 通知订单已取消
        self._notify_order_update(order, "CANCELED")
        
        return True
    
    def _match_order(self, order: Order, order_book: OrderBook) -> List[Trade]:
        """
        尝试撮合订单
        
        Parameters
        ----------
        order : Order
            待撮合的订单
        order_book : OrderBook
            订单簿
            
        Returns
        -------
        List[Trade]
            生成的交易列表
        """
        trades = []
        
        # 买单和卖单分别处理
        if order.side == OrderSide.BUY:
            # 买单与卖单簿撮合
            while order.remaining_quantity > 0:
                # 没有卖单或卖单价格高于买单价格，终止撮合
                if not order_book.sell_prices or (order.order_type == OrderType.LIMIT and order_book.sell_prices[0] > order.price):
                    break
                    
                # 获取当前最低卖价
                best_price = order_book.sell_prices[0]
                sell_orders = order_book.sell_orders[best_price]
                
                # 与该价格的卖单逐一撮合
                trades.extend(self._match_with_orders(order, sell_orders, order_book, best_price))
                
                # 如果订单已完全成交，终止撮合
                if order.remaining_quantity <= 0:
                    break
        else:
            # 卖单与买单簿撮合
            while order.remaining_quantity > 0:
                # 没有买单或买单价格低于卖单价格，终止撮合
                if not order_book.buy_prices or (order.order_type == OrderType.LIMIT and order_book.buy_prices[0] < order.price):
                    break
                    
                # 获取当前最高买价
                best_price = order_book.buy_prices[0]
                buy_orders = order_book.buy_orders[best_price]
                
                # 与该价格的买单逐一撮合
                trades.extend(self._match_with_orders(order, buy_orders, order_book, best_price))
                
                # 如果订单已完全成交，终止撮合
                if order.remaining_quantity <= 0:
                    break
                    
        return trades
    
    def _match_with_orders(self, order: Order, opposite_orders: List[Order], 
                          order_book: OrderBook, match_price: float) -> List[Trade]:
        """
        与对手方订单撮合
        
        Parameters
        ----------
        order : Order
            待撮合的订单
        opposite_orders : List[Order]
            对手方订单列表
        order_book : OrderBook
            订单簿
        match_price : float
            撮合价格
            
        Returns
        -------
        List[Trade]
            生成的交易列表
        """
        trades = []
        
        # 创建对手方订单的副本，防止循环中修改
        orders_to_match = opposite_orders.copy()
        
        for opposite_order in orders_to_match:
            # 自成交保护逻辑 - 如果是同一用户的订单
            if order.user_id and opposite_order.user_id and order.user_id == opposite_order.user_id:
                # 处理自成交保护
                if self._handle_self_trade_prevention(order, opposite_order, order_book):
                    # 如果交易被阻止，继续下一个订单
                    # 通知状态更新 - 自成交保护导致的订单过期
                    if order.status == OrderStatus.EXPIRED_IN_MATCH:
                        self._notify_order_update(order, "EXPIRED_IN_MATCH")
                    if opposite_order.status == OrderStatus.EXPIRED_IN_MATCH:
                        self._notify_order_update(opposite_order, "EXPIRED_IN_MATCH")
                    continue
            
            # 确定成交数量
            match_quantity = min(order.remaining_quantity, opposite_order.remaining_quantity)
            
            if match_quantity <= 0:
                continue
                
            # 更新订单状态
            order.fill(match_quantity, match_price)
            opposite_order.fill(match_quantity, match_price)
            
            # 通知对手方订单状态更新
            if opposite_order.status == OrderStatus.FILLED:
                self._notify_order_update(opposite_order, "FILLED")
            else:
                self._notify_order_update(opposite_order, "PARTIALLY_FILLED")
            
            # 当前订单的部分成交状态将在place_order方法中统一通知
            if order.status == OrderStatus.PARTIALLY_FILLED:
                self._notify_order_update(order, "PARTIALLY_FILLED")
                
            # 发送交易更新通知
            self._notify_order_update(order, "TRADE")
            self._notify_order_update(opposite_order, "TRADE")
            
            # 生成交易记录
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                symbol=order.symbol,
                buy_order_id=order.order_id if order.side == OrderSide.BUY else opposite_order.order_id,
                sell_order_id=order.order_id if order.side == OrderSide.SELL else opposite_order.order_id,
                price=match_price,
                quantity=match_quantity,
                buyer_user_id=order.user_id if order.side == OrderSide.BUY else opposite_order.user_id,
                seller_user_id=order.user_id if order.side == OrderSide.SELL else opposite_order.user_id
            )
            
            trades.append(trade)
            self.trades.append(trade)
            
            # 通知监听器
            for listener in self.trade_listeners:
                listener(trade)
            
            logger.info(f"成交: {trade.quantity}@{trade.price}, 买单:{trade.buy_order_id}, 卖单:{trade.sell_order_id}")
            
            # 如果对手方订单已完全成交，从订单簿移除
            if opposite_order.status == OrderStatus.FILLED:
                order_book.remove_order(opposite_order.order_id)
                
            # 如果当前订单已完全成交，终止撮合
            if order.remaining_quantity <= 0:
                break
                
        return trades
    
    def add_trade_listener(self, listener):
        """
        添加成交监听器
        
        Parameters
        ----------
        listener : callable
            监听器函数，接收Trade对象作为参数
        """
        self.trade_listeners.append(listener)
        
    def remove_trade_listener(self, listener):
        """
        移除成交监听器
        
        Parameters
        ----------
        listener : callable
            要移除的监听器函数
        """
        if listener in self.trade_listeners:
            self.trade_listeners.remove(listener)
    
    def get_market_price(self, symbol: str) -> Optional[float]:
        """
        获取市场价格（最后成交价）
        
        Parameters
        ----------
        symbol : str
            交易对
            
        Returns
        -------
        Optional[float]
            市场价格，无成交记录时返回None
        """
        # 倒序搜索，找到该交易对的最后一次成交
        for trade in reversed(self.trades):
            if trade.symbol == symbol:
                return trade.price
                
        return None

    def _handle_self_trade_prevention(self, taker_order: Order, maker_order: Order, order_book: OrderBook) -> bool:
        """
        处理自成交保护
        
        Parameters
        ----------
        taker_order : Order
            吃单（当前需要撮合的订单）
        maker_order : Order
            挂单（已在订单簿中的订单）
        order_book : OrderBook
            订单簿
            
        Returns
        -------
        bool
            是否阻止交易
        """
        # 如果用户ID不匹配，不需要自成交保护
        if taker_order.user_id != maker_order.user_id:
            return False
            
        logger.info(f"检测到自成交风险: 用户 {taker_order.user_id}, 吃单 {taker_order.order_id}({taker_order.side.value}), " +
                   f"挂单 {maker_order.order_id}({maker_order.side.value})")
            
        # 如果任一订单的自成交保护模式为NONE，允许自成交
        if taker_order.self_trade_prevention_mode == "NONE" or maker_order.self_trade_prevention_mode == "NONE":
            logger.info(f"允许自成交: 吃单模式 {taker_order.self_trade_prevention_mode}, 挂单模式 {maker_order.self_trade_prevention_mode}")
            return False
            
        # 根据自成交保护模式处理
        if taker_order.self_trade_prevention_mode == "EXPIRE_TAKER" or maker_order.self_trade_prevention_mode == "EXPIRE_TAKER":
            # 取消吃单
            taker_order.status = OrderStatus.EXPIRED_IN_MATCH
            logger.info(f"自成交保护: 取消吃单 {taker_order.order_id}, 数量: {taker_order.remaining_quantity}@{taker_order.price}")
            return True
            
        if taker_order.self_trade_prevention_mode == "EXPIRE_MAKER" or maker_order.self_trade_prevention_mode == "EXPIRE_MAKER":
            # 取消挂单
            maker_order.status = OrderStatus.EXPIRED_IN_MATCH
            order_book.remove_order(maker_order.order_id)
            logger.info(f"自成交保护: 取消挂单 {maker_order.order_id}, 数量: {maker_order.remaining_quantity}@{maker_order.price}")
            return True
            
        if taker_order.self_trade_prevention_mode == "EXPIRE_BOTH" or maker_order.self_trade_prevention_mode == "EXPIRE_BOTH":
            # 取消双方订单
            taker_order.status = OrderStatus.EXPIRED_IN_MATCH
            maker_order.status = OrderStatus.EXPIRED_IN_MATCH
            order_book.remove_order(maker_order.order_id)
            logger.info(f"自成交保护: 取消双方订单")
            logger.info(f"  - 吃单: {taker_order.order_id}, 数量: {taker_order.remaining_quantity}@{taker_order.price}")
            logger.info(f"  - 挂单: {maker_order.order_id}, 数量: {maker_order.remaining_quantity}@{maker_order.price}")
            return True
            
        # 默认允许自成交
        logger.warning(f"自成交保护模式未能识别: 吃单 {taker_order.self_trade_prevention_mode}, 挂单 {maker_order.self_trade_prevention_mode}")
        return False

    def _apply_price_match(self, order: Order, order_book: OrderBook) -> Optional[float]:
        """
        应用价格匹配逻辑
        
        Parameters
        ----------
        order : Order
            待撮合的订单
        order_book : OrderBook
            订单簿
            
        Returns
        -------
        Optional[float]
            匹配后的价格，如果匹配失败则返回None
        """
        # 获取匹配模式
        match_mode = order.price_match
        
        # 解析价格匹配深度
        depth = 1  # 默认第一档
        if "_" in match_mode:
            try:
                depth = int(match_mode.split("_")[1])
                if depth <= 0:
                    logger.warning(f"无效的价格匹配深度: {depth}，必须大于0")
                    return None
            except (ValueError, IndexError):
                logger.warning(f"无效的价格匹配模式格式: {match_mode}，使用默认第一档")
        
        # 对手价模式：买单匹配卖盘，卖单匹配买盘
        if match_mode == "OPPONENT" or match_mode.startswith("OPPONENT_"):
            return self._match_opponent_price(order, order_book, depth)
        
        # 同向价模式：买单匹配买盘，卖单匹配卖盘
        elif match_mode == "QUEUE" or match_mode.startswith("QUEUE_"):
            return self._match_queue_price(order, order_book, depth)
        
        # 未知的价格匹配模式
        else:
            logger.warning(f"未知的价格匹配模式: {match_mode}")
            return None
            
    def _match_opponent_price(self, order: Order, order_book: OrderBook, depth: int) -> Optional[float]:
        """
        匹配对手价
        
        Parameters
        ----------
        order : Order
            订单对象
        order_book : OrderBook
            订单簿
        depth : int
            匹配深度
            
        Returns
        -------
        Optional[float]
            匹配价格，失败返回None
        """
        if order.side == OrderSide.BUY:
            # 买单获取卖盘价格
            if not order_book.sell_prices or len(order_book.sell_prices) < depth:
                return None
            return order_book.sell_prices[depth-1]
        else:
            # 卖单获取买盘价格
            if not order_book.buy_prices or len(order_book.buy_prices) < depth:
                return None
            return order_book.buy_prices[depth-1]
            
    def _match_queue_price(self, order: Order, order_book: OrderBook, depth: int) -> Optional[float]:
        """
        匹配同向价
        
        Parameters
        ----------
        order : Order
            订单对象
        order_book : OrderBook
            订单簿
        depth : int
            匹配深度
            
        Returns
        -------
        Optional[float]
            匹配价格，失败返回None
        """
        if order.side == OrderSide.BUY:
            # 买单获取买盘价格
            if not order_book.buy_prices or len(order_book.buy_prices) < depth:
                return None
            return order_book.buy_prices[depth-1]
        else:
            # 卖单获取卖盘价格
            if not order_book.sell_prices or len(order_book.sell_prices) < depth:
                return None
            return order_book.sell_prices[depth-1]

    def add_order_listener(self, listener: Callable[[Order, str], None]) -> None:
        """
        添加订单状态更新监听器
        
        Parameters
        ----------
        listener : callable
            监听器函数，接收Order对象和更新类型作为参数
            更新类型包括: NEW, UPDATE, CANCELED, REJECTED, EXPIRED, FILLED, PARTIALLY_FILLED, EXPIRED_IN_MATCH
        """
        self.order_listeners.append(listener)
        
    def remove_order_listener(self, listener: Callable) -> None:
        """
        移除订单状态更新监听器
        
        Parameters
        ----------
        listener : callable
            要移除的监听器函数
        """
        if listener in self.order_listeners:
            self.order_listeners.remove(listener)
            
    def _notify_order_update(self, order: Order, update_type: str) -> None:
        """
        通知订单状态更新
        
        Parameters
        ----------
        order : Order
            更新的订单
        update_type : str
            更新类型
        """
        for listener in self.order_listeners:
            try:
                listener(order, update_type)
            except Exception as e:
                logger.error(f"订单监听器异常: {e}")