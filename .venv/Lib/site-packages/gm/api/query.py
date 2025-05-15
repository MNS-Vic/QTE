from gm.api._errors import check_gm_status, GmError
from gm.csdk.c_sdk import (
    py_gmi_get_fundamentals,
    py_gmi_get_fundamentals_n,
    py_gmi_get_instrumentInfos,
    py_gmi_get_history_instruments,
    py_gmi_get_constituents,
    py_gmi_get_industry,
    py_gmi_get_concept,
    py_gmi_get_trading_dates,
    py_gmi_get_previous_trading_date,
    py_gmi_get_next_trading_date,
    py_gmi_get_dividends,
    py_gmi_get_continuous_contracts,
    py_gmi_get_varietyinfos,
    py_gmi_get_trading_times_ext,
    py_gmi_option_get_symbols_by_exchange,
    py_gmi_option_get_symbols_by_in_at_out,
    py_gmi_option_get_delisted_dates,
    py_gmi_option_get_exercise_prices,
    py_gmi_history_ticks_pb,
    py_gmi_history_bars_pb,
    py_gmi_history_ticks_n_pb,
    py_gmi_history_bars_n_pb,
    py_gmi_get_instruments,
    py_gmi_get_convertible_bond_call_info,
    py_gmi_get_instrument_pools_pb,
    py_gmi_get_instrument_pool_by_name_pb,
    py_gmi_set_instrument_pool_symbols_pb,
    py_gmi_del_instrument_pool_by_name_pb,

)

from gm.pb.instrument_pool_service_pb2 import (
    InstrumentPool, AddInstrumentPoolReq, AddInstrumentPoolRsp,
    DelInstrumentPoolReq, SetInstrumentPoolNameReq, SetInstrumentPoolSymbolsReq,
    GetInstrumentPoolsReq, GetInstrumentPoolsRsp, GetInstrumentPoolByIdReq,
)

from gm.pb.account_pb2 import Cashes, Positions
from gm.pb.fundamental_pb2 import (
    GetConvertibleBondCallInfoReq, GetConvertibleBondCallInfoRsp, GetFundamentalsReq, GetFundamentalsRsp,
    GetFundamentalsNReq, GetInstrumentInfosReq, GetHistoryInstrumentsReq, GetConstituentsReq,
    GetInstrumentsReq, GetOptionDelistedDatesReq, GetOptionDelistedDatesRsp,
    GetOptionExercisePricesReq, GetOptionExercisePricesRsp, GetOptionSymbolsByExchangeReq, GetOptionSymbolsByExchangeRsp,
    GetOptionSymbolsByInAtOutReq, GetOptionSymbolsByInAtOutRsp, GetIndustryReq, GetIndustryRsp,
    GetConceptReq, GetConceptRsp, GetTradingDatesReq, GetTradingDatesRsp,
    GetPreviousTradingDateReq, GetPreviousTradingDateRsp, GetNextTradingDateReq, GetNextTradingDateRsp,
    GetDividendsReq, GetContinuousContractsReq, GetTradingTimesExtReq, GetTradingTimesExtRsp, GetVarietyInfosReq,
)
from gm.pb.data_pb2 import (
    InstrumentInfos,
    Instruments,
    Constituents,
    Dividends,
    ContinuousContracts,
    VarietyInfos,
)
import json
import zlib
from typing import Any, Text, List, Dict, Optional
from datetime import datetime as Datetime, date as Date

import pandas as pd

from gm import utils
from gm.constant import DATA_TYPE_TICK
from gm.csdk.c_sdk import py_gmi_history_ticks_l2, py_gmi_history_bars_l2, \
    py_gmi_history_transaction_l2, py_gmi_history_order_l2, py_gmi_history_order_queue_l2,\
    py_gmi_raw_func
from gm.enum import ADJUST_NONE
from gm.pb.data_pb2 import Ticks, Bars, L2Transactions, L2Orders, L2OrderQueues
# history 和 history level2 拆分成不同的proto文件进行重新定义了。这里不能直接用这样的路径引入.
# from gm.pb.history_pb2 import GetHistoryL2TicksReq, GetHistoryL2BarsReq, GetHistoryL2TransactionsReq
from gm.pb.history_l2_pb2 import GetHistoryL2TicksReq, GetHistoryL2BarsReq, GetHistoryL2TransactionsReq, GetHistoryL2OrdersReq, GetHistoryL2OrderQueuesReq
from gm.pb.history_pb2 import GetHistoryBarsNReq, GetHistoryBarsReq, GetHistoryTicksNReq, GetHistoryTicksReq
from gm.pb.trade_pb2 import GetCashReq, GetPositionsReq
from gm.pb.trade_rawfunc_service_pb2 import RawFuncReq, RawFuncRsp
from gm.pb_to_dict import protobuf_to_dict
from gm.utils import standard_fields, gmsdklogger, utc_datetime2beijing_datetime
from gm.api._utils import (
    unfold_field, rename_field, filter_field,
    param_convert_iter_to_str, param_convert_datetime, param_convert_date,
    param_convert_iter_to_list, param_convert_date_with_time,
)
from gm.csdk import gmpytool
from gm.csdk.c_sdk import c_status_fail, py_gmi_get_cash_pb_v2, py_gmi_get_positions_pb_v2

# 兼容 Pandas 1.4.0 版本, 之前的不做改动防止出错
try:
    _pd_version = pd.__version__.split(".")
    if int(_pd_version[0]) >= 2 or (int(_pd_version[0]) >= 1 and int(_pd_version[1]) >= 4):
        pd.set_option('display.precision', 8)
    else:
        pd.set_option('precision', 8)
except:
    pd.set_option('precision', 8)


