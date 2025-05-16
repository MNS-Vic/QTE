#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小测试脚本，逐步排查导入问题
"""

import os
import sys

print("1. 添加项目根目录到系统路径")
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
print(f"当前路径: {current_dir}")
print(f"项目根目录: {root_dir}")
print(f"系统路径: {sys.path}")

print("\n2. 尝试导入qte包")
try:
    import qte
    print(f"成功导入qte包，版本: {getattr(qte, '__version__', '未指定')}")
except Exception as e:
    print(f"导入qte包失败: {e}")

print("\n3. 尝试导入数据模块")
try:
    from qte import data
    print("成功导入qte.data模块")
except Exception as e:
    print(f"导入qte.data模块失败: {e}")

print("\n4. 尝试从数据模块导入数据重放相关类")
try:
    from qte.data.data_replay import ReplayMode, ReplayStatus
    print("成功导入ReplayMode和ReplayStatus")
except Exception as e:
    print(f"导入ReplayMode和ReplayStatus失败: {e}")

print("\n5. 尝试导入更多数据重放相关类")
try:
    from qte.data.data_replay import DataReplayInterface, BaseDataReplayController
    print("成功导入DataReplayInterface和BaseDataReplayController")
except Exception as e:
    print(f"导入DataReplayInterface和BaseDataReplayController失败: {e}")

print("\n6. 尝试导入DataFrameReplayController")
try:
    from qte.data.data_replay import DataFrameReplayController
    print("成功导入DataFrameReplayController")
except Exception as e:
    print(f"导入DataFrameReplayController失败: {e}")

print("\n7. 尝试导入引擎管理器相关类")
try:
    from qte.core.engine_manager import EngineType, EngineStatus
    print("成功导入EngineType和EngineStatus")
except Exception as e:
    print(f"导入EngineType和EngineStatus失败: {e}")

print("\n8. 尝试导入ReplayEngineManager类")
try:
    from qte.core.engine_manager import ReplayEngineManager
    print("成功导入ReplayEngineManager")
except Exception as e:
    print(f"导入ReplayEngineManager失败: {e}")

print("\n9. 尝试创建实例")
if 'ReplayEngineManager' in locals() and 'EngineType' in locals():
    try:
        engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
        print("成功创建ReplayEngineManager实例")
    except Exception as e:
        print(f"创建ReplayEngineManager实例失败: {e}")
else:
    print("无法创建ReplayEngineManager实例，因为相关类未成功导入")

print("\n测试完成") 