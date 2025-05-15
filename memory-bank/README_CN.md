# 量化回测引擎 - 项目管理知识库

## 简介

本知识库（Memory Bank）用于存储QTE（量化回测引擎）项目的各种规划、设计和开发文档。这些文档作为项目开发的指导和记录，帮助团队保持一致的开发方向和质量标准。

## 文档索引

### 架构与设计
- [项目初始架构](PROJECT_INITIAL_ARCHITECTURE_CN.md) - 初始项目架构和设计理念
- [架构优化方案](QTE_ARCHITECTURE_OPTIMIZATION_CN.md) - 基于借鉴其他框架后的架构优化方案
- [数据源规范](QTE_DATA_SOURCE_SPEC_CN.md) - 数据源模块的详细规范和接口定义

### 计划与任务
- [项目发展规划](QTE_DEVELOPMENT_PLAN_CN.md) - 项目长期发展目标和路线图
- [实施任务清单](QTE_IMPLEMENTATION_TASKS_CN.md) - 详细的开发任务分解和里程碑
- [项目计划任务](PROJECT_PLAN_TASKS_CN.md) - 项目初始规划任务

### 进展与记录
- [构建日志](BUILD_LOG_CN.md) - 项目构建过程的记录
- [规划模式概述](PLAN_MODE_OVERVIEW_CN.md) - 项目规划模式说明

## 使用指南

### 文档更新流程

1. **设计文档**：先在知识库中更新设计和规范，确保团队达成共识
2. **任务分解**：根据设计文档创建具体实施任务
3. **进度记录**：定期更新构建日志，记录实现进展和遇到的问题
4. **反馈与迭代**：根据实现过程中的经验反馈，更新和完善设计文档

### 命名规范

- 所有文档使用大写字母加下划线命名法
- 中文文档以`_CN`结尾
- 使用有意义的前缀分类文档，如`QTE_`表示量化回测引擎相关

## 最佳实践

1. **保持文档与代码同步**：代码改变时同步更新相关文档
2. **定期复审**：每月复审一次设计文档，确保其反映当前系统状态
3. **版本控制**：重大架构变更时，创建新版本的设计文档，而不是直接修改原文档
4. **决策记录**：记录重要设计决策及其原因，以便团队理解设计意图

## 目录结构约定

```
memory-bank/
├── README_CN.md                         # 本文件，知识库说明
├── PROJECT_INITIAL_ARCHITECTURE_CN.md   # 初始架构设计
├── QTE_ARCHITECTURE_OPTIMIZATION_CN.md  # 架构优化方案
├── QTE_DATA_SOURCE_SPEC_CN.md           # 数据源规范
├── QTE_DEVELOPMENT_PLAN_CN.md           # 项目发展规划
├── QTE_IMPLEMENTATION_TASKS_CN.md       # 实施任务清单
├── PROJECT_PLAN_TASKS_CN.md             # 项目规划任务
└── BUILD_LOG_CN.md                      # 构建日志
``` 