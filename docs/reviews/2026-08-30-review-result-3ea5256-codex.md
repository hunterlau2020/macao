# L3 / PG-2 Unanimous Final 独立复审（Codex）

- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Final.md`
- **冻结代码提交**：`3ea5256`
- **冻结差异范围**：`7973853..3ea5256`
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2，不构成“全员一致”**

## 1. 结论摘要

本轮对 dev manifest 的正式 Schema 校验是有效整改：缺 version/executor/signal/quality_metrics、错误 signal、测试失败和不存在 commit 均会 fail-closed；有效测试豁免与完整 manifest 可通过。64/64 自动化测试、真实 CLI `--version` PTY 冒烟、Mock E2E、编译、差异洁净度及冻结提交的 62 result / 13 request 计数均通过。

但 dev checkpoint 仍只验证 commit “存在”，没有验证 E6 所要求的“相对上一轮是新 commit、未被消费”。独立重放把任务置于 round 2 REWORK，并提交完全合法但仍引用 round 1 同一 checkpoint 的 `.dev.yml`，系统再次推进至 `READY_FOR_REVIEW`。

申请只整改 dev Schema 和 E9 源状态，未处理上一轮 Codex 报告中的其余 6 个 P1及 ANSI P2：旧代际 review 仍能在 retry 后参与共识，timeout 无生产驱动，review fan-out 可部分提交，push 后远端不确定态仅回退本地，artifact ledger 仍覆盖代际行且源文件不删除，真实 Adapter 消费链仍缺失。以上均再次复现或静态确认。

E9 新守卫也未完全对齐权威表：PRD §3.3 E9 的唯一源状态是 `CONSENSUS_CHECK`，代码额外允许 `UNKNOWN`；UNKNOWN 的规定动作是人工“Reset to last known state”，不是无条件转入 review。当前共 7 项 P1和 2 项 P2未关闭，故申请目标不通过。

## 2. 独立机验结果

| 检查项 | 独立结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 64/64 PASS | VERIFIED（仅限现有覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `git diff --check 7973853..3ea5256` | 返回码 0 | VERIFIED |
| `PYTHONPATH=src python3 -m macao.cli.main test-clis` | 4/4 PASS；均为 `--version` | VERIFIED（仅限 PTY 冒烟） |
| `PYTHONPATH=src python3 -m macao.cli.main e2e-run` | 7 步通过，终态 DONE | VERIFIED（仅限 Mock happy path） |
| 残缺 dev manifest | Schema-invalid，未发生状态转移 | VERIFIED |
| round 2 复用 round 1 同一 commit | 被接受并进入 READY_FOR_REVIEW | CONTRADICTED |
| E9 延迟旧代际 review | 被接受，自动 APPROVED → MERGING | CONTRADICTED |
| timeout 到期但无运行驱动 | 保持 WAITING_REVIEW，无 timeout audit | CONTRADICTED |
| 第二个 reviewer publish 失败 | 第一条已提交，dev 已 consumed | CONTRADICTED |
| push 成功后远端查询瞬时失败 | 返回失败，仅 local reset | CONTRADICTED |
| 两代 artifact ledger | 磁盘 4 份 review，SQLite 仅 2 行并指向 Gen 2 | CONTRADICTED |
| E9 源状态 | `CONSENSUS_CHECK` 和 `UNKNOWN` 均返回 True | CONTRADICTED（相对权威表） |

独立反例输出：

```text
checkpoint_validation {'invalid_schema_ok': False, 'invalid_transition': None, 'same_commit_round2_transition': 'READY_FOR_REVIEW', 'checkpoint_unchanged': True}
stale_generation {'state': 'MERGING', 'decision': 'APPROVED', 'generation_field': False}
timeout_without_driver {'state': 'WAITING_REVIEW', 'timeouts': 0}
partial_publish {'state': 'WAITING_REVIEW', 'codex': 1, 'opencode': 0, 'dev_consumed': 1}
post_push_uncertainty {'ok': False, 'local_resets': 1}
generation_ledger {'disk_reviews': 4, 'ledger_rows': 2, 'ledger_paths': ['g2_codex.review.yml', 'g2_opencode.review.yml'], 'active_dev': True, 'active_reviews': 2, 'active_vote': True}
e9_sources {'CONSENSUS_CHECK': True, 'UNKNOWN': True, 'all_other_states': False}
```

所有 fault injection 均在临时 git 仓库和临时 SQLite 中完成；临时脚本已删除，未修改项目业务状态。

## 3. 已确认的有效整改

- **CODE/TEST VERIFIED**：`check_development_checkpoint()` 现在先调用 `validate_dev_manifest()`，不再用 permissive default 补足 required 字段（`src/macao/workflow/orchestrator.py:194-260`）。
- **TEST VERIFIED**：新增测试实际覆盖缺 quality_metrics、缺 signal、IMPLICIT signal、缺 version、极简残缺清单、tests false、不存在 commit、合法 exempt 和完整合法 manifest（`tests/test_p0_p1_rectification.py:1348-1511`）。
- **CODE/TEST VERIFIED**：E9 不再从 IDLE/CODING/READY/WAITING/REWORK/MERGING/DONE/CANCELLED 放行；正常 deadlock/timeout 先进入 CONSENSUS_CHECK 后再 retry 的测试已修正（`src/macao/workflow/transitions.py:42-51`）。
- **DOC VERIFIED**：冻结提交时目录为 62 份 result、13 份 request，与 `STATUS.md` 标题一致。

上述只是局部整改，不足以覆盖 L3/PG-2。

## 4. P0：必须先解决

本轮未发现需单列为 P0 的问题。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：E6 仍接受旧/已消费 checkpoint，不满足“新 commit”门禁

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:219-260`；`docs/MACAO_PRD_v2.md:212-228,831,839`；`tests/test_p0_p1_rectification.py:1348-1511`

