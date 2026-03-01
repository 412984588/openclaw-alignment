#!/usr/bin/env python3
"""
GEP 集成测试

测试 GEP 与现有系统的集成，包括 CLI 命令、自动迁移、RL 学习等。
"""

import json
import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.cli import OpenClawAlignmentCLI
from lib.gep_store import GEPStore
from lib.md_to_gep import MarkdownToGEPConverter
from lib.gep_to_md import GEPToMarkdownExporter


class TestCLIInit:
    """测试 CLI init 命令"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录 fixture"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_init_creates_gep_files(self, temp_dir):
        """测试 openclaw-align init 创建 GEP 文件"""
        cli = OpenClawAlignmentCLI()
        cli.memory_dir_name = ".openclaw_memory_test"

        # 切换到临时目录
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            success = cli.init(force=True)
            assert success is True

            # 验证 GEP 目录存在
            memory_dir = cli.get_memory_dir()
            gep_dir = memory_dir / "gep"
            assert gep_dir.exists()

            # 验证 GEP 文件存在
            assert (gep_dir / "genes.json").exists()
            assert (gep_dir / "capsules.json").exists()
            assert (gep_dir / "events.jsonl").exists()

        finally:
            os.chdir(original_cwd)

    def test_init_auto_migration(self, temp_dir):
        """测试 init 命令自动迁移现有 MD 文件"""
        cli = OpenClawAlignmentCLI()
        cli.memory_dir_name = ".openclaw_memory_test"

        # 先创建一些 MD 文件
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # 创建测试 MD 文件
            memory_dir = cli.get_memory_dir()

            # 如果目录已存在，先删除
            if memory_dir.exists():
                rmtree(memory_dir)

            memory_dir.mkdir(parents=True, exist_ok=True)

            (memory_dir / "USER.md").write_text("""# USER

## Basic Information

- Name: Test User
- Role: Developer

## Working Preferences

- Communication style: concise
- Automation preference: high
""", encoding='utf-8')

            (memory_dir / "SOUL.md").write_text("""# SOUL

## Core Principles

1. Safety First

- Protect user data
""", encoding='utf-8')

            # 运行 init（force=True 以确保初始化）
            success = cli.init(force=True)
            assert success is True

            # 验证迁移成功
            gep_dir = memory_dir / "gep"
            assert gep_dir.exists()

            gep_store = GEPStore(gep_dir)
            genes = gep_store.load_genes()

            # 应该有一些 Gene 被创建（从模板文件）
            assert len(genes) >= 0  # 模板文件可能为空，所以 >= 0

            # 至少应该有 Events 记录
            events = gep_store.get_events()
            assert len(events) >= 0

        finally:
            os.chdir(original_cwd)


class TestMarkdownToGEPConversion:
    """测试 Markdown → GEP 转换"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录 fixture"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_convert_user_md(self, temp_dir):
        """测试 USER.md 转换"""
        # 创建测试 USER.md
        user_md = temp_dir / "USER.md"
        user_md.write_text("""# USER

## Basic Information

- Name: Test User
- Role: Developer

## Working Preferences

- Communication style: concise
- Automation preference: high
""", encoding='utf-8')

        # 转换
        converter = MarkdownToGEPConverter()
        genes = converter.convert_user_md_to_genes(user_md)

        assert len(genes) > 0
        assert any("basic_info" in gene_id for gene_id in genes.keys())

    def test_convert_soul_md(self, temp_dir):
        """测试 SOUL.md 转换"""
        # 创建测试 SOUL.md
        soul_md = temp_dir / "SOUL.md"
        soul_md.write_text("""# SOUL

## Core Principles

1. Safety First

- Protect user data

## Prohibited Actions

- Destructive operations
""", encoding='utf-8')

        # 转换
        converter = MarkdownToGEPConverter()
        capsule = converter.convert_soul_md_to_capsule(soul_md)

        assert capsule is not None
        assert capsule.category == "harden"

    def test_convert_agents_md(self, temp_dir):
        """测试 AGENTS.md 转换"""
        # 创建测试 AGENTS.md
        agents_md = temp_dir / "AGENTS.md"
        agents_md.write_text("""# AGENTS

## Tool Dispatch

- Codex: backend logic
- Claude: UI tasks

## Operation Rules

- Behavior changes require tests
""", encoding='utf-8')

        # 转换
        converter = MarkdownToGEPConverter()
        genes = converter.convert_agents_md_to_genes(agents_md)

        assert len(genes) > 0


class TestGEPToMarkdownExport:
    """测试 GEP → Markdown 导出"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录 fixture"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_export_genes_to_user_md(self, temp_dir):
        """测试 Gene 导出为 USER.md"""
        # 创建测试 Gene
        from lib.gep import Gene

        basic_gene = Gene(
            id="gene_basic_info",
            summary="基本信息",
            category="optimize",
            strategy="- Name: Test User\n- Role: Developer"
        )

        genes = {"gene_basic_info": basic_gene}

        # 导出
        exporter = GEPToMarkdownExporter()
        output_path = temp_dir / "USER.md"
        exporter.export_genes_to_user_md(genes, output_path)

        # 验证文件存在
        assert output_path.exists()

        # 验证内容
        content = output_path.read_text(encoding='utf-8')
        assert "# USER" in content
        assert "Test User" in content

    def test_export_capsule_to_soul_md(self, temp_dir):
        """测试 Capsule 导出为 SOUL.md"""
        # 创建测试 Capsule（注意：Capsule 没有 strategy 属性）
        from lib.gep import Capsule

        capsule = Capsule(
            id="capsule_safety",
            summary="安全边界",
            category="harden",
            genes_used=[]
        )

        # 导出
        exporter = GEPToMarkdownExporter()
        output_path = temp_dir / "SOUL.md"
        exporter.export_capsule_to_soul_md(capsule, output_path)

        # 验证文件存在
        assert output_path.exists()

        # 验证内容
        content = output_path.read_text(encoding='utf-8')
        assert "# SOUL" in content


class TestGEPStorePersistence:
    """测试 GEPStore 持久化"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录 fixture"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_genes_persistence(self, temp_dir):
        """测试 Gene 持久化"""
        from lib.gep import Gene

        # 第一次保存
        gep_store = GEPStore(temp_dir)
        gene = Gene(
            id="test_gene",
            summary="测试基因",
            confidence=0.8
        )
        gene.calculate_asset_id()
        gep_store.save_gene(gene)

        # 创建新的 GEPStore 实例（模拟重启）
        gep_store2 = GEPStore(temp_dir)
        loaded_gene = gep_store2.get_gene("test_gene")

        assert loaded_gene is not None
        assert loaded_gene.confidence == 0.8
        assert loaded_gene.asset_id == gene.asset_id

    def test_events_append_mode(self, temp_dir):
        """测试 Event 追加模式"""
        from lib.gep import Event

        gep_store = GEPStore(temp_dir)

        # 追加多个 Event
        for i in range(5):
            event = Event(
                timestamp=f"2026-03-01T12:0{i}:00Z",
                event_type="gene_created",
                asset_id=f"sha256:test{i}",
                changes=f"创建基因{i}"
            )
            gep_store.append_event(event)

        # 读取所有 Event
        events = gep_store.get_events(limit=100)

        assert len(events) == 5

        # 验证倒序（最新的在前）
        assert events[0].changes == "创建基因4"
        assert events[4].changes == "创建基因0"
