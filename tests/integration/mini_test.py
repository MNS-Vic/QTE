#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
极简测试脚本
"""
import os
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 打印调试信息
print("测试开始")
print(f"项目路径: {project_root}")

# 导入核心类
print("\n导入模块...")
from qte.core.engine_manager import ReplayEngineManager, EngineType, EngineStatus

# 创建实例
print("\n创建引擎实例...")
engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
print(f"引擎创建成功: {engine}")

# 初始化
print("\n初始化引擎...")
engine.initialize()
print(f"引擎状态: {engine.get_status()}")

# 结束
print("\n测试成功完成!")