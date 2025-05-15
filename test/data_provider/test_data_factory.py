"""
数据源工厂测试
"""

import unittest
import os
import sys
import pandas as pd
from datetime import datetime
import logging

# 将项目根目录添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from qte.data.data_factory import DataSourceFactory
from qte.data.sources.local_csv import LocalCsvSource
from qte.data.sources.gm_quant import GmQuantSource

# 定义测试用的简单数据源类
class CustomTestSource:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'default')
        
class AnotherTestSource:
    def __init__(self, **kwargs):
        self.value = kwargs.get('value', 0)

class TestDataSourceFactory(unittest.TestCase):
    """测试数据源工厂类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类启动时的准备工作"""
        # 注册测试用的数据源类型
        DataSourceFactory.register_creator('test_custom', lambda **kwargs: CustomTestSource(**kwargs))
        DataSourceFactory.register_source_class('test_another', AnotherTestSource)
        
        # 关闭DataSourceFactory的日志输出以避免测试输出过多日志
        logging.getLogger("DataSourceFactory").setLevel(logging.ERROR)
    
    def test_create_csv_source(self):
        """测试创建CSV数据源"""
        # 创建CSV数据源
        csv_source = DataSourceFactory.create('csv', base_path='examples/test_data/')
        
        # 验证返回的是正确的实例类型
        self.assertIsNotNone(csv_source)
        self.assertIsInstance(csv_source, LocalCsvSource)
        self.assertEqual(csv_source.base_path, 'examples/test_data/')
    
    def test_create_gm_source(self):
        """测试创建掘金数据源"""
        # 创建掘金数据源
        token = "test_token"
        gm_source = DataSourceFactory.create('gm', token=token)
        
        # 验证返回的是正确的实例类型
        self.assertIsNotNone(gm_source)
        self.assertIsInstance(gm_source, GmQuantSource)
        self.assertEqual(gm_source.token, token)
    
    def test_create_unknown_source(self):
        """测试创建未知数据源"""
        # 尝试创建未知数据源
        unknown_source = DataSourceFactory.create('unknown')
        
        # 验证返回的是None
        self.assertIsNone(unknown_source)
    
    def test_list_available_sources(self):
        """测试列出可用数据源类型"""
        # 列出可用的数据源类型
        sources = DataSourceFactory.list_available_sources()
        
        # 验证必须包含的数据源类型
        self.assertIsInstance(sources, list)
        self.assertIn('csv', sources)
        self.assertIn('gm', sources)
        self.assertIn('test_custom', sources)
        self.assertIn('test_another', sources)
    
    def test_custom_source_creation(self):
        """测试创建自定义数据源"""
        # 创建自定义数据源
        custom_source = DataSourceFactory.create('test_custom', name='test_name')
        
        # 验证
        self.assertIsNotNone(custom_source)
        self.assertIsInstance(custom_source, CustomTestSource)
        self.assertEqual(custom_source.name, 'test_name')
    
    def test_another_source_creation(self):
        """测试创建第二种自定义数据源"""
        # 创建数据源
        another_source = DataSourceFactory.create('test_another', value=42)
        
        # 验证
        self.assertIsNotNone(another_source)
        self.assertIsInstance(another_source, AnotherTestSource)
        self.assertEqual(another_source.value, 42)
    
    def test_case_insensitive(self):
        """测试数据源类型大小写不敏感"""
        # 使用大写和混合大小写测试
        csv_upper = DataSourceFactory.create('CSV')
        csv_mixed = DataSourceFactory.create('Csv')
        
        # 验证
        self.assertIsNotNone(csv_upper)
        self.assertIsInstance(csv_upper, LocalCsvSource)
        self.assertIsNotNone(csv_mixed)
        self.assertIsInstance(csv_mixed, LocalCsvSource)


if __name__ == '__main__':
    unittest.main() 