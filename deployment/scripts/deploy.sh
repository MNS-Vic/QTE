#!/bin/bash
# QTE生产环境部署脚本
# 用于安全、可靠地部署QTE交易引擎到生产环境

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEPLOYMENT_DIR="${PROJECT_ROOT}/deployment"
BACKUP_DIR="/opt/qte/backups"
LOG_FILE="/var/log/qte-deployment.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "${LOG_FILE}"
}

# 错误处理
error_exit() {
    log_error "$1"
    exit 1
}

# 检查先决条件
check_prerequisites() {
    log "检查部署先决条件..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker未安装或不在PATH中"
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose未安装或不在PATH中"
    fi
    
    # 检查必要的环境变量
    required_vars=("POSTGRES_PASSWORD" "GRAFANA_PASSWORD" "QTE_VERSION")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "必需的环境变量 $var 未设置"
        fi
    done
    
    # 检查磁盘空间
    available_space=$(df / | awk 'NR==2 {print $4}')
    required_space=5242880  # 5GB in KB
    if [[ $available_space -lt $required_space ]]; then
        error_exit "磁盘空间不足，需要至少5GB可用空间"
    fi
    
    log_success "先决条件检查通过"
}

# 创建备份
create_backup() {
    log "创建当前系统备份..."
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/qte_backup_${backup_timestamp}"
    
    mkdir -p "${backup_path}"
    
    # 备份数据库
    if docker ps | grep -q qte-postgres; then
        log "备份PostgreSQL数据库..."
        docker exec qte-postgres pg_dump -U qte qte > "${backup_path}/database.sql"
    fi
    
    # 备份Redis数据
    if docker ps | grep -q qte-redis; then
        log "备份Redis数据..."
        docker exec qte-redis redis-cli BGSAVE
        docker cp qte-redis:/data/dump.rdb "${backup_path}/redis.rdb"
    fi
    
    # 备份配置文件
    log "备份配置文件..."
    cp -r "${DEPLOYMENT_DIR}/config" "${backup_path}/"
    
    # 备份日志
    if [[ -d "/app/logs" ]]; then
        log "备份日志文件..."
        cp -r "/app/logs" "${backup_path}/"
    fi
    
    # 压缩备份
    tar -czf "${backup_path}.tar.gz" -C "${BACKUP_DIR}" "qte_backup_${backup_timestamp}"
    rm -rf "${backup_path}"
    
    log_success "备份创建完成: ${backup_path}.tar.gz"
    echo "${backup_path}.tar.gz"
}

# 健康检查
health_check() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    log "等待 ${service_name} 服务启动..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "${DEPLOYMENT_DIR}/docker/docker-compose.yml" ps | grep -q "${service_name}.*Up"; then
            log_success "${service_name} 服务已启动"
            return 0
        fi
        
        log "等待 ${service_name} 启动... (尝试 ${attempt}/${max_attempts})"
        sleep 10
        ((attempt++))
    done
    
    error_exit "${service_name} 服务启动失败"
}

# 验证部署
verify_deployment() {
    log "验证部署状态..."
    
    # 检查所有服务状态
    local services=("qte-engine" "qte-postgres" "qte-redis" "qte-prometheus" "qte-grafana")
    
    for service in "${services[@]}"; do
        if ! docker-compose -f "${DEPLOYMENT_DIR}/docker/docker-compose.yml" ps | grep -q "${service}.*Up"; then
            error_exit "服务 ${service} 未正常运行"
        fi
    done
    
    # 运行健康检查
    log "执行应用健康检查..."
    if ! python "${SCRIPT_DIR}/healthcheck.py"; then
        error_exit "健康检查失败"
    fi
    
    # 检查关键指标
    log "检查关键业务指标..."
    local metrics_url="http://localhost:9090/metrics"
    if ! curl -s "${metrics_url}" | grep -q "qte_"; then
        log_warning "未检测到QTE业务指标，可能需要等待更长时间"
    fi
    
    log_success "部署验证通过"
}

