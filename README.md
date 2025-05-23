# QTE - Quantitative Trading Engine

QTE是一个高性能的量化交易引擎，专为策略回测和实盘交易设计。

## 🏗️ 核心架构

### 📊 数据流架构图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   外部数据源      │    │   QTE Data模块    │    │  QTE虚拟交易所   │    │   vnpy Gateway  │
│                │    │                 │    │                │    │                │
│ • 币安API       │───▶│ • 数据源管理     │───▶│ • 撮合引擎      │───▶│ • QTE Gateway   │
│ • 掘金API       │    │ • 数据清洗      │    │ • 账户管理      │    │ • 订单转换      │
│ • 本地CSV       │    │ • 格式统一      │    │ • REST API     │    │ • 事件推送      │
│ • 其他数据源     │    │ • 数据回放      │    │ • WebSocket    │    │                │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │                        │
                                                       ▼                        ▼
                                              ┌─────────────────┐    ┌─────────────────┐
                                              │  回测/实盘数据   │    │   交易策略      │
                                              │                │    │                │
                                              │ • 历史价格      │    │ • 策略逻辑      │
                                              │ • 实时行情      │    │ • 风险管理      │
                                              │ • 订单簿       │    │ • 信号生成      │
                                              │ • 成交记录      │    │ • 组合管理      │
                                              └─────────────────┘    └─────────────────┘
```

### 🏢 模块化设计

## 📦 核心模块详解

### 1. 🗂️ Data模块 - 数据处理中心

**位置**: `qte/data/`

**核心功能**:
- **数据源抽象**: 统一的数据源接口，支持多种数据来源
- **数据清洗**: 自动处理缺失数据、异常值、格式转换
- **数据回放**: 支持多种回测模式的历史数据重放
- **实时数据**: 与外部API的实时数据连接

**关键组件**:
```python
# 数据源接口
qte/data/data_source_interface.py      # 基础数据源接口定义
qte/data/sources/binance_api.py        # 币安API数据源
qte/data/sources/gm_quant.py          # 掘金数据源  
qte/data/sources/local_csv.py         # 本地CSV数据源

# 数据回放控制器
qte/data/data_replay.py               # 数据回放控制器
  ├── DataFrameReplayController       # DataFrame回放
  ├── MultiSourceReplayController     # 多源同步回放
  └── FixedDataFrameReplayController  # 固定数据回放
```

**使用示例**:
```python
from qte.data.sources.binance_api import BinanceApiSource
from qte.data.data_replay import DataFrameReplayController, ReplayMode

# 1. 获取历史数据
data_source = BinanceApiSource(data_dir="data/binance")
data_source.connect()
btc_data = data_source.get_bars("BTCUSDT", "2024-01-01", "2024-12-31", "1d")

# 2. 创建数据回放控制器
replay_controller = DataFrameReplayController(
    dataframe=btc_data,
    mode=ReplayMode.BACKTEST,  # 回测模式
    speed_factor=1.0
)

# 3. 注册回调函数处理每个数据点
def on_market_data(data_point):
    print(f"价格更新: {data_point}")

replay_controller.register_callback(on_market_data)
replay_controller.start()
```

### 2. 🏛️ Exchange模块 - 虚拟交易所

**位置**: `qte/exchange/`

**核心功能**:
- **订单撮合**: 基于价格-时间优先级的高性能撮合引擎
- **账户管理**: 资金管理、余额控制、保证金计算
- **API服务**: Binance兼容的REST API和WebSocket接口
- **风险控制**: 实时风险监控和限制

**关键组件**:
```python
# 撮合引擎
qte/exchange/matching/matching_engine.py    # 核心撮合逻辑
qte/exchange/matching/order_book.py         # 订单簿管理

# 账户管理  
qte/exchange/account/account_manager.py     # 账户和资金管理
qte/exchange/account/balance_manager.py     # 余额管理

# API接口
qte/exchange/rest_api/rest_server.py        # REST API服务器
qte/exchange/websocket/websocket_server.py  # WebSocket服务器

# 主交易所
qte/exchange/mock_exchange.py               # 虚拟交易所主类
```

**Exchange与Data模块的集成**:
```python
# 虚拟交易所可以接收Data模块的实时数据
from qte.exchange import MockExchange
from qte.data.data_replay import DataFrameReplayController

