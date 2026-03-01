# 架构说明

## 核心流程

1. `collector` 收集项目信号。
2. `learner` 学习或更新偏好。
3. `environment` 将上下文映射为 RL 状态。
4. `agent` 选择动作并更新策略。
5. `reward` 计算多维加权奖励。
6. `trainer` 管理 episode 与 checkpoint。

## 模块分层

- 核心 RL：`reward.py`、`environment.py`、`agent.py`、`learner.py`、`trainer.py`
- 可选 Phase3：分布式训练、自动调参、监控、性能优化
- 集成层：`integration.py` 对外暴露任务开始/结束接口

## 契约

状态/动作维度以 `lib/contracts.py` 为唯一事实来源。
