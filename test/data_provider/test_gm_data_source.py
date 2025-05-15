import pandas as pd
import os
import sys
import unittest
from datetime import datetime

# 将项目根目录添加到sys.path，以便导入qte模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from qte.data.sources.gm_quant import GmQuantSource
from qte.data.data_source_manager import DataSourceManager, get_data_source_manager

class TestGmDataSource:
    """掘金数据源测试"""
    
    def __init__(self, token=None):
        """
        初始化测试类
        
        Parameters
        ----------
        token : str, optional
            掘金API的token, by default None
        """
        self.token = token or 'd6e3ba1ba79d0af43300589d35af32bdf9e5800b'  # 使用默认token或传入的token
        self.gm_source = GmQuantSource(token=self.token)
        
        # 创建数据源管理器
        self.manager = DataSourceManager()
        self.manager.register_source('gm', self.gm_source, make_default=True)
        self.manager.register_source('local', LocalCsvSource())
        
    def test_connect(self):
        """测试连接掘金API"""
        print("测试连接掘金API...")
        
        result = self.gm_source.connect()
        if result:
            print("✓ 成功连接到掘金API")
        else:
            print("✗ 连接掘金API失败")
        
        return result
            
    def test_get_symbols(self):
        """测试获取标的列表"""
        print("\n测试获取标的列表...")
        
        # 尝试获取上海交易所的标的
        symbols = self.gm_source.get_symbols(market='SHSE')
        
        if symbols and len(symbols) > 0:
            print(f"✓ 成功获取到 {len(symbols)} 个上海交易所标的")
            print(f"前5个标的: {symbols[:5]}")
        else:
            print("✗ 获取标的列表失败")
            
        return len(symbols) > 0
    
    def test_get_bars(self):
        """测试获取K线数据"""
        print("\n测试获取K线数据...")
        
        # 测试获取浦发银行的日线数据
        symbol = 'SHSE.600000'
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        
        bars = self.gm_source.get_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency='1d'
        )
        
        if bars is not None and not bars.empty:
            print(f"✓ 成功获取到 {len(bars)} 条K线数据")
            print("数据预览:")
            print(bars.head())
        else:
            print(f"✗ 获取K线数据失败")
            
        return bars is not None and not bars.empty
    
    def test_get_fundamentals(self):
        """测试获取基本面数据"""
        print("\n测试获取基本面数据...")
        
        # 测试获取浦发银行的财务数据
        symbols = ['SHSE.600000']
        table = 'trading_derivative_indicator'
        start_date = '2023-01-01'
        end_date = '2023-06-30'
        
        fundamentals = self.gm_source.get_fundamentals(
            table=table,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        if fundamentals is not None and not fundamentals.empty:
            print(f"✓ 成功获取到 {len(fundamentals)} 条基本面数据")
            print("数据预览:")
            print(fundamentals.head())
        else:
            print(f"✗ 获取基本面数据失败")
            
        return fundamentals is not None and not fundamentals.empty
    
    def test_manager(self):
        """测试数据源管理器"""
        print("\n测试数据源管理器...")
        
        # 测试获取标的列表
        symbols = self.manager.get_symbols(market='SHSE')
        
        if symbols and len(symbols) > 0:
            print(f"✓ 成功通过管理器获取到 {len(symbols)} 个上海交易所标的")
        else:
            print("✗ 通过管理器获取标的列表失败")
            
        # 测试获取K线数据
        symbol = 'SHSE.600000'
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        
        bars = self.manager.get_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency='1d'
        )
        
        if bars is not None and not bars.empty:
            print(f"✓ 成功通过管理器获取到 {len(bars)} 条K线数据")
        else:
            print(f"✗ 通过管理器获取K线数据失败")
            
        return len(symbols) > 0 and bars is not None and not bars.empty
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("开始测试掘金数据源...")
        print("=" * 50)
        
        tests = [
            self.test_connect,
            self.test_get_symbols,
            self.test_get_bars,
            self.test_get_fundamentals,
            self.test_manager
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
                
        print("\n" + "=" * 50)
        print(f"测试完成: {success_count}/{len(tests)} 通过")
        print("=" * 50)
        
        return success_count == len(tests)

def main():
    """主函数"""
    # 从环境变量或命令行参数获取token
    token = os.environ.get('GM_TOKEN', 'd6e3ba1ba79d0af43300589d35af32bdf9e5800b')
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
        
    tester = TestGmDataSource(token=token)
    tester.run_all_tests()

if __name__ == "__main__":
    # 为了导入LocalCsvSource
    from qte.data.sources.local_csv import LocalCsvSource
    main() 