Schema 校验只能证明结构合法。代码随后只调用 `commit_exists(latest_commit)`，没有比较 task 当前 `checkpoint_ref`，也没有查询 artifact consumed/history。独立设置 round 2 REWORK、当前 checkpoint 为 round 1 SHA，再提交结构完全合法且 review_round=2、但 `latest_commit` 仍为同一 SHA 的 manifest，系统返回 `READY_FOR_REVIEW`，checkpoint 完全未变化。

这会让 Executor 在没有任何新代码的情况下绕过返工门禁，重新触发同一对象评审。新增 9 分支测试没有旧 commit/已消费 commit case。

**验收标准**：E6 必须要求 `latest_commit != task.checkpoint_ref`，并证明新提交位于预期 source branch/history 且未被本任务前序 dev artifact 消费；测试覆盖相同 SHA、祖先回退 SHA、无关分支 SHA、有效后继 SHA和重启后的消费记录。

### P1-2：review manifest 仍未绑定派发代际，E9 可接受作废旧票

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:339-378,468-500,812-829`；`docs/schemas/review_manifest.schema.json:6-21`；`docs/MACAO_PRD_v2.md:840-841`

REVIEW_REQUEST payload、review schema 和 collector 仍没有 attempt/generation/所响应 message ID。独立将第一代 opencode 文件延迟到 RETRY_REVIEW 后投递，系统与新 codex 票形成 APPROVED 并进入 MERGING。磁盘代际归档不解决输入归属问题；unlink 失败仍被静默忽略并继续派发。

**验收标准**：不可变 attempt/message ID贯通 request、delivery、deadline、manifest、ACK、timeout、collector和 artifact；只接受当前 attempt；旧 attempt 延迟票审计隔离；清理/归档失败必须 fail-closed 或进入可恢复 HOLD。

### P1-3：timeout 没有生产 scanner、ping、退避、DLQ 与升级驱动

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:382-440,442-494`；`src/macao/msg/bus.py:59-138`；`docs/MACAO_PRD_v2.md:832-834,1120-1129,1369-1373`

