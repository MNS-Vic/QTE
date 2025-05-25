#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE具体事件转换器实现

注册所有QTE与vnpy之间的事件转换器
实现字段级精确转换和金融级精度保证
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from qte.vnpy import check_vnpy_availability
from .event_converter import (
    converter_registry, PrecisionConverter, DirectionConverter,
    OrderTypeConverter, StatusConverter, ConversionError,
    WarningConversionError, error_handler
)

# 检查vnpy可用性
VNPY_AVAILABLE, VNPY_INFO = check_vnpy_availability()

if VNPY_AVAILABLE:
    from vnpy.trader.object import (
        TickData, OrderData, TradeData, AccountData, ContractData,
        OrderRequest, CancelRequest, SubscribeRequest
    )
    from vnpy.trader.constant import Exchange, Product, Status, OrderType, Direction
else:
    # 模拟类型定义
    TickData = object
    OrderData = object
    TradeData = object
    AccountData = object
    ContractData = object
    OrderRequest = object
    CancelRequest = object
    SubscribeRequest = object
    Exchange = object
    Product = object
    Status = object
    OrderType = object
    Direction = object


# QTE数据类型定义（模拟）
class QTEMarketData:
    """QTE市场数据"""
    def __init__(self, symbol: str, price: Decimal, volume: Decimal, 
                 timestamp: datetime, **kwargs):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.timestamp = timestamp
        self.bid_price = kwargs.get('bid_price', price)
        self.ask_price = kwargs.get('ask_price', price)
        self.bid_volume = kwargs.get('bid_volume', volume)
        self.ask_volume = kwargs.get('ask_volume', volume)


class QTEOrderData:
    """QTE订单数据"""
    def __init__(self, order_id: str, symbol: str, side: str, 
                 order_type: str, quantity: Decimal, price: Decimal,
                 status: str, **kwargs):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.status = status
        self.filled_quantity = kwargs.get('filled_quantity', Decimal('0'))
        self.timestamp = kwargs.get('timestamp', datetime.now())


class QTETradeData:
    """QTE成交数据"""
    def __init__(self, trade_id: str, order_id: str, symbol: str,
                 side: str, quantity: Decimal, price: Decimal,
                 timestamp: datetime, **kwargs):
        self.trade_id = trade_id
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        self.commission = kwargs.get('commission', Decimal('0'))


class QTEAccountData:
    """QTE账户数据"""
    def __init__(self, account_id: str, balances: Dict[str, Decimal], **kwargs):
        self.account_id = account_id
        self.balances = balances
        self.timestamp = kwargs.get('timestamp', datetime.now())


# ==================== vnpy -> QTE 转换器 ====================

@converter_registry.register(OrderRequest, dict)
def convert_order_request_to_qte(vnpy_order: OrderRequest) -> dict:
    """将vnpy OrderRequest转换为QTE订单格式"""
    try:
        qte_order = {
            "symbol": vnpy_order.symbol,
            "side": DirectionConverter.vnpy_to_qte(vnpy_order.direction),
            "type": OrderTypeConverter.vnpy_to_qte(vnpy_order.type),
            "quantity": PrecisionConverter.to_decimal(vnpy_order.volume),
            "price": PrecisionConverter.to_decimal(vnpy_order.price) if vnpy_order.price else None,
            "client_order_id": getattr(vnpy_order, 'reference', ''),
            "timestamp": datetime.now()
        }
        
        # 处理市价单（无需价格）
        if vnpy_order.type == (OrderType.MARKET if VNPY_AVAILABLE else "MARKET"):
            qte_order.pop("price", None)
        
        return qte_order
        
    except Exception as e:
        raise WarningConversionError(f"OrderRequest转换失败: {e}")


