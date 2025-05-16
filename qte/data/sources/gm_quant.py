import pandas as pd
import time
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, date

from ..data_source_interface import BaseDataSource

class GmQuantSource(BaseDataSource):
    """掘金量化数据源实现"""
    
    def __init__(self, token: Optional[str] = None, use_cache: bool = True, **kwargs):
        """
        初始化掘金量化数据源
        
        Parameters
        ----------
        token : Optional[str], optional
            掘金量化API的Token, by default None
        use_cache : bool, optional
            是否使用缓存, by default True
        """
        super().__init__(use_cache=use_cache, **kwargs)
        self.token = token
        self.gm_client = None
        self.connected = False
        self.retry_count = 3
        self.retry_delay = 1  # 重试延迟秒数
        
        # 本地缓存目录
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cache', 'gm_quant')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def connect(self, token: Optional[str] = None, **kwargs) -> bool:
        """
        连接掘金API
        
        Parameters
        ----------
        token : Optional[str], optional
            掘金量化API的Token, by default None
            
        Returns
        -------
        bool
            连接是否成功
        """
        if token:
            self.token = token
            
        if not self.token:
            print("[GmQuantSource] 错误: 未提供Token. 无法连接掘金API")
            return False
            
        try:
            # 导入掘金API
            try:
                from gm.api import set_token
                set_token(self.token)
                self.connected = True
                print("[GmQuantSource] 成功连接到掘金API")
                return True
            except ImportError:
                print("[GmQuantSource] 错误: 未找到gm模块. 请安装掘金API: pip install gm")
                return False
            except Exception as e:
                print(f"[GmQuantSource] 连接掘金API时发生错误: {e}")
                return False
        except Exception as e:
            print(f"[GmQuantSource] 连接掘金API时发生一般错误: {e}")
            return False
    
    def get_symbols(self, market: Optional[str] = None) -> List[str]:
        """
        获取可用的标的列表
        
        Parameters
        ----------
        market : Optional[str], optional
            市场代码, by default None
            可选值: 'SHSE' (上海), 'SZSE' (深圳), 'CFFEX' (中金所), 
                   'SHFE' (上期所), 'DCE' (大商所), 'CZCE' (郑商所)
            
        Returns
        -------
        List[str]
            标的列表
        """
        if not self._ensure_connected():
            return []
            
        try:
            from gm.api import get_instruments
            
            exchanges = None
            if market:
                exchanges = market
                
            instruments = get_instruments(exchanges=exchanges, fields='symbol,sec_name,exchange')
            symbols = [item['symbol'] for item in instruments]
            print(f"[GmQuantSource] 获取到 {len(symbols)} 个标的")
            return symbols
        except Exception as e:
            print(f"[GmQuantSource] 获取标的列表时发生错误: {e}")
            return []
    
    def get_bars(self, symbol: str, start_date: Optional[str] = None, 
                end_date: Optional[str] = None, frequency: str = '1d', 
                adjust: str = 'ADJUST_PREV', **kwargs) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Parameters
        ----------
        symbol : str
            标的代码 (例如: 'SHSE.600000')
        start_date : Optional[str], optional
            开始日期 (格式: 'YYYY-MM-DD'), by default None
        end_date : Optional[str], optional
            结束日期 (格式: 'YYYY-MM-DD'), by default None
        frequency : str, optional
            数据频率, by default '1d'
            支持的值:
            - 分钟线: '1m', '5m', '15m', '30m', '60m'
            - 日线: '1d'
            - 周线: '1w'
            - 月线: '1M'
        adjust : str, optional
            复权方式, by default 'ADJUST_PREV'
            可选值: 
            - 'ADJUST_NONE': 不复权
            - 'ADJUST_PREV': 前复权
            - 'ADJUST_POST': 后复权
            
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据DataFrame
        """
        if not self._ensure_connected():
            return None
            
        # 转换日期格式
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # 转换频率格式
        freq_map = {
            '1m': '60s', '5m': '300s', '15m': '900s', '30m': '1800s', '60m': '3600s',
            '1d': '1d', '1w': '1w', '1M': '1m'
        }
        gm_frequency = freq_map.get(frequency, '1d')
        
        # 转换复权方式
        adjust_map = {
            'ADJUST_NONE': 'none', 'ADJUST_PREV': 'pre', 'ADJUST_POST': 'post'
        }
        gm_adjust = adjust_map.get(adjust, 'pre')
        
        # 检查缓存
        use_cache = kwargs.get('use_cache', True)
        if use_cache:
            cache_file = os.path.join(self.cache_dir, 
                                     f"{symbol.replace('.', '_')}_{frequency}_{start_date}_{end_date}_{adjust}.csv")
            if os.path.exists(cache_file):
                try:
                    df_cache = pd.read_csv(cache_file)
                    df_cache['datetime'] = pd.to_datetime(df_cache['datetime'])
                    df_cache.set_index('datetime', inplace=True)
                    print(f"[GmQuantSource] 从缓存加载数据: {cache_file}")
                    return df_cache
                except Exception as e:
                    print(f"[GmQuantSource] 读取缓存数据失败: {e}")
        
        # 从API获取数据
        try:
            from gm.api import history
            
            for attempt in range(self.retry_count):
                try:
                    # 掘金API调用
                    data = history(symbol=symbol, 
                                   frequency=gm_frequency, 
                                   start_time=start_date, 
                                   end_time=end_date,
                                   fields='bob,open,high,low,close,volume,amount,adjusted_factor,eob,position',
                                   adjust=gm_adjust,
                                   df=True)
                    
                    if data is None or data.empty:
                        print(f"[GmQuantSource] 警告: 未获取到数据 (Symbol: {symbol}, {start_date} to {end_date})")
                        return None
                        
                    # 列名转换为标准格式
                    rename_map = {
                        'bob': 'datetime',  # 区间开始时间
                        'eob': 'eob',       # 区间结束时间
                        'open': 'open',
                        'high': 'high', 
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume',
                        'amount': 'amount', 
                        'position': 'position',
                        'adjusted_factor': 'adjusted_factor'
                    }
                    data.rename(columns=rename_map, inplace=True)
                    
                    # 处理日期格式
                    # 对于日线以上级别使用eob作为索引，分钟线使用bob
                    if frequency in ['1d', '1w', '1M']:
                        if 'eob' in data.columns:
                            data['datetime'] = pd.to_datetime(data['eob'])
                            data.drop('eob', axis=1, inplace=True)
                    
                    # 设置索引
                    data['datetime'] = pd.to_datetime(data['datetime'])
                    data.set_index('datetime', inplace=True)
                    
                    # 缓存数据
                    if use_cache:
                        data.reset_index().to_csv(cache_file, index=False)
                        print(f"[GmQuantSource] 数据已缓存到: {cache_file}")
                    
                    # 只保留必要的列
                    required_cols = ['open', 'high', 'low', 'close', 'volume']
                    avail_cols = [col for col in required_cols if col in data.columns]
                    
                    print(f"[GmQuantSource] 成功获取数据: {symbol}, 行数: {len(data)}")
                    return data[avail_cols]
                    
                except Exception as e:
                    print(f"[GmQuantSource] 获取数据时发生错误 (尝试 {attempt+1}/{self.retry_count}): {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
            
            return None
                
        except ImportError:
            print("[GmQuantSource] 错误: 未找到gm模块. 请安装掘金API: pip install gm")
            return None
        except Exception as e:
            print(f"[GmQuantSource] 获取K线数据时发生一般错误: {e}")
            return None
    
    def get_ticks(self, symbol: str, date: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取Tick数据
        
        Parameters
        ----------
        symbol : str
            标的代码 (例如: 'SHSE.600000')
        date : str
            日期 (格式: 'YYYY-MM-DD')
            
        Returns
        -------
        Optional[pd.DataFrame]
            Tick数据
        """
        if not self._ensure_connected():
            return None
            
        # 检查缓存
        use_cache = kwargs.get('use_cache', True)
        if use_cache:
            cache_file = os.path.join(self.cache_dir, 
                                     f"{symbol.replace('.', '_')}_tick_{date}.csv")
            if os.path.exists(cache_file):
                try:
                    df_cache = pd.read_csv(cache_file)
                    df_cache['datetime'] = pd.to_datetime(df_cache['datetime'])
                    df_cache.set_index('datetime', inplace=True)
                    print(f"[GmQuantSource] 从缓存加载Tick数据: {cache_file}")
                    return df_cache
                except Exception as e:
                    print(f"[GmQuantSource] 读取缓存Tick数据失败: {e}")
            
        try:
            from gm.api import get_ticks
            
            for attempt in range(self.retry_count):
                try:
                    # 转换为掘金API的日期格式
                    dt_obj = datetime.strptime(date, '%Y-%m-%d')
                    ticks = get_ticks(symbol=symbol, 
                                      begin_time=dt_obj,
                                      end_time=dt_obj + timedelta(days=1),
                                      df=True)
                    
                    if ticks is None or ticks.empty:
                        print(f"[GmQuantSource] 警告: 未获取到Tick数据 (Symbol: {symbol}, Date: {date})")
                        return None
                    
                    # 列名转换为标准格式
                    rename_map = {
                        'created_at': 'datetime',
                        'price': 'price',
                        'volume': 'volume',
                        'bid_price': 'bid_price',
                        'bid_volume': 'bid_volume',
                        'ask_price': 'ask_price',
                        'ask_volume': 'ask_volume'
                    }
                    
                    # 选择需要的列并重命名
                    avail_cols = [col for col in rename_map.keys() if col in ticks.columns]
                    ticks = ticks[avail_cols].rename(columns={col: rename_map[col] for col in avail_cols})
                    
                    # 处理日期格式
                    ticks['datetime'] = pd.to_datetime(ticks['datetime'])
                    ticks.set_index('datetime', inplace=True)
                    
                    # 缓存数据
                    if use_cache:
                        ticks.reset_index().to_csv(cache_file, index=False)
                        print(f"[GmQuantSource] Tick数据已缓存到: {cache_file}")
                    
                    print(f"[GmQuantSource] 成功获取Tick数据: {symbol}, 行数: {len(ticks)}")
                    return ticks
                    
                except Exception as e:
                    print(f"[GmQuantSource] 获取Tick数据时发生错误 (尝试 {attempt+1}/{self.retry_count}): {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
            
            return None
                
        except ImportError:
            print("[GmQuantSource] 错误: 未找到gm模块. 请安装掘金API: pip install gm")
            return None
        except Exception as e:
            print(f"[GmQuantSource] 获取Tick数据时发生一般错误: {e}")
            return None
    
    def get_fundamentals(self, table: str, symbols: List[str], 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, 
                        fields: Optional[List[str]] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取基本面数据
        
        Parameters
        ----------
        table : str
            基本面数据表名
            可选值:
            - 'balance_sheet': 资产负债表
            - 'income': 利润表
            - 'cash_flow': 现金流量表
            - 'fundamentals_balance': 主要财务指标资产负债表
            - 'fundamentals_income': 主要财务指标利润表
            - 'fundamentals_cashflow': 主要财务指标现金流量表
            - 'trading_derivative_indicator': 交易衍生指标
        symbols : List[str]
            标的代码列表
        start_date : Optional[str], optional
            开始日期 (格式: 'YYYY-MM-DD'), by default None
        end_date : Optional[str], optional
            结束日期 (格式: 'YYYY-MM-DD'), by default None
        fields : Optional[List[str]], optional
            字段列表, by default None
            
        Returns
        -------
        Optional[pd.DataFrame]
            基本面数据
        """
        if not self._ensure_connected():
            return None
            
        # 转换日期格式
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 检查缓存
        use_cache = kwargs.get('use_cache', True)
        symbols_str = '_'.join([s.replace('.', '_') for s in symbols[:3]])
        if len(symbols) > 3:
            symbols_str += f"_and_{len(symbols)-3}_more"
        
        if use_cache:
            # 创建缓存文件名
            fields_str = 'all' if not fields else '_'.join(fields[:3])
            if fields and len(fields) > 3:
                fields_str += f"_and_{len(fields)-3}_more"
                
            cache_file = os.path.join(self.cache_dir, 
                                     f"{table}_{symbols_str}_{start_date}_{end_date}_{fields_str}.csv")
            if os.path.exists(cache_file):
                try:
                    df_cache = pd.read_csv(cache_file)
                    print(f"[GmQuantSource] 从缓存加载基本面数据: {cache_file}")
                    return df_cache
                except Exception as e:
                    print(f"[GmQuantSource] 读取缓存基本面数据失败: {e}")
            
        try:
            from gm.api import get_fundamentals
            
            for attempt in range(self.retry_count):
                try:
                    # 掘金API调用
                    data = get_fundamentals(table=table,
                                           symbols=symbols,
                                           start_date=start_date,
                                           end_date=end_date,
                                           fields=fields,
                                           df=True)
                    
                    if data is None or data.empty:
                        print(f"[GmQuantSource] 警告: 未获取到基本面数据 (Table: {table}, Symbols: {symbols_str})")
                        return None
                    
                    # 缓存数据
                    if use_cache:
                        data.to_csv(cache_file, index=False)
                        print(f"[GmQuantSource] 基本面数据已缓存到: {cache_file}")
                    
                    print(f"[GmQuantSource] 成功获取基本面数据: {table}, 行数: {len(data)}")
                    return data
                    
                except Exception as e:
                    print(f"[GmQuantSource] 获取基本面数据时发生错误 (尝试 {attempt+1}/{self.retry_count}): {e}")
                    if attempt < self.retry_count - 1:
                        time.sleep(self.retry_delay)
            
            return None
                
        except ImportError:
            print("[GmQuantSource] 错误: 未找到gm模块. 请安装掘金API: pip install gm")
            return None
        except Exception as e:
            print(f"[GmQuantSource] 获取基本面数据时发生一般错误: {e}")
            return None
    
    def _ensure_connected(self) -> bool:
        """确保已连接到掘金API"""
        if not self.connected:
            print("[GmQuantSource] 尚未连接到掘金API，尝试连接...")
            return self.connect()
        return True 