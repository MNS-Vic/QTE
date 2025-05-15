"""期权组合交易API"""

from typing import List
from gm.pb.trade_option_service_pb2 import (
    OptionCombEntrustReq, OptionCombEntrustRsp,
    OptionSepEntrustReq, OptionSepEntrustRsp,
    GetOptionCombinableReq, GetOptionCombinableRsp,
    GetOptionCombPositionReq, GetOptionCombPositionRsp,
)
from gm.csdk.c_sdk import (
    py_gmi_option_comb_entrust_pb,
    py_gmi_option_sep_entrust_pb,
    py_gmi_get_option_combinable_pb,
    py_gmi_get_option_comb_position_pb,
)
from gm.api._errors import check_gm_status


class CombOrder(dict):
    """组合拆分委托对象"""
    error_code: int
    """委托结果, 0表示成功, 非0为错误码"""
    error_desc: str
    """错误描述信息, error_code 非 0 时有效"""
    order_id: str
    """委托编号"""

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise NameError("name '{}' is not defined".format(name))

    def __setattr__(self, name, value):
        if name not in self:
            raise NameError("name '{}' is not defined".format(name))
        self.__setitem__(name, value)


class CombInfo(dict):
    """可组合策略对象"""
    underlying_symbol: str
    """标的证券代码"""
    optcomb_code: str
    """组合策略编码(如KS)"""
    optcomb_name: str
    """组合策略名称(如跨式空头)"""
    enable_volume: int
    """组合可用数量"""
    release_margin: float
    """组合释放保证金"""
    frozen_margin: float
    """组合冻结保证金"""
    first_symbol: str
    """第一腿合约代码"""
    first_option_name: str
    """第一腿合约名称"""
    first_option_type: str
    """第一腿合约期权类别(认购/认沽)"""
    first_opthold_type: str
    """第一腿合约持仓类别(权利方/义务方)"""
    first_opthold_covered_flag: int
    """第一腿合约持仓备兑标志"""
    first_opthold_volume: int
    """第一腿合约实际数量"""
    first_opt_enable_volume: int
    """第一腿合约持仓可用"""
    first_opt_comb_used_volume: int
    """第一腿合约组合冻结数量"""
    first_opt_last_price: float
    """第一腿合约最新价"""
    first_opt_cost_price: float
    """第一腿合约成本价"""
    first_opt_fpnl: float
    """第一腿合约浮动盈亏"""
    first_opt_used_bail: float
    """第一腿合约义务仓占用保证金"""
    first_opt_expire_day: int
    """第一腿合约到期天数"""
    second_symbol: str
    """第二腿合约代码"""
    second_option_name: str
    """第二腿合约名称"""
    second_option_type: str
    """第二腿合约期权类别(认购/认沽)"""
    second_opthold_type: str
    """第二腿合约持仓类别(权利方/义务方)"""
    second_opthold_covered_flag: int
    """第二腿合约持仓备兑标志"""
    second_opthold_volume: int
    """第二腿合约实际数量"""
    second_opt_enable_volume: int
    """第二腿合约持仓可用"""
    second_opt_comb_used_volume: int
    """第二腿合约组合冻结数量"""
    second_opt_last_price: float
    """第二腿合约最新价"""
    second_opt_cost_price: float
    """第二腿合约成本价"""
    second_opt_fpnl: float
    """第二腿合约浮动盈亏"""
    second_opt_used_bail: float
    """第二腿合约义务仓占用保证金"""
    second_opt_expire_day: int
    """第二腿合约到期天数"""

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise NameError("name '{}' is not defined".format(name))

    def __setattr__(self, name, value):
        if name not in self:
            raise NameError("name '{}' is not defined".format(name))
        self.__setitem__(name, value)


class CombPos(dict):
    """组合策略持仓对象"""
    optcomb_code: str
    """组合策略编码(如KS)"""
    optcomb_name: str
    """组合策略名称(如跨式空头)"""
    optcomb_id: str
    """组合编码"""
    current_volume: int
    """当前持有数量"""
    enable_volume: int
    """可用数量"""
    real_comb_volume: int
    """回报组合数量"""
    real_split_volume: int
    """回报拆分数量"""
    entrust_split_volume: int
    """委托拆分数量"""
    first_symbol: str
    """第一腿合约代码"""
    first_option_name: str
    """第一腿合约名称"""
    first_option_type: str
    """第一腿合约期权类别(认购/认沽)"""
    first_opthold_type: int
    """第一腿合约持仓类别(权利方/义务方)"""
    first_opthold_covered_flag: int
    """第一腿合约持仓备兑标志"""
    first_opt_volume: int
    """第一腿合约数量"""
    second_symbol: str
    """第二腿合约代码"""
    second_option_name: str
    """第二腿合约名称"""
    second_option_type: str
    """第二腿合约期权类别(认购/认沽)"""
    second_opthold_type: int
    """第二腿合约持仓类别(权利方/义务方)"""
    second_opthold_covered_flag: int
    """第二腿合约持仓备兑标志"""
    second_opt_volume: int
    """第二腿合约数量"""
    comb_bail_balance: float
    """组合占用保证金"""
    split_comb_margin: float
    """组合拆分后保证金"""
    comb_auto_split_date: float
    """组合自动拆分日期"""

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise NameError("name '{}' is not defined".format(name))

    def __setattr__(self, name, value):
        if name not in self:
            raise NameError("name '{}' is not defined".format(name))
        self.__setitem__(name, value)


