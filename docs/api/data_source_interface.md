# 数据源接口 API文档

## 概述

数据源接口定义了量化回测引擎中所有数据源类必须实现的方法，确保各数据源的一致性和可替换性。本文档详细说明了数据源接口的设计理念、核心方法和使用方式。

## 核心接口

### DataSourceInterface

`DataSourceInterface` 是所有数据源必须实现的抽象基类，定义了统一的数据获取接口。

```python
from qte.data import DataSourceInterface

class MyCustomSource(DataSourceInterface):
    # 必须实现所有抽象方法
    ...
```

#### 必须实现的方法

以下方法是所有数据源必须实现的核心方法：

##### connect

```python
def connect(self, **kwargs) -> bool:
    """连接到数据源"""
    pass
```

**说明**：连接到数据源，建立必要的连接，获取身份验证等。

**参数**：
- `**kwargs`: 连接参数，根据具体数据源而定，例如API密钥、服务器地址等

**返回值**：连接是否成功

**示例**：
```python
# 连接到掘金数据源
gm_source = GmQuantSource()
success = gm_source.connect(token="your_token_here")
```

##### get_symbols

```python
def get_symbols(self, market: Optional[str] = None, **kwargs) -> List[str]:
    """获取可用标的列表"""
    pass
```

**说明**：获取指定市场的所有可用交易标的。

**参数**：
- `market`: 市场代码，如'SHSE'（上海证券交易所）
- `**kwargs`: 其他参数

**返回值**：标的代码列表

**示例**：
```python
# 获取上交所股票列表
symbols = gm_source.get_symbols(market='SHSE')
```

##### get_bars

```python
def get_bars(self, symbol: str, 
           start_date: Optional[Union[str, datetime, date]] = None, 
           end_date: Optional[Union[str, datetime, date]] = None, 
           frequency: str = '1d', 
           **kwargs) -> Optional[pd.DataFrame]:
    """获取K线数据"""
    pass
```

**说明**：获取指定标的的K线数据。

**参数**：
- `symbol`: 标的代码
- `start_date`: 开始日期
- `end_date`: 结束日期
- `frequency`: 频率，如'1d'（日线）, '1h'（小时线）, '1m'（分钟线）
- `**kwargs`: 其他参数，如调整类型等

**返回值**：DataFrame格式的K线数据，包含以下列：
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量

**示例**：
```python
# 获取上证指数的日线数据
df = gm_source.get_bars(
    symbol='SHSE.000001',
    start_date='2022-01-01',
    end_date='2022-12-31',
    frequency='1d'
)
```

#### 可选实现的方法

以下方法是可选实现的，基类提供了默认实现（通常是返回None或空列表）：

##### get_ticks

```python
def get_ticks(self, symbol: str, 
             date: Optional[Union[str, datetime, date]] = None, 
             **kwargs) -> Optional[pd.DataFrame]:
    """获取Tick数据"""
    pass
```

**说明**：获取指定标的的Tick级别数据。

**参数**：
- `symbol`: 标的代码
- `date`: 日期
- `**kwargs`: 其他参数

**返回值**：DataFrame格式的Tick数据

**示例**：
```python
# 获取某只股票的当日Tick数据
ticks = gm_source.get_ticks(
    symbol='SHSE.600000',
    date='2022-01-04'
)
```

##### get_fundamentals

```python
def get_fundamentals(self, table: str, 
                     symbols: List[str], 
                     start_date: Optional[Union[str, datetime, date]] = None, 
                     end_date: Optional[Union[str, datetime, date]] = None, 
                     fields: Optional[List[str]] = None, 
                     **kwargs) -> Optional[pd.DataFrame]:
    """获取基本面数据"""
    pass
```

**说明**：获取基本面数据，如财务指标、估值指标等。

**参数**：
- `table`: 数据表名称
- `symbols`: 标的代码列表
- `start_date`: 开始日期
- `end_date`: 结束日期
- `fields`: 需要获取的字段列表
- `**kwargs`: 其他参数

**返回值**：DataFrame格式的基本面数据

**示例**：
```python
# 获取多只股票的市盈率数据
pe_data = gm_source.get_fundamentals(
    table='trading_derivative_indicator',
    symbols=['SHSE.600000', 'SHSE.601398'],
    start_date='2022-01-01',
    end_date='2022-12-31',
    fields=['pe_ratio']
)
```

## 辅助基类

### BaseDataSource

`BaseDataSource` 是实现了 `DataSourceInterface` 的基类，提供了一些通用功能的默认实现，简化了数据源的开发。

```python
from qte.data import BaseDataSource

class MyCustomSource(BaseDataSource):
    # 只需要实现核心方法，可以利用基类提供的辅助方法
    ...
```

#### 有用的辅助方法

