# Fix Log

## Batch P0

### F-001 CLI 参数崩溃

- File: `lib/integration.py`
- Change: `parser.add_argument("--repo", default=".")`
- Test:
  - `tests/test_integration_cli.py::test_integration_module_help`

## Batch P1

### F-002 task_type 规范化

- File: `lib/environment.py`
- Change:
  - `reset()` 将非法 task_type 回退为 `T2`
  - 规范化后写回 `current_task_context`
- Test:
  - `tests/test_environment.py::TestInteractionEnvironment::test_reset_invalid_task_type_fallback_to_t2`

### F-003 time_of_day 输入防护

- File: `lib/environment.py`
- Change:
  - `time_of_day` 安全转 float
  - 非法值回退中午（12）
  - 超范围值 clamp 到 `[0, 24]`
- Test:
  - `tests/test_environment.py::TestInteractionEnvironment::test_reset_clamps_time_of_day_into_valid_range`
  - `tests/test_environment.py::TestInteractionEnvironment::test_reset_invalid_time_of_day_uses_default_noon`

### F-004 配置结构保真写入

- File: `lib/integration.py`
- Change:
  - `update_preferences()` 保留顶层配置结构
  - 自动创建配置目录
- Test:
  - `tests/test_integration_engine.py::test_update_preferences_preserves_config_wrapper`
  - `tests/test_integration_engine.py::test_update_preferences_creates_config_parent_dir`

### F-005 推理确定性

- File: `lib/agent.py`
- Change: `sample_action(explore=False)` 改为每头 `argmax` 贪心选择
- Test:
  - `tests/test_agent_policy.py::test_policy_no_explore_is_deterministic`

### F-006 动作索引显式校验

- File: `lib/agent.py`
- Change: `decode_action_indices()` 增加长度与范围校验，统一抛 `ValueError`
- Test:
  - `tests/test_agent_policy.py::test_decode_action_indices_invalid_shape_or_range`

## Batch P2

### F-007 无效计算清理

- File: `lib/agent.py`
- Change: 移除 `update_policy()` 未使用的 `returns` 中间计算
- Test impact:
  - 全量回归覆盖

## Release Gate Batch

### F-008 sdist 治理文档完整性

- File: `MANIFEST.in`
- Change: 显式包含 `CHANGELOG/CONTRIBUTING/SECURITY/SUPPORT/CODE_OF_CONDUCT/RELEASING` 中英文件
- Verification:
  - `tar -tzf dist/openclaw_alignment-1.0.0.tar.gz | rg \"CONTRIBUTING|SECURITY|SUPPORT|CODE_OF_CONDUCT|RELEASING|CHANGELOG\"`

### F-009 changelog 发布信息补全

- File: `CHANGELOG.md`
- Change:
  - 补充 `Added/Changed/Fixed/Security/Breaking/Known Limitations`
  - 记录 1.0.0 关键发布价值与风险

### F-010 安全上报通道明确化

- Files: `SECURITY.md`, `SECURITY.zh-CN.md`
- Change:
  - 增加 GitHub private advisory 入口链接
  - 增加安全邮箱占位与发布前替换提示

### F-011 full 依赖路径稳定性

- Files: `lib/distributed_trainer.py`, `.github/workflows/ci.yml`, `tests/test_phase3.py`
- Change:
  - 分布式运行时增加 Redis/Worker 可用性探测，不可用则自动降级
  - 分布式任务提交失败时自动降级为顺序训练
  - CI 新增 `phase3-full-deps` job
  - 新增用例：`test_fallback_when_runtime_unreachable`
- Test:
  - `python3 -m pip install -r requirements-full.txt`
  - `python3 -m pytest tests/test_phase3.py -q`
