# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import os
import signal
import sys
from importlib import import_module
from optparse import OptionParser
from gm.utils import round_float

import six
from typing import Text, List, Dict, Any, Callable

from gm.__version__ import __version__
from gm.callback import callback_controller
from gm.constant import DATA_TYPE_TICK, SCHEDULE_INFO, DATA_TYPE_L2TRANSACTION, DATA_TYPE_DEPTH
from gm.csdk.c_sdk import (
    py_gmi_current, py_gmi_current_price, py_gmi_schedule, py_gmi_set_data_callback, py_gmi_set_strategy_id,
    gmi_set_mode, py_gmi_set_backtest_config, py_gmi_subscribe, py_gmi_set_token,
    py_gmi_get_encrypted_token, py_gmi_get_orgcode, py_gmi_unsubscribe, py_gmi_get_parameters,
    py_gmi_add_parameters, py_gmi_set_parameters, py_gmi_log, py_gmi_strerror, py_gmi_run,
    py_gmi_set_serv_addr, gmi_init, gmi_poll, gmi_get_c_version, py_gmi_set_apitoken,
    py_gmi_set_mfp, py_gmi_user_timer, py_gmi_user_timer_stop,
    py_gmi_set_serv_addr_v5, py_gmi_set_account_id, py_gmi_set_max_wait_time,
    py_gmi_set_backtest_threadnum, py_gmi_get_stop_error_code, py_gmi_set_ctp_md_info,
)
from gm.enum import MODE_UNKNOWN, ADJUST_NONE, MODE_BACKTEST, MODE_LIVE, ADJUST_POST, ADJUST_PREV
from gm.model.storage import Context, context, BarSubInfo, BarWaitgroupInfo
from gm.pb.common_pb2 import Logs, Log
from gm.pb.data_pb2 import Ticks
from gm.pb.rtconf_pb2 import Parameters, Parameter
from gm.pb.rtconf_service_pb2 import GetParametersReq
from gm.pb_to_dict import protobuf_to_dict
from gm.utils import load_to_list, load_to_second, adjust_frequency, GmSymbols, gmsdklogger, convert
from gm.api._errors import check_gm_status, GmError
from gm.pb.separate_bandwidth_service_pb2 import (
    LatestPriceReq,
    LatestPriceRsp
)

running = True


def _unsubscribe_all():
    context.bar_sub_infos.clear()
    context.tick_sub_symbols.clear()
    context.bar_waitgroup_frequency2Info.clear()
    context.max_tick_data_count = 1
    context.max_bar_data_count = 1


def _py_gmi_unsubscribe_all():
    """退订所有行情"""
    # print("~~~~~~~~~~~~~~~~~~~~退订所有行情~~~~~~~~~~~~~~~~~~~~")
    # 退订 tick
    for symbol in context.tick_sub_symbols:
        status = py_gmi_unsubscribe(symbol, "tick")
        check_gm_status(status)
    # 退订 bar
    for sub_info in context.bar_sub_infos:
        status = py_gmi_unsubscribe(sub_info.symbol, sub_info.frequency)
        check_gm_status(status)
    _unsubscribe_all()


def _handle_signal(signalnum, frame):
    """处理退出信号, 在推出前先退订所有行情"""
    _py_gmi_unsubscribe_all()
    # running 值设置为 False, 退出循环
    frame.f_globals["running"] = False
    sys.exit(2)


def _register_signal():
    signal.signal(signal.SIGABRT, _handle_signal)
    # signal.signal(signal.SIGEMT, _handle_signal)
    signal.signal(signal.SIGFPE, _handle_signal)
    signal.signal(signal.SIGILL, _handle_signal)
    # signal.signal(signal.SIGINFO, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGSEGV, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)


def _handle_exception(exc_type, exc_value, exc_traceback):
    """处理全局异常, 在程序退出前退订所有行情"""
    _py_gmi_unsubscribe_all()
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def _register_excepthook():
    sys.excepthook = _handle_exception


