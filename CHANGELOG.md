# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [2.0.0] - 2026-03-08

### Breaking Changes

- Public runtime and release documentation are now policy-only.
- Canonical local storage is `.openclaw_memory/policy/` with `rules.json`, `playbooks.json`, and `policy_events.jsonl`.
- Operational supervision is centered on `openclaw-align policy ...`.

### Changed

- Refactored the runtime around the policy lifecycle `hint -> candidate -> confirmed -> suspended -> archived`.
- Standardized the public CLI surface around `openclaw-align`, the compatibility alias `openclaw-alignment`, and `python -m openclaw_align`.
- Removed deprecated naming, deprecated bootstrap paths, and deprecated release text from the repository.

### Added

- Stable public API surface for policy storage and confirmation integrations:
  - `ConfirmationAPI`
  - `create_api`
  - `Rule`, `Playbook`, `PolicyEvent`
  - `PolicyStore`
  - `MarkdownToPolicyConverter`
  - `PolicyToMarkdownExporter`

## [1.0.1] - 2026-03-01

### Changed

- Release-line hardening around packaging, public CLI smoke coverage, and docs consistency validation before the policy cutover.

## [1.0.0] - 2026-03-01

### Added

- Packaging metadata and entrypoints via `pyproject.toml`, including `openclaw-alignment` CLI.
- Cross-platform installer scripts:
  - `scripts/install.py`
  - `scripts/install_unix.sh`
  - `scripts/install_windows.ps1`
- Release governance and community docs:
  - `CONTRIBUTING*.md`
  - `SECURITY*.md`
  - `SUPPORT*.md`
  - `CODE_OF_CONDUCT*.md`
  - `RELEASING*.md`
- CI/CD workflow templates:
  - cross-platform matrix CI
  - package build validation
  - release publishing workflow
  - dependency security audit workflow
- Path abstraction utilities for cross-platform config/cache/state directories (`lib/paths.py`).
- Audit artifacts and release scope docs under `audit/` and `docs/release/`.

### Changed

- Stabilized environment input normalization:
  - invalid `task_type` falls back safely
  - invalid/out-of-range `time_of_day` is normalized
  - explicit precondition error when `step()` is called before `reset()`
- Deterministic policy behavior for inference (`explore=False` now uses greedy selection).
- Improved config update behavior to preserve wrapper schema and create parent dirs automatically.
- Unified state/action dimension contracts through `lib/contracts.py` and consistent references.
- Updated README/README_EN to match actual install paths, dependencies, and support matrix.

### Fixed

- CLI parser option bug that previously caused `python -m lib.integration --help` to fail.
- Action decoding now returns explicit validation errors for malformed/overflow indices.
- Docs consistency checker now handles both pytest collection output formats.
- Removed generated model artifacts from source tracking to avoid dirty-tree churn and release noise.

### Security

- Added private vulnerability reporting policy and response SLO documentation.
- Added scheduled dependency audit workflow (`pip-audit`).

### Breaking Changes

- None.

### Known Limitations

- Phase3 full dependency installation is heavier (includes optional ML/monitoring stack).
- Legacy OpenClaw config/model paths are still supported for backward compatibility.