def get_fundamentals(table, symbols, start_date, end_date,
                     fields=None, filter=None, order_by=None, limit=1000, df=False,
                     ):
    # type: (str, str|List, str|Datetime|Date, str|Datetime|Date, str|List, str, str, int, bool) -> List[Dict]|pd.DataFrame
    """
    查询基本面财务数据(已弃用)
    """

    gmsdklogger.warning(f"函数[get_fundamentals]已弃用, 请切换新版数据函数[stk_get_fundamentals_balance, "
                        f"stk_get_fundamentals_cashflow,"
                        f"stk_get_fundamentals_income, stk_get_finance_prime, stk_get_finance_deriv, "
                        f"stk_get_daily_valuation, stk_get_daily_mktvalue, stk_get_daily_basic]")

    symbols = param_convert_iter_to_str(symbols)
    start_date = param_convert_date(start_date)
    end_date = param_convert_date(end_date)
    fields = param_convert_iter_to_str(fields)

    req = GetFundamentalsReq(
        table=table,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        filter=filter,
        order_by=order_by,
        limit=limit,
    )
    status, result = py_gmi_get_fundamentals(req.SerializeToString())
    check_gm_status(status)
    rsp = GetFundamentalsRsp()
    rsp.ParseFromString(result)
    ret = []
    # 需要把 fields 里嵌套的字段展开
    for item in rsp.data:  # type: GetFundamentalsRsp.Fundamental
        r = {
            'symbol': item.symbol,
            'pub_date': utils.utc_datetime2beijing_datetime(item.pub_date.ToDatetime()),
            'end_date': utils.utc_datetime2beijing_datetime(item.end_date.ToDatetime()),
            **item.fields,
        }
        ret.append(r)
    if df:
        return pd.DataFrame(ret)
    return ret


def get_fundamentals_n(table, symbols, end_date,
                       fields="", filter="", order_by="", count=1, df=False):
    # type: (str, str|List, str|Datetime|Date, str, str, str, int, bool) -> List[Dict]|pd.DataFrame
    """
    查询基本面财务数据,每个股票在end_date的前n条(已弃用)
    """

    gmsdklogger.warning(
        f"函数[get_fundamentals_n]已弃用, 请切换新版数据函数[stk_get_fundamentals_balance_pt, stk_get_fundamentals_cashflow_pt, "
        f"stk_get_fundamentals_income_pt, stk_get_finance_prime_pt, stk_get_finance_deriv_pt, "
        f"stk_get_daily_valuation_pt, stk_get_daily_mktvalue_pt, stk_get_daily_basic_pt]")

    symbols = param_convert_iter_to_str(symbols)
    end_date = param_convert_date(end_date)
    fields = param_convert_iter_to_str(fields)

    req = GetFundamentalsNReq(
        table=table,
        symbols=symbols,
        end_date=end_date,
        fields=fields,
        filter=filter,
        order_by=order_by,
        count=count,
    )
    status, result = py_gmi_get_fundamentals_n(req.SerializeToString())
    check_gm_status(status)
    rsp = GetFundamentalsRsp()
    rsp.ParseFromString(result)
    ret = []
    # 需要把 fields 里嵌套的字段展开
    for item in rsp.data:  # type: GetFundamentalsRsp.Fundamental
        r = {
            'symbol': item.symbol,
            'pub_date': utils.utc_datetime2beijing_datetime(item.pub_date.ToDatetime()),
            'end_date': utils.utc_datetime2beijing_datetime(item.end_date.ToDatetime()),
            **item.fields,
        }
        ret.append(r)
    if df:
        return pd.DataFrame(ret)
    return ret


def get_instruments(symbols=None, exchanges=None, sec_types=None, names=None,
                    skip_suspended=True, skip_st=True, fields=None, df=False):
    # type: (str|List, str|List, str|List|int, str|List, bool, bool, str|List, bool) -> List[Dict]|pd.DataFrame
    """
    查询最新交易标的信息,有基本数据及最新日频数据
    """
    symbols = param_convert_iter_to_str(symbols)
    exchanges = param_convert_iter_to_str(exchanges)
    if isinstance(sec_types, int):
        sec_types = str(sec_types)
    else:
        sec_types = param_convert_iter_to_str(sec_types)
    names = param_convert_iter_to_str(names)
    fields = param_convert_iter_to_list(fields)

    req = GetInstrumentsReq(
        symbols=symbols,
        exchanges=exchanges,
        sec_types=sec_types,
        names=names,
        skip_st=skip_st,
        skip_suspended=skip_suspended,
        #fields=",".join(fields),
    )
    # 字段处理
    # created_at 转 trade_date
    # listed_date, delisted_date, conversion_start_date 转北京时间 datetime 类型
    # is_adjusted 根据 is_strike_price_adjusted 取 1 或 0
    status, result = py_gmi_get_instruments(req.SerializeToString())
    check_gm_status(status)
    rsp = Instruments()
    rsp.ParseFromString(result)
    # ret = protobuf_to_dict(rsp).get("data", [])
    ret = []
    for item in rsp.data:  # type: Instrument
        r = protobuf_to_dict(item)
        if "info" in r:
            r.update(r.pop("info"))
        r["trade_date"] = r.pop("created_at")
        #is_adjusted 字段需要替换为 is_strike_price_adjusted 字段
        r["is_adjusted"] = int(r.pop('is_strike_price_adjusted'))
        if fields:
            new_r = {}
            for field in fields:
                if field in r:
                    new_r[field] = r[field]
            r = new_r
        ret.append(r)
    if df:
        return pd.DataFrame(ret)
    return ret


