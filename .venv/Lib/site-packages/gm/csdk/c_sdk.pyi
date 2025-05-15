# coding=utf-8
import datetime

from typing import List, Text


class QuoteItemLikeDict2(dict):
    bid_p = ... # type: float
    bid_v = ... # type: int
    ask_p = ... # type: float
    ask_v = ... # type: int


class TickLikeDict2(dict):
    quotes = ... # type: List[QuoteItemLikeDict2]
    symbol = ... # type: Text
    created_at = ... # type: datetime.datetime
    price = ... # type: float
    open = ... # type: float
    high = ... # type: float
    low = ... # type: float
    cum_volume = ... # type: float
    cum_amount = ... # type: float
    cum_position = ... # type: int
    last_amount = ... # type: float
    last_volume = ... # type: int
    trade_type = ... # type: int
    nanos = ... # type: int
    receive_local_time = ... # type: float
    flag = ... # type: int
    iopv = ... # type: float


class BarLikeDict2(dict):
    symbol = ... # type: Text
    eob = ... # type: datetime.datetime
    bob = ... # type: datetime.datetime
    open = ... # type: float
    close = ... # type: float
    high = ... # type: float
    low = ... # type: float
    volume = ... # type: float
    amount = ... # type: float
    pre_close = ... # type: float
    position = ... # type: int
    frequency = ... # type: Text
    receive_local_time = ... # type: float
