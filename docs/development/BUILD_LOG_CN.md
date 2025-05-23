# 量化回测引擎构建日志

本文档记录了量化回测引擎在构建 (BUILD) 模式下的主要步骤和进展。

## 项目阶段: 0 - 项目设置与核心基础设施 (已完成回顾)

*   **任务 0.1:** 初始化 Git 仓库，定义项目结构，设置虚拟环境 - **已完成**
*   **任务 0.2:** 配置 Linter (Flake8, Black) 和测试框架 (Pytest) - **已完成**
*   **任务 0.3:** 定义核心事件类 (`qte_core/events.py`) - **已完成** (注释已翻译，手动修复了末尾标签问题)
*   **任务 0.4:** 实现基础的 `BE_EventLoop` (`qte_core/event_loop.py`) - **已完成** (注释已翻译)
*   **任务 0.5:** 设置基础日志基础设施 (`qte_analysis_reporting/logger.py`) - **已完成** (文档字符串已翻译，行内注释翻译未完全生效)
*   **任务 0.6:** 定义关键组件的基础接口 - **已完成** (文档字符串已翻译，行内注释翻译未完全生效)
    *   `qte_data/interfaces.py`
    *   `qte_strategy/interfaces.py`
    *   `qte_execution/interfaces.py`
    *   `qte_portfolio_risk/interfaces.py`

---

## 项目阶段: 1 - MVP (最小可行产品) 实现

### 任务 1.1: 实现基础的CSV数据提供者 (`DP_CSVReader`)

*   **状态:** **已完成** (已重构以支持多品种时间排序流式传输)
*   **文件:** `qte_data/csv_data_provider.py`
*   **描述:** 创建了一个继承自 `DataProvider` 的 `CSVDataProvider` 类。该类能够从指定的CSV文件目录（每个合约一个文件，文件名即合约代码）加载OHLCV数据，并将所有合约的数据按时间戳全局排序后进行流式传输。它实现了 `get_historical_bars`, `get_latest_bar`, `get_latest_bars` 方法。包含基本的错误处理和日志记录，以及一个 `if __name__ == '__main__':` 测试块。

### 任务 1.2: 实现一个简单的示例策略 (`ST_MovingAverageCross`)

*   **状态:** **已完成** (基本实现)
*   **文件:** `qte_strategy/example_strategies.py`
*   **描述:** 创建了一个继承自 `Strategy` 的 `MovingAverageCrossStrategy` 类。该策略通过短长期移动平均线的交叉来生成买入/卖出信号 (`SignalEvent`)。策略内部维护价格序列，使用Pandas计算SMA，并在交叉发生时通过事件循环发送信号。构造函数接收一个 `DataProvider` 实例用于获取历史数据。包含一个 `if __name__ == '__main__':` 块用于基本测试。

### 任务 1.3: 实现一个基础的投资组合 (`PF_BasePortfolio`)

*   **状态:** **已完成** (已添加 `print_summary` 方法)
*   **文件:** `qte_portfolio_risk/base_portfolio.py`
*   **描述:** 创建了一个继承自 `Portfolio` 的 `BasePortfolio` 类。它能够处理 `SignalEvent` 生成 `OrderEvent`（基于固定数量或资产百分比的简单头寸管理，需要 `DataProvider` 获取价格），处理 `FillEvent` 更新持仓和现金（包括已实现盈亏和佣金计算），并根据 `MarketEvent` 更新持仓市值和未实现盈亏。实现了获取持仓、市值、投资组合快照和可用现金等方法。新增了 `print_summary()` 方法用于回测结束时输出摘要。包含一个 `if __name__ == '__main__':` 块用于基本功能测试。

### 任务 1.4: 实现一个基础的模拟经纪商 (`EX_BasicBroker`)

*   **状态:** **已完成** (基本实现)
*   **文件:** `qte_execution/basic_broker.py`
*   **描述:** 创建了一个继承自 `qte_execution.interfaces.BrokerSimulator` 的 `BasicBroker` 类，并同时在该文件中定义了简单的 `FixedPercentageCommission` 和 `SimpleRandomSlippage` 模型。`BasicBroker` 处理市价 `OrderEvent`，使用注入的佣金和滑点模型，并通过注入的 `DataProvider` 获取最新价格来模拟成交，最终生成 `FillEvent`。包含一个 `if __name__ == '__main__':` 块用于基本功能测试。

### 任务 1.5: 实现一个基础的回测编排器 (`BE_Backtester`)

