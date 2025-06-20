# QTE运维故障排除手册

## 📋 概述

本手册为QTE量化交易引擎的运维人员提供详细的故障排除指南、应急响应流程和日常维护操作。

## 🚨 紧急响应流程

### 1. 告警分级

| 级别 | 响应时间 | 影响范围 | 处理人员 |
|------|----------|----------|----------|
| **P0 - 关键** | 5分钟 | 系统完全不可用 | 主要工程师 + 经理 |
| **P1 - 高** | 15分钟 | 核心功能受影响 | 值班工程师 |
| **P2 - 中** | 1小时 | 部分功能受影响 | 运维团队 |
| **P3 - 低** | 4小时 | 性能下降 | 日常维护 |

### 2. 应急联系方式

```
主要联系人:
- 技术负责人: +86-xxx-xxxx-xxxx
- 运维负责人: +86-xxx-xxxx-xxxx
- 业务负责人: +86-xxx-xxxx-xxxx

备用联系人:
- 开发团队: dev-team@company.com
- 运维团队: ops-team@company.com
- 管理层: management@company.com
```

### 3. 应急处理步骤

1. **确认告警** - 验证告警真实性
2. **评估影响** - 确定影响范围和严重程度
3. **通知相关人员** - 根据级别通知对应人员
4. **执行应急措施** - 实施临时解决方案
5. **根本原因分析** - 找出问题根本原因
6. **永久修复** - 实施长期解决方案
7. **事后总结** - 编写事故报告

## 🔍 常见故障排除

### 1. 系统无法启动

#### 症状
- Docker容器启动失败
- 服务健康检查失败
- 无法访问API端点

#### 诊断步骤

```bash
# 1. 检查Docker服务状态
sudo systemctl status docker

# 2. 检查容器状态
docker-compose -f deployment/docker/docker-compose.yml ps

# 3. 查看容器日志
docker-compose -f deployment/docker/docker-compose.yml logs qte-engine

# 4. 检查端口占用
netstat -tlnp | grep -E ':(8080|8081|5432|6379)'

# 5. 检查磁盘空间
df -h

# 6. 检查内存使用
free -h
```

#### 解决方案

```bash
# 重启Docker服务
sudo systemctl restart docker

# 清理Docker资源
docker system prune -f

# 重新部署
sudo bash deployment/scripts/deploy.sh deploy full

# 如果仍然失败，从备份恢复
sudo bash deployment/scripts/deploy.sh rollback $(ls -t /opt/qte/backups/*.tar.gz | head -1)
```

### 2. 数据库连接问题

#### 症状
- 数据库连接超时
- 查询执行缓慢
- 连接池耗尽

#### 诊断步骤

```bash
# 1. 检查PostgreSQL状态
docker-compose -f deployment/docker/docker-compose.yml exec postgres pg_isready -U qte

# 2. 检查连接数
docker-compose -f deployment/docker/docker-compose.yml exec postgres psql -U qte -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';"

# 3. 检查慢查询
docker-compose -f deployment/docker/docker-compose.yml exec postgres psql -U qte -c "
SELECT query, query_start, now() - query_start AS duration 
FROM pg_stat_activity 
WHERE now() - query_start > interval '5 minutes';"

# 4. 检查数据库大小
docker-compose -f deployment/docker/docker-compose.yml exec postgres psql -U qte -c "
SELECT pg_size_pretty(pg_database_size('qte'));"
```

#### 解决方案

```bash
# 重启数据库
docker-compose -f deployment/docker/docker-compose.yml restart postgres

# 终止长时间运行的查询
docker-compose -f deployment/docker/docker-compose.yml exec postgres psql -U qte -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE now() - query_start > interval '10 minutes';"

# 清理连接
docker-compose -f deployment/docker/docker-compose.yml exec postgres psql -U qte -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND now() - state_change > interval '1 hour';"
```

### 3. Redis缓存问题

#### 症状
- 缓存命中率低
- Redis内存使用过高
- 连接Redis失败

