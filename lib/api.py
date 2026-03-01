#!/usr/bin/env python3
"""Public API entry points for intelligent confirmation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .confirmation import IntelligentConfirmation
from .gep_store import GEPStore


class ConfirmationAPI:
    """API wrapper for external integrations (for example gateway services)."""

    def __init__(self, memory_dir: Path | None = None):
        if memory_dir is None:
            memory_dir = Path.cwd() / ".openclaw_memory"

        self.memory_dir = Path(memory_dir)
        self.gep_store = self._bootstrap_gep_store(self.memory_dir)
        self.conf_engine = IntelligentConfirmation(self.gep_store)

    @staticmethod
    def _bootstrap_gep_store(memory_dir: Path) -> GEPStore:
        """Create and initialize GEP storage files when missing."""
        gep_dir = memory_dir / "gep"
        store = GEPStore(gep_dir)

        if not store.genes_file.exists():
            store.save_genes({})
        if not store.capsules_file.exists():
            store.save_capsules({})
        if not store.events_file.exists():
            store.events_file.touch()

        return store

    def should_auto_execute(self, task: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """Return `(auto_execute, reason, details)` for one task context."""
        should_confirm, reason = self.conf_engine.should_confirm(task)
        confidence_info = self.conf_engine.get_confidence_info(task)

        details: dict[str, Any] = {
            "confidence": confidence_info["max_confidence"],
            "success_streak": confidence_info["min_success_streak"],
            "relevant_genes_count": confidence_info["count"],
        }
        return not should_confirm, reason, details

    def record_execution_result(self, task: dict[str, Any], success: bool, auto_executed: bool) -> None:
        """Persist execution feedback into gene confidence history."""
        self.conf_engine.record_feedback(
            task,
            was_confirmed=not auto_executed,
            user_cancelled=not success,
        )

    def get_confidence_history(self, task_type: str | None = None) -> dict[str, Any]:
        """Return confidence history, optionally filtered by task type."""
        genes = self.gep_store.load_genes()

        if task_type:
            relevant_genes = [gene for gene in genes.values() if task_type in gene.trigger]
        else:
            relevant_genes = [gene for gene in genes.values() if gene.confidence > 0.5]

        return {
            "genes": [
                {
                    "id": gene.id,
                    "summary": gene.summary,
                    "confidence": gene.confidence,
                    "success_streak": gene.success_streak,
                }
                for gene in sorted(relevant_genes, key=lambda item: -item.confidence)
            ]
        }

    def get_explanation(self, task: dict[str, Any], should_confirm: bool, reason: str) -> str:
        """Return a readable explanation for one confirmation decision."""
        return self.conf_engine.get_explanation(task, should_confirm, reason)


def create_api(memory_dir: Path | None = None) -> ConfirmationAPI:
    """Convenience factory for `ConfirmationAPI`."""
    return ConfirmationAPI(memory_dir)
