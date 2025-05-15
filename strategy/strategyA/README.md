# 移动平均线交叉策略 (MA Cross Strategy)

本目录包含一个简单的移动平均线交叉策略实现，可用于量化回测引擎的测试和演示。

## 策略说明

该策略基于短期和长期移动平均线的交叉信号产生交易决策：

- 当短期均线上穿长期均线时产生买入信号（金叉）
- 当短期均线下穿长期均线时产生卖出信号（死叉）

这是一个经典的技术分析策略，适合初步了解量化交易系统的运作原理。

## 文件说明

- `ma_cross_strategy.py` - 移动平均线交叉策略实现
- `README.md` - 本说明文件

## 策略参数

- `short_window`: 短期移动平均线周期，默认为5天
- `long_window`: 长期移动平均线周期，默认为20天

## 使用方法

### 策略初始化

```python
from strategy.strategyA.ma_cross_strategy import MACrossStrategy

# 创建策略实例
strategy = MACrossStrategy(short_window=5, long_window=20)
```

### 数据处理

该策略实现了`on_bar`方法，可以逐条处理K线数据：

```python
# 处理新的K线数据
signal = strategy.on_bar(bar_data)

# signal包含交易动作和持仓状态
action = signal['action']  # 'BUY', 'SELL', 'CLOSE', 'HOLD'
position = signal['position']  # 1(多头), -1(空头), 0(空仓)
```

### 批量计算信号

如果已有一组历史数据，可以使用`calculate_signals`方法计算所有信号：

```python
import pandas as pd

# 历史数据
price_data = pd.DataFrame({
    'timestamp': [...],  # 时间戳
    'close': [...]       # 收盘价
})

# 计算信号
signals = strategy.calculate_signals(price_data)
```

## 回测方法

可以使用项目中的回测系统来测试该策略的表现：

```python
from test.test_ma_cross_strategy import run_backtest

# 运行回测
results = run_backtest(
    symbol="SHSE.000001",  # 回测品种
    start_date=datetime(2023, 1, 1),  # 回测起始日期
    end_date=datetime(2023, 12, 31),  # 回测结束日期
    short_window=5,  # 短期均线周期
    long_window=20,  # 长期均线周期
    initial_capital=100000.0  # 初始资金
)
```

回测结果包含以下指标：

- 总收益率
- 年化收益率
- 最大回撤
- 夏普比率
- 交易记录
- 净值曲线

## 性能优化建议

如果在实际应用中，可以考虑以下优化方向：

1. 使用向量化计算代替循环，提高性能
2. 添加止损止盈机制，控制风险
3. 考虑加入交易成本和滑点模型，更贴近实际
4. 增加信号过滤机制，减少假突破
5. 根据不同市场环境调整参数 