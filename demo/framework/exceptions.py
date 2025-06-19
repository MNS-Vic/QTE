"""
演示框架异常定义
"""


class DemoFrameworkError(Exception):
    """演示框架基础异常"""
    pass


class ServiceNotFoundError(DemoFrameworkError):
    """服务未找到异常"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"服务未找到: {service_name}")


class ValidationError(DemoFrameworkError):
    """验证失败异常"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        if field:
            super().__init__(f"验证失败 [{field}]: {message}")
        else:
            super().__init__(f"验证失败: {message}")


class ServiceInitializationError(DemoFrameworkError):
    """服务初始化异常"""
    
    def __init__(self, service_name: str, cause: Exception):
        self.service_name = service_name
        self.cause = cause
        super().__init__(f"服务初始化失败 [{service_name}]: {cause}")


class DemoExecutionError(DemoFrameworkError):
    """演示执行异常"""
    
    def __init__(self, demo_name: str, cause: Exception):
        self.demo_name = demo_name
        self.cause = cause
        super().__init__(f"演示执行失败 [{demo_name}]: {cause}")
