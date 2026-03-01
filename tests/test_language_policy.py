#!/usr/bin/env python3
"""
English-first language policy checks for public-facing surfaces.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def _contains_cjk(text: str) -> bool:
    return re.search(r"[\u4e00-\u9fff]", text) is not None


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_readme_primary_is_english_only() -> None:
    content = (_repo_root() / "README.md").read_text(encoding="utf-8")
    assert not _contains_cjk(content), "README.md should be English-only for primary docs"


def test_openclaw_align_help_is_english_only() -> None:
    result = subprocess.run(
        ["openclaw-align", "--help"],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not _contains_cjk(result.stdout), "openclaw-align --help should be English-only"


def test_integration_help_is_english_only() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lib.integration", "--help"],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not _contains_cjk(result.stdout), "python -m lib.integration --help should be English-only"


def test_new_confirmation_modules_are_english_only() -> None:
    repo = _repo_root()
    paths = [
        repo / "lib" / "api.py",
        repo / "lib" / "confirmation.py",
        repo / "lib" / "gep.py",
        repo / "lib" / "gep_store.py",
        repo / "lib" / "gep_to_md.py",
        repo / "lib" / "md_to_gep.py",
    ]
    for path in paths:
        content = path.read_text(encoding="utf-8")
        assert not _contains_cjk(content), f"{path.name} should be English-only"
