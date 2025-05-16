"""
数据源接口单元测试
测试数据源的基本接口功能
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, date, timedelta
import numpy as np

from qte.data.data_source_interface import DataSourceInterface, BaseDataSource

class TestBaseDataSource:
    """测试基础数据源类"""
    
    class MockDataSource(BaseDataSource):
        """用于测试的BaseDataSource子类，实现所有必要的抽象方法"""
        
        def __init__(self, use_cache=False):
            # 重写初始化方法，跳过原始的缓存初始化逻辑
            self._connected = False
            self._use_cache = use_cache
            self._cache = MagicMock() if use_cache else None
            self._test_data = None  # 用于测试的数据
            
        def set_test_data(self, data):
            """设置测试数据"""
            self._test_data = data
            
        def _get_bars_impl(self, symbol, start_date=None, end_date=None, frequency='1d', **kwargs):
            """实现具体的获取K线数据方法"""
            return self._test_data if self._test_data is not None else pd.DataFrame()
            
        def get_bars(self, symbol, start_date=None, end_date=None, frequency='1d', **kwargs):
            """实现抽象方法"""
            if self._use_cache:
                return self.get_bars_with_cache(symbol, start_date, end_date, frequency, **kwargs)
            else:
                return self._get_bars_impl(symbol, start_date, end_date, frequency, **kwargs)
    
    def setup_method(self):
        """测试前设置"""
        self.data_source = self.MockDataSource(use_cache=False)
    
    def test_initialization(self):
        """测试初始化"""
        assert self.data_source._connected == False
        assert self.data_source._use_cache == False
        assert self.data_source._cache is None
    
    def test_initialization_with_cache(self):
        """测试使用缓存的初始化"""
        # 创建一个带缓存的数据源
        data_source = self.MockDataSource(use_cache=True)
        
        # 验证缓存设置
        assert data_source._use_cache == True
        assert data_source._cache is not None
        assert isinstance(data_source._cache, MagicMock)
    
    def test_connect(self):
        """测试连接方法"""
        result = self.data_source.connect()
        assert result == True
        assert self.data_source._connected == True
    
    def test_get_symbols(self):
        """测试获取标的列表方法"""
        symbols = self.data_source.get_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) == 0  # 基类返回空列表
    
    def test_ensure_connected(self):
        """测试确保连接方法"""
        # 初始状态未连接
        assert self.data_source._connected == False
        
        # 调用会自动连接
        result = self.data_source._ensure_connected()
        assert result == True
        assert self.data_source._connected == True
    
    def test_format_date(self):
        """测试日期格式化方法"""
        # 测试None
        assert self.data_source._format_date(None) is None
        
        # 测试datetime对象
        dt = datetime(2023, 1, 1, 10, 30, 0)
        assert self.data_source._format_date(dt) == "2023-01-01"
        
        # 测试date对象
        d = date(2023, 1, 1)
        assert self.data_source._format_date(d) == "2023-01-01"
        
        # 测试字符串
        assert self.data_source._format_date("2023-01-01") == "2023-01-01"
    
    def test_get_bars_cache_enabled(self):
        """测试带缓存的K线获取方法"""
        # 创建一个mock缓存
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # 首次缓存未命中
        
        # 模拟数据
        test_df = pd.DataFrame({
            'open': [100, 101], 
            'high': [102, 103], 
            'low': [98, 99], 
            'close': [101, 102], 
            'volume': [1000, 1100]
        }, index=pd.date_range('2023-01-01', periods=2))
        
        # 创建一个带缓存的数据源
        data_source = self.MockDataSource(use_cache=False)  # 先禁用缓存
        data_source.set_test_data(test_df)  # 设置测试数据
        
        # 手动设置缓存和标志
        data_source._cache = mock_cache
        data_source._use_cache = True
        
        # 调用get_bars
        result = data_source.get_bars('000001.XSHE', '2023-01-01', '2023-01-02')
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert result.equals(test_df)
        
        # 验证缓存操作
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
    
    def test_get_bars_cache_hit(self):
        """测试缓存命中的K线获取方法"""
        # 创建一个mock缓存，设置为命中
        mock_cache = MagicMock()
        test_df = pd.DataFrame({
            'open': [100, 101], 
            'high': [102, 103], 
            'low': [98, 99], 
            'close': [101, 102], 
            'volume': [1000, 1100]
        }, index=pd.date_range('2023-01-01', periods=2))
        mock_cache.get.return_value = test_df
        
        # 创建一个带缓存的数据源
        data_source = self.MockDataSource(use_cache=False)  # 先禁用缓存
        
        # 手动设置缓存和标志
        data_source._cache = mock_cache
        data_source._use_cache = True
        
        # 模拟_get_bars_impl方法
        data_source._get_bars_impl = MagicMock()
        
        # 调用get_bars
        result = data_source.get_bars('000001.XSHE', '2023-01-01', '2023-01-02')
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert result.equals(test_df)
        
        # 验证缓存操作
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()
        data_source._get_bars_impl.assert_not_called()
    
    def test_get_bars_cache_disabled(self):
        """测试禁用缓存的K线获取方法"""
        # 模拟数据
        test_df = pd.DataFrame({
            'open': [100, 101], 
            'high': [102, 103], 
            'low': [98, 99], 
            'close': [101, 102], 
            'volume': [1000, 1100]
        }, index=pd.date_range('2023-01-01', periods=2))
        
        # 创建一个禁用缓存的数据源
        data_source = self.MockDataSource(use_cache=False)
        
        # 设置测试数据
        data_source.set_test_data(test_df)
        
        # 调用get_bars
        result = data_source.get_bars('000001.XSHE', '2023-01-01', '2023-01-02')
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert result.equals(test_df)

class TestDataSourceInterfaceContracts:
    """测试数据源接口契约"""
    
    class MinimalDataSource(DataSourceInterface):
        """实现所有必要方法的最小数据源"""
        
        def connect(self, **kwargs):
            return True
            
        def get_symbols(self, market=None, **kwargs):
            return ["000001.XSHE", "600000.XSHG"]
            
        def get_bars(self, symbol, start_date=None, end_date=None, frequency='1d', **kwargs):
            # 创建一个简单的DataFrame作为测试数据
            dates = pd.date_range(
                start=start_date or datetime.now().date() - timedelta(days=10),
                end=end_date or datetime.now().date(),
                freq='D'
            )
            
            df = pd.DataFrame({
                'open': np.random.rand(len(dates)) * 100 + 50,
                'high': np.random.rand(len(dates)) * 100 + 60,
                'low': np.random.rand(len(dates)) * 100 + 40,
                'close': np.random.rand(len(dates)) * 100 + 50,
                'volume': np.random.randint(1000, 10000, len(dates))
            }, index=dates)
            
            return df
    
    def setup_method(self):
        """测试前设置"""
        self.data_source = self.MinimalDataSource()
    
    def test_minimal_implementation(self):
        """测试最小实现"""
        # 验证connect方法
        assert self.data_source.connect() == True
        
        # 验证get_symbols方法
        symbols = self.data_source.get_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) == 2
        assert "000001.XSHE" in symbols
        
        # 验证get_bars方法
        bars = self.data_source.get_bars("000001.XSHE")
        assert isinstance(bars, pd.DataFrame)
        assert len(bars) > 0
        
        # 验证DataFrame结构符合接口要求
        assert all(col in bars.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        assert isinstance(bars.index, pd.DatetimeIndex)
    
    def test_get_ticks_default_implementation(self):
        """测试默认的get_ticks实现"""
        result = self.data_source.get_ticks("000001.XSHE")
        assert result is None
    
    def test_get_fundamentals_default_implementation(self):
        """测试默认的get_fundamentals实现"""
        result = self.data_source.get_fundamentals("balance", ["000001.XSHE"])
        assert result is None
    
    def test_interface_contract_enforcement(self):
        """测试接口契约强制执行"""
        # 尝试创建一个缺少必要方法的类
        with pytest.raises(TypeError):
            class IncompleteDataSource(DataSourceInterface):
                pass
            
            IncompleteDataSource()  # 这应该引发错误，因为没有实现抽象方法
        
        # 尝试创建一个只实现部分方法的类
        with pytest.raises(TypeError):
            class PartialDataSource(DataSourceInterface):
                def connect(self, **kwargs):
                    return True
            
            PartialDataSource()  # 这应该引发错误，因为没有实现所有抽象方法


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 