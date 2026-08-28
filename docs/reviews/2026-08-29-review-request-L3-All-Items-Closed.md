# MACAO Phase 1 / Phase 2 全量阻断项闭环与超时单测终局评审申请 (L3 / PG-2)

- **申请日期**：2026-08-29
- **申请目标**：**L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)**
- **待审范围**：`4df059e..HEAD`（针对四方专家复审 `4df059e` 所提 REQ-TIMEOUT、P0-1、P0-2、P1-1、P1-2、P2-1、P2-2 的全量单点闭环整改）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **机验结果**：`PYTHONPATH=src python3 -m unittest discover tests -v` **49 ran / 49 PASS (100%)**；5 轮连续全量回归 0 flake / 0 碰撞；`macao test-clis` 4/4 CLI PTY 验证 PASS；`macao e2e-run` 产物与状态 100% 匹配。

---

## 一、本轮四方专家复审意见精准闭环整改清单

| 编号 | 严重度 | 阻断问题描述 | 根因与修复落点 | 验证与回归测试 |
|---|---|---|---|---|
| **REQ-TIMEOUT**<br>(ZCode, Codex) | **阻断** | **L3 判据明列的"超时"场景测试证据缺失**<br>缺少 Reviewer 超时未响应 → 标记弃权 → 仲裁死锁 → 人工接管全链路测试证据。 | 修复 `src/macao/workflow/orchestrator.py`：`collect_and_evaluate_consensus` 增加超时判定与弃权合成逻辑，未响应 Reviewer 自动计入 `ABSTAIN` 并在有效票不足时安全进入 `DEADLOCK`（HOLD），发布 `HUMAN_OVERRIDE_REQUEST`。 | `test_reviewer_timeout_degradation_scenario`：完整测试超时 Reviewer 标记弃权、法定人数不足触发死锁、不提前写盘、发布接管请求、人工裁定批准合并全流程（PASS）。 |
| **P0-1**<br>(Codex) | **阻断** | **`task_id` 秒级时间戳同秒并发主键冲突**<br>`start_task()` 仅使用秒级时间戳，同秒连续调用抛出 `sqlite3.IntegrityError`。 | 修复 `src/macao/workflow/orchestrator.py`：`t_id = task_id or f"task-{date_str}-{uuid.uuid4().hex[:6]}"`，引入高熵 UUID 后缀保证并发唯一性。 | `test_task_id_concurrency_no_collision_in_100_tasks`：同秒并发生成 100 个任务 0 碰撞，100% 成功。 |
| **P0-2**<br>(Codex) | **阻断** | **达到最大返工轮次时 HOLD 却提前写盘自动 REWORK_REQUIRED**<br>`collect_and_evaluate_consensus()` 在检查上限前落盘，导致崩溃恢复绕过人工接管。 | 修复 `src/macao/workflow/orchestrator.py`：当 `rnd >= max_rework_rounds` 时严格与 DEADLOCK 一致——**DO NOT WRITE vote_result.json**，HOLD 在 `CONSENSUS_CHECK` 并发布 `HUMAN_OVERRIDE_REQUEST`。 | `test_max_rework_rounds_reached_holds_without_writing_disk_vote_result`：断言磁盘绝无自动文件、崩溃恢复后状态依旧稳固保持 `CONSENSUS_CHECK`。 |
| **P0-3**<br>(Codex) | **阻断** | **MergeController 对工作区未提交修改的保护**<br>避免工作区存在未提交文件时发生合并破坏。 | 修复 `src/macao/merge/controller.py`：合并前检查 `git diff --name-only` 与 `git diff --cached`，若存在未提交已跟踪修改则 Fail-closed 拒绝合并。 | `test_merge_controller_refuses_dirty_worktree_fail_closed`：工作区有脏数据时拒绝合并且数据完整保留（PASS）。 |
| **P1-1**<br>(Claude) | **重要** | **Worktree 异常清理方法名缺失与物理清理**<br>`orchestrator.py` 调用了未定义的 `remove_isolated_worktree`。 | 修复 `src/macao/utils/git_utils.py`：补齐 `remove_isolated_worktree(reviewer_id, task_id, review_round)` 方法，执行 `worktree remove --force` 与目录删除。 | `test_worktree_dispatch_exception_physically_cleans_created_worktrees`：断言第 2 个 reviewer 创建失败时，第 1 个 reviewer 的 worktree 目录被物理清理（PASS）。 |
| **P1-2**<br>(Claude) | **重要** | **恢复 `register_artifact` 生产流程调用点**<br>产物注册方法无调用点导致 `artifacts` 表为空。 | 修复 `src/macao/workflow/orchestrator.py`：在 `check_development_checkpoint`、`collect_and_evaluate_consensus` 及 `resolve_override` 中完整恢复 `register_artifact` 调用。 | `test_artifacts_registered_and_tracked_in_database`：E2E 全流程后断言 `artifacts` 表正确记录 5 份产物（dev_manifest / review_manifest / vote_result）。 |
| **P2-1**<br>(ZCode) | **建议** | **`consensus/vote.py` 先校验后写盘顺序复原**<br>避免非法产物先污染磁盘再报错。 | 修复 `src/macao/consensus/vote.py`：将 `validate_vote_result(result)` 恢复至 `write_to_disk` 之前，确保 Fail-closed。 | `test_vote_result_validation_before_write_and_fail_fast_on_invalid_resolution` PASS。 |
| **P2-2**<br>(ZCode, Qwen) | **建议** | **`human_resolution` 非法输入 Fail-fast 校验**<br>避免未知输入静默降级为 APPROVED。 | 修复 `src/macao/consensus/vote.py`：未知非法输入直接抛出 `ValueError` fail-fast。 | `test_vote_result_validation_before_write_and_fail_fast_on_invalid_resolution` PASS。 |

---

## 二、代码测试与机验清单

```bash
# 1. 全量 49 项单元与回归测试（49/49 全部 PASS，100% 通过）
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 五轮连续全量回归（0 flake / 0 碰撞 / 0 崩溃）
for i in {1..5}; do PYTHONPATH=src python3 -m unittest discover tests -v > /dev/null || exit 1; echo "Run $i PASS"; done

# 3. 4 款真实 AI CLI 进程生命周期与 PTY 强杀机验
PYTHONPATH=src python3 -m macao.cli.main test-clis

# 4. Phase 2 端到端微任务协同仿真（Adapter 驱动、3 评审人、物理归档 5 份、数据库跟踪 5 份）
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 5. 代码差异洁净度
git diff --check
```

---

## 三、申请定级请求

四方专家提出的全部阻断项（含 L3 超时场景单测证据、高熵 task_id、max-round 不提前写盘、工作区防护、Worktree 清理、Artifact 追踪及 vote 校验）已全部单点闭环并经过 49 项高覆盖回归测试验证。

恳请专家委员会（Claude / Qwen / ZCode / Codex）进行独立复审，准予授予 **L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)** 门禁认证。
