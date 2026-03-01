#!/usr/bin/env python3
"""
强化学习交互环境 - OpenClaw交互环境

定义状态空间和动作空间，实现OpenClaw交互的OpenAI Gym风格接口：
- state: 任务上下文（task_type, tech_stack, user_mood等）
- action: Agent选择（agent_selection, automation_level等）
- reward: 从reward.RewardCalculator计算
- done: 任务是否完成

支持：
- reset(task_context): 重置环境到新任务
- step(action): 执行动作 → (next_state, reward, done, info)
- _encode_state(context): 将上下文编码为状态向量
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from .reward import RewardCalculator


class TaskType(Enum):
    """任务类型枚举"""
    T1 = "T1"  # 轻量：<20行
    T2 = "T2"  # 中等：20-200行
    T3 = "T3"  # 重度：200+行
    T4 = "T4"  # 危险：核心系统


class AgentType(Enum):
    """Agent类型枚举"""
    CLAUDE = "claude"
    CODEX = "codex"
    GEMINI = "gemini"


class AutomationLevel(Enum):
    """自动化级别枚举"""
    LOW = "low"  # 需要频繁确认
    MEDIUM = "medium"  # 部分自动化
    HIGH = "high"  # 高度自动化


class CommunicationStyle(Enum):
    """沟通风格枚举"""
    BRIEF = "brief"  # 简洁
    DETAILED = "detailed"  # 详细
    INTERACTIVE = "interactive"  # 交互式


@dataclass
class State:
    """状态数据类"""
    # 任务类型（one-hot编码）
    task_type: np.ndarray  # [4] (T1, T2, T3, T4)

    # 技术栈（one-hot编码）
    tech_stack: np.ndarray  # [N] 根据支持的技术数量

    # 用户心情（one-hot编码）
    user_mood: np.ndarray  # [3] (focused, relaxed, stressed)

    # 时间（归一化0-1）
    time_of_day: float  # 0-1 (0=midnight, 0.5=noon, 1=midnight)

    # 近期性能（归一化0-1）
    recent_performance: float  # 0-1

    # 历史Agent使用（统计）
    agent_usage_history: Dict[str, int]  # agent名称 -> 使用次数

    def to_vector(self) -> np.ndarray:
        """将状态转换为向量"""
        # 组合所有特征
        vectors = [
            self.task_type.flatten(),
            self.tech_stack.flatten(),
            self.user_mood.flatten(),
            [self.time_of_day],
            [self.recent_performance]
        ]

        return np.concatenate(vectors)

    def __repr__(self) -> str:
        return (f"State(task_type={self.task_type}, "
                f"tech_stack={self.tech_stack}, "
                f"user_mood={self.user_mood}, "
                f"time={self.time_of_day:.2f}, "
                f"perf={self.recent_performance:.2f})")


@dataclass
class Action:
    """动作数据类"""
    agent_selection: AgentType  # 选择哪个Agent
    automation_level: AutomationLevel  # 自动化级别
    communication_style: CommunicationStyle  # 沟通风格
    confirmation_needed: bool  # 是否需要确认

    def to_vector(self, agent_map: Dict[AgentType, int],
                  automation_map: Dict[AutomationLevel, int],
                  style_map: Dict[CommunicationStyle, int]) -> np.ndarray:
        """将动作转换为one-hot编码向量"""
        vector_size = (
            len(agent_map) +
            len(automation_map) +
            len(style_map) +
            1  # confirmation_needed
        )

        vector = np.zeros(vector_size)

        # Agent选择（one-hot）
        vector[agent_map[self.agent_selection]] = 1

        # 自动化级别（one-hot）
        offset = len(agent_map)
        vector[offset + automation_map[self.automation_level]] = 1

        # 沟通风格（one-hot）
        offset += len(automation_map)
        vector[offset + style_map[self.communication_style]] = 1

        # 确认标志
        offset += len(style_map)
        vector[offset] = 1.0 if self.confirmation_needed else 0.0

        return vector

    def __repr__(self) -> str:
        return (f"Action(agent={self.agent_selection.value}, "
                f"automation={self.automation_level.value}, "
                f"style={self.communication_style.value}, "
                f"confirm={self.confirmation_needed})")


class InteractionEnvironment:
    """
    OpenClaw交互环境

    实现OpenAI Gym风格的环境接口：
    - observation_space: 状态空间维度
    - action_space: 动作空间维度
    - reset(): 重置环境
    - step(): 执行动作
    """

    # 状态空间定义
    STATE_DIM = {
        "task_type": 4,  # T1, T2, T3, T4
        "tech_stack": 8,  # react, vue, fastapi, express, python, js, ts, go
        "user_mood": 3,  # focused, relaxed, stressed
        "time_of_day": 1,  # 归一化时间
        "recent_performance": 1  # 归一化性能
    }
    TOTAL_STATE_DIM = sum(STATE_DIM.values())  # 17维

    # 动作空间定义
    ACTION_DIM = {
        "agent_selection": 3,  # claude, codex, gemini
        "automation_level": 3,  # low, medium, high
        "communication_style": 3,  # brief, detailed, interactive
        "confirmation_needed": 1  # bool
    }
    TOTAL_ACTION_DIM = sum(ACTION_DIM.values())  # 10维

    # 支持的技术栈
    SUPPORTED_TECH = {
        "react": 0, "vue": 1, "fastapi": 2, "express": 3,
        "python": 4, "javascript": 5, "typescript": 6, "go": 7
    }

    # Agent映射
    AGENT_MAP = {
        AgentType.CLAUDE: 0,
        AgentType.CODEX: 1,
        AgentType.GEMINI: 2
    }

    # 自动化级别映射
    AUTOMATION_MAP = {
        AutomationLevel.LOW: 0,
        AutomationLevel.MEDIUM: 1,
        AutomationLevel.HIGH: 2
    }

    # 沟通风格映射
    STYLE_MAP = {
        CommunicationStyle.BRIEF: 0,
        CommunicationStyle.DETAILED: 1,
        CommunicationStyle.INTERACTIVE: 2
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化环境

        Args:
            config_path: 模型配置路径（用于加载历史数据）
        """
        self.reward_calculator = RewardCalculator()

        # 当前状态
        self.current_state: Optional[State] = None
        self.current_task_context: Optional[Dict[str, Any]] = None

        # 历史统计
        self.episode_rewards: List[float] = []
        self.episode_count = 0
        self.agent_usage_history: Dict[str, int] = {
            "claude": 0,
            "codex": 0,
            "gemini": 0
        }

        # 近期性能（初始为0.5表示中等）
        self.recent_performance: float = 0.5

        # 尝试加载历史
        if config_path:
            self._load_history(config_path)

    def reset(self, task_context: Dict[str, Any]) -> State:
        """
        重置环境到新任务

        Args:
            task_context: 任务上下文，包含：
                - task_type: 任务类型（"T1", "T2", "T3", "T4"）
                - tech_stack: 使用的技术栈（list）
                - user_mood: 用户心情（"focused", "relaxed", "stressed"，可选）
                - time_of_day: 当前时间（0-24小时，可选）

        Returns:
            初始状态
        """
        self.current_task_context = task_context

        # 解析任务类型
        task_type_str = task_context.get("task_type", "T2")
        task_type = TaskType[task_type_str]

        # 解析技术栈
        tech_stacks = task_context.get("tech_stack", ["python"])
        tech_stack_vector = self._encode_tech_stack(tech_stacks)

        # 解析用户心情（默认为focused）
        user_mood_str = task_context.get("user_mood", "focused")
        user_mood_vector = self._encode_user_mood(user_mood_str)

        # 解析时间（默认为中午）
        time_of_day = task_context.get("time_of_day", 12.0)
        time_normalized = time_of_day / 24.0

        # 创建状态
        self.current_state = State(
            task_type=self._encode_task_type(task_type),
            tech_stack=tech_stack_vector,
            user_mood=user_mood_vector,
            time_of_day=time_normalized,
            recent_performance=self.recent_performance,
            agent_usage_history=self.agent_usage_history.copy()
        )

        return self.current_state

    def step(self, action: Action, task_result: Dict[str, Any]) -> Tuple[State, float, bool, Dict[str, Any]]:
        """
        执行动作

        Args:
            action: 采取的动作
            task_result: 任务执行结果，包含：
                - duration: 任务耗时（秒）
                - test_result: 测试结果
                - user_feedback: 用户反馈
                - metrics: 其他指标

        Returns:
            (next_state, reward, done, info)
        """
        # 1. 记录Agent使用
        agent_name = action.agent_selection.value
        self.agent_usage_history[agent_name] += 1

        # 2. 准备奖励计算的上下文
        reward_context = {
            "task_type": self.current_task_context.get("task_type", "T2"),
            "task_result": task_result,
            "test_result": task_result.get("test_result", {}),
            "user_feedback": task_result.get("user_feedback", {}),
            "metrics": task_result.get("metrics", {})
        }

        # 3. 计算奖励
        reward = self.reward_calculator.calculate_reward(reward_context)

        # 4. 更新近期性能（移动平均）
        self.recent_performance = 0.7 * self.recent_performance + 0.3 * reward

        # 5. 准备下一个状态（保持当前上下文，但更新性能）
        next_state = State(
            task_type=self.current_state.task_type.copy(),
            tech_stack=self.current_state.tech_stack.copy(),
            user_mood=self.current_state.user_mood.copy(),
            time_of_day=self.current_state.time_of_day,
            recent_performance=self.recent_performance,
            agent_usage_history=self.agent_usage_history.copy()
        )

        self.current_state = next_state

        # 6. 检查episode是否结束
        done = task_result.get("completed", True)

        # 7. 准备info
        info = {
            "action_taken": str(action),
            "agent_used": agent_name,
            "reward_breakdown": reward_context.get("debug_info", {}).get("reward_breakdown", {}),
            "task_duration": task_result.get("duration", 0)
        }

        return next_state, reward, done, info

    def _encode_task_type(self, task_type: TaskType) -> np.ndarray:
        """将任务类型编码为one-hot向量"""
        vector = np.zeros(self.STATE_DIM["task_type"])
        index = list(TaskType).index(task_type)
        vector[index] = 1.0
        return vector

    def _encode_tech_stack(self, tech_stacks: List[str]) -> np.ndarray:
        """将技术栈编码为one-hot向量（支持多标签）"""
        vector = np.zeros(self.STATE_DIM["tech_stack"])

        for tech in tech_stacks:
            tech_lower = tech.lower()
            # 检查直接匹配
            if tech_lower in self.SUPPORTED_TECH:
                vector[self.SUPPORTED_TECH[tech_lower]] = 1.0
            # 检查部分匹配
            else:
                for supported_tech, idx in self.SUPPORTED_TECH.items():
                    if supported_tech in tech_lower:
                        vector[idx] = 1.0

        # 如果没有匹配任何技术，默认python
        if not vector.any():
            vector[self.SUPPORTED_TECH["python"]] = 1.0

        return vector

    def _encode_user_mood(self, user_mood: str) -> np.ndarray:
        """将用户心情编码为one-hot向量"""
        moods = ["focused", "relaxed", "stressed"]
        vector = np.zeros(len(moods))

        if user_mood in moods:
            index = moods.index(user_mood)
            vector[index] = 1.0
        else:
            # 默认focused
            vector[0] = 1.0

        return vector

    def get_action_space_size(self) -> int:
        """获取动作空间大小"""
        return self.TOTAL_ACTION_DIM

    def get_state_space_size(self) -> int:
        """获取状态空间大小"""
        return self.TOTAL_STATE_DIM

    def save_history(self, path: str) -> None:
        """保存历史记录"""
        history = {
            "episode_count": self.episode_count,
            "agent_usage_history": self.agent_usage_history,
            "recent_performance": self.recent_performance,
            "reward_history": self.episode_rewards
        }

        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(history, f, indent=2)

    def _load_history(self, path: str) -> None:
        """加载历史记录"""
        path = Path(path).expanduser()

        if not path.exists():
            return

        with open(path, 'r') as f:
            history = json.load(f)

        self.episode_count = history.get("episode_count", 0)
        self.agent_usage_history = history.get("agent_usage_history", self.agent_usage_history)
        self.recent_performance = history.get("recent_performance", 0.5)
        self.episode_rewards = history.get("reward_history", [])


