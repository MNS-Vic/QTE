# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

from datetime import datetime

from typing import Any, Dict, List, Text, Optional


class DictLikeL2Transaction(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeL2Transaction, self).__str__()

    def __repr__(self):
        return super(DictLikeL2Transaction, self).__repr__()

    @property
    def symbol(self):
        # type: ()->Text
        """
        symbol
        """
        return self["symbol"]

    @symbol.setter
    def symbol(self, value):
        # type: (Text) -> None
        self["symbol"] = value

    @property
    def side(self):
        # type: ()->Text
        """
        买卖方向，取值参考enum OrderSide
        """
        return self["side"]

    @side.setter
    def side(self, value):
        # type: (int) -> None
        self["side"] = value

    @property
    def price(self):
        # type: ()->float
        """
        price
        """
        return self["price"]

    @price.setter
    def price(self, value):
        # type: (float) -> None
        self["price"] = value

    @property
    def volume(self):
        # type: ()->int
        """
        volume
        """
        return self["volume"]

    @volume.setter
    def volume(self, value):
        # type: (int) -> None
        self["volume"] = value

    @property
    def created_at(self):
        # type: ()->Optional[datetime]
        """
        回报创建时间
        """
        return self["created_at"]

    @created_at.setter
    def created_at(self, value):
        # type: (Optional[datetime]) -> None
        self["created_at"] = value


