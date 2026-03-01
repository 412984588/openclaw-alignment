# 工具调度配置 (Agent Dispatch Configuration)

> 此文件定义可用的 AI Agents、触发条件和调度策略
> OpenClaw Alignment 系统根据任务类型自动选择最合适的 Agent

## Agent 定义 (Agent Definitions)

### Codex Agent

```yaml
name: codex
display_name: "OpenAI Codex"
description: "代码生成和修复专家"
capabilities:
  - 代码生成
  - Bug 修复
  - 代码重构
  - 单元测试编写
tech_stack:
  - Python
  - JavaScript
  - TypeScript
  - Go
  - Rust
  - Java
  - C++
trigger_conditions:
  - task_type: "code_generation"
  - task_type: "bug_fix"
  - task_type: "refactoring"
  - code_size: "medium_to_large" # > 100 lines
cost_per_use: "medium"
response_time: "fast"
```

### Gemini Agent

```yaml
name: gemini
display_name: "Google Gemini"
description: "代码审查和安全专家"
capabilities:
  - 代码审查
  - 安全审计
  - 性能分析
  - 最佳实践建议
tech_stack:
  - 全栈（语言无关）
trigger_conditions:
  - task_type: "code_review"
  - task_type: "security_audit"
  - task_type: "performance_analysis"
  - requires_critical_eye: true
cost_per_use: "low"
response_time: "medium"
```

### Claude Agent

```yaml
name: claude
display_name: "Anthropic Claude"
description: "全栈开发协调者"
capabilities:
  - 需求分析
  - 架构设计
  - 任务编排
  - 代码审查
  - 技术方案制定
tech_stack:
  - 全栈（语言无关）
trigger_conditions:
  - task_type: "planning"
  - task_type: "coordination"
  - task_type: "architecture_design"
  - requires_deep_reasoning: true
cost_per_use: "medium"
response_time: "medium"
```

### Debug Agent

```yaml
name: debug
display_name: "调试专家"
description: "系统性调试和问题诊断"
capabilities:
  - Bug 复现
  - 根因分析
  - 日志分析
  - 性能剖析
tech_stack:
  - 全栈（语言无关）
trigger_conditions:
  - task_type: "debugging"
  - has_error: true
  - requires_investigation: true
cost_per_use: "low"
response_time: "fast"
```

### Test Agent

```yaml
name: test
display_name: "测试专家"
description: "测试策略和用例设计"
capabilities:
  - 测试用例设计
  - 测试覆盖率分析
  - 测试框架选型
  - 集成测试规划
tech_stack:
  - pytest
  - jest
  - unittest
  - Testcontainers
trigger_conditions:
  - task_type: "testing"
  - requires_test_coverage: true
  - quality_gate: true
cost_per_use: "low"
response_time: "fast"
```

### Refactor Agent

```yaml
name: refactor
display_name: "重构专家"
description: "代码重构和优化"
capabilities:
  - 代码重构
  - 性能优化
  - 技术债务清理
  - 架构优化
tech_stack:
  - 全栈（语言无关）
trigger_conditions:
  - task_type: "refactoring"
  - tech_debt_detected: true
  - performance_issue: true
cost_per_use: "medium"
response_time: "medium"
```

## 调度策略 (Dispatch Strategies)

### 单 Agent 策略 (Single Agent Strategy)

```yaml
strategy: "single_agent"
conditions:
  - task_complexity: "simple"
  - code_size: "small" # < 50 lines
  - single_domain: true
workflow: 1. 分析任务类型
  2. 选择最匹配的 Agent
  3. 执行任务
  4. 验证结果
```

### 协作策略 (Collaboration Strategy)

```yaml
strategy: "multi_agent_collaboration"
conditions:
  - task_complexity: "complex"
  - code_size: "large" # > 200 lines
  - multiple_domains: true
workflow: 1. Claude 分析需求和规划
  2. Codex 生成代码
  3. Gemini 审查代码
  4. Test Agent 编写测试
  5. Claude 整合结果
```

### 审查策略 (Review Strategy)

```yaml
strategy: "review_first"
conditions:
  - task_type: "critical_feature"
  - requires_security_review: true
  - production_deployment: true
workflow: 1. Claude 初步实现
  2. Gemini 安全审查
  3. Codex 修复问题
  4. 最终 Claude 验证
```

## 成本优化 (Cost Optimization)

### 预算控制 (Budget Control)

```yaml
monthly_budget: 100 # USD
cost_tracking:
  - per_task_cost
  - daily_total
  - monthly_total
alerts:
  - threshold: 80% # 80 USD
  - action: "notify_user"
```

### Agent 选择优先级 (Agent Selection Priority)

```yaml
priority_order: 1. 免费工具（CLI、本地工具）
  2. 低成本 Agent（Gemini）
  3. 中等成本 Agent（Codex, Claude）
  4. 高成本 Agent（仅在必要时）
fallback:
  - if_budget_exceeded: "use_free_alternatives"
  - if_agent_unavailable: "use_next_best"
```

## 质量门禁 (Quality Gates)

### 代码质量检查 (Code Quality Checks)

```yaml
mandatory_checks:
  - syntax_check
  - lint_check
  - type_check # 如果适用
  - security_scan
blocking_conditions:
  - syntax_error: "block"
  - lint_error: "warn"
  - security_issue: "block"
```

### 测试覆盖率 (Test Coverage)

```yaml
minimum_coverage: 80%
enforcement: "strict"
exemptions:
  - prototype_code
  - experimental_features
```

## 性能指标 (Performance Metrics)

### 响应时间 (Response Time)

```yaml
targets:
  - simple_task: "< 30s"
  - medium_task: "< 2min"
  - complex_task: "< 10min"
monitoring:
  - actual_response_time
  - queue_time
  - execution_time
```

### 成功率 (Success Rate)

```yaml
target: 95%
calculation: "successful_tasks / total_tasks"
improvement_actions:
  - if_below_90%: "review_prompts"
  - if_below_80%: "switch_strategy"
```

## 自定义 Agent (Custom Agents)

用户可以添加自定义 Agent：

```yaml
name: "[custom_name]"
display_name: "[显示名称]"
description: "[功能描述]"
capabilities:
  - "[能力1]"
  - "[能力2]"
tech_stack:
  - "[技术栈1]"
  - "[技术栈2]"
trigger_conditions:
  - "[条件1]"
  - "[条件2]"
endpoint: "[API端点或命令]"
auth_method: "[认证方法]"
```

---

> **配置优先级**: 用户自定义 > 系统默认
> **更新频率**: 根据使用情况自动优化
> **版本**: 1.0.0
