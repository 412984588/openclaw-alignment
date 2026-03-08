#!/usr/bin/env python3
"""Confirmation policy engine with structured explanations and feedback loops."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, TypedDict
from uuid import uuid4

from .demotion import DemotionGate
from .explanation import render_explanation
from .policy_models import PolicyEvent, Rule
from .policy_store import PolicyStore
from .policy_resolution import (
    PolicyResolver,
    infer_domain,
    normalize_text,
    safe_files,
    safe_text,
    task_summary,
)
from .promotion import PromotionGate
from .risk import RiskAssessor, RiskLevel


class MatchedRuleInfo(TypedDict):
    """Serialized matched rule metadata."""

    id: str
    summary: str
    status: str
    scope: str
    scope_key: str
    source_type: str
    evidence_count: int
    policy_decision: str
    confidence: float
    success_streak: int
    last_seen_at: str


class ConfidenceInfo(TypedDict):
    """Confidence summary for rules related to one task."""

    max_confidence: float
    avg_confidence: float
    min_success_streak: int
    count: int
    rules: list[Rule]
    status_counts: dict[str, int]


class DecisionExplanation(TypedDict):
    """Structured explanation for a confirmation decision."""

    heuristic_basis: list[str]
    matched_rules: list[MatchedRuleInfo]
    resolution: str
    final_decision: str
    confidence: dict[str, Any]
    fallback_reason: str


class DecisionRecord(TypedDict):
    """Structured decision record used by API and audit logging."""

    decision_id: str
    task_summary: str
    task_description: str
    task_type: str
    command: str
    files: list[str]
    risk_level: str
    heuristic_basis: list[str]
    matched_rules: list[MatchedRuleInfo]
    final_decision: str
    reason: str
    resolution: str
    confidence: dict[str, Any]
    fallback_reason: str
    explanation: DecisionExplanation
    explanation_text: str
    timestamp: str
    domain: str
    scope: str
    scope_key: str


class IntelligentConfirmation:
    """Risk-aware confirmation policy with explicit explanation and audit hooks."""

    def __init__(
        self,
        policy_store: PolicyStore | None = None,
        project_scope_key: str = "",
    ) -> None:
        self.policy_store = policy_store
        self.project_scope_key = project_scope_key
        self.promotion_gate = PromotionGate(policy_store) if policy_store else None
        self.demotion_gate = DemotionGate()
        self.risk_assessor = RiskAssessor()
        self.policy_resolver = PolicyResolver(project_scope_key)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def should_confirm(self, task_context: Mapping[str, Any]) -> tuple[bool, str]:
        """Return `(needs_confirmation, reason)` for a task."""
        decision = self.evaluate_task(task_context, persist=False)
        return decision["final_decision"] == "require_confirmation", decision["reason"]

    def evaluate_task(self, task_context: Mapping[str, Any], persist: bool = False) -> DecisionRecord:
        """Build a structured confirmation decision for one task."""
        risk_level, heuristic_basis = self.assess_risk_details(task_context)
        scope, scope_key = self._infer_scope(task_context)
        domain = infer_domain(task_context)
        matched_rules = self._get_matched_rules(task_context, scope_key)
        confirmed_rules = [rule for rule in matched_rules if rule.status == "confirmed" and rule.policy_decision]
        selected_rule, resolution = self._resolve_rules(confirmed_rules)
        fallback_reason = ""

        if risk_level == RiskLevel.CRITICAL:
            final_decision = "require_confirmation"
            reason = "Critical risk heuristic requires confirmation"
            if matched_rules:
                fallback_reason = "heuristic override"
            resolution = resolution if resolution != "heuristic_default" else "critical_risk_override"
        elif selected_rule:
            final_decision = selected_rule.policy_decision
            if final_decision == "auto_execute":
                reason = f"Confirmed {selected_rule.scope} rule allows auto execution"
            else:
                reason = f"Confirmed {selected_rule.scope} rule requires confirmation"
        elif confirmed_rules:
            final_decision = "require_confirmation"
            fallback_reason = "ambiguous confirmed conflict"
            reason = "Conflicting confirmed rules require confirmation"
        else:
            if risk_level == RiskLevel.LOW:
                final_decision = "auto_execute"
                fallback_reason = "first-time task; heuristic fallback"
                reason = "Low-risk heuristic fallback allows auto execution"
            else:
                final_decision = "require_confirmation"
                if any(rule.status == "suspended" for rule in matched_rules):
                    fallback_reason = "suspended rule requires confirmation"
                else:
                    fallback_reason = "insufficient confidence" if matched_rules else "first-time task"
                reason = "No confirmed rule; confirmation required"

        confidence_info = self.get_confidence_info(task_context)
        serialized_rules = [self._serialize_rule(rule) for rule in matched_rules if rule.policy_decision]
        decision_scope = selected_rule.scope if selected_rule else scope
        decision_scope_key = selected_rule.scope_key if selected_rule else scope_key
        decision: DecisionRecord = {
            "decision_id": f"dec_{uuid4().hex[:12]}",
            "task_summary": self._task_summary(task_context),
            "task_description": safe_text(task_context, "task_description"),
            "task_type": safe_text(task_context, "task_type") or "T2",
            "command": safe_text(task_context, "command"),
            "files": safe_files(task_context),
            "risk_level": risk_level.value,
            "heuristic_basis": heuristic_basis,
            "matched_rules": serialized_rules,
            "final_decision": final_decision,
            "reason": reason,
            "resolution": resolution,
            "confidence": {
                "max_confidence": confidence_info["max_confidence"],
                "avg_confidence": confidence_info["avg_confidence"],
                "matched_rule_count": confidence_info["count"],
                "status_counts": confidence_info["status_counts"],
            },
            "fallback_reason": fallback_reason,
            "explanation": {
                "heuristic_basis": heuristic_basis,
                "matched_rules": serialized_rules,
                "resolution": resolution,
                "final_decision": final_decision,
                "confidence": {
                    "max_confidence": confidence_info["max_confidence"],
                    "avg_confidence": confidence_info["avg_confidence"],
                    "matched_rule_count": confidence_info["count"],
                    "status_counts": confidence_info["status_counts"],
                },
                "fallback_reason": fallback_reason,
            },
            "explanation_text": "",
            "timestamp": self._now(),
            "domain": domain,
            "scope": decision_scope,
            "scope_key": decision_scope_key,
        }
        decision["explanation_text"] = self.render_explanation(decision)

        if persist and self.policy_store:
            self._mark_rules_applied(matched_rules, decision["timestamp"])
            self._append_decision_event(decision)

        return decision

    def assess_risk(self, task_context: Mapping[str, Any]) -> RiskLevel:
        """Assess task risk from command, description and file paths."""
        return self.risk_assessor.assess(task_context)

    def assess_risk_details(self, task_context: Mapping[str, Any]) -> tuple[RiskLevel, list[str]]:
        """Assess risk and return basis used for the decision."""
        return self.risk_assessor.assess_details(task_context)

    def get_confidence_info(self, task_context: Mapping[str, Any]) -> ConfidenceInfo:
        """Return confidence metrics for rules matching the task."""
        empty_info: ConfidenceInfo = {
            "max_confidence": 0.0,
            "avg_confidence": 0.0,
            "min_success_streak": 0,
            "count": 0,
            "rules": [],
            "status_counts": {},
        }
        if not self.policy_store:
            return empty_info

        scope_key = self._infer_scope(task_context)[1]
        rules = [rule for rule in self.policy_store.load_rules().values() if self._matches_rule(rule, task_context, scope_key)]
        if not rules:
            return empty_info

        confidences = [rule.confidence for rule in rules]
        status_counts: dict[str, int] = {}
        for rule in rules:
            status_counts[rule.status] = status_counts.get(rule.status, 0) + 1

        return {
            "max_confidence": max(confidences),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_success_streak": min(rule.success_streak for rule in rules),
            "count": len(rules),
            "rules": rules,
            "status_counts": status_counts,
        }

    def record_feedback(
        self,
        task_context: Mapping[str, Any],
        was_confirmed: bool,
        user_cancelled: bool,
        decision_id: str | None = None,
        execution_result: str | None = None,
        user_override: str | None = None,
    ) -> None:
        """Update matching rules and audit events from task execution feedback."""
        if not self.policy_store:
            return

        decision = self._find_decision(decision_id)
        if decision is None:
            decision = self.evaluate_task(task_context, persist=True)

        outcome = execution_result or ("cancel" if user_cancelled else "success")
        matched_rule_ids = [rule["id"] for rule in decision["matched_rules"]]
        rollback_happened = outcome == "rollback"
        lifecycle_transitions: list[str] = []

        rules = self.policy_store.load_rules()
        evidence_type = self._classify_evidence_source(user_override, decision["final_decision"], outcome)
        desired_policy = self._desired_policy_decision(user_override, decision["final_decision"], outcome)

        target_rules = [
            rules[rule_id]
            for rule_id in matched_rule_ids
            if rule_id in rules and rules[rule_id].policy_decision == desired_policy
        ]
        if evidence_type in {"repeated_failure"} or user_override in {
            "prefer_confirmation",
            "blocked_auto_execute",
            "should_have_required_confirmation",
        }:
            target_rules = [rules[rule_id] for rule_id in matched_rule_ids if rule_id in rules]

        if evidence_type in {
            "explicit_correction",
            "explicit_preference",
            "repeated_failure",
            "missed_confirmation",
        } and not target_rules:
            new_rule = self._create_candidate_rule(task_context, desired_policy, evidence_type)
            new_rule.risk_level = decision["risk_level"]
            rules[new_rule.id] = new_rule
            target_rules = [new_rule]

        updated = False
        for rule in target_rules:
            previous_status = rule.status
            if not self._apply_feedback_to_rule(rule, outcome, evidence_type, user_override, decision["risk_level"]):
                continue

            has_conflict = self._has_unresolved_conflict(rule, rules)
            transition = None
            if previous_status == "confirmed":
                suspend_trigger = self._suspension_trigger(user_override, decision["final_decision"], outcome)
                transition = self.demotion_gate.maybe_suspend(
                    rule,
                    trigger=suspend_trigger,
                    has_conflict=has_conflict,
                )
            elif previous_status == "suspended":
                transition = self.demotion_gate.maybe_reactivate(rule)

            if transition is None and rule.status == "candidate" and self.promotion_gate:
                promotion = self.promotion_gate.maybe_promote(rule, decision["risk_level"], has_conflict)
                if promotion.promoted:
                    transition = self._make_transition("rule_promoted", "candidate_promoted")

            if transition is None and rule.status == "suspended":
                transition = self.demotion_gate.maybe_archive(
                    rule,
                    superseded=self._is_superseded(rule, rules),
                )

            rule.last_lifecycle_event_at = self._now() if transition else rule.last_lifecycle_event_at
            rule.calculate_asset_id()
            self._append_rule_event(rule, decision, evidence_type, transition)
            if transition is not None:
                lifecycle_transitions.append(self._transition_event_type(transition))
            updated = True

        if updated:
            self._archive_superseded_suspended_rules(rules, decision)
        self.policy_store.save_rules(rules)
        self.policy_store.append_event(
            PolicyEvent(
                timestamp=self._now(),
                event_type="decision_outcome",
                asset_id="",
                trigger_signals=[decision["task_type"]],
                changes=f"Decision outcome: {outcome}",
                source_node_id="confirmation_policy",
                payload={
                    "decision_id": decision["decision_id"],
                    "final_decision": decision["final_decision"],
                    "user_override": user_override or "",
                    "execution_result": outcome,
                    "was_confirmed": was_confirmed,
                    "rule_ids": matched_rule_ids,
                    "task_summary": decision["task_summary"],
                    "task_type": decision["task_type"],
                    "command": decision["command"],
                    "files": decision["files"],
                    "risk_level": decision["risk_level"],
                    "scope": decision["scope"],
                    "scope_key": decision["scope_key"],
                    "heuristic_basis": decision["heuristic_basis"],
                    "matched_rule_ids": matched_rule_ids,
                    "explanation": decision["explanation"],
                    "rollback_happened": rollback_happened,
                    "lifecycle_transition": ",".join(lifecycle_transitions),
                },
            )
        )

    def get_explanation(self, task_context: Mapping[str, Any], should_confirm: bool, reason: str) -> str:
        """Return a human-readable explanation for the decision."""
        _ = should_confirm, reason
        decision = self.evaluate_task(task_context, persist=False)
        return self.render_explanation(decision)

    def render_explanation(self, decision: DecisionRecord) -> str:
        """Render a structured decision as concise audit text."""
        return render_explanation(decision)

    def _task_summary(self, task_context: Mapping[str, Any]) -> str:
        return task_summary(task_context)

    def _infer_scope(self, task_context: Mapping[str, Any]) -> tuple[str, str]:
        return self.policy_resolver.infer_scope(task_context)

    def _get_matched_rules(self, task_context: Mapping[str, Any], scope_key: str) -> list[Rule]:
        if not self.policy_store:
            return []
        rules = self.policy_store.load_rules().values()
        return self.policy_resolver.get_matched_rules(rules, task_context, scope_key)

    def _matches_rule(self, rule: Rule, task_context: Mapping[str, Any], scope_key: str) -> bool:
        return self.policy_resolver.matches_rule(rule, task_context, scope_key)

    def _resolve_rules(self, rules: list[Rule]) -> tuple[Rule | None, str]:
        return self.policy_resolver.resolve_rules(rules)

    def _serialize_rule(self, rule: Rule) -> MatchedRuleInfo:
        return {
            "id": rule.id,
            "summary": rule.summary,
            "status": rule.status,
            "scope": rule.scope,
            "scope_key": rule.scope_key,
            "source_type": rule.source_type,
            "evidence_count": rule.evidence_count,
            "policy_decision": rule.policy_decision,
            "confidence": rule.confidence,
            "success_streak": rule.success_streak,
            "last_seen_at": rule.last_seen_at,
        }

    def _mark_rules_applied(self, matched_rules: list[Rule], timestamp: str) -> None:
        if not self.policy_store or not matched_rules:
            return
        rules = self.policy_store.load_rules()
        updated = False
        for rule in matched_rules:
            if rule.id not in rules:
                continue
            rules[rule.id].last_applied_at = timestamp
            rules[rule.id].last_seen_at = timestamp or rules[rule.id].last_seen_at
            updated = True
        if updated:
            self.policy_store.save_rules(rules)

    def _append_decision_event(self, decision: DecisionRecord) -> None:
        if not self.policy_store:
            return
        self.policy_store.append_event(
            PolicyEvent(
                timestamp=decision["timestamp"],
                event_type="decision_evaluated",
                asset_id="",
                trigger_signals=[decision["task_type"]],
                changes=decision["reason"],
                source_node_id="confirmation_policy",
                payload=dict(decision),
            )
        )

    def _find_decision(self, decision_id: str | None) -> DecisionRecord | None:
        if not self.policy_store or not decision_id:
            return None
        for event in self.policy_store.get_decision_events(limit=1_000):
            if event.event_type != "decision_evaluated":
                continue
            if event.payload.get("decision_id") == decision_id:
                return event.payload  # type: ignore[return-value]
        return None

    def _classify_evidence_source(
        self,
        user_override: str | None,
        final_decision: str,
        execution_result: str,
    ) -> str:
        if user_override in {"prefer_auto_execute", "prefer_confirmation"}:
            return "explicit_preference"
        if user_override in {"confirmed_after_prompt", "blocked_auto_execute", "forced_auto_execute"}:
            return "explicit_correction"
        if user_override == "should_have_required_confirmation":
            return "missed_confirmation"
        if execution_result in {"failure", "rollback"} and final_decision == "auto_execute":
            return "repeated_failure"
        if execution_result == "success" and final_decision == "auto_execute":
            return "repeated_success"
        return ""

    def _suspension_trigger(
        self,
        user_override: str | None,
        final_decision: str,
        execution_result: str,
    ) -> str:
        if execution_result == "rollback":
            return "rollback"
        if user_override in {"prefer_confirmation", "blocked_auto_execute"}:
            return "override"
        if execution_result in {"failure"} and final_decision == "auto_execute":
            return "failure"
        if user_override == "should_have_required_confirmation":
            return "missed_confirmation"
        return ""

    def _desired_policy_decision(
        self,
        user_override: str | None,
        final_decision: str,
        execution_result: str,
    ) -> str:
        if user_override in {"prefer_auto_execute", "confirmed_after_prompt", "forced_auto_execute"}:
            return "auto_execute"
        if user_override in {"prefer_confirmation", "blocked_auto_execute"}:
            return "require_confirmation"
        if execution_result in {"failure", "rollback"} and final_decision == "auto_execute":
            return "require_confirmation"
        return final_decision

    def _create_candidate_rule(
        self,
        task_context: Mapping[str, Any],
        policy_decision: str,
        source_type: str,
    ) -> Rule:
        scope, scope_key = self._infer_scope(task_context)
        summary = (
            f"{'Auto execute' if policy_decision == 'auto_execute' else 'Require confirmation'} "
            f"for {self._task_summary(task_context)}"
        )
        rule = Rule(
            id=f"policy_{uuid4().hex[:10]}",
            summary=summary,
            category="harden",
            trigger=self._build_rule_triggers(task_context),
            strategy=self._build_rule_strategy(task_context, policy_decision),
            validation=[self._build_validation_assertion(task_context, policy_decision)],
            confidence=0.6 if source_type.startswith("explicit") else 0.5,
            success_streak=0,
            status="candidate",
            scope=scope,
            scope_key=scope_key,
            evidence_count=1,
            source_type=source_type,
            last_seen_at=self._now(),
            last_applied_at="",
            policy_decision=policy_decision,
            risk_level=self.assess_risk(task_context).value,
        )
        rule.calculate_asset_id()
        return rule

    def _build_rule_triggers(self, task_context: Mapping[str, Any]) -> list[str]:
        triggers: list[str] = []
        task_type = safe_text(task_context, "task_type") or "T2"
        triggers.append(f"task_type:{task_type}")
        command = normalize_text(safe_text(task_context, "command"))
        if command:
            triggers.append(f"command:{command}")
        else:
            triggers.append(f"task:{normalize_text(self._task_summary(task_context))}")
        return triggers

    def _build_rule_strategy(self, task_context: Mapping[str, Any], policy_decision: str) -> str:
        summary = self._task_summary(task_context)
        if policy_decision == "auto_execute":
            return f"Prefer automatic execution for tasks matching: {summary}"
        return f"Require explicit confirmation for tasks matching: {summary}"

    def _build_validation_assertion(self, task_context: Mapping[str, Any], policy_decision: str) -> str:
        task_type = safe_text(task_context, "task_type") or "T2"
        command = safe_text(task_context, "command") or self._task_summary(task_context)
        return (
            "assert decision.final_decision == "
            f"'{policy_decision}' for task_type={task_type} command={command}"
        )

    def _apply_feedback_to_rule(
        self,
        rule: Rule,
        outcome: str,
        evidence_type: str,
        user_override: str | None,
        risk_level: str,
    ) -> bool:
        if not evidence_type:
            return False

        timestamp = self._now()
        if rule.status == "hint" and evidence_type not in {"git_history", "rl_feedback", "legacy"}:
            rule.status = "candidate"

        rule.last_seen_at = timestamp
        rule.evidence_count += 1
        rule.risk_level = risk_level or rule.risk_level
        if not rule.last_applied_at:
            rule.last_applied_at = timestamp

        if user_override == "should_have_required_confirmation":
            rule.conflict_count += 1

        if outcome == "success":
            rule.success_streak += 1
            rule.failure_streak = 0
            rule.confidence = min(1.0, rule.confidence + (0.1 if evidence_type.startswith("explicit") else 0.05))
            if rule.policy_decision == "auto_execute":
                rule.accepted_auto_execute_count += 1
            if user_override in {"confirmed_after_prompt", "prefer_auto_execute", "forced_auto_execute"}:
                rule.accepted_confirmation_count += 1
            if user_override in {"prefer_confirmation", "blocked_auto_execute"}:
                rule.override_streak += 1
            else:
                rule.override_streak = 0
        else:
            rule.success_streak = 0
            if rule.policy_decision == "auto_execute":
                rule.confidence = max(0.0, rule.confidence - 0.2)
            else:
                rule.confidence = min(1.0, rule.confidence + 0.05)
            if outcome in {"failure", "rollback"}:
                rule.failure_streak += 1
            if outcome == "rollback":
                rule.rollback_count += 1
            if user_override in {"prefer_confirmation", "blocked_auto_execute"}:
                rule.override_streak += 1
        return True

    def _has_unresolved_conflict(self, rule: Rule, rules: Mapping[str, Rule]) -> bool:
        rule_signature = tuple(sorted(rule.trigger))
        for other in rules.values():
            if other.id == rule.id or other.status != "confirmed":
                continue
            if other.scope != rule.scope or other.scope_key != rule.scope_key:
                continue
            if tuple(sorted(other.trigger)) != rule_signature:
                continue
            if other.policy_decision != rule.policy_decision:
                return True
        return False

    def _is_superseded(self, rule: Rule, rules: Mapping[str, Rule]) -> bool:
        rule_signature = tuple(sorted(rule.trigger))
        for other in rules.values():
            if other.id == rule.id or other.status != "confirmed":
                continue
            if other.scope != rule.scope or other.scope_key != rule.scope_key:
                continue
            if tuple(sorted(other.trigger)) != rule_signature:
                continue
            return True
        return False

    def _make_transition(self, event_type: str, reason: str) -> dict[str, str]:
        return {"event_type": event_type, "reason": reason}

    @staticmethod
    def _transition_event_type(transition: Mapping[str, str] | Any) -> str:
        if hasattr(transition, "transition"):
            return str(transition.transition)
        return str(transition["event_type"])

    @staticmethod
    def _transition_reason(transition: Mapping[str, str] | Any) -> str:
        if hasattr(transition, "reason"):
            return str(transition.reason)
        return str(transition["reason"])

    def _append_rule_event(
        self,
        rule: Rule,
        decision: DecisionRecord,
        source_type: str,
        transition: Mapping[str, str] | Any | None,
    ) -> None:
        if not self.policy_store:
            return

        event_type = self._transition_event_type(transition) if transition else "rule_updated"
        reason = self._transition_reason(transition) if transition else "runtime_feedback"
        self.policy_store.append_event(
            PolicyEvent(
                timestamp=self._now(),
                event_type=event_type,
                asset_id=rule.asset_id,
                trigger_signals=[decision["task_type"]],
                changes=f"Policy rule updated: {rule.status} / {rule.policy_decision}",
                source_node_id=source_type or "runtime_feedback",
                payload={
                    "rule_id": rule.id,
                    "status": rule.status,
                    "policy_decision": rule.policy_decision,
                    "evidence_count": rule.evidence_count,
                    "trigger": reason,
                    "scope": rule.scope,
                    "scope_key": rule.scope_key,
                    "risk_level": rule.risk_level,
                },
            )
        )

    def _archive_superseded_suspended_rules(
        self,
        rules: Mapping[str, Rule],
        decision: DecisionRecord,
    ) -> None:
        if not self.policy_store:
            return
        for rule in rules.values():
            if rule.status != "suspended":
                continue
            transition = self.demotion_gate.maybe_archive(rule, superseded=self._is_superseded(rule, rules))
            if transition is None:
                continue
            rule.last_lifecycle_event_at = self._now()
            rule.calculate_asset_id()
            self._append_rule_event(rule, decision, "lifecycle", transition)
