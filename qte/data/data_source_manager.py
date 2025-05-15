import pandas as pd
from typing import Dict, List, Optional, Any, Type
import logging
import os

# 创建日志记录器
logger = logging.getLogger("DataSourceManager")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class DataSourceManager:
    """
    数据源管理器
    
    管理多个数据源，提供统一的数据访问接口，支持数据源注册、切换和缓存管理。
    """
    
    def __init__(self):
        """初始化数据源管理器"""
        self.sources = {}  # 存储注册的数据源实例
        self.default_source = None  # 默认数据源名称
        
        # 创建缓存目录
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def register_source(self, name: str, source: Any, make_default: bool = False) -> bool:
        """
        注册数据源
        
        Parameters
        ----------
        name : str
            数据源名称
        source : Any
            数据源实例
        make_default : bool, optional
            是否设为默认数据源, by default False
            
        Returns
        -------
        bool
            注册是否成功
        """
        if name in self.sources:
            logger.warning(f"数据源 '{name}' 已存在，将被覆盖")
            
        self.sources[name] = source
        logger.info(f"数据源 '{name}' 已注册")
        
        if make_default or self.default_source is None:
            self.default_source = name
            logger.info(f"'{name}' 已设为默认数据源")
            
        return True
    
    def get_source(self, name: Optional[str] = None) -> Any:
        """
        获取指定名称的数据源实例
        
        Parameters
        ----------
        name : Optional[str], optional
            数据源名称, by default None (使用默认数据源)
            
        Returns
        -------
        Any
            数据源实例
        
        Raises
        ------
        ValueError
            如果数据源不存在
        """
        source_name = name if name else self.default_source
        
        if not source_name or source_name not in self.sources:
            raise ValueError(f"数据源 '{source_name}' 不存在")
            
        return self.sources[source_name]
    
    def set_default_source(self, name: str) -> bool:
        """
        设置默认数据源
        
        Parameters
        ----------
        name : str
            要设为默认的数据源名称
            
        Returns
        -------
        bool
            操作是否成功
            
        Raises
        ------
        ValueError
            如果数据源不存在
        """
        if name not in self.sources:
            raise ValueError(f"数据源 '{name}' 不存在，无法设为默认")
            
        self.default_source = name
        logger.info(f"'{name}' 已设为默认数据源")
        return True
    
    def list_sources(self) -> List[str]:
        """
        列出所有注册的数据源
        
        Returns
        -------
        List[str]
            数据源名称列表
        """
        sources = list(self.sources.keys())
        logger.info(f"已注册的数据源: {sources}")
        return sources
    
    def get_bars(self, symbol: str, start_date: Optional[str] = None, 
                end_date: Optional[str] = None, frequency: str = '1d',
                source_name: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Parameters
        ----------
        symbol : str
            标的代码
        start_date : Optional[str], optional
            开始日期, by default None
        end_date : Optional[str], optional
            结束日期, by default None
        frequency : str, optional
            数据频率, by default '1d'
        source_name : Optional[str], optional
            数据源名称, by default None (使用默认数据源)
        **kwargs : dict
            传递给数据源的其他参数
            
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据DataFrame
        """
        try:
            source = self.get_source(source_name)
            logger.info(f"使用数据源 '{source_name or self.default_source}' 获取 {symbol} 的K线数据")
            
            # 检查是否有get_bars方法
            if not hasattr(source, 'get_bars'):
                logger.error(f"数据源 '{source_name or self.default_source}' 不支持get_bars方法")
                return None
                
            return source.get_bars(symbol, start_date, end_date, frequency, **kwargs)
            
        except Exception as e:
            logger.error(f"获取K线数据时发生错误: {e}")
            return None
    
    def get_ticks(self, symbol: str, date: str, 
                 source_name: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取Tick数据
        
        Parameters
        ----------
        symbol : str
            标的代码
        date : str
            日期
        source_name : Optional[str], optional
            数据源名称, by default None (使用默认数据源)
        **kwargs : dict
            传递给数据源的其他参数
            
        Returns
        -------
        Optional[pd.DataFrame]
            Tick数据
        """
        try:
            source = self.get_source(source_name)
            logger.info(f"使用数据源 '{source_name or self.default_source}' 获取 {symbol} 在 {date} 的Tick数据")
            
            # 检查是否有get_ticks方法
            if not hasattr(source, 'get_ticks'):
                logger.error(f"数据源 '{source_name or self.default_source}' 不支持get_ticks方法")
                return None
                
            return source.get_ticks(symbol, date, **kwargs)
            
        except Exception as e:
            logger.error(f"获取Tick数据时发生错误: {e}")
            return None
    
    def get_fundamentals(self, table: str, symbols: List[str], 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, 
                        fields: Optional[List[str]] = None,
                        source_name: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取基本面数据
        
        Parameters
        ----------
        table : str
            基本面数据表名
        symbols : List[str]
            标的代码列表
        start_date : Optional[str], optional
            开始日期, by default None
        end_date : Optional[str], optional
            结束日期, by default None
        fields : Optional[List[str]], optional
            字段列表, by default None
        source_name : Optional[str], optional
            数据源名称, by default None (使用默认数据源)
        **kwargs : dict
            传递给数据源的其他参数
            
        Returns
        -------
        Optional[pd.DataFrame]
            基本面数据
        """
        try:
            source = self.get_source(source_name)
            logger.info(f"使用数据源 '{source_name or self.default_source}' 获取基本面数据 {table}")
            
            # 检查是否有get_fundamentals方法
            if not hasattr(source, 'get_fundamentals'):
                logger.error(f"数据源 '{source_name or self.default_source}' 不支持get_fundamentals方法")
                return None
                
            return source.get_fundamentals(table, symbols, start_date, end_date, fields, **kwargs)
            
        except Exception as e:
            logger.error(f"获取基本面数据时发生错误: {e}")
            return None
    
    def get_symbols(self, market: Optional[str] = None, 
                   source_name: Optional[str] = None, **kwargs) -> List[str]:
        """
        获取可用的标的列表
        
        Parameters
        ----------
        market : Optional[str], optional
            市场代码, by default None
        source_name : Optional[str], optional
            数据源名称, by default None (使用默认数据源)
        **kwargs : dict
            传递给数据源的其他参数
            
        Returns
        -------
        List[str]
            标的列表
        """
        try:
            source = self.get_source(source_name)
            logger.info(f"使用数据源 '{source_name or self.default_source}' 获取标的列表")
            
            # 检查是否有get_symbols方法
            if not hasattr(source, 'get_symbols'):
                logger.error(f"数据源 '{source_name or self.default_source}' 不支持get_symbols方法")
                return []
                
            return source.get_symbols(market, **kwargs)
            
        except Exception as e:
            logger.error(f"获取标的列表时发生错误: {e}")
            return []

# 创建全局单例实例
data_source_manager = DataSourceManager()

def get_data_source_manager() -> DataSourceManager:
    """
    获取数据源管理器单例实例
    
    Returns
    -------
    DataSourceManager
        数据源管理器实例
    """
    return data_source_manager 