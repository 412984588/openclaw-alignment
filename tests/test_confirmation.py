#!/usr/bin/env python3
"""Tests for the intelligent confirmation system."""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from shutil import rmtree

import pytest

from lib.confirmation import IntelligentConfirmation, RiskLevel
from lib.policy_models import Rule
from lib.policy_store import PolicyStore


class TestIntelligentConfirmation:
    """Test intelligent confirmation decision logic."""

    @pytest.fixture
    def temp_policy_store(self):
        """Temporary policy store fixture."""
        temp_dir = Path(tempfile.mkdtemp())
        policy_store = PolicyStore(temp_dir)
        project_scope = str((temp_dir / "repo").resolve())

        now = datetime.now(timezone.utc)

        rule_high_conf = Rule(
            id="rule_test_high_conf",
            summary="Allow pytest tasks in this project",
            category="harden",
            confidence=0.95,
            success_streak=10,
            trigger=["task_type:T2", "command:python -m pytest tests/"],
            status="confirmed",
            scope="project",
            scope_key=project_scope,
            evidence_count=4,
            source_type="explicit_preference",
            last_seen_at=now.isoformat(),
            policy_decision="auto_execute",
            validation=["assert auto_execute for python -m pytest tests/"],
        )
        rule_high_conf.calculate_asset_id()

        rule_low_conf = Rule(
            id="rule_test_low_conf",
            summary="Legacy low-confidence profile",
            category="repair",
            confidence=0.4,
            success_streak=1,
            trigger=["T1", "test"],
        )
        rule_low_conf.calculate_asset_id()

        global_guard = Rule(
            id="rule_global_pytest_guard",
            summary="Require confirmation for pytest globally",
            category="harden",
            trigger=["task_type:T2", "command:python -m pytest tests/"],
            status="confirmed",
            scope="global",
            evidence_count=4,
            source_type="explicit_preference",
            last_seen_at=(now - timedelta(days=1)).isoformat(),
            policy_decision="require_confirmation",
            validation=["assert confirmation for python -m pytest tests/"],
        )
        global_guard.calculate_asset_id()

        destructive_hint = Rule(
            id="rule_git_history_delete_hint",
            summary="Git history suggests deleting temp files is often okay",
            category="optimize",
            trigger=["task_type:T3", "command:rm -rf workspace"],
            status="hint",
            scope="project",
            scope_key=project_scope,
            evidence_count=2,
            source_type="git_history",
            last_seen_at=now.isoformat(),
            policy_decision="auto_execute",
        )
        destructive_hint.calculate_asset_id()

        policy_store.save_rule(rule_high_conf)
        policy_store.save_rule(rule_low_conf)
        policy_store.save_rule(global_guard)
        policy_store.save_rule(destructive_hint)

        yield policy_store, project_scope

        if temp_dir.exists():
            rmtree(temp_dir)

    def test_assess_risk_low(self, temp_policy_store):
        policy_store, _ = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T1",
            "task_description": "Run format and lint checks",
            "command": "npm run format",
        }

        risk = conf_engine.assess_risk(task_context)
        assert risk == RiskLevel.LOW

    def test_assess_risk_high(self, temp_policy_store):
        policy_store, _ = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T3",
            "task_description": "Clean workspace directory",
            "command": "rm -rf workspace",
        }

        risk = conf_engine.assess_risk(task_context)
        assert risk == RiskLevel.CRITICAL

    def test_should_confirm_auto_execute_high_confidence(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
            "command": "python -m py_optimize",
            "project_path": project_scope,
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is True
        assert "insufficient" in reason.lower() or "confirmation" in reason.lower()

    def test_should_confirm_high_risk(self, temp_policy_store):
        policy_store, _ = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Delete test files",
            "command": "rm -rf tests/",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is True
        assert "risk" in reason.lower() or "critical" in reason.lower()

    def test_should_confirm_low_confidence(self, temp_policy_store):
        policy_store, _ = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T1",
            "task_description": "Update API schema",
            "command": "apply database schema update",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is True
        assert "insufficient" in reason.lower() or "first-time" in reason.lower() or "no confirmed rule" in reason.lower()

    def test_get_confidence_info(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
            "project_path": project_scope,
        }

        confidence_info = conf_engine.get_confidence_info(task_context)

        assert confidence_info["max_confidence"] >= 0.9
        assert confidence_info["count"] > 0

    def test_record_feedback_user_cancelled(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
            "project_path": project_scope,
        }

        decision = conf_engine.evaluate_task(task_context)
        conf_engine.record_feedback(
            task_context,
            was_confirmed=True,
            user_cancelled=True,
            decision_id=decision["decision_id"],
            execution_result="cancel",
            user_override="prefer_confirmation",
        )

        rules = policy_store.load_rules()
        rule = rules.get("rule_test_high_conf")

        assert rule is not None
        assert rule.last_seen_at

    def test_record_feedback_auto_executed(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
            "project_path": project_scope,
        }

        original_confidence = policy_store.get_rule("rule_test_high_conf").confidence
        decision = conf_engine.evaluate_task(task_context)

        conf_engine.record_feedback(
            task_context,
            was_confirmed=False,
            user_cancelled=False,
            decision_id=decision["decision_id"],
            execution_result="success",
        )

        rules = policy_store.load_rules()
        rule = rules.get("rule_test_high_conf")

        assert rule is not None
        assert rule.confidence >= original_confidence
        assert rule.last_applied_at

    def test_get_explanation_auto_execute(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Run tests",
            "command": "python -m pytest tests/",
            "project_path": project_scope,
        }

        decision = conf_engine.evaluate_task(task_context)
        should_confirm = decision["final_decision"] == "require_confirmation"
        reason = decision["reason"]
        explanation = conf_engine.get_explanation(task_context, should_confirm, reason)

        assert "auto-execute" in explanation.lower()
        assert "project" in explanation.lower()
        assert "global" in explanation.lower()

    def test_get_explanation_need_confirm(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        task_context = {
            "task_type": "T3",
            "task_description": "Clean workspace directory",
            "command": "rm -rf workspace",
            "project_path": project_scope,
        }

        decision = conf_engine.evaluate_task(task_context)
        should_confirm = decision["final_decision"] == "require_confirmation"
        reason = decision["reason"]
        explanation = conf_engine.get_explanation(task_context, should_confirm, reason)

        assert "confirmation required" in explanation.lower()
        assert "git history" in explanation.lower() or "heuristic" in explanation.lower()

    def test_project_confirmed_rule_overrides_global_rule(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        decision = conf_engine.evaluate_task(
            {
                "task_type": "T2",
                "task_description": "Run tests",
                "command": "python -m pytest tests/",
                "project_path": project_scope,
            }
        )

        assert decision["final_decision"] == "auto_execute"
        assert decision["resolution"] == "project_over_global"
        assert len(decision["matched_rules"]) >= 2

    def test_first_time_low_risk_task_uses_heuristic_fallback(self):
        conf_engine = IntelligentConfirmation()
        decision = conf_engine.evaluate_task(
            {
                "task_type": "T1",
                "task_description": "Show test summary",
                "command": "pytest --collect-only -q",
            }
        )

        assert decision["final_decision"] == "auto_execute"
        assert "first-time" in decision["fallback_reason"]
        assert decision["heuristic_basis"]

    def test_high_risk_weak_hint_cannot_auto_execute(self, temp_policy_store):
        policy_store, project_scope = temp_policy_store
        conf_engine = IntelligentConfirmation(policy_store)
        decision = conf_engine.evaluate_task(
            {
                "task_type": "T3",
                "task_description": "Clean workspace directory",
                "command": "rm -rf workspace",
                "project_path": project_scope,
            }
        )

        assert decision["final_decision"] == "require_confirmation"
        assert any(rule["status"] == "hint" for rule in decision["matched_rules"])
        assert any("rm" in basis.lower() for basis in decision["heuristic_basis"])


class TestRiskAssessment:
    """Test risk assessment logic."""

    @pytest.fixture
    def conf_engine(self):
        return IntelligentConfirmation()

    def test_detect_critical_keywords(self, conf_engine):
        dangerous_tasks = [
            {"task_description": "Remove directory", "command": "rm -rf /data"},
            {"task_description": "Format disk", "command": "mkfs.ext4 /dev/sda1"},
            {"task_description": "Force push git", "command": "git push --force"},
        ]

        for task in dangerous_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.CRITICAL

    def test_detect_medium_keywords(self, conf_engine):
        medium_tasks = [
            {"task_description": "Update database schema"},
            {"task_description": "Make API request"},
            {"task_description": "Install dependencies"},
        ]

        for task in medium_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.MEDIUM

    def test_detect_low_keywords(self, conf_engine):
        low_tasks = [
            {"task_description": "Run tests"},
            {"task_description": "Check code format"},
            {"task_description": "List files"},
        ]

        for task in low_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.LOW
