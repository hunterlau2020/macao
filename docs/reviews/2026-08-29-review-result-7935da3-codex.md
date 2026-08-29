# L3 All Items Closed 独立复审（Codex）

- **评审日期**：2026-08-29
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md`
- **冻结评审范围**：`4df059e..7935da3`（申请使用动态 `HEAD`；本报告固定为复审时的 `7935da3`）
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2**

## 1. 结论摘要

本轮实测 49/49 自动化测试通过，4 个 CLI 的 `--version` PTY 启停检查通过；max-round 守卫、脏工作区保护、Worktree 创建失败清理、终局 timeout ABSTAIN 票面、artifact reviewer key 与 SHA256 等整改均有实质进展。

但“全部阻断项闭环”仍与系统行为矛盾。独立故障重放发现：系统没有生产调度器主动推进 timeout；已经进入 timeout Deadlock 的 reviewer 若迟到补交，下一次收集会自动进入 `MERGING`，绕过人工接管；REVIEW_REQUEST 发布中途失败会留下部分分发和已消费的 dev manifest；push 成功后的校验不确定态仍只回退本地；artifact 账本虽标记 consumed，所有源产物仍留在原位置；真实 Adapter 的日志合同仍会抛 `TypeError`；旧 checkpoint 的 merge signoff 仍可授权新 checkpoint。

因此当前既不满足评审指引对 L3 的 timeout、崩溃恢复和消费方场景要求，也不满足 PG-1/PG-2 的 P0/P1 清零条件。

## 2. 独立机验结果

| 检查项 | 结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 49/49 PASS | VERIFIED（仅限现有测试覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `PYTHONPATH=src python3 -m macao.cli.main test-clis` | 4/4 显示 PASS | PARTIALLY_VERIFIED；只运行 `--version`，未覆盖 Adapter 合同 |
| E2E happy path | DONE，5 条 artifact ledger 记录均 `consumed=1` | PARTIALLY_VERIFIED；源产物未消费删除 |
| `git diff --check 4df059e..7935da3` | FAIL；5 处 trailing whitespace | CONTRADICTED |

关键反例输出：

```text
timeout_no_scheduler {'state': 'WAITING_REVIEW', 'timeout_audits': 0}
late_review_bypass {'first_change': None, 'after_timeout': 'CONSENSUS_CHECK', 'second_to': 'MERGING', 'after_late': 'MERGING', 'decision': 'APPROVED'}
partial_review_publish {'state': 'WAITING_REVIEW', 'codex_requests': 1, 'opencode_requests': 0, 'dev_consumed': 1}
post_push_indeterminate {'ok': False, 'local_resets': 1}
artifact_consumption {'ledger_consumed': [1, 1, 1, 1, 1], 'source_dev': True, 'source_reviews': ['antigravity.review.yml', 'codex.review.yml', 'opencode.review.yml'], 'source_vote': True}
adapter_get_logs TypeError
task_id_forced_collision {'second': 'IntegrityError'}
```

所有破坏性/失败路径测试均在临时仓库中完成，未修改真实项目状态。

## 3. 已确认的有效整改

- timeout reviewer 可由 `generate_vote_result()` 写为 `ABSTAIN`，并计入 `reviewers_responded` 与 `vote_breakdown.abstain`（`src/macao/consensus/vote.py:67-168`）。
- `resolve_override()` 会从本轮 timeout 审计中恢复 ABSTAIN reviewer（`src/macao/workflow/orchestrator.py:671-690`）。
- review artifact 的 reviewer key 已从 `codex.review` 修正为 `codex`，现有 E2E 中账本更新能命中（`src/macao/workflow/fsm.py:97-113`）。
- artifact 注册可从磁盘计算 SHA256，现有 E2E 的 5 条记录均为 64 位哈希（`src/macao/storage/store.py:69-105`）。
- 最大返工轮次时 HOLD 且不提前写自动 vote result；重启恢复专项测试通过。
- 工作树存在 tracked/staged 修改时 MergeController fail-closed；Worktree 部分创建失败时物理清理专项测试通过。

这些结果只能证明局部分支修正，不能覆盖下面仍开放的 L3/PG-2 阻断项。

## 4. P0：必须先解决

本轮未发现需要单列为 P0 的新增问题。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：timeout 检测没有生产驱动，也未实现 ping、重试与升级闭环

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:350-401,403-431`；`src/macao/workflow/e2e_runner.py:231-234`；`tests/test_p0_p1_rectification.py:108-118`；`docs/MACAO_PRD_v2.md:832-834,1152-1163,1369-1373`；`docs/MACAO_REVIEW_GUIDELINES.md:57-62`

