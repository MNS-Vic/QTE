# QTE用户使用指南

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pandas >= 1.5.3
- numpy >= 1.24.3

### 安装
```bash
# 克隆项目
git clone https://github.com/MNS-Vic/QTE.git
cd QTE

# 创建虚拟环境
conda create -n qte python=3.10
conda activate qte

# 安装依赖
pip install -r requirements-qte-tdd.txt
```

### 第一个回测示例
```python
from qte.core.engines import create_engine
import pandas as pd

# 1. 创建引擎
engine = create_engine('unified', {
    'initial_capital': 100000,
    'commission_rate': 0.001
})

# 2. 准备数据
data = pd.DataFrame({
    'datetime': pd.date_range('2023-01-01', periods=100),
    'open': [100 + i*0.1 for i in range(100)],
    'high': [105 + i*0.1 for i in range(100)],
    'low': [95 + i*0.1 for i in range(100)],
    'close': [103 + i*0.1 for i in range(100)],
    'volume': [1000] * 100
})

# 3. 创建简单策略
class SimpleStrategy:
    def generate_signals(self, data):
        signals = data.copy()
        signals['signal'] = 1  # 简单买入信号
        return signals

# 4. 运行回测
engine.set_data(data)
engine.add_strategy(SimpleStrategy())
result = engine.run_backtest()

print(f"回测结果: {result.success}")
print(f"最终收益: {engine.get_metrics()['total_return']:.2%}")
```

## 🏗️ 核心概念

### 1. 引擎类型
QTE提供多种引擎类型，适应不同需求：

#### 统一引擎 (推荐)
```python
# 自动模式 - 智能选择最优引擎
engine = create_engine('unified', {'compatibility_mode': 'auto'})

# V2高性能模式
engine = create_engine('unified', {'compatibility_mode': 'v2'})

# V1兼容模式
engine = create_engine('unified', {'compatibility_mode': 'v1'})
```

#### 专用引擎
```python
# V2高性能引擎 - 适合大数据集
from qte.core.engines import VectorEngineV2
engine = VectorEngineV2()

# V1兼容引擎 - 适合旧代码迁移
from qte.core.engines import VectorEngineV1Compat
engine = VectorEngineV1Compat()
```

### 2. 数据格式
QTE支持标准的OHLCV数据格式：

```python
# 必需列
required_columns = ['open', 'high', 'low', 'close', 'volume']

# 可选列
optional_columns = ['datetime', 'timestamp', 'symbol']

# 示例数据
data = pd.DataFrame({
    'datetime': pd.date_range('2023-01-01', periods=100),
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})
```

### 3. 策略开发
QTE支持多种策略开发方式：

#### 简单策略
```python
class MovingAverageStrategy:
    def __init__(self, short_window=10, long_window=30):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data):
        signals = data.copy()
        
        # 计算移动平均线
        signals['short_ma'] = signals['close'].rolling(self.short_window).mean()
        signals['long_ma'] = signals['close'].rolling(self.long_window).mean()
        
        # 生成信号
        signals['signal'] = 0
        signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
        signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1
        
        return signals
```

#### 高级策略
```python
class AdvancedStrategy:
    def __init__(self, **params):
        self.params = params
        self.indicators = {}
    
    def calculate_indicators(self, data):
        """计算技术指标"""
        self.indicators['rsi'] = self.calculate_rsi(data['close'])
        self.indicators['macd'] = self.calculate_macd(data['close'])
        return self.indicators
    
    def generate_signals(self, data):
        """生成交易信号"""
        signals = data.copy()
        indicators = self.calculate_indicators(data)
        
        # 多因子信号合成
        signals['signal'] = self.combine_signals(indicators)
        return signals
    
    def combine_signals(self, indicators):
        """信号合成逻辑"""
        # 实现复杂的信号合成逻辑
        pass
```

## 🔧 高级功能

### 1. 性能优化
根据数据规模选择合适的引擎：

```python
def choose_engine(data_size):
    """根据数据规模选择引擎"""
    if data_size < 1000:
        # 小数据集 - 使用自动模式
        return create_engine('unified', {'compatibility_mode': 'auto'})
    elif data_size < 10000:
        # 中等数据集 - 使用V2引擎
        return create_engine('v2', {'high_performance': True})
    else:
        # 大数据集 - 使用V2引擎 + 优化配置
        return create_engine('v2', {
            'high_performance': True,
            'batch_size': 10000,
            'parallel_processing': True
        })
```

### 2. 错误处理
QTE提供完善的错误处理机制：

```python
from qte.core.utils import ErrorHandler, safe_execute

# 创建错误处理器
error_handler = ErrorHandler("MyStrategy")

# 使用安全执行装饰器
@safe_execute(error_handler=error_handler)
def risky_strategy_operation():
    # 可能出错的策略操作
    pass

# 手动错误处理
try:
    result = engine.run_backtest()
except Exception as e:
    error_info = error_handler.handle_error(e)
    print(f"错误类型: {error_info['error_type']}")
    print(f"用户信息: {error_info['user_message']}")
    print(f"建议: {error_info['suggestions']}")
```

### 3. 事件系统
QTE支持事件驱动的策略开发：

```python
from qte.core.events import EventBus, MarketEvent

# 创建事件总线
event_bus = EventBus()

# 注册事件处理器
def on_market_data(event):
    print(f"收到市场数据: {event.symbol} - {event.close_price}")

event_bus.subscribe("MARKET", on_market_data)

# 发布事件
market_event = MarketEvent(
    symbol="AAPL",
    close_price=150.0,
    volume=1000000
)
event_bus.publish(market_event)
```

