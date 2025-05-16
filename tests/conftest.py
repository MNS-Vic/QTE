"""
QTE项目全局测试配置文件
提供共享测试夹具和环境配置
"""
import pytest
import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
@pytest.fixture(scope="session")
def configure_logging():
    """配置测试日志"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('qte_tests')

# 数据路径相关夹具
@pytest.fixture
def data_dir():
    """返回数据目录路径"""
    return os.path.join(os.path.dirname(__file__), '..', 'data')

@pytest.fixture
def sample_data_path():
    """返回样本数据路径"""
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'sample')

@pytest.fixture
def backtest_data_path():
    """返回回测数据路径"""
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'backtest')

# 测试配置夹具
@pytest.fixture
def test_config():
    """返回测试配置"""
    return {
        "test_mode": True,
        "log_level": "DEBUG",
        "use_sample_data": True,
        "timeout": 60,  # 测试超时时间(秒)
        "max_memory": 1024  # 最大内存使用限制(MB)
    }

# 模块特定夹具
@pytest.fixture
def setup_data_source():
    """设置测试数据源"""
    from qte.data.sources import DataSource
    # 创建一个测试专用的数据源实例
    data_source = DataSource()
    # 在这里进行数据源的初始化设置
    yield data_source
    # 测试后清理资源
    data_source = None

@pytest.fixture
def setup_backtest_engine():
    """设置回测引擎"""
    from qte.core import Engine
    # 创建一个测试专用的引擎实例
    engine = Engine()
    # 引擎初始化
    yield engine
    # 测试后清理资源
    engine = None

# 帮助函数夹具
@pytest.fixture
def generate_test_data():
    """生成测试数据的函数"""
    def _generate(data_type, size=100):
        """根据类型生成测试数据
        
        Args:
            data_type: 数据类型，可以是'price', 'tick', 'bar'等
            size: 数据量大小
            
        Returns:
            生成的测试数据
        """
        import numpy as np
        import pandas as pd
        
        if data_type == 'price':
            # 生成随机价格序列
            prices = np.random.normal(100, 5, size=size)
            dates = pd.date_range(start='2023-01-01', periods=size, freq='D')
            return pd.Series(prices, index=dates)
        
        elif data_type == 'tick':
            # 生成随机Tick数据
            dates = pd.date_range(start='2023-01-01', periods=size, freq='S')
            data = {
                'symbol': ['000001.XSHE'] * size,
                'last_price': np.random.normal(100, 5, size=size),
                'volume': np.random.randint(1, 1000, size=size),
                'bid_price': np.random.normal(99.5, 5, size=size),
                'ask_price': np.random.normal(100.5, 5, size=size),
                'bid_volume': np.random.randint(1, 500, size=size),
                'ask_volume': np.random.randint(1, 500, size=size)
            }
            return pd.DataFrame(data, index=dates)
        
        elif data_type == 'bar':
            # 生成随机K线数据
            dates = pd.date_range(start='2023-01-01', periods=size, freq='H')
            data = {
                'symbol': ['000001.XSHE'] * size,
                'open': np.random.normal(100, 5, size=size),
                'high': np.random.normal(102, 5, size=size),
                'low': np.random.normal(98, 5, size=size),
                'close': np.random.normal(101, 5, size=size),
                'volume': np.random.randint(1000, 10000, size=size)
            }
            # 确保high >= open, close, low和low <= open, close, high
            for i in range(size):
                high = max(data['high'][i], data['open'][i], data['close'][i])
                low = min(data['low'][i], data['open'][i], data['close'][i])
                data['high'][i] = high
                data['low'][i] = low
            
            return pd.DataFrame(data, index=dates)
        
        else:
            raise ValueError(f"未知的数据类型: {data_type}")
    
    return _generate

# 在每个测试会话开始时执行
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(configure_logging):
    """设置测试环境"""
    logger = configure_logging
    logger.info("开始测试会话")
    
    # 设置测试环境变量
    os.environ["QTE_TEST_MODE"] = "TRUE"
    os.environ["QTE_DATA_DIR"] = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    yield
    
    # 清理测试环境
    logger.info("测试会话结束")
    if "QTE_TEST_MODE" in os.environ:
        del os.environ["QTE_TEST_MODE"] 