def set_token(token):
    # type: (Text) -> None
    """
    设置用户的token, 用于身份认证
    """
    py_gmi_set_token(token)
    context.token = str('bearer {}'.format(token))


def get_encrypted_token():
    '''
    获取密文token
    '''
    encrypted_token = py_gmi_get_encrypted_token()
    if isinstance(encrypted_token, bytes):
        return str('bearer '+encrypted_token.decode("utf-8"))
    return str('bearer {}'.format(encrypted_token))


def get_orgcode():
    orgcode = py_gmi_get_orgcode()
    if isinstance(orgcode, bytes):
        return orgcode.decode("utf-8")
    return orgcode


def get_version():
    # type: () ->Text
    return __version__


def subscribe(symbols, frequency=None, count=1, wait_group=False, wait_group_timeout='10s', unsubscribe_previous=False, fields=None, format="df"):
    # type: (GmSymbols, Text, int, bool, Text, bool, str, str) -> None
    """
    订阅行情, 可以指定symbol,  数据滑窗大小, 以及是否需要等待全部代码的数据到齐再触发事件。
    wait_group: 是否等待全部相同频度订阅的symbol到齐再触发on_bar事件。
    一个 frequency, 只能有一个 wait_group_timeout 也就是说如果后面调用该函数时, 相同的frequency, 但是 wait_group_timeout 不同,
    则 wait_group_timeout 被忽略.
    同时要注意, 一个symbol与frequency组合, 只能有一种wait_group, 即wait_group要么为true, 要么为false
    """
    if format not in ["df", "row", "col"]:
            raise GmError(1027, "format 只能填df,row,col", "subscribe")
    if frequency == "tick" and format != "col":
        all_fields = ["symbol","open","high","low","price","quotes","cum_volume","cum_amount","cum_position","last_amount","last_volume","trade_type","flag","created_at","iopv","receive_local_time"]
    elif frequency == "tick" and format == "col":
        all_fields = ["symbol","open","high","low","price","cum_volume","cum_amount","cum_position","last_amount","last_volume","created_at","iopv","bid_p","bid_v","ask_p","ask_v"]
    elif format == "col":
        all_fields = ["symbol","frequency","open","high","low","close","volume","amount","position","bob","eob"]
    else:
        all_fields = ["symbol","frequency","open","high","low","close","volume","amount","position","bob","eob","pre_close"]
    if not fields:
        _fields = all_fields
    elif isinstance(fields, str):
        _fields  = []
        for field in fields.split(","):
            field = field.strip()
            if field not in all_fields:
                raise GmError(1027, f"无效fields值: {field}", "subscribe")
            _fields.append(field)
    elif isinstance(fields, list):
        _fields  = []
        for field in fields:
            field = field.strip()
            if field not in all_fields:
                raise GmError(1027, f"无效fields值: {field}", "subscribe")
            _fields.append(field)
    else:
        raise GmError(1027, "fields 类型错误, 只能填逗号分隔的字符串或列表", "subscribe")

    symbols = load_to_list(symbols)
    for symbol in symbols:
        if symbol.startswith("NEEQ") and frequency is None:
            raise GmError(1027, "exchange为NEEQ时的订阅频率frequency必填", "subscribe")
    if frequency is None:
        frequency = "1d"
    frequency = adjust_frequency(frequency)

    symbols_str = ','.join(symbols)
    status = py_gmi_subscribe(symbols_str, frequency, unsubscribe_previous)
    check_gm_status(status)

    if unsubscribe_previous:
        _unsubscribe_all()

    if frequency == DATA_TYPE_TICK:
        if context.max_tick_data_count < count:
            context.max_tick_data_count = count
        for sy in symbols:
            context._init_cache(sy, frequency, format, _fields, count)
            context.tick_sub_symbols.add(sy)
        return

    if frequency == DATA_TYPE_DEPTH:
        return

    if frequency == DATA_TYPE_L2TRANSACTION:
        return

    # 处理订阅bar的情况
    context._set_onbar_waitgroup_timeout_check()
    wait_group_timeoutint = load_to_second(wait_group_timeout)
    if context.max_bar_data_count < count:
        context.max_bar_data_count = count
    for sy in symbols:
        context._init_cache(sy, frequency, format, _fields, count)
        barsubinfo = BarSubInfo(sy, frequency)
        if barsubinfo not in context.bar_sub_infos:
            context.bar_sub_infos.add(barsubinfo)
            if wait_group:
                if frequency not in context.bar_waitgroup_frequency2Info:
                    context.bar_waitgroup_frequency2Info[frequency] = BarWaitgroupInfo(
                        frequency, wait_group_timeoutint)
                context.bar_waitgroup_frequency2Info[frequency].add_one_symbol(
                    sy)
        else:
            gmsdklogger.debug("symbol=%s frequency=%s 已订阅过", sy, frequency)
            continue


