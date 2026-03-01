#!/usr/bin/env python3
"""Exporter from GEP assets back to Markdown configuration files."""

from __future__ import annotations

from pathlib import Path

from .gep import Capsule, Gene
from .gep_store import GEPStore

# Legacy compatibility aliases. Chinese terms are encoded with unicode escapes to
# keep source files English-only while still matching old persisted data.
_BASIC_INFO_ALIASES = (
    "Basic information",
    "basic info",
    "\u57fa\u672c\u4fe1\u606f",
)
_WORK_PREF_ALIASES = (
    "Working preferences",
    "work habits",
    "\u5de5\u4f5c\u4e60\u60ef\u504f\u597d",
    "\u5de5\u4f5c\u4e60\u60ef",
)
_PROJECT_CONSTRAINT_ALIASES = (
    "Project constraints",
    "project specific constraints",
    "\u9879\u76ee\u7279\u5b9a\u7ea6\u675f",
)
_TOOL_DISPATCH_ALIASES = (
    "Agent tool dispatch",
    "tool dispatch",
    "\u5de5\u5177\u8c03\u5ea6\u7b56\u7565",
)
_OPERATION_RULE_ALIASES = (
    "Agent operation rules",
    "operation rules",
    "\u64cd\u4f5c\u89c4\u5219",
)
_ESCALATION_ALIASES = (
    "Escalation policy",
    "escalation",
    "\u4e0d\u786e\u5b9a\u65f6\u5347\u7ea7\u7b56\u7565",
)
_SAFETY_CAPSULE_ALIASES = (
    "Safety boundary",
    "Safety boundary and core principles",
    "\u5b89\u5168\u8fb9\u754c",
)


