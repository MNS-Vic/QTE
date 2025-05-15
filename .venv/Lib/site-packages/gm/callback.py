# coding=utf-8
"""
回调任务分发
"""
from __future__ import unicode_literals, print_function, absolute_import

import collections
import datetime
import time
import re

import six
from typing import Dict, Text, List, Set

from gm.constant import (
    CALLBACK_TYPE_TICK,
    CALLBACK_TYPE_DEPTH,
    CALLBACK_TYPE_BAR,
    CALLBACK_TYPE_SCHEDULE,
    CALLBACK_TYPE_EXECRPT,
    CALLBACK_TYPE_ORDER,
    CALLBACK_TYPE_INDICATOR,
    CALLBACK_TYPE_CASH,
    CALLBACK_TYPE_POSITION,
    CALLBACK_TYPE_PARAMETERS,
    CALLBACK_TYPE_ERROR,
    CALLBACK_TYPE_TIMER,
    CALLBACK_TYPE_BACKTEST_FINISH,
    CALLBACK_TYPE_STOP,
    CALLBACK_TYPE_TRADE_CONNECTED,
    CALLBACK_TYPE_DATA_CONNECTED,
    CALLBACK_TYPE_ACCOUNTSTATUS,
    CALLBACK_TYPE_DATA_DISCONNECTED,
    CALLBACK_TYPE_TRADE_DISCONNECTED,
    CALLBACK_TYPE_INIT,
    CALLBACK_TYPE_L2TRANSACTION,
    CALLBACK_TYPE_ALGOORDER,
    CALLBACK_TYPE_L2ORDER,
    CALLBACK_TYPE_L2ORDER_QUEUE,
    CALLBACK_TYPE_USER_TIMER,
    CALLBACK_TYPE_CUSTOMIZED_MESSAGE,
)
from gm.csdk.c_sdk import BarLikeDict2, TickLikeDict2, py_gmi_use_dsproxy
from gm.enum import MODE_BACKTEST, MODE_LIVE, OrderBusiness_MARKET_MAKING
from gm.model import (
    DictLikeDepth,
    DictLikeExecRpt,
    DictLikeOrder,
    DictLikeIndicator,
    DictLikeOrderMM,
    DictLikeParameter,
    DictLikeAccountStatus,
    DictLikeConnectionStatus,
    DictLikeError,
    DictLikeL2Transaction,
    DictLikeAlgoOrder,
    DictLikeL2Order,
    DictLikeL2OrderQueue,
)
from gm.model.storage import Context, context, BarWaitgroupInfo, BarSubInfo
from gm.pb.account_pb2 import ExecRpt, Order, Cash, Position, AccountStatus, AlgoOrder
from gm.pb.data_pb2 import Depth, Tick, Bar, L2Transaction, L2Order, L2OrderQueue
from gm.pb.common_pb2 import CustomizedMessage
from gm.pb.performance_pb2 import Indicator
from gm.pb.rtconf_pb2 import Parameters
from gm.pb_to_dict import protobuf_to_dict
from gm.utils import (
    gmsdklogger,
    protobuf_timestamp2bj_datetime,
    round_float,
)
from gm.csdk import gmpytool
from gm.api._errors import check_gm_status


def init_callback(data):
    context.bar_data_set.clear()  # 清空之前的
    if context.is_backtest_model() and py_gmi_use_dsproxy():
        print(
            """
回测开始，正下载数据到本地...

提示：
1. 如果请求数据量较大，首次准备数据可能需要较长时间，请耐心等待。
2. 可预先下载数据以加速回测，功能入口：掘金终端->量化研究->数据管理
3. 相关指引：https://www.myquant.cn/docs2/operatingInstruction/study/数据管理.html
"""
        )
    if context.init_fun is not None:
        context.init_fun(context)

