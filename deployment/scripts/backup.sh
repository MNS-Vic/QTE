#!/bin/bash
# QTE自动备份脚本
# 定期备份数据库、配置文件和关键数据

set -euo pipefail

# 配置变量
BACKUP_ROOT="/opt/qte/backups"
RETENTION_DAYS=30
COMPRESSION_LEVEL=6
ENCRYPTION_KEY_FILE="/opt/qte/keys/backup.key"
LOG_FILE="/var/log/qte-backup.log"

# 远程备份配置
REMOTE_BACKUP_ENABLED="${REMOTE_BACKUP_ENABLED:-false}"
REMOTE_BACKUP_HOST="${REMOTE_BACKUP_HOST:-}"
REMOTE_BACKUP_USER="${REMOTE_BACKUP_USER:-}"
REMOTE_BACKUP_PATH="${REMOTE_BACKUP_PATH:-}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 创建备份目录
create_backup_structure() {
    local backup_date="$1"
    local backup_dir="${BACKUP_ROOT}/${backup_date}"
    
    mkdir -p "${backup_dir}/database"
    mkdir -p "${backup_dir}/redis"
    mkdir -p "${backup_dir}/config"
    mkdir -p "${backup_dir}/logs"
    mkdir -p "${backup_dir}/data"
    
    echo "${backup_dir}"
}

# 备份PostgreSQL数据库
backup_database() {
    local backup_dir="$1"
    
    log "开始备份PostgreSQL数据库..."
    
    # 检查数据库连接
    if ! docker exec qte-postgres pg_isready -U qte -d qte &>/dev/null; then
        log_error "无法连接到PostgreSQL数据库"
        return 1
    fi
    
    # 创建数据库备份
    local db_backup_file="${backup_dir}/database/qte_db_$(date +%H%M%S).sql"
    
    if docker exec qte-postgres pg_dump -U qte -d qte --verbose --clean --if-exists > "${db_backup_file}"; then
        log_success "数据库备份完成: $(basename "${db_backup_file}")"
        
        # 压缩备份文件
        gzip -"${COMPRESSION_LEVEL}" "${db_backup_file}"
        log_success "数据库备份已压缩"
        
        return 0
    else
        log_error "数据库备份失败"
        return 1
    fi
}

# 备份Redis数据
backup_redis() {
    local backup_dir="$1"
    
    log "开始备份Redis数据..."
    
    # 检查Redis连接
    if ! docker exec qte-redis redis-cli ping &>/dev/null; then
        log_error "无法连接到Redis"
        return 1
    fi
    
    # 触发Redis保存
    docker exec qte-redis redis-cli BGSAVE
    
    # 等待保存完成
    local save_in_progress=1
    local timeout=60
    local elapsed=0
    
    while [[ $save_in_progress -eq 1 && $elapsed -lt $timeout ]]; do
        if docker exec qte-redis redis-cli LASTSAVE | grep -q "$(docker exec qte-redis redis-cli LASTSAVE)"; then
            save_in_progress=0
        else
            sleep 2
            elapsed=$((elapsed + 2))
        fi
    done
    
    if [[ $save_in_progress -eq 1 ]]; then
        log_warning "Redis保存超时，使用当前dump文件"
    fi
    
    # 复制Redis dump文件
    local redis_backup_file="${backup_dir}/redis/dump_$(date +%H%M%S).rdb"
    
    if docker cp qte-redis:/data/dump.rdb "${redis_backup_file}"; then
        log_success "Redis备份完成: $(basename "${redis_backup_file}")"
        
        # 压缩备份文件
        gzip -"${COMPRESSION_LEVEL}" "${redis_backup_file}"
        log_success "Redis备份已压缩"
        
        return 0
    else
        log_error "Redis备份失败"
        return 1
    fi
}

# 备份配置文件
backup_config() {
    local backup_dir="$1"
    
    log "开始备份配置文件..."
    
    local config_sources=(
        "/opt/qte/deployment/config"
        "/opt/qte/deployment/monitoring"
        "/opt/qte/deployment/nginx"
        "/opt/qte/deployment/logging"
    )
    
    for source in "${config_sources[@]}"; do
        if [[ -d "$source" ]]; then
            local dest_name=$(basename "$source")
            cp -r "$source" "${backup_dir}/config/${dest_name}"
            log "已备份配置: $dest_name"
        fi
    done
    
    # 压缩配置备份
    tar -czf "${backup_dir}/config.tar.gz" -C "${backup_dir}" config
    rm -rf "${backup_dir}/config"
    
    log_success "配置文件备份完成"
}

