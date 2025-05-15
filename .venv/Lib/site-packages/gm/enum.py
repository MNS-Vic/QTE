# coding=utf8
from __future__ import print_function, absolute_import, unicode_literals

ExecType_Unknown = 0
ExecType_New = 1  # 已报
ExecType_DoneForDay = 4  #
ExecType_Canceled = 5  # 已撤销
ExecType_PendingCancel = 6  # 待撤销
ExecType_Stopped = 7  #
ExecType_Rejected = 8  # 已拒绝
ExecType_Suspended = 9  # 挂起
ExecType_PendingNew = 10  # 待报
ExecType_Calculated = 11  #
ExecType_Expired = 12  # 过期
ExecType_Restated = 13  #
ExecType_PendingReplace = 14  #
ExecType_Trade = 15  # 成交
ExecType_TradeCorrect = 16  #
ExecType_TradeCancel = 17  #
ExecType_OrderStatus = 18  # 委托状态
ExecType_CancelRejected = 19  # 撤单被拒绝

OrderStatus_Unknown = 0
OrderStatus_New = 1  # 已报
OrderStatus_PartiallyFilled = 2  # 部成
OrderStatus_Filled = 3  # 已成
OrderStatus_DoneForDay = 4  #
OrderStatus_Canceled = 5  # 已撤
OrderStatus_PendingCancel = 6  # 待撤
OrderStatus_Stopped = 7  #
OrderStatus_Rejected = 8  # 已拒绝
OrderStatus_Suspended = 9  # 挂起
OrderStatus_PendingNew = 10  # 待报
OrderStatus_Calculated = 11  #
OrderStatus_Expired = 12  # 已过期
OrderStatus_AcceptedForBidding = 13  #
OrderStatus_PendingReplace = 14  #

OrderRejectReason_Unknown = 0  # 未知原因
OrderRejectReason_RiskRuleCheckFailed = 1  # 不符合风控规则
OrderRejectReason_NoEnoughCash = 2  # 资金不足
OrderRejectReason_NoEnoughPosition = 3  # 仓位不足
OrderRejectReason_IllegalAccountId = 4  # 非法账户ID
OrderRejectReason_IllegalStrategyId = 5  # 非法策略ID
OrderRejectReason_IllegalSymbol = 6  # 非法交易标的
OrderRejectReason_IllegalVolume = 7  # 非法委托量
OrderRejectReason_IllegalPrice = 8  # 非法委托价
OrderRejectReason_AccountDisabled = 10  # 交易账号被禁止交易
OrderRejectReason_AccountDisconnected = 11  # 交易账号未连接
OrderRejectReason_AccountLoggedout = 12  # 交易账号未登录
OrderRejectReason_NotInTradingSession = 13  # 非交易时段
OrderRejectReason_OrderTypeNotSupported = 14  # 委托类型不支持
OrderRejectReason_Throttle = 15  # 流控限制
OrderRejectReason_SymbolSusppended = 16  # 交易代码停牌
OrderRejectReason_Internal = 999  # 内部错误

CancelOrderRejectReason_OrderFinalized = 101  # 委托已完成
CancelOrderRejectReason_UnknownOrder = 102  # 未知委托
CancelOrderRejectReason_BrokerOption = 103  # 柜台设置
CancelOrderRejectReason_AlreadyInPendingCancel = 104  # 委托撤销中

OrderSide_Unknown = 0
OrderSide_Buy = 1  # 买入
OrderSide_Sell = 2  # 卖出

OrderType_Unknown = 0
OrderType_Limit = 1  # 限价委托
OrderType_Market = 2  # 市价委托
OrderType_Stop = 3  # 止损止盈委托
OrderType_AHT = 4 # 盘后定价交易
OrderType_Limit_FAK = 10 # 限价FAK
OrderType_Limit_FOK = 11 # 限价FOK
OrderType_Market_BOC = 20 # 市价对方最优价格
OrderType_Market_BOP = 21 # 市价己方最优价格
OrderType_Market_FAK = 22 # 市价即时成交剩余撤销
OrderType_Market_FOK = 23 # 市价即时全额成交或撤销
OrderType_Market_B5TC = 24 # 市价最优五档剩余撤销
OrderType_Market_B5TL = 25 # 市价最优五档剩余转限价
OrderType_Market_FAL = 26 # 市价剩余转限价
OrderType_Market_BOPC = 27 # 市价最优价成交剩余撤销
OrderType_Market_BOPL = 28 # 市价最优价成交剩余撤销


