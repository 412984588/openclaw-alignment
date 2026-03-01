# Task Plan: 强化学习奖励机制实施

## Goal

将 openclaw-alignment 从简单统计学习升级为完整的强化学习系统，实现 Actor-Critic 架构 + 四维度奖励信号 + 动态权重调整

## Phases

- [ ] Phase 1: 核心功能实现 (2600行, 2-3周)
  - [ ] 1.1 奖励系统 (lib/reward.py) - 600行
  - [ ] 1.2 交互环境 (lib/environment.py) - 400行
  - [ ] 1.3 RL智能体 (lib/agent.py) - 800行
  - [ ] 1.4 集成引擎扩展 (lib/integration.py) - 300行
  - [ ] 1.5 学习器重构 (lib/learner.py) - 400行

- [ ] Phase 2: 优化功能 (1650行, 1-2周)
  - [ ] 2.1 神经网络模型 (lib/nn_model.py) - 300行
  - [ ] 2.2 经验回放 (lib/experience_replay.py) - 150行
  - [ ] 2.3 训练器 (lib/trainer.py) - 300行
  - [ ] 2.4 反馈收集扩展 (lib/collector.py) - 200行

- [ ] Phase 3: 高级功能 (700行, 1周)
  - [ ] 3.1 分布式训练支持
  - [ ] 3.2 自动调参
  - [ ] 3.3 监控面板
  - [ ] 3.4 性能优化

- [ ] Phase 4: 测试与文档
  - [ ] 4.1 单元测试
  - [ ] 4.2 集成测试
  - [ ] 4.3 文档更新

## Status

**Currently in Phase 1** - 开始实现核心功能

## Decisions Made

- 使用 Actor-Critic (A2C) 算法 - 平衡性能和实现复杂度
- 分层实现：Phase 1 用 NumPy，Phase 2 可选 PyTorch
- 保持向后兼容：统计学习作为 fallback

## Technical Stack

- **Phase 1**: NumPy (零 ML 依赖)
- **Phase 2**: 可选 PyTorch (智能降级)
- **依赖控制**: requirements-core.txt vs requirements-full.txt

## Architecture

```
OpenClaw任务执行
      ↓
1. on_task_start(task_context)
   - Agent选择策略
   - 返回推荐 (agent/automation/style)
      ↓
2. 执行任务（使用推荐策略）
   - 调用选定的Agent
   - 按照automation_level执行
      ↓
3. on_task_complete(task_result)
   - 收集隐式反馈（测试覆盖率等）
   - 计算奖励
   - 更新策略
      ↓
4. collect_explicit_feedback()
   - 用户主动评分（可选）
   - 负向反馈触发策略调整
```

## Implementation Order (按依赖顺序)

1. lib/reward.py - 奖励计算核心（无依赖）
2. lib/environment.py - 状态/动作空间（依赖reward.py）
3. lib/agent.py - RL智能体（依赖environment.py）
4. lib/learner.py - 重构为RLLearner（依赖agent.py）
5. lib/integration.py - 扩展集成接口（依赖learner.py）

## Success Criteria

- Phase 1: 能运行完整episode，奖励计算正确，策略能更新
- Phase 2: 神经网络训练，经验回放生效，训练曲线收敛
- Phase 3: 多项目并行训练，可视化监控，模型<10MB

## Notes

- 每个模块都要有单元测试
- 测试覆盖率要求：≥80%
- 性能目标：单次step <100ms
