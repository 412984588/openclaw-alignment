#!/usr/bin/env python3
"""
RLLearner历史偏好测试
"""

import pytest

from lib.learner import RLLearner


def test_rl_learner_records_preference_history(tmp_path):
    learner = RLLearner(
        model_path=str(tmp_path / "models"),
        config_path=str(tmp_path / "config.json")
    )

    assert learner.get_agent_success_rate("T2", "claude") is None
    assert learner.get_workflow_success_rate("T2", "tdd") is None

    learner.record_preference_result(task_type="T2", agent="claude", workflow="tdd", reward=0.9)
    learner.record_preference_result(task_type="T2", agent="claude", workflow="tdd", reward=0.3)

    assert learner.get_agent_success_rate("T2", "claude") == pytest.approx(0.6)
    assert learner.get_workflow_success_rate("T2", "tdd") == pytest.approx(0.6)
    assert learner.env.reward_calculator.history_provider is learner
