#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化验证脚本

验证基础的导入和创建功能
"""
import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"已添加项目根目录到 Python 路径: {project_root}")

def main():
    """主函数"""
    logger.info("开始最小化验证...")
    
    try:
        # 1. 从主包导入
        logger.info("1. 从qte包导入...")
        from qte import (
            VectorEngine, 
            EventDrivenBacktester,
            BaseEngineManager,
            ReplayEngineManager,
            EngineType
        )
        logger.info("  导入主包成功")
        
        # 2. 从子模块导入
        logger.info("2. 从子模块导入...")
        from qte.core.engine_manager import (
            BaseEngineManager,
            ReplayEngineManager,
            EngineStatus
        )
        from qte.data.data_replay import (
            ReplayMode,
            DataFrameReplayController
        )
        logger.info("  导入子模块成功")
        
        # 3. 创建实例
        logger.info("3. 创建实例...")
        
        # 创建引擎管理器
        base_manager = BaseEngineManager()
        logger.info(f"  创建 BaseEngineManager 成功: {base_manager}")
        
        replay_manager = ReplayEngineManager()
        logger.info(f"  创建 ReplayEngineManager 成功: {replay_manager}")
        
        # 初始化
        base_manager.initialize()
        replay_manager.initialize()
        logger.info("  初始化管理器成功")
        
        # 验证方法
        base_status = base_manager.get_status()
        replay_status = replay_manager.get_status()
        logger.info(f"  BaseEngineManager 状态: {base_status}")
        logger.info(f"  ReplayEngineManager 状态: {replay_status}")
        
        logger.info("所有测试通过")
        return 0
        
    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())