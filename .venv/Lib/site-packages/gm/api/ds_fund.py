from typing import List, Dict, Any
from datetime import date as Date

import numpy as np
import pandas as pd
from cachetools import cached, TTLCache
from cachetools.keys import hashkey

from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime, timedelta
from gm.utils import utc_datetime2beijing_datetime, round_float

from gm.api._errors import check_gm_status
from gm.pb_to_dict import protobuf_to_dict
from gm.csdk.c_sdk import (
    py_gmi_stk_get_industry_category,
    py_gmi_stk_get_industry_constituents,
    py_gmi_stk_get_symbol_industry,
    py_gmi_stk_get_index_constituents,
    py_gmi_stk_get_index_history_constituents,
    py_gmi_stk_get_dividend,
    py_gmi_stk_get_adj_factor,
    py_gmi_fut_get_continuous_contracts,
    py_gmi_fut_get_contract_info,
    py_gmi_fnd_get_adj_factor,
    py_gmi_fnd_get_dividend,
    py_gmi_fnd_get_split,
    py_gmi_stk_get_sector_category,
    py_gmi_stk_get_sector_constituents,
    py_gmi_stk_get_symbol_sector,
    py_stk_get_ration,
    py_gmi_stk_get_shareholder_num,
    py_gmi_stk_get_top_shareholder,
    py_gmi_stk_get_share_change,
    py_gmi_stk_get_fundamentals_balance,
    py_gmi_stk_get_fundamentals_cashflow,
    py_gmi_stk_get_fundamentals_income,
    py_gmi_stk_get_fundamentals_balance_pt,
    py_gmi_stk_get_fundamentals_cashflow_pt,
    py_gmi_stk_get_fundamentals_income_pt,
    py_gmi_fut_get_transaction_ranking,
    py_gmi_fut_get_transaction_rankings,
    py_gmi_fut_get_warehouse_receipt,
    py_gmi_fnd_get_etf_constituents,
    py_gmi_fnd_get_portfolio,
    py_gmi_fnd_get_net_value,
    py_gmi_bnd_get_conversion_price,
    py_gmi_bnd_get_call_info,
    py_gmi_bnd_get_put_info,
    py_gmi_bnd_get_amount_change,
    py_gmi_stk_get_finance_prime,
    py_gmi_stk_get_finance_prime_pt,
    py_gmi_stk_get_finance_deriv,
    py_gmi_stk_get_finance_deriv_pt,
    py_gmi_stk_get_daily_valuation,
    py_gmi_stk_get_daily_valuation_pt,
    py_gmi_stk_get_daily_mktvalue,
    py_gmi_stk_get_daily_mktvalue_pt,
    py_gmi_stk_get_daily_basic,
    py_gmi_stk_get_daily_basic_pt,

    py_gmi_stk_abnor_change_stocks,
    py_gmi_stk_abnor_change_detail,
    py_gmi_stk_quota_shszhk_infos,
    py_gmi_stk_hk_inst_holding_detail_info,
    py_gmi_stk_hk_inst_holding_info,
    py_gmi_stk_active_stock_top10_shszhk_info,

    py_gmi_stk_get_money_flow,
    py_gmi_stk_get_finance_audit,
    py_gmi_stk_get_finance_forecast,
    py_gmi_fnd_get_share,
    py_gmi_bnd_get_analysis,

    py_gmi_get_open_call_auction,
)
from gm.pb.fund_stk_service_pb2 import (
    GetFinancePrimeReq,
    GetFinancePrimeRsp,
    GetFinancePrimePtReq,
    GetFinancePrimePtRsp,
    GetFinanceDerivReq,
    GetFinanceDerivRsp,
    GetFinanceDerivPtReq,
    GetFinanceDerivPtRsp,
    GetDailyValuationReq,
    GetDailyValuationRsp,
    GetDailyValuationPtReq,
    GetDailyValuationPtRsp,
    GetDailyMktvalueReq,
    GetDailyMktvalueRsp,
    GetDailyMktvaluePtReq,
    GetDailyMktvaluePtRsp,
    GetDailyBasicPtReq,
    GetDailyBasicPtRsp,
    GetDailyBasicReq,
    GetDailyBasicRsp,
    GetIndustryCategoryReq,
    GetIndustryCategoryRsp,
    GetIndustryConstituentsReq,
    GetIndustryConstituentsRsp,
    GetSymbolIndustryReq,
    GetSymbolIndustryRsp,
    GetIndexConstituentsReq,
    GetIndexConstituentsRsp,
    GetIndexHistoryConstituentsReq,
    GetIndexHistoryConstituentsRsp,
    GetDividendReq,
    GetDividendRsp,
    GetAdjFactorReq,
    GetAdjFactorRsp,
    GetSectorCategoryReq,
    GetSectorCategoryRsp,
    GetSectorConstituentsReq,
    GetSectorConstituentsRsp,
    GetSymbolSectorReq,
    GetSymbolSectorRsp,
    GetRationReq,
    GetRationRsp,
    GetShareholderNumReq,
    GetShareholderNumRsp,
    GetTopShareholderReq,
    GetTopShareholderRsp,
    GetShareChangeReq,
    GetShareChangeRsp,
    GetFundamentalsBalanceReq,
    GetFundamentalsBalanceRsp,
    GetFundamentalsCashflowReq,
    GetFundamentalsCashflowRsp,
    GetFundamentalsIncomeReq,
    GetFundamentalsIncomeRsp,
    GetFundamentalsBalancePtReq,
    GetFundamentalsBalancePtRsp,
    GetFundamentalsCashflowPtReq,
    GetFundamentalsCashflowPtRsp,
    GetFundamentalsIncomePtReq,
    GetFundamentalsIncomePtRsp,

    GetAbnorChangeStocksReq,
    GetAbnorChangeStocksRsp,
    GetAbnorChangeDetailReq,
    GetAbnorChangeDetailRsp,
    GetQuotaShszhkInfosReq,
    GetQuotaShszhkInfosRsp,
    GetHkInstHoldingDetailInfoReq,
    GetHkInstHoldingDetailInfoRsp,
    GetHkInstHoldingInfoReq,
    GetHkInstHoldingInfoRsp,
    GetActiveStockTop10ShszhkInfoReq,
    GetActiveStockTop10ShszhkInfoRsp,
    GetMoneyFlowReq,
    GetMoneyFlowRsp,
    GetFinanceAuditReq,
    GetFinanceAuditRsp,
    GetFinanceForecastReq,
    GetFinanceForecastRsp,
)
from gm.pb.fund_fut_service_pb2 import (
    GetContinuousContractsReq,
    GetContinuousContractsRsp,
    FutGetContractInfoReq,
    FutGetContractInfoRsp,
    FutGetTransactionRankingReq,
    FutGetTransactionRankingRsp,
    FutGetTransactionRankingsReq,
    FutGetTransactionRankingsRsp,
    GetWarehouseReceiptReq,
    GetWarehouseReceiptRsp,
)
from gm.pb.fund_fnd_service_pb2 import (
    FndGetAdjFactorReq,
    FndGetAdjFactorRsp,
    FndGetDividendReq,
    FndGetDividendRsp,
    GetSplitReq,
    GetSplitRsp,
    GetEtfConstituentsReq,
    GetEtfConstituentsRsp,
    GetPortfolioReq,
    GetPortfolioRsp,
    GetNetValueReq,
    GetNetValueRsp,
    GetShareReq,
    GetShareRsp,
)
from gm.pb.fund_bnd_service_pb2 import (
    GetConversionPriceReq,
    GetConversionPriceRsp,
    GetCallInfoReq,
    GetCallInfoRsp,
    GetPutInfoReq,
    GetPutInfoRsp,
    GetAmountChangeReq,
    GetAmountChangeRsp,
    GetAnalysisReq,
    GetAnalysisRsp,
)

