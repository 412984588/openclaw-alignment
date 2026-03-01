#!/usr/bin/env python3
"""Unit tests for GEP data models and storage manager."""

from __future__ import annotations

import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.gep import Capsule, Event, Gene
from lib.gep_store import GEPStore


class TestGene:
    def test_gene_creation(self) -> None:
        gene = Gene(
            id="test_gene",
            summary="Test gene",
            category="optimize",
            strategy="Test strategy",
            confidence=0.8,
        )

        assert gene.id == "test_gene"
        assert gene.type == "Gene"
        assert gene.summary == "Test gene"
        assert gene.category == "optimize"
        assert gene.confidence == 0.8

    def test_gene_calculate_asset_id(self) -> None:
        gene = Gene(
            id="test_gene",
            summary="Test gene",
            category="optimize",
            strategy="Test strategy",
        )

        asset_id = gene.calculate_asset_id()

        assert asset_id.startswith("sha256:")
        assert len(asset_id) == 71

    def test_gene_to_dict(self) -> None:
        gene = Gene(id="test_gene", summary="Test gene", category="optimize", confidence=0.8)
        data = gene.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "test_gene"
        assert data["summary"] == "Test gene"

    def test_gene_from_dict(self) -> None:
        data = {
            "id": "test_gene",
            "type": "Gene",
            "summary": "Test gene",
            "category": "optimize",
            "trigger": [],
            "strategy": "",
            "preconditions": [],
            "postconditions": [],
            "validation": [],
            "confidence": 0.8,
            "success_streak": 0,
            "asset_id": "",
        }

        gene = Gene.from_dict(data)

        assert gene.id == "test_gene"
        assert gene.summary == "Test gene"
        assert gene.confidence == 0.8

    def test_gene_increment_confidence(self) -> None:
        gene = Gene(id="test_gene", summary="Test gene", confidence=0.5, success_streak=0)

        gene.increment_confidence(0.8)
        assert gene.success_streak == 1
        assert gene.confidence > 0.5

        previous_confidence = gene.confidence
        gene.increment_confidence(0.2)
        assert gene.success_streak == 0
        assert gene.confidence < previous_confidence


class TestCapsule:
    def test_capsule_creation(self) -> None:
        capsule = Capsule(
            id="test_capsule",
            summary="Test capsule",
            genes_used=["gene1", "gene2"],
            category="innovate",
        )

        assert capsule.id == "test_capsule"
        assert capsule.type == "Capsule"
        assert len(capsule.genes_used) == 2

    def test_capsule_calculate_asset_id(self) -> None:
        capsule = Capsule(id="test_capsule", summary="Test capsule", genes_used=[])

        asset_id = capsule.calculate_asset_id()

        assert asset_id.startswith("sha256:")
        assert len(asset_id) == 71


class TestEvent:
    def test_event_creation(self) -> None:
        event = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
            rl_reward=0.8,
        )

        assert event.event_type == "gene_created"
        assert event.rl_reward == 0.8

    def test_event_to_jsonl(self) -> None:
        event = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
            changes="Created new gene",
        )

        jsonl = event.to_jsonl()

        assert isinstance(jsonl, str)
        assert "gene_created" in jsonl
        assert "Created new gene" in jsonl

    def test_event_from_jsonl(self) -> None:
        jsonl = (
            '{"timestamp":"2026-03-01T12:00:00Z","event_type":"gene_created",'
            '"asset_id":"sha256:abc123","trigger_signals":[],"rl_reward":0.8,'
            '"changes":"Created new gene","source_node_id":"test"}'
        )

        event = Event.from_jsonl(jsonl)

        assert event.event_type == "gene_created"
        assert event.changes == "Created new gene"
        assert event.rl_reward == 0.8


class TestGEPStore:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_gep_store_init(self, temp_dir: Path) -> None:
        gep_store = GEPStore(temp_dir)

        assert gep_store.base_dir == temp_dir
        assert gep_store.genes_file == temp_dir / "genes.json"
        assert gep_store.capsules_file == temp_dir / "capsules.json"
        assert gep_store.events_file == temp_dir / "events.jsonl"

    def test_save_and_load_genes(self, temp_dir: Path) -> None:
        gep_store = GEPStore(temp_dir)
        gene = Gene(id="test_gene", summary="Test gene", category="optimize", confidence=0.8)
        gene.calculate_asset_id()

        gep_store.save_gene(gene)
        loaded_gene = gep_store.get_gene("test_gene")

        assert loaded_gene is not None
        assert loaded_gene.id == "test_gene"
        assert loaded_gene.summary == "Test gene"
        assert loaded_gene.confidence == 0.8

    def test_save_and_load_capsules(self, temp_dir: Path) -> None:
        gep_store = GEPStore(temp_dir)
        capsule = Capsule(id="test_capsule", summary="Test capsule", genes_used=["gene1"])
        capsule.calculate_asset_id()

        gep_store.save_capsule(capsule)
        loaded_capsule = gep_store.get_capsule("test_capsule")

        assert loaded_capsule is not None
        assert loaded_capsule.id == "test_capsule"
        assert loaded_capsule.summary == "Test capsule"

    def test_append_and_get_events(self, temp_dir: Path) -> None:
        gep_store = GEPStore(temp_dir)

        event1 = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
            changes="Created gene 1",
        )

        event2 = Event(
            timestamp="2026-03-01T12:05:00Z",
            event_type="gene_created",
            asset_id="sha256:def456",
            changes="Created gene 2",
        )

        gep_store.append_event(event1)
        gep_store.append_event(event2)

        events = gep_store.get_events(limit=10)

        assert len(events) == 2
        assert events[0].changes == "Created gene 2"
        assert events[1].changes == "Created gene 1"

    def test_delete_gene(self, temp_dir: Path) -> None:
        gep_store = GEPStore(temp_dir)

        gene = Gene(id="test_gene", summary="Test gene")
        gep_store.save_gene(gene)

        result = gep_store.delete_gene("test_gene")

        assert result is True
        assert gep_store.get_gene("test_gene") is None

    def test_get_stats(self, temp_dir: Path) -> None:
        gep_store = GEPStore(temp_dir)

        gene = Gene(id="test_gene", summary="Test gene")
        capsule = Capsule(id="test_capsule", summary="Test capsule")
        event = Event(
            timestamp="2026-03-01T12:00:00Z",
            event_type="gene_created",
            asset_id="sha256:abc123",
        )

        gep_store.save_gene(gene)
        gep_store.save_capsule(capsule)
        gep_store.append_event(event)

        stats = gep_store.get_stats()

        assert stats["total_genes"] == 1
        assert stats["total_capsules"] == 1
        assert stats["total_events"] == 1
