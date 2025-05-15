from typing import Text, List, Dict, Any, Union

from gm.csdk.c_sdk import (
    py_gmi_place_order,
    py_gmi_get_unfinished_orders,
    py_gmi_get_orders,
    py_gmi_cancel_all_orders,
    py_gmi_close_all_positions,
    py_gmi_cancel_order,
    py_gmi_get_execution_reports,
    c_status_fail,
    py_gmi_place_algo_orders,
    py_gmi_algo_order_batch,
    py_gmi_cancel_algo_orders,
    py_gmi_pause_algo_orders,
    py_gmi_get_algo_orders,
    py_gmi_get_child_orders,
    py_gmi_smart_reorder,
    py_gmi_smart_reorder_cancel,
    py_gmi_get_entrustable_volume_by_symbol_pb,
)
from gm.enum import (
    OrderBusiness_MARKET_MAKING,
    OrderQualifier_Unknown,
    OrderDuration_Unknown,
    OrderSide_Buy,
    OrderSide_Sell,
    OrderType_Limit,
    OrderType_Market,
)

from gm.enum import (
    OrderTriggerType_Unknown,
    OrderTriggerType_LastPriceGreaterThanStopPrice,
    OrderTriggerType_LastPriceGreaterEqualStopPrice,
    OrderTriggerType_LastPriceLessThanStopPrice,
    OrderTriggerType_LastPriceLessEqualStopPrice,
    OrderTriggerType_AskPriceGreaterThanStopPrice,
    OrderTriggerType_AskPriceGreaterEqualStopPrice,
    OrderTriggerType_AskPriceLessThanStopPrice,
    OrderTriggerType_AskPriceLessEqualStopPrice,
    OrderTriggerType_BidPriceGreaterThanStopPrice,
    OrderTriggerType_BidPriceGreaterEqualStopPrice,
    OrderTriggerType_BidPriceLessThanStopPrice,
    OrderTriggerType_BidPriceLessEqualStopPrice,
)

from gm.model import DictLikeOrder, DictLikeOrderMM
from gm.model.storage import context
from gm.pb.account_pb2 import (
    Order,
    OrderBusiness_OPTION_BUY_OPEN,
    OrderBusiness_OPTION_COVERED_BUY_CLOSE,
    OrderBusiness_OPTION_COVERED_SELL_OPEN,
    OrderBusiness_OPTION_EXERCISE,
    OrderBusiness_OPTION_SELL_OPEN,
    Orders,
    OrderStyle_Volume,
    OrderStyle_Value,
    OrderStyle_Percent,
    OrderStyle_TargetVolume,
    OrderStyle_TargetValue,
    OrderStyle_TargetPercent,
    ExecRpts,
    AlgoOrder,
    AlgoOrders,
)
from gm.pb.algo_service_pb2 import GetAlgoOrdersReq
from gm.pb.trade_pb2 import (
    GetUnfinishedOrdersReq,
    GetOrdersReq,
    CancelAllOrdersReq,
    CloseAllPositionsReq,
    GetExecrptsReq,
)
from gm.pb.trade_query_service_pb2 import (
    GetEntrustableVolumeBySymbolReq,
    GetEntrustableVolumeBySymbolRsp,
)
from gm.pb_to_dict import protobuf_to_dict
from gm.utils import load_to_list, datetime2timestamp, gmsdklogger
from gm.api import stop
import time
from gm.api._errors import check_gm_status, send_custom_error


def _inner_place_order(o):
    # type: (Order) ->List[Dict[Text, Any]]
    """
    下单并返回order的信息. 同步调用, 在下单返回的order 的 client_order_id 将会有值.
    下单出错的话, 返回空的list
    """
    # 在回测模式且wait_group=True时, 设置这个created_at, 也就是通知c底层要根据这个时间设置price
    if context.is_backtest_model() and context.has_wait_group:
        o.created_at.seconds = datetime2timestamp(context.now)

    orders = Orders()
    orders.data.extend([o])

    req = orders.SerializeToString()
    status, result = py_gmi_place_order(req)
    check_gm_status(status)

    res = Orders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(
            res_order, including_default_value_fields=True, dcls=DictLikeOrder
        )
        for res_order in res.data
    ]


