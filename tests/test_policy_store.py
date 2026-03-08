#!/usr/bin/env python3
"""Canonical policy model and store tests."""

from __future__ import annotations

from pathlib import Path

from lib.policy_models import Playbook, PolicyEvent, Rule
from lib.policy_store import PolicyStore


def test_policy_models_use_canonical_type_names() -> None:
    rule = Rule(id="rule_test", summary="Run tests safely")
    playbook = Playbook(id="playbook_test", summary="Safe test playbook")
    event = PolicyEvent(
        timestamp="2026-03-01T12:00:00Z",
        event_type="decision_evaluated",
        asset_id="sha256:test",
    )

    assert rule.type == "Rule"
    assert playbook.type == "Playbook"
    assert event.type == "PolicyEvent"


def test_policy_store_uses_canonical_files(tmp_path: Path) -> None:
    store = PolicyStore(tmp_path)

    assert store.rules_file == tmp_path / "rules.json"
    assert store.playbooks_file == tmp_path / "playbooks.json"
    assert store.policy_events_file == tmp_path / "policy_events.jsonl"


def test_policy_store_bootstrap_provisions_canonical_files(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"

    store = PolicyStore.bootstrap(memory_dir, ensure_files=True)

    assert store.base_dir == memory_dir / "policy"
    assert store.rules_file.exists()
    assert store.playbooks_file.exists()
    assert store.policy_events_file.exists()


def test_policy_store_round_trips_rules_playbooks_and_events(tmp_path: Path) -> None:
    store = PolicyStore(tmp_path)
    rule = Rule(id="rule_test", summary="Run tests safely", confidence=0.8)
    playbook = Playbook(id="playbook_test", summary="Safe test playbook", rules_used=["rule_test"])
    event = PolicyEvent(
        timestamp="2026-03-01T12:00:00Z",
        event_type="decision_evaluated",
        asset_id="sha256:test",
        payload={"decision_id": "dec_123"},
    )

    store.save_rule(rule)
    store.save_playbook(playbook)
    store.append_event(event)

    assert store.get_rule("rule_test") is not None
    assert store.get_playbook("playbook_test") is not None
    assert store.get_policy_events(limit=5)[0].payload["decision_id"] == "dec_123"


def test_rule_from_dict_supports_suspended_and_domain_scope() -> None:
    rule = Rule.from_dict(
        {
            "id": "rule_test",
            "summary": "Use doc rules for docs tasks",
            "status": "suspended",
            "scope": "domain",
            "scope_key": "docs",
            "policy_decision": "require_confirmation",
        }
    )

    assert rule.status == "suspended"
    assert rule.scope == "domain"
    assert rule.scope_key == "docs"
