# OpenClaw 意图对齐系统

> 强化学习驱动的工作流对齐引擎（Actor-Critic）

**[English](README.md)** | **简体中文**

## 特性

- Actor-Critic 强化学习主链路
- 四维度奖励系统（客观指标/行为信号/显性反馈/模式偏好）
- 可选 Phase3（分布式训练、自动调参、监控、性能优化）
- 契约防漂移检查（状态/动作维度与文档一致性）
- 跨平台支持：Windows / macOS / Linux

## 支持矩阵

- Python: 3.10, 3.11, 3.12, 3.13
- OS: Windows, macOS, Linux

## 安装

### 1) PyPI（推荐）

```bash
pip install openclaw-alignment
```

可选 Phase3 依赖：

```bash
pip install "openclaw-alignment[phase3]"
```

### 2) 源码安装

```bash
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment
python3 scripts/install.py
```

开发安装：

```bash
python3 scripts/install.py --dev --editable
```

## 快速验证

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
openclaw-alignment --help
```

## 架构

### Core（Phase 1-2）

- `lib/reward.py`: 四维度奖励计算
- `lib/environment.py`: 交互环境
  - State: 状态数据类（17维）
  - Action: 动作数据类（11维）
- `lib/agent.py`: Actor-Critic 智能体
- `lib/learner.py`: 在线学习器
- `lib/trainer.py`: 训练循环
- `lib/contracts.py`: 维度契约唯一来源

### Optional（Phase 3）

- `lib/distributed_trainer.py`
- `lib/hyperparameter_tuner.py`
- `lib/monitoring.py`
- `lib/performance_optimizer.py`

## 文档

- 架构：`docs/architecture.zh-CN.md`
- 奖励模型：`docs/reward-model.zh-CN.md`
- 配置：`docs/configuration.zh-CN.md`
- 可选依赖：`docs/phase3-optional-deps.zh-CN.md`
- 贡献：`CONTRIBUTING.zh-CN.md`
- 安全：`SECURITY.zh-CN.md`
- 支持：`SUPPORT.zh-CN.md`

## 测试覆盖

- **总测试数**: 80个
- **通过率**: 100%
- **核心RL与集成**: 54个测试 ✅
- **Phase 2**: 1个测试 ✅
- **Phase 3**: 21个测试 ✅
- **文档/契约防漂移**: 4个测试 ✅

## 发布与版本

- 版本策略：SemVer（稳定分支：`release/1.0.x`）
- 发布流程：见 `RELEASING.zh-CN.md` / `RELEASING.md`
- 变更记录：`CHANGELOG.md`

## 许可证

MIT