def get_history_instruments(symbols, fields=None, start_date=None, end_date=None, df=False):
    # type: (str|List, str|List, str|Datetime|Date, str|Datetime|Date, bool) -> List[Dict]|pd.DataFrame
    """
    返回指定的symbols的标的日指标数据
    """
    symbols = param_convert_iter_to_str(symbols)
    fields = param_convert_iter_to_list(fields)
    start_date = param_convert_date(start_date)
    end_date = param_convert_date(end_date)

    # 不要传 fields, 否则可能没有 info 字段
    req = GetHistoryInstrumentsReq(
        symbols=symbols,
        # fields=fields,
        start_date=start_date,
        end_date=end_date,
    )
    status, result = py_gmi_get_history_instruments(req.SerializeToString())
    check_gm_status(status)
    rsp = Instruments()
    rsp.ParseFromString(result)

    # 字段处理
    # created_at 转 trade_date, exercise_price 转 strike_price
    # listed_date, delisted_date, conversion_start_date 转北京时间 datetime 类型
    # is_adjusted 根据 is_strike_price_adjusted 取 1 或 0
    ret = []
    for item in rsp.data:  # type: Instrument
        r = protobuf_to_dict(item)
        # 不要让info内的conversion_price覆盖外部conversion_price
        if "info" in r and "conversion_price" in r["info"]:
            del r["info"]["conversion_price"]
        unfold_field(r, "info")
        rename_field(r, "trade_date", "created_at")
        rename_field(r, "exercise_price", "strike_price")
        rename_field(r, "is_adjusted", "is_strike_price_adjusted")
        # 过滤字段
        r = filter_field(r, fields)
        ret.append(r)

    if df:
        return pd.DataFrame(ret)
    return ret


def get_instrumentinfos(symbols=None, exchanges=None, sec_types=None,
                        names=None, fields=None, df=False):
    # type: (str|List, str|List, str|List|int, str|List, str|List, bool) -> List[Dict]|pd.DataFrame
    """
    查询交易标的基本信息
    如果没有数据的话,返回空列表. 有的话, 返回list[dict]这样的列表. 其中 listed_date, delisted_date 为 datetime 类型
    @:param fields: 可以是 'symbol, sec_type' 这样的字符串, 也可以是 ['symbol', 'sec_type'] 这样的字符list
    """
    symbols = param_convert_iter_to_str(symbols)
    exchanges = param_convert_iter_to_str(exchanges)
    if isinstance(sec_types, int):
        sec_types = str(sec_types)
    else:
        sec_types = param_convert_iter_to_str(sec_types)
    names = param_convert_iter_to_str(names)
    fields = param_convert_iter_to_str(fields)

    req = GetInstrumentInfosReq(
        symbols=symbols,
        exchanges=exchanges,
        sec_types=sec_types,
        names=names,
        fields=fields,
    )
    status, result = py_gmi_get_instrumentInfos(req.SerializeToString())
    check_gm_status(status)
    rsp = InstrumentInfos()
    rsp.ParseFromString(result)

    ret = []
    for item in rsp.data:  # type: InstrumentInfo
        r = protobuf_to_dict(item)
        ret.append(r)

    if df:
        return pd.DataFrame(ret)
    return ret


def get_constituents(index, fields=None, df=False):
    # type: (str, str|List, bool) -> List[str]|pd.DataFrame
    """
    查询指数最新成分股(已弃用, 请切换新版数据函数stk_get_index_constituents)
    返回的list每项是个字典,包含的key值有:
    symbol 股票symbol
    weight 权重
    """

    gmsdklogger.warning("函数[get_constituents]已弃用, 请切换新版数据函数[stk_get_index_constituents]")

    fields = param_convert_iter_to_str(fields)
    req = GetConstituentsReq(
        index=index,
        fields=fields,
    )
    status, result = py_gmi_get_constituents(req.SerializeToString())
    check_gm_status(status)
    rsp = Constituents()
    rsp.ParseFromString(result)
    ret = []
    if len(rsp.data) > 0:
        for k, v in rsp.data[0].constituents.items():
            if fields is None or fields == "symbol":
                r = {"symbol": k}
            else:
                r = {"symbol": k, "weight": v}
            ret.append(r)
    if df:
        return pd.DataFrame(ret)
    return ret


def get_history_constituents(index, start_date=None, end_date=None):
    # type: (str, str|Datetime, str|Datetime|Date) -> List[Dict]
    """
    查询指数历史成分股(已弃用, 请切换新版数据函数stk_get_index_constituents)
    返回的list每项是个字典,包含的key值有:
    trade_date: 交易日期(datetime类型)
    constituents: 一个字典. 每个股票的sybol做为key值, weight做为value值
    """

    gmsdklogger.warning("函数[get_history_constituents]已弃用, 请切换新版数据函数[stk_get_index_constituents]")

    start_date = param_convert_date(start_date)
    end_date = param_convert_date(end_date)

    req = GetConstituentsReq(
        index=index,
        start_date=start_date,
        end_date=end_date,
    )
    status, result = py_gmi_get_constituents(req.SerializeToString())
    check_gm_status(status)
    rsp = Constituents()
    rsp.ParseFromString(result)

    ret = []
    for item in rsp.data:
        r = {
            'trade_date': utils.utc_datetime2beijing_datetime(item.created_at.ToDatetime()),
            'constituents': dict(item.constituents),
        }
        ret.append(r)
    return ret


def get_sector(code):
    """
    查询板块股票列表
    """
    # TODO 没有数据, 先不实现
    return []


def get_industry(code):
    # type: (str) -> List[str]
    """
    查询行业股票列表(已弃用, 请切换新版数据函数stk_get_industry_constituents)
    """

    gmsdklogger.warning("函数[get_industry]已弃用, 请切换新版数据函数[stk_get_industry_constituents]")

    req = GetIndustryReq(
        code=code,
    )
    status, result = py_gmi_get_industry(req.SerializeToString())
    check_gm_status(status)
    rsp = GetIndustryRsp()
    rsp.ParseFromString(result)
    ret = [item for item in rsp.symbols]
    return ret


