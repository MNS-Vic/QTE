import logging
import sys

# TODO: Make log level and format configurable later (e.g., from a config file)
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# LOG_FORMAT_DEBUG = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"

# Global logger instance for the application
# In a more complex app, you might have per-module loggers or a more sophisticated setup.
# For now, a single configured root logger or a dedicated app logger is fine.

def setup_logger(name="QTEngine", level=LOG_LEVEL, log_format=LOG_FORMAT):
    """
    设置一个基本的日志记录器。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter(log_format)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # TODO: File Handler (optional, can be added later)
        # fh = logging.FileHandler('qte_backtest.log')
        # fh.setLevel(level)
        # fh.setFormatter(formatter)
        # logger.addHandler(fh)

    return logger

# Get the default logger for the application
# Components can import this logger instance or get their own via logging.getLogger(__name__)
# after initial setup.
# Using a single global instance here for simplicity in early stages.
app_logger = setup_logger()

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