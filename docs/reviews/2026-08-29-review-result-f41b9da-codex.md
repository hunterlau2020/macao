# L3 / PG-2 Final Seal 独立复审（Codex）

- **评审日期**：2026-08-29
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-Final-Seal.md`
- **冻结代码范围**：`7935da3..f41b9da`（当前 `176df60` 仅为申请/状态文档提交）
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2**

## 1. 结论摘要

本轮新增的两项 timeout 修复有效覆盖了申请列出的直接场景：只要当前 consensus 调用携带非空 timeout 名单，即使 2/3 reviewer 已批准也会 HOLD 并要求人工接管；审计定向查询也不再受最近 50 条记录窗口限制。51/51 测试、CLI E2E happy path 和提交范围洁净度均可复现通过。

但“终局封板”仍不成立。新的 timeout 守卫没有冻结已发生的 timeout disposition：迟到 reviewer 补交后，下一次自动检测返回空名单，任务仍会从已 HOLD 的 `CONSENSUS_CHECK` 自动进入 `MERGING`。系统也仍无生产 scanner 主动推进 deadline/ping/retry/escalation。上一轮其余门禁项没有进入本次代码整改，独立重放继续确认部分 review 分发、push 后不确定态、artifact 假消费、真实 Adapter 合同、checkpoint signoff 和 task ID 碰撞问题。

评审指引明确规定真理不等于投票。申请中“P1-2 已被四方一致确认”不能替代磁盘反例；本轮 E2E 后 SQLite 虽全部 `consumed=1`，5 份源产物仍留在原位置，与 PRD 生命周期定义直接矛盾。

## 2. 独立机验结果

| 检查项 | 结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 51/51 PASS | VERIFIED（仅限现有覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `PYTHONPATH=src python3 -m macao.cli.main e2e-run` | 7 个展示步骤完成，终态 DONE | PARTIALLY_VERIFIED；Mock happy path |
| 3 reviewer：2 approve + 1 timeout | HOLD；人工 APPROVED 后进入 MERGING | VERIFIED |
| 100+ audit events 后 timeout 查询 | 仍可检出 | VERIFIED |
| `git diff --check 7935da3..f41b9da` | 返回码 0 | VERIFIED |

独立失败路径输出：

```text
timeout_without_driver {'state': 'WAITING_REVIEW', 'timeout_events': 0}
late_review_after_timeout {'first': None, 'held': 'CONSENSUS_CHECK', 'second_to': 'MERGING', 'decision': 'APPROVED'}
partial_publish {'state': 'WAITING_REVIEW', 'codex': 1, 'opencode': 0, 'dev_consumed': 1}
post_push_uncertainty {'ok': False, 'local_resets': 1}
artifact_sources {'consumed': [1, 1, 1, 1, 1], 'dev': True, 'reviews': 3, 'vote': True}
adapter_get_logs TypeError
stale_signoff {'signed': 'bbbbbbbb', 'accepted': True}
forced_task_collision IntegrityError
```

失败路径均在临时仓库中执行，未污染真实工作区。

## 3. 已确认的有效整改

- **CODE/TEST VERIFIED**：当前调用检测到任意 timeout reviewer 时，系统强制 HOLD、发布 `HUMAN_OVERRIDE_REQUEST` 且不写自动 vote result（`src/macao/workflow/orchestrator.py:474-524`）。
- **CODE/TEST VERIFIED**：`get_audit_events_by_type()` 消除了 `limit=50` 对 dispatch/timeout 事件查询的截断（`src/macao/storage/store.py:167-194`）。
- **CODE/TEST VERIFIED**：`REVIEWER_TIMEOUT_ABSTAIN` 对同一 task/round/reviewer 的写入在当前流程中幂等（`src/macao/workflow/orchestrator.py:474-491`）。
- **CODE/TEST VERIFIED**：E2E 的 `effective_votes` 改为 approve + reject，当前 happy path 输出 3（`src/macao/workflow/e2e_runner.py:236-240`）。
- **DOC VERIFIED**：`git diff --check 7935da3..f41b9da` 洁净。

这些修复关闭了申请表中的直接用例，但未关闭以下系统级门禁项。

## 4. P0：必须先解决

本轮未新增 P0。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：timeout 仍无生产驱动，deadline 可以无人处理

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:350-408,410-438`；`src/macao/workflow/e2e_runner.py:231-234`；`docs/MACAO_PRD_v2.md:832-834,1152-1163,1369-1373`

