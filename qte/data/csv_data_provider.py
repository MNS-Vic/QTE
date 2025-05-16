import os
import pandas as pd
from typing import List, Dict, Optional, Tuple, Generator, Union, Any
from datetime import datetime, timedelta
import time # 用于模拟，在回测中通常不使用
from pathlib import Path
import logging

from qte.core.event_loop import EventLoop
from qte.core.events import MarketEvent
from .interfaces import DataProvider, BarData, TickData # Relative import

logger = logging.getLogger(__name__)

class CSVDataProvider(DataProvider):
    # 中文：从CSV文件提供市场数据的类。
    # 支持从多个CSV文件（每个交易品种一个）加载数据，
    # 并按时间顺序合并和流式传输这些数据。
    def __init__(self, event_loop: EventLoop, csv_dir_path: str, symbols: List[str]):
        # 中文：构造函数。
        # Args:
        # event_loop: 事件循环实例。
        # csv_dir_path: 存储CSV文件的目录路径。
        # symbols: 需要加载数据的交易品种列表 (例如 ['AAPL', 'GOOGL'])。
        # 每个交易品种的数据应位于 <csv_dir_path>/<SYMBOL>.csv
        self.event_loop = event_loop  # 直接存储，不调用super().__init__，因为接口没有__init__方法
        self.csv_dir_path: str = csv_dir_path
        self.symbols: List[str] = symbols
        self.data: Dict[str, pd.DataFrame] = {}  # 中文：存储每个交易品种加载的DataFrame
        self.latest_data: Dict[str, Dict] = {}  # 中文：存储每个交易品种的最新K线数据
        # 中文：存储所有交易品种的、按时间戳和品种排序的K线元组 (timestamp, symbol, bar_data_dict)
        self.all_bars_sorted: List[Dict] = []
        
        self._load_all_data()
        self._prepare_sorted_bars()

    def _load_all_data(self) -> None:
        # 中文：为构造函数中指定的所有交易品种加载数据。
        # 数据应包含列: timestamp, open, high, low, close, volume
        print(f"开始从目录 '{self.csv_dir_path}' 为品种 {self.symbols} 加载数据...") # Starting data load...
        for symbol in self.symbols:
            file_path = os.path.join(self.csv_dir_path, f"{symbol}.csv")
            if not os.path.exists(file_path):
                print(f"警告：数据文件 {file_path} 未找到，跳过品种 {symbol}。") # Warning: Data file not found, skipping symbol.
                continue
            try:
                df = pd.read_csv(file_path, parse_dates=['timestamp'])
                # 确保列名符合预期 (可以添加列名映射逻辑如果需要)
                required_columns = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
                if not required_columns.issubset(df.columns):
                    print(f"警告：文件 {file_path} 缺少必要列。需要: {required_columns}，实际拥有: {df.columns}。跳过此文件。") # Warning: Missing required columns.
                    continue

                df['timestamp'] = pd.to_datetime(df['timestamp']) # 确保timestamp列是datetime类型
                df.sort_values(by='timestamp', inplace=True) # 按时间戳排序
                df.reset_index(drop=True, inplace=True) # 重置索引
                self.data[symbol] = df
                print(f"数据已加载: {symbol} 从 {file_path}, 共 {len(df)} 条记录。") # Data loaded for symbol.
            except Exception as e:
                print(f"错误：加载数据文件 {file_path} 失败: {e}") # Error loading data file.

    def _prepare_sorted_bars(self) -> None:
        # 中文：准备一个包含所有交易品种、并按时间戳全局排序的K线数据列表。
        # 每个元素是一个字典，包含时间戳、品种代码和K线数据。
        print("开始准备和排序所有品种的K线数据...") # Starting preparation and sorting of all bars...
        temp_bars_list = []
        for symbol, df in self.data.items():
            for _, row in df.iterrows():
                bar_data_dict = row.to_dict()
                # 确保bar_data_dict中的timestamp是datetime对象
                if not isinstance(bar_data_dict['timestamp'], datetime):
                    bar_data_dict['timestamp'] = pd.to_datetime(bar_data_dict['timestamp'])
                
                # 添加品种代码到字典中，用于排序和事件创建
                bar_info_for_sorting = {'symbol_for_event': symbol, **bar_data_dict}
                temp_bars_list.append(bar_info_for_sorting)
        
        # 按时间戳排序，如果时间戳相同，则按品种代码排序 (作为次要排序键)
        self.all_bars_sorted = sorted(temp_bars_list, key=lambda x: (x['timestamp'], x['symbol_for_event']))
        
        if self.all_bars_sorted:
            print(f"总共 {len(self.all_bars_sorted)} 条K线数据已准备并排序。时间范围从 {self.all_bars_sorted[0]['timestamp']} 到 {self.all_bars_sorted[-1]['timestamp']}。") # Total bars prepared and sorted.
        else:
            print("没有K线数据被加载或准备。") # No bars loaded or prepared.

    # 修改方法签名以匹配接口
    def stream_market_data(self, symbols: List[str] = None) -> Generator[Union[MarketEvent, TickData], None, None]:
        """
        按时间顺序流式传输所有已加载交易品种的市场数据。
        每个K线数据点将作为一个 MarketEvent 发送到事件循环。
        
        Args:
            symbols: 可选，需要流式传输的交易品种列表。如果为None，则使用构造函数中的所有品种。
        
        Yields:
            MarketEvent: 市场事件对象
        """
        # 如果没有指定symbols，使用所有已加载的品种
        streaming_symbols = symbols if symbols is not None else self.symbols
        
        if not self.all_bars_sorted:
            print("没有数据可供流式传输。请检查数据加载过程。") # No data to stream.
            return
            # 这里应该是yield而不是return，但由于我们直接将事件放入队列而不是yield，所以使用return也可以
            
        print(f"开始流式传输 {len(self.all_bars_sorted)} 条市场数据...") # Starting to stream market data...
        for bar_info in self.all_bars_sorted:
            symbol = bar_info['symbol_for_event'] # 从排序字典中获取品种代码
            
            # 如果指定了symbols且当前symbol不在其中，则跳过
            if symbols is not None and symbol not in streaming_symbols:
                continue
                
            timestamp = bar_info['timestamp']
            
            # 更新此品种的最新数据 self.latest_data
            # 从 bar_info 复制，移除临时的 'symbol_for_event' 键
            current_bar_for_latest = {k: v for k, v in bar_info.items() if k != 'symbol_for_event'}
            self.latest_data[symbol] = current_bar_for_latest
            
            try:
                event = MarketEvent(
                    symbol=symbol,
                    timestamp=timestamp,
                    open_price=float(bar_info['open']),
                    high_price=float(bar_info['high']),
                    low_price=float(bar_info['low']),
                    close_price=float(bar_info['close']),
                    volume=int(bar_info['volume'])
                )
                self.event_loop.put_event(event)
                yield event  # 添加yield以满足接口要求
            except KeyError as e:
                print(f"错误：在为品种 {symbol} 于 {timestamp} 创建MarketEvent时，K线数据缺少键: {e}。数据: {bar_info}") # Error: Missing key in bar_data when creating MarketEvent
                continue
            except ValueError as e:
                print(f"错误：在为品种 {symbol} 于 {timestamp} 创建MarketEvent时，数据转换失败: {e}。数据: {bar_info}") # Error: Data conversion failed when creating MarketEvent
                continue
            
            # time.sleep(0.001) # 可选：模拟微小延迟，通常不在回测中使用
        print("所有市场数据已流式传输完毕。事件队列中现在应包含所有市场事件。") # All market data streamed. Event queue should now contain all market events.

    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        获取指定交易品种的最新已处理K线数据。
        返回一个包含K线数据的字典，或者如果该品种没有数据则返回None。
        
        Args:
            symbol: 交易品种代码
            
        Returns:
            Optional[BarData]: 最新K线数据或None
        """
        return self.latest_data.get(symbol)

    # 修改方法签名以匹配接口
    def get_latest_bars(self, symbol: str, n: int = 1) -> Optional[List[BarData]]:
        """
        返回指定合约代码的N个最新K线柱。
        如果没有可用数据或K线柱数量不足，则返回None。
        
        Args:
            symbol: 交易品种代码
            n: 需要获取的K线数量
            
        Returns:
            Optional[List[BarData]]: 包含N个最新K线的列表或None
        """
        if symbol not in self.data or symbol not in self.latest_data:
            return None
            
        # 获取当前流处理到的该品种的最新时间戳
        latest_streamed_timestamp_for_symbol = self.latest_data[symbol]['timestamp']
        
        # 从原始加载的DataFrame中筛选数据
        symbol_df = self.data[symbol]
        
        # 选择所有时间戳小于或等于当前最新时间戳的K线
        historical_bars_df = symbol_df[symbol_df['timestamp'] <= latest_streamed_timestamp_for_symbol].copy()
        
        if historical_bars_df.empty:
            return None
            
        # 返回最后n条记录
        latest_bars_df = historical_bars_df.tail(n)
        if latest_bars_df.empty:
            return None
            
        # 将DataFrame转换为字典列表
        latest_bars = [row.to_dict() for _, row in latest_bars_df.iterrows()]
        return latest_bars

    # 修改方法签名以匹配接口
    def get_historical_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Generator[BarData, None, None]]:
        """
        生成器，在给定时期内为指定合约代码提供历史K线柱。
        如果没有可用数据，则返回None。
        
        Args:
            symbol: 交易品种代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Optional[Generator[BarData, None, None]]: 生成历史K线的生成器或None
        """
        if symbol not in self.data:
            return None
            
        # 从原始加载的DataFrame中筛选数据
        symbol_df = self.data[symbol]
        
        # 选择时间范围内的K线
        historical_bars_df = symbol_df[
            (symbol_df['timestamp'] >= start_date) & 
            (symbol_df['timestamp'] <= end_date)
        ].copy()
        
        if historical_bars_df.empty:
            return None
            
        # 创建生成器
        def bars_generator():
            for _, row in historical_bars_df.iterrows():
                yield row.to_dict()
                
        return bars_generator()
        
    # 与接口兼容的额外便捷方法
    def get_n_historical_bars(self, symbol: str, n: int = 1) -> Optional[pd.DataFrame]:
        """
        获取指定交易品种的最近N条历史K线数据。
        这是一个便捷方法，不是接口的一部分。
        
        Args:
            symbol: 交易品种代码
            n: 需要获取的K线数量
            
        Returns:
            Optional[pd.DataFrame]: 包含N条历史K线的DataFrame或None
        """
        if symbol not in self.data or symbol not in self.latest_data:
            return None
        
        # 获取当前流处理到的该品种的最新时间戳
        latest_streamed_timestamp_for_symbol = self.latest_data[symbol]['timestamp']
        
        # 从原始加载的DataFrame中筛选数据
        symbol_df = self.data[symbol]
        
        # 选择所有时间戳小于或等于当前最新时间戳的K线
        historical_bars_df = symbol_df[symbol_df['timestamp'] <= latest_streamed_timestamp_for_symbol].copy()
        
        if historical_bars_df.empty:
            return None
            
        # 返回最后N条记录
        return historical_bars_df.tail(n)

if __name__ == '__main__':
    # 中文：CSVDataProvider 的使用示例和测试。
    print("CSVDataProvider 测试开始...") # CSVDataProvider test started...
    
    # 准备测试环境
    event_loop_test = EventLoop()
    test_data_dir = "temp_test_data"
    os.makedirs(test_data_dir, exist_ok=True)

    # 创建示例CSV文件 SYM1.csv
    sym1_data = {
        'timestamp': pd.to_datetime(['2023-01-01 09:00:00', '2023-01-01 09:02:00', '2023-01-01 09:04:00']),
        'open': [100, 101, 102],
        'high': [105, 106, 107],
        'low': [99, 100, 101],
        'close': [102, 103, 105],
        'volume': [1000, 1200, 1100]
    }
    sym1_df = pd.DataFrame(sym1_data)
    sym1_df.to_csv(os.path.join(test_data_dir, "SYM1.csv"), index=False)
    print(f"创建了示例文件: {os.path.join(test_data_dir, 'SYM1.csv')}") # Created sample file

    # 创建示例CSV文件 SYM2.csv (数据与SYM1交错)
    sym2_data = {
        'timestamp': pd.to_datetime(['2023-01-01 09:01:00', '2023-01-01 09:03:00', '2023-01-01 09:05:00']),
        'open': [200, 201, 202],
        'high': [205, 206, 207],
        'low': [199, 200, 201],
        'close': [202, 203, 205],
        'volume': [500, 600, 550]
    }
    sym2_df = pd.DataFrame(sym2_data)
    sym2_df.to_csv(os.path.join(test_data_dir, "SYM2.csv"), index=False)
    print(f"创建了示例文件: {os.path.join(test_data_dir, 'SYM2.csv')}") # Created sample file

    # 1. 初始化DataProvider
    print("\n1. 初始化 DataProvider (SYM1, SYM2)...") # Initializing DataProvider
    try:
        data_provider = CSVDataProvider(event_loop_test, csv_dir_path=test_data_dir, symbols=["SYM1", "SYM2", "NONEXISTENT_SYM"])
        print("DataProvider 初始化成功。") # DataProvider initialized successfully.
        print(f"加载的数据品种: {list(data_provider.data.keys())}") # Loaded data symbols
        print(f"排序后的总K线条数: {len(data_provider.all_bars_sorted)}") # Total sorted bars
        if data_provider.all_bars_sorted:
            print("前5条排序K线:") # First 5 sorted bars:
            for bar in data_provider.all_bars_sorted[:5]:
                print(f"  {bar['timestamp']} - {bar['symbol_for_event']} - C:{bar['close']}")
        else:
            print("没有K线被排序。") # No bars were sorted.

    except Exception as e:
        print(f"DataProvider 初始化失败: {e}") # DataProvider initialization failed
        data_provider = None # Ensure it's None if init fails

    if data_provider:
        # 2. 流式传输数据
        print("\n2. 流式传输数据...") # Streaming data...
        data_provider.stream_market_data()
        print("数据流式传输完成。检查事件队列:") # Data streaming complete. Check event queue:
        
        event_count = 0
        while not event_loop_test.event_queue.empty():
            try:
                event = event_loop_test.get_event(block=False)
                event_count +=1
                if isinstance(event, MarketEvent):
                    print(f"  从队列收到 MarketEvent: {event.timestamp} {event.symbol} C:{event.close_price} V:{event.volume}") # Received MarketEvent from queue
                    
                    # 测试 get_latest_bar 和 get_historical_bars
                    latest_bar_sym = data_provider.get_latest_bar(event.symbol)
                    # print(f"    最新 {event.symbol} K线 (get_latest_bar): C={latest_bar_sym['close'] if latest_bar_sym else 'N/A'}")
                    
                    hist_bars_1 = data_provider.get_historical_bars(event.symbol, N=1)
                    # if hist_bars_1 is not None and not hist_bars_1.empty:
                    #     print(f"    历史1条 {event.symbol} K线 (get_historical_bars): 最近收盘价={hist_bars_1.iloc[-1]['close']}")
                    # else:
                    #     print(f"    历史1条 {event.symbol} K线 (get_historical_bars): 无数据")


                else:
                    print(f"  从队列收到非市场事件: {type(event)}") # Received non-MarketEvent from queue
            except queue.Empty:
                break # 队列已空
        print(f"从事件队列中总共处理了 {event_count} 个事件。") # Total events processed from queue.

        # 3. 测试 get_latest_bar 和 get_historical_bars 在流结束后
        print("\n3. 测试流结束后的API调用:") # Testing API calls after streaming:
        latest_sym1 = data_provider.get_latest_bar("SYM1")
        print(f"  SYM1 最新K线 (get_latest_bar): C={latest_sym1['close'] if latest_sym1 else 'N/A'} at {latest_sym1['timestamp'] if latest_sym1 else ''}")
        
        latest_sym2 = data_provider.get_latest_bar("SYM2")
        print(f"  SYM2 最新K线 (get_latest_bar): C={latest_sym2['close'] if latest_sym2 else 'N/A'} at {latest_sym2['timestamp'] if latest_sym2 else ''}")

        hist_sym1_N2 = data_provider.get_historical_bars("SYM1", N=2)
        if hist_sym1_N2 is not None and not hist_sym1_N2.empty:
            print(f"  SYM1 历史2条K线 (get_historical_bars), 最近的一条: T={hist_sym1_N2.iloc[-1]['timestamp']}, C={hist_sym1_N2.iloc[-1]['close']}") # SYM1 historical 2 bars
            print(hist_sym1_N2)
        else:
            print(f"  SYM1 历史2条K线: 无数据或返回空DataFrame") # SYM1 historical 2 bars: No data or empty DataFrame

        hist_sym2_N3 = data_provider.get_historical_bars("SYM2", N=3)
        if hist_sym2_N3 is not None and not hist_sym2_N3.empty:
            print(f"  SYM2 历史3条K线 (get_historical_bars), 最近的一条: T={hist_sym2_N3.iloc[-1]['timestamp']}, C={hist_sym2_N3.iloc[-1]['close']}") # SYM2 historical 3 bars
            print(hist_sym2_N3)
        else:
            print(f"  SYM2 历史3条K线: 无数据或返回空DataFrame") # SYM2 historical 3 bars: No data or empty DataFrame

    # 清理测试文件和目录
    try:
        os.remove(os.path.join(test_data_dir, "SYM1.csv"))
        os.remove(os.path.join(test_data_dir, "SYM2.csv"))
        os.rmdir(test_data_dir)
        print(f"\n已清理测试目录和文件: {test_data_dir}") # Cleaned up test directory and files.
    except OSError as e:
        print(f"清理测试文件时出错: {e}") # Error cleaning up test files.
    
    print("\nCSVDataProvider 测试结束。") # CSVDataProvider test finished. 