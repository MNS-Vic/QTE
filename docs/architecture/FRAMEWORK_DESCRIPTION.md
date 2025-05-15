# Quantitative Backtesting Engine - Framework Description

## 1. 引言

Quantitative Backtesting Engine (QTE) 是一个基于Python的开源量化回测框架。其核心目标是为量化策略开发者和研究人员提供一个**高效、真实、灵活且易于使用**的回测与研究平台。本项目致力于融合业界优秀回测框架的设计思想，提供从策略构思、开发、回测、优化到结果分析的全链路支持。

## 2. 核心架构原则

QTE的设计遵循以下核心原则：

*   **模块化 (Modularity):** 系统由清晰定义、功能独立的模块组成，如数据处理、策略逻辑、交易执行、风险管理和结果分析。这便于独立开发、测试和维护。
*   **可扩展性 (Extensibility):** 框架设计应易于扩展，方便用户添加新的数据源、自定义策略、集成新的技术指标、模拟不同的经纪商行为（未来）以及开发定制化的分析模块。
*   **双核回测模式 (Dual-Core Backtesting):**
    *   **事件驱动核心:** 提供高真实度的回测，模拟市场事件流，适合精细化策略验证和接近实盘的模拟。
    *   **向量化核心:** 提供极致的回测速度，利用NumPy和Pandas进行批量运算，适合策略的快速原型验证、大规模参数扫描和优化。
*   **数据源无关性 (Data Agnosticism):** 通过标准化的数据接口，支持从多种数据源（如CSV文件、API服务、数据库）获取数据，并统一内部数据格式。
*   **API驱动设计 (API-Driven Design):** 提供清晰、一致且用户友好的API，简化策略开发和系统交互的复杂度。
*   **性能优先 (Performance by Design):** 在保证功能的前提下，关注核心模块的性能，特别是在数据处理和回测执行方面。
*   **易用性 (Ease of Use):** 降低学习曲线，提供完善的文档和示例，使开发者能快速上手。

## 3. 关键组件 (模块)

QTE主要由以下模块构成：

*   **`qte_core` (核心引擎):**
    *   `event_driven_backtester.py`: 增强的事件驱动回测引擎。
    *   `vectorized_backtester.py`: 高性能向量化回测引擎。
    *   `event_system.py`: 事件定义、事件队列和事件分发机制。
    *   `data_structures.py`: 核心数据结构定义 (如Bar, Tick, Order, Trade, Position, Account)。

*   **`qte_data` (数据模块):**
    *   `base_data_provider.py`: 数据提供者抽象基类。
    *   `csv_data_provider.py`, `yf_data_provider.py`, `db_data_provider.py` (示例): 具体数据源实现。
    *   `data_loader.py`: 统一的数据加载和预处理接口。
    *   `data_utils.py`: 数据清洗、对齐、频率转换等工具函数。

*   **`qte_strategy` (策略模块):**
    *   `base_strategy.py`: 策略抽象基类，定义策略生命周期和核心方法 (`initialize`, `on_bar`, `on_tick`, `on_order`, `on_trade`等)。
    *   `strategy_parameter.py`: 策略参数定义和管理。
    *   `examples/`: 包含多种策略实现示例 (如均线交叉、布林带等)。

*   **`qte_indicators` (技术指标模块):**
    *   `base_indicator.py`: 指标基类。
    *   `indicator_factory.py`: 动态创建和管理指标实例。
    *   `ma.py`, `rsi.py`, `atr.py` (示例): 具体技术指标的实现，支持高效计算。
    *   考虑集成或封装 `TA-Lib` 等成熟库。

*   **`qte_execution` (交易执行模块):**
    *   `order_matching_engine.py`: 模拟订单撮合逻辑。
    *   `commission_model.py`: 手续费模型接口与实现。
    *   `slippage_model.py`: 滑点模型接口与实现。
    *   `order_types.py`: 支持多种订单类型 (市价单、限价单、止损单等)。

*   **`qte_portfolio_risk` (投资组合与风险管理模块):**
    *   `portfolio_manager.py`: 管理资产组合、持仓、现金、市值等。
    *   `performance_metrics.py`: 计算核心性能指标 (收益率、波动率、夏普比率、最大回撤等)。
    *   `risk_manager.py`: （可选，未来增强）实现风险控制规则，如止损、仓位限制等。

*   **`qte_analysis_reporting` (分析与报告模块):**
    *   `results_analyzer.py`: 深入分析回测结果，包括交易、持仓、盈亏等。
    *   `plotter.py`: 生成专业的、可交互的回测结果图表 (资金曲线、收益率分布、回撤图等)。
    *   `report_generator.py`: 生成HTML或PDF格式的综合回测报告。

*   **`qte_optimization` (参数优化模块):**
    *   `optimizer.py`: 实现参数优化算法 (网格搜索、随机搜索、遗传算法等)。
    *   `objective_functions.py`: 定义优化目标函数。
    *   `optimization_visualizer.py`: 参数优化结果可视化 (如热力图)。

*   **`qte_utils` (通用工具模块):**
    *   包含日志记录、配置管理、日期时间处理等通用辅助功能。

## 4. 系统工作流程

典型的用户使用QTE进行量化回测的流程如下：

1.  **数据准备:**
    *   用户通过 `qte_data` 模块配置并加载所需市场数据。
    *   数据被转换为内部标准格式。
2.  **策略编写:**
    *   用户继承 `qte_strategy.BaseStrategy` 类，实现自己的交易逻辑和参数。
    *   在策略中调用 `qte_indicators` 计算所需的技术指标。
3.  **回测配置:**
    *   用户选择回测模式 (事件驱动或向量化)。
    *   设置回测参数 (时间周期、初始资金、手续费、滑点等)。
4.  **执行回测:**
    *   `qte_core` 中的相应回测引擎根据配置运行策略。
    *   `qte_execution` 模块模拟订单执行和成交。
    *   `qte_portfolio_risk` 模块实时更新投资组合状态。
5.  **结果分析与报告:**
    *   回测结束后，`qte_analysis_reporting` 模块计算详细的性能指标。
    *   生成图表和结构化的回测报告。
6.  **策略优化 (可选):**
    *   用户可以使用 `qte_optimization` 模块对策略参数进行优化，寻找更优的参数组合。
    *   优化过程会多次执行回测步骤。

## 5. 技术栈 (初步)

*   **核心语言:** Python 3.8+
*   **数据处理:** Pandas, NumPy
*   **可视化:** Matplotlib, Plotly (用于交互式图表)
*   **性能加速 (可选):** Numba (用于加速特定计算密集型部分)
*   **指标计算 (可选):** TA-Lib

此框架描述将作为项目开发的指导性文档，并会随着项目的进展持续更新。 