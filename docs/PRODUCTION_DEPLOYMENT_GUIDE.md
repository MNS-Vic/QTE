# QTE生产环境部署指南

## 📋 概述

本文档提供QTE量化交易引擎在生产环境中的完整部署指南。QTE系统已通过全面的TDD测试（93.7%平均覆盖率），具备生产级别的质量保证。

## 🎯 部署目标

- **高可用性**: 99.9%系统可用性
- **高性能**: 支持每秒10,000+事件处理
- **安全性**: 企业级安全控制
- **可监控性**: 全面的监控和告警
- **可扩展性**: 支持水平扩展

## 📋 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 | 生产配置 |
|------|----------|----------|----------|
| **CPU** | 4核 | 8核 | 16核+ |
| **内存** | 8GB | 16GB | 32GB+ |
| **存储** | 100GB SSD | 500GB SSD | 1TB+ NVMe SSD |
| **网络** | 1Gbps | 10Gbps | 10Gbps+ |

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Nginx**: 1.20+

## 🚀 部署步骤

### 1. 环境准备

#### 1.1 系统初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y curl wget git vim htop

# 配置时区
sudo timedatectl set-timezone UTC

# 配置系统限制
echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf
```

#### 1.2 Docker安装

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
sudo systemctl enable docker
sudo systemctl start docker

# 添加用户到docker组
sudo usermod -aG docker $USER
```

#### 1.3 创建目录结构

```bash
# 创建QTE目录
sudo mkdir -p /opt/qte/{data,logs,backups,keys,config}

# 设置权限
sudo chown -R $USER:$USER /opt/qte
chmod 755 /opt/qte
chmod 700 /opt/qte/keys
```

### 2. 配置环境变量

#### 2.1 创建环境配置文件

```bash
# 创建环境变量文件
cat > /opt/qte/.env << 'EOF'
# QTE版本
QTE_VERSION=1.0.0

# 数据库配置
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=qte
POSTGRES_USER=qte

# Redis配置
REDIS_PASSWORD=your_redis_password_here

# Grafana配置
GRAFANA_PASSWORD=your_grafana_password_here

# 安全配置
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# 告警配置
ALERT_WEBHOOK_URL=https://your-webhook-url.com/alerts
SMTP_PASSWORD=your_smtp_password_here

# 备份配置
BACKUP_WEBHOOK_URL=https://your-webhook-url.com/backup
REMOTE_BACKUP_ENABLED=false
REMOTE_BACKUP_HOST=
REMOTE_BACKUP_USER=
REMOTE_BACKUP_PATH=

# 监控配置
WEBHOOK_TOKEN=your_webhook_token_here
SMS_API_TOKEN=your_sms_token_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook
EOF

# 设置安全权限
chmod 600 /opt/qte/.env
```

#### 2.2 生成安全密钥

```bash
# 生成随机密钥
python3 -c "
import secrets
import base64

print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))
print('ENCRYPTION_KEY=' + base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))
print('REDIS_PASSWORD=' + secrets.token_urlsafe(16))
print('GRAFANA_PASSWORD=' + secrets.token_urlsafe(12))
"
```

### 3. 部署QTE系统

#### 3.1 获取源代码

```bash
# 克隆代码库
cd /opt/qte
git clone https://github.com/your-org/QTE.git .

# 切换到生产分支
git checkout main
```

#### 3.2 配置SSL证书

```bash
# 创建SSL目录
mkdir -p deployment/nginx/ssl

# 生成自签名证书（测试用）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout deployment/nginx/ssl/qte.key \
    -out deployment/nginx/ssl/qte.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=QTE/CN=qte.local"

# 设置权限
chmod 600 deployment/nginx/ssl/qte.key
chmod 644 deployment/nginx/ssl/qte.crt
```

#### 3.3 执行部署

```bash
# 加载环境变量
source /opt/qte/.env

# 执行部署脚本
sudo bash deployment/scripts/deploy.sh deploy full

# 检查部署状态
docker-compose -f deployment/docker/docker-compose.yml ps
```

### 4. 验证部署

#### 4.1 健康检查

```bash
# 执行健康检查
python3 deployment/scripts/healthcheck.py

# 检查服务状态
curl -k https://localhost/health
curl -k https://localhost/api/health
```

#### 4.2 功能验证

```bash
# 检查API端点
curl -k https://localhost/api/status

# 检查监控端点
curl -k https://localhost/metrics

# 检查管理端点（需要内网访问）
curl http://localhost:8081/admin/status
```

#### 4.3 性能测试

```bash
# 运行性能测试
python3 deployment/scripts/performance_monitor.py --test-only

# 更新性能基准
python3 deployment/scripts/performance_monitor.py --test-only --update-baseline
```

## 🔧 配置管理

### 1. 生产配置文件

主要配置文件位于 `deployment/config/production.yaml`，包含：

