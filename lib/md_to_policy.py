#!/usr/bin/env python3
"""Converter from Markdown memory files to policy memory assets."""

from __future__ import annotations

import re
import time
from pathlib import Path

from .policy_models import Playbook, PolicyEvent, Rule
from .policy_store import PolicyStore

_BASIC_INFO_SECTIONS = ("Basic Information", "\u57fa\u672c\u4fe1\u606f")
_WORK_PREF_SECTIONS = ("Working Preferences", "\u5de5\u4f5c\u504f\u597d")
_NOTES_SECTIONS = ("Notes", "\u5907\u6ce8")

_TOOL_DISPATCH_SECTIONS = ("Tool Dispatch", "\u5de5\u5177\u8c03\u5ea6")
_OPERATION_RULES_SECTIONS = ("Operation Rules", "\u64cd\u4f5c\u89c4\u5219")
_ESCALATION_SECTIONS = ("Escalation", "\u5347\u7ea7\u7b56\u7565")

_CORE_PRINCIPLES_SECTIONS = ("Core Principles", "\u6838\u5fc3\u539f\u5219")
_PROHIBITED_SECTIONS = ("Prohibited Actions", "\u7981\u6b62\u884c\u4e3a")
_REWARD_SECTIONS = ("Reward Signals", "\u5956\u52b1\u4fe1\u53f7")


