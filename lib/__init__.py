"""
OpenClaw Alignment - explainable confirmation and local policy memory.

Phase 1-2: confirmation policy core, local policy memory, and optional RL optimization
Phase 3: advanced optional modules (distributed training, tuning, monitoring, performance)
"""

from __future__ import annotations

from typing import Any

# Phase 1: core module（always available）
from .reward import RewardSignal, RewardCalculator
from .environment import InteractionEnvironment, State, Action
from .agent import AlignmentAgent, PolicyNetwork, ValueNetwork
from .learner import RLLearner
from .experience_replay import Experience, ExperienceReplay
from .trainer import RLTrainer
from .paths import (
    get_config_dir,
    get_cache_dir,
    get_state_dir,
    resolve_config_path,
    resolve_model_dir,
)

# Policy memory module
from .policy_models import Rule, Playbook, PolicyEvent
from .policy_store import PolicyStore
from .md_to_policy import MarkdownToPolicyConverter
from .policy_to_md import PolicyToMarkdownExporter

# Intelligent Confirmation module
from .confirmation import IntelligentConfirmation, RiskLevel

# API module
from .api import ConfirmationAPI, create_api

# CLI module
from .cli import OpenClawAlignmentCLI

# Optional exports（Injection by dependency availability at runtime）
MLPModel: Any = None
PolicyNetworkPyTorch: Any = None
ValueNetworkPyTorch: Any = None
create_policy_network: Any = None
create_value_network: Any = None
TORCH_AVAILABLE = False

DistributedTrainer: Any = None
DistributedTrainingConfig: Any = None

LearningRateScheduler: Any = None
HyperparameterSearch: Any = None
EarlyStopping: Any = None
HyperparameterTuner: Any = None

TrainingMonitor: Any = None
MetricsAnalyzer: Any = None
TENSORBOARD_AVAILABLE = False

BatchInference: Any = None
ModelQuantization: Any = None
InferenceCache: Any = None
JITOptimizer: Any = None
PerformanceOptimizer: Any = None

try:
    from . import nn_model as _nn_model

    MLPModel = _nn_model.MLPModel
    PolicyNetworkPyTorch = _nn_model.PolicyNetworkPyTorch
    ValueNetworkPyTorch = _nn_model.ValueNetworkPyTorch
    create_policy_network = _nn_model.create_policy_network
    create_value_network = _nn_model.create_value_network
    TORCH_AVAILABLE = _nn_model.TORCH_AVAILABLE
except Exception:
    pass

try:
    from . import distributed_trainer as _distributed_trainer

    DistributedTrainer = _distributed_trainer.DistributedTrainer
    DistributedTrainingConfig = _distributed_trainer.DistributedTrainingConfig
except Exception:
    pass

try:
    from . import hyperparameter_tuner as _hyperparameter_tuner

    LearningRateScheduler = _hyperparameter_tuner.LearningRateScheduler
    HyperparameterSearch = _hyperparameter_tuner.HyperparameterSearch
    EarlyStopping = _hyperparameter_tuner.EarlyStopping
    HyperparameterTuner = _hyperparameter_tuner.HyperparameterTuner
except Exception:
    pass

try:
    from . import monitoring as _monitoring

    TrainingMonitor = _monitoring.TrainingMonitor
    MetricsAnalyzer = _monitoring.MetricsAnalyzer
    TENSORBOARD_AVAILABLE = _monitoring.TENSORBOARD_AVAILABLE
except Exception:
    pass

try:
    from . import performance_optimizer as _performance_optimizer

    BatchInference = _performance_optimizer.BatchInference
    ModelQuantization = _performance_optimizer.ModelQuantization
    InferenceCache = _performance_optimizer.InferenceCache
    JITOptimizer = _performance_optimizer.JITOptimizer
    PerformanceOptimizer = _performance_optimizer.PerformanceOptimizer
except Exception:
    pass

__all__ = [
    # Phase 1
    "RewardSignal",
    "RewardCalculator",
    "InteractionEnvironment",
    "State",
    "Action",
    "AlignmentAgent",
    "PolicyNetwork",
    "ValueNetwork",
    "RLLearner",
    "RLAlignmentEngine",
    "Experience",
    "ExperienceReplay",
    "RLTrainer",
    "get_config_dir",
    "get_cache_dir",
    "get_state_dir",
    "resolve_config_path",
    "resolve_model_dir",
    # Policy memory
    "Rule",
    "Playbook",
    "PolicyEvent",
    "PolicyStore",
    "MarkdownToPolicyConverter",
    "PolicyToMarkdownExporter",
    # Intelligent Confirmation
    "IntelligentConfirmation",
    "RiskLevel",
    # API
    "ConfirmationAPI",
    "create_api",
    # Phase 2
    "MLPModel",
    "PolicyNetworkPyTorch",
    "ValueNetworkPyTorch",
    "create_policy_network",
    "create_value_network",
    "TORCH_AVAILABLE",
    # Phase 3
    "DistributedTrainer",
    "DistributedTrainingConfig",
    "LearningRateScheduler",
    "HyperparameterSearch",
    "EarlyStopping",
    "HyperparameterTuner",
    "TrainingMonitor",
    "MetricsAnalyzer",
    "TENSORBOARD_AVAILABLE",
    "BatchInference",
    "ModelQuantization",
    "InferenceCache",
    "JITOptimizer",
    "PerformanceOptimizer",
    # CLI
    "OpenClawAlignmentCLI",
]


def __getattr__(name: str) -> Any:
    if name == "RLAlignmentEngine":
        # Delayed import，avoid `python -m lib.integration` Warning when module is loaded repeatedly
        from .integration import RLAlignmentEngine as _RLAlignmentEngine

        return _RLAlignmentEngine
    raise AttributeError(f"module 'lib' has no attribute '{name}'")


__version__ = "2.0.0"