def main():
    """测试交互环境"""
    # 创建环境
    env = InteractionEnvironment()

    # 模拟任务上下文
    task_context = {
        "task_type": "T2",
        "tech_stack": ["python", "fastapi"],
        "user_mood": "focused",
        "time_of_day": 14.0  # 下午2点
    }

    # 重置环境
    state = env.reset(task_context)
    print(f"初始状态: {state}")
    print(f"状态向量: {state.to_vector()}")
    print(f"状态空间大小: {env.get_state_space_size()}")
    print(f"动作空间大小: {env.get_action_space_size()}")

    # 模拟动作
    action = Action(
        agent_selection=AgentType.CLAUDE,
        automation_level=AutomationLevel.MEDIUM,
        communication_style=CommunicationStyle.DETAILED,
        confirmation_needed=True
    )

    print(f"\n采取动作: {action}")

    # 模拟任务结果
    task_result = {
        "duration": 300,  # 5分钟
        "completed": True,
        "test_result": {
            "coverage": 85.0,
            "passed": 10,
            "failed": 1
        },
        "user_feedback": {
            "accepted": True,
            "rating": 4
        },
        "metrics": {
            "complexity": 3,
            "duplication": 0.05,
            "lint_score": 0.9
        }
    }

    # 执行步骤
    next_state, reward, done, info = env.step(action, task_result)

    print(f"\n下一个状态: {next_state}")
    print(f"奖励: {reward:.3f}")
    print(f"完成: {done}")
    print(f"Info: {info}")

    # 保存历史
    env.save_history("/tmp/openclaw_env_history.json")
    print(f"\n历史已保存到 /tmp/openclaw_env_history.json")


if __name__ == "__main__":
    main()
