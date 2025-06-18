#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TimeManager高级功能测试 - TDD方式补充覆盖率
专注于测试未覆盖的核心业务逻辑
"""
import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from qte.core.time_manager import (
    TimeManager, TimeMode, time_manager,
    get_current_timestamp, get_current_time, set_backtest_time,
    set_live_mode, advance_backtest_time, now, timestamp_ms, timestamp_s
)


class TestTimeManagerAdvanced:
    """TimeManager高级功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置时间管理器到初始状态
        time_manager.set_mode(TimeMode.LIVE)
        time_manager._virtual_time = None
        time_manager._time_offset = 0
        time_manager._time_speed = 1.0
        time_manager._start_real_time = None
        time_manager._start_virtual_time = None
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        # Red: 编写失败的测试
        tm1 = TimeManager()
        tm2 = TimeManager()
        
        # 验证是同一个实例
        assert tm1 is tm2
        assert tm1 is time_manager
    
    def test_init_default_state(self):
        """测试初始化默认状态"""
        # Red: 编写失败的测试
        tm = TimeManager()
        
        # 验证默认状态
        assert tm._mode == TimeMode.LIVE
        assert tm._virtual_time is None
        assert tm._time_offset == 0
        assert tm._time_speed == 1.0
        assert tm._start_real_time is None
        assert tm._start_virtual_time is None
        assert hasattr(tm, '_original_time')
        assert hasattr(tm, '_original_time_ns')
    
    def test_set_mode_live(self):
        """测试设置实盘模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        
        # 设置为实盘模式
        tm.set_mode(TimeMode.LIVE)
        
        # 验证模式设置
        assert tm._mode == TimeMode.LIVE
        # 验证时间函数被恢复
        assert time.time == tm._original_time
        assert time.time_ns == tm._original_time_ns
    
    def test_set_mode_backtest(self):
        """测试设置回测模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        original_time_func = time.time
        original_time_ns_func = time.time_ns
        
        # 设置为回测模式
        tm.set_mode(TimeMode.BACKTEST)
        
        # 验证模式设置
        assert tm._mode == TimeMode.BACKTEST
        # 验证时间函数被替换
        assert time.time != original_time_func
        assert time.time_ns != original_time_ns_func
        
        # 恢复原始函数
        tm.set_mode(TimeMode.LIVE)
    
    def test_set_virtual_time_datetime(self):
        """测试设置虚拟时间 - datetime对象"""
        # Red: 编写失败的测试
        tm = TimeManager()
        test_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expected_ms = int(test_dt.timestamp() * 1000)
        
        # 设置虚拟时间
        tm.set_virtual_time(test_dt)
        
        # 验证虚拟时间设置
        assert tm._virtual_time == expected_ms
        assert tm._start_real_time is not None
        assert tm._start_virtual_time == expected_ms
    
    def test_set_virtual_time_float_seconds(self):
        """测试设置虚拟时间 - 浮点数秒"""
        # Red: 编写失败的测试
        tm = TimeManager()
        test_timestamp = 1672574400.5  # 2023-01-01 12:00:00.5
        expected_ms = int(test_timestamp * 1000)
        
        # 设置虚拟时间
        tm.set_virtual_time(test_timestamp)
        
        # 验证虚拟时间设置
        assert tm._virtual_time == expected_ms
    
    def test_set_virtual_time_int_seconds(self):
        """测试设置虚拟时间 - 整数秒"""
        # Red: 编写失败的测试
        tm = TimeManager()
        test_timestamp = 1672574400  # 2023-01-01 12:00:00
        expected_ms = test_timestamp * 1000
        
        # 设置虚拟时间
        tm.set_virtual_time(test_timestamp)
        
        # 验证虚拟时间设置
        assert tm._virtual_time == expected_ms
    
    def test_set_virtual_time_int_milliseconds(self):
        """测试设置虚拟时间 - 整数毫秒"""
        # Red: 编写失败的测试
        tm = TimeManager()
        test_timestamp = 1672574400000  # 2023-01-01 12:00:00 (毫秒)
        
        # 设置虚拟时间
        tm.set_virtual_time(test_timestamp)
        
        # 验证虚拟时间设置
        assert tm._virtual_time == test_timestamp
    
    def test_advance_time_backtest_mode(self):
        """测试推进时间 - 回测模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.BACKTEST)
        tm.set_virtual_time(1672574400000)  # 设置初始时间
        
        initial_time = tm._virtual_time
        delta_seconds = 60.0  # 推进60秒
        
        # 推进时间
        tm.advance_time(delta_seconds)
        
        # 验证时间推进
        expected_time = initial_time + int(delta_seconds * 1000)
        assert tm._virtual_time == expected_time
    
    def test_advance_time_live_mode(self):
        """测试推进时间 - 实盘模式（不应推进）"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.LIVE)
        tm._virtual_time = 1672574400000  # 设置虚拟时间
        
        initial_time = tm._virtual_time
        
        # 尝试推进时间
        tm.advance_time(60.0)
        
        # 验证时间没有推进（实盘模式下）
        assert tm._virtual_time == initial_time
    
    def test_advance_time_no_virtual_time(self):
        """测试推进时间 - 未设置虚拟时间"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.BACKTEST)
        tm._virtual_time = None
        
        # 尝试推进时间（应该不抛出异常）
        tm.advance_time(60.0)
        
        # 验证虚拟时间仍为None
        assert tm._virtual_time is None
    
    def test_get_current_time_live_mode(self):
        """测试获取当前时间 - 实盘模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.LIVE)
        
        # 获取当前时间
        current_time = tm.get_current_time()
        real_time = tm._original_time()
        
        # 验证返回真实时间
        assert abs(current_time - real_time) < 0.1  # 允许小的时间差
    
    def test_get_current_time_backtest_mode(self):
        """测试获取当前时间 - 回测模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.BACKTEST)
        test_time_ms = 1672574400000
        tm.set_virtual_time(test_time_ms)
        
        # 获取当前时间
        current_time = tm.get_current_time()
        expected_time = test_time_ms / 1000
        
        # 验证返回虚拟时间
        assert abs(current_time - expected_time) < 0.001
    
    def test_get_current_time_ms_live_mode(self):
        """测试获取当前时间毫秒 - 实盘模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.LIVE)
        
        # 获取当前时间毫秒
        current_time_ms = tm.get_current_time_ms()
        real_time_ms = int(tm._original_time() * 1000)
        
        # 验证返回真实时间毫秒
        assert abs(current_time_ms - real_time_ms) < 100  # 允许100ms差异
    
    def test_get_current_time_ms_backtest_mode(self):
        """测试获取当前时间毫秒 - 回测模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.BACKTEST)
        test_time_ms = 1672574400000
        tm.set_virtual_time(test_time_ms)
        
        # 获取当前时间毫秒
        current_time_ms = tm.get_current_time_ms()
        
        # 验证返回虚拟时间毫秒
        assert current_time_ms == test_time_ms
    
    def test_get_virtual_time_seconds_no_virtual_time(self):
        """测试获取虚拟时间秒 - 未设置虚拟时间"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm._virtual_time = None
        
        # 获取虚拟时间
        virtual_time = tm._get_virtual_time_seconds()
        real_time = tm._original_time()
        
        # 验证返回真实时间
        assert abs(virtual_time - real_time) < 0.1
    
    def test_get_virtual_time_seconds_with_speed(self):
        """测试获取虚拟时间秒 - 有时间速度"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm._virtual_time = 1672574400000
        tm._start_virtual_time = 1672574400000
        tm._start_real_time = tm._original_time()
        tm._time_speed = 2.0  # 2倍速
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 获取虚拟时间
        virtual_time = tm._get_virtual_time_seconds()
        
        # 验证时间加速效果
        expected_min = 1672574400.0  # 至少是初始时间
        assert virtual_time >= expected_min
    
    def test_get_virtual_time_ms_no_virtual_time(self):
        """测试获取虚拟时间毫秒 - 未设置虚拟时间"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm._virtual_time = None
        
        # 获取虚拟时间毫秒
        virtual_time_ms = tm._get_virtual_time_ms()
        real_time_ms = int(tm._original_time() * 1000)
        
        # 验证返回真实时间毫秒
        assert abs(virtual_time_ms - real_time_ms) < 100
    
    def test_get_virtual_time_ms_with_speed(self):
        """测试获取虚拟时间毫秒 - 有时间速度"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm._virtual_time = 1672574400000
        tm._start_virtual_time = 1672574400000
        tm._start_real_time = tm._original_time()
        tm._time_speed = 2.0  # 2倍速
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 获取虚拟时间毫秒
        virtual_time_ms = tm._get_virtual_time_ms()
        
        # 验证时间加速效果
        expected_min = 1672574400000  # 至少是初始时间
        assert virtual_time_ms >= expected_min

    def test_patch_time_functions(self):
        """测试时间函数替换"""
        # Red: 编写失败的测试
        tm = TimeManager()
        original_time = time.time
        original_time_ns = time.time_ns

        # 替换时间函数
        tm._patch_time_functions()

        # 验证函数被替换
        assert time.time != original_time
        assert time.time_ns != original_time_ns

        # 恢复原始函数
        tm._restore_time_functions()
        assert time.time == original_time
        assert time.time_ns == original_time_ns

    def test_virtual_time_ns_function(self):
        """测试虚拟时间纳秒函数"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.BACKTEST)
        tm.set_virtual_time(1672574400000)  # 设置虚拟时间

        # 调用time.time_ns（应该返回虚拟时间的纳秒）
        time_ns = time.time_ns()
        expected_ns = 1672574400000 * 1000000  # 毫秒转纳秒

        # 验证纳秒时间
        assert abs(time_ns - expected_ns) < 1000000  # 允许1ms误差

        # 恢复实盘模式
        tm.set_mode(TimeMode.LIVE)

    def test_format_time_default(self):
        """测试格式化时间 - 默认当前时间"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.LIVE)

        # 格式化当前时间
        formatted = tm.format_time()

        # 验证格式
        assert "🔴 LIVE" in formatted
        assert "2025" in formatted or "2024" in formatted or "2023" in formatted  # 包含年份
        assert ":" in formatted  # 包含时间分隔符

    def test_format_time_backtest_mode(self):
        """测试格式化时间 - 回测模式"""
        # Red: 编写失败的测试
        tm = TimeManager()
        tm.set_mode(TimeMode.BACKTEST)
        tm.set_virtual_time(1672574400.0)  # 2023-01-01 12:00:00

        # 格式化时间
        formatted = tm.format_time()

        # 验证格式
        assert "⏪ BACKTEST" in formatted
        assert "2023-01-01" in formatted
        assert "12:00:00" in formatted

    def test_format_time_specific_timestamp(self):
        """测试格式化时间 - 指定时间戳"""
        # Red: 编写失败的测试
        tm = TimeManager()
        test_timestamp = 1672574400.0  # 2023-01-01 12:00:00

        # 格式化指定时间
        formatted = tm.format_time(test_timestamp)

        # 验证格式
        assert "2023-01-01" in formatted
        assert "12:00:00" in formatted

    def test_global_functions(self):
        """测试全局函数"""
        # Red: 编写失败的测试
        # 测试get_current_timestamp
        timestamp = get_current_timestamp()
        assert isinstance(timestamp, int)
        assert timestamp > 0

        # 测试get_current_time
        current_time = get_current_time()
        assert isinstance(current_time, float)
        assert current_time > 0

        # 测试timestamp_ms
        ts_ms = timestamp_ms()
        assert isinstance(ts_ms, int)
        assert ts_ms > 0

        # 测试timestamp_s
        ts_s = timestamp_s()
        assert isinstance(ts_s, float)
        assert ts_s > 0

        # 测试now
        dt_now = now()
        assert isinstance(dt_now, datetime)

    def test_set_backtest_time_function(self):
        """测试设置回测时间全局函数"""
        # Red: 编写失败的测试
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # 设置回测时间
        set_backtest_time(test_time)

        # 验证模式和时间设置
        assert time_manager._mode == TimeMode.BACKTEST
        assert time_manager._virtual_time is not None

        # 恢复实盘模式
        set_live_mode()
        assert time_manager._mode == TimeMode.LIVE

    def test_advance_backtest_time_function(self):
        """测试推进回测时间全局函数"""
        # Red: 编写失败的测试
        # 设置回测模式
        set_backtest_time(1672574400.0)
        initial_time = time_manager._virtual_time

        # 推进时间
        advance_backtest_time(60.0)

        # 验证时间推进
        expected_time = initial_time + 60000  # 60秒 = 60000毫秒
        assert time_manager._virtual_time == expected_time

        # 恢复实盘模式
        set_live_mode()

    def test_time_manager_thread_safety(self):
        """测试时间管理器线程安全"""
        # Red: 编写失败的测试
        import threading

        results = []

        def create_time_manager():
            tm = TimeManager()
            results.append(id(tm))

        # 创建多个线程同时创建TimeManager实例
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_time_manager)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有实例都是同一个对象
        assert len(set(results)) == 1  # 所有ID应该相同

    def test_time_manager_reinitialization(self):
        """测试时间管理器重复初始化"""
        # Red: 编写失败的测试
        tm1 = TimeManager()
        original_mode = tm1._mode

        # 修改状态
        tm1._mode = TimeMode.BACKTEST

        # 重新初始化
        tm2 = TimeManager()

        # 验证状态没有被重置（因为已经初始化过）
        assert tm2._mode == TimeMode.BACKTEST
        assert tm1 is tm2

    def test_complex_time_scenario(self):
        """测试复杂时间场景"""
        # Red: 编写失败的测试
        tm = TimeManager()

        # 1. 开始时是实盘模式
        assert tm._mode == TimeMode.LIVE
        live_time = tm.get_current_time()

        # 2. 切换到回测模式
        tm.set_mode(TimeMode.BACKTEST)
        test_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        tm.set_virtual_time(test_time)

        backtest_time = tm.get_current_time()
        assert abs(backtest_time - test_time.timestamp()) < 0.001

        # 3. 推进回测时间
        tm.advance_time(3600)  # 推进1小时
        advanced_time = tm.get_current_time()
        assert advanced_time == test_time.timestamp() + 3600

        # 4. 切换回实盘模式
        tm.set_mode(TimeMode.LIVE)
        final_live_time = tm.get_current_time()
        assert abs(final_live_time - live_time) < 10  # 允许10秒差异

        # 5. 验证时间函数恢复正常
        assert time.time == tm._original_time
        assert time.time_ns == tm._original_time_ns