`detect_timed_out_reviewers()` 只能在调用时比较时间。仓库没有 scheduler、后台 scanner 或运维命令周期调用 consensus/detector，也没有 PRD 要求的 ping、退避重试、DLQ 与持续升级。独立使用 `per_reviewer=0s` 分发后不调用 collector，任务保持 `WAITING_REVIEW` 且 timeout audit 为 0。

如果 reviewer 在 deadline 后、首次扫描前补交 manifest，detector 只看文件是否存在而不看到达时间，会把它当作正常响应，deadline 事实上无法执行。

**验收标准**：提供可运行、可停止、可重启恢复的 scanner；持久化每个 delivery 的 deadline、到达时间与 timeout disposition；实现 ping、三次退避、DLQ/告警，并用可控时钟从“无人响应”自然驱动全链路。

### P1-2：timeout HOLD 仍可被迟到 review 绕过

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:405-408,436-524`；`docs/MACAO_PRD_v2.md:832-840,892-906`

本轮守卫只检查本次调用的 `timed_out_reviewers`。首次 timeout 后虽然写入审计，但下次 consensus 不读取既有 timeout disposition；迟到 manifest 使 detector 的集合差为空。独立重放结果为：先因 1 approve + 1 timeout HOLD，迟到 reviewer 再提交 approve，第二次收集自动得到 APPROVED 并转入 `MERGING`。

这仍违反 E7 的唯一人工离开路径，也说明新增三 reviewer 测试只覆盖了同一次调用，没有覆盖迟到响应与恢复。

**验收标准**：timeout 一经确认就冻结为本轮持久化 disposition；迟到 manifest 只能隔离/审计，不能重返自动计票；进入 timeout/deadlock HOLD 后只能通过 E7/E9/E10 离开。覆盖迟到 approve、迟到 reject、重启后三种反例。

### P1-3：REVIEW_REQUEST 发布仍存在部分提交

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:273-348`；`docs/MACAO_PRD_v2.md:828-834`

Orchestrator 在 fan-out 发布前先执行 E2、归档并标记 dev artifact consumed。向第二个 reviewer 发布失败时，没有回滚/outbox/恢复记录。独立注入结果：状态为 `WAITING_REVIEW`，codex 收到 1 条、opencode 为 0，而 dev 已 `consumed=1`。

**验收标准**：用事务性 outbox 或可恢复状态统一 Worktree、FSM、artifact 与 fan-out；任何发布边界崩溃后均能幂等补齐或整体恢复，不能让系统声称等待全体 reviewer 而实际只通知部分成员。

### P1-4：push 后校验不确定态仍只回退本地

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:107-132`；`src/macao/workflow/orchestrator.py:615-635`；`docs/MACAO_PRD_v2.md:1533-1544`

push 已成功、`ls-remote` 临时失败或空返回时，远端可能已经前移。当前代码仅执行本地 `reset --hard pre_merge_head` 并返回失败，随后 workflow 转入 REWORK。独立 fault injection 确认该路径执行本地 reset，无法恢复远端事实。

**验收标准**：将 post-push 无法确认持久化为 indeterminate/HOLD，进行有界重试和人工升级；只有远端 compare-and-set 回退且重新验证成功时才能声明 rollback。

### P1-5：artifact `consumed=1` 仍不代表产物被消费

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:71-113`；`docs/MACAO_PRD_v2.md:852-862,1361-1367`

FSM 只执行 `copy2()` 和数据库更新，不执行 PRD 规定的“git 提交 → 复制到 archive → 删除原位置”。独立 E2E 后 5 条账本均为 `consumed=1`，但 `.dev.yml`、三份 `.review.yml` 和 `vote_result.json` 全部仍存在源路径。因此申请所称“物理产物与 SQLite 双向核对 100% 一致”不成立。

**验收标准**：实现 git 审计、原子复制/rename、源删除及启动补偿；测试同时验证 archive/hash、源文件不存在、git 记录和 SQLite 状态，并覆盖复制中崩溃。

### P1-6：真实 Adapter 合同仍损坏，PTY 验证是冒烟而非合同测试

**验证状态**：CONTRADICTED

**证据**：`src/macao/adapter/pty_session.py:115-117`；`src/macao/adapter/codex.py:63-77`；`src/macao/adapter/claude.py:75-88`；`src/macao/adapter/kimi.py:65-75`；`src/macao/adapter/integ_harness.py:78-130`；`src/macao/workflow/e2e_runner.py:207-229`

Codex、Claude、Kimi 的 `get_logs(tail_lines)` 都把参数传给不接收参数的 `PTYSession.get_clean_logs()`；独立调用得到 `TypeError`。`test-clis` 只运行 `--version`，并无条件把 `ansi_stripped_ok` 设为 True。E2E 仍使用 Mock Adapter，review manifest 写入协调仓库而不是由真实 reviewer 在注入 Worktree 中生成并回传。

