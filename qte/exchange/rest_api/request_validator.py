#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
请求参数验证器 - 交易所REST API请求参数验证
"""
import logging
import time
from typing import Dict, Any, Tuple, Optional, Union
from decimal import Decimal, InvalidOperation

logger = logging.getLogger("RequestValidator")

class RequestValidator:
    """请求参数验证器，用于验证交易所REST API请求参数"""
    
    @staticmethod
    def validate_order_request(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证下单请求参数
        
        Parameters
        ----------
        data : Dict
            请求参数
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误信息)
        """
        # 验证数据是否为空
        if not data:
            return False, "请求数据为空"
            
        # 验证必填参数
        required_params = ["symbol", "side", "type", "quantity"]
        for param in required_params:
            if param not in data:
                return False, f"缺少必要参数: {param}"
        
        # 验证订单类型
        order_type = data["type"].upper() if isinstance(data["type"], str) else str(data["type"])
        if order_type not in ["LIMIT", "MARKET"]:
            return False, f"无效的订单类型: {order_type}"
            
        # 验证订单方向
        side = data["side"].upper() if isinstance(data["side"], str) else str(data["side"])
        if side not in ["BUY", "SELL"]:
            return False, f"无效的订单方向: {side}"
            
        # 验证数量
        try:
            quantity = float(data["quantity"])
            if quantity <= 0:
                return False, "数量必须大于0"
        except (ValueError, TypeError):
            return False, f"无效的数量格式: {data['quantity']}"
            
        # 对于限价单，验证价格
        if order_type == "LIMIT":
            if "price" not in data:
                return False, "限价单必须提供价格"
                
            try:
                price = float(data["price"])
                if price <= 0:
                    return False, "价格必须大于0"
            except (ValueError, TypeError):
                return False, f"无效的价格格式: {data['price']}"
                
        # 对于市价单，验证不应提供价格
        elif order_type == "MARKET" and "price" in data and data["price"]:
            return False, "市价单不应提供价格"
            
        # 验证交易对格式
        symbol = data["symbol"]
        if not isinstance(symbol, str) or len(symbol) < 2:
            return False, f"无效的交易对格式: {symbol}"
            
        return True, None
        
    @staticmethod
    def validate_cancel_request(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证取消订单请求参数
        
        Parameters
        ----------
        data : Dict[str, Any]
            请求数据
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        # 验证必须参数
        if 'symbol' not in data:
            return False, "缺少必要参数: symbol"
            
        # 验证订单ID或客户端订单ID
        if 'orderId' not in data and 'origClientOrderId' not in data:
            return False, "缺少必要参数: orderId 或 origClientOrderId"
            
        # 验证通过
        return True, None
        
    @staticmethod
    def validate_query_request(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证查询请求参数
        
        Parameters
        ----------
        data : Dict[str, Any]
            请求数据
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        # 与取消订单请求参数验证相同
        return RequestValidator.validate_cancel_request(data)
        
    @staticmethod
    def validate_deposit_request(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证充值请求参数
        
        Parameters
        ----------
        data : Dict[str, Any]
            请求数据
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        # 验证必须参数
        required_fields = ['asset', 'amount']
        for field in required_fields:
            if field not in data:
                return False, f"缺少必要参数: {field}"
                
        # 验证金额格式
        try:
            amount = Decimal(str(data.get('amount')))
            if amount <= 0:
                return False, "充值金额必须大于0"
        except (InvalidOperation, TypeError, ValueError):
            return False, "无效的金额格式"
            
        # 验证通过
        return True, None
        
    @staticmethod
    def validate_withdraw_request(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证提现请求参数
        
        Parameters
        ----------
        data : Dict[str, Any]
            请求数据
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (是否有效, 错误消息)
        """
        # 与充值请求参数验证相同
        return RequestValidator.validate_deposit_request(data)

    @staticmethod
    def validate_timestamp(timestamp: Union[int, str, None]) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        验证时间戳是否在有效范围内
        
        Parameters
        ----------
        timestamp : Union[int, str, None]
            毫秒时间戳
            
        Returns
        -------
        Tuple[bool, Optional[str], Optional[int]]
            (是否有效, 错误信息, 错误码)
        """
        if timestamp is None:
            return True, None, None
            
        try:
            # 转换为整数
            ts = int(timestamp)
            
            # 2017年1月1日时间戳（毫秒）
            min_timestamp = 1483228800000
            # 当前时间 + 10秒
            max_timestamp = int(time.time() * 1000) + 10000
            
            if ts < min_timestamp:
                return False, f"Timestamp is too early. Minimum allowed: {min_timestamp}", -1021
            
            if ts > max_timestamp:
                return False, f"Timestamp is too far in the future", -1021
            
            return True, None, None
            
        except (ValueError, TypeError):
            return False, "Invalid timestamp format", -1021