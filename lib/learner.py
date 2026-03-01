#!/usr/bin/env python3
"""
学习模块 - 从收集的数据中学习用户偏好

支持两种学习模式：
1. PreferenceLearner: 统计学习（Git历史频率分析）
2. RLLearner: 强化学习（Actor-Critic在线学习）
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from .agent import AlignmentAgent, Trajectory
from .environment import InteractionEnvironment, State, Action
from .paths import resolve_config_path, resolve_model_dir


class PreferenceLearner:
    """偏好学习算法"""

    def __init__(self, config_path: str = None):
        self.config_path = str(resolve_config_path(config_path))
        self.learned_preferences = {}

    def learn_from_git_history(self, git_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Git历史学习偏好"""
        print("\n🧠 正在学习偏好...")

        # 学习技术栈偏好
        tech_preferences = self._learn_tech_stack(git_data["tech_stack"])

        # 学习工作流偏好
        workflow_preferences = self._learn_workflow(git_data["workflow"])

        # 组合学习结果
        self.learned_preferences = {
            "tech_stack": tech_preferences,
            "workflow": workflow_preferences,
            "metadata": {
                "last_updated": git_data.get("metadata", {}).get("collected_at", "unknown"),
                "confidence": git_data.get("metadata", {}).get("confidence", 0.5),
                "data_source": "git_history"
            }
        }

        print(f"✅ 学习完成！置信度: {self.learned_preferences['metadata']['confidence']*100}%")
        return self.learned_preferences

    def _learn_tech_stack(self, tech_stack: Dict[str, int]) -> Dict[str, Any]:
        """学习技术栈偏好"""
        total = sum(tech_stack.values())

        if total == 0:
            return {"primary": "unknown", "stats": {}}

        # 找出最常用的技术
        sorted_tech = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)

        # 主要技术栈（前3名）
        primary = sorted_tech[0][0] if sorted_tech else "unknown"
        secondary = sorted_tech[1][0] if len(sorted_tech) > 1 else None
        tertiary = sorted_tech[2][0] if len(sorted_tech) > 2 else None

        # 计算占比
        stats = {
            tech: {
                "count": count,
                "percentage": round(count / total * 100, 1)
            }
            for tech, count in sorted_tech[:5] if count > 0
        }

        return {
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "stats": stats,
            "total_samples": total
        }

    def _learn_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """学习工作流偏好"""
        preferences = {
            "test_driven": workflow.get("test_first", False),
            "test_ratio": workflow.get("test_ratio", 0),
            "automation_level": "balanced"
        }

        # 根据测试比例推断自动化偏好
        if preferences["test_ratio"] > 0.5:
            preferences["automation_level"] = "quality_focused"
        elif preferences["test_ratio"] < 0.2:
            preferences["automation_level"] = "speed_focused"

        return preferences

    def save_preferences(self, output_path: str = None) -> None:
        """保存学习结果到配置文件"""
        output_path = output_path or self.config_path
        output_path = Path(output_path).expanduser()

        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有配置
        if output_path.exists():
            with open(output_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"version": "1.0.0"}

        # 更新配置
        config.update({
            "learned_preferences": self.learned_preferences,
            "last_updated": self.learned_preferences["metadata"]["last_updated"]
        })

        # 保存配置
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ 偏好已保存到: {output_path}")

    def generate_report(self) -> str:
        """生成学习报告"""
        if not self.learned_preferences:
            return "❌ 还没有学习任何偏好"

        tech = self.learned_preferences.get("tech_stack", {})
        workflow = self.learned_preferences.get("workflow", {})
        metadata = self.learned_preferences.get("metadata", {})

        report = f"""
# 意图对齐学习报告

## 📊 技术栈偏好

主要技术: **{tech.get('primary', 'unknown')}** (占比{tech.get('stats', {}).get(tech.get('primary', ''), {}).get('percentage', 0)}%)
次要技术: {tech.get('secondary', '无')}
第三选择: {tech.get('tertiary', '无')}

详细统计:
"""

        for tech_name, stats in tech.get("stats", {}).items():
            report += f"- {tech_name}: {stats['count']}次 ({stats['percentage']}%)\n"

        report += f"""
## 🔄 工作流偏好

测试驱动: {'✅ 是' if workflow.get('test_driven') else '❌ 否'}
自动化偏好: {workflow.get('automation_level', 'balanced')}
测试占比: {workflow.get('test_ratio', 0)*100:.0f}%

## 📈 元数据

置信度: {metadata.get('confidence', 0)*100:.0f}%
数据来源: {metadata.get('data_source', 'unknown')}
更新时间: {metadata.get('last_updated', 'unknown')}

---

💡 **建议**:
- 主要使用 {tech.get('primary', 'unknown')} 进行开发
- {'采用测试驱动开发' if workflow.get('test_driven') else '考虑增加测试覆盖率'}
- 保持当前{'的质量优先' if workflow.get('automation_level') == 'quality_focused' else '速度优先'}风格
"""

        return report


