#!/usr/bin/env python3
"""
QTE生产环境安全配置模块
实施全面的安全控制和合规措施
"""

import os
import hashlib
import secrets
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import ipaddress
import re


class SecurityConfig:
    """安全配置管理器"""
    
    def __init__(self, config_path: str = "/app/config/security.yaml"):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # 安全配置
        self.encryption_key = None
        self.api_keys = {}
        self.ip_whitelist = []
        self.rate_limits = {}
        self.security_headers = {}
        
        # 审计配置
        self.audit_log_path = "/var/log/qte/audit.log"
        self.failed_login_threshold = 5
        self.lockout_duration = 300  # 5分钟
        
        # 合规配置
        self.data_retention_days = 2555  # 7年
        self.backup_encryption = True
        self.access_log_retention = 90  # 90天
        
        self._load_security_config()
        self._setup_encryption()
    
    def _load_security_config(self):
        """加载安全配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            security_config = config.get('security', {})
            
            # API安全配置
            api_config = security_config.get('api', {})
            self.rate_limits = api_config.get('rate_limits', {
                'default': 1000,  # 每分钟1000次请求
                'admin': 100,     # 管理接口每分钟100次
                'auth': 10        # 认证接口每分钟10次
            })
            
            # IP白名单
            whitelist = security_config.get('ip_whitelist', [])
            self.ip_whitelist = [ipaddress.ip_network(ip) for ip in whitelist]
            
            # 安全头配置
            self.security_headers = security_config.get('headers', {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': "default-src 'self'",
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            })
            
            self.logger.info("安全配置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载安全配置失败: {e}")
            self._use_default_config()
    
    def _use_default_config(self):
        """使用默认安全配置"""
        self.logger.warning("使用默认安全配置")
        
        self.rate_limits = {'default': 1000, 'admin': 100, 'auth': 10}
        self.ip_whitelist = [
            ipaddress.ip_network('127.0.0.1/32'),
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16')
        ]
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }
    
    def _setup_encryption(self):
        """设置加密密钥"""
        key_file = "/opt/qte/keys/encryption.key"
        
        try:
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
                self.logger.info("已加载加密密钥")
            else:
                # 生成新密钥
                self.encryption_key = Fernet.generate_key()
                
                # 确保目录存在
                os.makedirs(os.path.dirname(key_file), mode=0o700, exist_ok=True)
                
                # 保存密钥
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                
                # 设置安全权限
                os.chmod(key_file, 0o600)
                
                self.logger.info("已生成新的加密密钥")
                
        except Exception as e:
            self.logger.error(f"设置加密密钥失败: {e}")
            # 使用临时密钥
            self.encryption_key = Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"数据加密失败: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            fernet = Fernet(self.encryption_key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"数据解密失败: {e}")
            raise
    
    def generate_api_key(self, user_id: str, permissions: List[str]) -> str:
        """生成API密钥"""
        # 生成随机密钥
        api_key = secrets.token_urlsafe(32)
        
        # 存储密钥信息
        key_info = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'usage_count': 0
        }
        
        # 加密存储
        encrypted_info = self.encrypt_data(json.dumps(key_info))
        self.api_keys[api_key] = encrypted_info
        
        self.logger.info(f"为用户 {user_id} 生成API密钥")
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        if api_key not in self.api_keys:
            return None
        
        try:
            # 解密密钥信息
            encrypted_info = self.api_keys[api_key]
            key_info = json.loads(self.decrypt_data(encrypted_info))
            
            # 更新使用信息
            key_info['last_used'] = datetime.now().isoformat()
            key_info['usage_count'] += 1
            
            # 重新加密存储
            self.api_keys[api_key] = self.encrypt_data(json.dumps(key_info))
            
            return key_info
            
        except Exception as e:
            self.logger.error(f"API密钥验证失败: {e}")
            return None
    
    def check_ip_whitelist(self, client_ip: str) -> bool:
        """检查IP白名单"""
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for network in self.ip_whitelist:
                if client_addr in network:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"IP白名单检查失败: {e}")
            return False
    
    def validate_input(self, input_data: str, input_type: str = "general") -> bool:
        """输入验证"""
        if not input_data:
            return False
        
        # 基本长度检查
        if len(input_data) > 10000:  # 10KB限制
            return False
        
        # SQL注入检测
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"].*['\"])"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                self.logger.warning(f"检测到可能的SQL注入: {input_data[:100]}")
                return False
        
        # XSS检测
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                self.logger.warning(f"检测到可能的XSS攻击: {input_data[:100]}")
                return False
        
        # 特定类型验证
        if input_type == "email":
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return bool(re.match(email_pattern, input_data))
        
        elif input_type == "symbol":
            # 交易标的验证
            symbol_pattern = r"^[A-Z0-9]{1,10}$"
            return bool(re.match(symbol_pattern, input_data))
        
        elif input_type == "numeric":
            try:
                float(input_data)
                return True
            except ValueError:
                return False
        
        return True
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """密码哈希"""
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """验证密码"""
        try:
            salt_bytes = base64.b64decode(salt.encode())
            expected_hash, _ = self.hash_password(password, salt_bytes)
            return expected_hash == hashed_password
        except Exception as e:
            self.logger.error(f"密码验证失败: {e}")
            return False
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """记录安全事件"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'details': details,
                'severity': self._get_event_severity(event_type)
            }
            
            # 确保审计日志目录存在
            os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
            
            # 写入审计日志
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            # 高严重性事件立即告警
            if event['severity'] == 'HIGH':
                self._send_security_alert(event)
                
        except Exception as e:
            self.logger.error(f"记录安全事件失败: {e}")
    
    def _get_event_severity(self, event_type: str) -> str:
        """获取事件严重性"""
        high_severity_events = [
            'authentication_failure',
            'authorization_failure',
            'sql_injection_attempt',
            'xss_attempt',
            'suspicious_activity',
            'data_breach_attempt'
        ]
        
        if event_type in high_severity_events:
            return 'HIGH'
        elif event_type.endswith('_failure'):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _send_security_alert(self, event: Dict[str, Any]):
        """发送安全告警"""
        try:
            # 这里可以集成告警系统
            self.logger.critical(f"安全告警: {event['event_type']} - {event['details']}")
            
            # 可以添加邮件、短信、Webhook等通知方式
            
        except Exception as e:
            self.logger.error(f"发送安全告警失败: {e}")
    
    def check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """检查速率限制"""
        # 这里应该使用Redis等缓存系统实现
        # 简化实现，实际生产环境需要更复杂的逻辑
        
        rate_limit_key = f"rate_limit:{client_id}:{endpoint}"
        current_time = datetime.now()
        
        # 获取速率限制配置
        limit = self.rate_limits.get(endpoint, self.rate_limits['default'])
        
        # 实际实现需要使用Redis的滑动窗口算法
        # 这里仅作示例
        return True
    
    def sanitize_log_data(self, data: Any) -> Any:
        """清理日志数据，移除敏感信息"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = ['password', 'token', 'key', 'secret', 'auth']
            
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = '***REDACTED***'
                else:
                    sanitized[key] = self.sanitize_log_data(value)
            
            return sanitized
        
        elif isinstance(data, list):
            return [self.sanitize_log_data(item) for item in data]
        
        elif isinstance(data, str):
            # 检查是否包含敏感信息模式
            if re.search(r'\b[A-Za-z0-9]{20,}\b', data):  # 可能的token
                return '***REDACTED***'
            return data
        
        else:
            return data
    
    def generate_csrf_token(self, session_id: str) -> str:
        """生成CSRF令牌"""
        timestamp = str(int(datetime.now().timestamp()))
        data = f"{session_id}:{timestamp}"
        
        # 使用HMAC生成令牌
        import hmac
        token = hmac.new(
            self.encryption_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}:{token}"
    
    def validate_csrf_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """验证CSRF令牌"""
        try:
            timestamp_str, token_hash = token.split(':', 1)
            timestamp = int(timestamp_str)
            
            # 检查令牌是否过期
            if datetime.now().timestamp() - timestamp > max_age:
                return False
            
            # 重新生成令牌进行比较
            expected_token = self.generate_csrf_token(session_id)
            expected_hash = expected_token.split(':', 1)[1]
            
            return hmac.compare_digest(token_hash, expected_hash)
            
        except Exception as e:
            self.logger.error(f"CSRF令牌验证失败: {e}")
            return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """获取安全头"""
        return self.security_headers.copy()
    
    def is_secure_connection(self, request_headers: Dict[str, str]) -> bool:
        """检查是否为安全连接"""
        # 检查HTTPS
        if request_headers.get('X-Forwarded-Proto') == 'https':
            return True
        
        if request_headers.get('X-Forwarded-SSL') == 'on':
            return True
        
        # 检查其他安全指标
        return False


def main():
    """主函数 - 用于测试和初始化"""
    import argparse
    
    parser = argparse.ArgumentParser(description='QTE安全配置管理')
    parser.add_argument('--init', action='store_true', help='初始化安全配置')
    parser.add_argument('--generate-key', help='为用户生成API密钥')
    parser.add_argument('--test-encryption', action='store_true', help='测试加密功能')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建安全配置实例
    security = SecurityConfig()
    
    if args.init:
        print("安全配置初始化完成")
        print(f"加密密钥已生成")
        print(f"审计日志路径: {security.audit_log_path}")
    
    elif args.generate_key:
        api_key = security.generate_api_key(args.generate_key, ['read', 'write'])
        print(f"为用户 {args.generate_key} 生成的API密钥: {api_key}")
    
    elif args.test_encryption:
        test_data = "这是测试数据"
        encrypted = security.encrypt_data(test_data)
        decrypted = security.decrypt_data(encrypted)
        
        print(f"原始数据: {test_data}")
        print(f"加密数据: {encrypted}")
        print(f"解密数据: {decrypted}")
        print(f"加密测试: {'成功' if test_data == decrypted else '失败'}")
    
    else:
        print("QTE安全配置管理器")
        print("使用 --help 查看可用选项")


if __name__ == "__main__":
    main()