def unsubscribe(symbols, frequency='1d'):
    # type: (GmSymbols, Text) -> None
    """
    unsubscribe - 取消行情订阅

    取消行情订阅, 默认取消所有已订阅行情
    """
    symbols = load_to_list(symbols)
    symbols_str = ','.join(symbols)
    frequency = adjust_frequency(frequency)

    status = py_gmi_unsubscribe(symbols_str, frequency)
    check_gm_status(status)

    if symbols_str == '*':
        _unsubscribe_all()
        return

    if frequency == "L2Transaction".lower():
        return

    if frequency == DATA_TYPE_TICK:
        for sy in symbols:
            if context._has_cache(sy, frequency):
                context.tick_sub_symbols.remove(sy)
            context._rm_cache(sy, frequency)
        return

    if frequency == DATA_TYPE_DEPTH:
        return

    # 处理bar的退订
    for sy in symbols:
        if context._has_cache(sy, frequency):
            context.bar_sub_infos.remove(BarSubInfo(sy, frequency))
            barwaitgroupinfo = context.bar_waitgroup_frequency2Info.get(
                frequency, None)
            if barwaitgroupinfo:
                barwaitgroupinfo.remove_one_symbol(sy)
        context._rm_cache(sy, frequency)

    # 处理已全部退订的 frequency
    for frequency in list(six.iterkeys(context.bar_waitgroup_frequency2Info)):
        if len(context.bar_waitgroup_frequency2Info[frequency]) == 0:
            gmsdklogger.debug('frequency=%s 已全部取消订阅', frequency)
            del context.bar_waitgroup_frequency2Info[frequency]


def current(symbols, fields='', include_call_auction=False):
    # type: (GmSymbols, Text, bool) -> List[Any]
    """
    查询当前行情快照, 返回tick数据
    """
    symbols = load_to_list(symbols)
    fields = load_to_list(fields)

    symbols_str = ','.join(symbols)
    fields_str = ','.join(fields)

    status, data = py_gmi_current(symbols_str, fields_str, include_call_auction)
    check_gm_status(status)

    ticks = Ticks()
    ticks.ParseFromString(data)
    # ticks = [protobuf_to_dict(tick, including_default_value_fields=False) for tick in ticks.data]
    ticksdata = []
    for tick in ticks.data:
        tick = protobuf_to_dict(tick, including_default_value_fields=True)
        quotes = tick.get('quotes')
        if quotes is not None:
            for item in quotes:
                for k in ['ask_p', 'ask_v', 'bid_p', 'bid_v']:
                    # 以 _p 结尾的都是浮点型。如果没有值的时候, 默认值赋值为0
                    item[k] = item.get(k, 0.0 if k.endswith('_p') else 0)
        ticksdata.append(tick)
    ticks = ticksdata

    if not fields:
        return ticks

    result = []
    for tick in ticks:
        tick_dict = {}
        for field in fields:
            if field in tick:
                tick_dict[field] = tick[field]
        result.append(tick_dict)
    return result