class RLLearner:
    """
    强化学习学习器 - 在线学习

    从任务执行中实时学习，使用Actor-Critic算法优化策略
    """

    def __init__(self, model_path: str = None, config_path: str = None):
        """
        初始化RL学习器

        Args:
            model_path: 模型保存路径
            config_path: 配置文件路径
        """
        self.model_path = str(resolve_model_dir(model_path))
        self.config_path = str(resolve_config_path(config_path))

        # 初始化环境和智能体
        self.env = InteractionEnvironment(config_path=self.config_path)

        self.agent = AlignmentAgent(
            state_dim=self.env.get_state_space_size(),
            action_dim=self.env.get_action_space_size()
        )

        # 尝试加载已有模型
        self._load_model()

        # 当前轨迹
        self.current_trajectory: Optional[Trajectory] = None

        # 历史偏好统计（task_type + 选择维度）
        self._agent_reward_history: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self._workflow_reward_history: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        # 契约：奖励系统优先读取学习器历史
        self.env.reward_calculator.set_history_provider(self)

    def _load_model(self) -> None:
        """加载已有模型"""
        model_dir = Path(self.model_path).expanduser()
        if model_dir.exists():
            try:
                self.agent.load_model(str(model_dir))
                print(f"✅ 已加载模型: {model_dir}")
            except Exception as e:
                print(f"⚠️  加载模型失败: {e}，使用新模型")

    def learn_from_task(self, task_context: Dict[str, Any],
                       task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        从单个任务中学习（在线学习）

        Args:
            task_context: 任务上下文
            task_result: 任务执行结果

        Returns:
            学习统计信息
        """
        # 1. 重置环境
        state = self.env.reset(task_context)

        # 2. 选择动作（使用当前策略）
        action = self.agent.select_action(state, explore=False)

        # 3. 执行动作，获得反馈
        next_state, reward, done, info = self.env.step(action, task_result)

        # 4. 构建单步轨迹
        trajectory = Trajectory(
            states=[state.to_vector()],
            actions=[self.agent.encode_action_indices(action)],
            rewards=[reward],
            dones=[done],
            next_states=[next_state.to_vector()]
        )

        # 4.1 记录偏好历史（用于后续奖励计算）
        self.record_preference_result(
            task_type=task_context.get("task_type", "T2"),
            agent=action.agent_selection.value,
            workflow=task_result.get("workflow", "standard"),
            reward=reward,
        )

        # 5. 更新策略
        stats = self.agent.update_policy(trajectory)

        # 6. 定期保存模型
        if self.agent.episode_count % 10 == 0:
            self.save_model()

        return {
            "reward": reward,
            "action_taken": str(action),
            "agent_used": action.agent_selection.value,
            **stats
        }

    def get_recommended_action(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取推荐动作（不更新策略）

        Args:
            task_context: 任务上下文

        Returns:
            推荐的动作
        """
        # 重置环境
        state = self.env.reset(task_context)

        # 选择动作（不探索）
        action = self.agent.select_action(state, explore=False)

        return {
            "agent": action.agent_selection.value,
            "automation_level": action.automation_level.value,
            "communication_style": action.communication_style.value,
            "confirmation_needed": action.confirmation_needed,
            "confidence": 0.7 + self.env.recent_performance * 0.3  # 基于性能的置信度
        }

    def save_model(self) -> None:
        """保存模型"""
        self.agent.save_model(self.model_path)
        self.env.save_history(f"{self.model_path}/env_history.json")
        print(f"✅ 模型已保存: {self.model_path}")

    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计"""
        return {
            "episode_count": self.agent.episode_count,
            "total_steps": self.agent.total_steps,
            "recent_performance": self.env.recent_performance,
            "agent_usage": self.env.agent_usage_history
        }

    def record_preference_result(self, task_type: str, agent: str, workflow: str, reward: float) -> None:
        """记录任务结果到偏好历史"""
        reward_clipped = max(0.0, min(1.0, float(reward)))
        self._agent_reward_history[(task_type, agent)].append(reward_clipped)
        self._workflow_reward_history[(task_type, workflow)].append(reward_clipped)

    def get_agent_success_rate(self, task_type: str, agent: str) -> Optional[float]:
        """提供Agent历史成功率（奖励均值）"""
        rewards = self._agent_reward_history.get((task_type, agent))
        if not rewards:
            return None
        return float(sum(rewards) / len(rewards))

    def get_workflow_success_rate(self, task_type: str, workflow: str) -> Optional[float]:
        """提供工作流历史成功率（奖励均值）"""
        rewards = self._workflow_reward_history.get((task_type, workflow))
        if not rewards:
            return None
        return float(sum(rewards) / len(rewards))


def main():
    """测试学习算法"""
    # 模拟Git数据
    git_data = {
        "tech_stack": {
            "python": 45,
            "javascript": 12,
            "react": 38,
            "vue": 3,
            "fastapi": 25
        },
        "file_types": {
            ".py": 45,
            ".js": 8,
            ".jsx": 12,
            ".ts": 4
        },
        "workflow": {
            "test_first": True,
            "test_ratio": 0.35
        },
        "metadata": {
            "collected_at": "2026-02-28T18:30:00Z",
            "confidence": 0.85
        }
    }

    # 学习偏好
    learner = PreferenceLearner()
    preferences = learner.learn_from_git_history(git_data)

    # 生成报告
    report = learner.generate_report()
    print(report)

    # 保存到配置
    # learner.save_preferences()


if __name__ == "__main__":
    main()
