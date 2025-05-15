# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

import logging
import sys
import time
import subprocess
from gm import __version__
import os
import sys
import six
from typing import Dict, Text, Any, List, Union
from datetime import date, datetime, timedelta, timezone
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp

GmDate = Union[Text, datetime, date]  # 自定义gm里可表示时间的类型
TextNone = Union[Text, None]  # 可表示str或者None类型
GmSymbols = Union[Text, List[Text]]  # 用逗号分割或list股票代码表示多个股票

gmsdklogger = logging.getLogger('gmsdklogger')
gmsdklogger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setLevel(logging.INFO)
gmformat = logging.Formatter(
    '%(asctime)-15s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')
console_handler.setFormatter(gmformat)
gmsdklogger.addHandler(console_handler)

__add_logfile = False


BJ_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")    # 东八区
UTC = timezone(timedelta(hours=0))


def gmsdklog2file():
    """
    增加一个handler, 把gmsdklog写入到日志文件. 只调用一次
    """
    global __add_logfile
    if __add_logfile:
        return

    file_handler = logging.FileHandler(
        'gmsdk_{}.log'.format(datetime.now().strftime("%Y%m%d%H%M%S")))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(gmformat)
    gmsdklogger.addHandler(file_handler)
    __add_logfile = True


def str_lowerstrip(s):
    # type: (Text) -> Text
    """
    把字符串进行lower跟strip操作
    """
    return s.lower().strip() if s else ''


def date2datetime(d):
    # type: (Union[date,str]) -> datetime
    """
    把date类型转换为datetime类型
    """
    if isinstance(d, six.string_types):
        if len(d) == 8:
            return datetime.strptime(d, '%Y%m%d')
        if len(d) == 10:
            return datetime.strptime(d, '%Y-%m-%d')
        raise Exception('字符串{}不能转为datetime'.format(d))
    return datetime.combine(d, datetime.min.time())


def str2datetime(d):
    # type: (Text) -> Union[datetime, None]
    """
    把字符串转成datetime类型
    """
    if len(d) == 8:
        return datetime.strptime(d, '%Y%m%d')
    if len(d) == 10:
        return datetime.strptime(d, '%Y-%m-%d')
    if len(d) == 17:  # 类于 201707010 8:50:00
        return datetime.strptime(d, '%Y%m%d %H:%M:%S')
    if len(d) == 19:  # 类于 2017-07-01 08:50:00
        return datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
    gmsdklogger.error(
        "字符串 %s 不能格式化成datetime类型, 请使用类似于 2017-07-01 08:50:00 这种格式", d)
    return None


def protobuf_timestamp2bj_datetime(timestamp):
    # type: (Timestamp) -> Union[datetime, None]
    """
    把 protobuf 的 timestamp(utc) 转为北京时间 datetime类型
    :return:
    """
    if timestamp is None:
        return None
    # +8 小时
    deltasec = timestamp.seconds + 8 * 60 * 60 + \
        timestamp.nanos / float(_NANOS_PER_SECOND)
    d = datetime(1970, 1, 1) + timedelta(seconds=deltasec)
    d = d.replace(tzinfo=BJ_TZ)
    return d


def protobuf_timestamp2datetime(timestamp):
    # type: (Timestamp) -> Union[datetime, None]
    """
    把 protobuf 的 timestamp 转为 datetime类型
    :return:
    """
    if timestamp is None:
        return None
    deltasec = timestamp.seconds + timestamp.nanos / float(_NANOS_PER_SECOND)
    return datetime(1970, 1, 1) + timedelta(seconds=deltasec)


# 来自于 google.protobuf.internal.well_nkown_types.py 里定义的变量
_NANOS_PER_SECOND = 1000000000


def protomessage2dict(protomessageobj, dictobj, *keys):
    # type: (Message, Dict[Text, Any], List[Text]) -> None
    """
    把 proto的message 上的指定的property,附值到dictobj上.其中timestamp会转换为 datetime类型
    """
    for k in keys:
        pv = getattr(protomessageobj, k, None)
        if need_round(protomessageobj.DESCRIPTOR.name, k):
            value = round_float(value)
        if pv is not None:
            if isinstance(pv, Timestamp):
                if pv.ListFields():
                    # pv.ToDatetime()  不要使用这个方法, 这个方法在python32位时, 最小只能转到 1969-12-31 12:00:00, 因为受限于
                    # ValueError: timestamp out of range for platform localtime()/gmtime() function
                    deltasec = pv.seconds + pv.nanos / float(_NANOS_PER_SECOND)
                    # 认为从服务器返回的时间都是utc时间
                    dictobj[k] = (
                        datetime(1970, 1, 1) + timedelta(seconds=deltasec)).replace(tzinfo=UTC)
                else:
                    dictobj[k] = None
            else:
                dictobj[k] = pv


def format_datetime_str(d):
    if d is None:
        dt = datetime.now()
    elif isinstance(d, six.string_types):
        dlen = len(d)
        if dlen == 19:
            dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
        elif dlen == 17:
            dt = datetime.strptime(d, "%Y%m%d %H:%M:%S")
        elif dlen == 10:
            dt = datetime.strptime(d, "%Y-%m-%d")
        elif dlen == 8:
            dt = datetime.strptime(d, "%Y%m%d")
        else:
            raise ValueError("无效时间: {}".format(d))
    elif isinstance(d, (date, datetime)):
        dt = d
    else:
        raise ValueError("时间类型错误: {}".format(d))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def to_datestr(d):
    # type: (GmDate) -> TextNone
    """
    把datetime.date或datetime.datetime, 或者 yyyy-mm-dd, yyyymmdd 表示日期的字符串统一转换为 yyyy-mm-dd的字符串
    如果不能转换返回None
    """
    date_str = ''
    if isinstance(d, (date, datetime)):
        date_str = d.strftime('%Y-%m-%d')
    if isinstance(d, six.string_types):
        if len(d) == 8:
            try:
                dt = datetime.strptime(d, '%Y%m%d')
                date_str = dt.strftime('%Y-%m-%d')
            except ValueError as e:
                pass
        if len(d) == 10:
            try:
                datetime.strptime(d, '%Y-%m-%d')
                date_str = d
            except ValueError as e:
                pass

    return date_str if date_str else d


