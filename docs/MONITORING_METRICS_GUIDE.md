# QTE监控指标指南

## 📊 概述

本指南详细说明QTE量化交易引擎的所有监控指标，包括指标含义、正常范围、异常阈值和响应流程。

## 🎯 监控指标分类

### 1. 业务指标 (Business Metrics)

#### 1.1 交易相关指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `qte_trades_total` | 总交易笔数 | 根据策略而定 | 1小时内<10笔 | 检查策略状态 |
| `qte_trading_volume_total` | 总交易量 | 根据市场而定 | 异常偏低/偏高 | 检查市场数据 |
| `qte_orders_total` | 总订单数 | 正常交易时段>0 | 30分钟内=0 | 检查订单系统 |
| `qte_orders_rejected_total` | 被拒绝订单数 | <5% | >10% | 检查风控规则 |

**响应流程**:
```
1. 检查策略运行状态
2. 验证市场数据连接
3. 检查风控参数设置
4. 联系交易团队确认
```

#### 1.2 投资组合指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `qte_portfolio_total_value` | 投资组合总价值 | 根据初始资金 | 偏离>20% | 立即检查持仓 |
| `qte_portfolio_pnl` | 投资组合盈亏 | 根据策略预期 | 日损失>5% | 风险控制检查 |
| `qte_portfolio_risk_exposure` | 风险敞口 | <风险限制 | >风险限制 | 立即减仓 |
| `qte_open_positions` | 开放持仓数 | 根据策略 | 异常增加 | 检查策略逻辑 |

**响应流程**:
```
1. 验证持仓数据准确性
2. 检查价格数据是否异常
3. 评估风险敞口合理性
4. 必要时执行风控措施
```

#### 1.3 策略指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `qte_strategy_pnl` | 策略盈亏 | 根据历史表现 | 连续亏损>阈值 | 暂停策略 |
| `qte_strategy_sharpe_ratio` | 夏普比率 | >0.5 | <0.3 | 策略优化 |
| `qte_strategy_win_rate` | 胜率 | 根据策略类型 | 显著下降 | 策略检查 |

### 2. 系统指标 (System Metrics)

#### 2.1 应用性能指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `qte_event_processing_rate` | 事件处理速率 | >1000/秒 | <500/秒 | 性能优化 |
| `qte_event_queue_size` | 事件队列长度 | <1000 | >5000 | 清理队列 |
| `qte_request_duration_seconds` | 请求响应时间 | <100ms | >1秒 | 性能调优 |
| `qte_memory_usage_bytes` | 内存使用量 | <80% | >90% | 内存优化 |

**响应流程**:
```
1. 检查系统资源使用情况
2. 分析性能瓶颈
3. 优化代码或增加资源
4. 监控改进效果
```

#### 2.2 基础设施指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `node_cpu_seconds_total` | CPU使用率 | <70% | >85% | 资源扩容 |
| `node_memory_MemAvailable_bytes` | 可用内存 | >20% | <10% | 内存清理 |
| `node_filesystem_avail_bytes` | 可用磁盘空间 | >20% | <10% | 磁盘清理 |
| `node_network_receive_bytes_total` | 网络接收字节 | 正常波动 | 异常峰值 | 网络检查 |

### 3. 数据质量指标 (Data Quality Metrics)

#### 3.1 市场数据指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `qte_last_market_data_timestamp` | 最后数据时间戳 | <5分钟前 | >5分钟前 | 检查数据源 |
| `qte_data_feed_connected` | 数据源连接状态 | 1 (连接) | 0 (断开) | 重连数据源 |
| `qte_price_anomalies_total` | 价格异常数量 | <1% | >5% | 数据验证 |
| `qte_market_data_latency_seconds` | 数据延迟 | <100ms | >1秒 | 网络优化 |

**响应流程**:
```
1. 检查数据源连接状态
2. 验证网络连接质量
3. 检查数据处理逻辑
4. 联系数据提供商
```

### 4. 安全指标 (Security Metrics)

#### 4.1 访问安全指标

| 指标名称 | 描述 | 正常范围 | 告警阈值 | 响应流程 |
|---------|------|----------|----------|----------|
| `qte_auth_failures_total` | 认证失败次数 | <10/小时 | >50/小时 | 安全检查 |
| `qte_suspicious_requests_total` | 可疑请求数 | 0 | >0 | 安全分析 |
| `nginx_http_requests_total` | HTTP请求总数 | 正常业务量 | 异常峰值 | DDoS检查 |

