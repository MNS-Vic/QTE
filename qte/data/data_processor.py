"""
数据处理器模块

提供各种数据处理和转换功能
"""

from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime, date
import logging

# 设置日志
logger = logging.getLogger("DataProcessor")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class DataProcessor:
    """
    数据处理器类
    
    提供各种数据处理和转换功能
    """
    
    @staticmethod
    def resample(data: pd.DataFrame, 
                source_freq: str, 
                target_freq: str, 
                method: str = 'ohlc',
                dropna: bool = True) -> pd.DataFrame:
        """
        重采样时间序列数据到不同频率
        
        Parameters
        ----------
        data : pd.DataFrame
            输入数据，必须有DatetimeIndex索引
        source_freq : str
            源数据频率（使用pandas频率字符串，如'D'表示日度，'H'表示小时）
        target_freq : str
            目标频率（使用pandas频率字符串，如'M'表示月度，'W'表示周度）
            注意：月度频率应使用'ME'而非'M'，表示月末
        method : str, optional
            重采样方法, by default 'ohlc'
            支持的方法:
            - 'ohlc': OHLC方法（适用于价格数据，保留开高低收）
            - 'last': 使用每个周期的最后一个值
            - 'mean': 使用每个周期的平均值
        dropna : bool, optional
            是否删除缺失值, by default True
            
        Returns
        -------
        pd.DataFrame
            重采样后的数据
            
        Examples
        --------
        >>> # 将日度数据重采样为月度
        >>> monthly_data = DataProcessor.resample(daily_data, 'D', 'ME', method='ohlc')
        """
        # 确保数据有时间索引
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("输入数据必须具有DatetimeIndex类型的索引")
        
        df = data.copy()
        
        # 处理目标频率，将'M'替换为'ME'（月末标识）
        if target_freq == 'M':
            target_freq = 'ME'  # 使用月末标识替代已弃用的月度标识
        
        # 根据方法进行重采样
        if method.lower() == 'ohlc':
            # 检查是否有必要的列
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if all(col.lower() in map(str.lower, df.columns) for col in required_cols):
                # 确保列名小写
                if not all(col in df.columns for col in required_cols):
                    df.columns = [col.lower() for col in df.columns]
            else:
                raise ValueError(f"OHLC重采样方法要求数据包含这些列: {required_cols}")
        
            # 执行OHLC重采样
            resampled = pd.DataFrame()
            resampled['open'] = df['open'].resample(target_freq).first()
            resampled['high'] = df['high'].resample(target_freq).max()
            resampled['low'] = df['low'].resample(target_freq).min()
            resampled['close'] = df['close'].resample(target_freq).last()
            resampled['volume'] = df['volume'].resample(target_freq).sum()
            
            # 处理其他列（如果有的话）
            other_cols = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
            for col in other_cols:
                # 默认使用last方法处理其他列
                resampled[col] = df[col].resample(target_freq).last()
        
        elif method.lower() == 'last':
            resampled = df.resample(target_freq).last()
            
        elif method.lower() == 'mean':
            resampled = df.resample(target_freq).mean()
            # 如果存在成交量列，使用sum而不是mean
            if 'volume' in df.columns:
                resampled['volume'] = df['volume'].resample(target_freq).sum()
            
        else:
            raise ValueError(f"不支持的重采样方法: {method}. 支持的方法: 'ohlc', 'last', 'mean'")
        
        # 处理缺失值
        if dropna:
            resampled = resampled.dropna()
            
        return resampled
    
    @staticmethod
    def align_multiple(data_dict: Dict[str, pd.DataFrame], 
                       method: str = 'outer',
                       fill_method: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        对齐多个数据源的时间索引
        
        Parameters
        ----------
        data_dict : Dict[str, pd.DataFrame]
            数据字典，键为数据标识，值为带时间索引的DataFrame
        method : str, optional
            对齐方法, by default 'outer'
            支持的方法:
            - 'outer': 所有出现的时间点(可能产生NaN)
            - 'inner': 只使用共同的时间点
        fill_method : Optional[str], optional
            填充缺失值的方法, by default None
            若为None，则不填充
            支持的方法:
            - 'ffill': 向前填充
            - 'bfill': 向后填充
            - 'zero': 填充为0
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            对齐后的数据字典
            
        Examples
        --------
        >>> # 对齐股票A和股票B的数据
        >>> aligned = DataProcessor.align_multiple({
        >>>     'stock_a': df_a, 
        >>>     'stock_b': df_b
        >>> }, method='outer', fill_method='ffill')
        """
        if not data_dict:
            return {}
            
        # 收集所有不同的索引
        all_indices = []
        for key, df in data_dict.items():
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValueError(f"数据 '{key}' 必须有DatetimeIndex类型的索引")
            all_indices.append(df.index)
        
        # 根据方法创建通用索引
        if method.lower() == 'outer':
            # 修复：使用reduce方法逐个合并索引
            from functools import reduce
            common_index = reduce(lambda x, y: x.union(y, sort=True), all_indices)
        elif method.lower() == 'inner':
            # 修复：使用reduce方法逐个合并索引
            from functools import reduce
            common_index = reduce(lambda x, y: x.intersection(y, sort=True), all_indices)
        else:
            raise ValueError(f"不支持的对齐方法: {method}. 支持的方法: 'outer', 'inner'")
        
        # 创建对齐后的数据字典
        result = {}
        for key, df in data_dict.items():
            # 重新索引
            aligned_df = df.reindex(common_index)
            
            # 应用填充方法（如果指定）
            if fill_method:
                if fill_method.lower() == 'ffill':
                    aligned_df = aligned_df.ffill()  # 使用ffill代替fillna(method='ffill')
                elif fill_method.lower() == 'bfill':
                    aligned_df = aligned_df.bfill()  # 使用bfill代替fillna(method='bfill')
                elif fill_method.lower() == 'zero':
                    aligned_df = aligned_df.fillna(0)
                else:
                    raise ValueError(f"不支持的填充方法: {fill_method}. 支持的方法: 'ffill', 'bfill', 'zero'")
            
            result[key] = aligned_df
            
        return result
    
    @staticmethod
    def fill_missing(data: pd.DataFrame, 
                    method: str = 'ffill',
                    limit: Optional[int] = None) -> pd.DataFrame:
        """
        填充缺失值
        
        Parameters
        ----------
        data : pd.DataFrame
            输入数据
        method : str, optional
            填充方法, by default 'ffill'
            支持的方法:
            - 'ffill': 向前填充（用前面的有效值填充）
            - 'bfill': 向后填充（用后面的有效值填充）
            - 'zero': 填充为0
            - 'mean': 填充为列均值
            - 'median': 填充为列中位数
            - 'interpolate': 线性插值
        limit : Optional[int], optional
            填充的最大连续NaN数, by default None
            
        Returns
        -------
        pd.DataFrame
            填充后的数据
            
        Examples
        --------
        >>> # 向前填充缺失值，最多连续填充5个
        >>> filled_data = DataProcessor.fill_missing(data, method='ffill', limit=5)
        """
        df = data.copy()
        
        if method.lower() == 'ffill':
            # 修复：使用ffill方法代替fillna(method='ffill')
            return df.ffill(limit=limit)
        elif method.lower() == 'bfill':
            # 修复：使用bfill方法代替fillna(method='bfill')
            return df.bfill(limit=limit)
        elif method.lower() == 'zero':
            return df.fillna(0)
        elif method.lower() == 'mean':
            return df.fillna(df.mean())
        elif method.lower() == 'median':
            return df.fillna(df.median())
        elif method.lower() == 'interpolate':
            return df.interpolate(method='linear', limit=limit)
        else:
            raise ValueError(f"不支持的填充方法: {method}")
    
    @staticmethod
    def adjust_price(data: pd.DataFrame, 
                     adjust_type: str = 'qfq',
                     adj_factor_col: str = 'adj_factor') -> pd.DataFrame:
        """
        价格前复权/后复权处理
        
        Parameters
        ----------
        data : pd.DataFrame
            输入数据，必须包含 'open', 'high', 'low', 'close' 和指定的复权因子列
        adjust_type : str, optional
            复权类型, by default 'qfq'
            支持的类型:
            - 'qfq': 前复权
            - 'hfq': 后复权
            - 'none': 不复权
        adj_factor_col : str, optional
            复权因子列名, by default 'adj_factor'
            
        Returns
        -------
        pd.DataFrame
            复权后的数据
            
        Raises
        ------
        ValueError
            当输入数据不包含必要的列或复权因子列时
            
        Examples
        --------
        >>> # 对价格进行前复权
        >>> adjusted_data = DataProcessor.adjust_price(data, adjust_type='qfq')
        """
        # 如果不复权，直接返回原始数据
        if adjust_type.lower() == 'none':
            return data.copy()
            
        # 检查数据是否包含必要的列
        required_cols = ['open', 'high', 'low', 'close']
        lowercase_cols = [col.lower() for col in data.columns]
        
        df = data.copy()
        
        # 检查列名并转换
        if not all(col in lowercase_cols for col in required_cols):
            # 尝试使用首字母大写的列名
            capitals = ['Open', 'High', 'Low', 'Close']
            if all(col in df.columns for col in capitals):
                # 转换列名为小写
                df.columns = [col.lower() for col in df.columns]
            else:
                raise ValueError(f"价格复权要求数据包含这些列: {required_cols}")
                
        # 检查是否包含复权因子列
        if adj_factor_col not in df.columns:
            raise ValueError(f"数据必须包含复权因子列: {adj_factor_col}")
        
        # 进行复权处理
        price_cols = ['open', 'high', 'low', 'close']
        
        if adjust_type.lower() == 'qfq':  # 前复权
            # 使用最新的复权因子作为基准
            latest_factor = df[adj_factor_col].iloc[-1]
            for col in price_cols:
                df[col] = df[col] * df[adj_factor_col] / latest_factor
                
        elif adjust_type.lower() == 'hfq':  # 后复权
            # 使用最早的复权因子作为基准
            earliest_factor = df[adj_factor_col].iloc[0]
            for col in price_cols:
                df[col] = df[col] * df[adj_factor_col] / earliest_factor
                
        else:
            raise ValueError(f"不支持的复权类型: {adjust_type}. 支持的类型: 'qfq', 'hfq', 'none'")
        
        return df 