# 备份日志文件
backup_logs() {
    local backup_dir="$1"
    
    log "开始备份日志文件..."
    
    local log_sources=(
        "/app/logs"
        "/var/log/qte"
        "/var/log/nginx"
    )
    
    for source in "${log_sources[@]}"; do
        if [[ -d "$source" ]]; then
            local dest_name=$(basename "$source")
            
            # 只备份最近7天的日志
            find "$source" -name "*.log" -mtime -7 -exec cp {} "${backup_dir}/logs/" \;
            log "已备份日志: $dest_name (最近7天)"
        fi
    done
    
    # 压缩日志备份
    if [[ -n "$(ls -A "${backup_dir}/logs" 2>/dev/null)" ]]; then
        tar -czf "${backup_dir}/logs.tar.gz" -C "${backup_dir}" logs
        rm -rf "${backup_dir}/logs"
        log_success "日志文件备份完成"
    else
        log_warning "未找到需要备份的日志文件"
    fi
}

# 备份应用数据
backup_application_data() {
    local backup_dir="$1"
    
    log "开始备份应用数据..."
    
    local data_sources=(
        "/app/data"
        "/opt/qte/data"
    )
    
    for source in "${data_sources[@]}"; do
        if [[ -d "$source" ]]; then
            local dest_name=$(basename "$source")
            cp -r "$source" "${backup_dir}/data/${dest_name}"
            log "已备份数据: $dest_name"
        fi
    done
    
    # 压缩数据备份
    if [[ -n "$(ls -A "${backup_dir}/data" 2>/dev/null)" ]]; then
        tar -czf "${backup_dir}/data.tar.gz" -C "${backup_dir}" data
        rm -rf "${backup_dir}/data"
        log_success "应用数据备份完成"
    else
        log_warning "未找到需要备份的应用数据"
    fi
}

