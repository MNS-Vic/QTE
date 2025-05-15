# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals

import getopt
import sys
import atexit
import os
from gm import __version__
from gm.csdk.c_sdk import py_gmi_set_version
from gm.enum import *
from gm.model.storage import Context
from gm.api._errors import GmError

# 基本api
from .basic import (
    set_token, set_mfp, get_version, subscribe, unsubscribe,
    current, current_price, get_strerror, schedule, run, set_parameter,
    add_parameter, log, set_serv_addr, stop,
    timer, timer_stop, set_serv_addr_v5, set_account_id,
    set_option,
)

# 两融api
from .credit import credit_get_borrowable_instruments_positions, credit_buying_on_collateral, \
    credit_repay_cash_by_selling_share, credit_get_cash, credit_buying_on_margin, credit_get_borrowable_instruments, \
    credit_get_collateral_instruments, credit_get_contracts, credit_repay_cash_directly, \
    credit_repay_share_by_buying_share, credit_repay_share_directly, credit_selling_on_collateral, credit_short_selling,\
    credit_collateral_in, credit_collateral_out

# IPO新股
from .ipo import ipo_buy, ipo_get_quota, ipo_get_lot_info, ipo_get_instruments, ipo_get_match_number

# 基金
from .fund import fund_buy, fund_etf_buy, fund_redemption, fund_subscribing, fund_etf_redemption

# 债券(含可转债)
from .bond import bond_reverse_repurchase_agreement, bond_convertible_put, bond_convertible_call, bond_convertible_put_cancel

# 数据查询api
from .query import (
    history_n, history, get_fundamentals, get_dividend, get_continuous_contracts, get_next_trading_date,
    get_previous_trading_date, get_trading_dates, get_concept, get_industry, get_constituents, get_history_constituents,
    get_history_instruments, get_instrumentinfos, get_instruments, get_sector, get_fundamentals_n,
    get_history_l2ticks, get_history_ticks_l2, get_history_l2bars, get_history_bars_l2, get_history_l2transactions,
    get_history_transaction_l2, get_history_l2orders, raw_func, get_history_l2orders_queue,
    get_varietyinfos, get_trading_times, option_get_symbols_by_exchange, option_get_symbols_by_in_at_out,
    option_get_delisted_dates, option_get_exercise_prices, get_expire_rest_days, bond_convertible_get_call_info,

    get_cash, get_position,
    universe_delete, universe_set, universe_get_names, universe_get_symbols,
)

# 交易api
from .trade import (
    algo_smart_reorder, option_covered_close, option_covered_open, option_exercise, option_preorder_sell_margin, option_preorder_valid_volume, order_target_volume, order_target_value, order_target_percent,
    order_volume, order_percent, order_value, order_batch,
    order_cancel_all, order_cancel, order_close_all,
    get_orders, get_unfinished_orders, get_execution_reports,
    algo_order, algo_order_batch, algo_order_cancel, algo_order_pause, get_algo_orders, get_algo_child_orders,
    option_exercise, option_covered_open, option_covered_close, option_preorder_valid_volume,
    option_preorder_sell_margin, algo_smart_reorder, algo_smart_reorder_cancel,
    get_orders_mm, get_unfinished_orders_mm, place_order_mm,
)

from .calc import (
    option_calculate_t, option_calculate_price, option_calculate_greeks, option_calculate_delta,
    option_calculate_vega, option_calculate_theta, option_calculate_rho, option_calculate_gamma,
    option_calculate_iv, option_calculate_hv, option_calculate_ivsurface,
)

