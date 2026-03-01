#!/usr/bin/env python3
"""
强化学习奖励系统 - 四维度奖励计算

实现完整的奖励机制，包括：
- 客观指标（测试覆盖率、代码质量、Bug数量、任务时间）
- 用户行为信号（接受率、采用率、重写率）
- 显性反馈（用户评分、反馈次数）
- 行为模式（Agent偏好、工作流偏好）

支持动态权重调整和负向反馈策略调整
"""

import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class RewardSignal:
    """单个奖励信号"""
    name: str  # 信号名称
    weight: float  # 当前权重
    collector: Callable  # 数据收集函数
    history: List[float] = field(default_factory=list)  # 历史记录
    min_value: float = 0.0  # 最小值（用于归一化）
    max_value: float = 1.0  # 最大值（用于归一化）

    def collect(self, context: Dict[str, Any]) -> float:
        """收集并归一化信号值"""
        raw_value = self.collector(context)

        # 归一化到 [0, 1]
        if self.max_value > self.min_value:
            normalized = (raw_value - self.min_value) / (self.max_value - self.min_value)
        else:
            normalized = raw_value

        # 限制在 [0, 1] 范围内
        normalized = max(0.0, min(1.0, normalized))

        # 记录历史
        self.history.append(normalized)

        return normalized

    def update_weight(self, delta: float) -> None:
        """更新权重"""
        self.weight = max(0.0, min(1.0, self.weight + delta))


