#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金数据下载器和数据提供者模块

该模块负责从掘金量化API下载各种类型的历史数据，并按照接口规范提供给回测系统使用。
支持日线级、分钟级和tick级数据，并实现了完整的DataProvider接口。
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Generator, Union, Any

# 导入接口模块
from qte_data.interfaces import DataProvider, BarData, TickData
from qte_core.events import MarketEvent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 尝试导入掘金量化的库
try:
    from gm.api import *
except ImportError:
    logging.error("错误: 未找到掘金量化API，请确保已正确安装掘金量化Python SDK (pip install gm)")
    print("可通过以下命令安装: pip install gm")
    sys.exit(1)


class GmDataDownloader:
    """掘金数据下载类，负责从掘金API下载历史数据并存储为本地CSV文件"""

    def __init__(self, token: str = None, data_dir: str = "qte_data/market_data"):
        """
        初始化下载器
        
        Args:
            token: 掘金量化Token
            data_dir: 数据保存目录
        """
        self.token = token
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # 已初始化标记
        self.initialized = False
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    def initialize(self) -> None:
        """初始化API连接"""
        if not self.initialized:
            if not self.token:
                raise ValueError("Token未设置，请提供掘金量化Token")
            
            try:
                # 设置token
                set_token(self.token)
                self.initialized = True
                self.logger.info(f"掘金API连接初始化成功")
            except Exception as e:
                self.logger.error(f"掘金API连接初始化失败: {e}")
                raise RuntimeError(f"掘金API连接初始化失败: {e}")
    
    def _check_symbol(self, symbol: str) -> bool:
        """
        检查标的代码格式是否正确
        
        Args:
            symbol: 标的代码，如SHSE.600000
            
        Returns:
            bool: 格式是否正确
        """
        if not symbol or '.' not in symbol:
            self.logger.warning(f"标的代码 {symbol} 格式不正确。应为 '交易所.代码' 格式，如 'SHSE.600000'")
            return False
        return True
    
    def _get_data_path(self, symbol: str, data_type: str, start_date: str, end_date: str, 
                       frequency: str = None, adjust: str = None) -> Path:
        """
        获取数据文件的保存路径
        
        Args:
            symbol: 标的代码，如SHSE.600000
            data_type: 数据类型，'tick'、'minute'或'daily'
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'
            frequency: 频率，对于minute类型有效，如'1'表示1分钟，'5'表示5分钟
            adjust: 复权类型，None为不复权，'prev'为前复权，'post'为后复权
            
        Returns:
            Path: 数据文件路径
        """
        exchange, code = symbol.split('.')
        
        # 确定子目录
        if data_type == 'tick':
            sub_dir = "tick"
        elif data_type == 'minute':
            sub_dir = f"{frequency}min"
        else:  # daily
            sub_dir = "daily"
        
        # 复权后缀
        adjust_suffix = ""
        if adjust == 'prev':
            adjust_suffix = "_前复权"
        elif adjust == 'post':
            adjust_suffix = "_后复权"
        
        # 创建目录
        output_dir = self.data_dir / sub_dir / exchange / code
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # 文件名
        if data_type == 'tick':
            # tick数据按天分文件
            return output_dir / f"{symbol.replace('.', '_')}_{start_date}_tick.csv"
        else:
            # K线数据一般按时间段保存
            return output_dir / f"{symbol.replace('.', '_')}_{start_date}_to_{end_date}_{sub_dir}{adjust_suffix}.csv"
    
    def download_tick_data(self, symbol: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        下载tick级别数据
        
        Args:
            symbol: 标的代码，如SHSE.600000
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            
        Returns:
            DataFrame: tick数据合并结果
        """
        self.initialize()
        
        if not self._check_symbol(symbol):
            return None
        
        # 解析日期
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date) if end_date else datetime.now()
        
        self.logger.info(f"开始下载 {symbol} 的tick数据，时间范围: {start_date} 到 {end_date or datetime.now().strftime('%Y-%m-%d')}")
        
        # 由于tick数据量大，按天下载并保存
        current_date = start
        all_data = []
        
        while current_date <= end:
            current_date_str = current_date.strftime('%Y-%m-%d')
            next_date = current_date + timedelta(days=1)
            
            try:
                self.logger.info(f"下载 {symbol} 在 {current_date_str} 的tick数据...")
                
                # 获取文件路径
                output_file = self._get_data_path(
                    symbol=symbol,
                    data_type='tick',
                    start_date=current_date_str,
                    end_date=current_date_str
                )
                
                # 如果文件已存在，直接读取文件
                if output_file.exists():
                    self.logger.info(f"文件已存在，直接读取: {output_file}")
                    data = pd.read_csv(output_file)
                else:
                    # 查询当天的tick数据
                    data = history(
                        symbol=symbol,
                        frequency='tick',
                        start_time=f"{current_date_str} 00:00:00",
                        end_time=f"{current_date_str} 23:59:59",
                        fields='last_price,created_at,trade_date,volume,position,last_volume,bid_price,bid_volume,ask_price,ask_volume',
                        df=True
                    )
                    
                    if data is not None and not data.empty:
                        self.logger.info(f"获取到 {len(data)} 条tick记录")
                        
                        # 保存当天数据到CSV
                        data.to_csv(output_file, index=False)
                        self.logger.info(f"数据已保存到 {output_file}")
                    else:
                        self.logger.warning(f"未获取到 {symbol} 在 {current_date_str} 的tick数据")
                
                if data is not None and not data.empty:
                    all_data.append(data)
            
            except Exception as e:
                self.logger.error(f"下载 {symbol} 在 {current_date_str} 的tick数据时出错: {e}")
            
            # 移动到下一天
            current_date = next_date
        
        # 如果需要合并所有数据
        if all_data:
            all_data_df = pd.concat(all_data, ignore_index=True)
            return all_data_df
        
        return None
    
    def download_bar_data(self, symbol: str, frequency: str, start_date: str, end_date: str = None, 
                          adjust: str = None) -> pd.DataFrame:
        """
        下载K线数据（分钟线或日线）
        
        Args:
            symbol: 标的代码，如SHSE.600000
            frequency: 频率，如'60s'为分钟线，'1d'为日线
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            adjust: 复权方式，None为不复权，'prev'为前复权，'post'为后复权
            
        Returns:
            DataFrame: K线数据
        """
        self.initialize()
        
        if not self._check_symbol(symbol):
            return None
        
        # 解析日期
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        
        # 确定数据类型
        if frequency in ['1d', 'daily', '1dm']:
            data_type = "daily"
            gm_frequency = '1d'  # 掘金API的参数
            minute_value = None
        else:
            data_type = "minute"
            
            # 解析分钟数
            if frequency.endswith('s'):
                gm_frequency = frequency  # 直接使用，如'60s'
                minute_value = int(frequency[:-1]) // 60
            elif frequency.endswith('m'):
                minute_value = int(frequency[:-1])
                gm_frequency = f"{minute_value * 60}s"  # 转换为秒
            else:
                try:
                    # 尝试直接作为分钟数处理
                    minute_value = int(frequency)
                    gm_frequency = f"{minute_value * 60}s"  # 转换为秒
                except ValueError:
                    self.logger.error(f"无法解析频率: {frequency}")
                    return None
        
        # 复权设置
        adjust_text = "不复权"
        adjust_end_time = end_date
        gm_adjust = None
        
        if adjust == 'prev':
            adjust_text = "前复权"
            gm_adjust = ADJUST_PREV
        elif adjust == 'post':
            adjust_text = "后复权"
            gm_adjust = ADJUST_POST
        
        self.logger.info(f"开始下载 {symbol} 的{data_type}数据，时间范围: {start_date} 到 {end_date}，复权方式: {adjust_text}")
        
        # 获取文件路径
        output_file = self._get_data_path(
            symbol=symbol,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date,
            frequency=minute_value if data_type == 'minute' else None,
            adjust=adjust
        )
        
        # 如果文件已存在，直接读取文件
        if output_file.exists():
            self.logger.info(f"文件已存在，直接读取: {output_file}")
            return pd.read_csv(output_file)
        
        try:
            # 查询K线数据
            data = history(
                symbol=symbol,
                frequency=gm_frequency,
                start_time=f"{start_date} 00:00:00",
                end_time=f"{end_date} 23:59:59",
                fields='open,high,low,close,volume,amount,position,bob,eob',
                adjust=gm_adjust,
                adjust_end_time=adjust_end_time if gm_adjust else None,
                df=True
            )
            
            if data is not None and not data.empty:
                self.logger.info(f"获取到 {len(data)} 条{data_type}记录")
                
                # 保存数据到CSV
                data.to_csv(output_file, index=False)
                self.logger.info(f"数据已保存到 {output_file}")
                
                return data
            else:
                self.logger.warning(f"未获取到 {symbol} 在 {start_date} 到 {end_date} 的{data_type}数据")
        
        except Exception as e:
            self.logger.error(f"下载 {symbol} 的{data_type}数据时出错: {e}")
        
        return None
    
    def download_daily_data(self, symbol: str, start_date: str, end_date: str = None, adjust: str = None) -> pd.DataFrame:
        """
        下载日线级别数据
        
        Args:
            symbol: 标的代码，如SHSE.600000
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            adjust: 复权方式，None为不复权，'prev'为前复权，'post'为后复权
            
        Returns:
            DataFrame: 日线数据
        """
        return self.download_bar_data(symbol, '1d', start_date, end_date, adjust)
    
    def download_minute_data(self, symbol: str, minutes: int, start_date: str, end_date: str = None, 
                            adjust: str = None) -> pd.DataFrame:
        """
        下载分钟线级别数据
        
        Args:
            symbol: 标的代码，如SHSE.600000
            minutes: 分钟数，如1为1分钟线，5为5分钟线
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'，默认为当天
            adjust: 复权方式，None为不复权，'prev'为前复权，'post'为后复权
            
        Returns:
            DataFrame: 分钟线数据
        """
        return self.download_bar_data(symbol, str(minutes), start_date, end_date, adjust)


class GmDataProvider(DataProvider):
    """
    掘金数据提供者，实现DataProvider接口
    
    通过GmDataDownloader下载数据，并按回测系统需要的格式提供数据
    """
    
    def __init__(self, token: str = None, event_loop = None, data_dir: str = "qte_data/market_data"):
        """
        初始化数据提供者
        
        Args:
            token: 掘金量化Token
            event_loop: 事件循环实例，用于发送事件
            data_dir: 数据保存目录
        """
        # 创建下载器
        self.downloader = GmDataDownloader(token=token, data_dir=data_dir)
        
        # 存储事件循环
        self.event_loop = event_loop
        
        # 数据缓存
        self.data_cache: Dict[str, Dict[str, pd.DataFrame]] = {}  # 格式: {symbol: {'daily': df, '1min': df, 'tick': df}}
        self.latest_data: Dict[str, Dict] = {}  # 存储每个交易品种的最新K线数据
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def _ensure_data_loaded(self, symbol: str, data_type: str, start_date: str, end_date: str = None, 
                           minutes: int = None, adjust: str = None) -> pd.DataFrame:
        """
        确保数据已加载到内存
        
        Args:
            symbol: 标的代码，如SHSE.600000
            data_type: 数据类型，'daily'、'minute'或'tick'
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'
            minutes: 分钟数，对于'minute'类型有效
            adjust: 复权方式，None为不复权，'prev'为前复权，'post'为后复权
            
        Returns:
            DataFrame: 加载的数据
        """
        # 确保symbol字典存在
        if symbol not in self.data_cache:
            self.data_cache[symbol] = {}
            
        # 生成缓存键
        cache_key = data_type
        if data_type == 'minute' and minutes is not None:
            cache_key = f"{minutes}min"
            
        # 检查缓存
        if cache_key in self.data_cache[symbol]:
            df = self.data_cache[symbol][cache_key]
            
            # 检查日期是否在已缓存范围内
            if self._check_date_range(df, start_date, end_date or start_date):
                # 已有数据，过滤日期
                filtered_df = self._filter_by_date(df, start_date, end_date or start_date)
                if not filtered_df.empty:
                    return filtered_df
        
        # 下载数据
        if data_type == 'daily':
            df = self.downloader.download_daily_data(symbol, start_date, end_date, adjust)
        elif data_type == 'minute':
            df = self.downloader.download_minute_data(symbol, minutes, start_date, end_date, adjust)
        elif data_type == 'tick':
            df = self.downloader.download_tick_data(symbol, start_date, end_date)
        else:
            self.logger.error(f"不支持的数据类型: {data_type}")
            return None
        
        # 转换时间列
        if df is not None and not df.empty:
            # 确保时间列是datetime类型
            if 'bob' in df.columns:  # K线数据
                df['timestamp'] = pd.to_datetime(df['bob'])
            elif 'created_at' in df.columns:  # Tick数据
                df['timestamp'] = pd.to_datetime(df['created_at'])
            
            # 确保按时间戳排序
            df.sort_values(by='timestamp', inplace=True)
            
            # 更新缓存
            self.data_cache[symbol][cache_key] = df
            
            # 过滤日期
            filtered_df = self._filter_by_date(df, start_date, end_date or start_date)
            return filtered_df
        
        return None
    
    def _check_date_range(self, df: pd.DataFrame, start_date: str, end_date: str) -> bool:
        """
        检查数据是否包含指定的日期范围
        
        Args:
            df: 数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            bool: 是否包含
        """
        if df is None or df.empty:
            return False
            
        # 确定时间列
        time_col = 'timestamp' if 'timestamp' in df.columns else ('bob' if 'bob' in df.columns else 'created_at')
        
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col])
        
        # 转换日期
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # 检查数据范围
        min_date = df[time_col].min()
        max_date = df[time_col].max()
        
        return min_date <= start and max_date >= end
    
    def _filter_by_date(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """
        按日期过滤数据
        
        Args:
            df: 数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 过滤后的数据
        """
        if df is None or df.empty:
            return pd.DataFrame()
            
        # 确定时间列
        time_col = 'timestamp' if 'timestamp' in df.columns else ('bob' if 'bob' in df.columns else 'created_at')
        
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col])
        
        # 转换日期
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # 提取日期部分进行比较
        if isinstance(start, pd.Timestamp):
            start = start.normalize()
        if isinstance(end, pd.Timestamp):
            # 使用当天结束时间
            end = end.normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        
        # 过滤数据
        mask = (df[time_col] >= start) & (df[time_col] <= end)
        return df[mask].copy()
    
    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        返回指定合约代码的最新K线柱。
        如果没有可用数据，则返回 None。
        """
        if symbol in self.latest_data:
            return self.latest_data[symbol]
        
        # 如果还没有通过stream_market_data加载数据，尝试加载
        # 这里使用日线数据作为默认
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = self._ensure_data_loaded(symbol, 'daily', start_date, end_date)
        if data is not None and not data.empty:
            latest_bar = data.iloc[-1].to_dict()
            self.latest_data[symbol] = latest_bar
            return latest_bar
        
        return None
    
    def get_latest_bars(self, symbol: str, n: int = 1) -> Optional[List[BarData]]:
        """
        返回指定合约代码的 N 个最新K线柱。
        如果没有可用数据或K线柱数量不足，则返回 None。
        """
        # 获取最近一个月的数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=max(30, n))).strftime('%Y-%m-%d')
        
        data = self._ensure_data_loaded(symbol, 'daily', start_date, end_date)
        if data is not None and len(data) >= n:
            return [row.to_dict() for _, row in data.tail(n).iterrows()]
        
        return None
    
    def get_historical_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Generator[BarData, None, None]]:
        """
        生成器，在给定时期内为指定合约代码提供历史K线柱。
        如果没有可用数据，则返回 None。
        """
        # 转换日期格式
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 加载数据
        data = self._ensure_data_loaded(symbol, 'daily', start_str, end_str)
        if data is None or data.empty:
            return None
        
        # 创建生成器
        def bars_generator():
            for _, row in data.iterrows():
                yield row.to_dict()
                
        return bars_generator()
    
    def stream_market_data(self, symbols: List[str]) -> Generator[Union[MarketEvent, TickData], None, None]:
        """
        为指定的合约代码列表流式传输实时或模拟的市场数据。
        对于K线柱，生成 MarketEvent；对于tick级数据，可以生成 TickData。
        """
        if not symbols:
            return
        
        # 确定时间范围
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # 合并所有数据
        all_data = []
        
        for symbol in symbols:
            # 优先使用tick数据，如果没有再使用日线数据
            data = self._ensure_data_loaded(symbol, 'tick', start_date, end_date)
            data_type = 'tick'
            
            if data is None or data.empty:
                data = self._ensure_data_loaded(symbol, 'daily', start_date, end_date)
                data_type = 'daily'
                
            if data is None or data.empty:
                self.logger.warning(f"未能加载 {symbol} 的数据，跳过")
                continue
                
            # 为每行数据添加symbol和data_type
            data = data.copy()
            data['symbol'] = symbol
            data['data_type'] = data_type
            all_data.append(data)
        
        if not all_data:
            self.logger.warning("没有加载到任何数据，无法生成事件流")
            return
            
        # 合并所有数据并按时间排序
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data.sort_values(by='timestamp', inplace=True)
        
        # 生成事件流
        for _, row in combined_data.iterrows():
            symbol = row['symbol']
            data_type = row['data_type']
            timestamp = row['timestamp']
            
            # 更新此品种的最新数据
            row_dict = row.to_dict()
            self.latest_data[symbol] = row_dict
            
            if data_type == 'tick':
                # 直接返回tick数据
                tick_data = row_dict
                # 确保包含必要的字段
                if 'last_price' in tick_data:
                    tick_data['price'] = tick_data['last_price']
                yield tick_data
            else:
                # 创建市场事件
                try:
                    event = MarketEvent(
                        symbol=symbol,
                        timestamp=timestamp,
                        open_price=float(row['open']),
                        high_price=float(row['high']),
                        low_price=float(row['low']),
                        close_price=float(row['close']),
                        volume=int(row['volume'])
                    )
                    
                    # 如果有事件循环，发送事件
                    if self.event_loop:
                        self.event_loop.put_event(event)
                    
                    yield event
                except (KeyError, ValueError) as e:
                    self.logger.error(f"创建 {symbol} 市场事件失败: {e}")
                    continue
    
    def get_minute_bar_generator(self, symbol: str, minutes: int, start_date: datetime, end_date: datetime) -> Optional[Generator[BarData, None, None]]:
        """
        获取分钟K线数据生成器
        
        Args:
            symbol: 标的代码，如SHSE.600000
            minutes: 分钟数，如1为1分钟线，5为5分钟线
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Optional[Generator]: 分钟K线数据生成器
        """
        # 转换日期格式
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 加载数据
        data = self._ensure_data_loaded(symbol, 'minute', start_str, end_str, minutes=minutes)
        if data is None or data.empty:
            return None
        
        # 创建生成器
        def bars_generator():
            for _, row in data.iterrows():
                yield row.to_dict()
                
        return bars_generator()
    
    def get_tick_generator(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[Generator[TickData, None, None]]:
        """
        获取Tick数据生成器
        
        Args:
            symbol: 标的代码，如SHSE.600000
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Optional[Generator]: Tick数据生成器
        """
        # 转换日期格式
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 加载数据
        data = self._ensure_data_loaded(symbol, 'tick', start_str, end_str)
        if data is None or data.empty:
            return None
        
        # 创建生成器
        def tick_generator():
            for _, row in data.iterrows():
                tick_data = row.to_dict()
                # 确保包含必要的字段
                if 'last_price' in tick_data:
                    tick_data['price'] = tick_data['last_price']
                yield tick_data
                
        return tick_generator()


# 兼容性别名，保留旧的类名以向后兼容
GmDownloaderProvider = GmDataProvider

if __name__ == "__main__":
    # 简单测试
    from qte_core.event_loop import EventLoop
    import queue
    
    print("开始测试GmDataProvider...")
    
    # 创建事件循环
    event_loop = EventLoop()
    
    # 当前项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 掘金量化数据目录
    gm_data_dir = os.path.join(project_root, "myquant_data")
    
    # 假设我们找到了一个期货品种，这里先用第一个测试
    try:
        # 连接数据库检查可用品种
        daybar_dir = os.path.join(gm_data_dir, "basic_data", "day_bar")
        db_file = None
        for f in os.listdir(daybar_dir):
            if f.endswith('.dat'):
                db_file = os.path.join(daybar_dir, f)
                break
        
        if db_file:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT symbol FROM dists_day_bar LIMIT 5")
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if symbols:
                print(f"找到交易品种: {symbols}")
                
                # 创建数据提供者
                data_provider = GmDataProvider(
                    event_loop=event_loop,
                    gm_data_dir=gm_data_dir,
                    symbols=symbols[:2],  # 使用前两个品种测试
                    use_csv_cache=True
                )
                
                # 流式传输数据
                print("\n开始流式传输数据...")
                event_count = 0
                max_events = 5  # 只处理前5个事件用于测试
                
                for event in data_provider.stream_market_data():
                    event_count += 1
                    print(f"接收到事件 {event_count}: {event.symbol} 于 {event.timestamp}, 收盘价: {event.close_price}")
                    
                    if event_count >= max_events:
                        break
                
                # 测试获取最新K线
                for symbol in symbols[:2]:
                    latest_bar = data_provider.get_latest_bar(symbol)
                    if latest_bar:
                        print(f"\n{symbol} 最新K线: {latest_bar['timestamp']}, 收盘价: {latest_bar['close']}")
                    
                    # 测试获取历史K线
                    if symbol in data_provider.data:
                        df = data_provider.data[symbol]
                        if not df.empty:
                            start_date = df['timestamp'].min()
                            end_date = df['timestamp'].max()
                            mid_date = start_date + (end_date - start_date) / 2
                            
                            print(f"测试获取历史K线, 从 {start_date} 到 {mid_date}")
                            hist_bars = data_provider.get_historical_bars(symbol, start_date, mid_date)
                            
                            if hist_bars:
                                bars_list = list(hist_bars)
                                print(f"获取到 {len(bars_list)} 条历史K线")
                                if bars_list:
                                    print(f"第一条: {bars_list[0]['timestamp']}, 收盘价: {bars_list[0]['close']}")
                                    print(f"最后一条: {bars_list[-1]['timestamp']}, 收盘价: {bars_list[-1]['close']}")
            else:
                print("未找到交易品种")
        else:
            print("未找到数据库文件")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nGmDataProvider测试完成") 