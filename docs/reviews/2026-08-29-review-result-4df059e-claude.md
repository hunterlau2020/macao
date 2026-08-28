# MACAO 独立复审报告 — Phase 1/2 终局整改申请 (commit `e7ba2d2..4df059e`)

> **评审人**：claude（独立复审，不采信申请文档或 codex/zcode 既有报告的结论，逐条重新阅读源码 + 独立重跑命令 + 编写复现脚本）
> **评审日期**：2026-08-29
> **评审对象**：[`2026-08-29-review-request-L3-Final-Rectification.md`](2026-08-29-review-request-L3-Final-Rectification.md)
> **评审范围**：`git diff e7ba2d2..4df059e`（唯一代码提交 `4df059e`，12 文件，671+/367-），重点复核申请文档"一、本轮四方专家复审意见精准闭环整改清单"中 P0-NEW-1 ~ P0-NEW-4 共 4 项声明（分别对应我本人上轮发现的 `message_id` 碰撞，与 codex 上轮发现的协议枚举断裂 / MergeController CI 原子性 / Adapter 契约驱动+Worktree 事务性）。

---

## 一、结论

**不予 L3 SCENARIO-VERIFIED / PG-2 准入**，理由与上轮结构相同：**申请所列 4 项 P0-NEW 经独立复核全部真实闭环**（含高质量、可复现的修复与新增回归测试），但本轮改动本身**引入了 2 项此前未被任何专家提出的新缺陷**，均为确定性可复现（非概率性），故仍不满足 PG-1"P0/P1 为零"门槛。

值得明确肯定的是：本次整改在协议一致性（恢复 PRD 权威 10 状态与 7 类 AEP 消息）、合并流水线原子性（CI 失败硬回滚、缺失远端 fail-closed、推送后远端 SHA 校验）、`message_id` 熵值（16 位随机数字，10^16 空间）三个方向上的修复均扎实、可独立复现，且新增的 `test_p0_p1_rectification.py` 用例是真实断言（如四分支人工裁定逐一验证 Schema 合法性、CI 失败后 HEAD 精确回滚断言），不是自证空转的浅层测试。

---

## 二、四项 P0-NEW 逐条独立复核

| 编号 | 申请声明 | 独立复核方法 | 结论 |
|---|---|---|---|
| **P0-NEW-1**（message_id 碰撞，claude/zcode/codex 共同发现） | `generate_message_id()` 升级为 16 位十进制随机后缀（10^16 空间） | 读 `msg/envelope.py:16-24`：`str(uuid.uuid4().int)[:16].zfill(16)`；核对 `docs/schemas/aep_envelope.schema.json:9` 正则 `^msg-[0-9]{8}-[0-9]{3,}$` 兼容（`{3,}` 允许 16 位）；**连续 5 次 `python3 -m unittest discover tests` 全量运行，43/43 稳定通过，无一次崩溃**（上轮 4 次中 1 次崩溃）；实测 `bus.publish()` 循环 500 次无冲突（对照上轮"第 129 条即崩溃"的确定复现） | **✅ VERIFIED** |
| **P0-NEW-2**（协议枚举/人工裁定断裂，codex 发现） | 恢复 PRD 10 状态（含 `UNKNOWN`）与 Schema 7 类标准 AEP 类型；`OverrideChoice` 恢复为 `APPROVED/REWORK/RETRY_REVIEW/CANCEL`；`resolve_override` 改发布 `STATE_CHANGED` | 读 `core/types.py:8-30,62-67`：`AgentState` 含 `UNKNOWN`，`AEPType` 恰为 7 类标准值，`OverrideChoice` 恰为 4 值，均与 `cli/main.py:265-285`（`OverrideChoice(choice)`）及 `docs/schemas/aep_envelope.schema.json` 对齐；读 `orchestrator.py:527-530`：`resolve_override` 末尾发布 `AEPType.STATE_CHANGED`（合法值）；读 `workflow/transitions.py` diff：`HUMAN_OVERRIDE` 状态全部替换为 `UNKNOWN`，E7/E8/E9 转移规则同步重写且逻辑自洽；跑 `test_resolve_override_all_four_choices_and_valid_aep`（PASS，且该测试对全部 4 个分支产生的消息逐条调用 `validate_aep_envelope` 断言 Schema 合法，非仅检查状态跳转） | **✅ VERIFIED** |
| **P0-NEW-3**（MergeController CI 原子性/远端校验，codex 发现） | CI 失败/异常时 `git reset --hard <pre_merge_head>` 原子回滚；`remote_name` 已配置但不存在时 Fail-closed；push 后 `git ls-remote` 校验远端 SHA | 读 `merge/controller.py:59-123`：`pre_merge_head` 在 checkout 后、merge 前捕获；CI 失败/异常/HEAD 校验失败/远端缺失/push 失败/远端 SHA 不符 6 个分支均执行 `git reset --hard pre_merge_head` 后返回 `False`；跑 `test_merge_controller_ci_gate_failure_rollback`、`test_merge_controller_missing_remote_fail_closed`（均 PASS） | **✅ VERIFIED**（附残余观察：远端 SHA 校验失败分支仅回滚本地，未处理"push 已成功但远端已被并发覆盖"这一边缘场景下的远端状态，属极端场景，非本轮声称范围，不计入阻断） |
| **P0-NEW-4**（Adapter 契约驱动 + Worktree 事务性，codex 发现） | E2E Runner 完整驱动 `start/inject_task/simulate_produce_*/ack/stop`；`dispatch_review_requests` 事务性——全部 Worktree 成功后才推进 FSM，任一失败立即清理并保持 `READY_FOR_REVIEW` | 读 `e2e_runner.py:172-226`：executor/reviewer adapter 的 `start()/inject_task()/simulate_produce_dev_manifest()/simulate_produce_review_manifest()/ack()/stop()` 全部被真实调用（非绕过）；读 `orchestrator.py:202-260`：worktree 创建循环置于 FSM 转移**之前**，全部成功后才 `fsm.transition(..., WAITING_REVIEW, "E2")`；跑 `test_worktree_dispatch_transactional_fail_closed`（PASS：断言失败后状态仍为 `READY_FOR_REVIEW`） | **✅ "状态安全"部分 VERIFIED；"立即清理"部分证伪，见下方新发现 A** |

