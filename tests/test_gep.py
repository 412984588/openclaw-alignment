#!/usr/bin/env python3
"""
GEP 单元测试

测试 Gene、Capsule、Event 数据模型和 GEPStore 存储管理器。
"""

import json
import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.gep import Gene, Capsule, Event
from lib.gep_store import GEPStore


class TestGene:
    """测试 Gene 数据模型"""

    def test_gene_creation(self):
        """测试 Gene 创建"""
        gene = Gene(
            id="test_gene",
            summary="测试基因",
            category="optimize",
            strategy="测试策略",
            confidence=0.8
        )

        assert gene.id == "test_gene"
        assert gene.type == "Gene"
        assert gene.summary == "测试基因"
        assert gene.category == "optimize"
        assert gene.confidence == 0.8

    def test_gene_calculate_asset_id(self):
        """测试 Gene asset_id 计算"""
        gene = Gene(
            id="test_gene",
            summary="测试基因",
            category="optimize",
            strategy="测试策略"
        )

        asset_id = gene.calculate_asset_id()

        assert asset_id.startswith("sha256:")
        assert len(asset_id) == 71  # "sha256:" + 64 个十六进制字符

    def test_gene_to_dict(self):
        """测试 Gene 转换为字典"""
        gene = Gene(
            id="test_gene",
            summary="测试基因",
            category="optimize",
            confidence=0.8
        )

        data = gene.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "test_gene"
        assert data["summary"] == "测试基因"

    def test_gene_from_dict(self):
        """测试从字典创建 Gene"""
        data = {
            "id": "test_gene",
            "type": "Gene",
            "summary": "测试基因",
            "category": "optimize",
            "trigger": [],
            "strategy": "",
            "preconditions": [],
            "postconditions": [],
            "validation": [],
            "confidence": 0.8,
            "success_streak": 0,
            "asset_id": ""
        }

        gene = Gene.from_dict(data)

        assert gene.id == "test_gene"
        assert gene.summary == "测试基因"
        assert gene.confidence == 0.8

    def test_gene_increment_confidence(self):
        """测试 Gene 信心度更新"""
        gene = Gene(
            id="test_gene",
            summary="测试基因",
            confidence=0.5,
            success_streak=0
        )

        # 高奖励
        gene.increment_confidence(0.8)
        assert gene.success_streak == 1
        assert gene.confidence > 0.5

        # 低奖励
        original_confidence = gene.confidence
        gene.increment_confidence(0.2)
        assert gene.success_streak == 0
        assert gene.confidence < original_confidence


class TestCapsule:
    """测试 Capsule 数据模型"""

    def test_capsule_creation(self):
        """测试 Capsule 创建"""
        capsule = Capsule(
            id="test_capsule",
            summary="测试胶囊",
            genes_used=["gene1", "gene2"],
            category="innovate"
        )

        assert capsule.id == "test_capsule"
        assert capsule.type == "Capsule"
        assert len(capsule.genes_used) == 2

    def test_capsule_calculate_asset_id(self):
        """测试 Capsule asset_id 计算"""
        capsule = Capsule(
            id="test_capsule",
            summary="测试胶囊",
            genes_used=[]
        )

        asset_id = capsule.calculate_asset_id()

        assert asset_id.startswith("sha256:")
        assert len(asset_id) == 71


class TestEvent:
    """测试 Event 数据模型"""

    def test_event_creation(self):
        """测试 Event 创建"""
        event = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
            rl_reward=0.8
        )

        assert event.event_type == "gene_created"
        assert event.rl_reward == 0.8

    def test_event_to_jsonl(self):
        """测试 Event 转换为 JSONL 格式"""
        event = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
            changes="创建新基因"
        )

        jsonl = event.to_jsonl()

        assert isinstance(jsonl, str)
        assert "gene_created" in jsonl
        assert "创建新基因" in jsonl

    def test_event_from_jsonl(self):
        """测试从 JSONL 格式解析 Event"""
        jsonl = '{"timestamp":"2026-03-01T12:00:00Z","event_type":"gene_created","asset_id":"sha256:abc123","trigger_signals":[],"rl_reward":0.8,"changes":"创建新基因","source_node_id":"test"}'

        event = Event.from_jsonl(jsonl)

        assert event.event_type == "gene_created"
        assert event.changes == "创建新基因"
        assert event.rl_reward == 0.8


