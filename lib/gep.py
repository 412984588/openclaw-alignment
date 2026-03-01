#!/usr/bin/env python3
"""Data models for GEP (Gene Evolution Protocol)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Gene:
    """A single reusable behavior strategy."""

    id: str
    type: str = "Gene"
    summary: str = ""
    category: str = "innovate"  # repair|optimize|innovate|harden
    trigger: list[str] = field(default_factory=list)
    strategy: str = ""
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    confidence: float = 0.0
    success_streak: int = 0
    asset_id: str = ""

    def calculate_asset_id(self) -> str:
        """Compute deterministic SHA256 asset id from record content."""
        content = asdict(self)
        content.pop("asset_id", None)
        serialized = json.dumps(content, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.asset_id = f"sha256:{digest}"
        return self.asset_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Gene":
        """Deserialize from dictionary."""
        return cls(**data)

    def increment_confidence(self, reward: float) -> None:
        """Adjust confidence and success streak by reward signal."""
        if reward > 0.7:
            self.success_streak += 1
            self.confidence = min(1.0, self.confidence + 0.05)
        elif reward < 0.3:
            self.success_streak = 0
            self.confidence = max(0.0, self.confidence - 0.1)

    def __str__(self) -> str:
        return f"[{self.id}] {self.summary} (confidence: {self.confidence:.2f})"


@dataclass
class Capsule:
    """A complete solution composed of multiple genes."""

    id: str
    type: str = "Capsule"
    summary: str = ""
    genes_used: list[str] = field(default_factory=list)
    trigger: list[str] = field(default_factory=list)
    category: str = "innovate"
    confidence: float = 0.0
    asset_id: str = ""

    def calculate_asset_id(self) -> str:
        """Compute deterministic SHA256 asset id from record content."""
        content = asdict(self)
        content.pop("asset_id", None)
        serialized = json.dumps(content, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.asset_id = f"sha256:{digest}"
        return self.asset_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Capsule":
        """Deserialize from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.summary} "
            f"({len(self.genes_used)} genes, confidence: {self.confidence:.2f})"
        )


@dataclass
class Event:
    """Append-only audit event for GEP evolution."""

    timestamp: str
    event_type: str
    asset_id: str
    trigger_signals: list[str] = field(default_factory=list)
    rl_reward: float = 0.0
    changes: str = ""
    source_node_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Deserialize from dictionary."""
        return cls(**data)

    def to_jsonl(self) -> str:
        """Serialize as one JSONL line."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, jsonl_str: str) -> "Event":
        """Deserialize from one JSONL line."""
        return cls(**json.loads(jsonl_str))

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.event_type}: {self.changes} (reward: {self.rl_reward:.2f})"
