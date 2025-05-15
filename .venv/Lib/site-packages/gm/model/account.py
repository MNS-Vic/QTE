# coding=utf-8
from __future__ import unicode_literals, print_function, absolute_import

import six
from typing import Text, Dict, Any, Tuple, Union
from gm.model import DictLikeConnectionStatus

from gm.pb.account_pb2 import Cash


class Account(object):
    """
    账户
    """
    def __init__(self, id, name, cash, positions, conn_status):
        self.id = id  # type: Text
        self.name = name  # type: Text
        self.cash = cash  # type: Union[Dict[Text, Any], Cash]
        # 这里的 inside_positions 是个字典, 用 symbol.side 作为key, value为Position的属性展开的字典
        self.inside_positions = positions  # type: Dict[Tuple[Text, int, int], Dict[Text, Any]]
        self.status = conn_status  # type: Union[DictLikeConnectionStatus, None]

    def match(self, name):
        return self.name == name or self.id == name

    def positions(self, symbol='', side=None, covered_flag=None):
        # covered_flag: 0: 普通仓, 1: 备兑仓; 默认返回所有
        if not symbol and side is None and covered_flag is None:
            return list(six.itervalues(self.inside_positions))
        return list(
            v for k, v in six.iteritems(self.inside_positions)
            if (not symbol or k[0] == symbol) and
            (side is None or k[1] == side) and
            (covered_flag is None or k[2] == covered_flag)
        )

    def position(self, symbol, side, covered_flag=0):
        return self.inside_positions.get((symbol, side, covered_flag))
