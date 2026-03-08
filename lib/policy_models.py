#!/usr/bin/env python3
"""Canonical policy models for rule, playbook, and policy event assets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

RULE_STATUSES = {"hint", "candidate", "confirmed", "suspended", "archived"}
RULE_SCOPES = {"global", "domain", "project"}
POLICY_DECISIONS = {"", "auto_execute", "require_confirmation"}


@dataclass
class Rule:
    """A reusable confirmation rule kept in local policy memory."""

    id: str
    type: str = "Rule"
    summary: str = ""
    category: str = "innovate"
    trigger: list[str] = field(default_factory=list)
    strategy: str = ""
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    confidence: float = 0.0
    success_streak: int = 0
    status: str = "hint"
    scope: str = "global"
    scope_key: str = ""
    evidence_count: int = 0
    source_type: str = "legacy"
    last_seen_at: str = ""
    last_applied_at: str = ""
    policy_decision: str = ""
    risk_level: str = ""
    failure_streak: int = 0
    override_streak: int = 0
    rollback_count: int = 0
    accepted_auto_execute_count: int = 0
    accepted_confirmation_count: int = 0
    conflict_count: int = 0
    suspension_reason: str = ""
    last_lifecycle_event_at: str = ""
    asset_id: str = ""

    def calculate_asset_id(self) -> str:
        """Compute a deterministic asset id from record content."""
        content = asdict(self)
        content.pop("asset_id", None)
        serialized = json.dumps(content, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.asset_id = f"sha256:{digest}"
        return self.asset_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Rule":
        """Deserialize and normalize legacy payloads."""
        payload = dict(data)
        payload["type"] = "Rule"
        payload.setdefault("status", "hint")
        payload.setdefault("scope", "global")
        payload.setdefault("scope_key", "")
        payload.setdefault("evidence_count", 0)
        payload.setdefault("source_type", "legacy")
        payload.setdefault("last_seen_at", "")
        payload.setdefault("last_applied_at", "")
        payload.setdefault("policy_decision", "")
        payload.setdefault("risk_level", "")
        payload.setdefault("failure_streak", 0)
        payload.setdefault("override_streak", 0)
        payload.setdefault("rollback_count", 0)
        payload.setdefault("accepted_auto_execute_count", 0)
        payload.setdefault("accepted_confirmation_count", 0)
        payload.setdefault("conflict_count", 0)
        payload.setdefault("suspension_reason", "")
        payload.setdefault("last_lifecycle_event_at", "")

        if payload["status"] not in RULE_STATUSES:
            payload["status"] = "hint"
        if payload["scope"] not in RULE_SCOPES:
            payload["scope"] = "global"
        if payload["policy_decision"] not in POLICY_DECISIONS:
            payload["policy_decision"] = ""

        return cls(**payload)

    def increment_confidence(self, reward: float) -> None:
        """Adjust confidence and success streak from a reward signal."""
        if reward > 0.7:
            self.success_streak += 1
            self.confidence = min(1.0, self.confidence + 0.05)
        elif reward < 0.3:
            self.success_streak = 0
            self.confidence = max(0.0, self.confidence - 0.1)

    def __str__(self) -> str:
        return f"[{self.id}] {self.summary} (confidence: {self.confidence:.2f})"


@dataclass
class Playbook:
    """A reusable playbook composed of multiple confirmation rules."""

    id: str
    type: str = "Playbook"
    summary: str = ""
    rules_used: list[str] = field(default_factory=list)
    trigger: list[str] = field(default_factory=list)
    category: str = "innovate"
    confidence: float = 0.0
    asset_id: str = ""

    def calculate_asset_id(self) -> str:
        """Compute a deterministic asset id from record content."""
        content = asdict(self)
        content.pop("asset_id", None)
        serialized = json.dumps(content, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.asset_id = f"sha256:{digest}"
        return self.asset_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Playbook":
        """Deserialize and normalize legacy payloads."""
        payload = dict(data)
        payload["type"] = "Playbook"
        payload["rules_used"] = list(payload.get("rules_used") or payload.get("genes_used") or [])
        payload.pop("genes_used", None)
        return cls(**payload)

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.summary} "
            f"({len(self.rules_used)} rules, confidence: {self.confidence:.2f})"
        )


@dataclass
class PolicyEvent:
    """Append-only policy event for evaluation and decision history."""

    timestamp: str
    event_type: str
    asset_id: str
    type: str = "PolicyEvent"
    trigger_signals: list[str] = field(default_factory=list)
    rl_reward: float = 0.0
    changes: str = ""
    source_node_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyEvent":
        """Deserialize and normalize legacy payloads."""
        payload = dict(data)
        payload["type"] = "PolicyEvent"
        return cls(**payload)

    def to_jsonl(self) -> str:
        """Serialize as one JSONL line."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, jsonl_str: str) -> "PolicyEvent":
        """Deserialize from one JSONL line."""
        return cls.from_dict(json.loads(jsonl_str))

    def __str__(self) -> str:
        if self.payload.get("decision_id"):
            decision = self.payload.get("final_decision", "unknown")
            return f"[{self.timestamp}] {self.event_type}: {decision} ({self.payload['decision_id']})"
        return f"[{self.timestamp}] {self.event_type}: {self.changes} (reward: {self.rl_reward:.2f})"

__all__ = [
    "RULE_STATUSES",
    "RULE_SCOPES",
    "POLICY_DECISIONS",
    "Rule",
    "Playbook",
    "PolicyEvent",
]