`detect_timed_out_reviewers()` 已能在被调用时比较时间，但仓库中没有 scanner、scheduler 或 CLI 生产入口周期性调用它。唯一生产调用来自 `collect_and_evaluate_consensus()`，该方法本身也只在 E2E/测试代码被显式调用。时间流逝不会产生状态变化、timeout audit、ping、退避重试或升级通知。

现有 timeout 测试先手动调用 detector，再把检测结果通过 `timed_out_reviewers` 参数传回 consensus；注释声称“不传入”，实际 `tests/test_p0_p1_rectification.py:114-118` 仍显式传入。这不能证明无人响应时系统会自动完成降级。

**验收标准**：实现可启动、可停止、可重启恢复的 deadline scanner；持久化 per-delivery timeout disposition；按 PRD 执行 ping、最多三次退避重试、DLQ/告警和人工升级；测试只推进可控时钟，不直接调用 detector 或传入答案。

### P1-2：timeout Deadlock 可被迟到 review 自动越过

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:398-401,429-510`；`docs/MACAO_PRD_v2.md:832-840,892-906`

timeout reviewer 只通过审计事件记录，没有形成冻结的本轮 disposition。独立重放中，1 个 approve + 1 个 timeout 首先正确 HOLD 在 `CONSENSUS_CHECK` 并发布人工接管；随后已经超时的 reviewer 补交 approve，再次调用 consensus 时 detector 看到两份 manifest，返回空 timeout 列表，系统自动生成 APPROVED 并转入 `MERGING`。

这绕过了已经建立的 E7 人工裁定边，与 PRD “timeout → Deadlock → HOLD → 人工裁定”的唯一转移路径矛盾。

**验收标准**：timeout disposition 一旦生效，本轮后续迟到 manifest 必须拒绝、隔离或仅作审计，不得重新参与自动共识；Deadlock/HUMAN_OVERRIDE_REQUEST 建立后只能由 E7/E9/E10 离开。增加迟到 approve、迟到 reject、进程重启后三个反例。

### P1-3：REVIEW_REQUEST 分发不是事务性的

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:273-348`；`docs/MACAO_PRD_v2.md:828-834`

代码只保证 Worktree 创建阶段先全部成功，却在消息发布前就执行 E2、归档并标记 `.dev.yml` consumed。独立注入第二个 reviewer 的 publish 失败后，任务留在 `WAITING_REVIEW`，codex 有 1 条请求、opencode 为 0，dev artifact 已 `consumed=1`，且没有补偿清理或安全重试状态。

**验收标准**：Worktree、FSM、artifact 与消息 fan-out 使用可恢复 outbox/事务边界；部分 publish 后重启必须幂等补齐或整体回滚，不能让任务处于“已等待所有 reviewer、实际只通知部分 reviewer”的状态。

