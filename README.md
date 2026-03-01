# OpenClaw 意图对齐 Skill

> **简简单单，让OpenClaw更懂你**

这个Skill通过观察你的工作模式，学习你的偏好，帮助OpenClaw更好地为你服务。

## 🎯 核心价值

- **零配置启动** - 自动从你的操作中学习
- **持续优化** - 每次使用后微调理解
- **本地存储** - 数据不上云，隐私无忧
- **简单实用** - 没有复杂的强化学习，就是简单的偏好学习

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment

# 安装Skill
./install.sh
```

### 使用

```
你: "优化我的工作流"
OpenClaw: "我来帮你分析工作偏好..."
```

## 📖 功能说明

### 1. 偏好学习

自动学习：

- ✅ 任务类型偏好（T1/T2/T3/T4）
- ✅ 技术栈选择（React vs Vue）
- ✅ 代码风格（命名规范、注释风格）
- ✅ 交互风格（直接 vs 详细）

### 2. 模式识别

自动识别：

- ✅ 常用工作流（测试驱动 vs 先写后测）
- ✅ 决策模式（性能优先 vs 可读性优先）
- ✅ 禁忌事项（拒绝使用的库、拒绝的模式）

### 3. 自适应优化

- ✅ 沟通风格（学习你喜欢的汇报格式）
- ✅ 决策边界（理解哪些需要确认，哪些可以自主）
- ✅ 自动化水平（根据任务复杂度动态调整）

## 📂 文件结构

```
openclaw-alignment/
├── skills/
│   └── 意图对齐.md          # OpenClaw Skill主文件
├── config/
│   └── config.json         # 偏好配置
├── backups/                # 自动备份
└── README.md
```

## ⚙️ 配置文件

配置位置：`~/.openclaw/extensions/intent-alignment/config.json`

```json
{
  "automation_level": "balanced",
  "communication_style": "direct",
  "tech_stack": {
    "frontend": "react",
    "backend": "fastapi"
  }
}
```

## 🔧 高级功能

### 导出偏好

```bash
openclaw intent-alignment export > preferences.json
```

### 导入偏好

```bash
openclaw intent-alignment import < preferences.json
```

### 重置学习

```bash
rm -rf ~/.openclaw/extensions/intent-alignment/
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**最后更新**：2026-02-28
