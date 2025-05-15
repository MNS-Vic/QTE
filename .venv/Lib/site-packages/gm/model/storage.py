# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

import collections
import datetime
import struct
import sys
import sysconfig

import pandas as pd
from typing import Callable, Text, Dict, Any, List, Set, Sequence, Union

from gm import __version__
from gm.constant import DATA_TYPE_L2TRANSACTION
from gm.csdk.c_sdk import (
    BarLikeDict2,
    TickLikeDict2,
    py_gmi_get_cash,
    py_gmi_get_positions,
    py_gmi_get_accounts,
    py_gmi_set_timer,
    gmi_now_plus,
    c_status_fail,
    py_gmi_get_account_status,
)
from gm.enum import MODE_BACKTEST, MODE_LIVE
from gm.model import DictLikeConnectionStatus, DictLikeError
from gm.model.account import Account
from gm.pb.account_pb2 import Positions, Cashes, Accounts, AccountStatuses
from gm.pb.trade_pb2 import GetCashReq, GetPositionsReq
from gm.pb.tradegw_service_pb2 import GetAccountStatusesReq
from gm.pb_to_dict import protobuf_to_dict
from gm.utils import adjust_frequency, gmsdklogger, BJ_TZ
from gm.api._errors import GmError


class BarSubInfo(object):
    __slots__ = ["symbol", "frequency"]

    def __init__(self, symbol, frequency):
        self.symbol = symbol  # type: Text
        self.frequency = frequency  # type: Text

    def __hash__(self):
        return hash((self.symbol, self.frequency))

    def __eq__(self, other):
        if not isinstance(other, BarSubInfo):
            return False

        return (self.symbol, self.frequency) == (other.symbol, other.frequency)


class BarWaitgroupInfo(object):
    __slots__ = ["symbols", "frequency", "timeout_seconds"]

    def __init__(self, frequency, timeout_seconds):
        self.symbols = set()  # type: Set[Text]
        self.frequency = frequency  # type: Text
        self.timeout_seconds = timeout_seconds  # type: int

    def add_one_symbol(self, symbol):
        # type: (Text) -> None
        self.symbols.add(symbol)

    def add_symbols(self, syms):
        # type: (Sequence[Text]) -> None
        self.symbols.union(syms)

    def remove_one_symbol(self, symbol):
        # type: (Text) -> None
        self.symbols.discard(symbol)

    def is_symbol_in(self, symbol):
        # type: (Text) -> bool
        return symbol in self.symbols

    def __len__(self):
        return len(self.symbols)


class DefaultFileModule(object):
    def on_tick(self, ctx, tick):
        print("请初始化on_tick方法")

    def on_bar(self, ctx, bar):
        print("请初始化on_bar方法")

    def on_bod(self, ctx, bod):
        print("请初始化on_bod方法")

    def on_eod(self, ctx, eod):
        print("请初始化on_eod方法")


