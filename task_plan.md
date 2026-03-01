# Task Plan: OpenClaw Alignment GEP Protocol Support

## Goal

将 openclaw-alignment 的输出层从 Markdown 文件（USER.md/SOUL.md/AGENTS.md）改造为 GEP (Genome Evolution Protocol) 格式，支持跨 agent 的能力复用和进化追踪。

## Phases

- [x] Phase 1: GEP 资产层实现（核心）
- [x] Phase 2: RL 输出层改造（含自动迁移）
- [x] Phase 3: 新增 CLI 命令
- [x] Phase 4: GEP → Markdown 导出器（第一版本必须实现）
- [x] Phase 5: 测试验证

## Status

**✅ 所有 Phase 已完成！**

## Phase 5 完成情况

✅ **单元测试**：16 个测试全部通过

- TestGene: 5 个测试
- TestCapsule: 2 个测试
- TestEvent: 3 个测试
- TestGEPStore: 6 个测试

✅ **集成测试**：9 个测试全部通过

- TestCLIInit: 2 个测试（init 创建 GEP 文件、自动迁移）
- TestMarkdownToGEPConversion: 3 个测试（USER/SOUL/AGENTS 转换）
- TestGEPToMarkdownExport: 2 个测试（导出 Markdown）
- TestGEPStorePersistence: 2 个测试（持久化、追加模式）

## 最终交付物

### 新建文件（6 个）

- `lib/gep.py` - GEP 数据模型（Gene、Capsule、Event）
- `lib/gep_store.py` - GEP 存储管理器
- `lib/md_to_gep.py` - Markdown → GEP 转换器
- `lib/gep_to_md.py` - GEP → Markdown 导出器
- `tests/test_gep.py` - GEP 单元测试
- `tests/test_gep_integration.py` - GEP 集成测试

### 修改文件（3 个）

- `lib/cli.py` - 扩展 init/status，新增 6 个 CLI 命令
- `lib/learner.py` - 集成 GEP 自动创建/更新逻辑
- `lib/__init__.py` - 导出 GEP 相关类

## 验收标准检查

1. ✅ `openclaw-align init` 生成 `.openclaw_memory/gep/` 目录和三个 GEP 文件
2. ✅ 检测到现有 MD 文件时自动迁移到 GEP 格式
3. ✅ RL 评估后（`openclaw-align analyze`）自动创建/更新 Gene
4. ✅ 每次进化正确记录到 `events.jsonl`（追加模式）
5. ✅ `openclaw-align gene list` 能列出所有 Gene
6. ✅ `openclaw-align gene show <id>` 能显示 Gene 详情
7. ✅ `openclaw-align capsule list` 能列出所有 Capsule
8. ✅ `openclaw-align capsule show <id>` 能显示 Capsule 详情
9. ✅ `openclaw-align events` 能显示最近 20 条进化记录
10. ✅ `openclaw-align export-md` 能从 GEP 导出 Markdown 格式
11. ✅ 保留原有的 fail-closed 安全模型（无回归）
12. ✅ 测试通过（25/25 测试全部通过）
13. ✅ 所有 Gene/Capsule 的 asset_id 正确计算（SHA256）
14. ✅ 中文注释和文档完整

## 关键设计决策已实现

- ✅ **MD 迁移**：init 时检测并转换现有 MD 文件
- ✅ **RL 触发**：每次任务完成后自动运行 RL 评估并更新 Gene
- ✅ **兼容模式**：export-md 在第一版实现
- ✅ **存储位置**：`.openclaw_memory/gep/` 子目录

## Decisions Made

- **GEP 存储位置**: `.openclaw_memory/gep/` 子目录
- **自动迁移**: init 时检测并转换现有 MD 文件
- **向后兼容**: 第一版本必须实现 export-md 命令
- **纯 Python 实现**: 不依赖 EvoMap API

## Key Technical Constraints

- 保留 RL 核心逻辑（Actor-Critic、四维奖励、fail-closed 安全模型）
- SHA256 asset_id 计算
- 中文注释和文档
- Event 审计日志使用 jsonl 格式（追加模式）

## Files to Create

- `lib/gep.py` - GEP 数据模型
- `lib/gep_store.py` - GEP 存储管理器
- `lib/md_to_gep.py` - Markdown → GEP 转换器
- `lib/gep_to_md.py` - GEP → Markdown 导出器
- `tests/test_gep.py` - GEP 单元测试
- `tests/test_gep_integration.py` - GEP 集成测试

## Files to Modify

- `lib/cli.py` - 扩展 init 命令，新增 gene/capsule/events/export-md 子命令
- `lib/learner.py` - 修改 RL 输出逻辑，生成 Gene 和 Event
- `lib/__init__.py` - 导出 GEP 相关类

## Acceptance Criteria

1. ✅ `openclaw-align init` 生成 `.openclaw_memory/gep/` 目录和三个 GEP 文件
2. ✅ 检测到现有 MD 文件时自动迁移到 GEP 格式
3. ✅ RL 评估后（`openclaw-align analyze`）自动创建/更新 Gene
4. ✅ 每次进化正确记录到 `events.jsonl`（追加模式）
5. ✅ `openclaw-align gene list` 能列出所有 Gene
6. ✅ `openclaw-align gene show <id>` 能显示 Gene 详情
7. ✅ `openclaw-align capsule list` 能列出所有 Capsule
8. ✅ `openclaw-align capsule show <id>` 能显示 Capsule 详情
9. ✅ `openclaw-align events` 能显示最近 20 条进化记录
10. ✅ `openclaw-align export-md` 能从 GEP 导出 Markdown 格式
11. ✅ 保留原有的 fail-closed 安全模型（无回归）
12. ✅ 测试通过（单元测试 + 集成测试）
