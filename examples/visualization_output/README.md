# QTE框架可视化报告演示

## 📊 演示结果

这个目录包含了QTE框架可视化功能的完整演示结果。

### 🎯 演示策略
- **策略名称**: 双均线策略演示
- **回测期间**: 2023-01-01 至 2023-12-31
- **初始资金**: ¥100,000
- **最终资金**: ¥203,536

### 📈 核心指标
- **总收益率**: 103.54%
- **年化收益率**: 63.34%
- **年化波动率**: 39.20%
- **夏普比率**: 1.6158
- **最大回撤**: -10.26%
- **胜率**: 51.78%

### 📁 生成的文件

#### 1. 📄 HTML报告
- **文件**: `visualization_report.html`
- **描述**: 完整的HTML格式回测报告
- **功能**: 
  - 响应式设计，支持各种设备
  - 美观的指标卡片展示
  - 嵌入式图表显示
  - 详细的统计表格

#### 2. 📊 策略完整分析图
- **文件**: `strategy_overview.png`
- **描述**: 2x2布局的综合分析图表
- **包含内容**:
  - 价格走势与交易信号
  - 资金曲线
  - 回撤分析
  - 收益分布直方图

#### 3. 📈 资金曲线详细图
- **文件**: `equity_curve.png`
- **描述**: 单独的资金曲线图，包含详细统计信息
- **特点**:
  - 高分辨率图表
  - 内嵌关键指标
  - 专业的图表样式

## 🚀 如何使用

### 查看HTML报告
```bash
# 在浏览器中打开
open visualization_report.html
```

### 查看图片文件
```bash
# 查看策略概览图
open strategy_overview.png

# 查看资金曲线图
open equity_curve.png
```

## 🎨 QTE框架可视化功能特点

### ✅ 支持的图表类型
1. **资金曲线图** - 展示策略资金变化
2. **回撤分析图** - 显示最大回撤和回撤恢复
3. **收益分布图** - 日收益率分布直方图
4. **月度收益热图** - 月度收益表现
5. **交易信号图** - 价格走势与买卖点
6. **风险指标图** - 各种风险度量指标

### ✅ 支持的输出格式
1. **PNG图片** - 高分辨率图表文件
2. **HTML报告** - 交互式网页报告
3. **PDF报告** - 专业打印格式
4. **Excel报告** - 数据表格格式

### ✅ 核心功能
1. **自动化生成** - 一键生成完整报告
2. **模板化设计** - 专业的报告模板
3. **响应式布局** - 适配各种屏幕尺寸
4. **中文支持** - 完整的中文界面
5. **数据导出** - 支持多种格式导出

## 💡 扩展使用

### 自定义可视化
```python
from qte.analysis.backtest_report import BacktestReport

# 创建报告生成器
report = BacktestReport(
    strategy_name="我的策略",
    results=backtest_results,
    metrics=performance_metrics,
    trades=trade_records
)

# 生成各种图表
equity_fig = report.plot_equity_curve()
drawdown_fig = report.plot_drawdown()
monthly_fig = report.plot_monthly_returns()

# 保存HTML报告
report.save_report_html("my_report.html")
```

### 批量报告生成
```python
# 为多个策略生成报告
strategies = ["策略A", "策略B", "策略C"]
for strategy in strategies:
    report = BacktestReport(strategy_name=strategy, ...)
    report.generate_full_report(f"reports/{strategy}")
```

## 📚 相关文档

- [QTE框架文档](../../docs/)
- [API参考](../../docs/api/)
- [使用教程](../../docs/tutorials/)
- [示例代码](../)

---

🎉 **QTE框架** - 专业的量化交易引擎，让量化投资更简单！ 