# 1. 启动虚拟交易所
exchange = MockExchange(rest_port=5001)
exchange.start()

# 2. Data模块推送历史数据到交易所
def feed_to_exchange(data_point):
    # 更新交易所的市场数据
    exchange.update_market_price(data_point.symbol, data_point.close)

replay_controller.register_callback(feed_to_exchange)
```

### 3. 🔌 vnpy集成模块 - 策略接口

**位置**: `qte/vnpy/`

**核心功能**:
- **标准接口**: 提供vnpy标准的Gateway接口
- **事件转换**: 将QTE事件转换为vnpy事件格式
- **订单路由**: 将策略订单路由到QTE虚拟交易所
- **数据适配**: 将交易所数据适配为vnpy格式

**关键组件**:
```python
qte/vnpy/__init__.py                    # vnpy可用性检查
qte/vnpy/gateways/binance_spot.py      # QTE Binance Gateway
qte/vnpy/data_source.py               # vnpy数据源适配器
```

**vnpy与Exchange的连接**:
```python
from qte.vnpy.gateways.binance_spot import QTEBinanceSpotGateway
from vnpy.event import EventEngine

# 1. 创建vnpy事件引擎和网关
event_engine = EventEngine()
gateway = QTEBinanceSpotGateway(event_engine)

# 2. 连接到QTE虚拟交易所
gateway_setting = {
    "API密钥": "demo_api_key",
    "私钥": "demo_secret_key", 
    "服务器": "QTE_MOCK",  # 连接QTE虚拟交易所
}
gateway.connect(gateway_setting)

# 3. 策略通过vnpy接口交易
from vnpy.trader.object import OrderRequest
from vnpy.trader.constant import Direction, OrderType, Exchange

order_req = OrderRequest(
    symbol="BTCUSDT",
    exchange=Exchange.OTC,
    direction=Direction.LONG,
    type=OrderType.MARKET,
    volume=0.1
)
gateway.send_order(order_req)
```

### 4. 🧠 Core模块 - 核心引擎

**位置**: `qte/core/`

**核心功能**:
- **时间管理**: 统一的时间源，支持回测和实盘模式
- **事件系统**: 高性能的事件驱动架构
- **配置管理**: 全局配置和参数管理

**时间管理系统**:
```python
from qte.core.time_manager import set_backtest_time, get_current_time

# 回测模式：Data模块控制时间推进
for data_point in historical_data:
    set_backtest_time(data_point.timestamp)  # 设置虚拟时间
    # 所有模块(Exchange, vnpy, Strategy)都使用这个统一时间
    current_time = get_current_time()  # 获取统一时间源
```

### 5. 📈 其他模块

**ML模块** (`qte/ml/`): 机器学习策略支持
**Portfolio模块** (`qte/portfolio/`): 投资组合管理
**Execution模块** (`qte/execution/`): 执行算法
**Analysis模块** (`qte/analysis/`): 回测分析和报告

## 🔄 完整的数据流向

### 📥 历史数据回测流程

```
1. 数据获取阶段:
   币安API ──┐
   掘金API   ├──▶ Data Sources ──▶ 标准化数据格式 ──▶ 存储到CSV/数据库
   本地文件 ──┘

2. 回测执行阶段:
   历史数据 ──▶ DataReplayController ──▶ 按时间顺序推送 ──▶ QTE虚拟交易所
                        │                                        │
                        ▼                                        ▼
               设置虚拟时间(Core)                           更新市场数据
                        │                                        │
                        ▼                                        ▼
               vnpy Gateway ◀──── 监听市场数据和订单状态 ─────── 撮合引擎
                        │                                        ▲
                        ▼                                        │
                  交易策略 ──── 发送交易订单 ─────────────────────┘
```

### 📊 实时交易流程

```
1. 实时数据流:
   外部API ──▶ Data Sources ──▶ 实时数据推送 ──▶ QTE虚拟交易所
                                                        │
                                                        ▼
   交易策略 ◀──── vnpy Gateway ◀──── 实时行情推送 ─────┘
      │                                    ▲
      └──── 发送交易订单 ──────────────────┘