def tick_callback_new(data):
    # 回测模式使用 gmpytool.to_tick 函数解包数据, 提高性能
    if context.is_backtest_model():
        tick = {}
        status = gmpytool.to_tick(data, len(data), tick)
        check_gm_status(status)
        tick_callback(tick)
        return

    tick = Tick()
    tick.ParseFromString(data)
    quotes = []
    for q in tick.quotes:  # type: Quote
        quotes.append(
            {
                "bid_p": round_float(q.bid_p),
                "bid_v": q.bid_v,
                "ask_p": round_float(q.ask_p),
                "ask_v": q.ask_v,
                "bid_q": {
                    "total_orders": q.bid_q.total_orders,
                    "queue_volumes": q.bid_q.queue_volumes,
                },
                "ask_q": {
                    "total_orders": q.ask_q.total_orders,
                    "queue_volumes": q.ask_q.queue_volumes,
                },
            }
        )

    if len(quotes) < 10:
        for _ in range(len(quotes), 10):
            zero_val = {
                "bid_p": 0,
                "bid_v": 0,
                "ask_p": 0,
                "ask_v": 0,
                "bid_q": {"total_orders": 0, "queue_volumes": []},
                "ask_q": {"total_orders": 0, "queue_volumes": []},
            }
            quotes.append(zero_val)

    ticknew = {
        "quotes": quotes,
        "symbol": tick.symbol,
        "created_at": protobuf_timestamp2bj_datetime(tick.created_at),
        "price": round_float(tick.price),
        "open": round_float(tick.open),
        "high": round_float(tick.high),
        "low": round_float(tick.low),
        "cum_volume": tick.cum_volume,
        "cum_amount": tick.cum_amount,
        "cum_position": tick.cum_position,
        "last_amount": tick.last_amount,
        "last_volume": tick.last_volume,
        "trade_type": tick.trade_type,
        "flag": tick.flag,  # 协议里新增了这个字段
        "receive_local_time": time.time(),  # 收到时的本地时间秒数
        "iopv": tick.iopv,  # 基金份额参考净值
    }
    tick_callback(ticknew)


def tick_callback(ticknew):
    tick = TickLikeDict2(ticknew)  # type: TickLikeDict2
    symbol = tick["symbol"]
    if symbol not in context.tick_sub_symbols:
        gmsdklogger.debug("tick data symbol=%s 不在订阅列表里, 跳过不处理", symbol)
        return

    context._add_data_to_cache(symbol, "tick", ticknew)
    if context.on_tick_fun is not None:
        context.on_tick_fun(context, tick)


def depth_callback(data):
    if context.on_depth_fun is None:
        return
    depth = Depth()
    depth.ParseFromString(data)
    depth = protobuf_to_dict(
        depth, including_default_value_fields=True, dcls=DictLikeDepth
    )
    context.on_depth_fun(context, depth)


# 回测模式下前一个eob的时间
pre_eob_in_backtest = None  # type: datetime.datetime
# 回测模式且wait_group下的bar集合. 以 frequency 作为 key
bars_in_waitgroup_backtest = collections.defaultdict(
    list
)  # type: Dict[Text, List[BarLikeDict2]]
# 实时模式且wait_group下的bar集合  以 frequency 作为 一级key, eob做为二级key
# type:  Dict[Text, Dict[datetime.datetime, List[BarLikeDict2]]]
bars_in_waitgroup_live = dict()


def bar_callback_new(data):
    # 回测模式使用 gmpytool.to_bar 函数解包数据, 提高性能
    if context.is_backtest_model():
        bar = {}
        status = gmpytool.to_bar(data, len(data), bar)
        check_gm_status(status)
        bar_callback(bar)
        return

    bar = Bar()
    bar.ParseFromString(data)
    barnew = {
        "symbol": bar.symbol,
        "eob": protobuf_timestamp2bj_datetime(bar.eob),
        "bob": protobuf_timestamp2bj_datetime(bar.bob),
        "open": round_float(bar.open),
        "close": round_float(bar.close),
        "high": round_float(bar.high),
        "low": round_float(bar.low),
        "volume": bar.volume,
        "amount": bar.amount,
        "pre_close": round_float(bar.pre_close),
        "position": bar.position,
        "frequency": bar.frequency,
        "receive_local_time": time.time(),  # 收到时的本地时间秒数
    }
    bar_callback(barnew)


