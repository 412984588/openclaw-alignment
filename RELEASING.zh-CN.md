# 发布流程

## 前置条件

- CI 在所有支持平台通过。
- `python3 -m pytest tests/ -v` 全绿。
- `python3 scripts/check_docs_consistency.py` 通过。
- `CHANGELOG.md` 已更新。

## 发布步骤

1. 更新 `pyproject.toml` 与 changelog 版本号。
2. 打 tag 并推送：
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`
3. 构建包：
   - `python3 -m build`
4. 校验包：
   - `python3 -m twine check dist/*`
5. 发布：
   - 先 TestPyPI，再正式 PyPI。
6. 创建 GitHub Release 并附变更摘要。

## 发布后

- 首周跟踪 issue。
- 必要时发布 `X.Y.(Z+1)` 热修版本。