---

## 三、新发现（本轮改动自身引入，此前无专家提出）

### A（P1）：Worktree 失败清理调用不存在的方法，"事务性清理"实际从未执行，产生孤儿 Worktree

`orchestrator.py:244-248`：
```python
for rev_id, p in created_worktrees.items():
    try:
        self.git.remove_isolated_worktree(rev_id, task_id, rnd)
    except Exception:
        pass
```
`GitManager`（`utils/git_utils.py`）**没有 `remove_isolated_worktree` 方法**（只有接受 `Path` 参数的 `remove_worktree(worktree_path)`）。每次触发该清理分支都会抛 `AttributeError`，被 `except Exception: pass` 静默吞掉——清理代码 100% 从未真正执行。

**复现**（改造申请文档自带的 `test_worktree_dispatch_transactional_fail_closed` 场景，额外断言磁盘状态）：
```
$ python3 -c "... 见下方完整脚本 ..."
RuntimeError raised as expected: Security Gate Blocked: ...
rev1 worktree still on disk after failed dispatch (should be cleaned up): True
$ git worktree list
/tmp/tmpupgfzjmm                                   519ce76 [main]
/tmp/tmpupgfzjmm/.macao/worktrees/rev1/task-tx/r1  519ce76 (detached HEAD)
```
即：第一个 reviewer（`rev1`）的 worktree 已成功创建，第二个（`rev2`）失败触发异常；申请文档 P0-NEW-4 声称"任意 Worktree 失败立即清理"，但 `rev1` 的 worktree 在异常抛出、FSM 保持 `READY_FOR_REVIEW`（这一核心安全不变量确实成立，见上表）之后，**仍然遗留在磁盘与 `git worktree list` 中**，从未被移除。

`test_worktree_dispatch_transactional_fail_closed` 本身只断言了 FSM 状态（`READY_FOR_REVIEW`），未断言已创建 worktree 是否被清理，因此该回归测试无法捕获此缺陷——这不是虚报，而是测试覆盖盲区。

**影响**：非阻断安全属性（状态机不会带着不完整的评审分发前进），但会造成 `.macao/worktrees/` 下孤儿目录与孤儿 `git worktree` 注册项持续累积，多次失败重试后可能导致磁盘占用增长或后续同名 worktree 创建冲突。

**建议修复**：`GitManager` 增加 `remove_isolated_worktree(reviewer_id, task_id, review_round)` 方法（或改为调用既有 `remove_worktree(path)` 并传入 `created_worktrees[rev_id]`），并在回归测试中增加"失败后已创建的 worktree 已被物理清理"断言。

### B（P1）：`register_artifact()` 在生产路径中已无调用点，`artifacts` 表永久为空，"已归档物理产物"追踪功能静默失效

