#!/usr/bin/env python3
"""Converter from Markdown memory files to GEP assets."""

from __future__ import annotations

import re
import time
from pathlib import Path

from .gep import Capsule, Event, Gene
from .gep_store import GEPStore

_BASIC_INFO_SECTIONS = ("Basic Information", "\u57fa\u672c\u4fe1\u606f")
_WORK_PREF_SECTIONS = ("Working Preferences", "\u5de5\u4f5c\u504f\u597d")
_NOTES_SECTIONS = ("Notes", "\u5907\u6ce8")

_TOOL_DISPATCH_SECTIONS = ("Tool Dispatch", "\u5de5\u5177\u8c03\u5ea6")
_OPERATION_RULES_SECTIONS = ("Operation Rules", "\u64cd\u4f5c\u89c4\u5219")
_ESCALATION_SECTIONS = ("Escalation", "\u5347\u7ea7\u7b56\u7565")

_CORE_PRINCIPLES_SECTIONS = ("Core Principles", "\u6838\u5fc3\u539f\u5219")
_PROHIBITED_SECTIONS = ("Prohibited Actions", "\u7981\u6b62\u884c\u4e3a")
_REWARD_SECTIONS = ("Reward Signals", "\u5956\u52b1\u4fe1\u53f7")


class MarkdownToGEPConverter:
    """Convert USER/SOUL/AGENTS markdown files into GEP entities."""

    def convert_user_md_to_genes(self, user_md_path: Path) -> dict[str, Gene]:
        """Convert USER.md sections into genes."""
        if not user_md_path.exists():
            print(f"⚠️  USER.md not found: {user_md_path}")
            return {}

        content = user_md_path.read_text(encoding="utf-8")
        genes: dict[str, Gene] = {}
        timestamp = int(time.time())

        basic_info = self._extract_section_by_aliases(content, _BASIC_INFO_SECTIONS)
        if basic_info:
            genes["gene_basic_info"] = Gene(
                id=f"gene_basic_info_{timestamp}",
                summary="Basic information",
                category="optimize",
                strategy=basic_info,
                trigger=["task_start", "user_query"],
                confidence=0.8,
            )

        work_prefs = self._extract_section_by_aliases(content, _WORK_PREF_SECTIONS)
        if work_prefs:
            genes["gene_work_habits"] = Gene(
                id=f"gene_work_habits_{timestamp}",
                summary="Working preferences",
                category="optimize",
                strategy=work_prefs,
                trigger=["task_execution", "workflow_decision"],
                confidence=0.8,
            )

        notes = self._extract_section_by_aliases(content, _NOTES_SECTIONS)
        if notes:
            genes["gene_project_constraints"] = Gene(
                id=f"gene_project_constraints_{timestamp}",
                summary="Project constraints",
                category="harden",
                strategy=notes,
                trigger=["constraint_check", "validation"],
                confidence=0.7,
            )

        for gene in genes.values():
            gene.calculate_asset_id()

        return genes

    def convert_soul_md_to_capsule(self, soul_md_path: Path) -> Capsule | None:
        """Convert SOUL.md into one safety capsule while preserving key semantics."""
        if not soul_md_path.exists():
            print(f"⚠️  SOUL.md not found: {soul_md_path}")
            return None

        content = soul_md_path.read_text(encoding="utf-8")

        core_principles = self._extract_section_by_aliases(content, _CORE_PRINCIPLES_SECTIONS)
        prohibited = self._extract_section_by_aliases(content, _PROHIBITED_SECTIONS)
        rewards = self._extract_section_by_aliases(content, _REWARD_SECTIONS)

        summary = self._compose_soul_summary(core_principles, prohibited, rewards)

        capsule = Capsule(
            id=f"capsule_safety_{int(time.time())}",
            summary=summary,
            genes_used=[],
            trigger=self._build_soul_triggers(core_principles, prohibited, rewards),
            category="harden",
            confidence=0.9,
        )
        capsule.calculate_asset_id()
        return capsule

    def convert_agents_md_to_genes(self, agents_md_path: Path) -> dict[str, Gene]:
        """Convert AGENTS.md sections into genes."""
        if not agents_md_path.exists():
            print(f"⚠️  AGENTS.md not found: {agents_md_path}")
            return {}

        content = agents_md_path.read_text(encoding="utf-8")
        genes: dict[str, Gene] = {}
        timestamp = int(time.time())

        tool_dispatch = self._extract_section_by_aliases(content, _TOOL_DISPATCH_SECTIONS)
        if tool_dispatch:
            genes["gene_tool_dispatch"] = Gene(
                id=f"gene_tool_dispatch_{timestamp}",
                summary="Agent tool dispatch",
                category="optimize",
                strategy=tool_dispatch,
                trigger=["agent_selection", "task_dispatch"],
                confidence=0.8,
            )

        operation_rules = self._extract_section_by_aliases(content, _OPERATION_RULES_SECTIONS)
        if operation_rules:
            genes["gene_operation_rules"] = Gene(
                id=f"gene_operation_rules_{timestamp}",
                summary="Agent operation rules",
                category="harden",
                strategy=operation_rules,
                trigger=["operation_check", "validation"],
                confidence=0.8,
            )

        escalation = self._extract_section_by_aliases(content, _ESCALATION_SECTIONS)
        if escalation:
            genes["gene_escalation"] = Gene(
                id=f"gene_escalation_{timestamp}",
                summary="Escalation policy",
                category="harden",
                strategy=escalation,
                trigger=["high_uncertainty", "escalation_request"],
                confidence=0.8,
            )

        for gene in genes.values():
            gene.calculate_asset_id()

        return genes

    def migrate_all(self, memory_dir: Path, gep_store: GEPStore) -> None:
        """Migrate USER.md/SOUL.md/AGENTS.md into GEP storage."""
        print("🔄 Migrating markdown files into GEP assets...")

        user_md = memory_dir / "USER.md"
        soul_md = memory_dir / "SOUL.md"
        agents_md = memory_dir / "AGENTS.md"

        if user_md.exists():
            print("📄 Processing USER.md...")
            user_genes = self.convert_user_md_to_genes(user_md)
            existing_genes = gep_store.load_genes()
            existing_genes.update(user_genes)
            gep_store.save_genes(existing_genes)
            print(f"✅ Imported {len(user_genes)} gene(s) from USER.md")

            for gene in user_genes.values():
                gep_store.append_event(
                    Event(
                        timestamp=self._current_timestamp(),
                        event_type="gene_created",
                        asset_id=gene.asset_id,
                        changes=f"Migrated from USER.md: {self._compact_text(gene.summary)}",
                        source_node_id="md_migration",
                    )
                )

        if soul_md.exists():
            print("📄 Processing SOUL.md...")
            soul_capsule = self.convert_soul_md_to_capsule(soul_md)
            if soul_capsule:
                existing_capsules = gep_store.load_capsules()
                existing_capsules[soul_capsule.id] = soul_capsule
                gep_store.save_capsules(existing_capsules)
                print("✅ Imported 1 capsule from SOUL.md")

                gep_store.append_event(
                    Event(
                        timestamp=self._current_timestamp(),
                        event_type="capsule_created",
                        asset_id=soul_capsule.asset_id,
                        changes=f"Migrated from SOUL.md: {self._compact_text(soul_capsule.summary, 180)}",
                        source_node_id="md_migration",
                    )
                )

        if agents_md.exists():
            print("📄 Processing AGENTS.md...")
            agent_genes = self.convert_agents_md_to_genes(agents_md)
            existing_genes = gep_store.load_genes()
            existing_genes.update(agent_genes)
            gep_store.save_genes(existing_genes)
            print(f"✅ Imported {len(agent_genes)} gene(s) from AGENTS.md")

            for gene in agent_genes.values():
                gep_store.append_event(
                    Event(
                        timestamp=self._current_timestamp(),
                        event_type="gene_created",
                        asset_id=gene.asset_id,
                        changes=f"Migrated from AGENTS.md: {self._compact_text(gene.summary)}",
                        source_node_id="md_migration",
                    )
                )

        print("✨ Migration completed")

    @staticmethod
    def _extract_section(content: str, section_name: str) -> str:
        """Extract one markdown section body by heading name."""
        pattern = rf"##\s+{re.escape(section_name)}\s*\n+(.*?)(?=\n##\s+|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _extract_section_by_aliases(self, content: str, section_names: tuple[str, ...]) -> str:
        """Extract one section using multiple possible heading aliases."""
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
        """Build a summary that keeps human-meaningful source snippets."""
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
        """Build trigger list while preserving stable defaults."""
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
        """Return current ISO-8601 timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()
