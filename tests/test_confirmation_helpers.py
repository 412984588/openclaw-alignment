#!/usr/bin/env python3
"""Focused tests for extracted confirmation helper modules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lib.explanation import render_explanation
from lib.policy_models import Rule
from lib.policy_resolution import resolve_rules
from lib.risk import RiskAssessor, RiskLevel


def _iso(minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def test_risk_assessor_classifies_low_and_critical_tasks() -> None:
    assessor = RiskAssessor()

    low_risk, low_basis = assessor.assess_details(
        {
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
        }
    )
    critical_risk, critical_basis = assessor.assess_details(
        {
            "task_description": "Clean workspace directory",
            "command": "rm -rf workspace",
            "files": ["workspace/delete-me"],
        }
    )

    assert low_risk == RiskLevel.LOW
    assert low_basis
    assert critical_risk == RiskLevel.CRITICAL
    assert any("rm" in basis.lower() or "delete" in basis.lower() for basis in critical_basis)


def test_resolve_rules_prefers_project_rule_over_global_rule() -> None:
    project_rule = Rule(
        id="project_rule",
        summary="Project pytest rule",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key="/repo",
        source_type="explicit_preference",
        evidence_count=3,
        policy_decision="auto_execute",
        last_seen_at=_iso(0),
    )
    global_rule = Rule(
        id="global_rule",
        summary="Global pytest rule",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="global",
        scope_key="",
        source_type="explicit_preference",
        evidence_count=3,
        policy_decision="require_confirmation",
        last_seen_at=_iso(-5),
    )

    selected, resolution = resolve_rules([project_rule, global_rule])

    assert selected is project_rule
    assert resolution == "project_over_global"


def test_resolve_rules_uses_newest_same_scope_rule_when_conflict_is_older() -> None:
    older_rule = Rule(
        id="older_rule",
        summary="Older project rule",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key="/repo",
        source_type="explicit_preference",
        evidence_count=3,
        policy_decision="require_confirmation",
        last_seen_at=_iso(0),
    )
    newer_conflict = Rule(
        id="newer_conflict",
        summary="Newer conflicting project rule",
        category="harden",
        trigger=["task_type:T2", "command:python -m pytest tests/"],
        status="confirmed",
        scope="project",
        scope_key="/repo",
        source_type="explicit_preference",
        evidence_count=3,
        policy_decision="auto_execute",
        last_seen_at=_iso(1),
    )

    selected, resolution = resolve_rules([older_rule, newer_conflict])

    assert selected is not None
    assert resolution == "same_scope_newer_confirmed"


def test_render_explanation_includes_resolution_and_confidence() -> None:
    explanation = render_explanation(
        {
            "final_decision": "auto_execute",
            "reason": "Confirmed project rule allows auto execution",
            "heuristic_basis": ["LOW risk command context: Python verification command"],
            "matched_rules": [
                {
                    "id": "project_rule",
                    "status": "confirmed",
                    "scope": "project",
                    "policy_decision": "auto_execute",
                }
            ],
            "resolution": "project_over_global",
            "fallback_reason": "",
            "confidence": {
                "max_confidence": 0.95,
                "matched_rule_count": 1,
            },
        }
    )

    assert "auto-execute" in explanation.lower()
    assert "resolution: project_over_global" in explanation.lower()
    assert "confidence:" in explanation.lower()
