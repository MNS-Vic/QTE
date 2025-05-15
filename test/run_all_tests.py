#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化回测框架测试入口脚本

本脚本用于一键运行所有的回测框架测试，包括:
1. 单独测试各个回测框架
2. 比较多个框架的性能
"""

import os
import sys
import time
import argparse

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_dependencies():
    """检查必要的依赖包是否已安装"""
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'psutil'
    ]
    
    optional_packages = [
        'vectorbt'
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print(f"缺少必要的依赖包: {', '.join(missing_required)}")
        print("请使用以下命令安装:")
        print(f"pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"警告: 缺少可选的依赖包: {', '.join(missing_optional)}")
        print("某些测试可能无法运行。请使用以下命令安装:")
        print(f"pip install {' '.join(missing_optional)}")
    
    return True

def run_single_test(framework, verbose=True):
    """运行单个框架的测试"""
    test_file = f"test_{framework}_backtest.py"
    test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_file)
    
    if not os.path.exists(test_path):
        print(f"测试文件不存在: {test_file}")
        return False
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"开始运行 {framework} 回测框架测试")
        print(f"{'='*50}")
    
    try:
        start_time = time.time()
        
        # 运行测试模块
        if framework == "vectorbt":
            from test.test_vectorbt_backtest import test_ma_crossover_strategy
            result = test_ma_crossover_strategy()
        elif framework == "lean":
            from test.test_lean_backtest import test_lean_backtest
            result = test_lean_backtest()
        elif framework == "vnpy":
            from test.test_vnpy_backtest import test_vnpy_backtest
            result = test_vnpy_backtest()
        else:
            print(f"未知的框架: {framework}")
            return False
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        if verbose:
            print(f"\n{framework} 测试完成，耗时: {elapsed:.4f} 秒")
        
        return True
    
    except Exception as e:
        print(f"\n运行 {framework} 测试时出错:")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_comparison(verbose=True):
    """运行框架比较测试"""
    if verbose:
        print(f"\n{'='*50}")
        print(f"开始运行回测框架性能比较")
        print(f"{'='*50}")
    
    try:
        from test.test_backtest_frameworks import compare_frameworks, recommend_framework
        
        # 运行比较
        perf_results = compare_frameworks()
        
        # 提供建议
        recommend_framework()
        
        return True
    
    except Exception as e:
        print(f"\n运行比较测试时出错:")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests(verbose=True):
    """运行所有测试"""
    frameworks = ["vectorbt", "lean", "vnpy"]
    
    results = {}
    for framework in frameworks:
        success = run_single_test(framework, verbose)
        results[framework] = success
    
    # 运行比较测试
    comparison_success = run_comparison(verbose)
    results["comparison"] = comparison_success
    
    # 输出汇总结果
    if verbose:
        print(f"\n{'='*50}")
        print(f"测试结果汇总")
        print(f"{'='*50}")
        
        for name, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"{name.ljust(15)}: {status}")
    
    # 所有测试都成功返回True
    return all(results.values())

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="量化回测框架测试工具")
    
    parser.add_argument(
        '--framework', '-f',
        choices=['vectorbt', 'lean', 'vnpy', 'all', 'comparison'],
        default='all',
        help='指定要测试的回测框架或运行所有测试'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，减少输出信息'
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    verbose = not args.quiet
    
    if args.framework == 'all':
        success = run_all_tests(verbose)
    elif args.framework == 'comparison':
        success = run_comparison(verbose)
    else:
        success = run_single_test(args.framework, verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 