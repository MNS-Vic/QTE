#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V1到V2迁移工具

提供代码分析、兼容性检查和自动迁移功能
"""

import ast
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

# 导入在需要时进行，避免循环依赖


@dataclass
class CompatibilityIssue:
    """兼容性问题"""
    severity: str  # "error", "warning", "info"
    category: str  # "api_change", "deprecated", "performance", "behavior"
    description: str
    suggestion: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None


@dataclass
class MigrationReport:
    """迁移报告"""
    total_issues: int
    errors: int
    warnings: int
    infos: int
    issues: List[CompatibilityIssue]
    compatibility_score: float  # 0-100
    migration_complexity: str  # "simple", "moderate", "complex"
    estimated_effort: str  # "1-2 hours", "1-2 days", etc.


class V1ToV2Migrator:
    """
    V1到V2迁移器
    
    分析V1代码，检查兼容性问题，提供迁移建议
    """
    
    def __init__(self):
        """初始化迁移器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # V1 API映射到V2 API
        self._api_mappings = {
            # 方法映射
            "set_initial_capital": "initialize({'initial_capital': value})",
            "set_commission": "initialize({'commission': value})",
            "get_portfolio_value": "get_metrics()['portfolio_value']",
            "get_total_return": "get_metrics()['total_return']",
            "get_positions": "get_metrics()['positions']",
            "get_trades": "get_metrics()['trades']",
            "run": "run_backtest()",
            
            # 属性映射
            "portfolio_value": "get_metrics()['portfolio_value']",
            "initial_capital": "config['initial_capital']",
            "commission": "config['commission']",
            "data": "internal data (use set_data())",
            "strategies": "internal strategies (use add_strategy())",
            "results": "backtest result object"
        }
        
        # 已弃用的API
        self._deprecated_apis = {
            "set_initial_capital": "使用 initialize() 方法",
            "set_commission": "使用 initialize() 方法",
            "portfolio_value": "使用 get_metrics() 方法",
            "direct_attribute_access": "使用相应的方法调用"
        }
        
        # V1特有的模式
        self._v1_patterns = [
            "VectorEngine()",
            ".set_initial_capital(",
            ".set_commission(",
            ".portfolio_value",
            ".get_portfolio_value()",
            ".get_total_return()",
            ".run(",
            "engine.data",
            "engine.strategies",
            "engine.results"
        ]
        
        self.logger.info("✅ V1到V2迁移器初始化完成")
    
    def analyze_code(self, code: str, filename: str = "unknown") -> MigrationReport:
        """
        分析代码兼容性
        
        Parameters
        ----------
        code : str
            要分析的代码
        filename : str, optional
            文件名, by default "unknown"
            
        Returns
        -------
        MigrationReport
            迁移报告
        """
        try:
            issues = []
            
            # 解析代码
            try:
                tree = ast.parse(code)
                issues.extend(self._analyze_ast(tree))
            except SyntaxError as e:
                issues.append(CompatibilityIssue(
                    severity="error",
                    category="syntax",
                    description=f"语法错误: {e}",
                    suggestion="修复语法错误后重新分析",
                    line_number=e.lineno
                ))
            
            # 文本模式分析
            issues.extend(self._analyze_text_patterns(code))
            
            # 生成报告
            report = self._generate_report(issues, filename)
            
            self.logger.info(f"代码分析完成: {filename} ({report.total_issues} 个问题)")
            return report
            
        except Exception as e:
            self.logger.error("代码分析失败: %s", e)
            return MigrationReport(
                total_issues=1,
                errors=1,
                warnings=0,
                infos=0,
                issues=[CompatibilityIssue(
                    severity="error",
                    category="analysis",
                    description="分析失败: %s" % str(e),
                    suggestion="请检查代码格式和内容"
                )],
                compatibility_score=0.0,
                migration_complexity="unknown",
                estimated_effort="unknown"
            )
    
    def analyze_file(self, filepath: str) -> MigrationReport:
        """
        分析文件兼容性
        
        Parameters
        ----------
        filepath : str
            文件路径
            
        Returns
        -------
        MigrationReport
            迁移报告
        """
        try:
            path = Path(filepath)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {filepath}")
            
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return self.analyze_code(code, path.name)
            
        except Exception as e:
            self.logger.error("文件分析失败: %s", e)
            return MigrationReport(
                total_issues=1,
                errors=1,
                warnings=0,
                infos=0,
                issues=[CompatibilityIssue(
                    severity="error",
                    category="file",
                    description="文件分析失败: %s" % str(e),
                    suggestion="检查文件路径和权限"
                )],
                compatibility_score=0.0,
                migration_complexity="unknown",
                estimated_effort="unknown"
            )
    
    def _analyze_ast(self, tree: ast.AST) -> List[CompatibilityIssue]:
        """分析AST"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查方法调用
            if isinstance(node, ast.Call):
                issues.extend(self._check_method_call(node))
            
            # 检查属性访问
            elif isinstance(node, ast.Attribute):
                issues.extend(self._check_attribute_access(node))
            
            # 检查类实例化
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "VectorEngine":
                    issues.append(CompatibilityIssue(
                        severity="warning",
                        category="api_change",
                        description="使用了V1的VectorEngine类",
                        suggestion="考虑使用UnifiedVectorEngine或VectorEngineV1Compat",
                        line_number=getattr(node, 'lineno', None)
                    ))
        
        return issues
    
    def _check_method_call(self, node: ast.Call) -> List[CompatibilityIssue]:
        """检查方法调用"""
        issues = []
        
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            if method_name in self._api_mappings:
                issues.append(CompatibilityIssue(
                    severity="warning",
                    category="api_change",
                    description=f"V1方法 '{method_name}' 在V2中有变化",
                    suggestion=f"建议使用: {self._api_mappings[method_name]}",
                    line_number=getattr(node, 'lineno', None)
                ))
            
            if method_name in self._deprecated_apis:
                issues.append(CompatibilityIssue(
                    severity="warning",
                    category="deprecated",
                    description=f"方法 '{method_name}' 已弃用",
                    suggestion=self._deprecated_apis[method_name],
                    line_number=getattr(node, 'lineno', None)
                ))
        
        return issues
    
    def _check_attribute_access(self, node: ast.Attribute) -> List[CompatibilityIssue]:
        """检查属性访问"""
        issues = []
        
        attr_name = node.attr
        
        if attr_name in self._api_mappings:
            issues.append(CompatibilityIssue(
                severity="info",
                category="api_change",
                description=f"V1属性 '{attr_name}' 在V2中的访问方式有变化",
                suggestion=f"建议使用: {self._api_mappings[attr_name]}",
                line_number=getattr(node, 'lineno', None)
            ))
        
        return issues
    
    def _analyze_text_patterns(self, code: str) -> List[CompatibilityIssue]:
        """分析文本模式"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self._v1_patterns:
                if pattern in line:
                    issues.append(CompatibilityIssue(
                        severity="info",
                        category="pattern",
                        description=f"检测到V1模式: {pattern}",
                        suggestion="检查是否需要迁移到V2 API",
                        line_number=i,
                        code_snippet=line.strip()
                    ))
        
        return issues
    
    def _generate_report(self, issues: List[CompatibilityIssue], filename: str = "unknown") -> MigrationReport:
        """生成迁移报告"""
        errors = sum(1 for issue in issues if issue.severity == "error")
        warnings = sum(1 for issue in issues if issue.severity == "warning")
        infos = sum(1 for issue in issues if issue.severity == "info")
        
        # 计算兼容性分数
        total_issues = len(issues)
        if total_issues == 0:
            compatibility_score = 100.0
        else:
            # 错误权重3，警告权重2，信息权重1
            weighted_issues = errors * 3 + warnings * 2 + infos * 1
            max_possible_score = total_issues * 3
            compatibility_score = max(0, 100 - (weighted_issues / max_possible_score * 100))
        
        # 确定迁移复杂度
        if errors > 0:
            migration_complexity = "complex"
            estimated_effort = "1-2 weeks"
        elif warnings > 5:
            migration_complexity = "moderate"
            estimated_effort = "2-3 days"
        elif warnings > 0 or infos > 10:
            migration_complexity = "simple"
            estimated_effort = "1-2 days"
        else:
            migration_complexity = "minimal"
            estimated_effort = "1-2 hours"
        
        return MigrationReport(
            total_issues=total_issues,
            errors=errors,
            warnings=warnings,
            infos=infos,
            issues=issues,
            compatibility_score=compatibility_score,
            migration_complexity=migration_complexity,
            estimated_effort=estimated_effort
        )
    
    def generate_migration_guide(self, report: MigrationReport) -> str:
        """
        生成迁移指南
        
        Parameters
        ----------
        report : MigrationReport
            迁移报告
            
        Returns
        -------
        str
            迁移指南文本
        """
        guide = []
        guide.append("# V1到V2迁移指南")
        guide.append("=" * 50)
        guide.append("")
        
        # 概述
        guide.append("## 迁移概述")
        guide.append(f"- 兼容性分数: {report.compatibility_score:.1f}/100")
        guide.append(f"- 迁移复杂度: {report.migration_complexity}")
        guide.append(f"- 预估工作量: {report.estimated_effort}")
        guide.append(f"- 总问题数: {report.total_issues}")
        guide.append(f"  - 错误: {report.errors}")
        guide.append(f"  - 警告: {report.warnings}")
        guide.append(f"  - 信息: {report.infos}")
        guide.append("")
        
        # 迁移策略
        guide.append("## 推荐迁移策略")
        if report.errors > 0:
            guide.append("1. **渐进式迁移**: 先使用VectorEngineV1Compat保持兼容性")
            guide.append("2. **逐步替换**: 逐个替换V1 API调用")
            guide.append("3. **测试验证**: 每次修改后进行充分测试")
        elif report.warnings > 0:
            guide.append("1. **直接迁移**: 可以直接迁移到UnifiedVectorEngine")
            guide.append("2. **API更新**: 更新已弃用的API调用")
            guide.append("3. **性能优化**: 利用V2的性能优势")
        else:
            guide.append("1. **无缝迁移**: 代码基本兼容，可直接使用新引擎")
            guide.append("2. **性能提升**: 考虑启用V2的高性能特性")
        guide.append("")
        
        # 具体问题
        if report.issues:
            guide.append("## 具体问题和建议")
            for i, issue in enumerate(report.issues, 1):
                guide.append(f"### 问题 {i}: {issue.description}")
                guide.append(f"- **严重程度**: {issue.severity}")
                guide.append(f"- **类别**: {issue.category}")
                if issue.line_number:
                    guide.append(f"- **行号**: {issue.line_number}")
                if issue.code_snippet:
                    guide.append(f"- **代码**: `{issue.code_snippet}`")
                guide.append(f"- **建议**: {issue.suggestion}")
                guide.append("")
        
        # 示例代码
        guide.append("## 迁移示例")
        guide.append("### V1代码")
        guide.append("```python")
        guide.append("from qte.core.vector_engine import VectorEngine")
        guide.append("")
        guide.append("engine = VectorEngine()")
        guide.append("engine.set_initial_capital(100000)")
        guide.append("engine.set_commission(0.001)")
        guide.append("engine.set_data(data)")
        guide.append("engine.add_strategy(strategy)")
        guide.append("result = engine.run()")
        guide.append("portfolio_value = engine.portfolio_value")
        guide.append("```")
        guide.append("")
        
        guide.append("### V2代码（推荐）")
        guide.append("```python")
        guide.append("from qte.core.engines import UnifiedVectorEngine")
        guide.append("")
        guide.append("engine = UnifiedVectorEngine(compatibility_mode='auto')")
        guide.append("engine.initialize({")
        guide.append("    'initial_capital': 100000,")
        guide.append("    'commission': 0.001")
        guide.append("})")
        guide.append("engine.set_data(data)")
        guide.append("engine.add_strategy(strategy)")
        guide.append("result = engine.run_backtest()")
        guide.append("portfolio_value = engine.get_metrics()['portfolio_value']")
        guide.append("```")
        guide.append("")
        
        guide.append("### 兼容性代码（过渡期）")
        guide.append("```python")
        guide.append("from qte.core.engines import VectorEngineV1Compat")
        guide.append("")
        guide.append("# 完全兼容V1 API")
        guide.append("engine = VectorEngineV1Compat()")
        guide.append("engine.set_initial_capital(100000)")
        guide.append("engine.set_commission(0.001)")
        guide.append("# ... 其他V1代码无需修改")
        guide.append("```")
        
        return "\n".join(guide)


def check_compatibility(code: str = None, filepath: str = None) -> MigrationReport:
    """
    检查代码兼容性（便捷函数）
    
    Parameters
    ----------
    code : str, optional
        要检查的代码
    filepath : str, optional
        要检查的文件路径
        
    Returns
    -------
    MigrationReport
        兼容性报告
    """
    migrator = V1ToV2Migrator()
    
    if code is not None:
        return migrator.analyze_code(code)
    elif filepath is not None:
        return migrator.analyze_file(filepath)
    else:
        raise ValueError("必须提供code或filepath参数")


def generate_migration_guide(report: MigrationReport) -> str:
    """生成迁移指南（便捷函数）"""
    migrator = V1ToV2Migrator()
    return migrator.generate_migration_guide(report)
