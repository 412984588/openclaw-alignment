#!/usr/bin/env python3
"""Unit tests for canonical policy models and storage manager."""

from __future__ import annotations

import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.policy_models import Playbook, PolicyEvent, Rule
from lib.policy_store import PolicyStore


class TestRule:
    def test_rule_creation(self) -> None:
        rule = Rule(
            id="test_rule",
            summary="Test rule",
            category="optimize",
            strategy="Test strategy",
            confidence=0.8,
        )

        assert rule.id == "test_rule"
        assert rule.type == "Rule"
        assert rule.summary == "Test rule"
        assert rule.category == "optimize"
        assert rule.confidence == 0.8

    def test_rule_calculate_asset_id(self) -> None:
        rule = Rule(
            id="test_rule",
            summary="Test rule",
            category="optimize",
            strategy="Test strategy",
        )

        asset_id = rule.calculate_asset_id()

        assert asset_id.startswith("sha256:")
        assert len(asset_id) == 71

    def test_rule_to_dict(self) -> None:
        rule = Rule(id="test_rule", summary="Test rule", category="optimize", confidence=0.8)
        data = rule.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "test_rule"
        assert data["summary"] == "Test rule"

    def test_rule_from_dict(self) -> None:
        data = {
            "id": "test_rule",
            "type": "Rule",
            "summary": "Test rule",
            "category": "optimize",
            "trigger": [],
            "strategy": "",
            "preconditions": [],
            "postconditions": [],
            "validation": [],
            "confidence": 0.8,
            "success_streak": 0,
            "asset_id": "",
        }

        rule = Rule.from_dict(data)

        assert rule.id == "test_rule"
        assert rule.type == "Rule"
        assert rule.summary == "Test rule"
        assert rule.confidence == 0.8

    def test_rule_from_dict_applies_policy_defaults(self) -> None:
        rule = Rule.from_dict(
            {
                "id": "legacy_rule",
                "summary": "Legacy rule",
                "trigger": ["T2"],
                "confidence": 0.9,
                "success_streak": 6,
            }
        )

        assert rule.status == "hint"
        assert rule.scope == "global"
        assert rule.scope_key == ""
        assert rule.evidence_count == 0
        assert rule.source_type == "legacy"
        assert rule.policy_decision == ""

    def test_rule_increment_confidence(self) -> None:
        rule = Rule(id="test_rule", summary="Test rule", confidence=0.5, success_streak=0)

        rule.increment_confidence(0.8)
        assert rule.success_streak == 1
        assert rule.confidence > 0.5

        previous_confidence = rule.confidence
        rule.increment_confidence(0.2)
        assert rule.success_streak == 0
        assert rule.confidence < previous_confidence


class TestPlaybook:
    def test_playbook_creation(self) -> None:
        playbook = Playbook(
            id="test_playbook",
            summary="Test playbook",
            rules_used=["rule1", "rule2"],
            category="innovate",
        )

        assert playbook.id == "test_playbook"
        assert playbook.type == "Playbook"
        assert len(playbook.rules_used) == 2

    def test_playbook_calculate_asset_id(self) -> None:
        playbook = Playbook(id="test_playbook", summary="Test playbook", rules_used=[])

        asset_id = playbook.calculate_asset_id()

        assert asset_id.startswith("sha256:")
        assert len(asset_id) == 71


class TestPolicyEvent:
    def test_policy_event_creation(self) -> None:
        event = PolicyEvent(
            timestamp="2026-03-01T12:00:00Z",
            event_type="rule_created",
            asset_id="sha256:abc123",
            rl_reward=0.8,
        )

        assert event.type == "PolicyEvent"
        assert event.event_type == "rule_created"
        assert event.rl_reward == 0.8

    def test_policy_event_to_jsonl(self) -> None:
        event = PolicyEvent(
            timestamp="2026-03-01T12:00:00Z",
            event_type="rule_created",
            asset_id="sha256:abc123",
            changes="Created new rule",
        )

        jsonl = event.to_jsonl()

        assert isinstance(jsonl, str)
        assert "rule_created" in jsonl
        assert "Created new rule" in jsonl

    def test_policy_event_from_jsonl(self) -> None:
        jsonl = (
            '{"timestamp":"2026-03-01T12:00:00Z","event_type":"rule_created",'
            '"asset_id":"sha256:abc123","trigger_signals":[],"rl_reward":0.8,'
            '"changes":"Created new rule","source_node_id":"test"}'
        )

        event = PolicyEvent.from_jsonl(jsonl)

        assert event.type == "PolicyEvent"
        assert event.event_type == "rule_created"
        assert event.changes == "Created new rule"
        assert event.rl_reward == 0.8

    def test_policy_event_payload_roundtrip(self) -> None:
        event = PolicyEvent(
            timestamp="2026-03-01T12:00:00Z",
            event_type="decision_evaluated",
            asset_id="sha256:decision",
            payload={
                "decision_id": "dec_123",
                "final_decision": "auto_execute",
            },
        )

        restored = PolicyEvent.from_jsonl(event.to_jsonl())

        assert restored.payload["decision_id"] == "dec_123"
        assert restored.payload["final_decision"] == "auto_execute"


class TestPolicyStore:
    @pytest.fixture
    def temp_dir(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_policy_store_init(self, temp_dir: Path) -> None:
        store = PolicyStore(temp_dir)

        assert store.base_dir == temp_dir
        assert store.rules_file == temp_dir / "rules.json"
        assert store.playbooks_file == temp_dir / "playbooks.json"
        assert store.policy_events_file == temp_dir / "policy_events.jsonl"

    def test_save_and_load_rules(self, temp_dir: Path) -> None:
        store = PolicyStore(temp_dir)
        rule = Rule(id="test_rule", summary="Test rule", category="optimize", confidence=0.8)
        rule.calculate_asset_id()

        store.save_rule(rule)
        loaded_rule = store.get_rule("test_rule")

        assert loaded_rule is not None
        assert loaded_rule.id == "test_rule"
        assert loaded_rule.summary == "Test rule"
        assert loaded_rule.confidence == 0.8

    def test_save_and_load_playbooks(self, temp_dir: Path) -> None:
        store = PolicyStore(temp_dir)
        playbook = Playbook(id="test_playbook", summary="Test playbook", rules_used=["rule1"])
        playbook.calculate_asset_id()

        store.save_playbook(playbook)
        loaded_playbook = store.get_playbook("test_playbook")

        assert loaded_playbook is not None
        assert loaded_playbook.id == "test_playbook"
        assert loaded_playbook.summary == "Test playbook"

    def test_append_and_get_events(self, temp_dir: Path) -> None:
        store = PolicyStore(temp_dir)

        event1 = PolicyEvent(
            timestamp="2026-03-01T12:00:00Z",
            event_type="rule_created",
            asset_id="sha256:abc123",
            changes="Created rule 1",
        )

        event2 = PolicyEvent(
            timestamp="2026-03-01T12:05:00Z",
            event_type="rule_created",
            asset_id="sha256:def456",
            changes="Created rule 2",
        )

        store.append_event(event1)
        store.append_event(event2)

        events = store.get_events(limit=10)

        assert len(events) == 2
        assert events[0].changes == "Created rule 2"
        assert events[1].changes == "Created rule 1"

    def test_delete_rule(self, temp_dir: Path) -> None:
        store = PolicyStore(temp_dir)

        rule = Rule(id="test_rule", summary="Test rule")
        store.save_rule(rule)

        result = store.delete_rule("test_rule")

        assert result is True
        assert store.get_rule("test_rule") is None
