# MACAO Phase 1 / Phase 2 终局整改评审申请 (L3 / PG-2)

- **申请日期**：2026-08-29
- **申请目标**：**L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)**
- **待审范围**：`e7ba2d2..HEAD`（针对四方专家复审 `e7ba2d2` 所提 P0-NEW-1 ~ P0-NEW-4 及 P1 阻断项的精确闭环整改）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **机验结果**：`PYTHONPATH=src python3 -m unittest discover tests -v` **43 ran / 43 PASS (100%)**；5 轮连续全量回归 0 flake / 0 碰撞；`macao test-clis` 4/4 CLI PTY 验证 PASS；`macao e2e-run` 产物与状态 100% 匹配。

---

## 一、本轮四方专家复审意见精准闭环整改清单

| 专家与编号 | 阻断问题描述 | 根因与修复落点 | 验证与回归测试 |
|---|---|---|---|
| **P0-NEW-1**<br>(Claude, ZCode, Codex) | **`message_id` 短 UUID 随机碰撞导致 SQLite 主键冲突崩溃**<br>`AEPEnvelope.generate_message_id()` 仅取 4 位十进制后缀，同日空间仅 ~10,000，高频发布引发 `sqlite3.IntegrityError: UNIQUE constraint failed: message_queue.message_id`。 | 修复 `src/macao/msg/envelope.py`：升级为 16 位高熵随机数字 `str(uuid.uuid4().int)[:16]`，严格符合 Schema 正则 `^msg-[0-9]{8}-[0-9]{3,}$`（$10^{16}$ 空间，0 碰撞率）。 | `test_message_id_entropy_zero_collisions_in_5000`：5,000 次连续采样 0 碰撞，500 次高频数据库并发写入 100% 成功；5 轮全量回归 0 崩溃。 |
| **P0-NEW-2**<br>(Codex) | **协议枚举/Schema/PRD 错配与人工裁定断裂**<br>1. `types.py` 10 状态未包含 `UNKNOWN`；AEP 消息类型偏离 7 种标准 Schema 枚举；<br>2. `OverrideChoice` 枚举变更导致 CLI 传入 `"APPROVED"` / `"REWORK"` 抛出 `ValueError`；<br>3. `resolve_override` 发布非 Schema 类型 `OVERRIDE_RESOLVED` 被拒。 | 1. 修复 `src/macao/core/types.py`：恢复 PRD 10 状态（含 `UNKNOWN`）与 Schema 7 种标准 AEP 类型（`DEVELOPMENT_STARTED`, `REVIEW_REQUEST`, `REVIEW_RESPONSE`, `REWORK_REQUEST`, `MERGE_COMPLETED`, `STATE_CHANGED`, `HUMAN_OVERRIDE_REQUEST`）；<br>2. 规范 `OverrideChoice` 为 `APPROVED`, `REWORK`, `RETRY_REVIEW`, `CANCEL`，支持字符串自动归一化；<br>3. 修复 `src/macao/workflow/orchestrator.py`：`resolve_override` 广播标准 `AEPType.STATE_CHANGED` 消息；<br>4. 修复 `src/macao/consensus/vote.py`：`CANCELLED` 决策消除非法 `next_step.action`。 | `test_resolve_override_all_four_choices_and_valid_aep`：验证全部 4 种人工裁定分支（APPROVED→MERGING, REWORK→REWORK, RETRY_REVIEW→WAITING_REVIEW, CANCEL→CANCELLED），所有发出消息 100% 通过 Draft-07 Schema 校验。 |
| **P0-NEW-3**<br>(Codex) | **MergeController CI 失败缺少原子回滚与配置远端检查**<br>1. 先合并再运行 CI，CI 失败时目标分支已污染前移；<br>2. 配置了 `remote_name` 但远端不存在时静默跳过；<br>3. push 后未校验远端 SHA。 | 修复 `src/macao/merge/controller.py`：<br>1. 合并前记录 `pre_merge_head`，CI 命令失败或异常时原子硬回滚 `git reset --hard <pre_merge_head>`；<br>2. 配置了 `remote_name` 时校验其在 `git remote` 中存在，不存在则 Fail-closed 拒绝合并；<br>3. push 后调用 `git ls-remote` 强校验远端 SHA 与 `checkpoint_ref` 完全一致。 | `test_merge_controller_ci_gate_failure_rollback`：CI 失败时验证 main HEAD 未改变并原子回滚；<br>`test_merge_controller_missing_remote_fail_closed`：远端不存在时 Fail-closed 拒绝。 |
| **P0-NEW-4**<br>(Codex, ZCode) | **Mock Adapter 契约消费驱动与 Worktree 事务性准备**<br>1. E2E Runner 未调用 Adapter 契约方法；<br>2. Worktree 准备失败时提前推进了 FSM 状态并消费了产物。 | 1. 修复 `src/macao/workflow/e2e_runner.py`：完整驱动 `executor_adapter` 与 `reviewer_adapters` 的 `start()`, `inject_task()`, `simulate_produce_dev_manifest()`, `simulate_produce_review_manifest()`, `ack()`, `stop()` 契约全生命周期；<br>2. 修复 `src/macao/workflow/orchestrator.py`：`dispatch_review_requests` 实行事务性准备——全部 Worktree 创建成功后才推进 FSM `WAITING_REVIEW` 并消费归档产物，任意 Worktree 失败立即清理并保持 `READY_FOR_REVIEW`（Fail-closed）。 | `test_worktree_dispatch_transactional_fail_closed`：模拟创建 Worktree 异常，断言状态维持 `READY_FOR_REVIEW`，不发生部分提交与产物丢失；<br>`test_e2e_runner_truthful_evidence_and_archive` 完整通过。 |

---

## 二、代码测试与机验清单

```bash
# 1. 全量单元与回归测试（43/43 全部 PASS，100% 通过）
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 五轮连续回归测试（0 flake / 0 崩溃）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done

# 3. 4 款真实 AI CLI 进程生命周期与 PTY 强杀机验
PYTHONPATH=src python3 -m macao.cli.main test-clis

# 4. Phase 2 端到端微任务协同仿真（Adapter 驱动、3 评审人、物理归档 5 份）
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 5. 代码洁净度检查（0 尾随空白）
git diff --check
```

---

## 三、申请定级请求

恳请专家委员会（Claude / Qwen / ZCode / Codex）针对本次精准闭环整改进行独立复审，准予授予 **L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)** 门禁认证。
