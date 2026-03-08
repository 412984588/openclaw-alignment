# OpenClaw Alignment

> Explainable autonomous execution policy engine for low-touch, auditable agent execution

**English (Primary)** | **[Chinese (Simplified)](README.zh-CN.md)**

## 2.0.0 Highlights

- Policy lifecycle: `hint -> candidate -> confirmed -> suspended -> archived`
- Canonical local storage: `.openclaw_memory/policy/`
- Policy-first supervision CLI: `openclaw-align policy ...`
- Stable Python API for confirmation, policy storage, and Markdown conversion/export
- Optional Phase 3 extras remain available through `openclaw-alignment[phase3]`

## Installation

### PyPI

```bash
python3 -m pip install openclaw-alignment
```

Optional Phase 3 extras:

```bash
python3 -m pip install "openclaw-alignment[phase3]"
```

### Source checkout

```bash
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment
python3 -m pip install -e ".[dev]"
```

## CLI Entry Points

- `openclaw-align`: primary console entry point
- `openclaw-alignment`: compatibility console alias
- `python -m openclaw_align`: module entry point

Initialize policy memory and inspect the current lifecycle state:

```bash
openclaw-align init
openclaw-align analyze
openclaw-align policy status
openclaw-align policy recent
```

`init` provisions:

- `.openclaw_memory/policy/rules.json`
- `.openclaw_memory/policy/playbooks.json`
- `.openclaw_memory/policy/policy_events.jsonl`
- `.openclaw_memory/USER.md`
- `.openclaw_memory/SOUL.md`
- `.openclaw_memory/AGENTS.md`

Low-frequency supervision commands:

```bash
openclaw-align policy status
openclaw-align policy recent
openclaw-align policy risky
openclaw-align policy suspended
python -m openclaw_align policy status
```

## Public Python API

The `lib` package exposes the supported policy-facing surface:

```python
from lib import (
    ConfirmationAPI,
    PolicyEvent,
    PolicyStore,
    Playbook,
    Rule,
    MarkdownToPolicyConverter,
    PolicyToMarkdownExporter,
    create_api,
)
```

- `ConfirmationAPI` / `create_api`: runtime confirmation and feedback loop integration
- `PolicyStore`: canonical policy asset persistence
- `Rule`, `Playbook`, `PolicyEvent`: public policy models
- `MarkdownToPolicyConverter`: convert Markdown memory into policy assets
- `PolicyToMarkdownExporter`: export canonical policy assets back to Markdown

## Verification

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
python3 -m ruff check lib tests scripts
python3 -m openclaw_align policy status
openclaw-align policy status
```

## Core Modules

- `lib/policy_models.py`: canonical `Rule`, `Playbook`, and `PolicyEvent` models
- `lib/policy_store.py`: canonical `PolicyStore` and policy asset persistence
- `lib/policy_resolution.py`: scope inference and precedence resolution
- `lib/confirmation.py`: runtime truth loop, event recording, and feedback application
- `lib/promotion.py`: promotion gates for `candidate -> confirmed`
- `lib/demotion.py`: suspension, reactivation, and archive gates
- `lib/learner.py`: weak-hint derivation and strong-evidence aggregation
- `lib/api.py`: stable confirmation API surface
- `lib/cli.py`: initialization, status, supervision, export, and inspection commands
- `lib/environment.py`: interaction environment
  - `State`: State data class (17 dimensions)
  - `Action`: Action data class (11 dimensions)
- `lib/contracts.py`: single source of truth for state and action dimensions

## Optional Phase 3 Modules

- `lib/distributed_trainer.py`
- `lib/hyperparameter_tuner.py`
- `lib/monitoring.py`
- `lib/performance_optimizer.py`

## Test Coverage

- **Total Tests**: 169
- **Local Validation**: `python3 -m pytest tests/ -v`
- **Coverage Areas**: policy lifecycle promotion and suspension, scope precedence, public surface hard cut, canonical policy storage, CLI supervision, confirmation policy, RL core, optional Phase 3 modules, and docs/contract drift guards

## Release and Versioning

- Versioning: SemVer
- Current release line: `2.x`
- Release runbook: `RELEASING.md` / `RELEASING.zh-CN.md`
- Changelog: `CHANGELOG.md`

## Documentation

- Architecture: `docs/architecture.md`
- Reward model: `docs/reward-model.md`
- Configuration: `docs/configuration.md`
- Optional dependencies: `docs/phase3-optional-deps.md`
- Contributing: `CONTRIBUTING.md`
- Security: `SECURITY.md`
- Support: `SUPPORT.md`

## License

MIT
