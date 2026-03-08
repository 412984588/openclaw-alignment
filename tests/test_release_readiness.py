#!/usr/bin/env python3
"""Release readiness regression tests."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_pyproject_readme_points_to_existing_file() -> None:
    repo_root = _repo_root()
    content = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^readme\s*=\s*"([^"]+)"\s*$', content, flags=re.MULTILINE)
    assert match is not None, "pyproject.toml is missing the readme field."

    readme_path = repo_root / match.group(1)
    assert readme_path.exists(), f"readme file does not exist: {readme_path.name}"


def test_pyproject_exposes_public_cli_entrypoint() -> None:
    repo_root = _repo_root()
    content = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'openclaw-align = "openclaw_align.cli:main"' in content


def test_import_lib_works_without_torch_installed() -> None:
    repo_root = _repo_root()
    script = (
        "import importlib, sys\n"
        "sys.modules['torch'] = None\n"
        "sys.modules.pop('torch.nn', None)\n"
        "sys.modules.pop('torch.nn.functional', None)\n"
        "importlib.import_module('lib')\n"
        "print('ok')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok" in result.stdout


def test_ci_workflow_covers_master_and_phase3_has_pytest() -> None:
    repo_root = _repo_root()
    content = (repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "master" in content, "CI push branches do not include master."

    assert "phase3-smoke" in content
    assert "phase3-full-deps" in content
    phase3_install_has_pytest = (
        "python -m pip install -r requirements-dev.txt" in content
        or "python -m pip install pytest" in content
    )
    assert phase3_install_has_pytest, "phase3 job does not install pytest."


def test_release_workflow_has_pypi_token_fallback() -> None:
    repo_root = _repo_root()
    content = (repo_root / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "PYPI_API_TOKEN" in content, "release workflow is missing the PYPI_API_TOKEN fallback path."