# 部署函数
deploy() {
    local deployment_type="${1:-full}"
    
    log "开始QTE生产环境部署 (类型: ${deployment_type})"
    
    # 检查先决条件
    check_prerequisites
    
    # 创建备份
    local backup_file
    backup_file=$(create_backup)
    
    # 切换到部署目录
    cd "${DEPLOYMENT_DIR}/docker"
    
    case "${deployment_type}" in
        "full")
            log "执行完整部署..."
            
            # 停止现有服务
            log "停止现有服务..."
            docker-compose down --remove-orphans || true
            
            # 清理旧镜像
            log "清理旧镜像..."
            docker system prune -f
            
            # 构建新镜像
            log "构建QTE镜像..."
            docker-compose build --no-cache qte-engine
            
            # 启动所有服务
            log "启动所有服务..."
            docker-compose up -d
            ;;
            
        "update")
            log "执行应用更新..."
            
            # 仅重启QTE引擎
            log "重启QTE引擎..."
            docker-compose stop qte-engine
            docker-compose build --no-cache qte-engine
            docker-compose up -d qte-engine
            ;;
            
        "config")
            log "执行配置更新..."
            
            # 重新加载配置
            log "重新加载配置..."
            docker-compose restart qte-engine
            ;;
            
        *)
            error_exit "未知的部署类型: ${deployment_type}"
            ;;
    esac
    
    # 等待服务启动
    health_check "qte-engine"
    health_check "qte-postgres"
    health_check "qte-redis"
    
    # 验证部署
    verify_deployment
    
    log_success "QTE部署完成！"
    log "备份文件: ${backup_file}"
    log "监控面板: http://localhost:3000"
    log "API端点: http://localhost:8080"
    log "管理端点: http://localhost:8081"
}

# 回滚函数
rollback() {
    local backup_file="$1"
    
    if [[ -z "${backup_file}" ]]; then
        error_exit "请指定备份文件路径"
    fi
    
    if [[ ! -f "${backup_file}" ]]; then
        error_exit "备份文件不存在: ${backup_file}"
    fi
    
    log "开始回滚到备份: ${backup_file}"
    
    # 停止当前服务
    log "停止当前服务..."
    cd "${DEPLOYMENT_DIR}/docker"
    docker-compose down
    
    # 恢复备份
    log "恢复备份数据..."
    local restore_dir="/tmp/qte_restore_$(date +%s)"
    mkdir -p "${restore_dir}"
    tar -xzf "${backup_file}" -C "${restore_dir}"
    
    # 恢复配置
    local backup_name=$(basename "${backup_file}" .tar.gz)
    cp -r "${restore_dir}/${backup_name}/config/"* "${DEPLOYMENT_DIR}/config/"
    
    # 启动服务
    log "启动服务..."
    docker-compose up -d
    
    # 等待数据库启动
    health_check "qte-postgres"
    
    # 恢复数据库
    if [[ -f "${restore_dir}/${backup_name}/database.sql" ]]; then
        log "恢复数据库..."
        docker exec -i qte-postgres psql -U qte qte < "${restore_dir}/${backup_name}/database.sql"
    fi
    
    # 恢复Redis
    if [[ -f "${restore_dir}/${backup_name}/redis.rdb" ]]; then
        log "恢复Redis数据..."
        docker cp "${restore_dir}/${backup_name}/redis.rdb" qte-redis:/data/dump.rdb
        docker-compose restart qte-redis
    fi
    
    # 清理临时文件
    rm -rf "${restore_dir}"
    
    # 验证回滚
    verify_deployment
    
    log_success "回滚完成"
}

# 主函数
main() {
    case "${1:-deploy}" in
        "deploy")
            deploy "${2:-full}"
            ;;
        "update")
            deploy "update"
            ;;
        "config")
            deploy "config"
            ;;
        "rollback")
            rollback "${2:-}"
            ;;
        "backup")
            create_backup
            ;;
        "health")
            verify_deployment
            ;;
        *)
            echo "用法: $0 {deploy|update|config|rollback|backup|health} [参数]"
            echo ""
            echo "命令说明:"
            echo "  deploy [full|update|config] - 部署QTE系统"
            echo "  update                      - 仅更新应用"
            echo "  config                      - 仅更新配置"
            echo "  rollback <backup_file>      - 回滚到指定备份"
            echo "  backup                      - 创建备份"
            echo "  health                      - 健康检查"
            exit 1
            ;;
    esac
}

# 确保以root权限运行
if [[ $EUID -ne 0 ]]; then
    error_exit "此脚本需要root权限运行"
fi

# 创建必要目录
mkdir -p "${BACKUP_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# 执行主函数
main "$@"