def order_volume(
    symbol,
    volume,
    side,
    order_type,
    position_effect,
    price=0,
    trigger_type=0,
    stop_price=0,
    order_duration=OrderDuration_Unknown,
    order_qualifier=OrderQualifier_Unknown,
    account="",
):
    # type: (Text, float, int, int, int, float, int, int, Text) ->List[Dict[Text, Any]]
    """
    按指定量委托
    """
    order_style = OrderStyle_Volume
    account_id = get_account_id(account)

    o = Order()
    o.symbol = symbol
    o.volume = volume
    o.price = price
    o.side = side
    o.order_type = order_type
    o.position_effect = position_effect
    o.order_style = order_style
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.account_id = account_id
    o.stop_price = stop_price
    o.trigger_type = trigger_type

    return _inner_place_order(o)


def order_value(
    symbol,
    value,
    side,
    order_type,
    position_effect,
    price=0,
    order_duration=OrderDuration_Unknown,
    order_qualifier=OrderQualifier_Unknown,
    account="",
):
    # type:(Text, float, int, int, int, float, int, int, Text) ->List[Dict[Text, Any]]
    """
    按指定价值委托
    """
    order_style = OrderStyle_Value
    account_id = get_account_id(account)

    o = Order()
    o.symbol = symbol
    o.value = value
    o.price = price
    o.side = side
    o.order_type = order_type
    o.position_effect = position_effect
    o.order_style = order_style
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.account_id = account_id

    return _inner_place_order(o)


def order_percent(
    symbol,
    percent,
    side,
    order_type,
    position_effect,
    price=0,
    order_duration=OrderDuration_Unknown,
    order_qualifier=OrderQualifier_Unknown,
    account="",
):
    # type: (Text, float, int, int, int, float, int, int, Text)->List[Dict[Text, Any]]
    """
    按指定比例委托
    """
    order_style = OrderStyle_Percent
    account_id = get_account_id(account)

    o = Order()
    o.symbol = symbol
    o.percent = percent
    o.price = price
    o.side = side
    o.order_type = order_type
    o.position_effect = position_effect
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.order_style = order_style
    o.account_id = account_id

    return _inner_place_order(o)


def order_target_volume(
    symbol,
    volume,
    position_side,
    order_type,
    price=0,
    order_duration=OrderDuration_Unknown,
    order_qualifier=OrderQualifier_Unknown,
    account="",
):
    # type: (Text, float, int, int, float, int, int, Text) ->List[Dict[Text, Any]]
    """
    调仓到目标持仓量
    """
    order_style = OrderStyle_TargetVolume
    account_id = get_account_id(account)

    o = Order()
    o.symbol = symbol
    o.target_volume = volume
    o.price = price
    o.position_side = position_side
    o.order_type = order_type
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.order_style = order_style
    o.account_id = account_id

    return _inner_place_order(o)


def order_target_value(
    symbol,
    value,
    position_side,
    order_type,
    price=0,
    order_duration=OrderDuration_Unknown,
    order_qualifier=OrderQualifier_Unknown,
    account="",
):
    # type: (Text, float, int, int, float, int, int, Text) ->List[Dict[Text, Any]]
    """
    调仓到目标持仓额
    """
    order_style = OrderStyle_TargetValue
    account_id = get_account_id(account)

    o = Order()
    o.symbol = symbol
    o.target_value = value
    o.price = price
    o.position_side = position_side
    o.order_type = order_type
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.order_style = order_style
    o.account_id = account_id

    return _inner_place_order(o)


def order_target_percent(
    symbol,
    percent,
    position_side,
    order_type,
    price=0,
    order_duration=OrderDuration_Unknown,
    order_qualifier=OrderQualifier_Unknown,
    account="",
):
    # type: (Text, float, int, int, float, int, int, Text) ->List[Dict[Text, Any]]
    """
    调仓到目标持仓比例
    """
    order_style = OrderStyle_TargetPercent
    account_id = get_account_id(account)

    o = Order()
    o.symbol = symbol
    o.target_percent = percent
    o.price = price
    o.position_side = position_side
    o.order_type = order_type
    o.order_qualifier = order_qualifier
    o.order_duration = order_duration
    o.order_style = order_style
    o.account_id = account_id

    return _inner_place_order(o)


