"""
QTE演示系统模块
提供完整的端到端量化交易演示功能
"""

__version__ = "1.0.0"
__author__ = "QTE Development Team"

from .simple_trading_demo import SimpleTradeDemo
from .advanced_trading_demo import AdvancedTradeDemo
from .demo_test_suite import DemoTestSuite

__all__ = [
    'SimpleTradeDemo',
    'AdvancedTradeDemo', 
    'DemoTestSuite'
]
