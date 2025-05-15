#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VectorBT风格的向量化回测测试脚本 - 高频数据与机器学习扩展版
特点：高性能、向量化操作、大规模参数优化、高频数据处理、机器学习集成
"""
import os
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import psutil
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import warnings
warnings.filterwarnings('ignore')  # 抑制警告信息

# 模拟VectorBT的核心向量化回测逻辑
class VectorizedMLBacktester:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.ml_model = None
        self.feature_columns = []
        self.scaler = StandardScaler()
        
    def load_data(self, file_path=None, start_date=None, end_date=None, freq='1d', high_freq=False):
        """加载数据或生成模拟数据，支持高频数据"""
        if file_path and os.path.exists(file_path):
            # 如果文件存在，直接读取
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        else:
            # 否则生成模拟数据
            print("未找到数据文件，生成模拟数据...")
            if not start_date:
                start_date = '2022-01-01'
            if not end_date:
                end_date = '2022-12-31'
                
            # 生成日期范围，支持多种频率
            if freq == '1d':
                # 日线数据
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                # 只保留交易日 (工作日)
                date_range = date_range[date_range.dayofweek < 5]
            elif freq == '1h':
                # 小时线数据
                date_range = pd.date_range(start=start_date, end=end_date, freq='H')
                # 只保留交易时间 (9:30-15:00)
                date_range = date_range[
                    (date_range.time >= datetime.time(9, 30)) &
                    (date_range.time <= datetime.time(15, 0)) &
                    (date_range.dayofweek < 5)
                ]
            elif freq == '1min':
                # 分钟线数据
                date_range = pd.date_range(start=start_date, end=end_date, freq='min')
                # 只保留交易时间 (9:30-11:30, 13:00-15:00)
                date_range = date_range[
                    (((date_range.time >= datetime.time(9, 30)) &
                     (date_range.time <= datetime.time(11, 30))) |
                     ((date_range.time >= datetime.time(13, 0)) &
                     (date_range.time <= datetime.time(15, 0)))) &
                    (date_range.dayofweek < 5)
                ]
            elif freq == 'tick':
                # Tick数据 (每秒多个tick)
                date_range = pd.date_range(start=start_date, end=end_date, freq='s')
                # 只保留交易时间
                date_range = date_range[
                    (((date_range.time >= datetime.time(9, 30)) &
                     (date_range.time <= datetime.time(11, 30))) |
                     ((date_range.time >= datetime.time(13, 0)) &
                     (date_range.time <= datetime.time(15, 0)))) &
                    (date_range.dayofweek < 5)
                ]
                # 高频数据，每秒产生1-5个tick
                if high_freq:
                    new_range = []
                    for dt in date_range:
                        # 每秒随机生成1-5个tick
                        ticks_per_second = np.random.randint(1, 6)
                        for i in range(ticks_per_second):
                            # 添加毫秒
                            ms = np.random.randint(0, 1000)
                            new_dt = dt + datetime.timedelta(milliseconds=ms)
                            new_range.append(new_dt)
                    date_range = pd.DatetimeIndex(sorted(new_range))
            
            # 生成价格数据
            np.random.seed(42)  # 保证可重复性
            price = 3000  # 起始价格
            prices = [price]
            
            # 生成随机走势
            # 波动率根据数据频率调整
            if freq == '1d':
                volatility = 0.01  # 日线波动率约1%
            elif freq == '1h':
                volatility = 0.005  # 小时线波动率约0.5%
            elif freq == '1min':
                volatility = 0.001  # 分钟线波动率约0.1% 
            else:  # tick
                volatility = 0.0005  # tick波动率约0.05%
                
            # 生成随机走势
            for i in range(1, len(date_range)):
                # 添加一些趋势和季节性因素
                time_factor = np.sin(i / len(date_range) * 2 * np.pi) * 0.0002
                
                # 添加一些跳跃
                jump = 0
                if np.random.random() < 0.01:  # 1%的概率发生跳跃
                    jump = np.random.normal(0, volatility * 5)
                
                # 正常波动 + 趋势 + 跳跃
                change_percent = np.random.normal(0, volatility) + time_factor + jump
                price = price * (1 + change_percent)
                prices.append(price)
                
            # 创建DataFrame
            df = pd.DataFrame(index=date_range)
            df['close'] = prices
            
            # 其他价格数据
            df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0] * 0.99)
            
            # 高低价与交易量
            if freq != 'tick':
                df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, volatility * 3, size=len(df)))
                df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, volatility * 3, size=len(df)))
                
                # 交易量 - 与波动率有一定相关性
                vol_base = 1000000 if freq == '1d' else 100000 if freq == '1h' else 10000
                df['volume'] = np.random.randint(vol_base * 0.5, vol_base * 1.5, size=len(df))
                # 大波动时交易量增加
                big_moves = abs(df['close'].pct_change()) > volatility * 2
                df.loc[big_moves, 'volume'] = df.loc[big_moves, 'volume'] * np.random.uniform(1.5, 3, size=sum(big_moves))
            else:
                # Tick数据特有列
                df['bid'] = df['close'] * (1 - np.random.uniform(0, 0.0005, size=len(df)))
                df['ask'] = df['close'] * (1 + np.random.uniform(0, 0.0005, size=len(df)))
                df['bid_volume'] = np.random.randint(100, 1000, size=len(df))
                df['ask_volume'] = np.random.randint(100, 1000, size=len(df))
                
                # 确保买卖价差合理
                df['bid'] = df['close'] - np.random.uniform(0.01, 0.05, size=len(df))
                df['ask'] = df['close'] + np.random.uniform(0.01, 0.05, size=len(df))
            
        self.data = df
        self.data_freq = freq
        return df
    
    def add_features(self):
        """添加特征，用于机器学习模型"""
        data = self.data.copy()
        
        # 添加基础技术指标作为特征
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
        
        # 高频数据特有特征
        if self.data_freq in ['1min', 'tick']:
            # 微观结构特征
            if 'bid' in data.columns and 'ask' in data.columns:
                # 买卖价差
                data['spread'] = data['ask'] - data['bid']
                data['spread_pct'] = data['spread'] / data['close'] * 100
                
                # 买卖压力比率
                if 'bid_volume' in data.columns and 'ask_volume' in data.columns:
                    data['bid_ask_volume_ratio'] = data['bid_volume'] / data['ask_volume']
                    data['buy_pressure'] = data['bid_volume'] / (data['bid_volume'] + data['ask_volume'])
            
            # 日内效应
            if isinstance(data.index, pd.DatetimeIndex):
                # 交易时间特征
                data['hour'] = data.index.hour
                data['minute'] = data.index.minute
                data['time_from_open'] = (data.index.hour * 60 + data.index.minute) - (9 * 60 + 30)
                
                # 处理午休时间
                afternoon_mask = data.index.hour >= 13
                data.loc[afternoon_mask, 'time_from_open'] = data.loc[afternoon_mask, 'time_from_open'] - 90  # 减去90分钟的午休时间
                
                # 时间周期性特征
                data['time_sin'] = np.sin(2 * np.pi * data['time_from_open'] / (4 * 60))  # 4小时交易时段
                data['time_cos'] = np.cos(2 * np.pi * data['time_from_open'] / (4 * 60))
        
        # 价格剧烈变化
        data['price_jump'] = abs(data['close'].pct_change()) > data['close'].pct_change().rolling(20).std() * 3
        data['price_jump'] = data['price_jump'].astype(int)
        
        # 删除NaN值
        data = data.dropna()
        
        self.feature_data = data
        
        # 记录特征列名
        feature_cols = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'bid', 'ask', 'bid_volume', 'ask_volume']]
        self.feature_columns = feature_cols
        
        return data
    
    def prepare_ml_data(self, target_column='signal', prediction_horizon=1):
        """准备机器学习数据，包括特征和目标变量"""
        if not hasattr(self, 'feature_data'):
            self.add_features()
        
        data = self.feature_data.copy()
        
        # 创建目标变量 - 未来价格变化方向
        data['future_return'] = data['close'].shift(-prediction_horizon) / data['close'] - 1
        data['target'] = np.where(data['future_return'] > 0, 1, 0)  # 1表示上涨，0表示下跌
        
        # 删除NaN值
        data = data.dropna()
        
        # 分割特征和目标
        X = data[self.feature_columns]
        y = data['target']
        
        # 标准化特征
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # 保存处理后的数据
        self.ml_data = {
            'X': X,
            'X_scaled': X_scaled,
            'y': y,
            'data': data
        }
        
        return X_scaled, y
    
    def train_ml_model(self, model_type='random_forest', test_size=0.3, random_state=42):
        """训练机器学习模型"""
        if not hasattr(self, 'ml_data'):
            self.prepare_ml_data()
        
        X = self.ml_data['X_scaled']
        y = self.ml_data['y']
        
        # 分割训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
        
        # 选择并训练模型
        if model_type == 'random_forest':
            model = RandomForestClassifier(n_estimators=100, random_state=random_state)
        elif model_type == 'gradient_boosting':
            model = GradientBoostingClassifier(n_estimators=100, random_state=random_state)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 训练模型
        model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = model.predict(X_test)
        
        # 计算评估指标
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        print(f"\n============= 机器学习模型评估 =============")
        print(f"准确率: {accuracy:.4f}")
        print(f"精确率: {precision:.4f}")
        print(f"召回率: {recall:.4f}")
        print(f"F1分数: {f1:.4f}")
        
        # 特征重要性
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            print("\n特征重要性 (前10):")
            print(feature_importance.head(10))
        
        # 保存模型
        self.ml_model = model
        self.model_evaluation = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'feature_importance': feature_importance if hasattr(model, 'feature_importances_') else None
        }
        
        # 保存测试数据以便后续分析
        self.test_data = {
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': y_pred
        }
        
        return model
    
    def save_model(self, model_path):
        """保存训练好的模型"""
        if self.ml_model is None:
            print("没有可保存的模型")
            return False
        
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # 保存模型
        joblib.dump(self.ml_model, model_path)
        
        # 保存特征缩放器
        scaler_path = os.path.join(os.path.dirname(model_path), 'scaler.pkl')
        joblib.dump(self.scaler, scaler_path)
        
        # 保存特征列名
        feature_path = os.path.join(os.path.dirname(model_path), 'features.pkl')
        joblib.dump(self.feature_columns, feature_path)
        
        print(f"模型已保存至 {model_path}")
        return True
    
    def load_model(self, model_path):
        """加载预训练模型"""
        if not os.path.exists(model_path):
            print(f"模型文件不存在: {model_path}")
            return False
        
        # 加载模型
        self.ml_model = joblib.load(model_path)
        
        # 加载特征缩放器
        scaler_path = os.path.join(os.path.dirname(model_path), 'scaler.pkl')
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
        
        # 加载特征列名
        feature_path = os.path.join(os.path.dirname(model_path), 'features.pkl')
        if os.path.exists(feature_path):
            self.feature_columns = joblib.load(feature_path)
        
        print(f"模型已从 {model_path} 加载")
        return True
    
    def generate_ml_signals(self):
        """使用机器学习模型生成交易信号"""
        if self.ml_model is None:
            print("没有可用的机器学习模型")
            return None
        
        if not hasattr(self, 'feature_data'):
            self.add_features()
        
        data = self.feature_data.copy()
        
        # 准备特征
        X = data[self.feature_columns]
        
        # 标准化特征
        X_scaled = self.scaler.transform(X)
        
        # 生成预测
        y_pred = self.ml_model.predict(X_scaled)
        
        # 添加预测到数据中
        data['ml_signal'] = y_pred
        
        # 为了符合交易信号的格式，需要将上涨预测(1)转换为买入信号(1)，下跌预测(0)转换为卖出信号(-1)
        # 同时，我们只在信号变化时生成交易信号
        data['ml_position'] = data['ml_signal']
        data['signal'] = data['ml_position'].diff().fillna(0)
        
        # 计算信号：1表示买入，-1表示卖出，0表示不操作
        # 从持有到不持有是卖出信号
        data.loc[data['signal'] < 0, 'signal'] = -1
        # 从不持有到持有是买入信号
        data.loc[data['signal'] > 0, 'signal'] = 1
        # 其他情况不操作
        data.loc[data['signal'] == 0, 'signal'] = 0
        
        self.signals = data
        return data
    
    def backtest(self, commission_rate=0.001):
        """执行回测 - 向量化计算"""
        if not hasattr(self, 'signals'):
            self.generate_ml_signals()
            
        signals = self.signals.copy()
        
        # 计算持仓 (0表示空仓，1表示持仓)
        signals['position'] = signals['ml_position']
        signals['position'] = signals['position'].shift(1).fillna(0)  # 下一个周期才能交易
        
        # 计算每期收益率
        signals['returns'] = signals['close'].pct_change()
        signals['strategy_returns'] = signals['position'] * signals['returns']
        
        # 考虑交易成本 (仅在交易发生时)
        signals['trade'] = signals['position'].diff().fillna(0)
        signals['cost'] = abs(signals['trade']) * commission_rate
        signals['strategy_returns'] = signals['strategy_returns'] - signals['cost']
        
        # 计算累积收益
        signals['cum_returns'] = (1 + signals['returns']).cumprod()
        signals['cum_strategy_returns'] = (1 + signals['strategy_returns']).cumprod()
        
        # 计算回撤
        signals['cum_max'] = signals['cum_strategy_returns'].cummax()
        signals['drawdown'] = (signals['cum_max'] - signals['cum_strategy_returns']) / signals['cum_max']
        
        # 计算最终资金
        signals['equity'] = self.initial_capital * signals['cum_strategy_returns']
        
        self.results = signals
        
        # 计算策略统计
        self.calculate_statistics()
        
        return signals
    
    def calculate_statistics(self):
        """计算策略统计指标"""
        results = self.results
        
        # 总收益率
        self.total_return = results['cum_strategy_returns'].iloc[-1] - 1
        
        # 年化收益率
        if self.data_freq == '1d':
            annual_factor = 252  # 交易日
        elif self.data_freq == '1h':
            annual_factor = 252 * 4  # 假设每天4小时交易
        elif self.data_freq == '1min':
            annual_factor = 252 * 240  # 假设每天240分钟交易
        else:  # tick
            annual_factor = 252 * 240 * 60  # 估计值
            
        days = (results.index[-1] - results.index[0]).days
        if days > 0:
            self.annual_return = (1 + self.total_return) ** (365 / days) - 1
        else:
            # 如果数据周期少于一天，使用交易周期数来估算
            periods = len(results)
            self.annual_return = (1 + self.total_return) ** (annual_factor / periods) - 1
        
        # 最大回撤
        self.max_drawdown = results['drawdown'].max()
        
        # 夏普比率
        self.sharpe_ratio = results['strategy_returns'].mean() / results['strategy_returns'].std() * np.sqrt(annual_factor) if results['strategy_returns'].std() > 0 else 0
        
        # 索提诺比率 (使用负收益的标准差)
        negative_returns = results['strategy_returns'][results['strategy_returns'] < 0]
        self.sortino_ratio = results['strategy_returns'].mean() / negative_returns.std() * np.sqrt(annual_factor) if len(negative_returns) > 0 and negative_returns.std() > 0 else 0
        
        # 交易次数
        self.trade_count = (results['trade'] != 0).sum()
        
        # 盈利交易
        profitable_trades = (results[results['trade'] != 0]['strategy_returns'] > 0).sum()
        self.win_rate = profitable_trades / self.trade_count if self.trade_count > 0 else 0
        
        # 收益风险比
        self.profit_factor = abs(results[results['strategy_returns'] > 0]['strategy_returns'].sum() / results[results['strategy_returns'] < 0]['strategy_returns'].sum()) if results[results['strategy_returns'] < 0]['strategy_returns'].sum() != 0 else float('inf')
    
    def plot_results(self):
        """绘制回测结果图表"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 15), gridspec_kw={'height_ratios': [2, 1, 1]})
        
        # 绘制价格和交易信号
        ax1 = axes[0]
        ax1.plot(self.results.index, self.results['close'], label='收盘价', alpha=0.7)
        
        # 根据ML预测的持仓状态标记背景
        # 持有状态（看多）时标记为浅绿色背景
        buy_regions = self.results['ml_position'] == 1
        for i in range(len(self.results)-1):
            if buy_regions.iloc[i]:
                ax1.axvspan(self.results.index[i], self.results.index[i+1], alpha=0.2, color='green')
        
        # 标记买卖点
        buy_signals = self.results[self.results['signal'] == 1]
        sell_signals = self.results[self.results['signal'] == -1]
        ax1.scatter(buy_signals.index, buy_signals['close'], color='red', marker='^', s=100, label='买入信号')
        ax1.scatter(sell_signals.index, sell_signals['close'], color='green', marker='v', s=100, label='卖出信号')
        
        ax1.set_title('机器学习交易策略回测结果', fontsize=15)
        ax1.set_xlabel('日期/时间')
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制资金曲线
        ax2 = axes[1]
        ax2.plot(self.results.index, self.results['equity'], label='策略资金曲线', color='blue')
        ax2.plot(self.results.index, self.initial_capital * self.results['cum_returns'], label='买入持有资金曲线', color='grey', alpha=0.5)
        ax2.set_xlabel('日期/时间')
        ax2.set_ylabel('资金')
        ax2.legend()
        ax2.grid(True)
        
        # 绘制回撤
        ax3 = axes[2]
        ax3.fill_between(self.results.index, self.results['drawdown'], color='red', alpha=0.3)
        ax3.set_title('回撤')
        ax3.set_xlabel('日期/时间')
        ax3.set_ylabel('回撤比例')
        ax3.grid(True)
        
        plt.tight_layout()
        plt.savefig('ml_hft_backtest_results.png', dpi=300)
        plt.show()
        
        # 如果有机器学习模型评估结果，绘制特征重要性
        if hasattr(self, 'model_evaluation') and self.model_evaluation['feature_importance'] is not None:
            plt.figure(figsize=(10, 6))
            top_features = self.model_evaluation['feature_importance'].head(15)  # 只显示前15个特征
            plt.barh(top_features['feature'], top_features['importance'])
            plt.title('特征重要性 (前15)')
            plt.xlabel('重要性')
            plt.gca().invert_yaxis()  # 从上到下按重要性降序排列
            plt.tight_layout()
            plt.savefig('ml_feature_importance.png', dpi=300)
            plt.show()