def get_unfinished_orders():
    # type: ()->List[Dict[Text, Any]]
    """
    查询所有未结委托
    """
    unfinished_orders = []
    for account in context.accounts.values():
        req = GetUnfinishedOrdersReq()
        req.account_id = account.id
        req = req.SerializeToString()
        status, result = py_gmi_get_unfinished_orders(req)
        if c_status_fail(status, "py_gmi_get_unfinished_orders"):
            continue
        if result:
            res = Orders()
            res.ParseFromString(result)
            unfinished_orders.extend(
                [
                    protobuf_to_dict(
                        res_order,
                        including_default_value_fields=True,
                        dcls=DictLikeOrder,
                    )
                    for res_order in res.data
                ]
            )

    return unfinished_orders


def get_orders():
    # type: () ->List[Dict[Text, Any]]
    """
    查询日内全部委托
    """
    all_orders = []
    for account in context.accounts.values():
        req = GetOrdersReq()
        req.account_id = account.id
        req = req.SerializeToString()
        status, result = py_gmi_get_orders(req)
        if c_status_fail(status, "py_gmi_get_orders"):
            continue
        if result:
            res = Orders()
            res.ParseFromString(result)
            all_orders.extend(
                [
                    protobuf_to_dict(
                        res_order,
                        including_default_value_fields=True,
                        dcls=DictLikeOrder,
                    )
                    for res_order in res.data
                ]
            )

    return all_orders


def order_cancel_all():
    # type: () -> None
    """
    撤销所有委托
    """
    req = CancelAllOrdersReq()
    for account in context.accounts.values():
        req.account_ids.extend([account.id])

    req = req.SerializeToString()
    py_gmi_cancel_all_orders(req)


def order_close_all():
    # type: () ->List[Dict[Text, Any]]
    """
    平当前所有可平持仓
    """
    req = CloseAllPositionsReq()
    for account in context.accounts.values():
        req.account_ids.extend([account.id])

    req = req.SerializeToString()
    status, result = py_gmi_close_all_positions(req)
    check_gm_status(status)

    res = Orders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(
            res_order, including_default_value_fields=True, dcls=DictLikeOrder
        )
        for res_order in res.data
    ]


def order_cancel(wait_cancel_orders):
    # type: (Union[Dict[Text,Any], List[Dict[Text, Any]]]) -> None
    """
    撤销委托. 传入单个字典. 或者list字典. 每个字典包含key: cl_ord_id, account_id
    """
    wait_cancel_orders = load_to_list(wait_cancel_orders)

    orders = Orders()

    if len(wait_cancel_orders) == 0:
        send_custom_error("撤单信息不能为空")

    for wait_cancel_order in wait_cancel_orders:
        order = orders.data.add()
        order.cl_ord_id = wait_cancel_order.get("cl_ord_id")
        order.account_id = wait_cancel_order.get("account_id")

    req = orders.SerializeToString()
    status = py_gmi_cancel_order(req)
    check_gm_status(status)


def order_batch(order_infos, combine=False, account=""):
    """
    批量委托接口
    """

    if len(order_infos) == 0:
        send_custom_error("委托信息不能为空")

    orders = Orders()
    for order_info in order_infos:
        order_info["account_id"] = get_account_id(account)
        order = orders.data.add()
        [setattr(order, k, order_info[k]) for k in order_info]
        if context.is_backtest_model():
            order.created_at.seconds = datetime2timestamp(context.now)

    req = orders.SerializeToString()
    status, result = py_gmi_place_order(req)
    check_gm_status(status)

    res = Orders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(
            res_order, including_default_value_fields=True, dcls=DictLikeOrder
        )
        for res_order in res.data
    ]


def get_account_id(name_or_id):
    # type: (Text) ->Text
    for one in context.accounts.values():
        if one.match(name_or_id):
            return one.id

    # 都没有匹配上, 等着后端去拒绝
    return name_or_id


def get_execution_reports():
    # type: () -> List[Dict[Text, Any]]
    """
    返回执行回报
    """
    reports = []
    for account in context.accounts.values():
        req = GetExecrptsReq()
        req.account_id = account.id
        req = req.SerializeToString()
        status, result = py_gmi_get_execution_reports(req)
        if c_status_fail(status, "py_gmi_get_execution_reports"):
            continue
        if result:
            res = ExecRpts()
            res.ParseFromString(result)
            reports.extend(
                [
                    protobuf_to_dict(res_order, including_default_value_fields=True)
                    for res_order in res.data
                ]
            )

    return reports