def option_comb(optcomb_code,
                volume,
                first_symbol,
                first_opthold_type,
                first_opthold_covered_flag,
                second_symbol=None,
                second_opthold_type=None,
                second_opthold_covered_flag=None,
                account_id='',
                ):
    # type: (str, int, str, int, int, str, int, int, str) -> CombOrder
    """组合申报委托, 指定组合策略编码、两腿合约信息和组合委托数量进行组合申报

    普通转备兑(optcomb_code='ZBD')时, 第二腿合约参数second_symbol, second_opthold_type, second_opthold_covered_flag 不需要指定, 若指定也无效.
    除此之外其余组合，第二腿合约参数必填
    """
    if optcomb_code == "ZBD":
        second_symbol = ""
        second_opthold_type = 0
        second_opthold_covered_flag = 0
    elif second_symbol is None or second_opthold_type is None or second_opthold_covered_flag is None:
        raise ValueError("第二腿合约参数必填")

    req = OptionCombEntrustReq(
        optcomb_code=optcomb_code,
        volume=volume,
        first_option_code=first_symbol,
        first_opthold_side=first_opthold_type,
        first_opthold_covered_flag=first_opthold_covered_flag,
        second_option_code=second_symbol,
        second_opthold_side=second_opthold_type,
        second_opthold_covered_flag=second_opthold_covered_flag,
        account_id=account_id,
    )
    req = req.SerializeToString()
    status, result = py_gmi_option_comb_entrust_pb(req)
    check_gm_status(status)
    rsp = OptionCombEntrustRsp()
    rsp.ParseFromString(result)
    return CombOrder(
        error_code=rsp.error_code,
        error_desc=rsp.error_desc,
        order_id=rsp.order_id,
    )


def option_comb_by_comb_info(comb_info, account_id=''):
    # type: (List[CombInfo], str) -> List[CombOrder]
    """可组合申报, 指定可组合策略对象并按组合可用数量进行组合申报"""
    if not comb_info:
        return []
    items = []  # type: List[CombOrder]
    for item in comb_info:
        req = OptionCombEntrustReq(
            optcomb_code=item.optcomb_code,
            volume=item.enable_volume,
            first_option_code=item.first_symbol,
            first_opthold_side=item.first_opthold_type,
            first_opthold_covered_flag=item.first_opthold_covered_flag,
            second_option_code=item.second_symbol,
            second_opthold_side=item.second_opthold_type,
            second_opthold_covered_flag=item.second_opthold_covered_flag,
            account_id=account_id,
        )
        req = req.SerializeToString()
        status, result = py_gmi_option_comb_entrust_pb(req)
        check_gm_status(status)

        rsp = OptionCombEntrustRsp()
        rsp.ParseFromString(result)
        items.append(CombOrder(
            error_code=rsp.error_code,
            error_desc=rsp.error_desc,
            order_id=rsp.order_id,
        ))
    return items


def option_sep(optcomb_id,
               optcomb_code,
               volume,
               first_symbol,
               first_opthold_type,
               first_opthold_covered_flag,
               second_symbol=None,
               second_opthold_type=None,
               second_opthold_covered_flag=None,
               account_id='',
               ):
    # type: (str, str, int, str, int, int, str, int, int, str) -> CombOrder
    """ 拆分申报委托, 指定组合编码和委托数量进行拆分申报"""
    if optcomb_code in ["ZBD", "ZXJ"]:
        second_symbol = ""
        second_opthold_type = 0
        second_opthold_covered_flag = 0
    elif second_symbol is None or second_opthold_type is None or second_opthold_covered_flag is None:
        raise ValueError("第二腿合约参数必填")

    req = OptionSepEntrustReq(
        optcomb_id=optcomb_id,
        optcomb_code=optcomb_code,
        volume=volume,
        first_option_code=first_symbol,
        first_opthold_side=first_opthold_type,
        first_opthold_covered_flag=first_opthold_covered_flag,
        second_option_code=second_symbol,
        second_opthold_side=second_opthold_type,
        second_opthold_covered_flag=second_opthold_covered_flag,
        account_id=account_id,
    )
    req = req.SerializeToString()
    status, result = py_gmi_option_sep_entrust_pb(req)
    check_gm_status(status)

    rsp = OptionSepEntrustRsp()
    rsp.ParseFromString(result)
    return CombOrder(
        error_code=rsp.error_code,
        error_desc=rsp.error_desc,
        order_id=rsp.order_id,
    )


