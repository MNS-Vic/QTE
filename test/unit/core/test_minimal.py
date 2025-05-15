#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化导入测试
用于验证导入功能正常工作，没有循环导入问题
"""
import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"已添加项目根目录到 Python 路径: {project_root}")

def test_imports():
    """测试从qte包导入模块"""
    try:
        logger.info("测试从qte导入核心模块...")
        from qte import (
            VectorEngine, 
            EventDrivenBacktester,
            BaseEngineManager,
            ReplayEngineManager,
            EngineType
        )
        logger.info("核心模块导入成功")
        
        logger.info("测试从qte.core.engine_manager导入...")
        from qte.core.engine_manager import (
            BaseEngineManager,
            ReplayEngineManager,
            EngineType,
            EngineStatus,
            EngineEvent,
            MarketDataEvent,
            SignalEvent,
            OrderEvent,
            FillEvent
        )
        logger.info("引擎管理器模块导入成功")
        
        logger.info("测试从qte.data.data_replay导入...")
        from qte.data.data_replay import (
            ReplayMode,
            ReplayStatus,
            DataReplayInterface,
            BaseDataReplayController,
            DataFrameReplayController,
            MultiSourceReplayController
        )
        logger.info("数据重放模块导入成功")
        
        return True
    except ImportError as e:
        logger.error(f"导入错误: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        logger.info("所有导入测试通过")
        sys.exit(0)
    else:
        logger.error("导入测试失败")
        sys.exit(1)