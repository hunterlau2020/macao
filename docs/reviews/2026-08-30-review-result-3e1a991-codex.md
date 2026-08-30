# L3 / PG-2 Final Seal 独立复审（Codex）

- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-Final-Seal.md`
- **冻结代码提交**：`3e1a991`
- **冻结差异范围**：`99526aa..3e1a991`
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2**

## 1. 结论摘要

本轮确实关闭了上轮 E9 的一个具体故障：`RETRY_REVIEW` 重新派发后，旧代际的 `REVIEWER_TIMEOUT_ABSTAIN` 不再继续毒化新代际，重试后两份新票可以形成自动共识。Schema 环境变量测试、ANSI 结果列不再硬编码、注册表数量也已修正。60/60 自动化测试、CLI PTY 冒烟、Mock E2E、编译和差异洁净度均通过。

但“E9 代际绑定”仍只存在于 timeout 审计查询，未进入 REVIEW_REQUEST→review manifest 的生产/消费协议。独立重放证明：第一代已经生成、但在 `RETRY_REVIEW` 之后才送达的旧 review manifest，会被当作第二代新票并自动推进至 `MERGING`。现有新增测试在重试后重新生成 manifest，却没有任何字段能证明它属于新派发代际，因此不能排除该反例。

此外，上轮其余 5 项 P1 均未在本差异中整改，且 timeout 无生产驱动、REVIEW_REQUEST 部分扇出、push 后远端不确定态、产物归档语义、真实 Adapter 消费链均再次复现或静态确认。当前共 6 项 P1 未关闭。按评审指引，PG-1/PG-2 要求 P0/P1 为零，L3 还要求关键失败/恢复和消费方场景均 VERIFIED，故本次申请不通过。

## 2. 独立机验结果

| 检查项 | 独立结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 60/60 PASS | VERIFIED（仅限现有覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `git diff --check 99526aa..3e1a991` | 返回码 0 | VERIFIED |
| `PYTHONPATH=src python3 -m macao.cli.main test-clis` | 4/4 PASS；均为 `--version` PTY 冒烟 | VERIFIED（仅限冒烟） |
| `PYTHONPATH=src python3 -m macao.cli.main e2e-run` | 7 步显示通过、终态 DONE | VERIFIED（仅限 Mock happy path） |
| E9 旧 timeout disposition 跨代际污染 | 新增测试通过，旧 timeout 不再隔离新票 | VERIFIED |
| E9 延迟到达的旧代际 manifest | 被当作新代际票，任务自动进入 MERGING | CONTRADICTED |
| timeout 到期但无外部调用 | 保持 WAITING_REVIEW，无 timeout audit | CONTRADICTED |
| 第二个 reviewer 发布失败 | 第一条消息已提交，任务仍 WAITING_REVIEW，dev 已 consumed | CONTRADICTED |
| push 成功、`ls-remote` 瞬时失败 | 返回失败并仅执行本地 reset | CONTRADICTED |
| 终态产物生命周期 | archive 有 5 份副本，但 5 份源产物仍存在 | CONTRADICTED |

故障注入摘要：

```text
stale_generation {'state': 'MERGING', 'change': 'MERGING', 'decision': 'APPROVED', 'late_isolated': 0, 'manifest_has_generation': False}
timeout_without_driver {'state': 'WAITING_REVIEW', 'timeout_audits': 0}
partial_publish {'state': 'WAITING_REVIEW', 'codex_pending': 1, 'opencode_pending': 0, 'dev_consumed': 1, 'dispatch_claimed_reviewers': ['codex', 'opencode']}
post_push_uncertainty {'ok': False, 'local_resets': 1}
artifact_sources {'archived': 5, 'sources_still_exist': {'dev': True, 'reviews': 3, 'vote': True}}
```

全部失败路径均在临时 git 仓库和临时 SQLite 中执行，测试脚本已删除，未污染项目业务状态。

## 3. 已确认的有效整改

- **CODE/TEST VERIFIED**：当前派发后的 timeout audit 才会进入当前代际计算；旧派发 timeout 不再使 E9 新票稳定活锁（`src/macao/workflow/orchestrator.py:454-472,754-763`；`tests/test_p0_p1_rectification.py:952-1103`）。
- **CODE/TEST VERIFIED**：新增的两项 E9 测试分别覆盖“重试后两票批准”和“重试后再次超时 HOLD”。
- **CODE VERIFIED**：`test-clis` 的 ANSI 列已由硬编码 `True` 改为扫描 `clean_logs`（`src/macao/adapter/integ_harness.py:102-110`）。
- **TEST VERIFIED**：`MACAO_SCHEMAS_DIR` 现在由测试真实设置和恢复（`tests/test_config.py:116-128`）。
- **DOC VERIFIED**：目录实数为 55 份 result、11 份 request，与 `docs/reviews/STATUS.md` 标题一致；Qwen 文件名已修正。

## 4. P0：必须先解决

本轮未发现需要单列为 P0 的新增问题。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：review manifest 未绑定派发代际，E9 可接受被明确作废的旧票

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:325-364,454-472,791-801`；`docs/schemas/review_manifest.schema.json:6-21`；`src/macao/adapter/mock.py:147-166`；`docs/MACAO_PRD_v2.md:840-841,892-906`

