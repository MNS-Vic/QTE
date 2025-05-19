"""
数据缓存模块

提供高效的内存和磁盘缓存功能
"""

from typing import Dict, Any, Optional, List, Union, Tuple
import os
import pickle
import time
import hashlib
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re

# 设置日志
logger = logging.getLogger("DataCache")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 全局缓存实例
_GLOBAL_CACHE = None

def get_cache() -> 'DataCache':
    """
    获取全局缓存实例（单例模式）
    
    Returns
    -------
    DataCache
        全局缓存实例
        
    Examples
    --------
    >>> from qte.data.data_cache import get_cache
    >>> cache = get_cache()
    >>> data = cache.get('my_data_key')
    """
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = DataCache()
    return _GLOBAL_CACHE

class DataCache:
    """
    数据缓存类
    
    实现了内存和磁盘双层缓存机制
    """
    
    def __init__(self, cache_dir: Optional[str] = None, 
                max_memory_items: int = 100,
                max_disk_size_mb: int = 1000,
                default_expire: int = 86400):
        """
        初始化缓存
        
        Parameters
        ----------
        cache_dir : Optional[str], optional
            磁盘缓存目录, by default None (使用默认目录)
        max_memory_items : int, optional
            内存缓存最大项数, by default 100
        max_disk_size_mb : int, optional
            磁盘缓存最大容量(MB), by default 1000
        default_expire : int, optional
            默认过期时间(秒), by default 86400 (1天)
        """
        # 内存缓存
        self._memory_cache: Dict[str, Tuple[Any, float, float]] = {}  # (值, 过期时间, 访问时间)
        self._max_memory_items = max_memory_items
        
        # 磁盘缓存
        if cache_dir is None:
            # 默认缓存目录
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            cache_dir = os.path.join(root_dir, 'cache', 'data_cache')
        
        self._cache_dir = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        self._max_disk_size = max_disk_size_mb * 1024 * 1024  # 转换为字节
        self._default_expire = default_expire
        
        # 初始化时清理过期缓存
        self._clean_expired_cache()
        logger.info(f"数据缓存初始化完成，缓存目录: {self._cache_dir}")
    
    def get(self, key: str) -> Any:
        """
        获取缓存数据
        
        Parameters
        ----------
        key : str
            缓存键名
            
        Returns
        -------
        Any
            缓存数据，如果不存在或已过期则返回None
            
        Examples
        --------
        >>> cache = DataCache()
        >>> data = cache.get('stock_data_SHSE.600000_daily')
        """
        # 标准化键名
        key = self._normalize_key(key)
        
        # 首先检查内存缓存
        if key in self._memory_cache:
            value, expire_time, _ = self._memory_cache[key]
            
            # 检查是否过期
            if expire_time > time.time():
                # 更新访问时间
                self._memory_cache[key] = (value, expire_time, time.time())
                return value
            else:
                # 从内存缓存中删除过期项
                del self._memory_cache[key]
        
        # 如果内存缓存不存在或已过期，检查磁盘缓存
        disk_path = self._get_disk_path(key)
        if os.path.exists(disk_path):
            try:
                with open(disk_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # 检查磁盘缓存是否过期
                if cache_data['expire_time'] > time.time():
                    value = cache_data['value']
                    
                    # 将磁盘缓存加载到内存缓存中
                    self._set_memory_cache(key, value, cache_data['expire_time'])
                    
                    return value
                else:
                    # 删除过期的磁盘缓存
                    os.remove(disk_path)
            except Exception as e:
                logger.warning(f"读取磁盘缓存 '{key}' 时发生错误: {e}")
                # 删除可能损坏的缓存文件
                if os.path.exists(disk_path):
                    os.remove(disk_path)
        
        # 如果缓存不存在或已过期，返回None
        return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """
        设置缓存数据
        
        Parameters
        ----------
        key : str
            缓存键名
        value : Any
            要缓存的数据
        expire : Optional[int], optional
            过期时间(秒), by default None (使用默认过期时间)
            
        Examples
        --------
        >>> cache = DataCache()
        >>> cache.set('stock_data_SHSE.600000_daily', df, expire=3600)  # 缓存1小时
        """
        # 标准化键名
        key = self._normalize_key(key)
        
        # 计算过期时间
        expire_time = time.time() + (expire if expire is not None else self._default_expire)
        
        # 设置内存缓存
        self._set_memory_cache(key, value, expire_time)
        
        # 设置磁盘缓存
        try:
            disk_path = self._get_disk_path(key)
            cache_data = {
                'value': value,
                'expire_time': expire_time,
                'create_time': time.time()
            }
            
            with open(disk_path, 'wb') as f:
                pickle.dump(cache_data, f)
                
            # 检查并清理磁盘缓存
            self._check_disk_cache_size()
            
        except Exception as e:
            logger.warning(f"写入磁盘缓存 '{key}' 时发生错误: {e}")
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        清除缓存
        
        Parameters
        ----------
        pattern : Optional[str], optional
            缓存键名模式，支持简单的通配符, by default None (清除所有缓存)
            
        Returns
        -------
        int
            清除的缓存项数量
            
        Examples
        --------
        >>> cache = DataCache()
        >>> # 清除所有缓存
        >>> cache.clear()
        >>> # 清除特定股票的所有缓存
        >>> cache.clear('stock_data_SHSE.600000_*')
        """
        count = 0
        
        # 如果是单个具体键名且不含通配符，标准化它
        if pattern is not None and '*' not in pattern:
            pattern = self._normalize_key(pattern)
        
        # 清除内存缓存
        if pattern is None:
            # 清除所有内存缓存
            count += len(self._memory_cache)
            self._memory_cache.clear()
        else:
            # 清除匹配模式的内存缓存
            keys_to_remove = []
            
            for key in self._memory_cache:
                if self._match_pattern(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._memory_cache[key]
            
            count += len(keys_to_remove)
        
        # 清除磁盘缓存
        try:
            for filename in os.listdir(self._cache_dir):
                file_path = os.path.join(self._cache_dir, filename)
                
                if os.path.isfile(file_path):
                    # 检查是否是缓存文件
                    if filename.endswith('.cache'):
                        # 对于具体键名，获取对应的磁盘路径
                        if pattern is not None and '*' not in pattern:
                            disk_path = self._get_disk_path(pattern)
                            if os.path.basename(disk_path) == filename:
                                os.remove(file_path)
                                count += 1
                        # 对于模式匹配
                        elif pattern is None or self._match_pattern(self._normalize_key(filename), pattern):
                            os.remove(file_path)
                            count += 1
        except Exception as e:
            logger.warning(f"清除磁盘缓存时发生错误: {e}")
        
        logger.info(f"已清除 {count} 个缓存项")
        return count
    
    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns
        -------
        Dict[str, Any]
            缓存统计信息，包括内存缓存项数、磁盘缓存大小等
            
        Examples
        --------
        >>> cache = DataCache()
        >>> cache.stats()
        {'memory_cache_items': 10, 'disk_cache_size_mb': 50.5, 'disk_cache_items': 100}
        """
        # 计算磁盘缓存大小和项数
        disk_size = 0
        disk_items = 0
        
        try:
            for filename in os.listdir(self._cache_dir):
                file_path = os.path.join(self._cache_dir, filename)
                
                if os.path.isfile(file_path):
                    disk_size += os.path.getsize(file_path)
                    disk_items += 1
        except Exception as e:
            logger.warning(f"获取磁盘缓存统计信息时发生错误: {e}")
        
        # 返回统计信息
        return {
            'memory_cache_items': len(self._memory_cache),
            'max_memory_items': self._max_memory_items,
            'disk_cache_size_mb': disk_size / (1024 * 1024),
            'max_disk_size_mb': self._max_disk_size / (1024 * 1024),
            'disk_cache_items': disk_items
        }
    
    def _normalize_key(self, key: str) -> str:
        """标准化缓存键名"""
        # 替换特殊字符为下划线
        for char in [' ', '/', '\\', ':', '?', '*', '<', '>', '|', '"']: 
            key = key.replace(char, '_')
        return key
    
    def _get_disk_path(self, key: str) -> str:
        """获取磁盘缓存文件路径"""
        # 使用MD5对键名进行哈希，避免文件名过长或包含特殊字符
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self._cache_dir, f"{hashed_key}.cache")
    
    def _set_memory_cache(self, key: str, value: Any, expire_time: float) -> None:
        """设置内存缓存"""
        # 如果内存缓存已满，清理最早访问的项
        if len(self._memory_cache) >= self._max_memory_items and key not in self._memory_cache:
            self._clean_memory_cache()
            
        # 设置内存缓存
        self._memory_cache[key] = (value, expire_time, time.time())
    
    def _clean_memory_cache(self) -> None:
        """清理内存缓存，移除最早访问的项"""
        if not self._memory_cache:
            return
            
        # 按访问时间排序
        sorted_keys = sorted(self._memory_cache.keys(), 
                             key=lambda k: self._memory_cache[k][2])
        
        # 移除前25%的项或至少一个
        remove_count = max(1, len(sorted_keys) // 4)
        for i in range(remove_count):
            del self._memory_cache[sorted_keys[i]]
            
        logger.debug(f"已清理 {remove_count} 个内存缓存项")
    
    def _clean_expired_cache(self) -> None:
        """清理过期的缓存项"""
        # 清理内存缓存
        now = time.time()
        expired_keys = [k for k, (_, expire_time, _) in self._memory_cache.items() 
                       if expire_time <= now]
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        # 清理磁盘缓存
        try:
            expired_count = 0
            for filename in os.listdir(self._cache_dir):
                file_path = os.path.join(self._cache_dir, filename)
                
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            cache_data = pickle.load(f)
                        
                        if cache_data['expire_time'] <= now:
                            os.remove(file_path)
                            expired_count += 1
                    except Exception:
                        # 删除可能损坏的缓存文件
                        os.remove(file_path)
                        expired_count += 1
            
            if expired_count > 0:
                logger.info(f"已清理 {expired_count} 个过期的磁盘缓存项")
        except Exception as e:
            logger.warning(f"清理过期磁盘缓存时发生错误: {e}")
    
    def _check_disk_cache_size(self) -> None:
        """检查并清理磁盘缓存大小"""
        try:
            # 计算当前磁盘缓存大小
            total_size = 0
            file_info = []
            
            for filename in os.listdir(self._cache_dir):
                file_path = os.path.join(self._cache_dir, filename)
                
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_mtime = os.path.getmtime(file_path)
                    total_size += file_size
                    file_info.append((file_path, file_size, file_mtime))
            
            # 如果超过最大限制，删除最旧的文件直到大小符合要求
            if total_size > self._max_disk_size:
                # 按修改时间排序
                file_info.sort(key=lambda x: x[2])
                
                # 需要删除的大小
                need_to_free = total_size - self._max_disk_size * 0.8  # 释放到80%
                freed_size = 0
                deleted_count = 0
                
                for file_path, file_size, _ in file_info:
                    os.remove(file_path)
                    freed_size += file_size
                    deleted_count += 1
                    
                    if freed_size >= need_to_free:
                        break
                
                logger.info(f"磁盘缓存超过限制，已删除 {deleted_count} 个文件，释放 {freed_size/(1024*1024):.2f} MB")
        except Exception as e:
            logger.warning(f"检查磁盘缓存大小时发生错误: {e}")
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """
        简单的模式匹配，支持 * 通配符
        * 表示匹配任意字符序列
        """
        if pattern == '*':
            return True
            
        if '*' not in pattern:
            # 没有通配符，精确匹配
            return key == pattern
        
        # 转换为正则表达式
        regex_pattern = pattern.replace('.', '\\.').replace('*', '.*')
        return re.match(f"^{regex_pattern}$", key) is not None
            
    def __contains__(self, key: str) -> bool:
        """实现'in'操作符，检查缓存是否包含指定键名
        
        Examples
        --------
        >>> cache = DataCache()
        >>> cache.set("test_key", "test_value")
        >>> "test_key" in cache
        True
        """
        # 标准化键名
        key = self._normalize_key(key)
        
        # 先检查内存缓存
        if key in self._memory_cache:
            value, expire_time, _ = self._memory_cache[key]
            # 检查是否过期
            if expire_time > time.time():
                return True
                
        # 再检查磁盘缓存
        disk_path = self._get_disk_path(key)
        if os.path.exists(disk_path):
            try:
                with open(disk_path, "rb") as f:
                    cache_data = pickle.load(f)
                # 检查是否过期
                if cache_data["expire_time"] > time.time():
                    return True
            except Exception:
                pass
                
        return False