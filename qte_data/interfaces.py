from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generator, Optional, Union, List # Added List

from qte_core.events import MarketEvent # Assuming MarketEvent is in qte_core.events

# For now, using Any for data return types.
# Consider more specific types later, e.g., pandas DataFrame, or custom BarData class.
BarData = Any # Placeholder for a bar data structure (e.g., a Dict or a custom dataclass)
TickData = Any # Placeholder for a tick data structure

class DataProvider(ABC):
    """
    所有数据提供程序的抽象基类。
    数据提供程序负责获取历史或实时市场数据。
    """

    @abstractmethod
    def get_latest_bar(self, symbol: str) -> Optional[BarData]:
        """
        返回指定合约代码的最新K线柱。
        如果没有可用数据，则返回 None。
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest_bars(self, symbol: str, n: int = 1) -> Optional[List[BarData]]:
        """
        返回指定合约代码的 N 个最新K线柱。
        如果没有可用数据或K线柱数量不足，则返回 None。
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        # resolution: str = "1D" # e.g., "1T", "1H", "1D" - consider adding resolution/frequency
    ) -> Optional[Generator[BarData, None, None]]: # Or List[BarData]
        """
        生成器，在给定时期内为指定合约代码提供历史K线柱。
        如果没有可用数据，则返回 None。
        """
        raise NotImplementedError

    @abstractmethod
    def stream_market_data(self, symbols: List[str]) -> Generator[Union[MarketEvent, TickData], None, None]:
        """
        为指定的合约代码列表流式传输实时或模拟的市场数据。
        这将是事件驱动回测的主要数据源。
        对于K线柱，生成 MarketEvent；对于tick级数据，可以生成 TickData。
        """
        # This interface is more for live trading or very fine-grained backtests.
        # For basic bar-based backtesting, get_historical_bars might be used by TimeSim directly.
        # Or, this method could be adapted to simulate the stream from historical data.
        raise NotImplementedError

    # Optional: Methods for specific data types like options, futures, order book, news, etc.
    # @abstractmethod
    # def get_order_book(self, symbol: str) -> Optional[Any]:
    #     raise NotImplementedError

    # @abstractmethod
    # def get_news(self, symbol: str, limit: int = 10) -> Optional[List[Any]]:
    #     raise NotImplementedError