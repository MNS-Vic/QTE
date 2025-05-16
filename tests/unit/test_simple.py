"""
简单测试文件

用于测试导入和基本功能
"""

import os
import sys

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """主测试函数"""
    print("测试导入...")
    
    # 测试导入数据重放模块
    from qte.data.data_replay import (
        ReplayMode, ReplayStatus, 
        DataFrameReplayController
    )
    print("成功导入数据重放模块")
    
    # 测试导入引擎管理器模块
    from qte.core.engine_manager import (
        EngineType, EngineStatus,
        ReplayEngineManager
    )
    print("成功导入引擎管理器模块")
    
    # 测试创建实例
    print("\n测试创建实例...")
    
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01 09:30:00', periods=5, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'price': [100, 101, 99, 102, 103],
        'volume': [1000, 1200, 900, 1100, 1300],
        'symbol': ['000001.SZ'] * 5
    })
    
    # 创建数据重放控制器
    controller = DataFrameReplayController(
        dataframe=df,
        timestamp_column='timestamp',
        mode=ReplayMode.BACKTEST
    )
    print("成功创建数据重放控制器")
    
    # 创建引擎管理器
    engine = ReplayEngineManager(EngineType.EVENT_DRIVEN)
    engine.initialize()
    print("成功初始化引擎管理器")
    
    # 测试添加控制器
    result = engine.add_replay_controller(
        name="test_data",
        controller=controller,
        symbol="000001.SZ"
    )
    print(f"添加重放控制器: {'成功' if result else '失败'}")
    
    print("\n所有测试完成!")
    
if __name__ == "__main__":
    main() 