OrderDuration_Unknown = 0
OrderDuration_FAK = 1  # 即时成交剩余撤销(fill and kill)
OrderDuration_FOK = 2  # 即时全额成交或撤销(fill or kill)
OrderDuration_GFD = 3  # 当日有效(good for day)
OrderDuration_GFS = 4  # 本节有效(good for section)
OrderDuration_GTD = 5  # 指定日期前有效(goodltilldate)
OrderDuration_GTC = 6  # 撤销前有效(goodtillcancel)
OrderDuration_GFA = 7  # 集合竞价前有效(good for auction)
OrderDuration_AHT = 8  # 盘后定价交易(after hour trading)


OrderQualifier_Unknown = 0
OrderQualifier_BOC = 1  # 对方最优价格(best of counterparty)
OrderQualifier_BOP = 2  # 己方最优价格(best of party)
OrderQualifier_B5TC = 3  # 最优五档剩余撤销(best 5 then cancel)
OrderQualifier_B5TL = 4  # 最优五档剩余转限价(best 5 then limit)

OrderStyle_Unknown = 0
OrderStyle_Volume = 1
OrderStyle_Value = 2
OrderStyle_Percent = 3
OrderStyle_TargetVolume = 4
OrderStyle_TargetValue = 5
OrderStyle_TargetPercent = 6

PositionSide_Unknown = 0
PositionSide_Long = 1  # 多方向
PositionSide_Short = 2  # 空方向

PositionEffect_Unknown = 0
PositionEffect_Open = 1  # 开仓
PositionEffect_Close = 2  # 平仓, 具体语义取决于对应的交易所
PositionEffect_CloseToday = 3  # 平今仓
PositionEffect_CloseYesterday = 4  # 平昨仓

CashPositionChangeReason_Unknown = 0
CashPositionChangeReason_Trade = 1  # 交易
CashPositionChangeReason_Inout = 2  # 出入金 / 出入持仓
CashPositionChangeReason_Dividend = 3  # 分红送股
CashPositionChangeReason_Delivery = 4  # 交割合约

AlgoOrderStatus_Unknown = 0
AlgoOrderStatus_Resume = 1  # 恢复母单
AlgoOrderStatus_Pause = 2  # 暂停母单
AlgoOrderStatus_PauseAndCancelSubOrders = 3  # 暂算母单并撤子单

MODE_UNKNOWN = 0
MODE_LIVE = 1
MODE_BACKTEST = 2

ADJUST_NONE = 0
ADJUST_PREV = 1
ADJUST_POST = 2

SEC_TYPE_STOCK = 1  # 股票
SEC_TYPE_FUND = 2  # 基金
SEC_TYPE_INDEX = 3  # 指数
SEC_TYPE_FUTURE = 4  # 期货
SEC_TYPE_OPTION = 5  # 期权
SEC_TYPE_CREDIT = 6  # 信用交易
SEC_TYPE_BOND = 7  # 债券
SEC_TYPE_BOND_CONVERTIBLE = 8  # 可转债
SEC_TYPE_CONFUTURE = 10  # 虚拟合约

PositionSrc_Unknown = 0
PositionSrc_L1 = 1  # 普通券
PositionSrc_L2 = 2  # 专项券

OrderBusiness_NORMAL = 0  # 普通交易。默认值为空，以保持向前兼容
# 股票交易
OrderBusiness_STOCK_BUY = 1  # 股票买入
OrderBusiness_STOCK_SELL = 2  # 股票卖出
OrderBusiness_MARKET_MAKING = 6  # 做市交易

# 期货交易
OrderBusiness_FUTURE_BUY_OPEN = 10  # 买入开仓
OrderBusiness_FUTURE_SELL_CLOSE = 11  # 卖出平仓
OrderBusiness_FUTURE_SELL_CLOSE_TODAY = 12  # 卖出平仓，优先平今
OrderBusiness_FUTURE_SELL_CLOSE_YESTERDAY = 13  # 卖出平仓，优先平昨
OrderBusiness_FUTURE_SELL_OPEN = 14  # 卖出开仓
OrderBusiness_FUTURE_BUY_CLOSE = 15  # 买入平仓
OrderBusiness_FUTURE_BUY_CLOSE_TODAY = 16  # 买入平仓，优先平今
OrderBusiness_FUTURE_BUY_CLOSE_YESTERDAY = 17  # 买入平仓，优先平昨

# 新股交易(IPO)
OrderBusiness_IPO_BUY = 100  # 新股申购