def get_concept(code):
    # type: (str) -> List[str]
    """
    查询概念股票列表
    """
    req = GetConceptReq(
        code=code,
    )
    status, result = py_gmi_get_concept(req.SerializeToString())
    check_gm_status(status)
    rsp = GetConceptRsp()
    rsp.ParseFromString(result)
    ret = [item for item in rsp.symbols]
    return ret


def get_trading_dates(exchange, start_date, end_date):
    # type: (str, str|Datetime|Date, str|Datetime|Date) -> List[str]
    """
    查询交易日列表
    如果指定的市场不存在, 返回空列表. 有值的话,返回 yyyy-mm-dd 格式的列表
    """
    exchange = utils.to_exchange(exchange)
    sdate = param_convert_date(start_date)
    edate = param_convert_date(end_date)

    req = GetTradingDatesReq(
        exchange=exchange,
        start_date=sdate,
        end_date=edate,
    )
    status, result = py_gmi_get_trading_dates(req.SerializeToString())
    check_gm_status(status)
    rsp = GetTradingDatesRsp()
    rsp.ParseFromString(result)

    ds = []
    for t in rsp.dates:  # type: Timestamp
        ds.append(utils.utc_datetime2beijing_datetime(
            t.ToDatetime()).strftime('%Y-%m-%d'))
    return ds


def get_previous_trading_date(exchange, date):
    # type: (str, str|Datetime|Date) -> str
    """
    返回指定日期的上一个交易日
    @:param exchange: 交易市场
    @:param date: 指定日期, 可以是datetime.date 或者 datetime.datetime 类型. 或者是 yyyy-mm-dd 或 yyyymmdd 格式的字符串
    @:return 返回下一交易日, 为 yyyy-mm-dd 格式的字符串, 如果不存在则返回None
    """
    exchange = utils.to_exchange(exchange)
    date = param_convert_date(date)

    req = GetPreviousTradingDateReq(exchange=exchange, date=date)
    status, result = py_gmi_get_previous_trading_date(req.SerializeToString())
    check_gm_status(status)
    rsp = GetPreviousTradingDateRsp()
    rsp.ParseFromString(result)
    rdate = rsp.date
    #! 这里应该触发异常
    if not rdate.ListFields():  # 这个说明查询结果没有
        return None
    return utils.utc_datetime2beijing_datetime(rdate.ToDatetime()).strftime('%Y-%m-%d')


def get_next_trading_date(exchange, date):
    # type: (str, str|Datetime|Date) -> str
    """
    返回指定日期的下一个交易日
    @:param exchange: 交易市场
    @:param date: 指定日期, 可以是datetime.date 或者 datetime.datetime 类型. 或者是 yyyy-mm-dd 或 yyyymmdd 格式的字符串
    @:return 返回下一交易日, 为 yyyy-mm-dd 格式的字符串, 如果不存在则返回None
    """
    exchange = utils.to_exchange(exchange)
    date = param_convert_date(date)
    req = GetNextTradingDateReq(exchange=exchange, date=date)
    status, result = py_gmi_get_next_trading_date(req.SerializeToString())
    check_gm_status(status)
    rsp = GetNextTradingDateRsp()
    rsp.ParseFromString(result)
    rdate = rsp.date
    #! 这里应该触发异常
    if not rdate.ListFields():  # 这个说明查询结果没有
        return None
    return utils.utc_datetime2beijing_datetime(rdate.ToDatetime()).strftime('%Y-%m-%d')


def get_dividend(symbol, start_date, end_date=None, df=False):
    # type: (str, str|Datetime|Date, str|Datetime|Date, bool) -> List[Dict]|pd.DataFrame
    """
    查询分红送配
    """
    start_date = param_convert_date(start_date)
    end_date = param_convert_date(end_date)
    req = GetDividendsReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    status, result = py_gmi_get_dividends(req.SerializeToString())
    check_gm_status(status)
    rsp = Dividends()
    rsp.ParseFromString(result)

    ret = []
    for item in rsp.data:  # type: Dividend
        r = protobuf_to_dict(item)
        ret.append(r)

    if df:
        return pd.DataFrame(ret)
    return ret


def get_continuous_contracts(csymbol, start_date=None, end_date=None):
    # type: (str, str|Datetime|Date, str|Datetime|Date) -> List[Dict]
    """
    获取连续合约
    """

    start_date = param_convert_date(start_date)
    end_date = param_convert_date(end_date)
    req = GetContinuousContractsReq(
        csymbol=csymbol,
        start_date=start_date,
        end_date=end_date,
    )
    status, result = py_gmi_get_continuous_contracts(req.SerializeToString())
    check_gm_status(status)
    rsp = ContinuousContracts()
    rsp.ParseFromString(result)
    result = []
    for cc in rsp.data:  # type: ContinuousContract
        row = {'symbol': cc.symbol, 'trade_date': utils.utc_datetime2beijing_datetime(
            cc.created_at.ToDatetime())}
        result.append(row)
    return result


