"""
引擎配置模式定义
"""

from ..config_schema import ConfigSchema, FieldType


def create_engine_config_schema() -> ConfigSchema:
    """创建引擎配置模式"""
    schema = ConfigSchema(
        name="engine",
        description="QTE引擎系统配置模式"
    )
    
    # 引擎基础配置
    schema.field(
        "engine_type",
        FieldType.STRING,
        default="vectorized_v2",
        choices=["vectorized", "vectorized_v2", "event_driven", "event_driven_v2"],
        description="引擎类型"
    ).field(
        "max_workers",
        FieldType.INTEGER,
        default=4,
        min_value=1,
        max_value=32,
        description="最大工作线程数"
    ).field(
        "queue_size",
        FieldType.INTEGER,
        default=1000,
        min_value=100,
        max_value=10000,
        description="事件队列大小"
    )
    
    # 向量化引擎配置
    schema.field(
        "vectorized_batch_size",
        FieldType.INTEGER,
        default=1000,
        min_value=100,
        max_value=10000,
        description="向量化批处理大小"
    ).field(
        "enable_parallel_processing",
        FieldType.BOOLEAN,
        default=True,
        description="启用并行处理"
    ).field(
        "memory_limit_mb",
        FieldType.INTEGER,
        default=1024,
        min_value=256,
        max_value=8192,
        description="内存限制(MB)"
    )
    
    # 事件驱动引擎配置
    schema.field(
        "event_processing_timeout",
        FieldType.FLOAT,
        default=1.0,
        min_value=0.1,
        max_value=10.0,
        description="事件处理超时(秒)"
    ).field(
        "enable_event_persistence",
        FieldType.BOOLEAN,
        default=False,
        description="启用事件持久化"
    ).field(
        "event_buffer_size",
        FieldType.INTEGER,
        default=10000,
        min_value=1000,
        max_value=100000,
        description="事件缓冲区大小"
    )
    
    # 性能监控配置
    schema.field(
        "enable_performance_monitoring",
        FieldType.BOOLEAN,
        default=True,
        description="启用性能监控"
    ).field(
        "metrics_collection_interval",
        FieldType.FLOAT,
        default=1.0,
        min_value=0.1,
        max_value=60.0,
        description="指标收集间隔(秒)"
    ).field(
        "enable_memory_profiling",
        FieldType.BOOLEAN,
        default=False,
        description="启用内存分析"
    )
    
    # 缓存配置
    schema.field(
        "enable_result_caching",
        FieldType.BOOLEAN,
        default=True,
        description="启用结果缓存"
    ).field(
        "cache_size_mb",
        FieldType.INTEGER,
        default=256,
        min_value=64,
        max_value=2048,
        description="缓存大小(MB)"
    ).field(
        "cache_ttl_seconds",
        FieldType.INTEGER,
        default=3600,
        min_value=60,
        max_value=86400,
        description="缓存TTL(秒)"
    )
    
    # 错误处理配置
    schema.field(
        "max_retry_attempts",
        FieldType.INTEGER,
        default=3,
        min_value=0,
        max_value=10,
        description="最大重试次数"
    ).field(
        "retry_delay_seconds",
        FieldType.FLOAT,
        default=1.0,
        min_value=0.1,
        max_value=10.0,
        description="重试延迟(秒)"
    ).field(
        "enable_graceful_degradation",
        FieldType.BOOLEAN,
        default=True,
        description="启用优雅降级"
    )
    
    return schema


def create_backtest_config_schema() -> ConfigSchema:
    """创建回测配置模式"""
    schema = ConfigSchema(
        name="backtest",
        description="回测配置模式"
    )
    
    # 回测基础配置
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
        "slippage_rate",
        FieldType.FLOAT,
        default=0.0001,
        min_value=0.0,
        max_value=1.0,
        description="滑点率"
    )
    
    # 风险管理配置
    schema.field(
        "max_position_size",
        FieldType.FLOAT,
        default=0.1,
        min_value=0.01,
        max_value=1.0,
        description="最大持仓比例"
    ).field(
        "stop_loss_pct",
        FieldType.FLOAT,
        default=0.05,
        min_value=0.01,
        max_value=0.5,
        description="止损百分比"
    ).field(
        "take_profit_pct",
        FieldType.FLOAT,
        default=0.1,
        min_value=0.01,
        max_value=1.0,
        description="止盈百分比"
    )
    
    # 数据配置
    schema.field(
        "data_start_date",
        FieldType.STRING,
        description="数据开始日期 (YYYY-MM-DD)"
    ).field(
        "data_end_date",
        FieldType.STRING,
        description="数据结束日期 (YYYY-MM-DD)"
    ).field(
        "benchmark_symbol",
        FieldType.STRING,
        default="SPY",
        description="基准标的"
    )
    
    # 输出配置
    schema.field(
        "save_trades",
        FieldType.BOOLEAN,
        default=True,
        description="保存交易记录"
    ).field(
        "save_positions",
        FieldType.BOOLEAN,
        default=True,
        description="保存持仓记录"
    ).field(
        "save_portfolio",
        FieldType.BOOLEAN,
        default=True,
        description="保存组合记录"
    )
    
    return schema


# 创建全局实例
EngineConfigSchema = create_engine_config_schema()
BacktestConfigSchema = create_backtest_config_schema()