class DictLikeExecRpt(dict):
    """
    A dict that allows for ExecRpt-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeExecRpt, self).__str__()

    def __repr__(self):
        return super(DictLikeExecRpt, self).__repr__()

    @property
    def strategy_id(self):
        # type: ()->Text
        """
        策略ID
        """
        return self["strategy_id"]

    @strategy_id.setter
    def strategy_id(self, value):
        # type: (Text) -> None
        self["strategy_id"] = value

    @property
    def account_id(self):
        # type: ()->Text
        """
        账号ID
        """
        return self["account_id"]

    @account_id.setter
    def account_id(self, value):
        # type: (Text) -> None
        self["account_id"] = value

    @property
    def account_name(self):
        # type: ()->Text
        """
        账户登录名
        """
        return self["account_name"]

    @account_name.setter
    def account_name(self, value):
        # type: (Text) -> None
        self["account_name"] = value

    @property
    def cl_ord_id(self):
        # type: ()->Text
        """
        委托客户端ID
        """
        return self["cl_ord_id"]

    @cl_ord_id.setter
    def cl_ord_id(self, value):
        # type: (Text) -> None
        self["cl_ord_id"] = value

    @property
    def order_id(self):
        # type: ()->Text
        """
        委托柜台ID
        """
        return self["order_id"]

    @order_id.setter
    def order_id(self, value):
        # type: (Text) -> None
        self["order_id"] = value

    @property
    def exec_id(self):
        # type: ()->Text
        """
        委托回报ID
        """
        return self["exec_id"]

    @exec_id.setter
    def exec_id(self, value):
        # type: (Text) -> None
        self["exec_id"] = value

    @property
    def symbol(self):
        # type: ()->Text
        """
        symbol
        """
        return self["symbol"]

    @symbol.setter
    def symbol(self, value):
        # type: (Text) -> None
        self["symbol"] = value

    @property
    def position_effect(self):
        # type: ()->int
        """
        开平标志，取值参考enum PositionEffect
        """
        return self["position_effect"]

    @position_effect.setter
    def position_effect(self, value):
        # type: (int) -> None
        self["position_effect"] = value

    @property
    def side(self):
        # type: ()->int
        """
        买卖方向，取值参考enum OrderSide
        """
        return self["side"]

    @side.setter
    def side(self, value):
        # type: (int) -> None
        self["side"] = value

    @property
    def ord_rej_reason(self):
        # type: ()->int
        """
        委托拒绝原因，取值参考enum OrderRejectReason
        """
        return self["ord_rej_reason"]

    @ord_rej_reason.setter
    def ord_rej_reason(self, value):
        # type: (int) -> None
        self["ord_rej_reason"] = value

    @property
    def ord_rej_reason_detail(self):
        # type: ()->Text
        """
        委托拒绝原因描述
        """
        return self["ord_rej_reason_detail"]

    @ord_rej_reason_detail.setter
    def ord_rej_reason_detail(self, value):
        # type: (Text) -> None
        self["ord_rej_reason_detail"] = value

    @property
    def exec_type(self):
        # type: ()->Text
        """
        执行回报类型, 取值参考enum ExecType
        """
        return self["exec_type"]

    @exec_type.setter
    def exec_type(self, value):
        # type: (Text) -> None
        self["exec_type"] = value

    @property
    def price(self):
        # type: ()->float
        """
        委托成交价格
        """
        return self["price"]

    @price.setter
    def price(self, value):
        # type: (float) -> None
        self["price"] = value

    @property
    def volume(self):
        # type: ()->int
        """
        委托成交量
        """
        return self["volume"]

    @volume.setter
    def volume(self, value):
        # type: (int) -> None
        self["volume"] = value

    @property
    def amount(self):
        # type: ()->float
        """
        委托成交金额
        """
        return self["amount"]

    @amount.setter
    def amount(self, value):
        # type: (float) -> None
        self["amount"] = value

    @property
    def commission(self):
        # type: ()->Text
        """
        委托成交手续费
        """
        return self["commission"]

    @commission.setter
    def commission(self, value):
        # type: (Text) -> None
        self["commission"] = value

    @property
    def const(self):
        # type: ()->float
        """
        成本
        """
        return self["const"]

    @const.setter
    def const(self, value):
        # type: (float) -> None
        self["const"] = value

    @property
    def created_at(self):
        # type: ()->Optional[datetime]
        """
        回报创建时间
        """
        return self["created_at"]

    @created_at.setter
    def created_at(self, value):
        # type: (Optional[datetime]) -> None
        self["created_at"] = value


class DictLikeAlgoOrder(dict):
    """
    A dict that allows for Order-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeAlgoOrder, self).__str__()

    def __repr__(self):
        return super(DictLikeAlgoOrder, self).__repr__()

    @property
    def strategy_id(self):
        # type: ()->Text
        """
        策略ID
        """
        return self["strategy_id"]

    @strategy_id.setter
    def strategy_id(self, value):
        # type: (Text) -> None
        self["strategy_id"] = value

    @property
    def ccount_id(self):
        # type: ()->Text
        """
        账号ID
        """
        return self["ccount_id"]

    @ccount_id.setter
    def ccount_id(self, value):
        # type: (Text) -> None
        self["ccount_id"] = value

    @property
    def ccount_name(self):
        # type: ()->Text
        """
        账户登录名
        """
        return self["ccount_name"]

    @ccount_name.setter
    def ccount_name(self, value):
        # type: (Text) -> None
        self["ccount_name"] = value

    @property
    def l_ord_id(self):
        # type: ()->Text
        """
        委托客户端ID
        """
        return self["l_ord_id"]

    @l_ord_id.setter
    def l_ord_id(self, value):
        # type: (Text) -> None
        self["l_ord_id"] = value

    @property
    def rder_id(self):
        # type: ()->Text
        """
        委托柜台ID
        """
        return self["rder_id"]

    @rder_id.setter
    def rder_id(self, value):
        # type: (Text) -> None
        self["rder_id"] = value

    @property
    def x_ord_id(self):
        # type: ()->Text
        """
        委托交易所ID
        """
        return self["x_ord_id"]

    @x_ord_id.setter
    def x_ord_id(self, value):
        # type: (Text) -> None
        self["x_ord_id"] = value

    @property
    def symbol(self):
        # type: ()->Text
        """
        委托交易所ID
        """
        return self["symbol"]

    @symbol.setter
    def symbol(self, value):
        # type: (Text) -> None
        self["symbol"] = value

    @property
    def side(self):
        # type: ()->int
        """
        买卖方向，取值参考enum OrderSide
        """
        return self["side"]

    @side.setter
    def side(self, value):
        # type: (int) -> None
        self["side"] = value

    @property
    def position_effect(self):
        # type: ()->int
        """
        开平标志，取值参考enum PositionEffect
        """
        return self["position_effect"]

    @position_effect.setter
    def position_effect(self, value):
        # type: (int) -> None
        self["position_effect"] = value

    @property
    def position_side(self):
        # type: ()->int
        """
        持仓方向，取值参考enum PositionSide
        """
        return self["position_side"]

    @position_side.setter
    def position_side(self, value):
        # type: (int) -> None
        self["position_side"] = value

    @property
    def order_type(self):
        # type: ()->int
        """
        委托类型，取值参考enum OrderType
        """
        return self["order_type"]

    @order_type.setter
    def order_type(self, value):
        # type: (int) -> None
        self["order_type"] = value

    @property
    def order_duration(self):
        # type: ()->int
        """
        委托时间属性，取值参考enum OrderDuration
        """
        return self["order_duration"]

    @order_duration.setter
    def order_duration(self, value):
        # type: (int) -> None
        self["order_duration"] = value

    @property
    def order_qualifier(self):
        # type: ()->int
        """
        委托成交属性，取值参考enum OrderQualifier
        """
        return self["order_qualifier"]

    @order_qualifier.setter
    def order_qualifier(self, value):
        # type: (int) -> None
        self["order_qualifier"] = value

    @property
    def order_src(self):
        # type: ()->int
        """
        委托来源，取值参考enum OrderSrc
        """
        return self["order_src"]

    @order_src.setter
    def order_src(self, value):
        # type: (int) -> None
        self["order_src"] = value

    @property
    def status(self):
        # type: ()->int
        """
        委托状态，取值参考enum OrderStatus
        """
        return self["status"]

    @status.setter
    def status(self, value):
        # type: (int) -> None
        self["status"] = value

    @property
    def ord_rej_reason(self):
        # type: ()->int
        """
        委托拒绝原因，取值参考enum OrderRejectReason
        """
        return self["ord_rej_reason"]

    @ord_rej_reason.setter
    def ord_rej_reason(self, value):
        # type: (int) -> None
        self["ord_rej_reason"] = value

    @property
    def rd_rej_reason_detail(self):
        # type: ()->Text
        """
        委托拒绝原因描述
        """
        return self["rd_rej_reason_detail"]

    @rd_rej_reason_detail.setter
    def rd_rej_reason_detail(self, value):
        # type: (Text) -> None
        self["rd_rej_reason_detail"] = value

    @property
    def price(self):
        # type: ()->float
        """
        委托价格
        """
        return self["price"]

    @price.setter
    def price(self, value):
        # type: (float) -> None
        self["price"] = value

    @property
    def stop_price(self):
        # type: ()->float
        """
        委托止损/止盈触发价格
        """
        return self["stop_price"]

    @stop_price.setter
    def stop_price(self, value):
        # type: (float) -> None
        self["stop_price"] = value

    @property
    def order_style(self):
        # type: ()->int
        """
        委托风格，取值参考 enum OrderStyle
        """
        return self["order_style"]

    @order_style.setter
    def order_style(self, value):
        # type: (int) -> None
        self["order_style"] = value

    @property
    def volume(self):
        # type: ()->int
        """
        委托量
        """
        return self["volume"]

    @volume.setter
    def volume(self, value):
        # type: (int) -> None
        self["volume"] = value

    @property
    def value(self):
        # type: ()->float
        """
        委托额
        """
        return self["value"]

    @value.setter
    def value(self, value):
        # type: (float) -> None
        self["value"] = value

    @property
    def percent(self):
        # type: ()->float
        """
        委托百分比
        """
        return self["percent"]

    @percent.setter
    def percent(self, value):
        # type: (float) -> None
        self["percent"] = value

    @property
    def target_volume(self):
        # type: ()->int
        """
        委托目标量
        """
        return self["target_volume"]

    @target_volume.setter
    def target_volume(self, value):
        # type: (int) -> None
        self["target_volume"] = value

    @property
    def target_value(self):
        # type: ()->float
        """
        委托目标额
        """
        return self["target_value"]

    @target_value.setter
    def target_value(self, value):
        # type: (float) -> None
        self["target_value"] = value

    @property
    def target_percent(self):
        # type: ()->float
        """
        委托目标百分比
        """
        return self["target_percent"]

    @target_percent.setter
    def target_percent(self, value):
        # type: (float) -> None
        self["target_percent"] = value

    @property
    def filled_volume(self):
        # type: ()->int
        """
        已成量
        """
        return self["filled_volume"]

    @filled_volume.setter
    def filled_volume(self, value):
        # type: (int) -> None
        self["filled_volume"] = value

    @property
    def filled_vwap(self):
        # type: ()->float
        """
        已成均价
        """
        return self["filled_vwap"]

    @filled_vwap.setter
    def filled_vwap(self, value):
        # type: (float) -> None
        self["filled_vwap"] = value

    @property
    def filled_amount(self):
        # type: ()->float
        """
        已成金额
        """
        return self["filled_amount"]

    @filled_amount.setter
    def filled_amount(self, value):
        # type: (float) -> None
        self["filled_amount"] = value

    @property
    def filled_commission(self):
        # type: ()->float
        """
        已成手续费
        """
        return self["filled_commission"]

    @filled_commission.setter
    def filled_commission(self, value):
        # type: (float) -> None
        self["filled_commission"] = value

    @property
    def algo_name(self):
        # type: ()->Text
        """
        算法策略名
        """
        return self["algo_name"]

    @algo_name.setter
    def algo_name(self, value):
        # type: (Text) -> None
        self["algo_name"] = value

    @property
    def algo_param(self):
        # type: ()->Text
        """
        算法策略参数
        """
        return self["algo_param"]

    @algo_param.setter
    def algo_param(self, value):
        # type: (Text) -> None
        self["algo_param"] = value

    @property
    def algo_status(self):
        # type: ()->int
        """
        算法策略状态,仅作为AlgoOrder Pause请求入参，取值参考 enum AlgoOrderStatus
        """
        return self["algo_status"]

    @algo_status.setter
    def algo_status(self, value):
        # type: (int) -> None
        self["algo_status"] = value

    @property
    def algo_comment(self):
        # type: ()->Text
        """
        算法单备注
        """
        return self["algo_comment"]

    @algo_comment.setter
    def algo_comment(self, value):
        # type: (Text) -> None
        self["algo_comment"] = value

    @property
    def created_at(self):
        # type: ()->Optional[datetime]
        """
        委托创建时间
        """
        return self["created_at"]

    @created_at.setter
    def created_at(self, value):
        # type: (Optional[datetime]) -> None
        self["created_at"] = value

    @property
    def updated_at(self):
        # type: ()->Optional[datetime]
        """
        委托更新时间
        """
        return self["updated_at"]

    @updated_at.setter
    def updated_at(self, value):
        # type: (Optional[datetime]) -> None
        self["updated_at"] = value


