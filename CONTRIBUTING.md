# Contributing

Thanks for contributing to OpenClaw Alignment.

## Development Setup

```bash
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment
python3 scripts/install.py --dev --editable
```

## Workflow

1. Create a feature branch.
2. Write/adjust tests first for behavior changes.
3. Keep commits focused and reviewable.
4. Run checks before opening PR.

## Local Checks

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
python3 -m build
```

## Pull Requests

- Explain problem, solution, and test evidence.
- Link issue if available.
- Update docs/changelog for user-visible changes.

## Commit Style

Use Conventional Commits:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `chore: ...`
- `test: ...`
