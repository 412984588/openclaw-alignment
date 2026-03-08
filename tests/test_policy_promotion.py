#!/usr/bin/env python3
"""Focused tests for policy promotion and scope precedence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib.api import ConfirmationAPI
from lib.policy_models import Rule
from lib.policy_store import PolicyStore


def _iso(minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def test_explicit_correction_creates_candidate_rule(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
    }

    _, _, details = api.should_auto_execute(task)
    api.record_execution_result(
        task=task,
        success=True,
        auto_executed=False,
        decision_id=details["decision_id"],
        execution_result="success",
        user_override="confirmed_after_prompt",
    )

    rules = PolicyStore(memory_dir / "policy").load_rules()
    candidate_rules = [rule for rule in rules.values() if rule.status == "candidate"]

    assert candidate_rules
    assert candidate_rules[0].source_type in {"explicit_correction", "explicit_preference"}


def test_candidate_promotes_after_gate_when_evidence_is_strong(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
    }

    for _ in range(3):
        _, _, details = api.should_auto_execute(task)
        api.record_execution_result(
            task=task,
            success=True,
            auto_executed=False,
            decision_id=details["decision_id"],
            execution_result="success",
            user_override="confirmed_after_prompt",
        )

    rules = PolicyStore(memory_dir / "policy").load_rules()
    confirmed_rules = [rule for rule in rules.values() if rule.status == "confirmed"]

    assert confirmed_rules
    assert all(rule.validation for rule in confirmed_rules)


def test_same_scope_newer_confirmed_rule_wins(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    older_rule = Rule(
        id="older_rule",
        summary="Older project rule says confirm",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(-10),
        policy_decision="require_confirmation",
        validation=["assert confirmation for pytest"],
    )
    older_rule.calculate_asset_id()

    newer_rule = Rule(
        id="newer_rule",
        summary="Newer project rule says auto",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(0),
        policy_decision="auto_execute",
        validation=["assert auto execute for pytest"],
    )
    newer_rule.calculate_asset_id()

    store.save_rule(older_rule)
    store.save_rule(newer_rule)

    auto_execute, _, details = api.should_auto_execute(
        {
            "task_type": "T2",
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
            "project_path": project_scope,
        }
    )

    assert auto_execute is True
    assert details["decision"]["resolution"] == "same_scope_newer_confirmed"


def test_high_risk_candidate_does_not_confirm_from_statistics_only(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    candidate = Rule(
        id="dangerous_auto_rule",
        summary="Auto-delete workspace",
        category="harden",
        trigger=["task_type:T3", "command:rm -rf workspace"],
        status="candidate",
        scope="project",
        scope_key=project_scope,
        evidence_count=2,
        source_type="repeated_success",
        last_seen_at=_iso(-5),
        policy_decision="auto_execute",
        validation=["assert auto execute for rm -rf workspace"],
        confidence=0.9,
        success_streak=5,
    )
    candidate.calculate_asset_id()
    store.save_rule(candidate)

    for _ in range(2):
        _, _, details = api.should_auto_execute(
            {
                "task_type": "T3",
                "task_description": "Clean workspace directory",
                "command": "rm -rf workspace",
                "project_path": project_scope,
            }
        )
        api.record_execution_result(
            task={
                "task_type": "T3",
                "task_description": "Clean workspace directory",
                "command": "rm -rf workspace",
                "project_path": project_scope,
            },
            success=True,
            auto_executed=True,
            decision_id=details["decision_id"],
            execution_result="success",
        )

    refreshed = store.get_rule("dangerous_auto_rule")
    assert refreshed is not None
    assert refreshed.status == "candidate"


def test_domain_confirmed_rule_overrides_global_when_project_rule_missing(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    store = PolicyStore(memory_dir / "policy")

    global_rule = Rule(
        id="global_docs_rule",
        summary="Docs changes require confirmation globally",
        category="harden",
        trigger=["task_type:T2", "command:python -m mkdocs build"],
        status="confirmed",
        scope="global",
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(-10),
        policy_decision="require_confirmation",
        validation=["assert confirmation for docs build"],
    )
    global_rule.calculate_asset_id()

    domain_rule = Rule(
        id="domain_docs_rule",
        summary="Docs builds auto execute in docs domain",
        category="harden",
        trigger=["task_type:T2", "command:python -m mkdocs build"],
        status="confirmed",
        scope="domain",
        scope_key="docs",
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(0),
        policy_decision="auto_execute",
        validation=["assert auto execute for docs build"],
    )
    domain_rule.calculate_asset_id()

    store.save_rule(global_rule)
    store.save_rule(domain_rule)

    auto_execute, _, details = api.should_auto_execute(
        {
            "task_type": "T2",
            "task_description": "Build docs site",
            "command": "python -m mkdocs build",
            "files": ["docs/index.md"],
        }
    )

    assert auto_execute is True
    assert details["decision"]["resolution"] == "domain_over_global"
    assert details["decision"]["scope"] == "domain"
    assert details["decision"]["scope_key"] == "docs"


def test_confirmed_rule_suspends_after_repeated_auto_execute_failures(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    confirmed = Rule(
        id="confirmed_pytest_rule",
        summary="Project pytest runs may auto execute",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(-5),
        policy_decision="auto_execute",
        validation=["assert auto execute for pytest"],
        confidence=0.9,
    )
    confirmed.calculate_asset_id()
    store.save_rule(confirmed)

    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
        "project_path": project_scope,
    }

    for _ in range(2):
        _, _, details = api.should_auto_execute(task)
        api.record_execution_result(
            task=task,
            success=False,
            auto_executed=True,
            decision_id=details["decision_id"],
            execution_result="failure",
        )

    refreshed = store.get_rule("confirmed_pytest_rule")
    lifecycle_events = store.get_events_by_type({"rule_suspended"}, limit=10)

    assert refreshed is not None
    assert refreshed.status == "suspended"
    assert lifecycle_events
    assert lifecycle_events[0].payload["rule_id"] == "confirmed_pytest_rule"


def test_suspended_rule_reactivates_to_candidate_after_explicit_reapproval(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    suspended = Rule(
        id="suspended_pytest_rule",
        summary="Project pytest runs were suspended",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="suspended",
        scope="project",
        scope_key=project_scope,
        evidence_count=5,
        source_type="explicit_preference",
        last_seen_at=_iso(-5),
        policy_decision="auto_execute",
        validation=["assert auto execute for pytest"],
        confidence=0.4,
    )
    suspended.calculate_asset_id()
    store.save_rule(suspended)

    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
        "project_path": project_scope,
    }

    for _ in range(2):
        _, _, details = api.should_auto_execute(task)
        api.record_execution_result(
            task=task,
            success=True,
            auto_executed=False,
            decision_id=details["decision_id"],
            execution_result="success",
            user_override="confirmed_after_prompt",
        )

    refreshed = store.get_rule("suspended_pytest_rule")
    lifecycle_events = store.get_events_by_type({"rule_reactivated"}, limit=10)

    assert refreshed is not None
    assert refreshed.status == "candidate"
    assert lifecycle_events
    assert lifecycle_events[0].payload["rule_id"] == "suspended_pytest_rule"


def test_rollback_immediately_suspends_confirmed_auto_rule(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    confirmed = Rule(
        id="rollback_sensitive_rule",
        summary="Project deploy preview may auto execute",
        category="harden",
        trigger=["task_type:T2", "command:deploy preview"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(-5),
        policy_decision="auto_execute",
        validation=["assert auto execute for deploy preview"],
        confidence=0.9,
    )
    confirmed.calculate_asset_id()
    store.save_rule(confirmed)

    task = {
        "task_type": "T2",
        "task_description": "Deploy preview",
        "command": "deploy preview",
        "project_path": project_scope,
    }

    _, _, details = api.should_auto_execute(task)
    api.record_execution_result(
        task=task,
        success=False,
        auto_executed=True,
        decision_id=details["decision_id"],
        execution_result="rollback",
    )

    refreshed = store.get_rule("rollback_sensitive_rule")
    lifecycle_events = store.get_events_by_type({"rule_suspended"}, limit=10)

    assert refreshed is not None
    assert refreshed.status == "suspended"
    assert lifecycle_events[0].payload["trigger"] == "rollback"


def test_ambiguous_same_scope_conflict_requires_confirmation(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    first = Rule(
        id="conflict_rule_one",
        summary="Require confirmation for pytest",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at="2026-03-07T12:00:00+00:00",
        policy_decision="require_confirmation",
        validation=["assert confirmation for pytest"],
    )
    first.calculate_asset_id()

    second = Rule(
        id="conflict_rule_two",
        summary="Auto execute pytest",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at="2026-03-07T12:00:00+00:00",
        policy_decision="auto_execute",
        validation=["assert auto execute for pytest"],
    )
    second.calculate_asset_id()

    store.save_rule(first)
    store.save_rule(second)

    auto_execute, reason, details = api.should_auto_execute(
        {
            "task_type": "T2",
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
            "project_path": project_scope,
        }
    )

    assert auto_execute is False
    assert "confirmation" in reason.lower()
    assert details["decision"]["resolution"] == "ambiguous_same_scope_conflict"


def test_suspended_rule_archives_when_superseded_by_new_confirmed_rule(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    project_scope = str(tmp_path.resolve())
    store = PolicyStore(memory_dir / "policy")

    suspended = Rule(
        id="superseded_suspended_rule",
        summary="Old suspended pytest policy",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="suspended",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(-10),
        policy_decision="require_confirmation",
        validation=["assert confirmation for pytest"],
    )
    suspended.calculate_asset_id()

    confirmed = Rule(
        id="confirmed_replacement_rule",
        summary="New confirmed pytest policy",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key=project_scope,
        evidence_count=4,
        source_type="explicit_preference",
        last_seen_at=_iso(0),
        policy_decision="auto_execute",
        validation=["assert auto execute for pytest"],
    )
    confirmed.calculate_asset_id()

    store.save_rule(suspended)
    store.save_rule(confirmed)

    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
        "project_path": project_scope,
    }

    _, _, details = api.should_auto_execute(task)
    api.record_execution_result(
        task=task,
        success=True,
        auto_executed=True,
        decision_id=details["decision_id"],
        execution_result="success",
    )

    archived = store.get_rule("superseded_suspended_rule")
    lifecycle_events = store.get_events_by_type({"rule_archived"}, limit=10)

    assert archived is not None
    assert archived.status == "archived"
    assert lifecycle_events
    assert lifecycle_events[0].payload["rule_id"] == "superseded_suspended_rule"