本轮用 audit `sequence_id >= latest_dispatch_seq` 过滤 timeout disposition，但 REVIEW_REQUEST payload、review schema 和 manifest 都没有 `dispatch_generation`、`attempt_id` 或所响应的 `message_id`。E9 删除活跃文件再派发，并不能阻止旧 CLI 进程稍后把第一代结果重新写回同一路径。

独立重放先在隔离目录生成第一代 opencode manifest，之后执行“codex 批准 + opencode timeout → HOLD → RETRY_REVIEW”；重试后提交新 codex 票，再把第一代 opencode 文件延迟送入活跃目录。系统将两票均视为新票，输出 `decision=APPROVED` 并进入 `MERGING`，且没有 `LATE_REVIEW_ISOLATED`。这与 E9“本轮已收意见作废”矛盾。

新增 `test_retry_review_override_full_recovery_and_consensus` 也未验证票的代际：重试后生成的文件只有 checkpoint/round，系统无法证明它响应的是第二代请求。

**验收标准**：每次派发持久化不可变的 attempt/generation；REVIEW_REQUEST、deadline、delivery、ACK 和 review manifest 共同绑定该标识（优先绑定 AEP `message_id`）；collector 只接受当前 attempt，旧 attempt 延迟票必须隔离并保留审计。专项测试必须在 retry 前生成旧文件、retry 后延迟投递，断言其不能参与共识；另用携带新 attempt 的两票证明恢复成功。

### P1-2：timeout 仍没有生产 scanner、ping、重试与升级驱动

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:368-426,428-480`；`src/macao/msg/bus.py:59-137`；`docs/MACAO_PRD_v2.md:832-834,1152-1163,1369-1373`

deadline 仅在外部调用 `detect_timed_out_reviewers()` 或 `collect_and_evaluate_consensus()` 时被检查。仓库没有持续运行/可恢复的 deadline driver；MessageBus 虽有手工 `fail_to_dlq()`，但没有未 ACK 的退避重试 worker、三次重试推进或升级告警流程。

独立以 `per_reviewer=0s` 完成派发后不调用 collector，任务仍保持 `WAITING_REVIEW`，timeout audit 为 0。reviewer 在 deadline 后、首次扫描前写入同 round/ref 文件时，detector 只看文件是否存在，也无法依据到达时间判迟到。

**验收标准**：实现可启动、停止、重启恢复的 deadline/queue driver；持久化 delivery deadline、arrival/ACK time、attempt 和 disposition；用可控时钟自然驱动 ping、最多三次退避重试、DLQ 和持续升级，测试不得直接注入 `timed_out_reviewers` 作为唯一证据。

### P1-3：REVIEW_REQUEST fan-out 仍可部分提交，且审计会虚报全员已派发

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:311-366`；`src/macao/msg/bus.py:21-57`；`docs/MACAO_PRD_v2.md:828-834,1369-1373`

Orchestrator 在发送第一条 reviewer 消息前已转为 `WAITING_REVIEW`、消费 `.dev.yml`，并先写入声称包含全体 reviewer 的 `REVIEW_REQUESTS_DISPATCHED`。随后逐 reviewer 各自调用一次事务性 `publish()`；第二次发布失败时，没有统一事务、outbox、补偿状态或清理路径。