from .ds_fund import (
    stk_get_industry_category, stk_get_industry_constituents, stk_get_symbol_industry,
    stk_get_index_constituents, stk_get_index_history_constituents, stk_get_dividend,
    stk_get_adj_factor, fut_get_continuous_contracts, fut_get_contract_info,
    fnd_get_adj_factor, fnd_get_dividend, fnd_get_split,
    stk_get_sector_category, stk_get_sector_constituents,
    stk_get_symbol_sector, stk_get_ration,
    stk_get_shareholder_num, stk_get_top_shareholder,
    stk_get_share_change, fut_get_transaction_ranking, fut_get_transaction_rankings,
    fut_get_warehouse_receipt, fnd_get_etf_constituents,
    fnd_get_portfolio, fnd_get_net_value,
    bnd_get_conversion_price, bnd_get_call_info,
    bnd_get_put_info, bnd_get_amount_change,
    stk_get_fundamentals_balance, stk_get_fundamentals_cashflow, stk_get_fundamentals_income,
    stk_get_fundamentals_balance_pt, stk_get_fundamentals_cashflow_pt, stk_get_fundamentals_income_pt,
    stk_get_finance_prime, stk_get_finance_prime_pt, stk_get_finance_deriv, stk_get_finance_deriv_pt,
    stk_get_daily_valuation, stk_get_daily_valuation_pt, stk_get_daily_mktvalue, stk_get_daily_mktvalue_pt,
    stk_get_daily_basic, stk_get_daily_basic_pt,

    stk_abnor_change_stocks,
    stk_abnor_change_detail,
    stk_quota_shszhk_infos,
    stk_hk_inst_holding_detail_info,
    stk_hk_inst_holding_info,
    stk_active_stock_top10_shszhk_info, stk_get_money_flow, stk_get_finance_audit, stk_get_finance_forecast,
    fnd_get_share, bnd_get_analysis,

    get_open_call_auction,
)
from .ds_instrument import (
    get_symbol_infos, get_symbols, get_history_symbol,
    get_trading_session, get_contract_expire_rest_days,
    get_trading_dates_by_year,

    get_previous_n_trading_dates,
    get_next_n_trading_dates,
)
from .trade_option import (
    option_comb, option_comb_by_comb_info,
    option_sep, option_sep_by_comb_pos,
    option_get_comb_info, option_get_comb_pos,
)