timeout 仍只在外部调用 detector/collector 时计算。以 `per_reviewer=0s` 派发后不调用 collector，任务永久保持 WAITING_REVIEW，且无 timeout audit。MessageBus 没有自动 retry/DLQ worker。

**验收标准**：实现可启停、重启恢复的 deadline/delivery driver，持久化 arrival/ACK/deadline/attempt，自然驱动 ping、最多三次退避、DLQ和持续升级；不得以测试直接传入 timeout 名单代替生产场景。

### P1-4：REVIEW_REQUEST fan-out 仍可部分提交并虚报派发完成

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:325-378`；`src/macao/msg/bus.py:21-57`；`docs/MACAO_PRD_v2.md:828-834`

状态/产物消费和全员 dispatch audit 发生在逐 reviewer publish 之前。第二次 publish 注入失败后，codex 有消息、opencode 无消息、dev consumed=1、任务仍 WAITING_REVIEW。

**验收标准**：以事务性 outbox/可恢复 generation 持久化逐 delivery 事实；部分失败后幂等补齐或 HOLD，审计区分 planned/sent/acked。

### P1-5：push 后远端事实不确定时仍只回退本地

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:115-140`；`src/macao/workflow/orchestrator.py:670-708`；`docs/MACAO_PRD_v2.md:1533-1544`

push 成功、`ls-remote` 瞬时失败时，代码 reset 本地并使 workflow 进入 REWORK，但远端可能已经前移。独立 stub 再次得到 `local_resets=1`。

**验收标准**：持久化 indeterminate/HOLD，执行有界远端重查和人工升级；仅在确认远端事实或完成远端 CAS/revert 并复验后宣告回滚。

### P1-6：artifact 代际账本与完整生命周期仍未实现

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:83-165`；`src/macao/storage/store.py:99-139`；`docs/MACAO_PRD_v2.md:852-862,1353-1367`

磁盘可保留两代 4 份 review，但数据库唯一键没有 generation，注册使用 UPSERT，最终只有每 reviewer 一行且路径指向 Gen 2；Gen 1 artifact row 被覆盖。归档仍是 `copy2()` 后更新 consumed，没有 git commit、原子完成标志和源删除。独立终态仍存在 active dev、2 reviews和 vote result。

**验收标准**：数据模型纳入 attempt/generation，每次生成/归档追加不可变行；实现 git 审计、原子归档、源删除和 reconcile，覆盖每个写入边界崩溃。

### P1-7：真实 Adapter 消费方链路仍未验证

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:34-130`；`src/macao/workflow/e2e_runner.py:98-122,194-229`；`src/macao/adapter/codex.py:49-71`；`docs/MACAO_PRD_v2.md:1381-1391,1420-1427`

`test-clis` 只执行 `--version`；`e2e-run` 仍全部使用 Mock Adapter、自造 payload/ACK并向协调仓库写 manifest。真实 Adapter没有从 MessageBus消费实际 envelope、在隔离 worktree生成产物并 ACK delivery。

**验收标准**：至少一个真实 Reviewer Adapter 完成 MessageBus → envelope → isolated worktree → schema-valid manifest → real ACK，并覆盖重复 message、失败不 ACK和重启恢复。

## 6. P2/P3：可延期但必须登记

### P2-1：E9 仍额外允许权威转移表未列出的 UNKNOWN 源状态

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/transitions.py:42-51`；`docs/MACAO_PRD_v2.md:840-843,1111-1148`

权威表 E9 明确为 `CONSENSUS_CHECK → WAITING_REVIEW`。UNKNOWN 的处置是询问“Reset to last known state?”。当前代码和申请却自行解释为“CONSENSUS_CHECK 或 UNKNOWN”，使 `TransitionTable.can_transition(UNKNOWN, WAITING_REVIEW, E9)` 返回 True。

**验收标准**：若遵循现行 PRD，E9 仅允许 CONSENSUS_CHECK；UNKNOWN 使用独立、携带 last_confirmed_state 的恢复命令。若产品确需 UNKNOWN→WAITING_REVIEW，应先修订权威表、说明 checkpoint/round 前置条件并补正反测试。

### P2-2：ANSI 检查仍未证明 raw 输入实际含控制序列

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:79-110`；`src/macao/adapter/pty_session.py:71-98`

