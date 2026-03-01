# 贡献指南

感谢你为 OpenClaw Alignment 贡献代码。

## 开发环境

```bash
git clone https://github.com/412984588/openclaw-alignment.git
cd openclaw-alignment
python3 scripts/install.py --dev --editable
```

## 工作流

1. 从主分支切功能分支。
2. 行为改动优先补测试。
3. 提交保持小而清晰。
4. 提交 PR 前完成本地检查。

## 本地检查

```bash
python3 -m pytest tests/ -v
python3 scripts/check_docs_consistency.py
python3 -m build
```

## PR 要求

- 说明问题、方案与测试结果。
- 有 issue 则关联 issue。
- 用户可见变更需同步文档与 changelog。

## 提交信息规范

建议使用 Conventional Commits：

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `chore: ...`
- `test: ...`
