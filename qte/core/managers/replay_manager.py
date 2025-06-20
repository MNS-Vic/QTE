#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据重放管理器

专门负责历史数据重放、时间控制和数据流管理
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import pandas as pd
import numpy as np

from qte.core.events import Event as CoreEvent, MarketEvent as CoreMarketEvent
from .base_manager import BaseManager
from .event_manager import EventManager


class ReplayManager(BaseManager):
    """
    数据重放管理器
    
    负责历史数据的时序重放、速度控制和数据流管理
    """
    
    def __init__(self, event_manager: EventManager, name: str = "ReplayManager"):
        """
        初始化数据重放管理器
        
        Parameters
        ----------
        event_manager : EventManager
            事件管理器实例
        name : str, optional
            管理器名称
        """
        super().__init__(name)
        
        self.event_manager = event_manager
        
        # 数据和配置
        self._data_sources: Dict[str, pd.DataFrame] = {}
        self._replay_config = {
            'speed_multiplier': 1.0,  # 重放速度倍数
            'start_time': None,       # 开始时间
            'end_time': None,         # 结束时间
            'time_column': 'timestamp',  # 时间列名
            'batch_size': 1000,       # 批处理大小
        }
        
        # 重放控制
        self._replay_thread = None
        self._stop_replay = threading.Event()
        self._pause_replay = threading.Event()
        self._pause_replay.set()  # 开始时不暂停
        
        # 重放状态
        self._current_time = None
        self._replay_start_time = None
        self._replay_end_time = None
        self._total_events = 0
        self._processed_events = 0
        
        # 回调函数
        self._data_callbacks: Dict[str, List[Callable]] = {}
        
        # 性能统计
        self._performance_stats = {
            "total_events": 0,
            "processed_events": 0,
            "start_time": None,
            "end_time": None,
            "replay_speed": 0.0,
            "current_progress": 0.0
        }
        
        self.logger.info("✅ 数据重放管理器初始化完成")
    
    def add_data_source(self, source_name: str, data: pd.DataFrame) -> bool:
        """
        添加数据源
        
        Parameters
        ----------
        source_name : str
            数据源名称
        data : pd.DataFrame
            数据框，必须包含时间列
            
        Returns
        -------
        bool
            添加是否成功
        """
        try:
            if not isinstance(data, pd.DataFrame):
                self.logger.error("数据必须是pandas DataFrame")
                return False
            
            time_column = self._replay_config['time_column']
            if time_column not in data.columns:
                self.logger.error(f"数据缺少时间列: {time_column}")
                return False
            
            # 确保时间列是datetime类型
            if not pd.api.types.is_datetime64_any_dtype(data[time_column]):
                try:
                    data[time_column] = pd.to_datetime(data[time_column])
                except Exception as e:
                    self.logger.error(f"时间列转换失败: {e}")
                    return False
            
            # 按时间排序
            data_sorted = data.sort_values(time_column).reset_index(drop=True)
            
            self._data_sources[source_name] = data_sorted
            self.logger.info(f"✅ 已添加数据源 '{source_name}': {len(data_sorted)} 行数据")
            
            # 更新总事件数
            self._total_events += len(data_sorted)
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加数据源失败: {e}")
            return False
    
    def set_replay_config(self, config: Dict[str, Any]) -> bool:
        """
        设置重放配置
        
        Parameters
        ----------
        config : Dict[str, Any]
            重放配置参数
            
        Returns
        -------
        bool
            设置是否成功
        """
        try:
            # 验证配置
            if 'speed_multiplier' in config:
                speed = config['speed_multiplier']
                if not isinstance(speed, (int, float)) or speed <= 0:
                    self.logger.error("速度倍数必须是正数")
                    return False
            
            if 'batch_size' in config:
                batch_size = config['batch_size']
                if not isinstance(batch_size, int) or batch_size <= 0:
                    self.logger.error("批处理大小必须是正整数")
                    return False
            
            # 更新配置
            self._replay_config.update(config)
            self.logger.info(f"✅ 重放配置已更新: {config}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置重放配置失败: {e}")
            return False
    
    def register_data_callback(self, source_name: str, callback: Callable[[str, Dict[str, Any]], None]) -> bool:
        """
        注册数据回调函数
        
        Parameters
        ----------
        source_name : str
            数据源名称
        callback : Callable[[str, Dict[str, Any]], None]
            回调函数，接收(source_name, data_row)参数
            
        Returns
        -------
        bool
            注册是否成功
        """
        if not callable(callback):
            self.logger.error("回调函数必须是可调用对象")
            return False
        
        if source_name not in self._data_callbacks:
            self._data_callbacks[source_name] = []
        
        if callback not in self._data_callbacks[source_name]:
            self._data_callbacks[source_name].append(callback)
            self.logger.debug(f"✅ 已注册数据回调: {source_name}")
            return True
        
        return True
    
    def start_replay(self) -> bool:
        """
        开始数据重放
        
        Returns
        -------
        bool
            启动是否成功
        """
        if not self._data_sources:
            self.logger.error("没有可重放的数据源")
            return False
        
        if self._replay_thread and self._replay_thread.is_alive():
            self.logger.warning("重放线程已在运行")
            return False
        
        # 准备重放
        self._prepare_replay()
        
        # 启动重放线程
        self._stop_replay.clear()
        self._pause_replay.set()
        
        self._replay_thread = threading.Thread(
            target=self._replay_loop,
            name=f"{self.name}_ReplayThread"
        )
        self._replay_thread.daemon = True
        self._replay_thread.start()
        
        self._performance_stats["start_time"] = time.time()
        
        self.logger.info(f"🚀 数据重放已启动，总事件数: {self._total_events}")
        return True
    
    def stop_replay(self) -> bool:
        """
        停止数据重放
        
        Returns
        -------
        bool
            停止是否成功
        """
        self._stop_replay.set()
        self._pause_replay.set()
        
        if self._replay_thread:
            self._replay_thread.join(timeout=3.0)
            if self._replay_thread.is_alive():
                self.logger.warning("重放线程未在超时内结束")
            else:
                self.logger.info("✅ 数据重放已停止")
        
        self._performance_stats["end_time"] = time.time()
        return True
    
    def pause_replay(self) -> bool:
        """
        暂停数据重放
        
        Returns
        -------
        bool
            暂停是否成功
        """
        self._pause_replay.clear()
        self.logger.info("⏸️ 数据重放已暂停")
        return True
    
    def resume_replay(self) -> bool:
        """
        恢复数据重放
        
        Returns
        -------
        bool
            恢复是否成功
        """
        self._pause_replay.set()
        self.logger.info("▶️ 数据重放已恢复")
        return True
    
    def get_replay_progress(self) -> Dict[str, Any]:
        """
        获取重放进度
        
        Returns
        -------
        Dict[str, Any]
            重放进度信息
        """
        progress = 0.0
        if self._total_events > 0:
            progress = self._processed_events / self._total_events
        
        return {
            "total_events": self._total_events,
            "processed_events": self._processed_events,
            "progress": progress,
            "current_time": self._current_time,
            "replay_start_time": self._replay_start_time,
            "replay_end_time": self._replay_end_time
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns
        -------
        Dict[str, Any]
            性能统计信息
        """
        stats = self._performance_stats.copy()
        
        # 计算重放速度
        start_time = stats.get("start_time")
        if start_time:
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                stats["replay_speed"] = self._processed_events / elapsed_time
        
        # 添加进度信息
        stats.update(self.get_replay_progress())
        
        return stats
    
    def _prepare_replay(self):
        """准备重放数据"""
        # 合并所有数据源并按时间排序
        all_data = []
        time_column = self._replay_config['time_column']
        
        for source_name, data in self._data_sources.items():
            data_with_source = data.copy()
            data_with_source['_source'] = source_name
            all_data.append(data_with_source)
        
        if all_data:
            self._merged_data = pd.concat(all_data, ignore_index=True)
            self._merged_data = self._merged_data.sort_values(time_column).reset_index(drop=True)
            
            # 设置时间范围
            self._replay_start_time = self._merged_data[time_column].iloc[0]
            self._replay_end_time = self._merged_data[time_column].iloc[-1]
            self._current_time = self._replay_start_time
            
            self.logger.info(f"📊 重放数据准备完成: {len(self._merged_data)} 行，时间范围: {self._replay_start_time} - {self._replay_end_time}")
    
    def _replay_loop(self):
        """重放循环，在单独线程中运行"""
        self.logger.info("🚀 数据重放线程启动")
        
        time_column = self._replay_config['time_column']
        speed_multiplier = self._replay_config['speed_multiplier']
        batch_size = self._replay_config['batch_size']
        
        last_timestamp = None
        processed_in_session = 0
        
        try:
            for index, row in self._merged_data.iterrows():
                # 检查停止信号
                if self._stop_replay.is_set():
                    break
                
                # 等待恢复（如果暂停）
                if not self._pause_replay.wait(timeout=0.1):
                    continue
                
                current_timestamp = row[time_column]
                source_name = row['_source']
                
                # 时间控制
                if last_timestamp is not None and speed_multiplier > 0:
                    time_diff = (current_timestamp - last_timestamp).total_seconds()
                    sleep_time = time_diff / speed_multiplier
                    if sleep_time > 0:
                        time.sleep(min(sleep_time, 1.0))  # 最大睡眠1秒
                
                # 处理数据行
                self._process_data_row(source_name, row.to_dict())
                
                # 更新状态
                self._current_time = current_timestamp
                self._processed_events += 1
                processed_in_session += 1
                last_timestamp = current_timestamp
                
                # 批量进度报告
                if processed_in_session % batch_size == 0:
                    progress = self._processed_events / self._total_events * 100
                    self.logger.debug(f"📊 重放进度: {progress:.1f}% ({self._processed_events}/{self._total_events})")
        
        except Exception as e:
            self.logger.error(f"重放循环异常: {e}", exc_info=True)
        
        self.logger.info(f"🏁 数据重放线程结束，本次处理: {processed_in_session} 事件")
    
    def _process_data_row(self, source_name: str, data_row: Dict[str, Any]):
        """
        处理单行数据
        
        Parameters
        ----------
        source_name : str
            数据源名称
        data_row : Dict[str, Any]
            数据行
        """
        try:
            # 移除内部字段
            clean_data = {k: v for k, v in data_row.items() if not k.startswith('_')}
            
            # 调用注册的回调函数
            if source_name in self._data_callbacks:
                for callback in self._data_callbacks[source_name]:
                    try:
                        callback(source_name, clean_data)
                    except Exception as e:
                        self.logger.error(f"数据回调函数执行失败: {e}")
            
            # 创建并发送市场数据事件
            if 'symbol' in clean_data:
                timestamp = clean_data.get(self._replay_config['time_column'])
                if timestamp:
                    # 创建CoreEvent并发送到事件管理器
                    core_event = CoreEvent(
                        event_type="MARKET_DATA",
                        timestamp=timestamp,
                        data=clean_data
                    )
                    self.event_manager.send_event(core_event)
            
        except Exception as e:
            self.logger.error(f"处理数据行失败: {e}")
            self.logger.debug(f"问题数据: {data_row}")
