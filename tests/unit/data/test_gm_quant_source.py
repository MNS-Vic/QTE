"""
掘金量化数据源测试
测试从掘金量化API获取数据的功能
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import os
from datetime import datetime
import sys

from qte.data.sources.gm_quant import GmQuantSource
from qte.data.data_source_interface import BaseDataSource

# 创建一个mock的gm模块
mock_gm = MagicMock()
mock_gm.api = MagicMock()
mock_gm.api.set_token = MagicMock()
mock_gm.api.get_instruments = MagicMock()
mock_gm.api.history = MagicMock()
mock_gm.api.get_ticks = MagicMock()
mock_gm.api.get_fundamentals = MagicMock()

# 将模拟的gm模块添加到sys.modules中
sys.modules['gm'] = mock_gm
sys.modules['gm.api'] = mock_gm.api

class TestGmQuantSource:
    """测试掘金量化数据源"""
    
    def setup_method(self):
        """测试前设置"""
        # 使用测试模式初始化数据源
        self.data_source = GmQuantSource(token="test_token")
        # 替换缓存目录为测试目录
        self.data_source.cache_dir = os.path.join(os.path.dirname(__file__), 'test_cache')
        os.makedirs(self.data_source.cache_dir, exist_ok=True)
    
    def teardown_method(self):
        """测试后清理"""
        # 清理测试缓存
        import shutil
        if os.path.exists(self.data_source.cache_dir):
            shutil.rmtree(self.data_source.cache_dir)
    
    def test_initialization(self):
        """测试初始化"""
        assert self.data_source.token == "test_token"
        assert self.data_source.connected == False
        assert self.data_source.retry_count == 3
        assert os.path.exists(self.data_source.cache_dir)
        
    def test_inheritance(self):
        """测试是否正确继承自BaseDataSource"""
        assert isinstance(self.data_source, BaseDataSource)
    
    def test_connect_success(self):
        """测试连接成功"""
        with patch.object(mock_gm.api, 'set_token') as mock_set_token:
            assert self.data_source.connect() == True
            mock_set_token.assert_called_once_with("test_token")
            assert self.data_source.connected == True
    
    def test_connect_no_token(self):
        """测试没有Token时连接失败"""
        data_source = GmQuantSource()  # 没有提供token
        assert data_source.connect() == False
        assert data_source.connected == False
    
    def test_connect_import_error(self):
        """测试导入错误时连接失败"""
        with patch.object(mock_gm.api, 'set_token', side_effect=ImportError("模块未找到")):
            assert self.data_source.connect() == False
            assert self.data_source.connected == False
    
    def test_connect_general_error(self):
        """测试一般错误时连接失败"""
        with patch.object(mock_gm.api, 'set_token', side_effect=Exception("一般错误")):
            assert self.data_source.connect() == False
            assert self.data_source.connected == False
    
    def test_get_symbols_success(self):
        """测试成功获取标的列表"""
        mock_instruments = [
            {'symbol': 'SHSE.600000', 'sec_name': '浦发银行', 'exchange': 'SHSE'},
            {'symbol': 'SZSE.000001', 'sec_name': '平安银行', 'exchange': 'SZSE'}
        ]
        
        with patch.object(mock_gm.api, 'get_instruments', return_value=mock_instruments) as mock_get:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                symbols = self.data_source.get_symbols()
                assert len(symbols) == 2
                assert 'SHSE.600000' in symbols
                assert 'SZSE.000001' in symbols
                mock_get.assert_called_once()
    
    def test_get_symbols_with_market(self):
        """测试带市场参数获取标的列表"""
        mock_instruments = [
            {'symbol': 'SHSE.600000', 'sec_name': '浦发银行', 'exchange': 'SHSE'},
        ]
        
        with patch.object(mock_gm.api, 'get_instruments', return_value=mock_instruments) as mock_get:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                symbols = self.data_source.get_symbols(market='SHSE')
                assert len(symbols) == 1
                assert 'SHSE.600000' in symbols
                mock_get.assert_called_once_with(exchanges='SHSE', fields='symbol,sec_name,exchange')
    
    def test_get_symbols_connection_failed(self):
        """测试连接失败时获取标的列表"""
        with patch.object(self.data_source, '_ensure_connected', return_value=False):
            symbols = self.data_source.get_symbols()
            assert symbols == []
    
    def test_get_symbols_api_error(self):
        """测试API错误时获取标的列表"""
        with patch.object(mock_gm.api, 'get_instruments', side_effect=Exception("API错误")):
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                symbols = self.data_source.get_symbols()
                assert symbols == []
    
    def test_get_bars_from_cache(self):
        """测试从缓存获取K线数据"""
        # 准备缓存数据
        test_data = """datetime,open,high,low,close,volume
