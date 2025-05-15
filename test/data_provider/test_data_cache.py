"""
数据缓存测试
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import tempfile
import shutil

# 将项目根目录添加到sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from qte.data.data_cache import DataCache

class TestDataCache(unittest.TestCase):
    """测试数据缓存类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时缓存目录
        self.temp_dir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.temp_dir, max_memory_items=10)
        
        # 创建测试用数据
        dates = pd.date_range(start='2022-01-01', periods=10, freq='1D')
        self.test_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 10),
            'high': np.random.uniform(105, 115, 10),
            'low': np.random.uniform(95, 105, 10),
            'close': np.random.uniform(100, 110, 10),
            'volume': np.random.randint(1000, 10000, 10)
        }, index=dates)
    
    def tearDown(self):
        """测试后清理"""
        # 移除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_set_get_basic(self):
        """测试基本的设置和获取功能"""
        # 设置缓存
        key = "test_data_1"
        self.cache.set(key, self.test_data)
        
        # 获取缓存
        cached_data = self.cache.get(key)
        
        # 验证
        self.assertIsNotNone(cached_data)
        pd.testing.assert_frame_equal(cached_data, self.test_data)
    
    def test_expired_cache(self):
        """测试缓存过期"""
        # 设置缓存，1秒后过期
        key = "test_data_expire"
        self.cache.set(key, self.test_data, expire=1)
        
        # 立即获取，应该存在
        cached_data1 = self.cache.get(key)
        self.assertIsNotNone(cached_data1)
        
        # 等待缓存过期
        time.sleep(1.5)
        
        # 再次获取，应该为None
        cached_data2 = self.cache.get(key)
        self.assertIsNone(cached_data2)
    
    def test_memory_cache_limit(self):
        """测试内存缓存容量限制"""
        # 设置多个缓存项，超过最大内存项数(10)
        for i in range(15):
            key = f"test_data_{i}"
            self.cache.set(key, self.test_data)
        
        # 验证总内存缓存项数不超过限制
        stats = self.cache.stats()
        self.assertLessEqual(stats['memory_items'], 10)
        
        # 验证最新加入的缓存项仍在缓存中
        for i in range(10, 15):
            key = f"test_data_{i}"
            cached_data = self.cache.get(key)
            self.assertIsNotNone(cached_data)
    
    def test_clear_cache(self):
        """测试清除缓存"""
        # 设置多个缓存项
        for i in range(5):
            key = f"test_data_{i}"
            self.cache.set(key, self.test_data)
            
        # 设置一个不同前缀的缓存项
        self.cache.set("other_prefix", self.test_data)
        
        # 清除特定前缀的缓存
        count = self.cache.clear("test_data_*")
        
        # 验证
        self.assertEqual(count, 5)  # 应该清除了5个项
        
        # 验证特定前缀的缓存已被清除
        for i in range(5):
            key = f"test_data_{i}"
            self.assertIsNone(self.cache.get(key))
            
        # 验证其他前缀的缓存仍存在
        self.assertIsNotNone(self.cache.get("other_prefix"))
        
        # 清除所有缓存
        self.cache.clear()
        self.assertIsNone(self.cache.get("other_prefix"))
    
    def test_pattern_matching(self):
        """测试模式匹配"""
        # 设置多个缓存项
        self.cache.set("abc_123", self.test_data)
        self.cache.set("abc_456", self.test_data)
        self.cache.set("xyz_123", self.test_data)
        
        # 测试开头匹配
        count = self.cache.clear("abc_*")
        self.assertEqual(count, 2)
        self.assertIsNone(self.cache.get("abc_123"))
        self.assertIsNone(self.cache.get("abc_456"))
        self.assertIsNotNone(self.cache.get("xyz_123"))
        
        # 设置新的缓存项
        self.cache.set("test_start", self.test_data)
        self.cache.set("test_middle", self.test_data)
        self.cache.set("start_test", self.test_data)
        
        # 测试中间匹配
        count = self.cache.clear("*test*")
        self.assertEqual(count, 3)
    
    def test_disk_cache(self):
        """测试磁盘缓存"""
        # 设置缓存
        key = "disk_test"
        self.cache.set(key, self.test_data)
        
        # 清除内存缓存，但保留磁盘缓存
        self.cache._memory_cache.clear()
        
        # 获取应该从磁盘加载
        cached_data = self.cache.get(key)
        
        # 验证
        self.assertIsNotNone(cached_data)
        pd.testing.assert_frame_equal(cached_data, self.test_data)
        
        # 检查是否已加载到内存
        self.assertIn(key, self.cache._memory_cache)
    
    def test_cache_stats(self):
        """测试缓存统计信息"""
        # 设置多个缓存项
        for i in range(5):
            key = f"stats_test_{i}"
            self.cache.set(key, self.test_data)
        
        # 获取统计信息
        stats = self.cache.stats()
        
        # 验证
        self.assertEqual(stats['memory_items'], 5)
        self.assertEqual(stats['max_memory_items'], 10)
        self.assertGreater(stats['disk_items'], 0)
        self.assertGreater(stats['disk_size_mb'], 0)


if __name__ == '__main__':
    unittest.main()