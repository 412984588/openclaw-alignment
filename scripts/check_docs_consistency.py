#!/usr/bin/env python3
"""
检查README关键指标与代码真实状态是否一致。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.contracts import ACTION_VECTOR_DIM


def _extract_first_int(pattern: str, content: str) -> Optional[int]:
    match = re.search(pattern, content)
    if not match:
        return None
    return int(match.group(1))


def collect_pytest_count(repo_root: Path) -> int:
    """通过pytest收集真实测试总数。"""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        raise RuntimeError(f"pytest collect failed: {output}")

    count = _extract_first_int(r"(\d+)\s+tests\s+collected", output)
    if count is not None:
        return count

    # pytest 在部分配置下会输出每个文件的测试数量：
    # tests/test_x.py: 5
    line_counts = re.findall(r"^tests/.+:\s*(\d+)\s*$", output, flags=re.MULTILINE)
    if line_counts:
        return sum(int(item) for item in line_counts)

    raise RuntimeError(f"cannot parse pytest collected count: {output}")


def validate_readme_metrics(repo_root: Path, expected_tests: int) -> list[str]:
    errors: list[str] = []

    zh_content = (repo_root / "README.md").read_text(encoding="utf-8")
    en_content = (repo_root / "README_EN.md").read_text(encoding="utf-8")

    zh_tests = _extract_first_int(r"\*\*总测试数\*\*:\s*(\d+)个", zh_content)
    en_tests = _extract_first_int(r"\*\*Total Tests\*\*:\s*(\d+)", en_content)
    zh_action_dim = _extract_first_int(r"Action:\s*动作数据类（(\d+)维）", zh_content)
    en_action_dim = _extract_first_int(
        r"`Action`:\s*Action data class \((\d+) dimensions\)",
        en_content,
    )

    if zh_tests is None:
        errors.append("README.md 缺少“总测试数”字段。")
    elif zh_tests != expected_tests:
        errors.append(f"README.md 总测试数={zh_tests}，应为 {expected_tests}。")

    if en_tests is None:
        errors.append("README_EN.md 缺少“Total Tests”字段。")
    elif en_tests != expected_tests:
        errors.append(f"README_EN.md Total Tests={en_tests}，应为 {expected_tests}。")

    if zh_action_dim is None:
        errors.append("README.md 缺少Action维度字段。")
    elif zh_action_dim != ACTION_VECTOR_DIM:
        errors.append(f"README.md Action维度={zh_action_dim}，应为 {ACTION_VECTOR_DIM}。")

    if en_action_dim is None:
        errors.append("README_EN.md 缺少Action dimension字段。")
    elif en_action_dim != ACTION_VECTOR_DIM:
        errors.append(f"README_EN.md Action dimensions={en_action_dim}，应为 {ACTION_VECTOR_DIM}。")

    if "<repository_url>" in zh_content:
        errors.append("README.md 仍包含 <repository_url> 占位符。")

    required_files = ["requirements.txt", "requirements-full.txt", "requirements-dev.txt"]
    for rel in required_files:
        if not (repo_root / rel).exists():
            errors.append(f"缺少依赖文件: {rel}")

    governance_files = [
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "CONTRIBUTING.zh-CN.md",
        "SECURITY.md",
        "SECURITY.zh-CN.md",
        "SUPPORT.md",
        "SUPPORT.zh-CN.md",
        "CODE_OF_CONDUCT.md",
        "CODE_OF_CONDUCT.zh-CN.md",
        "RELEASING.md",
        "RELEASING.zh-CN.md",
    ]
    for rel in governance_files:
        if not (repo_root / rel).exists():
            errors.append(f"缺少治理文档: {rel}")

    manifest_content = (repo_root / "MANIFEST.in").read_text(encoding="utf-8")
    for rel in governance_files:
        if f"include {rel}" not in manifest_content:
            errors.append(f"MANIFEST.in 未包含治理文档: {rel}")

    security_en = (repo_root / "SECURITY.md").read_text(encoding="utf-8")
    security_zh = (repo_root / "SECURITY.zh-CN.md").read_text(encoding="utf-8")
    advisory_url = "https://github.com/412984588/openclaw-alignment/security/advisories/new"
    if advisory_url not in security_en:
        errors.append("SECURITY.md 缺少 GitHub 私有安全通告链接。")
    if advisory_url not in security_zh:
        errors.append("SECURITY.zh-CN.md 缺少 GitHub 私有安全通告链接。")

    return errors


def main() -> int:
    repo_root = REPO_ROOT

    try:
        total_tests = collect_pytest_count(repo_root)
        errors = validate_readme_metrics(repo_root, total_tests)
    except Exception as exc:  # pragma: no cover - CLI兜底
        print(f"[docs-check] ERROR: {exc}")
        return 1

    if errors:
        print("[docs-check] FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"[docs-check] OK: tests={total_tests}, action_dim={ACTION_VECTOR_DIM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
