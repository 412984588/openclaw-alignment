"""
OpenClaw Alignment - Reinforcement Learning Alignment System

Phase 1-2: Core features and optimizations
Phase 3: Advanced features（Distributed training、Automatic parameter adjustment、monitor、Performance optimization）
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

# GEP module（Gene Evolution Protocol）
from .gep import Gene, Capsule, Event
from .gep_store import GEPStore
from .md_to_gep import MarkdownToGEPConverter
from .gep_to_md import GEPToMarkdownExporter

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
    # GEP
    "Gene",
    "Capsule",
    "Event",
    "GEPStore",
    "MarkdownToGEPConverter",
    "GEPToMarkdownExporter",
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


__version__ = "1.0.1"