def bar_callback(barnew):
    data = BarLikeDict2(barnew)

    global pre_eob_in_backtest, bars_in_waitgroup_backtest, bars_in_waitgroup_live
    bar = data  # type: BarLikeDict2
    symbol, frequency = bar["symbol"], bar["frequency"]  # type: Text, Text
    if BarSubInfo(symbol, frequency) not in context.bar_sub_infos:
        gmsdklogger.debug(
            "bar data symbol=%s frequency=%s 不在订阅列表里, 跳过不处理", symbol, frequency
        )
        return

    # wait_group = True的情况下, 就先不要放入, 不然第一个symbol得到的数据跟别的symbol的数据对不齐
    if not context.has_wait_group:
        context._add_data_to_cache(symbol, frequency, barnew)

    if context.on_bar_fun is None:
        return

    # 没有wait_group的情况, 那就直接发了
    if not context.has_wait_group:
        context.on_bar_fun(context, [bar])
        return

    # wait_group = True, 但是股票不在waitgroup的列表里时, 直接发了.
    # 在调用完 on_bar_fun 后, 在把数据放入到bar_data_cache里
    barwaitgroupinfo = context.bar_waitgroup_frequency2Info.get(
        frequency, BarWaitgroupInfo(frequency, 0)
    )
    if not barwaitgroupinfo.is_symbol_in(symbol):
        # gmsdklogger.debug(
        #     "wait_group = True, 但是股票不在waitgroup的列表里时, 直接发了, symbol=%s, frequency=%s",
        #     symbol,
        #     frequency,
        # )
        context.on_bar_fun(context, [bar])
        context._add_bar2bar_data_cache(barnew)
        return

    eob = bar["eob"]  # type: datetime.datetime

    if context.mode == MODE_BACKTEST:  # 处理回测模式下, wait_group = True
        # 在回测模式下, 数据都是按顺序组织好的, 所以可以认为到下一个时间点时, 就把所有的数据统一放出来就好了
        if pre_eob_in_backtest is None:
            pre_eob_in_backtest = eob
            bars_in_waitgroup_backtest[frequency].append(bar)
            context._add_bar2bar_data_cache(barnew)
            return

        if pre_eob_in_backtest == eob:
            bars_in_waitgroup_backtest[frequency].append(bar)
            context._add_bar2bar_data_cache(barnew)
            return

        if pre_eob_in_backtest < eob:  # 说明是下一个时间点了
            for bs in six.itervalues(bars_in_waitgroup_backtest):
                context.on_bar_fun(context, bs)
            context._add_bar2bar_data_cache(barnew)

            pre_eob_in_backtest = eob
            bars_in_waitgroup_backtest.clear()
            bars_in_waitgroup_backtest[frequency].append(bar)
            return

        return

    if context.mode == MODE_LIVE:  # 处理实时模式下, wait_group = True
        if frequency not in bars_in_waitgroup_live:
            bars_in_waitgroup_live[frequency] = dict()

        # 以eob做为key值, bar做为value值. 二级dict
        # type: Dict[datetime.datetime, List[BarLikeDict2]]
        eob_bar_dict = bars_in_waitgroup_live[frequency]
        if eob not in eob_bar_dict:
            eob_bar_dict[eob] = [bar]
        else:
            eob_bar_dict[eob].append(bar)

        # 检查一下是否全部都到了. 到了的话触发一下
        if len(barwaitgroupinfo) == len(eob_bar_dict[eob]):
            gmsdklogger.debug("实时模式下, wait_group的bar都到齐了, 触发on_bar. eob=%s", eob)
            context._add_data_to_cache(symbol, frequency, barnew)
            context.on_bar_fun(context, eob_bar_dict[eob])
            del eob_bar_dict[eob]
        else:
            context._add_data_to_cache(symbol, frequency, barnew)

        return


def l2transaction_callback(data):
    if context.on_l2transaction_fun:
        trans = L2Transaction()
        trans.ParseFromString(data)
        trans = protobuf_to_dict(
            trans, including_default_value_fields=True, dcls=DictLikeL2Transaction
        )
        context.on_l2transaction_fun(context, trans)


def l2order_queue_callback(data):
    if context.on_l2order_queue_fun is not None:
        l2order_queue = L2OrderQueue()
        l2order_queue.ParseFromString(data)
        l2order_queue = protobuf_to_dict(
            l2order_queue,
            including_default_value_fields=True,
            dcls=DictLikeL2OrderQueue,
        )
        context.on_l2order_queue_fun(context, l2order_queue)


def l2order_callback(data):
    if context.on_l2order_fun is not None:
        l2order = L2Order()
        l2order.ParseFromString(data)
        l2order = protobuf_to_dict(
            l2order, including_default_value_fields=True, dcls=DictLikeL2Order
        )
        context.on_l2order_fun(context, l2order)


def schedule_callback(data):
    # python 3 传过来的是bytes 类型， 转成str
    if isinstance(data, bytes):
        data = bytes.decode(data)

    schedule_func = context.inside_schedules.get(data)
    if not schedule_func:
        return

    schedule_func(context)


