# 通用错误 1000～1099
SUCCESS                             = 0       # "成功"
ERR_INVALID_TOKEN                   = 1000    # "错误或无效的token"
ERR_CONNECT_TERM_SERV               = 1001    # "无法连接到终端服务"
ERR_CONNECT_HISTORY_SERV            = 1002    # "无法连接到历史行情服务"
ERR_QUERY_SERVER_ADDR_ERROR         = 1010    # "无法获取掘金服务器地址列表"
ERR_PARSE_MASSAGE                   = 1011    # "消息包解析错误"
ERR_PARSE_NETWORK_MASSAGE           = 1012    # "网络消息包解析错误"
ERR_CALL_TRADE_SERVICE              = 1013    # "交易服务调用错误"
ERR_CALL_HISTORY_SERVICE            = 1014    # "历史行情服务调用错误"
ERR_CALL_STRATEGY_SERIVCE           = 1015    # "策略服务调用错误"
ERR_CALL_RTCONFIG_SERIVCE           = 1016    # "动态参数调用错误"
ERR_CALL_FUNDMENTAL_SERVICE         = 1017    # "基本面数据服务调用错误"
ERR_CALL_BACKTEST_SERVICE           = 1018    # "回测服务调用错误"
ERR_CALL_TRADEGW_SERIVCE            = 1019    # "交易网关服务调用错误"
ERR_INVALID_ACCOUNT_ID              = 1020    # "无效的ACCOUNT_ID"
ERR_INVALID_DATE                    = 1021    # "非法日期格式"
ERR_TIMEOUT                         = 1022    # "执行超时"
ERR_TOO_MANY_REQUESTS               = 1023    # "执行过于频繁，服务拒绝请求"
ERR_GET_ORGCODE                     = 1024    # "获取orgcode错误"
ERR_CONNECT_AUTH_SERV               = 1025    # "无法连接到认证服务"
ERR_UPDATE_ENTOKEN                  = 1026    # "更新令牌错误"
ERR_INVALID_PAPAM_INPUT             = 1027    # "输入参数错误"

# 交易部分 1100～1199
ERR_TD_LIVE_CONNECT                 = 1100    # "交易消息服务连接失败"
ERR_TD_LIVE_CONNECT_LOST            = 1101    # "交易消息服务断开"

# 数据部分 1200～1299
ERR_MD_LIVE_CONNECT                 = 1200    # "实时行情服务连接失败"
ERR_MD_LIVE_CONNECT_LOST            = 1201    # "实时行情服务连接断开"
ERR_MD_LIVE_SUBSCRIBE_FAIL          = 1202    # "订阅实时行情失败"

# 回测部分 1300~1399
ERR_BT_BEGIN                        = 1300    # "初始化回测失败，可能是终端未启动或无法连接到终端"
ERR_BT_INVALID_TIMESPAN             = 1301    # "回测时间区间错误"
ERR_BT_READ_CACHE_ERROR             = 1302    # "回测读取缓存数据错误"
ERR_BT_WRITE_CACHE_ERROR            = 1303    # "回测写入缓存数据错误"


error_dict = {
    ERR_INVALID_TOKEN:              "错误或无效的token",
    ERR_CONNECT_TERM_SERV:          "无法连接到终端服务",
    ERR_CONNECT_HISTORY_SERV:       "无法连接到历史行情服务",
    ERR_QUERY_SERVER_ADDR_ERROR:    "无法获取掘金服务器地址列表",
    ERR_PARSE_MASSAGE:              "消息包解析错误",
    ERR_PARSE_NETWORK_MASSAGE:      "网络消息包解析错误",
    ERR_CALL_TRADE_SERVICE:         "交易服务调用错误",
    ERR_CALL_HISTORY_SERVICE:       "历史行情服务调用错误",
    ERR_CALL_STRATEGY_SERIVCE:      "策略服务调用错误",
    ERR_CALL_RTCONFIG_SERIVCE:      "动态参数调用错误",
    ERR_CALL_FUNDMENTAL_SERVICE:    "基本面数据服务调用错误",
    ERR_CALL_BACKTEST_SERVICE:      "回测服务调用错误",
    ERR_CALL_TRADEGW_SERIVCE:       "交易网关服务调用错误",
    ERR_INVALID_ACCOUNT_ID:         "无效的ACCOUNT_ID",
    ERR_INVALID_DATE:               "非法日期格式",
    ERR_TIMEOUT:                    "执行超时",
    ERR_TOO_MANY_REQUESTS:          "执行过于频繁，服务拒绝请求",
    ERR_GET_ORGCODE:                "获取orgcode错误",
    ERR_CONNECT_AUTH_SERV:          "无法连接到认证服务",
    ERR_UPDATE_ENTOKEN:             "更新令牌错误",
    ERR_INVALID_PAPAM_INPUT:        "输入参数错误",

    ERR_TD_LIVE_CONNECT:            "交易消息服务连接失败",
    ERR_TD_LIVE_CONNECT_LOST:       "交易消息服务断开",

    ERR_MD_LIVE_CONNECT:            "实时行情服务连接失败",
    ERR_MD_LIVE_CONNECT_LOST:       "实时行情服务连接断开",
    ERR_MD_LIVE_SUBSCRIBE_FAIL:     "订阅实时行情失败",

    ERR_BT_BEGIN:                   "初始化回测失败，可能是终端未启动或无法连接到终端",
    ERR_BT_INVALID_TIMESPAN:        "回测时间区间错误",
    ERR_BT_READ_CACHE_ERROR:        "回测读取缓存数据错误",
    ERR_BT_WRITE_CACHE_ERROR:       "回测写入缓存数据错误",
}
