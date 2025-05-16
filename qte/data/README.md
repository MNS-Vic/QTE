# 量化回测引擎 - 数据模块 (QTE Data)

本目录包含量化回测引擎的数据模块，负责提供回测过程中所需的各类市场数据。

## 模块结构

- `interfaces.py` - 数据提供者接口定义
- `csv_data_provider.py` - CSV数据提供者实现
- `gm_data_provider.py` - 掘金量化数据提供者实现
- `gm_data_adapter.py` - 掘金数据适配器（兼容性模块）
- `__init__.py` - 包初始化文件

## 掘金量化数据提供者

掘金量化数据提供者（GmDataProvider）支持从掘金量化平台下载各类市场数据，包括日线、分钟线和tick级别数据，
并按照回测系统所需的标准格式提供这些数据。

### 功能特点

1. **数据下载与缓存**
   - 支持下载日线、分钟线和tick级别的行情数据
   - 自动缓存下载的数据，避免重复下载
   - 数据存储为CSV格式，方便查看和分析

2. **完整实现DataProvider接口**
   - 支持获取最新K线、历史K线和流式市场数据
   - 支持生成市场事件，与事件驱动的回测系统无缝集成

3. **高效数据访问**
   - 使用内存缓存提高数据访问效率
   - 提供数据生成器，支持高效处理大量数据

4. **模块化结构**
   - GmDataDownloader类：负责数据下载和本地存储
   - GmDataProvider类：实现DataProvider接口，提供标准化数据访问
   - 支持自定义数据目录和掘金量化Token

### 使用方法

#### 初始化数据提供者

```python
from qte_core.event_loop import EventLoop
from qte_data.gm_data_provider import GmDataProvider

# 创建事件循环
event_loop = EventLoop()

# 创建掘金数据提供者
provider = GmDataProvider(
    token="your_gm_token_here",  # 掘金量化API令牌
    event_loop=event_loop,       # 事件循环实例
    data_dir="data/market_data"  # 数据存储目录
)
```

#### 获取历史K线数据

```python
from datetime import datetime

# 定义时间范围
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 1, 31)

# 获取上证指数的历史日线数据
bars_gen = provider.get_historical_bars("SHSE.000001", start_date, end_date)

# 遍历数据
for bar in bars_gen:
    print(f"日期: {bar['timestamp']}, 收盘价: {bar['close']}")
```

#### 获取分钟线数据

```python
# 获取贵州茅台的1分钟线数据
minute_gen = provider.get_minute_bar_generator(
    symbol="SHSE.600519",
    minutes=1,
    start_date=datetime(2023, 1, 10, 9, 30),
    end_date=datetime(2023, 1, 10, 15, 0)
)

for bar in minute_gen:
    print(f"时间: {bar['timestamp']}, 价格: {bar['close']}")
```

#### 获取Tick数据

```python
# 获取贵州茅台的tick数据
tick_gen = provider.get_tick_generator(
    symbol="SHSE.600519",
    start_date=datetime(2023, 1, 10, 9, 30),
    end_date=datetime(2023, 1, 10, 10, 0)
)

for tick in tick_gen:
    print(f"时间: {tick['timestamp']}, 价格: {tick['price'] if 'price' in tick else tick['last_price']}")
```

#### 生成市场事件流

```python
# 生成多个交易品种的市场事件流
symbols = ["SHSE.000001", "SHSE.600519"]
for event in provider.stream_market_data(symbols):
    # 处理市场事件
    print(f"{event.timestamp} - {event.symbol}: {event.close_price}")
```

### 数据目录结构

数据将按以下结构存储在指定的数据目录中：

```
data_dir/
  ├── daily/                # 日线数据
  │   └── SHSE/             # 交易所
  │       └── 000001/       # 股票代码
  │           └── SHSE_000001_2023-01-01_to_2023-01-31_daily.csv
  │
  ├── 1min/                 # 分钟线数据
  │   └── SHSE/
  │       └── 600519/
  │           └── SHSE_600519_2023-01-10_to_2023-01-10_1min.csv
  │
  └── tick/                 # Tick数据
      └── SHSE/
          └── 600519/
              └── SHSE_600519_2023-01-10_tick.csv
```

### 兼容性说明

为了保持与旧代码的兼容性，模块提供了以下兼容性别名：

```python
# 这些导入是等效的
from qte_data.gm_data_provider import GmDataProvider
from qte_data.gm_data_adapter import GmDataAdapter  # 兼容性别名
```

建议在新代码中直接使用`GmDataProvider`，`GmDataAdapter`类将在未来版本中移除。

### 注意事项

1. 使用前需要安装掘金量化SDK：`pip install gm`
2. 需要有效的掘金量化API令牌
3. 首次下载数据可能需要较长时间，后续会使用缓存提高效率
4. Tick数据量较大，按天下载并保存
5. 如果遇到时区相关问题，请确保datetime对象的时区设置正确 