"""
交易配置模式定义
"""

from ..config_schema import ConfigSchema, FieldType


def create_trading_config_schema() -> ConfigSchema:
    """创建交易配置模式"""
    schema = ConfigSchema(
        name="trading",
        description="交易系统配置模式"
    )
    
    # 交易基础配置
    schema.field(
        "trading_mode",
        FieldType.STRING,
        default="simulation",
        choices=["simulation", "paper", "live"],
        description="交易模式"
    ).field(
        "default_order_type",
        FieldType.STRING,
        default="market",
        choices=["market", "limit", "stop", "stop_limit"],
        description="默认订单类型"
    ).field(
        "default_time_in_force",
        FieldType.STRING,
        default="day",
        choices=["day", "gtc", "ioc", "fok"],
        description="默认订单有效期"
    )
    
    # 资金管理配置
    schema.field(
        "max_portfolio_risk",
        FieldType.FLOAT,
        default=0.02,
        min_value=0.001,
        max_value=0.1,
        description="最大组合风险"
    ).field(
        "max_single_position_risk",
        FieldType.FLOAT,
        default=0.01,
        min_value=0.001,
        max_value=0.05,
        description="最大单笔持仓风险"
    ).field(
        "position_sizing_method",
        FieldType.STRING,
        default="fixed_fractional",
        choices=["fixed_amount", "fixed_fractional", "volatility_based", "kelly"],
        description="仓位计算方法"
    )
    
    # 风险控制配置
    schema.field(
        "enable_stop_loss",
        FieldType.BOOLEAN,
        default=True,
        description="启用止损"
    ).field(
        "enable_take_profit",
        FieldType.BOOLEAN,
        default=True,
        description="启用止盈"
    ).field(
        "enable_trailing_stop",
        FieldType.BOOLEAN,
        default=False,
        description="启用跟踪止损"
    ).field(
        "max_drawdown_limit",
        FieldType.FLOAT,
        default=0.1,
        min_value=0.01,
        max_value=0.5,
        description="最大回撤限制"
    )
    
    # 交易时间配置
    schema.field(
        "trading_start_time",
        FieldType.STRING,
        default="09:30",
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="交易开始时间 (HH:MM)"
    ).field(
        "trading_end_time",
        FieldType.STRING,
        default="16:00",
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="交易结束时间 (HH:MM)"
    ).field(
        "trading_timezone",
        FieldType.STRING,
        default="US/Eastern",
        description="交易时区"
    )
    
    # 数据源配置
    schema.field(
        "primary_data_source",
        FieldType.STRING,
        default="yahoo",
        choices=["yahoo", "alpha_vantage", "quandl", "iex", "custom"],
        description="主要数据源"
    ).field(
        "backup_data_source",
        FieldType.STRING,
        default="alpha_vantage",
        choices=["yahoo", "alpha_vantage", "quandl", "iex", "custom"],
        description="备用数据源"
    ).field(
        "data_update_interval",
        FieldType.INTEGER,
        default=60,
        min_value=1,
        max_value=3600,
        description="数据更新间隔(秒)"
    )
    
    # 通知配置
    schema.field(
        "enable_email_notifications",
        FieldType.BOOLEAN,
        default=False,
        description="启用邮件通知"
    ).field(
        "enable_sms_notifications",
        FieldType.BOOLEAN,
        default=False,
        description="启用短信通知"
    ).field(
        "notification_events",
        FieldType.LIST,
        default=["order_filled", "stop_loss_triggered", "system_error"],
        item_type=FieldType.STRING,
        description="通知事件列表"
    )
    
    return schema


def create_strategy_config_schema() -> ConfigSchema:
    """创建策略配置模式"""
    schema = ConfigSchema(
        name="strategy",
        description="策略配置模式"
    )
    
    # 策略基础配置
    schema.field(
        "strategy_name",
        FieldType.STRING,
        required=True,
        description="策略名称"
    ).field(
        "strategy_version",
        FieldType.STRING,
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="策略版本"
    ).field(
        "strategy_description",
        FieldType.STRING,
        default="",
        description="策略描述"
    )
    
    # 策略参数配置
    schema.field(
        "lookback_period",
        FieldType.INTEGER,
        default=20,
        min_value=1,
        max_value=252,
        description="回看期"
    ).field(
        "rebalance_frequency",
        FieldType.STRING,
        default="daily",
        choices=["minute", "hourly", "daily", "weekly", "monthly"],
        description="再平衡频率"
    ).field(
        "min_holding_period",
        FieldType.INTEGER,
        default=1,
        min_value=1,
        max_value=252,
        description="最小持有期(天)"
    )
    
    # 信号生成配置
    schema.field(
        "signal_threshold",
        FieldType.FLOAT,
        default=0.02,
        min_value=0.001,
        max_value=1.0,
        description="信号阈值"
    ).field(
        "signal_smoothing",
        FieldType.BOOLEAN,
        default=True,
        description="信号平滑"
    ).field(
        "enable_signal_filtering",
        FieldType.BOOLEAN,
        default=True,
        description="启用信号过滤"
    )
    
    # 执行配置
    schema.field(
        "execution_delay",
        FieldType.FLOAT,
        default=0.0,
        min_value=0.0,
        max_value=60.0,
        description="执行延迟(秒)"
    ).field(
        "partial_fill_handling",
        FieldType.STRING,
        default="wait",
        choices=["wait", "cancel", "market"],
        description="部分成交处理"
    )
    
    return schema


# 创建全局实例
TradingConfigSchema = create_trading_config_schema()
StrategyConfigSchema = create_strategy_config_schema()