class MarkdownToPolicyConverter:
    """Convert USER/SOUL/AGENTS markdown files into policy assets."""

    def convert_user_md_to_rules(self, user_md_path: Path) -> dict[str, Rule]:
        if not user_md_path.exists():
            return {}

        content = user_md_path.read_text(encoding="utf-8")
        rules: dict[str, Rule] = {}
        timestamp = int(time.time())

        basic_info = self._extract_section_by_aliases(content, _BASIC_INFO_SECTIONS)
        if basic_info:
            rules["rule_basic_info"] = Rule(
                id=f"rule_basic_info_{timestamp}",
                summary="Basic information",
                category="optimize",
                strategy=basic_info,
                trigger=["task_start", "user_query"],
                confidence=0.8,
            )

        work_prefs = self._extract_section_by_aliases(content, _WORK_PREF_SECTIONS)
        if work_prefs:
            rules["rule_work_habits"] = Rule(
                id=f"rule_work_habits_{timestamp}",
                summary="Working preferences",
                category="optimize",
                strategy=work_prefs,
                trigger=["task_execution", "workflow_decision"],
                confidence=0.8,
            )

        notes = self._extract_section_by_aliases(content, _NOTES_SECTIONS)
        if notes:
            rules["rule_project_constraints"] = Rule(
                id=f"rule_project_constraints_{timestamp}",
                summary="Project constraints",
                category="harden",
                strategy=notes,
                trigger=["constraint_check", "validation"],
                confidence=0.7,
            )

        for rule in rules.values():
            rule.calculate_asset_id()
        return rules

    def convert_soul_md_to_playbook(self, soul_md_path: Path) -> Playbook | None:
        if not soul_md_path.exists():
            return None

        content = soul_md_path.read_text(encoding="utf-8")
        core_principles = self._extract_section_by_aliases(content, _CORE_PRINCIPLES_SECTIONS)
        prohibited = self._extract_section_by_aliases(content, _PROHIBITED_SECTIONS)
        rewards = self._extract_section_by_aliases(content, _REWARD_SECTIONS)

        playbook = Playbook(
            id=f"playbook_safety_{int(time.time())}",
            summary=self._compose_soul_summary(core_principles, prohibited, rewards),
            rules_used=[],
            trigger=self._build_soul_triggers(core_principles, prohibited, rewards),
            category="harden",
            confidence=0.9,
        )
        playbook.calculate_asset_id()
        return playbook

    def convert_agents_md_to_rules(self, agents_md_path: Path) -> dict[str, Rule]:
        if not agents_md_path.exists():
            return {}

        content = agents_md_path.read_text(encoding="utf-8")
        rules: dict[str, Rule] = {}
        timestamp = int(time.time())

        tool_dispatch = self._extract_section_by_aliases(content, _TOOL_DISPATCH_SECTIONS)
        if tool_dispatch:
            rules["rule_tool_dispatch"] = Rule(
                id=f"rule_tool_dispatch_{timestamp}",
                summary="Agent tool dispatch",
                category="optimize",
                strategy=tool_dispatch,
                trigger=["agent_selection", "task_dispatch"],
                confidence=0.8,
            )

        operation_rules = self._extract_section_by_aliases(content, _OPERATION_RULES_SECTIONS)
        if operation_rules:
            rules["rule_operation_rules"] = Rule(
                id=f"rule_operation_rules_{timestamp}",
                summary="Agent operation rules",
                category="harden",
                strategy=operation_rules,
                trigger=["operation_check", "validation"],
                confidence=0.8,
            )

        escalation = self._extract_section_by_aliases(content, _ESCALATION_SECTIONS)
        if escalation:
            rules["rule_escalation"] = Rule(
                id=f"rule_escalation_{timestamp}",
                summary="Escalation policy",
                category="harden",
                strategy=escalation,
                trigger=["high_uncertainty", "escalation_request"],
                confidence=0.8,
            )

        for rule in rules.values():
            rule.calculate_asset_id()
        return rules

    def migrate_all(self, memory_dir: Path, policy_store: PolicyStore) -> None:
        user_md = memory_dir / "USER.md"
        soul_md = memory_dir / "SOUL.md"
        agents_md = memory_dir / "AGENTS.md"

        if user_md.exists():
            existing_rules = policy_store.load_rules()
            existing_rules.update(self.convert_user_md_to_rules(user_md))
            policy_store.save_rules(existing_rules)
            for rule in existing_rules.values():
                policy_store.append_event(
                    PolicyEvent(
                        timestamp=self._current_timestamp(),
                        event_type="rule_created",
                        asset_id=rule.asset_id,
                        changes=f"Migrated from USER.md: {self._compact_text(rule.summary)}",
                        source_node_id="md_migration",
                    )
                )

        if soul_md.exists():
            playbook = self.convert_soul_md_to_playbook(soul_md)
            if playbook is not None:
                playbooks = policy_store.load_playbooks()
                playbooks[playbook.id] = playbook
                policy_store.save_playbooks(playbooks)
                policy_store.append_event(
                    PolicyEvent(
                        timestamp=self._current_timestamp(),
                        event_type="playbook_created",
                        asset_id=playbook.asset_id,
                        changes=f"Migrated from SOUL.md: {self._compact_text(playbook.summary, 180)}",
                        source_node_id="md_migration",
                    )
                )

        if agents_md.exists():
            existing_rules = policy_store.load_rules()
            existing_rules.update(self.convert_agents_md_to_rules(agents_md))
            policy_store.save_rules(existing_rules)
            for rule in existing_rules.values():
                policy_store.append_event(
                    PolicyEvent(
                        timestamp=self._current_timestamp(),
                        event_type="rule_created",
                        asset_id=rule.asset_id,
                        changes=f"Migrated from AGENTS.md: {self._compact_text(rule.summary)}",
                        source_node_id="md_migration",
                    )
                )

    @staticmethod
    def _extract_section(content: str, section_name: str) -> str:
        pattern = rf"##\s+{re.escape(section_name)}\s*\n+(.*?)(?=\n##\s+|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _extract_section_by_aliases(self, content: str, section_names: tuple[str, ...]) -> str:
        for name in section_names:
            extracted = self._extract_section(content, name)
            if extracted:
                return extracted
        return ""

    @staticmethod
    def _first_content_line(section_text: str) -> str:
        for raw_line in section_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            return line[2:].strip() if line.startswith("- ") else line
        return ""

    def _compose_soul_summary(self, core: str, prohibited: str, rewards: str) -> str:
        summary_parts: list[str] = []

        core_line = self._first_content_line(core)
        if core_line:
            summary_parts.append(f"Core: {core_line}")

        prohibited_line = self._first_content_line(prohibited)
        if prohibited_line:
            summary_parts.append(f"Prohibited: {prohibited_line}")

        rewards_line = self._first_content_line(rewards)
        if rewards_line:
            summary_parts.append(f"Reward: {rewards_line}")

        if not summary_parts:
            return "Safety boundary and core principles"

        return self._compact_text(" | ".join(summary_parts), 220)

    def _build_soul_triggers(self, core: str, prohibited: str, rewards: str) -> list[str]:
        triggers = ["safety_check", "boundary_validation"]
        if prohibited:
            triggers.append("high_risk_operation")
        if rewards:
            triggers.append("reward_adjustment")
        if core:
            triggers.append("core_principles")
        return sorted(set(triggers))

    @staticmethod
    def _compact_text(value: str, max_len: int = 120) -> str:
        compact = " ".join(value.split())
        if len(compact) <= max_len:
            return compact
        return compact[: max_len - 3] + "..."

    @staticmethod
    def _current_timestamp() -> str:
        return str(int(time.time()))
