import logging
import os
from datetime import datetime
from typing import Optional

# TODO: Make log level and format configurable later (e.g., from a config file)
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# LOG_FORMAT_DEBUG = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"

# Global logger instance for the application
# In a more complex app, you might have per-module loggers or a more sophisticated setup.
# For now, a single configured root logger or a dedicated app logger is fine.

# 定义日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

# 创建默认日志记录器
app_logger = logging.getLogger('qte.analysis')
app_logger.setLevel(logging.INFO)

# 默认控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 添加处理器到记录器
app_logger.addHandler(console_handler)

def setup_logger(level: str = 'info', 
                 log_file: Optional[str] = None, 
                 log_dir: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Parameters
    ----------
    level : str, optional
        日志级别，可以是'debug', 'info', 'warning', 'error', 'critical'中的一个, by default 'info'
    log_file : Optional[str], optional
        日志文件名, by default None
    log_dir : Optional[str], optional
        日志文件目录, by default None
        
    Returns
    -------
    logging.Logger
        配置好的日志记录器
    """
    # 设置日志级别
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    app_logger.setLevel(log_level)
    console_handler.setLevel(log_level)
    
    # 如果提供了日志文件，添加文件处理器
    if log_file:
        # 如果提供了日志目录，确保目录存在
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, log_file)
        else:
            # 默认在logs目录下
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, log_file)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # 如果已经有同名处理器，先移除
        for handler in app_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                app_logger.removeHandler(handler)
        
        # 添加新处理器
        app_logger.addHandler(file_handler)
        app_logger.info(f"日志将输出到文件: {log_path}")
    
    return app_logger

# Get the default logger for the application
# Components can import this logger instance or get their own via logging.getLogger(__name__)
# after initial setup.
# Using a single global instance here for simplicity in early stages.

if __name__ == '__main__':
    # Example usage:
    app_logger.debug("This is a debug message.") # Won't show if LOG_LEVEL is INFO
    app_logger.info("This is an info message.")
    app_logger.warning("This is a warning message.")
    app_logger.error("This is an error message.")
    app_logger.critical("This is a critical message.")

    # Example of getting a module-specific logger (recommended for larger apps)
    module_logger = logging.getLogger("QTEngine.MyModule")
    # If QTEngine logger is already configured, child loggers inherit its settings by default.
    # You can also configure them separately if needed.
    module_logger.info("Info message from MyModule.")

    # Test if handler is added only once
    app_logger_again = setup_logger()
    app_logger_again.info("Another info message from app_logger (testing handler duplication).")
    assert len(app_logger.handlers) == 1, "Logger should only have one console handler."
    print("Logger setup example finished.")

# 为测试环境设置更低的日志级别
if os.environ.get('PYTEST_CURRENT_TEST'):
    app_logger.setLevel(logging.WARNING)