*   **状态:** **已完成**
*   **文件:** `qte_core/backtester.py`
*   **描述:** 创建了 `BE_Backtester` 类，负责协调整个回测流程。它在初始化时接收事件循环、数据提供者、策略、投资组合和模拟经纪商的实例。通过 `_register_event_handlers` 方法注册必要的事件处理器。`run_backtest` 方法首先命令数据提供者流式传输所有市场数据到事件队列，然后进入一个主循环，从事件队列中获取事件并使用事件循环的调度逻辑进行处理，直到队列为空且无新事件生成。回测结束后，调用投资组合的 `print_summary` 方法输出结果。文件中包含一个 `if __name__ == '__main__':` 块，用于实例化所有MVP组件并运行一个完整的端到端回测示例，使用 `myquant_data` 目录下的 `TEST_SYM_A.csv` 和 `TEST_SYM_B.csv` (或在测试代码中指定的符号) 作为数据源。

## 2023-05-20：数据缓存系统实现

### 1. 设计并实现了分层缓存架构

完成了高效的内存和磁盘双层缓存系统（`DataCache`类），支持以下功能：

- 内存缓存：实现快速访问常用数据
- 磁盘缓存：持久存储大量数据
- 自动过期机制：基于时间的缓存失效
- 容量管理：限制内存项数和磁盘空间使用
- 缓存统计：监控缓存使用情况

```python
class DataCache:
    def __init__(self, cache_dir=None, max_memory_items=100, max_disk_size_mb=1000):
        """初始化缓存"""
        self._memory_cache = {}  # 内存缓存
        self._max_memory_items = max_memory_items
        # ...设置磁盘缓存目录和限制...
        
    def get(self, key: str) -> Any:
        """获取缓存数据，优先从内存获取，不存在则从磁盘获取"""
        
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """同时设置内存和磁盘缓存"""
        
    def clear(self, pattern: Optional[str] = None) -> int:
        """清除缓存，支持模式匹配"""
```

### 2. 将缓存集成到数据源框架

更新了`BaseDataSource`基类，使所有数据源都能轻松使用缓存功能：

- 添加了缓存控制参数
- 实现了缓存键生成策略
- 根据数据类型调整缓存过期时间
- 提供了带缓存的数据获取方法

```python
class BaseDataSource(DataSourceInterface):
    def __init__(self, use_cache: bool = True, **kwargs):
        """初始化数据源，可选启用缓存"""
        self._use_cache = use_cache
        self._cache = None
        
        # 如果启用缓存，获取缓存实例
        if self._use_cache:
            # ...获取或创建缓存实例...
    
    def get_bars_with_cache(self, symbol: str, 
                          start_date=None, end_date=None, 
                          frequency: str = '1d', **kwargs):
        """带缓存的K线获取"""
        # 检查缓存
        # 缓存未命中则从数据源获取
        # 更新缓存并返回数据
```

### 3. 编写了完整的单元测试

编写了全面的`test_data_cache.py`，测试缓存的各种功能和边界情况：

- 基本的设置和获取功能
- 缓存过期机制
- 内存缓存容量限制
- 缓存清除功能
- 模式匹配
- 磁盘缓存功能
- 缓存统计信息

### 4. 更新了模块初始化文件

更新了`qte/data/__init__.py`，添加了缓存相关导入和单例获取功能：

```python
from .data_cache import DataCache

# 创建一个方便获取缓存单例实例的函数
_data_cache_instance = None
def get_data_cache():
    """获取数据缓存的单例实例"""
    global _data_cache_instance
    if _data_cache_instance is None:
        _data_cache_instance = DataCache()
    return _data_cache_instance
```

这些实现完成了数据源架构优化的重要部分，使系统能够高效处理和复用数据，减少重复请求，提高性能。下一步将集成数据重放控制器，实现更丰富的回测场景支持。

## 2023-05-15：数据源架构优化实施

### 1. 完成数据源接口与基类

按照架构优化方案，我们成功实现了数据源接口和基类，为所有数据源定义了统一的接口规范：

```python
class DataSourceInterface(abc.ABC):
    @abc.abstractmethod
    def connect(self, **kwargs) -> bool:
        """连接到数据源"""
        pass
        
    @abc.abstractmethod
    def get_symbols(self, market: Optional[str] = None, **kwargs) -> List[str]:
        """获取可用标的列表"""
        pass
        
    @abc.abstractmethod
    def get_bars(self, symbol: str, ...) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        pass
```

同时提供了基础实现类`BaseDataSource`，实现了一些通用功能，简化了具体数据源的开发工作。

### 2. 实现数据源工厂

实现了`DataSourceFactory`类，支持以下功能：
- 通过类型名称创建数据源实例
- 注册自定义数据源创建函数
- 自动发现并注册数据源类
- 大小写不敏感的数据源类型识别