**响应流程**:
```
1. 分析安全日志
2. 检查IP来源
3. 实施安全措施
4. 通知安全团队
```

## 🚨 告警响应流程

### 1. P0级别告警 (关键)

**触发条件**:
- 系统完全不可用
- 数据丢失风险
- 安全漏洞

**响应流程**:
```
1. 立即响应 (5分钟内)
2. 通知所有相关人员
3. 启动应急预案
4. 实施临时解决方案
5. 根本原因分析
6. 永久修复
7. 事后总结
```

**联系人**:
- 技术负责人: +86-xxx-xxxx-xxxx
- 运维负责人: +86-xxx-xxxx-xxxx
- 业务负责人: +86-xxx-xxxx-xxxx

### 2. P1级别告警 (高)

**触发条件**:
- 核心功能受影响
- 性能严重下降
- 数据质量问题

**响应流程**:
```
1. 15分钟内响应
2. 通知值班工程师
3. 诊断问题原因
4. 实施修复措施
5. 监控修复效果
6. 更新文档
```

### 3. P2级别告警 (中)

**触发条件**:
- 部分功能受影响
- 性能轻微下降
- 非关键组件故障

**响应流程**:
```
1. 1小时内响应
2. 通知运维团队
3. 计划修复时间
4. 实施修复
5. 验证修复效果
```

### 4. P3级别告警 (低)

**触发条件**:
- 性能监控告警
- 容量规划提醒
- 维护提醒

**响应流程**:
```
1. 4小时内响应
2. 记录问题
3. 计划维护窗口
4. 实施改进
```

## 📈 监控最佳实践

### 1. 指标收集

```bash
# 定期检查指标收集状态
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# 验证指标数据完整性
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result[] | select(.value[1] != "1")'
```

### 2. 告警规则优化

```yaml
# 避免告警风暴
groups:
  - name: qte_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(qte_errors_total[5m]) > 0.1
        for: 2m  # 持续2分钟才告警
        labels:
          severity: warning
```

### 3. 仪表板设计

```
关键原则:
1. 分层展示 - 总览 -> 详细
2. 实时更新 - 5-30秒刷新
3. 颜色编码 - 绿色正常，黄色警告，红色错误
4. 趋势分析 - 显示历史趋势
5. 钻取能力 - 支持深入分析
```

### 4. 容量规划

```bash
# 监控资源使用趋势
# CPU使用率趋势
curl -s "http://localhost:9090/api/v1/query_range?query=100-avg(irate(node_cpu_seconds_total{mode='idle'}[5m]))*100&start=$(date -d '7 days ago' +%s)&end=$(date +%s)&step=3600"

# 内存使用趋势
curl -s "http://localhost:9090/api/v1/query_range?query=(1-node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)*100&start=$(date -d '7 days ago' +%s)&end=$(date +%s)&step=3600"
```

## 🔧 监控工具使用

### 1. Grafana仪表板

**访问地址**: https://grafana.qte.local:3000

**主要仪表板**:
- QTE总览仪表板
- 业务指标仪表板
- 系统性能仪表板
- 安全监控仪表板

### 2. Prometheus查询

```promql
# 常用查询示例

# 事件处理速率
rate(qte_events_processed_total[5m])

# API响应时间95分位数
histogram_quantile(0.95, rate(qte_request_duration_seconds_bucket[5m]))

# 错误率
rate(qte_errors_total[5m]) / rate(qte_requests_total[5m])

# 内存使用率
(qte_memory_usage_bytes / qte_memory_limit_bytes) * 100
```

### 3. 告警管理

```bash
# 查看活跃告警
curl -s http://localhost:9093/api/v1/alerts | jq '.data[] | select(.status.state == "firing")'

# 静默告警
curl -X POST http://localhost:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{"matchers":[{"name":"alertname","value":"HighCPUUsage"}],"startsAt":"2023-12-18T10:00:00Z","endsAt":"2023-12-18T12:00:00Z","comment":"维护窗口"}'
```

## 📞 支持和培训

### 联系方式
- **监控支持**: monitoring@company.com
- **培训预约**: training@company.com
- **文档反馈**: docs@company.com

### 培训资源
- Grafana使用培训
- Prometheus查询语言培训
- 告警响应流程培训
- 故障排除技能培训

---

**注意**: 本指南应与系统更新同步维护，确保指标定义和阈值的准确性。
