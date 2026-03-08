#!/usr/bin/env python3
"""Persistence layer for canonical policy assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .policy_models import Playbook, PolicyEvent, Rule


class PolicyStore:
    """Storage manager for rules, playbooks, and policy events."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.rules_file = self.base_dir / "rules.json"
        self.playbooks_file = self.base_dir / "playbooks.json"
        self.policy_events_file = self.base_dir / "policy_events.jsonl"

    @classmethod
    def bootstrap(cls, memory_dir: Path, *, ensure_files: bool = False) -> "PolicyStore":
        """Open canonical policy storage for one memory directory."""
        store = cls(Path(memory_dir) / "policy")
        if ensure_files:
            if not store.rules_file.exists():
                store.save_rules({})
            if not store.playbooks_file.exists():
                store.save_playbooks({})
            if not store.policy_events_file.exists():
                store.policy_events_file.touch()
        return store

    @staticmethod
    def _read_json_mapping(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"⚠️  Failed to load {path.name}: {exc}")
            return None

    @staticmethod
    def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
        temp_file = path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(path)

    def load_rules(self) -> dict[str, Rule]:
        """Load all rules from canonical storage."""
        data = self._read_json_mapping(self.rules_file) or {}
        return {rule_id: Rule.from_dict(rule_data) for rule_id, rule_data in data.items()}

    def save_rules(self, rules: dict[str, Rule]) -> None:
        """Persist canonical rules to disk."""
        data = {rule_id: rule.to_dict() for rule_id, rule in rules.items()}
        self._atomic_write_json(self.rules_file, data)

    def load_playbooks(self) -> dict[str, Playbook]:
        """Load all playbooks from canonical storage."""
        data = self._read_json_mapping(self.playbooks_file) or {}
        return {
            playbook_id: Playbook.from_dict(playbook_data)
            for playbook_id, playbook_data in data.items()
        }

    def save_playbooks(self, playbooks: dict[str, Playbook]) -> None:
        """Persist canonical playbooks to disk."""
        data = {
            playbook_id: playbook.to_dict()
            for playbook_id, playbook in playbooks.items()
        }
        self._atomic_write_json(self.playbooks_file, data)

    def _read_event_lines(self) -> list[str]:
        if not self.policy_events_file.exists():
            return []
        return self.policy_events_file.read_text(encoding="utf-8").splitlines()

    def append_event(self, event: PolicyEvent) -> None:
        """Append one policy event to canonical event storage."""
        if not self.policy_events_file.exists():
            self.policy_events_file.touch()
        with open(self.policy_events_file, "a", encoding="utf-8") as handle:
            handle.write(event.to_jsonl() + "\n")

    def get_events(self, limit: int = 100) -> list[PolicyEvent]:
        """Return latest events in reverse chronological order."""
        events: list[PolicyEvent] = []
        try:
            lines = self._read_event_lines()
            for line in reversed(lines[-limit:]):
                payload = line.strip()
                if not payload:
                    continue
                try:
                    events.append(PolicyEvent.from_jsonl(payload))
                except Exception:
                    continue
            return events
        except Exception as exc:
            print(f"⚠️  Failed to read policy events: {exc}")
            return []

    def get_events_by_type(self, event_types: set[str], limit: int = 100) -> list[PolicyEvent]:
        """Return latest events matching a set of event types."""
        return [event for event in self.get_events(limit=limit) if event.event_type in event_types]

    def get_policy_events(self, limit: int = 100) -> list[PolicyEvent]:
        """Return latest policy events."""
        return self.get_events(limit=limit)

    def get_decision_events(self, limit: int = 100) -> list[PolicyEvent]:
        """Return latest decision evaluation/outcome events."""
        return self.get_events_by_type({"decision_evaluated", "decision_outcome"}, limit=limit)

    def get_recent_lifecycle_events(self, limit: int = 100) -> list[PolicyEvent]:
        """Return recent lifecycle transition events."""
        return self.get_events_by_type(
            {"rule_promoted", "rule_suspended", "rule_reactivated", "rule_archived"},
            limit=limit,
        )

    def get_rules_by_status(self, status: str) -> list[Rule]:
        """Return rules filtered by lifecycle status."""
        return [rule for rule in self.load_rules().values() if rule.status == status]

    def get_risky_confirmed_rules(self) -> list[Rule]:
        """Return confirmed high-risk rules that currently auto execute."""
        return [
            rule
            for rule in self.load_rules().values()
            if rule.status == "confirmed"
            and rule.policy_decision == "auto_execute"
            and rule.risk_level in {"high", "critical"}
        ]

    def get_policy_status_snapshot(self) -> dict[str, Any]:
        """Return a lightweight operational snapshot for policy lifecycle monitoring."""
        rules = list(self.load_rules().values())
        lifecycle_events = self.get_recent_lifecycle_events(limit=100)
        status_counts = {
            status: sum(1 for rule in rules if rule.status == status)
            for status in ["hint", "candidate", "confirmed", "suspended", "archived"]
        }

        special_scopes = [
            {
                "id": rule.id,
                "scope": rule.scope,
                "scope_key": rule.scope_key,
                "status": rule.status,
                "policy_decision": rule.policy_decision,
            }
            for rule in rules
            if rule.scope in {"domain", "project"} and rule.status in {"confirmed", "suspended"}
        ]

        return {
            "status_counts": status_counts,
            "recent_promotions": [
                event.payload for event in lifecycle_events if event.event_type == "rule_promoted"
            ],
            "recent_suspensions": [
                event.payload for event in lifecycle_events if event.event_type == "rule_suspended"
            ],
            "risky_confirmed_rules": [
                {
                    "id": rule.id,
                    "summary": rule.summary,
                    "risk_level": rule.risk_level,
                    "scope": rule.scope,
                    "scope_key": rule.scope_key,
                }
                for rule in self.get_risky_confirmed_rules()
            ],
            "special_scopes": special_scopes,
        }

    def get_rule(self, rule_id: str) -> Rule | None:
        """Return one rule by id."""
        return self.load_rules().get(rule_id)

    def save_rule(self, rule: Rule) -> None:
        """Insert or update one rule."""
        rules = self.load_rules()
        rules[rule.id] = rule
        self.save_rules(rules)

    def get_playbook(self, playbook_id: str) -> Playbook | None:
        """Return one playbook by id."""
        return self.load_playbooks().get(playbook_id)

    def save_playbook(self, playbook: Playbook) -> None:
        """Insert or update one playbook."""
        playbooks = self.load_playbooks()
        playbooks[playbook.id] = playbook
        self.save_playbooks(playbooks)

    def delete_rule(self, rule_id: str) -> bool:
        """Delete one rule if it exists."""
        rules = self.load_rules()
        if rule_id not in rules:
            return False
        del rules[rule_id]
        self.save_rules(rules)
        return True

    def delete_playbook(self, playbook_id: str) -> bool:
        """Delete one playbook if it exists."""
        playbooks = self.load_playbooks()
        if playbook_id not in playbooks:
            return False
        del playbooks[playbook_id]
        self.save_playbooks(playbooks)
        return True

    def get_stats(self) -> dict[str, Any]:
        """Return aggregated storage statistics."""
        rules = self.load_rules()
        playbooks = self.load_playbooks()
        events = self.get_events(limit=1_000_000)

        return {
            "total_rules": len(rules),
            "total_playbooks": len(playbooks),
            "total_policy_events": len(events),
            "rules_file_size": self.rules_file.stat().st_size if self.rules_file.exists() else 0,
            "playbooks_file_size": self.playbooks_file.stat().st_size
            if self.playbooks_file.exists()
            else 0,
            "policy_events_file_size": self.policy_events_file.stat().st_size
            if self.policy_events_file.exists()
            else 0,
        }