def current_price(symbols):
    # type: (str|list[str]) -> List[Any]
    """
    查询当前行情快照, 返回tick数据
    """
    symbols = load_to_list(symbols)
    req = LatestPriceReq(
        symbols=symbols
    )

    req = req.SerializeToString()
    status, result = py_gmi_current_price(req)
    check_gm_status(status)

    rsp = LatestPriceRsp()
    rsp.ParseFromString(result)

    result = protobuf_to_dict(rsp)
    data = result.get("data", [])  # type: List[Dict[str, Any]]
    for v in data:
        last_price = v.get('last_price')
        if last_price is not None:
            v['price'] = round_float(last_price)
            del v['last_price']
    return data

def get_strerror(error_code):
    # type: (int) -> Text
    e = py_gmi_strerror(error_code)
    if sys.version >= '3':
        # Python3及以上版本, 需要专门处理一下, 否则会返回字符串类似: b'\xe6\x97\xa0\xe6\xb3\x95\xe8\x8e\xb7\xe5\x8f\x96\xe6\x8e\x98\xe9\x87\x91\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x99\xa8\xe5\x9c\xb0\xe5\x9d\x80\xe5\x88\x97\xe8\xa1\xa8'
        e = str(e, encoding='utf-8')
    return e


def schedule(schedule_func, date_rule, time_rule):
    # type: (Any, Text, Text) -> None
    """
    定时任务. 这里的schedule_func 要求只能有一个context参数的函数
    """
    schemdule_info = SCHEDULE_INFO.format(
        date_rule=date_rule, time_rule=time_rule)
    context.inside_schedules[schemdule_info] = schedule_func
    status = py_gmi_schedule(date_rule, time_rule)
    check_gm_status(status)

