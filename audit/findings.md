# Audit Findings

## P0

1. `lib/integration.py` CLI 参数定义错误导致 `python -m lib.integration --help` 崩溃。
   - Impact: CLI 不可用。
   - Repro: `python3 -m lib.integration --help`
   - Status: fixed

## P1

1. `InteractionEnvironment.reset()` 对非法 `task_type` 仅局部回退，内部上下文仍保留非法值。
   - Impact: 后续奖励计算可能基于错误 task_type。
   - Status: fixed

2. `InteractionEnvironment.reset()` 对非法 `time_of_day` 输入会抛异常；超范围值未规范化。
   - Impact: 外部输入易触发异常或状态漂移。
   - Status: fixed

3. `IntentAlignmentEngine.update_preferences()` 会覆盖配置结构，丢失顶层字段（如 `version`），且不会自动创建父目录。
   - Impact: 配置损坏或写入失败。
   - Status: fixed

4. `PolicyNetwork.sample_action(explore=False)` 之前是随机采样，推理推荐不稳定。
   - Impact: 同状态推荐抖动，难以复现。
   - Status: fixed

5. `AlignmentAgent.decode_action_indices()` 对越界/错误维度输入错误语义不明确。
   - Impact: 调试困难，调用方难以恢复。
   - Status: fixed

## P2

1. `AlignmentAgent.update_policy()` 存在无效中间计算（未使用回报列表）。
   - Impact: 微小性能损耗，可维护性下降。
   - Status: fixed

## Release Gate Recheck

1. `B1`（误报）: CI 引用缺失测试文件。
   - Evidence: `.github/workflows/ci.yml` 引用 `tests/test_phase3.py`，文件存在。
   - Status: closed (false-positive)

2. `B2`: sdist 缺少治理文档（CONTRIBUTING/SECURITY/SUPPORT/CODE_OF_CONDUCT/RELEASING/CHANGELOG）。
   - Impact: 开源分发产物缺少关键治理信息。
   - Status: fixed

3. `B3`: `CHANGELOG.md` 作为 `1.0.0` 发布说明不完整。
   - Impact: 用户无法快速理解版本价值与风险。
   - Status: fixed

4. `H1`: `requirements-full.txt` 路径未在 CI 中验证。
   - Impact: 可选依赖安装或 Phase3 路径可能在发布后失败。
   - Status: fixed

5. `H2`: `SECURITY*.md` 缺少明确漏洞私密提交流程。
   - Impact: 安全问题无法规范上报。
   - Status: fixed