class DictLikeOrder(dict):
    """
    A dict that allows for Order-like property access syntax.
    """

    _fields = {
        "strategy_id",  # 策略ID
        "account_id",  # 账号ID
        "account_name",  # 账户登录名
        "cl_ord_id",  # 委托客户端ID
        "order_id",  # 委托柜台ID
        "ex_ord_id",  # 委托交易所ID
        "algo_order_id",  # 算法母单ID
        "symbol",  # 标的代码
        "status",  # 委托状态，取值参考enum OrderStatus
        "side",  # 买卖方向，取值参考enum OrderSide
        "position_effect",  # 开平标志，取值参考enum PositionEffect
        "position_side",  # 持仓方向，取值参考enum PositionSide
        "order_type",  # 委托类型，取值参考enum OrderType
        "order_duration",  # 委托时间属性，取值参考enum OrderDuration
        "order_qualifier",  # 委托成交属性，取值参考enum OrderQualifier
        "order_business",  # 委托业务属性 取值参考 OrderBusiness
        "ord_rej_reason",  # 委托拒绝原因，取值参考enum OrderRejectReason
        "ord_rej_reason_detail",  # 委托拒绝原因描述
        "position_src",  # 头寸来源（系统字段）
        "volume",  # 委托量
        "price",  # 委托价格
        "trigger_type", # 条件委托触发方式，适用于CTP条件单
        "value",  # 委托额
        "percent",  # 委托百分比
        "target_volume",  # 委托目标量
        "target_value",  # 委托目标额
        "target_percent",  # 委托目标百分比
        "filled_volume",  # 已成量
        "filled_vwap",  # 已成均价
        "filled_amount",  # 已成金额
        "filled_commission",  # 已成手续费
        "created_at",  # 委托创建时间
        "updated_at",  # 委托更新时间
        "order_src",  # 委托来源，取值参考enum OrderSrc
        "stop_price",  # 委托止损/止盈触发价格
        "order_style",  # 委托风格，取值参考 enum OrderStyle
        "properties",  # 扩展字段
    }

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key not in self._fields:
            return
        return super().__setitem__(key, value)

    def __getattr__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        return super().__setitem__(name, value)

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return super().__repr__()