# 以下为算法单
def algo_order(
    symbol,
    volume,
    side,
    order_type,
    position_effect,
    price,
    algo_name,
    algo_param,
    account="",
):
    # type: (Text, float, int, int, int, float, Text, Dict, Text) -> List[Dict[Text, Any]]
    """
    委托算法单. 返回列表里字典项是AlgoOrder的字段
    :param algo_param 为必填参数, 且只能是 dict 且必须包含4个必要的key
    """
    # 回测模式不支持算法单
    input_algo_param = dict(**algo_param)
    if context.is_backtest_model():
        msg = "!~~~~~~~~~~~!回测模式不支持算法单, 策略退出!~~~~~~~~~~~!"
        gmsdklogger.warning(msg)
        stop()

    # 检查参数是否正确
    if algo_name is None or len(algo_name.strip()) == 0:
        msg = "!~~~~~~~~~~~!algo_name必填, 策略退出!~~~~~~~~~~~!"
        gmsdklogger.warning(msg)
        stop()

    if algo_name is None or not isinstance(algo_param, dict) or len(algo_param) == 0:
        msg = "!~~~~~~~~~~~!algo_param error, 策略退出!~~~~~~~~~~~!"
        gmsdklogger.warning(msg)
        stop()
    else:
        algo_param_str = ""  # 默认
        try:
            # TWAP
            lower_algo_name = algo_name.lower()
            if lower_algo_name == "ats-smart":
                # 示例 start_time&&1605147796||end_time_referred&&1605150016||end_time&&1605150016||stop_sell_when_dl&&1||cancel_when_pl&&0||min_trade_amount&&10000
                today = time.strftime("%Y-%m-%d ", time.localtime(time.time()))
                algo_param["start_time"] = "%d" % time.mktime(
                    time.strptime(today + algo_param["start_time"], "%Y-%m-%d %H:%M:%S")
                )
                algo_param["end_time"] = "%d" % time.mktime(
                    time.strptime(today + algo_param["end_time"], "%Y-%m-%d %H:%M:%S")
                )
                algo_param["end_time_referred"] = "%d" % time.mktime(
                    time.strptime(
                        today + algo_param["end_time_referred"], "%Y-%m-%d %H:%M:%S"
                    )
                )
                algo_param_str = "||".join(
                    [key + "&&" + str(algo_param.get(key)) for key in algo_param.keys()]
                )
            elif lower_algo_name in ("twap", "vwap"):
                # get date today
                today = time.strftime("%Y-%m-%d ", time.localtime(time.time()))

                # 兼容处理
                start_time = (
                    algo_param.get("time_start", None)
                    if algo_param.get("start_time", None) is None
                    else algo_param.get("start_time", None)
                )
                end_time = (
                    algo_param.get("time_end", None)
                    if algo_param.get("end_time", None) is None
                    else algo_param.get("end_time", None)
                )

                time_start = "%d" % time.mktime(
                    time.strptime(today + start_time, "%Y-%m-%d %H:%M:%S")
                )
                time_end = "%d" % time.mktime(
                    time.strptime(today + end_time, "%Y-%m-%d %H:%M:%S")
                )

                time_start = "TimeStart&&" + time_start
                time_end = "TimeEnd&&" + time_end
                part_rate = "PartRate&&" + "%f" % algo_param["part_rate"]
                min_amount = "MinAmount&&" + "%d" % algo_param["min_amount"]
                algo_param_str = "||".join(
                    [time_start, time_end, part_rate, min_amount]
                )
            else:
                algo_param_str = "||".join(
                    [key + "&&" + str(algo_param.get(key)) for key in algo_param.keys()]
                )
        except Exception as e:
            msg = "!~~~~~~~~~~~!algo_param error, 策略退出!~~~~~~~~~~~!"
            gmsdklogger.warning(msg, e)
            stop()

    account_id = get_account_id(account)
    ao = AlgoOrder()
    ao.symbol = symbol
    ao.volume = volume
    ao.side = side
    ao.order_type = order_type
    ao.position_effect = position_effect
    ao.price = price
    ao.algo_name = algo_name
    ao.algo_param = algo_param_str
    ao.account_id = account_id
    ao.order_style = OrderStyle_Volume

    for k, v in input_algo_param.items():
        ao.algo_params[k] = str(v)

    algo_orders = AlgoOrders()
    algo_orders.data.extend([ao])

    req = algo_orders.SerializeToString()
    status, result = py_gmi_place_algo_orders(req)
    check_gm_status(status)

    res = AlgoOrders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(res_order, including_default_value_fields=True)
        for res_order in res.data
    ]

