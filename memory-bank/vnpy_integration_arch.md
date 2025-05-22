# QTE vnpy 集成与本地模拟交易环境架构

**最后更新**: 2024-08-23

## 1. 背景与目标

### 1.1 当前痛点
*   QTE 项目虽然有内部的回测引擎和模拟交易所，但在策略从模拟迁移到实盘时，可能存在环境差异导致的行为不一致。
*   缺乏一个能在本地完整模拟实盘交易链路（包括网络延迟、API交互特性等）的测试环境。
*   直接对接实盘进行频繁测试风险高、成本高。

### 1.2 设计目标
1.  **统一接口层**：通过集成 `vnpy`，为策略提供统一的行情数据和交易执行接口，无论是连接 QTE 内部模拟环境还是真实交易所。
2.  **高保真本地测试**：创建一个自定义的 `vnpy` 网关，该网关连接到 QTE 内部实现的、模拟币安行为的交易所API。这使得策略可以在本地进行端到端的、接近实盘行为的测试。
3.  **平滑实盘过渡**：策略代码在本地模拟环境和真实交易环境（通过 `vnpy` 官方网关）中保持高度一致，只需切换配置即可。
4.  **利用 `vnpy` 生态**：复用 `vnpy` 成熟的事件引擎、主引擎、多样的官方交易网关和社区支持。

## 2. 核心架构组件

### 2.1 QTE 内部交易所API (模拟币安)
*   **职责**: 在 QTE 内部运行一个API服务（已知基于Flask实现），该服务模拟币安交易所的核心API功能（行情、下单、账户等）。
*   **实现**: 审视、适配并完善现有的 `qte/exchange/` Flask API 服务。
*   **交互**: 此API服务将作为自定义 `vnpy` 网关的目标。

### 2.2 自定义 `vnpy` 网关 (`MockBinanceGateway`)
*   **职责**: 作为一个标准的 `vnpy` 网关，但其网络请求目标是 QTE 内部交易所API。
*   **实现**: 基于 `vnpy` 官方的币安网关代码进行修改（主要是 `BASE_URL` 和认证逻辑）。
*   **位置**: `qte/custom_vnpy_gateways/`
*   **作用**: 使得 `vnpy` 的 `MainEngine` 可以像连接真实交易所一样连接到 QTE 的本地模拟环境。

### 2.3 QTE `vnpy` 适配层
*   **`VnpyDataSource`**: `qte/data/sources/vnpy_data_source.py`
    *   **职责**: 实现 QTE 的数据源接口，通过 `vnpy` `MainEngine` 和选定的网关（`MockBinanceGateway` 或官方币安网关）获取行情数据。
*   **`VnpyExecutionHandler`**: `qte/execution/vnpy_execution_handler.py`
    *   **职责**: 实现 QTE 的执行处理器接口，通过 `vnpy` `MainEngine` 和选定的网关发送和管理交易订单。

### 2.4 QTE 引擎管理器 (`EngineManager`)
*   **职责**: 根据配置加载和初始化合适的组件：
    *   **模式1 (纯内部模拟)**: 使用 QTE 原有的模拟数据源和撮合逻辑。
    *   **模式2 (本地vnpy模拟)**: 使用 `VnpyDataSource` + `VnpyExecutionHandler` + `MockBinanceGateway`。
    *   **模式3 (vnpy实盘/测试网)**: 使用 `VnpyDataSource` + `VnpyExecutionHandler` + `vnpy` 官方币安网关。

## 3. 数据流与交互

*   **本地模拟模式**:
    `策略 -> QTE抽象接口 -> VnpyDataSource/Handler -> vnpy.MainEngine -> MockBinanceGateway -> QTE内部交易所Flask API -> QTE撮合/账户`
*   **实盘模式**:
    `策略 -> QTE抽象接口 -> VnpyDataSource/Handler -> vnpy.MainEngine -> vnpy.OfficialBinanceGateway -> 真实币安API`

## 4. 设计决策与理由