**验收标准**：真实执行 start → inject → get_logs → ack → stop；用可控 ANSI 输出校验日志；从 MessageBus 消费权威 payload，在隔离 Worktree 完成任务并通过明确回传协议交付 manifest。

### P1-7：旧 checkpoint 的 merge signoff 可授权新 checkpoint

**验证状态**：CONTRADICTED

**证据**：`src/macao/cli/main.py:291-312`；`src/macao/merge/controller.py:44-53`；`docs/MACAO_PRD_v2.md:1512-1523,1533-1542`

CLI 已在 signoff detail 中记录 checkpoint，但 Controller 只检查任务下是否存在任意 signoff 类型，不比较 checkpoint。独立重放用完全不同 SHA 的旧签字，当前 checkpoint 仍成功通过 merge pipeline。

**验收标准**：签字绑定完整 checkpoint SHA、round、target branch 与 actor；Controller 仅接受当前合并对象的有效签字，并加入返工后旧签字失效测试。

## 6. P2/P3：可延期但必须登记

### P2-1：task ID 仍有 24-bit 随机碰撞且无重试

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/workflow/orchestrator.py:122-144`；`tests/test_p0_p1_rectification.py:50-65`

同秒 task ID 只使用 UUID 的 6 个十六进制字符。100 次抽样不能证明唯一；固定随机源重放时第二次创建直接抛 `sqlite3.IntegrityError`。同秒 1,000 次的生日碰撞概率约 2.9%，5,000 次超过 50%。

**验收标准**：使用完整 UUID/ULID 或等价高熵 ID；捕获唯一键冲突并有界重试，以确定性碰撞注入测试验收。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| F41B9DA-P1-1 | P1 | Workflow/Scheduler | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P1-2 | P1 | Workflow/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P1-3 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P1-4 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P1-5 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P1-6 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P1-7 | P1 | CLI/MergeController | 下次 L3 申请前 | 待补 | OPEN |
| F41B9DA-P2-1 | P2 | Workflow/ID | PG-2 前或显式风险接受 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 原因 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 仅保留此前已确认的局部范围 | 当前仍有多处代码与 PRD 明确偏差 |
| L3 SCENARIO-VERIFIED | **不通过** | timeout、迟到响应、部分分发、恢复和真实 Adapter 场景未闭环 |
| PG-1 | **不通过** | P1 未清零 |
| PG-2 | **不通过** | 继承 PG-1 失败，消费者合同、远端一致性与 artifact 生命周期仍不稳定 |

## 9. 建议闭环顺序与验收标准

1. 先实现 timeout 持久化 disposition 和生产 scanner，禁止迟到 review 绕过人工接管。
2. 以 outbox/恢复状态修复 review fan-out 部分提交，并逐写入边界做崩溃重启测试。
3. 处理 post-push indeterminate 状态并把 merge signoff 绑定当前 checkpoint。
4. 按 PRD 完成 artifact 的 git 审计、原子归档、源删除和启动补偿。
5. 修复真实 Adapter 日志合同，让 E2E 走 MessageBus → Worktree → manifest 回传的生产接口。
6. 扩大 task ID 熵并加入冲突重试；最后全量重放 L3 场景。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-29-review-request-L3-Final-Seal.md:20` 的“只要存在超时 Reviewer，一律强制 HOLD”只能描述同一次调用；在 timeout audit 已存在但 detector 因迟到 manifest 返回空列表时并不成立。
- `docs/reviews/2026-08-29-review-request-L3-Final-Seal.md:11,40` 的“物理产物与 SQLite 双向核对 100% 一致”“Adapter 契约驱动”应改为“Mock happy path 中 archive 副本与 ledger 字段存在”。
- `docs/reviews/2026-08-29-review-request-L3-Final-Seal.md:51` 的“所有残余问题彻底闭环”应撤回；一致投票不能替代本报告中的可复现反例。

## 11. Reviewer 自审记录

- 未引用其他 reviewer 的结论作为证据；申请中的 reviewer 共识仅作为待验证声明。
- 每项 P1 均通过当前源码与临时仓库 fault injection 独立确认，并给出路径、行号、行为和关闭标准。
- 没有把 51/51 PASS、测试名称、E2E 展示行或“100%”措辞外推到未覆盖的失败/恢复路径。
- 强制检查了 timeout 事实的持续性、部分副作用、远端事实、源文件状态和 checkpoint 授权边界。
