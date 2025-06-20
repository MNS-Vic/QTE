# QTE故障排除指南

## 🚨 常见问题快速解决

### 安装和环境问题

#### 1. 依赖安装失败
**问题**: `pip install` 失败或依赖冲突

**解决方案**:
```bash
# 使用指定版本的依赖
pip install pandas==1.5.3 numpy==1.24.3

# 清理缓存重新安装
pip cache purge
pip install -r requirements-qte-tdd.txt

# 使用conda环境
conda create -n qte python=3.10
conda activate qte
pip install -r requirements-qte-tdd.txt
```

#### 2. Python版本兼容性
**问题**: Python版本不兼容

**解决方案**:
```bash
# 检查Python版本
python --version

# 推荐使用Python 3.10
conda install python=3.10
```

### 数据相关问题

#### 1. 数据格式错误
**问题**: `KeyError: 'close'` 或列名不匹配

**解决方案**:
```python
# 检查数据格式
print(data.columns.tolist())
print(data.head())

# 标准化列名
def fix_column_names(data):
    column_mapping = {
        'Open': 'open', 'HIGH': 'high', 'Low': 'low',
        'Close': 'close', 'VOLUME': 'volume',
        'Date': 'datetime', 'Timestamp': 'datetime'
    }
    return data.rename(columns=column_mapping)

data = fix_column_names(data)
```

#### 2. 数据类型问题
**问题**: `TypeError: unsupported operand type(s)`

**解决方案**:
```python
# 确保数值列为数值类型
numeric_columns = ['open', 'high', 'low', 'close', 'volume']
for col in numeric_columns:
    if col in data.columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')

# 处理时间列
if 'datetime' in data.columns:
    data['datetime'] = pd.to_datetime(data['datetime'])
```

#### 3. 缺失数据处理
**问题**: `ValueError: Input contains NaN`

**解决方案**:
```python
# 检查缺失值
print(data.isnull().sum())

# 处理缺失值
# 方法1: 删除含有缺失值的行
data = data.dropna()

# 方法2: 前向填充
data = data.fillna(method='ffill')

# 方法3: 插值
data = data.interpolate()
```

### 引擎相关问题

#### 1. 引擎初始化失败
**问题**: `EngineError: 引擎初始化失败`

**解决方案**:
```python
# 检查配置参数
config = {
    'initial_capital': 100000,  # 必须 > 0
    'commission_rate': 0.001,   # 必须 >= 0
}

# 使用错误处理
from qte.core.utils import ErrorHandler
error_handler = ErrorHandler("Engine")

try:
    engine = create_engine('unified', config)
    success = engine.initialize(config)
    if not success:
        print("引擎初始化失败，请检查配置")
except Exception as e:
    error_info = error_handler.handle_error(e)
    print(f"错误: {error_info['user_message']}")
    print(f"建议: {error_info['suggestions']}")
```

#### 2. 策略添加失败
**问题**: `ValueError: 无效的策略对象`

**解决方案**:
```python
# 确保策略类有必需的方法
class ValidStrategy:
    def generate_signals(self, data):
        """必需方法：生成交易信号"""
        signals = data.copy()
        signals['signal'] = 0  # 添加信号列
        return signals

# 检查策略对象
strategy = ValidStrategy()
if hasattr(strategy, 'generate_signals'):
    engine.add_strategy(strategy)
else:
    print("策略缺少generate_signals方法")
```

### 性能问题

#### 1. 回测速度慢
**问题**: 大数据集回测耗时过长

**解决方案**:
```python
# 1. 选择高性能引擎
engine = create_engine('v2', {
    'high_performance': True,
    'vectorized_operations': True
})

# 2. 数据预处理
def optimize_data(data):
    # 减少数据精度
    float_cols = data.select_dtypes(include=['float64']).columns
    data[float_cols] = data[float_cols].astype('float32')
    
    # 设置索引
    if 'datetime' in data.columns:
        data = data.set_index('datetime')
    
    return data

data = optimize_data(data)

# 3. 分批处理大数据集
def process_large_dataset(data, batch_size=50000):
    if len(data) <= batch_size:
        return engine.run_backtest()
    
    results = []
    for i in range(0, len(data), batch_size):
        batch = data.iloc[i:i+batch_size]
        engine.set_data(batch)
        result = engine.run_backtest()
        results.append(result)
    
    return combine_results(results)
```