#### 诊断步骤

```bash
# 1. 检查Redis状态
docker-compose -f deployment/docker/docker-compose.yml exec redis redis-cli ping

# 2. 检查内存使用
docker-compose -f deployment/docker/docker-compose.yml exec redis redis-cli info memory

# 3. 检查连接数
docker-compose -f deployment/docker/docker-compose.yml exec redis redis-cli info clients

# 4. 检查缓存统计
docker-compose -f deployment/docker/docker-compose.yml exec redis redis-cli info stats
```

#### 解决方案

```bash
# 清理过期键
docker-compose -f deployment/docker/docker-compose.yml exec redis redis-cli --scan --pattern "*" | xargs -L 1000 redis-cli del

# 重启Redis
docker-compose -f deployment/docker/docker-compose.yml restart redis

# 调整内存策略
docker-compose -f deployment/docker/docker-compose.yml exec redis redis-cli config set maxmemory-policy allkeys-lru
```

### 4. 性能问题

#### 症状
- API响应时间过长
- 事件处理积压
- CPU/内存使用率过高

#### 诊断步骤

```bash
# 1. 检查系统资源
htop
iotop
nethogs

# 2. 检查应用指标
curl -k https://localhost/metrics | grep -E "(qte_event_queue_size|qte_request_duration)"

# 3. 检查事件队列
curl -k https://localhost:8081/admin/queue/status

# 4. 分析慢日志
grep "SLOW" /opt/qte/logs/qte.log | tail -20
```

#### 解决方案

```bash
# 增加工作进程
# 编辑 deployment/config/production.yaml
# 修改 server.workers 参数

# 优化数据库查询
# 添加索引，优化查询语句

# 清理事件队列积压
curl -X POST https://localhost:8081/admin/queue/clear

# 重启服务释放资源
docker-compose -f deployment/docker/docker-compose.yml restart qte-engine
```

### 5. 网络连接问题

#### 症状
- 外部API调用失败
- 市场数据连接中断
- 负载均衡器健康检查失败

#### 诊断步骤

```bash
# 1. 检查网络连通性
ping 8.8.8.8
curl -I https://api.external-service.com

# 2. 检查DNS解析
nslookup api.external-service.com

# 3. 检查防火墙规则
sudo ufw status

# 4. 检查Nginx状态
docker-compose -f deployment/docker/docker-compose.yml logs nginx
```

#### 解决方案

```bash
# 重启网络服务
sudo systemctl restart networking

# 刷新DNS缓存
sudo systemctl restart systemd-resolved

# 重启Nginx
docker-compose -f deployment/docker/docker-compose.yml restart nginx

# 检查路由表
route -n
```

## 📊 监控和诊断工具

### 1. 系统监控命令

```bash
# CPU使用率
top -p $(pgrep -f qte-engine)

# 内存使用详情
cat /proc/$(pgrep -f qte-engine)/status | grep -E "(VmRSS|VmSize)"

# 网络连接
ss -tulpn | grep -E ":(8080|8081)"

# 磁盘I/O
iostat -x 1

# 进程树
pstree -p $(pgrep -f qte-engine)
```

### 2. 应用监控

```bash
# 健康检查
python3 deployment/scripts/healthcheck.py

# 性能测试
python3 deployment/scripts/performance_monitor.py --test-only

# 业务指标
curl -s https://localhost/metrics | grep qte_portfolio_total_value
```

### 3. 日志分析

```bash
# 错误日志
grep -i error /opt/qte/logs/qte.log | tail -20

# 访问日志分析
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10

# 实时日志监控
tail -f /opt/qte/logs/qte.log | grep -E "(ERROR|CRITICAL)"
```

## 🔧 维护操作

### 1. 日常维护检查清单

#### 每日检查
- [ ] 系统健康状态
- [ ] 关键业务指标
- [ ] 错误日志审查
- [ ] 备份状态确认
- [ ] 磁盘空间检查