def run(strategy_id='', filename='', mode=MODE_UNKNOWN, token='',
        backtest_start_time='',
        backtest_end_time='',
        backtest_initial_cash=1000000,
        backtest_transaction_ratio=1,
        backtest_commission_ratio=0,
        backtest_commission_unit=0,
        backtest_slippage_ratio=0,
        backtest_marginfloat_ratio1=0.2,
        backtest_marginfloat_ratio2=0.4,
        backtest_adjust=ADJUST_NONE,
        backtest_check_cache=1,
        serv_addr='',
        backtest_match_mode=0,
        ):
    # type: (Text, Text, int, Text, Text, Text, float, float, float, float, float, float, float, int, int, Text, int) -> None
    """
    执行策略
    """

    parser = OptionParser()
    parser.add_option("--strategy_id", action="store",
                      dest="strategy_id",
                      default=strategy_id,
                      help="策略id")

    parser.add_option("--filename", action="store",
                      dest="filename",
                      default=filename,
                      help="策略文件名称")

    parser.add_option("--mode", action="store",
                      dest="mode",
                      default=mode,
                      help="策略模式选择")

    parser.add_option("--token", action="store",
                      dest="token",
                      default=token,
                      help="用户token")

    parser.add_option("--apitoken", action="store",
                      dest="apitoken",
                      default='',
                      help="用户token")

    parser.add_option("--backtest_start_time", action="store",
                      dest="backtest_start_time",
                      default=backtest_start_time,
                      help="回测开始时间")

    parser.add_option("--backtest_end_time", action="store",
                      dest="backtest_end_time",
                      default=backtest_end_time,
                      help="回测结束时间")

    parser.add_option("--backtest_initial_cash", action="store",
                      dest="backtest_initial_cash",
                      default=backtest_initial_cash,
                      help="回测初始资金")

    parser.add_option("--backtest_transaction_ratio", action="store",
                      dest="backtest_transaction_ratio",
                      default=backtest_transaction_ratio,
                      help="回测成交比例")

    parser.add_option("--backtest_commission_ratio", action="store",
                      dest="backtest_commission_ratio",
                      default=backtest_commission_ratio,
                      help="回测佣金比例")

    parser.add_option("--backtest_commission_unit", action="store",
                      dest="backtest_commission_unit",
                      default=backtest_commission_unit,
                      help="回测单位佣金(元)")

    parser.add_option("--backtest_slippage_ratio", action="store",
                      dest="backtest_slippage_ratio",
                      default=backtest_slippage_ratio,
                      help="回测滑点费率")

    parser.add_option("--backtest_marginfloat_ratio1", action="store",
                      dest="backtest_marginfloat_ratio1",
                      default=backtest_marginfloat_ratio1,
                      help="回测保证金上浮比例1(距到期日>2天)")

    parser.add_option("--backtest_marginfloat_ratio2", action="store",
                      dest="backtest_marginfloat_ratio2",
                      default=backtest_marginfloat_ratio2,
                      help="回测保证金上浮比例2(距到期日<=2天)")

    parser.add_option("--backtest_adjust", action="store",
                      dest="backtest_adjust",
                      default=backtest_adjust,
                      help="回测复权模式")

    parser.add_option("--backtest_check_cache", action="store",
                      dest="backtest_check_cache",
                      default=backtest_check_cache,
                      help="回测是否使用缓存")

    parser.add_option("--serv_addr", action="store",
                      dest="serv_addr",
                      default=serv_addr,
                      help="终端地址")

    parser.add_option("--backtest_match_mode", action="store",
                      dest="backtest_match_mode",
                      default=backtest_match_mode,
                      help="回测撮合模式")

    (options, args) = parser.parse_args()
    strategy_id = options.strategy_id
    filename = options.filename
    mode = convert(options.mode, int, mode)
    if mode not in (MODE_UNKNOWN, MODE_LIVE, MODE_BACKTEST):
        raise ValueError('模式只能设置成 MODE_UNKNOWN, MODE_LIVE, MODE_BACKTEST 值')

    token = options.token
    apitoken = options.apitoken
    backtest_start_time = options.backtest_start_time
    backtest_end_time = options.backtest_end_time
    backtest_initial_cash = convert(
        options.backtest_initial_cash, float, backtest_initial_cash)
    backtest_transaction_ratio = convert(
        options.backtest_transaction_ratio, float, backtest_transaction_ratio)
    backtest_commission_ratio = convert(
        options.backtest_commission_ratio, float, backtest_commission_ratio)
    backtest_commission_unit = convert(
        options.backtest_commission_unit, float, backtest_commission_unit)
    backtest_slippage_ratio = convert(
        options.backtest_slippage_ratio, float, backtest_slippage_ratio)
    backtest_marginfloat_ratio1 = convert(
        options.backtest_marginfloat_ratio1, float, backtest_marginfloat_ratio1)
    backtest_marginfloat_ratio2 = convert(
        options.backtest_marginfloat_ratio2, float, backtest_marginfloat_ratio2)

    backtest_adjust = convert(options.backtest_adjust, int, backtest_adjust)
    if backtest_adjust == 3:
        backtest_adjust = ADJUST_NONE  # 这个修改是为了适合终端之前把 3 认为是 不复权
    if backtest_adjust not in (ADJUST_NONE, ADJUST_POST, ADJUST_PREV):
        raise ValueError('回测复权模式只能设置成 ADJUST_NONE, ADJUST_POST, ADJUST_PREV 值')

    if backtest_initial_cash < 1:
        raise ValueError(
            '回测初始资金不能设置为小于1, 当前值为:{}'.format(backtest_initial_cash))

    if not 0 <= backtest_transaction_ratio <= 1:
        raise ValueError('回测成交比例允许的范围值为 0<=x<=1, 当前值为{}'.format(
            backtest_transaction_ratio))

    if not 0 <= backtest_commission_ratio <= 0.1:
        raise ValueError('回测佣金比例允许的范围值为 0<=x<=0.1, 当前值为{}'.format(
            backtest_commission_ratio))

    if not 0 <= backtest_slippage_ratio <= 0.1:
        raise ValueError('回测滑点比例允许的范围值为 0<=x<=0.1, 当前值为{}'.format(
            backtest_slippage_ratio))

    backtest_check_cache = convert(
        options.backtest_check_cache, int, backtest_check_cache)
    serv_addr = options.serv_addr
    backtest_match_mode = convert(
        options.backtest_match_mode, int, backtest_match_mode)

    from gm import api

    # 处理用户传入 __file__这个特殊变量的情况
    syspathes = set(s.replace('\\', '/') for s in sys.path)
    commonpaths = [os.path.commonprefix([p, filename]) for p in syspathes]
    commonpaths.sort(key=lambda s: len(s), reverse=True)
    maxcommonpath = commonpaths[0]
    filename = filename.replace(maxcommonpath, '')  # type: str
    if filename.startswith('/'):
        filename = filename[1:]

    if filename.endswith(".py"):
        filename = filename[:-3]
    filename = filename.replace("/", ".")
    filename = filename.replace('\\', ".")
    fmodule = import_module(filename)

    # 把gm.api里的所有的符号都导出到当前策略文件(fmodule)的命令空间, 方便使用
    for name in api.__all__:
        if name not in fmodule.__dict__:
            fmodule.__dict__[name] = getattr(api, name)

    # 服务地址设置
    if serv_addr:
        set_serv_addr(serv_addr)

    set_token(token)
    py_gmi_set_apitoken(apitoken)

    py_gmi_set_strategy_id(strategy_id)
    gmi_set_mode(mode)
    context.mode = mode
    context.strategy_id = strategy_id

    # 调用户文件的init
    context.inside_file_module = fmodule
    context.on_tick_fun = getattr(fmodule, 'on_tick', None)
    context.on_depth_fun = getattr(fmodule, 'on_depth', None)
    context.on_order_status_mm_fun = getattr(fmodule, 'on_order_status_mm', None)
    context.on_bar_fun = getattr(fmodule, 'on_bar', None)
    context.on_l2transaction_fun = getattr(fmodule, 'on_l2transaction', None)
    context.on_l2order_fun = getattr(fmodule, 'on_l2order', None)
    context.on_l2order_queue_fun = getattr(fmodule, 'on_l2order_queue', None)
    context.init_fun = getattr(fmodule, 'init', None)
    context.on_execution_report_fun = getattr(
        fmodule, 'on_execution_report', None)
    context.on_order_status_fun = getattr(fmodule, 'on_order_status', None)
    context.on_algo_order_status_fun = getattr(
        fmodule, 'on_algo_order_status', None)
    context.on_backtest_finished_fun = getattr(
        fmodule, 'on_backtest_finished', None)
    context.on_parameter_fun = getattr(fmodule, 'on_parameter', None)
    context.on_error_fun = getattr(fmodule, 'on_error', None)
    context.on_shutdown_fun = getattr(fmodule, 'on_shutdown', None)
    context.on_trade_data_connected_fun = getattr(
        fmodule, 'on_trade_data_connected', None)
    context.on_market_data_connected_fun = getattr(
        fmodule, 'on_market_data_connected', None)
    context.on_account_status_fun = getattr(fmodule, 'on_account_status', None)
    context.on_market_data_disconnected_fun = getattr(
        fmodule, 'on_market_data_disconnected', None)
    context.on_trade_data_disconnected_fun = getattr(
        fmodule, 'on_trade_data_disconnected', None)
    context.on_customized_message_fun = getattr(
        fmodule, 'on_customized_message', None)

    context.backtest_start_time = backtest_start_time
    context.backtest_end_time = backtest_end_time
    context.adjust_mode = backtest_adjust
    py_gmi_set_data_callback(callback_controller)  # 设置事件处理的回调函数

    splash_msgs = [
        '-' * 40,
        'python sdk version: {}'.format(__version__),
        'c sdk version: {}'.format(gmi_get_c_version().decode('utf8')),
        '-' * 40,
    ]

    print(os.linesep.join(splash_msgs))

    if mode == MODE_BACKTEST:
        py_gmi_set_backtest_config(start_time=backtest_start_time,
                                   end_time=backtest_end_time,
                                   initial_cash=backtest_initial_cash,
                                   transaction_ratio=backtest_transaction_ratio,
                                   commission_ratio=backtest_commission_ratio,
                                   commission_unit=backtest_commission_unit,
                                   slippage_ratio=backtest_slippage_ratio,
                                   option_float_margin_ratio1=backtest_marginfloat_ratio1,
                                   option_float_margin_ratio2=backtest_marginfloat_ratio2,
                                   adjust=backtest_adjust,
                                   match_mode=backtest_match_mode,
                                   check_cache=backtest_check_cache,
                                   )

        status = py_gmi_run()
        check_gm_status(status)
        return status

    status = gmi_init()
    check_gm_status(status)

    context._set_accounts()

    _register_signal()
    _register_excepthook()

    while running:
        gmi_poll()

    status = py_gmi_get_stop_error_code()
    check_gm_status(status)
    return status


