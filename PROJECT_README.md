# 全域意图对齐与完全自主进化协议

> 基于 OpenClaw 的强化学习风格 AI 协作系统，支持双模式深度意图建模

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-green.svg)](https://openclaw.dev)

---

## ✨ 特性

### 🎯 双模式支持

- **深度模式**：基于历史数据（GPT 聊天记录、OpenClaw 配置）自动构建用户画像
- **快速模式**：新设备零历史记录时，通过 25 个访谈问题快速建立画像

### 🎁 强化学习风格奖励机制

- **多维度信号采集**：
  - 客观指标（40%）：测试覆盖率、代码质量、Bug 数量
  - 用户行为（30%）：接受建议、修改后使用、完全重写
  - 显性反馈（20%）：直接评分、正向/负向反馈
  - 行为模式（10%）：Agent 选择、工作流偏好

- **动态权重调整**：
  - 初期：70% 即时奖励 + 30% 长期优化
  - 成熟期：30% 即时奖励 + 70% 长期优化

- **策略调整机制**：记录错误模式，调整权重，避免重蹈覆辙

### 🔄 闭环自动化

- **每日优化**（Heartbeat 06:00）：
  - Review（回顾过去 24 小时）
  - Analyze（分析优化机会）
  - Sandbox Test（沙盒测试）
  - Execute（自主落地）
  - Report（事后简报）

- **每周修剪**（周日 09:00）：
  - 迷你访谈（5-10 个问题）
  - 断舍离（记忆折叠）
  - 深度重构

### 🛡️ 安全沙盒

- **Git Worktree 隔离**：所有优化在隔离环境中测试
- **强制备份**：优化前自动备份
- **一键回滚**：不满意可立即恢复

### 🧠 动态自适应协作

- **Oh My OpenCode 风格**：Agent 自主决策委派
- **Ask @oracle 模式**：代理可以主动请求外部专家协助
- **完全自主修复**：3 次自主修复循环，可以修改代码、切换方案、调用外部 Agent

---

## 🚀 快速开始

### 一键安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/openclaw-alignment.git
cd openclaw-alignment

# 运行一键安装脚本
./install.sh
```

安装脚本会自动：

1. 检查系统要求
2. 创建目录结构
3. 安装核心文件
4. 配置自动化脚本
5. 运行初始化向导

### 手动安装

```bash
# 1. 创建目录
mkdir -p ~/.claude/{skills,config,backups,scripts}

# 2. 复制文件
cp USER.md SOUL.md AGENTS.md ~/.claude/
cp skills/*.md ~/.claude/skills/
cp config/*.json ~/.claude/config/
cp scripts/*.sh ~/.claude/scripts/

# 3. 添加执行权限
chmod +x ~/.claude/scripts/*.sh

# 4. 运行初始化
~/.claude/scripts/quick-mode-init.sh
```

---

## 📖 核心概念

### 三文件架构

```
~/.claude/
├── USER.md              # 指挥官画像（偏好、雷区、交互习惯）
├── SOUL.md              # 系统宪法（世界观、最高准则、思维链）
└── AGENTS.md            # 兵力编排（Agent 特长、协作规则）
```

### Agent 阵容

- **Oracle（GPT）**：架构师和调试专家
- **Librarian（OpenClaw）**：文档管理和代码库查询专家
- **Frontend（Gemini）**：前端开发专家
- **Sisyphus（协调器）**：任务编排与质量管理

---

## 🎮 使用示例

### 主动优化

```bash
# 每日优化
~/.claude/scripts/daily-evolution.sh

# 每周修剪
~/.claude/scripts/weekly-pruning.sh
```

### 通过 Skill 调用

在 OpenClaw 中选择技能「全域意图对齐与自主进化」

---

## ⚙️ 配置说明

### reward-config.json

**位置**：`~/.claude/config/reward-config.json`

**主要配置**：

- `weights`：奖励信号权重
- `dynamic_adjustment`：动态权重调整（初期/成熟期）
- `optimization_triggers`：优化触发条件
- `sandbox`：沙盒配置

### 自定义配置

```bash
# 编辑奖励配置
vim ~/.claude/config/reward-config.json

# 禁用每日自动优化
jq '.optimization_triggers.daily_optimization = false' \
  ~/.claude/config/reward-config.json > /tmp/config.json
mv /tmp/config.json ~/.claude/config/reward-config.json
```

---

## 📁 项目结构

```
openclaw-alignment/
├── install.sh                  # 一键安装脚本
├── README.md                   # 项目文档
├── USER.md                     # 指挥官画像模板
├── SOUL.md                     # 系统宪法模板
├── AGENTS.md                   # 兵力编排模板
├── skills/
│   └── 全域意图对齐与自主进化.md  # OpenClaw Skill
├── config/
│   ├── reward-config.json       # 奖励系统配置
│   ├── heartbeat-state.json     # Heartbeat 状态
│   └── interview-questions.json # 访谈问题（25个）
├── scripts/
│   ├── daily-evolution.sh       # 每日自动优化
│   ├── weekly-pruning.sh        # 每周修剪与重构
│   └── quick-mode-init.sh       # 快速模式初始化
└── backups/
    └── optimization-log.json    # 优化历史日志
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 更新日志

### v1.0.0 (2026-02-28)

- ✅ 完整实施双模式（深度 + 快速）
- ✅ 强化学习风格奖励机制
- ✅ 闭环自动化系统（每日 + 每周）
- ✅ 安全沙盒（Git Worktree 隔离）
- ✅ 25 个访谈问题
- ✅ 一键安装脚本

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [OpenClaw](https://openclaw.dev) - 强大的 AI 协作平台
- [Oh My OpenCode](https://github.com/example) - 多 Agent 编排灵感来源
- [Anthropic OpenClaw](https://claude.ai) - 核心 AI 能力支持

---

## 📮 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/openclaw-alignment/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/openclaw-alignment/discussions)

---

**最后更新**：2026-02-28
**维护者**：OpenClaw Community
