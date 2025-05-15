"""
数据源接口定义

定义所有数据源必须实现的接口
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date
import pandas as pd
import abc
import logging

# 设置日志
logger = logging.getLogger("DataSourceInterface")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class DataSourceInterface(abc.ABC):
    """
    数据源接口类
    
    定义了所有数据源必须实现的方法
    """
    
    @abc.abstractmethod
    def connect(self, **kwargs) -> bool:
        """
        连接到数据源
        
        Parameters
        ----------
        **kwargs : dict
            连接参数，根据具体数据源而定
            
        Returns
        -------
        bool
            连接是否成功
        """
        pass
        
    @abc.abstractmethod
    def get_symbols(self, market: Optional[str] = None, **kwargs) -> List[str]:
        """
        获取可用标的列表
        
        Parameters
        ----------
        market : Optional[str], optional
            市场代码, by default None
        **kwargs : dict
            其他参数
            
        Returns
        -------
        List[str]
            标的代码列表
        """
        pass
        
    @abc.abstractmethod
    def get_bars(self, symbol: str, 
                start_date: Optional[Union[str, datetime, date]] = None, 
                end_date: Optional[Union[str, datetime, date]] = None, 
                frequency: str = '1d', 
                **kwargs) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Parameters
        ----------
        symbol : str
            标的代码
        start_date : Optional[Union[str, datetime, date]], optional
            开始日期, by default None
        end_date : Optional[Union[str, datetime, date]], optional
            结束日期, by default None
        frequency : str, optional
            频率，支持的格式如：'1d', '1h', '5m'等, by default '1d'
        **kwargs : dict
            其他参数
            
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据，若无数据则返回None
            
        Notes
        -----
        返回的DataFrame必须包含以下列：
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - close: 收盘价
        - volume: 成交量
        并且索引必须是datetime类型的日期时间索引
        """
        pass
        
    def get_ticks(self, symbol: str, 
                 date: Optional[Union[str, datetime, date]] = None, 
                 **kwargs) -> Optional[pd.DataFrame]:
        """
        获取Tick数据
        
        Parameters
        ----------
        symbol : str
            标的代码
        date : Optional[Union[str, datetime, date]], optional
            日期, by default None (表示当天)
        **kwargs : dict
            其他参数
            
        Returns
        -------
        Optional[pd.DataFrame]
            Tick数据，若无数据则返回None
            
        Notes
        -----
        返回的DataFrame必须包含以下列：
        - price: 成交价
        - volume: 成交量
        并且索引必须是datetime类型的时间索引，精确到毫秒
        
        如可能，还应包含以下列：
        - bid_price: 买一价
        - ask_price: 卖一价
        - bid_volume: 买一量
        - ask_volume: 卖一量
        """
        # 默认实现返回None，子类可以覆盖此方法
        return None
        
    def get_fundamentals(self, table: str, 
                         symbols: List[str], 
                         start_date: Optional[Union[str, datetime, date]] = None, 
                         end_date: Optional[Union[str, datetime, date]] = None, 
                         fields: Optional[List[str]] = None, 
                         **kwargs) -> Optional[pd.DataFrame]:
        """
        获取基本面数据
        
        Parameters
        ----------
        table : str
            数据表名称
        symbols : List[str]
            标的代码列表
        start_date : Optional[Union[str, datetime, date]], optional
            开始日期, by default None
        end_date : Optional[Union[str, datetime, date]], optional
            结束日期, by default None
        fields : Optional[List[str]], optional
            字段列表, by default None (表示所有字段)
        **kwargs : dict
            其他参数
            
        Returns
        -------
        Optional[pd.DataFrame]
            基本面数据，若无数据则返回None
        """
        # 默认实现返回None，子类可以覆盖此方法
        return None