def get_parameters():
    # type: () ->List[Dict[Text, Any]]
    req = GetParametersReq()
    req.owner_id = context.strategy_id
    req = req.SerializeToString()
    status, result = py_gmi_get_parameters(req)
    check_gm_status(status)

    req = Parameters()
    req.ParseFromString(result)

    return [protobuf_to_dict(parameters) for parameters in req.parameters]


def add_parameter(key, value, min=0, max=0, name='', intro='', group='', readonly=False):
    # type: (Text, float, float, float, Text, Text, Text, bool) -> None
    req = Parameters()
    req.owner_id = context.strategy_id
    p = req.parameters.add()  # type: Parameter
    p.key = key
    p.value = value
    p.min = min
    p.max = max
    p.name = name
    p.intro = intro
    p.group = group
    p.readonly = readonly
    req = req.SerializeToString()
    status = py_gmi_add_parameters(req)
    check_gm_status(status)


def set_parameter(key, value, min=0, max=0, name='', intro='', group='', readonly=False):
    # type: (Text, float, float, float, Text, Text, Text, bool) -> None
    req = Parameters()
    req.owner_id = context.strategy_id
    p = req.parameters.add()  # type: Parameter
    p.key = key
    p.value = value
    p.min = min
    p.max = max
    p.name = name
    p.intro = intro
    p.group = group
    p.readonly = readonly
    req = req.SerializeToString()
    status = py_gmi_set_parameters(req)
    check_gm_status(status)