2023-01-01,100,110,95,105,1000
2023-01-02,105,115,100,110,1200"""
        
        cache_file = os.path.join(self.data_source.cache_dir, "SHSE_600000_1d_2023-01-01_2023-01-02_ADJUST_PREV.csv")
        
        with open(cache_file, 'w') as f:
            f.write(test_data)
        
        with patch.object(self.data_source, '_ensure_connected', return_value=True):
            result = self.data_source.get_bars('SHSE.600000', start_date='2023-01-01', end_date='2023-01-02')
            
            assert result is not None
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert 'open' in result.columns
            assert result.index[0] == pd.Timestamp('2023-01-01')
    
    def test_get_bars_api_call(self):
        """测试通过API获取K线数据"""
        # 创建模拟API返回数据
        mock_data = pd.DataFrame({
            'bob': pd.date_range(start='2023-01-01', periods=2, freq='D'),
            'eob': pd.date_range(start='2023-01-01', periods=2, freq='D'),
            'open': [100, 105],
            'high': [110, 115],
            'low': [95, 100],
            'close': [105, 110],
            'volume': [1000, 1200],
            'amount': [100000, 120000],
            'adjusted_factor': [1.0, 1.0],
            'position': [0, 0]
        })
        
        with patch.object(mock_gm.api, 'history', return_value=mock_data) as mock_history:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                with patch('os.path.exists', return_value=False):  # 确保不走缓存
                    result = self.data_source.get_bars(
                        'SHSE.600000', 
                        start_date='2023-01-01', 
                        end_date='2023-01-02',
                        use_cache=False  # 不使用缓存
                    )
                    
                    assert result is not None
                    assert isinstance(result, pd.DataFrame)
                    assert len(result) == 2
                    assert 'open' in result.columns
                    assert 'high' in result.columns
                    assert 'low' in result.columns
                    assert 'close' in result.columns
                    assert 'volume' in result.columns
                    
                    # 验证API调用参数
                    mock_history.assert_called_once()
                    args, kwargs = mock_history.call_args
                    assert kwargs['symbol'] == 'SHSE.600000'
                    assert kwargs['start_time'] == '2023-01-01'
                    assert kwargs['end_time'] == '2023-01-02'
    
    def test_get_bars_frequency_conversion(self):
        """测试K线频率转换"""
        # 测试不同频率的转换正确性
        freq_cases = [
            ('1m', '60s'),
            ('5m', '300s'),
            ('15m', '900s'),
            ('30m', '1800s'),
            ('60m', '3600s'),
            ('1d', '1d'),
            ('1w', '1w'),
            ('1M', '1m')
        ]
        
        mock_data = pd.DataFrame({
            'bob': pd.date_range(start='2023-01-01', periods=2, freq='D'),
            'eob': pd.date_range(start='2023-01-01', periods=2, freq='D'),
            'open': [100, 105],
            'high': [110, 115],
            'low': [95, 100],
            'close': [105, 110],
            'volume': [1000, 1200]
        })
        
        for qte_freq, gm_freq in freq_cases:
            with patch.object(mock_gm.api, 'history', return_value=mock_data) as mock_history:
                with patch.object(self.data_source, '_ensure_connected', return_value=True):
                    with patch('os.path.exists', return_value=False):
                        self.data_source.get_bars(
                            'SHSE.600000', 
                            frequency=qte_freq,
                            use_cache=False
                        )
                        
                        args, kwargs = mock_history.call_args
                        assert kwargs['frequency'] == gm_freq
    
    def test_get_bars_empty_result(self):
        """测试空结果处理"""
        with patch.object(mock_gm.api, 'history', return_value=pd.DataFrame()) as mock_history:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                with patch('os.path.exists', return_value=False):
                    result = self.data_source.get_bars('SHSE.600000', use_cache=False)
                    assert result is None
    
    def test_get_bars_api_error(self):
        """测试API错误处理"""
        with patch.object(mock_gm.api, 'history', side_effect=Exception("API错误")):
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                with patch('os.path.exists', return_value=False):
                    result = self.data_source.get_bars('SHSE.600000', use_cache=False)
                    assert result is None
    
    def test_get_bars_retry_mechanism(self):
        """测试重试机制"""
        # 前两次调用失败，第三次成功
        mock_data = pd.DataFrame({
            'bob': pd.date_range(start='2023-01-01', periods=2, freq='D'),
            'eob': pd.date_range(start='2023-01-01', periods=2, freq='D'),
            'open': [100, 105],
            'high': [110, 115],
            'low': [95, 100],
            'close': [105, 110],
            'volume': [1000, 1200]
        })
        
        with patch.object(mock_gm.api, 'history', side_effect=[Exception("错误1"), Exception("错误2"), mock_data]) as mock_history:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                with patch('os.path.exists', return_value=False):
                    with patch('time.sleep') as mock_sleep:  # 模拟sleep以加速测试
                        result = self.data_source.get_bars('SHSE.600000', use_cache=False)
                        
                        assert result is not None
                        assert len(result) == 2
                        assert mock_history.call_count == 3
                        assert mock_sleep.call_count == 2
    
    def test_get_ticks(self):
        """测试获取Tick数据"""
        # 创建模拟API返回数据
        mock_data = pd.DataFrame({
            'created_at': pd.date_range(start='2023-01-01 09:30:00', periods=5, freq='s'),
            'price': [10.0, 10.1, 10.05, 10.0, 10.2],
            'volume': [100, 200, 150, 300, 250],
            'position': [1000, 1200, 1350, 1650, 1900],
            'trade_type': [0, 0, 0, 0, 0]
        })
        
        with patch.object(mock_gm.api, 'get_ticks', return_value=mock_data) as mock_get_ticks:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                result = self.data_source.get_ticks('SHSE.600000', date='2023-01-01')
                
                assert result is not None
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 5
                assert 'price' in result.columns
                assert 'volume' in result.columns
                assert result.index[0].strftime('%Y-%m-%d') == '2023-01-01'
                
                mock_get_ticks.assert_called_once()
    
    def test_get_fundamentals(self):
        """测试获取基本面数据"""
        # 模拟API返回数据
        mock_data = pd.DataFrame({
            'symbol': ['SHSE.600000', 'SZSE.000001'],
            'date': ['2023-01-01', '2023-01-01'],
            'total_revenue': [1000000, 2000000],
            'net_profit': [100000, 200000]
        })
        
        with patch.object(mock_gm.api, 'get_fundamentals', return_value=mock_data) as mock_get_fundamentals:
            with patch.object(self.data_source, '_ensure_connected', return_value=True):
                result = self.data_source.get_fundamentals(
                    'income', 
                    ['SHSE.600000', 'SZSE.000001'],
                    start_date='2023-01-01',
                    end_date='2023-01-01'
                )
                
                assert result is not None
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 2
                assert 'total_revenue' in result.columns
                assert 'net_profit' in result.columns
                
                mock_get_fundamentals.assert_called_once() 