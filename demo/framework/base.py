"""
演示框架基础类定义
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .exceptions import DemoFrameworkError, ValidationError, DemoExecutionError


class DemoStatus(Enum):
    """演示状态枚举"""
    INITIALIZED = "initialized"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DemoResult:
    """统一的演示结果格式"""
    status: DemoStatus
    execution_time: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str):
        """添加错误信息"""
        if self.errors is None:
            self.errors = []
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """添加警告信息"""
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(warning)
    
    def is_successful(self) -> bool:
        """判断演示是否成功"""
        return self.status == DemoStatus.COMPLETED and (self.errors is None or len(self.errors) == 0)


@dataclass
class DemoContext:
    """演示上下文 - 提供演示执行环境信息"""
    demo_name: str
    output_dir: Path
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_output_path(self, filename: str) -> Path:
        """获取输出文件路径"""
        return self.output_dir / filename
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self.metadata.get(key, default)


class DemoFramework(ABC):
    """
    演示框架基类 - 提供统一的演示抽象
    
    这个基类定义了所有演示模块应该遵循的标准接口和生命周期：
    1. 初始化 (initialize)
    2. 验证前置条件 (validate_prerequisites)
    3. 执行演示 (execute_demo)
    4. 清理资源 (cleanup)
    """
    
    def __init__(self, context: DemoContext, services: Optional[Dict[str, Any]] = None):
        """
        初始化演示框架
        
        Args:
            context: 演示上下文
            services: 服务依赖字典 (可选，通常由ServiceRegistry提供)
        """
        self.context = context
        self.services = services or {}
        self.logger = self._setup_logger()
        self.start_time = None
        self.end_time = None
        
        # 演示状态
        self._status = DemoStatus.INITIALIZED
        self._result = None
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger_name = f'Demo.{self.__class__.__name__}'
        logger = logging.getLogger(logger_name)
        
        # 如果logger还没有handler，添加一个
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    @property
    def status(self) -> DemoStatus:
        """获取当前状态"""
        return self._status
    
    @property
    def result(self) -> Optional[DemoResult]:
        """获取演示结果"""
        return self._result
    
    def get_service(self, service_name: str) -> Any:
        """
        获取服务依赖
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            ServiceNotFoundError: 当服务不存在时
        """
        if service_name not in self.services:
            from .exceptions import ServiceNotFoundError
            raise ServiceNotFoundError(service_name)
        return self.services[service_name]
    
    def has_service(self, service_name: str) -> bool:
        """检查是否有指定服务"""
        return service_name in self.services
    
    @abstractmethod
    def validate_prerequisites(self) -> bool:
        """
        验证演示前置条件
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValidationError: 当验证失败时
        """
        pass
    
    @abstractmethod
    def execute_demo(self) -> DemoResult:
        """
        执行演示的抽象方法
        
        Returns:
            DemoResult: 演示结果
            
        Raises:
            DemoExecutionError: 当演示执行失败时
        """
        pass
    
    def cleanup(self):
        """
        清理资源 (可选实现)
        
        子类可以重写此方法来清理特定资源
        """
        pass
    
    def run(self) -> DemoResult:
        """
        运行完整的演示流程
        
        这是演示的主入口点，负责协调整个演示生命周期
        
        Returns:
            DemoResult: 演示结果
        """
        self.start_time = time.time()
        
        try:
            self.logger.info(f"🚀 开始执行演示: {self.context.demo_name}")
            
            # 1. 验证前置条件
            self._status = DemoStatus.VALIDATING
            self.logger.info("🔍 验证前置条件...")
            
            if not self.validate_prerequisites():
                raise ValidationError("前置条件验证失败")
            
            self.logger.info("✅ 前置条件验证通过")
            
            # 2. 执行演示
            self._status = DemoStatus.RUNNING
            self.logger.info("⚡ 执行演示逻辑...")
            
            result = self.execute_demo()
            
            # 3. 更新状态和时间
            self.end_time = time.time()
            result.execution_time = self.end_time - self.start_time
            
            if result.status == DemoStatus.COMPLETED:
                self._status = DemoStatus.COMPLETED
                self.logger.info(f"🎉 演示执行成功! 耗时: {result.execution_time:.2f}秒")
            else:
                self._status = DemoStatus.FAILED
                self.logger.error(f"❌ 演示执行失败! 状态: {result.status}")
            
            self._result = result
            return result
            
        except Exception as e:
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time if self.start_time else 0
            
            self._status = DemoStatus.FAILED
            self.logger.error(f"❌ 演示执行异常: {e}")
            
            # 创建失败结果
            result = DemoResult(
                status=DemoStatus.FAILED,
                execution_time=execution_time,
                errors=[str(e)]
            )
            
            self._result = result
            return result
            
        finally:
            # 4. 清理资源
            try:
                self.cleanup()
            except Exception as e:
                self.logger.warning(f"⚠️ 资源清理时发生异常: {e}")
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(demo={self.context.demo_name}, status={self.status})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}("
                f"demo={self.context.demo_name}, "
                f"status={self.status}, "
                f"services={list(self.services.keys())})")
