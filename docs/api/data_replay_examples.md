# 数据重放控制器API使用指南

## 概述

数据重放控制器(DataReplayController)是QTE量化交易引擎的核心组件之一，用于控制数据的重放过程。本文档重点说明如何正确使用数据重放控制器的同步API和异步API。

## API类型

数据重放控制器提供两种API风格：

1. **同步API**：直接返回结果，适合简单应用场景和测试
   - `step_sync()` - 同步方式获取下一个数据点
   - `process_all_sync()` - 同步处理并返回所有数据点

2. **异步API**：基于线程和回调，适合复杂应用场景
   - `start()` - 启动异步处理
   - `stop()` - 停止异步处理  
   - `step()` - 手动步进(注意：step与异步模式的线程状态交互，两者不能混用)
   - 基于回调函数注册 - `register_callback(callback_func)`

## 同步API使用示例

### DataFrame控制器同步API示例

```python
import pandas as pd
from qte.data.data_replay import DataFrameReplayController, ReplayMode

# 创建测试数据
dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
data = {'price': [100, 101, 102, 103, 104], 'volume': [1000, 1100, 1200, 1300, 1400]}
df = pd.DataFrame(data, index=dates)

# 创建控制器
controller = DataFrameReplayController(df)

# 方法1: 使用step_sync逐个获取数据点
print("使用step_sync逐个获取数据点:")
while True:
    data_point = controller.step_sync()
    if data_point is None:
        break
    print(f"  时间: {data_point.name}, 价格: {data_point['price']}, 成交量: {data_point['volume']}")

# 重置控制器
controller.reset()

# 方法2: 使用process_all_sync一次获取所有数据
print("使用process_all_sync一次获取所有数据:")
all_data = controller.process_all_sync()
for i, data_point in enumerate(all_data):
    print(f"  第{i+1}条: 时间: {data_point.name}, 价格: {data_point['price']}")
```

### 多数据源控制器同步API示例

```python
import pandas as pd
from qte.data.data_replay import MultiSourceReplayController

# 创建价格数据
price_dates = pd.date_range(start='2023-01-01', periods=3, freq='D')
price_data = {'price': [100, 101, 102]}
price_df = pd.DataFrame(price_data, index=price_dates)

# 创建成交量数据(更频繁)
volume_dates = pd.date_range(start='2023-01-01', periods=6, freq='12h')
volume_data = {'volume': [1000, 1100, 1200, 1300, 1400, 1500]}
volume_df = pd.DataFrame(volume_data, index=volume_dates)

# 创建多数据源控制器
controller = MultiSourceReplayController({
    'price': price_df,
    'volume': volume_df
})

# 使用同步API处理所有数据
print("多数据源同步处理:")
all_data = controller.process_all_sync()

# 输出结果(按时间排序)
for i, data in enumerate(all_data):
    time_str = data.get('_timestamp', 'Unknown')
    if '_source' in data:
        source = data['_source']
        if source == 'price' and 'price' in data:
            print(f"  数据点{i+1}: 来源={source}, 时间={time_str}, 价格={data['price']}")
        elif source == 'volume' and 'volume' in data:
            print(f"  数据点{i+1}: 来源={source}, 时间={time_str}, 成交量={data['volume']}")
```

## 最佳实践

1. **避免API混用**：在同一控制器实例上，避免同时使用同步API和异步API

2. **选择正确的API**：
   - 测试和简单数据处理场景 → 使用同步API
   - 实时交易、界面交互场景 → 使用异步API

3. **同步API性能考虑**：
   - 处理大型数据集时，考虑启用内存优化选项 `memory_optimized=True`
   - 同步API没有速度控制，适合回测场景

4. **异步API注意事项**：
   - 确保注册回调函数后再启动控制器
   - 合理处理线程同步问题

## 排障指南

### 常见问题

1. **数据重放过快或过慢**
   - 检查是否使用了`speed_factor`参数
   - 确认使用的是正确的模式(ReplayMode)

2. **没有接收到数据**
   - 确认数据源不为空
   - 检查回调函数注册是否正确
   - 验证是否正确启动了控制器

3. **线程同步问题**
   - 避免混用同步和异步API
   - 使用`step_sync`和`process_all_sync`代替需要线程交互的方法

### 日志调试

启用详细日志可以帮助排查问题：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 兼容性说明

- 同步API在v1.2.0版本引入，用于解决之前版本中存在的线程同步问题
- 所有旧版本代码应更新为使用新的同步API，特别是在测试和数据处理场景中