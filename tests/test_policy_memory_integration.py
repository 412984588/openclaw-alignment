#!/usr/bin/env python3
"""Integration tests for policy memory, CLI, and markdown conversion."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import rmtree

import pytest

from lib.cli import OpenClawAlignmentCLI
from lib.md_to_policy import MarkdownToPolicyConverter
from lib.policy_store import PolicyStore
from lib.policy_to_md import PolicyToMarkdownExporter


class TestCLIInit:
    """Tests for `openclaw-align init`."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_init_creates_policy_files(self, temp_dir: Path) -> None:
        cli = OpenClawAlignmentCLI()
        cli.memory_dir_name = ".openclaw_memory_test"

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            success = cli.init(force=True)
            assert success is True

            memory_dir = cli.get_memory_dir()
            policy_dir = memory_dir / "policy"
            assert policy_dir.exists()
            assert (policy_dir / "rules.json").exists()
            assert (policy_dir / "playbooks.json").exists()
            assert (policy_dir / "policy_events.jsonl").exists()
        finally:
            os.chdir(original_cwd)

    def test_init_writes_timestamp_and_working_directory_fields(self, temp_dir: Path) -> None:
        cli = OpenClawAlignmentCLI()
        cli.memory_dir_name = ".openclaw_memory_test"

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            success = cli.init(force=True)
            assert success is True

            config_path = cli.get_memory_dir() / cli.config_file_name
            config = json.loads(config_path.read_text(encoding="utf-8"))

            initialized_at = datetime.fromisoformat(config["initialized_at"])
            assert initialized_at.tzinfo is not None
            assert initialized_at.utcoffset() == timezone.utc.utcoffset(initialized_at)
            assert Path(config["initialized_in"]).resolve() == temp_dir.resolve()
            assert config["memory_path"] == str(cli.get_memory_dir())
        finally:
            os.chdir(original_cwd)

    def test_init_auto_migrates_markdown_into_policy_assets(self, temp_dir: Path) -> None:
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

            success = cli.init(force=False)
            assert success is True

            policy_dir = memory_dir / "policy"
            store = PolicyStore(policy_dir)

            assert policy_dir.exists()
            assert store.load_rules() or store.load_playbooks() or store.get_events()
        finally:
            os.chdir(original_cwd)


class TestMarkdownToPolicyConversion:
    """Tests for markdown -> policy conversion."""

    @pytest.fixture
    def temp_dir(self) -> Path:
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

        converter = MarkdownToPolicyConverter()
        rules = converter.convert_user_md_to_rules(user_md)

        assert rules
        assert any("basic_info" in rule_id for rule_id in rules)

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

        converter = MarkdownToPolicyConverter()
        playbook = converter.convert_soul_md_to_playbook(soul_md)

        assert playbook is not None
        assert playbook.category == "harden"

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

        converter = MarkdownToPolicyConverter()
        rules = converter.convert_agents_md_to_rules(agents_md)

        assert rules


class TestPolicyToMarkdownExport:
    """Tests for policy memory -> markdown export."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_export_rules_to_user_md(self, temp_dir: Path) -> None:
        from lib.policy_models import Rule

        basic_rule = Rule(
            id="rule_basic_info",
            summary="Basic information",
            category="optimize",
            strategy="- Name: Test User\n- Role: Developer",
        )

        rules = {"rule_basic_info": basic_rule}

        exporter = PolicyToMarkdownExporter()
        output_path = temp_dir / "USER.md"
        exporter.export_rules_to_user_md(rules, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# USER" in content
        assert "Test User" in content

    def test_export_playbook_to_soul_md(self, temp_dir: Path) -> None:
        from lib.policy_models import Playbook

        playbook = Playbook(
            id="playbook_safety",
            summary="Safety boundary",
            category="harden",
            rules_used=[],
        )

        exporter = PolicyToMarkdownExporter()
        output_path = temp_dir / "SOUL.md"
        exporter.export_playbook_to_soul_md(playbook, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# SOUL" in content