### P1-4：push 后校验失败仍制造远端、本地与工作流状态分叉

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:107-132`；`src/macao/workflow/orchestrator.py:601-621`；`docs/MACAO_PRD_v2.md:1533-1544`

若 `git push` 已成功，而随后的 `ls-remote` 临时失败或返回空输出，远端可能已包含 checkpoint。当前代码只执行本地 `reset --hard pre_merge_head` 并返回失败；Orchestrator 随即转到 `REWORK`。独立 fault injection 确认 push success + verify failure 会执行一次本地 reset。

**验收标准**：post-push 无法确认必须进入持久化的 indeterminate/HOLD 状态并有界重试、人工升级；只有远端 compare-and-set 回退并再次验证成功时才能声明 rollback。不得用 local-only reset 表示远端已恢复。

### P1-5：artifact 账本的 consumed 与实际生命周期相矛盾

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:71-113`；`src/macao/storage/store.py:107-116`；`docs/MACAO_PRD_v2.md:852-862,1361-1367`

FSM 仅 `copy2()` 并更新 SQLite，不执行 PRD 定义的“git 提交 → 复制 → 删除原位置”。独立 E2E 后 5 条 ledger 全为 `consumed=1`，但 `.macao/.dev.yml`、三份 `.review.yml` 和 `vote_result.json` 全部仍存在原路径。因此 consumed 字段不是物理生命周期事实，启动恢复也没有对这种双账不一致进行补偿。

**验收标准**：按 PRD 完成提交、原子复制/rename、删除源文件和可重放恢复；测试同时断言 archive 哈希、源文件不存在、git 审计记录存在、SQLite consumed 与磁盘状态一致，并覆盖复制中崩溃。

### P1-6：真实 Adapter 合同未被测试且当前实现会抛 TypeError

**验证状态**：CONTRADICTED

**证据**：`src/macao/adapter/pty_session.py:115-117`；`src/macao/adapter/codex.py:63-77`；`src/macao/adapter/claude.py:75-88`；`src/macao/adapter/kimi.py:65-75`；`src/macao/adapter/integ_harness.py:78-130`；`src/macao/workflow/e2e_runner.py:207-229`

Codex、Claude 与 Kimi Adapter 均调用 `PTYSession.get_clean_logs(tail_lines)`，而该方法不接收参数；独立调用 `CodexAdapter.get_logs()` 得到 `TypeError`。`test-clis` 只启动各 CLI 的 `--version`，且不检查真实 ANSI 输入就无条件设置 `ansi_stripped_ok=True`。E2E 使用 Mock Adapter，虽然检查 Worktree 路径存在，却仍把 review manifest 直接写入协调仓库，并没有让真实 Reviewer 在注入 Worktree 中完成消费、ACK 与产物回传。

**验收标准**：以真实 Adapter 执行 start → inject → get_logs → ack → stop 合同测试；输入带 ANSI 的可控输出并校验剥离结果；Reviewer 必须从 MessageBus 消费权威 payload，在隔离 Worktree 工作，经明确回传协议交付 manifest。

### P1-7：merge signoff 未绑定当前 checkpoint

**验证状态**：CONTRADICTED

**证据**：`src/macao/cli/main.py:291-312`；`src/macao/merge/controller.py:48-53`；`docs/MACAO_PRD_v2.md:1512-1523,1533-1542`

CLI 写入 signoff 时包含 `checkpoint_ref`，但 MergeController 只检查任务下是否存在任意 `HUMAN_MERGE_APPROVED`/`MERGE_SIGNOFF_APPROVED` 事件，不比较事件中的 checkpoint。任务返工产生新 checkpoint 后，旧签字仍能放行新代码。

**验收标准**：签字必须绑定 task、完整 checkpoint SHA、review round、target branch 与签字人；Controller 只接受当前合并对象的有效签字。增加旧 checkpoint signoff 不能授权新 checkpoint 的测试。

## 6. P2/P3：可延期但必须登记

