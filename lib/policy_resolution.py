#!/usr/bin/env python3
"""Policy matching and precedence helpers for confirmation decisions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from .policy_models import Rule


def safe_text(task_context: Mapping[str, Any], key: str) -> str:
    """Return a task field as a normalized string."""
    value = task_context.get(key, "")
    if isinstance(value, str):
        return value
    return str(value)


def safe_files(task_context: Mapping[str, Any]) -> list[str]:
    """Return the task file list as strings."""
    raw_files = task_context.get("files", [])
    if not isinstance(raw_files, Sequence) or isinstance(raw_files, (str, bytes)):
        return []
    return [str(item) for item in raw_files]


def normalize_text(value: str) -> str:
    """Collapse whitespace and lowercase for matching."""
    return " ".join(value.lower().strip().split())


def parse_timestamp(value: str) -> datetime:
    """Parse timestamps defensively for precedence decisions."""
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def task_summary(task_context: Mapping[str, Any]) -> str:
    """Build a short human-readable task summary."""
    summary = safe_text(task_context, "task_summary")
    if summary:
        return summary
    description = safe_text(task_context, "task_description")
    if description:
        return description[:120]
    command = safe_text(task_context, "command")
    return command[:120]


def infer_domain(task_context: Mapping[str, Any]) -> str:
    """Infer a coarse task domain for scope matching."""
    explicit_domain = normalize_text(safe_text(task_context, "domain"))
    if explicit_domain in {"code", "ops", "docs", "review", "analysis"}:
        return explicit_domain

    command = normalize_text(safe_text(task_context, "command"))
    summary = normalize_text(task_summary(task_context))
    description = normalize_text(safe_text(task_context, "task_description"))
    files = [normalize_text(item) for item in safe_files(task_context)]
    combined = " ".join(filter(None, [command, summary, description, " ".join(files)]))

    if any(item in combined for item in ["docs/", "mkdocs", "readme", ".md", "documentation"]):
        return "docs"
    if any(item in combined for item in ["deploy", "docker", "kubernetes", "kubectl", "terraform", "ops"]):
        return "ops"
    if any(item in combined for item in ["review", "approve", "comment", "diff", "audit"]):
        return "review"
    if any(item in combined for item in ["analyze", "analysis", "benchmark", "profile", "measure"]):
        return "analysis"
    return "code"


def infer_scope(task_context: Mapping[str, Any], project_scope_key: str = "") -> tuple[str, str]:
    """Infer global/domain/project scope from task context."""
    task_project_scope_key = safe_text(task_context, "scope_key") or safe_text(task_context, "project_path")
    inferred_domain = infer_domain(task_context)

    if task_project_scope_key or project_scope_key:
        default_scope = "project"
    elif inferred_domain:
        default_scope = "domain"
    else:
        default_scope = "global"

    raw_scope = safe_text(task_context, "scope") or default_scope
    scope = raw_scope if raw_scope in {"global", "domain", "project"} else default_scope
    scope_key = ""
    if scope == "project":
        scope_key = task_project_scope_key or project_scope_key
        if not scope_key:
            scope = "domain" if inferred_domain else "global"
            scope_key = inferred_domain if scope == "domain" else ""
    elif scope == "domain":
        scope_key = safe_text(task_context, "domain") or inferred_domain
        if not scope_key:
            scope = "global"
    return scope, scope_key


def matches_rule(rule: Rule, task_context: Mapping[str, Any], scope_key: str) -> bool:
    """Check whether one rule matches the current task context."""
    if rule.status == "archived":
        return False
    if rule.scope == "project" and rule.scope_key and rule.scope_key != scope_key:
        return False
    if rule.scope == "domain" and rule.scope_key and rule.scope_key != infer_domain(task_context):
        return False

    task_type = safe_text(task_context, "task_type")
    command = normalize_text(safe_text(task_context, "command"))
    summary = normalize_text(task_summary(task_context))
    description = normalize_text(safe_text(task_context, "task_description"))
    combined_text = " ".join(filter(None, [summary, description, command]))
    normalized_files = [normalize_text(item) for item in safe_files(task_context)]

    structured_triggers = [
        trigger
        for trigger in rule.trigger
        if any(trigger.startswith(prefix) for prefix in ["task_type:", "command:", "task:", "file:", "keyword:"])
    ]
    legacy_triggers = [trigger for trigger in rule.trigger if trigger not in structured_triggers]

    if structured_triggers:
        for trigger in structured_triggers:
            prefix, value = trigger.split(":", 1)
            normalized_value = normalize_text(value)
            if prefix == "task_type" and task_type != value:
                return False
            if prefix == "command" and command != normalized_value:
                return False
            if prefix == "task" and summary != normalized_value:
                return False
            if prefix == "file" and normalized_value not in normalized_files:
                return False
            if prefix == "keyword" and normalized_value not in combined_text:
                return False
        return True

    if not legacy_triggers:
        return False

    for trigger in legacy_triggers:
        normalized_trigger = normalize_text(trigger)
        if trigger == task_type:
            return True
        if normalized_trigger in combined_text:
            return True
    return False


def get_matched_rules(rules: Iterable[Rule], task_context: Mapping[str, Any], scope_key: str) -> list[Rule]:
    """Return matched rules ordered by recency."""
    matched = [rule for rule in rules if matches_rule(rule, task_context, scope_key)]
    matched.sort(key=lambda rule: parse_timestamp(rule.last_seen_at), reverse=True)
    return matched


def resolve_rules(rules: list[Rule]) -> tuple[Rule | None, str]:
    """Resolve confirmed rules using project/domain/global and recency precedence."""
    if not rules:
        return None, "heuristic_default"

    project_rules = [rule for rule in rules if rule.scope == "project"]
    domain_rules = [rule for rule in rules if rule.scope == "domain"]
    global_rules = [rule for rule in rules if rule.scope == "global"]

    if project_rules:
        rule, resolution = _resolve_same_scope(project_rules)
        if rule and (domain_rules or global_rules):
            return rule, "project_over_domain" if domain_rules else "project_over_global"
        return rule, resolution

    if domain_rules:
        rule, resolution = _resolve_same_scope(domain_rules)
        if rule and global_rules:
            return rule, "domain_over_global"
        return rule, resolution

    return _resolve_same_scope(global_rules)


def _resolve_same_scope(rules: list[Rule]) -> tuple[Rule | None, str]:
    if not rules:
        return None, "heuristic_default"

    ordered = sorted(rules, key=lambda rule: parse_timestamp(rule.last_seen_at), reverse=True)
    top_rule = ordered[0]
    conflicting = [rule for rule in ordered[1:] if rule.policy_decision != top_rule.policy_decision]

    if conflicting:
        newest_conflict = conflicting[0]
        if parse_timestamp(top_rule.last_seen_at) > parse_timestamp(newest_conflict.last_seen_at):
            return top_rule, "same_scope_newer_confirmed"
        return None, "ambiguous_same_scope_conflict"

    if len(ordered) > 1:
        return top_rule, "same_scope_consistent_confirmed"
    return top_rule, f"{top_rule.scope}_confirmed_rule"


class PolicyResolver:
    """Convenience wrapper for matching and resolving policies for one project scope."""

    def __init__(self, project_scope_key: str = "") -> None:
        self.project_scope_key = project_scope_key

    def infer_scope(self, task_context: Mapping[str, Any]) -> tuple[str, str]:
        return infer_scope(task_context, self.project_scope_key)

    def matches_rule(self, rule: Rule, task_context: Mapping[str, Any], scope_key: str) -> bool:
        return matches_rule(rule, task_context, scope_key)

    def get_matched_rules(self, rules: Iterable[Rule], task_context: Mapping[str, Any], scope_key: str) -> list[Rule]:
        return get_matched_rules(rules, task_context, scope_key)

    def resolve_rules(self, rules: list[Rule]) -> tuple[Rule | None, str]:
        return resolve_rules(rules)
