# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

from typing import Text, List, Dict, Any

from gm.enum import OrderQualifier_Unknown, OrderDuration_Unknown
from gm.pb.account_pb2 import Order, OrderType_Limit, OrderBusiness_FUND_BUY, OrderBusiness_ETF_BUY, \
    OrderBusiness_ETF_RED, OrderBusiness_FUND_SUB, OrderBusiness_FUND_RED
from .trade import _inner_place_order


def fund_etf_buy(symbol, volume, price, account_id=''):
    # type: (Text, int, float, Text) -> List[Dict[Text, Any]]
    """
    ETF申购
    :param symbol:          标的
    :param volume:          数量
    :param price:           价格
    :param account_id:      账户ID，不指定则使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = price
    o.order_type = OrderType_Limit
    o.order_business = OrderBusiness_ETF_BUY
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def fund_etf_redemption(symbol, volume, price, account_id=''):
    # type: (Text, int, float, Text) -> List[Dict[Text, Any]]
    """
    ETF赎回
    :param symbol:          标的
    :param volume:          数量
    :param price:           价格
    :param account_id:      账户ID，不指定则使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = price
    o.order_type = OrderType_Limit
    o.order_business = OrderBusiness_ETF_RED
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def fund_subscribing(symbol, volume, account_id=''):
    # type: (Text, int, Text) -> List[Dict[Text, Any]]
    """
    基金认购
    :param symbol:          标的
    :param volume:          数量
    :param account_id:      账户ID，不指定这使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.order_type = OrderType_Limit
    o.order_business = OrderBusiness_FUND_SUB
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def fund_buy(symbol, volume, account_id=''):
    # type: (Text, int, Text) -> List[Dict[Text, Any]]
    """
    基金申购
    :param symbol:          标的
    :param volume:          数量
    :param account_id:      账户ID，不指定这使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.order_type = OrderType_Limit
    o.order_business = OrderBusiness_FUND_BUY
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def fund_redemption(symbol, volume, account_id=''):
    # type: (Text, int, Text) -> List[Dict[Text, Any]]
    """
    基金赎回
    :param symbol:          标的
    :param volume:          数量
    :param account_id:      账户ID，不指定这使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.order_type = OrderType_Limit
    o.order_business = OrderBusiness_FUND_RED
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)
