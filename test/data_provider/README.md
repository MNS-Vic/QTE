# 掘金行情数据下载工具

这个工具用于从掘金量化平台下载行情数据，支持tick级、分钟级和日线级数据。

## 功能特点

- 支持多种数据类型：tick数据、分钟线数据、日线数据
- 支持各种标的：股票、指数、期货等
- 支持不同复权方式：前复权、后复权、不复权
- 自动按日期、交易所、品种分类保存数据
- 支持命令行调用和作为库导入使用
- 自动处理大量数据的分片下载（特别是tick数据）
- 保存为CSV格式，便于后续分析使用

## 环境要求

- Python 3.6+
- 掘金量化Python SDK（`pip install gm`）
- pandas

## 使用方法

### 命令行使用

#### 下载日线数据

```bash
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-12-31 --daily --pre-adjust
```

#### 下载分钟线数据

```bash
# 下载1分钟K线数据
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-01-10 --minute 1

# 下载5分钟K线数据
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-01-10 --minute 5
```

#### 下载tick数据

```bash
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-01-05 --tick
```

#### 复权选项

```bash
# 前复权
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-12-31 --daily --pre-adjust

# 后复权
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-12-31 --daily --post-adjust

# 不复权（默认）
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-12-31 --daily --no-adjust
```

#### 指定输出目录

```bash
python download_gm_data.py --symbol SHSE.600000 --start-date 2023-01-01 --end-date 2023-12-31 --daily --output-dir my_data
```

### 作为库使用

您也可以在自己的Python代码中导入并使用这个工具：

```python
from download_gm_data import GoldenMineDataDownloader
from gm.api import ADJUST_PREV

# 创建下载器实例
downloader = GoldenMineDataDownloader(
    token="your_token_here",
    output_dir="downloaded_data"
)

# 下载日线数据
daily_data = downloader.download_daily_data(
    symbol="SHSE.600000",
    start_date="2023-01-01",
    end_date="2023-12-31",
    adjust=ADJUST_PREV  # 前复权
)

# 下载分钟线数据
minute_data = downloader.download_minute_data(
    symbol="SHSE.600000",
    minutes=5,  # 5分钟线
    start_date="2023-01-01",
    end_date="2023-01-10",
    adjust=None  # 不复权
)

# 下载tick数据
tick_data = downloader.download_tick_data(
    symbol="SHSE.600000",
    start_date="2023-01-01",
    end_date="2023-01-02"
)
```

## 命令行参数说明

| 参数 | 说明 |
|------|------|
| `--token` | 掘金量化Token，如果不提供，将使用默认Token |
| `--output-dir` | 数据保存目录，默认为`downloaded_data` |
| `--symbol` | 标的代码，如`SHSE.600000` |
| `--start-date` | 开始日期，格式为`YYYY-MM-DD` |
| `--end-date` | 结束日期，格式为`YYYY-MM-DD`，默认为当天 |
| `--tick` | 下载tick数据 |
| `--minute N` | 下载N分钟线数据，N为分钟数，如`--minute 5`表示5分钟线 |
| `--daily` | 下载日线数据 |
| `--no-adjust` | 不复权（默认） |
| `--pre-adjust` | 前复权 |
| `--post-adjust` | 后复权 |

## 示例

查看[download_gm_data_example.py](download_gm_data_example.py)了解更多使用示例。

## 数据输出格式

下载的数据将保存在以下目录结构中：

### 日线数据

```
downloaded_data/
  └── daily/
      └── SHSE/
          └── 600000/
              └── SHSE_600000_2023-01-01_to_2023-12-31_daily_前复权.csv
```

### 分钟线数据

```
downloaded_data/
  └── 5min/
      └── SHSE/
          └── 600000/
              └── SHSE_600000_2023-01-01_to_2023-01-10_5min.csv
```

### Tick数据

Tick数据按天拆分保存：

```
downloaded_data/
  └── tick/
      └── SHSE/
          └── 600000/
              ├── SHSE_600000_2023-01-01_tick.csv
              ├── SHSE_600000_2023-01-02_tick.csv
              └── ...
```

## 常见问题

1. **Token无效**：请确保提供的掘金量化Token有效。您可以在掘金量化平台的"用户-密钥管理"中获取有效的Token。

2. **数据下载失败**：可能是网络问题或者所请求的数据不存在（如非交易日数据）。尝试缩小日期范围或检查网络连接。

3. **Tick数据量大**：Tick数据量非常大，建议按天或按较短的时间段下载。

4. **安装依赖**：确保正确安装了掘金量化SDK（`pip install gm`）和pandas。

## 免责声明

本工具仅用于学习和研究目的。使用掘金量化API获取数据需遵守掘金量化的使用条款和数据许可协议。请确保您有权限访问相关数据。

# 数据提供者测试目录该目录包含数据相关的测试和示例代码。## 文件说明- `download_gm_data.py` - 掘金数据下载工具，支持命令行参数- `gm_data_example.py` - 掘金数据提供者使用示例- `analyze_tick_data.py` - Tick数据分析工具- `debug_gm_provider.py` - 掘金数据提供者调试脚本- `downloaded_data/` - 下载的测试数据存储目录

## 掘金数据下载工具

`download_gm_data.py`是一个命令行工具，可以用来下载掘金量化平台的历史行情数据，支持日线、分钟线和tick级别数据。

### 使用方法

```bash
# 下载日线数据
python download_gm_data.py --token YOUR_TOKEN --symbol SHSE.000001 --start-date 2023-01-01 --end-date 2023-01-31 --daily

# 下载分钟线数据
python download_gm_data.py --token YOUR_TOKEN --symbol SHSE.600519 --start-date 2023-01-10 --minute 1

# 下载tick数据
python download_gm_data.py --token YOUR_TOKEN --symbol SHSE.600519 --start-date 2023-01-10 --tick
```

## 掘金数据提供者示例

`gm_data_example.py`演示了如何使用掘金数据提供者(GmDataProvider)获取和处理各种类型的市场数据。

### 示例功能

1. 获取日线数据
2. 获取分钟线数据
3. 获取Tick数据
4. 生成市场事件流

## Tick数据分析工具

`analyze_tick_data.py`是一个用于分析tick数据特征的工具，帮助了解tick数据的结构和内容。 