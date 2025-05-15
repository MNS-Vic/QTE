# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

from typing import Text, List, Dict, Any

import pandas as pd
from gm.csdk.c_sdk import c_status_fail, \
    py_gmi_get_ipo_quota_pb, py_gmi_get_ipo_instruments_pb, \
    py_gmi_get_ipo_match_number_pb, py_gmi_get_ipo_lot_info_pb

from gm.enum import OrderQualifier_Unknown, OrderDuration_Unknown
from gm.pb.account_pb2 import Order, OrderType_Limit, OrderBusiness_IPO_BUY
from gm.pb.data_pb2 import SecurityType
from gm.pb.trade_ipo_service_pb2 import *
from gm.pb_to_dict import protobuf_to_dict
from .trade import _inner_place_order
from ..utils import str2datetime


def ipo_buy(symbol, volume, price, account_id=''):
    # type: (Text, int, float, Text) -> List[Dict[str, Any]]
    """
    新股/新债申购
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
    o.order_business = OrderBusiness_IPO_BUY
    o.order_qualifier = OrderQualifier_Unknown
    o.order_duration = OrderDuration_Unknown
    o.account_id = account_id
    return _inner_place_order(o)


def ipo_get_quota(account_id=''):
    # type: (Text) -> List[Dict[str, Any]]
    """
    查询新股申购额度
    :param account_id:  账户ID，不指定则使用默认账户
    :return:
    """
    req = GetIPOQuotaReq(account_id=account_id)
    req = req.SerializeToString()
    status, result = py_gmi_get_ipo_quota_pb(req)
    if c_status_fail(status, 'py_gmi_get_ipo_quota_pb') or not result:
        return None
    res = GetIPOQuotaRsp()
    res.ParseFromString(result)
    res = protobuf_to_dict(res)
    return res.get('data', None)


def ipo_get_instruments(sec_type, account_id='', df=False):
    # type: (SecurityType, Text, bool) -> List[Dict[str, Any]]
    """
    查询当日新股/新债清单
    :param account_id:      账户ID，不指定则使用默认账户
    :param df:              是否显示为 DataFrame
    :return:
    """
    req = GetIPOInstrumentsReq(sec_type=sec_type, account_id=account_id)
    req = req.SerializeToString()
    status, result = py_gmi_get_ipo_instruments_pb(req)
    if c_status_fail(status, 'py_gmi_get_ipo_instruments_pb') or not result:
        return None
    res = GetIPOInstrumentsRsp()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(item, is_utc_time=True, including_default_value_fields=True) for item in res.data]
    return datas if not df else pd.DataFrame(datas)


def ipo_get_match_number(start_time, end_time, account_id='', df=False):
    # type: (Text, Text, Text, bool) -> List[Dict[str, Any]]
    """
    配号查询
    :param start_time: 开始时间
    :param end_time: 结束时间
    :param account_id: 账号id
    :param df:
    :return:
    """
    # 日期整数格式
    start_time = int(str2datetime(start_time).strftime("%Y%m%d"))
    end_time = int(str2datetime(end_time).strftime("%Y%m%d"))

    req = GetIPOMatchNumberReq(start_date=start_time, end_date=end_time, account_id=account_id)
    req = req.SerializeToString()
    status, result = py_gmi_get_ipo_match_number_pb(req)
    if c_status_fail(status, 'py_gmi_get_ipo_match_number_pb') or not result:
        return None
    res = GetIPOMatchNumberRsp()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(item, is_utc_time=True, including_default_value_fields=True) for item in res.data]
    return datas if not df else pd.DataFrame(datas)


def ipo_get_lot_info(start_time, end_time, account_id='', df=False):
    # type: (Text, Text, Text, bool) -> List[Dict[str, Any]]
    """
    中签查询
    :param account_id:      账户ID，不指定则使用默认账户
    :param df:              是否显示为 DataFrame
    :return:
    """
    # 日期整数格式
    start_time = int(str2datetime(start_time).strftime("%Y%m%d"))
    end_time = int(str2datetime(end_time).strftime("%Y%m%d"))

    req = GetIPOLotInfoReq(start_date=start_time, end_date=end_time, account_id=account_id)
    req = req.SerializeToString()
    status, result = py_gmi_get_ipo_lot_info_pb(req)
    if c_status_fail(status, 'py_gmi_get_ipo_lot_info_pb') or not result:
        return None
    res = GetIPOLotInfoRsp()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(item, is_utc_time=True, including_default_value_fields=True) for item in res.data]
    return datas if not df else pd.DataFrame(datas)