from gm.pb.fund_general_service_pb2 import (
    GetOpenCallAuctionReq,
    GetOpenCallAuctionRsp
)

_int_fields = ["data_type", "rpt_type"]
_str_fields = ["begin_dt", "curr"]


def _extract_data(result):
    data = []
    for item in result.get("data", []):
        for k, v in item["data"].items():
            if k in _int_fields:
                item[k] = int(v)
            elif k in _str_fields:
                item[k] = v
            # dicimal 类型
            elif v == "":
                if np.__version__.startswith('1'):
                    item[k] = np.NAN
                else:
                    item[k] = np.nan
            else:
                item[k] = float(v)
        del item["data"]
        data.append(item)
    return data


def _extract_decimal_data(result):
    data = []
    for item in result.get("data", []):
        for k, v in item["data"].items():
            # dicimal 类型
            if v == "":
                if np.__version__.startswith('1'):
                    item[k] = np.NAN
                else:
                    item[k] = np.nan
            else:
                item[k] = float(v)
        del item["data"]
        data.append(item)
    return data

def _make_hash_key(*args, **kwargs):
    args = tuple(tuple(arg) if isinstance(arg, list) else arg for arg in args)
    kwargs = {k: tuple(v) if isinstance(v, list) else v for k, v in kwargs.items()}
    return hashkey(*args, **kwargs)

def stk_get_industry_category(source="zjh2012", level=1):
    # type: (str, int) -> pd.DataFrame
    """
    查询行业分类

    * source: 行业来源, 默认值 'zjh2012'
    * level: 行业分级, 默认值 1, (1:一级行业, 2:二级行业, 3:三级行业)
    """
    req = GetIndustryCategoryReq(
        source=source,
        level=level,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_industry_category(req)
    check_gm_status(status)
    res = GetIndustryCategoryRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str]]
    return pd.DataFrame(data)