对比 `e7ba2d2` 与 `4df059e`：`e7ba2d2` 版本的 `orchestrator.py:150`（`check_development_checkpoint` 内）调用 `self.store.register_artifact(task_id=..., kind="dev_manifest", checkpoint_ref=..., review_round=rnd, path=dev_path)`；本轮重写该方法（新增 `content: Optional[bytes]` 参数、移除自动读取磁盘文件的逻辑）后，**全仓库 `grep -rn "register_artifact" src/macao/` 已无任何调用点**——只在 `storage/store.py` 中定义，从未被 orchestrator 或其他生产代码调用。而 `fsm.py:89,105` 仍在调用 `mark_artifact_consumed()`（纯 `UPDATE ... WHERE ...`，无 upsert），由于从未有对应行被 `register_artifact` 插入，这些 `UPDATE` 语句始终影响 0 行，等效于空操作。

**复现**：完整跑一次真实 `ControlledE2ERunner.run_e2e_cycle()`（7 步全部 OK，DONE，5 份产物物理归档），随后直接查询该任务的 `artifacts` 表：
```python
rows = conn.execute('SELECT * FROM artifacts WHERE task_id=?', (task_id,)).fetchall()
print(len(rows))   # -> 0
```
实测输出 `artifacts rows for this task: 0`——即便任务成功走完全生命周期并产生 5 份归档文件，`artifacts` 表中不会留下任何记录。

`tests/test_state_store.py::test_artifact_registration_and_append_semantics` 依旧 PASS，因为它直接调用 `store.register_artifact()`/`store.mark_artifact_consumed()`，绕开了 orchestrator 真实调用链，因此没有捕获"生产代码不再调用该方法"这一回归——同样是测试覆盖盲区，非虚报。

**影响**：`cli/ui.py::render_task_status()` 的"Tracked Physical Artifacts"表（`macao status <task_id>` 命令的一部分）此后对任何真实任务都会显示为空，是一项此前工作正常、本轮静默回归的用户可见功能缺陷。

**建议修复**：在 `check_development_checkpoint`（及审阅产物生成处）恢复对 `register_artifact()` 的调用（适配其新签名，传入 `content=` 字节内容），并补充一条覆盖"orchestrator 真实流程 → artifacts 表非空"的集成级回归测试（而非仅单元测试 store 方法本身）。

---

## 四、残余问题（非本轮声明范围，历史遗留，未改变判定但供归档）

- **`consensus/vote.py:119-128`**：未知 `human_resolution` 值仍静默落 `Decision.APPROVED`（qwen 上轮 R1，本轮未在整改清单内，代码确认未变，仍开放）。
- **`adapter/integ_harness.py:108-109`**：`ansi_stripped_ok = True` 仍为无条件常量（本人上轮发现，本轮该文件未被触碰，仍开放）。
- **`docs/POC_VERIFICATION_REPORT.md:25`**：本轮改动重新引入 1 处尾随空白（`git diff --check e7ba2d2 4df059e -- src/ tests/` 干净，问题仅限该文档文件），纯格式问题，非阻断。

---

## 五、正向确认

- 5 次连续 `python3 -m unittest discover tests` 全部 43/43 PASS，无 flake（对照上轮 4 次中 1 次因 message_id 崩溃）；
- `macao e2e-run` 复现：`votes_yes=3, effective_votes=3`, 5 份归档, `merge_exact_match=True`, 终态 `DONE`；
- `test_resolve_override_all_four_choices_and_valid_aep`、`test_merge_controller_ci_gate_failure_rollback`、`test_merge_controller_missing_remote_fail_closed`、`test_worktree_dispatch_transactional_fail_closed`、`test_message_id_entropy_zero_collisions_in_5000` 五个新增专项测试均为真实断言（非仅 `status=="PASS"` 式空转），独立复跑全部 PASS；
- `src/`、`tests/` 范围 `git diff --check` 完全干净。

---

## 六、准入建议

**暂不批准 L3 SCENARIO-VERIFIED / PG-2。** 上轮四方专家提出的 4 项 P0-NEW **全部真实闭环**，整改质量与本项目历轮一致地扎实、无虚报。但本轮改动自身引入 2 项新 P1 级回归（Worktree 孤儿清理失效、Artifact 追踪表永久置空），且均为**确定性 100% 可复现**（不同于此前 message_id 的概率性缺陷），故仍不满足 PG-1"P0/P1 为零"门槛。

**放行条件**（均为局部小修复，预计一轮内可闭环）：
1. `GitManager` 补齐 `remove_isolated_worktree()` 方法（或修正调用点），并补充"失败后 worktree 已被物理清理"的回归断言；
2. 恢复 `register_artifact()` 在 orchestrator 真实流程中的调用点，并补充"真实流程执行后 artifacts 表非空"的集成级回归测试；
3. （可选，非阻断）随手清理 `docs/POC_VERIFICATION_REPORT.md:25` 的尾随空白；`consensus/vote.py` 的未知 `human_resolution` fail-fast 化建议一并纳入下一轮小修复批次。