def excerpt_callback(data):
    if context.on_execution_report_fun:
        excerpt = ExecRpt()
        excerpt.ParseFromString(data)
        excerpt = protobuf_to_dict(
            excerpt, including_default_value_fields=True, dcls=DictLikeExecRpt
        )
        context.on_execution_report_fun(context, excerpt)


def order_callback(data):
    if context.on_order_status_fun is None and context.on_order_status_mm_fun is None:
        return

    order = Order()
    order.ParseFromString(data)
    if (
        order.order_business == OrderBusiness_MARKET_MAKING
        and context.on_order_status_mm_fun
    ):
        orderMM = protobuf_to_dict(
            order, including_default_value_fields=True, dcls=DictLikeOrderMM
        )

        context.on_order_status_mm_fun(context, orderMM)
        return
    if context.on_order_status_fun:
        order = protobuf_to_dict(
            order, including_default_value_fields=True, dcls=DictLikeOrder
        )
        context.on_order_status_fun(context, order)
        return


def indicator_callback(data):
    if context.on_backtest_finished_fun:
        indicator = Indicator()
        indicator.ParseFromString(data)
        indicator = protobuf_to_dict(
            indicator, including_default_value_fields=True, dcls=DictLikeIndicator
        )
        context.on_backtest_finished_fun(context, indicator)


def cash_callback(data):
    cash = Cash()
    cash.ParseFromString(data)
    cash = protobuf_to_dict(cash, including_default_value_fields=True)
    account_id = cash["account_id"]
    accounts = context.accounts
    if accounts.get(account_id) is not None:
        accounts[account_id].cash = cash


def position_callback(data):
    position = Position()
    position.ParseFromString(data)
    position = protobuf_to_dict(position, including_default_value_fields=True)
    symbol = position["symbol"]
    side = position["side"]
    covered_flag = position["covered_flag"]
    account_id = position["account_id"]
    accounts = context.accounts
    position_key = (symbol, int(side), int(covered_flag))
    if accounts.get(account_id) is not None:
        accounts[account_id].inside_positions[position_key] = position

        if not position.get("volume"):
            if accounts[account_id].inside_positions.get(position_key):
                return accounts[account_id].inside_positions.pop(position_key)


def parameters_callback(data):
    if context.on_parameter_fun:
        parameters = Parameters()
        parameters.ParseFromString(data)
        parameters = [
            protobuf_to_dict(
                p, including_default_value_fields=True, dcls=DictLikeParameter
            )
            for p in parameters.parameters
        ]
        if len(parameters) > 0:
            context.on_parameter_fun(context, parameters[0])


def default_err_callback(ctx, code, info):
    # type: (Context, Text, Text) -> None
    if code in ("1201", "1200"):
        gmsdklogger.warning(
            "行情重连中..., error code=%s, info=%s. 可用on_error事件处理", code, info
        )
    else:
        gmsdklogger.warning(
            "发生错误, 调用默认的处理函数, error code=%s, info=%s.  你可以在策略里自定义on_error函数接管它. 类似于on_tick",
            code,
            info,
        )


def err_callback(data):
    """
    遇到错误时回调, 错误代码跟错误信息的对应关系参考: https://www.myquant.cn/docs/cpp/170
    """
    if context.on_error_fun is None:
        context.on_error_fun = default_err_callback

    try:
        data_unicode = data.decode("utf8")
        sparr = data_unicode.split("|", 1)
        if len(sparr) == 1:
            code, info = "code解析不出来", sparr[0]
        else:
            code, info = sparr
        context.on_error_fun(context, code, info)
    except Exception as e:
        gmsdklogger.exception("字符编码解析错误", e)
        context.on_error_fun(context, "1011", data)


# 已超时触发过的eob集合, 原则上是触发过的, 即可后面在收到数据也不再次触发
already_fire_timeout_eobs = set()  # type: Set[datetime.datetime]