独立注入第二次发布失败后：codex 有 1 条 PENDING、opencode 为 0，dev ledger 为 `consumed=1`，任务仍为 `WAITING_REVIEW`，而 dispatch audit 声称 reviewers 是 `[codex, opencode]`。

**验收标准**：用事务性 outbox/dispatch generation 记录每个 delivery 的事实状态；部分失败后必须幂等补发或进入明确 HOLD/恢复态，审计不得把计划接收人当作成功投递人。覆盖每个持久化边界的崩溃恢复测试。

### P1-4：push 成功后的远端校验不确定态仍被当作可本地回滚的失败

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:115-140`；`src/macao/workflow/orchestrator.py:649-687`；`docs/MACAO_PRD_v2.md:1533-1544`

`git push` 成功后若 `ls-remote` 瞬时失败或返回空，远端可能已经指向 checkpoint。当前实现只 `reset --hard` 本地分支并返回失败，Orchestrator 随即进入 `REWORK`。独立 stub 明确模拟 push 成功、校验瞬时失败，确认执行了一次 local reset。远端、本地和 workflow 状态由此可能三方分叉。

**验收标准**：将 post-push 无法确认持久化为 indeterminate/HOLD，执行有界远端重查并升级人工；只有确认 push 未生效，或远端 compare-and-set/revert 且再次验证成功，才能转换为确定失败/回滚状态。

### P1-5：artifact ledger 的 consumed 仍与 PRD 物理生命周期矛盾

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:71-113`；`docs/MACAO_PRD_v2.md:852-862,1353-1367`

FSM 仍以 `shutil.copy2()` 复制后立即把原记录标记 consumed；没有 PRD 指定的 git 提交、原子 rename/复制完成标志或源删除。独立 E2E 的 archive 确有 5 个文件，但 `.dev.yml`、3 份 `.review.yml` 和 `vote_result.json` 仍全部留在活跃源路径。

因此申请中的“物理产物与 SQLite 账本双向核对 100% 一致”最多证明副本和 ledger 字段存在，不能证明消费生命周期完成，也未覆盖 PRD §11.5 的半完成恢复。

**验收标准**：实现“git 审计 → 原子归档 → 源删除 → ledger 完成”的可补偿流程；测试同时断言 archive hash、源不存在、git 记录和 SQLite 状态，并覆盖复制前后、数据库提交前后的崩溃重扫。

### P1-6：PG-2 所需真实 Adapter 消费方链路仍未验证

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:34-130`；`src/macao/workflow/e2e_runner.py:98-122,194-229`；`src/macao/adapter/codex.py:49-71`；`docs/MACAO_PRD_v2.md:1381-1391,1420-1427`

`test-clis` 只启动四个真实二进制的 `--version`，没有调用真实 Adapter 的 `start → inject_task → ack → stop` 任务链。`e2e-run` 则全部使用 `MockAgentAdapter`，没有从 MessageBus `receive_pending()` 取得权威 envelope；它自行构造 payload，以伪造的 `msg-ack-*` 调用永远返回 True 的 mock ACK，并把 review manifest 直接写到协调仓库而非隔离 worktree。

真实 Codex Adapter 的 `inject_task()` 虽取出 `review_context`，实际 prompt 未使用该 context，也未关联 AEP message ID。故“4/4 真实 CLI PTY”只证明版本进程可启动/退出，“Adapter 契约驱动 E2E”只证明 Mock happy path，尚不满足 PG-2 的消费方场景测试。

**验收标准**：至少选一个真实 Reviewer Adapter，从 MessageBus 接收实际 REVIEW_REQUEST，在请求指定的隔离 worktree 中执行，携带 message/attempt 生成 schema-valid manifest，再对真实 delivery ACK；验证重复 message 幂等、失败不 ACK、重启恢复和产物消费者解析。

## 6. P2/P3：可延期但必须登记

### P2-1：ANSI 检查由硬编码改为运行表达式，但仍不能证明真实清洗发生

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:79-110`；`src/macao/adapter/pty_session.py:71-98`

