#!/usr/bin/env python3
"""
交互环境单元测试
"""

import pytest
import numpy as np
from lib.environment import (
    InteractionEnvironment, State, Action,
    TaskType, AgentType, AutomationLevel, CommunicationStyle
)


class TestState:
    """测试State类"""

    def test_state_creation(self):
        """测试状态创建"""
        state = State(
            task_type=np.array([1, 0, 0, 0]),
            tech_stack=np.array([1, 0, 0, 0, 1, 0, 0, 0]),
            user_mood=np.array([1, 0, 0]),
            time_of_day=0.5,
            recent_performance=0.7,
            agent_usage_history={"claude": 5, "codex": 2}
        )

        assert state.task_type.shape == (4,)
        assert state.tech_stack.shape == (8,)
        assert state.user_mood.shape == (3,)
        assert state.time_of_day == 0.5
        assert state.recent_performance == 0.7

    def test_to_vector(self):
        """测试状态向量转换"""
        state = State(
            task_type=np.array([1, 0, 0, 0]),
            tech_stack=np.array([1, 0, 0, 0, 0, 0, 0, 0]),
            user_mood=np.array([0, 1, 0]),
            time_of_day=0.5,
            recent_performance=0.8,
            agent_usage_history={}
        )

        vector = state.to_vector()

        # 4 + 8 + 3 + 1 + 1 = 17
        assert vector.shape == (17,)
        assert vector[0] == 1.0  # task_type[0]
        assert vector[4] == 1.0  # tech_stack[0]
        assert vector[13] == 1.0  # user_mood[1]


class TestAction:
    """测试Action类"""

    def test_action_creation(self):
        """测试动作创建"""
        action = Action(
            agent_selection=AgentType.CLAUDE,
            automation_level=AutomationLevel.HIGH,
            communication_style=CommunicationStyle.BRIEF,
            confirmation_needed=False
        )

        assert action.agent_selection == AgentType.CLAUDE
        assert action.automation_level == AutomationLevel.HIGH
        assert action.communication_style == CommunicationStyle.BRIEF
        assert action.confirmation_needed == False

    def test_to_vector(self):
        """测试动作向量转换"""
        action = Action(
            agent_selection=AgentType.GEMINI,
            automation_level=AutomationLevel.MEDIUM,
            communication_style=CommunicationStyle.INTERACTIVE,
            confirmation_needed=True
        )

        vector = action.to_vector(
            InteractionEnvironment.AGENT_MAP,
            InteractionEnvironment.AUTOMATION_MAP,
            InteractionEnvironment.STYLE_MAP
        )

        # 3 + 3 + 3 + 1 = 10
        assert vector.shape == (10,)
        assert vector[2] == 1.0  # gemini
        assert vector[4] == 1.0  # medium
        assert vector[8] == 1.0  # interactive
        assert vector[9] == 1.0  # confirmation


