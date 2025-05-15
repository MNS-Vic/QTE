from typing import Dict, List
from datetime import datetime, date as Date, timedelta

from gm.csdk.c_sdk import gmi_get_ext_errormsg
from gm.utils import utc_datetime2beijing_datetime


def invalid_status(status: int) -> bool:
    if status == 0:
        return False
    gmi_get_ext_errormsg()
    return True


def unfold_field(dictory, field):
    # type: (Dict, str) -> None
    """展开字典内嵌套的字段"""
    if field in dictory:
        dictory.update(dictory.pop(field))


def rename_field(dictory, after_field, before_field):
    # type: (Dict, str, str) -> None
    """重命名字典内的字段"""
    if before_field in dictory:
        dictory[after_field] = dictory.pop(before_field)


def filter_field(dictory, fields):
    # type: (Dict, List[str]|str) -> Dict
    """过滤字典内的字段, 只保留 fields 内的字段"""
    if not fields:
        return dictory
    if isinstance(fields, str):
        fields = fields.split(',')
    fields = [field.strip() for field in fields]
    res = {}
    for field in fields:
        if field in dictory:
            res[field] = dictory[field]
    return res


def param_convert_iter_to_str(values):
    # type: (List|str) -> str|None
    """参数转换"""
    if not values:
        return None
    if isinstance(values, str):
        values = values.split(',')
    values = [str(value).strip() for value in values]
    return ','.join(values)


def param_convert_iter_to_list(values):
    # type: (List[str]|str) -> str|None
    """参数转换"""
    if not values:
        return None
    if isinstance(values, str):
        values = values.split(',')
    values = [value.strip() for value in values]
    return values


def param_convert_datetime(date):
    # type: (str|datetime) -> str|None
    """参数转换, 日期类型"""
    if not date:
        return None
    if isinstance(date, str):
        return date
    if isinstance(date, datetime):
        return date.strftime("%Y-%m-%d")
    raise ValueError("错误日期格式")


def param_convert_date(date):
    # type: (str|datetime|Date) -> str|None
    """参数转换, 日期类型"""
    if not date:
        return None
    if isinstance(date, str):
        return date
    if isinstance(date, (datetime, Date)):
        return date.strftime("%Y-%m-%d")
    raise ValueError("错误日期格式")


def param_convert_date_with_time(date):
    # type: (str|datetime|Date) -> str|None
    """参数转换, 日期类型"""
    if not date:
        return None
    if isinstance(date, str):
        return date
    if isinstance(date, (datetime, Date)):
        return date.strftime("%Y-%m-%d %H:%M:%S")
    raise ValueError("错误日期格式")


def _timestamp_to_str(value, is_utc_time=True, datetime_to_str=False):
    # 这个方法是对value.ToDatetime()的改造， 防止1969年报错
    _NANOS_PER_SECOND = 1000000000
    deltasec = value.seconds + value.nanos / float(_NANOS_PER_SECOND)
    result = (datetime(1970, 1, 1) + timedelta(seconds=deltasec))

    if is_utc_time:
        result = utc_datetime2beijing_datetime(result)
    if datetime_to_str:
        result = result.strftime("%Y-%m-%d")
    return result
