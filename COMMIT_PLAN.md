# Git提交计划

## 提交策略
将TDD实施的所有改动分为逻辑相关的多个提交，便于代码审查和版本管理。

## 提交顺序

### 1. 基础设施和配置
- `.coveragerc` - 覆盖率配置
- `.github/workflows/test-coverage.yml` - CI/CD流水线（如果存在）

### 2. 文档和培训材料
- `docs/TDD_TRAINING_GUIDE.md` - TDD培训指南
- `docs/TDD_QUICK_REFERENCE.md` - TDD快速参考
- `TDD_IMPLEMENTATION_SUMMARY.md` - TDD实施总结
- `TDD_PROGRESS_REPORT.md` - TDD进度报告

### 3. 核心代码修复和改进
- 修复发现的代码缺陷
- 改进代码质量和可维护性

### 4. 测试用例 - 第一批（核心模块）
- Portfolio相关测试
- OrderBook相关测试
- Strategy相关测试

### 5. 测试用例 - 第二批（数据和回测）
- Data Provider相关测试
- Backtester相关测试
- Time Manager相关测试

### 6. 测试用例 - 第三批（交易所和引擎）
- Virtual Exchange相关测试
- Mock Exchange相关测试
- Event Engine相关测试
- Engine Manager相关测试

### 7. 性能测试结果
- 性能测试报告和结果文件

## 提交信息模板

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- test: 测试相关
- refactor: 重构
- style: 代码格式
- ci: CI/CD相关