#### 每周检查
- [ ] 性能趋势分析
- [ ] 安全日志审查
- [ ] 数据库维护
- [ ] 系统更新检查
- [ ] 容量规划评估

#### 每月检查
- [ ] 全面性能测试
- [ ] 灾难恢复演练
- [ ] 安全漏洞扫描
- [ ] 配置审计
- [ ] 文档更新

### 2. 维护脚本

```bash
# 日常健康检查脚本
#!/bin/bash
echo "=== QTE日常健康检查 ==="
echo "时间: $(date)"
echo

echo "1. 系统资源使用:"
df -h | grep -E "(/$|/opt)"
free -h
echo

echo "2. 服务状态:"
docker-compose -f /opt/qte/deployment/docker/docker-compose.yml ps
echo

echo "3. 关键指标:"
curl -s https://localhost/metrics | grep -E "(qte_portfolio_total_value|qte_trades_total)"
echo

echo "4. 最近错误:"
grep -i error /opt/qte/logs/qte.log | tail -5
echo "=== 检查完成 ==="
```

### 3. 自动化维护

```bash
# 设置定时任务
sudo crontab -e

# 添加以下任务
# 每小时健康检查
0 * * * * /opt/qte/scripts/health_check.sh >> /var/log/qte_health.log 2>&1

# 每日备份
0 2 * * * /opt/qte/deployment/scripts/backup.sh backup

# 每周日志清理
0 3 * * 0 find /opt/qte/logs -name "*.log" -mtime +7 -delete

# 每月性能报告
0 1 1 * * /opt/qte/deployment/scripts/performance_monitor.py --test-only > /opt/qte/reports/monthly_$(date +%Y%m).txt
```

## 📈 性能优化

### 1. 数据库优化

```sql
-- 创建必要索引
CREATE INDEX CONCURRENTLY idx_trades_created_at ON trades(created_at);
CREATE INDEX CONCURRENTLY idx_trades_symbol ON trades(symbol);
CREATE INDEX CONCURRENTLY idx_positions_symbol ON positions(symbol);

-- 更新统计信息
ANALYZE;

-- 清理无用数据
DELETE FROM trades WHERE created_at < NOW() - INTERVAL '1 year';
VACUUM ANALYZE trades;
```

### 2. 应用优化

```bash
# 调整JVM参数（如果使用Java组件）
export JAVA_OPTS="-Xmx2g -Xms2g -XX:+UseG1GC"

# 调整Python GC
export PYTHONOPTIMIZE=1

# 调整工作进程数
# 编辑 deployment/config/production.yaml
# server.workers: 8
```

### 3. 系统优化

```bash
# 调整内核参数
echo 'net.core.somaxconn = 65535' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 调整文件描述符限制
echo '* soft nofile 65535' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65535' | sudo tee -a /etc/security/limits.conf
```

## 🔐 安全维护

### 1. 安全检查

```bash
# 检查失败登录
grep "authentication failure" /var/log/qte/audit.log

# 检查可疑活动
grep "suspicious" /var/log/qte/audit.log

# 检查SSL证书有效期
openssl x509 -in deployment/nginx/ssl/qte.crt -noout -dates
```

### 2. 安全更新

```bash
# 更新系统安全补丁
sudo apt update && sudo apt upgrade -y

# 更新Docker镜像
docker-compose -f deployment/docker/docker-compose.yml pull
docker-compose -f deployment/docker/docker-compose.yml up -d

# 轮换密钥
python3 deployment/security/security_config.py --generate-key admin
```

## 📞 升级支持

### 联系信息
- **紧急热线**: +86-400-xxx-xxxx
- **技术支持**: support@qte.com
- **在线文档**: https://docs.qte.com

### 支持级别
- **基础支持**: 工作日 9:00-18:00
- **标准支持**: 7x24小时响应
- **高级支持**: 专属技术顾问

---

**注意**: 本手册应定期更新，确保与系统版本保持同步。遇到手册中未涵盖的问题，请及时联系技术支持团队。
