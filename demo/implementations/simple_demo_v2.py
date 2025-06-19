"""
简单演示 V2 - 基于新架构的重构版本
"""

import time
from typing import Dict, Any
from pathlib import Path

from ..framework import DemoFramework, DemoResult, DemoStatus, DemoContext
from ..framework.exceptions import ValidationError, DemoExecutionError


class SimpleDemoV2(DemoFramework):
    """
    简单演示 V2 - 重构后的简单演示
    
    展示基础量化交易流程：
    1. 生成示例市场数据
    2. 创建移动平均策略
    3. 执行回测
    4. 生成报告
    """
    
    def validate_prerequisites(self) -> bool:
        """验证前置条件"""
        self.logger.info("🔍 验证简单演示前置条件...")
        
        # 检查必需的服务
        required_services = ['data_generator', 'strategy_engine', 'backtester', 'report_generator']
        missing_services = []
        
        for service_name in required_services:
            if not self.has_service(service_name):
                missing_services.append(service_name)
        
        if missing_services:
            raise ValidationError(f"缺少必需的服务: {missing_services}")
        
        # 检查配置参数
        config = self.context.config
        
        # 验证初始资金
        initial_capital = config.get('initial_capital', 0)
        if initial_capital <= 0:
            raise ValidationError("初始资金必须大于0", "initial_capital")
        
        # 验证测试标的
        test_symbols = config.get('test_symbols', [])
        if not test_symbols or len(test_symbols) == 0:
            raise ValidationError("测试标的列表不能为空", "test_symbols")
        
        # 验证测试周期
        test_period_days = config.get('test_period_days', 0)
        if test_period_days <= 0:
            raise ValidationError("测试周期必须大于0天", "test_period_days")
        
        self.logger.info("✅ 前置条件验证通过")
        return True
    
    def execute_demo(self) -> DemoResult:
        """执行简单演示"""
        self.logger.info("🚀 开始执行简单演示...")
        
        result = DemoResult(
            status=DemoStatus.RUNNING,
            execution_time=0.0
        )
        
        try:
            # 第1步：生成示例数据
            self.logger.info("📊 第1步：生成示例市场数据...")
            market_data = self._generate_market_data(result)
            
            # 第2步：创建交易策略
            self.logger.info("🧠 第2步：创建简单移动平均策略...")
            strategy = self._create_trading_strategy(result)
            
            # 第3步：执行回测
            self.logger.info("🔄 第3步：执行回测...")
            backtest_result = self._run_backtest(market_data, strategy, result)
            
            # 第4步：生成报告
            self.logger.info("📋 第4步：生成回测报告...")
            report_info = self._generate_report(backtest_result, result)
            
            # 更新结果状态
            result.status = DemoStatus.COMPLETED
            
            # 设置输出数据
            result.outputs = {
                'market_data': market_data,
                'backtest_result': backtest_result,
                'report_info': report_info,
                'demo_type': 'simple',
                'demo_version': 'v2'
            }
            
            # 设置关键指标
            if hasattr(backtest_result, 'metrics'):
                result.metrics = backtest_result.metrics.copy()
            
            # 添加演示特定指标
            result.metrics.update({
                'data_generation_time': result.metadata.get('data_generation_time', 0),
                'strategy_creation_time': result.metadata.get('strategy_creation_time', 0),
                'backtest_execution_time': result.metadata.get('backtest_execution_time', 0),
                'report_generation_time': result.metadata.get('report_generation_time', 0)
            })
            
            self.logger.info("🎉 简单演示执行成功!")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 简单演示执行失败: {e}")
            result.status = DemoStatus.FAILED
            result.add_error(str(e))
            raise DemoExecutionError("SimpleDemoV2", e)
    
    def _generate_market_data(self, result: DemoResult) -> Dict[str, Any]:
        """生成市场数据"""
        start_time = time.time()
        
        try:
            data_generator = self.get_service('data_generator')
            
            # 从配置获取参数
            config = self.context.config
            symbols = config.get('test_symbols', ['AAPL', 'GOOGL', 'MSFT'])
            period_days = config.get('test_period_days', 30)
            
            # 生成数据
            market_data = data_generator.generate_sample_data(
                symbols=symbols,
                period_days=period_days
            )
            
            # 记录执行时间
            execution_time = time.time() - start_time
            result.metadata['data_generation_time'] = execution_time
            
            self.logger.info(f"✅ 市场数据生成完成，耗时: {execution_time:.2f}秒")
            return market_data
            
        except Exception as e:
            self.logger.error(f"❌ 市场数据生成失败: {e}")
            raise
    
    def _create_trading_strategy(self, result: DemoResult) -> Any:
        """创建交易策略"""
        start_time = time.time()
        
        try:
            strategy_engine = self.get_service('strategy_engine')
            
            # 从配置获取策略参数
            config = self.context.config
            strategy_type = config.get('strategy_type', 'moving_average')
            
            # 策略参数
            strategy_params = {
                'short_window': config.get('short_window', 5),
                'long_window': config.get('long_window', 15)
            }
            
            # 创建策略
            strategy = strategy_engine.create_strategy(
                strategy_type=strategy_type,
                parameters=strategy_params
            )
            
            # 记录执行时间
            execution_time = time.time() - start_time
            result.metadata['strategy_creation_time'] = execution_time
            
            self.logger.info(f"✅ 策略创建完成: {strategy_type}，耗时: {execution_time:.2f}秒")
            return strategy
            
        except Exception as e:
            self.logger.error(f"❌ 策略创建失败: {e}")
            raise
    
    def _run_backtest(self, market_data: Dict[str, Any], strategy: Any, result: DemoResult) -> Any:
        """执行回测"""
        start_time = time.time()
        
        try:
            backtester = self.get_service('backtester')
            
            # 从配置获取回测参数
            config = self.context.config
            initial_capital = config.get('initial_capital', 100000.0)
            
            # 执行回测
            backtest_result = backtester.run_backtest(
                data=market_data,
                strategy=strategy,
                initial_capital=initial_capital
            )
            
            # 记录执行时间
            execution_time = time.time() - start_time
            result.metadata['backtest_execution_time'] = execution_time
            
            self.logger.info(f"✅ 回测执行完成，总交易次数: {backtest_result.total_trades}，耗时: {execution_time:.2f}秒")
            return backtest_result
            
        except Exception as e:
            self.logger.error(f"❌ 回测执行失败: {e}")
            raise
    
    def _generate_report(self, backtest_result: Any, result: DemoResult) -> Dict[str, Any]:
        """生成报告"""
        start_time = time.time()
        
        try:
            report_generator = self.get_service('report_generator')
            
            # 准备额外数据
            additional_data = {
                'demo_name': self.context.demo_name,
                'demo_version': 'v2',
                'config': self.context.config,
                'execution_metadata': result.metadata
            }
            
            # 生成报告
            report_info = report_generator.generate_backtest_report(
                backtest_result=backtest_result,
                demo_name=f"{self.context.demo_name}_v2",
                additional_data=additional_data
            )
            
            # 记录执行时间
            execution_time = time.time() - start_time
            result.metadata['report_generation_time'] = execution_time
            
            self.logger.info(f"✅ 报告生成完成，耗时: {execution_time:.2f}秒")
            return report_info
            
        except Exception as e:
            self.logger.error(f"❌ 报告生成失败: {e}")
            raise
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("🧹 清理简单演示资源...")
        
        # 这里可以添加特定的清理逻辑
        # 例如：清理临时文件、关闭连接等
        
        # 记录清理完成
        self.context.set_metadata('cleanup_completed', True)
        self.logger.info("✅ 资源清理完成")
    
    def get_demo_info(self) -> Dict[str, Any]:
        """获取演示信息"""
        return {
            'name': 'SimpleDemoV2',
            'version': '2.0.0',
            'description': '基于新架构的简单量化交易演示',
            'features': [
                '示例市场数据生成',
                '移动平均策略',
                '完整回测流程',
                '多格式报告生成'
            ],
            'required_services': ['data_generator', 'strategy_engine', 'backtester', 'report_generator'],
            'estimated_duration': '5-10秒',
            'complexity': 'simple'
        }