def utc_datetime2beijing_datetime(dt):
    # type: (datetime) -> datetime
    """
    把utc的datetime转化为北京时间的datetime. 这样2016-04-16T16:00:00+00:00 转化后得到的date就是 2016-04-17
    """
    return dt.replace(tzinfo=BJ_TZ) + timedelta(hours=8)


def beijing_datetime2utc_datetime(dt):
    # type: (datetime) -> datetime
    """
    把北京时间的datetime转化为utc的datetime
    """
    return dt.replace(tzinfo=UTC) - timedelta(hours=8)


def to_exchange(exchange):
    # type: (Text) -> TextNone
    """转换成正确的交易市场. 如果不存在, 则返回None"""
    exchange_set = {'SHSE', 'SZSE', 'CFFEX', 'SHFE', 'DCE', 'CZCE', 'INE', 'GFEX'}
    if not exchange:
        return None
    s = str(exchange).upper().strip()
    return s if s in exchange_set else None


def load_to_list(value):
    """
    无论输入的是啥类型， 都转成list
    """
    if not value:
        return []
    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        return [value]

    if isinstance(value, six.string_types):
        return [item.strip() for item in value.split(',')]
    return value


def load_to_datetime_str(value):
    if isinstance(value, (date, datetime)):
        return value.strftime('%Y-%m-%d %H:%M:%S')

    return value


def to_datetime_bjtzinfo(value):
    if isinstance(value, datetime):
        pass
    if isinstance(value, date):
        value = datetime(value.year, value.month, value.day)
    if isinstance(value, six.string_types):
        value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    value = value.replace(tzinfo=BJ_TZ)
    return value


def load_to_second(value):
    # type: (Text) -> int
    value = value.strip().lower()

    if value.endswith('h'):
        return int(value[0:-1]) * 60 * 60

    if value.endswith('d'):
        return int(value[0:-1]) * 60 * 60 * 24

    if value.endswith('s'):
        return int(value[0:-1])

    raise ValueError('仅支持s(秒), h(小时), d(天) 结尾')


def adjust_frequency(frequency):
    # type: (Text)->Text
    """
    把frequency为1m这样的分钟, 调整为秒
    """
    frequency = frequency.strip().lower()
    return '{}s'.format(int(frequency[0:-1]) * 60) if frequency.endswith('m') else frequency


class DictLikeObject(dict):
    """
    A dict that allows for object-like property access syntax.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, item, value):
        self[item] = value

    def __str__(self):
        return super(DictLikeObject, self).__str__()

    def __repr__(self):
        return super(DictLikeObject, self).__repr__()


class ObjectLikeDict(object):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data.get(item)

    # 如果前面没有定义过的属性， 就会调用这个函数
    def __getattr__(self, item):
        return self.data.get(item)

    def __setitem__(self, item, value):
        self.data[item] = value

    def __setattr__(self, item, value):
        if item != 'data':
            self.data[item] = value
        else:
            super(ObjectLikeDict, self).__setattr__(item, value)

    def __str__(self):
        return self.data.__str__()

    def __repr__(self):
        return self.data.__repr__()


def datetime2timestamp(dt):
    """
    Converts a datetime object to UNIX timestamp in milliseconds.
    """
    if isinstance(dt, datetime):
        timestamp = time.mktime(dt.timetuple())
        return int(timestamp)
    return dt


def standard_fields(fields, letter_upper=False):
    if not fields:
        return None, None

    if letter_upper:
        fields_list = [field.strip().upper() for field in fields.split(',')]

    else:
        fields_list = [field.strip().lower() for field in fields.split(',')]

    fields_str = ','.join(fields_list)
    return fields_str, fields_list


def proto_to_dict(obj):
    # type: (object) ->  Dict
    d = dict()
    for field in dir(obj):
        first_char = field[0]
        if first_char.islower() and first_char != '_':
            d[field] = getattr(obj, field)
    return d


def get_position_key(symbol, side, covered_flag):
    # type: (Text, Text, Text) -> Text
    return "{}.{}.{}".format(symbol, side, covered_flag)


def round_float(value):
    """将浮点数类型的值四舍五入保留4位小数, 其他类型的值原样输出"""
    if isinstance(value, float):
        return round(value, 4)
    else:
        return value


_need_round_set = {
    ('Tick', 'open'),
    ('Tick', 'high'),
    ('Tick', 'low'),
    ('Tick', 'price'),
    ('Quote', 'bid_p'),
    ('Quote', 'ask_p'),
    ('Bar', 'open'),
    ('Bar', 'high'),
    ('Bar', 'low'),
    ('Bar', 'close'),
    ('Bar', 'pre_close'),
    ('Order', 'price'),
    ('ExecRpt', 'price'),
    ('Position', 'vwap_diluted'),
    ('Position', 'vwap'),
    ('Position', 'vwap_open'),
    ('Position', 'price'),
}


def need_round(message, field):
    return (message, field) in _need_round_set


def beijing_zero_oclock(d):
    # type: (datetime) -> datetime
    """返回北京时间零点"""
    return d.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=BJ_TZ)


def convert(value, t, default):
    # 将value转换为t类型, 如果转换失败, 则返回default
    try:
        return t(value)
    except:
        return default
