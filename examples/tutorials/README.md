# QTE框架教程示例

本目录包含QTE量化交易引擎框架的完整教程示例，帮助用户快速上手并掌握框架的核心功能。

## 🎯 教程概览

### 完整工作流示例 (`complete_workflow_example.py`)

这是一个综合性的教程，展示了使用QTE框架进行量化交易的完整流程：

#### 📊 1. 数据获取
- 从CSV文件加载历史数据
- 使用DataSourceFactory管理多种数据源
- 生成模拟的OHLCV股票数据

#### 🧠 2. 策略定义
- 实现双均线交叉策略
- 策略信号生成逻辑
- 策略参数配置

#### ⚡ 3. 向量化回测
- 使用VectorEngine进行快速回测
- 配置初始资金和手续费
- 计算持仓和收益

#### 🏦 4. 虚拟交易所交互
- 事件驱动回测架构
- 订单生成和匹配
- 模拟真实交易环境

#### 📈 5. 结果分析
- 性能指标计算
- 风险指标评估
- 可视化报告生成

## 🚀 快速开始

### 环境要求

确保您已安装以下依赖：

```bash
pip install pandas numpy matplotlib scipy
```

### 运行教程

1. **导航到项目根目录**：
   ```bash
   cd /path/to/QTE
   ```

2. **运行完整工作流示例**：
   ```bash
   python examples/tutorials/complete_workflow_example.py
   ```

3. **查看生成的结果**：
   - 示例数据：`examples/tutorials/sample_data/`
   - 回测报告：`examples/tutorials/backtest_reports/`

## 📋 输出说明

运行示例后，您将看到：

### 控制台输出
- 📊 数据加载和处理信息
- 🔄 回测执行进度
- 📈 核心性能指标
- 💰 资金曲线变化

### 生成文件
- **CSV数据文件**：模拟的股票价格数据
- **HTML报告**：详细的回测分析报告
- **图表文件**：资金曲线、回撤分析等可视化图表
- **性能指标**：CSV格式的量化指标

## 📊 核心性能指标

教程将计算并展示以下关键指标：

| 指标类别 | 具体指标 | 说明 |
|---------|---------|------|
| **收益指标** | 总收益率 | 整个回测期间的总收益 |
| | 年化收益率 | 年化后的收益率 |
| **风险指标** | 最大回撤 | 资金曲线的最大回撤幅度 |
| | 夏普比率 | 风险调整后的收益率 |
| | 索提诺比率 | 下行风险调整后的收益率 |
| **交易指标** | 交易次数 | 总交易次数 |
| | 胜率 | 盈利交易占比 |
| | 盈亏比 | 平均盈利/平均亏损 |

## 🛠️ 自定义和扩展

### 修改策略参数

您可以轻松调整策略参数：

```python
# 修改移动平均线周期
strategy = DualMovingAverageStrategy(short_window=10, long_window=30)

# 修改回测参数
engine = VectorEngine(
    initial_capital=200000.0,  # 20万初始资金
    commission_rate=0.0005     # 0.05%手续费
)
```

### 使用真实数据

替换模拟数据为真实历史数据：

```python
# 使用CSV文件
data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)

# 或使用其他数据源
from qte.data.sources.gm_quant import GmQuantSource
gm_source = GmQuantSource(token='your_token')
data = gm_source.get_bars('SHSE.600000', '2022-01-01', '2023-12-31')
```

### 实现自定义策略

创建您自己的交易策略：

```python
class YourCustomStrategy:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
    
    def generate_signals(self, data):
        # 实现您的策略逻辑
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = your_logic(data)
        return signals
```

## 🔧 故障排除

### 常见问题

1. **导入错误**：
   ```
   ModuleNotFoundError: No module named 'qte'
   ```
   - 确保在项目根目录运行
   - 检查PYTHONPATH设置

2. **数据加载失败**：
   - 检查数据文件路径
   - 确认数据格式符合OHLCV标准

3. **图表生成失败**：
   ```bash
   pip install matplotlib seaborn
   ```

### 获取帮助

- 📖 查看详细文档：`docs/` 目录
- 🔍 参考其他示例：`examples/` 目录  
- 💬 提交Issues：项目GitHub页面

## 📚 进阶学习

完成本教程后，建议继续学习：

1. **高级策略开发**：
   - 多因子策略
   - 机器学习策略
   - 期货和期权策略

2. **风险管理**：
   - 投资组合优化
   - 风险预算管理
   - 实时风控系统

3. **实盘交易**：
   - 券商API集成
   - 订单管理系统
   - 监控和报警

4. **性能优化**：
   - 并行计算
   - 数据缓存策略
   - 内存管理优化

---

**Happy Trading! 🚀**

如有问题，请参考项目文档或联系开发团队。 