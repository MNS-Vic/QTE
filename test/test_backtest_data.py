import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# 获取当前脚本文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已添加项目路径: {project_root}")

def generate_test_data():
    """
    生成用于回测的测试数据文件。
    创建两个股票符号的价格数据：TEST_A 和 TEST_B
    """
    # 确保目录存在
    data_dir = os.path.join(project_root, "myquant_data")
    os.makedirs(data_dir, exist_ok=True)
    
    # 生成日期序列 - 使用30天的数据
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(30)]
    
    # 生成TEST_A的数据 - 上升趋势
    test_a_data = {
        'timestamp': dates,
        'open': [100 + i + np.random.normal(0, 0.5) for i in range(30)],
        'high': [100 + i + 2 + np.random.normal(0, 0.5) for i in range(30)],
        'low': [100 + i - 2 + np.random.normal(0, 0.5) for i in range(30)],
        'close': [100 + i + np.random.normal(0, 0.5) for i in range(30)],
        'volume': [int(10000 + np.random.normal(0, 1000)) for _ in range(30)]
    }
    
    # 生成TEST_B的数据 - 下降趋势后上升
    test_b_data = {
        'timestamp': dates,
        'open': [150 - i/2 + np.random.normal(0, 0.5) if i < 15 else 142.5 + (i-15)/2 + np.random.normal(0, 0.5) for i in range(30)],
        'high': [150 - i/2 + 2 + np.random.normal(0, 0.5) if i < 15 else 142.5 + (i-15)/2 + 2 + np.random.normal(0, 0.5) for i in range(30)],
        'low': [150 - i/2 - 2 + np.random.normal(0, 0.5) if i < 15 else 142.5 + (i-15)/2 - 2 + np.random.normal(0, 0.5) for i in range(30)],
        'close': [150 - i/2 + np.random.normal(0, 0.5) if i < 15 else 142.5 + (i-15)/2 + np.random.normal(0, 0.5) for i in range(30)],
        'volume': [int(15000 + np.random.normal(0, 1500)) for _ in range(30)]
    }
    
    # 创建DataFrame
    test_a_df = pd.DataFrame(test_a_data)
    test_b_df = pd.DataFrame(test_b_data)
    
    # 保存到CSV文件
    test_a_path = os.path.join(data_dir, "TEST_SYM_A.csv")
    test_b_path = os.path.join(data_dir, "TEST_SYM_B.csv")
    
    test_a_df.to_csv(test_a_path, index=False)
    test_b_df.to_csv(test_b_path, index=False)
    
    print(f"测试数据生成完成：")
    print(f"  - {test_a_path} (上升趋势)")
    print(f"  - {test_b_path} (下降后上升趋势)")
    print(f"  - 每个文件包含30天的OHLCV数据")
    
    return test_a_path, test_b_path

if __name__ == "__main__":
    generate_test_data() 