class TestGEPStore:
    """测试 GEPStore 存储管理器"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录 fixture"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_gep_store_init(self, temp_dir):
        """测试 GEPStore 初始化"""
        gep_store = GEPStore(temp_dir)

        assert gep_store.base_dir == temp_dir
        assert gep_store.genes_file == temp_dir / "genes.json"
        assert gep_store.capsules_file == temp_dir / "capsules.json"
        assert gep_store.events_file == temp_dir / "events.jsonl"

    def test_save_and_load_genes(self, temp_dir):
        """测试 Gene 保存和加载"""
        gep_store = GEPStore(temp_dir)

        # 创建测试 Gene
        gene = Gene(
            id="test_gene",
            summary="测试基因",
            category="optimize",
            confidence=0.8
        )
        gene.calculate_asset_id()

        # 保存
        gep_store.save_gene(gene)

        # 加载
        loaded_gene = gep_store.get_gene("test_gene")

        assert loaded_gene is not None
        assert loaded_gene.id == "test_gene"
        assert loaded_gene.summary == "测试基因"
        assert loaded_gene.confidence == 0.8

    def test_save_and_load_capsules(self, temp_dir):
        """测试 Capsule 保存和加载"""
        gep_store = GEPStore(temp_dir)

        # 创建测试 Capsule
        capsule = Capsule(
            id="test_capsule",
            summary="测试胶囊",
            genes_used=["gene1"]
        )
        capsule.calculate_asset_id()

        # 保存
        gep_store.save_capsule(capsule)

        # 加载
        loaded_capsule = gep_store.get_capsule("test_capsule")

        assert loaded_capsule is not None
        assert loaded_capsule.id == "test_capsule"
        assert loaded_capsule.summary == "测试胶囊"

    def test_append_and_get_events(self, temp_dir):
        """测试 Event 追加和读取"""
        gep_store = GEPStore(temp_dir)

        # 创建测试 Event
        event1 = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
            changes="创建基因1"
        )

        event2 = Event(
            timestamp="2026-03-01T12:05:00Z",
            event_type="gene_created",
            asset_id="sha256:def456",
            changes="创建基因2"
        )

        # 追加
        gep_store.append_event(event1)
        gep_store.append_event(event2)

        # 读取
        events = gep_store.get_events(limit=10)

        assert len(events) == 2
        # 应该是倒序（最新的在前）
        assert events[0].changes == "创建基因2"
        assert events[1].changes == "创建基因1"

    def test_delete_gene(self, temp_dir):
        """测试删除 Gene"""
        gep_store = GEPStore(temp_dir)

        # 创建并保存 Gene
        gene = Gene(
            id="test_gene",
            summary="测试基因"
        )
        gep_store.save_gene(gene)

        # 删除
        result = gep_store.delete_gene("test_gene")

        assert result is True

        # 验证已删除
        loaded_gene = gep_store.get_gene("test_gene")
        assert loaded_gene is None

    def test_get_stats(self, temp_dir):
        """测试获取统计信息"""
        gep_store = GEPStore(temp_dir)

        # 添加一些数据
        gene = Gene(id="test_gene", summary="测试基因")
        capsule = Capsule(id="test_capsule", summary="测试胶囊")
        event = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123"
        )

        gep_store.save_gene(gene)
        gep_store.save_capsule(capsule)
        gep_store.append_event(event)

        # 获取统计
        stats = gep_store.get_stats()

        assert stats["total_genes"] == 1
        assert stats["total_capsules"] == 1
        assert stats["total_events"] == 1
