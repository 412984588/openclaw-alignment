#!/usr/bin/env python3
"""Experience replay tests."""

import numpy as np
from lib.experience_replay import ExperienceReplay, Experience


def _make_exp(reward: float) -> Experience:
    return Experience(
        state=np.zeros(17),
        action=np.zeros(4),
        reward=reward,
        next_state=np.zeros(17),
        done=False,
        priority=abs(reward)
    )


def test_ring_buffer_overwrite():
    replay = ExperienceReplay(capacity=3, use_prioritized=False)

    for i in range(5):
        replay.add(_make_exp(float(i)))

    assert len(replay) == 3

    rewards = [exp.reward for exp in replay.buffer]
    assert set(rewards) == {2.0, 3.0, 4.0}


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
