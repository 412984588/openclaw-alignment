"""
OpenClaw Alignment - 强化学习对齐系统

Phase 1-2: 核心功能和优化
Phase 3: 高级功能（分布式训练、自动调参、监控、性能优化）
"""

# Phase 1: 核心模块
from .reward import RewardSignal, RewardCalculator
from .environment import InteractionEnvironment, State, Action
from .agent import AlignmentAgent, PolicyNetwork, ValueNetwork
from .learner import RLLearner
from .integration import RLAlignmentEngine

# Phase 2: 优化模块
from .nn_model import (
    MLPModel,
    PolicyNetworkPyTorch,
    ValueNetworkPyTorch,
    create_policy_network,
    create_value_network,
    TORCH_AVAILABLE
)
from .experience_replay import Experience, ExperienceReplay
from .trainer import RLTrainer

# Phase 3: 高级功能模块
from .distributed_trainer import (
    DistributedTrainer,
    DistributedTrainingConfig
)
from .hyperparameter_tuner import (
    LearningRateScheduler,
    HyperparameterSearch,
    EarlyStopping,
    HyperparameterTuner
)
from .monitoring import (
    TrainingMonitor,
    MetricsAnalyzer,
    TENSORBOARD_AVAILABLE
)
from .performance_optimizer import (
    BatchInference,
    ModelQuantization,
    InferenceCache,
    JITOptimizer,
    PerformanceOptimizer
)
from .paths import (
    get_config_dir,
    get_cache_dir,
    get_state_dir,
    resolve_config_path,
    resolve_model_dir,
)

__all__ = [
    # Phase 1
    "RewardSignal", "RewardCalculator",
    "InteractionEnvironment", "State", "Action",
    "AlignmentAgent", "PolicyNetwork", "ValueNetwork",
    "RLLearner", "RLAlignmentEngine",

    # Phase 2
    "MLPModel", "PolicyNetworkPyTorch", "ValueNetworkPyTorch",
    "create_policy_network", "create_value_network", "TORCH_AVAILABLE",
    "Experience", "ExperienceReplay",
    "RLTrainer",

    # Phase 3
    "DistributedTrainer", "DistributedTrainingConfig",
    "LearningRateScheduler", "HyperparameterSearch",
    "EarlyStopping", "HyperparameterTuner",
    "TrainingMonitor", "MetricsAnalyzer", "TENSORBOARD_AVAILABLE",
    "BatchInference", "ModelQuantization", "InferenceCache",
    "JITOptimizer", "PerformanceOptimizer",
    "get_config_dir", "get_cache_dir", "get_state_dir",
    "resolve_config_path", "resolve_model_dir",
]

__version__ = "1.0.0"
