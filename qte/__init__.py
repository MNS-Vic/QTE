#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QTE - 量化回测引擎

一个高性能的量化回测框架，支持向量化和事件驱动两种回测方式，以及机器学习集成。
"""

from qte.core import (
    VectorEngine, EventDrivenBacktester, 
    BaseEngineManager, ReplayEngineManager, EngineType
)
from qte.ml import FeatureGenerator, ModelManager

__version__ = "0.1.0"

__all__ = [
    'VectorEngine', 
    'EventDrivenBacktester',
    'BaseEngineManager',
    'ReplayEngineManager',
    'EngineType',
    'FeatureGenerator',
    'ModelManager'
]