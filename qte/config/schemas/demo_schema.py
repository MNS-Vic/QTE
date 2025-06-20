"""
演示配置模式定义
"""

from ..config_schema import ConfigSchema, FieldType


def create_demo_config_schema() -> ConfigSchema:
    """创建演示配置模式"""
    schema = ConfigSchema(
        name="demo",
        description="QTE演示系统配置模式"
    )
    
    # 基础配置
    schema.field(
        "initial_capital", 
        FieldType.FLOAT,
        required=True,
        min_value=1000.0,
        description="初始资金"
    ).field(
        "commission_rate",
        FieldType.FLOAT,
        default=0.001,
        min_value=0.0,
        max_value=1.0,
        description="手续费率"
    ).field(
        "slippage",
        FieldType.FLOAT,
        default=0.0001,
        min_value=0.0,
        max_value=1.0,
        description="滑点"
    )
    
    # 测试数据配置
    schema.field(
        "test_symbols",
        FieldType.LIST,
        default=["AAPL", "GOOGL", "MSFT"],
        item_type=FieldType.STRING,
        min_length=1,
        description="测试标的列表"
    ).field(
        "test_period_days",
        FieldType.INTEGER,
        default=30,
        min_value=1,
        max_value=365,
        description="测试周期天数"
    ).field(
        "data_frequency",
        FieldType.STRING,
        default="1d",
        choices=["1min", "5min", "15min", "30min", "1h", "1d"],
        description="数据频率"
    )
    
    # 策略配置
    schema.field(
        "strategy_type",
        FieldType.STRING,
        default="moving_average",
        choices=["moving_average", "momentum", "mean_reversion", "custom"],
        description="策略类型"
    ).field(
        "short_window",
        FieldType.INTEGER,
        default=5,
        min_value=1,
        max_value=100,
        description="短期窗口"
    ).field(
        "long_window",
        FieldType.INTEGER,
        default=15,
        min_value=1,
        max_value=200,
        description="长期窗口"
    ).field(
        "lookback_period",
        FieldType.INTEGER,
        default=10,
        min_value=1,
        max_value=100,
        description="回看期"
    ).field(
        "momentum_threshold",
        FieldType.FLOAT,
        default=0.02,
        min_value=0.001,
        max_value=1.0,
        description="动量阈值"
    )
    
    # 输出配置
    schema.field(
        "output_dir",
        FieldType.STRING,
        default="demo_output",
        description="输出目录"
    ).field(
        "reports_dir",
        FieldType.STRING,
        default="demo_reports",
        description="报告目录"
    ).field(
        "generate_html_report",
        FieldType.BOOLEAN,
        default=True,
        description="是否生成HTML报告"
    ).field(
        "generate_json_report",
        FieldType.BOOLEAN,
        default=True,
        description="是否生成JSON报告"
    )
    
    # 日志配置
    schema.field(
        "log_level",
        FieldType.STRING,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="日志级别"
    ).field(
        "verbose",
        FieldType.BOOLEAN,
        default=False,
        description="详细输出"
    )
    
    return schema


# 创建全局实例
DemoConfigSchema = create_demo_config_schema()