class Context(object):
    """
    策略运行的上下文类. 这在整个进程中要保证是单一实例
    注意: 一个运行的python进程只能运行一个策略.
    警告: 客户写的策略代码不要直接使用这个类来实例化, 而是使用 sdk 实例化好的 context 实例
    """

    inside_file_module = DefaultFileModule()
    on_bar_fun = None
    on_tick_fun = None
    on_depth_fun = None
    on_order_status_mm_fun = None
    on_l2order_queue_fun = None
    on_l2order_fun = None
    on_l2transaction_fun = None
    init_fun = None
    on_execution_report_fun = None
    on_order_status_fun = None
    on_algo_order_status_fun = None
    on_backtest_finished_fun = None
    on_parameter_fun = None
    on_error_fun = None
    on_shutdown_fun = None
    on_trade_data_connected_fun = None
    on_market_data_connected_fun = None
    on_account_status_fun = None
    on_market_data_disconnected_fun = None
    on_trade_data_disconnected_fun = None
    on_customized_message_fun = None

    strategy_id = ""  # type: Text
    token = None  # type: Text
    mode = None  # type: int
    backtest_and_not_wait_group = False  # type: bool
    _temporary_now = (
        None
    )  # type: datetime.datetime  # 用于回测模式下, 且wait_group=True时, 要修改context.now 时的值, 因为这时时钟是走到了下一个时刻, 而数据还是上一时刻的, 所以要修改时钟为上一时刻,跟数据时间一致
    backtest_start_time = None  # type: Text
    backtest_end_time = None  # type: Text
    adjust_mode = None  # type: int
    inside_schedules = {}  # type: Dict[Text, Any]
    _timer_funcs = {}  # type: Dict[int, Callable[[Context], None]]

    sdk_lang = "python{}.{}".format(
        sys.version_info.major, sys.version_info.minor
    )  # type: Text
    sdk_version = __version__.__version__  # type: Text
    sdk_arch = str(struct.calcsize("P") * 8)  # type: Text
    sdk_os = sysconfig.get_platform()  # type: Text

    max_tick_data_count = 1
    # type: Dict[Text, Deque[Any]]  # 以 bar.symbol+bar.frequency作为key
    max_bar_data_count = 1
    bar_data_set = set()  # type: Set  # 保存已有的bar的 (symbol, frequency, eob), 用于判断是否重复值
    tick_sub_symbols = set()  # type: Set[Text]   # 订阅tick的symbol
    bar_sub_infos = set()  # type: Set[BarSubInfo]   # 订阅bar的信息集合
    # 订阅bar用freequency做为key, 相应的股票集合做为value
    bar_waitgroup_frequency2Info = dict()  # type: Dict[Text, BarWaitgroupInfo]

    is_set_onbar_timeout_check = False

    def __init__(self):
        self.inside_accounts = {}  # type: Dict[Text, Account]
        self._cache = _Cache()

    def _set_onbar_waitgroup_timeout_check(self):
        if self.is_live_model() and not self.is_set_onbar_timeout_check:
            # 实时模式下 3000毫秒触发一次timer事件 用来处理wait_group的过期.
            # fixme 这里底层不支持动态设置多个, 先固定一个吧
            py_gmi_set_timer(3000)
            self.is_set_onbar_timeout_check = True

    def _add_bar2bar_data_cache(self, bar):
        # type: (Text, Dict[Text, Any]) -> None
        kk = (bar["symbol"], bar["frequency"], bar["eob"])
        if kk in self.bar_data_set:
            gmsdklogger.debug("bar data %s 已存在, 跳过不加入", kk)
        else:
            context._add_data_to_cache(bar["symbol"], bar["frequency"], bar)
            self.bar_data_set.add(kk)

    @property
    def has_wait_group(self):
        # type: () ->bool
        return len(self.bar_waitgroup_frequency2Info) > 0

    @property
    def now(self):
        # type: ()->datetime.datetime
        """
        实时模式返回当前本地时间, 回测模式返回当前回测时间
        """
        if self._temporary_now:  # 这个是在回测模式且wait_group=True的情况下时存在的
            if self._temporary_now.tzinfo is None:
                return self._temporary_now.replace(tzinfo=BJ_TZ)
            return self._temporary_now

        now = gmi_now_plus()
        # now == 0 说明是回测模式而且处于init装填 c sdk拿不到时间
        if now == 0:
            return datetime.datetime.strptime(
                context.backtest_start_time, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=BJ_TZ)

        return datetime.datetime.fromtimestamp(now).replace(tzinfo=BJ_TZ)

    @property
    def symbols(self):
        # type: ()->Set[Text]
        """
        订阅bar跟tick的symbol集合
        bar 的symbols + tick 的symbols
        """
        return set(barsub.symbol for barsub in self.bar_sub_infos).union(
            self.tick_sub_symbols
        )

    @property
    def accounts(self):
        # type: ()->Dict[Text, Account]
        """
        用户资金 & 持仓情况
        """
        if not self.inside_accounts:
            self._set_accounts()
        return self.inside_accounts

    def account(self, account_id=""):
        accounts = self.accounts
        # 只有一个账户 且未有account_id 的情况下返回唯一用户
        if not account_id and len(accounts) == 1:
            default_id = sorted(accounts.keys())[0]
            return accounts.get(default_id)

        return accounts.get(account_id)

    @property
    def parameters(self):
        """
        动态参数
        """
        from gm.api.basic import get_parameters

        parameters = get_parameters()
        return {p["key"]: p for p in parameters}

    def _set_accounts(self):
        status, result = py_gmi_get_accounts()
        if c_status_fail(status, "py_gmi_get_accounts") or not result:
            return

        accounts = Accounts()
        accounts.ParseFromString(result)
        for account in accounts.data:
            self._get_account_info(account.account_id, account.account_name)

    def data(self, symbol, frequency, count=1, fields=None):
        # type: (str, str, int, str, bool) -> Union[List[Union[TickLikeDict2, BarLikeDict2]], pd.DataFrame]
        """
        获取订阅的bar或tick滑窗, 数据为包含当前时刻推送bar或tick的前count条bar(tick)数据.
        返回的数据类型为 pandas的DataFrame.
        bar_df 参数已弃用

        fields 参数的取值情况:
          1. 当 frequency == 'tick' 时, fields的取值可以为:'quotes,symbol,created_at,price,open,high,low,cum_volume,cum_amount,cum_position,last_amount,last_volume,trade_type'
          2. 当 数据为bar时, fields的取值可以为: 'symbol,eob,bob,open,close,high,low,volume,amount,pre_close,position,frequency'
        """
        if not frequency:
            frequency = ""
        frequency = frequency.strip()
        if frequency == DATA_TYPE_L2TRANSACTION:
            gmsdklogger.warning(
                "context.data 不支持 frequency={}, 返回空数据", DATA_TYPE_L2TRANSACTION
            )
            return pd.DataFrame()

        symbol = symbol.strip()
        if "," in symbol:
            gmsdklogger.warning("不支持返回多个symbol, 返回空list")
            return pd.DataFrame()
        if "," in frequency:
            gmsdklogger.warning("不支持多个频率, 返回空list")
            return pd.DataFrame()

        if count < 1:
            count = 1
        frequency = adjust_frequency(frequency)

        return self._cache.get_data(symbol, frequency, count, fields)

    def _get_account_info(self, account_id, account_name):
        # 资金信息
        req = GetCashReq()
        req.account_id = account_id
        req = req.SerializeToString()
        status, result = py_gmi_get_cash(req)
        if c_status_fail(status, "py_gmi_get_cash"):
            return
        if result:
            cashes = Cashes()
            cashes.ParseFromString(result)
            cashes = [protobuf_to_dict(cash) for cash in cashes.data]
            cash = cashes[0]
        else:
            cash = {}

        # 持仓信息
        req = GetPositionsReq()
        req.account_id = account_id
        req = req.SerializeToString()
        status, result = py_gmi_get_positions(req)
        if c_status_fail(status, "py_gmi_get_positions"):
            return
        if result:
            positions = Positions()
            positions.ParseFromString(result)
            # positions = [protobuf_to_dict(position, including_default_value_fields=True) for position in positions.data]
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

        positions_infos = {
            (
                position["symbol"],
                position["side"],
                position["covered_flag"],
            ): position
            for position in positions
        }

        # 状态信息  req = tradegw.api.GetAccountStatusesReq, res = core.api.AccountStatuses
        acc_status_req = GetAccountStatusesReq()
        acc_status_req.account_ids.append(account_id)
        acc_status_req = acc_status_req.SerializeToString()
        status, result = py_gmi_get_account_status(acc_status_req)
        if c_status_fail(status, "py_gmi_get_account_status"):
            return
        conn_status = None
        if result:
            acc_statuses = AccountStatuses()
            acc_statuses.ParseFromString(result)
            if len(acc_statuses.data) > 0:
                conn_status = acc_statuses.data[0].status

        status_dict = DictLikeConnectionStatus()
        status_dict["state"] = conn_status.state
        error_dict = DictLikeError()
        status_dict["error"] = error_dict
        if conn_status.error is not None:
            error_dict["code"] = conn_status.error.code
            error_dict["type"] = conn_status.error.type
            error_dict["info"] = conn_status.error.info

        account = Account(account_id, account_name, cash, positions_infos, status_dict)
        self.inside_accounts[account_id] = account

    def is_backtest_model(self):
        # type: () ->bool
        """
        是否回测模式
        """
        return self.mode == MODE_BACKTEST

    def is_live_model(self):
        # type: () ->bool
        """
        是否实时模式
        """
        return self.mode == MODE_LIVE

    def _init_cache(self, symbol, freq, format, fields, count):
        self._cache.init_cache(symbol, freq, format, fields, count)

    def _has_cache(self, symbol, freq):
        return self._cache.has_cache(symbol, freq)

    def _rm_cache(self, symbol, freq):
        self._cache.rm_cache(symbol, freq)

    def _add_data_to_cache(self, symbol, freq, data):
        if data is None:
            return
        self._cache.add_data(symbol, freq, data)


