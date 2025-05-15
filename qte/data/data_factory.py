"""
数据源工厂模块

提供创建和管理各类数据源的工厂类
"""

from typing import Dict, Callable, Optional, Any, List, Type
import importlib
import inspect
import logging
import os
import sys

# 创建日志记录器
logger = logging.getLogger("DataSourceFactory")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 导入基础数据源和内置数据源
from .sources.local_csv import LocalCsvSource
from .sources.gm_quant import GmQuantSource

# 尝试创建一个类型别名，表示数据源接口
try:
    from .data_source_interface import DataSourceInterface
    SourceType = DataSourceInterface
except ImportError:
    # 如果接口尚未定义，使用Any作为临时占位符
    SourceType = Any

class DataSourceFactory:
    """
    数据源工厂类
    
    负责创建和管理各类数据源实例
    """
    
    # 存储注册的数据源创建函数
    _creators: Dict[str, Callable[..., SourceType]] = {}
    
    # 自动注册内置数据源
    _creators['csv'] = lambda **kwargs: LocalCsvSource(**kwargs)
    _creators['gm'] = lambda **kwargs: GmQuantSource(**kwargs)
    
    @classmethod
    def create(cls, source_type: str, **kwargs) -> Optional[SourceType]:
        """
        根据类型创建数据源实例
        
        Parameters
        ----------
        source_type : str
            数据源类型名称
        **kwargs : dict
            传递给数据源构造函数的参数
            
        Returns
        -------
        Optional[SourceType]
            创建的数据源实例，如果类型不存在则返回None
            
        Examples
        --------
        >>> csv_source = DataSourceFactory.create('csv', base_path='data/stocks/')
        >>> gm_source = DataSourceFactory.create('gm', token='your_token_here')
        """
        # 转换为小写以忽略大小写差异
        source_type = source_type.lower()
        
        if source_type not in cls._creators:
            logger.error(f"未知的数据源类型: {source_type}. 可用类型: {', '.join(cls._creators.keys())}")
            return None
            
        try:
            instance = cls._creators[source_type](**kwargs)
            logger.info(f"成功创建 {source_type} 类型的数据源")
            return instance
        except Exception as e:
            logger.error(f"创建 {source_type} 数据源时发生错误: {e}")
            return None
    
    @classmethod
    def register_creator(cls, source_type: str, creator_func: Callable[..., SourceType]) -> bool:
        """
        注册自定义数据源创建函数
        
        Parameters
        ----------
        source_type : str
            数据源类型名称，将用于create()方法的source_type参数
        creator_func : Callable[..., SourceType]
            创建数据源实例的函数，应接受**kwargs并返回数据源实例
            
        Returns
        -------
        bool
            注册是否成功
            
        Examples
        --------
        >>> def create_my_source(**kwargs):
        >>>     return MyCustomSource(**kwargs)
        >>> DataSourceFactory.register_creator('my_source', create_my_source)
        """
        source_type = source_type.lower()
        
        if source_type in cls._creators:
            logger.warning(f"数据源类型 '{source_type}' 已存在，将被覆盖")
            
        cls._creators[source_type] = creator_func
        logger.info(f"已注册数据源类型: {source_type}")
        return True
    
    @classmethod
    def register_source_class(cls, source_type: str, source_class: Type[SourceType]) -> bool:
        """
        直接注册数据源类（而非创建函数）
        
        Parameters
        ----------
        source_type : str
            数据源类型名称
        source_class : Type[SourceType]
            数据源类，必须可以通过kwargs实例化
            
        Returns
        -------
        bool
            注册是否成功
            
        Examples
        --------
        >>> DataSourceFactory.register_source_class('mysql', MySqlDataSource)
        """
        def creator(**kwargs):
            return source_class(**kwargs)
            
        return cls.register_creator(source_type, creator)
    
    @classmethod
    def list_available_sources(cls) -> List[str]:
        """
        列出所有可用的数据源类型
        
        Returns
        -------
        List[str]
            可用数据源类型列表
            
        Examples
        --------
        >>> DataSourceFactory.list_available_sources()
        ['csv', 'gm', 'mysql', ...]
        """
        return list(cls._creators.keys())
    
    @classmethod
    def auto_discover(cls, package_name: str = 'qte.data.sources') -> int:
        """
        自动发现并注册指定包中的数据源类
        
        Parameters
        ----------
        package_name : str, optional
            要扫描的包名, by default 'qte.data.sources'
            
        Returns
        -------
        int
            新注册的数据源数量
            
        Notes
        -----
        数据源类必须满足以下条件才会被自动注册:
        1. 类名以'Source'结尾
        2. 类有一个__init__方法接受**kwargs
        """
        count = 0
        try:
            # 导入包
            package = importlib.import_module(package_name)
            package_path = os.path.dirname(package.__file__)
            
            # 扫描包中的所有.py文件
            for filename in os.listdir(package_path):
                if filename.endswith('.py') and not filename.startswith('__'):
                    module_name = f"{package_name}.{filename[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        # 查找模块中的所有类
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            # 检查类名是否以Source结尾且不是已经导入的基类
                            if (name.endswith('Source') and 
                                obj.__module__ == module_name and 
                                name not in ['DataSourceInterface', 'BaseDataSource']):
                                # 推断数据源类型名称（移除Source后缀并转为小写）
                                source_type = name[:-6].lower()
                                if source_type and source_type not in cls._creators:
                                    cls.register_source_class(source_type, obj)
                                    count += 1
                    except (ImportError, AttributeError) as e:
                        logger.warning(f"无法导入模块 {module_name}: {e}")
                        
            logger.info(f"自动发现并注册了 {count} 个数据源")
            return count
        except Exception as e:
            logger.error(f"自动发现数据源时发生错误: {e}")
            return 0 