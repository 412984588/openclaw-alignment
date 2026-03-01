# OpenClaw Alignment System

> Reinforcement-learning driven workflow alignment engine (Actor-Critic)

**English** | **[简体中文](README.zh-CN.md)**

## Features

- Actor-Critic RL core pipeline
- Four-dimensional reward system (objective/behavior/explicit/pattern)
- Optional Phase3 modules (distributed training, tuning, monitoring, performance)
- Contract drift guards (state/action dimensions + docs consistency)
- Cross-platform support: Windows / macOS / Linux

## Support Matrix

- Python: 3.10, 3.11, 3.12, 3.13
- OS: Windows, macOS, Linux

## Demo

### Quick Start Demo

![OpenClaw Alignment Quick Start](quick_start.gif)

> Watch how easy it is to get started with OpenClaw Alignment! Just run `openclaw-align init` and you're ready to go.

### Disaster Recovery Demo

![OpenClaw Alignment Disaster Recovery](disaster_recovery.gif)

> **场景对比**：未受保护的 Agent 失控（🔴）vs OpenClaw Alignment 阻断（🟢）

The disaster recovery demo showcases:

- **Scene A (Red)**: Unprotected agent receiving vague instruction "clean-workspace --aggressive" and executing dangerous `rm -rf` commands
- **Scene B (Green)**: OpenClaw Alignment Commander intercepting the same instruction by:
  - Reading SOUL.md boundary rules
  - Detecting high-risk intent
  - Triggering fail-closed safety mechanism
  - Requesting user confirmation

## Installation

### 1) PyPI (Recommended)

```bash
pip install openclaw-alignment
```

Optional Phase3 extras:

```bash
pip install "openclaw-alignment[phase3]"
```

### 2) Install from source

```bash
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment
python3 scripts/install.py
```

Development install:

```bash
python3 scripts/install.py --dev --editable
```

## Quick Start

Get started with OpenClaw Alignment in three simple steps:

### Step 1: Install

```bash
pip install openclaw-alignment
```

### Step 2: Initialize

```bash
# Initialize in current directory
openclaw-align init

# Or initialize in a specific directory
openclaw-align init ~/projects/my-project
```

This creates a `.openclaw_memory` folder with three configuration files:

- **USER.md** - Your personal preferences (tech stack, coding style, work habits)
- **SOUL.md** - System constitution (principles, boundaries, ethics)
- **AGENTS.md** - Tool dispatch configuration (available AI agents and strategies)

### Step 3: Customize

Edit the generated files to match your needs:

```bash
# Edit your personal profile
vim .openclaw_memory/USER.md

# Review system principles
vim .openclaw_memory/SOUL.md

# Check available agents
vim .openclaw_memory/AGENTS.md
```

### Step 4: Analyze (Optional)

Let the system learn from your Git history:

```bash
openclaw-align analyze
```

### What's Next?

After initialization, the system will:

✅ Learn your coding preferences from Git history
✅ Recommend the best AI agent for each task
✅ Adapt to your workflow automatically
✅ Respect the boundaries defined in SOUL.md

### Status Check

```bash
openclaw-align status
```

## Quick Verification

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
openclaw-alignment --help
```

## Architecture

### System Flow

```mermaid
flowchart TB
    subgraph 用户层
        A[用户输入意图<br/>User Input]:::input
    end

    subgraph Commander层[指挥官节点<br/>Commander Node]
        B[深度分析<br/>Deep Analysis]:::commander
        C[读取记忆库<br/>Read Memory]
        C1[USER.md<br/>用户画像]:::memory
        C2[SOUL.md<br/>系统宪法]:::memory
        C3[AGENTS.md<br/>工具调度]:::memory
        D[安全检查<br/>Security Check]:::security
        E[任务边界定义<br/>Boundary Definition]:::boundary
    end

    subgraph Executor层[执行者节点<br/>Executor Node]
        F[接收指令<br/>Receive Command]:::executor
        G[沙盒验证<br/>Sandbox Testing]:::sandbox
        G1{验证通过?<br/>Passed?}
        H[执行任务<br/>Execute Task]:::execute
        I[高危检测<br/>Risk Detection]:::monitor
        J[兜底机制<br/>Auto-Healing]:::healing
        K{触发兜底?<br/>Trigger Healing?}
        L[阻断执行<br/>Block Execution]:::block
    end

    subgraph 进化层[闭环进化<br/>Evolution Loop]
        M[每日备份<br/>Daily Backup]:::backup
        N[性能分析<br/>Performance Analysis]:::analysis
        O[更新记忆库<br/>Update Memory]:::update
        O1[更新 USER.md]:::memory
        O2[更新 SOUL.md]:::memory
        O3[更新 AGENTS.md]:::memory
    end

    subgraph 输出层[结果反馈<br/>Output]
        P[执行结果<br/>Execution Result]:::output
        Q[用户反馈<br/>User Feedback]:::feedback
    end

    %% 主流程
    A --> B
    B --> C
    C --> C1
    C --> C2
    C --> C3
    C1 & C2 & C3 --> D
    D --> E
    E --> F

    %% Executor 流程
    F --> G
    G --> G1
    G1 -->|是| H
    G1 -->|否| L

    H --> I
    I --> K
    K -->|是| J
    K -->|否| P

    J --> P

    %% 进化循环
    P --> M
    M --> N
    N --> O
    O --> O1
    O --> O2
    O --> O3

    %% 反馈循环
    Q --> A

    %% 样式定义
    classDef input fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef commander fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef memory fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef security fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef boundary fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef executor fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef sandbox fill:#fff9c4,stroke:#f57c00,stroke-width:2px
    classDef execute fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef monitor fill:#ffe0b2,stroke:#ff6f00,stroke-width:2px
    classDef healing fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef block fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    classDef backup fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef analysis fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef update fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#ff6f00,stroke-width:2px
    classDef feedback fill:#fce4ec,stroke:#e91e63,stroke-width:2px

    class A input
    class B commander
    class C,D,E commander
    class C1,C2,C3 memory
    class F,G,G1,H executor
    class I execute
    class J monitor
    class K healing
    class L block
    class M backup
    class N analysis
    class O,O1,O2,O3 update
    class P output
    class Q feedback
```

### Core (Phase 1-2)

- `lib/reward.py`: reward calculation engine
- `lib/environment.py`: interaction environment
  - `State`: State data class (17 dimensions)
  - `Action`: Action data class (11 dimensions)
- `lib/agent.py`: Actor-Critic agent
- `lib/learner.py`: online learner
- `lib/trainer.py`: training loop
- `lib/contracts.py`: single source of truth for dimensions

### Optional (Phase 3)

- `lib/distributed_trainer.py`
- `lib/hyperparameter_tuner.py`
- `lib/monitoring.py`
- `lib/performance_optimizer.py`

## Documentation

- Architecture: `docs/architecture.md`
- Reward model: `docs/reward-model.md`
- Configuration: `docs/configuration.md`
- Optional dependencies: `docs/phase3-optional-deps.md`
- Contributing: `CONTRIBUTING.md`
- Security: `SECURITY.md`
- Support: `SUPPORT.md`

## Test Coverage

- **Total Tests**: 80
- **Pass Rate**: 100%
- **Core RL + integration**: 54 tests ✅
- **Phase 2**: 1 test ✅
- **Phase 3**: 21 tests ✅
- **Docs/contract drift guards**: 4 tests ✅

## Release and Versioning

- Versioning: SemVer (stable branch: `release/1.0.x`)
- Release runbook: `RELEASING.md` / `RELEASING.zh-CN.md`
- Changelog: `CHANGELOG.md`

## License

MIT