class _Cache:
    def __init__(self):
        self._col_cache = {} # type: Dict[str, _ColQuote]
        self._row_cache = {} # type: Dict[str, _RowQuote]
        self._initialized = set()

    def init_cache(self, symbol, freq, format, fields, count):
        key = (symbol, freq)
        if format == "col":
            self._col_cache[key] = _ColQuote(symbol, freq, format, fields, count)
        else:
            self._row_cache[key] = _RowQuote(symbol, freq, format, fields, count)

        if key in self._initialized:
            self._initialized.remove(key)

    def rm_cache(self, symbol, freq):
        key = (symbol, freq)
        if key in self._col_cache:
            del self._col_cache[key]
        if key in self._row_cache:
            del self._row_cache[key]
        if key in self._initialized:
            self._initialized.remove(key)

    def has_cache(self, symbol, freq):
        key = (symbol, freq)
        if key in self._col_cache:
            return True
        if key in self._row_cache:
            return True
        return False

    def add_data(self, symbol, freq, data: Dict):
        key = (symbol, freq)
        if key in self._col_cache:
            self._col_cache[key].add_data(data)
        if key in self._row_cache:
            self._row_cache[key].add_data(data)

    def get_data(self, symbol, freq, count, fields):
        key = (symbol, freq)
        if key not in self._col_cache and key not in self._row_cache:
            raise GmError(1027, f"获取窗口数据前需先订阅行情: {symbol}, {freq}", "context.data")

        if key in self._col_cache:
            q = self._col_cache[key]
        else:
            q = self._row_cache[key]

        if key not in self._initialized:
            miss_count = q.miss_count(count)
            if miss_count != 0:
                from gm.api.query import history_n
                query_data_end_time = q.earliest_time()
                if query_data_end_time is None:
                    query_data_end_time = context.now
                adjust_end_time = (
                    context.now.strftime("%Y-%m-%d %H:%M:%S")
                    if context.is_live_model()
                    else context.backtest_end_time
                )
                data = history_n(
                    symbol=symbol,
                    frequency=freq,
                    count=miss_count+1,
                    end_time=query_data_end_time,
                    adjust=context.adjust_mode,
                    adjust_end_time=adjust_end_time,
                )
                if freq == "1d":
                    for item in data[::-1]:
                        item["eob"] = item["eob"].replace(hour=15, minute=15, second=1)
                        #过滤大于now的日线
                        if context.now < item["eob"]:
                            continue
                        q.add_data(item, left=True)
                else:
                    for item in data[::-1]:
                        q.add_data(item, left=True)
            self._initialized.add(key)

        return q.get_data(fields, count)


