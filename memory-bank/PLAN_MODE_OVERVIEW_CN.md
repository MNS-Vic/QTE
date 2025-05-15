# MEMORY BANK 规划模式概述 (中文)

## 核心职责

根据在"初始化模式"中确定的复杂度级别，为任务执行创建详细的计划。

## 工作流程

```mermaid
graph TD
    Start["🚀 开始规划"] --> ReadTasks["📚 阅读 tasks.md<br>(及 .cursor/rules/isolation_rules/main.mdc)"]

    %% 复杂度级别判定
    ReadTasks --> CheckLevel{"🧩 判定<br>复杂度级别"}
    CheckLevel -->|"级别 2"| Level2["📝 级别 2 规划<br>(参考 .cursor/rules/isolation_rules/visual-maps/plan-mode-map.mdc)"]
    CheckLevel -->|"级别 3"| Level3["📋 级别 3 规划<br>(参考 .cursor/rules/isolation_rules/visual-maps/plan-mode-map.mdc)"]
    CheckLevel -->|"级别 4"| Level4["📊 级别 4 规划<br>(参考 .cursor/rules/isolation_rules/visual-maps/plan-mode-map.mdc)"]

    %% 级别 2 规划
    Level2 --> L2Review["🔍 查看代码<br>结构"]
    L2Review --> L2Document["📄 文档化<br>计划的变更"]
    L2Document --> L2Challenges["⚠️ 识别<br>挑战"]
    L2Challenges --> L2Checklist["✅ 创建任务<br>检查清单"]
    L2Checklist --> L2Update["📝 更新 tasks.md<br>写入计划"]
    L2Update --> L2Verify["✓ 验证计划<br>完整性"]

    %% 级别 3 规划
    Level3 --> L3Review["🔍 查看代码库<br>结构"]
    L3Review --> L3Requirements["📋 文档化详细<br>需求"]
    L3Requirements --> L3Components["🧩 识别受影响<br>的组件"]
    L3Components --> L3Plan["📝 创建全面的<br>实施计划"]
    L3Plan --> L3Challenges["⚠️ 文档化挑战<br>与解决方案"]
    L3Challenges --> L3Update["📝 更新 tasks.md<br>写入计划"]
    L3Update --> L3Flag["🎨 标记需要<br>创造性阶段的组件"]
    L3Flag --> L3Verify["✓ 验证计划<br>完整性"]

    %% 级别 4 规划
    Level4 --> L4Analysis["🔍 代码库结构<br>分析"]
    L4Analysis --> L4Requirements["📋 文档化全面的<br>需求"]
    L4Requirements --> L4Diagrams["📊 创建架构<br>图表"]
    L4Diagrams --> L4Subsystems["🧩 识别受影响的<br>子系统"]
    L4Subsystems --> L4Dependencies["🔄 文档化依赖<br>与集成点"]
    L4Dependencies --> L4Plan["📝 创建分阶段的<br>实施计划"]
    L4Plan --> L4Update["📝 更新 tasks.md<br>写入计划"]
    L4Update --> L4Flag["🎨 标记需要<br>创造性阶段的组件"]
    L4Flag --> L4Verify["✓ 验证计划<br>完整性"]

    %% 验证与完成
    L2Verify & L3Verify & L4Verify --> CheckCreative{"🎨 是否需要<br>创造性<br>阶段?"}

    %% 模式转换
    CheckCreative -->|"是"| RecCreative["⏭️ 下一模式:<br>创造性模式"]
    CheckCreative -->|"否"| RecImplement["⏭️ 下一模式:<br>实施模式"]

    %% 模板选择
    L2Update -.- Template2["模板 L2:<br>- 概述<br>- 待修改文件<br>- 实施步骤<br>- 潜在挑战"]
    L3Update & L4Update -.- TemplateAdv["模板 L3-4:<br>- 需求分析<br>- 受影响组件<br>- 架构考虑<br>- 实施策略<br>- 详细步骤<br>- 依赖项<br>- 挑战与缓解<br>- 创造性阶段组件"]

    %% 验证选项
    Start -.-> Validation["🔍 验证选项:<br>- 查看复杂度级别<br>- 创建规划模板<br>- 识别创造性需求<br>- 生成计划文档<br>- 显示模式转换"]

    %% 样式
    style Start fill:#4da6ff,stroke:#0066cc,color:white
    style ReadTasks fill:#80bfff,stroke:#4da6ff
    style CheckLevel fill:#d94dbb,stroke:#a3378a,color:white
    style Level2 fill:#4dbb5f,stroke:#36873f,color:white
    style Level3 fill:#ffa64d,stroke:#cc7a30,color:white
    style Level4 fill:#ff5555,stroke:#cc0000,color:white
    style CheckCreative fill:#d971ff,stroke:#a33bc2,color:white
    style RecCreative fill:#ffa64d,stroke:#cc7a30
    style RecImplement fill:#4dbb5f,stroke:#36873f
```

## 实施步骤

### 步骤 1: 阅读主要规则与任务文档

*   读取 `.cursor/rules/isolation_rules/main.mdc` (如果存在且相关)
*   读取 `tasks.md` (或项目计划核心文件, 例如 `memory-bank/PROJECT_PLAN_TASKS_CN.md`)

### 步骤 2: 加载规划模式图

*   读取 `.cursor/rules/isolation_rules/visual-maps/plan-mode-map.mdc` (如果存在且相关, 作为流程参考)

### 步骤 3: 加载特定复杂度的规划参考