class DictLikeIndicator(dict):
    """
    A dict that allows for Indicator-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeIndicator, self).__str__()

    def __repr__(self):
        return super(DictLikeIndicator, self).__repr__()

    @property
    def account_id(self):
        # type: ()->Text
        """
        账号ID
        """
        return self["account_id"]

    @account_id.setter
    def account_id(self, value):
        # type: (Text) -> None
        self["account_id"] = value

    @property
    def pnl_ratio(self):
        # type: ()->float
        """
        累计收益率(pnl/cum_inout)
        """
        return self["pnl_ratio"]

    @pnl_ratio.setter
    def pnl_ratio(self, value):
        # type: (float) -> None
        self["pnl_ratio"] = value

    @property
    def pnl_ratio_annual(self):
        # type: ()->float
        """
        年化收益率
        """
        return self["pnl_ratio_annual"]

    @pnl_ratio_annual.setter
    def pnl_ratio_annual(self, value):
        # type: (float) -> None
        self["pnl_ratio_annual"] = value

    @property
    def sharp_ratio(self):
        # type: ()->float
        """
        夏普比率
        """
        return self["sharp_ratio"]

    @sharp_ratio.setter
    def sharp_ratio(self, value):
        # type: (float) -> None
        self["sharp_ratio"] = value

    @property
    def max_drawdown(self):
        # type: ()->float
        """
        最大回撤
        """
        return self["max_drawdown"]

    @max_drawdown.setter
    def max_drawdown(self, value):
        # type: (float) -> None
        self["max_drawdown"] = value

    @property
    def risk_ratio(self):
        # type: ()->float
        """
        风险比率
        """
        return self["risk_ratio"]

    @risk_ratio.setter
    def risk_ratio(self, value):
        # type: (float) -> None
        self["risk_ratio"] = value

    @property
    def open_count(self):
        # type: ()->int
        """
        开仓次数
        """
        return self["open_count"]

    @open_count.setter
    def open_count(self, value):
        # type: (int) -> None
        self["open_count"] = value

    @property
    def close_count(self):
        # type: ()->int
        """
        平仓次数
        """
        return self["close_count"]

    @close_count.setter
    def close_count(self, value):
        # type: (int) -> None
        self["close_count"] = value

    @property
    def win_count(self):
        # type: ()->int
        """
        盈利次数
        """
        return self["win_count"]

    @win_count.setter
    def win_count(self, value):
        # type: (int) -> None
        self["win_count"] = value

    @property
    def lose_count(self):
        # type: ()->int
        """
        亏损次数
        """
        return self["lose_count"]

    @lose_count.setter
    def lose_count(self, value):
        # type: (int) -> None
        self["lose_count"] = value

    @property
    def win_ratio(self):
        # type: ()->float
        """
        胜率
        """
        return self["win_ratio"]

    @win_ratio.setter
    def win_ratio(self, value):
        # type: (float) -> None
        self["win_ratio"] = value

    @property
    def calmar_ratio(self):
        # type: ()->float
        """
        卡玛比率
        """
        return self["calmar_ratio"]

    @calmar_ratio.setter
    def calmar_ratio(self, value):
        # type: (float) -> None
        self["calmar_ratio"] = value

    @property
    def created_at(self):
        # type: ()->Optional[datetime]
        """ """
        return self["created_at"]

    @created_at.setter
    def created_at(self, value):
        # type: (Optional[datetime]) -> None
        self["created_at"] = value

    @property
    def updated_at(self):
        # type: ()->Optional[datetime]
        """ """
        return self["updated_at"]

    @updated_at.setter
    def updated_at(self, value):
        # type: (Optional[datetime]) -> None
        self["updated_at"] = value


class DictLikeParameter(dict):
    """
    A dict that allows for Parameter-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeParameter, self).__str__()

    def __repr__(self):
        return super(DictLikeParameter, self).__repr__()

    @property
    def key(self):
        # type: ()->Text
        """ """
        return self["key"]

    @key.setter
    def key(self, value):
        # type: (Text) -> None
        self["key"] = value

    @property
    def value(self):
        # type: ()->float
        """ """
        return self["value"]

    @value.setter
    def value(self, value):
        # type: (float) -> None
        self["value"] = value

    @property
    def min(self):
        # type: ()->float
        """ """
        return self["min"]

    @min.setter
    def min(self, value):
        # type: (float) -> None
        self["min"] = value

    @property
    def max(self):
        # type: ()->float
        """ """
        return self["max"]

    @max.setter
    def max(self, value):
        # type: (float) -> None
        self["max"] = value

    @property
    def name(self):
        # type: ()->Text
        """ """
        return self["name"]

    @name.setter
    def name(self, value):
        # type: (Text) -> None
        self["name"] = value

    @property
    def intro(self):
        # type: ()->Text
        """ """
        return self["intro"]

    @intro.setter
    def intro(self, value):
        # type: (Text) -> None
        self["intro"] = value

    @property
    def group(self):
        # type: ()->Text
        """ """
        return self["group"]

    @group.setter
    def group(self, value):
        # type: (Text) -> None
        self["group"] = value

    @property
    def readonly(self):
        # type: ()->bool
        """ """
        return self["readonly"]

    @readonly.setter
    def readonly(self, value):
        # type: (bool) -> None
        self["readonly"] = value


