"""
期权定价计算
"""
from datetime import datetime as Datetime, timedelta
from gm import utils
from gm.enum import SEC_TYPE_OPTION
from gm.api.query import get_history_instruments, get_instrumentinfos, get_instruments, history_n
from typing import Dict, Text

import numpy as np
import pandas as pd

from gm._calc import binomial, black_scholes, black76
from gm.utils import load_to_second, to_datestr


def _get_cp(call_or_put):
    # type: (Text) -> float
    return 1.0 if call_or_put == 'C' else -1.0


def option_calculate_t(start_time=Datetime.now(), end_time=""):
    # type: (Text|Datetime, Text|Datetime) -> float
    """
    计算剩余时间 \n
    params:\n
    \t start_time:      开始时间，默认当前时间
    \t end_time:        结束时间(通常为退市时间，必填)
    start_time和start_time必须是pd.to_dateime()可识别的字符串str格式，
    例'yyyy-mm-dd', 'yyyy-mm-dd %H:%M:%S',或者是datetime对象
    """
    return (pd.to_datetime(end_time) - pd.to_datetime(start_time)) / timedelta(365)


def option_calculate_price(s, k, v, t, call_or_put, r=0.02, pricing_model="black_scholes", n=15):
    # type: (float, float, float, float, Text, float, Text, int) -> float
    """
    计算期权理论价格 \n
    params: \n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_price(s, k, r, v, t, cp)
    elif pricing_model == 'black76':
        return black76.calculate_price(s, k, r, v, t, cp)
    elif pricing_model == 'binomial':
        return binomial.calculate_price(s, k, r, v, t, cp, n)


def option_calculate_greeks(s, k, v, t, call_or_put, r=0.02, pricing_model="black_scholes", n=15, cash=False):
    # type: (float, float, float, float, Text, float, Text, int, bool) -> Dict[Text, float]
    """
    计算期权全部希腊字母greeks \n
    params:\n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    \t cash:            现金希腊值,默认False
    return: dict \n

    \t delta:           期权价格对标的物价格的一阶偏微分
    \t vega:            期权价格对标的物波动率的一阶偏微分
    \t theta:           期权价格对时间的一阶偏微分
    \t rho:             期权价格对利率的一阶偏微分
    \t gamma:           期权价格对标的物价格的二阶偏微分
    """
    greeks = {}
    greeks['delta'] = option_calculate_delta(
        s, k, v, t, call_or_put, r, pricing_model, n, cash)
    greeks['vega'] = option_calculate_vega(
        s, k, v, t, call_or_put, r, pricing_model, n, cash)
    greeks['theta'] = option_calculate_theta(
        s, k, v, t, call_or_put, r, pricing_model, n, cash)
    greeks['rho'] = option_calculate_rho(
        s, k, v, t, call_or_put, r, pricing_model, n, cash)
    greeks['gamma'] = option_calculate_gamma(
        s, k, v, t, call_or_put, r, pricing_model, n, cash)

    return greeks


def option_calculate_delta(s, k, v, t, call_or_put, r=0.02, pricing_model='black_scholes', n=15, cash=False):
    # type: (float, float, float, float, Text, float, Text, int, bool) -> float
    """
    计算期权delta \n
    params: \n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    \t cash:            现金希腊值,默认False
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_delta(s, k, r, v, t, cp, cash)
    elif pricing_model == 'black76':
        return black76.calculate_delta(s, k, r, v, t, cp, cash)
    elif pricing_model == 'binomial':
        return binomial.calculate_delta(s, k, r, v, t, cp, cash, n)