def history(symbol, frequency, start_time, end_time, fields=None,
            skip_suspended=True, fill_missing=None, adjust=None,
            adjust_end_time='', df=False):
    # type: (str|List, str, str|Datetime|Date, str|Datetime|Date, str, bool, str, int, str, bool) -> List[Dict]|pd.DataFrame
    """
    查询历史行情
    """
    symbol = param_convert_iter_to_str(symbol)
    start_time = param_convert_date_with_time(start_time)
    end_time = param_convert_date_with_time(end_time)
    adjust_end_time = param_convert_datetime(adjust_end_time)
    fields = param_convert_iter_to_str(fields)

    frequency = frequency.strip()

    if frequency == DATA_TYPE_TICK:
        req = GetHistoryTicksReq(
            symbols=symbol,
            start_time=start_time,
            end_time=end_time,
            fields=fields,
            skip_suspended=skip_suspended,
            fill_missing=fill_missing,
            adjust=adjust,
            adjust_end_time=adjust_end_time,
        )
        status, result = py_gmi_history_ticks_pb(req.SerializeToString())
        check_gm_status(status)

        datas = []
        status = gmpytool.to_ticks(result, len(result), fields, datas)
        return datas if not df else pd.DataFrame(datas)
    else:
        req = GetHistoryBarsReq(
            symbols=symbol,
            frequency=frequency,
            start_time=start_time,
            end_time=end_time,
            fields=fields,
            skip_suspended=skip_suspended,
            fill_missing=fill_missing,
            adjust=adjust,
            adjust_end_time=adjust_end_time,
        )
        status, result = py_gmi_history_bars_pb(req.SerializeToString())
        check_gm_status(status)

        datas = []
        status = gmpytool.to_bars(result, len(result), fields, datas)
        return datas if not df else pd.DataFrame(datas)


def history_n(symbol, frequency, count, end_time=None, fields=None,
              skip_suspended=True, fill_missing=None, adjust=None,
              adjust_end_time='', df=False):
    # type: (str, str, int, str|Datetime|Date, str|List, bool, str, int, str|Datetime|Date, bool) -> List[Dict]|pd.DataFrame
    """
    查询历史行情
    """
    symbol = symbol.strip()
    if "," in symbol:
        raise GmError(1027, "指定代码个数不正确, 只能指定一个代码", "history_n")
    end_time = param_convert_date_with_time(end_time)
    adjust_end_time = param_convert_date_with_time(adjust_end_time)
    fields = param_convert_iter_to_str(fields)

    frequency = frequency.strip()

    if frequency == DATA_TYPE_TICK:
        req = GetHistoryTicksNReq(
            symbol=symbol,
            count=count,
            end_time=end_time,
            fields=fields,
            skip_suspended=skip_suspended,
            fill_missing=fill_missing,
            adjust=adjust,
            adjust_end_time=adjust_end_time,
        )
        status, result = py_gmi_history_ticks_n_pb(req.SerializeToString())
        check_gm_status(status)

        datas = []
        status = gmpytool.to_ticks(result, len(result), fields, datas)
        return datas if not df else pd.DataFrame(datas)
    else:
        req = GetHistoryBarsNReq(
            symbol=symbol,
            frequency=frequency,
            count=count,
            end_time=end_time,
            fields=fields,
            skip_suspended=skip_suspended,
            fill_missing=fill_missing,
            adjust=adjust,
            adjust_end_time=adjust_end_time,
        )
        status, result = py_gmi_history_bars_n_pb(req.SerializeToString())
        check_gm_status(status)

        datas = []
        status = gmpytool.to_bars(result, len(result), fields, datas)
        return datas if not df else pd.DataFrame(datas)


def get_history_ticks_l2(symbols, start_time, end_time, fields=None,
                         skip_suspended=True, fill_missing=None,
                         adjust=ADJUST_NONE, adjust_end_time='', df=False):
    gmsdklogger.warning("请使用 get_history_l2ticks 查询数据")
    return get_history_l2ticks(symbols, start_time, end_time, fields,
                               skip_suspended, fill_missing,
                               adjust, adjust_end_time, df)


def get_history_l2ticks(symbols, start_time, end_time, fields=None,
                        skip_suspended=True, fill_missing=None,
                        adjust=ADJUST_NONE, adjust_end_time='', df=False):
    req = GetHistoryL2TicksReq(symbols=symbols, start_time=start_time, end_time=end_time, fields=fields,
                               skip_suspended=skip_suspended, fill_missing=fill_missing, adjust=adjust,
                               adjust_end_time=adjust_end_time)

    req = req.SerializeToString()
    status, result = py_gmi_history_ticks_l2(req)
    check_gm_status(status)

    res = Ticks()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(tick) for tick in res.data]
    return datas if not df else pd.DataFrame(datas)


def get_history_bars_l2(symbols, frequency, start_time, end_time, fields=None,
                        skip_suspended=True, fill_missing=None,
                        adjust=ADJUST_NONE, adjust_end_time='', df=False):
    gmsdklogger.warning("请使用 get_history_l2bars 查询数据")
    return get_history_l2bars(symbols, frequency, start_time, end_time, fields,
                              skip_suspended, fill_missing,
                              adjust, adjust_end_time, df)


def get_history_l2bars(symbols, frequency, start_time, end_time, fields=None,
                       skip_suspended=True, fill_missing=None,
                       adjust=ADJUST_NONE, adjust_end_time='', df=False):
    req = GetHistoryL2BarsReq(symbols=symbols, frequency=frequency, start_time=start_time, end_time=end_time,
                              fields=fields,
                              skip_suspended=skip_suspended, fill_missing=fill_missing, adjust=adjust,
                              adjust_end_time=adjust_end_time)

    req = req.SerializeToString()
    status, result = py_gmi_history_bars_l2(req)
    check_gm_status(status)

    res = Bars()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(bar) for bar in res.data]
    return datas if not df else pd.DataFrame(datas)


def get_history_transaction_l2(symbols, start_time, end_time, fields=None, df=False):
    gmsdklogger.warning("请使用 get_history_l2transactions 查询数据")
    return get_history_l2transactions(symbols, start_time, end_time, fields, df)