class BaseDataSource(DataSourceInterface):
    """
    数据源基类
    
    实现了一些通用功能，具体数据源可以继承此类
    """
    
    def __init__(self, use_cache: bool = True, **kwargs):
        """
        初始化数据源基类
        
        Parameters
        ----------
        use_cache : bool, optional
            是否使用缓存, by default True
        **kwargs : dict
            其他参数
        """
        self._connected = False
        self._use_cache = use_cache
        self._cache = None
        
        # 如果启用缓存，创建或获取缓存实例
        if self._use_cache:
            try:
                from .data_cache import DataCache
                self._cache = kwargs.get('cache', None)
                
                # 如果没有传入缓存实例，尝试获取全局单例
                if self._cache is None:
                    try:
                        from . import get_data_cache
                        self._cache = get_data_cache()
                    except ImportError:
                        self._cache = DataCache()
                
                logger.info(f"数据源 '{self.__class__.__name__}' 已启用缓存")
            except ImportError:
                logger.warning("找不到DataCache类，缓存功能将被禁用")
                self._use_cache = False
        
    def connect(self, **kwargs) -> bool:
        """
        连接到数据源（基类默认实现）
        
        Returns
        -------
        bool
            连接是否成功
        """
        self._connected = True
        return True
        
    def get_symbols(self, market: Optional[str] = None, **kwargs) -> List[str]:
        """
        获取可用标的列表（基类默认实现）
        
        Parameters
        ----------
        market : Optional[str], optional
            市场代码, by default None
            
        Returns
        -------
        List[str]
            标的代码列表
        """
        # 基类提供一个空列表实现，子类应该覆盖此方法
        return []
    
    def get_bars_with_cache(self, symbol: str, 
                          start_date: Optional[Union[str, datetime, date]] = None, 
                          end_date: Optional[Union[str, datetime, date]] = None, 
                          frequency: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """
        带缓存的K线获取
        
        Parameters
        ----------
        与get_bars相同
            
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据，若无数据则返回None
        """
        # 如果未启用缓存或缓存不可用，直接获取数据
        if not self._use_cache or self._cache is None:
            return self._get_bars_impl(symbol, start_date, end_date, frequency, **kwargs)
        
        # 格式化日期
        start_date_str = self._format_date(start_date) if start_date else "earliest"
        end_date_str = self._format_date(end_date) if end_date else "latest"
        
        # 构建缓存键
        cache_key = f"bars_{self.__class__.__name__}_{symbol}_{frequency}_{start_date_str}_{end_date_str}"
        
        # 尝试从缓存获取
        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"从缓存获取K线数据: {cache_key}")
            return cached_data
        
        # 缓存未命中，从数据源获取
        data = self._get_bars_impl(symbol, start_date, end_date, frequency, **kwargs)
        
        # 如果获取成功，更新缓存
        if data is not None:
            # 根据数据量确定缓存时间
            if frequency.endswith('d') or frequency.endswith('D'):  # 日线级别
                expire_time = 24 * 3600  # 1天
            elif frequency.endswith('h') or frequency.endswith('H'):  # 小时线级别
                expire_time = 6 * 3600  # 6小时
            else:  # 分钟线级别
                expire_time = 3600  # 1小时
                
            self._cache.set(cache_key, data, expire=expire_time)
            logger.debug(f"K线数据已缓存: {cache_key}")
        
        return data
    
    def _get_bars_impl(self, symbol: str, 
                     start_date: Optional[Union[str, datetime, date]] = None, 
                     end_date: Optional[Union[str, datetime, date]] = None, 
                     frequency: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """
        获取K线数据的实际实现（子类应覆盖此方法）
        
        Parameters
        ----------
        与get_bars相同
            
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据，若无数据则返回None
        """
        # 基类不提供实现，子类应该覆盖此方法
        return None
        
    def _ensure_connected(self) -> bool:
        """
        确保已连接到数据源
        
        Returns
        -------
        bool
            是否已连接
        """
        if not self._connected:
            return self.connect()
        return True
        
    def _format_date(self, date_obj: Optional[Union[str, datetime, date]]) -> Optional[str]:
        """
        将日期对象格式化为字符串
        
        Parameters
        ----------
        date_obj : Optional[Union[str, datetime, date]]
            日期对象
            
        Returns
        -------
        Optional[str]
            格式化后的日期字符串，如'2022-01-01'
        """
        if date_obj is None:
            return None
            
        if isinstance(date_obj, str):
            return date_obj
            
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d')
            
        if isinstance(date_obj, date):
            return date_obj.strftime('%Y-%m-%d')
            
        return str(date_obj) 