class DictLikeAccountStatus(dict):
    """
    A dict that allows for AccountStatus-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeAccountStatus, self).__str__()

    def __repr__(self):
        return super(DictLikeAccountStatus, self).__repr__()

    @property
    def account_id(self):
        # type: ()->Text

        return self["account_id"]

    @account_id.setter
    def account_id(self, value):
        # type: (Text) -> None
        self["account_id"] = value

    @property
    def account_name(self):
        # type: ()->Text

        return self["account_name"]

    @account_name.setter
    def account_name(self, value):
        # type: (Text) -> None
        self["account_name"] = value

    @property
    def status(self):
        # type: ()->DictLikeConnectionStatus

        return self["status"]

    @status.setter
    def status(self, value):
        # type: (DictLikeConnectionStatus) -> None
        self["status"] = value


class DictLikeConnectionStatus(dict):
    """
    A dict that allows for ConnectionStatus-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeConnectionStatus, self).__str__()

    def __repr__(self):
        return super(DictLikeConnectionStatus, self).__repr__()

    @property
    def state(self):
        # type: ()->int

        return self["state"]

    @state.setter
    def state(self, value):
        # type: (int) -> None
        self["state"] = value

    @property
    def error(self):
        # type: ()->DictLikeError

        return self["error"]

    @error.setter
    def error(self, value):
        # type: (DictLikeError) -> None
        self["error"] = value