class TestInteractionEnvironment:
    """测试InteractionEnvironment类"""

    def test_initialization(self):
        """测试环境初始化"""
        env = InteractionEnvironment()

        assert env.get_state_space_size() == 17
        assert env.get_action_space_size() == 10
        assert env.episode_count == 0
        assert env.recent_performance == 0.5

    def test_reset(self):
        """测试环境重置"""
        env = InteractionEnvironment()

        task_context = {
            "task_type": "T2",
            "tech_stack": ["python", "fastapi"],
            "user_mood": "focused",
            "time_of_day": 14.0
        }

        state = env.reset(task_context)

        assert state is not None
        assert state.task_type[1] == 1.0  # T2
        assert state.time_of_day == pytest.approx(14.0 / 24.0)

    def test_reset_with_default_values(self):
        """测试使用默认值重置"""
        env = InteractionEnvironment()

        task_context = {
            "task_type": "T1"
        }

        state = env.reset(task_context)

        # 默认值检查
        assert state.user_mood[0] == 1.0  # focused
        assert state.time_of_day == pytest.approx(12.0 / 24.0)  # noon

    def test_step(self):
        """测试执行步骤"""
        env = InteractionEnvironment()

        # 重置环境
        task_context = {"task_type": "T2", "tech_stack": ["python"]}
        env.reset(task_context)

        # 创建动作
        action = Action(
            agent_selection=AgentType.CLAUDE,
            automation_level=AutomationLevel.MEDIUM,
            communication_style=CommunicationStyle.DETAILED,
            confirmation_needed=True
        )

        # 模拟任务结果
        task_result = {
            "duration": 300,
            "completed": True,
            "test_result": {"coverage": 80.0, "passed": 10, "failed": 0},
            "user_feedback": {"accepted": True, "rating": 5},
            "metrics": {"complexity": 2}
        }

        # 执行步骤
        next_state, reward, done, info = env.step(action, task_result)

        # 检查返回值
        assert next_state is not None
        assert 0.0 <= reward <= 1.0
        assert done == True
        assert "action_taken" in info
        assert "reward_breakdown" in info

        # 检查Agent使用历史已更新
        assert env.agent_usage_history["claude"] == 1

    def test_multi_episode(self):
        """测试多episode运行"""
        env = InteractionEnvironment()

        for episode in range(3):
            # 重置
            task_context = {
                "task_type": f"T{(episode % 4) + 1}",
                "tech_stack": ["python"]
            }
            env.reset(task_context)

            # 执行动作
            action = Action(
                agent_selection=AgentType.CODEX,
                automation_level=AutomationLevel.HIGH,
                communication_style=CommunicationStyle.BRIEF,
                confirmation_needed=False
            )

            task_result = {
                "duration": 200,
                "completed": True,
                "test_result": {},
                "user_feedback": {},
                "metrics": {}
            }

            env.step(action, task_result)

        # 检查codex使用了3次
        assert env.agent_usage_history["codex"] == 3

    def test_performance_update(self):
        """测试性能更新"""
        env = InteractionEnvironment()

        # 初始性能
        assert env.recent_performance == 0.5

        # 重置并执行高奖励任务
        env.reset({"task_type": "T2", "tech_stack": ["python"]})

        action = Action(
            agent_selection=AgentType.CLAUDE,
            automation_level=AutomationLevel.MEDIUM,
            communication_style=CommunicationStyle.DETAILED,
            confirmation_needed=True
        )

        task_result = {
            "duration": 100,
            "completed": True,
            "test_result": {"coverage": 100.0, "passed": 10, "failed": 0},
            "user_feedback": {"accepted": True, "rating": 5},
            "metrics": {"complexity": 1, "duplication": 0.0, "lint_score": 1.0}
        }

        env.step(action, task_result)

        # 性能应该提高
        assert env.recent_performance > 0.5

    def test_save_load_history(self):
        """测试历史保存和加载"""
        import tempfile
        import os

        env1 = InteractionEnvironment()

        # 运行一个episode
        env1.reset({"task_type": "T2", "tech_stack": ["python"]})

        action = Action(
            agent_selection=AgentType.GEMINI,
            automation_level=AutomationLevel.LOW,
            communication_style=CommunicationStyle.INTERACTIVE,
            confirmation_needed=True
        )

        task_result = {
            "duration": 400,
            "completed": True,
            "test_result": {},
            "user_feedback": {},
            "metrics": {}
        }

        env1.step(action, task_result)

        # 保存历史
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            env1.save_history(temp_path)

            # 创建新环境并加载历史
            env2 = InteractionEnvironment(config_path=temp_path)

            # 检查历史已恢复
            assert env2.agent_usage_history["gemini"] == 1

        finally:
            os.unlink(temp_path)

    def test_tech_stack_encoding(self):
        """测试技术栈编码"""
        env = InteractionEnvironment()

        # 单个技术
        state = env.reset({"task_type": "T2", "tech_stack": ["python"]})
        assert state.tech_stack[4] == 1.0  # python index

        # 多个技术
        state = env.reset({"task_type": "T2", "tech_stack": ["python", "react"]})
        assert state.tech_stack[4] == 1.0  # python
        assert state.tech_stack[0] == 1.0  # react

        # 未知技术（应该默认为python）
        state = env.reset({"task_type": "T2", "tech_stack": ["unknown_tech"]})
        assert state.tech_stack[4] == 1.0  # python as default

    def test_task_type_encoding(self):
        """测试任务类型编码"""
        env = InteractionEnvironment()

        for i, task_type in enumerate(["T1", "T2", "T3", "T4"], 1):
            state = env.reset({"task_type": task_type, "tech_stack": ["python"]})
            assert state.task_type[i-1] == 1.0
            assert np.sum(state.task_type) == 1.0

    def test_user_mood_encoding(self):
        """测试用户心情编码"""
        env = InteractionEnvironment()

        for mood in ["focused", "relaxed", "stressed"]:
            state = env.reset({
                "task_type": "T2",
                "tech_stack": ["python"],
                "user_mood": mood
            })

            assert np.sum(state.user_mood) == 1.0


class TestEnvironmentIntegration:
    """集成测试"""

    def test_full_episode(self):
        """测试完整episode"""
        env = InteractionEnvironment()

        # 1. Reset
        task_context = {
            "task_type": "T3",
            "tech_stack": ["react", "typescript"],
            "user_mood": "stressed",
            "time_of_day": 16.0
        }

        state = env.reset(task_context)
        assert state is not None

        # 2. Step
        action = Action(
            agent_selection=AgentType.CODEX,
            automation_level=AutomationLevel.HIGH,
            communication_style=CommunicationStyle.BRIEF,
            confirmation_needed=False
        )

        task_result = {
            "duration": 600,  # 10分钟
            "completed": True,
            "test_result": {
                "coverage": 75.0,
                "passed": 8,
                "failed": 2
            },
            "user_feedback": {
                "accepted": True,
                "rating": 4,
                "revisions": 1
            },
            "metrics": {
                "complexity": 4,
                "duplication": 0.08,
                "lint_score": 0.85
            }
        }

        next_state, reward, done, info = env.step(action, task_result)

        # 3. 验证
        assert 0.0 <= reward <= 1.0
        assert done == True
        assert info["agent_used"] == "codex"
        assert "reward_breakdown" in info

        # 4. 检查状态已更新
        assert next_state.recent_performance >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
