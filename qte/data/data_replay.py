"""
数据重放控制器模块

用于控制数据重放的速度、暂停/恢复等功能，支持回测和模拟交易场景
"""

from typing import List, Dict, Optional, Any, Union, Callable, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import time
import threading
import abc
import logging
from enum import Enum

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
    
    实现了基本的重放控制功能
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
            
            if self._mode in [ReplayMode.REALTIME, ReplayMode.ACCELERATED, ReplayMode.BACKTEST]:
                # 在单独线程中运行
                self._replay_thread = threading.Thread(target=self._replay_task)
                self._replay_thread.daemon = True
                self._replay_thread.start()
            
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
                logger.warning(f"无法暂停，当前状态: {self._status.name}")
                return False
            
            self._status = ReplayStatus.PAUSED
            self._event.clear()  # 清除事件，暂停线程
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
                logger.warning(f"无法恢复，当前状态: {self._status.name}")
                return False
            
            self._status = ReplayStatus.RUNNING
            self._event.set()  # 设置事件，恢复线程
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
            if self._status in [ReplayStatus.STOPPED, ReplayStatus.COMPLETED]:
                logger.warning(f"重放已经处于停止状态: {self._status.name}")
                return False
            
            prev_status = self._status
            self._status = ReplayStatus.STOPPED
            self._event.set()  # 确保线程不被阻塞
            
            # 如果之前是运行状态，等待线程结束
            if prev_status == ReplayStatus.RUNNING and self._replay_thread is not None:
                self._replay_thread.join(timeout=1.0)
            
            logger.info("重放已停止")
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
            if self._status not in [ReplayStatus.INITIALIZED, ReplayStatus.PAUSED, ReplayStatus.RUNNING]:
                logger.warning(f"无法步进，当前状态: {self._status.name}")
                return None
            
            # 获取下一个数据点
            data_point = self._get_next_data_point()
            if data_point is None:
                self._status = ReplayStatus.COMPLETED
                logger.info("重放已完成所有数据")
                return None
            
            # 触发回调
            self._notify_callbacks(data_point)
            
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
            logger.warning(f"速度因子必须大于0，当前值: {speed_factor}")
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
            if self._status == ReplayStatus.RUNNING:
                logger.warning("重放正在运行中，无法更改模式")
                return False
            
            self._mode = mode
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
            self._callbacks[callback_id] = callback
            self._callback_counter += 1
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
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]
                return True
            return False
    
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
            logger.info("重放器已重置")
            return True
    
    def _replay_task(self):
        """重放线程的主任务函数"""
        try:
            while self._status == ReplayStatus.RUNNING:
                # 等待事件，支持暂停/恢复
                self._event.wait()
                
                # 如果状态变更，则退出
                if self._status != ReplayStatus.RUNNING:
                    break
                
                # 获取下一个数据点
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
                
        except Exception as e:
            logger.error(f"重放过程中发生错误: {str(e)}")
            with self._lock:
                self._status = ReplayStatus.STOPPED
    
    def _notify_callbacks(self, data_point):
        """触发所有注册的回调函数"""
        callbacks = list(self._callbacks.values())
        for callback in callbacks:
            try:
                callback(data_point)
            except Exception as e:
                logger.error(f"执行回调时发生错误: {str(e)}")
    
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
            return row.to_dict()
    
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
        if self._timestamp_column and self._timestamp_column in data_point:
            current_timestamp = data_point[self._timestamp_column]
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
            数据源字典，键为数据源名称，值为数据源对象
        timestamp_extractors : Dict[str, Callable], optional
            时间戳提取函数字典，键为数据源名称，值为从数据点提取时间戳的函数, by default None
        mode : ReplayMode, optional
            重放模式, by default ReplayMode.BACKTEST
        speed_factor : float, optional
            速度因子, by default 1.0
        """
        super().__init__(data_source=data_sources, mode=mode, speed_factor=speed_factor)
        
        self._data_sources = data_sources
        self._timestamp_extractors = timestamp_extractors or {}
        
        # 初始化数据源迭代器和当前数据点
        self._iterators = {}
        self._current_data_points = {}
        self._previous_timestamp = None
        
        # 初始化各数据源的迭代器
        self._initialize_iterators()
    
    def _initialize_iterators(self):
        """初始化所有数据源的迭代器"""
        for name, source in self._data_sources.items():
            if isinstance(source, pd.DataFrame):
                # DataFrame类型直接转为迭代器
                self._iterators[name] = source.iterrows()
            elif hasattr(source, '__iter__'):
                # 可迭代对象直接使用
                self._iterators[name] = iter(source)
            else:
                logger.warning(f"无法为数据源 '{name}' 创建迭代器，类型: {type(source)}")
        
        # 预加载每个数据源的第一个数据点
        for name in self._iterators:
            self._load_next_for_source(name)
    
    def _load_next_for_source(self, source_name: str) -> bool:
        """
        加载指定数据源的下一个数据点
        
        Parameters
        ----------
        source_name : str
            数据源名称
            
        Returns
        -------
        bool
            是否成功加载
        """
        try:
            if source_name in self._iterators:
                iterator = self._iterators[source_name]
                idx, data = next(iterator)
                
                # 如果是Series则转为字典
                if isinstance(data, pd.Series):
                    data = data.to_dict()
                
                # 添加数据源名称和索引
                data['_source'] = source_name
                data['_index'] = idx
                
                self._current_data_points[source_name] = data
                return True
        except StopIteration:
            # 该数据源没有更多数据
            if source_name in self._current_data_points:
                del self._current_data_points[source_name]
            return False
        except Exception as e:
            logger.error(f"加载数据源 '{source_name}' 的下一个数据点时出错: {str(e)}")
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
            提取的时间戳，若无法提取则返回None
        """
        # 使用指定的提取器
        if source_name in self._timestamp_extractors:
            try:
                return self._timestamp_extractors[source_name](data_point)
            except Exception as e:
                logger.error(f"使用提取器获取数据源 '{source_name}' 的时间戳时出错: {str(e)}")
        
        # 尝试从索引获取（如果是日期时间）
        if '_index' in data_point and isinstance(data_point['_index'], (datetime, pd.Timestamp)):
            return data_point['_index']
        
        # 尝试查找常见的时间戳字段
        for field in ['timestamp', 'time', 'date', 'datetime']:
            if field in data_point and isinstance(data_point[field], (datetime, pd.Timestamp, str)):
                if isinstance(data_point[field], str):
                    try:
                        return pd.to_datetime(data_point[field])
                    except:
                        continue
                return data_point[field]
        
        return None
    
    def _get_next_data_point(self) -> Optional[Dict]:
        """
        获取下一个要处理的数据点
        
        Returns
        -------
        Optional[Dict]
            下一个数据点，如果没有更多数据则返回None
        """
        with self._lock:
            # 如果没有活跃的数据源，则结束
            if not self._current_data_points:
                return None
            
            # 找出时间最早的数据点
            earliest_source = None
            earliest_timestamp = None
            
            for source_name, data_point in self._current_data_points.items():
                timestamp = self._get_timestamp(source_name, data_point)
                if timestamp is None:
                    continue
                
                if earliest_timestamp is None or timestamp < earliest_timestamp:
                    earliest_timestamp = timestamp
                    earliest_source = source_name
            
            # 如果找不到有效的时间戳，则使用第一个数据点
            if earliest_source is None:
                earliest_source = next(iter(self._current_data_points.keys()))
            
            # 获取并移除最早的数据点
            result = self._current_data_points.pop(earliest_source, None)
            
            # 记录前一个时间戳
            self._previous_timestamp = earliest_timestamp
            
            # 加载该数据源的下一个数据点
            self._load_next_for_source(earliest_source)
            
            # 增加位置计数
            self._current_position += 1
            
            return result
    
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
        source_name = data_point.get('_source', '')
        current_timestamp = self._get_timestamp(source_name, data_point)
        
        if current_timestamp is None or self._previous_timestamp is None:
            return 0
        
        # 计算时间差（秒）
        try:
            time_delta = (current_timestamp - self._previous_timestamp).total_seconds()
            return max(0, time_delta)  # 防止负值
        except Exception as e:
            logger.warning(f"计算时间差时出错: {str(e)}")
            return 0 