# 数据源模块API文档

## 概述

数据源模块（`qte.data`）提供了统一的数据访问接口和多数据源支持功能。通过数据源管理器可以灵活注册、管理和切换不同的数据源。

## 数据源管理器

### DataSourceManager

数据源管理器是整个数据访问模块的核心，负责管理多个数据源，提供统一的数据访问接口。

```python
from qte.data.data_source_manager import get_data_source_manager

# 获取数据源管理器单例实例
dsm = get_data_source_manager()
```

#### 主要方法

- `register_source(name, source, make_default=False)`: 注册数据源
- `get_source(name=None)`: 获取指定名称的数据源实例
- `set_default_source(name)`: 设置默认数据源
- `list_sources()`: 列出所有注册的数据源
- `get_bars(symbol, start_date=None, end_date=None, frequency='1d', source_name=None, **kwargs)`: 获取K线数据
- `get_ticks(symbol, date, source_name=None, **kwargs)`: 获取Tick数据
- `get_fundamentals(table, symbols, start_date=None, end_date=None, fields=None, source_name=None, **kwargs)`: 获取基本面数据
- `get_symbols(market=None, source_name=None, **kwargs)`: 获取可用的标的列表

## 支持的数据源

### LocalCsvSource

从本地CSV文件加载数据的数据源。

```python
from qte.data.sources.local_csv import LocalCsvSource

# 初始化本地CSV数据源
csv_source = LocalCsvSource(base_path="examples/test_data/")

# 获取数据
data = csv_source.get_bars(
    symbol='sh.600000',
    start_date='2022-01-01',
    end_date='2022-01-31',
    file_name='real_stock_data.csv',
    date_col='date',
    symbol_col_in_file='code'
)
```

#### 主要方法

- `connect(**kwargs)`: 连接数据源（对于CSV只是验证路径存在）
- `get_symbols(market=None)`: 获取可用的标的列表（文件名）
- `get_bars(symbol, start_date=None, end_date=None, frequency='1d', file_name=None, date_col='datetime', symbol_col_in_file=None, **kwargs)`: 获取K线数据
- `get_ticks(symbol, date, **kwargs)`: 获取Tick数据（CSV实现有限制）
- `get_fundamentals(table, symbols, start_date=None, end_date=None, fields=None, **kwargs)`: 获取基本面数据（CSV实现有限制）

### GmQuantSource

掘金量化数据源，通过掘金API获取数据。

```python
from qte.data.sources.gm_quant import GmQuantSource

# 初始化掘金数据源
gm_source = GmQuantSource(token='your_token_here')
gm_source.connect()

# 获取数据
data = gm_source.get_bars(
    symbol='SHSE.600000',
    start_date='2023-01-01',
    end_date='2023-12-31',
    frequency='1d'
)
```

#### 主要方法

- `connect(token=None, **kwargs)`: 连接掘金API
- `get_symbols(market=None)`: 获取可用的标的列表
- `get_bars(symbol, start_date=None, end_date=None, frequency='1d', adjust='ADJUST_PREV', **kwargs)`: 获取K线数据
- `get_ticks(symbol, date, **kwargs)`: 获取Tick数据
- `get_fundamentals(table, symbols, start_date=None, end_date=None, fields=None, **kwargs)`: 获取基本面数据

## 数据格式标准

为确保各个数据源返回的数据格式一致，所有数据源都应遵循以下标准：

### K线数据
- 包含列：`open`, `high`, `low`, `close`, `volume`
- 索引为datetime类型
- 按时间升序排列

### Tick数据
- 包含列：`price`, `volume`, `bid_price`, `ask_price`, `bid_volume`, `ask_volume`
- 索引为datetime类型
- 按时间升序排列

### 基本面数据
- 格式视具体数据源而定，但应包含symbol和时间信息

## 添加新的数据源

添加新的数据源需要实现以下标准接口：

```python
class YourNewDataSource:
    def __init__(self, ...):
        """初始化数据源"""
        pass
        
    def connect(self, **kwargs) -> bool:
        """连接数据源"""
        pass
        
    def get_symbols(self, market=None, **kwargs) -> list:
        """获取可用标的列表"""
        pass
        
    def get_bars(self, symbol, start_date=None, end_date=None, frequency='1d', **kwargs) -> pd.DataFrame:
        """获取K线数据"""
        pass
        
    def get_ticks(self, symbol, date, **kwargs) -> pd.DataFrame:
        """获取Tick数据"""
        pass
        
    def get_fundamentals(self, table, symbols, start_date=None, end_date=None, fields=None, **kwargs) -> pd.DataFrame:
        """获取基本面数据"""
        pass
```

实现后，通过数据源管理器注册：

```python
dsm = get_data_source_manager()
dsm.register_source('your_source_name', YourNewDataSource(), make_default=True)
```

## 使用示例

### 注册并使用多个数据源

```python
from qte.data.sources.local_csv import LocalCsvSource
from qte.data.sources.gm_quant import GmQuantSource
from qte.data.data_source_manager import get_data_source_manager

# 初始化数据源
csv_source = LocalCsvSource()
gm_source = GmQuantSource(token='your_token_here')
gm_source.connect()

# 获取数据源管理器
dsm = get_data_source_manager()

# 注册数据源
dsm.register_source('csv', csv_source)
dsm.register_source('gm', gm_source, make_default=True)

# 从默认数据源获取数据
data_default = dsm.get_bars(
    symbol='SHSE.600000',
    start_date='2023-01-01',
    end_date='2023-12-31'
)

# 从指定数据源获取数据
data_csv = dsm.get_bars(
    symbol='sh.600000',
    start_date='2022-01-01',
    end_date='2022-01-31',
    source_name='csv',
    file_name='real_stock_data.csv',
    date_col='date',
    symbol_col_in_file='code'
)
```

### 在回测中使用

```python
from qte.core.engine_manager import EngineManager, EngineType
from strategies.traditional.dual_ma_strategy import DualMaStrategy
from qte.data.data_source_manager import get_data_source_manager

# 获取数据
dsm = get_data_source_manager()
data = dsm.get_bars(
    symbol='SHSE.600000',
    start_date='2023-01-01',
    end_date='2023-12-31'
)

# 创建策略和引擎
strategy = DualMaStrategy(short_window=5, long_window=20)
manager = EngineManager(engine_type=EngineType.VECTOR)
manager.add_strategy(strategy)

# 运行回测
results = manager.run(data)
``` 