def get_history_l2transactions(symbols, start_time, end_time, fields=None, df=False):
    req = GetHistoryL2TransactionsReq(
        symbols=symbols, start_time=start_time, end_time=end_time, fields=fields)
    req = req.SerializeToString()
    status, result = py_gmi_history_transaction_l2(req)
    check_gm_status(status)

    res = L2Transactions()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(trans) for trans in res.data]
    return datas if not df else pd.DataFrame(datas)


def get_history_l2orders(symbols, start_time, end_time, fields=None, df=False):
    req = GetHistoryL2OrdersReq(
        symbols=symbols, start_time=start_time, end_time=end_time, fields=fields)
    req = req.SerializeToString()
    status, result = py_gmi_history_order_l2(req)
    check_gm_status(status)

    res = L2Orders()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(item) for item in res.data]
    return datas if not df else pd.DataFrame(datas)


def get_history_l2orders_queue(symbols, start_time, end_time, fields=None, df=False):
    req = GetHistoryL2OrderQueuesReq(
        symbols=symbols,
        start_time=start_time,
        end_time=end_time,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_history_order_queue_l2(req)
    check_gm_status(status)

    res = L2OrderQueues()
    res.ParseFromString(result)
    datas = [protobuf_to_dict(item) for item in res.data]
    return datas if not df else pd.DataFrame(datas)


def raw_func(account_id, func_id, func_args):
    # type: (Text, Text, Dict) -> Dict
    """
    功能码调用
    :param account_id:  资金账户id
    :param func_id:     功能码id
    :param func_args:   功能码参数
    :return:
    """
    func_args = bytes(json.dumps(func_args), encoding='utf8')

    req = RawFuncReq(
        account_id=account_id,
        func_id=func_id,
        func_args=func_args,
    )
    req = req.SerializeToString()
    status, result = py_gmi_raw_func(req)
    check_gm_status(status)

    res = RawFuncRsp()
    res.ParseFromString(result)
    res = protobuf_to_dict(res)
    data = res.get("data", None)
    if data:
        # 为了减少数据传输, data使用了zlib压缩, 所以这里要用zlib解压一下
        return {'data': json.loads(zlib.decompress(data).decode('utf-8'))}
    return {"error": res.get("error")}


def get_varietyinfos(variety_names="", fields=None, df=False):
    # type: (Text|List, Optional[Text], bool) -> List[Dict[Text, Any]]|pd.DataFrame
    """
    查询品种信息\n
    VarietyInfo:
        variety_name        品种名称\n
        sec_type                   \n
        sec_type_ext        扩展类型\n
        exchange            交易市场代码\n
        quote_unit          报价单位\n
        price_tick          最小变动单位\n
        multiplier          合约乘数\n
        trade_n             交易制度\n
        option_type         行权方式\n
    """
    variety_names = param_convert_iter_to_list(variety_names)
    fields = param_convert_iter_to_list(fields)

    req = GetVarietyInfosReq(
        variety_names=variety_names,
        fields=fields,
    )
    status, result = py_gmi_get_varietyinfos(req.SerializeToString())
    check_gm_status(status)
    rsp = VarietyInfos()
    rsp.ParseFromString(result)

    ret = []
    for item in rsp.data:
        r = protobuf_to_dict(item)
        ret.append(r)
    if df:
        return pd.DataFrame(ret)
    return ret


def _get_times(time_list):
    # type: (List) -> List[Dict[Text, Any]]
    times = []
    for i in range(0, len(time_list), 2):
        times.append(
            {
                "start": time_list[i],
                "end": time_list[i+1],
            }
        )
    return times


def _tte_to_dict(tte):
    # type: (GetTradingTimesExtRsp.TTE) -> Dict
    time_trading = _get_times(tte.sections)
    time_callauction = _get_times(tte.auctions)
    return {
        "variety_name": tte.variety_name,
        "time_trading": time_trading,
        "time_callauction": time_callauction,
    }


def get_trading_times(variety_names=""):
    # type: (Text|List|None) -> List[Dict[Text, Any]]
    """
    查询品种的交易时段 \n
    params: \n
    \t variety_names:           品种名称(全部大写)
    return: \n
    \t variety_name:            品种名称(全部大写)
    \t time_trading:            交易时段, 如[{'start': '09:30','end': '11:30'}, {'start': '13:00', 'end': '15:00'}]
    \t time_callauction:        集合竞价时段, 如[{'start': '09:15', 'end': '09:25'},{'start': '14:57', 'end': '15:00'}]
    """
    variety_names = param_convert_iter_to_list(variety_names)
    req = GetTradingTimesExtReq(
        variety_names=variety_names,
    )
    status, result = py_gmi_get_trading_times_ext(req.SerializeToString())
    check_gm_status(status)
    rsp = GetTradingTimesExtRsp()
    rsp.ParseFromString(result)
    ret = []
    for tte in rsp.data:
        ret.append(_tte_to_dict(tte))
    return ret


def _bin_search(lst, value):
    lo = 0
    hi = len(lst)
    while lo < hi:
        mid = (hi+lo)//2
        if lst[mid] == value:
            return mid
        elif lst[mid] > value:
            hi = mid - 1
        else:
            lo = mid + 1
    if lo < len(lst) and lst[lo] != value:
        return lo - 1
    return lo


def get_expire_rest_days(symbols=None, trade_date=None, trading_days=False, df=False):
    # type: (Text|List|None, Text|Datetime|None, bool, bool) -> List[Dict]|pd.DataFrame
    """查询到期剩余天数"""
    # 规范化输入参数
    date_fmt = "%Y-%m-%d"
    if trade_date is None:
        trade_date = Datetime.now()
    elif isinstance(trade_date, str):
        trade_date = utils.str2datetime(trade_date)
    trade_date = utils.beijing_zero_oclock(trade_date)
    if symbols is None:
        symbols = []
    elif isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(',')]

    result = []
    infos = get_instrumentinfos(
        symbols=symbols,
        sec_types="4,5",    # 限制只能是期货/期权
        fields='symbol,delisted_date,listed_date',
    )
    if len(infos) != len(symbols):
        valid_symbols = {info["symbol"].strip() for info in infos}
        invalid_symbols = [s for s in symbols if s not in valid_symbols]
        msg = "合约{}不存在".format(invalid_symbols)
        raise GmError(1027, msg, "get_expire_rest_days")

    trade_date_str = Datetime.strftime(trade_date, date_fmt)
    if trading_days:

        valid_exchange = {'SHSE', 'SZSE',
                          'CFFEX', 'SHFE', 'DCE', 'CZCE', 'INE'}
        trading_date_range = {}  # key: exchange, value: [start_date, end_date]
        unlisted_symbols = []   # 未上市合约

        for info in infos:
            if info["listed_date"] > trade_date:
                unlisted_symbols.append(info["symbol"])
            exchange = info["symbol"].split(".")[0].strip()
            if exchange not in valid_exchange:
                continue

            delisted_date = info["delisted_date"]
            if exchange not in trading_date_range:
                if trade_date < delisted_date:
                    trading_date_range[exchange] = [trade_date, delisted_date]
                else:
                    trading_date_range[exchange] = [delisted_date, trade_date]
            else:
                trading_date_range[exchange][0] = min(
                    trading_date_range[exchange][0], delisted_date)
                trading_date_range[exchange][1] = max(
                    trading_date_range[exchange][1], delisted_date)

        if unlisted_symbols:
            msg = "合约{}在[{}]未上市".format(unlisted_symbols, trade_date_str)
            raise GmError(1027, msg, "get_expire_rest_days")

        exchange_trading_dates = {}
        for exchange, [start_date, end_date] in trading_date_range.items():
            exchange_trading_dates[exchange] = get_trading_dates(
                exchange, start_date, end_date)

        for info in infos:
            exchange = info["symbol"].split(".")[0].strip()
            delisted_date_str = info["delisted_date"].strftime(date_fmt)
            idx = _bin_search(
                exchange_trading_dates[exchange], delisted_date_str)
            trade_date_idx = _bin_search(
                exchange_trading_dates[exchange], trade_date_str)
            result.append({
                "symbol": info["symbol"],
                "days_to_expire": idx - trade_date_idx,
            })
    else:
        unlisted_symbols = []   # 未上市合约
        for info in infos:
            if info["listed_date"] > trade_date:
                unlisted_symbols.append(info["symbol"])
            result.append({
                "symbol": info["symbol"],
                "days_to_expire": (info["delisted_date"] - trade_date).days,
            })
        if unlisted_symbols:
            msg = "合约{}在[{}]未上市".format(unlisted_symbols, trade_date_str)
            raise GmError(1027, msg, "get_expire_rest_days")
    if df:
        return pd.DataFrame(result)
    return result