当前检查扫描的 `clean_logs` 已经由 `PTYSession._read_loop()` 调用 `strip_ansi()` 处理，而且 harness 没有断言原始输出确实包含 ANSI；`clean_logs` 为空时也直接判 True。它可以防止“清洗后仍有残留”，但不能支撑申请中的“ANSI Escape 序列真实输入已验证”。

**验收标准**：增加可控 PTY 子进程，明确输出多类 ANSI/OSC 序列，同时保留测试侧原始输出事实；断言 raw 含控制序列、clean 不含且文本语义保留。真实 CLI `--version` 结果应单列为环境冒烟，不与该确定性 fixture 混称。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 3E1A991-P1-1 | P1 | Workflow/Protocol/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| 3E1A991-P1-2 | P1 | Workflow/Timeout/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 3E1A991-P1-3 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 3E1A991-P1-4 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| 3E1A991-P1-5 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| 3E1A991-P1-6 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |
| 3E1A991-P2-1 | P2 | Adapter/PTY Test | 可延期但须登记 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 保留已验证的局部范围 | E9 timeout 查询等局部实现与测试已对齐；整体仍有 PRD 偏差 |
| L3 SCENARIO-VERIFIED | **不通过** | E9 延迟旧票、timeout 生产驱动、故障恢复和真实消费链未闭环 |
| PG-1 | **不通过** | P1 未清零 |
| PG-2 | **不通过** | 继承 PG-1 失败，且接口消费者场景未 VERIFIED |
| PG-3 / L4 | **不评定** | 本次申请目标不是发布门禁，且 L3 尚未通过 |

## 9. 建议闭环顺序与验收标准

1. 先把 dispatch attempt/message ID 贯通 request、delivery、manifest、ACK、timeout 和 consensus，关闭 E9 延迟旧票与迟到判定漏洞。
2. 在同一 delivery 状态模型上实现 deadline driver、ping、三次退避、DLQ 和升级，并做重启恢复。
3. 将 reviewer fan-out 改为 outbox/幂等可恢复派发，避免状态、审计和实际 delivery 分叉。
4. 将 post-push 不确定态持久化为 HOLD，加入远端重查和显式恢复。
5. 完成产物 git 审计、原子归档、源删除及启动补偿。
6. 以至少一个真实 Adapter 完成 MessageBus → worktree → manifest → ACK 消费链，再执行全量 L3 反例库。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-30-review-request-L3-Final-Seal.md` 中“超时处置一律绑定当前轮次最新一次派发代际”“E9 重试全流程自愈”“彻底根除 E9 重试活锁”应缩窄为“旧 timeout audit 不再污染新派发”；manifest 本身尚未绑定代际。
- “ANSI Escape 序列真实无残留检测通过”应改为“对已清洗日志执行残留扫描”；在 raw 含 ANSI 的前置条件未验证前，不应声明真实序列覆盖。
- “macao e2e-run Adapter 契约驱动”应明确为 Mock Adapter 仿真；真实 AEP 消费、真实 ACK 和真实 worktree 产出尚未验证。
- “5 份物理产物与 SQLite 账本双向核对 100% 一致”应改为“5 份 archive 副本及 consumed ledger 字段存在”；源删除、git 审计与崩溃补偿未实现。
- `docs/reviews/STATUS.md` 的实时门禁状态应在纳入本次复审时保留“待整改/未获 L3”，不得把申请方的完成声明当作授予定级。

## 11. Reviewer 自审记录

- 独立冻结 `3e1a991`，未把当前 HEAD 的动态含义带入证据范围。
- 未引用其他 reviewer 的赞成/反对票作为通过或拒绝依据；历史报告仅用于确定需复验的问题清单。
- 对申请中的“100%”“真实”“彻底根除”“全流程自愈”“双向一致”逐项检查证据边界，没有把测试数量外推到未覆盖场景。
- 每项 P1 均提供代码/规范位置、可复现行为和关闭标准；所有 fault injection 均在临时目录执行并清理。
- 强制检查了字段读取路径、完成声明、确定性措辞、YAML/JSON 可解析性和评审文件命名；未发现本次申请 Markdown/YAML 代码块解析类新增 P0/P1。