def option_calculate_vega(s, k, v, t, call_or_put, r=0.02, pricing_model='black_scholes', n=15, cash=False):
    # type: (float, float, float, float, Text, float, Text, int, bool) -> float
    """
    计算期权vega \n
    params: \n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    \t cash:            现金希腊值,默认False
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_vega(s, k, r, v, t, cash)
    elif pricing_model == 'black76':
        return black76.calculate_vega(s, k, r, v, t, cash)
    elif pricing_model == 'binomial':
        return binomial.calculate_vega(s, k, r, v, t, cp, cash, n)


def option_calculate_theta(s, k, v, t, call_or_put, r=0.02, pricing_model='black_scholes', n=15, cash=False):
    # type: (float, float, float, float, Text, float, Text, int, bool) -> float
    """
    计算期权theta \n
    params: \n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    \t cash:            现金希腊值,默认False
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_theta(s, k, r, v, t, cp, cash)
    elif pricing_model == 'black76':
        return black76.calculate_theta(s, k, r, v, t, cp, cash)
    elif pricing_model == 'binomial':
        return binomial.calculate_theta(s, k, r, v, t, cp, cash, n)


def option_calculate_rho(s, k, v, t, call_or_put, r=0.02, pricing_model='black_scholes', n=15, cash=False):
    # type: (float, float, float, float, Text, float, Text, int, bool) -> float
    """
    计算期权rho \n
    params: \n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    \t cash:            现金希腊值,默认False
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_rho(s, k, r, v, t, cp, cash)
    elif pricing_model == 'black76':
        return black76.calculate_rho(s, k, r, v, t, cp, cash)
    elif pricing_model == 'binomial':
        return binomial.calculate_rho(s, k, r, v, t, cp, cash, n)


def option_calculate_gamma(s, k, v, t, call_or_put, r=0.02, pricing_model='black_scholes', n=15, cash=False):
    # type: (float, float, float, float, Text, float, Text, int, bool) -> float
    """
    计算期权gamma \n
    params: \n
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t v:               波动率，例0.16
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    \t cash:            现金希腊值,默认False
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_gamma(s, k, r, v, t, cash)
    elif pricing_model == 'black76':
        return black76.calculate_gamma(s, k, r, v, t, cash)
    elif pricing_model == 'binomial':
        return binomial.calculate_gamma(s, k, r, v, t, cp, cash, n)


def option_calculate_iv(p, s, k, t, call_or_put, r=0.02, pricing_model='black_scholes', n=15):
    # type: (float, float, float, float, Text, float, Text, int) -> float
    """
    计算期权隐含波动率 \n
    params: \n
    \t p:               期权价格
    \t s:               标的物价格
    \t k:               执行价格(行权价)
    \t t:               剩余时间，例(datetime(2021, 7, 28, 15) - datetime.now())/timedelta(365)
    \t call_or_put:     认购：'C'/认沽：'P'
    \t r:               无风险利率，默认0.02
    \t pricing_model:   定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:               binomial模型迭代次数，默认15
    """
    cp = _get_cp(call_or_put)
    if pricing_model == 'black_scholes':
        return black_scholes.calculate_iv(p, s, k, r, t, cp)
    elif pricing_model == 'black76':
        return black76.calculate_iv(p, s, k, r, t, cp)
    elif pricing_model == 'binomial':
        return binomial.calculate_iv(p, s, k, r, t, cp, n)


def option_calculate_hv(price, frequency='1d'):
    # type: (pd.Series, Text) -> float
    """
    计算期权历史波动率hv \n
    params:
    \t price:       标的物价格
    \t frequency:   频率, 支持 'tick', '1d', '15s', '30s' 等,详情见股票行情数据和期货行情数据
    """
    if not isinstance(price, pd.Series):
        raise TypeError("price 为标的物价格序列pd.Series类型, 传入类型为", type(price))
    price = price.dropna()
    if price.shape[0] < 5:
        return 0
    ret_series = np.log(price.shift(1)[1:] / price[1:])
    second = load_to_second(frequency)
    if 'd' not in frequency:
        return np.std(ret_series) * np.sqrt(252 * 4 * 60 / (second / 60))
    else:
        return np.std(ret_series) * np.sqrt(252)


