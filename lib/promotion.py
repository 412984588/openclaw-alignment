#!/usr/bin/env python3
"""Lightweight promotion gate for confirmation policy rules."""

from __future__ import annotations

from dataclasses import dataclass

from .policy_models import Rule
from .policy_store import PolicyStore

MIN_PROMOTION_EVIDENCE = 3
MIN_STABLE_SUCCESS_COUNT = 3
MIN_ACCEPTED_AUTO_EXECUTE_COUNT = 3

WEAK_SOURCE_TYPES = {
    "git_history",
    "file_pattern",
    "workflow_test_ratio",
    "tech_stack_frequency",
    "rl_feedback",
    "legacy",
}

EXPLICIT_CONFIRMATION_OVERRIDES = {
    "confirmed_after_prompt",
    "prefer_auto_execute",
    "prefer_confirmation",
    "blocked_auto_execute",
}


@dataclass
class PromotionResult:
    """Structured promotion decision."""

    promoted: bool
    reasons: list[str]


class PromotionGate:
    """Minimal candidate -> confirmed promotion gate."""

    def __init__(self, policy_store: PolicyStore):
        self.policy_store = policy_store

    def evaluate(self, rule: Rule, risk_level: str, has_unresolved_conflict: bool) -> PromotionResult:
        """Evaluate whether a candidate rule can be promoted."""
        reasons: list[str] = []
        if rule.status != "candidate":
            return PromotionResult(False, ["rule is not a candidate"])

        if not rule.scope:
            reasons.append("scope missing")
        if not rule.policy_decision:
            reasons.append("policy decision missing")
        if rule.evidence_count < MIN_PROMOTION_EVIDENCE:
            reasons.append("insufficient evidence")
        if not rule.summary:
            reasons.append("summary missing")
        if not rule.validation:
            reasons.append("minimal test missing")
        if has_unresolved_conflict:
            reasons.append("unresolved conflict")
        if rule.source_type in WEAK_SOURCE_TYPES:
            reasons.append("weak hints cannot promote directly")

        explicit_confirmation, stable_success, accepted_auto_executes = self._collect_signal_strength(rule)
        if not (explicit_confirmation or stable_success or accepted_auto_executes):
            reasons.append("no explicit confirmation or stable success pattern")

        if risk_level in {"high", "critical"} and rule.policy_decision == "auto_execute" and not explicit_confirmation:
            reasons.append("high-risk auto rules require explicit confirmation")

        return PromotionResult(not reasons, reasons)

    def maybe_promote(self, rule: Rule, risk_level: str, has_unresolved_conflict: bool) -> PromotionResult:
        """Promote candidate rule to confirmed when the gate passes."""
        result = self.evaluate(rule, risk_level, has_unresolved_conflict)
        if result.promoted:
            rule.status = "confirmed"
        return result

    def _collect_signal_strength(self, rule: Rule) -> tuple[bool, bool, bool]:
        events = self.policy_store.get_decision_events(limit=2_000)
        outcome_events = [
            event
            for event in events
            if event.event_type == "decision_outcome"
            and rule.id in (
                event.payload.get("matched_rule_ids", [])
                or event.payload.get("rule_ids", [])
            )
        ]
        explicit_confirmation = any(
            event.payload.get("user_override") in EXPLICIT_CONFIRMATION_OVERRIDES
            for event in outcome_events
        )
        stable_success_count = sum(
            1 for event in outcome_events if event.payload.get("execution_result") == "success"
        )
        accepted_auto_executes = max(
            rule.accepted_auto_execute_count,
            sum(
                1
                for event in outcome_events
                if event.payload.get("execution_result") == "success"
                and event.payload.get("final_decision") == "auto_execute"
                and not event.payload.get("user_override")
            ),
        )
        return (
            explicit_confirmation,
            stable_success_count >= MIN_STABLE_SUCCESS_COUNT,
            accepted_auto_executes >= MIN_ACCEPTED_AUTO_EXECUTE_COUNT,
        )
