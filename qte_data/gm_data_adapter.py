#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金数据适配器 - 兼容性文件

该文件提供与旧版本代码的兼容性，所有功能已移至gm_data_provider.py
"""

import logging
import warnings

# 导入新模块中的类
from qte_data.gm_data_provider import GmDataProvider, GmDataDownloader

# 兼容性别名
GmDataAdapter = GmDataProvider

# 显示弃用警告
warnings.warn(
    "gm_data_adapter.py已被弃用，请直接使用qte_data.gm_data_provider模块。该兼容性文件将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2
)
