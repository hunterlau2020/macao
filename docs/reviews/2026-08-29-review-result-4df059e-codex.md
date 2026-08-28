# L3 Final Rectification 独立复审（Codex）

- 评审日期：2026-08-29
- 评审对象：`e7ba2d2..4df059e`
- 基准：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- 结论：**REJECT；不准予 L3 SCENARIO-VERIFIED / PG-2**

## 1. 结论摘要

上一轮四个 P0 的主要修复均有实质进展：AEP/FSM/Override 枚举已重新对齐，message ID 空间扩大，missing remote 已 fail-closed，CI 失败会尝试回退，Worktree 创建也调整为先准备后转移；43/43 测试和 happy-path E2E 均可复现。

但独立反例仍发现 4 个 P0：CI 回退会删除用户未提交代码、默认 task ID 同秒碰撞、最大返工轮次的自动 vote_result 会在恢复时绕过人工接管，以及 E2E 注入了不存在的 Reviewer Worktree 路径。另有超时/ACK、部分 Worktree 清理、远端验证失败、归档和 PTY 等 P1 未闭环。因此当前结果不能满足 L3 场景完整性，也不能满足 PG-2 的稳定消费方接口要求。

## 2. P0 阻断项

### P0-1：CI 失败使用 `git reset --hard`，可直接删除用户未提交代码

`MergeController` 在目标工作区执行 fast-forward 后，CI 失败即对目标分支执行 `git reset --hard <pre_merge_head>`（`src/macao/merge/controller.py:66-90`）。它没有先验证工作树完全干净，也没有在独立 Worktree 中运行流水线。

独立反例：在 main 上保留一个与 feature 变更无冲突的已跟踪未提交修改，再执行会失败的 CI。结果 `ok=False`，但该文件内容从 `USER UNCOMMITTED WORK` 被恢复成提交版本，`git status` 中修改消失。也就是说“原子回滚”以不可恢复地覆盖用户数据为代价。

影响：这是破坏性数据丢失，不可作为安全回滚进入 PG-2。

修复要求：合并流水线必须在专用临时 Worktree/clone 中运行；或在任何 checkout/merge/reset 前强制验证 tracked、untracked、staged 均满足明确策略并 fail-closed。禁止在用户工作区用 `reset --hard` 做补偿。增加“存在未提交 tracked 文件”“存在 staged 文件”“CI 异常/超时且回滚命令失败”的反例。

### P0-2：默认 task_id 只有秒级时间戳，同一秒第二个任务主键冲突

`Orchestrator.start_task()` 使用 `task-YYYYMMDDHHMMSS`（`src/macao/workflow/orchestrator.py:100-120`）。`tasks.task_id` 是主键；同一秒内连续调用两次，实测第二次抛出：

```text
IntegrityError: UNIQUE constraint failed: tasks.task_id
```

message ID 的碰撞问题虽然已整改，但同类缺陷被转移到了任务主标识。修复要求：使用 UUID/ULID 或由数据库保证唯一的高熵 ID，并增加并发/固定时钟测试；冲突应有有界重试而不是让任务创建中断。

### P0-3：达到最大返工轮次时仍写自动 REWORK_REQUIRED，恢复后绕过人工接管

`collect_and_evaluate_consensus()` 在判断 `rnd < max_rework_rounds` 之前就调用 `generate_vote_result(..., write_to_disk=True)`（`src/macao/workflow/orchestrator.py:366-375`）；达到上限后虽然状态 HOLD 在 `CONSENSUS_CHECK`（`396-413`），磁盘上已经存在自动 `REWORK_REQUIRED`。

独立重放结果：

```text
before_reconcile = CONSENSUS_CHECK
vote_result_exists = True, decision = REWORK_REQUIRED
after_reconcile = REWORK
```

`StateReconciler` 会把该文件直接解释为 REWORK（`src/macao/storage/reconcile.py:34-57`），从而绕过 max-round 人工接管守卫。该行为与 PRD E5/E7 及此前回归承诺相矛盾。

修复要求：只有确定可执行的终局分支才落盘；max-round 必须 HOLD、发 `HUMAN_OVERRIDE_REQUEST` 且不写自动 vote_result。恢复逻辑还应验证当前状态、resolution 和 max-round guard。专项测试必须同时断言“文件不存在”和重启后仍 HOLD。

### P0-4：E2E 给 Reviewer Adapter 注入不存在的 Worktree 路径

实际 Worktree 路径由 `GitManager` 创建为：

```text
.macao/worktrees/<reviewer>/<task_id>/r<round>
```

但 E2E Runner 构造并注入的是 `.macao/worktrees/<reviewer>/r1_<short_sha>`（`src/macao/workflow/e2e_runner.py:207-217`）。独立重放中三条注入路径全部 `exists=False`，而实际创建路径全部存在。随后 Mock Reviewer 又把 `.review.yml` 直接写到主仓库（`e2e_runner.py:218-224`），没有在注入的 Worktree 中消费任务。

影响：Adapter 方法虽然被调用，PG-2 所需的“消费方使用 Orchestrator 分发的真实路径”仍是假阳性。

修复要求：`dispatch_review_requests()` 返回或保存每位 Reviewer 的权威 payload/路径，Runner 从 MessageBus 消费该消息并原样交给 Adapter；Reviewer 必须在该 Worktree 内生成产物，再由明确的回传/采集步骤导入主协调仓库。测试必须断言注入路径存在、等于 AEP payload 路径且三个路径互不相同。

