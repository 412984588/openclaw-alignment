#!/usr/bin/env python3
"""
神经网络模型 - 可选PyTorch实现

提供PyTorch版本的策略网络和价值网络，如果PyTorch不可用则降级到NumPy版本
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# 尝试导入PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

from .agent import PolicyNetwork as NumpyPolicyNetwork
from .agent import ValueNetwork as NumpyValueNetwork


class MLPModel(nn.Module):
    """多层感知机模型"""

    def __init__(self, input_dim: int, hidden_dims: List[int], output_dim: int):
        super(MLPModel, self).__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class PolicyNetworkPyTorch:
    """PyTorch策略网络（多头）"""

    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        """
        初始化PyTorch策略网络

        Args:
            state_dim: 状态维度
            action_dim: 动作维度（应为11）
            hidden_dims: 隐藏层维度列表
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch不可用，请使用NumPy版本")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims or [128, 128]

        self.head_dims = {
            "agent": 3,
            "automation": 3,
            "style": 3,
            "confirm": 2
        }

        # 共享骨干网络
        layers = []
        prev_dim = state_dim
        for hidden_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        self.backbone = nn.Sequential(*layers)

        # 多头输出层
        self.heads = nn.ModuleDict({
            name: nn.Linear(prev_dim, dim)
            for name, dim in self.head_dims.items()
        })

        # 优化器
        self.optimizer = torch.optim.Adam(
            list(self.backbone.parameters()) + list(self.heads.parameters()),
            lr=0.001
        )

    def _forward_logits(self, state_tensor: torch.Tensor) -> Dict[str, torch.Tensor]:
        """前向传播，获取各头logits"""
        features = self.backbone(state_tensor)
        return {name: head(features) for name, head in self.heads.items()}

    def get_action_probs(self, state: np.ndarray) -> Dict[str, np.ndarray]:
        """获取动作概率分布（多头）"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state)
            logits = self._forward_logits(state_tensor)
            probs = {name: F.softmax(head_logits, dim=-1).numpy() for name, head_logits in logits.items()}
            return probs

    def sample_action(self, state: np.ndarray, explore: bool = True) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """采样动作"""
        action_probs = self.get_action_probs(state)

        if explore and np.random.random() < 0.1:
            action_indices = np.array([
                np.random.randint(self.head_dims["agent"]),
                np.random.randint(self.head_dims["automation"]),
                np.random.randint(self.head_dims["style"]),
                np.random.randint(self.head_dims["confirm"])
            ], dtype=int)
        else:
            action_indices = np.array([
                np.random.choice(self.head_dims["agent"], p=action_probs["agent"]),
                np.random.choice(self.head_dims["automation"], p=action_probs["automation"]),
                np.random.choice(self.head_dims["style"], p=action_probs["style"]),
                np.random.choice(self.head_dims["confirm"], p=action_probs["confirm"])
            ], dtype=int)

        return action_indices, action_probs

    def update(self, state: np.ndarray, action_indices: np.ndarray, advantage: float) -> float:
        """更新策略网络"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        logits = self._forward_logits(state_tensor)

        # 计算损失（多头累加）
        loss = 0.0
        head_order = ["agent", "automation", "style", "confirm"]
        for head_idx, head_name in enumerate(head_order):
            log_prob = F.log_softmax(logits[head_name], dim=-1)
            loss = loss - log_prob[0, int(action_indices[head_idx])] * advantage

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return float(loss.item())

    def save(self, path: str) -> None:
        """保存模型"""
        torch.save({
            "backbone": self.backbone.state_dict(),
            "heads": self.heads.state_dict()
        }, path)

    def load(self, path: str) -> None:
        """加载模型"""
        state = torch.load(path)
        self.backbone.load_state_dict(state["backbone"])
        self.heads.load_state_dict(state["heads"])


class ValueNetworkPyTorch:
    """PyTorch价值网络"""

    def __init__(self, state_dim: int, hidden_dims: List[int] = None):
        """
        初始化PyTorch价值网络

        Args:
            state_dim: 状态维度
            hidden_dims: 隐藏层维度列表
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch不可用，请使用NumPy版本")

        self.state_dim = state_dim
        self.hidden_dims = hidden_dims or [128, 128]

        # 创建MLP模型（输出1维）
        self.model = MLPModel(state_dim, self.hidden_dims, 1)

        # 优化器
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

    def forward(self, state: np.ndarray) -> float:
        """前向传播"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state)
            value = self.model(state_tensor)
            return value.item()

    def update(self, state: np.ndarray, target_value: float) -> float:
        """更新价值网络"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        value = self.model(state_tensor)

        # 计算损失（MSE）
        target_tensor = torch.FloatTensor([target_value])
        loss = F.mse_loss(value, target_tensor)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def save(self, path: str) -> None:
        """保存模型"""
        torch.save(self.model.state_dict(), path)

    def load(self, path: str) -> None:
        """加载模型"""
        self.model.load_state_dict(torch.load(path))


def create_policy_network(state_dim: int, action_dim: int,
                          use_pytorch: bool = True):
    """
    创建策略网络（自动选择PyTorch或NumPy版本）

    Args:
        state_dim: 状态维度
        action_dim: 动作维度
        use_pytorch: 是否尝试使用PyTorch

    Returns:
        策略网络实例
    """
    if use_pytorch and TORCH_AVAILABLE:
        return PolicyNetworkPyTorch(state_dim, action_dim)
    else:
        return NumpyPolicyNetwork(state_dim, action_dim)


def create_value_network(state_dim: int, use_pytorch: bool = True):
    """
    创建价值网络（自动选择PyTorch或NumPy版本）

    Args:
        state_dim: 状态维度
        use_pytorch: 是否尝试使用PyTorch

    Returns:
        价值网络实例
    """
    if use_pytorch and TORCH_AVAILABLE:
        return ValueNetworkPyTorch(state_dim)
    else:
        return NumpyValueNetwork(state_dim)


def main():
    """测试神经网络模型"""
    state_dim = 17
    action_dim = 11

    print(f"PyTorch可用: {TORCH_AVAILABLE}")

    # 创建网络
    policy_net = create_policy_network(state_dim, action_dim)
    value_net = create_value_network(state_dim)

    print(f"✅ 策略网络: {type(policy_net).__name__}")
    print(f"✅ 价值网络: {type(value_net).__name__}")

    # 测试前向传播
    state = np.random.randn(state_dim)

    action_probs = policy_net.get_action_probs(state)
    value = value_net.forward(state)

    print(f"动作概率: {action_probs}")
    print(f"状态价值: {value:.3f}")


if __name__ == "__main__":
    main()
