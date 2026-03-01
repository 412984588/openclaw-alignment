#!/usr/bin/env python3
"""Backward-compatibility tests for legacy GEP data and markdown migration."""

from __future__ import annotations

from pathlib import Path

from lib.gep import Gene
from lib.gep_to_md import GEPToMarkdownExporter
from lib.md_to_gep import MarkdownToGEPConverter


def test_export_user_md_accepts_legacy_chinese_gene_summaries(tmp_path: Path) -> None:
    genes = {
        "gene_basic_info": Gene(
            id="gene_basic_info",
            summary="\u57fa\u672c\u4fe1\u606f",
            strategy="- Name: Legacy User\n- Role: Engineer",
        ),
        "gene_work_habits": Gene(
            id="gene_work_habits",
            summary="\u5de5\u4f5c\u4e60\u60ef\u504f\u597d",
            strategy="- Communication style: concise\n- Automation preference: high",
        ),
        "gene_constraints": Gene(
            id="gene_constraints",
            summary="\u9879\u76ee\u7279\u5b9a\u7ea6\u675f",
            strategy="- Never run rm -rf in production",
        ),
    }

    output_path = tmp_path / "USER.md"
    GEPToMarkdownExporter().export_genes_to_user_md(genes, output_path)
    content = output_path.read_text(encoding="utf-8")

    assert "Legacy User" in content
    assert "Automation preference: high" in content
    assert "Never run rm -rf in production" in content


def test_export_agents_md_accepts_legacy_chinese_gene_summaries(tmp_path: Path) -> None:
    genes = {
        "gene_tool_dispatch": Gene(
            id="gene_tool_dispatch",
            summary="Agent \u5de5\u5177\u8c03\u5ea6\u7b56\u7565",
            strategy="- Codex: backend tasks",
        ),
        "gene_operation_rules": Gene(
            id="gene_operation_rules",
            summary="Agent \u64cd\u4f5c\u89c4\u5219",
            strategy="- Behavior changes require tests",
        ),
        "gene_escalation": Gene(
            id="gene_escalation",
            summary="\u4e0d\u786e\u5b9a\u65f6\u5347\u7ea7\u7b56\u7565",
            strategy="- Ask for confirmation when uncertainty is high",
        ),
    }

    output_path = tmp_path / "AGENTS.md"
    GEPToMarkdownExporter().export_agent_genes_to_agents_md(genes, output_path)
    content = output_path.read_text(encoding="utf-8")

    assert "Codex: backend tasks" in content
    assert "Behavior changes require tests" in content
    assert "Ask for confirmation when uncertainty is high" in content


def test_convert_soul_md_preserves_english_semantics(tmp_path: Path) -> None:
    soul_md = tmp_path / "SOUL.md"
    soul_md.write_text(
        """# SOUL

## Core Principles

- Keep user data safe

## Prohibited Actions

- Never delete .env files

## Reward Signals

- Reward reproducible tests
""",
        encoding="utf-8",
    )

    capsule = MarkdownToGEPConverter().convert_soul_md_to_capsule(soul_md)

    assert capsule is not None
    assert "Never delete .env files" in capsule.summary
    assert "Keep user data safe" in capsule.summary


def test_convert_soul_md_supports_legacy_chinese_sections(tmp_path: Path) -> None:
    soul_md = tmp_path / "SOUL.md"
    soul_md.write_text(
        (
            "# SOUL\n\n"
            "## \u6838\u5fc3\u539f\u5219\n\n"
            "- \u5b89\u5168\u7b2c\u4e00\n\n"
            "## \u7981\u6b62\u884c\u4e3a\n\n"
            "- \u7981\u6b62\u5220\u9664 .env\n\n"
            "## \u5956\u52b1\u4fe1\u53f7\n\n"
            "- \u9f13\u52b1\u9ad8\u8d28\u91cf\u6d4b\u8bd5\n"
        ),
        encoding="utf-8",
    )

    capsule = MarkdownToGEPConverter().convert_soul_md_to_capsule(soul_md)

    assert capsule is not None
    assert "\u5b89\u5168\u7b2c\u4e00" in capsule.summary
    assert "\u7981\u6b62\u5220\u9664 .env" in capsule.summary