# 算法单批量下单
def algo_order_batch(algo_orders, algo_name, algo_param, account=''):
    # type: (List[Dict[Text, Any]], str, Dict[Text, Any], str) -> List[Dict[Text, Any]]
    """
    委托算法单. 返回列表里字典项是AlgoOrder的字段
    :param algo_param 为必填参数, 且只能是 dict 且必须包含4个必要的key
    """

    algo_param_str = ""
    algo_orders_req = AlgoOrders()
    # 回测模式不支持算法单
    input_algo_param = dict(**algo_param)
    if context.is_backtest_model():
        msg = "!~~~~~~~~~~~!回测模式不支持算法单, 策略退出!~~~~~~~~~~~!"
        gmsdklogger.warning(msg)
        stop()

    # 检查参数是否正确
    if algo_name is None or len(algo_name.strip()) == 0:
        msg = "!~~~~~~~~~~~!algo_name必填, 策略退出!~~~~~~~~~~~!"
        gmsdklogger.warning(msg)
        stop()

    if algo_name is None or not isinstance(algo_param, dict) or len(algo_param) == 0:
        msg = "!~~~~~~~~~~~!algo_param error, 策略退出!~~~~~~~~~~~!"
        gmsdklogger.warning(msg)
        stop()
    else:
        try:
            algo_param_str = "||".join(
                [key + "&&" + str(algo_param.get(key)) for key in algo_param.keys()]
            )
        except Exception as e:
            msg = "!~~~~~~~~~~~!algo_param error, 策略退出!~~~~~~~~~~~!"
            gmsdklogger.warning(msg, e)
            stop()

    for order in algo_orders:
        account_id = get_account_id(account)
        ao = AlgoOrder()
        ao.symbol = order["symbol"]
        ao.volume = int(order["volume"])
        ao.side = int(order["side"])
        ao.order_type = int(order["order_type"])
        ao.position_effect = int(order["position_effect"])
        ao.price = float(order["price"])
        ao.account_id = account_id
        ao.order_style = OrderStyle_Volume
        algo_orders_req.data.extend([ao])

    req = algo_orders_req.SerializeToString()
    status, result = py_gmi_algo_order_batch(req, algo_name, algo_param_str)
    check_gm_status(status)

    res = AlgoOrders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(res_order, including_default_value_fields=True)
        for res_order in res.data
    ]


def algo_order_cancel(wait_cancel_orders):
    # type: (Union[Dict[Text,Any], List[Dict[Text, Any]]]) -> None
    """
    撤单算法委托. 传入单个字典. 或者list字典. 每个字典包含key:
    cl_ord_id
    account_id  默认帐号时为 ''
    """
    default_account_id = get_account_id("")
    wait_cancel_orders = load_to_list(wait_cancel_orders)

    algo_orders = AlgoOrders()

    for item in wait_cancel_orders:
        ao = algo_orders.data.add()  # type: AlgoOrder
        ao.account_id = item.get("account_id", "")
        ao.cl_ord_id = item.get("cl_ord_id", "")

    req = algo_orders.SerializeToString()
    status = py_gmi_cancel_algo_orders(req)
    check_gm_status(status)


def algo_order_pause(alorders):
    # type: (Union[Dict[Text,Any], List[Dict[Text, Any]]]) -> None
    """
    暂停/恢复算法单. 传入单个字典. 或者list字典. 每个字典包含key:
    cl_ord_id
    account_id  默认帐号时为 ''
    status      参见 AlgoOrderStatus_ 开头的常量
    """
    default_account_id = get_account_id("")
    alorders = load_to_list(alorders)

    algo_orders = AlgoOrders()

    for item in alorders:
        ao = algo_orders.data.add()  # type: AlgoOrder
        ao.cl_ord_id = item.get("cl_ord_id")
        account_id = item.get("account_id", "")
        if not account_id:
            account_id = default_account_id
        ao.account_id = account_id
        ao.algo_status = item.get("algo_status")

    req = algo_orders.SerializeToString()
    status = py_gmi_pause_algo_orders(req)
    check_gm_status(status)


def get_algo_orders(account=""):
    # type: (Text) -> List[Dict[Text, Any]]
    """
    查询算法委托. 返回列表里字典项是AlgoOrder的字段
    """
    account_id = get_account_id(account)
    req = GetAlgoOrdersReq()
    req.account_id = account_id
    status, result = py_gmi_get_algo_orders(req.SerializeToString())
    check_gm_status(status)

    res = AlgoOrders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(res_order, including_default_value_fields=True)
        for res_order in res.data
    ]


