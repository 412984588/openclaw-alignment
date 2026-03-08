#!/usr/bin/env python3
"""
Audit and optionally repair local Codex/Claude skill directories.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

CommandRunner = Callable[[list[str]], int]


@dataclass(frozen=True)
class HealthIssue:
    code: str
    severity: str
    path: str
    detail: str


@dataclass
class HealthReport:
    checked_roots: list[str]
    checked_entries: int
    issues: list[HealthIssue]
    cloned_repos: list[str]
    repaired_actions: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "checked_roots": self.checked_roots,
            "checked_entries": self.checked_entries,
            "issues": [asdict(issue) for issue in self.issues],
            "cloned_repos": self.cloned_repos,
            "repaired_actions": self.repaired_actions,
        }


DEFAULT_SOURCE_REPO_MAP: dict[str, str] = {
    "_anthropics-skills": "https://github.com/anthropics/skills.git",
    "agent-skills-context-engineering": "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering.git",
    "ai-skills-sanjay": "https://github.com/sanjay3290/ai-skills.git",
    "awesome-claude-skills": "https://github.com/ComposioHQ/awesome-claude-skills.git",
    "beautiful_prose": "https://github.com/SHADOWPR0/beautiful_prose.git",
    "skill-from-masters": "https://github.com/GBSOSS/skill-from-masters.git",
    "trailofbits-skills": "https://github.com/trailofbits/skills.git",
    "ui-ux-pro-max-skill": "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git",
    "vercel-labs-agent-skills": "https://github.com/vercel-labs/agent-skills.git",
    "vercel-labs-skills": "https://github.com/vercel-labs/skills.git",
    "x-article-publisher-skill": "https://github.com/wshuyi/x-article-publisher-skill.git",
}

NON_SKILL_SUPPORT_DIRS: set[str] = {
    "assets",
    "core",
    "docs",
    "reference",
    "references",
    "resources",
    "scripts",
    "templates",
}


def default_relink_rules(agents_root: Path) -> dict[str, Path]:
    return {
        "find-skills": agents_root / "vercel-labs-skills" / "skills" / "find-skills",
    }


def _run_command(command: list[str]) -> int:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return result.returncode
    return 0


def _resolve_symlink_target(path: Path) -> Path:
    target = Path(os.readlink(path))
    if target.is_absolute():
        return target
    return (path.parent / target).resolve(strict=False)


def _extract_repo_name(target: Path, agents_root: Path) -> str | None:
    try:
        relative_path = target.relative_to(agents_root)
    except ValueError:
        return None
    if not relative_path.parts:
        return None
    return relative_path.parts[0]


def _has_nested_skills(path: Path) -> bool:
    for child in path.iterdir():
        if child.is_dir() and (child / "SKILL.md").is_file():
            return True
    return False


def _scan_one_root(root: Path, agents_root: Path) -> tuple[list[HealthIssue], int]:
    issues: list[HealthIssue] = []
    checked_entries = 0

    if not root.exists():
        issues.append(
            HealthIssue(
                code="ROOT_NOT_FOUND",
                severity="P1",
                path=str(root),
                detail="Skill root does not exist.",
            )
        )
        return issues, checked_entries

    for entry in sorted(root.iterdir()):
        checked_entries += 1

        if entry.is_symlink():
            target = _resolve_symlink_target(entry)
            if not target.exists():
                repo_name = _extract_repo_name(target, agents_root)
                detail = f"Broken symlink target: {target}"
                if repo_name:
                    detail += f" (source repo: {repo_name})"
                issues.append(
                    HealthIssue(
                        code="BROKEN_SYMLINK",
                        severity="P0",
                        path=str(entry),
                        detail=detail,
                    )
                )
                continue

            if target.is_dir() and not (target / "SKILL.md").is_file() and not _has_nested_skills(target):
                issues.append(
                    HealthIssue(
                        code="TARGET_MISSING_SKILL_MD",
                        severity="P1",
                        path=str(entry),
                        detail=f"Linked target has no SKILL.md: {target}",
                    )
                )
            continue

        if not entry.is_dir():
            continue

        if entry.name.startswith("."):
            continue

        if entry.name in NON_SKILL_SUPPORT_DIRS:
            continue

        if (entry / "SKILL.md").is_file():
            continue

        if _has_nested_skills(entry):
            continue

        issues.append(
            HealthIssue(
                code="MISSING_SKILL_MD",
                severity="P2",
                path=str(entry),
                detail="Directory has no SKILL.md and is not a skill namespace.",
            )
        )

    return issues, checked_entries


def _scan_all_roots(skill_roots: list[Path], agents_root: Path) -> tuple[list[HealthIssue], int]:
    all_issues: list[HealthIssue] = []
    total_entries = 0

    for root in skill_roots:
        issues, count = _scan_one_root(root, agents_root)
        all_issues.extend(issues)
        total_entries += count

    return all_issues, total_entries


def _ensure_repo(
    repo_name: str,
    agents_root: Path,
    source_repo_map: dict[str, str],
    command_runner: CommandRunner,
) -> bool:
    repo_path = agents_root / repo_name
    if repo_path.exists():
        return True

    source_url = source_repo_map.get(repo_name)
    if not source_url:
        return False

    repo_path.parent.mkdir(parents=True, exist_ok=True)
    command = ["git", "clone", "--depth", "1", source_url, str(repo_path)]
    return command_runner(command) == 0 and repo_path.exists()


def _replace_symlink(link_path: Path, target_path: Path) -> None:
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(target_path)


def _repair_issues(
    issues: list[HealthIssue],
    agents_root: Path,
    source_repo_map: dict[str, str],
    relink_rules: dict[str, Path],
    command_runner: CommandRunner,
) -> tuple[list[str], list[str]]:
    cloned_repos: list[str] = []
    repaired_actions: list[str] = []
    seen_clones: set[str] = set()

    for issue in issues:
        if issue.code != "BROKEN_SYMLINK":
            continue

        link_path = Path(issue.path)
        if not link_path.is_symlink():
            continue

        desired_target = relink_rules.get(link_path.name)
        if desired_target is not None:
            desired_repo = _extract_repo_name(desired_target, agents_root)
            if desired_repo and desired_repo not in seen_clones:
                if _ensure_repo(desired_repo, agents_root, source_repo_map, command_runner):
                    seen_clones.add(desired_repo)
                    cloned_repos.append(desired_repo)
            if desired_target.exists():
                _replace_symlink(link_path, desired_target)
                repaired_actions.append(f"Relinked {link_path} -> {desired_target}")
                continue

        broken_target = _resolve_symlink_target(link_path)
        repo_name = _extract_repo_name(broken_target, agents_root)
        if not repo_name:
            continue

        if repo_name not in seen_clones:
            if _ensure_repo(repo_name, agents_root, source_repo_map, command_runner):
                seen_clones.add(repo_name)
                cloned_repos.append(repo_name)

        if broken_target.exists():
            repaired_actions.append(f"Restored source for {link_path}")

    return cloned_repos, repaired_actions


def run_health_check(
    skill_roots: list[Path],
    agents_root: Path,
    source_repo_map: dict[str, str],
    relink_rules: dict[str, Path],
    repair: bool,
    command_runner: CommandRunner = _run_command,
) -> HealthReport:
    issues, checked_entries = _scan_all_roots(skill_roots, agents_root)
    cloned_repos: list[str] = []
    repaired_actions: list[str] = []

    if repair and issues:
        cloned_repos, repaired_actions = _repair_issues(
            issues=issues,
            agents_root=agents_root,
            source_repo_map=source_repo_map,
            relink_rules=relink_rules,
            command_runner=command_runner,
        )
        issues, checked_entries = _scan_all_roots(skill_roots, agents_root)

    return HealthReport(
        checked_roots=[str(path) for path in skill_roots],
        checked_entries=checked_entries,
        issues=issues,
        cloned_repos=cloned_repos,
        repaired_actions=repaired_actions,
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit and repair local skill directories.")
    parser.add_argument("--repair", action="store_true", help="Attempt auto-repair for known issues.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument("--codex-root", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--claude-root", type=Path, default=Path.home() / ".claude" / "skills")
    parser.add_argument("--agents-root", type=Path, default=Path.home() / ".agents" / "skills")
    return parser


def main() -> int:
    parser = _build_argument_parser()
    args = parser.parse_args()

    skill_roots = [args.codex_root, args.claude_root]
    relink_rules = default_relink_rules(args.agents_root)
    report = run_health_check(
        skill_roots=skill_roots,
        agents_root=args.agents_root,
        source_repo_map=DEFAULT_SOURCE_REPO_MAP,
        relink_rules=relink_rules,
        repair=args.repair,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(
            "[skills-health] "
            f"roots={len(report.checked_roots)} "
            f"entries={report.checked_entries} "
            f"issues={len(report.issues)} "
            f"cloned={len(report.cloned_repos)} "
            f"repaired={len(report.repaired_actions)}"
        )
        for issue in report.issues:
            print(f"- [{issue.severity}] {issue.code} {issue.path}: {issue.detail}")
        for action in report.repaired_actions:
            print(f"- [repair] {action}")

    return 0 if not report.issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
