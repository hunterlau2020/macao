# L3 / PG-2 Final Certification 独立复审（Codex）

- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-Final-Certification.md`
- **冻结代码范围**：`f41b9da..bf5ae2d`（当前 `99526aa` 仅新增认证申请）
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2**

## 1. 结论摘要

本轮整改取得明确进展：迟到 review 已从自动共识隔离，merge signoff 已绑定 checkpoint，非法 override 不再先写孤儿产物，Adapter 日志接口类型已统一，task ID 增加到 32-bit 随机后缀并具备有界冲突重试。58/58 自动化测试、happy-path E2E、编译与提交范围洁净度均通过。

但“全部问题彻底闭环”仍不成立。新增的 E9 `RETRY_REVIEW` 在 timeout 场景中会继承同一 round 的历史 timeout disposition；重新派发后即使全部 reviewer 重新批准，旧 timeout 仍把对应新票隔离并再次 HOLD，形成稳定活锁。生产 timeout scanner、REVIEW_REQUEST 事务性 fan-out、push 后远端不确定态、PRD artifact 消费语义以及真实 Adapter 消费方 E2E 仍未实现。

当前共有 6 项 P1 未关闭。按照评审指引，PG-1/PG-2 要求 P0/P1 为零，L3 还必须覆盖 timeout、崩溃恢复、返工/重试和真实消费方场景，因此本次认证申请不通过。

## 2. 独立机验结果

| 检查项 | 结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 58/58 PASS | VERIFIED（仅限现有覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `git diff --check f41b9da..bf5ae2d` | 返回码 0 | VERIFIED |
| timeout 后迟到 review | 保持 HOLD，终局保留 ABSTAIN | VERIFIED |
| 旧 checkpoint signoff | 被拒绝；当前 checkpoint signoff 可通过 | VERIFIED |
| Adapter `get_logs(2)` | 返回尾部两行字符串 | VERIFIED |
| task ID 首次碰撞 | 第二次随机生成后成功 | VERIFIED |
| timeout 后 E9 重试 | 新票仍被历史 timeout 隔离，再次 HOLD | CONTRADICTED |

独立反例输出：

```text
timeout_without_driver {'state': 'WAITING_REVIEW', 'timeouts': 0}
retry_timeout_livelock {'state': 'CONSENSUS_CHECK', 'change': None, 'decision': None, 'historical_timeouts': ['opencode'], 'late_isolated': 1}
partial_publish {'state': 'WAITING_REVIEW', 'codex': 1, 'opencode': 0, 'dev_consumed': 1}
post_push_uncertainty {'ok': False, 'local_resets': 1}
artifact_sources {'consumed': [1, 1, 1, 1, 1], 'dev': True, 'reviews': 3, 'vote': True}
adapter_logs {'value': 'b\nc', 'type': 'str'}
task_retry {'one': 'aaaaaaaa', 'two': 'bbbbbbbb', 'unique': True}
```

所有失败路径均在临时仓库执行，未修改项目业务状态。

## 3. 已确认的有效整改

- **CODE/TEST VERIFIED**：历史 timeout disposition 会合并进当前共识输入；迟到 reviewer manifest 被标记 `LATE_REVIEW_ISOLATED`，不再触发自动合并（`src/macao/workflow/orchestrator.py:454-565`；`src/macao/consensus/vote.py:87-94`）。
- **CODE/TEST VERIFIED**：MergeController 只接受 detail 中 checkpoint_ref 与当前 task checkpoint 完全一致的签字（`src/macao/merge/controller.py:48-61`）。
- **CODE/TEST VERIFIED**：`resolve_override()` 在写 audit、vote result 和 artifact 之前校验 FSM 转移合法性（`src/macao/workflow/orchestrator.py:711-743`）。
- **CODE/TEST VERIFIED**：`PTYSession.get_clean_logs()` 支持 tail，真实与 Mock Adapter 的 `get_logs()` 统一返回字符串。
- **CODE/TEST VERIFIED**：task ID 使用 8 位十六进制后缀，数据库冲突后最多重试 5 次；独立注入首次碰撞可成功恢复（`src/macao/workflow/orchestrator.py:129-158`）。
- **CODE/TEST VERIFIED**：非法 duration 会显式报错；Schema 环境变量寻址和 archive SHA256 补写测试通过。

## 4. P0：必须先解决

本轮未发现需要单列为 P0 的新增问题。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：E9 RETRY_REVIEW 继承旧 timeout disposition，形成必现活锁

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:454-463,745-789`；`tests/test_p0_p1_rectification.py` 中 `test_retry_review_override_clears_reviews_and_redispatches_fresh_requests`；`docs/MACAO_PRD_v2.md:840-841,892-906`