def option_get_symbols_by_exchange(exchange=None, trade_date=None, call_or_put="", adjust_flag=""):
    # type: (Text|List|None, Text|Datetime, Text, Text) -> List[Text]
    """
    查询期权合约 \n
    return:
        list[symbol]
    """
    exchange = param_convert_iter_to_str(exchange)
    trade_date = param_convert_datetime(trade_date)

    req = GetOptionSymbolsByExchangeReq(
        exchange=exchange,
        trade_date=trade_date,
        call_or_put=call_or_put,
        adjust_flag=adjust_flag,
    )
    status, result = py_gmi_option_get_symbols_by_exchange(
        req.SerializeToString())
    check_gm_status(status)
    rsp = GetOptionSymbolsByExchangeRsp()
    rsp.ParseFromString(result)
    ret = [symbol for symbol in rsp.symbols]
    return ret


def option_get_symbols_by_in_at_out(underlying_symbol=None,
                                    trade_date=None,
                                    execute_month=None,
                                    call_or_put=None,
                                    in_at_out=None,
                                    s=None,
                                    adjust_flag="",
                                    ):
    # type: (Text|None, Text|Datetime, int|None, Text, int|None, float|Text|None, Text) -> list[Text]
    """
    查询实平虚值某档合约 \n
    return:z
        list[symbol]
    """
    trade_date = param_convert_datetime(trade_date)
    if isinstance(in_at_out, int):
        in_at_out = str(in_at_out)
    if s is None:
        price = 0.0
        price_type = "last"
    elif isinstance(s, float):
        price = s
        price_type = ""
    elif isinstance(s, str):
        price = 0.0
        price_type = s

    req = GetOptionSymbolsByInAtOutReq(
        underlying_symbol=underlying_symbol,
        trade_time=trade_date,
        execute_month=execute_month,
        call_or_put=call_or_put,
        in_at_out=in_at_out,
        price=price,
        price_type=price_type,
        adjust_flag=adjust_flag,
    )
    status, result = py_gmi_option_get_symbols_by_in_at_out(
        req.SerializeToString())
    check_gm_status(status)
    rsp = GetOptionSymbolsByInAtOutRsp()
    rsp.ParseFromString(result)
    ret = [symbol for symbol in rsp.symbols]
    return ret


