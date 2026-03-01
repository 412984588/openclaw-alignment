#!/usr/bin/env python3
"""
奖励系统单元测试
"""

import pytest
import numpy as np
from lib.reward import RewardCalculator, RewardSignal


class TestRewardSignal:
    """测试RewardSignal类"""

    def test_collect_normalize(self):
        """测试信号收集和归一化"""
        signal = RewardSignal(
            name="test",
            weight=0.5,
            collector=lambda ctx: ctx.get("value", 0),
            min_value=0.0,
            max_value=10.0
        )

        # 测试中间值
        result = signal.collect({"value": 5.0})
        assert result == 0.5

        # 测试最大值
        result = signal.collect({"value": 10.0})
        assert result == 1.0

        # 测试最小值
        result = signal.collect({"value": 0.0})
        assert result == 0.0

        # 测试超出范围（截断）
        result = signal.collect({"value": 15.0})
        assert result == 1.0

        result = signal.collect({"value": -5.0})
        assert result == 0.0

    def test_history_tracking(self):
        """测试历史记录"""
        signal = RewardSignal(
            name="test",
            weight=0.5,
            collector=lambda ctx: ctx.get("value", 0),
            min_value=0.0,
            max_value=10.0
        )

        signal.collect({"value": 3.0})
        signal.collect({"value": 7.0})

        assert len(signal.history) == 2
        assert signal.history[0] == 0.3
        assert signal.history[1] == 0.7

    def test_update_weight(self):
        """测试权重更新"""
        signal = RewardSignal(
            name="test",
            weight=0.5,
            collector=lambda ctx: 0,
            min_value=0.0,
            max_value=1.0
        )

        signal.update_weight(0.1)
        assert signal.weight == 0.6

        signal.update_weight(-0.3)
        assert signal.weight == 0.3

        # 测试边界
        signal.update_weight(1.0)
        assert signal.weight == 1.0

        signal.update_weight(-2.0)
        assert signal.weight == 0.0


class TestRewardCalculator:
    """测试RewardCalculator类"""

    def test_initialization(self):
        """测试初始化"""
        calc = RewardCalculator()

        # 检查所有信号都已初始化
        expected_signals = [
            "test_coverage", "code_quality", "bug_count", "task_time",
            "acceptance_rate", "adoption_rate", "rewrite_rate",
            "user_rating", "feedback_count",
            "agent_preference", "workflow_preference"
        ]

        for signal_name in expected_signals:
            assert signal_name in calc.signals

    def test_calculate_reward(self):
        """测试奖励计算"""
        calc = RewardCalculator()

        context = {
            "task_type": "T2",
            "task_result": {
                "agent": "claude",
                "workflow": "tdd",
                "duration": 300,
                "test_files_created": True,
                "committed": True
            },
            "test_result": {
                "coverage": 80.0,
                "passed": 10,
                "failed": 0
            },
            "user_feedback": {
                "accepted": True,
                "rating": 5
            },
            "metrics": {
                "complexity": 3,
                "duplication": 0.05,
                "lint_score": 0.9
            }
        }

        reward = calc.calculate_reward(context)

        # 奖励应该在 [0, 1] 范围内
        assert 0.0 <= reward <= 1.0

        # 高质量任务应该有较高奖励
        assert reward > 0.5

    def test_weight_adjustment(self):
        """测试负向反馈后的权重调整"""
        calc = RewardCalculator()

        # 记录初始权重
        initial_weights = {
            name: signal.weight
            for name, signal in calc.signals.items()
        }

        # 记录负向反馈
        calc.record_feedback("rating", 2)

        # 检查权重已调整
        # 注意：由于归一化，我们检查相对变化而非绝对增减
        agent_auto_weights = ["agent_preference", "workflow_preference"]
        feedback_quality_weights = ["user_rating", "feedback_count", "code_quality", "test_coverage"]

        # 计算平均变化
        agent_auto_change = np.mean([
            (calc.signals[name].weight - initial_weights[name]) / initial_weights[name]
            for name in agent_auto_weights
        ])
        feedback_quality_change = np.mean([
            (calc.signals[name].weight - initial_weights[name]) / initial_weights[name]
            for name in feedback_quality_weights
        ])

        # 自动化权重的平均变化应该小于反馈/质量权重
        assert agent_auto_change < feedback_quality_change

    def test_weight_normalization(self):
        """测试权重归一化"""
        calc = RewardCalculator(learning_phase="early")
        total_weight = sum(signal.weight for signal in calc.signals.values())
        assert total_weight == pytest.approx(1.0, rel=1e-3)

    def test_negative_signals_reduce_reward(self):
        """测试负向信号对奖励的影响"""
        calc = RewardCalculator()

        base_context = {
            "task_result": {"duration": 100, "errors": 0},
            "test_result": {"coverage": 90.0, "failed": 0},
            "user_feedback": {"accepted": True, "rating": 5},
            "metrics": {"complexity": 2, "duplication": 0.0, "lint_score": 1.0}
        }

        high_bug_context = {
            "task_result": {"duration": 1000, "errors": 5},
            "test_result": {"coverage": 90.0, "failed": 5},
            "user_feedback": {"accepted": True, "rating": 5},
            "metrics": {"complexity": 2, "duplication": 0.0, "lint_score": 1.0}
        }

        reward_base = calc.calculate_reward(base_context)
        reward_high_bug = calc.calculate_reward(high_bug_context)

        assert reward_high_bug < reward_base

    def test_learning_phase_transition(self):
        """测试学习阶段转换"""
        calc = RewardCalculator(learning_phase="early")

        # 初始阶段应该是early
        assert calc.learning_phase == "early"

        # 模拟20个任务
        for i in range(20):
            context = {
                "task_result": {},
                "test_result": {},
                "user_feedback": {},
                "metrics": {}
            }
            calc.calculate_reward(context)

        # 应该转换为mature阶段
        assert calc.learning_phase == "mature"

    def test_reward_stats(self):
        """测试奖励统计"""
        calc = RewardCalculator()

        # 生成一些奖励数据
        for i in range(10):
            context = {
                "task_result": {"duration": 300},
                "test_result": {"coverage": 50 + i * 5},
                "user_feedback": {"accepted": True},
                "metrics": {}
            }
            calc.calculate_reward(context)

        stats = calc.get_reward_stats()

        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert stats["count"] == 10

    def test_signal_stats(self):
        """测试单个信号统计"""
        calc = RewardCalculator()

        # 生成一些数据
        for i in range(5):
            context = {
                "task_result": {},
                "test_result": {"coverage": 50 + i * 10},
                "user_feedback": {},
                "metrics": {}
            }
            calc.calculate_reward(context)

        stats = calc.get_signal_stats("test_coverage")

        assert stats["count"] == 5
        assert "mean" in stats
        assert "current_weight" in stats

    def test_save_load_state(self):
        """测试状态保存和加载"""
        import tempfile
        import os

        calc1 = RewardCalculator()

        # 生成一些数据
        for i in range(3):
            context = {
                "task_result": {"duration": 300},
                "test_result": {"coverage": 50 + i * 10},
                "user_feedback": {"rating": 4},
                "metrics": {}
            }
            calc1.calculate_reward(context)

        # 保存状态
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            calc1.save_state(temp_path)

            # 创建新的计算器并加载状态
            calc2 = RewardCalculator()
            calc2.load_state(temp_path)

            # 检查状态已恢复
            assert calc2.task_count == calc1.task_count
            assert len(calc2.reward_history) == len(calc1.reward_history)
            assert calc2.learning_phase == calc1.learning_phase

        finally:
            os.unlink(temp_path)