def timer_callback(data):
    global bars_in_waitgroup_live, already_fire_timeout_eobs
    if (
        (context.on_bar_fun is not None)
        and context.has_wait_group
        and context.is_live_model()
    ):
        # 这里处理实时模式下wait_group=true时, on_bar超时触发
        # 比较逻辑是: 取本地时间, 然后跟相同的eob的bars里的第1个bar的 receive_local_time (接收到时的本地时间) 相比
        cur_now_s = time.time()
        must_del_keys = []
        for frequency, eob_tick_dict in six.iteritems(bars_in_waitgroup_live):
            barwaitgroupinfo = context.bar_waitgroup_frequency2Info.get(frequency, None)
            if barwaitgroupinfo is not None:
                timeout_seconds = barwaitgroupinfo.timeout_seconds
                for eob_time in list(six.iterkeys(eob_tick_dict)):
                    first_bar = eob_tick_dict[eob_time][0]  # 这个eob下的收到的第1个bar
                    delta_second = (
                        cur_now_s - first_bar["receive_local_time"]
                    )  # type: float
                    if delta_second >= timeout_seconds:
                        if eob_time in already_fire_timeout_eobs:
                            gmsdklogger.debug(
                                "frequency=%s eob=%s timeout_seconds=%d, 已超时触发过, 后面又收到数据, 不进行触发",
                                frequency,
                                eob_time,
                            )
                            del eob_tick_dict[eob_time]
                            continue

                        gmsdklogger.info(
                            "frequency=%s eob=%s timeout_seconds=%d 已超时了超时秒数=%s, 触发on_bar",
                            frequency,
                            eob_time,
                            timeout_seconds,
                            delta_second,
                        )
                        context.on_bar_fun(context, eob_tick_dict[eob_time])
                        del eob_tick_dict[eob_time]
                        already_fire_timeout_eobs.add(eob_time)
            else:
                # 说明有些 frequency 已经退订了
                gmsdklogger.debug("frequency =%s 已全部退订", frequency)
                must_del_keys.append(frequency)

        if must_del_keys:
            for k in must_del_keys:
                del bars_in_waitgroup_live[k]
        return


def backtest_finish_callback(data):
    global pre_eob_in_backtest, bars_in_waitgroup_backtest
    # 在回测结束前, 把之前累积的bar给放出来
    if bars_in_waitgroup_backtest:
        for bs in six.itervalues(bars_in_waitgroup_backtest):
            context.on_bar_fun(context, bs)

    pre_eob_in_backtest = None
    bars_in_waitgroup_backtest = collections.defaultdict(list)
    context._temporary_now = None
    context.bar_data_set.clear()  # 清空之前的
    context.max_tick_data_count = 1
    context.max_bar_data_count = 1


def stop_callback(data):
    if context.on_shutdown_fun is not None:
        context.on_shutdown_fun(context)

    from gm.api import stop

    print("!~~~~~~~~~~~!停止策略!~~~~~~~~~~~!")
    stop()


def trade_connected_callback():
    gmsdklogger.info("连接交易服务成功")

    # 当SDK连接远程的终端时如果跟终端意外断连, 这期间在终端操作的交易事件无法推送到本地,
    # 会造成本地数据与终端数据不一致的问题, 所以需要在每次重连交易服务时获取一遍完整的
    # 交易数据
    context._set_accounts()

    if context.on_trade_data_connected_fun is not None:
        context.on_trade_data_connected_fun(context)


def data_connected_callback(data):
    gmsdklogger.info("连接行情服务成功")
    if context.on_market_data_connected_fun is not None:
        context.message = data.decode("utf8")
        context.on_market_data_connected_fun(context)


def algo_order_status_callback(data):
    gmsdklogger.debug("母单状态变化回调")
    if context.on_algo_order_status_fun:
        algo_order = AlgoOrder()
        algo_order.ParseFromString(data)
        algo_order = protobuf_to_dict(
            algo_order, including_default_value_fields=True, dcls=DictLikeAlgoOrder
        )
        context.on_algo_order_status_fun(context, algo_order)


def account_status_callback(data):
    if context.on_account_status_fun:
        account_status = AccountStatus()
        account_status.ParseFromString(data)
        account_id = account_status.account_id

        account_status_dict = DictLikeAccountStatus()
        account_status_dict["account_id"] = account_id
        account_status_dict["account_name"] = account_status.account_name

        status_dict = DictLikeConnectionStatus()
        account_status_dict["status"] = status_dict
        if account_status.status is not None:
            status_dict["state"] = account_status.status.state
            error_dict = DictLikeError()
            status_dict["error"] = error_dict
            if account_status.status.error is not None:
                error_dict["code"] = account_status.status.error.code
                error_dict["type"] = account_status.status.error.type
                error_dict["info"] = account_status.status.error.info

        # 给context上的帐号修改状态值
        if account_status.status and account_id in context.inside_accounts:
            context.inside_accounts[account_id].status = status_dict
        context.on_account_status_fun(context, account_status_dict)


