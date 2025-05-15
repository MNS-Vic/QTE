import pandas as pd
import os
from typing import Dict, List, Optional, Any

class LocalCsvSource:
    """从本地CSV文件加载数据的数据源"""
    
    def __init__(self, base_path: str = "examples/test_data/"):
        """
        初始化本地CSV数据源
        
        Parameters
        ----------
        base_path : str, optional
            CSV文件的基础路径, by default "examples/test_data/"
        """
        self.base_path = base_path
        # 确保基路径相对于项目根目录是正确的
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.resolved_base_path = os.path.join(self.project_root, self.base_path)
        
    def connect(self, **kwargs) -> bool:
        """
        连接数据源（对于本地CSV，只需验证路径存在）
        
        Returns
        -------
        bool
            连接是否成功
        """
        return os.path.exists(self.resolved_base_path)
    
    def get_symbols(self, market: Optional[str] = None) -> List[str]:
        """
        获取可用的标的列表
        
        Parameters
        ----------
        market : Optional[str], optional
            市场代码, by default None
            
        Returns
        -------
        List[str]
            标的列表
        """
        # 对于本地CSV，这个函数可能不太实用，因为我们需要解析CSV文件内容
        # 这里简化实现，返回CSV文件名列表（假设每个CSV对应一个标的）
        symbols = []
        for file in os.listdir(self.resolved_base_path):
            if file.endswith('.csv'):
                symbols.append(file.replace('.csv', ''))
        return symbols
    
    def get_bars(self, symbol: str, start_date: Optional[str] = None, 
                end_date: Optional[str] = None, frequency: str = '1d', 
                file_name: Optional[str] = None, date_col: str = 'datetime', 
                symbol_col_in_file: Optional[str] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Parameters
        ----------
        symbol : str
            标的代码
        start_date : Optional[str], optional
            开始日期, by default None
        end_date : Optional[str], optional
            结束日期, by default None
        frequency : str, optional
            数据频率, by default '1d'
        file_name : Optional[str], optional
            CSV文件名, by default None
        date_col : str, optional
            日期列名, by default 'datetime'
        symbol_col_in_file : Optional[str], optional
            标的代码列名, by default None
        
        Returns
        -------
        Optional[pd.DataFrame]
            K线数据DataFrame
        """
        if file_name is None:
            file_path = os.path.join(self.resolved_base_path, "real_stock_data.csv")
        else:
            file_path = os.path.join(self.resolved_base_path, file_name.format(symbol=symbol))

        print(f"[LocalCsvSource] 尝试加载数据从: {file_path}")
        if not os.path.exists(file_path):
            print(f"[LocalCsvSource] 错误: 文件不存在于 {file_path}")
            return None

        try:
            data = pd.read_csv(file_path)
            
            # 列名重命名
            column_rename_map = kwargs.get('column_rename_map', {})
            if date_col not in column_rename_map and date_col != 'datetime':
                 column_rename_map[date_col] = 'datetime'
            
            data.rename(columns=column_rename_map, inplace=True)

            if 'datetime' not in data.columns:
                print(f"[LocalCsvSource] 错误: 日期时间列 ('datetime' 重命名后, 原始为 '{date_col}') 未在 {file_path} 中找到.")
                return None
            
            data['datetime'] = pd.to_datetime(data['datetime'])
            data.set_index('datetime', inplace=True)

            # 如果提供了 symbol_col_in_file，则筛选特定 symbol 的数据
            if symbol_col_in_file and symbol_col_in_file in data.columns:
                data = data[data[symbol_col_in_file] == symbol]
                if data.empty:
                    print(f"[LocalCsvSource] 未找到标的 '{symbol}' 在列 '{symbol_col_in_file}' 中在文件 {file_path}.")
                    return None
            
            # 按日期筛选
            if start_date:
                data = data[data.index >= pd.to_datetime(start_date)]
            if end_date:
                data = data[data.index <= pd.to_datetime(end_date)]

            # 确保标准列存在
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in data.columns:
                    print(f"[LocalCsvSource] 警告: 列 '{col}' 未在标的 '{symbol}' 的数据中找到. 填充0或NaN.")
                    data[col] = 0

            data.sort_index(inplace=True)
            return data[required_cols]
            
        except Exception as e:
            print(f"[LocalCsvSource] 加载或处理 {file_path} 中的数据时发生错误: {e}")
            return None
            
    def get_ticks(self, symbol: str, date: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取Tick数据
        
        Parameters
        ----------
        symbol : str
            标的代码
        date : str
            日期
            
        Returns
        -------
        Optional[pd.DataFrame]
            Tick数据
        """
        # 本地CSV实现可能不太容易直接获取Tick数据
        # 这里提供一个简单实现，实际使用时可能需要调整
        print(f"[LocalCsvSource] 警告: get_ticks 未完全实现. 请使用指定tick文件名的get_bars.")
        return None
        
    def get_fundamentals(self, table: str, symbols: List[str], 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, 
                        fields: Optional[List[str]] = None, **kwargs) -> Optional[pd.DataFrame]:
        """
        获取基本面数据
        
        Parameters
        ----------
        table : str
            基本面数据表名
        symbols : List[str]
            标的代码列表
        start_date : Optional[str], optional
            开始日期, by default None
        end_date : Optional[str], optional
            结束日期, by default None
        fields : Optional[List[str]], optional
            字段列表, by default None
            
        Returns
        -------
        Optional[pd.DataFrame]
            基本面数据
        """
        # 本地CSV实现通常不包含基本面数据
        # 这里提供一个简单实现，实际使用时可能需要调整
        print(f"[LocalCsvSource] 警告: get_fundamentals 未实现. 请指定基本面数据CSV文件.")
        return None 