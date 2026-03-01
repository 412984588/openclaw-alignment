#!/usr/bin/env python3
"""
强化学习智能体 - Actor-Critic实现

实现Actor-Critic算法，包括：
- PolicyNetwork: 策略网络（输出动作概率分布）
- ValueNetwork: 价值网络（估计状态价值）
- AlignmentAgent: Actor-Critic智能体

Phase 1: 纯NumPy实现（线性模型）
Phase 2: 可选PyTorch实现（神经网络）
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from .environment import State, Action, AgentType, AutomationLevel, CommunicationStyle


@dataclass
class Trajectory:
    """轨迹数据类"""
    states: List[np.ndarray]  # 状态序列
    actions: List[np.ndarray]  # 动作序列
    rewards: List[float]  # 奖励序列
    dones: List[bool]  # 完成标志
    next_states: List[np.ndarray]  # 下一状态序列

    def __len__(self) -> int:
        return len(self.states)

    def __repr__(self) -> str:
        return f"Trajectory(length={len(self)}, total_reward={sum(self.rewards):.2f})"


class PolicyNetwork:
    """
    策略网络 - 输出动作概率分布

    Phase 1: 线性模型（logits = state @ weights + bias）
    Phase 2: 可选神经网络（PyTorch）
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 64):
        """
        初始化策略网络

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            hidden_dim: 隐藏层维度（Phase 2使用）
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        # Phase 1: 线性模型参数
        self.weights = np.random.randn(state_dim, action_dim) * 0.01
        self.bias = np.zeros(action_dim)

    def forward(self, state: np.ndarray) -> np.ndarray:
        """前向传播：计算logits"""
        return state @ self.weights + self.bias

    def softmax(self, logits: np.ndarray) -> np.ndarray:
        """Softmax激活函数"""
        # 数值稳定性：减去最大值
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / np.sum(exp_logits)

    def get_action_probs(self, state: np.ndarray) -> np.ndarray:
        """获取动作概率分布"""
        logits = self.forward(state)
        return self.softmax(logits)

    def sample_action(self, state: np.ndarray, explore: bool = True) -> Tuple[int, np.ndarray]:
        """
        采样动作

        Args:
            state: 当前状态
            explore: 是否探索（epsilon-greedy）

        Returns:
            (action_index, action_probs)
        """
        action_probs = self.get_action_probs(state)

        if explore and np.random.random() < 0.1:  # 10% epsilon-greedy
            # 随机探索
            action_idx = np.random.randint(self.action_dim)
        else:
            # 按概率采样
            action_idx = np.random.choice(self.action_dim, p=action_probs)

        return action_idx, action_probs

    def update(self, state: np.ndarray, action_idx: int, advantage: float,
               learning_rate: float = 0.01) -> float:
        """
        更新策略网络（REINFORCE算法）

        Args:
            state: 当前状态
            action_idx: 执行的动作
            advantage: 优势函数 A(s,a) = Q(s,a) - V(s)
            learning_rate: 学习率

        Returns:
            损失值
        """
        # 计算梯度
        action_probs = self.get_action_probs(state)
        log_prob = np.log(action_probs[action_idx] + 1e-10)

        # Policy gradient: -log π(a|s) * A
        loss = -log_prob * advantage

        # 计算梯度
        grad_log_prob = -np.eye(self.action_dim)[action_idx] / (action_probs + 1e-10)

        # 更新权重
        grad_w = np.outer(state, grad_log_prob[action_idx] * advantage)
        self.weights -= learning_rate * grad_w
        self.bias -= learning_rate * grad_log_prob[action_idx] * advantage

        return loss

    def save(self, path: str) -> None:
        """保存模型参数"""
        params = {
            "weights": self.weights.tolist(),
            "bias": self.bias.tolist(),
            "state_dim": self.state_dim,
            "action_dim": self.action_dim
        }

        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(params, f)

    def load(self, path: str) -> None:
        """加载模型参数"""
        path = Path(path).expanduser()

        if not path.exists():
            return

        with open(path, 'r') as f:
            params = json.load(f)

        self.weights = np.array(params["weights"])
        self.bias = np.array(params["bias"])
        self.state_dim = params["state_dim"]
        self.action_dim = params["action_dim"]


class ValueNetwork:
    """
    价值网络 - 估计状态价值 V(s)

    Phase 1: 线性模型
    Phase 2: 可选神经网络（PyTorch）
    """

    def __init__(self, state_dim: int, hidden_dim: int = 64):
        """
        初始化价值网络

        Args:
            state_dim: 状态维度
            hidden_dim: 隐藏层维度（Phase 2使用）
        """
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim

        # 线性模型参数
        self.weights = np.random.randn(state_dim) * 0.01
        self.bias = 0.0

    def forward(self, state: np.ndarray) -> float:
        """前向传播：计算状态价值"""
        return float(state @ self.weights + self.bias)

    def update(self, state: np.ndarray, target_value: float,
               learning_rate: float = 0.01) -> float:
        """
        更新价值网络（MSE损失）

        Args:
            state: 当前状态
            target_value: 目标价值（实际回报）
            learning_rate: 学习率

        Returns:
            损失值
        """
        # 计算当前价值
        current_value = self.forward(state)

        # 计算损失
        loss = (current_value - target_value) ** 2

        # 计算梯度
        grad_w = 2 * (current_value - target_value) * state
        grad_b = 2 * (current_value - target_value)

        # 更新权重
        self.weights -= learning_rate * grad_w
        self.bias -= learning_rate * grad_b

        return loss

    def save(self, path: str) -> None:
        """保存模型参数"""
        params = {
            "weights": self.weights.tolist(),
            "bias": float(self.bias),
            "state_dim": self.state_dim
        }

        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(params, f)

    def load(self, path: str) -> None:
        """加载模型参数"""
        path = Path(path).expanduser()

        if not path.exists():
            return

        with open(path, 'r') as f:
            params = json.load(f)

        self.weights = np.array(params["weights"])
        self.bias = params["bias"]
        self.state_dim = params["state_dim"]


class AlignmentAgent:
    """
    Actor-Critic智能体

    结合策略网络和价值网络，实现Actor-Critic算法：
    - Actor: 策略网络，选择动作
    - Critic: 价值网络，评估状态价值

    算法流程：
    1. 使用当前策略选择动作
    2. 执行动作，获得奖励和下一状态
    3. 计算优势函数 A = R + γV(s') - V(s)
    4. 更新Actor：-log π(a|s) * A
    5. 更新Critic：(V(s) - R)²
    """

    def __init__(self, state_dim: int, action_dim: int,
                 gamma: float = 0.99,
                 actor_lr: float = 0.01,
                 critic_lr: float = 0.01):
        """
        初始化智能体

        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            gamma: 折扣因子
            actor_lr: Actor学习率
            critic_lr: Critic学习率
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma

        # 初始化网络
        self.policy_net = PolicyNetwork(state_dim, action_dim)
        self.value_net = ValueNetwork(state_dim)

        # 学习率
        self.actor_lr = actor_lr
        self.critic_lr = critic_lr

        # 训练统计
        self.episode_count = 0
        self.total_steps = 0

    def select_action(self, state: State, explore: bool = True) -> Action:
        """
        选择动作

        Args:
            state: 当前状态
            explore: 是否探索

        Returns:
            选择的动作
        """
        # 将状态转换为向量
        state_vector = state.to_vector()

        # 采样动作索引
        action_idx, action_probs = self.policy_net.sample_action(state_vector, explore)

        # 将动作索引转换为Action对象
        action = self._decode_action(action_idx)

        return action

    def _decode_action(self, action_idx: int) -> Action:
        """将动作索引解码为Action对象"""
        # 简化的解码：将索引映射到动作
        # 实际应用中需要更复杂的映射

        # 分解action_idx为各个维度
        agent_idx = action_idx // 9  # 3*3
        automation_idx = (action_idx % 9) // 3  # 3
        style_idx = action_idx % 3  # 3
        confirm = (action_idx % 2) == 0  # 偶数需要确认

        # 映射到枚举
        agent_type = [AgentType.CLAUDE, AgentType.CODEX, AgentType.GEMINI][agent_idx % 3]
        automation = [AutomationLevel.LOW, AutomationLevel.MEDIUM, AutomationLevel.HIGH][automation_idx % 3]
        style = [CommunicationStyle.BRIEF, CommunicationStyle.DETAILED, CommunicationStyle.INTERACTIVE][style_idx]

        return Action(
            agent_selection=agent_type,
            automation_level=automation,
            communication_style=style,
            confirmation_needed=confirm
        )

    def update_policy(self, trajectory: Trajectory) -> Dict[str, float]:
        """
        更新策略（Actor-Critic算法）

        Args:
            trajectory: 完整轨迹

        Returns:
            损失统计
        """
        if len(trajectory) == 0:
            return {}

        # 计算回报
        returns = self._compute_returns(trajectory.rewards, trajectory.dones)

        total_actor_loss = 0.0
        total_critic_loss = 0.0

        # 逐步更新
        for i in range(len(trajectory)):
            state = trajectory.states[i]
            action_idx = np.argmax(trajectory.actions[i])  # 从one-hot获取索引
            reward = trajectory.rewards[i]
            next_state = trajectory.next_states[i]
            done = trajectory.dones[i]

            # 计算目标价值
            if done:
                target_value = reward
            else:
                target_value = reward + self.gamma * self.value_net.forward(next_state)

            # 计算优势函数
            current_value = self.value_net.forward(state)
            advantage = target_value - current_value

            # 更新Actor
            actor_loss = self.policy_net.update(state, action_idx, advantage, self.actor_lr)
            total_actor_loss += actor_loss

            # 更新Critic
            critic_loss = self.value_net.update(state, target_value, self.critic_lr)
            total_critic_loss += critic_loss

        # 更新统计
        self.episode_count += 1
        self.total_steps += len(trajectory)

        return {
            "actor_loss": total_actor_loss / len(trajectory),
            "critic_loss": total_critic_loss / len(trajectory),
            "episode_length": len(trajectory),
            "total_return": sum(trajectory.rewards)
        }

    def _compute_returns(self, rewards: List[float], dones: List[bool]) -> List[float]:
        """
        计算折扣回报

        Args:
            rewards: 奖励序列
            dones: 完成标志序列

        Returns:
            折扣回报序列
        """
        returns = []
        running_return = 0.0

        # 从后往前计算
        for reward, done in zip(reversed(rewards), reversed(dones)):
            if done:
                running_return = reward
            else:
                running_return = reward + self.gamma * running_return

            returns.insert(0, running_return)

        return returns

    def save_model(self, path: str) -> None:
        """保存模型"""
        model_dir = Path(path).expanduser()
        model_dir.mkdir(parents=True, exist_ok=True)

        # 保存策略网络
        self.policy_net.save(str(model_dir / "policy_network.json"))

        # 保存价值网络
        self.value_net.save(str(model_dir / "value_network.json"))

        # 保存元数据
        metadata = {
            "episode_count": self.episode_count,
            "total_steps": self.total_steps,
            "gamma": self.gamma,
            "actor_lr": self.actor_lr,
            "critic_lr": self.critic_lr
        }

        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

    def load_model(self, path: str) -> None:
        """加载模型"""
        model_dir = Path(path).expanduser()

        # 加载策略网络
        self.policy_net.load(str(model_dir / "policy_network.json"))

        # 加载价值网络
        self.value_net.load(str(model_dir / "value_network.json"))

        # 加载元数据
        metadata_path = model_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            self.episode_count = metadata.get("episode_count", 0)
            self.total_steps = metadata.get("total_steps", 0)


def main():
    """测试智能体"""
    from .environment import InteractionEnvironment

    # 创建环境和智能体
    env = InteractionEnvironment()
    agent = AlignmentAgent(
        state_dim=env.get_state_space_size(),
        action_dim=env.get_action_space_size()
    )

    print(f"智能体已创建")
    print(f"状态空间: {env.get_state_space_size()}")
    print(f"动作空间: {env.get_action_space_size()}")

    # 模拟训练
    for episode in range(3):
        print(f"\n=== Episode {episode + 1} ===")

        # 重置环境
        task_context = {
            "task_type": "T2",
            "tech_stack": ["python"],
            "user_mood": "focused"
        }

        state = env.reset(task_context)

        # 收集轨迹
        trajectory = Trajectory([], [], [], [], [])

        for step in range(5):  # 每个episode最多5步
            # 选择动作
            action = agent.select_action(state, explore=True)

            # 模拟任务结果
            task_result = {
                "duration": 200 + step * 50,
                "completed": step == 4,  # 最后一步完成
                "test_result": {"coverage": 70 + step * 5},
                "user_feedback": {"accepted": True},
                "metrics": {}
            }

            # 执行步骤
            next_state, reward, done, info = env.step(action, task_result)

            # 记录轨迹
            trajectory.states.append(state.to_vector())
            trajectory.actions.append(action.to_vector(
                env.AGENT_MAP, env.AUTOMATION_MAP, env.STYLE_MAP
            ))
            trajectory.rewards.append(reward)
            trajectory.dones.append(done)
            trajectory.next_states.append(next_state.to_vector())

            state = next_state

            print(f"  Step {step + 1}: reward={reward:.3f}, done={done}")

            if done:
                break

        # 更新策略
        stats = agent.update_policy(trajectory)
        print(f"  总回报: {stats['total_return']:.3f}")
        print(f"  Actor损失: {stats['actor_loss']:.4f}")
        print(f"  Critic损失: {stats['critic_loss']:.4f}")

    # 保存模型
    agent.save_model("/tmp/openclaw_rl_agent")
    print(f"\n模型已保存到 /tmp/openclaw_rl_agent")


if __name__ == "__main__":
    main()