根据从 `tasks.md` (或核心项目计划文件) 中确定的复杂度级别，加载相应的参考规则文档 (如果存在且相关)：

#### 级别 2:
*   例如: `.cursor/rules/isolation_rules/Level2/task-tracking-basic.mdc`

#### 级别 3:
*   例如: `.cursor/rules/isolation_rules/Level3/task-tracking-intermediate.mdc`
*   例如: `.cursor/rules/isolation_rules/Level3/planning-comprehensive.mdc`

#### 级别 4:
*   例如: `.cursor/rules/isolation_rules/Level4/task-tracking-advanced.mdc`
*   例如: `.cursor/rules/isolation_rules/Level4/architectural-planning.mdc`

## 规划方法

根据初始化阶段确定的复杂度级别，创建一个详细的实施计划。你的方法应提供清晰的指导，同时保持对项目需求和技术限制的适应性。

### 级别 2: 简单增强规划

对于级别 2 的任务，专注于创建一个简化的计划，识别所需的具体变更和任何潜在挑战。查看代码库结构以了解受增强影响的区域，并文档化一个直接的实施方法。

```mermaid
graph TD
    L2["📝 级别 2 规划"] --> Doc["计划文档包含以下组件:"]
    Doc --> OV["📋 变更概述"]
    Doc --> FM["📁 待修改文件"]
    Doc --> IS["🔄 实施步骤"]
    Doc --> PC["⚠️ 潜在挑战"]
    Doc --> TS["✅ 测试策略"]

    style L2 fill:#4dbb5f,stroke:#36873f,color:white
    style Doc fill:#80bfff,stroke:#4da6ff
    style OV fill:#cce6ff,stroke:#80bfff
    style FM fill:#cce6ff,stroke:#80bfff
    style IS fill:#cce6ff,stroke:#80bfff
    style PC fill:#cce6ff,stroke:#80bfff
    style TS fill:#cce6ff,stroke:#80bfff
```

### 级别 3-4: 全面规划

对于级别 3-4 的任务，制定一个全面的计划，解决架构、依赖关系和集成点问题。识别需要创造性阶段的组件，并文档化详细的需求。对于级别 4 的任务，包括架构图并提出分阶段的实施方法。

```mermaid
graph TD
    L34["📊 级别 3-4 规划"] --> Doc["计划文档包含以下组件:"]
    Doc --> RA["📋 需求分析"]
    Doc --> CA["🧩 受影响组件"]
    Doc --> AC["🏗️ 架构考虑"]
    Doc --> IS_strat["📝 实施策略"]
    Doc --> DS["🔢 详细步骤"]
    Doc --> DP["🔄 依赖项"]
    Doc --> CM["⚠️ 挑战与缓解措施"]
    Doc --> CP["🎨 创造性阶段组件"]

    style L34 fill:#ffa64d,stroke:#cc7a30,color:white
    style Doc fill:#80bfff,stroke:#4da6ff
    style RA fill:#ffe6cc,stroke:#ffa64d
    style CA fill:#ffe6cc,stroke:#ffa64d
    style AC fill:#ffe6cc,stroke:#ffa64d
    style IS_strat fill:#ffe6cc,stroke:#ffa64d
    style DS fill:#ffe6cc,stroke:#ffa64d
    style DP fill:#ffe6cc,stroke:#ffa64d
    style CM fill:#ffe6cc,stroke:#ffa64d
    style CP fill:#ffe6cc,stroke:#ffa64d
```

## 创造性阶段识别

```mermaid
graph TD
    CPI["🎨 创造性阶段识别"] --> Question{"组件是否需要<br>设计决策?"}
    Question -->|"是"| Identify["标记为创造性阶段"]
    Question -->|"否"| Skip["进入实施阶段"]

    Identify --> Types["识别创造性阶段类型:"]
    Types --> ArchD["🏗️ 架构设计"]
    Types --> AlgoD["⚙️ 算法设计"]
    Types --> UIUXD["🎨 UI/UX 设计"]

    style CPI fill:#d971ff,stroke:#a33bc2,color:white
    style Question fill:#80bfff,stroke:#4da6ff
    style Identify fill:#ffa64d,stroke:#cc7a30
    style Skip fill:#4dbb5f,stroke:#36873f
    style Types fill:#ffe6cc,stroke:#ffa64d
```

识别需要创造性解决问题或重大设计决策的组件。对于这些组件，将其标记为进入"创造性模式"。关注架构考虑、算法设计需求或 UI/UX 需求，这些方面将从结构化设计探索中受益。

## 验证

```mermaid
graph TD
    V["✅ 验证检查清单"] --> P["计划是否解决了所有需求?"]
    V --> C["是否识别了需要创造性阶段的组件?"]
    V --> S["实施步骤是否清晰定义?"]
    V --> D["依赖项和挑战是否已文档化?"]

    P & C & S & D --> Decision{"全部验证通过?"}
    Decision -->|"是"| Complete["准备进入下一模式"]
    Decision -->|"否"| Fix["完成缺失项目"]

    style V fill:#4dbbbb,stroke:#368787,color:white
    style Decision fill:#ffa64d,stroke:#cc7a30,color:white
    style Complete fill:#5fd94d,stroke:#3da336,color:white
    style Fix fill:#ff5555,stroke:#cc0000,color:white
```

在完成规划阶段之前，验证计划是否解决了所有需求，是否识别了需要创造性阶段的组件，实施步骤是否清晰定义，以及依赖项和挑战是否已文档化。用完整的计划更新 `tasks.md` (或核心项目计划文件)，并根据是否需要创造性阶段推荐合适的下一模式。 