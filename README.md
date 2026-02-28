# 全域意图对齐与完全自主进化协议

> **版本**：1.0.0
> **更新**：2026-02-28
> **状态**：已实施完成

---

## 📖 概述

这是一个将"全域意图对齐与完全自主进化协议"产品化为 OpenClaw Skill/插件的完整实现，支持双模式：

- **深度模式**：有历史记录时的完整意图建模
- **快速模式**：新设备零历史记录的快速上手

**核心特性**：

- 🎯 **强化学习风格奖励机制**：多维度加权计算，动态调整策略
- 🔄 **闭环自动化**：每日优化 + 每周修剪 + 自我兜底
- 🛡️ **安全沙盒**：Git Worktree 隔离测试
- 🧠 **动态自适应协作**：Oh My OpenCode 风格的 Agent 编排

---

## 📁 文件结构

```
~/.claude/
├── USER.md                           # 指挥官画像
├── SOUL.md                           # 系统宪法与永久记忆
├── AGENTS.md                         # 兵力编排与调度
├── skills/
│   └── 全域意图对齐与自主进化.md      # OpenClaw Skill 文件
├── config/
│   ├── reward-config.json            # 奖励系统配置
│   ├── heartbeat-state.json          # Heartbeat 状态
│   └── interview-questions.json      # 访谈问题（20+）
├── backups/
│   └── optimization-log.json         # 优化历史日志
└── scripts/
    ├── daily-evolution.sh            # 每日自动优化脚本
    ├── weekly-pruning.sh             # 每周修剪脚本
    └── quick-mode-init.sh            # 快速模式初始化脚本
```

---

## 🚀 快速开始

### 首次启动

**深度模式**（有历史记录）：

```bash
# 技能会自动检测历史数据并执行深度建模
# 无需手动操作
```

**快速模式**（新设备零历史）：

```bash
# 运行快速模式初始化
~/.claude/scripts/quick-mode-init.sh

# 或通过 Skill 菜单选择「全域意图对齐与自主进化」
```

### 主动优化

```bash
# 方式 1：通过 Skill 菜单
# 方式 2：运行每日优化脚本
~/.claude/scripts/daily-evolution.sh

# 方式 3：运行每周修剪脚本
~/.claude/scripts/weekly-pruning.sh
```

---

## 🎯 核心文件说明

### USER.md - 指挥官画像

**内容**：

- AI 利用哲学（多 Agent 协作、自动化、防跑偏）
- 偏好与雷区
- 交互习惯
- 行为模式分析

**更新频率**：高（每次优化）

---

### SOUL.md - 系统宪法与永久记忆

**内容**：

- 世界观（动态自适应协作）
- 最高准则（测试铁律、原子提交、Ralph Loop）
- 思维链模板
- 自我兜底机制
- 历史错误记录

**更新频率**：极低（仅重大决策变更）

---

### AGENTS.md - 兵力编排与调度

**内容**：

- Agent 特长（Oracle、Librarian、Frontend、Sisyphus）
- 协作规则（Ask @oracle、动态委派）
- 自主边界（完全自主修复）
- Agent 编排优化

**更新频率**：中（发现更优编排时）

---

## 🎁 奖励机制

### 奖励信号采集

**优先级 1：客观指标（40%）**

- 测试覆盖率
- 代码质量评分
- Bug 数量
- 任务完成时间
- 自动修复成功率

**优先级 2：用户行为信号（30%）**

- 接受建议比例
- 修改后使用比例
- 完全重写比例
- 重复使用某功能次数

**优先级 3：显性反馈（20%）**

- 用户直接评分（1-5）
- 正向反馈次数
- 负向反馈次数

**优先级 4：行为模式（10%）**

- Agent 选择偏好
- 工作流偏好

### 动态权重调整

**初期（前 10 个任务）**：

- 即时奖励：70%
- 长期优化：30%

**成熟期（20+ 个任务）**：

- 即时奖励：30%
- 长期优化：70%

---

## 🔄 闭环自动化

### 每日优化（Heartbeat 触发）

**Trigger**：每天早上 06:00

**流程**：

1. Review（回顾过去 24 小时）
2. Analyze（分析优化机会）
3. Sandbox Test（沙盒测试）
4. Execute（自主落地）
5. Report（事后简报）