class RewardCalculator:
    """多维度奖励计算引擎

    实现四维度奖励系统：
    1. 客观指标（40%）: test_coverage(15%), code_quality(10%), bug_count(10%), task_time(5%)
    2. 用户行为（30%）: acceptance_rate(15%), adoption_rate(10%), rewrite_rate(5%)
    3. 显性反馈（20%）: user_rating(15%), feedback_count(5%)
    4. 行为模式（10%）: agent_preference(5%), workflow_preference(5%)
    """

    def __init__(self, learning_phase: str = "early"):
        """
        初始化奖励计算器

        Args:
            learning_phase: 学习阶段 ("early": 前10个任务, "mature": 20+个任务)
        """
        self.learning_phase = learning_phase
        self.task_count = 0

        # 初始化奖励信号
        self.signals: Dict[str, RewardSignal] = {}
        self._initialize_signals()

        # 负向反馈计数（用于策略调整）
        self.negative_feedback_count = 0

        # 奖励历史（用于训练）
        self.reward_history: List[float] = []

        # 负向信号集合（归一化后反转）
        self.negative_signals = {"bug_count", "task_time", "rewrite_rate"}

    def _initialize_signals(self) -> None:
        """初始化所有奖励信号"""

        # ===== 优先级1: 客观指标（40%） =====

        # 测试覆盖率（15%）
        self.signals["test_coverage"] = RewardSignal(
            name="test_coverage",
            weight=0.15,
            collector=lambda ctx: self._collect_test_coverage(ctx),
            min_value=0.0,
            max_value=100.0
        )

        # 代码质量（10%）
        self.signals["code_quality"] = RewardSignal(
            name="code_quality",
            weight=0.10,
            collector=lambda ctx: self._collect_code_quality(ctx),
            min_value=0.0,
            max_value=10.0
        )

        # Bug数量（10%）- 负向奖励
        self.signals["bug_count"] = RewardSignal(
            name="bug_count",
            weight=0.10,
            collector=lambda ctx: self._collect_bug_count(ctx),
            min_value=0.0,
            max_value=10.0  # 假设10个bug为最差情况
        )

        # 任务时间（5%）- 负向奖励（时间越长越差）
        self.signals["task_time"] = RewardSignal(
            name="task_time",
            weight=0.05,
            collector=lambda ctx: self._collect_task_time(ctx),
            min_value=0.0,
            max_value=3600.0  # 1小时为最差情况
        )

        # ===== 优先级2: 用户行为信号（30%） =====

        # 接受率（15%）
        self.signals["acceptance_rate"] = RewardSignal(
            name="acceptance_rate",
            weight=0.15,
            collector=lambda ctx: self._collect_acceptance_rate(ctx),
            min_value=0.0,
            max_value=1.0
        )

        # 采用率（10%）
        self.signals["adoption_rate"] = RewardSignal(
            name="adoption_rate",
            weight=0.10,
            collector=lambda ctx: self._collect_adoption_rate(ctx),
            min_value=0.0,
            max_value=1.0
        )

        # 重写率（5%）- 负向奖励
        self.signals["rewrite_rate"] = RewardSignal(
            name="rewrite_rate",
            weight=0.05,
            collector=lambda ctx: self._collect_rewrite_rate(ctx),
            min_value=0.0,
            max_value=1.0
        )

        # ===== 优先级3: 显性反馈（20%） =====

        # 用户评分（15%）
        self.signals["user_rating"] = RewardSignal(
            name="user_rating",
            weight=0.15,
            collector=lambda ctx: self._collect_user_rating(ctx),
            min_value=1.0,
            max_value=5.0
        )

        # 反馈次数（5%）
        self.signals["feedback_count"] = RewardSignal(
            name="feedback_count",
            weight=0.05,
            collector=lambda ctx: self._collect_feedback_count(ctx),
            min_value=0.0,
            max_value=10.0  # 假设10次反馈为最好情况
        )

        # ===== 优先级4: 行为模式（10%） =====

        # Agent偏好（5%）
        self.signals["agent_preference"] = RewardSignal(
            name="agent_preference",
            weight=0.05,
            collector=lambda ctx: self._collect_agent_preference(ctx),
            min_value=0.0,
            max_value=1.0
        )

        # 工作流偏好（5%）
        self.signals["workflow_preference"] = RewardSignal(
            name="workflow_preference",
            weight=0.05,
            collector=lambda ctx: self._collect_workflow_preference(ctx),
            min_value=0.0,
            max_value=1.0
        )

        # 根据学习阶段调整权重
        self._adjust_weights_for_phase()

    def _adjust_weights_for_phase(self) -> None:
        """根据学习阶段调整权重

        早期阶段（前10个任务）：70%即时奖励 + 30%长期优化
        成熟阶段（20+个任务）：30%即时奖励 + 70%长期优化
        """
        if self.learning_phase == "early":
            # 早期：更关注即时反馈（用户行为、显性反馈）
            self.signals["acceptance_rate"].weight *= 1.5
            self.signals["adoption_rate"].weight *= 1.3
            self.signals["user_rating"].weight *= 1.5
        else:
            # 成熟：更关注长期优化（客观指标、行为模式）
            self.signals["test_coverage"].weight *= 1.5
            self.signals["code_quality"].weight *= 1.3
            self.signals["agent_preference"].weight *= 1.5
            self.signals["workflow_preference"].weight *= 1.3

        self._normalize_weights()

    def _normalize_weights(self) -> None:
        """归一化权重，确保总和为1"""
        total_weight = sum(s.weight for s in self.signals.values())
        if total_weight == 0:
            return
        for signal in self.signals.values():
            signal.weight /= total_weight

    def calculate_reward(self, context: Dict[str, Any]) -> float:
        """
        计算加权总奖励

        Args:
            context: 任务上下文，包含：
                - task_result: 任务执行结果
                - test_result: 测试结果（可选）
                - user_feedback: 用户反馈（可选）
                - metrics: 其他指标

        Returns:
            总奖励值（归一化到 [0, 1]）
        """
        total_reward = 0.0
        reward_breakdown = {}

        # 收集每个信号的奖励
        for name, signal in self.signals.items():
            signal_value = signal.collect(context)
            if name in self.negative_signals:
                signal_value = 1.0 - signal_value
            weighted_value = signal_value * signal.weight

            total_reward += weighted_value
            reward_breakdown[name] = {
                "value": signal_value,
                "weight": signal.weight,
                "weighted": weighted_value
            }

        # 记录历史
        self.reward_history.append(total_reward)
        self.task_count += 1

        # 检查是否需要更新学习阶段
        self._update_learning_phase()

        # 记录奖励明细（用于调试）
        if "debug_info" not in context:
            context["debug_info"] = {}
        context["debug_info"]["reward_breakdown"] = reward_breakdown
        context["debug_info"]["total_reward"] = total_reward

        return max(0.0, min(1.0, total_reward))

    def record_feedback(self, feedback_type: str, value: Any) -> None:
        """
        记录用户显性反馈

        Args:
            feedback_type: 反馈类型 ("rating", "comment", "correction")
            value: 反馈值（评分、评论内容等）
        """
        if feedback_type == "rating":
            # 用户评分（1-5）
            if isinstance(value, (int, float)) and 1 <= value <= 5:
                # 评分是显性正向/负向反馈
                if value <= 2:
                    self.negative_feedback_count += 1
                    self._adjust_weights_on_negative_feedback()
        elif feedback_type == "correction":
            # 用户修正（负向反馈）
            self.negative_feedback_count += 1
            self._adjust_weights_on_negative_feedback()

    def _adjust_weights_on_negative_feedback(self) -> None:
        """负向反馈时调整策略权重

        当收到负向反馈时：
        1. 降低自动化权重（agent_preference, workflow_preference）
        2. 提高用户反馈权重（user_rating, feedback_count）
        3. 提高代码质量权重（code_quality, test_coverage）
        """
        # 降低自动化权重
        self.signals["agent_preference"].weight *= 0.8
        self.signals["workflow_preference"].weight *= 0.8

        # 提高用户反馈和代码质量权重
        self.signals["user_rating"].weight *= 1.3
        self.signals["feedback_count"].weight *= 1.2
        self.signals["code_quality"].weight *= 1.2
        self.signals["test_coverage"].weight *= 1.2

        # 重新归一化权重（保持总和为1）
        total_weight = sum(s.weight for s in self.signals.values())
        for signal in self.signals.values():
            signal.weight /= total_weight

    def _update_learning_phase(self) -> None:
        """更新学习阶段"""
        if self.task_count >= 20 and self.learning_phase == "early":
            self.learning_phase = "mature"
            # 重新调整权重
            self._adjust_weights_for_phase()

    # ===== 数据收集函数 =====

    def _collect_test_coverage(self, context: Dict[str, Any]) -> float:
        """收集测试覆盖率（0-100）"""
        test_result = context.get("test_result", {})
        coverage = test_result.get("coverage", 0.0)

        # 如果没有测试结果，从task_result推断
        if coverage == 0:
            task_result = context.get("task_result", {})
            # 检查是否创建了测试文件
            if "test_files_created" in task_result:
                coverage = 50.0  # 假设创建测试文件 = 50%覆盖
            if "tests_passed" in task_result:
                coverage = min(coverage + 30.0, 100.0)

        return coverage

    def _collect_code_quality(self, context: Dict[str, Any]) -> float:
        """收集代码质量评分（0-10）"""
        metrics = context.get("metrics", {})

        # 综合多个质量指标
        quality_score = 5.0  # 基础分

        # 代码复杂度（越低越好）
        complexity = metrics.get("complexity", 5)
        quality_score += (10 - complexity) * 0.3

        # 代码重复率（越低越好）
        duplication = metrics.get("duplication", 0.1)
        quality_score += (1.0 - duplication) * 2.0

        # 代码风格检查
        lint_score = metrics.get("lint_score", 0.8)
        quality_score += lint_score * 1.5

        return max(0.0, min(10.0, quality_score))

    def _collect_bug_count(self, context: Dict[str, Any]) -> float:
        """收集Bug数量（负向奖励）"""
        test_result = context.get("test_result", {})
        failed_tests = test_result.get("failed", 0)

        # 也要考虑task_result中的错误
        task_result = context.get("task_result", {})
        errors = task_result.get("errors", 0)

        total_bugs = failed_tests + errors

        # 转换为负向奖励（bug越多，奖励越低）
        return total_bugs

    def _collect_task_time(self, context: Dict[str, Any]) -> float:
        """收集任务完成时间（负向奖励，秒）"""
        task_result = context.get("task_result", {})
        duration = task_result.get("duration", 0)

        return duration

    def _collect_acceptance_rate(self, context: Dict[str, Any]) -> float:
        """收集接受率（0-1）"""
        user_feedback = context.get("user_feedback", {})

        # 首先检查是否有明确的accepted字段
        if "accepted" in user_feedback:
            return 1.0 if user_feedback["accepted"] else 0.0

        # 如果没有明确accepted，检查revisions来推断
        if "revisions" in user_feedback:
            # 修改次数越多，接受率越低
            revisions = user_feedback["revisions"]
            return max(0.0, 1.0 - revisions * 0.2)

        # 默认接受
        return 1.0

    def _collect_adoption_rate(self, context: Dict[str, Any]) -> float:
        """收集采用率（0-1）"""
        task_result = context.get("task_result", {})

        # 检查生成的代码是否被使用
        if "code_adoption" in task_result:
            return task_result["code_adoption"]

        # 检查是否commit了
        if "committed" in task_result:
            return 1.0 if task_result["committed"] else 0.0

        # 默认采用
        return 1.0

    def _collect_rewrite_rate(self, context: Dict[str, Any]) -> float:
        """收集重写率（负向奖励，0-1）"""
        user_feedback = context.get("user_feedback", {})

        # 检查是否有大量重写
        if "rewrite_percentage" in user_feedback:
            return user_feedback["rewrite_percentage"]

        # 检查修改次数
        if "revisions" in user_feedback:
            revisions = user_feedback["revisions"]
            # 假设3次以上修改表示大量重写
            return min(1.0, revisions / 3.0)

        return 0.0

    def _collect_user_rating(self, context: Dict[str, Any]) -> float:
        """收集用户评分（1-5）"""
        user_feedback = context.get("user_feedback", {})

        if "rating" in user_feedback:
            return user_feedback["rating"]

        # 如果没有显式评分，从acceptance推断
        acceptance = self._collect_acceptance_rate(context)
        if acceptance == 1.0:
            return 4.0  # 接受 = 4分
        else:
            return 2.0  # 拒绝 = 2分

    def _collect_feedback_count(self, context: Dict[str, Any]) -> float:
        """收集反馈次数"""
        user_feedback = context.get("user_feedback", {})

        count = 0

        # 正向反馈
        if user_feedback.get("positive_comments"):
            count += len(user_feedback["positive_comments"])

        # 负向反馈
        if user_feedback.get("negative_comments"):
            count += len(user_feedback["negative_comments"])

        return count

    def _collect_agent_preference(self, context: Dict[str, Any]) -> float:
        """收集Agent选择偏好（0-1）"""
        task_result = context.get("task_result", {})
        used_agent = task_result.get("agent", "claude")

        # 从历史中学习偏好
        # TODO: 需要从learner中获取历史Agent使用情况
        # 这里简化为：如果使用的Agent与任务类型匹配，则奖励高
        task_type = context.get("task_type", "T2")

        # 简单的匹配规则
        preference_match = {
            ("T1", "claude"): 0.9,
            ("T2", "claude"): 0.8,
            ("T3", "codex"): 0.9,
            ("T4", "codex"): 0.95,
        }

        return preference_match.get((task_type, used_agent), 0.5)

    def _collect_workflow_preference(self, context: Dict[str, Any]) -> float:
        """收集工作流偏好（0-1）"""
        task_result = context.get("task_result", {})
        workflow = task_result.get("workflow", "standard")

        # 从历史中学习工作流偏好
        # TODO: 需要从learner中获取历史工作流使用情况
        # 这里简化为：TDD工作流奖励更高
        if workflow == "tdd":
            return 0.9
        elif workflow == "test_first":
            return 0.85
        else:
            return 0.6

    # ===== 工具方法 =====

    def get_reward_stats(self) -> Dict[str, Any]:
        """获取奖励统计信息"""
        if not self.reward_history:
            return {}

        rewards = np.array(self.reward_history)

        return {
            "mean": float(np.mean(rewards)),
            "std": float(np.std(rewards)),
            "min": float(np.min(rewards)),
            "max": float(np.max(rewards)),
            "latest": float(rewards[-1]),
            "count": len(rewards)
        }

    def get_signal_stats(self, signal_name: str) -> Dict[str, Any]:
        """获取单个信号的统计信息"""
        if signal_name not in self.signals:
            return {}

        signal = self.signals[signal_name]

        if not signal.history:
            return {}

        history = np.array(signal.history)

        return {
            "mean": float(np.mean(history)),
            "std": float(np.std(history)),
            "min": float(np.min(history)),
            "max": float(np.max(history)),
            "latest": float(history[-1]),
            "count": len(history),
            "current_weight": signal.weight
        }

    def save_state(self, path: str) -> None:
        """保存奖励计算器状态"""
        state = {
            "learning_phase": self.learning_phase,
            "task_count": self.task_count,
            "negative_feedback_count": self.negative_feedback_count,
            "reward_history": self.reward_history,
            "signals": {
                name: {
                    "weight": signal.weight,
                    "history": signal.history
                }
                for name, signal in self.signals.items()
            }
        }

        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: str) -> None:
        """加载奖励计算器状态"""
        path = Path(path).expanduser()

        if not path.exists():
            return

        with open(path, 'r') as f:
            state = json.load(f)

        self.learning_phase = state.get("learning_phase", "early")
        self.task_count = state.get("task_count", 0)
        self.negative_feedback_count = state.get("negative_feedback_count", 0)
        self.reward_history = state.get("reward_history", [])

        # 恢复信号状态
        for name, signal_state in state.get("signals", {}).items():
            if name in self.signals:
                self.signals[name].weight = signal_state.get("weight", self.signals[name].weight)
                self.signals[name].history = signal_state.get("history", [])