def get_algo_child_orders(cl_ord_id, account=""):
    # type: (Text, Text) -> List[Dict[Text, Any]]
    """
    查询算法子委托. 返回列表里字典项是Order的字段
    """
    account_id = get_account_id(account)
    status, result = py_gmi_get_child_orders(account_id, cl_ord_id)
    check_gm_status(status)

    res = Orders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(res_order, including_default_value_fields=True)
        for res_order in res.data
    ]


def option_exercise(symbol, volume, account=""):
    # type: (Text, int, Text) -> List[Dict[Text, Any]]
    """
    行权
    """
    account_id = get_account_id(account)

    order = Order()
    order.order_style = OrderStyle_Volume  # 按指定量委托
    order.order_business = OrderBusiness_OPTION_EXERCISE
    order.symbol = symbol
    order.volume = volume
    order.account_id = account_id

    return _inner_place_order(order)


def option_covered_open(symbol, volume, order_type, price=0.0, account=""):
    # type: (Text, int, int, float, Text) -> List[Dict[Text, Any]]
    """
    备兑开仓 \n
    return:
        list[order]
    """
    account_id = get_account_id(account)

    order = Order()
    order.order_business = OrderBusiness_OPTION_COVERED_SELL_OPEN
    order.symbol = symbol
    order.volume = volume
    order.side = OrderSide_Sell
    order.order_type = order_type
    order.price = price
    order.account_id = account_id

    return _inner_place_order(order)


def option_covered_close(symbol, volume, order_type, price=0, account=""):
    # type: (Text, int, int, float, Text) -> List[Dict[Text, Any]]
    """
    备兑平仓 \n
    return:
        list[order]
    """
    account_id = get_account_id(account)

    order = Order()
    order.order_business = OrderBusiness_OPTION_COVERED_BUY_CLOSE
    order.symbol = symbol
    order.volume = volume
    order.side = OrderSide_Buy
    order.order_type = order_type
    order.price = price
    order.account_id = account_id

    return _inner_place_order(order)


def option_preorder_valid_volume(symbol, price, side, covered_flag=0, account=""):
    # type: (Text, float, int, int, Text) -> int
    """
    获取可开数量 \n
    params: \n
    \t symbol:              标的代码
    \t price:               用户指定价格
    \t side:                订单委托方向
    \t covered_flag:        备兑标志
    \t account:             账户
    """
    account_id = get_account_id(account)
    if side == OrderSide_Buy:
        order_business = OrderBusiness_OPTION_BUY_OPEN
    elif side == OrderSide_Sell:
        if covered_flag == 1:
            order_business = OrderBusiness_OPTION_COVERED_SELL_OPEN
        else:
            order_business = OrderBusiness_OPTION_SELL_OPEN
    req = GetEntrustableVolumeBySymbolReq(
        account_id=account_id,
        symbol=symbol,
        price=price,
        order_business=order_business,
        order_type=OrderType_Limit,
    ).SerializePartialToString()
    status, rsp_str = py_gmi_get_entrustable_volume_by_symbol_pb(req)
    check_gm_status(status)
    rsp = GetEntrustableVolumeBySymbolRsp()
    rsp.ParseFromString(rsp_str)
    return rsp.max_entrustable_volume


def option_preorder_sell_margin(symbol, account=""):
    # type: (Text, Text) -> float
    """
    计算期权卖方开仓保证金 \n
    params: \n
    \t symbol:              期权合约代码,如SHSE.10002498
    """
    account_id = get_account_id(account)
    req = GetEntrustableVolumeBySymbolReq(
        account_id=account_id,
        symbol=symbol,
        order_business=OrderBusiness_OPTION_SELL_OPEN,
        order_type=OrderType_Market,
        price=0.0,
    ).SerializePartialToString()
    status, rsp_str = py_gmi_get_entrustable_volume_by_symbol_pb(req)
    check_gm_status(status)
    rsp = GetEntrustableVolumeBySymbolRsp()
    rsp.ParseFromString(rsp_str)
    return rsp.margin_per_unit