```

## 🚀 核心特性

### 📊 完整的交易基础设施
- **高性能撮合引擎**：基于订单簿的实时价格匹配
- **账户管理系统**：资金管理、余额控制、佣金计算
- **REST API服务器**：Binance兼容的交易接口
- **WebSocket服务**：实时市场数据推送

### ⏰ 先进的时间管理系统
- **虚拟时间支持**：完美解决回测与实盘时间冲突
- **无缝模式切换**：策略代码无需修改即可在回测/实盘间切换
- **时间戳一致性**：确保所有组件使用统一时间源
- **精确时间控制**：支持毫秒级时间推进

### 🔧 开发友好特性
- **事件驱动架构**：高度模块化和可扩展
- **完整测试覆盖**：单元测试、集成测试、性能测试
- **详细文档**：API文档、架构说明、使用示例
- **规范化开发**：严格的代码规范和项目结构

## 📁 项目结构

```
QTE/
├── qte/                    # 核心源代码包
│   ├── core/               # 核心引擎模块
│   │   ├── time_manager.py # 时间管理器（NEW! 🕐）
│   │   ├── events.py       # 事件系统
│   │   └── event_loop.py   # 事件循环
│   ├── data/               # 数据处理模块
│   │   ├── sources/        # 数据源实现
│   │   │   ├── binance_api.py    # 币安API数据源
│   │   │   ├── gm_quant.py       # 掘金数据源
│   │   │   └── local_csv.py      # 本地CSV数据源
│   │   ├── data_source_interface.py  # 数据源接口
│   │   └── data_replay.py         # 数据回放控制器
│   ├── exchange/           # 虚拟交易所模块
│   │   ├── matching/       # 撮合引擎
│   │   ├── account/        # 账户管理
│   │   ├── rest_api/       # REST API服务
│   │   ├── websocket/      # WebSocket服务
│   │   └── mock_exchange.py # 虚拟交易所主类
│   ├── vnpy/               # vnpy集成模块
│   │   ├── gateways/       # vnpy网关实现
│   │   │   └── binance_spot.py   # QTE Binance Gateway
│   │   ├── __init__.py     # vnpy可用性检查
│   │   └── data_source.py  # vnpy数据源适配器
│   ├── ml/                 # 机器学习策略
│   ├── portfolio/          # 投资组合管理
│   ├── execution/          # 执行系统
│   ├── analysis/           # 回测分析
│   └── utils/              # 工具函数
├── tests/                  # 测试代码
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── performance/        # 性能测试
├── examples/               # 示例代码
│   ├── simple_strategies/  # 简单策略示例
│   ├── ml_strategies/      # 机器学习策略示例
│   └── strategy_coin_flip.py  # 抛硬币策略示例
├── docs/                   # 文档
├── data/                   # 数据存储
│   ├── binance/           # 币安历史数据
│   ├── sample/            # 样本数据
│   └── backtest/          # 回测数据
└── scripts/               # 工具脚本
    └── download_binance_data.py  # 数据下载脚本
```

## 🔄 时间管理系统使用

### 回测模式
```python
from qte.core.time_manager import set_backtest_time, advance_backtest_time
from datetime import datetime

# 设置回测时间
set_backtest_time(datetime(2024, 6, 15, 9, 30, 0))

# 处理历史数据
for data_point in historical_data:
    # 设置当前数据时间
    set_backtest_time(data_point.timestamp)
    
    # 策略代码（无需修改）
    if should_buy():
        place_order(symbol="BTCUSDT", side="BUY", ...)
    
    # 推进时间
    advance_backtest_time(60)  # 推进1分钟
```

### 实盘模式
```python
from qte.core.time_manager import set_live_mode

# 切换到实盘模式
set_live_mode()

# 相同的策略代码自动使用真实时间
if should_buy():
    place_order(symbol="BTCUSDT", side="BUY", ...)
```

## 🚦 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 下载历史数据
```bash
# 下载币安热门交易对数据
python scripts/download_binance_data.py --action popular

# 下载指定交易对数据
python scripts/download_binance_data.py --action custom --symbols BTCUSDT ETHUSDT --days 365
```

### 3. 启动虚拟交易所
```bash
python start_exchange.py
```

### 4. 运行回测策略
```bash
# 使用历史数据回测的抛硬币策略
python examples/strategy_coin_flip.py
```

### 5. 运行实时策略
```bash
# 连接虚拟交易所的实时策略
python examples/strategy_coin_flip_vnpy.py
```

## 🧪 测试

### 运行所有测试
```bash
python -m pytest tests/ -v
```

### 运行特定模块测试
```bash
# 数据模块测试
python -m pytest tests/unit/data/ -v

