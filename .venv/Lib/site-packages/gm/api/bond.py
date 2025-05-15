# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

from typing import Text, List, Dict, Any

from gm.enum import OrderDuration_Unknown, OrderQualifier_Unknown, OrderType_Unknown
from gm.pb.account_pb2 import Order, OrderType_Limit, OrderBusiness_BOND_RRP, \
    OrderBusiness_BOND_CONVERTIBLE_CALL, OrderBusiness_BOND_CONVERTIBLE_PUT, OrderBusiness_BOND_CONVERTIBLE_PUT_CANCEL
from .trade import _inner_place_order


def bond_reverse_repurchase_agreement(symbol, volume, price,
                                      order_type=OrderType_Limit,
                                      order_duration=OrderQualifier_Unknown,
                                      order_qualifier=OrderQualifier_Unknown,
                                      account_id=''
                                      ):
    # type: (Text, int, float, int, int, int, Text) -> List[Dict[Text, Any]]
    """
    国债逆回购
    :param symbol:                  标的
    :param volume:                  数量
    :param price:                   价格
    :param order_type:              委托类型
    :param order_duration:          委托时间属性
    :param order_qualifier:         委托成交属性
    :param account_id:              账户ID，不指定则使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = price
    o.order_type = order_type
    o.order_business = OrderBusiness_BOND_RRP
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.account_id = account_id
    return _inner_place_order(o)


def bond_convertible_call(symbol, volume, price=0.0, account_id=''):
    # type: (Text, int, float, Text) -> List[Dict[Text, Any]]
    """
    可转债转股
    :param symbol:                  标的
    :param volume:                  数量
    :param price:                   价格
    :param account_id:              账户ID，不指定则使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = price
    o.order_type = OrderType_Unknown
    o.order_business = OrderBusiness_BOND_CONVERTIBLE_CALL
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def bond_convertible_put(symbol, volume, price=0.0, account_id=''):
    # type: (Text, int, float, Text) -> List[Dict[Text, Any]]
    """
    可转债回售
    :param symbol:                  标的
    :param volume:                  数量
    :param price:                   价格
    :param account_id:              账户ID，不指定则使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = price
    o.order_type = OrderType_Unknown
    o.order_business = OrderBusiness_BOND_CONVERTIBLE_PUT
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def bond_convertible_put_cancel(symbol, volume, account_id=''):
    # type: (Text, int, Text) -> List[Dict[Text, Any]]
    """
    可转债回售撤销
    :param symbol:                  标的
    :param volume:                  数量
    :param account_id:              账户ID，不指定则使用默认账户
    :return:
    """
    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = 0.0
    o.order_type = OrderType_Unknown
    o.order_business = OrderBusiness_BOND_CONVERTIBLE_PUT_CANCEL
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)