@converter_registry.register(CancelRequest, dict)
def convert_cancel_request_to_qte(vnpy_cancel: CancelRequest) -> dict:
    """将vnpy CancelRequest转换为QTE取消订单格式"""
    try:
        return {
            "order_id": vnpy_cancel.orderid,
            "symbol": vnpy_cancel.symbol,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise WarningConversionError(f"CancelRequest转换失败: {e}")


@converter_registry.register(SubscribeRequest, dict)
def convert_subscribe_request_to_qte(vnpy_sub: SubscribeRequest) -> dict:
    """将vnpy SubscribeRequest转换为QTE订阅格式"""
    try:
        return {
            "symbol": vnpy_sub.symbol,
            "exchange": vnpy_sub.exchange.value if hasattr(vnpy_sub.exchange, 'value') else str(vnpy_sub.exchange),
            "data_type": "ticker",  # 默认订阅ticker数据
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise WarningConversionError(f"SubscribeRequest转换失败: {e}")


# ==================== QTE -> vnpy 转换器 ====================

@converter_registry.register(QTEMarketData, TickData)
def convert_qte_market_data_to_tick(qte_data: QTEMarketData) -> TickData:
    """将QTE市场数据转换为vnpy TickData"""
    if not VNPY_AVAILABLE:
        return None
    
    try:
        return TickData(
            symbol=qte_data.symbol,
            exchange=Exchange.OTC,  # 使用OTC交易所代码
            datetime=qte_data.timestamp,
            name=qte_data.symbol,
            volume=PrecisionConverter.to_float(qte_data.volume),
            turnover=PrecisionConverter.to_float(qte_data.price * qte_data.volume),
            open_interest=0,
            last_price=PrecisionConverter.to_float(qte_data.price),
            last_volume=PrecisionConverter.to_float(qte_data.volume),
            limit_up=0,
            limit_down=0,
            open_price=PrecisionConverter.to_float(qte_data.price),
            high_price=PrecisionConverter.to_float(qte_data.price),
            low_price=PrecisionConverter.to_float(qte_data.price),
            pre_close=PrecisionConverter.to_float(qte_data.price),
            bid_price_1=PrecisionConverter.to_float(qte_data.bid_price),
            bid_price_2=0,
            bid_price_3=0,
            bid_price_4=0,
            bid_price_5=0,
            ask_price_1=PrecisionConverter.to_float(qte_data.ask_price),
            ask_price_2=0,
            ask_price_3=0,
            ask_price_4=0,
            ask_price_5=0,
            bid_volume_1=PrecisionConverter.to_float(qte_data.bid_volume),
            bid_volume_2=0,
            bid_volume_3=0,
            bid_volume_4=0,
            bid_volume_5=0,
            ask_volume_1=PrecisionConverter.to_float(qte_data.ask_volume),
            ask_volume_2=0,
            ask_volume_3=0,
            ask_volume_4=0,
            ask_volume_5=0,
            localtime=qte_data.timestamp,
            gateway_name="QTE"
        )
    except Exception as e:
        raise WarningConversionError(f"QTE市场数据转换失败: {e}")


@converter_registry.register(QTEOrderData, OrderData)
def convert_qte_order_to_vnpy(qte_order: QTEOrderData) -> OrderData:
    """将QTE订单数据转换为vnpy OrderData"""
    if not VNPY_AVAILABLE:
        return None
    
    try:
        return OrderData(
            symbol=qte_order.symbol,
            exchange=Exchange.OTC,
            orderid=qte_order.order_id,
            type=OrderTypeConverter.qte_to_vnpy(qte_order.order_type),
            direction=DirectionConverter.qte_to_vnpy(qte_order.side),
            offset=None,  # 现货交易无需offset
            price=PrecisionConverter.to_float(qte_order.price),
            volume=PrecisionConverter.to_float(qte_order.quantity),
            traded=PrecisionConverter.to_float(qte_order.filled_quantity),
            status=StatusConverter.qte_to_vnpy(qte_order.status),
            datetime=qte_order.timestamp,
            reference="",
            gateway_name="QTE"
        )
    except Exception as e:
        raise WarningConversionError(f"QTE订单数据转换失败: {e}")


@converter_registry.register(QTETradeData, TradeData)
def convert_qte_trade_to_vnpy(qte_trade: QTETradeData) -> TradeData:
    """将QTE成交数据转换为vnpy TradeData"""
    if not VNPY_AVAILABLE:
        return None
    
    try:
        return TradeData(
            symbol=qte_trade.symbol,
            exchange=Exchange.OTC,
            orderid=qte_trade.order_id,
            tradeid=qte_trade.trade_id,
            direction=DirectionConverter.qte_to_vnpy(qte_trade.side),
            offset=None,  # 现货交易无需offset
            price=PrecisionConverter.to_float(qte_trade.price),
            volume=PrecisionConverter.to_float(qte_trade.quantity),
            datetime=qte_trade.timestamp,
            gateway_name="QTE"
        )
    except Exception as e:
        raise WarningConversionError(f"QTE成交数据转换失败: {e}")


@converter_registry.register(QTEAccountData, AccountData)
def convert_qte_account_to_vnpy(qte_account: QTEAccountData) -> AccountData:
    """将QTE账户数据转换为vnpy AccountData"""
    if not VNPY_AVAILABLE:
        return None
    
    try:
        # 计算总余额（假设USDT为基准货币）
        total_balance = qte_account.balances.get('USDT', Decimal('0'))
        
        return AccountData(
            accountid=qte_account.account_id,
            balance=PrecisionConverter.to_float(total_balance),
            frozen=0,  # QTE暂不支持冻结资金查询
            gateway_name="QTE"
        )
    except Exception as e:
        raise WarningConversionError(f"QTE账户数据转换失败: {e}")


# ==================== 字典数据转换器 ====================

@converter_registry.register(dict, TickData)
def convert_dict_to_tick_data(data: dict) -> TickData:
    """将字典数据转换为vnpy TickData"""
    if not VNPY_AVAILABLE:
        return None
    
    try:
        # 创建QTE市场数据对象，然后转换
        qte_data = QTEMarketData(
            symbol=data.get('symbol', ''),
            price=PrecisionConverter.to_decimal(data.get('price', 0)),
            volume=PrecisionConverter.to_decimal(data.get('volume', 0)),
            timestamp=data.get('timestamp', datetime.now()),
            bid_price=PrecisionConverter.to_decimal(data.get('bid_price', data.get('price', 0))),
            ask_price=PrecisionConverter.to_decimal(data.get('ask_price', data.get('price', 0))),
            bid_volume=PrecisionConverter.to_decimal(data.get('bid_volume', data.get('volume', 0))),
            ask_volume=PrecisionConverter.to_decimal(data.get('ask_volume', data.get('volume', 0)))
        )
        
        return convert_qte_market_data_to_tick(qte_data)
        
    except Exception as e:
        raise WarningConversionError(f"字典到TickData转换失败: {e}")


@converter_registry.register(dict, OrderData)
def convert_dict_to_order_data(data: dict) -> OrderData:
    """将字典数据转换为vnpy OrderData"""
    if not VNPY_AVAILABLE:
        return None
    
    try:
        # 创建QTE订单数据对象，然后转换
        qte_order = QTEOrderData(
            order_id=data.get('order_id', ''),
            symbol=data.get('symbol', ''),
            side=data.get('side', 'BUY'),
            order_type=data.get('type', 'LIMIT'),
            quantity=PrecisionConverter.to_decimal(data.get('quantity', 0)),
            price=PrecisionConverter.to_decimal(data.get('price', 0)),
            status=data.get('status', 'NEW'),
            filled_quantity=PrecisionConverter.to_decimal(data.get('filled_quantity', 0)),
            timestamp=data.get('timestamp', datetime.now())
        )
        
        return convert_qte_order_to_vnpy(qte_order)
        
    except Exception as e:
        raise WarningConversionError(f"字典到OrderData转换失败: {e}")


# ==================== 转换器工具函数 ====================

def safe_convert(source_obj, target_type, context: str = ""):
    """
    安全转换函数，包含错误处理
    
    Args:
        source_obj: 源对象
        target_type: 目标类型
        context: 转换上下文
        
    Returns:
        转换结果或None（如果转换失败）
    """
    try:
        return converter_registry.convert(source_obj, target_type)
    except ConversionError as e:
        can_continue = error_handler.handle_error(e, context)
        if not can_continue:
            raise
        return None
    except Exception as e:
        # 包装未知错误
        conversion_error = WarningConversionError(f"未知转换错误: {e}")
        can_continue = error_handler.handle_error(conversion_error, context)
        if not can_continue:
            raise conversion_error
        return None


def batch_convert(source_objects: list, target_type, context: str = ""):
    """
    批量转换函数
    
    Args:
        source_objects: 源对象列表
        target_type: 目标类型
        context: 转换上下文
        
    Returns:
        转换结果列表（跳过失败的转换）
    """
    results = []
    for i, obj in enumerate(source_objects):
        obj_context = f"{context}[{i}]"
        result = safe_convert(obj, target_type, obj_context)
        if result is not None:
            results.append(result)
    
    return results


def get_conversion_stats():
    """获取转换统计信息"""
    return {
        "registered_converters": len(converter_registry.list_converters()),
        "converter_list": [
            f"{src.__name__} -> {tgt.__name__}" 
            for src, tgt in converter_registry.list_converters()
        ],
        "error_stats": error_handler.get_error_stats()
    }


# 初始化日志
import logging
logging.getLogger(__name__).info(f"QTE事件转换器已加载，注册转换器数量: {len(converter_registry.list_converters())}") 