# 交易所模块测试 
python -m pytest tests/unit/exchange/ -v

# vnpy集成测试
python -m pytest tests/unit/vnpy/ -v

# 时间管理器测试
python -m pytest tests/unit/core/test_time_manager.py -v
```

### 当前测试状态
- ✅ **核心模块测试**: 87/87通过
- ✅ **交易所模块测试**: 184/184通过  
- ✅ **数据模块测试**: 完整覆盖
- ✅ **vnpy集成测试**: 10/12通过 (2个跳过)
- ✅ **总计**: 281+通过

## 📋 API兼容性

QTE REST API完全兼容Binance Spot API v3：

- **市场数据**: `/api/v3/ticker/price`, `/api/v3/depth`, `/api/v3/trades`
- **交易接口**: `/api/v3/order`, `/api/v3/openOrders`, `/api/v3/allOrders`
- **账户信息**: `/api/v3/account`, `/api/v3/myTrades`
- **系统接口**: `/api/v3/ping`, `/api/v3/time`, `/api/v3/exchangeInfo`

## 🎯 核心优势

### 完整的数据处理管道
- **多数据源支持**: 币安API、掘金API、本地CSV等
- **自动数据清洗**: 处理缺失值、异常值、格式转换
- **灵活回放控制**: 支持实时、加速、步进等多种回测模式
- **数据缓存机制**: 提高重复访问效率

### 生产级虚拟交易所
- **高性能撮合**: 毫秒级延迟，支持多种订单类型
- **完整账户系统**: 资金管理、风险控制、佣金计算
- **API兼容性**: 与主流交易所API完全兼容
- **实时数据推送**: WebSocket支持实时行情和交易推送

### 无缝vnpy集成
- **标准接口**: 完全兼容vnpy Gateway接口
- **零修改策略**: 现有vnpy策略可直接使用
- **事件驱动**: 高效的事件处理和推送机制
- **多模式支持**: 同时支持回测和实盘模式

### 时间一致性解决方案
- **问题**: 回测时策略代码获取真实时间，与历史数据时间不匹配
- **解决**: 虚拟时间管理器统一所有组件的时间源
- **结果**: 代码无需修改，时间完全一致，回测更准确

## 💡 使用场景

### 📊 量化策略开发
```python
# 1. 数据获取和预处理
from qte.data.sources.binance_api import BinanceApiSource

data_source = BinanceApiSource()
historical_data = data_source.get_bars("BTCUSDT", "2024-01-01", "2024-12-31")

# 2. 策略回测
from qte.data.data_replay import DataFrameReplayController
from examples.strategy_coin_flip import CoinFlipStrategy

strategy = CoinFlipStrategy(symbols=['BTCUSDT'])
controller = DataFrameReplayController(historical_data)
controller.register_callback(strategy.on_market_data)
controller.start()

# 3. 结果分析
strategy.print_results()
strategy.plot_results()
```

### 🔄 算法交易回测
```python
# 使用虚拟交易所进行完整回测
from qte.exchange import MockExchange

exchange = MockExchange()
exchange.start()

# 策略通过vnpy接口与虚拟交易所交互
# 获得完全真实的交易体验
```

### 📈 机器学习策略验证
```python
# ML策略可以使用相同的基础设施
from qte.ml import MLStrategy

ml_strategy = MLStrategy(model_path="trained_model.pkl")
# 使用相同的数据和交易接口进行验证
```

## 📚 文档

- [时间管理系统详解](backtest_time_solution.md)
- [vnpy集成完成报告](QTE_VNPY_INTEGRATION_COMPLETED.md)
- [项目完成总结](PROJECT_COMPLETION_SUMMARY.md)
- [API文档](docs/api/)
- [架构设计](docs/architecture/)
- [开发指南](docs/development/)

## 🤝 贡献

欢迎提交Issue和Pull Request！请遵循项目的代码规范和测试要求。

## 📄 许可证

MIT License - 详见[LICENSE](LICENSE)文件

---

**QTE** - 让量化交易更简单、更准确、更可靠！ 🎯 