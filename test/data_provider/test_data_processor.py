"""
数据处理器测试
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 将项目根目录添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from qte.data.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    """测试数据处理器类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试用的分钟K线数据
        dates = pd.date_range(start='2022-01-01', periods=100, freq='1min')
        self.minute_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(105, 115, 100),
            'low': np.random.uniform(95, 105, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # 创建测试用的日K线数据
        dates = pd.date_range(start='2022-01-01', periods=30, freq='1D')
        self.daily_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 30),
            'high': np.random.uniform(105, 115, 30),
            'low': np.random.uniform(95, 105, 30),
            'close': np.random.uniform(100, 110, 30),
            'volume': np.random.randint(10000, 100000, 30),
            'adj_factor': np.linspace(1.0, 1.2, 30)  # 复权因子从1.0到1.2
        }, index=dates)
        
        # 创建用于对齐测试的数据
        dates1 = pd.date_range(start='2022-01-01', periods=20, freq='1D')
        dates2 = pd.date_range(start='2022-01-05', periods=20, freq='1D')
        
        self.data1 = pd.DataFrame({
            'value': np.random.uniform(1, 10, 20)
        }, index=dates1)
        
        self.data2 = pd.DataFrame({
            'value': np.random.uniform(1, 10, 20)
        }, index=dates2)
        
        # 创建带有缺失值的数据
        dates = pd.date_range(start='2022-01-01', periods=10, freq='1D')
        self.missing_data = pd.DataFrame({
            'value': [1.0, 2.0, np.nan, 4.0, np.nan, np.nan, 7.0, 8.0, 9.0, 10.0]
        }, index=dates)
    
    def test_resample_ohlc(self):
        """测试OHLC重采样"""
        # 将1分钟数据重采样为5分钟数据
        result = DataProcessor.resample(
            self.minute_data, 
            source_freq='1min', 
            target_freq='5min', 
            method='ohlc'
        )
        
        # 验证
        self.assertEqual(len(result), len(self.minute_data) // 5)
        self.assertTrue(all(col in result.columns for col in ['open', 'high', 'low', 'close', 'volume']))
        
        # 验证第一个5分钟K线的数据
        first_candle = result.iloc[0]
        first_5min_data = self.minute_data.iloc[:5]
        
        self.assertEqual(first_candle['open'], first_5min_data['open'].iloc[0])
        self.assertEqual(first_candle['high'], first_5min_data['high'].max())
        self.assertEqual(first_candle['low'], first_5min_data['low'].min())
        self.assertEqual(first_candle['close'], first_5min_data['close'].iloc[-1])
        self.assertEqual(first_candle['volume'], first_5min_data['volume'].sum())
    
    def test_resample_last(self):
        """测试last重采样"""
        # 将1分钟数据重采样为5分钟数据，使用last方法
        result = DataProcessor.resample(
            self.minute_data, 
            source_freq='1min', 
            target_freq='5min', 
            method='last'
        )
        
        # 验证
        self.assertEqual(len(result), len(self.minute_data) // 5)
        
        # 验证第一个5分钟K线的数据
        first_candle = result.iloc[0]
        first_5min_data = self.minute_data.iloc[:5]
        
        for col in first_5min_data.columns:
            self.assertEqual(first_candle[col], first_5min_data[col].iloc[-1])
    
    def test_resample_mean(self):
        """测试mean重采样"""
        # 将1分钟数据重采样为5分钟数据，使用mean方法
        result = DataProcessor.resample(
            self.minute_data, 
            source_freq='1min', 
            target_freq='5min', 
            method='mean'
        )
        
        # 验证
        self.assertEqual(len(result), len(self.minute_data) // 5)
        
        # 验证第一个5分钟K线的数据
        first_candle = result.iloc[0]
        first_5min_data = self.minute_data.iloc[:5]
        
        for col in first_5min_data.columns:
            if col == 'volume':
                self.assertEqual(first_candle[col], first_5min_data[col].sum())
            else:
                self.assertAlmostEqual(first_candle[col], first_5min_data[col].mean())
    
    def test_align_multiple_outer(self):
        """测试多个数据源的外连接对齐"""
        # 执行外连接对齐
        result = DataProcessor.align_multiple(
            {'data1': self.data1, 'data2': self.data2},
            method='outer'
        )
        
        # 验证
        self.assertIn('data1', result)
        self.assertIn('data2', result)
        
        # 外连接应该包含所有日期
        expected_dates = self.data1.index.union(self.data2.index)
        self.assertEqual(len(result['data1']), len(expected_dates))
        self.assertEqual(len(result['data2']), len(expected_dates))
        
        # 检查NaN值
        # data1在前5天是有数据的，后面应该有NaN
        self.assertTrue(np.isnan(result['data1']['value'].iloc[-1]))
        # data2在前5天是没有数据的，应该有NaN
        self.assertTrue(np.isnan(result['data2']['value'].iloc[0]))
    
    def test_align_multiple_inner(self):
        """测试多个数据源的内连接对齐"""
        # 执行内连接对齐
        result = DataProcessor.align_multiple(
            {'data1': self.data1, 'data2': self.data2},
            method='inner'
        )
        
        # 验证
        expected_dates = self.data1.index.intersection(self.data2.index)
        self.assertEqual(len(result['data1']), len(expected_dates))
        
        # 内连接不应该有NaN值
        self.assertFalse(np.isnan(result['data1']['value']).any())
        self.assertFalse(np.isnan(result['data2']['value']).any())
    
    def test_align_with_fill(self):
        """测试对齐并填充缺失值"""
        # 执行外连接对齐并向前填充
        result = DataProcessor.align_multiple(
            {'data1': self.data1, 'data2': self.data2},
            method='outer',
            fill_method='ffill'
        )
        
        # 验证填充
        # data2的第一条记录应该仍然是NaN（因为之前没有数据可以向前填充）
        self.assertTrue(np.isnan(result['data2']['value'].iloc[0]))
        # 但第二条记录不应该是NaN（应该被填充）
        self.assertFalse(np.isnan(result['data2']['value'].iloc[1]))
    
    def test_fill_missing_ffill(self):
        """测试向前填充缺失值"""
        # 向前填充
        result = DataProcessor.fill_missing(self.missing_data, method='ffill')
        
        # 验证
        expected = [1.0, 2.0, 2.0, 4.0, 4.0, 4.0, 7.0, 8.0, 9.0, 10.0]
        np.testing.assert_array_equal(result['value'].values, expected)
    
    def test_fill_missing_bfill(self):
        """测试向后填充缺失值"""
        # 向后填充
        result = DataProcessor.fill_missing(self.missing_data, method='bfill')
        
        # 验证
        expected = [1.0, 2.0, 4.0, 4.0, 7.0, 7.0, 7.0, 8.0, 9.0, 10.0]
        np.testing.assert_array_equal(result['value'].values, expected)
    
    def test_fill_missing_limit(self):
        """测试限制填充次数"""
        # 向前填充，最多填充1个
        result = DataProcessor.fill_missing(
            self.missing_data, 
            method='ffill',
            limit=1
        )
        
        # 验证
        expected = [1.0, 2.0, 2.0, 4.0, 4.0, np.nan, 7.0, 8.0, 9.0, 10.0]
        for i in range(len(expected)):
            if np.isnan(expected[i]):
                self.assertTrue(np.isnan(result['value'].iloc[i]))
            else:
                self.assertEqual(result['value'].iloc[i], expected[i])
    
    def test_adjust_price_qfq(self):
        """测试前复权处理"""
        # 前复权
        result = DataProcessor.adjust_price(self.daily_data, adjust_type='qfq')
        
        # 验证
        # 前复权后，最新价格应该不变，而最早的价格应该变小
        latest_factor = self.daily_data['adj_factor'].iloc[-1]
        earliest_factor = self.daily_data['adj_factor'].iloc[0]
        
        # 比较第一条记录的开盘价
        expected_first_open = self.daily_data['open'].iloc[0] * earliest_factor / latest_factor
        self.assertAlmostEqual(result['open'].iloc[0], expected_first_open, places=10)
        
        # 最后一条记录的价格应保持不变
        self.assertEqual(result['open'].iloc[-1], self.daily_data['open'].iloc[-1])
    
    def test_adjust_price_hfq(self):
        """测试后复权处理"""
        # 后复权
        result = DataProcessor.adjust_price(self.daily_data, adjust_type='hfq')
        
        # 验证
        # 后复权后，最早价格应该不变，而最新的价格应该变大
        latest_factor = self.daily_data['adj_factor'].iloc[-1]
        earliest_factor = self.daily_data['adj_factor'].iloc[0]
        
        # 最早的记录的价格应保持不变
        self.assertEqual(result['open'].iloc[0], self.daily_data['open'].iloc[0])
        
        # 比较最后一条记录的收盘价
        expected_last_close = self.daily_data['close'].iloc[-1] * latest_factor / earliest_factor
        self.assertAlmostEqual(result['close'].iloc[-1], expected_last_close, places=10)
    
    def test_adjust_price_none(self):
        """测试不做复权处理"""
        # 不复权
        result = DataProcessor.adjust_price(self.daily_data, adjust_type='none')
        
        # 验证价格没有变化
        pd.testing.assert_frame_equal(result[['open', 'high', 'low', 'close']], 
                                     self.daily_data[['open', 'high', 'low', 'close']])


if __name__ == '__main__':
    unittest.main() 