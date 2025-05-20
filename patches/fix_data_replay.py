#!/usr/bin/env python
"""
修复data_replay.py中的问题，确保测试不会卡住

此脚本:
1. 修改DataFrameReplayController.step_sync方法，确保其不会调用reset()
2. 修改DataFrameReplayController.process_all_sync方法，确保其不会调用reset()
3. 移除所有诊断print语句
"""

import sys
import os
import re

def fix_data_replay():
    """应用修复到data_replay.py文件"""
    file_path = "qte/data/data_replay.py"
    
    # 创建备份
    backup_path = file_path + ".pre_fix"
    os.system(f"cp {file_path} {backup_path}")
    print(f"已创建备份: {backup_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 移除print调试语句
    content = re.sub(r'print\(["\']DEBUG:.*?"\).*?\n', '', content)
    content = re.sub(r'print\(f"DEBUG:.*?"\).*?\n', '', content)
    
    # 修复1: 找到第一个step_sync实现
    step_sync_match = re.search(r'def step_sync\(self\):\s+"""[\s\S]+?"""', content)
    if step_sync_match:
        first_step_sync_doc = step_sync_match.group(0)
        if "由子类实现具体逻辑" not in first_step_sync_doc:
            # 这是BaseDataReplayController类的step_sync方法，修改其实现
            base_step_sync = first_step_sync_doc + '\n        logger.debug("基类step_sync被调用，返回None")\n        return None'
            content = content.replace(step_sync_match.group(0), base_step_sync)
            print("已修复BaseDataReplayController.step_sync方法")
    
    # 修复2: 找到DataFrameReplayController类的step_sync方法
    df_step_sync_pattern = r'(class DataFrameReplayController[\s\S]+?def step_sync\(self\):[\s\S]+?if self\._status == ReplayStatus.COMPLETED or self\._status == ReplayStatus.FINISHED:[\s\S]+?)(?:self\.reset\(\)|# 简单地重置基本状态变量)'
    df_step_sync_match = re.search(df_step_sync_pattern, content)
    
    if df_step_sync_match:
        df_step_sync_prefix = df_step_sync_match.group(1)
        # 替换为直接重置状态的代码
        df_step_sync_fixed = df_step_sync_prefix + """            # 直接重置状态变量，避免调用reset()可能引起的循环
            self._current_position = 0
            self.current_index = 0
            self._status = ReplayStatus.INITIALIZED"""
        content = content.replace(df_step_sync_match.group(0), df_step_sync_fixed)
        print("已修复DataFrameReplayController.step_sync方法")
    
    # 修复3: 找到DataFrameReplayController类的process_all_sync方法
    process_all_pattern = r'(def process_all_sync\(self\):[\s\S]+?results = \[\][\s\S]+?)# 重置状态确保从头开始[\s\S]+?self\.reset\(\)'
    process_all_match = re.search(process_all_pattern, content)
    
    if process_all_match:
        process_all_prefix = process_all_match.group(1)
        # 替换为直接重置状态的代码
        process_all_fixed = process_all_prefix + """        # 直接重置状态而不调用self.reset()
        self._current_position = 0
        self.current_index = 0
        self._status = ReplayStatus.INITIALIZED"""
        content = content.replace(process_all_match.group(0), process_all_fixed)
        print("已修复DataFrameReplayController.process_all_sync方法")
    
    # 保存修改后的文件
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("修复完成。请运行测试验证: python -m pytest tests/unit/data/test_data_replay_sync.py::TestSyncAPI::test_dataframe_step_sync -vv")

if __name__ == "__main__":
    fix_data_replay()