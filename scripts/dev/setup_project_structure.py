#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
规范项目结构的脚本

根据docs/development/code_standards.md中定义的项目结构规范，
创建和整理项目目录结构。
"""

import os
import shutil
import sys
from pathlib import Path


def create_directory(path, description=None):
    """
    创建目录，如果不存在
    
    Parameters
    ----------
    path : str
        目录路径
    description : str, optional
        目录描述，用于打印
    """
    path = Path(path)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"√ 创建目录 {path}")
        except Exception as e:
            print(f"× 创建目录 {path} 失败: {e}")
    else:
        print(f"- 目录 {path} 已存在")


def create_project_structure():
    """创建项目规范的目录结构"""
    # 主要目录
    directories = [
        # 源代码目录
        ("qte/core", "核心引擎模块"),
        ("qte/data/sources", "数据源实现"),
        ("qte/ml", "机器学习模块"),
        ("qte/portfolio", "投资组合管理"),
        ("qte/execution", "执行模块"),
        ("qte/analysis", "回测分析"),
        ("qte/utils", "工具函数"),
        
        # 测试目录
        ("tests/unit/core", "核心模块单元测试"),
        ("tests/unit/data", "数据模块单元测试"),
        ("tests/unit/ml", "机器学习模块单元测试"),
        ("tests/integration", "集成测试"),
        ("tests/performance", "性能测试"),
        
        # 示例目录
        ("examples/simple_strategies", "简单策略示例"),
        ("examples/ml_strategies", "机器学习策略示例"),
        ("examples/tutorials", "教程示例"),
        
        # 文档目录
        ("docs/api", "API文档"),
        ("docs/tutorials", "教程文档"),
        ("docs/architecture", "架构文档"),
        ("docs/development", "开发规范"),
        
        # 数据目录
        ("data/sample", "样本数据"),
        ("data/backtest", "回测数据"),
        ("data/research", "研究数据"),
        
        # 脚本目录
        ("scripts/dev", "开发脚本"),
        ("scripts/deploy", "部署脚本"),
        
        # 结果目录
        ("results/figures", "图表和可视化"),
        ("results/reports", "报告文件"),
        
        # GitHub配置
        (".github/workflows", "CI/CD工作流"),
    ]
    
    for directory, description in directories:
        create_directory(directory, description)


def migrate_data():
    """从旧的测试数据目录迁移数据到规范的数据目录"""
    old_dirs = ["test_data", "test/data"]
    target_dir = "data"
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    for old_dir in old_dirs:
        if os.path.exists(old_dir):
            # 检查旧目录
            for subdir in os.listdir(old_dir):
                old_path = os.path.join(old_dir, subdir)
                if os.path.isdir(old_path):
                    # 根据子目录内容决定迁移到哪个新目录
                    if "backtest" in subdir.lower():
                        new_path = os.path.join(target_dir, "backtest")
                    else:
                        new_path = os.path.join(target_dir, "sample")
                    
                    # 确保目标目录存在
                    os.makedirs(new_path, exist_ok=True)
                    
                    # 复制文件
                    for root, dirs, files in os.walk(old_path):
                        for file in files:
                            old_file = os.path.join(root, file)
                            # 计算相对路径
                            rel_path = os.path.relpath(old_file, old_path)
                            # 目标文件路径
                            new_file = os.path.join(new_path, rel_path)
                            # 确保目标目录存在
                            os.makedirs(os.path.dirname(new_file), exist_ok=True)
                            
                            # 复制文件
                            try:
                                shutil.copy2(old_file, new_file)
                                print(f"√ 复制文件 {old_file} -> {new_file}")
                            except Exception as e:
                                print(f"× 复制文件 {old_file} 失败: {e}")
            
            print(f"✓ 从 {old_dir} 迁移数据完成")
        else:
            print(f"- 目录 {old_dir} 不存在，跳过")


def migrate_images():
    """迁移根目录的图片到results/figures目录"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
    target_dir = "results/figures"
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    # 遍历根目录
    for file in os.listdir('.'):
        file_path = os.path.join('.', file)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file)
            if ext.lower() in image_extensions:
                target_path = os.path.join(target_dir, file)
                try:
                    shutil.copy2(file_path, target_path)
                    print(f"√ 复制图片 {file_path} -> {target_path}")
                except Exception as e:
                    print(f"× 复制图片 {file_path} 失败: {e}")
                
    print(f"✓ 迁移图片完成")


def move_example_scripts():
    """移动根目录的示例脚本到examples目录"""
    example_scripts = [
        "simple_ma_backtest.py", 
        "demo_strategyA_backtest.py"
    ]
    target_dir = "examples/simple_strategies"
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    for script in example_scripts:
        if os.path.exists(script):
            target_path = os.path.join(target_dir, script)
            try:
                shutil.copy2(script, target_path)
                print(f"√ 复制示例脚本 {script} -> {target_path}")
            except Exception as e:
                print(f"× 复制示例脚本 {script} 失败: {e}")
    
    print(f"✓ 移动示例脚本完成")


def main():
    """主函数"""
    print("\n===== 开始规范项目结构 =====\n")
    
    # 1. 创建规范的目录结构
    print("\n----- 创建目录结构 -----\n")
    create_project_structure()
    
    # 2. 迁移测试数据
    print("\n----- 迁移测试数据 -----\n")
    migrate_data()
    
    # 3. 迁移图片
    print("\n----- 迁移图片 -----\n")
    migrate_images()
    
    # 4. 移动示例脚本
    print("\n----- 移动示例脚本 -----\n")
    move_example_scripts()
    
    print("\n===== 项目结构规范完成 =====\n")
    print("注意：此过程只复制文件，没有删除原文件。可手动删除不再需要的文件。")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 