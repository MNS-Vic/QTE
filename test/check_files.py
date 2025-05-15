#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查关键文件是否存在
"""

import os
import sys

def check_file(filepath):
    """检查文件是否存在并打印其前10行内容"""
    print(f"\n检查文件: {filepath}")
    if os.path.exists(filepath):
        print(f"文件存在: {os.path.abspath(filepath)}")
        print("文件前10行内容:")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i < 10:
                        print(f"  {i+1}: {line.rstrip()}")
                    else:
                        break
        except Exception as e:
            print(f"读取文件时出错: {e}")
    else:
        print(f"文件不存在: {os.path.abspath(filepath)}")

def main():
    """主程序"""
    print("检查项目关键文件...")
    
    # 检查数据重放模块
    check_file("qte/data/data_replay.py")
    
    # 检查引擎管理器模块
    check_file("qte/core/engine_manager.py")
    
    # 检查初始化文件
    check_file("qte/data/__init__.py")
    check_file("qte/core/__init__.py")
    
    # 检查测试文件
    check_file("test/unit/core/test_replay_engine_integration.py")
    
    print("\n检查完成")

if __name__ == "__main__":
    main() 