## 📊 性能监控

### 1. 基本指标
```python
# 获取引擎指标
metrics = engine.get_metrics()

print(f"总收益率: {metrics['total_return']:.2%}")
print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
print(f"最大回撤: {metrics['max_drawdown']:.2%}")
print(f"胜率: {metrics['win_rate']:.2%}")
```

### 2. 性能分析
```python
# 获取详细性能统计
performance = engine.get_performance_stats()

print(f"处理速度: {performance['throughput']:.0f} 行/秒")
print(f"内存使用: {performance['memory_usage']:.1f} MB")
print(f"执行时间: {performance['execution_time']:.2f} 秒")
```

### 3. 实时监控
```python
import time

def monitor_backtest(engine):
    """实时监控回测进度"""
    start_time = time.time()
    
    while engine.is_running():
        stats = engine.get_performance_stats()
        elapsed = time.time() - start_time
        
        print(f"进度: {stats['progress']:.1%}, "
              f"耗时: {elapsed:.1f}s, "
              f"速度: {stats['throughput']:.0f} 行/秒")
        
        time.sleep(1)
```

## 🛠️ 故障排除

### 常见问题

#### 1. 数据格式错误
```python
# 问题：数据列名不匹配
# 解决：标准化列名
def standardize_data(data):
    column_mapping = {
        'Open': 'open',
        'High': 'high', 
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    }
    return data.rename(columns=column_mapping)
```

#### 2. 内存不足
```python
# 问题：大数据集内存不足
# 解决：分批处理
def process_large_dataset(data, batch_size=10000):
    results = []
    for i in range(0, len(data), batch_size):
        batch = data.iloc[i:i+batch_size]
        result = engine.run_backtest_batch(batch)
        results.append(result)
    return combine_results(results)
```

#### 3. 性能问题
```python
# 问题：回测速度慢
# 解决：优化配置
engine = create_engine('v2', {
    'high_performance': True,
    'vectorized_operations': True,
    'parallel_processing': True,
    'cache_enabled': True
})
```

### 调试技巧

#### 1. 启用详细日志
```python
import logging

# 设置日志级别
logging.getLogger('QTE').setLevel(logging.DEBUG)

# 查看详细执行信息
engine.set_debug_mode(True)
```

#### 2. 性能分析
```python
import cProfile

# 性能分析
def profile_backtest():
    cProfile.run('engine.run_backtest()', 'backtest_profile.prof')

# 查看分析结果
# python -m pstats backtest_profile.prof
```

## 🎯 最佳实践

### 1. 数据准备
- 确保数据质量，处理缺失值和异常值
- 使用标准的OHLCV格式
- 合理设置数据频率和时间范围

### 2. 策略开发
- 从简单策略开始，逐步增加复杂度
- 充分测试策略的边界情况
- 使用向量化操作提高性能

### 3. 回测配置
- 根据数据规模选择合适的引擎
- 设置合理的手续费和滑点
- 考虑市场冲击和流动性约束

### 4. 结果分析
- 关注风险调整后收益
- 分析回撤和波动性
- 进行样本外测试验证

## 📞 技术支持

### 获取帮助
- **文档**: 查看完整技术文档
- **示例**: 参考demo示例代码
- **社区**: 加入QTE用户社区
- **问题反馈**: 提交GitHub Issues

### 联系方式
- **项目地址**: https://github.com/MNS-Vic/QTE
- **文档地址**: docs/
- **示例代码**: examples/

## 📖 API参考

### 核心引擎API

#### create_engine()
```python
def create_engine(engine_type: str, config: Dict[str, Any] = None) -> IBacktestEngine
```
创建回测引擎实例。

**参数**:
- `engine_type`: 引擎类型 ('unified', 'v1', 'v2', 'auto')
- `config`: 引擎配置字典

**返回**: 引擎实例

**示例**:
```python
engine = create_engine('unified', {
    'initial_capital': 100000,
    'commission_rate': 0.001,
    'compatibility_mode': 'auto'
})
```

#### UnifiedVectorEngine
```python
class UnifiedVectorEngine(IBacktestEngine)
```
统一向量化回测引擎。

**主要方法**:
- `initialize(config: Dict[str, Any]) -> bool`: 初始化引擎
- `set_data(data: pd.DataFrame) -> bool`: 设置回测数据
- `add_strategy(strategy) -> bool`: 添加交易策略
- `run_backtest() -> BacktestResult`: 运行回测
- `get_metrics() -> Dict[str, Any]`: 获取性能指标
- `reset() -> bool`: 重置引擎状态
- `cleanup() -> bool`: 清理资源

### 事件系统API

#### Event
```python
class Event:
    def __init__(self, event_type: str, **kwargs)
```
事件基类。

**属性**:
- `event_type`: 事件类型
- `timestamp`: 时间戳
- `event_id`: 事件ID
- `metadata`: 元数据字典

#### EventBus
```python
class EventBus:
    def subscribe(self, event_type: str, handler: Callable)
    def publish(self, event: Event)
    def unsubscribe(self, event_type: str, handler: Callable)
```

### 错误处理API

#### ErrorHandler
```python
class ErrorHandler:
    def handle_error(self, error: Exception) -> Dict[str, Any]
    def register_handler(self, exception_type: Type, handler: Callable)
    def register_recovery_strategy(self, error_code: str, strategy: Callable)
```

---

*QTE用户指南 v2.0*
*更新时间: 2025-06-20*