def option_get_delisted_dates(underlying_symbol="", trade_date=None, execute_month=0):
    # type: (Text, Text|Datetime, int) -> List[Date]
    """
    查询期权到期日列表 \n
    params: \n
    \t underlying_symbol:       标的物symbol, 全部大写, 不指定具体到期月份, 例'DCE.V'
    \t trade_date:              交易时间, 默认当前最新时间
    \t execute_month:           合约月份, 1-当月, 2-下月, 3-下季, 4-隔季,
                                默认0, 返回所有合约月份的到期日列表
    return:
    \t 包含指定标的物的到期日列表 list
    """
    trade_date = param_convert_datetime(trade_date)
    req = GetOptionDelistedDatesReq(
        underlying_symbol=underlying_symbol,
        trade_date=trade_date,
        execute_month=execute_month,
    )
    status, result = py_gmi_option_get_delisted_dates(req.SerializeToString())
    check_gm_status(status)
    rsp = GetOptionDelistedDatesRsp()
    rsp.ParseFromString(result)
    return [utc_datetime2beijing_datetime(t.ToDatetime()).date() for t in rsp.delisted_date]


def option_get_exercise_prices(underlying_symbol="",
                               trade_date=None,
                               execute_month=0,
                               adjust_flag=""
                               ):
    # type: (Text, Text|Datetime, int, Text) -> List[float]
    """
    查询期权行权价列表 \n
    params: \n
    \t underlying_symbol:       标的物symbol, 全部大写, 不指定具体到期月份, 例'DCE.V'
    \t trade_date:              交易时间, 默认当前最新时间
    \t execute_month:           合约月份, 1-当月, 2-下月, 3-下季, 4-隔季,
                                默认0, 返回所有合约月份的到期日列表
    \t adjust_flag:             表示是否过滤除权后合约(带A合约), 不填默认为''（空字符串)\n
                                'M'表示不返回带A合约\n
                                'A'表示只返回带A合约\n
                                '' 表示不做过滤都返回\n
    return:
    \t 包含指定标的物、到期日的行权价列表 list
    """
    trade_date = param_convert_datetime(trade_date)
    req = GetOptionExercisePricesReq(
        underlying_symbol=underlying_symbol,
        trade_date=trade_date,
        execute_month=execute_month,
        adjust_flag=adjust_flag,
    )
    status, result = py_gmi_option_get_exercise_prices(req.SerializeToString())
    check_gm_status(status)
    rsp = GetOptionExercisePricesRsp()
    rsp.ParseFromString(result)
    ret = [exercise_price for exercise_price in rsp.exercise_prices]
    return ret


def bond_convertible_get_call_info(symbols=None, start_date=None, end_date=None):
    # type: (str|List, str|Datetime|None, str|Datetime|None) -> pd.DataFrame
    """
    查询可转债赎回信息
    """
    symbols = param_convert_iter_to_list(symbols)

    start_date = param_convert_datetime(start_date)
    end_date = param_convert_datetime(end_date)

    req = GetConvertibleBondCallInfoReq(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
    )
    status, result = py_gmi_get_convertible_bond_call_info(
        req.SerializeToString())
    check_gm_status(status)
    rsp = GetConvertibleBondCallInfoRsp()
    rsp.ParseFromString(result)
    data = protobuf_to_dict(rsp)
    infos = data.get("infos", [])
    return pd.DataFrame(infos)


def get_cash(account_id=None):
    """查询指定账户资金"""
    req = GetCashReq(
        account_id=account_id,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_cash_pb_v2(req)
    check_gm_status(status)
    if result:
        cashes = Cashes()
        cashes.ParseFromString(result)
        cashes = [protobuf_to_dict(cash) for cash in cashes.data]
        cash = cashes[0]
        return cash
    return {}


def get_position(account_id=None):
    """查询指定账户所有持仓"""
    req = GetPositionsReq(
        account_id=account_id,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_positions_pb_v2(req)
    check_gm_status(status)
    if result:
        positions = Positions()
        positions.ParseFromString(result)
        tmp_positions = []
        for position in positions.data:
            position = protobuf_to_dict(
                position, including_default_value_fields=True
            )
            position["credit_position_sellable_volume"] = 0  # 默认为0
            properties = position.get("properties", None)
            if properties is not None:
                position["credit_position_sellable_volume"] = properties.get(
                    "credit_position_sellable_volume", 0
                )
            tmp_positions.append(position)
        positions = tmp_positions
    else:
        positions = []
    return positions

def universe_delete(universe_name):
    # type: (str) -> None
    """
    删除标的池
    """
    req = DelInstrumentPoolReq(
        pool_ids=[universe_name]
    )
    status = py_gmi_del_instrument_pool_by_name_pb(req.SerializeToString())
    check_gm_status(status)

def universe_set(universe_name, universe_symbols=None):
    # type: (str, List[str]|None) -> None
    """
    设置标的池
    """
    req = SetInstrumentPoolSymbolsReq(
        pool_id=universe_name,
        symbols=universe_symbols,
    )
    status = py_gmi_set_instrument_pool_symbols_pb(req.SerializePartialToString())
    check_gm_status(status)

def universe_get_symbols(universe_name):
    # type: (str) -> List[str]
    """
    获取标的池成分
    """
    req = GetInstrumentPoolByIdReq(
        pool_id=universe_name,
    )
    status, result = py_gmi_get_instrument_pool_by_name_pb(req.SerializePartialToString())
    check_gm_status(status)
    if result:
        instrumentPool = InstrumentPool()
        instrumentPool.ParseFromString(result)
        return instrumentPool.symbols


def universe_get_names():
    # type: () -> List[str]
    """
    获取全部标的池名称
    """
    req = GetInstrumentPoolsReq(

    )
    status, result = py_gmi_get_instrument_pools_pb(req.SerializePartialToString())
    check_gm_status(status)
    if result:
        getInstrumentPoolsRsp = GetInstrumentPoolsRsp()
        getInstrumentPoolsRsp.ParseFromString(result)
        return [ipool.pool_name for ipool in getInstrumentPoolsRsp.pools]

    return []
