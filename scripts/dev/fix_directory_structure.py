#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修正项目目录结构脚本

按照项目规范修正不符合标准的目录结构:
1. 将qte_*目录的内容合并到qte/下的对应模块
2. 将test/目录下的测试文件移动到tests/下的对应子目录
3. 将test_data目录的内容移动到data/下
"""

import os
import shutil
import sys
from pathlib import Path


def create_directory(path, description=None):
    """创建目录，如果不存在"""
    path = Path(path)
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"√ 创建目录 {path}")
        except Exception as e:
            print(f"× 创建目录 {path} 失败: {e}")
    else:
        print(f"- 目录 {path} 已存在")


def migrate_qte_modules():
    """将qte_*目录的内容合并到qte/下的对应模块"""
    # 映射表，旧目录名到新目录名
    module_mapping = {
        "qte_core": "qte/core",
        "qte_data": "qte/data",
        "qte_execution": "qte/execution",
        "qte_portfolio_risk": "qte/portfolio",
        "qte_strategy": "qte/strategy",
        "qte_analysis_reporting": "qte/analysis"
    }
    
    # 保存已处理的文件，防止重复
    processed_files = set()
    
    # 遍历映射表
    for old_dir, new_dir in module_mapping.items():
        if os.path.exists(old_dir):
            # 确保目标目录存在
            create_directory(new_dir)
            
            # 复制文件
            for root, dirs, files in os.walk(old_dir):
                for file in files:
                    # 忽略__pycache__目录下的文件
                    if "__pycache__" in root:
                        continue
                    
                    # 计算源文件路径
                    old_file = os.path.join(root, file)
                    
                    # 计算相对路径
                    rel_path = os.path.relpath(old_file, old_dir)
                    
                    # 目标文件路径
                    new_file = os.path.join(new_dir, rel_path)
                    
                    # 检查是否已处理过
                    if new_file in processed_files:
                        continue
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(new_file), exist_ok=True)
                    
                    # 检查目标文件是否已存在
                    if os.path.exists(new_file):
                        print(f"! 文件已存在: {new_file}")
                        continue
                    
                    # 复制文件
                    try:
                        shutil.copy2(old_file, new_file)
                        print(f"√ 复制文件 {old_file} -> {new_file}")
                        processed_files.add(new_file)
                    except Exception as e:
                        print(f"× 复制文件 {old_file} 失败: {e}")
            
            print(f"✓ 模块 {old_dir} 迁移完成")
        else:
            print(f"- 目录 {old_dir} 不存在，跳过")


def migrate_tests():
    """将test/目录下的测试文件移动到tests/下的对应子目录"""
    old_test_dir = "test"
    new_test_dir = "tests"
    
    if not os.path.exists(old_test_dir):
        print(f"- 目录 {old_test_dir} 不存在，跳过")
        return
    
    # 确保目标目录存在
    create_directory(new_test_dir)
    
    # 测试文件分类规则
    def classify_test_file(file_name):
        """根据文件名分类测试"""
        if "unit" in file_name.lower():
            return "unit"
        elif "integration" in file_name.lower() or "component" in file_name.lower():
            return "integration"
        elif "performance" in file_name.lower():
            return "performance"
        
        # 根据文件名前缀进一步分类
        if file_name.startswith("test_"):
            # 根据测试内容分类
            if "core" in file_name or "event" in file_name or "backtest" in file_name:
                return "unit/core"
            elif "data" in file_name or "provider" in file_name:
                return "unit/data"
            elif "ml" in file_name or "model" in file_name or "feature" in file_name:
                return "unit/ml"
            else:
                return "unit"
        else:
            # 非标准测试文件，移到integration
            return "integration"
    
    # 复制测试文件
    for root, dirs, files in os.walk(old_test_dir):
        for file in files:
            # 忽略__pycache__和数据目录下的文件
            if "__pycache__" in root or "data" in root.split(os.path.sep):
                continue
            
            # 检查是否是Python文件
            if not file.endswith(".py"):
                continue
            
            # 计算源文件路径
            old_file = os.path.join(root, file)
            
            # 分类文件
            category = classify_test_file(file)
            
            # 目标文件路径
            new_file = os.path.join(new_test_dir, category, file)
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(new_file), exist_ok=True)
            
            # 检查目标文件是否已存在
            if os.path.exists(new_file):
                print(f"! 文件已存在: {new_file}")
                continue
            
            # 复制文件
            try:
                shutil.copy2(old_file, new_file)
                print(f"√ 复制测试文件 {old_file} -> {new_file}")
            except Exception as e:
                print(f"× 复制测试文件 {old_file} 失败: {e}")
    
    print(f"✓ 测试目录 {old_test_dir} 迁移完成")


def migrate_test_data():
    """将test_data目录和test/data的内容移动到data/下"""
    old_dirs = ["test_data", "test/data"]
    target_dir = "data"
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    for old_dir in old_dirs:
        if os.path.exists(old_dir):
            # 检查旧目录
            for root, dirs, files in os.walk(old_dir):
                for file in files:
                    old_file = os.path.join(root, file)
                    # 计算相对路径
                    rel_path = os.path.relpath(old_file, old_dir)
                    
                    # 判断数据类型
                    if "backtest" in rel_path.lower():
                        sub_dir = "backtest"
                    elif "research" in rel_path.lower():
                        sub_dir = "research"
                    else:
                        sub_dir = "sample"
                    
                    # 目标文件路径
                    new_file = os.path.join(target_dir, sub_dir, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(new_file), exist_ok=True)
                    
                    # 检查目标文件是否已存在
                    if os.path.exists(new_file):
                        # print(f"! 数据文件已存在: {new_file}")
                        continue
                    
                    # 复制文件
                    try:
                        shutil.copy2(old_file, new_file)
                        print(f"√ 复制数据文件 {old_file} -> {new_file}")
                    except Exception as e:
                        print(f"× 复制数据文件 {old_file} 失败: {e}")
            
            print(f"✓ 数据目录 {old_dir} 迁移完成")
        else:
            print(f"- 目录 {old_dir} 不存在，跳过")


def migrate_strategies():
    """将strategies目录整理到规范位置"""
    old_dir = "strategies"
    if not os.path.exists(old_dir):
        print(f"- 目录 {old_dir} 不存在，跳过")
        return
    
    # 映射表，根据策略类型决定目标位置
    target_dirs = {
        "ml": "examples/ml_strategies",
        "traditional": "examples/simple_strategies"
    }
    
    # 复制策略文件
    for subdir in os.listdir(old_dir):
        old_subdir = os.path.join(old_dir, subdir)
        if os.path.isdir(old_subdir):
            # 决定目标目录
            if subdir.lower() in target_dirs:
                new_dir = target_dirs[subdir.lower()]
            else:
                new_dir = "examples/simple_strategies"
            
            # 确保目标目录存在
            create_directory(new_dir)
            
            # 复制文件
            for root, dirs, files in os.walk(old_subdir):
                for file in files:
                    # 忽略__pycache__目录下的文件
                    if "__pycache__" in root:
                        continue
                    
                    # 计算源文件路径
                    old_file = os.path.join(root, file)
                    
                    # 计算相对路径
                    rel_path = os.path.relpath(old_file, old_subdir)
                    
                    # 目标文件路径
                    new_file = os.path.join(new_dir, rel_path)
                    
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(new_file), exist_ok=True)
                    
                    # 检查目标文件是否已存在
                    if os.path.exists(new_file):
                        print(f"! 策略文件已存在: {new_file}")
                        continue
                    
                    # 复制文件
                    try:
                        shutil.copy2(old_file, new_file)
                        print(f"√ 复制策略文件 {old_file} -> {new_file}")
                    except Exception as e:
                        print(f"× 复制策略文件 {old_file} 失败: {e}")
            
            print(f"✓ 策略目录 {old_subdir} 迁移完成")
    
    print(f"✓ 策略目录整理完成")


def create_missing_init_files():
    """为所有Python包目录创建缺失的__init__.py文件"""
    # 需要检查的目录
    dirs_to_check = [
        "qte",
        "qte/core",
        "qte/data",
        "qte/data/sources",
        "qte/ml",
        "qte/portfolio",
        "qte/execution",
        "qte/analysis",
        "qte/utils",
        "tests/unit/core",
        "tests/unit/data",
        "tests/unit/ml",
        "tests/integration",
        "tests/performance",
    ]
    
    # 创建__init__.py文件
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            init_file = os.path.join(dir_path, "__init__.py")
            if not os.path.exists(init_file):
                try:
                    with open(init_file, "w") as f:
                        f.write('"""QTE项目模块"""\n')
                    print(f"√ 创建__init__.py文件: {init_file}")
                except Exception as e:
                    print(f"× 创建__init__.py文件失败: {init_file} - {e}")
            else:
                print(f"- __init__.py文件已存在: {init_file}")
        else:
            print(f"- 目录不存在，跳过创建__init__.py: {dir_path}")


def main():
    """主函数"""
    print("\n===== 开始修正项目目录结构 =====\n")
    
    # 1. 将qte_*目录的内容合并到qte/下的对应模块
    print("\n----- 修正模块目录结构 -----\n")
    migrate_qte_modules()
    
    # 2. 将test/目录下的测试文件移动到tests/下的对应子目录
    print("\n----- 整理测试文件 -----\n")
    migrate_tests()
    
    # 3. 将测试数据移动到规范位置
    print("\n----- 整理测试数据 -----\n")
    migrate_test_data()
    
    # 4. 整理策略文件
    print("\n----- 整理策略文件 -----\n")
    migrate_strategies()
    
    # 5. 创建缺失的__init__.py文件
    print("\n----- 创建缺失的__init__.py文件 -----\n")
    create_missing_init_files()
    
    print("\n===== 项目目录结构修正完成 =====\n")
    print("注意：此过程只复制文件，没有删除原文件。建议备份后手动删除不再需要的目录。")
    print("如果有内容冲突，请手动解决冲突。")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 