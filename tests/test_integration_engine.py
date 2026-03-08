#!/usr/bin/env python3
"""
IntentAlignmentEngineBehavioral testing
"""

import json

from lib.integration import IntentAlignmentEngine
from lib.learner import PreferenceLearner
from lib.policy_models import PolicyEvent
from lib.policy_store import PolicyStore


def test_update_preferences_preserves_config_wrapper(tmp_path):
    config_path = tmp_path / "cfg" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "learned_preferences": {"existing": 1},
                "last_updated": "2026-03-01",
            }
        ),
        encoding="utf-8",
    )

    engine = IntentAlignmentEngine(repo_path=".", config_path=str(config_path))
    engine.update_preferences({"new_key": 2})

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    assert updated["version"] == "1.0.0"
    assert updated["learned_preferences"]["existing"] == 1
    assert updated["learned_preferences"]["new_key"] == 2


def test_update_preferences_creates_config_parent_dir(tmp_path):
    config_path = tmp_path / "nested" / "config" / "config.json"
    engine = IntentAlignmentEngine(repo_path=".", config_path=str(config_path))
    engine.update_preferences({"first": "value"})

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    assert updated["learned_preferences"]["first"] == "value"


def test_preference_learner_builds_git_history_hints_only(tmp_path):
    learner = PreferenceLearner(config_path=tmp_path / "config.json")
    learner.learn_from_git_history(
        {
            "tech_stack": {"python": 12, "typescript": 4},
            "workflow": {"test_first": True, "test_ratio": 0.45},
            "metadata": {"collected_at": "2026-03-07T12:00:00Z", "confidence": 0.7},
        }
    )

    hints = learner.build_hint_rules(scope_key="repo:/tmp/demo")

    assert hints
    assert all(rule.status == "hint" for rule in hints)
    assert all(rule.source_type == "git_history" for rule in hints)
    assert all(rule.policy_decision != "require_confirmation" for rule in hints)


def test_preference_learner_report_frames_results_as_weak_hints(tmp_path):
    learner = PreferenceLearner(config_path=tmp_path / "config.json")
    learner.learn_from_git_history(
        {
            "tech_stack": {"python": 12, "typescript": 4},
            "workflow": {"test_first": True, "test_ratio": 0.45},
            "metadata": {"collected_at": "2026-03-07T12:00:00Z", "confidence": 0.7},
        }
    )

    report = learner.generate_report().lower()

    assert "weak hint" in report
    assert "observed" in report
    assert "learned your workflow" not in report


def test_preference_learner_summarizes_strong_runtime_signals(tmp_path):
    store = PolicyStore(tmp_path / "policy")
    store.append_event(
        PolicyEvent(
            timestamp="2026-03-07T12:00:00Z",
            event_type="decision_outcome",
            asset_id="",
            payload={
                "task_type": "T2",
                "execution_result": "success",
                "user_override": "confirmed_after_prompt",
                "rule_ids": ["rule_one"],
            },
        )
    )
    store.append_event(
        PolicyEvent(
            timestamp="2026-03-07T12:10:00Z",
            event_type="decision_outcome",
            asset_id="",
            payload={
                "task_type": "T2",
                "execution_result": "rollback",
                "user_override": "",
                "rule_ids": ["rule_two"],
            },
        )
    )

    learner = PreferenceLearner(config_path=tmp_path / "config.json")
    signals = learner.collect_runtime_policy_signals(store)

    assert signals["strong_signals"]["explicit_user_corrections"] == 1
    assert signals["strong_signals"]["rollback_failures"] == 1