### P2-1：task ID 仍只有 24-bit 随机熵且冲突未重试

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/workflow/orchestrator.py:122-144`；`tests/test_p0_p1_rectification.py:50-65`

同秒 task ID 只保留 UUID 的 6 个十六进制字符。100 次抽样未碰撞不能证明唯一性；同秒 1,000 次的生日碰撞概率约 2.9%，5,000 次超过 50%。独立固定随机源重放时，第二次创建直接抛 `sqlite3.IntegrityError`。

**验收标准**：使用完整 UUID/ULID 或等价高熵 ID；对数据库唯一键冲突执行有界重试，并用注入冲突的确定性测试验证。

### P3-1：申请的代码洁净度命令不能证明提交范围，当前范围实际失败

**验证状态**：CONTRADICTED

**证据**：`docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md:26-43`

申请使用裸 `git diff --check`，在 clean worktree 上只能检查未提交差异。对冻结评审范围执行 `git diff --check 4df059e..7935da3`，实际报告 `docs/reviews/2026-08-29-review-result-ea536ab-codex.md` 5 处 trailing whitespace。因此“代码差异洁净度”不能按申请证据判为 VERIFIED。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 7935DA3-P1-1 | P1 | Workflow/Scheduler | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P1-2 | P1 | Workflow/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P1-3 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P1-4 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P1-5 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P1-6 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P1-7 | P1 | CLI/MergeController | 下次 L3 申请前 | 待补 | OPEN |
| 7935DA3-P2-1 | P2 | Workflow/ID | PG-2 前或显式风险接受 | 待补 | OPEN |
| 7935DA3-P3-1 | P3 | Docs | 下次申请前 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 仅保留此前已确认的局部范围 | 当前仍有多处代码与 PRD 明确矛盾，不扩大认证范围 |
| L3 SCENARIO-VERIFIED | **不通过** | timeout、迟到响应、部分分发、恢复和真实 Adapter 场景未闭环 |
| PG-1 | **不通过** | P1 未清零 |
| PG-2 | **不通过** | 继承 PG-1 失败，且消费者合同、远端一致性与 artifact 生命周期不稳定 |

## 9. 建议闭环顺序与验收标准

1. 先冻结 timeout disposition，修复迟到 review 绕过，并实现生产 scanner/ping/retry/DLQ/升级闭环。
2. 用 outbox/幂等恢复修复 review fan-out 部分提交；加入进程在每个写入边界崩溃的重启测试。
3. 将 post-push 不确定态建模为 HOLD，绑定 checkpoint signoff，补远端成功/校验失败反例。
4. 按 PRD 完成 artifact 的 git 审计、原子归档、源删除与恢复，并核对磁盘/SQLite/hash 三方一致。
5. 修复真实 Adapter 日志合同，让 E2E 从 MessageBus 到隔离 Worktree 再到 manifest 回传走完整生产接口。
6. 扩大 task ID 熵并加入冲突重试；最后运行所有场景和提交范围的 `git diff --check`。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md:15,49` 的“完整测试超时全链路”“全部阻断项已闭环”与当前证据冲突，应撤回或改为局部整改声明。
- `docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md:16` 的“高熵 UUID 后缀保证并发唯一性”应改为“降低碰撞概率”，直到使用完整高熵 ID 或冲突重试。
- `docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md:35-39` 的“真实 CLI 生命周期”“Adapter 驱动”应明确当前仅为 CLI `--version` PTY 冒烟和 Mock happy path。
- 后续申请必须把动态 `HEAD` 固定成明确短 SHA，并使用带提交范围的洁净度命令。

## 11. Reviewer 自审记录

- 未引用其他 reviewer 的结论作为证据；所有结论来自当前提交的代码、权威 PRD、现有测试和临时仓库 fault injection。
- 强制检查了申请中的 `[PASS]`/“完整”“全部闭环”“100%”是否对应真实生产路径，而非测试名称。
- 每项 P1 均给出文件路径、行号、具体矛盾、可复现行为与关闭标准。
- 重点检查了 happy path 未覆盖的时间流逝、迟到响应、部分发布、push 后不确定态、源文件副作用和 checkpoint 绑定。