def log(level, msg, source):
    # type: (Text, Text, Text) -> None
    logs = Logs()
    item = logs.data.add()  # type: Log
    item.owner_id = context.strategy_id
    item.source = source
    item.level = level
    item.msg = msg

    req = logs.SerializeToString()
    status = py_gmi_log(req)
    check_gm_status(status)


def stop():
    """
    停止策略的运行,用exit(2)退出
    """
    _py_gmi_unsubscribe_all()

    global running
    running = False
    sys.exit(2)


def set_serv_addr(addr):
    # type: (Text) -> None
    """
    设置终端服务地址
    """
    py_gmi_set_serv_addr(addr)


def set_mfp(mfp):
    # type: (Text) -> None
    """
    根据合规要求, 设置相关mfp信息。mfp信息, 键值使用key=value的形式拼接。多个键值对之间用竖线(“|”)分隔。
    如 "cpu=xxxx|fdsn=yyyyy|..."。

    信息项如下:

    CPU   string  // CPU 信息

    FDSN  string // Hard Disk Serieal Number (compatible old spec)

    HD    string // Hard Disk

    LIP   string // Lan IP

    IIP   string // 互联网IP

    IPORT string // 互联网PORT

    MAC   string // mac 地址

    OSV   string // Operating System Version

    PCN   string // Personal Computer Name

    PI    string // Partition Information, 磁盘分区信息

    VER   string // 客户端版本信息

    UUID  string // uuid
    """
    py_gmi_set_mfp(mfp)


