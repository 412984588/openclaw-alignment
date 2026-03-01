# Task Plan

## Objective

Stabilize the confirmation and GEP feature set so the repository is release-ready under strict quality gates.

## Workstreams

### 1) Type and Lint Stability

- Fix all mypy errors in `lib/confirmation.py` and related modules.
- Remove all ruff violations introduced by recent feature work.
- Keep behavior unchanged while improving type safety.

### 2) Bootstrap Reliability

- Ensure `ConfirmationAPI` auto-creates `memory_dir/gep` and required storage files.
- Verify first-run feedback is persisted without manual initialization.

### 3) English-First Consistency

- Remove non-English text from new modules, tests, and CLI output strings.
- Enforce policy with language regression tests.

### 4) Validation and Audit

- Run full tests (`pytest`).
- Run static checks (`mypy`, `ruff`).
- Run repository language scan and document final status.

## Done Criteria

- All checks green.
- No regressions in confirmation decisions.
- No CJK text in tracked code/test/public-facing files.