def option_sep_by_comb_pos(comb_pos, account_id=''):
    # type: (List[CombPos], str) -> List[CombOrder]
    """组合持仓拆分申报, 指定组合策略持仓对象并按可用数量进行拆分申报"""
    if not comb_pos:
        return []
    items = []  # type: List[CombOrder]
    for item in comb_pos:
        req = OptionSepEntrustReq(
            optcomb_id=item.optcomb_id,
            optcomb_code=item.optcomb_code,
            volume=item.enable_volume,
            first_option_code=item.first_symbol,
            first_opthold_side=item.first_opthold_type,
            first_opthold_covered_flag=item.first_opthold_covered_flag,
            second_option_code=item.second_symbol,
            second_opthold_side=item.second_opthold_type,
            second_opthold_covered_flag=item.second_opthold_covered_flag,
            account_id=account_id,
        )
        req = req.SerializeToString()
        status, result = py_gmi_option_sep_entrust_pb(req)
        check_gm_status(status)

        rsp = OptionSepEntrustRsp()
        rsp.ParseFromString(result)
        items.append(CombOrder(
            error_code=rsp.error_code,
            error_desc=rsp.error_desc,
            order_id=rsp.order_id,
        ))
    return items


def option_get_comb_info(exchange, optcomb_code, account_id=''):
    # type: (str, str, str) -> List[CombInfo]
    """可组合策略查询, 查询当前期权持仓中，可组合成特定组合的信息，包括策略编码，策略名称，组合可用数量等信息"""
    req = GetOptionCombinableReq(
        exchange=exchange,
        comb_code=optcomb_code,
        account_id=account_id,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_option_combinable_pb(req)
    check_gm_status(status)

    rsp = GetOptionCombinableRsp()
    rsp.ParseFromString(result)
    items = []
    for item in rsp.data:
        items.append(CombInfo(
            underlying_symbol=item.first_leg.stock_code,
            optcomb_code=item.optcombCode,
            optcomb_name=item.optcombName,
            enable_volume=item.enableAmount,
            release_margin=item.releaseMargin,
            frozen_margin=item.frozenMargin,
            first_symbol=item.first_leg.symbol,
            first_option_name=item.first_leg.option_name,
            first_option_type=item.first_leg.option_type,
            first_opthold_type=item.first_leg.opthold_side,
            first_opthold_covered_flag=item.first_leg.covered_flag,
            first_opthold_volume=item.first_leg.hold_amount,
            first_opt_enable_volume=item.first_leg.enable_amount,
            first_opt_comb_used_volume=item.first_leg.optcomb_used_amount,
            first_opt_last_price=item.first_leg.opt_last_price,
            first_opt_cost_price=item.first_leg.opt_cost_price,
            first_opt_fpnl=item.first_leg.income_balance,
            first_opt_used_bail=item.first_leg.duty_used_bail,
            first_opt_expire_day=item.first_leg.expire_day,
            second_symbol=item.second_leg.symbol,
            second_option_name=item.second_leg.option_name,
            second_option_type=item.second_leg.option_type,
            second_opthold_type=item.second_leg.opthold_side,
            second_opthold_covered_flag=item.second_leg.covered_flag,
            second_opthold_volume=item.second_leg.hold_amount,
            second_opt_enable_volume=item.second_leg.enable_amount,
            second_opt_comb_used_volume=item.second_leg.optcomb_used_amount,
            second_opt_last_price=item.second_leg.opt_last_price,
            second_opt_cost_price=item.second_leg.opt_cost_price,
            second_opt_fpnl=item.second_leg.income_balance,
            second_opt_used_bail=item.second_leg.duty_used_bail,
            second_opt_expire_day=item.second_leg.expire_day,
        ))
    return items


def option_get_comb_pos(optcomb_code='', account_id=''):
    # type: (str, str) -> List[CombPos]
    """组合策略持仓查询, 查询当前组合策略持仓信息，可拆分成普通持仓的组合策略代码，策略名称，组合编码，可用数量等信息"""
    req = GetOptionCombPositionReq(
        comb_code=optcomb_code,
        account_id=account_id,
    )
    req = req.SerializeToString()
    status, result = py_gmi_get_option_comb_position_pb(req)
    check_gm_status(status)

    rsp = GetOptionCombPositionRsp()
    rsp.ParseFromString(result)
    items = []
    for item in rsp.data:
        items.append(CombPos(
            optcomb_code=item.optcomb_code,
            optcomb_name=item.optcomb_name,
            optcomb_id=item.optcomb_id,
            current_volume=item.current_amount,
            enable_volume=item.enable_amount,
            real_comb_volume=item.real_comb_amount,
            real_split_volume=item.real_split_amount,
            entrust_split_volume=item.entrust_split_amount,
            first_symbol=item.first_symbol,
            first_option_name=item.first_option_name,
            first_option_type=item.first_option_type,
            first_opthold_type=item.first_opthold_side,
            first_opthold_covered_flag=item.first_opthold_covered_flag,
            first_opt_volume=item.first_opt_amount,
            second_symbol=item.second_symbol,
            second_option_name=item.second_option_name,
            second_option_type=item.second_option_type,
            second_opthold_type=item.second_opthold_side,
            second_opthold_covered_flag=item.second_opthold_covered_flag,
            second_opt_volume=item.second_opt_amount,
            comb_bail_balance=item.comb_bail_balance,
            split_comb_margin=item.split_comb_margin,
            comb_auto_split_date=item.comb_auto_split_date,
        ))
    return items