##### _ensure_connected

```python
def _ensure_connected(self) -> bool:
    """确保已连接到数据源"""
    ...
```

**说明**：检查是否已连接到数据源，如果未连接则尝试连接。

**返回值**：是否已连接

**使用场景**：
```python
def get_bars(self, symbol, ...):
    if not self._ensure_connected():
        return None
    # 继续获取数据...
```

##### _format_date

```python
def _format_date(self, date_obj: Optional[Union[str, datetime, date]]) -> Optional[str]:
    """将日期对象格式化为字符串"""
    ...
```

**说明**：将各种类型的日期对象统一格式化为字符串格式。

**参数**：
- `date_obj`: 日期对象，可以是字符串、datetime或date类型

**返回值**：格式化后的日期字符串，如'2022-01-01'

**使用场景**：
```python
def get_bars(self, symbol, start_date, ...):
    start_date_str = self._format_date(start_date)
    # 使用格式化后的日期字符串...
```

## 最佳实践

### 数据源实现示例

下面是一个简单的自定义数据源实现示例：

```python
from qte.data import BaseDataSource
import pandas as pd
from typing import Optional, List, Union
from datetime import datetime, date

class MyCustomSource(BaseDataSource):
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.api_client = None
    
    def connect(self, api_key: Optional[str] = None, **kwargs) -> bool:
        if api_key:
            self.api_key = api_key
        
        if not self.api_key:
            return False
        
        try:
            # 初始化API客户端
            self.api_client = MyApiClient(self.api_key)
            self._connected = True
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def get_symbols(self, market: Optional[str] = None, **kwargs) -> List[str]:
        if not self._ensure_connected():
            return []
        
        try:
            # 获取符号列表
            return self.api_client.get_symbols(market)
        except Exception as e:
            print(f"获取标的列表失败: {e}")
            return []
    
    def get_bars(self, symbol: str, 
                start_date: Optional[Union[str, datetime, date]] = None, 
                end_date: Optional[Union[str, datetime, date]] = None, 
                frequency: str = '1d', 
                **kwargs) -> Optional[pd.DataFrame]:
        if not self._ensure_connected():
            return None
        
        try:
            # 格式化日期
            start_date_str = self._format_date(start_date)
            end_date_str = self._format_date(end_date)
            
            # 获取K线数据
            data = self.api_client.get_bars(
                symbol=symbol,
                start_date=start_date_str,
                end_date=end_date_str,
                freq=frequency
            )
            
            # 转换为DataFrame并设置正确的列名和索引
            df = pd.DataFrame(data)
            df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            
            return df
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return None
```

### 注册和使用自定义数据源

使用`DataSourceFactory`注册和使用自定义数据源：

```python
from qte.data import DataSourceFactory, get_data_source_manager

# 注册自定义数据源
DataSourceFactory.register_source_class('mycustom', MyCustomSource)

# 使用工厂创建实例
my_source = DataSourceFactory.create('mycustom', api_key='your_key_here')

# 或者通过数据源管理器使用
dsm = get_data_source_manager()
dsm.register_source('my_data', my_source, make_default=True)

# 获取数据
data = dsm.get_bars(
    symbol='SHSE.600000',
    start_date='2022-01-01',
    end_date='2022-12-31'
)
```

## 错误处理指南

实现数据源时，应遵循以下错误处理原则：

1. **连接失败**: 在`connect()`方法中返回`False`，而不是抛出异常
2. **数据获取失败**: 返回`None`或空数据结构，并通过日志记录错误
3. **参数错误**: 对于明显的参数错误，可以抛出`ValueError`异常
4. **网络问题**: 实现重试机制，多次失败后返回`None`

示例：
```python
def get_bars(self, symbol, ...):
    if not symbol:
        raise ValueError("标的代码不能为空")
    
    for attempt in range(3):  # 重试3次
        try:
            # 尝试获取数据...
            return data
        except ConnectionError:
            if attempt == 2:  # 最后一次尝试
                return None
            time.sleep(1)  # 等待后重试
```

## 性能优化建议

1. **实现缓存机制**: 缓存频繁请求的数据
2. **批量获取**: 尽可能批量获取数据而不是多次单独请求
3. **延迟加载**: 只在实际需要时加载数据
4. **异步预取**: 预测并异步加载可能需要的数据

示例缓存实现：
```python
def get_bars(self, symbol, ...):
    # 构建缓存键
    cache_key = f"{symbol}_{start_date}_{end_date}_{frequency}"
    
    # 检查缓存
    if self._cache and (cached_data := self._cache.get(cache_key)):
        return cached_data
    
    # 获取数据
    data = self._fetch_data(...)
    
    # 更新缓存
    if self._cache and data is not None:
        self._cache.set(cache_key, data)
    
    return data
``` 