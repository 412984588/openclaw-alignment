#!/usr/bin/env python3
"""Regression tests for ConfirmationAPI bootstrap behavior."""

from __future__ import annotations

from pathlib import Path

from lib.api import ConfirmationAPI
from lib.cli import OpenClawAlignmentCLI
from lib.policy_store import PolicyStore


def test_confirmation_api_bootstraps_policy_store_when_missing(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"

    api = ConfirmationAPI(memory_dir=memory_dir)

    assert api.policy_store is not None
    assert not hasattr(api, "gep_store")
    assert (memory_dir / "policy").exists()
    assert (memory_dir / "policy" / "rules.json").exists()
    assert (memory_dir / "policy" / "playbooks.json").exists()
    assert (memory_dir / "policy" / "policy_events.jsonl").exists()


def test_confirmation_api_returns_structured_decision_details(tmp_path: Path) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)

    task = {
        "task_type": "T2",
        "task_description": "Run tests",
        "command": "python -m pytest tests/",
    }

    auto_execute, reason, details = api.should_auto_execute(task)

    assert auto_execute is True
    assert reason
    assert details["decision_id"]
    assert details["decision"]["final_decision"] == "auto_execute"
    assert "heuristic_basis" in details["decision"]
    assert "matched_rules" in details["decision"]
    assert details["relevant_rules_count"] == details["decision"]["confidence"]["matched_rule_count"]


def test_confirmation_api_persists_decision_history_with_outcome(tmp_path: Path) -> None:
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
        auto_executed=True,
        decision_id=details["decision_id"],
        execution_result="success",
    )

    history = api.get_recent_decisions(limit=5)
    assert history["decisions"]
    latest = history["decisions"][0]
    assert latest["decision_id"] == details["decision_id"]
    assert latest["execution_result"] == "success"
    assert latest["final_decision"] == "auto_execute"
    assert latest["explanation"]["final_decision"] == "auto_execute"


def test_confirmation_api_records_explicit_override_as_policy_candidate(tmp_path: Path) -> None:
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
    assert any(rule.status == "candidate" for rule in rules.values())


def test_decision_history_cli_shows_recent_trace(tmp_path: Path, capsys) -> None:
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
        auto_executed=True,
        decision_id=details["decision_id"],
        execution_result="success",
    )

    cli = OpenClawAlignmentCLI()
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        cli.decision_history(limit=5)
    finally:
        os.chdir(original_cwd)

    output = capsys.readouterr().out
    assert details["decision_id"] in output
    assert "auto_execute" in output
    assert "Run tests" in output


def test_status_cli_uses_policy_terminology(tmp_path: Path, capsys) -> None:
    cli = OpenClawAlignmentCLI()

    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        cli.init(force=True)
        cli.status()
    finally:
        os.chdir(original_cwd)

    output = capsys.readouterr().out
    assert "Policy" in output
    assert "Rules" in output
    assert "Playbooks" in output


def test_policy_status_and_suspended_cli_show_recent_lifecycle(tmp_path: Path, capsys) -> None:
    memory_dir = tmp_path / ".openclaw_memory"
    api = ConfirmationAPI(memory_dir=memory_dir)
    store = PolicyStore(memory_dir / "policy")
    project_scope = str(tmp_path.resolve())

    confirmed_rule = store.get_rule("confirmed_cli_rule")
    if confirmed_rule is None:
        from lib.policy_models import Rule

        confirmed_rule = Rule(
            id="confirmed_cli_rule",
            summary="Project pytest runs may auto execute",
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
        confirmed_rule.calculate_asset_id()
        store.save_rule(confirmed_rule)

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

    cli = OpenClawAlignmentCLI()
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        cli.policy_status()
        cli.policy_suspended(limit=5)
    finally:
        os.chdir(original_cwd)

    output = capsys.readouterr().out
    assert "confirmed" in output.lower()
    assert "suspended" in output.lower()
    assert "confirmed_cli_rule" in output
