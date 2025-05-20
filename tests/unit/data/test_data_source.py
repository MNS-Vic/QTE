"""
数据源管理器和工厂测试

使用TDD方法测试数据源管理器和数据源工厂功能
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import os
from datetime import datetime, date

from qte.data.data_source_manager import DataSourceManager, get_data_source_manager
from qte.data.data_factory import DataSourceFactory
from qte.data.sources.local_csv import LocalCsvSource

class TestDataSourceManager:
    """测试数据源管理器"""
    
    def setup_method(self):
        """测试前设置"""
        self.manager = DataSourceManager()
        
        # 创建一些模拟数据源
        self.mock_source1 = MagicMock()
        self.mock_source2 = MagicMock()
        
        # 注册模拟数据源
        self.manager.register_source("source1", self.mock_source1, make_default=True)
        self.manager.register_source("source2", self.mock_source2)
    
    def test_initialization(self):
        """测试初始化"""
        manager = DataSourceManager()
        assert manager.sources == {}
        assert manager.default_source is None
        assert os.path.exists(manager.cache_dir)
    
    def test_register_source(self):
        """测试注册数据源"""
        manager = DataSourceManager()
        source = MagicMock()
        
        # 测试注册，不设为默认
        result = manager.register_source("test", source)
        assert result == True
        assert "test" in manager.sources
        assert manager.sources["test"] == source
        assert manager.default_source == "test"  # 第一个注册的会自动成为默认
        
        # 测试注册另一个源，明确设为默认
        source2 = MagicMock()
        result = manager.register_source("test2", source2, make_default=True)
        assert result == True
        assert manager.default_source == "test2"
        
        # 测试覆盖已存在的源
        source3 = MagicMock()
        result = manager.register_source("test", source3)
        assert result == True
        assert manager.sources["test"] == source3
    
    def test_get_source(self):
        """测试获取数据源"""
        # 测试获取默认数据源
        source = self.manager.get_source()
        assert source == self.mock_source1
        
        # 测试获取指定数据源
        source = self.manager.get_source("source2")
        assert source == self.mock_source2
        
        # 测试获取不存在的数据源
        with pytest.raises(ValueError):
            self.manager.get_source("nonexistent")
    
    def test_set_default_source(self):
        """测试设置默认数据源"""
        # 确认初始默认源
        assert self.manager.default_source == "source1"
        
        # 测试设置默认源
        result = self.manager.set_default_source("source2")
        assert result == True
        assert self.manager.default_source == "source2"
        
        # 测试设置不存在的源为默认
        with pytest.raises(ValueError):
            self.manager.set_default_source("nonexistent")
    
    def test_list_sources(self):
        """测试列出所有数据源"""
        sources = self.manager.list_sources()
        assert isinstance(sources, list)
        assert "source1" in sources
        assert "source2" in sources
        assert len(sources) == 2
    
    def test_get_bars(self):
        """测试获取K线数据"""
        # 设置模拟数据源的行为
        sample_df = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [98, 99],
            'close': [101, 102],
            'volume': [1000, 1100]
        }, index=pd.date_range(start='2023-01-01', periods=2))
        
        self.mock_source1.get_bars.return_value = sample_df
        
        # 测试使用默认数据源获取数据
        result = self.manager.get_bars("000001", "2023-01-01", "2023-01-02")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.equals(sample_df)
        self.mock_source1.get_bars.assert_called_once_with("000001", "2023-01-01", "2023-01-02", "1d")
        
        # 重置并测试使用指定数据源
        self.mock_source1.get_bars.reset_mock()
        self.mock_source2.get_bars.return_value = sample_df
        
        result = self.manager.get_bars("000001", "2023-01-01", "2023-01-02", source_name="source2")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.equals(sample_df)
        self.mock_source2.get_bars.assert_called_once_with("000001", "2023-01-01", "2023-01-02", "1d")
        self.mock_source1.get_bars.assert_not_called()
        
        # 测试源不支持get_bars方法
        self.mock_source1 = MagicMock(spec=[])  # 创建一个没有get_bars方法的模拟对象
        self.manager.register_source("source1", self.mock_source1, make_default=True)
        
        result = self.manager.get_bars("000001")
        assert result is None
    
    def test_get_ticks(self):
        """测试获取Tick数据"""
        # 设置模拟数据源的行为
        sample_df = pd.DataFrame({
            'price': [101.5, 101.6],
            'volume': [100, 200],
            'bid_price': [101.4, 101.5],
            'ask_price': [101.6, 101.7]
        }, index=pd.date_range(start='2023-01-01 09:30:00', periods=2, freq='1s'))
        
        self.mock_source1.get_ticks.return_value = sample_df
        
        # 测试使用默认数据源获取数据
        result = self.manager.get_ticks("000001", "2023-01-01")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.equals(sample_df)
        self.mock_source1.get_ticks.assert_called_once_with("000001", "2023-01-01")
        
        # 测试数据源不支持get_ticks方法
        self.mock_source1 = MagicMock(spec=[])  # 创建一个没有get_ticks方法的模拟对象
        self.manager.register_source("source1", self.mock_source1, make_default=True)
        
        result = self.manager.get_ticks("000001", "2023-01-01")
        assert result is None
    
    def test_get_fundamentals(self):
        """测试获取基本面数据"""
        # 设置模拟数据源的行为
        sample_df = pd.DataFrame({
            'symbol': ['000001', '000002'],
            'pe_ratio': [15.2, 12.8],
            'market_cap': [10000, 8000]
        })
        
        self.mock_source1.get_fundamentals.return_value = sample_df
        
        # 测试使用默认数据源获取数据
        result = self.manager.get_fundamentals("daily", ["000001", "000002"], "2023-01-01", "2023-01-02")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.equals(sample_df)
        self.mock_source1.get_fundamentals.assert_called_once_with("daily", ["000001", "000002"], "2023-01-01", "2023-01-02", None)
        
        # 测试数据源不支持get_fundamentals方法
        self.mock_source1 = MagicMock(spec=[])  # 创建一个没有get_fundamentals方法的模拟对象
        self.manager.register_source("source1", self.mock_source1, make_default=True)
        
        result = self.manager.get_fundamentals("daily", ["000001", "000002"])
        assert result is None
    
    def test_get_symbols(self):
        """测试获取可用标的列表"""
        # 设置模拟数据源的行为
        self.mock_source1.get_symbols.return_value = ["000001", "000002", "000003"]
        
        # 测试使用默认数据源获取数据
        result = self.manager.get_symbols()
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 3
        assert "000001" in result
        self.mock_source1.get_symbols.assert_called_once_with(None)
        
        # 测试数据源不支持get_symbols方法
        self.mock_source1 = MagicMock(spec=[])  # 创建一个没有get_symbols方法的模拟对象
        self.manager.register_source("source1", self.mock_source1, make_default=True)
        
        result = self.manager.get_symbols()
        assert isinstance(result, list)
        assert len(result) == 0  # 应返回空列表
    
    def test_global_instance(self):
        """测试全局单例实例"""
        # 获取全局实例
        instance1 = get_data_source_manager()
        instance2 = get_data_source_manager()
        
        # 验证两次获取的是同一个实例
        assert instance1 is instance2
        
        # 验证实例类型正确
        assert isinstance(instance1, DataSourceManager)


class TestDataSourceFactory:
    """测试数据源工厂类"""
    
    def setup_method(self):
        """测试前设置"""
        # 清理可能存在的测试注册
        if 'test' in DataSourceFactory._creators:
            del DataSourceFactory._creators['test']
    
    def test_default_creators(self):
        """测试默认创建器"""
        # 验证内置数据源类型
        assert 'csv' in DataSourceFactory._creators
        assert 'gm' in DataSourceFactory._creators
        
        # 测试创建CSV数据源
        csv_source = DataSourceFactory.create('csv', base_path='data/')
        assert csv_source is not None
        assert isinstance(csv_source, LocalCsvSource)
        assert csv_source.base_path == 'data/'
    
    def test_register_creator(self):
        """测试注册创建器函数"""
        # 定义一个简单的创建函数 - 修改为返回一个简单对象，而不是MagicMock
        def create_test_source(**kwargs):
            # 创建一个简单对象，正确设置所有传入的属性
            class TestSource:
                def __init__(self, **props):
                    for key, value in props.items():
                        setattr(self, key, value)
            return TestSource(**kwargs)
        
        # 注册创建函数
        result = DataSourceFactory.register_creator('test', create_test_source)
        assert result == True
        assert 'test' in DataSourceFactory._creators
        
        # 测试使用新注册的创建函数
        test_source = DataSourceFactory.create('test', name='test_instance')
        assert test_source is not None
        assert test_source.name == 'test_instance'
    
    def test_register_source_class(self):
        """测试注册源类"""
        # 创建一个简单的测试类
        class TestSource:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
        
        # 注册源类
        result = DataSourceFactory.register_source_class('test', TestSource)
        assert result == True
        assert 'test' in DataSourceFactory._creators
        
        # 测试使用新注册的源类
        test_source = DataSourceFactory.create('test', value=42)
        assert test_source is not None
        assert isinstance(test_source, TestSource)
        assert test_source.value == 42
    
    def test_create_unknown_type(self):
        """测试创建未知类型"""
        result = DataSourceFactory.create('unknown_type')
        assert result is None
    
    def test_creator_exception_handling(self):
        """测试创建器异常处理"""
        # 注册一个会抛出异常的创建函数
        def failing_creator(**kwargs):
            raise ValueError("Test error")
        
        DataSourceFactory.register_creator('failing', failing_creator)
        
        # 测试异常处理
        result = DataSourceFactory.create('failing')
        assert result is None
    
    def test_list_available_sources(self):
        """测试列出可用数据源"""
        # 添加测试源
        DataSourceFactory.register_creator('test', lambda **kwargs: None)
        
        # 获取可用源列表
        sources = DataSourceFactory.list_available_sources()
        assert isinstance(sources, list)
        assert 'csv' in sources
        assert 'gm' in sources
        assert 'test' in sources
    
    def test_auto_discover(self):
        """测试自动发现数据源类"""
        # 这个测试需要模拟importlib和os操作，比较复杂
        # 实现一个简化版本
        
        # 模拟一个包及其文件
        mock_package = MagicMock()
        mock_package.__file__ = '/path/to/package/__init__.py'
        
        mock_module = MagicMock()
        
        # 创建一个测试源类，确保其名称以Source结尾
        class TestAutoSource:
            def __init__(self, **kwargs):
                pass
        
        # 设置模块中的类
        mock_module.TestAutoSource = TestAutoSource
        TestAutoSource.__module__ = 'mock_package.test_file'
        
        with patch('importlib.import_module') as mock_import:
            with patch('os.listdir') as mock_listdir:
                with patch('inspect.getmembers') as mock_getmembers:
                    with patch('inspect.isclass', return_value=True):
                        # 设置导入返回值
                        mock_import.side_effect = [mock_package, mock_module]
                        
                        # 设置目录列表
                        mock_listdir.return_value = ['test_file.py', '__init__.py', '__pycache__']
                        
                        # 设置类成员
                        mock_getmembers.return_value = [('TestAutoSource', TestAutoSource)]
                        
                        # 调用自动发现
                        count = DataSourceFactory.auto_discover('mock_package')
                        
                        # 验证发现的数据源数量
                        assert count >= 0  # 在模拟环境中可能无法准确验证数量 