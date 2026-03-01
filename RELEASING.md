# Releasing

## Prerequisites

- CI is green on all supported platforms.
- `python3 -m pytest tests/ -v` passes.
- `python3 scripts/check_docs_consistency.py` passes.
- `CHANGELOG.md` updated.

## Release Steps

1. Bump version in `pyproject.toml` and changelog.
2. Create release branch/tag:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`
3. Build package:
   - `python3 -m build`
4. Validate artifacts:
   - `python3 -m twine check dist/*`
5. Publish:
   - TestPyPI first, then PyPI.
6. Create GitHub Release and paste changelog summary.

## Post-release

- Monitor issues for 7 days.
- Prepare `X.Y.(Z+1)` hotfix if needed.
