#!/usr/bin/env python3
"""
Tests for the skills health check script.
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

import scripts.check_skills_health as skills_health


def _write_skill(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text("# skill\n", encoding="utf-8")


def test_scan_detects_broken_symlink_and_missing_skill_md(tmp_path: Path) -> None:
    skills_root = tmp_path / ".codex" / "skills"
    skills_root.mkdir(parents=True)
    _write_skill(skills_root / "healthy-skill")

    broken_target = tmp_path / ".agents" / "skills" / "missing-source" / "skills" / "ghost-skill"
    (skills_root / "ghost-skill").symlink_to(broken_target)

    (skills_root / "invalid-skill").mkdir()

    report = skills_health.run_health_check(
        skill_roots=[skills_root],
        agents_root=tmp_path / ".agents" / "skills",
        source_repo_map={},
        relink_rules={},
        repair=False,
    )

    issue_codes = {issue.code for issue in report.issues}
    assert "BROKEN_SYMLINK" in issue_codes
    assert "MISSING_SKILL_MD" in issue_codes


def test_scan_ignores_support_directories_without_skill_md(tmp_path: Path) -> None:
    skills_root = tmp_path / ".codex" / "skills"
    skills_root.mkdir(parents=True)
    (skills_root / "assets").mkdir()
    (skills_root / "templates").mkdir()

    report = skills_health.run_health_check(
        skill_roots=[skills_root],
        agents_root=tmp_path / ".agents" / "skills",
        source_repo_map={},
        relink_rules={},
        repair=False,
    )

    assert not report.issues


def test_repair_clones_missing_source_repo_and_recovers_symlink(tmp_path: Path) -> None:
    skills_root = tmp_path / ".codex" / "skills"
    skills_root.mkdir(parents=True)

    agents_root = tmp_path / ".agents" / "skills"
    broken_target = agents_root / "skill-from-masters" / "skills" / "search-skill"
    broken_link = skills_root / "search-skill"
    broken_link.symlink_to(broken_target)

    source_template = tmp_path / "source-template"
    _write_skill(source_template / "skills" / "search-skill")

    def fake_runner(command: Sequence[str]) -> int:
        assert command[:4] == ["git", "clone", "--depth", "1"]
        destination = Path(command[5])
        shutil.copytree(source_template, destination)
        return 0

    report = skills_health.run_health_check(
        skill_roots=[skills_root],
        agents_root=agents_root,
        source_repo_map={"skill-from-masters": "https://example.invalid/skill-from-masters.git"},
        relink_rules={},
        repair=True,
        command_runner=fake_runner,
    )

    assert not report.issues
    assert report.cloned_repos == ["skill-from-masters"]
    assert broken_link.exists()
    assert (broken_link / "SKILL.md").is_file()


def test_repair_relinks_find_skills_to_known_target(tmp_path: Path) -> None:
    claude_skills = tmp_path / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    agents_root = tmp_path / ".agents" / "skills"

    broken_link = claude_skills / "find-skills"
    broken_link.symlink_to(agents_root / "find-skills")

    fixed_target = agents_root / "vercel-labs-skills" / "skills" / "find-skills"
    _write_skill(fixed_target)

    report = skills_health.run_health_check(
        skill_roots=[claude_skills],
        agents_root=agents_root,
        source_repo_map={},
        relink_rules={"find-skills": fixed_target},
        repair=True,
    )

    assert not report.issues
    assert broken_link.resolve() == fixed_target.resolve()
    assert any("find-skills" in action for action in report.repaired_actions)
