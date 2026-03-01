#!/usr/bin/env python3
"""Tests for the intelligent confirmation system."""

from __future__ import annotations

import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.confirmation import IntelligentConfirmation, RiskLevel
from lib.gep import Gene
from lib.gep_store import GEPStore


class TestIntelligentConfirmation:
    """Test intelligent confirmation decision logic."""

    @pytest.fixture
    def temp_gep_store(self):
        """Temporary GEP store fixture."""
        temp_dir = Path(tempfile.mkdtemp())
        gep_store = GEPStore(temp_dir)

        gene_high_conf = Gene(
            id="gene_test_high_conf",
            summary="Python optimization specialist",
            category="optimize",
            confidence=0.95,
            success_streak=10,
            trigger=["T2", "optimize", "python"],
        )
        gene_high_conf.calculate_asset_id()

        gene_low_conf = Gene(
            id="gene_test_low_conf",
            summary="Newbie test profile",
            category="repair",
            confidence=0.4,
            success_streak=1,
            trigger=["T1", "test"],
        )
        gene_low_conf.calculate_asset_id()

        gep_store.save_gene(gene_high_conf)
        gep_store.save_gene(gene_low_conf)

        yield gep_store

        if temp_dir.exists():
            rmtree(temp_dir)

    def test_assess_risk_low(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T1",
            "task_description": "Run format and lint checks",
            "command": "npm run format",
        }

        risk = conf_engine.assess_risk(task_context)
        assert risk == RiskLevel.LOW

    def test_assess_risk_high(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T3",
            "task_description": "Clean workspace directory",
            "command": "rm -rf workspace",
        }

        risk = conf_engine.assess_risk(task_context)
        assert risk == RiskLevel.CRITICAL

    def test_should_confirm_auto_execute_high_confidence(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
            "command": "python -m py_optimize",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is False
        assert "confidence" in reason.lower()

    def test_should_confirm_high_risk(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Delete test files",
            "command": "rm -rf tests/",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is True
        assert "risk" in reason.lower() or "critical" in reason.lower()

    def test_should_confirm_low_confidence(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T1",
            "task_description": "Run tests",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is True
        assert "insufficient" in reason.lower() or "first-time" in reason.lower()

    def test_get_confidence_info(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
        }

        confidence_info = conf_engine.get_confidence_info(task_context)

        assert confidence_info["max_confidence"] >= 0.9
        assert confidence_info["count"] > 0

    def test_record_feedback_user_cancelled(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
        }

        conf_engine.record_feedback(task_context, was_confirmed=True, user_cancelled=True)

        genes = temp_gep_store.load_genes()
        gene = genes.get("gene_test_high_conf")

        assert gene is not None
        assert gene.confidence < 0.95
        assert gene.success_streak == 0

    def test_record_feedback_auto_executed(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
        }

        original_confidence = temp_gep_store.get_gene("gene_test_high_conf").confidence

        conf_engine.record_feedback(task_context, was_confirmed=False, user_cancelled=False)

        genes = temp_gep_store.load_genes()
        gene = genes.get("gene_test_high_conf")

        assert gene is not None
        assert gene.confidence > original_confidence
        assert gene.success_streak == 11

    def test_get_explanation_auto_execute(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)
        explanation = conf_engine.get_explanation(task_context, should_confirm, reason)

        assert "auto-execute" in explanation.lower()
        assert "confidence" in explanation.lower() or "success" in explanation.lower()

    def test_get_explanation_need_confirm(self, temp_gep_store):
        conf_engine = IntelligentConfirmation(temp_gep_store)
        task_context = {
            "task_type": "T1",
            "task_description": "Delete files",
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)
        explanation = conf_engine.get_explanation(task_context, should_confirm, reason)

        assert "confirmation required" in explanation.lower()


class TestRiskAssessment:
    """Test risk assessment logic."""

    @pytest.fixture
    def conf_engine(self):
        return IntelligentConfirmation()

    def test_detect_critical_keywords(self, conf_engine):
        dangerous_tasks = [
            {"task_description": "Remove directory", "command": "rm -rf /data"},
            {"task_description": "Format disk", "command": "mkfs.ext4 /dev/sda1"},
            {"task_description": "Force push git", "command": "git push --force"},
        ]

        for task in dangerous_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.CRITICAL

    def test_detect_medium_keywords(self, conf_engine):
        medium_tasks = [
            {"task_description": "Update database schema"},
            {"task_description": "Make API request"},
            {"task_description": "Install dependencies"},
        ]

        for task in medium_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.MEDIUM

    def test_detect_low_keywords(self, conf_engine):
        low_tasks = [
            {"task_description": "Run tests"},
            {"task_description": "Check code format"},
            {"task_description": "List files"},
        ]

        for task in low_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.LOW