def main():
    """测试奖励计算器"""
    # 创建奖励计算器
    calculator = RewardCalculator(learning_phase="early")

    # 模拟任务上下文
    context = {
        "task_type": "T2",
        "task_result": {
            "agent": "claude",
            "workflow": "tdd",
            "duration": 300,  # 5分钟
            "test_files_created": True,
            "tests_passed": True,
            "committed": True,
            "code_adoption": 0.9
        },
        "test_result": {
            "coverage": 85.0,
            "passed": 10,
            "failed": 1
        },
        "user_feedback": {
            "accepted": True,
            "rating": 4,
            "positive_comments": ["很好", "有帮助"],
            "revisions": 1
        },
        "metrics": {
            "complexity": 3,
            "duplication": 0.05,
            "lint_score": 0.9
        }
    }

    # 计算奖励
    reward = calculator.calculate_reward(context)

    print(f"总奖励: {reward:.3f}")
    print(f"\n奖励明细:")
    for name, detail in context["debug_info"]["reward_breakdown"].items():
        print(f"  {name}: {detail['value']:.3f} × {detail['weight']:.2f} = {detail['weighted']:.3f}")

    print(f"\n奖励统计:")
    stats = calculator.get_reward_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 模拟负向反馈
    print(f"\n记录负向反馈...")
    calculator.record_feedback("rating", 2)

    print(f"调整后的权重:")
    for name, signal in calculator.signals.items():
        print(f"  {name}: {signal.weight:.3f}")


if __name__ == "__main__":
    main()