# 加密备份
encrypt_backup() {
    local backup_dir="$1"
    
    if [[ ! -f "${ENCRYPTION_KEY_FILE}" ]]; then
        log_warning "未找到加密密钥文件，跳过加密"
        return 0
    fi
    
    log "开始加密备份文件..."
    
    for file in "${backup_dir}"/*.{sql.gz,rdb.gz,tar.gz} 2>/dev/null; do
        if [[ -f "$file" ]]; then
            openssl enc -aes-256-cbc -salt -in "$file" -out "${file}.enc" -pass file:"${ENCRYPTION_KEY_FILE}"
            rm "$file"
            log "已加密: $(basename "${file}")"
        fi
    done
    
    log_success "备份加密完成"
}

# 创建备份清单
create_manifest() {
    local backup_dir="$1"
    local manifest_file="${backup_dir}/manifest.json"
    
    log "创建备份清单..."
    
    cat > "${manifest_file}" << EOF
{
  "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "backup_type": "full",
  "qte_version": "${QTE_VERSION:-unknown}",
  "hostname": "$(hostname)",
  "files": [
EOF

    local first=true
    for file in "${backup_dir}"/*; do
        if [[ -f "$file" && "$(basename "$file")" != "manifest.json" ]]; then
            if [[ "$first" == "true" ]]; then
                first=false
            else
                echo "," >> "${manifest_file}"
            fi
            
            local file_size=$(stat -c%s "$file")
            local file_hash=$(sha256sum "$file" | cut -d' ' -f1)
            
            cat >> "${manifest_file}" << EOF
    {
      "name": "$(basename "$file")",
      "size": ${file_size},
      "sha256": "${file_hash}"
    }
EOF
        fi
    done
    
    echo -e "\n  ]\n}" >> "${manifest_file}"
    
    log_success "备份清单创建完成"
}

# 上传到远程存储
upload_to_remote() {
    local backup_dir="$1"
    
    if [[ "${REMOTE_BACKUP_ENABLED}" != "true" ]]; then
        log "远程备份未启用，跳过上传"
        return 0
    fi
    
    if [[ -z "${REMOTE_BACKUP_HOST}" || -z "${REMOTE_BACKUP_USER}" || -z "${REMOTE_BACKUP_PATH}" ]]; then
        log_warning "远程备份配置不完整，跳过上传"
        return 0
    fi
    
    log "开始上传备份到远程存储..."
    
    local backup_name=$(basename "${backup_dir}")
    local remote_path="${REMOTE_BACKUP_PATH}/${backup_name}"
    
    if rsync -avz --progress "${backup_dir}/" "${REMOTE_BACKUP_USER}@${REMOTE_BACKUP_HOST}:${remote_path}/"; then
        log_success "备份已上传到远程存储"
    else
        log_error "远程备份上传失败"
        return 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    log "清理超过 ${RETENTION_DAYS} 天的旧备份..."
    
    local deleted_count=0
    
    # 清理本地备份
    while IFS= read -r -d '' backup_dir; do
        rm -rf "$backup_dir"
        deleted_count=$((deleted_count + 1))
        log "已删除旧备份: $(basename "$backup_dir")"
    done < <(find "${BACKUP_ROOT}" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -print0)
    
    # 清理远程备份
    if [[ "${REMOTE_BACKUP_ENABLED}" == "true" ]]; then
        ssh "${REMOTE_BACKUP_USER}@${REMOTE_BACKUP_HOST}" \
            "find ${REMOTE_BACKUP_PATH} -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \;"
    fi
    
    if [[ $deleted_count -gt 0 ]]; then
        log_success "已清理 ${deleted_count} 个旧备份"
    else
        log "未找到需要清理的旧备份"
    fi
}

# 验证备份完整性
verify_backup() {
    local backup_dir="$1"
    local manifest_file="${backup_dir}/manifest.json"
    
    log "验证备份完整性..."
    
    if [[ ! -f "${manifest_file}" ]]; then
        log_error "备份清单文件不存在"
        return 1
    fi
    
    local verification_failed=false
    
    # 验证文件完整性
    while IFS= read -r line; do
        if [[ "$line" =~ \"name\":\ \"([^\"]+)\" ]]; then
            local file_name="${BASH_REMATCH[1]}"
            local file_path="${backup_dir}/${file_name}"
            
            if [[ ! -f "$file_path" ]]; then
                log_error "备份文件缺失: $file_name"
                verification_failed=true
            fi
        fi
    done < "${manifest_file}"
    
    if [[ "$verification_failed" == "true" ]]; then
        log_error "备份完整性验证失败"
        return 1
    else
        log_success "备份完整性验证通过"
        return 0
    fi
}

# 主备份函数
perform_backup() {
    local backup_date=$(date +%Y%m%d_%H%M%S)
    local backup_dir
    
    log "开始QTE系统备份 (${backup_date})"
    
    # 创建备份目录结构
    backup_dir=$(create_backup_structure "${backup_date}")
    
    # 执行各项备份
    local backup_success=true
    
    if ! backup_database "${backup_dir}"; then
        backup_success=false
    fi
    
    if ! backup_redis "${backup_dir}"; then
        backup_success=false
    fi
    
    backup_config "${backup_dir}"
    backup_logs "${backup_dir}"
    backup_application_data "${backup_dir}"
    
    # 加密备份
    encrypt_backup "${backup_dir}"
    
    # 创建清单
    create_manifest "${backup_dir}"
    
    # 验证备份
    if ! verify_backup "${backup_dir}"; then
        backup_success=false
    fi
    
    if [[ "$backup_success" == "true" ]]; then
        # 上传到远程存储
        upload_to_remote "${backup_dir}"
        
        # 清理旧备份
        cleanup_old_backups
        
        log_success "备份完成: ${backup_dir}"
        
        # 发送成功通知
        if command -v curl &> /dev/null && [[ -n "${BACKUP_WEBHOOK_URL:-}" ]]; then
            curl -X POST "${BACKUP_WEBHOOK_URL}" \
                -H "Content-Type: application/json" \
                -d "{\"status\":\"success\",\"backup_path\":\"${backup_dir}\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
                &>/dev/null || true
        fi
    else
        log_error "备份过程中出现错误"
        
        # 发送失败通知
        if command -v curl &> /dev/null && [[ -n "${BACKUP_WEBHOOK_URL:-}" ]]; then
            curl -X POST "${BACKUP_WEBHOOK_URL}" \
                -H "Content-Type: application/json" \
                -d "{\"status\":\"failed\",\"backup_path\":\"${backup_dir}\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
                &>/dev/null || true
        fi
        
        exit 1
    fi
}

# 主函数
main() {
    case "${1:-backup}" in
        "backup")
            perform_backup
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "verify")
            if [[ -z "${2:-}" ]]; then
                echo "用法: $0 verify <backup_directory>"
                exit 1
            fi
            verify_backup "$2"
            ;;
        *)
            echo "用法: $0 {backup|cleanup|verify} [参数]"
            echo ""
            echo "命令说明:"
            echo "  backup                    - 执行完整备份"
            echo "  cleanup                   - 清理旧备份"
            echo "  verify <backup_directory> - 验证备份完整性"
            exit 1
            ;;
    esac
}

# 创建必要目录
mkdir -p "${BACKUP_ROOT}"
mkdir -p "$(dirname "${LOG_FILE}")"

# 执行主函数
main "$@"
