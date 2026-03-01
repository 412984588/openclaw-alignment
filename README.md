# OpenClaw Alignment System

> Reinforcement-learning driven workflow alignment engine (Actor-Critic)

**English (Primary)** | **[Chinese (Simplified)](README.zh-CN.md)**

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

> **Scenario comparison**: unprotected agent runaway (🔴) vs OpenClaw Alignment interception (🟢)

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
    subgraph User Layer
        A[User Intent Input]:::input
    end

    subgraph Commander Layer
        B[Deep Analysis]:::commander
        C[Read Memory]:::commander
        C1[USER.md<br/>User Profile]:::memory
        C2[SOUL.md<br/>System Constitution]:::memory
        C3[AGENTS.md<br/>Tool Dispatch]:::memory
        D[Security Check]:::security
        E[Task Boundary Definition]:::boundary
    end

    subgraph Executor Layer
        F[Receive Command]:::executor
        G[Sandbox Validation]:::sandbox
        G1{Validation Passed?}
        H[Execute Task]:::execute
        I[High-Risk Detection]:::monitor
        J[Auto-Healing Fallback]:::healing
        K{Trigger Fallback?}
        L[Block Execution]:::block
    end

    subgraph Evolution Loop
        M[Daily Backup]:::backup
        N[Performance Analysis]:::analysis
        O[Update Memory]:::update
        O1[Update USER.md]:::memory
        O2[Update SOUL.md]:::memory
        O3[Update AGENTS.md]:::memory
    end

    subgraph Output Layer
        P[Execution Result]:::output
        Q[User Feedback]:::feedback
    end

    %% Main flow
    A --> B
    B --> C
    C --> C1
    C --> C2
    C --> C3
    C1 & C2 & C3 --> D
    D --> E
    E --> F

    %% Executor flow
    F --> G
    G --> G1
    G1 -->|Yes| H
    G1 -->|No| L

    H --> I
    I --> K
    K -->|Yes| J
    K -->|No| P

    J --> P

    %% Evolution loop
    P --> M
    M --> N
    N --> O
    O --> O1
    O --> O2
    O --> O3

    %% Feedback loop
    Q --> A

    %% Style definitions
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

- **Total Tests**: 132
- **Pass Rate**: 99.2% (124/125)
- **Core RL + integration**: 54 tests ✅
- **GEP System**: 25 tests ✅
- **Intelligent Confirmation**: 13 tests ✅
- **Phase 2**: 1 test ✅
- **Phase 3**: 21 tests ✅
- **Docs/contract drift guards**: 11 tests ✅

## Release and Versioning

- Versioning: SemVer (stable branch: `release/1.0.x`)
- Release runbook: `RELEASING.md` / `RELEASING.zh-CN.md`
- Changelog: `CHANGELOG.md`

## License

MIT
