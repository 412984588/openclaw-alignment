#!/usr/bin/env python3
"""
强化学习训练器 - 完整训练循环

实现完整的训练流程：
- 多episode训练
- 检查点保存/加载
- 训练统计和可视化
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

from .agent import AlignmentAgent, Trajectory
from .environment import InteractionEnvironment
from .experience_replay import ExperienceReplay, Experience


class RLTrainer:
    """
    强化学习训练器

    功能：
    - 完整训练循环（多个episode）
    - 检查点保存/加载
    - 训练统计和可视化
    """

    def __init__(self, model_dir: str = None,
                 use_experience_replay: bool = True,
                 replay_capacity: int = 10000):
        """
        初始化训练器

        Args:
            model_dir: 模型保存目录
            use_experience_replay: 是否使用经验回放
            replay_capacity: 经验回放容量
        """
        self.model_dir = Path(model_dir).expanduser() if model_dir else Path("./models/rl")
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # 初始化环境
        self.env = InteractionEnvironment()

        # 初始化智能体
        self.agent = AlignmentAgent(
            state_dim=self.env.get_state_space_size(),
            action_dim=self.env.get_action_space_size()
        )

        # 初始化经验回放
        self.use_experience_replay = use_experience_replay
        self.replay_buffer = ExperienceReplay(capacity=replay_capacity) if use_experience_replay else None

        # 训练统计
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []
        self.training_losses: List[Dict[str, float]] = []

        # 当前episode
        self.current_episode = 0

    def train(self, num_episodes: int = 100,
              max_steps_per_episode: int = 100,
              save_interval: int = 10) -> Dict[str, Any]:
        """
        训练智能体

        Args:
            num_episodes: 训练episode数量
            max_steps_per_episode: 每个episode最大步数
            save_interval: 保存间隔

        Returns:
            训练统计
        """
        print(f"🚀 开始训练（{num_episodes} episodes）...")

        for episode in range(num_episodes):
            self.current_episode = episode + 1

            # 运行一个episode
            episode_reward, episode_length, episode_loss = self._run_episode(max_steps_per_episode)

            # 记录统计
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_length)
            self.training_losses.append(episode_loss)

            # 打印进度
            if episode % 10 == 0 or episode == num_episodes - 1:
                avg_reward = np.mean(self.episode_rewards[-10:])
                print(f"Episode {episode + 1}/{num_episodes} | "
                      f"奖励: {episode_reward:.3f} | "
                      f"平均: {avg_reward:.3f} | "
                      f"步数: {episode_length}")

            # 定期保存
            if episode % save_interval == 0 and episode > 0:
                self.save_checkpoint(f"checkpoint_episode_{episode}")

        print(f"✅ 训练完成！")

        # 保存最终模型
        self.save_checkpoint("final")

        return self.get_training_stats()

    def _run_episode(self, max_steps: int) -> Tuple[float, int, Dict[str, float]]:
        """
        运行一个episode

        Args:
            max_steps: 最大步数

        Returns:
            (总奖励, 步数, 损失统计)
        """
        # 随机任务上下文
        task_context = self._generate_random_task_context()

        # 重置环境
        state = self.env.reset(task_context)

        trajectory = Trajectory([], [], [], [], [])
        total_reward = 0.0

        for step in range(max_steps):
            # 选择动作
            action = self.agent.select_action(state, explore=True)

            # 模拟任务结果
            task_result = self._simulate_task_result()

            # 执行步骤
            next_state, reward, done, info = self.env.step(action, task_result)

            action_indices = self.agent.encode_action_indices(action)

            # 记录轨迹
            trajectory.states.append(state.to_vector())
            trajectory.actions.append(action_indices)
            trajectory.rewards.append(reward)
            trajectory.dones.append(done)
            trajectory.next_states.append(next_state.to_vector())

            # 添加到经验回放
            if self.replay_buffer:
                exp = Experience(
                    state=state.to_vector(),
                    action=action_indices,
                    reward=reward,
                    next_state=next_state.to_vector(),
                    done=done,
                    priority=abs(reward)
                )
                self.replay_buffer.add(exp)

            total_reward += reward
            state = next_state

            if done:
                break

        # 更新策略
        loss_stats = self.agent.update_policy(trajectory)

        # 如果使用经验回放且有足够经验，进行额外的训练更新
        if self.replay_buffer and self.replay_buffer.is_ready(min_size=32):
            additional_loss = self._train_from_replay()
            # 合并损失统计
            if additional_loss:
                for key, value in additional_loss.items():
                    loss_stats[key] = loss_stats.get(key, 0) + value

        return total_reward, len(trajectory), loss_stats

    def _train_from_replay(self, num_updates: int = 4) -> Optional[Dict[str, float]]:
        """
        从经验回放中训练

        Args:
            num_updates: 更新次数

        Returns:
            损失统计
        """
        if not self.replay_buffer:
            return None

        total_actor_loss = 0.0
        total_critic_loss = 0.0

        for _ in range(num_updates):
            states, actions, rewards, next_states, dones = self.replay_buffer.get_batch(batch_size=32)

            if len(states) == 0:
                continue

            # 使用经验回放数据更新策略
            for i in range(len(states)):
                state = states[i]
                action_indices = actions[i]
                reward = rewards[i]
                next_state = next_states[i]
                done = dones[i]

                # 计算目标价值
                if done:
                    target_value = reward
                else:
                    target_value = reward + self.agent.gamma * self.agent.value_net.forward(next_state)

                # 计算优势
                current_value = self.agent.value_net.forward(state)
                advantage = target_value - current_value

                # 更新Actor和Critic
                actor_loss = self.agent.policy_net.update(state, action_indices, advantage)
                critic_loss = self.agent.value_net.update(state, target_value)

                total_actor_loss += actor_loss
                total_critic_loss += critic_loss

        return {
            "actor_loss": total_actor_loss / (num_updates * 32),
            "critic_loss": total_critic_loss / (num_updates * 32)
        }

    def _generate_random_task_context(self) -> Dict[str, Any]:
        """生成随机任务上下文"""
        task_types = ["T1", "T2", "T3", "T4"]
        tech_stacks = [["python"], ["javascript"], ["python", "fastapi"], ["react", "typescript"]]
        moods = ["focused", "relaxed", "stressed"]

        # 使用Python的random.choice而不是numpy
        import random
        return {
            "task_type": random.choice(task_types),
            "tech_stack": random.choice(tech_stacks),
            "user_mood": random.choice(moods),
            "time_of_day": float(np.random.uniform(0, 24))
        }

    def _simulate_task_result(self) -> Dict[str, Any]:
        """模拟任务结果"""
        # 随机生成结果
        coverage = np.random.uniform(50, 100)
        passed = int(np.random.uniform(5, 15))
        failed = int(np.random.uniform(0, 3))

        return {
            "duration": np.random.uniform(100, 600),
            "completed": True,
            "test_result": {
                "coverage": coverage,
                "passed": passed,
                "failed": failed
            },
            "user_feedback": {
                "accepted": np.random.random() > 0.2,
                "rating": np.random.randint(3, 6)
            },
            "metrics": {
                "complexity": np.random.uniform(1, 7),
                "duplication": np.random.uniform(0, 0.2),
                "lint_score": np.random.uniform(0.6, 1.0)
            }
        }

    def save_checkpoint(self, name: str) -> None:
        """
        保存检查点

        Args:
            name: 检查点名称
        """
        checkpoint_dir = self.model_dir / name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 保存智能体
        self.agent.save_model(str(checkpoint_dir))

        # 保存统计
        stats = {
            "episode": self.current_episode,
            "episode_rewards": self.episode_rewards,
            "episode_lengths": self.episode_lengths,
            "training_losses": self.training_losses[-100:]  # 最近100个
        }

        with open(checkpoint_dir / "training_stats.json", 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"✅ 检查点已保存: {checkpoint_dir}")

    def load_checkpoint(self, name: str) -> None:
        """
        加载检查点

        Args:
            name: 检查点名称
        """
        checkpoint_dir = self.model_dir / name

        # 加载智能体
        self.agent.load_model(str(checkpoint_dir))

        # 加载统计
        stats_path = checkpoint_dir / "training_stats.json"
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                stats = json.load(f)

            self.current_episode = stats["episode"]
            self.episode_rewards = stats["episode_rewards"]
            self.episode_lengths = stats["episode_lengths"]
            self.training_losses = stats["training_losses"]

        print(f"✅ 检查点已加载: {checkpoint_dir}")

    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计"""
        if not self.episode_rewards:
            return {}

        return {
            "total_episodes": len(self.episode_rewards),
            "average_reward": float(np.mean(self.episode_rewards)),
            "reward_std": float(np.std(self.episode_rewards)),
            "max_reward": float(np.max(self.episode_rewards)),
            "min_reward": float(np.min(self.episode_rewards)),
            "average_length": float(np.mean(self.episode_lengths)),
            "latest_reward": float(self.episode_rewards[-1]),
            "improvement": float(np.mean(self.episode_rewards[-10:]) - np.mean(self.episode_rewards[:10])) if len(self.episode_rewards) >= 20 else 0.0
        }


def main():
    """测试训练器"""
    trainer = RLTrainer(model_dir="/tmp/rl_trainer_test", use_experience_replay=True)

    print(f"✅ 训练器已创建")

    # 训练几个episode
    stats = trainer.train(num_episodes=5, max_steps_per_episode=10, save_interval=2)

    print(f"\n📊 训练统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