**脚本**：`~/.claude/scripts/daily-evolution.sh`

---

### 每周修剪（每周日 09:00）

**流程**：

1. 迷你访谈（5-10 个问题）
2. 断舍离（记忆折叠）
3. 深度重构

**脚本**：`~/.claude/scripts/weekly-pruning.sh`

---

## 🛡️ 安全保障

### Git Worktree 沙盒

所有优化和测试必须在隔离环境中进行：

```bash
# 创建隔离环境
mkdir -p .worktrees/skill-test
git worktree add .worktrees/skill-test -b skill-test-branch

# 测试
cd .worktrees/skill-test
# 测试功能

# 清理
git worktree remove .worktrees/skill-test
```

### 强制备份

优化前必须备份：

```bash
# 自动执行
timestamp=$(date +%Y%m%d_%H%M%S)
cp -r ~/.claude ~/.claude.backup.$timestamp
```

### 回滚机制

如果优化不满意，可以一键回滚：

```bash
# 查看备份列表
ls -la ~/.claude.backup.*

# 回滚到指定版本
rm -rf ~/.claude
cp -r ~/.claude.backup.20260228_060000 ~/.claude
```

---

## ⚙️ 配置说明

### reward-config.json

**位置**：`~/.claude/config/reward-config.json`

**主要配置**：

- `weights`: 奖励信号权重
- `objective_metrics`: 客观指标配置
- `dynamic_adjustment`: 动态权重调整
- `optimization_triggers`: 优化触发条件
- `backup`: 备份配置
- `sandbox`: 沙盒配置

---

### heartbeat-state.json

**位置**：`~/.claude/config/heartbeat-state.json`

**主要字段**：

- `last_checks`: 最后检查时间
- `statistics`: 统计数据
- `stage`: 当前阶段（early_stage / mature_stage）
- `mode`: 模式（deep / quick）
- `profile`: 用户画像进度

---

## 🔧 高级配置

### 禁用每日自动优化

编辑 `~/.claude/config/reward-config.json`：

```json
{
  "optimization_triggers": {
    "daily_optimization": false
  }
}
```

### 调整奖励权重

编辑 `~/.claude/config/reward-config.json`：

```json
{
  "weights": {
    "objective_metrics": 0.5,
    "user_behavior": 0.3,
    "explicit_feedback": 0.1,
    "behavior_pattern": 0.1
  }
}
```

### 自定义访谈问题

编辑 `~/.claude/config/interview-questions.json`，添加或修改问题。

---

## 📊 使用示例

### 示例 1：首次启动（深度模式）

```bash
# 检测到历史数据
✅ GPT 聊天记录（~/Documents/gpt聊天记录）
✅ OpenClaw 配置（~/.claude/）
✅ OpenClaw 配置（~/.openclaw/）

# 自动执行深度建模
📊 扫描历史数据...
🧠 提取 AI 利用哲学...
📋 构建核心文件...

✅ 深度建模完成
```

### 示例 2：主动优化

```bash
# 运行每日优化
~/.claude/scripts/daily-evolution.sh

# 输出
╔════════════════════════════════════════════════════════════╗
║     全域意图对齐与自主进化 - 每日自动优化                   ║
╚════════════════════════════════════════════════════════════╝

📦 备份当前状态...
🔍 回顾过去 24 小时...
🧠 分析优化机会...
🧪 沙盒测试...
🚀 执行优化...
📝 生成事后简报...

✅ 每日优化完成！
```

---

## ❓ 常见问题

### Q: 如何查看优化历史？

A: 查看 `~/.claude/backups/optimization-log.json`

### Q: 如何重置用户画像？

A: 删除 `~/.claude/USER.md`，重新运行初始化脚本

### Q: 如何手动触发优化？

A: 运行 `~/.claude/scripts/daily-evolution.sh`

### Q: 如何禁用自动优化？

A: 编辑 `~/.claude/config/reward-config.json`，设置 `"enabled": false`

---

## 📝 版本历史

| 版本  | 日期       | 变更内容           |
| ----- | ---------- | ------------------ |
| 1.0.0 | 2026-02-28 | 初始版本，完整实施 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**：2026-02-28
**维护者**：OpenClaw Community
