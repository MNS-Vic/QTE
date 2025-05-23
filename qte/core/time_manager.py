#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间管理器 - 解决回测与实盘时间戳冲突问题
"""
import time
from typing import Optional, Callable, Union
from datetime import datetime, timezone
from enum import Enum
import threading


class TimeMode(Enum):
    """时间模式"""
    LIVE = "LIVE"          # 实盘模式 - 使用真实时间
    BACKTEST = "BACKTEST"  # 回测模式 - 使用虚拟时间


class TimeManager:
    """
    时间管理器
    
    在回测模式下，提供虚拟时间来替代真实时间，
    确保策略代码在回测和实盘环境下无缝切换。
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TimeManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化时间管理器"""
        if hasattr(self, '_initialized'):
            return
            
        self._mode = TimeMode.LIVE
        self._virtual_time = None  # 虚拟时间（毫秒时间戳）
        self._time_offset = 0      # 时间偏移量
        self._time_speed = 1.0     # 时间流逝速度（回测加速用）
        self._start_real_time = None
        self._start_virtual_time = None
        
        # 保存原始时间函数
        self._original_time = time.time
        self._original_time_ns = time.time_ns
        
        self._initialized = True
    
    def set_mode(self, mode: TimeMode):
        """
        设置时间模式
        
        Parameters
        ----------
        mode : TimeMode
            时间模式
        """
        self._mode = mode
        
        if mode == TimeMode.LIVE:
            self._restore_time_functions()
        else:  # BACKTEST
            self._patch_time_functions()
    
    def set_virtual_time(self, timestamp: Union[int, float, datetime]):
        """
        设置虚拟时间
        
        Parameters
        ----------
        timestamp : Union[int, float, datetime]
            时间戳（秒或毫秒）或datetime对象
        """
        if isinstance(timestamp, datetime):
            # datetime对象转换为毫秒时间戳
            self._virtual_time = int(timestamp.timestamp() * 1000)
        elif isinstance(timestamp, float):
            # 浮点数秒时间戳转换为毫秒
            self._virtual_time = int(timestamp * 1000)
        elif isinstance(timestamp, int):
            # 判断是秒还是毫秒时间戳
            if timestamp > 1e12:  # 毫秒时间戳
                self._virtual_time = timestamp
            else:  # 秒时间戳
                self._virtual_time = timestamp * 1000
        
        # 记录设置虚拟时间的起始点
        self._start_real_time = self._original_time()
        self._start_virtual_time = self._virtual_time
    
    def advance_time(self, delta_seconds: float):
        """
        推进虚拟时间
        
        Parameters
        ----------
        delta_seconds : float
            推进的秒数
        """
        if self._mode == TimeMode.BACKTEST and self._virtual_time is not None:
            self._virtual_time += int(delta_seconds * 1000)
    
    def get_current_time(self) -> float:
        """
        获取当前时间（秒）
        
        Returns
        -------
        float
            当前时间戳（秒）
        """
        if self._mode == TimeMode.LIVE:
            return self._original_time()
        else:
            return self._get_virtual_time_seconds()
    
    def get_current_time_ms(self) -> int:
        """
        获取当前时间（毫秒）
        
        Returns
        -------
        int
            当前时间戳（毫秒）
        """
        if self._mode == TimeMode.LIVE:
            return int(self._original_time() * 1000)
        else:
            return self._get_virtual_time_ms()
    
    def _get_virtual_time_seconds(self) -> float:
        """获取虚拟时间（秒）"""
        if self._virtual_time is None:
            return self._original_time()
        
        # 如果设置了时间流逝速度，计算相对时间
        if self._start_real_time is not None and self._time_speed != 1.0:
            elapsed_real = self._original_time() - self._start_real_time
            elapsed_virtual = elapsed_real * self._time_speed
            return (self._start_virtual_time + elapsed_virtual * 1000) / 1000
        
        return self._virtual_time / 1000
    
    def _get_virtual_time_ms(self) -> int:
        """获取虚拟时间（毫秒）"""
        if self._virtual_time is None:
            return int(self._original_time() * 1000)
        
        # 如果设置了时间流逝速度，计算相对时间
        if self._start_real_time is not None and self._time_speed != 1.0:
            elapsed_real = self._original_time() - self._start_real_time
            elapsed_virtual = elapsed_real * self._time_speed
            return int(self._start_virtual_time + elapsed_virtual * 1000)
        
        return self._virtual_time
    
    def _patch_time_functions(self):
        """在回测模式下，替换系统时间函数"""
        # 替换 time.time
        time.time = self._get_virtual_time_seconds
        
        # 替换 time.time_ns  
        def virtual_time_ns():
            return self._get_virtual_time_ms() * 1000000
        time.time_ns = virtual_time_ns
        
        # 可以根据需要替换更多时间相关函数
        # datetime.now 等
    
    def _restore_time_functions(self):
        """恢复原始时间函数"""
        time.time = self._original_time
        time.time_ns = self._original_time_ns
    
    def format_time(self, timestamp: Optional[float] = None) -> str:
        """
        格式化时间显示
        
        Parameters
        ----------
        timestamp : Optional[float]
            时间戳，默认使用当前时间
            
        Returns
        -------
        str
            格式化的时间字符串
        """
        if timestamp is None:
            timestamp = self.get_current_time()
        
        dt = datetime.fromtimestamp(timestamp)
        mode_str = "🔴 LIVE" if self._mode == TimeMode.LIVE else "⏪ BACKTEST"
        return f"{mode_str} {dt.strftime('%Y-%m-%d %H:%M:%S')}"


# 全局时间管理器实例
time_manager = TimeManager()


def get_current_timestamp() -> int:
    """
    获取当前时间戳（毫秒）
    策略代码应该使用这个函数而不是 time.time()
    
    Returns
    -------
    int
        当前时间戳（毫秒）
    """
    return time_manager.get_current_time_ms()


def get_current_time() -> float:
    """
    获取当前时间（秒）
    
    Returns
    -------
    float
        当前时间戳（秒）
    """
    return time_manager.get_current_time()


def set_backtest_time(timestamp: Union[int, float, datetime]):
    """
    设置回测时间
    
    Parameters
    ----------
    timestamp : Union[int, float, datetime]
        回测时间戳
    """
    time_manager.set_mode(TimeMode.BACKTEST)
    time_manager.set_virtual_time(timestamp)


def set_live_mode():
    """切换到实盘模式"""
    time_manager.set_mode(TimeMode.LIVE)


def advance_backtest_time(delta_seconds: float):
    """
    推进回测时间
    
    Parameters
    ----------
    delta_seconds : float
        推进的秒数
    """
    time_manager.advance_time(delta_seconds)


# 为了兼容现有代码，提供一些常用的时间函数
def now() -> datetime:
    """获取当前datetime对象"""
    return datetime.fromtimestamp(time_manager.get_current_time())


def timestamp_ms() -> int:
    """获取毫秒时间戳"""
    return time_manager.get_current_time_ms()


def timestamp_s() -> float:
    """获取秒时间戳"""
    return time_manager.get_current_time() 