检查对象已经是 strip 后 clean logs，且空日志也判 True；本轮未修改。4/4只证明版本进程可启动/退出以及 clean logs未见残留，不能证明真实 ANSI 输入路径。

**验收标准**：使用可控 PTY fixture 输出 ANSI/OSC，断言 raw 含序列、clean 不含且语义保留；真实 CLI冒烟单列。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 3EA5256-P1-1 | P1 | Workflow/Checkpoint | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P1-2 | P1 | Workflow/Protocol/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P1-3 | P1 | Workflow/Timeout/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P1-4 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P1-5 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P1-6 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P1-7 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |
| 3EA5256-P2-1 | P2 | Workflow/FSM/PRD | 下次规范修订 | 待补 | OPEN |
| 3EA5256-P2-2 | P2 | Adapter/PTY Test | 可延期但须登记 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 保留已验证的局部范围 | Schema 门禁有效；E6、协议、FSM和 artifact 仍有规范偏差 |
| L3 SCENARIO-VERIFIED | **不通过** | 返工、E9、timeout、失败恢复和真实消费场景未闭环 |
| PG-1 | **不通过** | 仍有 7 项 P1 |
| PG-2 | **不通过** | 继承 PG-1 失败，且消费方场景未 VERIFIED |
| “全员一致” | **不成立** | 本次 Codex 独立结论为 REJECT；投票不能覆盖可复现反例 |

## 9. 建议闭环顺序与验收标准

1. 先补 E6 新/未消费 commit 校验，并修正 E9 UNKNOWN 规范偏差。
2. 将 attempt/message ID贯通 review request、manifest、timeout、ACK、collector和 artifact。
3. 实现 timeout driver和事务性/可恢复 fan-out。
4. 将 artifact 改为逐代际追加行，完成 git、原子归档、源删除与 reconcile。
5. 将 post-push 未确认态改为持久化 HOLD和远端恢复。
6. 用真实 Adapter 跑通 PG-2 消费链，再重放评审指引 §6全部场景。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Final.md` 的“核心问题全部彻底闭环”应撤回；申请没有列入上一轮 Codex P1-2至 P1-7和 P2-1。
- dev Schema fail-open可声明关闭，但“checkpoint不变式彻底闭环”应排除 E6，直到验证新/未消费 commit。
- “E9 限 CONSENSUS_CHECK / UNKNOWN 对齐 PRD §3.3:841”不属实；该行只列 CONSENSUS_CHECK。
- “多代际不可变归档完整审计”应注明 SQLite artifact行仍覆盖且无 git/源删除。
- “真实 CLI”“数据库完全匹配”应分别注明 `--version` 冒烟和 Mock E2E 的边界。
- `STATUS.md` 后续登记本次结果时应保持未获 L3/PG-2；“Qwen/Kimi 授予”不能替代 P1 清零。

## 11. Reviewer 自审记录

- 冻结实际 commit `3ea5256`，未使用动态 HEAD作证据。
- 独立重放上一轮所有 Codex P1/P2，不以“全员一致”标题或其他 reviewer 票数代替事实。
- 专门核对 Schema通过与业务不变式的区别，并验证 round 2相同 commit反例。
- 每项 P1均给出代码/规范位置、具体行为和关闭标准；故障注入均在临时目录执行并清理。
- 检查字段读取路径、Schema required、测试体、状态表、强声明、注册表数量和文件命名。
