#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机器学习模型管理模块 - 提供模型训练、评估、保存和加载功能
"""
import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Optional, Any, Tuple
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)


class ModelManager:
    """
    模型管理器类
    
    负责模型的训练、评估、保存和加载
    """
    
    def __init__(self, model_dir: Optional[str] = None) -> None:
        """
        初始化模型管理器
        """
        self.model = None
        self.model_type = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_classifier = True
        self.evaluation_metrics = {}
        
    def train_classifier(self, X: np.ndarray, y: np.ndarray, model_type: str = 'random_forest',
                       feature_names: Optional[List[str]] = None, **model_params) -> Any:
        """
        训练分类模型
        
        Parameters
        ----------
        X : np.ndarray
            特征矩阵
        y : np.ndarray
            目标变量
        model_type : str, optional
            模型类型, by default 'random_forest'
        feature_names : Optional[List[str]], optional
            特征名称, by default None
        **model_params
            模型参数
        
        Returns
        -------
        Any
            训练好的模型
        """
        self.is_classifier = True
        self.model_type = model_type
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        # 记录特征名称
        if feature_names:
            self.feature_names = feature_names
        else:
            self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        # 创建模型
        if model_type == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            if not model_params:
                model_params = {'n_estimators': 100, 'random_state': 42}
            self.model = RandomForestClassifier(**model_params)
            
        elif model_type == 'gradient_boosting':
            from sklearn.ensemble import GradientBoostingClassifier
            if not model_params:
                model_params = {'n_estimators': 100, 'random_state': 42}
            self.model = GradientBoostingClassifier(**model_params)
            
        elif model_type == 'xgboost':
            try:
                import xgboost as xgb
                if not model_params:
                    model_params = {'n_estimators': 100, 'random_state': 42}
                self.model = xgb.XGBClassifier(**model_params)
            except ImportError:
                raise ImportError("XGBoost未安装，请使用pip install xgboost安装")
            
        elif model_type == 'lightgbm':
            try:
                import lightgbm as lgb
                if not model_params:
                    model_params = {'n_estimators': 100, 'random_state': 42}
                self.model = lgb.LGBMClassifier(**model_params)
            except ImportError:
                raise ImportError("LightGBM未安装，请使用pip install lightgbm安装")
            
        elif model_type == 'svm':
            from sklearn.svm import SVC
            if not model_params:
                model_params = {'kernel': 'rbf', 'C': 1.0, 'random_state': 42}
            self.model = SVC(**model_params)
            
        elif model_type == 'logistic_regression':
            from sklearn.linear_model import LogisticRegression
            if not model_params:
                model_params = {'C': 1.0, 'random_state': 42}
            self.model = LogisticRegression(**model_params)
            
        elif model_type == 'neural_network':
            from sklearn.neural_network import MLPClassifier
            if not model_params:
                model_params = {'hidden_layer_sizes': (100,), 'random_state': 42}
            self.model = MLPClassifier(**model_params)
            
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        return self.model
    
    def train_regressor(self, X: np.ndarray, y: np.ndarray, model_type: str = 'random_forest',
                      feature_names: Optional[List[str]] = None, **model_params) -> Any:
        """
        训练回归模型
        
        Parameters
        ----------
        X : np.ndarray
            特征矩阵
        y : np.ndarray
            目标变量
        model_type : str, optional
            模型类型, by default 'random_forest'
        feature_names : Optional[List[str]], optional
            特征名称, by default None
        **model_params
            模型参数
        
        Returns
        -------
        Any
            训练好的模型
        """
        self.is_classifier = False
        self.model_type = model_type
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        # 记录特征名称
        if feature_names:
            self.feature_names = feature_names
        else:
            self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        # 创建模型
        if model_type == 'random_forest':
            from sklearn.ensemble import RandomForestRegressor
            if not model_params:
                model_params = {'n_estimators': 100, 'random_state': 42}
            self.model = RandomForestRegressor(**model_params)
            
        elif model_type == 'gradient_boosting':
            from sklearn.ensemble import GradientBoostingRegressor
            if not model_params:
                model_params = {'n_estimators': 100, 'random_state': 42}
            self.model = GradientBoostingRegressor(**model_params)
            
        elif model_type == 'xgboost':
            try:
                import xgboost as xgb
                if not model_params:
                    model_params = {'n_estimators': 100, 'random_state': 42}
                self.model = xgb.XGBRegressor(**model_params)
            except ImportError:
                raise ImportError("XGBoost未安装，请使用pip install xgboost安装")
            
        elif model_type == 'lightgbm':
            try:
                import lightgbm as lgb
                if not model_params:
                    model_params = {'n_estimators': 100, 'random_state': 42}
                self.model = lgb.LGBMRegressor(**model_params)
            except ImportError:
                raise ImportError("LightGBM未安装，请使用pip install lightgbm安装")
            
        elif model_type == 'svr':
            from sklearn.svm import SVR
            if not model_params:
                model_params = {'kernel': 'rbf', 'C': 1.0}
            self.model = SVR(**model_params)
            
        elif model_type == 'linear_regression':
            from sklearn.linear_model import LinearRegression
            self.model = LinearRegression(**model_params)
            
        elif model_type == 'neural_network':
            from sklearn.neural_network import MLPRegressor
            if not model_params:
                model_params = {'hidden_layer_sizes': (100,), 'random_state': 42}
            self.model = MLPRegressor(**model_params)
            
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        return self.model
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        使用模型进行预测
        
        Parameters
        ----------
        X : np.ndarray
            特征矩阵
        
        Returns
        -------
        np.ndarray
            预测结果
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        # 标准化特征
        X_scaled = self.scaler.transform(X)
        
        # 预测
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        使用分类模型进行概率预测
        
        Parameters
        ----------
        X : np.ndarray
            特征矩阵
        
        Returns
        -------
        np.ndarray
            预测概率
        """
        if self.model is None:
            raise ValueError("模型未训练")
            
        if not self.is_classifier:
            raise ValueError("只有分类模型才能使用predict_proba")
            
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError(f"模型{self.model_type}不支持predict_proba")
        
        # 标准化特征
        X_scaled = self.scaler.transform(X)
        
        # 预测概率
        return self.model.predict_proba(X_scaled)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        评估模型性能
        
        Parameters
        ----------
        X : np.ndarray
            特征矩阵
        y : np.ndarray
            真实标签
        
        Returns
        -------
        Dict[str, float]
            评估指标
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        # 标准化特征
        X_scaled = self.scaler.transform(X)
        
        # 预测
        y_pred = self.model.predict(X_scaled)
        
        # 评估
        if self.is_classifier:
            metrics = {
                'accuracy': accuracy_score(y, y_pred),
                'precision': precision_score(y, y_pred, average='weighted'),
                'recall': recall_score(y, y_pred, average='weighted'),
                'f1': f1_score(y, y_pred, average='weighted')
            }
        else:
            metrics = {
                'mse': mean_squared_error(y, y_pred),
                'rmse': np.sqrt(mean_squared_error(y, y_pred)),
                'mae': mean_absolute_error(y, y_pred),
                'r2': r2_score(y, y_pred)
            }
        
        self.evaluation_metrics = metrics
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性
        
        Returns
        -------
        pd.DataFrame
            特征重要性DataFrame
        """
        if self.model is None:
            raise ValueError("模型未训练")
            
        if not hasattr(self.model, 'feature_importances_'):
            raise ValueError(f"模型{self.model_type}不支持特征重要性")
        
        # 获取特征重要性
        importance = self.model.feature_importances_
        
        # 创建特征重要性DataFrame
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        })
        
        # 排序
        df = df.sort_values(by='importance', ascending=False)
        
        return df
    
    def save_model(self, filepath: str) -> None:
        """
        保存模型
        
        Parameters
        ----------
        filepath : str
            保存路径
        """
        if self.model is None:
            raise ValueError("模型未训练")
        
        # 创建目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存模型和相关组件
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_classifier': self.is_classifier,
            'evaluation_metrics': self.evaluation_metrics
        }
        
        # 保存
        joblib.dump(model_data, filepath)
        
    def load_model(self, filepath: str) -> None:
        """
        加载模型
        
        Parameters
        ----------
        filepath : str
            模型文件路径
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"模型文件不存在: {filepath}")
        
        # 加载模型
        model_data = joblib.load(filepath)
        
        # 提取模型和相关组件
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.is_classifier = model_data['is_classifier']
        self.evaluation_metrics = model_data['evaluation_metrics']
    
    def get_params(self) -> Dict[str, Any]:
        """
        获取模型参数
        
        Returns
        -------
        Dict[str, Any]
            模型参数
        """
        if self.model is None:
            raise ValueError("模型未训练")
            
        return self.model.get_params()
    
    def model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns
        -------
        Dict[str, Any]
            模型信息
        """
        if self.model is None:
            return {"status": "未训练"}
            
        info = {
            "model_type": self.model_type,
            "is_classifier": self.is_classifier,
            "feature_count": len(self.feature_names),
            "feature_names": self.feature_names,
            "model_params": self.get_params(),
            "evaluation_metrics": self.evaluation_metrics
        }
        
        return info
# 为了向后兼容，提供别名
ModelTrainer = ModelManager