def main():
    """主函数"""
    start_time = time.time()
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # 初始内存 (MB)
    
    print("============= VectorBT风格回测引擎 - ML高频数据版本 =============")
    
    # 初始化回测器
    backtester = VectorizedMLBacktester(initial_capital=100000)
    
    # 加载数据 - 选择数据频率
    freq = '1min'  # 可选: '1d', '1h', '1min', 'tick'
    print(f"使用 {freq} 数据进行回测")
    
    # 尝试加载数据，若无则生成模拟数据
    try:
        # 尝试读取实际数据
        if freq == '1d':
            data_path = "../data/backtest_data/daily/SHSE/000001/price.csv"
        elif freq == '1h':
            data_path = "../data/provider/downloaded_data/1h/SHSE/000001/price.csv"
        elif freq == '1min':
            data_path = "../test/data_provider/downloaded_data/1min/SHSE/600519/price.csv"
        else:  # tick
            data_path = "../test/data_provider/downloaded_data/tick/SHSE/600519/tick.csv"
            
        df = backtester.load_data(data_path, '2022-01-01', '2022-12-31', freq=freq, high_freq=(freq=='tick'))
    except Exception as e:
        print(f"加载数据出错: {e}")
        # 生成模拟数据
        df = backtester.load_data(start_date='2022-01-01', end_date='2022-12-31', freq=freq, high_freq=(freq=='tick'))
    
    print(f"数据加载完成，共 {len(df)} 个数据点")
    
    # 特征工程
    print("计算特征...")
    feature_data = backtester.add_features()
    print(f"生成 {len(backtester.feature_columns)} 个特征")
    
    # 准备机器学习数据
    print("准备机器学习数据...")
    X, y = backtester.prepare_ml_data(prediction_horizon=5)  # 预测未来5个时间单位的价格走势
    
    # 训练模型
    print("训练机器学习模型...")
    model = backtester.train_ml_model(model_type='random_forest', test_size=0.3)
    
    # 保存模型
    model_path = os.path.join('models', f'ml_model_{freq}.pkl')
    backtester.save_model(model_path)
    
    # 生成交易信号
    print("生成交易信号...")
    signals = backtester.generate_ml_signals()
    
    # 执行回测
    print("执行回测...")
    results = backtester.backtest(commission_rate=0.001)
    
    # 打印回测性能指标
    print("\n============= 回测结果 =============")
    print(f"总收益率: {backtester.total_return:.2%}")
    print(f"年化收益率: {backtester.annual_return:.2%}")
    print(f"最大回撤: {backtester.max_drawdown:.2%}")
    print(f"夏普比率: {backtester.sharpe_ratio:.2f}")
    print(f"索提诺比率: {backtester.sortino_ratio:.2f}")
    print(f"交易次数: {backtester.trade_count}")
    print(f"胜率: {backtester.win_rate:.2%}")
    print(f"收益风险比: {backtester.profit_factor:.2f}")
    
    # 绘制回测结果
    try:
        backtester.plot_results()
    except Exception as e:
        print(f"绘图过程中出错: {e}")
    
    # 计算内存使用和总耗时
    end_time = time.time()
    final_memory = process.memory_info().rss / 1024 / 1024  # 最终内存 (MB)
    
    print("\n============= 性能指标 =============")
    print(f"总耗时: {end_time - start_time:.2f}秒")
    print(f"内存使用: {final_memory - initial_memory:.2f} MB")
    print("注：向量化计算对高频数据处理效率高，模型训练和回测速度快")

if __name__ == "__main__":
    # 检查是否已安装依赖库
    try:
        import numpy
        import pandas
        import matplotlib.pyplot
        import sklearn
        import joblib
        import psutil
        # 导入可选库，用于高级可视化
        try:
            import seaborn
        except ImportError:
            print("提示: 安装seaborn可以获得更好的可视化效果")
        main()
    except ImportError as e:
        print(f"缺少必要的依赖库: {e}")
        print("请安装依赖: pip install numpy pandas matplotlib scikit-learn joblib psutil seaborn") 