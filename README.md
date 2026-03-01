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

## Quick Verification

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
openclaw-alignment --help
```

## Architecture

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