def timer(timer_func, period, start_delay):
    # type: (Callable[[Context], None], int, int) -> Dict[Text, int]
    """
    定时器设置 (只在实时模式生效, 回测模式不起作用!)\n
    params:\n
    \t timer_func:      在timer设置的时间到达时触发的事件函数\n
    \t period:          定时事件间隔秒数(毫秒), 设定每隔多少秒触发一次定时器, 范围在[1,43200]\n
    \t start_delay:     等待秒数(毫秒), 设定多少秒后启动定时器, 范围在[0,43200]\n
    return: dict\n
    \t timer_id:        设定好的定时器id
    \t status:          定时器设置是否成功, 成功=0, 失败=非0错误码。
    """
    timer_id = py_gmi_user_timer(period, start_delay)
    # timer_id 小于 10000 时定时器设置失败, 返回的是错误码
    if timer_id < 10000:
        return dict(timer_id=0, status=timer_id)
    else:
        context._timer_funcs[timer_id] = timer_func
        return dict(timer_id=timer_id, status=0)


def timer_stop(timer_id):
    # type: (int) -> bool
    """
    定时器停止 \n
    params:\n
    \t timer_id:        要停止的定时器id
    return: \n
    \t is_stop:         是否成功停止, True or False
    """
    if timer_id in context._timer_funcs:
        # 调用C接口停止产生定时器事件
        py_gmi_user_timer_stop(timer_id)
        # 删除注册的定时器函数
        context._timer_funcs.pop(timer_id)
        return True
    else:
        # 未注册的定时器id则无法停止, 返回 False
        return False


def set_serv_addr_v5(addr, orgcode, site_id):
    # type: (str, str, str) -> None
    """自定义服务地址V5版"""
    py_gmi_set_serv_addr_v5(
        addr.encode('utf-8'),
        orgcode.encode('utf-8'),
        site_id.encode('utf-8'),
    )


def set_account_id(account_id):
    # type: (str) -> None
    """预设账号"""
    py_gmi_set_account_id(account_id.encode('utf-8'))


def set_option(max_wait_time=3600000, backtest_thread_num=1, ctp_md_info={}):
    # type: (int, int, {}) -> None
    """
    设置策略运行系统选项

    参数
    ----
    max_wait_time: api调用触发流控(超出单位时间调用次数)时, 允许系统冷却的最大等待时间(单位: 毫秒).
        若系统冷却需要时间>设定的最大等待时间, api调用失败, 返回流控错误, 需要策略自行处理(如捕获错误提示
        后等待对应时间). 默认`max_wait_time=3600000`, 即最大`3600000`毫秒, 可设范围`[0,3600000]`.
    backtest_thread_num: 回测运行的最大线程个数. 默认`backtest_thread_num=1`, 即回测运行最多使
        用1个线程, 可设范围`[1,32]`.
    ctp_md_info： ctp行情参数, 如：
    {
        'addr': '',
        'user_name': '',
        'password': ''
    }
    返回值
    ------
    None

    注意
    ----
    1. 设置 `max_wait_time`, 在回测模式/实时模式均可生效, 与 `run()` 中设定的策略模式mode一致
    2. 设置 `backtest_thread_num`, 只对回测模式生效

    参考文档
    --------


    示例
    ----

    >>> set_option(max_wait_time=3000)
    >>> set_option(backtest_thread_num=4)
    >>> set_option(ctp_md_info={
        'addr':'',
        'user_name':'',
        'password':'',
        })
    >>> set_option(max_wait_time=3000, backtest_thread_num=4)
    """
    py_gmi_set_max_wait_time(max_wait_time)
    py_gmi_set_backtest_threadnum(backtest_thread_num)
    py_gmi_set_ctp_md_info(ctp_md_info.get('addr', ''), ctp_md_info.get('user_name', ''), ctp_md_info.get('password', ''))
