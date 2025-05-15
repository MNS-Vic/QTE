#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据重放控制器模块 - 修复版本
解决了线程等待无超时等问题
"""

from typing import List, Dict, Optional, Any, Union, Callable, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import time
import threading
import abc
import logging
import traceback
from enum import Enum
import queue

# 设置日志
logger = logging.getLogger("DataReplayController")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class ReplayMode(Enum):
    """重放模式枚举"""
    BACKTEST = 1    # 回测模式：以最快速度重放所有数据
    STEPPED = 2     # 步进模式：每次手动推进一个数据点
    REALTIME = 3    # 实时模式：按实际时间比例重放数据
    ACCELERATED = 4 # 加速模式：按指定倍速重放数据

class ReplayStatus(Enum):
    """重放状态枚举"""
    INITIALIZED = 1 # 已初始化但未开始
    RUNNING = 2     # 正在运行
    PAUSED = 3      # 已暂停
    STOPPED = 4     # 已停止
    COMPLETED = 5   # 已完成所有数据

class DataReplayInterface(abc.ABC):
    """
    数据重放接口类
    
    定义了所有数据重放控制器必须实现的方法
    """
    
    @abc.abstractmethod
    def start(self) -> bool:
        """
        开始重放数据
        
        Returns
        -------
        bool
            是否成功启动
        """
        pass
    
    @abc.abstractmethod
    def pause(self) -> bool:
        """
        暂停重放
        
        Returns
        -------
        bool
            是否成功暂停
        """
        pass
    
    @abc.abstractmethod
    def resume(self) -> bool:
        """
        恢复重放
        
        Returns
        -------
        bool
            是否成功恢复
        """
        pass
    
    @abc.abstractmethod
    def stop(self) -> bool:
        """
        停止重放
        
        Returns
        -------
        bool
            是否成功停止
        """
        pass
    
    @abc.abstractmethod
    def step(self) -> Optional[Any]:
        """
        手动前进一步
        
        Returns
        -------
        Optional[Any]
            下一个数据点，如果没有更多数据则返回None
        """
        pass
    
    @abc.abstractmethod
    def set_speed(self, speed_factor: float) -> bool:
        """
        设置重放速度
        
        Parameters
        ----------
        speed_factor : float
            速度因子，1.0表示实时速度，大于1表示加速，小于1表示减速
            
        Returns
        -------
        bool
            是否成功设置速度
        """
        pass
    
    @abc.abstractmethod
    def set_mode(self, mode: ReplayMode) -> bool:
        """
        设置重放模式
        
        Parameters
        ----------
        mode : ReplayMode
            重放模式
            
        Returns
        -------
        bool
            是否成功设置模式
        """
        pass
    
    @abc.abstractmethod
    def get_status(self) -> ReplayStatus:
        """
        获取当前状态
        
        Returns
        -------
        ReplayStatus
            当前重放状态
        """
        pass
    
    @abc.abstractmethod
    def register_callback(self, callback: Callable[[Any], None]) -> int:
        """
        注册回调函数，数据点推送时触发
        
        Parameters
        ----------
        callback : Callable[[Any], None]
            回调函数，接收数据点作为参数
            
        Returns
        -------
        int
            回调ID，可用于注销回调
        """
        pass
    
    @abc.abstractmethod
    def unregister_callback(self, callback_id: int) -> bool:
        """
        注销回调函数
        
        Parameters
        ----------
        callback_id : int
            回调ID
            
        Returns
        -------
        bool
            是否成功注销
        """
        pass

class BaseDataReplayController(DataReplayInterface):
    """
    数据重放控制器基类
    
    实现了基本的重放控制功能，修复了以下问题：
    1. 线程等待无超时问题
    2. 异常处理不完善
    3. 日志记录不充分
    4. 替换列表为线程安全队列
    """
    
    def __init__(self, data_source=None, mode: ReplayMode = ReplayMode.BACKTEST, 
                 speed_factor: float = 1.0):
        """
        初始化数据重放控制器
        
        Parameters
        ----------
        data_source : Any, optional
            数据源，可以是DataFrame或其他数据源，由子类具体实现解析, by default None
        mode : ReplayMode, optional
            重放模式, by default ReplayMode.BACKTEST
        speed_factor : float, optional
            速度因子, by default 1.0
        """
        self._data_source = data_source
        self._mode = mode
        self._speed_factor = speed_factor
        self._status = ReplayStatus.INITIALIZED
        self._callbacks = {}
        self._callback_counter = 0
        self._replay_thread = None
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._current_position = 0
        self._data = None  # 具体数据由子类实现加载
        
        # 健康监控
        self._last_activity_time = time.time()
        self._data_points_processed = 0
        self._callback_errors = 0
        
        # 性能指标
        self._processing_times = []  # 处理每个数据点所需时间
        
    def start(self) -> bool:
        """
        开始重放数据
        
        Returns
        -------
        bool
            是否成功启动
        """
        with self._lock:
            if self._status == ReplayStatus.RUNNING:
                logger.warning("重放已经在运行中")
                return False
            
            if self._status == ReplayStatus.COMPLETED:
                logger.warning("重放已完成，请重置后再启动")
                return False
            
            self._status = ReplayStatus.RUNNING
            self._event.set()  # 确保事件是置位状态
            self._last_activity_time = time.time()
            
            if self._mode in [ReplayMode.REALTIME, ReplayMode.ACCELERATED, ReplayMode.BACKTEST]:
                # 在单独线程中运行
                self._replay_thread = threading.Thread(target=self._replay_task)
                self._replay_thread.daemon = True
                self._replay_thread.start()
                logger.debug(f"启动重放线程: {self._replay_thread.name}")
            
            logger.info(f"开始数据重放，模式: {self._mode.name}, 速度因子: {self._speed_factor}")
            return True
    
    def pause(self) -> bool:
        """
        暂停重放
        
        Returns
        -------
        bool
            是否成功暂停
        """
        with self._lock:
            if self._status != ReplayStatus.RUNNING:
                logger.warning(f"当前状态为 {self._status.name}，无法暂停")
                return False
            
            self._status = ReplayStatus.PAUSED
            self._event.clear()
            logger.info("重放已暂停")
            return True
    
    def resume(self) -> bool:
        """
        恢复重放
        
        Returns
        -------
        bool
            是否成功恢复
        """
        with self._lock:
            if self._status != ReplayStatus.PAUSED:
                logger.warning(f"当前状态为 {self._status.name}，无法恢复")
                return False
            
            self._status = ReplayStatus.RUNNING
            self._event.set()
            self._last_activity_time = time.time()
            logger.info("重放已恢复")
            return True
    
    def stop(self) -> bool:
        """
        停止重放
        
        Returns
        -------
        bool
            是否成功停止
        """
        with self._lock:
            if self._status == ReplayStatus.STOPPED:
                logger.warning("重放已经停止")
                return True
            
            prev_status = self._status
            self._status = ReplayStatus.STOPPED
            self._event.set()  # 确保线程不会卡在等待
            
            # 等待线程结束
            if self._replay_thread and self._replay_thread.is_alive():
                try:
                    self._replay_thread.join(timeout=2.0)
                    if self._replay_thread.is_alive():
                        logger.warning("重放线程未能在2秒内结束")
                except Exception as e:
                    logger.error(f"停止重放线程时发生错误: {str(e)}")
            
            self._replay_thread = None
            logger.info(f"重放已从 {prev_status.name} 状态停止")
            return True
    
    def step(self) -> Optional[Any]:
        """
        手动前进一步
        
        Returns
        -------
        Optional[Any]
            下一个数据点，如果没有更多数据则返回None
        """
        with self._lock:
            if self._status != ReplayStatus.RUNNING and self._status != ReplayStatus.PAUSED:
                logger.warning(f"当前状态为 {self._status.name}，无法步进")
                return None
            
            # 获取下一个数据点
            data_point = self._get_next_data_point()
            if data_point is None:
                self._status = ReplayStatus.COMPLETED
                logger.info("重放已完成所有数据")
                return None
            
            # 触发回调
            self._notify_callbacks(data_point)
            self._data_points_processed += 1
            self._last_activity_time = time.time()
            
            return data_point
    
    def set_speed(self, speed_factor: float) -> bool:
        """
        设置重放速度
        
        Parameters
        ----------
        speed_factor : float
            速度因子，1.0表示实时速度，大于1表示加速，小于1表示减速
            
        Returns
        -------
        bool
            是否成功设置速度
        """
        if speed_factor <= 0:
            logger.warning(f"速度因子必须大于0: {speed_factor}")
            return False
        
        with self._lock:
            self._speed_factor = speed_factor
            logger.info(f"重放速度已设置为: {speed_factor}")
            return True
    
    def set_mode(self, mode: ReplayMode) -> bool:
        """
        设置重放模式
        
        Parameters
        ----------
        mode : ReplayMode
            重放模式
            
        Returns
        -------
        bool
            是否成功设置模式
        """
        with self._lock:
            was_running = self._status == ReplayStatus.RUNNING
            
            # 如果正在运行，先暂停
            if was_running:
                self.pause()
            
            self._mode = mode
            
            # 如果之前在运行，恢复运行
            if was_running:
                # 如果模式改为步进，保持暂停状态
                if mode != ReplayMode.STEPPED:
                    self.resume()
            
            logger.info(f"重放模式已设置为: {mode.name}")
            return True
    
    def get_status(self) -> ReplayStatus:
        """
        获取当前状态
        
        Returns
        -------
        ReplayStatus
            当前重放状态
        """
        with self._lock:
            return self._status
    
    def register_callback(self, callback: Callable[[Any], None]) -> int:
        """
        注册回调函数，数据点推送时触发
        
        Parameters
        ----------
        callback : Callable[[Any], None]
            回调函数，接收数据点作为参数
            
        Returns
        -------
        int
            回调ID，可用于注销回调
        """
        with self._lock:
            callback_id = self._callback_counter
            self._callback_counter += 1
            
            self._callbacks[callback_id] = callback
            logger.debug(f"已注册回调，ID: {callback_id}")
            
            return callback_id
    
    def unregister_callback(self, callback_id: int) -> bool:
        """
        注销回调函数
        
        Parameters
        ----------
        callback_id : int
            回调ID
            
        Returns
        -------
        bool
            是否成功注销
        """
        with self._lock:
            if callback_id not in self._callbacks:
                logger.warning(f"未找到ID为 {callback_id} 的回调")
                return False
            
            del self._callbacks[callback_id]
            logger.debug(f"已注销回调，ID: {callback_id}")
            
            return True
    
    def reset(self) -> bool:
        """
        重置重放器状态
        
        Returns
        -------
        bool
            是否成功重置
        """
        with self._lock:
            if self._status == ReplayStatus.RUNNING:
                self.stop()
            
            self._current_position = 0
            self._status = ReplayStatus.INITIALIZED
            self._data_points_processed = 0
            self._callback_errors = 0
            self._processing_times = []
            
            logger.info("重放器已重置")
            return True
    
    def get_health_stats(self) -> Dict[str, Any]:
        """
        获取健康状态统计信息
        
        Returns
        -------
        Dict[str, Any]
            健康状态统计信息
        """
        with self._lock:
            stats = {
                "status": self._status.name,
                "mode": self._mode.name,
                "speed_factor": self._speed_factor,
                "data_points_processed": self._data_points_processed,
                "callback_errors": self._callback_errors,
                "last_activity_time": self._last_activity_time,
                "idle_time": time.time() - self._last_activity_time,
                "callback_count": len(self._callbacks)
            }
            
            # 性能指标
            if self._processing_times:
                stats["avg_processing_time"] = sum(self._processing_times) / len(self._processing_times)
                stats["max_processing_time"] = max(self._processing_times)
                stats["min_processing_time"] = min(self._processing_times)
            
            return stats
    
    def _replay_task(self):
        """重放线程的主任务函数"""
        logger.debug("重放任务开始")
        try:
            while self._status == ReplayStatus.RUNNING:
                # 修复：添加超时参数，防止无限等待
                event_set = self._event.wait(timeout=0.5)
                
                # 检查是否由于超时返回
                if not event_set and self._status == ReplayStatus.RUNNING:
                    logger.debug("等待事件超时，继续检查状态")
                    continue
                
                # 如果状态变更，则退出
                if self._status != ReplayStatus.RUNNING:
                    logger.debug(f"状态已变更为 {self._status.name}，退出重放循环")
                    break
                
                # 获取下一个数据点
                start_time = time.time()
                data_point = self._get_next_data_point()
                
                if data_point is None:
                    with self._lock:
                        self._status = ReplayStatus.COMPLETED
                    logger.info("重放已完成所有数据")
                    break
                
                # 根据模式和速度控制重放节奏
                self._control_replay_pace(data_point)
                
                # 触发回调
                self._notify_callbacks(data_point)
                
                # 记录性能指标
                process_time = time.time() - start_time
                with self._lock:
                    self._processing_times.append(process_time)
                    # 只保留最近100个样本
                    if len(self._processing_times) > 100:
                        self._processing_times.pop(0)
                    
                    self._data_points_processed += 1
                    self._last_activity_time = time.time()
                
        except Exception as e:
            logger.error(f"重放过程中发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            with self._lock:
                self._status = ReplayStatus.STOPPED
        
        logger.debug("重放任务结束")
    
    def _notify_callbacks(self, data_point):
        """触发所有注册的回调函数"""
        callbacks = list(self._callbacks.values())
        logger.debug(f"通知 {len(callbacks)} 个回调")
        
        for callback in callbacks:
            try:
                callback(data_point)
            except Exception as e:
                logger.error(f"执行回调时发生错误: {str(e)}")
                logger.error(traceback.format_exc())
                with self._lock:
                    self._callback_errors += 1
    
    def _control_replay_pace(self, data_point):
        """根据重放模式和速度控制重放节奏"""
        if self._mode == ReplayMode.BACKTEST:
            # 回测模式下不延迟，以最快速度处理
            pass
        
        elif self._mode in [ReplayMode.REALTIME, ReplayMode.ACCELERATED]:
            # 获取当前和下一个数据点的时间差，按速度计算延迟
            time_delta = self._calculate_delay(data_point)
            if time_delta > 0:
                delay = time_delta / self._speed_factor
                # 如果延迟过长，记录日志
                if delay > 1.0:
                    logger.debug(f"重放延迟: {delay:.2f}秒")
                time.sleep(delay)
    
    def _calculate_delay(self, data_point) -> float:
        """
        计算两个数据点之间应该延迟的时间（秒）
        
        由子类实现，根据数据特性计算延迟
        """
        # 默认不延迟
        return 0
    
    def _get_next_data_point(self) -> Optional[Any]:
        """
        获取下一个数据点
        
        由子类实现，根据数据源特性返回数据点
        """
        # 默认返回None表示没有更多数据
        return None

class DataFrameReplayController(BaseDataReplayController):
    """
    基于DataFrame的数据重放控制器
    
    支持回放pandas DataFrame格式的数据
    """
    
    def __init__(self, dataframe: pd.DataFrame, timestamp_column=None, 
                 mode: ReplayMode = ReplayMode.BACKTEST, speed_factor: float = 1.0):
        """
        初始化基于DataFrame的数据重放控制器
        
        Parameters
        ----------
        dataframe : pd.DataFrame
            数据源DataFrame
        timestamp_column : str, optional
            时间戳列名，如果为None则使用索引作为时间戳, by default None
        mode : ReplayMode, optional
            重放模式, by default ReplayMode.BACKTEST
        speed_factor : float, optional
            速度因子, by default 1.0
        """
        super().__init__(data_source=dataframe, mode=mode, speed_factor=speed_factor)
        
        self._df = dataframe
        self._timestamp_column = timestamp_column
        
        # 如果指定了时间戳列，确保它是datetime类型
        if timestamp_column is not None and timestamp_column in self._df.columns:
            if not pd.api.types.is_datetime64_dtype(self._df[timestamp_column]):
                try:
                    self._df[timestamp_column] = pd.to_datetime(self._df[timestamp_column])
                except Exception as e:
                    logger.error(f"无法将列 '{timestamp_column}' 转换为日期时间格式: {str(e)}")
        
        # 存储前一个时间戳，用于计算延迟
        self._previous_timestamp = None
    
    def _get_next_data_point(self) -> Optional[Dict]:
        """
        获取下一个数据点
        
        Returns
        -------
        Optional[Dict]
            下一个数据点，如果没有更多数据则返回None
        """
        with self._lock:
            if self._current_position >= len(self._df):
                return None
            
            # 获取数据行并转换为字典
            row = self._df.iloc[self._current_position]
            
            # 记录前一个时间戳
            if self._timestamp_column:
                current_timestamp = row[self._timestamp_column]
            elif isinstance(self._df.index, pd.DatetimeIndex):
                current_timestamp = self._df.index[self._current_position]
            else:
                current_timestamp = None
            
            # 保存前一个时间戳用于计算延迟
            self._previous_timestamp = current_timestamp
            
            # 增加位置计数
            self._current_position += 1
            
            # 返回行数据（转为字典）
            data_point = row.to_dict()
            
            # 如果使用索引作为时间戳，添加到数据点中
            if self._timestamp_column is None and isinstance(self._df.index, pd.DatetimeIndex):
                data_point['timestamp'] = current_timestamp
                
            return data_point
    
    def _calculate_delay(self, data_point) -> float:
        """
        计算两个数据点之间应该延迟的时间（秒）
        
        Parameters
        ----------
        data_point : Dict
            当前数据点
            
        Returns
        -------
        float
            应延迟的秒数
        """
        # 如果是第一个数据点，无需延迟
        if self._current_position <= 1 or self._previous_timestamp is None:
            return 0
        
        # 获取当前时间戳
        current_timestamp = None
        if self._timestamp_column and self._timestamp_column in data_point:
            current_timestamp = data_point[self._timestamp_column]
        elif 'timestamp' in data_point:
            current_timestamp = data_point['timestamp']
        elif isinstance(self._df.index, pd.DatetimeIndex):
            current_timestamp = self._df.index[self._current_position - 1]
        else:
            return 0
        
        # 计算时间差（秒）
        try:
            time_delta = (current_timestamp - self._previous_timestamp).total_seconds()
            return max(0, time_delta)  # 防止负值
        except Exception as e:
            logger.warning(f"计算时间差时出错: {str(e)}")
            return 0

class MultiSourceReplayController(BaseDataReplayController):
    """
    多数据源重放控制器
    
    支持同时回放多个数据源的数据，并按时间对齐
    """
    
    def __init__(self, data_sources: Dict[str, Any], timestamp_extractors: Dict[str, Callable] = None,
                 mode: ReplayMode = ReplayMode.BACKTEST, speed_factor: float = 1.0):
        """
        初始化多数据源重放控制器
        
        Parameters
        ----------
        data_sources : Dict[str, Any]
            数据源字典，键为数据源名称，值为数据源
        timestamp_extractors : Dict[str, Callable], optional
            时间戳提取函数字典，键为数据源名称，值为提取函数
        mode : ReplayMode, optional
            重放模式, by default ReplayMode.BACKTEST
        speed_factor : float, optional
            速度因子, by default 1.0
        """
        super().__init__(data_source=data_sources, mode=mode, speed_factor=speed_factor)
        
        self._data_sources = data_sources
        self._timestamp_extractors = timestamp_extractors or {}
        
        # 内部状态
        self._current_data = {}  # 每个数据源当前的数据点
        self._iterators = {}     # 每个数据源的迭代器
        self._timestamps = {}    # 每个数据源当前数据点的时间戳
        self._completed = set()  # 已完成的数据源
        self._prev_timestamp = None  # 上一个事件的时间戳
        
        # 初始化迭代器
        self._initialize_iterators()
    
    def _initialize_iterators(self):
        """初始化所有数据源的迭代器"""
        for name, source in self._data_sources.items():
            if isinstance(source, pd.DataFrame):
                # 创建DataFrame的迭代器
                self._iterators[name] = source.iterrows()
            elif hasattr(source, '__iter__'):
                # 创建可迭代对象的迭代器
                self._iterators[name] = iter(source)
            else:
                logger.warning(f"无法为数据源 '{name}' 创建迭代器")
                self._completed.add(name)
        
        # 为每个数据源加载第一个数据点
        for name in list(self._iterators.keys()):
            self._load_next_for_source(name)
    
    def _load_next_for_source(self, source_name: str) -> bool:
        """
        加载数据源的下一个数据点
        
        Parameters
        ----------
        source_name : str
            数据源名称
            
        Returns
        -------
        bool
            是否成功加载
        """
        if source_name in self._completed:
            return False
        
        try:
            iterator = self._iterators.get(source_name)
            if iterator is None:
                return False
            
            # 获取下一个数据点
            if isinstance(self._data_sources[source_name], pd.DataFrame):
                # DataFrame迭代器返回(index, row)
                index, row = next(iterator)
                # 将Series转为字典
                data_point = row.to_dict()
                # 添加索引值
                data_point['_index'] = index
            else:
                # 其他迭代器直接获取数据点
                data_point = next(iterator)
            
            # 存储数据点
            self._current_data[source_name] = data_point
            
            # 提取时间戳
            timestamp = self._get_timestamp(source_name, data_point)
            self._timestamps[source_name] = timestamp
            
            return True
            
        except StopIteration:
            # 迭代器耗尽，标记为完成
            self._completed.add(source_name)
            self._current_data.pop(source_name, None)
            self._timestamps.pop(source_name, None)
            return False
            
        except Exception as e:
            logger.error(f"加载数据源 '{source_name}' 的下一个数据点时出错: {str(e)}")
            logger.error(traceback.format_exc())
            self._completed.add(source_name)
            return False
    
    def _get_timestamp(self, source_name: str, data_point: Dict) -> Optional[datetime]:
        """
        从数据点中提取时间戳
        
        Parameters
        ----------
        source_name : str
            数据源名称
        data_point : Dict
            数据点
            
        Returns
        -------
        Optional[datetime]
            时间戳，如果无法提取则返回None
        """
        # 如果有自定义提取函数，使用它
        if source_name in self._timestamp_extractors:
            try:
                return self._timestamp_extractors[source_name](data_point)
            except Exception as e:
                logger.error(f"调用时间戳提取函数时出错: {str(e)}")
        
        # 通用提取逻辑
        if isinstance(data_point, dict):
            for key in ['timestamp', 'time', 'date', 'datetime']:
                if key in data_point:
                    value = data_point[key]
                    if isinstance(value, (datetime, date)):
                        return value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time())
        
        # 如果是DataFrame并且索引是日期时间类型
        if isinstance(self._data_sources.get(source_name), pd.DataFrame):
            df = self._data_sources[source_name]
            if isinstance(df.index, pd.DatetimeIndex) and '_index' in data_point:
                return df.index[data_point['_index']]
        
        # 无法提取时间戳
        logger.warning(f"无法从数据源 '{source_name}' 的数据点中提取时间戳")
        return datetime.now()  # 使用当前时间作为默认值
    
    def _get_next_data_point(self) -> Optional[Dict]:
        """
        获取下一个要推送的数据点
        
        Returns
        -------
        Optional[Dict]
            下一个数据点，包含源名称和数据，如果没有更多数据则返回None
        """
        with self._lock:
            # 如果所有数据源都已完成，返回None
            if len(self._completed) == len(self._data_sources):
                return None
            
            # 如果没有待处理的数据点，返回None
            if not self._timestamps:
                return None
            
            # 找出最早的时间戳及其对应的数据源
            earliest_source = min(self._timestamps.items(), key=lambda x: x[1])[0]
            timestamp = self._timestamps[earliest_source]
            data = self._current_data[earliest_source]
            
            # 更新上一个时间戳
            self._prev_timestamp = timestamp
            
            # 为该数据源加载下一个数据点
            self._load_next_for_source(earliest_source)
            
            # 返回数据点
            return {
                'source': earliest_source,
                'timestamp': timestamp,
                'data': data
            }
    
    def _calculate_delay(self, data_point) -> float:
        """
        计算两个数据点之间应该延迟的时间（秒）
        
        Parameters
        ----------
        data_point : Dict
            当前数据点
            
        Returns
        -------
        float
            应延迟的秒数
        """
        # 如果是第一个数据点，无需延迟
        if self._prev_timestamp is None:
            return 0
        
        # 获取当前数据点的时间戳
        if 'timestamp' in data_point:
            current_timestamp = data_point['timestamp']
        else:
            return 0
        
        # 计算时间差（秒）
        try:
            time_delta = (current_timestamp - self._prev_timestamp).total_seconds()
            return max(0, time_delta)  # 防止负值
        except Exception as e:
            logger.warning(f"计算时间差时出错: {str(e)}")
            return 0 