#### 2. 内存使用过高
**问题**: `MemoryError` 或系统内存不足

**解决方案**:
```python
import gc
import psutil

# 监控内存使用
def monitor_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"内存使用: {memory_mb:.1f} MB")

# 内存优化策略
def optimize_memory():
    # 1. 及时清理
    engine.cleanup()
    gc.collect()
    
    # 2. 使用内存映射
    data = pd.read_csv('large_file.csv', 
                       dtype={'close': 'float32'},
                       chunksize=10000)
    
    # 3. 删除不需要的列
    data = data[['open', 'high', 'low', 'close', 'volume']]

monitor_memory()
```

### 错误诊断

#### 1. 启用调试模式
```python
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('QTE')

# 引擎调试模式
engine.set_debug_mode(True)

# 查看详细错误信息
try:
    result = engine.run_backtest()
except Exception as e:
    logger.exception("回测失败")
    print(f"错误详情: {str(e)}")
```

#### 2. 性能分析
```python
import cProfile
import time

# 性能分析
def profile_backtest():
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = engine.run_backtest()
    end_time = time.time()
    
    profiler.disable()
    profiler.dump_stats('backtest_profile.prof')
    
    print(f"执行时间: {end_time - start_time:.2f}秒")
    return result

# 查看分析结果
# python -m pstats backtest_profile.prof
```

#### 3. 内存分析
```python
from memory_profiler import profile

@profile
def memory_test():
    engine = create_engine('unified')
    engine.initialize({'initial_capital': 100000})
    engine.set_data(data)
    result = engine.run_backtest()
    return result

# 运行内存分析
# python -m memory_profiler script.py
```

## 🔧 高级故障排除

### 1. 并发问题
**问题**: 多线程环境下的竞态条件

**解决方案**:
```python
import threading

# 使用线程锁
lock = threading.Lock()

def thread_safe_backtest():
    with lock:
        result = engine.run_backtest()
    return result

# 或者为每个线程创建独立引擎
def create_thread_engine():
    return create_engine('unified', {
        'initial_capital': 100000,
        'thread_safe': True
    })
```

### 2. 数据一致性问题
**问题**: 数据在处理过程中被修改

**解决方案**:
```python
# 创建数据副本
def safe_data_processing(data):
    data_copy = data.copy()
    engine.set_data(data_copy)
    return engine.run_backtest()

# 使用不可变数据
def freeze_data(data):
    return data.copy().set_flags(write=False)
```

### 3. 版本兼容性问题
**问题**: 不同版本API不兼容

**解决方案**:
```python
# 检查版本
import qte
print(f"QTE版本: {qte.__version__}")

# 使用兼容性检查
from qte.core.engines.migration_tools import CompatibilityChecker

checker = CompatibilityChecker()
report = checker.check_compatibility(strategy_code)
if report.compatibility_score < 0.8:
    print("需要迁移到新版本API")
    print(report.migration_suggestions)
```

## 📞 获取帮助

### 自助诊断
1. **检查日志**: 查看详细的错误日志
2. **验证数据**: 确保数据格式正确
3. **测试配置**: 使用最小配置测试
4. **查看文档**: 参考API文档和示例

### 社区支持
- **GitHub Issues**: 提交bug报告和功能请求
- **讨论区**: 参与技术讨论
- **示例代码**: 查看官方示例

### 报告问题
提交问题时请包含：
1. **错误信息**: 完整的错误堆栈
2. **环境信息**: Python版本、依赖版本
3. **重现步骤**: 最小化的重现代码
4. **数据样本**: 脱敏的数据样本

```python
# 环境信息收集脚本
def collect_env_info():
    import sys
    import pandas as pd
    import numpy as np
    
    print(f"Python版本: {sys.version}")
    print(f"Pandas版本: {pd.__version__}")
    print(f"Numpy版本: {np.__version__}")
    print(f"QTE版本: {qte.__version__}")
    
    # 系统信息
    import platform
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    # 内存信息
    import psutil
    memory = psutil.virtual_memory()
    print(f"总内存: {memory.total / 1024**3:.1f} GB")
    print(f"可用内存: {memory.available / 1024**3:.1f} GB")

collect_env_info()
```

---

*QTE故障排除指南 v2.0*  
*更新时间: 2025-06-20*
