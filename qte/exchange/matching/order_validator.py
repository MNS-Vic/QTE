#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
订单验证器 - 处理订单验证逻辑
"""
import logging
from typing import Optional, Tuple, Dict, List, Union
from decimal import Decimal

from qte.exchange.matching.matching_engine import Order, OrderStatus, OrderType

logger = logging.getLogger("OrderValidator")

class OrderValidator:
    """订单验证器，处理订单验证逻辑"""
    
    @staticmethod
    def validate_order(order: Order) -> Tuple[bool, List[str]]:
        """
        验证订单有效性
        
        Parameters
        ----------
        order : Order
            订单对象
            
        Returns
        -------
        Tuple[bool, List[str]]
            (是否有效, 错误消息列表)
        """
        errors = []
        
        # 基础验证
        if not order.symbol:
            error_msg = "订单必须指定交易对"
            logger.warning(error_msg)
            errors.append(error_msg)
            order.status = OrderStatus.REJECTED
        
        # 验证数量
        if order.quantity <= 0:
            error_msg = f"订单数量必须大于0: {order.quantity}"
            logger.warning(error_msg)
            errors.append(error_msg)
            order.status = OrderStatus.REJECTED
            
        # 验证价格（限价单）
        if order.order_type == OrderType.LIMIT and order.price is None:
            error_msg = "限价单必须指定价格"
            logger.warning(error_msg)
            errors.append(error_msg)
            order.status = OrderStatus.REJECTED
            
        # 验证价格（限价单）
        if order.order_type == OrderType.LIMIT and order.price is not None and order.price <= 0:
            error_msg = f"限价单价格必须大于0: {order.price}"
            logger.warning(error_msg)
            errors.append(error_msg)
            order.status = OrderStatus.REJECTED
            
        # 验证止损单
        if order.order_type == OrderType.STOP and order.stop_price is None:
            error_msg = "止损单必须指定触发价格"
            logger.warning(error_msg)
            errors.append(error_msg)
            order.status = OrderStatus.REJECTED
            
        # 验证止损限价单
        if order.order_type == OrderType.STOP_LIMIT:
            if order.stop_price is None:
                error_msg = "止损限价单必须指定触发价格"
                logger.warning(error_msg)
                errors.append(error_msg)
                order.status = OrderStatus.REJECTED
                
            if order.price is None:
                error_msg = "止损限价单必须同时指定触发价格和限价"
                logger.warning(error_msg)
                errors.append(error_msg)
                order.status = OrderStatus.REJECTED
        
        # 如果有错误，返回
        if errors:
            return False, errors
            
        return True, []
    
    @staticmethod
    def validate_order_price(price: Optional[Decimal]) -> Tuple[bool, Optional[str]]:
        """
        验证订单价格
        
        Parameters
        ----------
        price : Optional[Decimal]
            订单价格
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        if price is None:
            return False, "价格不能为空"
            
        if price <= 0:
            return False, f"价格必须大于零: {price}"
            
        return True, None
    
    @staticmethod
    def validate_order_quantity(quantity: Decimal) -> Tuple[bool, Optional[str]]:
        """
        验证订单数量
        
        Parameters
        ----------
        quantity : Decimal
            订单数量
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        if quantity <= 0:
            return False, f"数量必须大于零: {quantity}"
            
        return True, None
        
    @staticmethod
    def check_price_precision(price: Decimal, symbol: str, price_precision: Dict[str, int]) -> Tuple[bool, Optional[str]]:
        """
        检查价格精度
        
        Parameters
        ----------
        price : Decimal
            价格
        symbol : str
            交易对
        price_precision : Dict[str, int]
            价格精度配置
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        if symbol not in price_precision:
            return True, None
            
        precision = price_precision[symbol]
        price_str = str(price)
        
        if '.' in price_str:
            decimal_places = len(price_str.split('.')[1])
            if decimal_places > precision:
                return False, f"价格精度超过限制，最多{precision}位小数: {price}"
                
        return True, None
        
    @staticmethod
    def check_quantity_precision(quantity: Decimal, symbol: str, quantity_precision: Dict[str, int]) -> Tuple[bool, Optional[str]]:
        """
        检查数量精度
        
        Parameters
        ----------
        quantity : Decimal
            数量
        symbol : str
            交易对
        quantity_precision : Dict[str, int]
            数量精度配置
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        if symbol not in quantity_precision:
            return True, None
            
        precision = quantity_precision[symbol]
        quantity_str = str(quantity)
        
        if '.' in quantity_str:
            decimal_places = len(quantity_str.split('.')[1])
            if decimal_places > precision:
                return False, f"数量精度超过限制，最多{precision}位小数: {quantity}"
                
        return True, None
        
    @staticmethod
    def check_min_order_size(price: Decimal, quantity: Decimal, symbol: str, min_notional: Dict[str, float]) -> Tuple[bool, Optional[str]]:
        """
        检查最小订单金额
        
        Parameters
        ----------
        price : Decimal
            价格
        quantity : Decimal
            数量
        symbol : str
            交易对
        min_notional : Dict[str, float]
            最小交易金额配置
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        if symbol not in min_notional:
            return True, None
            
        min_value = min_notional[symbol]
        order_value = price * quantity
        
        if order_value < min_value:
            return False, f"订单金额小于最小要求，至少{min_value}: {order_value}"
            
        return True, None