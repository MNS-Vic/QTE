"""
数据缓存测试

使用TDD方法测试数据缓存系统
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import os
import time
import pickle
import shutil
from tempfile import TemporaryDirectory

from qte.data.data_cache import DataCache, get_cache

class TestDataCache:
    """测试数据缓存"""
    
    def setup_method(self):
        """测试前设置"""
        # 使用临时目录作为缓存目录
        self.temp_dir = TemporaryDirectory()
        self.cache_dir = self.temp_dir.name
        
        # 创建缓存实例
        self.cache = DataCache(
            cache_dir=self.cache_dir,
            max_memory_items=10,  # 设置较小的最大内存项数便于测试
            max_disk_size_mb=5,   # 设置较小的最大磁盘缓存大小便于测试
            default_expire=60     # 设置较短的默认过期时间便于测试
        )
        
        # 创建一些测试数据
        self.test_data_small = "test_data_value"
        self.test_data_large = pd.DataFrame({
            'a': np.random.randn(1000),
            'b': np.random.randn(1000),
            'c': np.random.randn(1000)
        })
    
    def teardown_method(self):
        """测试后清理"""
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """测试初始化"""
        # 验证初始状态
        assert self.cache._memory_cache == {}
        assert os.path.exists(self.cache_dir)
        assert self.cache._max_memory_items == 10
        assert self.cache._max_disk_size == 5 * 1024 * 1024  # 5MB
        assert self.cache._default_expire == 60
    
    def test_normalize_key(self):
        """测试键名标准化"""
        # 测试普通键名
        key = "test_key"
        assert self.cache._normalize_key(key) == key
        
        # 测试包含特殊字符的键名
        key_special = "test/key:with?special*chars"
        normalized = self.cache._normalize_key(key_special)
        assert "/" not in normalized
        assert ":" not in normalized
        assert "?" not in normalized
        assert "*" not in normalized
    
    def test_get_disk_path(self):
        """测试获取磁盘路径"""
        key = "test_key"
        disk_path = self.cache._get_disk_path(key)
        
        # 验证路径是否正确
        assert disk_path.startswith(self.cache_dir)
        assert disk_path.endswith(".cache")
        # 哈希后的路径不再包含原始键名
        # assert "test_key" in disk_path
    
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        key = "test_key"
        value = self.test_data_small
        
        # 设置缓存
        self.cache.set(key, value)
        
        # 验证内存缓存
        assert key in self.cache._memory_cache
        
        # 验证磁盘缓存
        disk_path = self.cache._get_disk_path(key)
        assert os.path.exists(disk_path)
        
        # 获取缓存
        retrieved = self.cache.get(key)
        assert retrieved == value
    
    def test_set_and_get_dataframe(self):
        """测试设置和获取DataFrame数据"""
        key = "test_dataframe"
        value = self.test_data_large
        
        # 设置缓存
        self.cache.set(key, value)
        
        # 获取缓存
        retrieved = self.cache.get(key)
        
        # 验证DataFrame是否相等
        pd.testing.assert_frame_equal(retrieved, value)
    
    def test_expire(self):
        """测试缓存过期"""
        key = "test_expire"
        value = self.test_data_small
        
        # 设置一个很短的过期时间
        self.cache.set(key, value, expire=1)
        
        # 立即获取应该成功
        assert self.cache.get(key) == value
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后获取应该返回None
        assert self.cache.get(key) is None
        
        # 内存缓存中应该没有这个键
        assert key not in self.cache._memory_cache
        
        # 磁盘缓存文件可能仍然存在，但下次清理会删除
        # 调用显式清理
        self.cache._clean_expired_cache()
        disk_path = self.cache._get_disk_path(key)
        assert not os.path.exists(disk_path)
    
    def test_memory_cache_limit(self):
        """测试内存缓存容量限制"""
        # 设置多个缓存项，超过最大内存项数
        for i in range(15):  # 比max_memory_items多
            self.cache.set(f"key_{i}", f"value_{i}")
        
        # 验证内存缓存项数不超过限制
        assert len(self.cache._memory_cache) <= self.cache._max_memory_items
        
        # 但是所有15个项在磁盘上应该都能找到
        for i in range(15):
            disk_path = self.cache._get_disk_path(f"key_{i}")
            assert os.path.exists(disk_path)
    
    def test_disk_cache_limit(self):
        """测试磁盘缓存容量限制"""
        # 创建一个大的数据项逐渐填满磁盘缓存
        # 由于pandas DataFrame已经很大，我们可以多次设置大DataFrame
        for i in range(10):  # 设置足够多的大数据项来触发清理
            df = pd.DataFrame({
                f'col_{j}': np.random.randn(5000) for j in range(10)  # 创建一个大DataFrame
            })
            self.cache.set(f"large_df_{i}", df)
        
        # 获取缓存目录大小
        def get_dir_size(path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size
        
        # 验证磁盘缓存大小不会超出限制太多
        # 注意：清理不是马上发生，所以可能会略微超出限制
        disk_size = get_dir_size(self.cache_dir)
        assert disk_size <= self.cache._max_disk_size * 1.2  # 允许一些容差
    
    def test_clear_cache(self):
        """测试清空缓存"""
        # 设置多个缓存项
        for i in range(5):
            self.cache.set(f"key_{i}", f"value_{i}")
            self.cache.set(f"other_{i}", f"other_value_{i}")
        
        # 验证设置成功
        assert len(self.cache._memory_cache) > 0
        
        # 手动删除key_开头的键
        keys_to_remove = [k for k in list(self.cache._memory_cache.keys()) if k.startswith("key_")]
        for k in keys_to_remove:
            del self.cache._memory_cache[k]
            
        # 验证手动删除后的状态
        assert all(not k.startswith("key_") for k in self.cache._memory_cache.keys())
        assert all(k.startswith("other_") for k in self.cache._memory_cache.keys())
        assert len(self.cache._memory_cache) == 5  # 应该剩下5个other_开头的键
        
        # 清除所有缓存
        self.cache.clear()
        
        # 验证所有缓存都被清除
        assert len(self.cache._memory_cache) == 0
    
    def test_cache_stats(self):
        """测试缓存统计信息"""
        # 设置一些缓存项
        for i in range(5):
            self.cache.set(f"key_{i}", f"value_{i}")
        
        # 获取统计信息
        stats = self.cache.stats()
        
        # 验证统计信息内容
        assert isinstance(stats, dict)
        assert "memory_cache_items" in stats
        assert "disk_cache_items" in stats
        assert "disk_cache_size_mb" in stats
        
        # 验证统计信息正确性
        assert stats["memory_cache_items"] == 5
        assert stats["disk_cache_items"] >= 5
        assert stats["disk_cache_size_mb"] > 0
    
    def test_contains(self):
        """测试包含检查"""
        key = "test_contains"
        value = self.test_data_small
        
        # 设置缓存
        self.cache.set(key, value)
        
        # 验证包含
        assert key in self.cache
        assert "non_existent_key" not in self.cache
    
    def test_match_pattern(self):
        """测试模式匹配"""
        # 测试精确匹配
        assert self.cache._match_pattern("test_key", "test_key") is True
        
        # 测试前缀通配符
        assert self.cache._match_pattern("test_key", "*_key") is True
        assert self.cache._match_pattern("not_match", "*_key") is False
        
        # 测试后缀通配符
        assert self.cache._match_pattern("test_key", "test_*") is True
        assert self.cache._match_pattern("not_match", "test_*") is False
        
        # 测试中间通配符
        assert self.cache._match_pattern("test_some_key", "test_*_key") is True
        assert self.cache._match_pattern("not_match", "test_*_key") is False
        
        # 测试多个通配符
        assert self.cache._match_pattern("test_some_complex_key", "test_*_*_key") is True
        assert self.cache._match_pattern("test_key", "test_*_*_key") is False
    
    def test_disk_cache_reload(self):
        """测试从磁盘重新加载缓存"""
        key = "test_reload"
        value = self.test_data_small
        
        # 设置缓存
        self.cache.set(key, value)
        
        # 清除内存缓存，保留磁盘缓存
        self.cache._memory_cache.clear()
        
        # 重新从磁盘加载
        retrieved = self.cache.get(key)
        assert retrieved == value
        
        # 现在应该在内存缓存中了
        assert key in self.cache._memory_cache
    
    def test_invalid_disk_cache(self):
        """测试无效的磁盘缓存处理"""
        key = "test_invalid"
        disk_path = self.cache._get_disk_path(key)
        
        # 创建一个无效的缓存文件
        with open(disk_path, 'wb') as f:
            f.write(b"invalid data")
        
        # 尝试获取这个无效缓存
        retrieved = self.cache.get(key)
        assert retrieved is None
        
        # 验证无效缓存文件已被删除
        assert not os.path.exists(disk_path)


class TestGlobalCache:
    """测试全局缓存单例"""
    
    def setup_method(self):
        """测试前设置"""
        # 清理全局缓存
        global _GLOBAL_CACHE
        from qte.data.data_cache import _GLOBAL_CACHE
        _GLOBAL_CACHE = None
    
    def test_get_cache_singleton(self):
        """测试获取全局缓存单例"""
        # 获取全局缓存实例
        cache1 = get_cache()
        cache2 = get_cache()
        
        # 验证是同一个实例
        assert cache1 is cache2
        
        # 验证类型正确
        assert isinstance(cache1, DataCache)
    
    def test_global_cache_operations(self):
        """测试全局缓存操作"""
        # 获取全局缓存
        cache = get_cache()
        
        # 设置缓存
        key = "global_test"
        value = "global_value"
        cache.set(key, value)
        
        # 获取缓存
        retrieved = cache.get(key)
        assert retrieved == value
        
        # 清除缓存
        cache.clear(key)
        assert cache.get(key) is None 