```python
# 使用示例
csv_source = DataSourceFactory.create('csv', base_path='data/path/')
gm_source = DataSourceFactory.create('gm', token='your_token')
```

### 3. 开发数据处理器

实现了强大的数据处理功能，支持以下操作：
- 数据重采样（如1分钟转5分钟、日线转周线）
- 多数据源的时间对齐
- 缺失数据填充
- 价格前/后复权处理

```python
# 使用示例 
# 将1分钟数据重采样为5分钟数据
five_min_data = DataProcessor.resample(
    one_min_data, 
    source_freq='1min', 
    target_freq='5min'
)

# 对齐多个数据源
aligned_data = DataProcessor.align_multiple({
    'stock_a': df_a, 
    'stock_b': df_b
})
```

### 4. 编写单元测试和文档

完成了数据源工厂和数据处理器的单元测试，验证了功能正确性：
- `test_data_factory.py`：测试数据源工厂的创建、注册等功能
- `test_data_processor.py`：测试数据处理器的重采样、对齐等功能

编写了详细的API文档：
- `data_source_interface.md`：数据源接口的详细说明和使用示例

## 2023-05-10：双引擎回测框架基础功能完成

- 实现了向量化引擎和事件驱动引擎的基础功能
- 完成了引擎管理器，可以选择使用哪种回测引擎
- 实现了基础数据获取模块，支持从CSV文件读取数据
- 实现了双均线策略的样例代码 

## 2023-05-21 数据重放控制器实现

### 完成任务
- 设计并实现了数据重放控制器接口 (`DataReplayInterface`)
- 实现了基础数据重放控制器 (`BaseDataReplayController`)
- 开发了基于DataFrame的数据重放控制器 (`DataFrameReplayController`)
- 实现了多数据源重放控制器 (`MultiSourceReplayController`)
- 添加了各种重放模式支持 (回测、步进、实时、加速)
- 实现了暂停/恢复功能
- 开发了速度控制机制
- 添加了回调注册/注销功能
- 编写了完整的单元测试和示例脚本

### 技术细节
- 使用线程安全的设计，支持并发操作
- 实现了基于事件的模型，通过回调机制通知数据变化
- 提供了灵活的时间戳提取和延迟计算逻辑
- 多数据源重放控制器支持按时间排序处理来自不同数据源的数据点
- 所有重放控制器都支持状态管理和异常处理

### 下一步计划
- 集成数据重放控制器到引擎管理器
- 添加更多的数据源适配器
- 实现更高级的事件过滤和处理机制

## 2023-05-15 缓存系统实现完成

### 完成任务
- 完成了分层缓存架构设计与实现
- 实现了内存缓存组件，支持LRU策略
- 开发了磁盘缓存组件，支持数据持久化
- 添加了缓存键生成策略
- 实现了缓存过期管理
- 增加了缓存统计与监控功能
- 将缓存系统集成到数据源基类中
- 编写了完整的单元测试

### 技术细节
- 使用装饰器模式实现缓存功能
- 采用哈希函数生成缓存键，支持复杂参数
- 使用JSON进行序列化/反序列化以支持磁盘缓存
- 实现了线程安全的访问机制
- 添加了模式匹配的缓存清除功能
- 增加了缓存命中率和使用统计监控

### 下一步计划
- 优化大数据量处理性能
- 增加更多的缓存策略选项
- 实现分布式缓存支持

## 2023-05-08 数据处理器开发完成

### 完成任务
- 实现了数据预处理功能
- 开发了数据重采样组件
- 完成了缺失数据处理功能
- 实现了价格复权处理
- 创建了数据转换器接口
- 添加了后处理钩子支持
- 编写了相关测试用例

### 技术细节
- 使用策略模式实现不同的数据处理算法
- 利用pandas提供的高性能数据操作
- 支持自定义处理链配置
- 实现了处理器的懒加载评估

### 下一步计划
- 实现数据缓存系统
- 优化大数据量处理性能
- 增加更多专业处理器

## 2023-05-01 数据源架构设计完成

### 完成任务
- 定义了统一的数据源接口 (DataSourceInterface)
- 实现了数据源基类 (BaseDataSource)
- 创建了数据源工厂类 (DataSourceFactory)
- 开发了本地CSV数据源和掘金数据源
- 设计了数据源管理器

### 技术细节
- 使用工厂模式创建数据源实例
- 采用策略模式处理不同的数据格式
- 实现了数据源自动注册机制
- 添加了异常处理和日志记录

### 下一步计划
- 实现数据处理功能
- 开发缓存系统
- 扩展更多数据源支持 