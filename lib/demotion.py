#!/usr/bin/env python3
"""Lifecycle demotion gates for autonomous confirmation policies."""

from __future__ import annotations

from dataclasses import dataclass

from .policy_models import Rule

SUSPEND_FAILURE_STREAK = 2
SUSPEND_OVERRIDE_STREAK = 2
SUSPEND_MISSED_CONFIRMATION_COUNT = 2
REACTIVATE_POSITIVE_EVIDENCE = 2
ARCHIVE_NEGATIVE_EVIDENCE = 3


@dataclass
class DemotionResult:
    """Structured suspension/archive/reactivation decision."""

    transition: str
    reason: str


class DemotionGate:
    """Evaluate when policies should be suspended, reactivated, or archived."""

    def maybe_suspend(
        self,
        rule: Rule,
        *,
        trigger: str,
        has_conflict: bool = False,
    ) -> DemotionResult | None:
        if rule.status != "confirmed":
            return None

        if trigger == "rollback":
            rule.status = "suspended"
            rule.suspension_reason = "rollback"
            return DemotionResult("rule_suspended", "rollback")
        if has_conflict:
            rule.status = "suspended"
            rule.suspension_reason = "conflict"
            return DemotionResult("rule_suspended", "conflict")
        if trigger == "failure" and rule.failure_streak >= SUSPEND_FAILURE_STREAK:
            rule.status = "suspended"
            rule.suspension_reason = "repeated_failure"
            return DemotionResult("rule_suspended", "repeated_failure")
        if trigger == "override" and rule.override_streak >= SUSPEND_OVERRIDE_STREAK:
            rule.status = "suspended"
            rule.suspension_reason = "repeated_override"
            return DemotionResult("rule_suspended", "repeated_override")
        if trigger == "missed_confirmation" and rule.conflict_count >= SUSPEND_MISSED_CONFIRMATION_COUNT:
            rule.status = "suspended"
            rule.suspension_reason = "missed_confirmation"
            return DemotionResult("rule_suspended", "missed_confirmation")
        return None

    def maybe_reactivate(self, rule: Rule) -> DemotionResult | None:
        if rule.status != "suspended":
            return None
        if (
            rule.accepted_confirmation_count >= REACTIVATE_POSITIVE_EVIDENCE
            or rule.accepted_auto_execute_count >= REACTIVATE_POSITIVE_EVIDENCE
        ):
            rule.status = "candidate"
            rule.suspension_reason = ""
            rule.failure_streak = 0
            rule.override_streak = 0
            rule.conflict_count = 0
            return DemotionResult("rule_reactivated", "positive_evidence")
        return None

    def maybe_archive(self, rule: Rule, *, superseded: bool = False) -> DemotionResult | None:
        if rule.status != "suspended":
            return None
        negative_score = rule.failure_streak + rule.override_streak + rule.rollback_count + rule.conflict_count
        if superseded:
            rule.status = "archived"
            return DemotionResult("rule_archived", "superseded")
        if negative_score >= ARCHIVE_NEGATIVE_EVIDENCE:
            rule.status = "archived"
            return DemotionResult("rule_archived", "continued_negative_evidence")
        return None
