#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
币安API错误码映射

此模块定义了与币安API兼容的错误码
"""

# 服务器或网络错误 (-1xxx)
SERVER_ERROR = -1000  # 未知错误
DISCONNECTED = -1001  # 与服务器断开连接
UNAUTHORIZED = -1002  # 未授权
TOO_MANY_REQUESTS = -1003  # 请求过多
SERVER_BUSY = -1004  # 服务器繁忙
TIMEOUT = -1005  # 超时
UNKNOWN_ORDER_COMPOSITION = -1006  # 未知的订单组合
UNEXPECTED_RESP = -1007  # 系统异常
INVALID_TIMESTAMP = -1021  # 无效的时间戳
INVALID_PARAM = -1022  # 无效的参数
INVALID_LISTEN_KEY = -1023  # 无效的listenKey

# 市场相关错误
UNKNOWN_SYMBOL = -1121  # 无效的交易对

# 请求错误 (-3xxx)
BAD_API_KEY_FMT = -3000  # 错误的API Key格式
INVALID_API_KEY = -3001  # 无效的API Key
INVALID_SIGNED_MSG = -3002  # 无效的签名
MALFORMED_MSG = -3003  # 格式错误
API_KEY_NOT_REQUIRED = -3004  # 请求中不需要API密钥
TOO_MANY_REQUESTS_IP = -3005  # IP请求频率超限
TOO_MANY_REQUESTS_WEIGHT = -3006  # 请求权重超限
NO_PERMISSION = -3007  # 无权限
TOO_MANY_REQUESTS_EMPTY = -3008  # 请求过多(服务器未响应时)

# 订单错误 (-2xxx)
NEW_ORDER_REJECTED = -2010  # 新订单被拒绝
CANCEL_REJECTED = -2011  # 取消订单被拒绝
CANCEL_ALL_FAIL = -2012  # 无法取消所有订单
NO_SUCH_ORDER = -2013  # 订单不存在
BAD_API_KEY_FMT_ORDER = -2014  # API密钥格式无效(下单)
INVALID_API_KEY_ORDER = -2015  # 无效的API KEY(下单)
UNKNOWN_ACCOUNT = -2016  # 未知账户
INSUFFICIENT_BALANCE = -2017  # 余额不足
SERVER_BUSY_ORDER = -2018  # 下单时服务器忙
INSUFFICIENT_ACCOUNT = -2019  # 账户不足(保证金不足)
ORDER_NOT_ALLOWED = -2020  # 不允许交易操作
MARKET_IS_CLOSED = -2021  # 市场已关闭
PRICE_QTY_EXCEED_HARD_LIMITS = -2022  # 价格*数量超过硬性上限
INSUFFICIENT_QUANTITY = -2023  # 数量不足
TOO_MANY_ORDERS = -2024  # 订单过多
ORDER_WOULD_TRIGGER_IMMEDIATELY = -2025  # 订单会立即触发
ORDER_ARCHIVED = -2026  # 订单已归档
CANCEL_RESTRICTED = -2027  # 订单因限制无法取消

# 过滤器失败 (-4xxx)
PRICE_FILTER = -4000  # 价格过滤器
PERCENT_PRICE = -4001  # 百分比价格
LOT_SIZE = -4002  # 订单量过滤器
MIN_NOTIONAL = -4003  # 最小名义值
ICEBERG_PARTS = -4004  # 分段订单
MARKET_LOT_SIZE = -4005  # 市价订单量
MAX_NUM_ORDERS = -4006  # 最大订单数
MAX_ALGO_ORDERS = -4007  # 最大算法订单数
MAX_NUM_ICEBERG_ORDERS = -4008  # 最大分段订单数
EXCHANGE_MAX_NUM_ORDERS = -4010  # 交易所最大订单数
EXCHANGE_MAX_ALGO_ORDERS = -4011  # 交易所最大算法订单数 