PRD 的 E9 保持 review round 不变，但要求作废旧意见并使用全新 message ID/deadline 重试。当前实现删除活跃 review 文件并重新派发，却保留相同 task/round 下的 `REVIEWER_TIMEOUT_ABSTAIN` 和 `DEADLOCK_DETECTED` 审计。下一次 consensus 会无条件把这些历史 timeout reviewer 加回 `timed_out_reviewers`，并隔离他们的新 manifest。

独立重放：opencode 首次 timeout → 管理员选择 RETRY_REVIEW → codex/opencode 均重新提交 approve → opencode 新票被记为 `LATE_REVIEW_ISOLATED`，任务再次 HOLD 在 `CONSENSUS_CHECK`。现有 E9 测试没有先建立 timeout disposition，只验证删除文件和生成消息，因此未覆盖申请所称的“超时活锁”。

**验收标准**：为每次 E9 引入独立 review attempt/generation，timeout、deadline、message 和 manifest 均绑定 attempt；或在保留审计历史的同时明确关闭旧 disposition，不能物理删除审计证据。专项测试必须从真实 timeout → E9 → 两份新批准票 → 自动 APPROVED 完整重放，并验证旧、新 attempt 的审计可区分。

### P1-2：timeout 仍没有生产 scanner、ping、重试与升级驱动

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:368-426,428-463`；`src/macao/workflow/e2e_runner.py:231-234`；`docs/MACAO_PRD_v2.md:832-834,1152-1163,1369-1373`

deadline 只有在外部主动调用 detector/consensus 时才处理。仓库中仍无 scheduler、后台 scanner 或 CLI 生产入口推进超时，也没有 PRD 规定的 ping、退避三次、DLQ 和持续升级。独立以 `per_reviewer=0s` 分发后不调用 collector，任务保持 `WAITING_REVIEW`，timeout audit 为 0。

reviewer 在 deadline 后、首次扫描前提交时，detector 只看文件是否存在，不验证到达时间，仍可被视为正常响应。

**验收标准**：实现可运行、可停止、重启可恢复的 deadline scanner；持久化每个 delivery 的 deadline、arrival time、attempt 和 disposition；以可控时钟自然驱动 ping/retry/DLQ/escalation，不得由测试直接调用 detector 或传入超时名单。

### P1-3：REVIEW_REQUEST fan-out 仍可部分提交

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:287-366`；`docs/MACAO_PRD_v2.md:828-834`

代码在发布 reviewer 消息前先转入 `WAITING_REVIEW` 并归档/消费 dev manifest。向第二个 reviewer 发布失败时没有 outbox、回滚或恢复标记。独立注入后 codex 有 1 条请求、opencode 为 0，任务仍是 `WAITING_REVIEW`，dev ledger 已 `consumed=1`。

**验收标准**：以事务性 outbox 或可恢复 dispatch generation 统一 Worktree、FSM、artifact 与消息 fan-out；每个写入边界崩溃后都必须幂等补齐或安全恢复。

### P1-4：push 成功后的校验不确定态仍只回退本地

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:115-140`；`src/macao/workflow/orchestrator.py:658-680`；`docs/MACAO_PRD_v2.md:1533-1544`

若 push 已成功而 `ls-remote` 临时失败/空返回，远端可能已前移。当前实现只把本地分支 reset 到 pre-merge HEAD，然后 workflow 进入 REWORK。独立 fault injection 确认该路径仍执行一次 local reset，无法恢复或确认远端事实。

**验收标准**：将 post-push 无法确认持久化为 indeterminate/HOLD，执行有界重试和人工升级；只有远端 compare-and-set 回退并重新验证成功后才能声明 rollback。

### P1-5：artifact ledger 的 consumed 状态仍与磁盘生命周期矛盾

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:71-113`；`src/macao/storage/store.py:111-140`；`docs/MACAO_PRD_v2.md:852-862,1361-1367`