def stk_get_industry_constituents(industry_code, date=""):
    # type: (str, str) -> pd.DataFrame
    """
    查询行业成分股
    """
    req = GetIndustryConstituentsReq(
        industry_code=industry_code,
        date=date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_industry_constituents(req)
    check_gm_status(status)
    res = GetIndustryConstituentsRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict]
    return pd.DataFrame(data)


def stk_get_symbol_industry(symbols, source="zjh2012", level=1, date=""):
    # type: (str|List[str], str, int, str) -> pd.DataFrame
    """
    查询股票的所属行业

    证监会行业分类2012没有三级行业, 若输入source='zjh2012', level=3则参数无效, 返回空
    """
    if isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]
    req = GetSymbolIndustryReq(
        symbols=symbols,
        source=source,
        level=level,
        date=date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_symbol_industry(req)
    check_gm_status(status)
    res = GetSymbolIndustryRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str]]
    return pd.DataFrame(data)


def stk_get_sector_category(sector_type):
    # type: (str) -> pd.DataFrame
    """
    查询板块分类
    """
    req = GetSectorCategoryReq(
        sector_type=sector_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_sector_category(req)
    check_gm_status(status)
    rsp = GetSectorCategoryRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str]]
    return pd.DataFrame(data)


def stk_get_sector_constituents(sector_code):
    # type: (str) -> pd.DataFrame
    """
    查询板块成分股
    """
    req = GetSectorConstituentsReq(
        sector_code=sector_code,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_sector_constituents(req)
    check_gm_status(status)
    rsp = GetSectorConstituentsRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str]]
    return pd.DataFrame(data)


def stk_get_symbol_sector(symbols, sector_type):
    # type: (str|List[str], str) -> pd.DataFrame
    """
    查询股票的所属板块
    """
    if isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]
    req = GetSymbolSectorReq(
        symbols=symbols,
        sector_type=sector_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_symbol_sector(req)
    check_gm_status(status)
    rsp = GetSymbolSectorRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str]]
    return pd.DataFrame(data)


