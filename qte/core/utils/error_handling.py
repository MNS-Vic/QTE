#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强的错误处理模块

提供统一的错误处理、异常恢复和用户友好的错误信息
"""

import logging
import traceback
import functools
from typing import Dict, Any, Optional, Callable, Type, Union
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QTEError(Exception):
    """QTE基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "QTE_UNKNOWN"
        self.severity = severity
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'severity': self.severity.value,
            'context': self.context
        }


class EngineError(QTEError):
    """引擎相关错误"""
    pass


class DataError(QTEError):
    """数据相关错误"""
    pass


class ConfigurationError(QTEError):
    """配置相关错误"""
    pass


class CompatibilityError(QTEError):
    """兼容性相关错误"""
    pass


class ErrorHandler:
    """
    统一错误处理器
    
    提供错误捕获、日志记录、用户友好消息和恢复机制
    """
    
    def __init__(self, logger_name: str = "QTE"):
        """
        初始化错误处理器
        
        Parameters
        ----------
        logger_name : str
            日志器名称
        """
        self.logger = logging.getLogger(logger_name)
        self._error_handlers: Dict[Type[Exception], Callable] = {}
        self._recovery_strategies: Dict[str, Callable] = {}
        
        # 注册默认错误处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认错误处理器"""
        self._error_handlers[ValueError] = self._handle_value_error
        self._error_handlers[TypeError] = self._handle_type_error
        self._error_handlers[KeyError] = self._handle_key_error
        self._error_handlers[FileNotFoundError] = self._handle_file_not_found_error
        self._error_handlers[ImportError] = self._handle_import_error
        self._error_handlers[QTEError] = self._handle_qte_error
    
    def register_handler(self, exception_type: Type[Exception], 
                        handler: Callable[[Exception], Dict[str, Any]]):
        """
        注册自定义错误处理器
        
        Parameters
        ----------
        exception_type : Type[Exception]
            异常类型
        handler : Callable
            处理函数
        """
        self._error_handlers[exception_type] = handler
    
    def register_recovery_strategy(self, error_code: str, strategy: Callable):
        """
        注册错误恢复策略
        
        Parameters
        ----------
        error_code : str
            错误代码
        strategy : Callable
            恢复策略函数
        """
        self._recovery_strategies[error_code] = strategy
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理错误
        
        Parameters
        ----------
        error : Exception
            异常对象
        context : Dict[str, Any], optional
            错误上下文
            
        Returns
        -------
        Dict[str, Any]
            错误处理结果
        """
        try:
            # 获取错误处理器
            handler = self._get_error_handler(type(error))
            
            # 处理错误
            result = handler(error)
            
            # 添加上下文信息
            if context:
                result['context'] = context
            
            # 记录错误日志
            self._log_error(error, result)
            
            # 尝试恢复
            recovery_result = self._attempt_recovery(result)
            if recovery_result:
                result['recovery'] = recovery_result
            
            return result
            
        except Exception as e:
            # 错误处理器本身出错
            self.logger.critical("错误处理器失败: %s", e)
            return {
                'error_type': 'ErrorHandlerFailure',
                'message': '错误处理器本身出现问题',
                'original_error': str(error),
                'handler_error': str(e),
                'severity': ErrorSeverity.CRITICAL.value
            }
    
    def _get_error_handler(self, error_type: Type[Exception]) -> Callable:
        """获取错误处理器"""
        # 精确匹配
        if error_type in self._error_handlers:
            return self._error_handlers[error_type]
        
        # 继承匹配
        for registered_type, handler in self._error_handlers.items():
            if issubclass(error_type, registered_type):
                return handler
        
        # 默认处理器
        return self._handle_generic_error
    
    def _log_error(self, error: Exception, result: Dict[str, Any]):
        """记录错误日志"""
        severity = result.get('severity', ErrorSeverity.MEDIUM.value)
        
        if severity == ErrorSeverity.CRITICAL.value:
            self.logger.critical("严重错误: %s", result['message'])
            self.logger.critical("错误详情: %s", traceback.format_exc())
        elif severity == ErrorSeverity.HIGH.value:
            self.logger.error("高级错误: %s", result['message'])
        elif severity == ErrorSeverity.MEDIUM.value:
            self.logger.warning("中级错误: %s", result['message'])
        else:
            self.logger.info("低级错误: %s", result['message'])
    
    def _attempt_recovery(self, error_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """尝试错误恢复"""
        error_code = error_result.get('error_code')
        if error_code and error_code in self._recovery_strategies:
            try:
                strategy = self._recovery_strategies[error_code]
                recovery_result = strategy(error_result)
                self.logger.info("错误恢复成功: %s", error_code)
                return recovery_result
            except Exception as e:
                self.logger.error("错误恢复失败: %s", e)
        
        return None
    
    # 默认错误处理器
    def _handle_value_error(self, error: ValueError) -> Dict[str, Any]:
        """处理值错误"""
        return {
            'error_type': 'ValueError',
            'message': '输入值无效: %s' % str(error),
            'error_code': 'QTE_INVALID_VALUE',
            'severity': ErrorSeverity.MEDIUM.value,
            'user_message': '请检查输入的数据格式和值是否正确',
            'suggestions': [
                '检查数据类型是否匹配',
                '验证数值范围是否合理',
                '确认字符串格式是否正确'
            ]
        }
    
    def _handle_type_error(self, error: TypeError) -> Dict[str, Any]:
        """处理类型错误"""
        return {
            'error_type': 'TypeError',
            'message': '数据类型错误: %s' % str(error),
            'error_code': 'QTE_TYPE_MISMATCH',
            'severity': ErrorSeverity.MEDIUM.value,
            'user_message': '数据类型不匹配，请检查输入参数',
            'suggestions': [
                '检查函数参数类型',
                '确认数据结构是否正确',
                '验证类型注解是否匹配'
            ]
        }
    
    def _handle_key_error(self, error: KeyError) -> Dict[str, Any]:
        """处理键错误"""
        return {
            'error_type': 'KeyError',
            'message': '缺少必需的键: %s' % str(error),
            'error_code': 'QTE_MISSING_KEY',
            'severity': ErrorSeverity.MEDIUM.value,
            'user_message': '配置或数据中缺少必需的字段',
            'suggestions': [
                '检查配置文件是否完整',
                '确认数据字段是否存在',
                '参考文档补充缺失字段'
            ]
        }
    
    def _handle_file_not_found_error(self, error: FileNotFoundError) -> Dict[str, Any]:
        """处理文件未找到错误"""
        return {
            'error_type': 'FileNotFoundError',
            'message': '文件未找到: %s' % str(error),
            'error_code': 'QTE_FILE_NOT_FOUND',
            'severity': ErrorSeverity.HIGH.value,
            'user_message': '指定的文件或路径不存在',
            'suggestions': [
                '检查文件路径是否正确',
                '确认文件是否存在',
                '验证文件权限是否足够'
            ]
        }
    
    def _handle_import_error(self, error: ImportError) -> Dict[str, Any]:
        """处理导入错误"""
        return {
            'error_type': 'ImportError',
            'message': '模块导入失败: %s' % str(error),
            'error_code': 'QTE_IMPORT_FAILED',
            'severity': ErrorSeverity.HIGH.value,
            'user_message': '缺少必需的依赖包或模块',
            'suggestions': [
                '安装缺失的依赖包',
                '检查Python环境配置',
                '确认模块路径是否正确'
            ]
        }
    
    def _handle_qte_error(self, error: QTEError) -> Dict[str, Any]:
        """处理QTE自定义错误"""
        return error.to_dict()
    
    def _handle_generic_error(self, error: Exception) -> Dict[str, Any]:
        """处理通用错误"""
        return {
            'error_type': type(error).__name__,
            'message': '未知错误: %s' % str(error),
            'error_code': 'QTE_UNKNOWN_ERROR',
            'severity': ErrorSeverity.MEDIUM.value,
            'user_message': '发生了未预期的错误，请联系技术支持',
            'suggestions': [
                '检查输入数据是否正确',
                '尝试重新执行操作',
                '查看详细日志信息'
            ]
        }


def safe_execute(error_handler: ErrorHandler = None, 
                default_return: Any = None,
                reraise: bool = False):
    """
    安全执行装饰器
    
    Parameters
    ----------
    error_handler : ErrorHandler, optional
        错误处理器
    default_return : Any, optional
        默认返回值
    reraise : bool, optional
        是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    error_result = error_handler.handle_error(e)
                    if reraise:
                        raise
                    return error_result
                else:
                    if reraise:
                        raise
                    return default_return
        return wrapper
    return decorator


# 全局错误处理器实例
global_error_handler = ErrorHandler("QTE.Global")