# 信用交易
OrderBusiness_CREDIT_BOM = 200  # 融资买入(buying on margin)
OrderBusiness_CREDIT_SS = 201  # 融券卖出(short selling)
OrderBusiness_CREDIT_RSBBS = 202  # 买券还券(repay share by buying share)
OrderBusiness_CREDIT_RCBSS = 203  # 卖券还款(repay cash by selling share)
OrderBusiness_CREDIT_DRS = 204  # 直接还券(directly repay share)
# 直接还款(directly repay cash) （直接还款有专有接口，柜台也有专用功能号，不通过委托请求；此枚举定义为兼容部分柜台(顶点），其在查询委托时会包含直接还款的记录）
OrderBusiness_CREDIT_DRC = 211
OrderBusiness_CREDIT_CPOM = 205  # 融资平仓(close position on margin)
OrderBusiness_CREDIT_CPOSS = 206  # 融券平仓(close position on short selling)
OrderBusiness_CREDIT_BOC = 207  # 担保品买入(buying on collateral)
OrderBusiness_CREDIT_SOC = 208  # 担保品卖出(selling on collateral)
OrderBusiness_CREDIT_CI = 209  # 担保品转入(collateral in)
OrderBusiness_CREDIT_CO = 210  # 担保品转出(collateral out)
OrderBusiness_CREDIT_BOM_VIP = 212  # 专项融资买入(buying on margin for vip)
OrderBusiness_CREDIT_SS_VIP = 213  # 专项融券卖出(short selling for vip)
# 专项买券还券(repay share by buying share for vip)
OrderBusiness_CREDIT_RSBBS_VIP = 214
# 专项卖券还款(repay cash by selling share for vip)
OrderBusiness_CREDIT_RCBSS_VIP = 215
OrderBusiness_CREDIT_DRS_VIP = 216  # 专项直接还券(directly repay share for vip)
# 专项直接还款(directly repay cash for vip) （直接还款有专有接口，柜台也有专用功能号，不通过委托请求；此枚举定义为兼容部分柜台(顶点），其在查询委托时会包含直接还款的记录）
OrderBusiness_CREDIT_DRC_VIP = 217

# 基金申赎
OrderBusiness_ETF_BUY = 301  # ETF申购(purchase)
OrderBusiness_ETF_RED = 302  # ETF赎回(redemption)
OrderBusiness_FUND_SUB = 303  # 基金认购(subscribing)
OrderBusiness_FUND_BUY = 304  # 基金申购(purchase)
OrderBusiness_FUND_RED = 305  # 基金赎回(redemption)
OrderBusiness_FUND_CONVERT = 306  # 基金转换(convert)
OrderBusiness_FUND_SPLIT = 307  # 基金分拆(split)
OrderBusiness_FUND_MERGE = 308  # 基金合并(merge)

# 债券交易
# 债券逆回购(reverse repurchase agreement (RRP) or reverse repo)
OrderBusiness_BOND_RRP = 400
OrderBusiness_BOND_CONVERTIBLE_BUY = 401  # 可转债申购(purchase)
OrderBusiness_BOND_CONVERTIBLE_CALL = 402  # 可转债转股
OrderBusiness_BOND_CONVERTIBLE_PUT = 403  # 可转债回售
OrderBusiness_BOND_CONVERTIBLE_PUT_CANCEL = 404  # 可转债回售撤销

#账号连接状态
State_CONNECTING = 1                     # 连接中
State_CONNECTED = 2                      # 已连接
State_LOGGEDIN = 3                       # 已登录
State_DISCONNECTING = 4                  # 断开中
State_DISCONNECTED = 5                   # 已断开
State_ERROR = 6                          # 错误

# 期货条件单触发方式
OrderTriggerType_Unknown = 0        # 普通单
OrderTriggerType_LastPriceGreaterThanStopPrice = 1        # 条件单，触发条件：最新价大于条件价
OrderTriggerType_LastPriceGreaterEqualStopPrice = 2        # 条件单，触发条件：最新价大于等于条件价
OrderTriggerType_LastPriceLessThanStopPrice = 3        # 条件单，触发条件：最新价小于条件价
OrderTriggerType_LastPriceLessEqualStopPrice = 4        # 条件单，触发条件：最新价小于等于条件价
OrderTriggerType_AskPriceGreaterThanStopPrice = 5        # 条件单，触发条件：卖一价大于条件价
OrderTriggerType_AskPriceGreaterEqualStopPrice = 6        # 条件单，触发条件：卖一价大于等于条件价
OrderTriggerType_AskPriceLessThanStopPrice = 7        # 条件单，触发条件：卖一价小于条件价
OrderTriggerType_AskPriceLessEqualStopPrice = 8        # 条件单，触发条件：卖一价小于等于条件价
OrderTriggerType_BidPriceGreaterThanStopPrice = 9        # 条件单，触发条件：买一价大于条件价
OrderTriggerType_BidPriceGreaterEqualStopPrice = 10        # 条件单，触发条件：买一价大于等于条件价
OrderTriggerType_BidPriceLessThanStopPrice = 11        # 条件单，触发条件：买一价小于条件价
OrderTriggerType_BidPriceLessEqualStopPrice = 12        # 条件单，触发条件：买一价小于等于条件价
