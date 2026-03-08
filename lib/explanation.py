#!/usr/bin/env python3
"""Explanation rendering helpers for confirmation decisions."""

from __future__ import annotations

from typing import Any, Mapping


def render_explanation(decision: Mapping[str, Any]) -> str:
    """Render one structured decision into concise audit text."""
    prefix = "Confirmation required" if decision["final_decision"] == "require_confirmation" else "Auto-execute"
    lines = [f"{prefix}: {decision['reason']}"]

    heuristic_basis = decision.get("heuristic_basis", [])
    if heuristic_basis:
        lines.append("Heuristic basis: " + "; ".join(heuristic_basis))

    matched_rules = decision.get("matched_rules", [])
    if matched_rules:
        rendered_rules = ", ".join(
            f"{rule['id']}[{rule['status']}/{rule['scope']}/{rule['policy_decision']}]"
            for rule in matched_rules
        )
        lines.append("Matched rules: " + rendered_rules)
        if any(rule["status"] == "suspended" for rule in matched_rules):
            lines.append("Lifecycle: suspended rules matched, so confirmation stayed fail-closed")

    lines.append(f"Resolution: {decision['resolution']}")

    fallback_reason = decision.get("fallback_reason", "")
    if fallback_reason:
        lines.append(f"Fallback: {fallback_reason}")

    confidence = decision.get("confidence", {})
    lines.append(
        "Confidence: "
        f"max={confidence.get('max_confidence', 0.0):.2f}, "
        f"matched={confidence.get('matched_rule_count', 0)}"
    )
    return "\n".join(lines)
