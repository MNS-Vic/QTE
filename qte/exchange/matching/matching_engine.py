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
from decimal import Decimal

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
    STOP_LOSS = "STOP_LOSS"  # Not directly supported by Binance spot, but part of general order types
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT" # Not directly supported by Binance spot
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"

class OrderStatus(Enum):
    """订单状态"""
    NEW = "NEW"            # 新订单
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # 部分成交
    FILLED = "FILLED"      # 完全成交
    CANCELED = "CANCELED"  # 已取消
    REJECTED = "REJECTED"  # 已拒绝
    EXPIRED = "EXPIRED"    # 已过期
    EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH"  # 因自成交保护而过期
    PENDING_CANCEL = "PENDING_CANCEL"

class TimeInForce(Enum):
    GTC = "GTC"  # Good Til Canceled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill
    # GTD = "GTD"  # Good Til Date (Not supported by Binance Spot)
    # GTX = "GTX"  # Good Til Crossing (Post Only - similar to LIMIT_MAKER) - Binance uses LIMIT_MAKER type

@dataclass
class Order:
    """订单类"""
    # 必需字段 (无默认值)
    user_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    
    # 可选字段 (有默认值)
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_order_id: Optional[str] = None
    time_in_force: Optional[TimeInForce] = None
    price: Optional[float] = None

    quote_order_qty: Optional[float] = None
    orig_quote_order_qty: Optional[float] = None

    status: OrderStatus = OrderStatus.NEW
    executed_quantity: Decimal = Decimal('0.0')
    cummulative_quote_qty: Decimal = Decimal('0.0')
    avg_fill_price: Optional[Decimal] = None

    stop_price: Optional[Decimal] = None
    iceberg_qty: Optional[Decimal] = None

    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    transact_time: Optional[int] = None
    update_time: Optional[int] = None
    working_time: Optional[int] = None

    commission: Decimal = Decimal('0.0')
    commission_asset: Optional[str] = None

    is_maker: bool = False
    status_history: List[Dict[str, Any]] = field(default_factory=list)

    self_trade_prevention_mode: str = "NONE"  # STP mode
    price_match: str = "NONE"  # Price match mode

    def __post_init__(self):
        if isinstance(self.side, str):
            self.side = OrderSide[self.side.upper()]
        if isinstance(self.order_type, str):
            self.order_type = OrderType[self.order_type.upper()]
        if self.time_in_force and isinstance(self.time_in_force, str):
            self.time_in_force = TimeInForce[self.time_in_force.upper()]
        if isinstance(self.status, str):
            self.status = OrderStatus[self.status.upper()]

        if self.update_time is None:
            self.update_time = self.timestamp
        if self.transact_time is None:
            self.transact_time = self.timestamp

        if not self.status_history:
            self.status_history.append({"status": self.status.value, "timestamp": self.timestamp})
            
        if self.quote_order_qty is not None and self.orig_quote_order_qty is None:
            self.orig_quote_order_qty = self.quote_order_qty

    def update_status(self, new_status: OrderStatus, update_timestamp: Optional[int] = None):
        if not isinstance(new_status, OrderStatus):
            raise ValueError(f"new_status must be an OrderStatus Enum member, got {type(new_status)}")
        
        current_ts = update_timestamp if update_timestamp is not None else int(time.time() * 1000)
        
        if self.status != new_status or (new_status == OrderStatus.NEW and self.working_time is None):
            self.status = new_status
            self.update_time = current_ts
            self.status_history.append({"status": self.status.value, "timestamp": current_ts})

            if self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED] and self.working_time is None:
                if self.order_type not in [OrderType.MARKET] and \
                   (self.time_in_force not in [TimeInForce.IOC, TimeInForce.FOK] if self.time_in_force else True):
                    self.working_time = current_ts
    
    @property
    def remaining_quantity(self) -> Decimal:
        return self.quantity - self.executed_quantity

    def add_fill(self, fill_qty: Decimal, fill_price: Decimal, fill_timestamp: int, commission_paid: Decimal, commission_asset_paid: str, trade_is_maker: bool):
        if fill_qty <= 0: return

        self.executed_quantity += fill_qty
        fill_value = fill_qty * fill_price
        self.cummulative_quote_qty += fill_value
        
        if self.executed_quantity > 0:
            self.avg_fill_price = self.cummulative_quote_qty / self.executed_quantity
        else:
            self.avg_fill_price = None

        self.update_time = fill_timestamp
        self.transact_time = fill_timestamp

        self.commission += commission_paid
        if self.commission_asset is None:
            self.commission_asset = commission_asset_paid
        elif self.commission_asset != commission_asset_paid:
            logger.warning(f"Order {self.order_id} has mixed commission assets. Current: {self.commission_asset}, New: {commission_asset_paid}")

        self.is_maker = trade_is_maker 

        if self.remaining_quantity <= Decimal('1e-9'):
            self.update_status(OrderStatus.FILLED, fill_timestamp)
        else:
            self.update_status(OrderStatus.PARTIALLY_FILLED, fill_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        price_str = "0"
        if self.price is not None:
            price_str = "{:.8f}".format(self.price).rstrip('0').rstrip('.')
        elif self.order_type == OrderType.MARKET and self.avg_fill_price is not None: # For filled market orders, show avg price
            price_str = "{:.8f}".format(self.avg_fill_price).rstrip('0').rstrip('.')

        response_dict = {
            "symbol": self.symbol,
            "orderId": self.order_id,
            "orderListId": -1,
            "clientOrderId": self.client_order_id,
            "price": price_str,
            "origQty": "{:.8f}".format(self.quantity).rstrip('0').rstrip('.'),
            "executedQty": "{:.8f}".format(self.executed_quantity).rstrip('0').rstrip('.'),
            "cummulativeQuoteQty": "{:.8f}".format(self.cummulative_quote_qty).rstrip('0').rstrip('.'),
            "status": self.status.value,
            "timeInForce": self.time_in_force.value if self.time_in_force else None,
            "type": self.order_type.value,
            "side": self.side.value,
            "stopPrice": "{:.8f}".format(self.stop_price).rstrip('0').rstrip('.') if self.stop_price is not None else "0.0",
            "icebergQty": "{:.8f}".format(self.iceberg_qty).rstrip('0').rstrip('.') if self.iceberg_qty is not None else "0.0",
            "time": self.timestamp,
            "updateTime": self.update_time,
            "isWorking": self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED],
            "workingTime": self.working_time if self.status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED] else None,
            "origQuoteOrderQty": "{:.8f}".format(self.orig_quote_order_qty if self.orig_quote_order_qty is not None else 0.0).rstrip('0').rstrip('.'),
            "transactTime": self.transact_time, # Added for ACK/RESULT/FULL responses
            "selfTradePreventionMode": self.self_trade_prevention_mode
        }
        if self.price_match != "NONE":
            response_dict["priceMatch"] = self.price_match
        
        # For FULL order response, fills would be added here by the logic in rest_server.py
        # if newOrderRespType == 'FULL': response_dict['fills'] = [trade.to_dict() for trade in associated_trades]
        return response_dict

    def cancel(self, cancel_time: Optional[int] = None) -> bool:
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED, OrderStatus.PENDING_CANCEL]:
            logger.warning(f"Order {self.order_id} in status {self.status.value} cannot be canceled.")
            return False
        
        cancel_timestamp = cancel_time if cancel_time is not None else int(time.time() * 1000)
        self.update_status(OrderStatus.CANCELED, cancel_timestamp)
        # self.transact_time = cancel_timestamp # For cancel confirmation, update_time is usually sufficient
        logger.info(f"Order {self.order_id} has been canceled at {cancel_timestamp}.")
        return True

    def fill(self, quantity, price):
        """
        简化的填充订单方法，用于测试
        
        Parameters
        ----------
        quantity : float
            成交数量
        price : float
            成交价格
        """
        from decimal import Decimal
        fill_qty = Decimal(str(quantity))
        fill_price = Decimal(str(price))
        
        # 更新已成交数量
        self.executed_quantity += fill_qty
        
        # 更新状态
        if self.executed_quantity >= Decimal(str(self.quantity)):
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    @property
    def filled_quantity(self) -> Decimal:
        """获取已成交数量，与executed_quantity等价"""
        return self.executed_quantity

    @filled_quantity.setter
    def filled_quantity(self, value):
        """设置已成交数量"""
        self.executed_quantity = Decimal(str(value))

