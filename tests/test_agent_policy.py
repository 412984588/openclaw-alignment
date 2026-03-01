import numpy as np
from lib.agent import PolicyNetwork, AlignmentAgent
from lib.environment import Action, AgentType, AutomationLevel, CommunicationStyle


def test_policy_multihead_shapes():
    policy = PolicyNetwork(state_dim=17)
    probs = policy.get_action_probs(np.ones(17, dtype=np.float32))
    assert set(probs) == {"agent", "automation", "style", "confirm"}
    assert probs["agent"].shape == (3,)
    assert probs["automation"].shape == (3,)
    assert probs["style"].shape == (3,)
    assert probs["confirm"].shape == (2,)
    for head_probs in probs.values():
        assert np.isclose(np.sum(head_probs), 1.0)


def test_policy_update_increases_selected_prob():
    policy = PolicyNetwork(state_dim=17)
    for key in policy.weights:
        policy.weights[key].fill(0.0)
        policy.bias[key].fill(0.0)
    state = np.ones(17, dtype=np.float32)
    indices = np.array([0, 0, 0, 1], dtype=int)
    before = policy.get_action_probs(state)
    policy.update(state, indices, advantage=1.0, learning_rate=0.1)
    after = policy.get_action_probs(state)
    assert after["agent"][0] > before["agent"][0]
    assert after["automation"][0] > before["automation"][0]
    assert after["style"][0] > before["style"][0]
    assert after["confirm"][1] > before["confirm"][1]


def test_action_roundtrip_indices():
    agent = AlignmentAgent(state_dim=17, action_dim=11)
    action = Action(
        agent_selection=AgentType.GEMINI,
        automation_level=AutomationLevel.HIGH,
        communication_style=CommunicationStyle.INTERACTIVE,
        confirmation_needed=True,
    )
    indices = agent.encode_action_indices(action)
    assert agent.decode_action_indices(indices) == action