def stk_get_index_constituents(index, trade_date=None):
    # type: (str, str) -> pd.DataFrame
    """
    查询指数最新成分股
    """
    req = GetIndexConstituentsReq(
        index=index,
        trade_date=trade_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_index_constituents(req)
    check_gm_status(status)
    res = GetIndexConstituentsRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_index_history_constituents(index, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询指数历史成分股
    """
    req = GetIndexHistoryConstituentsReq(
        index=index,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_index_history_constituents(req)
    check_gm_status(status)
    res = GetIndexHistoryConstituentsRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_dividend(symbol, start_date, end_date):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询股票分红送股信息
    """
    req = GetDividendReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_dividend(req)
    check_gm_status(status)
    res = GetDividendRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_ration(symbol, start_date, end_date):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询股票配股信息
    """
    req = GetRationReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_stk_get_ration(req)
    check_gm_status(status)
    res = GetRationRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_adj_factor(symbol, start_date="", end_date="", base_date=""):
    # type: (str, str, str, str) -> pd.DataFrame
    """
    查询股票的复权因子
    """
    req = GetAdjFactorReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        base_date=base_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_adj_factor(req)
    check_gm_status(status)
    res = GetAdjFactorRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str|float]]
    return pd.DataFrame(data)


def stk_get_shareholder_num(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询股东户数
    """
    req = GetShareholderNumReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_shareholder_num(req)
    check_gm_status(status)
    res = GetShareholderNumRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_top_shareholder(symbol, start_date="", end_date="", tradable_holder=False):
    # type: (str, str, str, bool) -> pd.DataFrame
    """
    查询十大股东
    """
    req = GetTopShareholderReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        tradable_holder=tradable_holder,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_top_shareholder(req)
    check_gm_status(status)
    res = GetTopShareholderRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_share_change(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询股本变动
    """
    req = GetShareChangeReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_share_change(req)
    check_gm_status(status)
    res = GetShareChangeRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_get_fundamentals_balance(
    symbol,
    fields,
    rpt_type=None,
    data_type=None,
    start_date=None,
    end_date=None,
    df=False,
):
    # type: (str, str, int, int, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询资产负债表数据"""
    if rpt_type is None:
        rpt_type = 0
    if data_type is None:
        data_type = 0
    if start_date is None:
        start_date = ""
    if end_date is None:
        end_date = ""
    if fields is None:
        fields = ""
    else:
        fields = [field.strip() for field in fields.split(",")]

    req = GetFundamentalsBalanceReq(
        symbol=symbol,
        rpt_type=rpt_type,
        data_type=data_type,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_fundamentals_balance(req)
    check_gm_status(status)

    data = []
    rsp = GetFundamentalsBalanceRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_data(result)
    if df:
        return pd.DataFrame(data)
    return data


def stk_get_fundamentals_balance_pt(
    symbols, fields, rpt_type=None, data_type=None, date=None, df=False
):
    # type: (str|List[str], str, int, int, str, bool) -> pd.DataFrame | List[Dict]
    """查询资产负债表截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    if rpt_type is None:
        rpt_type = 0
    if data_type is None:
        data_type = 0
    if date is None:
        date = ""

    req = GetFundamentalsBalancePtReq(
        symbols=symbols,
        rpt_type=rpt_type,
        data_type=data_type,
        date=date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_fundamentals_balance_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetFundamentalsBalancePtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_data(result)
    if df:
        return pd.DataFrame(data)
    return data


def stk_get_fundamentals_cashflow(
    symbol,
    fields,
    rpt_type=None,
    data_type=None,
    start_date=None,
    end_date=None,
    df=False,
):
    # type: (str, str, int, int, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询现金流量表数据"""
    if rpt_type is None:
        rpt_type = 0
    if data_type is None:
        data_type = 0
    if start_date is None:
        start_date = ""
    if end_date is None:
        end_date = ""
    if fields is None:
        fields = ""
    else:
        fields = [field.strip() for field in fields.split(",")]

    req = GetFundamentalsCashflowReq(
        symbol=symbol,
        rpt_type=rpt_type,
        data_type=data_type,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_fundamentals_cashflow(req)
    check_gm_status(status)
    data = []
    rsp = GetFundamentalsCashflowRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_data(result)
    if df:
        return pd.DataFrame(data)
    return data


def stk_get_fundamentals_cashflow_pt(
    symbols, fields, rpt_type=None, data_type=None, date=None, df=False
):
    # type: (str|List[str], str, int, int, str, bool) -> pd.DataFrame | List[Dict]
    """查询现金流量表截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    if rpt_type is None:
        rpt_type = 0
    if data_type is None:
        data_type = 0
    if date is None:
        date = ""

    req = GetFundamentalsCashflowPtReq(
        symbols=symbols,
        rpt_type=rpt_type,
        data_type=data_type,
        date=date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_fundamentals_cashflow_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetFundamentalsCashflowPtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_data(result)
    if df:
        return pd.DataFrame(data)
    return data


def stk_get_fundamentals_income(
    symbol,
    fields,
    rpt_type=None,
    data_type=None,
    start_date=None,
    end_date=None,
    df=False,
):
    # type: (str, str, int, int, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询利润表数据"""
    if rpt_type is None:
        rpt_type = 0
    if data_type is None:
        data_type = 0
    if start_date is None:
        start_date = ""
    if end_date is None:
        end_date = ""
    if fields is None:
        fields = []
    else:
        fields = [field.strip() for field in fields.split(",")]

    req = GetFundamentalsIncomeReq(
        symbol=symbol,
        rpt_type=rpt_type,
        data_type=data_type,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_fundamentals_income(req)
    check_gm_status(status)
    data = []
    rsp = GetFundamentalsIncomeRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_fundamentals_income_pt(
    symbols, fields, rpt_type=None, data_type=None, date=None, df=False
):
    # type: (str|List[str], str, int, int, str, bool) -> pd.DataFrame | List[Dict]
    """查询利润表截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    if rpt_type is None:
        rpt_type = 0
    if data_type is None:
        data_type = 0
    if date is None:
        date = ""

    req = GetFundamentalsIncomePtReq(
        symbols=symbols,
        rpt_type=rpt_type,
        data_type=data_type,
        date=date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_fundamentals_income_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetFundamentalsIncomePtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_finance_prime(symbol, fields, rpt_type=None, data_type=None, start_date=None, end_date=None, df=False):
    # type: (str, str, int, int, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询财务主要指标数据"""
    if fields:
        fields = [field.strip() for field in fields.split(",")]
    else:
        fields = None

    req = GetFinancePrimeReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        rpt_type=rpt_type,
        data_type=data_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_finance_prime(req)
    check_gm_status(status)
    data = []
    rsp = GetFinancePrimeRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_finance_prime_pt(symbols, fields, rpt_type=None, data_type=None, date=None, df=False):
    # type: (str|List[str], str, int, int, str, bool) -> pd.DataFrame | List[Dict]
    """查询财务主要指标截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    req = GetFinancePrimePtReq(
        symbols=symbols,
        date=date,
        fields=fields,
        rpt_type=rpt_type,
        data_type=data_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_finance_prime_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetFinancePrimePtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_finance_deriv(symbol, fields, rpt_type=None, data_type=None, start_date=None, end_date=None, df=False):
    # type: (str, str, int, int, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询财务衍生指标数据"""
    if fields:
        fields = [field.strip() for field in fields.split(",")]
    else:
        fields = None

    req = GetFinanceDerivReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        rpt_type=rpt_type,
        data_type=data_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_finance_deriv(req)
    check_gm_status(status)
    data = []
    rsp = GetFinanceDerivRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_finance_deriv_pt(symbols, fields, rpt_type=None, data_type=None, date=None, df=False):
    # type: (str|List[str], str, int, int, str, bool) -> pd.DataFrame | List[Dict]
    """查询财务衍生指标截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    req = GetFinanceDerivPtReq(
        symbols=symbols,
        date=date,
        fields=fields,
        rpt_type=rpt_type,
        data_type=data_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_finance_deriv_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetFinanceDerivPtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_daily_valuation(symbol, fields, start_date=None, end_date=None, df=False):
    # type: (str, str, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询估值指标每日数据"""
    if fields:
        fields = [field.strip() for field in fields.split(",")]
    else:
        fields = None

    req = GetDailyValuationReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_daily_valuation(req)
    check_gm_status(status)
    data = []
    rsp = GetDailyValuationRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_daily_valuation_pt(symbols, fields, trade_date=None, df=False):
    # type: (str|List[str], str, str, bool) -> pd.DataFrame | List[Dict]
    """查询估值指标单日截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    req = GetDailyValuationPtReq(
        symbols=symbols,
        trade_date=trade_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_daily_valuation_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetDailyValuationPtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_daily_mktvalue(symbol, fields, start_date=None, end_date=None, df=False):
    # type: (str, str, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询市值指标每日数据"""
    if fields:
        fields = [field.strip() for field in fields.split(",")]
    else:
        fields = None

    req = GetDailyMktvalueReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_daily_mktvalue(req)
    check_gm_status(status)
    data = []
    rsp = GetDailyMktvalueRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_daily_mktvalue_pt(symbols, fields, trade_date=None, df=False):
    # type: (str|List[str], str, str, bool) -> pd.DataFrame | List[Dict]
    """查询基础指标单日截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    req = GetDailyMktvaluePtReq(
        symbols=symbols,
        trade_date=trade_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_daily_mktvalue_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetDailyMktvaluePtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_daily_basic(symbol, fields, start_date=None, end_date=None, df=False):
    # type: (str, str, str, str, bool) -> pd.DataFrame | List[Dict]
    """查询基础指标每日数据"""
    if fields:
        fields = [field.strip() for field in fields.split(",")]
    else:
        fields = None

    req = GetDailyBasicReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_daily_basic(req)
    check_gm_status(status)
    data = []
    rsp = GetDailyBasicRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def stk_get_daily_basic_pt(symbols, fields, trade_date=None, df=False):
    # type: (str|List[str], str, str, bool) -> pd.DataFrame | List[Dict]
    """查询基础指标单日截面数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [field.strip() for field in fields.split(",")]

    req = GetDailyBasicPtReq(
        symbols=symbols,
        trade_date=trade_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_get_daily_basic_pt(req)
    check_gm_status(status)
    data = []
    rsp = GetDailyBasicPtRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = _extract_decimal_data(result)
    if df:
        data = pd.DataFrame(data)
    return data


def fut_get_continuous_contracts(csymbol, start_date="", end_date=""):
    # type: (str, str, str) -> List[Dict[str, Any]]
    """
    查询连续合约对应的真实合约
    """
    req = GetContinuousContractsReq(
        csymbol=csymbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fut_get_continuous_contracts(req)
    check_gm_status(status)
    res = GetContinuousContractsRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str]]
    return data


def fut_get_contract_info(product_codes, df=False):
    # type: (str|List[str], bool) -> List[Dict[str, str|int]] | pd.DataFrame
    """
    查询期货标准品种信息
    """
    if isinstance(product_codes, str):
        product_codes = [code.strip() for code in product_codes.split(",")]
    req = FutGetContractInfoReq(
        product_codes=product_codes,
    )

    req = req.SerializeToString()
    status, result = py_gmi_fut_get_contract_info(req)
    check_gm_status(status)
    res = FutGetContractInfoRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str|int]]
    if df:
        return pd.DataFrame(data)
    return data


def fut_get_transaction_ranking(symbol, trade_date="", indicator="volume"):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询期货每日成交持仓排名
    """
    req = FutGetTransactionRankingReq(
        symbol=symbol,
        trade_date=trade_date,
        indicator=indicator,
    )

    req = req.SerializeToString()
    status, result = py_gmi_fut_get_transaction_ranking(req)
    check_gm_status(status)
    rsp = FutGetTransactionRankingRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    data = pd.DataFrame(data)  # type: pd.DataFrame
    if data.empty:
        return data
    # ranking_change_is_null 字段用于判断 ranking_change 是否为空, 最终输出需要删除这个字段
    data.loc[data["ranking_change_is_null"] == True, "ranking_change"] = None
    return data.drop(axis=1, columns="ranking_change_is_null")

def fut_get_transaction_rankings(symbols, trade_date="", indicators="volume"):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询期货每日成交持仓排名
    """
    if isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    if isinstance(indicators, str):
        indicators = [indicator.strip() for indicator in indicators.split(",")]

    req = FutGetTransactionRankingsReq(
        symbols=symbols,
        trade_date=trade_date,
        indicators=indicators,
    )

    req = req.SerializeToString()
    status, result = py_gmi_fut_get_transaction_rankings(req)
    check_gm_status(status)
    rsp = FutGetTransactionRankingsRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    data = pd.DataFrame(data)  # type: pd.DataFrame
    if data.empty:
        return data
    # ranking_change_is_null 字段用于判断 ranking_change 是否为空, 最终输出需要删除这个字段
    data.loc[data["ranking_change_is_null"] == True, "ranking_change"] = None
    return data.drop(axis=1, columns="ranking_change_is_null")

def fut_get_warehouse_receipt(product_code, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询期货仓单数据
    """
    req = GetWarehouseReceiptReq(
        product_code=product_code,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_fut_get_warehouse_receipt(req)
    check_gm_status(status)
    rsp = GetWarehouseReceiptRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def fnd_get_etf_constituents(etf):
    # type: (str) -> pd.DataFrame
    """
    查询ETF最新成分股
    """
    req = GetEtfConstituentsReq(
        etf=etf,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_etf_constituents(req)
    check_gm_status(status)
    rsp = GetEtfConstituentsRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def fnd_get_portfolio(fund, report_type, portfolio_type, start_date="", end_date=""):
    # type: (str, int, str, str, str) -> pd.DataFrame
    """
    查询基金的资产组合
    """
    req = GetPortfolioReq(
        fund=fund,
        start_date=start_date,
        end_date=end_date,
        report_type=report_type,
        portfolio_type=portfolio_type,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_portfolio(req)
    check_gm_status(status)
    rsp = GetPortfolioRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    if portfolio_type == "stk":
        data = result.get("portfolio_stock", [])
    elif portfolio_type == "bnd":
        data = result.get("portfolio_bond", [])
    elif portfolio_type == "fnd":
        data = result.get("portfolio_fund", [])
    else:
        data = []
    return pd.DataFrame(data)


def fnd_get_net_value(fund, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询基金的净值数据
    """
    req = GetNetValueReq(
        fund=fund,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_net_value(req)
    check_gm_status(status)
    rsp = GetNetValueRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def fnd_get_adj_factor(fund, start_date="", end_date="", base_date=""):
    # type: (str, str, str, str) -> pd.DataFrame
    """
    查询基金复权因子
    """
    req = FndGetAdjFactorReq(
        fund=fund,
        start_date=start_date,
        end_date=end_date,
        base_date=base_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_adj_factor(req)
    check_gm_status(status)
    res = FndGetAdjFactorRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, str|float]]
    return pd.DataFrame(data)


def fnd_get_dividend(fund, start_date, end_date):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询基金分红信息
    """
    req = FndGetDividendReq(
        fund=fund,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_dividend(req)
    check_gm_status(status)
    res = FndGetDividendRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def fnd_get_split(fund, start_date, end_date):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询基金分红信息
    """
    req = GetSplitReq(
        fund=fund,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_split(req)
    check_gm_status(status)
    res = GetSplitRsp()
    res.ParseFromString(result)
    result = protobuf_to_dict(res, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def bnd_get_conversion_price(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询可转债转股价变动信息
    """
    req = GetConversionPriceReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_bnd_get_conversion_price(req)
    check_gm_status(status)
    rsp = GetConversionPriceRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def bnd_get_call_info(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询可转债赎回信息
    """
    req = GetCallInfoReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_bnd_get_call_info(req)
    check_gm_status(status)
    rsp = GetCallInfoRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def bnd_get_put_info(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询可转债回售信息
    """
    req = GetPutInfoReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_bnd_get_put_info(req)
    check_gm_status(status)
    rsp = GetPutInfoRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def bnd_get_amount_change(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询可转债剩余规模变动信息
    """
    req = GetAmountChangeReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_bnd_get_amount_change(req)
    check_gm_status(status)
    rsp = GetAmountChangeRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def bnd_get_amount_change(symbol, start_date="", end_date=""):
    # type: (str, str, str) -> pd.DataFrame
    """
    查询可转债剩余规模变动信息
    """
    req = GetAmountChangeReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_bnd_get_amount_change(req)
    check_gm_status(status)
    rsp = GetAmountChangeRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)


def stk_abnor_change_stocks(symbols=None, change_types=None, trade_date=None, fields=None, df=False):
    # type: (str|List[str], str|List[str], str|Date, str, bool) -> List[Dict]|pd.DataFrame
    """查询龙虎榜股票数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [x.strip() for x in symbols.split(",")]
    if not change_types:
        change_types = None
    elif isinstance(change_types, str):
        change_types = [x.strip() for x in change_types.split(",")]
    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [x.strip() for x in fields.split(",")]
    if isinstance(trade_date, Date):
        trade_date = trade_date.strftime("%Y-%m-%d")

    req = GetAbnorChangeStocksReq(
        symbols=symbols,
        change_types=change_types,
        trade_date=trade_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_abnor_change_stocks(req)
    check_gm_status(status)
    rsp = GetAbnorChangeStocksRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, including_default_value_fields=df, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data, columns=fields)
    return data


def stk_abnor_change_detail(symbols=None, change_types=None, trade_date=None, fields=None, df=False):
    # type: (str|List[str], str|List[str], str|Date, str, bool) -> List[Dict]|pd.DataFrame
    """查询龙虎榜营业部数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [x.strip() for x in symbols.split(",")]
    if not change_types:
        change_types = None
    elif isinstance(change_types, str):
        change_types = [x.strip() for x in change_types.split(",")]
    if not fields:
        fields = None
    elif isinstance(fields, str):
        fields = [x.strip() for x in fields.split(",")]
    if isinstance(trade_date, Date):
        trade_date = trade_date.strftime("%Y-%m-%d")

    req = GetAbnorChangeDetailReq(
        symbols=symbols,
        change_types=change_types,
        trade_date=trade_date,
        fields=fields,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_abnor_change_detail(req)
    check_gm_status(status)
    rsp = GetAbnorChangeDetailRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, including_default_value_fields=df, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data, columns=fields)
    return data


def stk_quota_shszhk_infos(types=None, start_date=None, end_date=None, count=None, df=False):
    # type: (str|List[str], str|Date, str|Date, int, bool) -> List[Dict] | pd.DataFrame
    """查询沪深港通额度数据"""
    if not types:
        types = None
    if isinstance(types, str):
        types = [x.strip() for x in types.split(",")]
    if isinstance(start_date, Date):
        start_date = start_date.strftime("%Y-%m-%d")
    if isinstance(end_date, Date):
        end_date = end_date.strftime("%Y-%m-%d")

    req = GetQuotaShszhkInfosReq(
        types=types,
        start_date=start_date,
        end_date=end_date,
        count=count,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_quota_shszhk_infos(req)
    check_gm_status(status)
    rsp = GetQuotaShszhkInfosRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data)
    return data


def stk_hk_inst_holding_detail_info(symbols=None, trade_date=None, df=False):
 # type: (str|List[str], str|Date, bool) -> List[Dict] | pd.DataFrame
    """查询沪深港通标的港股机构持股明细数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [x.strip() for x in symbols.split(",")]
    if isinstance(trade_date, Date):
        trade_date = trade_date.strftime("%Y-%m-%d")

    req = GetHkInstHoldingDetailInfoReq(
        symbols=symbols,
        trade_date=trade_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_hk_inst_holding_detail_info(req)
    check_gm_status(status)
    rsp = GetHkInstHoldingDetailInfoRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data)
    return data


def stk_hk_inst_holding_info(symbols=None, trade_date=None, df=False):
 # type: (str|List[str], str|Date, bool) -> List[Dict] | pd.DataFrame
    """查询沪深港通标的港股机构持股数据"""
    if not symbols:
        symbols = None
    elif isinstance(symbols, str):
        symbols = [x.strip() for x in symbols.split(",")]
    if isinstance(trade_date, Date):
        trade_date = trade_date.strftime("%Y-%m-%d")

    req = GetHkInstHoldingInfoReq(
        symbols=symbols,
        trade_date=trade_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_hk_inst_holding_info(req)
    check_gm_status(status)
    rsp = GetHkInstHoldingInfoRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data)
    return data


def stk_active_stock_top10_shszhk_info(types=None, trade_date=None, df=False):
    # type: (str|List[str], str|Date, bool) -> List[Dict] | pd.DataFrame
    """查询沪深港通十大活跃成交股数据"""
    if not types:
        types = None
    if isinstance(types, str):
        types = [x.strip() for x in types.split(",")]
    if isinstance(trade_date, Date):
        trade_date = trade_date.strftime("%Y-%m-%d")

    req = GetActiveStockTop10ShszhkInfoReq(
        types=types,
        trade_date=trade_date,
    )
    req = req.SerializeToString()
    status, result = py_gmi_stk_active_stock_top10_shszhk_info(req)
    check_gm_status(status)
    rsp = GetActiveStockTop10ShszhkInfoRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data)
    return data

@cached(cache=TTLCache(maxsize=1024, ttl=900),key=_make_hash_key)
def stk_get_money_flow(symbols, trade_date=None):
    # type: (str|List[str], str) -> List[Dict]
    if isinstance(symbols, list):
        symbols = ",".join(symbols)

    if trade_date is None:
        trade_date = ''
    req = GetMoneyFlowReq(
        symbols=symbols,
        trade_date=trade_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_money_flow(req)
    check_gm_status(status)
    rsp = GetMoneyFlowRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)

@cached(cache=TTLCache(maxsize=1024, ttl=900),key=_make_hash_key)
def stk_get_finance_audit(symbols, date = None, rpt_date = None, df = False):
    # type: (str|List[str], str, str, bool) -> List[Dict]|pd.DataFrame
    if isinstance(symbols, list):
        symbols = ",".join(symbols)

    if date is None:
        date = ''
    if rpt_date is None:
        rpt_date = ''

    req = GetFinanceAuditReq(
        symbols=symbols, date=date, rpt_date=rpt_date
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_finance_audit(req)
    check_gm_status(status)
    rsp = GetFinanceAuditRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data)
    return data

@cached(cache=TTLCache(maxsize=1024, ttl=900),key=_make_hash_key)
def stk_get_finance_forecast(symbols, rpt_type = None, date = None, df=False):
    # type: (str|List[str], int, str, bool) -> List[Dict]|pd.DataFrame
    if isinstance(symbols, list):
        symbols = ",".join(symbols)

    if rpt_type is None:
        rpt_type = ''
    if date is None:
        date = ''

    req = GetFinanceForecastReq(
        symbols=symbols,
        rpt_type=str(rpt_type),
        date=date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_stk_get_finance_forecast(req)
    check_gm_status(status)
    rsp = GetFinanceForecastRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    if df:
        return pd.DataFrame(data)
    return data

@cached(cache=TTLCache(maxsize=1024, ttl=900),key=_make_hash_key)
def fnd_get_share(fund, start_date=None, end_date=None):
    # type: (str, str, str) -> List[Dict]

    if start_date is None:
        start_date = ''
    if end_date is None:
        end_date = ''

    req = GetShareReq(
        fund=fund,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_fnd_get_share(req)
    check_gm_status(status)
    rsp = GetShareRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)

@cached(cache=TTLCache(maxsize=1024, ttl=900),key=_make_hash_key)
def bnd_get_analysis(symbol, start_date=None, end_date=None):
    # type: (str, str, str) -> List[Dict]

    if start_date is None:
        start_date = ''
    if end_date is None:
        end_date = ''

    req = GetAnalysisReq(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_bnd_get_analysis(req)
    check_gm_status(status)
    rsp = GetAnalysisRsp()
    rsp.ParseFromString(result)
    result = protobuf_to_dict(rsp, datetime_to_str=True)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    return pd.DataFrame(data)

def get_open_call_auction (symbols, trade_date=None):
    # type: (str|List[str], str) -> List[Dict]

    if isinstance(symbols, str):
        symbols = [symbol.strip() for symbol in symbols.split(",")]

    req = GetOpenCallAuctionReq(
        symbols=symbols,
        trade_date=trade_date,
    )

    req = req.SerializeToString()
    status, result = py_gmi_get_open_call_auction(req)
    check_gm_status(status)
    rsp = GetOpenCallAuctionRsp()
    rsp.ParseFromString(result)

    result = []
    for tick in rsp.data:
        item = {}
        item['symbol'] = tick.symbol

        if isinstance(tick.created_at, Timestamp):
            # 这个方法是对value.ToDatetime()的改造， 防止1969年报错
            _NANOS_PER_SECOND = 1000000000
            deltasec = tick.created_at.seconds + tick.created_at.nanos / float(_NANOS_PER_SECOND)
            item['time'] = utc_datetime2beijing_datetime(datetime(1970, 1, 1) + timedelta(seconds=deltasec))

        item['current_price'] = round_float(tick.price)
        item['open_volume'] = tick.cum_volume
        item['open_amount'] = tick.cum_amount
        for i in range(0, len(tick.quotes)):
            item.update({f'ask_v{i + 1}': tick.quotes[i].ask_v})
            item.update({f'ask_p{i + 1}': round_float(tick.quotes[i].ask_p)})
            item.update({f'bid_v{i + 1}': tick.quotes[i].bid_v})
            item.update({f'bid_p{i + 1}': round_float(tick.quotes[i].bid_p)})
        result.append(item)

    return pd.DataFrame(result) # type: List[Dict[str, Any]]
