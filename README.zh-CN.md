# OpenClaw Alignment

> 面向低人工介入场景的可解释自治执行策略引擎

**[English (Primary)](README.md)** | **中文（简体）**

## 2.0.0 发布重点

- 生命周期主链：`hint -> candidate -> confirmed -> suspended -> archived`
- canonical 本地存储：`.openclaw_memory/policy/`
- 主监督 CLI：`openclaw-align policy ...`
- 对外 Python API 已收敛到 confirmation、policy storage、Markdown conversion/export
- 可选 Phase 3 依赖仍通过 `openclaw-alignment[phase3]` 提供

## 安装

### PyPI

```bash
python3 -m pip install openclaw-alignment
```

可选 Phase 3 依赖：

```bash
python3 -m pip install "openclaw-alignment[phase3]"
```

### 从源码安装

```bash
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment
python3 -m pip install -e ".[dev]"
```

## CLI 入口

- `openclaw-align`：主控制台入口
- `openclaw-alignment`：兼容别名
- `python -m openclaw_align`：模块入口

初始化并查看当前 policy 状态：

```bash
openclaw-align init
openclaw-align analyze
openclaw-align policy status
openclaw-align policy recent
```

`init` 会生成：

- `.openclaw_memory/policy/rules.json`
- `.openclaw_memory/policy/playbooks.json`
- `.openclaw_memory/policy/policy_events.jsonl`
- `.openclaw_memory/USER.md`
- `.openclaw_memory/SOUL.md`
- `.openclaw_memory/AGENTS.md`

低频监督命令：

```bash
openclaw-align policy status
openclaw-align policy recent
openclaw-align policy risky
openclaw-align policy suspended
python -m openclaw_align policy status
```

## 公共 Python API

`lib` 包当前公开的 policy surface：

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

- `ConfirmationAPI` / `create_api`：运行时确认决策与反馈吸收
- `PolicyStore`：canonical policy 资产持久化
- `Rule`、`Playbook`、`PolicyEvent`：公开 policy 模型
- `MarkdownToPolicyConverter`：把 Markdown memory 转成 policy assets
- `PolicyToMarkdownExporter`：把 canonical policy assets 导出回 Markdown

## 验证

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
python3 -m ruff check lib tests scripts
python3 -m openclaw_align policy status
openclaw-align policy status
```

## 核心模块

- `lib/policy_models.py`：canonical `Rule`、`Playbook`、`PolicyEvent`
- `lib/policy_store.py`：canonical `PolicyStore` 与 policy 资产持久化
- `lib/policy_resolution.py`：scope 推断与 precedence 解析
- `lib/confirmation.py`：runtime truth loop、事件记录、反馈吸收
- `lib/promotion.py`：`candidate -> confirmed` 晋升 gate
- `lib/demotion.py`：收权、再激活与归档 gate
- `lib/learner.py`：弱提示与强证据聚合
- `lib/api.py`：稳定 confirmation API surface
- `lib/cli.py`：初始化、状态查看、监督、导出与检查命令
- `lib/environment.py`
  - `State`: State data class (17 dimensions)
  - `Action`: Action data class (11 dimensions)
- `lib/contracts.py`：state/action 维度的单一真源

## 可选 Phase 3 模块

- `lib/distributed_trainer.py`
- `lib/hyperparameter_tuner.py`
- `lib/monitoring.py`
- `lib/performance_optimizer.py`

## 测试覆盖

- **Total Tests**: 169
- **Local Validation**: `python3 -m pytest tests/ -v`
- 覆盖范围：生命周期晋升与收权、scope precedence、public surface hard cut、canonical policy storage、CLI supervision、confirmation policy、RL core、可选 Phase 3 模块，以及 docs/contract drift guards

## 发布与版本

- Versioning：SemVer
- 当前发布线：`2.x`
- Release runbook：`RELEASING.md` / `RELEASING.zh-CN.md`
- Changelog：`CHANGELOG.md`

## 文档

- `docs/architecture.md`
- `docs/reward-model.md`
- `docs/configuration.md`
- `docs/phase3-optional-deps.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`

## License

MIT