class DictLikeError(dict):
    """
    A dict that allows for Error-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeError, self).__str__()

    def __repr__(self):
        return super(DictLikeError, self).__repr__()

    @property
    def code(self):
        # type: ()->int

        return self["code"]

    @code.setter
    def code(self, value):
        # type: (int) -> None
        self["code"] = value

    @property
    def type(self):
        # type: ()->Text

        return self["type"]

    @type.setter
    def type(self, value):
        # type: (Text) -> None
        self["type"] = value

    @property
    def info(self):
        # type: ()->Text

        return self["info"]

    @info.setter
    def info(self, value):
        # type: (Text) -> None
        self["info"] = value


class DictLikeL2Order(dict):
    """
    A dict that allows for L2Order-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeL2Order, self).__str__()

    def __repr__(self):
        return super(DictLikeL2Order, self).__repr__()

    @property
    def symbol(self):
        # type: ()->Text
        """
        标的
        """
        return self["symbol"]

    @symbol.setter
    def symbol(self, value):
        # type: (Text) -> None
        self["symbol"] = value

    @property
    def side(self):
        # type: ()->Text
        """
        买卖方向，取值参考enum OrderSide
        """
        return self["side"]

    @side.setter
    def side(self, value):
        # type: (int) -> None
        self["side"] = value

    @property
    def price(self):
        # type: ()->float
        """
        委托价格
        """
        return self["price"]

    @price.setter
    def price(self, value):
        # type: (float) -> None
        self["price"] = value

    @property
    def volume(self):
        # type: ()->int
        """
        委托量
        """
        return self["volume"]

    @volume.setter
    def volume(self, value):
        # type: (int) -> None
        self["volume"] = value

    @property
    def order_type(self):
        # type: ()->Text
        """
        委托类型
        """
        return self["order_type"]

    @volume.setter
    def order_type(self, value):
        # type: (Text) -> None
        self["order_type"] = value

    @property
    def created_at(self):
        # type: ()->Optional[datetime]
        """
        逐笔委托创建时间
        """
        return self["created_at"]

    @created_at.setter
    def created_at(self, value):
        # type: (Optional[datetime]) -> None
        self["created_at"] = value


