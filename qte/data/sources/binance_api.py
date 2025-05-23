"""
币安API数据源

通过币安API下载数据并存储为CSV，提供给QTE框架使用
"""

import pandas as pd
import os
import time
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, timedelta
import requests

from ..data_source_interface import BaseDataSource

class BinanceApiSource(BaseDataSource):
    """币安API数据源实现"""
    
    def __init__(self, 
                 data_dir: str = "data/binance", 
                 use_cache: bool = True, 
                 base_url: str = "https://api.binance.com",
                 **kwargs):
        """
        初始化币安API数据源
        
        Parameters
        ----------
        data_dir : str, optional
            数据存储目录, by default "data/binance"
        use_cache : bool, optional
            是否使用缓存, by default True
        base_url : str, optional
            币安API基础URL, by default "https://api.binance.com"
        """
        super().__init__(use_cache=use_cache, **kwargs)
        self.base_url = base_url
        self.data_dir = data_dir
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 缓存交易对信息
        self._symbols_cache = None
        self._last_symbols_update = 0
        self.symbols_cache_ttl = 3600  # 1小时
        
        print(f"[BinanceApiSource] 初始化完成，数据目录: {os.path.abspath(self.data_dir)}")
    
    def connect(self, **kwargs) -> bool:
        """
        连接币安API
        
        Returns
        -------
        bool
            连接是否成功
        """
        try:
            # 测试API连接
            response = requests.get(f"{self.base_url}/api/v3/ping", timeout=10)
            self._connected = response.status_code == 200
            
            if self._connected:
                print("[BinanceApiSource] 成功连接到币安API")
            else:
                print(f"[BinanceApiSource] 连接失败，状态码: {response.status_code}")
                
            return self._connected
            
        except Exception as e:
            print(f"[BinanceApiSource] 连接币安API时发生错误: {e}")
            self._connected = False
            return False
    
    def get_symbols(self, market: Optional[str] = None, **kwargs) -> List[str]:
        """
        获取可用的交易对列表
        
        Parameters
        ----------
        market : Optional[str], optional
            市场筛选（如'USDT', 'BTC'等）, by default None
            
        Returns
        -------
        List[str]
            交易对列表
        """
        if not self._ensure_connected():
            return []
        
        # 检查缓存
        if (self._symbols_cache is not None and 
            time.time() - self._last_symbols_update < self.symbols_cache_ttl):
            symbols = self._symbols_cache
        else:
            # 从API获取交易对信息
            try:
                response = requests.get(f"{self.base_url}/api/v3/exchangeInfo", timeout=10)
                if response.status_code != 200:
                    print(f"[BinanceApiSource] 获取交易对信息失败: {response.status_code}")
                    return []
                
                data = response.json()
                symbols = [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING']
                
                # 更新缓存
                self._symbols_cache = symbols
                self._last_symbols_update = time.time()
                
            except Exception as e:
                print(f"[BinanceApiSource] 获取交易对列表时发生错误: {e}")
                return []
        
        # 按市场筛选
        if market:
            symbols = [s for s in symbols if s.endswith(market)]
        
        print(f"[BinanceApiSource] 获取到 {len(symbols)} 个交易对")
        return symbols
    
    def _download_klines(self, symbol: str, interval: str, 
                        start_time: Optional[int] = None, 
                        end_time: Optional[int] = None,
                        limit: int = 1000) -> List[List]:
        """
        下载K线数据
        
        Parameters
        ----------
        symbol : str
            交易对
        interval : str
            时间间隔
        start_time : Optional[int], optional
            开始时间戳(毫秒), by default None
        end_time : Optional[int], optional
            结束时间戳(毫秒), by default None
        limit : int, optional
            数据条数限制, by default 1000
            
        Returns
        -------
        List[List]
            K线数据
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response = requests.get(f"{self.base_url}/api/v3/klines", 
                                  params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[BinanceApiSource] API请求失败: {response.status_code}, {response.text}")
                return []
                
        except Exception as e:
            print(f"[BinanceApiSource] 下载K线数据时发生错误: {e}")
            return []
    
    def _interval_to_binance(self, frequency: str) -> str:
        """
        将QTE频率格式转换为币安API格式
        
        Parameters
        ----------
        frequency : str
            QTE频率格式
            
        Returns
        -------
        str
            币安API频率格式
        """
        mapping = {
            '1m': '1m',
            '5m': '5m', 
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w',
            '1M': '1M'
        }
        return mapping.get(frequency, '1d')
    
    def _get_csv_filename(self, symbol: str, frequency: str) -> str:
        """获取CSV文件名"""
        return os.path.join(self.data_dir, f"{symbol}_{frequency}.csv")
    
    def _load_existing_data(self, csv_file: str) -> Optional[pd.DataFrame]:
        """加载已存在的CSV数据"""
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                return df
            except Exception as e:
                print(f"[BinanceApiSource] 加载现有数据失败: {e}")
        return None
    
    def _save_data_to_csv(self, data: pd.DataFrame, csv_file: str):
        """保存数据到CSV"""
        try:
            # 重置索引以保存datetime列
            data_to_save = data.reset_index()
            data_to_save.to_csv(csv_file, index=False)
            print(f"[BinanceApiSource] 数据已保存到: {csv_file}")
        except Exception as e:
            print(f"[BinanceApiSource] 保存数据失败: {e}")
    
    def _get_bars_impl(self, symbol: str, 
                     start_date: Optional[Union[str, datetime, date]] = None, 
                     end_date: Optional[Union[str, datetime, date]] = None, 
                     frequency: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """
        实现具体的获取K线数据方法
        
        Parameters
        ----------
        symbol : str
            交易对代码
        start_date : Optional[Union[str, datetime, date]], optional
            开始日期, by default None
        end_date : Optional[Union[str, datetime, date]], optional
            结束日期, by default None
        frequency : str, optional
            数据频率, by default '1d'
            
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据DataFrame
        """
        if not self._ensure_connected():
            return None
        
        # 转换频率格式
        binance_interval = self._interval_to_binance(frequency)
        
        # 获取CSV文件路径
        csv_file = self._get_csv_filename(symbol, frequency)
        
        # 加载现有数据
        existing_data = self._load_existing_data(csv_file)
        
        # 确定数据下载范围
        if start_date:
            start_dt = pd.to_datetime(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=365)  # 默认1年
        
        if end_date:
            end_dt = pd.to_datetime(end_date) 
        else:
            end_dt = datetime.now()
        
        # 检查是否需要下载新数据
        need_download = True
        if existing_data is not None and not existing_data.empty:
            data_start = existing_data.index.min()
            data_end = existing_data.index.max()
            
            # 如果现有数据已覆盖请求范围，直接使用
            if data_start <= start_dt and data_end >= end_dt:
                print(f"[BinanceApiSource] 使用现有数据: {symbol} {frequency}")
                need_download = False
            else:
                # 需要补充数据
                if data_end < end_dt:
                    start_dt = data_end + timedelta(milliseconds=1)
                    print(f"[BinanceApiSource] 需要补充数据从 {start_dt} 到 {end_dt}")
        
        if need_download:
            print(f"[BinanceApiSource] 开始下载数据: {symbol} {frequency} ({start_dt} 到 {end_dt})")
            
            # 转换为时间戳
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)
            
            all_klines = []
            current_start = start_timestamp
            
            # 分批下载数据（币安API限制每次最多1000条）
            while current_start < end_timestamp:
                print(f"[BinanceApiSource] 下载批次: {datetime.fromtimestamp(current_start/1000)}")
                
                klines = self._download_klines(
                    symbol=symbol,
                    interval=binance_interval,
                    start_time=current_start,
                    end_time=min(current_start + 1000 * self._get_interval_ms(binance_interval), end_timestamp),
                    limit=1000
                )
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                
                # 更新下一批的开始时间
                current_start = klines[-1][6] + 1  # Close time + 1ms
                
                # 避免请求过于频繁
                time.sleep(0.1)
            
            if all_klines:
                # 转换为DataFrame
                new_data = self._klines_to_dataframe(all_klines)
                
                # 合并现有数据
                if existing_data is not None and not existing_data.empty:
                    combined_data = pd.concat([existing_data, new_data]).drop_duplicates()
                    combined_data.sort_index(inplace=True)
                else:
                    combined_data = new_data
                
                # 保存到CSV
                self._save_data_to_csv(combined_data, csv_file)
                
                # 返回请求范围内的数据
                mask = (combined_data.index >= start_dt) & (combined_data.index <= end_dt)
                return combined_data[mask]
            else:
                print(f"[BinanceApiSource] 未获取到数据: {symbol}")
                return None
        else:
            # 使用现有数据
            mask = (existing_data.index >= start_dt) & (existing_data.index <= end_dt)
            return existing_data[mask]
    
    def _get_interval_ms(self, interval: str) -> int:
        """获取时间间隔的毫秒数"""
        mapping = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
            '1M': 30 * 24 * 60 * 60 * 1000  # 近似值
        }
        return mapping.get(interval, 24 * 60 * 60 * 1000)
    
    def _klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """
        将币安K线数据转换为DataFrame
        
        Parameters
        ----------
        klines : List[List]
            币安K线数据
            
        Returns
        -------
        pd.DataFrame
            标准格式的K线数据
        """
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # 转换数据类型
        df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # 设置索引并选择需要的列
        df.set_index('datetime', inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]
    
    def get_bars(self, symbol: str, 
                start_date: Optional[Union[str, datetime, date]] = None, 
                end_date: Optional[Union[str, datetime, date]] = None, 
                frequency: str = '1d', **kwargs) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Parameters
        ----------
        symbol : str
            交易对代码
        start_date : Optional[Union[str, datetime, date]], optional
            开始日期, by default None
        end_date : Optional[Union[str, datetime, date]], optional
            结束日期, by default None
        frequency : str, optional
            数据频率, by default '1d'
        
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据DataFrame
        """
        # 确保已连接
        if not self._ensure_connected():
            return None
        
        # 使用缓存或直接获取数据
        if self._use_cache:
            return self.get_bars_with_cache(symbol, start_date, end_date, frequency, **kwargs)
        else:
            return self._get_bars_impl(symbol, start_date, end_date, frequency, **kwargs)

    def get_popular_symbols(self, base_currency: str = 'USDT', limit: int = 10) -> List[str]:
        """
        获取热门交易对
        
        Parameters
        ----------
        base_currency : str, optional
            基础货币, by default 'USDT'
        limit : int, optional
            返回数量限制, by default 10
            
        Returns
        -------
        List[str]
            热门交易对列表
        """
        popular_pairs = [
            f'BTC{base_currency}', f'ETH{base_currency}', f'BNB{base_currency}',
            f'ADA{base_currency}', f'DOT{base_currency}', f'XRP{base_currency}',
            f'LTC{base_currency}', f'LINK{base_currency}', f'BCH{base_currency}',
            f'SOL{base_currency}', f'MATIC{base_currency}', f'UNI{base_currency}',
            f'DOGE{base_currency}', f'AVAX{base_currency}', f'ATOM{base_currency}'
        ]
        
        # 验证交易对是否存在
        available_symbols = self.get_symbols()
        valid_pairs = [pair for pair in popular_pairs if pair in available_symbols]
        
        return valid_pairs[:limit] 