## 3. P1 重要问题

1. **部分 Worktree 没有真正清理。** 异常补偿调用不存在的 `GitManager.remove_isolated_worktree()`（`src/macao/workflow/orchestrator.py:242-248`），异常又被吞掉；真实方法名是 `remove_worktree(path)`。独立故障注入后状态虽保持 READY_FOR_REVIEW，但第一份物理 Worktree 仍存在。现有测试只断言状态，未断言资源清零。

2. **L3 必需的 timeout 场景仍没有实现。** 配置中虽有 timeouts，消息表虽有 deadline/retry_count，但没有 deadline 扫描、三次退避、自动 ABSTAIN/DLQ 或工作流级超时测试。评审指南明确把超时列为 L3 必测场景。

3. **独立 ACK API 仍允许全量误确认。** `MessageBus.ack(message_id, recipient=None)` 会更新该消息所有 deliveries（`src/macao/msg/bus.py:91-106`）。Reviewer E2E 只调用 Mock Adapter 自身的恒真 `ack()`，没有 ACK MessageBus 中的实际 REVIEW_REQUEST。

4. **远端校验命令失败会静默成功。** push 后只有在 `ls-remote` 返回码为 0 且输出非空时才比较 SHA（`src/macao/merge/controller.py:114-123`）；命令失败或空输出仍返回 merge success。应将这两种情况 fail-closed。

5. **人工签字未绑定 checkpoint。** Controller 只检查任务下存在任意指定类型的 signoff，不核对 audit detail 中的 checkpoint_ref；返工后的旧签字可授权新 checkpoint。

6. **归档生命周期仍未实现 PRD 的消费语义。** FSM 仅 `copy2`，不执行“git 提交 → 复制 → 删除源文件”（`src/macao/workflow/fsm.py:71-111`）；E2E 只数 archive 文件，没有验证源文件删除、哈希和 SQLite 双账本一致。

7. **PTY/真实 Adapter 合同测试仍是假阳性。** Harness 只执行 `--version`，无条件设置 `ansi_stripped_ok=True`（`src/macao/adapter/integ_harness.py:78-130`）；Codex/Claude/Kimi 的 `get_logs(tail_lines)` 仍调用不接收参数的 `PTYSession.get_clean_logs()`。43 项测试没有覆盖真实 Adapter 的 start/inject/log/stop。

8. **代码洁净度声明不可复现。** `git diff --check e7ba2d2..4df059e` 仍报告 POC 报告和前一份整改申请中的多处 trailing whitespace。申请使用不带范围的 `git diff --check` 检查 clean worktree，只能证明没有未提交 diff，不能证明提交增量无尾随空白。

## 4. 已独立确认的有效整改

- PRD 的 10 状态、7 种 AEP 类型和四种 OverrideChoice 已恢复一致。
- APPROVED、REWORK、RETRY_REVIEW、CANCEL 四条人工裁定测试通过，生成消息可通过 AEP Schema。
- message_id 已从 4 位扩展为 16 位数字；5000 次生成和 500 次顺序发布未发现碰撞。
- missing remote 能 fail-closed；CI 失败能把干净测试仓库的 HEAD 恢复到原提交。
- Worktree 全部准备成功后才推进 WAITING_REVIEW；创建失败时 FSM 保持 READY_FOR_REVIEW。
- `PYTHONPATH=src python3 -m unittest discover tests -v`：43/43 PASS。
- `PYTHONPATH=src python3 -m compileall -q src`：PASS。
- `macao e2e-run`：Mock happy path 显示 3 票、5 份归档和 DONE。

说明：申请中的“500 次数据库并发写入”实际测试是单线程 for 循环；“10^16 空间，0 碰撞率”应改为“碰撞概率显著降低”，不能声称数学上的零概率。

## 5. 门禁判定

按照评审指南：L3 必须覆盖全同意、Deadlock、超时、弃权、恢复、返工等关键场景；PG-2 还要求 P0/P1 为零、接口稳定并有消费方场景测试。当前存在上述 P0/P1，故：

- L3 SCENARIO-VERIFIED：**不通过**
- PG-2：**不通过**
- 建议状态：维持整改中；上一轮协议修复可保留，但不得把当前 happy path 外推为下游可依赖接口。

## 6. 建议闭环顺序

1. 立即移除用户工作区 `reset --hard` 回滚方案，并修复 task ID 唯一性。
2. 修复 max-round 落盘/恢复绕过，补齐重启反例。
3. 让 E2E 从 MessageBus 消费真实 Worktree payload，并修复部分 Worktree 清理。
4. 实现 timeout/retry/DLQ/recipient ACK 场景，补齐远端校验失败和 checkpoint-bound signoff。
5. 完成归档与真实 Adapter 合同测试，最后以提交范围执行 `git diff --check`。

完成全部 P0/P1 后再申请 L3 / PG-2。

## 7. Reviewer 自审

本轮未引用其他专家结论作为证据；所有阻断项均通过当前提交的源码交叉检查或临时仓库反例独立复现。重点检查了申请测试未断言的物理副作用：用户未提交文件、Worktree 残留、恢复后的状态和 Adapter 实际接收路径。