class GEPToMarkdownExporter:
    """Export genes/capsules to USER.md, SOUL.md and AGENTS.md."""

    def export_genes_to_user_md(self, genes: dict[str, Gene], output_path: Path) -> None:
        """Export USER.md from user-related genes."""
        basic_info_gene = self._find_gene_by_aliases(genes, _BASIC_INFO_ALIASES)
        work_habits_gene = self._find_gene_by_aliases(genes, _WORK_PREF_ALIASES)
        constraints_gene = self._find_gene_by_aliases(genes, _PROJECT_CONSTRAINT_ALIASES)

        content = "# USER\n\n"
        content += "## Basic Information\n\n"
        if basic_info_gene:
            content += self._format_gene_strategy(basic_info_gene)
        else:
            content += "- Name: [Your Name]\n"
            content += "- Role: [Developer | Data Scientist | DevOps | Manager]\n"
            content += "- Primary Stack: [Python | JavaScript | Go | Rust | Other]\n"

        content += "\n## Working Preferences\n\n"
        if work_habits_gene:
            content += self._format_gene_strategy(work_habits_gene)
        else:
            content += "- Communication style: [concise | detailed | interactive]\n"
            content += "- Automation preference: [low | medium | high]\n"
            content += "- Review depth: [light | standard | strict]\n"

        content += "\n## Notes\n\n"
        if constraints_gene:
            content += self._format_gene_strategy(constraints_gene)
        else:
            content += "- Add project-specific constraints and personal preferences here.\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"✅ Exported USER.md: {output_path}")

    def export_capsule_to_soul_md(self, capsule: Capsule | None, output_path: Path) -> None:
        """Export SOUL.md from a capsule (currently template-based)."""
        _ = capsule

        content = "# SOUL\n\n"
        content += "## Core Principles\n\n"
        content += "1. Safety First\n\n"
        content += "- Protect user data\n"
        content += "- Require explicit confirmation for high-risk actions\n"
        content += "- Respect task boundaries\n\n"
        content += "2. Transparency and Control\n\n"
        content += "- Explain recommendations\n"
        content += "- Keep user as final decision-maker\n"
        content += "- Keep auditable logs\n\n"
        content += "3. Continuous Learning\n\n"
        content += "- Improve incrementally from feedback\n"
        content += "- Avoid overfitting to short-term patterns\n\n"
        content += "4. Quality Assurance\n\n"
        content += "- Prefer test-first workflows\n"
        content += "- Keep documentation in sync with behavior\n"
        content += "- Monitor performance and regressions\n\n"
        content += "## Prohibited Actions\n\n"
        content += "- Destructive file operations without confirmation\n"
        content += "- Unauthorized external network or data export\n"
        content += "- Secret disclosure\n\n"
        content += "## Reward Signals\n\n"
        content += "- Positive: task completion, quality improvement, user acceptance\n"
        content += "- Negative: regressions, boundary violations, repeated failures\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"✅ Exported SOUL.md: {output_path}")

    def export_agent_genes_to_agents_md(self, genes: dict[str, Gene], output_path: Path) -> None:
        """Export AGENTS.md from agent-related genes."""
        tool_dispatch_gene = self._find_gene_by_aliases(genes, _TOOL_DISPATCH_ALIASES)
        operation_rules_gene = self._find_gene_by_aliases(genes, _OPERATION_RULE_ALIASES)
        escalation_gene = self._find_gene_by_aliases(genes, _ESCALATION_ALIASES)

        content = "# AGENTS\n\n"
        content += "## Tool Dispatch\n\n"
        if tool_dispatch_gene:
            content += self._format_gene_strategy(tool_dispatch_gene)
        else:
            content += "- Codex: backend logic, APIs, data processing\n"
            content += "- Claude Code: UI and interaction-heavy tasks\n"
            content += "- Gemini: research and external references\n"

        content += "\n## Operation Rules\n\n"
        if operation_rules_gene:
            content += self._format_gene_strategy(operation_rules_gene)
        else:
            content += "- Behavior changes require tests\n"
            content += "- Keep changes atomic and reviewable\n"
            content += "- Run full validation before release\n"

        content += "\n## Escalation\n\n"
        if escalation_gene:
            content += self._format_gene_strategy(escalation_gene)
        else:
            content += "- If uncertainty is high, request explicit confirmation before proceeding\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"✅ Exported AGENTS.md: {output_path}")

    def export_all(self, gep_dir: Path, output_dir: Path) -> None:
        """Export all supported Markdown files from one GEP directory."""
        gep_store = GEPStore(gep_dir)
        genes = gep_store.load_genes()
        capsules = gep_store.load_capsules()

        safety_capsule = self._find_capsule_by_aliases(capsules, _SAFETY_CAPSULE_ALIASES)

        self.export_genes_to_user_md(genes, output_dir / "USER.md")
        self.export_capsule_to_soul_md(safety_capsule, output_dir / "SOUL.md")
        self.export_agent_genes_to_agents_md(genes, output_dir / "AGENTS.md")

        print("\n✨ Markdown export completed")

    def _find_gene_by_aliases(self, genes: dict[str, Gene], aliases: tuple[str, ...]) -> Gene | None:
        for gene in genes.values():
            summary = gene.summary.lower()
            for alias in aliases:
                if alias.lower() in summary:
                    return gene
        return None

    def _find_capsule_by_aliases(
        self,
        capsules: dict[str, Capsule],
        aliases: tuple[str, ...],
    ) -> Capsule | None:
        for capsule in capsules.values():
            summary = capsule.summary.lower()
            for alias in aliases:
                if alias.lower() in summary:
                    return capsule
        return None

    @staticmethod
    def _format_gene_strategy(gene: Gene) -> str:
        strategy = gene.strategy.strip()
        if strategy.startswith("-") or "\n-" in strategy:
            return strategy if strategy.endswith("\n") else strategy + "\n"

        lines = strategy.split("\n")
        normalized: list[str] = []
        for line in lines:
            item = line.strip()
            if not item:
                continue
            if not item.startswith("-"):
                item = f"- {item}"
            normalized.append(item)
        return "\n".join(normalized) + "\n"
