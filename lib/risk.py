#!/usr/bin/env python3
"""Risk assessment helpers for confirmation decisions."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Mapping, Sequence


class RiskLevel(Enum):
    """Risk categories for task execution."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def _safe_text(task_context: Mapping[str, Any], key: str) -> str:
    value = task_context.get(key, "")
    if isinstance(value, str):
        return value
    return str(value)


def _safe_files(task_context: Mapping[str, Any]) -> list[str]:
    raw_files = task_context.get("files", [])
    if not isinstance(raw_files, Sequence) or isinstance(raw_files, (str, bytes)):
        return []
    return [str(item) for item in raw_files]


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _max_risk(current: RiskLevel, new: RiskLevel) -> RiskLevel:
    order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    return new if order[new] > order[current] else current


class RiskAssessor:
    """Classify task contexts into coarse execution risk buckets."""

    def __init__(self) -> None:
        self.high_risk_keywords = [
            "rm",
            "remove",
            "delete",
            "unlink",
            "rmdir",
            "format",
            "fdisk",
            "mkfs",
            "chmod",
            "chown",
            "iptables",
            "docker",
            "podman",
            "kubectl",
            "git push --force",
            "git reset --hard",
        ]
        self.medium_risk_keywords = [
            "database",
            "migrate",
            "schema",
            "api",
            "fetch",
            "request",
            "install",
            "uninstall",
            "update",
        ]
        self.low_risk_keywords = [
            "test",
            "tests",
            "format",
            "lint",
            "check",
            "log",
            "status",
            "info",
            "list",
            "validate",
            "verify",
            "docs",
            "read",
            "view",
            "show",
            "display",
            "inspect",
            "describe",
            "explain",
            "analyze",
            "measure",
            "benchmark",
            "profile",
            "build",
            "compile",
            "bundle",
        ]

    def assess(self, task_context: Mapping[str, Any]) -> RiskLevel:
        """Return only the risk bucket for one task."""
        risk_level, _ = self.assess_details(task_context)
        return risk_level

    def assess_details(self, task_context: Mapping[str, Any]) -> tuple[RiskLevel, list[str]]:
        """Assess risk and return the heuristic basis for that assessment."""
        task_desc = _normalize_text(_safe_text(task_context, "task_description"))
        command = _normalize_text(_safe_text(task_context, "command"))
        files = _safe_files(task_context)
        combined_text = f"{task_desc} {command}".strip()

        risk_level = RiskLevel.MEDIUM
        basis: list[str] = []

        context_risk, context_basis = self._assess_command_context(command)
        if context_basis:
            basis.extend(context_basis)
            risk_level = _max_risk(risk_level, context_risk)

        for keyword in self.high_risk_keywords:
            if keyword == "format":
                if any(ctx in combined_text for ctx in ["mkfs", "fdisk", "format disk", "format /dev"]):
                    basis.append("HIGH risk keyword: format disk")
                    risk_level = _max_risk(risk_level, RiskLevel.CRITICAL)
                continue
            if " " in keyword:
                if keyword in combined_text:
                    basis.append(f"HIGH risk keyword: {keyword}")
                    risk_level = _max_risk(risk_level, RiskLevel.CRITICAL)
                continue
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                basis.append(f"HIGH risk keyword: {keyword}")
                risk_level = _max_risk(risk_level, RiskLevel.CRITICAL)

        for keyword in self.medium_risk_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                basis.append(f"MEDIUM risk keyword: {keyword}")
                risk_level = _max_risk(risk_level, RiskLevel.MEDIUM)

        for keyword in self.low_risk_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                basis.append(f"LOW risk keyword: {keyword}")
                risk_level = RiskLevel.LOW if risk_level == RiskLevel.MEDIUM else risk_level

        file_risk, file_basis = self._assess_file_operation_risk_details(files)
        if file_basis:
            basis.extend(file_basis)
            risk_level = _max_risk(risk_level, file_risk)

        if not basis:
            basis.append("No strong heuristic match")

        return risk_level, basis

    def _assess_command_context(self, command: str) -> tuple[RiskLevel, list[str]]:
        if "git" in command:
            if any(item in command for item in ["git status", "git log", "git diff", "git show"]):
                return RiskLevel.LOW, ["LOW risk command context: git read-only"]
            if "git push" in command and "--force" not in command:
                return RiskLevel.MEDIUM, ["MEDIUM risk command context: git push"]
            if any(item in command for item in ["git commit", "git add"]):
                return RiskLevel.LOW, ["LOW risk command context: git local write"]

        if any(item in command for item in ["npm run", "pnpm run", "yarn"]):
            if any(item in command for item in ["test", "lint", "format", "check", "build"]):
                return RiskLevel.LOW, ["LOW risk command context: package manager verification command"]

        if "python" in command or "pytest" in command:
            if any(item in command for item in ["-m pytest", "pytest", "mypy", "black", "ruff"]):
                return RiskLevel.LOW, ["LOW risk command context: Python verification command"]

        return RiskLevel.MEDIUM, []

    def _assess_file_operation_risk_details(self, files: Sequence[str]) -> tuple[RiskLevel, list[str]]:
        if not files:
            return RiskLevel.MEDIUM, []

        basis: list[str] = []
        risk_level = RiskLevel.MEDIUM
        for file_path in files:
            normalized = _normalize_text(str(file_path))
            if any(item in normalized for item in ["home", "etc", "system", "root"]):
                basis.append(f"HIGH risk file path: {file_path}")
                risk_level = _max_risk(risk_level, RiskLevel.HIGH)
            if any(item in normalized for item in [".env", "config.py", "config.json", "secrets"]):
                basis.append(f"HIGH risk file path: {file_path}")
                risk_level = _max_risk(risk_level, RiskLevel.HIGH)
            if any(item in normalized for item in ["package.json", "requirements.txt", "pom.xml", "build.gradle"]):
                basis.append(f"MEDIUM risk file path: {file_path}")
                risk_level = _max_risk(risk_level, RiskLevel.MEDIUM)
            if any(item in normalized for item in ["delete", "remove", "unlink"]):
                basis.append(f"CRITICAL risk file path: {file_path}")
                risk_level = _max_risk(risk_level, RiskLevel.CRITICAL)
        return risk_level, basis