class TestRewardCollectors:
    """测试各个数据收集函数"""

    def test_collect_test_coverage(self):
        """测试测试覆盖率收集"""
        calc = RewardCalculator()

        # 有测试结果
        context = {
            "test_result": {"coverage": 85.0}
        }
        assert calc._collect_test_coverage(context) == 85.0

        # 无测试结果，但有创建测试文件
        context = {
            "task_result": {"test_files_created": True}
        }
        assert calc._collect_test_coverage(context) == 50.0

    def test_collect_code_quality(self):
        """测试代码质量收集"""
        calc = RewardCalculator()

        context = {
            "metrics": {
                "complexity": 3,
                "duplication": 0.1,
                "lint_score": 0.8
            }
        }

        quality = calc._collect_code_quality(context)

        # 应该在 [0, 10] 范围内
        assert 0.0 <= quality <= 10.0

        # 低复杂度、低重复、高lint应该得到高质量分
        assert quality > 5.0

    def test_collect_bug_count(self):
        """测试Bug数量收集"""
        calc = RewardCalculator()

        context = {
            "test_result": {"failed": 2},
            "task_result": {"errors": 1}
        }

        bugs = calc._collect_bug_count(context)
        assert bugs == 3

    def test_collect_task_time(self):
        """测试任务时间收集"""
        calc = RewardCalculator()

        context = {
            "task_result": {"duration": 600}
        }

        time = calc._collect_task_time(context)
        assert time == 600

    def test_collect_acceptance_rate(self):
        """测试接受率收集"""
        calc = RewardCalculator()

        # 接受
        context = {
            "user_feedback": {"accepted": True}
        }
        assert calc._collect_acceptance_rate(context) == 1.0

        # 拒绝
        context = {
            "user_feedback": {"accepted": False}
        }
        assert calc._collect_acceptance_rate(context) == 0.0

        # 有修改
        context = {
            "user_feedback": {"revisions": 3}
        }
        rate = calc._collect_acceptance_rate(context)
        assert rate < 1.0

    def test_collect_user_rating(self):
        """测试用户评分收集"""
        calc = RewardCalculator()

        # 显式评分
        context = {
            "user_feedback": {"rating": 5}
        }
        assert calc._collect_user_rating(context) == 5

        # 从acceptance推断
        context = {
            "user_feedback": {"accepted": True}
        }
        assert calc._collect_user_rating(context) == 4.0

    def test_collect_agent_preference(self):
        """测试Agent偏好收集"""
        calc = RewardCalculator()

        # T2任务使用Claude
        context = {
            "task_type": "T2",
            "task_result": {"agent": "claude"}
        }
        preference = calc._collect_agent_preference(context)
        assert preference > 0.5

        # T3任务使用Codex
        context = {
            "task_type": "T3",
            "task_result": {"agent": "codex"}
        }
        preference = calc._collect_agent_preference(context)
        assert preference > 0.5

    def test_collect_workflow_preference(self):
        """测试工作流偏好收集"""
        calc = RewardCalculator()

        # TDD工作流
        context = {
            "task_result": {"workflow": "tdd"}
        }
        preference = calc._collect_workflow_preference(context)
        assert preference > 0.8

        # 标准工作流
        context = {
            "task_result": {"workflow": "standard"}
        }
        preference = calc._collect_workflow_preference(context)
        assert preference < 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
