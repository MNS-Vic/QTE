from typing import List, Dict

from datetime import datetime
import pandas as pd

from gm.api._errors import check_gm_status
from gm.csdk.c_sdk import (
    py_gmi_get_symbol_infos,
    py_gmi_get_symbols_v2,
    py_gmi_get_history_symbol,
    py_get_trading_dates_by_year,
    py_gmi_get_trading_session,
    py_gmi_get_contract_expire_rest_days,

    py_gmi_get_previous_n_trading_dates,
    py_gmi_get_next_n_trading_dates,
)
from gm.pb_to_dict import protobuf_to_dict
from gm.pb.instrument_service_pb2 import (
    GetSymbolInfosReq, GetSymbolInfosResp,
    GetSymbolsReq, GetSymbolsResp,
    GetHistorySymbolReq, GetHistorySymbolResp,
    GetTradingDatesByYearReq, GetTradingDatesByYearResp,
    GetTradingSessionReq, GetTradingSessionResp,
    GetContractExpireRestDaysReq, GetContractExpireRestDaysResp,

    GetTradingDatesPrevNReq, GetTradingDatesPrevNResp,
    GetTradingDatesNextNReq, GetTradingDatesNextNResp,
)
from gm.api._utils import _timestamp_to_str


def _datetime_to_str(value):
    if pd.notnull(value):
        return value.strftime("%Y-%m-%d")
    return ""


def get_symbol_infos(sec_type1, sec_type2=0, exchanges=None, symbols=None, df=False):
    # type: (int, int, str|List[str], str|List[str], bool) -> List[Dict]|pd.DataFrame
    """
    查询标的基本信息
    """
    if exchanges is None:
        exchanges = []
    elif isinstance(exchanges, str):
        exchanges = [exchange.strip() for exchange in exchanges.split(",")]
    if symbols is None:
        symbols = []
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    req = GetSymbolInfosReq(
        sec_type1=sec_type1,
        sec_type2=sec_type2,
        exchanges=exchanges,
        symbols=symbols,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_symbol_infos(req)
    check_gm_status(status)
    rsp = GetSymbolInfosResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("symbol_infos", [])   # type: List[Dict]

    for item in data:
        if 'delisting_begin_date' in item and item['delisting_begin_date'] != "":
            item['delisting_begin_date'] = datetime.strptime(item['delisting_begin_date'], '%Y-%m-%d')

    if df:
        data = pd.DataFrame(data)
    return data


def get_symbols(sec_type1, sec_type2=0, exchanges=None, symbols=None, skip_suspended=True, skip_st=True, trade_date="", df=False):
    # type: (int, int, str|List[str], str|List[str], bool, bool, str, bool) -> List[Dict]|pd.DataFrame
    """
    查询指定交易日多标的交易信息
    """
    if exchanges is None:
        exchanges = []
    elif isinstance(exchanges, str):
        exchanges = [exchange.strip() for exchange in exchanges.split(",")]
    if symbols is None:
        symbols = []
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    req = GetSymbolsReq(
        sec_type1=sec_type1,
        sec_type2=sec_type2,
        exchanges=exchanges,
        symbols=symbols,
        skip_suspended=skip_suspended,
        skip_st=skip_st,
        trade_date=trade_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_symbols_v2(req)
    check_gm_status(status)
    data = []
    rsp = GetSymbolsResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("symbols", [])   # type: List[Dict]
    for item in data:
        item.update(item["info"])
        del item["info"]

        if 'delisting_begin_date' in item and item['delisting_begin_date'] != "":
            item['delisting_begin_date'] = datetime.strptime(item['delisting_begin_date'], '%Y-%m-%d')
    if df:
        data = pd.DataFrame(data)
    return data


def get_history_symbol(symbol, start_date="", end_date="", df=False):
    # type: (str, str, str, bool) -> List[Dict]|pd.DataFrame
    """
    查询指定标的多日交易信息
    """
    req = GetHistorySymbolReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_history_symbol(req)
    check_gm_status(status)
    rsp = GetHistorySymbolResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("symbols", [])   # type: List[Dict]
    for item in data:
        item.update(item["info"])
        del item["info"]

        if 'delisting_begin_date' in item and item['delisting_begin_date'] != "":
            item['delisting_begin_date'] = datetime.strptime(item['delisting_begin_date'], '%Y-%m-%d')
    if df:
        data = pd.DataFrame(data)
    return data


def get_trading_dates_by_year(exchange, start_year, end_year):
    # type: (str, int, int) -> pd.DataFrame
    """查询年度交易日历"""
    req = GetTradingDatesByYearReq(
        exchange=exchange,
        start_year=start_year,
        end_year=end_year,
    )
    req = req.SerializeToString()
    status, result = py_get_trading_dates_by_year(req)
    check_gm_status(status)

    data = []
    rsp = GetTradingDatesByYearResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("dates", [])
    return pd.DataFrame(data).applymap(_datetime_to_str)


def get_trading_session(symbols, df=False):
    # type: (str|List[str], bool) -> List
    """
    查询交易日的可交易时段
    """
    if isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]
    req = GetTradingSessionReq(
        symbols=symbols,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_trading_session(req)
    check_gm_status(status)
    rsp = GetTradingSessionResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("trading_sessions", [])   # type: List[Dict]
    if df:
        data = pd.DataFrame(data)
    return data


def get_contract_expire_rest_days(symbols, start_date="", end_date="", trade_flag=False, df=False):
    # type: (str|List[str], str, str, bool, bool) -> List
    """
    查询合约到期剩余天数
    """
    if isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]
    req = GetContractExpireRestDaysReq(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        by_trading_days=trade_flag,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_contract_expire_rest_days(req)
    check_gm_status(status)

    rsp = GetContractExpireRestDaysResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("contract_expire_rest_days", [])   # type: List[Dict]
    for value in data:
        if value["days_to_expire"] == "":
            value["days_to_expire"] = None
        else:
            value["days_to_expire"] = int(value["days_to_expire"])

    if df:
        data = pd.DataFrame(data)
    return data


def get_previous_n_trading_dates(exchange, date, n=1):
    # type: (str, str, int) -> List[str]
    """
    查询指定日期的前n个交易日
    """
    req = GetTradingDatesPrevNReq(
        exchange=exchange,
        date=date,
        n=n,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_previous_n_trading_dates(req)
    check_gm_status(status)

    rsp = GetTradingDatesPrevNResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp)
    data = result.get("trading_dates", [])
    return [_timestamp_to_str(x, is_utc_time=True, datetime_to_str=True) for x in data]


def get_next_n_trading_dates(exchange, date, n=1):
    # type: (str, str, int) -> List[str]
    """
    查询指定日期的后n个交易日
    """
    req = GetTradingDatesNextNReq(
        exchange=exchange,
        date=date,
        n=n,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_next_n_trading_dates(req)
    check_gm_status(status)

    rsp = GetTradingDatesNextNResp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("trading_dates", [])   # type: List[str]
    return [_timestamp_to_str(x, is_utc_time=True, datetime_to_str=True) for x in data]