class DictLikeL2OrderQueue(dict):
    """
    A dict that allows for L2OrderQueue-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeL2OrderQueue, self).__str__()

    def __repr__(self):
        return super(DictLikeL2OrderQueue, self).__repr__()

    @property
    def symbol(self):
        # type: ()->Text
        """
        标的
        """
        return self["symbol"]

    @symbol.setter
    def symbol(self, value):
        # type: (Text) -> None
        self["symbol"] = value

    @property
    def side(self):
        # type: ()->Text
        """
        买卖方向，取值参考enum OrderSide
        """
        return self["side"]

    @side.setter
    def side(self, value):
        # type: (int) -> None
        self["side"] = value

    @property
    def price(self):
        # type: ()->float
        """
        委托价格
        """
        return self["price"]

    @price.setter
    def price(self, value):
        # type: (float) -> None
        self["price"] = value

    @property
    def volume(self):
        # type: ()->int
        """
        委托量
        """
        return self["volume"]

    @volume.setter
    def volume(self, value):
        # type: (int) -> None
        self["volume"] = value

    @property
    def total_orders(self):
        # type: ()->int
        """
        委托总个数
        """
        return self["total_orders"]

    @total_orders.setter
    def total_orders(self, value):
        # type: (int) -> None
        self["total_orders"] = value

    @property
    def queue_orders(self):
        # type: ()->int
        """
        委托量队列中元素个数
        """
        return self["queue_orders"]

    @queue_orders.setter
    def queue_orders(self, value):
        # type: (int) -> None
        self["queue_orders"] = value

    @property
    def queue_volumes(self):
        # type: ()->int
        """
        委托量队列
        """
        return self["queue_volumes"]

    @queue_volumes.setter
    def queue_volumes(self, value):
        # type: (int) -> None
        self["queue_volumes"] = value

    @property
    def created_at(self):
        # type: ()->Optional[datetime]
        """
        逐笔委托创建时间
        """
        return self["created_at"]

    @created_at.setter
    def created_at(self, value):
        # type: (Optional[datetime]) -> None
        self["created_at"] = value


class DictLikeDepth(dict):
    """交易深度数据，包含做市商和投资者的买卖报价"""

    _fields = {
        "symbol",  # 标的代码
        "points",  # 最大深度档位数, 股转(基础层、创新层)做市业务统一为10
        "bids_mm",  # 做市商买方报价列表（原始报价），每档报价的展开结构见报价字典
        "asks_mm",  # 做市商卖方报价列表（原始报价），每档报价的展开结构见报价字典
        "bids",  # 投资者买方报价列表，每档报价的展开结构见报价字典
        "asks",  # 投资者卖方报价列表，每档报价的展开结构见报价字典
        "bids_mm_mg",  # 做市商卖方报价列表（合并报价），每档报价的展开结构见报价字典
        "asks_mm_mg",  # 做市商卖方报价列表（合并报价），每档报价的展开结构见报价字典
        "created_at",  # 创建时间
        "properties",  # 扩展字段
    }

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key not in self._fields:
            return
        return super().__setitem__(key, value)

    def __getattr__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        return super().__setitem__(name, value)

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

class DictLikeOrderMM(dict):
    """做市委托对象"""

    _fields = {
        "strategy_id",  # 策略ID
        "account_id",  # 账号ID
        "account_name",  # 账号登录名
        "cl_ord_id",  # 委托客户端 ID，下单生成，固定不变（掘金维护，下单唯一标识）
        "order_id",  # 委托柜台 ID（系统字段，下单不会立刻生成，委托报到柜台才会生成）
        "ex_ord_id",  # 委托交易所 ID（系统字段，下单不会立刻生成，委托报到柜台才会生成）
        "symbol",  # 标的代码
        "order_business",  # 委托业务属性，取值参考OrderBusiness
        "ord_rej_reason",  # 委托拒绝原因，取值参考OrderRejectReason
        "ord_rej_reason_detail",  # 委托状态，取值参考OrderStatus，订单状态需要按实际可能调整
        "status",  # 委托状态，取值参考OrderStatus，订单状态需要按实际可能调整
        "buy_price",  # 报买价（做市报价）
        "buy_volume",  # 报买量（做市报价）
        "buy_filled_volume",  # buy_filled_volume
        "buy_cancelled_volume",  # 买已撤量（做市报价）
        "sell_price",  # 报卖价（做市报价）
        "sell_volume",  # 报卖量（做市报价）
        "sell_filled_volume",  # 卖成量（做市报价）
        "sell_cancelled_volume",  # 卖已撤量（做市报价）
        "created_at",  # 委托创建时间
        "updated_at",  # 委托更新时间
        "properties",  # 扩展字段
    }

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key not in self._fields:
            return
        return super().__setitem__(key, value)

    def __getattr__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        return super().__setitem__(name, value)

    def __str__(self):
        return super().__str__()

    def __repr__(self):
        return super().__repr__()