def data_disconnected_callback(data):
    if context.on_market_data_disconnected_fun is not None:
        context.message = data.decode("utf8")
        context.on_market_data_disconnected_fun(context)


def trade_disconnected_callback():
    if context.on_trade_data_disconnected_fun is not None:
        context.on_trade_data_disconnected_fun(context)


def user_timer_callback(data):
    # type: (bytes) -> None
    """定时器设置回调函数"""
    # data 值: b'time_id=10000'
    timer_id = int(re.sub(r"\D", "", str(data)))
    timer_func = context._timer_funcs.get(timer_id)
    if timer_func is not None:
        timer_func(context)

def customized_message_callback(data):
    # type: (bytes) -> None
    if context.on_customized_message_fun is None:
        return
    msg = CustomizedMessage()
    msg.ParseFromString(data)
    context.on_customized_message_fun(context, msg.msg_type, msg.msg_body)


def callback_controller(msg_type, data):
    """
    回调任务控制器
    """
    try:
        # python 3 传过来的是bytes 类型， 转成str
        if isinstance(msg_type, bytes):
            msg_type = bytes.decode(msg_type)

        if msg_type == CALLBACK_TYPE_TICK:
            return tick_callback_new(data)

        if msg_type == CALLBACK_TYPE_DEPTH:
            return depth_callback(data)

        if msg_type == CALLBACK_TYPE_BAR:
            return bar_callback_new(data)

        if msg_type == CALLBACK_TYPE_L2TRANSACTION:
            return l2transaction_callback(data)

        if msg_type == CALLBACK_TYPE_L2ORDER:
            return l2order_callback(data)

        if msg_type == CALLBACK_TYPE_L2ORDER_QUEUE:
            return l2order_queue_callback(data)

        if msg_type == CALLBACK_TYPE_INIT:
            return init_callback(data)

        if msg_type == CALLBACK_TYPE_SCHEDULE:
            return schedule_callback(data)

        if msg_type == CALLBACK_TYPE_ERROR:
            return err_callback(data)

        if msg_type == CALLBACK_TYPE_TIMER:
            return timer_callback(data)

        if msg_type == CALLBACK_TYPE_EXECRPT:
            return excerpt_callback(data)

        if msg_type == CALLBACK_TYPE_ORDER:
            return order_callback(data)

        if msg_type == CALLBACK_TYPE_INDICATOR:
            return indicator_callback(data)

        if msg_type == CALLBACK_TYPE_CASH:
            return cash_callback(data)

        if msg_type == CALLBACK_TYPE_POSITION:
            return position_callback(data)

        if msg_type == CALLBACK_TYPE_PARAMETERS:
            return parameters_callback(data)

        if msg_type == CALLBACK_TYPE_BACKTEST_FINISH:
            return backtest_finish_callback(data)

        if msg_type == CALLBACK_TYPE_STOP:
            return stop_callback(data)

        if msg_type == CALLBACK_TYPE_TRADE_CONNECTED:
            return trade_connected_callback()

        if msg_type == CALLBACK_TYPE_TRADE_DISCONNECTED:
            return trade_disconnected_callback()

        if msg_type == CALLBACK_TYPE_DATA_CONNECTED:
            return data_connected_callback(data)

        if msg_type == CALLBACK_TYPE_DATA_DISCONNECTED:
            return data_disconnected_callback(data)

        if msg_type == CALLBACK_TYPE_ACCOUNTSTATUS:
            return account_status_callback(data)

        if msg_type == CALLBACK_TYPE_ALGOORDER:
            return algo_order_status_callback(data)

        if msg_type == CALLBACK_TYPE_USER_TIMER:
            return user_timer_callback(data)

        if msg_type == CALLBACK_TYPE_CUSTOMIZED_MESSAGE:
            return customized_message_callback(data)

        gmsdklogger.warn("没有处理消息:%s的处理函数", msg_type)

    except SystemExit:
        gmsdklogger.debug("^^--------------SystemExit--------------^^")
        from gm.api import stop

        stop()

    except BaseException as e:
        gmsdklogger.exception("^^--------------遇到exception--------------^^")
        from gm.api import stop

        stop()
