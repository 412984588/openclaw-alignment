#!/usr/bin/env python3
"""
核心契约一致性测试
"""

from lib.agent import PolicyNetwork
from lib.contracts import ACTION_HEAD_DIMS, ACTION_VECTOR_DIM, STATE_VECTOR_DIM
from lib.environment import InteractionEnvironment


def test_action_head_dims_sum_matches_action_vector_dim():
    assert sum(ACTION_HEAD_DIMS.values()) == ACTION_VECTOR_DIM


def test_environment_space_sizes_match_contract():
    env = InteractionEnvironment()
    assert env.get_state_space_size() == STATE_VECTOR_DIM
    assert env.get_action_space_size() == ACTION_VECTOR_DIM


def test_policy_default_action_dim_matches_contract():
    policy = PolicyNetwork(state_dim=STATE_VECTOR_DIM)
    assert policy.action_dim == ACTION_VECTOR_DIM