def option_calculate_ivsurface(underlying_symbol,
                               call_or_put,
                               trade_date=Datetime.now(),
                               adjust_flag=None,
                               r=0.02,
                               pricing_model='black_scholes',
                               n=15):
    # type: (Text, Text, Text|Datetime, Text|None, float, Text, int) -> pd.DataFrame
    """
    计算隐含波动率曲面 \n
    params:
    \t underlying_symbol:       标的物symbol，全部大写，不指定具体到期月份, 例'DCE.V'
    \t call_or_put:             认购：'C'/认沽：'P'
    \t trade_date:              交易时间，默认当前最新时间
    \t adjust_flag:             表示是否过滤除权后合约行权价(带A合约），不填默认为None
                                'M'表示不返回带A合约, 'A'表示只返回带A合约, None表示不做过滤都返回
    \t r:                       无风险利率，默认0.02
    \t pricing_model:           定价模型，'black_scholes'/'black76'/'binomial'，默认'black_scholes'
    \t n:                       binomial模型迭代次数，默认15
    """
    date = utils.to_datestr(trade_date)

    # 查询交易标的基本信息
    fields = "underlying_symbol,call_or_put,symbol,exercise_price,delisted_date"
    exchange = underlying_symbol.split(".")[0]
    df = get_instrumentinfos(
        sec_types=SEC_TYPE_OPTION,  # 期权
        exchanges=exchange,
        df=True,
        fields=fields,
    )  # type: pd.DataFrame
    # 过滤标的物
    df = df[df["underlying_symbol"] == underlying_symbol]
    # 过滤期权到期日
    df["delisted_date"] = df["delisted_date"].dt.strftime('%Y-%m-%d')
    df = df[df["delisted_date"] >= to_datestr(trade_date)]
    # 过滤认购/认沽
    df = df[df["call_or_put"] == call_or_put]

    # 获取期权价格
    df["option_price"] = df["symbol"].apply(
        _get_option_price, args=(trade_date,))
    s = _get_option_price(underlying_symbol, trade_date)
    # 计算剩余时间
    df["t"] = option_calculate_t(start_time=date, end_time=df["delisted_date"])
    # 计算隐含波动率
    df["implied_volatility"] = df.apply(
        lambda df: option_calculate_iv(
            p=df["option_price"],
            s=s,
            k=df["exercise_price"],
            t=df["t"],
            call_or_put=call_or_put,
            r=r,
            pricing_model=pricing_model,
            n=n,
        ),
        axis=1,
    )

    # 查询合约是否经过调整
    symbols = df["symbol"].drop_duplicates().to_list()
    symbols = ",".join(symbols)
    is_adjusted_df = _get_is_adjusted_df(symbols, date)
    if is_adjusted_df.empty:
        df["is_adjusted"] = 0
    else:
        df = pd.merge(df, is_adjusted_df)

    # 过滤除权后合约行权价(带A合约)
    if adjust_flag:
        if adjust_flag.upper() == 'A':
            df = df[df["is_adjusted"] == 1]
        elif adjust_flag.upper() == 'M':
            df = df[df["is_adjusted"] == 0]

    # 取到期日, 行权价, 隐含波动率
    columns = ["delisted_date", "exercise_price", "implied_volatility"]
    return df[columns].sort_values(by="delisted_date")  # 按到期日排序输出


def _get_option_price(symbol, trade_date):
    # type: (Text, Text|Datetime) -> float
    result = history_n(
        symbol=symbol,
        frequency="60s",
        count=1,
        end_time=trade_date,
    )
    if result:
        return result[0]['close']
    else:
        return 0


def _get_is_adjusted_df(symbols, date):
    # type: (Text, Text) -> pd.DataFrame
    if date == utils.to_datestr(Datetime.now()):
        df = get_instruments(
            symbols=symbols,
            fields='symbol,is_adjusted',
            df=True,
        )
    else:
        df = get_history_instruments(
            symbols=symbols,
            fields='symbol,is_adjusted',
            start_date=date,
            end_date=date,
            df=True,
        )
    return df
