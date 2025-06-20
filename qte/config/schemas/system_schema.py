"""
系统配置模式定义
"""

from ..config_schema import ConfigSchema, FieldType


def create_system_config_schema() -> ConfigSchema:
    """创建系统配置模式"""
    schema = ConfigSchema(
        name="system",
        description="QTE系统配置模式"
    )
    
    # 系统基础配置
    schema.field(
        "environment",
        FieldType.STRING,
        default="development",
        choices=["development", "testing", "staging", "production"],
        description="运行环境"
    ).field(
        "debug_mode",
        FieldType.BOOLEAN,
        default=False,
        description="调试模式"
    ).field(
        "log_level",
        FieldType.STRING,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="日志级别"
    )
    
    # 数据库配置
    schema.field(
        "database_url",
        FieldType.STRING,
        default="sqlite:///qte.db",
        description="数据库连接URL"
    ).field(
        "database_pool_size",
        FieldType.INTEGER,
        default=10,
        min_value=1,
        max_value=100,
        description="数据库连接池大小"
    ).field(
        "database_timeout",
        FieldType.FLOAT,
        default=30.0,
        min_value=1.0,
        max_value=300.0,
        description="数据库超时(秒)"
    )
    
    # 缓存配置
    schema.field(
        "cache_backend",
        FieldType.STRING,
        default="memory",
        choices=["memory", "redis", "memcached"],
        description="缓存后端"
    ).field(
        "cache_url",
        FieldType.STRING,
        default="redis://localhost:6379/0",
        description="缓存连接URL"
    ).field(
        "cache_default_ttl",
        FieldType.INTEGER,
        default=3600,
        min_value=60,
        max_value=86400,
        description="缓存默认TTL(秒)"
    )
    
    # 消息队列配置
    schema.field(
        "message_broker",
        FieldType.STRING,
        default="memory",
        choices=["memory", "redis", "rabbitmq", "kafka"],
        description="消息代理"
    ).field(
        "broker_url",
        FieldType.STRING,
        default="redis://localhost:6379/1",
        description="消息代理URL"
    ).field(
        "queue_max_size",
        FieldType.INTEGER,
        default=10000,
        min_value=100,
        max_value=100000,
        description="队列最大大小"
    )
    
    # 安全配置
    schema.field(
        "secret_key",
        FieldType.STRING,
        required=True,
        min_length=32,
        description="密钥"
    ).field(
        "enable_authentication",
        FieldType.BOOLEAN,
        default=True,
        description="启用身份验证"
    ).field(
        "session_timeout",
        FieldType.INTEGER,
        default=3600,
        min_value=300,
        max_value=86400,
        description="会话超时(秒)"
    )
    
    # 监控配置
    schema.field(
        "enable_metrics",
        FieldType.BOOLEAN,
        default=True,
        description="启用指标收集"
    ).field(
        "metrics_port",
        FieldType.INTEGER,
        default=8080,
        min_value=1024,
        max_value=65535,
        description="指标服务端口"
    ).field(
        "enable_health_check",
        FieldType.BOOLEAN,
        default=True,
        description="启用健康检查"
    )
    
    # 文件存储配置
    schema.field(
        "data_directory",
        FieldType.STRING,
        default="./data",
        description="数据目录"
    ).field(
        "log_directory",
        FieldType.STRING,
        default="./logs",
        description="日志目录"
    ).field(
        "temp_directory",
        FieldType.STRING,
        default="./temp",
        description="临时目录"
    )
    
    # 性能配置
    schema.field(
        "max_memory_usage_mb",
        FieldType.INTEGER,
        default=2048,
        min_value=512,
        max_value=16384,
        description="最大内存使用(MB)"
    ).field(
        "max_cpu_usage_pct",
        FieldType.FLOAT,
        default=80.0,
        min_value=10.0,
        max_value=100.0,
        description="最大CPU使用率(%)"
    ).field(
        "gc_threshold",
        FieldType.INTEGER,
        default=1000,
        min_value=100,
        max_value=10000,
        description="垃圾回收阈值"
    )
    
    return schema


def create_logging_config_schema() -> ConfigSchema:
    """创建日志配置模式"""
    schema = ConfigSchema(
        name="logging",
        description="日志配置模式"
    )
    
    # 日志基础配置
    schema.field(
        "level",
        FieldType.STRING,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="日志级别"
    ).field(
        "format",
        FieldType.STRING,
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    ).field(
        "date_format",
        FieldType.STRING,
        default="%Y-%m-%d %H:%M:%S",
        description="日期格式"
    )
    
    # 文件日志配置
    schema.field(
        "enable_file_logging",
        FieldType.BOOLEAN,
        default=True,
        description="启用文件日志"
    ).field(
        "log_file",
        FieldType.STRING,
        default="qte.log",
        description="日志文件名"
    ).field(
        "max_file_size_mb",
        FieldType.INTEGER,
        default=100,
        min_value=1,
        max_value=1000,
        description="最大文件大小(MB)"
    ).field(
        "backup_count",
        FieldType.INTEGER,
        default=5,
        min_value=1,
        max_value=50,
        description="备份文件数量"
    )
    
    # 控制台日志配置
    schema.field(
        "enable_console_logging",
        FieldType.BOOLEAN,
        default=True,
        description="启用控制台日志"
    ).field(
        "console_level",
        FieldType.STRING,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="控制台日志级别"
    )
    
    # 远程日志配置
    schema.field(
        "enable_remote_logging",
        FieldType.BOOLEAN,
        default=False,
        description="启用远程日志"
    ).field(
        "remote_host",
        FieldType.STRING,
        default="localhost",
        description="远程日志主机"
    ).field(
        "remote_port",
        FieldType.INTEGER,
        default=514,
        min_value=1,
        max_value=65535,
        description="远程日志端口"
    )
    
    return schema


# 创建全局实例
SystemConfigSchema = create_system_config_schema()
LoggingConfigSchema = create_logging_config_schema()
