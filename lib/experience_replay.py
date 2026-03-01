#!/usr/bin/env python3
"""
经验回放缓冲区 - 提升样本效率

存储和采样经验（state, action, reward, next_state, done），
支持优先级采样和批量采样
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
import random


@dataclass
class Experience:
    """单个经验"""
    state: np.ndarray
    action: np.ndarray
    reward: float
    next_state: np.ndarray
    done: bool
    priority: float = 1.0  # 优先级（用于优先级采样）

    def __repr__(self) -> str:
        return f"Experience(reward={self.reward:.3f}, done={self.done})"


class ExperienceReplay:
    """
    经验回放缓冲区

    功能：
    - 存储经验
    - 随机采样
    - 优先级采样（可选）
    - 批量采样
    """

    def __init__(self, capacity: int = 10000, use_prioritized: bool = False):
        """
        初始化经验回放缓冲区

        Args:
            capacity: 缓冲区容量
            use_prioritized: 是否使用优先级采样
        """
        self.capacity = capacity
        self.use_prioritized = use_prioritized

        # 存储经验的缓冲区
        self.buffer: List[Experience] = []

        # 优先级采样相关
        self.priorities = np.zeros(capacity)
        self.max_priority = 1.0
        self.alpha = 0.6  # 优先级指数
        self.beta = 0.4   # 重要性采样指数
        self.epsilon = 1e-6  # 避免零优先级

    def add(self, experience: Experience) -> None:
        """
        添加经验到缓冲区

        Args:
            experience: 要添加的经验
        """
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            if self.use_prioritized:
                self.priorities[len(self.buffer) - 1] = self.max_priority
        else:
            # 覆盖最旧的经验（循环缓冲）
            idx = len(self.buffer) % self.capacity
            if idx >= len(self.buffer):
                self.buffer.append(experience)
            else:
                self.buffer[idx] = experience

            if self.use_prioritized:
                self.priorities[idx] = self.max_priority

        # 更新最大优先级
        if self.use_prioritized:
            self.max_priority = max(self.max_priority, experience.priority)

    def sample(self, batch_size: int = 32) -> List[Experience]:
        """
        随机采样一批经验

        Args:
            batch_size: 批次大小

        Returns:
            经验批次
        """
        if len(self.buffer) < batch_size:
            batch_size = len(self.buffer)

        if self.use_prioritized:
            return self._prioritized_sample(batch_size)
        else:
            return random.sample(self.buffer, batch_size)

    def _prioritized_sample(self, batch_size: int) -> List[Experience]:
        """
        优先级采样

        根据优先级进行采样，优先级越高被采样概率越大
        """
        if len(self.buffer) == 0:
            return []

        # 计算采样概率
        priorities = self.priorities[:len(self.buffer)]
        probs = priorities ** self.alpha
        probs /= probs.sum()

        # 采样索引
        indices = np.random.choice(len(self.buffer), size=min(batch_size, len(self.buffer)), p=probs)

        # 计算重要性权重
        weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
        weights /= weights.max()

        return [self.buffer[idx] for idx in indices]

    def get_batch(self, batch_size: int = 32) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        获取批次数据（用于训练）

        Args:
            batch_size: 批次大小

        Returns:
            (states, actions, rewards, next_states, dones)
        """
        experiences = self.sample(batch_size)

        if not experiences:
            return (
                np.zeros((0, 17)),  # states
                np.zeros((0, 10)),  # actions
                np.zeros(0),      # rewards
                np.zeros((0, 17)), # next_states
                np.zeros(0)       # dones
            )

        states = np.array([exp.state for exp in experiences])
        actions = np.array([exp.action for exp in experiences])
        rewards = np.array([exp.reward for exp in experiences])
        next_states = np.array([exp.next_state for exp in experiences])
        dones = np.array([exp.done for exp in experiences])

        return states, actions, rewards, next_states, dones

    def update_priorities(self, indices: List[int], priorities: List[float]) -> None:
        """
        更新经验的优先级

        Args:
            indices: 经验索引
            priorities: 新的优先级
        """
        for idx, priority in zip(indices, priorities):
            if idx < len(self.buffer):
                self.priorities[idx] = priority + self.epsilon
                self.max_priority = max(self.max_priority, priority)

    def __len__(self) -> int:
        return len(self.buffer)

    def is_ready(self, min_size: int = 100) -> bool:
        """
        检查缓冲区是否准备好采样

        Args:
            min_size: 最小大小要求

        Returns:
            是否可以采样
        """
        return len(self.buffer) >= min_size

    def clear(self) -> None:
        """清空缓冲区"""
        self.buffer.clear()
        self.priorities = np.zeros(self.capacity)
        self.max_priority = 1.0


def main():
    """测试经验回放"""
    # 创建经验回放缓冲区
    replay = ExperienceReplay(capacity=1000, use_prioritized=True)

    print(f"✅ 经验回放缓冲区已创建（容量：{replay.capacity}）")

    # 添加一些模拟经验
    for i in range(10):
        state = np.random.randn(17)
        action = np.random.randn(10)
        reward = np.random.randn()
        next_state = np.random.randn(17)
        done = i % 5 == 0

        exp = Experience(state, action, reward, next_state, done, priority=abs(reward))
        replay.add(exp)

    print(f"✅ 已添加 {len(replay)} 个经验")

    # 采样批次
    states, actions, rewards, next_states, dones = replay.get_batch(batch_size=4)

    print(f"✅ 采样批次: states={states.shape}, actions={actions.shape}")
    print(f"   奖励: {rewards}")
    print(f"   完成: {dones}")

    # 检查是否准备好
    print(f"✅ 准备采样: {replay.is_ready(min_size=5)}")


if __name__ == "__main__":
    main()
