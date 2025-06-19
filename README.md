# 🚀 QTE - 量化交易引擎演示系统

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Coverage](https://img.shields.io/badge/Coverage-97.93%25-brightgreen.svg)](https://github.com/MNS-Vic/QTE)
[![Tests](https://img.shields.io/badge/Tests-468%20passed-brightgreen.svg)](https://github.com/MNS-Vic/QTE)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**QTE (Quantitative Trading Engine)** 是一个完整的量化交易引擎，提供从数据获取到策略执行、从回测分析到实盘交易的全栈解决方案。本项目包含了**9种完整的演示模式**，展示了现代量化交易系统的所有核心功能。

## ✨ 核心特性

🎯 **完整技术栈演示** - 从数据源到分析报告的端到端展示
🧠 **机器学习集成** - 特征工程、模型训练、策略优化
🏛️ **虚拟交易所** - 完整的撮合引擎和账户管理系统
🔌 **vnpy框架集成** - 无缝对接vnpy生态系统
📊 **专业可视化** - 深色主题的交互式分析报告
🗄️ **多数据源支持** - 本地CSV、API服务、交易所数据
⚡ **高性能架构** - 事件驱动、异步处理、毫秒级响应
🧪 **高测试覆盖** - 97.93%测试覆盖率，468个测试用例

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.9+ (推荐 3.9 或 3.10，避免 pandas 兼容性问题)
- **操作系统**: Windows / macOS / Linux
- **内存**: 最低 4GB，推荐 8GB+
- **磁盘空间**: 最低 2GB

### ⚡ 一键安装

```bash
# 1. 克隆项目
git clone https://github.com/MNS-Vic/QTE.git
cd QTE

# 2. 创建虚拟环境 (推荐)
conda create -n qte-demo python=3.9
conda activate qte-demo

# 或使用 venv
python -m venv qte-demo
source qte-demo/bin/activate  # Linux/macOS
# qte-demo\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python run_qte_demo.py --mode test
```

### 🎯 立即体验

```bash
# 🌟 一键体验所有功能 (推荐)
python run_qte_demo.py --mode all --verbose

# 🎬 单独体验各个模块
python run_qte_demo.py --mode simple      # 基础量化交易
python run_qte_demo.py --mode ml          # 机器学习策略
python run_qte_demo.py --mode exchange    # 虚拟交易所
python run_qte_demo.py --mode report      # 可视化报告
```

## 🎬 演示模式详解

QTE提供了**9种完整的演示模式**，每种模式都展示了量化交易系统的不同方面：

### 🌟 综合演示模式 (`--mode all`)

**一键体验所有功能，最佳入门选择！**

```bash
python run_qte_demo.py --mode all --verbose
```

**功能展示**:
- 依次运行所有7个核心演示模式
- 实时进度显示：`[1/7] → [7/7]`
- 生成综合分析报告
- 完整的技术栈覆盖验证

**预期输出**:
```
🚀 QTE量化交易引擎 - 综合演示模式
📋 将依次运行 7 个演示模式
⏱️ 预计总耗时: 76 秒
📊 演示功能: 数据源 → 策略执行 → 交易所 → 分析报告

✅ 成功运行的演示:
   - 简单演示 (0.02s)
   - 高级演示 (1.61s)
   - 虚拟交易所 (3.08s)
   - 机器学习 (5.01s)
   - vnpy集成 (0.02s)
   - 数据源生态系统 (7.58s)
   - 可视化报告 (0.33s)

📈 聚合指标:
   总交易数: 7笔
   ML模型训练: 5个
   数据源测试: 3个
   vnpy事件处理: 7个

🏗️ 技术栈覆盖:
   ✅ 数据层 ✅ 策略层 ✅ 执行层 ✅ 交易所层 ✅ 分析层
```

### 📊 基础演示模式

#### 🎯 简单演示 (`--mode simple`)

**展示基础量化交易流程**

```bash
python run_qte_demo.py --mode simple
```

**功能展示**:
- 生成模拟市场数据
- 实现移动平均策略
- 执行回测和性能分析
- 生成交易报告

**预期输出**:
```
📊 回测结果摘要:
   初始资金: $100,000.00
   最终权益: $41,156.00
   总收益: $-58,844.00
   收益率: -58.84%
   交易次数: 7
   夏普比率: -1.033
```

#### ⚡ 高级演示 (`--mode advanced`)

**展示事件驱动架构**

```bash
python run_qte_demo.py --mode advanced
```

**功能展示**:
- 多策略系统架构
- 事件驱动回测引擎
- 风险管理系统
- 投资组合分析

### 🏛️ 虚拟交易所演示 (`--mode exchange`)

**展示完整的交易所功能**

```bash
python run_qte_demo.py --mode exchange
```

**功能展示**:
- 高性能撮合引擎
- 完整的账户管理系统
- REST API 和 WebSocket 服务
- 实时市场数据推送
- 订单生命周期管理

**预期输出**:
```
🏛️ 虚拟交易所演示启动...
✅ 撮合引擎已启动
✅ REST API服务器启动 (端口: 5001)
✅ WebSocket服务器启动 (端口: 8766)
📊 处理订单: 15笔
📈 市场数据更新: 1000次
💰 账户余额管理: 正常
```

### 🧠 机器学习演示 (`--mode ml`)

**展示AI驱动的交易策略**

```bash
python run_qte_demo.py --mode ml
```

**功能展示**:
- 技术指标特征工程
- 随机森林模型训练
- 特征重要性分析
- ML驱动的交易信号
- 模型性能评估

**预期输出**:
```
🧠 机器学习交易策略演示...
📊 生成特征: 345个
🤖 训练模型: 5个 (AAPL, GOOGL, MSFT, TSLA, NVDA)
📈 模型性能:
   AAPL: R² = -0.04, RMSE = 0.036
   GOOGL: R² = -0.07, RMSE = 0.044
   MSFT: R² = 0.06, RMSE = 0.034
   TSLA: R² = 0.11, RMSE = 0.112
   NVDA: R² = 0.04, RMSE = 0.080
```

### 🔌 vnpy集成演示 (`--mode vnpy`)

**展示与vnpy框架的无缝集成**

```bash
python run_qte_demo.py --mode vnpy
```

**功能展示**:
- vnpy事件引擎集成
- QTE Gateway创建和连接
- 标准订单接口
- 市场数据订阅
- 账户和持仓查询

**预期输出**:
```
🔌 vnpy集成架构演示...
✅ vnpy集成可用
📡 订阅标的: 3个
📋 发送订单: 2笔
💼 执行交易: 2笔
📊 处理事件: 7个
```

### 🗄️ 数据源生态系统演示 (`--mode datasource`)

**展示多数据源管理和性能对比**

```bash
python run_qte_demo.py --mode datasource
```

**功能展示**:
- 多数据源注册和管理
- 数据源性能基准测试
- 数据质量分析和评估
- 数据聚合策略演示
- 智能数据源选择

**预期输出**:
```
🗄️ 数据源生态系统演示...
🔧 注册数据源: 3个
   - LocalCSV: 本地CSV文件数据源
   - GmQuant: 掘金量化数据API
   - BinanceAPI: 币安交易所API
⚡ 性能测试:
   local_csv: 连接时间 0.001s, 可靠性 100/100
   gm_quant: 连接时间 0.002s, 可靠性 95/100
   binance_api: 连接时间 0.613s, 可靠性 85/100
🏆 综合冠军: local_csv (评分: 18.0)
```

### 📊 可视化报告演示 (`--mode report`)

**展示专业级分析报告生成**

```bash
python run_qte_demo.py --mode report
```

**功能展示**:
- 专业深色主题设计
- 交互式Plotly图表
- 多演示数据聚合分析
- 响应式网页设计
- 功能覆盖雷达图

**预期输出**:
```
📊 可视化报告演示...
📈 分析演示: 3个
📊 创建图表: 3个
   - 交易数量对比柱状图
   - ML策略收益率曲线
   - 功能覆盖雷达图
🎨 HTML报告: demo_reports/qte_demo_analysis_report.html
```

### 🧪 系统验证模式 (`--mode test`)

**验证系统功能完整性**

```bash
python run_qte_demo.py --mode test
```

**功能展示**:
- 核心模块可用性检查
- 依赖环境验证
- 基础功能测试
- 系统健康状态报告

## 📋 演示模式对比表

| 演示模式 | 主要功能 | 技术栈 | 运行时间 | 适合场景 |
|---------|---------|--------|----------|----------|
| 🌟 **all** | 一键体验所有功能 | 全栈 | ~20秒 | **首次使用推荐** |
| 🎯 **simple** | 基础量化交易 | 策略+回测 | ~1秒 | 快速了解 |
| ⚡ **advanced** | 事件驱动架构 | 引擎+多策略 | ~2秒 | 架构学习 |
| 🏛️ **exchange** | 虚拟交易所 | 撮合+API | ~3秒 | 交易所开发 |
| 🧠 **ml** | 机器学习策略 | AI+特征工程 | ~5秒 | AI量化 |
| 🔌 **vnpy** | vnpy框架集成 | Gateway+事件 | ~1秒 | vnpy用户 |
| 🗄️ **datasource** | 数据源管理 | 多源+性能 | ~8秒 | 数据工程 |
| 📊 **report** | 可视化报告 | 图表+分析 | ~1秒 | 结果展示 |
| 🧪 **test** | 系统验证 | 测试+检查 | ~1秒 | 环境验证 |

## 🛠️ 安装和配置

### 📦 依赖管理

QTE使用严格的依赖版本控制以确保稳定性：

```bash
# 核心依赖 (requirements.txt)
pandas==1.5.3          # 数据处理 (避免3.12兼容性问题)
numpy==1.24.3           # 数值计算
scikit-learn>=1.3.0     # 机器学习
plotly>=5.0.0           # 交互式图表
fastapi>=0.68.0         # REST API服务
websockets>=10.0        # WebSocket服务
pydantic>=1.8.0         # 数据验证

# 可选依赖
vnpy>=3.0.0             # vnpy框架集成 (可选)
gm>=3.0.0               # 掘金数据源 (可选)
```

### 🔧 环境配置

#### 方案1: Conda环境 (推荐)

```bash
# 创建专用环境
conda create -n qte-demo python=3.9
conda activate qte-demo

# 安装依赖
pip install -r requirements.txt

# 验证安装
python run_qte_demo.py --mode test
```

#### 方案2: Docker环境

```bash
# 构建镜像
docker build -t qte-demo .

# 运行容器
docker run -it --rm -p 5001:5001 -p 8766:8766 qte-demo

# 在容器内运行演示
python run_qte_demo.py --mode all
```

#### 方案3: 虚拟环境

```bash
# 创建虚拟环境
python -m venv qte-demo

# 激活环境
source qte-demo/bin/activate  # Linux/macOS
# qte-demo\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

## 🚨 故障排除

### 常见问题和解决方案

#### ❌ 问题1: pandas兼容性错误

```bash
# 错误信息
AttributeError: module 'pandas' has no attribute '_NoValueType'

# 解决方案
pip uninstall pandas numpy
pip install pandas==1.5.3 numpy==1.24.3
```

#### ❌ 问题2: vnpy模块导入失败

```bash
# 错误信息
ModuleNotFoundError: No module named 'vnpy'

# 解决方案 (可选安装)
pip install vnpy>=3.0.0

# 或跳过vnpy演示
python run_qte_demo.py --mode simple  # 使用其他模式
```

#### ❌ 问题3: 端口占用错误

```bash
# 错误信息
OSError: [Errno 48] Address already in use

# 解决方案
# 查找占用进程
lsof -i :5001  # REST API端口
lsof -i :8766  # WebSocket端口

# 终止进程
kill -9 <PID>

# 或使用不同端口
python run_qte_demo.py --mode exchange --port 5002
```

#### ❌ 问题4: 内存不足

```bash
# 错误信息
MemoryError: Unable to allocate array

# 解决方案
# 减少数据量或使用更小的演示
python run_qte_demo.py --mode simple  # 使用轻量级模式
```

#### ❌ 问题5: 权限错误

```bash
# 错误信息
PermissionError: [Errno 13] Permission denied

# 解决方案
# 确保有写入权限
chmod 755 demo_output/
chmod 755 demo_reports/

# 或使用sudo (不推荐)
sudo python run_qte_demo.py --mode test
```

## 📁 项目结构

```
QTE/
├── 🚀 run_qte_demo.py          # 主演示启动脚本
├── 📋 requirements.txt         # 依赖列表
├── 📖 README.md               # 项目文档 (本文件)
│
├── qte/                       # 🏗️ 核心源代码包
│   ├── core/                  # 核心引擎模块
│   │   ├── time_manager.py    # ⏰ 时间管理器
│   │   ├── events.py          # 📡 事件系统
│   │   └── event_loop.py      # 🔄 事件循环
│   ├── data/                  # 📊 数据处理模块
│   │   ├── sources/           # 数据源实现
│   │   │   ├── binance_api.py # 🟡 币安API数据源
│   │   │   ├── gm_quant.py    # 🟢 掘金数据源
│   │   │   └── local_csv.py   # 📄 本地CSV数据源
│   │   ├── data_source_interface.py  # 🔌 数据源接口
│   │   └── data_replay.py     # ⏯️ 数据回放控制器
│   ├── exchange/              # 🏛️ 虚拟交易所模块
│   │   ├── matching/          # ⚡ 撮合引擎
│   │   ├── account/           # 💰 账户管理
│   │   ├── rest_api/          # 🌐 REST API服务
│   │   ├── websocket/         # 📡 WebSocket服务
│   │   └── mock_exchange.py   # 🏛️ 虚拟交易所主类
│   ├── vnpy/                  # 🔌 vnpy集成模块
│   │   ├── gateways/          # vnpy网关实现
│   │   │   └── binance_spot.py # QTE Binance Gateway
│   │   ├── __init__.py        # vnpy可用性检查
│   │   └── data_source.py     # vnpy数据源适配器
│   ├── ml/                    # 🧠 机器学习策略
│   ├── portfolio/             # 📈 投资组合管理
│   ├── execution/             # ⚡ 执行系统
│   ├── analysis/              # 📊 回测分析
│   └── utils/                 # 🛠️ 工具函数
│
├── demo/                      # 🎬 演示模块
│   ├── comprehensive_demo.py  # 🌟 综合演示 (--mode all)
│   ├── ml_trading_demo.py     # 🧠 机器学习演示
│   ├── vnpy_integration_demo.py # 🔌 vnpy集成演示
│   ├── virtual_exchange_demo.py # 🏛️ 虚拟交易所演示
│   ├── datasource_ecosystem_demo.py # 🗄️ 数据源演示
│   └── visualization_report_demo.py # 📊 可视化报告演示
│
├── tests/                     # 🧪 测试代码 (97.93%覆盖率)
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── performance/           # 性能测试
│
├── demo_output/               # 📁 演示输出目录
├── demo_reports/              # 📊 HTML报告目录
├── demo_data/                 # 📄 演示数据目录
└── docs/                      # 📚 详细文档
```

## 🏗️ 技术架构

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

### 🔄 完整的数据流向

#### 📥 历史数据回测流程

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

## 🎓 学习路径

### 🌟 推荐学习顺序

1. **🎯 从综合演示开始** (5分钟)
   ```bash
   python run_qte_demo.py --mode all --verbose
   ```
   - 一键体验所有功能
   - 了解QTE的完整能力
   - 获得整体架构认知

2. **📊 理解基础概念** (10分钟)
   ```bash
   python run_qte_demo.py --mode simple
   python run_qte_demo.py --mode advanced
   ```
   - 学习量化交易基础
   - 理解事件驱动架构
   - 掌握回测流程

3. **🏛️ 深入交易所机制** (15分钟)
   ```bash
   python run_qte_demo.py --mode exchange
   ```
   - 理解撮合引擎原理
   - 学习订单生命周期
   - 掌握账户管理

4. **🧠 探索AI量化** (20分钟)
   ```bash
   python run_qte_demo.py --mode ml
   ```
   - 学习特征工程
   - 理解模型训练
   - 掌握AI策略开发

5. **🔌 集成实际框架** (10分钟)
   ```bash
   python run_qte_demo.py --mode vnpy
   ```
   - 学习vnpy集成
   - 理解Gateway模式
   - 掌握实盘对接

6. **🗄️ 掌握数据管理** (15分钟)
   ```bash
   python run_qte_demo.py --mode datasource
   ```
   - 学习多数据源管理
   - 理解数据质量控制
   - 掌握性能优化

7. **📊 生成专业报告** (5分钟)
   ```bash
   python run_qte_demo.py --mode report
   ```
   - 学习可视化分析
   - 理解报告生成
   - 掌握结果展示
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
python run_qte_demo.py --mode ml

# 查看特征工程和模型训练结果
# 所有ML功能都已集成到演示系统中
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！QTE是一个开源项目，依靠社区的力量不断改进。

### 🛠️ 开发环境设置

```bash
# 1. Fork并克隆项目
git clone https://github.com/YOUR_USERNAME/QTE.git
cd QTE

# 2. 创建开发环境
conda create -n qte-dev python=3.9
conda activate qte-dev

# 3. 安装开发依赖
pip install -r requirements.txt

# 4. 运行测试确保环境正常
python run_qte_demo.py --mode test
```

### 📝 提交规范

- **清晰的提交信息**: 使用描述性的提交信息
- **代码规范**: 遵循PEP 8和项目现有代码风格
- **测试覆盖**: 为新功能添加相应的测试
- **文档更新**: 更新相关文档和README

### 🐛 报告问题

在[GitHub Issues](https://github.com/MNS-Vic/QTE/issues)中报告bug时，请包含：
- 详细的问题描述
- 复现步骤
- 系统环境信息
- 错误日志和截图

### 💡 功能建议

我们欢迎新功能建议！请在Issues中详细描述：
- 功能的用途和价值
- 预期的实现方式
- 可能的替代方案

## 📊 项目统计

- **📈 测试覆盖率**: 97.93%
- **🧪 测试用例**: 468个
- **📦 核心模块**: 8个
- **🎬 演示模式**: 9种
- **⭐ GitHub Stars**: [点击查看](https://github.com/MNS-Vic/QTE)

## 🏆 项目亮点

### 🎯 完整性
- **端到端解决方案**: 从数据获取到策略执行的完整链路
- **生产就绪**: 高测试覆盖率和严格的代码质量控制
- **文档完善**: 详细的使用指南和API文档

### 🚀 先进性
- **现代化架构**: 事件驱动、异步处理、微服务设计
- **AI集成**: 机器学习特征工程和模型训练
- **专业可视化**: 深色主题的交互式分析报告

### 🔧 实用性
- **易于使用**: 一键安装和运行
- **高度可配置**: 灵活的配置系统
- **扩展性强**: 模块化设计，易于扩展

## 📄 许可证

本项目采用 **MIT许可证** - 详见 [LICENSE](LICENSE) 文件。

这意味着您可以：
- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发代码
- ✅ 私人使用

## 🙏 致谢

感谢以下开源项目和社区的支持：

- **[vnpy](https://github.com/vnpy/vnpy)** - 优秀的量化交易框架
- **[pandas](https://pandas.pydata.org/)** - 强大的数据分析库
- **[FastAPI](https://fastapi.tiangolo.com/)** - 现代化的API框架
- **[Plotly](https://plotly.com/)** - 交互式可视化库
- **[scikit-learn](https://scikit-learn.org/)** - 机器学习库

## 📞 联系我们

- 💬 **讨论**: [GitHub Discussions](https://github.com/MNS-Vic/QTE/discussions)
- 🐛 **问题**: [GitHub Issues](https://github.com/MNS-Vic/QTE/issues)
- 📧 **邮件**: [133777532+MNS-Vic@users.noreply.github.com](mailto:133777532+MNS-Vic@users.noreply.github.com)

---

<div align="center">

### 🌟 如果QTE对您有帮助，请给我们一个星标！

[![GitHub stars](https://img.shields.io/github/stars/MNS-Vic/QTE.svg?style=social&label=Star)](https://github.com/MNS-Vic/QTE)
[![GitHub forks](https://img.shields.io/github/forks/MNS-Vic/QTE.svg?style=social&label=Fork)](https://github.com/MNS-Vic/QTE)

**QTE - 让量化交易更简单、更专业、更强大！** 🚀

</div>