- **应用配置**: 服务端口、工作进程数
- **引擎配置**: 事件队列、线程池设置
- **交易配置**: 交易所、投资组合设置
- **数据配置**: 数据源、缓存配置
- **监控配置**: 指标、健康检查设置
- **安全配置**: 认证、加密设置

### 2. 环境特定配置

```bash
# 开发环境
deployment/config/development.yaml

# 测试环境
deployment/config/testing.yaml

# 生产环境
deployment/config/production.yaml
```

### 3. 配置热更新

```bash
# 更新配置后重启服务
sudo bash deployment/scripts/deploy.sh config
```

## 📊 监控和告警

### 1. 监控面板访问

- **Grafana**: https://grafana.qte.local:3000
  - 用户名: admin
  - 密码: 环境变量中的GRAFANA_PASSWORD

- **Prometheus**: https://prometheus.qte.local:9090
  - 仅限内网访问

### 2. 关键监控指标

#### 业务指标
- 交易量和频率
- 投资组合价值和盈亏
- 策略表现指标
- 风险敞口监控

#### 系统指标
- CPU、内存、磁盘使用率
- 网络延迟和吞吐量
- 数据库连接和查询性能
- 缓存命中率

#### 应用指标
- 事件处理速率
- API响应时间
- 错误率和异常数量
- 队列长度和积压

### 3. 告警配置

告警规则定义在 `deployment/monitoring/alert_rules.yml`：

- **关键告警**: 立即通知（短信+邮件）
- **警告告警**: 15分钟内通知
- **信息告警**: 1小时内通知

## 🔒 安全配置

### 1. 网络安全

```bash
# 配置防火墙
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8080/tcp   # 阻止直接访问应用端口
sudo ufw deny 8081/tcp   # 阻止直接访问管理端口
```

### 2. SSL/TLS配置

- 使用TLS 1.2+协议
- 强制HTTPS重定向
- HSTS安全头
- 证书自动更新（Let's Encrypt）

### 3. 访问控制

- IP白名单限制
- API密钥认证
- 速率限制
- CSRF保护

### 4. 数据加密

- 数据库连接加密
- 备份文件加密
- 敏感配置加密存储
- 传输层加密

## 💾 备份和恢复

### 1. 自动备份

```bash
# 配置定时备份
sudo crontab -e

# 添加以下行（每天凌晨2点备份）
0 2 * * * /opt/qte/deployment/scripts/backup.sh backup
```

### 2. 备份验证

```bash
# 验证备份完整性
bash deployment/scripts/backup.sh verify /opt/qte/backups/qte_backup_20231218_020000.tar.gz
```

### 3. 恢复操作

```bash
# 从备份恢复
sudo bash deployment/scripts/deploy.sh rollback /opt/qte/backups/qte_backup_20231218_020000.tar.gz
```

## 🔄 维护操作

### 1. 日常维护

```bash
# 检查系统状态
bash deployment/scripts/deploy.sh health

# 查看日志
docker-compose -f deployment/docker/docker-compose.yml logs -f qte-engine

# 清理旧日志
find /opt/qte/logs -name "*.log" -mtime +30 -delete
```

### 2. 更新部署

```bash
# 更新应用代码
git pull origin main
sudo bash deployment/scripts/deploy.sh update

# 更新配置
sudo bash deployment/scripts/deploy.sh config
```

### 3. 扩容操作

```bash
# 水平扩展（添加更多实例）
# 编辑 docker-compose.yml 添加更多服务实例
# 更新负载均衡配置
```

## 🚨 故障排除

### 1. 常见问题

#### 服务启动失败
```bash
# 检查日志
docker-compose -f deployment/docker/docker-compose.yml logs qte-engine

# 检查配置
python3 -c "import yaml; yaml.safe_load(open('deployment/config/production.yaml'))"

# 检查端口占用
netstat -tlnp | grep :8080
```

#### 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f deployment/docker/docker-compose.yml exec postgres pg_isready

# 检查连接配置
docker-compose -f deployment/docker/docker-compose.yml exec qte-engine env | grep POSTGRES
```

#### 性能问题
```bash
# 检查资源使用
htop
iotop
nethogs

# 检查应用指标
curl -k https://localhost/metrics | grep qte_
```

### 2. 紧急恢复

```bash
# 快速重启所有服务
docker-compose -f deployment/docker/docker-compose.yml restart

# 从最新备份恢复
sudo bash deployment/scripts/deploy.sh rollback $(ls -t /opt/qte/backups/*.tar.gz | head -1)
```

## 📞 支持联系

- **技术支持**: tech-support@company.com
- **紧急联系**: +86-xxx-xxxx-xxxx
- **文档更新**: docs@company.com

---

**注意**: 本指南基于QTE v1.0.0，请确保使用与您的版本匹配的文档。
