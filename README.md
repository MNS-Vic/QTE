# 量化回测引擎 (QTE)

一个高性能的量化回测框架，支持向量化和事件驱动两种回测方式，以及机器学习集成。

## 核心特性

- **双引擎架构**：同时支持高性能向量化回测和高真实度事件驱动回测
- **机器学习集成**：内置特征工程和模型管理，支持高频数据的机器学习回测
- **高性能设计**：向量化计算核心，比传统事件驱动框架快10-100倍
- **灵活性**：统一的API，通过引擎管理器无缝切换不同回测方式

## 项目结构

```
qte/
├── core/                  # 核心回测引擎模块
│   ├── vector_engine.py   # 向量化回测引擎
│   ├── event_engine.py    # 事件驱动回测引擎
│   └── engine_manager.py  # 引擎管理器，统一API
├── ml/                    # 机器学习模块
│   ├── features.py        # 特征工程
│   └── models.py          # 模型管理
├── data/                  # 数据处理模块
├── execution/             # 执行模块
├── portfolio/             # 投资组合管理
├── analysis/              # 回测分析
└── utils/                 # 工具函数

strategies/               # 策略实现
├── traditional/          # 传统交易策略
└── ml/                   # 机器学习策略

examples/                 # 使用示例
tests/                    # 测试集
docs/                     # 文档
```

## 快速开始

### 安装

```bash
pip install -e .
```

### 简单示例

```python
import pandas as pd
from qte.core import EngineManager, EngineType

# 创建双均线策略
class DualMaStrategy:
    def __init__(self, short_window=10, long_window=30):
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data):
        signals = data.copy()
        signals['short_ma'] = signals['close'].rolling(window=self.short_window).mean()
        signals['long_ma'] = signals['close'].rolling(window=self.long_window).mean()
        signals['signal'] = 0
        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1
        return signals

# 加载数据
data = pd.read_csv('your_data.csv')

# 创建策略
strategy = DualMaStrategy(short_window=10, long_window=30)

# 创建引擎管理器并运行回测
manager = EngineManager(engine_type=EngineType.VECTOR)
manager.add_strategy(strategy)
results = manager.run(data)

# 输出回测结果
print(results['metrics'])
```

## 向量化 vs 事件驱动

QTE框架支持两种回测方式，各有优势：

1. **向量化引擎**：
   - 基于NumPy和Pandas的高效向量化计算
   - 高性能，适合大规模参数优化和高频数据回测
   - 实现简单，代码量少

2. **事件驱动引擎**：
   - 真实市场事件流模拟
   - 高度灵活，支持复杂市场条件和订单类型
   - 更逼真的交易模拟

使用引擎管理器，您可以轻松切换这两种模式，甚至可以同时运行以进行比较。

## 机器学习集成

QTE框架提供了全面的机器学习工具链：

- **特征工程**：自动化的技术指标计算、特征提取和转换
- **模型管理**：训练、评估、保存和加载机器学习模型
- **高频数据处理**：针对高频交易数据的特殊特征

```python
from qte.ml import FeatureGenerator, ModelManager

# 特征工程
fg = FeatureGenerator()
data_with_features = fg.add_technical_indicators(data)
data_with_features = fg.add_high_frequency_features(data_with_features)

# 准备ML数据
X_train, X_test, y_train, y_test = fg.prepare_ml_data(
    data_with_features, 
    target='direction', 
    prediction_horizon=5,
    train_test_split=True
)

# 训练模型
mm = ModelManager()
model = mm.train_classifier(X_train, y_train, model_type='gradient_boosting')

# 评估模型
metrics = mm.evaluate(X_test, y_test)
print(metrics)

# 保存模型
mm.save_model('models/my_model.pkl')
```

## 开发计划

1. **数据接口扩展**：支持更多数据源
2. **高级策略模板**：提供更多预置策略模板
3. **性能优化**：进一步提升计算效率
4. **深度学习支持**：集成深度学习框架
5. **可视化工具**：增强分析和可视化能力

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。

## 许可证

MIT许可证 

## 数据源支持

本系统支持多种数据源，当前已实现：

1. **本地CSV数据源** (LocalCsvSource)
   - 从本地CSV文件加载数据
   - 支持自定义文件路径和列映射

2. **掘金量化数据源** (GmQuantSource)
   - 连接掘金量化API获取实时和历史数据
   - 支持股票、期货等多种品种
   - 包含K线、Tick和基本面数据

### 数据源使用示例

```python
from qte.data.sources.gm_quant import GmQuantSource
from qte.data.data_source_manager import get_data_source_manager

# 初始化掘金数据源
gm_source = GmQuantSource(token='your_token_here')
gm_source.connect()

# 注册到数据源管理器
dsm = get_data_source_manager()
dsm.register_source('gm', gm_source, make_default=True)

# 获取数据
data = dsm.get_bars(
    symbol='SHSE.600000',
    start_date='2023-01-01',
    end_date='2023-12-31',
    frequency='1d'
)
```

## 添加新的数据源

系统设计为可扩展的数据源架构，添加新的数据源只需实现以下接口：

1. 创建新的数据源类，实现标准接口：
   - `connect()`: 连接数据源
   - `get_symbols()`: 获取可用标的
   - `get_bars()`: 获取K线数据
   - `get_ticks()`: 获取Tick数据
   - `get_fundamentals()`: 获取基本面数据

2. 在数据源管理器中注册新的数据源

详细使用方法请参考 `test/data_provider/` 目录下的示例。 