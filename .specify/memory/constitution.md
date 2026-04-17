<!-- Sync Impact Report
  Version change: N/A → 1.0.0 (initial ratification)
  Modified principles: N/A (first version)
  Added sections:
    - Core Principles: 3 principles (翻译质量优先, 测试优先, 模块化架构)
    - Performance & Portability Constraints
    - Development Workflow
    - Governance
  Removed sections: None (initial)
  Templates requiring updates:
    ✅ .specify/templates/plan-template.md — Constitution Check section is dynamic, compatible
    ✅ .specify/templates/spec-template.md — Requirements and testing sections align with principles
    ✅ .specify/templates/tasks-template.md — Phase structure compatible with modular architecture
    ✅ .specify/templates/checklist-template.md — Generic template, no updates needed
  Follow-up TODOs: None
-->

# Jimao Translator Constitution

## Core Principles

### I. Translation Quality First (翻译质量优先)

- 翻译准确性和自然度是最高优先级，MUST NOT 为性能或速度牺牲翻译质量
- 所有翻译输出 MUST 经过质量评估流程验证（自动化指标 + 人工抽检）
- 翻译引擎 MUST 支持上下文感知翻译，避免逐句/逐词机械翻译
- AI 翻译结果 MUST 提供置信度指标，低置信度翻译 MUST 明确标注
- 术语一致性 MUST 通过术语库（glossary）机制保证
- 语音翻译场景中，语音识别错误 MUST NOT 被无条件传递给翻译引擎，
  MUST 有纠错或置信度过滤机制

### II. Test-First (测试优先, NON-NEGOTIABLE)

- TDD 强制执行：先写测试 → 测试失败 → 再实现 → 测试通过 → 重构
- Red-Green-Refactor 循环严格遵守，无例外
- 翻译质量测试 MUST 包含：多语言对照测试集、边界用例
  （空输入、超长文本、特殊字符、混合语言）
- 语音翻译 MUST 包含端到端测试：语音输入 → 识别 → 翻译 → 输出验证
- 每个模块 MUST 有独立的单元测试，集成测试覆盖模块间交互
- 使用 pytest 作为测试框架，测试覆盖率 MUST >= 80%

### III. Modular Architecture (模块化架构)

- 每个功能域（文本翻译、语音识别、语音合成、AI 翻译）
  MUST 独立封装为可替换组件
- 模块间通过定义明确的接口（Protocol/ABC）通信，
  MUST NOT 直接依赖具体实现
- 翻译引擎 MUST 支持插件化：可通过配置切换不同翻译后端
  （API 服务、本地模型等）
- 每个模块 MUST 可独立测试、独立部署、独立更新
- 新增翻译场景 MUST 通过扩展（新增模块）实现，
  MUST NOT 修改已有模块的核心逻辑

## Performance & Portability Constraints

- 作为便携式随身翻译工具，应用启动时间 MUST < 3 秒
- 实时翻译延迟 MUST < 500ms（文本）/ < 2s（语音端到端）
- 内存占用 MUST < 500MB（含本地模型时 MUST < 2GB）
- MUST 支持离线模式下的基础翻译功能（至少覆盖常用语言对）
- 跨平台兼容：MUST 支持 Windows、macOS、Linux
- 所有外部 API 调用 MUST 有超时控制和降级策略

## Development Workflow

- 使用 Python 3.11+ 作为主要开发语言
- 依赖管理使用 pip + requirements.txt 或 Poetry
- 代码风格使用 Ruff 进行 lint 和格式化，MUST 通过 CI 检查
- 所有功能变更 MUST 通过 feature branch → PR → review → merge 流程
- 提交信息 MUST 遵循 Conventional Commits 规范
- 每个 PR MUST 包含对应的测试更新

## Governance

- 本宪法是项目开发的最高准则，所有代码审查 MUST 验证合规性
- 宪法修订流程：提出修改 → 记录理由 → 审批 → 更新版本号 → 通知团队
- 版本号遵循语义化版本：MAJOR（原则删除/重定义）、MINOR（新增原则/章节）、PATCH（措辞修订）
- 复杂度 MUST 有充分理由：每个架构决策 MUST 能解释为什么更简单的方案不可行

**Version**: 1.0.0 | **Ratified**: 2026-04-17 | **Last Amended**: 2026-04-17
