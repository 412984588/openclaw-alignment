#!/usr/bin/env python3
"""Public API entry points for intelligent confirmation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .confirmation import IntelligentConfirmation
from .policy_store import PolicyStore


class ConfirmationAPI:
    """API wrapper for external integrations (for example gateway services)."""

    def __init__(self, memory_dir: Path | None = None):
        if memory_dir is None:
            memory_dir = Path.cwd() / ".openclaw_memory"

        self.memory_dir = Path(memory_dir)
        self.policy_store = self._bootstrap_policy_store(self.memory_dir)
        self.conf_engine = IntelligentConfirmation(
            self.policy_store,
            project_scope_key=str(self.memory_dir.parent.resolve()),
        )

    @staticmethod
    def _bootstrap_policy_store(memory_dir: Path) -> PolicyStore:
        """Create and initialize policy storage files when missing."""
        return PolicyStore.bootstrap(memory_dir, ensure_files=True)

    def should_auto_execute(self, task: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        """Return `(auto_execute, reason, details)` for one task context."""
        decision = self.conf_engine.evaluate_task(task, persist=True)

        details: dict[str, Any] = {
            "decision_id": decision["decision_id"],
            "decision": decision,
            "matched_rules": decision["matched_rules"],
            "confidence": decision["confidence"]["max_confidence"],
            "success_streak": 0,
            "relevant_rules_count": decision["confidence"]["matched_rule_count"],
        }
        return decision["final_decision"] == "auto_execute", decision["reason"], details

    def record_execution_result(
        self,
        task: dict[str, Any],
        success: bool,
        auto_executed: bool,
        decision_id: str | None = None,
        execution_result: str | None = None,
        user_override: str | None = None,
    ) -> None:
        """Persist execution feedback into policy confidence history."""
        self.conf_engine.record_feedback(
            task,
            was_confirmed=not auto_executed,
            user_cancelled=not success,
            decision_id=decision_id,
            execution_result=execution_result,
            user_override=user_override,
        )

    def get_confidence_history(self, task_type: str | None = None) -> dict[str, Any]:
        """Return confidence history, optionally filtered by task type."""
        rules = self.policy_store.load_rules()

        if task_type:
            relevant_rules = [
                rule
                for rule in rules.values()
                if task_type in rule.trigger or f"task_type:{task_type}" in rule.trigger
            ]
        else:
            relevant_rules = [rule for rule in rules.values() if rule.confidence > 0.5]

        history = [
            {
                "id": rule.id,
                "summary": rule.summary,
                "confidence": rule.confidence,
                "success_streak": rule.success_streak,
                "status": rule.status,
                "scope": rule.scope,
                "source_type": rule.source_type,
                "policy_decision": rule.policy_decision,
            }
            for rule in sorted(relevant_rules, key=lambda item: -item.confidence)
        ]
        return {"rules": history}

    def get_recent_decisions(self, limit: int = 20) -> dict[str, Any]:
        """Return merged decision evaluation/outcome history."""
        events = list(reversed(self.policy_store.get_decision_events(limit=limit * 10)))
        merged: dict[str, dict[str, Any]] = {}

        for event in events:
            decision_id = event.payload.get("decision_id")
            if not decision_id:
                continue

            record = merged.setdefault(
                decision_id,
                {
                    "decision_id": decision_id,
                    "execution_result": "",
                    "user_override": "",
                    "rollback_happened": False,
                    "lifecycle_transition": "",
                },
            )
            if event.event_type == "decision_evaluated":
                record.update(event.payload)
            elif event.event_type == "decision_outcome":
                record["execution_result"] = event.payload.get("execution_result", "")
                record["user_override"] = event.payload.get("user_override", "")
                record["rollback_happened"] = event.payload.get("rollback_happened", False)
                record["lifecycle_transition"] = event.payload.get("lifecycle_transition", "")

        decisions = sorted(
            merged.values(),
            key=lambda item: item.get("timestamp", ""),
            reverse=True,
        )[:limit]
        return {"decisions": decisions}

    def get_explanation(self, task: dict[str, Any], should_confirm: bool, reason: str) -> str:
        """Return a readable explanation for one confirmation decision."""
        return self.conf_engine.get_explanation(task, should_confirm, reason)


def create_api(memory_dir: Path | None = None) -> ConfirmationAPI:
    """Convenience factory for `ConfirmationAPI`."""
    return ConfirmationAPI(memory_dir)