SHA256 补写得到改善，但 FSM 仍只 `copy2()` 并更新 SQLite，不执行 PRD 规定的“git 提交 → 复制到 archive → 删除原位置”。独立 E2E 后 5 条 ledger 均 `consumed=1`，但 `.dev.yml`、三份 `.review.yml` 和 `vote_result.json` 全部保留在源路径。因此申请中的“物理产物与 SQLite 双向核对 100% 一致”仍不成立。

**验收标准**：实现 git 审计、原子复制/rename、源删除和启动补偿；测试同时验证 archive hash、源文件不存在、git 记录和 SQLite 状态，并覆盖复制中崩溃。

### P1-6：真实 Adapter 消费方场景仍未验证

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:78-130`；`src/macao/workflow/e2e_runner.py:207-229`；`docs/MACAO_REVIEW_GUIDELINES.md:57-62,66-73`

接口签名问题已经关闭，但 `test-clis` 仍只运行 CLI `--version`，且不检查真实 ANSI 输入便把 `ansi_stripped_ok=True`。E2E 仍使用 Mock Adapter；它检查 Worktree 存在，却把 review manifest 直接写入协调仓库，并未从 MessageBus 消费实际 REVIEW_REQUEST、在隔离 Worktree 完成真实评审、ACK delivery 再回传产物。

PG-2 明确要求接口稳定和消费方场景测试，`--version` PTY 冒烟与 Mock happy path 不满足该条件。

**验收标准**：至少以一个真实 Reviewer Adapter 执行 start → receive/inject → get_logs → ack → stop；用可控 ANSI 输出验证清洗；从 MessageBus 消费权威 payload，在隔离 Worktree 工作并通过明确协议回传 manifest。

## 6. P2/P3：可延期但必须登记

本轮没有新增需要单列的 P2/P3。32-bit task ID + 5 次冲突重试已满足上一轮关闭条件；若未来提升到高并发调度，应再评估改用完整 UUID/ULID。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| BF5AE2D-P1-1 | P1 | Workflow/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| BF5AE2D-P1-2 | P1 | Workflow/Scheduler | 下次 L3 申请前 | 待补 | OPEN |
| BF5AE2D-P1-3 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| BF5AE2D-P1-4 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| BF5AE2D-P1-5 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| BF5AE2D-P1-6 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 保留已验证的局部实现范围 | 当前仍有代码与 PRD 的明确偏差 |
| L3 SCENARIO-VERIFIED | **不通过** | timeout/E9、部分分发、恢复与真实消费方场景未闭环 |
| PG-1 | **不通过** | P1 未清零 |
| PG-2 | **不通过** | 继承 PG-1 失败，且消费方、远端与 artifact 生命周期不稳定 |

## 9. 建议闭环顺序与验收标准

1. 为 E9 引入 review attempt/generation，解除旧 timeout disposition 对新尝试的污染。
2. 实现生产 timeout scanner 与 delivery arrival/deadline/ping/retry/DLQ 状态机。
3. 用 outbox/恢复状态关闭 review fan-out 部分提交。
4. 将 post-push 不确定态改为持久化 HOLD，并补远端确认/恢复测试。
5. 完成 artifact 的 git 审计、原子归档、源删除及崩溃恢复。
6. 使用真实 Adapter 完成 MessageBus → Worktree → manifest → ACK 的消费方场景，再执行全量 L3 重放。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-29-review-request-L3-Final-Certification.md` 中“RETRY_REVIEW 解决超时活锁”的声明应撤回；当前测试未包含旧 timeout disposition。
- “5 份物理产物与 SQLite 双向核对 100% 一致”应改为“archive 副本与 ledger 字段存在”，直到源文件删除和 git 审计完成。
- “真实 CLI PTY 验证”应明确为 `--version` 冒烟；“Adapter 契约驱动”应明确为 Mock E2E。
- “全部问题彻底闭环”应在上述 P1 完成并通过失败/恢复重放后再使用。

## 11. Reviewer 自审记录

- 未引用其他 reviewer 的结论作为证据；`docs/EXPERT_QUALITY.md` 仅作为检查清单，不作为实现通过证明。
- 每个 P1 均有当前代码路径、权威 PRD 对照、具体行为和关闭条件。
- 强制检查了申请中的“100%”“彻底闭环”“真实”“双向一致”等强声明，没有把测试名称或通过数量外推到未覆盖路径。
- 所有失败/恢复测试均在临时仓库进行；重点检查了 E9 attempt 边界、部分副作用、远端事实和源文件状态。
