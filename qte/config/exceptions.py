"""
配置管理异常定义
"""


class ConfigError(Exception):
    """配置管理基础异常"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证异常"""
    
    def __init__(self, message: str, field: str = None, value=None):
        self.field = field
        self.value = value
        if field:
            super().__init__(f"配置验证失败 [{field}]: {message}")
        else:
            super().__init__(f"配置验证失败: {message}")


class ConfigNotFoundError(ConfigError):
    """配置文件未找到异常"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        super().__init__(f"配置文件未找到: {config_path}")


class ConfigFormatError(ConfigError):
    """配置格式异常"""
    
    def __init__(self, message: str, format_type: str = None):
        self.format_type = format_type
        if format_type:
            super().__init__(f"配置格式错误 [{format_type}]: {message}")
        else:
            super().__init__(f"配置格式错误: {message}")


class ConfigLoadError(ConfigError):
    """配置加载异常"""
    
    def __init__(self, message: str, config_path: str = None, cause: Exception = None):
        self.config_path = config_path
        self.cause = cause
        if config_path:
            super().__init__(f"配置加载失败 [{config_path}]: {message}")
        else:
            super().__init__(f"配置加载失败: {message}")


class ConfigSaveError(ConfigError):
    """配置保存异常"""
    
    def __init__(self, message: str, config_path: str = None, cause: Exception = None):
        self.config_path = config_path
        self.cause = cause
        if config_path:
            super().__init__(f"配置保存失败 [{config_path}]: {message}")
        else:
            super().__init__(f"配置保存失败: {message}")


class ConfigWatchError(ConfigError):
    """配置监控异常"""
    
    def __init__(self, message: str, config_path: str = None):
        self.config_path = config_path
        if config_path:
            super().__init__(f"配置监控异常 [{config_path}]: {message}")
        else:
            super().__init__(f"配置监控异常: {message}")


class ConfigSchemaError(ConfigError):
    """配置模式异常"""
    
    def __init__(self, message: str, schema_name: str = None):
        self.schema_name = schema_name
        if schema_name:
            super().__init__(f"配置模式错误 [{schema_name}]: {message}")
        else:
            super().__init__(f"配置模式错误: {message}")


class ConfigEnvironmentError(ConfigError):
    """配置环境异常"""
    
    def __init__(self, message: str, environment: str = None):
        self.environment = environment
        if environment:
            super().__init__(f"配置环境错误 [{environment}]: {message}")
        else:
            super().__init__(f"配置环境错误: {message}")
