#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化测试脚本
"""

print("开始测试...")

try:
    from qte.data.data_replay import ReplayMode, DataFrameReplayController
    print("导入数据重放模块成功")
except Exception as e:
    print(f"导入数据重放模块失败: {e}")

try:
    from qte.core.engine_manager import EngineType, ReplayEngineManager
    print("导入引擎管理器模块成功")
except Exception as e:
    print(f"导入引擎管理器模块失败: {e}")

try:
    engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    print("创建引擎管理器实例成功")
except Exception as e:
    print(f"创建引擎管理器实例失败: {e}")

print("测试完成") 