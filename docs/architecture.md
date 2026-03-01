# Architecture

## Core Flow

1. `collector` gathers project signals.
2. `learner` builds or updates preferences.
3. `environment` maps context to RL state.
4. `agent` selects actions and updates policy.
5. `reward` computes weighted reward signals.
6. `trainer` orchestrates episodes and checkpoints.

## Module Layers

- Core RL: `reward.py`, `environment.py`, `agent.py`, `learner.py`, `trainer.py`
- Optional Phase3: distributed training, hyperparameter tuning, monitoring, performance
- Integration: `integration.py` provides task-start/task-complete API surface

## Contracts

`lib/contracts.py` is the single source of truth for state/action dimensions.
