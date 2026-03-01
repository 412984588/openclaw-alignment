#!/usr/bin/env python3
"""Intelligent confirmation decision engine.

The engine decides whether user confirmation is required based on:
1. task risk assessment,
2. learned confidence from GEP genes, and
3. recent success streak.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Mapping, Sequence, TypedDict

from .gep import Event, Gene
from .gep_store import GEPStore


class RiskLevel(Enum):
    """Risk categories for task execution."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceInfo(TypedDict):
    """Confidence summary for genes related to one task."""

    max_confidence: float
    avg_confidence: float
    min_success_streak: int
    count: int
    genes: list[Gene]


class IntelligentConfirmation:
    """Risk-aware confirmation policy with feedback learning."""

    def __init__(self, gep_store: GEPStore | None = None) -> None:
        self.gep_store = gep_store

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

    @staticmethod
    def _safe_text(task_context: Mapping[str, Any], key: str) -> str:
        value = task_context.get(key, "")
        if isinstance(value, str):
            return value
        return str(value)

    @staticmethod
    def _safe_files(task_context: Mapping[str, Any]) -> list[str]:
        raw_files = task_context.get("files", [])
        if not isinstance(raw_files, Sequence) or isinstance(raw_files, (str, bytes)):
            return []
        return [str(item) for item in raw_files]

    def should_confirm(self, task_context: Mapping[str, Any]) -> tuple[bool, str]:
        """Return `(needs_confirmation, reason)` for a task."""
        risk_level = self.assess_risk(task_context)
        confidence_info = self.get_confidence_info(task_context)
        return self._decide(risk_level, confidence_info)

    def assess_risk(self, task_context: Mapping[str, Any]) -> RiskLevel:
        """Assess task risk from command, description and file paths."""
        task_desc = self._safe_text(task_context, "task_description").lower()
        command = self._safe_text(task_context, "command").lower()
        files = self._safe_files(task_context)
        combined_text = f"{task_desc} {command}".strip()

        context_risk = self._assess_command_context(command)
        if context_risk != RiskLevel.MEDIUM:
            return context_risk

        for keyword in self.high_risk_keywords:
            if keyword == "format":
                if any(ctx in combined_text for ctx in ["mkfs", "fdisk", "format disk", "format /dev"]):
                    return RiskLevel.CRITICAL
                continue
            if " " in keyword:
                if keyword in combined_text:
                    return RiskLevel.CRITICAL
                continue
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                return RiskLevel.CRITICAL

        for keyword in self.medium_risk_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                return RiskLevel.MEDIUM

        for keyword in self.low_risk_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, combined_text):
                return RiskLevel.LOW

        file_risk = self.assess_file_operation_risk(files)
        if file_risk != RiskLevel.MEDIUM:
            return file_risk

        return RiskLevel.MEDIUM

    def _assess_command_context(self, command: str) -> RiskLevel:
        """Risk overrides for known command patterns."""
        if "git" in command:
            if any(item in command for item in ["git status", "git log", "git diff", "git show"]):
                return RiskLevel.LOW
            if "git push" in command and "--force" not in command:
                return RiskLevel.MEDIUM
            if any(item in command for item in ["git commit", "git add"]):
                return RiskLevel.LOW

        if any(item in command for item in ["npm run", "pnpm run", "yarn"]):
            if any(item in command for item in ["test", "lint", "format", "check", "build"]):
                return RiskLevel.LOW

        if "python" in command or "pytest" in command:
            if any(item in command for item in ["-m pytest", "test", "mypy", "black", "ruff"]):
                return RiskLevel.LOW

        return RiskLevel.MEDIUM

    def assess_file_operation_risk(self, files: Sequence[str]) -> RiskLevel:
        """Assess risk from touched file paths."""
        if not files:
            return RiskLevel.MEDIUM

        for file_path in files:
            normalized = str(file_path).lower()

            if any(item in normalized for item in ["home", "etc", "system", "root"]):
                return RiskLevel.HIGH
            if any(item in normalized for item in [".env", "config.py", "config.json", "secrets"]):
                return RiskLevel.HIGH
            if any(item in normalized for item in ["package.json", "requirements.txt", "pom.xml", "build.gradle"]):
                return RiskLevel.MEDIUM
            if any(item in normalized for item in ["delete", "remove", "unlink"]):
                return RiskLevel.CRITICAL
            if any(normalized.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".md", ".txt"]):
                return RiskLevel.LOW

        return RiskLevel.MEDIUM

    def get_confidence_info(self, task_context: Mapping[str, Any]) -> ConfidenceInfo:
        """Return confidence metrics for genes matching the task."""
        empty_info: ConfidenceInfo = {
            "max_confidence": 0.0,
            "avg_confidence": 0.0,
            "min_success_streak": 0,
            "count": 0,
            "genes": [],
        }
        if not self.gep_store:
            return empty_info

        genes = self.gep_store.load_genes()
        task_type = self._safe_text(task_context, "task_type") or "T2"
        task_desc = self._safe_text(task_context, "task_description").lower()

        relevant_genes: list[Gene] = []
        for gene in genes.values():
            trigger_values = [trigger.lower() for trigger in gene.trigger]
            if task_type in gene.trigger:
                relevant_genes.append(gene)
                continue
            if any(trigger in task_desc for trigger in trigger_values):
                relevant_genes.append(gene)

        if not relevant_genes:
            return empty_info

        confidences = [gene.confidence for gene in relevant_genes]
        return {
            "max_confidence": max(confidences),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_success_streak": min(gene.success_streak for gene in relevant_genes),
            "count": len(relevant_genes),
            "genes": relevant_genes,
        }

    def _decide(self, risk_level: RiskLevel, confidence_info: ConfidenceInfo) -> tuple[bool, str]:
        """Apply policy thresholds and return decision + reason."""
        confidence = confidence_info["max_confidence"]
        success_streak = confidence_info["min_success_streak"]
        count = confidence_info["count"]

        if count == 0:
            return True, "First-time task category: confirmation required"

        if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return True, f"{risk_level.value.upper()} risk operation: confirmation required"

        if confidence >= 0.9 and risk_level == RiskLevel.LOW:
            if success_streak >= 5:
                return False, f"High confidence ({confidence:.2f}) with {success_streak} consecutive successes"
            return False, f"High confidence ({confidence:.2f}) with low risk"

        if confidence >= 0.8 and risk_level == RiskLevel.LOW:
            return False, f"Medium confidence ({confidence:.2f}) with low risk"

        if confidence >= 0.8 and risk_level == RiskLevel.MEDIUM and success_streak >= 10:
            return False, f"Medium confidence ({confidence:.2f}) with strong success streak ({success_streak})"

        return True, f"Insufficient confidence ({confidence:.2f}); confirmation required"

    def record_feedback(self, task_context: Mapping[str, Any], was_confirmed: bool, user_cancelled: bool) -> None:
        """Update related genes based on task outcome feedback."""
        if not self.gep_store:
            return

        from datetime import datetime

        genes = self.gep_store.load_genes()
        task_type = self._safe_text(task_context, "task_type") or "T2"

        relevant_genes = [gene for gene in genes.values() if task_type in gene.trigger]

        if not relevant_genes:
            gene_id = f"gene_{task_type.lower()}_confirmation"
            if gene_id not in genes:
                new_gene = Gene(
                    id=gene_id,
                    summary=f"Confirmation preference for {task_type}",
                    category="harden",
                    strategy=(
                        f"Use execution history to decide whether {task_type} tasks "
                        "can run without explicit confirmation."
                    ),
                    trigger=[task_type],
                    confidence=0.0,
                    success_streak=0,
                )
                new_gene.calculate_asset_id()
                genes[gene_id] = new_gene
            relevant_genes = [genes[gene_id]]

        updated = False
        for gene in relevant_genes:
            original_confidence = gene.confidence

            if user_cancelled:
                gene.success_streak = 0
                gene.confidence = max(0.0, gene.confidence - 0.2)
                reward = -0.2
                changes = (
                    f"User cancelled execution; confidence {original_confidence:.2f} "
                    f"-> {gene.confidence:.2f}"
                )
                source = "user_feedback"
            elif not was_confirmed:
                gene.success_streak += 1
                gene.confidence = min(1.0, gene.confidence + 0.05)
                reward = 0.05
                changes = (
                    f"Auto-execution succeeded; confidence {original_confidence:.2f} "
                    f"-> {gene.confidence:.2f}"
                )
                source = "auto_execution"
            else:
                gene.success_streak += 1
                gene.confidence = min(1.0, gene.confidence + 0.03)
                reward = 0.03
                changes = (
                    f"User-confirmed execution succeeded; confidence {original_confidence:.2f} "
                    f"-> {gene.confidence:.2f}"
                )
                source = "user_confirmed"

            self.gep_store.append_event(
                Event(
                    timestamp=datetime.now().isoformat(),
                    event_type="gene_updated",
                    asset_id=gene.asset_id,
                    rl_reward=reward,
                    changes=changes,
                    source_node_id=source,
                )
            )
            updated = True

        if updated:
            self.gep_store.save_genes(genes)

    def get_explanation(self, task_context: Mapping[str, Any], should_confirm: bool, reason: str) -> str:
        """Return a human-readable explanation for the decision."""
        if should_confirm:
            return f"Confirmation required: {reason}"

        info = self.get_confidence_info(task_context)
        explanation = f"Auto-execute: {reason}\n"
        relevant_genes = info["genes"]
        if relevant_genes:
            top_gene = max(relevant_genes, key=lambda gene: gene.confidence)
            explanation += f"Primary signal: {top_gene.summary}\n"
            explanation += (
                f"Confidence: {top_gene.confidence:.2f} | "
                f"Success streak: {top_gene.success_streak}"
            )
        return explanation