class _RowQuote:
    def __init__(self, symbol, freq, format, fields, count):
        self._symbol = symbol
        self._freq = freq
        self._format = format
        self._fields = fields
        self._earliest_time = None
        self._data = collections.deque(maxlen=count)

    def add_data(self, data: Dict, left=False):
        if left and self.full():
            return
        if left and self._earliest_time is not None:
            if (self._freq == "tick") and (data["created_at"] >= self._earliest_time):
                return
            if (self._freq != "tick") and (data["eob"] >= self._earliest_time):
                return
        if self._earliest_time is None:
            if self._freq == "tick":
                self._earliest_time = data["created_at"]
            else:
                self._earliest_time = data["eob"]
        newdata = {}
        for field in self._fields:
            newdata[field] = data.get(field)
        if left:
            self._data.appendleft(newdata)
            return
        self._data.append(newdata)

    def get_data(self, fields, count):
        start = len(self._data)-count
        if start < 0:
            start = 0
        result = []
        for i in range(start, len(self._data)):
            if not fields:
                result.append(self._data[i])
            else:
                result.append({k: v for k, v in self._data[i].items() if k in fields})
        if self._format == "df":
            return pd.DataFrame(result)
        return result

    def miss_count(self, count):
        if count <= len(self._data):
            return 0
        return self._data.maxlen - len(self._data)

    def earliest_time(self):
        return self._earliest_time

    def full(self):
        return len(self._data) == self._data.maxlen


class _ColQuote:
    def __init__(self, symbol, freq, format, fields, count):
        self._symbol = symbol
        self._freq = freq
        self._format = format
        self._fields = fields
        self._earliest_time = None
        self._data = {} # type: Dict[str, collections.deque]
        for field in fields:
            if field == "symbol":
                continue
            self._data[field] = collections.deque(maxlen=count)

    def add_data(self, data: Dict, left=False):
        if left and self.full():
            return
        if left and self._earliest_time is not None:
            if (self._freq == "tick") and (data["created_at"] >= self._earliest_time):
                return
            if (self._freq != "tick") and (data["eob"] >= self._earliest_time):
                return
        if self._earliest_time is None:
            if self._freq == "tick":
                self._earliest_time = data["created_at"]
            else:
                self._earliest_time = data["eob"]
        for field in self._fields:
            if field == "symbol": # 所有的symbol都一样,不需要队列保存
                continue
            if field in ["bid_p", "bid_v", "ask_p", "ask_v"]:
                quotes = data.get("quotes")
                if quotes and len(quotes) != 0:
                    item = quotes[0].get(field)
                else:
                    item = None
            else:
                item = data.get(field)
            if left:
                self._data[field].appendleft(item)
                continue
            self._data[field].append(item)

    def get_data(self, fields, count):
        if not fields:
            fields = self._fields
        result = {}
        for field in self._fields:
            if field not in fields:
                continue
            if field == "symbol" and field in fields:
                result["symbol"] = self._symbol
                continue
            q = self._data[field]
            start = len(q) - count
            if start < 0:
                start = 0
            l = []
            for i in range(start, len(q)):
                l.append(q[i])
            result[field] = l
        return result

    def miss_count(self, count):
        for q in self._data.values():
            if count <= len(q):
                return 0
            return q.maxlen - len(q)

    def earliest_time(self):
        return self._earliest_time

    def full(self):
        for q in self._data.values():
            return len(q) == q.maxlen


# 提供给API的唯一上下文实例
context = Context()
