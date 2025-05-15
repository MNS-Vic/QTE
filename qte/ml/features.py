#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机器学习特征工程模块 - 为回测提供特征生成功能
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Tuple, Any


class FeatureGenerator:
    """
    特征生成器
    
    为机器学习模型生成并处理特征
    """
    
    def __init__(self) -> None:
        """
        初始化特征生成器
        """
        self.feature_columns = []
        self.data = None
        
    def add_technical_indicators(self, data: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        添加技术指标特征
        
        Parameters
        ----------
        data : pd.DataFrame
            价格数据，需要包含OHLCV列
        inplace : bool, optional
            是否在原数据上修改, by default False
        
        Returns
        -------
        pd.DataFrame
            添加了技术指标的数据
        """
        if not inplace:
            data = data.copy()
            
        # 记录特征列
        original_columns = data.columns.tolist()
        
        # 移动平均线
        for window in [5, 10, 20, 30, 60]:
            # 价格移动平均
            data[f'ma_{window}'] = data['close'].rolling(window=window).mean()
            # 移动平均差
            data[f'ma_diff_{window}'] = data['close'] - data[f'ma_{window}']
            # 归一化移动平均差
            data[f'ma_diff_norm_{window}'] = data[f'ma_diff_{window}'] / data[f'ma_{window}'] * 100
        
        # 波动率指标
        for window in [5, 10, 20]:
            # 价格标准差
            data[f'std_{window}'] = data['close'].rolling(window=window).std()
            # 归一化波动率
            data[f'volatility_{window}'] = data[f'std_{window}'] / data['close'] * 100
            
        # RSI - 相对强弱指标
        for window in [6, 14, 21]:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            data[f'rsi_{window}'] = 100 - (100 / (1 + rs))
        
        # MACD - 平滑异同移动平均线
        ema12 = data['close'].ewm(span=12, adjust=False).mean()
        ema26 = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = ema12 - ema26
        data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
        data['macd_hist'] = data['macd'] - data['macd_signal']
        
        # 动量指标
        for window in [5, 10, 20]:
            # 价格动量
            data[f'momentum_{window}'] = data['close'].pct_change(window) * 100
            
        # 趋势指标
        for window in [10, 20, 30]:
            # 计算线性回归斜率
            x = np.arange(window)
            
            def rolling_slope(y):
                if len(y) < window:
                    return np.nan
                return np.polyfit(x, y, 1)[0]
            
            data[f'slope_{window}'] = data['close'].rolling(window=window).apply(rolling_slope, raw=True)
        
        # 交易量指标（如果有交易量数据）
        if 'volume' in data.columns:
            # 交易量移动平均
            for window in [5, 10, 20]:
                data[f'volume_ma_{window}'] = data['volume'].rolling(window=window).mean()
            
            # 交易量变化率
            data['volume_change'] = data['volume'].pct_change() * 100
            
            # 价量相关性
            for window in [10, 20]:
                price_change = data['close'].pct_change()
                # 使用rolling应用来计算相关性
                data[f'price_volume_corr_{window}'] = data['close'].pct_change().rolling(window).corr(data['volume'].pct_change())
        
        # 布林带
        for window in [20]:
            data[f'bb_middle_{window}'] = data['close'].rolling(window=window).mean()
            data[f'bb_std_{window}'] = data['close'].rolling(window=window).std()
            data[f'bb_upper_{window}'] = data[f'bb_middle_{window}'] + 2 * data[f'bb_std_{window}']
            data[f'bb_lower_{window}'] = data[f'bb_middle_{window}'] - 2 * data[f'bb_std_{window}']
            data[f'bb_width_{window}'] = (data[f'bb_upper_{window}'] - data[f'bb_lower_{window}']) / data[f'bb_middle_{window}']
            # BB位置百分比
            data[f'bb_pct_{window}'] = (data['close'] - data[f'bb_lower_{window}']) / (data[f'bb_upper_{window}'] - data[f'bb_lower_{window}'])
            
        # 随机指标
        for window in [14]:
            low_min = data['low'].rolling(window=window).min()
            high_max = data['high'].rolling(window=window).max()
            data[f'stochastic_k_{window}'] = 100 * (data['close'] - low_min) / (high_max - low_min)
            data[f'stochastic_d_{window}'] = data[f'stochastic_k_{window}'].rolling(window=3).mean()
        
        # 价格剧烈变化
        data['price_jump'] = (abs(data['close'].pct_change()) > data['close'].pct_change().rolling(20).std() * 3).astype(int)
        
        # 更新特征列列表
        self.feature_columns = [col for col in data.columns if col not in original_columns]
        self.data = data
        
        return data
    
    def add_date_features(self, data: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        添加日期特征
        
        Parameters
        ----------
        data : pd.DataFrame
            带有日期索引的数据
        inplace : bool, optional
            是否在原数据上修改, by default False
        
        Returns
        -------
        pd.DataFrame
            添加了日期特征的数据
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("数据需要有DatetimeIndex索引")
            
        if not inplace:
            data = data.copy()
        
        # 记录原始列
        original_columns = data.columns.tolist()
        
        # 提取日期特征
        data['day_of_week'] = data.index.dayofweek
        data['day_of_month'] = data.index.day
        data['month'] = data.index.month
        data['quarter'] = data.index.quarter
        data['year'] = data.index.year
        data['is_month_start'] = data.index.is_month_start.astype(int)
        data['is_month_end'] = data.index.is_month_end.astype(int)
        data['is_quarter_start'] = data.index.is_quarter_start.astype(int)
        data['is_quarter_end'] = data.index.is_quarter_end.astype(int)
        data['is_year_start'] = data.index.is_year_start.astype(int)
        data['is_year_end'] = data.index.is_year_end.astype(int)
        
        # 季节性特征 - 周期性编码（避免数值顺序问题）
        data['day_of_week_sin'] = np.sin(2 * np.pi * data.index.dayofweek / 7)
        data['day_of_week_cos'] = np.cos(2 * np.pi * data.index.dayofweek / 7)
        data['month_sin'] = np.sin(2 * np.pi * data.index.month / 12)
        data['month_cos'] = np.cos(2 * np.pi * data.index.month / 12)
        
        # 如果有时间信息（对于日内数据）
        if any(data.index.hour > 0) or any(data.index.minute > 0):
            data['hour'] = data.index.hour
            data['minute'] = data.index.minute
            
            # 计算交易日内的分钟数（假设9:30开盘，15:00收盘，中间有90分钟午休）
            data['time_from_open'] = (data.index.hour * 60 + data.index.minute) - (9 * 60 + 30)
            afternoon_mask = data.index.hour >= 13
            data.loc[afternoon_mask, 'time_from_open'] = data.loc[afternoon_mask, 'time_from_open'] - 90  # 减去午休90分钟
            
            # 周期性编码
            data['time_sin'] = np.sin(2 * np.pi * data['time_from_open'] / (4 * 60))  # 4小时交易时段
            data['time_cos'] = np.cos(2 * np.pi * data['time_from_open'] / (4 * 60))
        
        # 更新特征列列表
        date_features = [col for col in data.columns if col not in original_columns]
        self.feature_columns.extend(date_features)
        
        return data
    
    def add_high_frequency_features(self, data: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        添加高频数据特有特征
        
        Parameters
        ----------
        data : pd.DataFrame
            高频数据，包含OHLCV和可能的微观结构数据
        inplace : bool, optional
            是否在原数据上修改, by default False
        
        Returns
        -------
        pd.DataFrame
            添加了高频特征的数据
        """
        if not inplace:
            data = data.copy()
            
        # 记录原始列
        original_columns = data.columns.tolist()
        
        # 微观结构特征（如果有买卖盘数据）
        if 'bid' in data.columns and 'ask' in data.columns:
            # 买卖价差
            data['spread'] = data['ask'] - data['bid']
            data['spread_pct'] = data['spread'] / data['close'] * 100
            
            # 买卖压力比率
            if 'bid_volume' in data.columns and 'ask_volume' in data.columns:
                data['bid_ask_volume_ratio'] = data['bid_volume'] / data['ask_volume']
                data['buy_pressure'] = data['bid_volume'] / (data['bid_volume'] + data['ask_volume'])
        
        # 波动特征
        # 高频波动率 - 使用高低价计算当前bar的波动
        if 'high' in data.columns and 'low' in data.columns:
            data['bar_volatility'] = (data['high'] - data['low']) / data['close'] * 100
            
            # 计算不同时间窗口的价格波动范围
            for window in [5, 10, 20]:
                data[f'price_range_{window}'] = (data['high'].rolling(window).max() - data['low'].rolling(window).min()) / data['close'] * 100
        
        # 价格跳动
        data['tick_change'] = data['close'].diff()
        data['tick_change_pct'] = data['close'].pct_change() * 100
        
        # 跳动方向
        data['direction'] = np.sign(data['tick_change'])
        
        # 连续同向移动
        data['direction_streak'] = (data['direction'] * (data['direction'] == data['direction'].shift(1))).cumsum()
        data['direction_streak'] = data['direction_streak'].fillna(0)
        
        # 计算短期加速度（价格变化率的变化率）
        data['acceleration'] = data['tick_change_pct'].diff()
        
        # 更新特征列列表
        hf_features = [col for col in data.columns if col not in original_columns]
        self.feature_columns.extend(hf_features)
        
        return data
    
    def normalize_features(self, data: pd.DataFrame, columns: Optional[List[str]] = None,
                          method: str = 'zscore', inplace: bool = False) -> pd.DataFrame:
        """
        标准化特征
        
        Parameters
        ----------
        data : pd.DataFrame
            包含特征的数据
        columns : Optional[List[str]], optional
            要标准化的列，如果为None则使用所有特征列, by default None
        method : str, optional
            标准化方法，'zscore'或'minmax', by default 'zscore'
        inplace : bool, optional
            是否在原数据上修改, by default False
        
        Returns
        -------
        pd.DataFrame
            标准化后的数据
        """
        if not inplace:
            data = data.copy()
            
        # 确定要标准化的列
        if columns is None:
            columns = self.feature_columns if self.feature_columns else data.select_dtypes(include=[np.number]).columns.tolist()
        
        # 应用标准化
        if method == 'zscore':
            for col in columns:
                mean = data[col].mean()
                std = data[col].std()
                if std > 0:
                    data[col] = (data[col] - mean) / std
                else:
                    data[col] = 0
        elif method == 'minmax':
            for col in columns:
                min_val = data[col].min()
                max_val = data[col].max()
                if max_val > min_val:
                    data[col] = (data[col] - min_val) / (max_val - min_val)
                else:
                    data[col] = 0.5
        else:
            raise ValueError(f"不支持的标准化方法: {method}")
            
        return data
    
    def prepare_ml_data(self, data: Optional[pd.DataFrame] = None, target: str = 'direction',
                       prediction_horizon: int = 1, train_test_split: bool = False,
                       test_size: float = 0.3, random_state: int = 42) -> Union[Tuple[np.ndarray, np.ndarray], 
                                                                              Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
        """
        准备机器学习数据
        
        Parameters
        ----------
        data : Optional[pd.DataFrame], optional
            包含特征的数据，如果为None则使用保存的数据, by default None
        target : str, optional
            目标变量类型，可选'direction'(方向), 'return'(收益率), 'custom'(自定义列), by default 'direction'
        prediction_horizon : int, optional
            预测时间周期, by default 1
        train_test_split : bool, optional
            是否分割训练和测试集, by default False
        test_size : float, optional
            测试集比例, by default 0.3
        random_state : int, optional
            随机种子, by default 42
        
        Returns
        -------
        Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]
            (X, y)或(X_train, X_test, y_train, y_test)
        """
        if data is None:
            if self.data is None:
                raise ValueError("数据未设置")
            data = self.data.copy()
        else:
            data = data.copy()
            
        # 确保特征列
        if not self.feature_columns:
            self.add_technical_indicators(data, inplace=True)
            
        # 创建目标变量
        if target == 'direction':
            # 未来价格方向
            future_return = data['close'].shift(-prediction_horizon) / data['close'] - 1
            data['target'] = np.where(future_return > 0, 1, 0)
        elif target == 'return':
            # 未来收益率
            data['target'] = data['close'].shift(-prediction_horizon) / data['close'] - 1
        elif target in data.columns:
            # 使用自定义列作为目标
            data['target'] = data[target]
        else:
            raise ValueError(f"目标变量类型不支持: {target}")
            
        # 删除NaN值
        data = data.dropna()
        
        # 准备特征和目标
        X = data[self.feature_columns].values
        y = data['target'].values
        
        # 分割训练和测试集
        if train_test_split:
            from sklearn.model_selection import train_test_split as sk_train_test_split
            X_train, X_test, y_train, y_test = sk_train_test_split(X, y, test_size=test_size, random_state=random_state)
            return X_train, X_test, y_train, y_test
        else:
            return X, y
    
    def select_features(self, X: np.ndarray, y: np.ndarray, n_features: int = 10,
                       method: str = 'importance') -> List[int]:
        """
        特征选择
        
        Parameters
        ----------
        X : np.ndarray
            特征矩阵
        y : np.ndarray
            目标变量
        n_features : int, optional
            选择的特征数量, by default 10
        method : str, optional
            选择方法，'importance', 'f_test', 'mutual_info', by default 'importance'
        
        Returns
        -------
        List[int]
            选中特征的索引
        """
        if method == 'importance':
            from sklearn.ensemble import RandomForestClassifier
            if len(np.unique(y)) < 5:  # 分类任务
                model = RandomForestClassifier(n_estimators=100, random_state=42)
            else:  # 回归任务
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                
            model.fit(X, y)
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1][:n_features]
            
        elif method == 'f_test':
            from sklearn.feature_selection import SelectKBest, f_regression, f_classif
            if len(np.unique(y)) < 5:  # 分类任务
                selector = SelectKBest(score_func=f_classif, k=n_features)
            else:  # 回归任务
                selector = SelectKBest(score_func=f_regression, k=n_features)
                
            selector.fit(X, y)
            indices = selector.get_support(indices=True)
            
        elif method == 'mutual_info':
            from sklearn.feature_selection import SelectKBest, mutual_info_regression, mutual_info_classif
            if len(np.unique(y)) < 5:  # 分类任务
                selector = SelectKBest(score_func=mutual_info_classif, k=n_features)
            else:  # 回归任务
                selector = SelectKBest(score_func=mutual_info_regression, k=n_features)
                
            selector.fit(X, y)
            indices = selector.get_support(indices=True)
            
        else:
            raise ValueError(f"不支持的特征选择方法: {method}")
            
        return indices.tolist()
    
    def get_feature_names(self) -> List[str]:
        """
        获取特征名称
        
        Returns
        -------
        List[str]
            特征名称列表
        """
        return self.feature_columns