# ============ 算法接口 ==================
def algo_smart_reorder(
    symbol,
    price,
    volume,
    side,
    position_effect,
    repeat_n,
    max_price_offset,
    time_out,
    time_wait,
    account="",
):
    # type: (Text, float, int, int, int, int, int, int, int, Text) -> Dict[Text, int]
    """
    智能追单委托
    """
    # 返回值大于等于1百万追单委托成功, 否则失败返回错误码
    order_type = OrderType_Limit
    value = py_gmi_smart_reorder(
        symbol,
        price,
        volume,
        side,
        order_type,
        position_effect,
        repeat_n,
        max_price_offset,
        time_out,
        time_wait,
        account,
    )
    if value >= 1000000:
        return dict(reorder_id=value, reorder_status=0)
    else:
        return dict(reorder_id=0, reorder_status=value)


def algo_smart_reorder_cancel(reorder_id):
    # type: (int) -> bool
    """
    智能追单撤销
    """
    status = py_gmi_smart_reorder_cancel(reorder_id)  # 撤销成功返回0, 失败返回非0
    return status == 0  # 成功返回 True, 失败返回 False


def place_order_mm(
    symbol,
    buy_volume=0,
    buy_price=0.0,
    sell_volume=0,
    sell_price=0.0,
    order_auto_fill=True,
    price_br=None,
    account_id="",
):
    # type: (str, int, float, int, float, bool, float , str) -> List[Dict]
    """做市报价委托"""
    if price_br is None:
        price_br = 0.05
    order = Order(
        symbol=symbol,
        buy_volume=buy_volume,
        buy_price=buy_price,
        sell_volume=sell_volume,
        sell_price=sell_price,
        order_auto_fill=int(order_auto_fill),
        float_br=price_br,
        account_id=account_id,
        volume=1000,
        order_business=OrderBusiness_MARKET_MAKING,
    )
    if context.is_backtest_model() and context.has_wait_group:
        order.created_at.seconds = datetime2timestamp(context.now)

    orders = Orders()
    orders.data.extend([order])

    req = orders.SerializeToString()
    status, result = py_gmi_place_order(req)
    check_gm_status(status)

    res = Orders()
    res.ParseFromString(result)

    return [
        protobuf_to_dict(
            res_order, including_default_value_fields=True, dcls=DictLikeOrderMM
        )
        for res_order in res.data
    ]


def get_orders_mm(symbol="", order_ids="", account_id=""):
    # type: (str, str|List, str) -> List[Dict]
    """查询日内所有做市委托"""
    if symbol:
        symbols = [symbol]
    else:
        symbols = None
    if not order_ids:
        order_ids = None
    elif isinstance(order_ids, str):
        order_ids = [id.strip() for id in order_ids.split(",")]

    all_orders = []
    if account_id:
        account_ids = [account_id]
    else:
        account_ids = [account.id for account in context.accounts.values()]
    for id in account_ids:
        req = GetOrdersReq(
            account_id=id,
            symbols=symbols,
            cl_ord_ids=order_ids,
        ).SerializeToString()
        status, res = py_gmi_get_orders(req)
        if c_status_fail(status, "get_orders_mm"):
            continue
        if res:
            rsp = Orders()
            rsp.ParseFromString(res)
            all_orders.extend(
                [
                    protobuf_to_dict(
                        res_order,
                        including_default_value_fields=True,
                        dcls=DictLikeOrderMM,
                    )
                    for res_order in rsp.data
                ]
            )
    return all_orders


def get_unfinished_orders_mm(symbol="", order_ids="", account_id=""):
    # type: (str, str|List, str) -> List[Dict]
    """查询日内所有未结的做市委托"""
    if symbol:
        symbols = [symbol]
    else:
        symbols = None
    if not order_ids:
        order_ids = None
    elif isinstance(order_ids, str):
        order_ids = [id.strip() for id in order_ids.split(",")]

    all_orders = []
    if account_id:
        account_ids = [account_id]
    else:
        account_ids = [account.id for account in context.accounts.values()]
    for id in account_ids:
        req = GetUnfinishedOrdersReq(
            account_id=id,
            symbols=symbols,
            cl_ord_ids=order_ids,
        ).SerializeToString()
        status, res = py_gmi_get_unfinished_orders(req)
        if c_status_fail(status, "get_unfinished_orders_mm"):
            continue
        if res:
            rsp = Orders()
            rsp.ParseFromString(res)
            all_orders.extend(
                [
                    protobuf_to_dict(
                        res_order,
                        including_default_value_fields=True,
                        dcls=DictLikeOrderMM,
                    )
                    for res_order in rsp.data
                ]
            )
    return all_orders
