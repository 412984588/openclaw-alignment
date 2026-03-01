#!/usr/bin/env python3
"""
智能确认系统测试

测试基于 GEP confidence 和风险评估的智能确认决策。
"""

import tempfile
from pathlib import Path
from shutil import rmtree

import pytest

from lib.confirmation import IntelligentConfirmation, RiskLevel
from lib.gep import Gene, Event
from lib.gep_store import GEPStore


class TestIntelligentConfirmation:
    """测试智能确认决策引擎"""

    @pytest.fixture
    def temp_gep_store(self):
        """临时 GEP Store fixture"""
        temp_dir = Path(tempfile.mkdtemp())
        gep_store = GEPStore(temp_dir)

        # 创建测试 Gene
        gene_high_conf = Gene(
            id="gene_test_high_conf",
            summary="Python 优化专家",
            category="optimize",
            confidence=0.95,
            success_streak=10,
            trigger=["T2", "optimize", "python"]
        )
        gene_high_conf.calculate_asset_id()

        gene_low_conf = Gene(
            id="gene_test_low_conf",
            summary="新手测试",
            category="repair",
            confidence=0.4,
            success_streak=1,
            trigger=["T1", "test"]
        )
        gene_low_conf.calculate_asset_id()

        gep_store.save_gene(gene_high_conf)
        gep_store.save_gene(gene_low_conf)

        yield gep_store

        # 清理
        if temp_dir.exists():
            rmtree(temp_dir)

    def test_assess_risk_low(self, temp_gep_store):
        """测试低风险评估"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T1",
            "task_description": "Run format and lint checks",
            "command": "npm run format"
        }

        risk = conf_engine.assess_risk(task_context)
        assert risk == RiskLevel.LOW

    def test_assess_risk_high(self, temp_gep_store):
        """测试高风险评估"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T3",
            "task_description": "Clean workspace directory",
            "command": "rm -rf workspace"
        }

        risk = conf_engine.assess_risk(task_context)
        assert risk == RiskLevel.CRITICAL

    def test_should_confirm_auto_execute_high_confidence(self, temp_gep_store):
        """测试高信心 + 低风险 = 自动执行"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code",
            "command": "python -m py_optimize"
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is False  # 不需要确认
        assert "自动执行" in reason

    def test_should_confirm_high_risk(self, temp_gep_store):
        """测试高风险操作 = 必须确认"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T2",
            "task_description": "Delete test files",
            "command": "rm -rf tests/"
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        assert should_confirm is True  # 需要确认
        assert "高风险" in reason or "CRITICAL" in reason

    def test_should_confirm_low_confidence(self, temp_gep_store):
        """测试低信心 = 需要确认"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T1",
            "task_description": "Run tests"
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)

        # 首次执行，信心度低
        assert should_confirm is True
        assert "信心度不足" in reason or "首次" in reason

    def test_get_confidence_info(self, temp_gep_store):
        """测试获取 confidence 信息"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code"
        }

        confidence_info = conf_engine.get_confidence_info(task_context)

        assert confidence_info["max_confidence"] >= 0.9
        assert confidence_info["count"] > 0

    def test_record_feedback_user_cancelled(self, temp_gep_store):
        """测试记录用户撤销反馈"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code"
        }

        # 记录用户撤销
        conf_engine.record_feedback(
            task_context,
            was_confirmed=True,
            user_cancelled=True
        )

        # 验证 confidence 降低
        genes = temp_gep_store.load_genes()
        gene = genes.get("gene_test_high_conf")

        assert gene is not None
        assert gene.confidence < 0.95  # confidence 降低
        assert gene.success_streak == 0  # 成功次数清零

    def test_record_feedback_auto_executed(self, temp_gep_store):
        """测试记录自动执行成功反馈"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code"
        }

        # 记录自动执行成功
        original_confidence = temp_gep_store.get_gene("gene_test_high_conf").confidence

        conf_engine.record_feedback(
            task_context,
            was_confirmed=False,
            user_cancelled=False
        )

        # 验证 confidence 提升
        genes = temp_gep_store.load_genes()
        gene = genes.get("gene_test_high_conf")

        assert gene is not None
        assert gene.confidence > original_confidence  # confidence 提升
        assert gene.success_streak == 11  # 成功次数增加

    def test_get_explanation_auto_execute(self, temp_gep_store):
        """测试自动执行的说明"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T2",
            "task_description": "Optimize Python code"
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)
        explanation = conf_engine.get_explanation(task_context, should_confirm, reason)

        assert "自动执行" in explanation
        assert "信心度" in explanation or "成功" in explanation

    def test_get_explanation_need_confirm(self, temp_gep_store):
        """测试需要确认的说明"""
        conf_engine = IntelligentConfirmation(temp_gep_store)

        task_context = {
            "task_type": "T1",
            "task_description": "Delete files"
        }

        should_confirm, reason = conf_engine.should_confirm(task_context)
        explanation = conf_engine.get_explanation(task_context, should_confirm, reason)

        assert "需要确认" in explanation


class TestRiskAssessment:
    """测试风险评估逻辑"""

    @pytest.fixture
    def conf_engine(self):
        """确认引擎 fixture"""
        return IntelligentConfirmation()

    def test_detect_critical_keywords(self, conf_engine):
        """测试检测危险关键词"""
        dangerous_tasks = [
            {"task_description": "Remove directory", "command": "rm -rf /data"},
            {"task_description": "Format disk", "command": "mkfs.ext4 /dev/sda1"},
            {"task_description": "Force push git", "command": "git push --force"}
        ]

        for task in dangerous_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.CRITICAL

    def test_detect_medium_keywords(self, conf_engine):
        """测试检测中风险关键词"""
        medium_tasks = [
            {"task_description": "Update database schema"},
            {"task_description": "Make API request"},
            {"task_description": "Install dependencies"}
        ]

        for task in medium_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.MEDIUM

    def test_detect_low_keywords(self, conf_engine):
        """测试检测低风险关键词"""
        low_tasks = [
            {"task_description": "Run tests"},
            {"task_description": "Check code format"},
            {"task_description": "List files"}
        ]

        for task in low_tasks:
            risk = conf_engine.assess_risk(task)
            assert risk == RiskLevel.LOW
