# 项目初始架构描述 (中文)

## 概述

本文档用于存放量化回测引擎项目的初始架构设想。

## 架构图 (Mermaid)

```mermaid
-- 请在此处粘贴您最初提供的 Mermaid 架构图 --

graph TD
    subgraph "用户接口层 (User Interface Layer)"
        UI_Config[回测配置界面]
        UI_Strategy[策略选择/编辑器]
        UI_Results[结果展示/可视化]
    end

    subgraph "回测引擎核心 (Backtesting Engine Core)"
        BE_Coordinator[回测协调器/总控]
        BE_EventLoop[事件循环处理器]
        BE_TimeSim[时间模拟器]
    end

    subgraph "数据层 (Data Layer)"
        DM_Provider[数据提供者 Data Provider]
        DM_Storage[历史数据库/文件存储]
        DM_Loader[数据加载与预处理]
        DM_MarketData[实时/模拟行情数据流 Market Data Stream]
    end

    subgraph "策略层 (Strategy Layer)"
        SM_Loader[策略加载器 Strategy Loader]
        SM_Instance[策略实例 Strategy Instance]
        SM_SignalGen[信号生成器 Signal Generator]
        SM_Params[策略参数管理器]
    end

    subgraph "执行层 (Execution Layer)"
        EM_BrokerSim[模拟经纪商 Broker Simulator]
        EM_OrderManager[订单管理器 Order Manager]
        EM_FillHandler[成交处理器 Fill Handler]
        EM_Slippage[滑点模型 Slippage Model]
        EM_Commission[手续费模型 Commission Model]
    end

    subgraph "组合与风险管理层 (Portfolio & Risk Layer)"
        PM_Portfolio[投资组合管理器 Portfolio Manager]
        PM_Position[持仓跟踪器 Position Tracker]
        PM_Pnl[盈亏计算器 P&L Calculator]
        RM_Manager[风险管理器 Risk Manager]
    end

    subgraph "分析与报告层 (Analysis & Reporting Layer)"
        AR_Metrics[绩效指标计算器 Performance Metrics Calculator]
        AR_Logger[日志记录器 Logger]
        AR_Visualizer[结果可视化器 Result Visualizer]
        AR_ReportGen[报告生成器 Report Generator]
    end

    subgraph "参数优化层 (Parameter Optimization Layer)"
        PO_Optimizer[优化器 (网格/遗传/贝叶斯)]
        PO_TaskRunner[多任务运行器]
    end

    %% Connections
    UI_Config --> BE_Coordinator
    UI_Strategy --> SM_Loader
    UI_Results <-- AR_ReportGen
    UI_Results <-- AR_Visualizer

    BE_Coordinator -- 控制 --> BE_EventLoop
    BE_Coordinator -- 控制 --> BE_TimeSim
    BE_Coordinator -- 初始化 --> DM_Provider
    BE_Coordinator -- 初始化 --> SM_Loader
    BE_Coordinator -- 初始化 --> EM_BrokerSim
    BE_Coordinator -- 初始化 --> PM_Portfolio
    BE_Coordinator -- 初始化 --> RM_Manager
    BE_Coordinator -- 触发 --> PO_Optimizer

    BE_EventLoop -- 驱动 --> BE_TimeSim
    BE_EventLoop -- 派发事件 --> SM_Instance
    BE_EventLoop -- 派发事件 --> EM_OrderManager
    BE_EventLoop -- 派发事件 --> PM_Portfolio
    BE_EventLoop -- 派发事件 --> AR_Logger

    BE_TimeSim -- 产生时间事件 --> BE_EventLoop
    BE_TimeSim -- 请求数据 --> DM_MarketData

    DM_Provider -- 从 --> DM_Storage
    DM_Provider -- 使用 --> DM_Loader
    DM_Provider -- 提供 --> DM_MarketData
    DM_MarketData -- 提供数据 --> SM_Instance
    DM_MarketData -- 提供数据 --> EM_FillHandler  // 用于撮合
    DM_MarketData -- 提供数据 --> PM_Portfolio   // 用于市值更新

    SM_Loader -- 加载 --> SM_Instance
    SM_Instance -- 使用 --> SM_SignalGen
    SM_Instance -- 使用 --> SM_Params
    SM_Instance -- 接收数据 --> BE_EventLoop
    SM_Instance -- 生成交易指令 --> EM_OrderManager

    EM_OrderManager -- 提交订单 --> EM_BrokerSim
    EM_BrokerSim -- 处理订单 --> EM_FillHandler
    EM_FillHandler -- 使用 --> EM_Slippage
    EM_FillHandler -- 使用 --> EM_Commission
    EM_FillHandler -- 产生撮合事件 --> BE_EventLoop
    EM_FillHandler -- 更新 --> PM_Portfolio

    PM_Portfolio -- 管理 --> PM_Position
    PM_Portfolio -- 使用 --> PM_Pnl
    PM_Portfolio -- 接收撮合更新 --> BE_EventLoop
    PM_Portfolio -- 被查询 --> RM_Manager
    PM_Portfolio -- 被查询 --> AR_Metrics

    RM_Manager -- 检查 --> EM_OrderManager   // 如：禁止开仓
    RM_Manager -- 检查 --> PM_Portfolio    // 如：触发止损

    AR_Metrics -- 计算基于 --> PM_Portfolio
    AR_Metrics -- 计算基于 --> EM_FillHandler // 交易记录
    AR_Metrics -- 输出 --> AR_ReportGen
    AR_Metrics -- 输出 --> AR_Visualizer
    AR_Logger -- 记录 --> [日志文件/数据库]

    PO_Optimizer -- 多次回测 --> BE_Coordinator
    PO_Optimizer -- 使用 --> PO_TaskRunner
```

## 各模块详细说明

-- 请在此处粘贴您最初提供的各模块详细说明 --

**例如：**

### 用户接口层 (User Interface Layer)
*   **回测配置界面 (UI_Config):**
    *   选择回测标的、时间周期（开始/结束日期）、K线级别（日/分钟/Tick）。
    *   ...
*   **策略选择/编辑器 (UI_Strategy):**
    *   ...
*   **结果展示/可视化 (UI_Results):**
    *   ...

### 数据层 (Data Layer)
*   **历史数据库/文件存储 (DM_Storage):**
    *   ...
*   ...

**(以此类推，补充所有模块的说明)**