__all__ = [
    'order_target_volume', 'order_target_value', 'order_target_percent',
    'order_volume', 'order_percent', 'order_value', 'order_batch',
    'order_cancel_all', 'order_cancel', 'order_close_all',
    'get_orders', 'get_unfinished_orders', 'get_execution_reports',
    'algo_order', 'algo_order_batch', 'algo_order_cancel', 'algo_order_pause', 'get_algo_orders', 'get_algo_child_orders',

    'set_token', 'set_mfp', 'get_version', 'subscribe', 'unsubscribe',
    'current', 'current_price', 'get_strerror', 'schedule', 'run',
    'set_parameter', 'add_parameter', 'log', 'stop',
    'set_serv_addr_v5', 'set_account_id',

    'history_n', 'history', 'get_fundamentals', 'get_dividend',
    'get_continuous_contracts', 'get_next_trading_date',
    'get_previous_trading_date', 'get_trading_dates', 'get_concept',
    'get_industry', 'get_constituents', 'get_history_constituents',
    'get_history_instruments', 'get_instrumentinfos', 'get_fundamentals_n',
    'get_instruments', 'get_sector', 'set_serv_addr', 'get_history_l2ticks', 'get_history_ticks_l2',
    'get_history_l2bars', 'get_history_bars_l2', 'raw_func',
    'get_history_l2transactions', 'get_history_transaction_l2', 'get_history_l2orders', 'get_history_l2orders_queue',

    'credit_get_borrowable_instruments_positions', 'credit_buying_on_collateral',
    'credit_repay_cash_by_selling_share', 'credit_get_cash', 'credit_buying_on_margin', 'credit_get_borrowable_instruments',
    'credit_get_collateral_instruments', 'credit_get_contracts', 'credit_repay_cash_directly',
    'credit_repay_share_by_buying_share', 'credit_repay_share_directly', 'credit_selling_on_collateral',
    'credit_short_selling', 'credit_collateral_in', 'credit_collateral_out',

    'ipo_buy', 'ipo_get_quota', 'ipo_get_lot_info', 'ipo_get_instruments', 'ipo_get_match_number',

    'fund_buy', 'fund_etf_redemption', 'fund_subscribing', 'fund_redemption', 'fund_etf_buy',

    'bond_reverse_repurchase_agreement', 'bond_convertible_put', 'bond_convertible_call', 'bond_convertible_put_cancel',

    'timer', 'timer_stop', 'get_varietyinfos', 'get_trading_times', 'option_get_symbols_by_exchange',
    'option_get_symbols_by_in_at_out', 'option_get_delisted_dates', 'option_get_exercise_prices',
    'get_expire_rest_days', 'bond_convertible_get_call_info',
    'option_exercise', 'option_covered_open', 'option_covered_close', 'option_preorder_valid_volume',
    'option_preorder_sell_margin', 'algo_smart_reorder', 'algo_smart_reorder_cancel',

    'option_calculate_t', 'option_calculate_price', 'option_calculate_greeks', 'option_calculate_delta',
    'option_calculate_vega', 'option_calculate_theta', 'option_calculate_rho', 'option_calculate_gamma',
    'option_calculate_iv', 'option_calculate_hv', 'option_calculate_ivsurface',

    'Context',

    'ExecType_Unknown',
    'ExecType_New',
    'ExecType_DoneForDay',
    'ExecType_Canceled',
    'ExecType_PendingCancel',
    'ExecType_Stopped',
    'ExecType_Rejected',
    'ExecType_Suspended',
    'ExecType_PendingNew',
    'ExecType_Calculated',
    'ExecType_Expired',
    'ExecType_Restated',
    'ExecType_PendingReplace',
    'ExecType_Trade',
    'ExecType_TradeCorrect',
    'ExecType_TradeCancel',
    'ExecType_OrderStatus',
    'ExecType_CancelRejected',
    'OrderStatus_Unknown',
    'OrderStatus_New',
    'OrderStatus_PartiallyFilled',
    'OrderStatus_Filled',
    'OrderStatus_DoneForDay',
    'OrderStatus_Canceled',
    'OrderStatus_PendingCancel',
    'OrderStatus_Stopped',
    'OrderStatus_Rejected',
    'OrderStatus_Suspended',
    'OrderStatus_PendingNew',
    'OrderStatus_Calculated',
    'OrderStatus_Expired',
    'OrderStatus_AcceptedForBidding',
    'OrderStatus_PendingReplace',
    'OrderRejectReason_Unknown',
    'OrderRejectReason_RiskRuleCheckFailed',
    'OrderRejectReason_NoEnoughCash',
    'OrderRejectReason_NoEnoughPosition',
    'OrderRejectReason_IllegalAccountId',
    'OrderRejectReason_IllegalStrategyId',
    'OrderRejectReason_IllegalSymbol',
    'OrderRejectReason_IllegalVolume',
    'OrderRejectReason_IllegalPrice',
    'OrderRejectReason_AccountDisabled',
    'OrderRejectReason_AccountDisconnected',
    'OrderRejectReason_AccountLoggedout',
    'OrderRejectReason_NotInTradingSession',
    'OrderRejectReason_OrderTypeNotSupported',
    'OrderRejectReason_Throttle',
    'OrderRejectReason_SymbolSusppended',
    'OrderRejectReason_Internal',
    'CancelOrderRejectReason_OrderFinalized',
    'CancelOrderRejectReason_UnknownOrder',
    'CancelOrderRejectReason_BrokerOption',
    'CancelOrderRejectReason_AlreadyInPendingCancel',
    'OrderSide_Unknown',
    'OrderSide_Buy',
    'OrderSide_Sell',

    'OrderType_Unknown',
    'OrderType_Limit',
    'OrderType_Market',
    'OrderType_Stop',
    'OrderType_AHT',
    'OrderType_Limit_FAK',
    'OrderType_Limit_FOK',
    'OrderType_Market_BOC',
    'OrderType_Market_BOP',
    'OrderType_Market_FAK',
    'OrderType_Market_FOK',
    'OrderType_Market_B5TC',
    'OrderType_Market_B5TL',
    'OrderType_Market_FAL',
    'OrderType_Market_BOPC',
    'OrderType_Market_BOPL',

    'OrderDuration_Unknown',
    'OrderDuration_FAK',
    'OrderDuration_FOK',
    'OrderDuration_GFD',
    'OrderDuration_GFS',
    'OrderDuration_GTD',
    'OrderDuration_GTC',
    'OrderDuration_GFA',
    'OrderDuration_AHT',
    'OrderQualifier_Unknown',
    'OrderQualifier_BOC',
    'OrderQualifier_BOP',
    'OrderQualifier_B5TC',
    'OrderQualifier_B5TL',
    'OrderStyle_Unknown',
    'OrderStyle_Volume',
    'OrderStyle_Value',
    'OrderStyle_Percent',
    'OrderStyle_TargetVolume',
    'OrderStyle_TargetValue',
    'OrderStyle_TargetPercent',
    'PositionSide_Unknown',
    'PositionSide_Long',
    'PositionSide_Short',
    'PositionEffect_Unknown',
    'PositionEffect_Open',
    'PositionEffect_Close',
    'PositionEffect_CloseToday',
    'PositionEffect_CloseYesterday',
    'CashPositionChangeReason_Unknown',
    'CashPositionChangeReason_Trade',
    'CashPositionChangeReason_Inout',
    'MODE_LIVE',
    'MODE_BACKTEST',
    'ADJUST_NONE',
    'ADJUST_PREV',
    'ADJUST_POST',
    'SEC_TYPE_STOCK',
    'SEC_TYPE_FUND',
    'SEC_TYPE_INDEX',
    'SEC_TYPE_FUTURE',
    'SEC_TYPE_OPTION',
    'SEC_TYPE_CONFUTURE',
    'SEC_TYPE_BOND',
    'SEC_TYPE_BOND_CONVERTIBLE',
    'PositionSrc_Unknown',
    'PositionSrc_L1',
    'PositionSrc_L2',

    'OrderBusiness_NORMAL',
    'OrderBusiness_STOCK_BUY',
    'OrderBusiness_STOCK_SELL',
    'OrderBusiness_FUTURE_BUY_OPEN',
    'OrderBusiness_FUTURE_SELL_CLOSE',
    'OrderBusiness_FUTURE_SELL_CLOSE_TODAY',
    'OrderBusiness_FUTURE_SELL_CLOSE_YESTERDAY',
    'OrderBusiness_FUTURE_SELL_OPEN',
    'OrderBusiness_FUTURE_BUY_CLOSE',
    'OrderBusiness_FUTURE_BUY_CLOSE_TODAY',
    'OrderBusiness_FUTURE_BUY_CLOSE_YESTERDAY',
    'OrderBusiness_IPO_BUY',
    'OrderBusiness_CREDIT_BOM',
    'OrderBusiness_CREDIT_SS',
    'OrderBusiness_CREDIT_RSBBS',
    'OrderBusiness_CREDIT_RCBSS',
    'OrderBusiness_CREDIT_DRS',
    'OrderBusiness_CREDIT_DRC',
    'OrderBusiness_CREDIT_CPOM',
    'OrderBusiness_CREDIT_CPOSS',
    'OrderBusiness_CREDIT_BOC',
    'OrderBusiness_CREDIT_SOC',
    'OrderBusiness_CREDIT_CI',
    'OrderBusiness_CREDIT_CO',
    'OrderBusiness_CREDIT_BOM_VIP',
    'OrderBusiness_CREDIT_SS_VIP',
    'OrderBusiness_CREDIT_RSBBS_VIP',
    'OrderBusiness_CREDIT_RCBSS_VIP',
    'OrderBusiness_CREDIT_DRS_VIP',
    'OrderBusiness_CREDIT_DRC_VIP',
    'OrderBusiness_ETF_BUY',
    'OrderBusiness_ETF_RED',
    'OrderBusiness_FUND_SUB',
    'OrderBusiness_FUND_BUY',
    'OrderBusiness_FUND_RED',
    'OrderBusiness_FUND_CONVERT',
    'OrderBusiness_FUND_SPLIT',
    'OrderBusiness_FUND_MERGE',
    'OrderBusiness_BOND_RRP',
    'OrderBusiness_BOND_CONVERTIBLE_BUY',
    'OrderBusiness_BOND_CONVERTIBLE_CALL',
    'OrderBusiness_BOND_CONVERTIBLE_PUT',
    'OrderBusiness_BOND_CONVERTIBLE_PUT_CANCEL',
    "State_CONNECTING",
    "State_CONNECTED",
    "State_LOGGEDIN",
    "State_DISCONNECTING",
    "State_DISCONNECTED",
    "State_ERROR",

    "OrderTriggerType_Unknown",
    "OrderTriggerType_LastPriceGreaterThanStopPrice",
    "OrderTriggerType_LastPriceGreaterEqualStopPrice",
    "OrderTriggerType_LastPriceLessThanStopPrice",
    "OrderTriggerType_LastPriceLessEqualStopPrice",
    "OrderTriggerType_AskPriceGreaterThanStopPrice",
    "OrderTriggerType_AskPriceGreaterEqualStopPrice",
    "OrderTriggerType_AskPriceLessThanStopPrice",
    "OrderTriggerType_AskPriceLessEqualStopPrice",
    "OrderTriggerType_BidPriceGreaterThanStopPrice",
    "OrderTriggerType_BidPriceGreaterEqualStopPrice",
    "OrderTriggerType_BidPriceLessThanStopPrice",
    "OrderTriggerType_BidPriceLessEqualStopPrice",

    'AlgoOrderStatus_Unknown', 'AlgoOrderStatus_Resume', 'AlgoOrderStatus_Pause',
    'AlgoOrderStatus_PauseAndCancelSubOrders',

    'stk_get_industry_category', 'stk_get_industry_constituents', 'stk_get_symbol_industry',
    'stk_get_index_constituents', 'stk_get_index_history_constituents', 'stk_get_dividend',
    'stk_get_adj_factor', 'fut_get_continuous_contracts', 'fut_get_contract_info',
    'fnd_get_adj_factor', 'fnd_get_dividend', 'fnd_get_split',

    'stk_get_sector_category', 'stk_get_sector_constituents',
    'stk_get_symbol_sector', 'stk_get_ration',
    'stk_get_shareholder_num', 'stk_get_top_shareholder',
    'stk_get_share_change', 'fut_get_transaction_ranking', 'fut_get_transaction_rankings',
    'fut_get_warehouse_receipt', 'fnd_get_etf_constituents',
    'fnd_get_portfolio', 'fnd_get_net_value',
    'bnd_get_conversion_price', 'bnd_get_call_info',
    'bnd_get_put_info', 'bnd_get_amount_change',

    'stk_get_fundamentals_balance', 'stk_get_fundamentals_cashflow', 'stk_get_fundamentals_income',
    'stk_get_fundamentals_balance_pt', 'stk_get_fundamentals_cashflow_pt', 'stk_get_fundamentals_income_pt',

    'stk_get_finance_prime', 'stk_get_finance_prime_pt', 'stk_get_finance_deriv', 'stk_get_finance_deriv_pt',
    'stk_get_daily_valuation', 'stk_get_daily_valuation_pt', 'stk_get_daily_mktvalue', 'stk_get_daily_mktvalue_pt',
    'stk_get_daily_basic', 'stk_get_daily_basic_pt',

    'get_symbol_infos', 'get_symbols', 'get_history_symbol',
    'get_trading_dates_by_year',
    'get_trading_session', 'get_contract_expire_rest_days',

    'option_comb', 'option_comb_by_comb_info',
    'option_sep', 'option_sep_by_comb_pos',
    'option_get_comb_info', 'option_get_comb_pos',

    'GmError', 'set_option',

    'get_orders_mm', 'get_unfinished_orders_mm', 'place_order_mm',

    'stk_abnor_change_stocks',
    'stk_abnor_change_detail',
    'stk_quota_shszhk_infos',
    'stk_hk_inst_holding_detail_info',
    'stk_hk_inst_holding_info',
    'stk_active_stock_top10_shszhk_info',
    'get_previous_n_trading_dates',
    'get_next_n_trading_dates',

    'stk_get_money_flow', 'stk_get_finance_audit', 'stk_get_finance_forecast',
    'fnd_get_share',
    'bnd_get_analysis',

    'get_cash', 'get_position',
    'universe_delete', 'universe_set', 'universe_get_names', 'universe_get_symbols',

    'get_open_call_auction',
]

def exit_handler():
    os._exit(0)

atexit.register(exit_handler)

try:
    if sys.version_info.major < 3:
        __all__ = [str(item) for item in __all__]
    ver_info = sys.version_info
    sdk_lang = "python{}.{}".format(ver_info.major, ver_info.minor)
    sdk_version = __version__.__version__

    py_gmi_set_version(sdk_version, sdk_lang)

    command_argv = sys.argv[1:]
    options, args = getopt.getopt(command_argv, None,
                                  ['strategy_id=', 'filename=',
                                   'mode=', 'token=', 'apitoken=',
                                   'backtest_start_time=',
                                   'backtest_end_time=',
                                   'backtest_initial_cash=',
                                   'backtest_transaction_ratio=',
                                   'backtest_commission_ratio=',
                                   'backtest_slippage_ratio=',
                                   'backtest_adjust=',
                                   'backtest_check_cache=',
                                   'serv_addr=',
                                   'port=',  # 用于pycharm的python console时会额外传入port参数
                                   ])

    for option, value in options:
        if option == '--serv_addr' and value:
            set_serv_addr(value)
            break
except BaseException as e:
    pass