*   **选择 `vnpy`**: 成熟的开源框架，社区活跃，支持众多交易所，提供事件驱动核心。
*   **自定义网关而非直接修改 `vnpy` 核心**: 保持与 `vnpy` 主版本的兼容性，降低升级 `vnpy` 时的冲突风险。自定义网关是 `vnpy` 支持的扩展方式。
*   **QTE 内部交易所API化 (基于现有Flask)**: 这是实现高保真本地模拟的关键，使得自定义网关有明确的"连接"目标。
*   **币安作为首要模拟和对接目标**: 币安API文档完善，用户基数大，作为起点具有代表性。

## 5. 开发计划

**Phase 1: 审视、适配并完善 `QTE` 内部交易所的现有 Flask API (以模拟币安为目标)**
*   **任务 1.1**: 审视并文档化现有 Flask API。
    *   **描述**: 详细梳理 `qte/exchange/` 中现有 Flask API 的所有端点、请求/响应格式、认证方式。与真实的币安API进行仔细对比。
    *   **产出**: 内部API文档, 币安API映射文档, 差距分析报告。
*   **任务 1.2**: 适配与扩展 Flask API 以满足 `MockBinanceGateway` 需求。
    *   **描述**: 根据任务 1.1 的差距分析，修改或扩展现有的 Flask API，使其行为尽可能接近真实币安API。
    *   **产出**: 更新后的 Flask API 服务代码。
*   **任务 1.3**: 强化 Flask API 的测试。
    *   **描述**: 确保所有关键的、经过调整或新增的API端点都有充分的单元测试和集成测试。
    *   **产出**: 更新和新增的 Flask API 测试用例。

**Phase 2: 创建自定义的 `vnpy` "模拟币安"网关 (`MockBinanceGateway`)**
*   **任务 2.1**: 复制并选取基础 `vnpy` 币安网关。
*   **任务 2.2**: 修改网关实现，对接 Phase 1 中完善后的 `QTE` 内部交易所 Flask API。
*   **任务 2.3**: 在 `QTE` 项目中注册自定义网关。
*   **任务 2.4**: 编写自定义网关的单元测试 (Mock `QTE` Flask API)。

**Phase 3: 实现 `QTE` 的 `vnpy` 适配层**
*   **任务 3.1**: 实现 `VnpyDataSource` (`qte/data/sources/vnpy_data_source.py`)。
*   **任务 3.2**: 实现 `VnpyExecutionHandler` (`qte/execution/vnpy_execution_handler.py`)。
*   **任务 3.3**: 编写 `VnpyDataSource` 和 `VnpyExecutionHandler` 的单元测试。

**Phase 4: `QTE` 核心逻辑调整与配置**
*   **任务 4.1**: 修改 `QTE` 引擎管理器 (`EngineManager` 或等效模块) 以支持多后端。
*   **任务 4.2**: 实现配置系统，允许方便地切换和配置 `vnpy` 网关。

**Phase 5: 集成测试**
*   **任务 5.1**: 端到端本地模拟环境测试。
*   **任务 5.2**: （可选，但推荐）连接币安测试网进行测试。

**Phase 6: 文档更新**
*   **任务 6.1**: 更新 `README.md`，详细说明新架构和使用方法。
*   **任务 6.2**: 持续更新此 `memory-bank` 文件，记录开发过程中的重要决策和变更。


## 6. 未来考虑与潜在挑战

*   **维护自定义网关**: 当 `vnpy` 官方币安网关或币安API本身发生较大变化时，需要同步更新 `MockBinanceGateway`。
*   **模拟交易所的完备性**: QTE 内部交易所API需要不断迭代以更精确地模拟真实交易所的行为（如错误处理、特定订单类型、流动性等）。
*   **性能**: 本地API服务的性能对于高频策略的模拟测试可能需要关注。
*   **扩展到其他交易所**: 未来可以类似地创建其他交易所的模拟API和对应的自定义 `vnpy` 网关。

## 7. 配置管理
*   通过外部配置文件（如 YAML/JSON）管理运行模式、API密钥、网关参数等，提高灵活性。 