@dataclass
class Trade:
    """交易类，表示一次成交"""
    # 必需字段 (无默认值)
    user_id: str # User ID of the party involved in this trade (could be buyer or seller for this specific trade object)
    order_id: str  # ID of the order that generated this trade
    symbol: str
    price: Decimal
    quantity: Decimal  # Quantity of the base asset traded
    quote_qty: Decimal # Calculated as price * quantity
    side: OrderSide # Side of the order that generated this trade (e.g. if order was BUY, this trade is a BUY)
    commission: Decimal
    commission_asset: str
    is_maker: bool # True if this trade was a result of a maker order (resting on book)
    id: int  # Trade ID - now using integer instead of UUID
    
    # 可选字段 (有默认值)
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    # Optional linking to the counter-party trade/order if needed for advanced analysis
    # counter_order_id: Optional[str] = None
    # counter_user_id: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.side, str):
            self.side = OrderSide[self.side.upper()]
        # Ensure quote_qty is calculated if not provided, though it should be.
        if self.quote_qty is None and self.price is not None and self.quantity is not None:
             self.quote_qty = self.price * self.quantity

    def to_dict(self, perspective_user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Converts the trade to a dictionary suitable for API responses (Binance 'myTrades' like).
        'perspective_user_id' helps determine 'isBuyer' field correctly if this Trade object is generic.
        If this Trade object always represents the trade from self.user_id's perspective, then
        isBuyer can be determined directly from self.side.
        """
        is_buyer = False
        if perspective_user_id is not None: # If a specific user's view is requested
            if self.user_id == perspective_user_id:
                is_buyer = (self.side == OrderSide.BUY)
            # else: # This trade belongs to the counterparty, infer their side if needed
            #    is_buyer = (self.side == OrderSide.SELL) # if my side was SELL, then counterparty was BUYER
        else: # Default: assume the perspective is of self.user_id stored in the trade
             is_buyer = (self.side == OrderSide.BUY)

        return {
            "symbol": self.symbol,
            "id": self.id,  # Trade ID
            "orderId": self.order_id,
            # "orderListId": -1, # If OCO orders are involved
            "price": "{:.8f}".format(self.price).rstrip('0').rstrip('.'),
            "qty": "{:.8f}".format(self.quantity).rstrip('0').rstrip('.'),
            "quoteQty": "{:.8f}".format(self.quote_qty).rstrip('0').rstrip('.'),
            "commission": "{:.8f}".format(self.commission).rstrip('0').rstrip('.'),
            "commissionAsset": self.commission_asset,
            "time": self.timestamp,
            "isBuyer": is_buyer,
            "isMaker": self.is_maker,
            "isBestMatch": True,  # Placeholder, assume all our matches are best matches for now
        }

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
        
        # 添加订单历史存储
        self.order_history: Dict[str, Order] = {}  # 所有订单历史，order_id -> Order
        self.user_orders: Dict[str, List[str]] = {}  # 用户订单索引，user_id -> [order_id]
        self.client_order_index: Dict[str, Dict[str, str]] = {}  # client_order_id索引，user_id -> {client_order_id -> order_id}
        
        # 添加交易ID计数器
        self.trade_id_counter: int = 1  # 从1开始的递增整数ID
        
        logger.info("撮合引擎已初始化")
    
    def _get_next_trade_id(self) -> int:
        """
        获取下一个交易ID
        
        Returns
        -------
        int
            递增的整数交易ID
        """
        trade_id = self.trade_id_counter
        self.trade_id_counter += 1
        return trade_id
    
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
        
        # 立即将订单存储到历史记录中
        self._store_order_in_history(order)
        
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
                if order.quote_order_qty is not None and order.executed_quantity > 0:
                    order.status = OrderStatus.EXPIRED
                    logger.info(f"市价单 {order.order_id} 因流动性不足而过期，已成交: {order.executed_quantity}")
                    self._notify_order_update(order, "EXPIRED")
            else:
                # 非市价单加入订单簿
                order_book.add_order(order)
        elif order.status == OrderStatus.FILLED:
            # 订单完全成交
            self._notify_order_update(order, "FILLED")
            
        return trades
    
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        取消订单
        
        Parameters
        ----------
        order_id : str
            订单ID
        symbol : Optional[str], optional
            交易对, by default None (现在从order对象获取)
            
        Returns
        -------
        bool
            是否成功取消
        """
        # 使用新的get_order方法查找订单
        order = self.get_order(order_id)
        
        if not order:
            logger.warning(f"订单 {order_id} 不存在")
            return False
        
        # 如果提供了symbol参数，验证是否匹配
        if symbol and order.symbol != symbol:
            logger.warning(f"订单 {order_id} 的交易对 {order.symbol} 与请求的 {symbol} 不匹配")
            return False
            
        # 获取订单簿并尝试从中移除（如果订单在订单簿中）
        order_book = self.get_order_book(order.symbol)
        removed_order = order_book.remove_order(order_id)
        
        # 更新订单状态
        success = order.cancel()
        
        if success:
            # 通知订单已取消
            self._notify_order_update(order, "CANCELED")
        
        return success
    
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
            while order.remaining_quantity > 0 and order.status not in [OrderStatus.EXPIRED_IN_MATCH, OrderStatus.CANCELED, OrderStatus.REJECTED]:
                # 没有卖单或卖单价格高于买单价格，终止撮合
                if not order_book.sell_prices or (order.order_type == OrderType.LIMIT and order_book.sell_prices[0] > order.price):
                    break
                    
                # 获取当前最低卖价
                best_price = order_book.sell_prices[0]
                sell_orders = order_book.sell_orders[best_price]
                
                # 与该价格的卖单逐一撮合
                new_trades = self._match_with_orders(order, sell_orders, order_book, best_price)
                trades.extend(new_trades)
                
                # 如果订单已完全成交或因自成交保护被过期，终止撮合
                if order.remaining_quantity <= 0 or order.status == OrderStatus.EXPIRED_IN_MATCH:
                    break
                    
                # 防护措施: 如果没有产生任何新交易且订单簿状态没有变化，退出防止无限循环
                if not new_trades and order_book.sell_prices and order_book.sell_prices[0] == best_price:
                    break
                    
        else:
            # 卖单与买单簿撮合
            while order.remaining_quantity > 0 and order.status not in [OrderStatus.EXPIRED_IN_MATCH, OrderStatus.CANCELED, OrderStatus.REJECTED]:
                # 没有买单或买单价格低于卖单价格，终止撮合
                if not order_book.buy_prices or (order.order_type == OrderType.LIMIT and order_book.buy_prices[0] < order.price):
                    break
                    
                # 获取当前最高买价
                best_price = order_book.buy_prices[0]
                buy_orders = order_book.buy_orders[best_price]
                
                # 与该价格的买单逐一撮合
                new_trades = self._match_with_orders(order, buy_orders, order_book, best_price)
                trades.extend(new_trades)
                
                # 如果订单已完全成交或因自成交保护被过期，终止撮合
                if order.remaining_quantity <= 0 or order.status == OrderStatus.EXPIRED_IN_MATCH:
                    break
                    
                # 防护措施: 如果没有产生任何新交易且订单簿状态没有变化，退出防止无限循环
                if not new_trades and order_book.buy_prices and order_book.buy_prices[0] == best_price:
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
            
            fill_timestamp = int(time.time() * 1000)
            
            # 确定maker和taker
            # 已在订单簿中的订单是maker，新进入的订单是taker
            taker_order = order
            maker_order = opposite_order
            
            # 转换match_price为Decimal类型以确保精度
            match_price_decimal = Decimal(str(match_price))
            
            # 计算commission
            # 佣金率：买方按USDT计算，卖方按BTC计算
            commission_rate = Decimal('0.001')  # 0.1%
            
            if taker_order.side == OrderSide.BUY:
                # 买方付出USDT，佣金用USDT计算
                taker_commission = match_quantity * match_price_decimal * commission_rate
                taker_commission_asset = taker_order.symbol[-4:] if taker_order.symbol.endswith('USDT') else taker_order.symbol[3:]  # 简化，假设为USDT
                maker_commission = match_quantity * commission_rate
                maker_commission_asset = maker_order.symbol[:3] if maker_order.symbol.endswith('USDT') else maker_order.symbol[:-3]  # 简化，假设为BTC
            else:
                # 卖方卖出BTC，佣金用BTC计算
                taker_commission = match_quantity * commission_rate  
                taker_commission_asset = taker_order.symbol[:3] if taker_order.symbol.endswith('USDT') else taker_order.symbol[:-3]  # 简化，假设为BTC
                maker_commission = match_quantity * match_price_decimal * commission_rate
                maker_commission_asset = maker_order.symbol[-4:] if maker_order.symbol.endswith('USDT') else maker_order.symbol[3:]  # 简化，假设为USDT
            
            # 更新订单成交信息
            taker_order.add_fill(match_quantity, match_price_decimal, fill_timestamp, taker_commission, taker_commission_asset, False)  # taker不是maker
            maker_order.add_fill(match_quantity, match_price_decimal, fill_timestamp, maker_commission, maker_commission_asset, True)   # maker是maker
            
            # 生成交易记录 - 为每个参与方创建单独的Trade对象
            # Taker方的交易记录
            taker_trade = Trade(
                user_id=taker_order.user_id,
                order_id=taker_order.order_id,
                symbol=taker_order.symbol,
                price=match_price_decimal,
                quantity=match_quantity,
                quote_qty=match_quantity * match_price_decimal,
                side=taker_order.side,
                commission=taker_commission,
                commission_asset=taker_commission_asset,
                is_maker=False,
                id=self._get_next_trade_id(),
                timestamp=fill_timestamp
            )
            
            # Maker方的交易记录
            maker_trade = Trade(
                user_id=maker_order.user_id,
                order_id=maker_order.order_id,
                symbol=maker_order.symbol,
                price=match_price_decimal,
                quantity=match_quantity,
                quote_qty=match_quantity * match_price_decimal,
                side=maker_order.side,
                commission=maker_commission,
                commission_asset=maker_commission_asset,
                is_maker=True,
                id=self._get_next_trade_id(),
                timestamp=fill_timestamp
            )
            
            trades.extend([taker_trade, maker_trade])
            self.trades.extend([taker_trade, maker_trade])
            
            # 通知监听器
            for listener in self.trade_listeners:
                listener(taker_trade)
                listener(maker_trade)
            
            logger.info(f"成交: {match_quantity}@{match_price}, " +
                       f"Taker:{taker_order.order_id}({taker_order.side.value}), " +
                       f"Maker:{maker_order.order_id}({maker_order.side.value})")
            
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

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单（包括历史订单）
        
        Parameters
        ----------
        order_id : str
            订单ID
            
        Returns
        -------
        Optional[Order]
            订单对象，如不存在则返回None
        """
        # 先查订单簿中的活跃订单
        for order_book in self.order_books.values():
            order = order_book.get_order(order_id)
            if order:
                return order
        
        # 再查历史订单
        return self.order_history.get(order_id)
    
    def get_order_by_client_id(self, user_id: str, client_order_id: str) -> Optional[Order]:
        """
        根据客户端订单ID获取订单
        
        Parameters
        ----------
        user_id : str
            用户ID
        client_order_id : str
            客户端订单ID
            
        Returns
        -------
        Optional[Order]
            订单对象，如不存在则返回None
        """
        user_client_orders = self.client_order_index.get(user_id, {})
        order_id = user_client_orders.get(client_order_id)
        if order_id:
            return self.get_order(order_id)
        return None
    
    def get_best_bid(self, symbol: str) -> Optional[float]:
        """
        获取指定交易对的最高买价
        
        Parameters
        ----------
        symbol : str
            交易对
            
        Returns
        -------
        Optional[float]
            最高买价，无买单时返回None
        """
        if symbol not in self.order_books:
            return None
        return self.order_books[symbol].get_best_bid()
    
    def get_best_ask(self, symbol: str) -> Optional[float]:
        """
        获取指定交易对的最低卖价
        
        Parameters
        ----------
        symbol : str
            交易对
            
        Returns
        -------
        Optional[float]
            最低卖价，无卖单时返回None
        """
        if symbol not in self.order_books:
            return None
        return self.order_books[symbol].get_best_ask()
    
    def get_all_user_orders(self, user_id: str, symbol: Optional[str] = None) -> List[Order]:
        """
        获取用户所有订单（包括历史）
        
        Parameters
        ----------
        user_id : str
            用户ID
        symbol : Optional[str], optional
            交易对过滤, by default None
            
        Returns
        -------
        List[Order]
            订单列表
        """
        user_order_ids = self.user_orders.get(user_id, [])
        orders = []
        
        for order_id in user_order_ids:
            order = self.get_order(order_id)
            if order and (symbol is None or order.symbol == symbol):
                orders.append(order)
        
        return orders
    
    def _store_order_in_history(self, order: Order):
        """
        将订单存储到历史记录中
        
        Parameters
        ----------
        order : Order
            订单对象
        """
        # 存储到全局订单历史
        self.order_history[order.order_id] = order
        
        # 更新用户订单索引
        if order.user_id not in self.user_orders:
            self.user_orders[order.user_id] = []
        if order.order_id not in self.user_orders[order.user_id]:
            self.user_orders[order.user_id].append(order.order_id)
        
        # 更新客户端订单ID索引
        if order.client_order_id:
            if order.user_id not in self.client_order_index:
                self.client_order_index[order.user_id] = {}
            self.client_order_index[order.user_id][order.client_order_id] = order.order_id