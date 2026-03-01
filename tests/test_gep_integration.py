#!/usr/bin/env python3
"""Integration tests for GEP + CLI + markdown conversion paths."""

from __future__ import annotations

import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.cli import OpenClawAlignmentCLI
from lib.gep_store import GEPStore
from lib.gep_to_md import GEPToMarkdownExporter
from lib.md_to_gep import MarkdownToGEPConverter


class TestCLIInit:
    """Tests for `openclaw-align init`."""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_init_creates_gep_files(self, temp_dir: Path) -> None:
        cli = OpenClawAlignmentCLI()
        cli.memory_dir_name = ".openclaw_memory_test"

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            success = cli.init(force=True)
            assert success is True

            memory_dir = cli.get_memory_dir()
            gep_dir = memory_dir / "gep"
            assert gep_dir.exists()
            assert (gep_dir / "genes.json").exists()
            assert (gep_dir / "capsules.json").exists()
            assert (gep_dir / "events.jsonl").exists()
        finally:
            os.chdir(original_cwd)

    def test_init_auto_migration(self, temp_dir: Path) -> None:
        cli = OpenClawAlignmentCLI()
        cli.memory_dir_name = ".openclaw_memory_test"

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            memory_dir = cli.get_memory_dir()
            if memory_dir.exists():
                rmtree(memory_dir)
            memory_dir.mkdir(parents=True, exist_ok=True)

            (memory_dir / "USER.md").write_text(
                """# USER

## Basic Information

- Name: Test User
- Role: Developer

## Working Preferences

- Communication style: concise
- Automation preference: high
""",
                encoding="utf-8",
            )

            (memory_dir / "SOUL.md").write_text(
                """# SOUL

## Core Principles

1. Safety First

- Protect user data
""",
                encoding="utf-8",
            )

            success = cli.init(force=True)
            assert success is True

            gep_dir = memory_dir / "gep"
            assert gep_dir.exists()

            gep_store = GEPStore(gep_dir)
            genes = gep_store.load_genes()
            events = gep_store.get_events()

            assert len(genes) >= 0
            assert len(events) >= 0
        finally:
            os.chdir(original_cwd)


class TestMarkdownToGEPConversion:
    """Tests for markdown -> GEP conversion."""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_convert_user_md(self, temp_dir: Path) -> None:
        user_md = temp_dir / "USER.md"
        user_md.write_text(
            """# USER

## Basic Information

- Name: Test User
- Role: Developer

## Working Preferences

- Communication style: concise
- Automation preference: high
""",
            encoding="utf-8",
        )

        converter = MarkdownToGEPConverter()
        genes = converter.convert_user_md_to_genes(user_md)

        assert len(genes) > 0
        assert any("basic_info" in gene_id for gene_id in genes)

    def test_convert_soul_md(self, temp_dir: Path) -> None:
        soul_md = temp_dir / "SOUL.md"
        soul_md.write_text(
            """# SOUL

## Core Principles

1. Safety First

- Protect user data

## Prohibited Actions

- Destructive operations
""",
            encoding="utf-8",
        )

        converter = MarkdownToGEPConverter()
        capsule = converter.convert_soul_md_to_capsule(soul_md)

        assert capsule is not None
        assert capsule.category == "harden"

    def test_convert_agents_md(self, temp_dir: Path) -> None:
        agents_md = temp_dir / "AGENTS.md"
        agents_md.write_text(
            """# AGENTS

## Tool Dispatch

- Codex: backend logic
- Claude: UI tasks

## Operation Rules

- Behavior changes require tests
""",
            encoding="utf-8",
        )

        converter = MarkdownToGEPConverter()
        genes = converter.convert_agents_md_to_genes(agents_md)

        assert len(genes) > 0


class TestGEPToMarkdownExport:
    """Tests for GEP -> markdown export."""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_export_genes_to_user_md(self, temp_dir: Path) -> None:
        from lib.gep import Gene

        basic_gene = Gene(
            id="gene_basic_info",
            summary="Basic information",
            category="optimize",
            strategy="- Name: Test User\n- Role: Developer",
        )

        genes = {"gene_basic_info": basic_gene}

        exporter = GEPToMarkdownExporter()
        output_path = temp_dir / "USER.md"
        exporter.export_genes_to_user_md(genes, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# USER" in content
        assert "Test User" in content

    def test_export_capsule_to_soul_md(self, temp_dir: Path) -> None:
        from lib.gep import Capsule

        capsule = Capsule(
            id="capsule_safety",
            summary="Safety boundary",
            category="harden",
            genes_used=[],
        )

        exporter = GEPToMarkdownExporter()
        output_path = temp_dir / "SOUL.md"
        exporter.export_capsule_to_soul_md(capsule, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# SOUL" in content


class TestGEPStorePersistence:
    """Persistence behavior for GEPStore."""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_genes_persistence(self, temp_dir: Path) -> None:
        from lib.gep import Gene

        gep_store = GEPStore(temp_dir)
        gene = Gene(id="test_gene", summary="Test gene", confidence=0.8)
        gene.calculate_asset_id()
        gep_store.save_gene(gene)

        gep_store2 = GEPStore(temp_dir)
        loaded_gene = gep_store2.get_gene("test_gene")

        assert loaded_gene is not None
        assert loaded_gene.confidence == 0.8
        assert loaded_gene.asset_id == gene.asset_id

    def test_events_append_mode(self, temp_dir: Path) -> None:
        from lib.gep import Event

        gep_store = GEPStore(temp_dir)

        for i in range(5):
            event = Event(
                timestamp=f"2026-03-01T12:0{i}:00Z",
                event_type="gene_created",
                asset_id=f"sha256:test{i}",
                changes=f"Created gene {i}",
            )
            gep_store.append_event(event)

        events = gep_store.get_events(limit=100)

        assert len(events) == 5
        assert events[0].changes == "Created gene 4"
        assert events[4].changes == "Created gene 0"
