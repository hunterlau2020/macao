# L3 / PG-2 Unanimous Seal 独立复审（Codex）

- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Seal.md`
- **冻结代码提交**：`8296f3c`
- **冻结差异范围**：`3ea5256..8296f3c`
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2，不构成“全员一致封板”**

## 1. 结论摘要

本轮两处整改均有局部效果：E9 现已严格限制为 `CONSENSUS_CHECK → WAITING_REVIEW`；E6 会拒绝与上一 checkpoint 完全相同的 SHA以及本任务已消费的相同 dev commit。65/65 自动化测试、真实 CLI `--version` PTY 冒烟、Mock E2E、编译和差异洁净度均通过；冻结提交时 66 份 result / 14 份 request 的目录计数属实。

但 E6 的“新 commit”判断仍只是字符串不等且对象存在，没有验证提交拓扑。独立重放以 round 1 checkpoint 的祖先 commit 作为 round 2 `latest_commit`，该 SHA不同、存在且未作为 dev artifact消费，于是系统接受它、把 checkpoint倒退并进入 `READY_FOR_REVIEW`。这仍不满足“返工产生新 commit”的语义。

本轮没有触及上一轮其余 6 个 P1及 ANSI P2。旧代际 review 可在 retry 后参与新共识、timeout 没有生产驱动、消息扇出可部分提交、push 后远端不确定态仅回退本地、artifact ledger 覆盖代际且源文件残留、真实 Adapter 消费链缺失，均再次复现或静态确认。

当前仍有 7 项 P1和 1 项 P2。按评审指引，PG-1/PG-2 要求 P0/P1 为零，且 PG-2要求消费方场景验证，因此本次封板申请不通过。

## 2. 独立机验结果

| 检查项 | 独立结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 65/65 PASS | VERIFIED（仅限现有覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `git diff --check 3ea5256..8296f3c` | 返回码 0 | VERIFIED |
| `PYTHONPATH=src python3 -m macao.cli.main test-clis` | 4/4 PASS；均为 `--version` | VERIFIED（仅限 PTY 冒烟） |
| `PYTHONPATH=src python3 -m macao.cli.main e2e-run` | 7 步通过，终态 DONE | VERIFIED（仅限 Mock happy path） |
| E6 相同 SHA | 拒绝，保持 REWORK | VERIFIED |
| E6 新后继 commit | 接受并进入 READY_FOR_REVIEW | VERIFIED（现有测试范围） |
| E6 提交祖先 SHA | 接受，checkpoint 从新 SHA倒退到旧 SHA | CONTRADICTED |
| E9 状态源 | 仅 CONSENSUS_CHECK 返回 True | VERIFIED |
| E9 延迟旧代际 review | 被接受，APPROVED → MERGING | CONTRADICTED |
| timeout 到期但无运行驱动 | WAITING_REVIEW，timeout audit=0 | CONTRADICTED |
| 第二个 reviewer publish 失败 | 第一条已提交，dev consumed=1 | CONTRADICTED |
| push 成功、远端查询瞬时失败 | 返回失败，仅 local reset | CONTRADICTED |
| 两代 artifact ledger | 磁盘 4 份 review，ledger 仅 2 行且指向 Gen 2 | CONTRADICTED |

独立反例摘要：

```text
rework_ancestor {'previous': 'c01d0f82', 'submitted_ancestor': '50fd6bb2', 'is_ancestor': True, 'transition': 'READY_FOR_REVIEW', 'new_checkpoint': '50fd6bb2'}
stale_generation {'state': 'MERGING', 'decision': 'APPROVED', 'generation_field': False}
timeout_without_driver {'state': 'WAITING_REVIEW', 'timeouts': 0}
partial_publish {'state': 'WAITING_REVIEW', 'codex': 1, 'opencode': 0, 'dev_consumed': 1}
post_push {'ok': False, 'local_resets': 1}
generation_ledger {'disk_reviews': 4, 'ledger_rows': 2, 'paths': ['g2_codex.review.yml', 'g2_opencode.review.yml'], 'active_dev': True, 'active_reviews': 2, 'active_vote': True}
e9_sources {'CONSENSUS_CHECK': True}
```

所有 fault injection 均在临时 git 仓库和临时 SQLite 中完成；临时脚本已删除，未污染项目业务状态。

## 3. 已确认的有效整改

- **CODE/TEST VERIFIED**：E6 会拒绝 `latest_commit == task.checkpoint_ref`，并查询本任务已 consumed 的同 SHA dev artifact（`src/macao/workflow/orchestrator.py:236-254`）。
- **TEST VERIFIED**：新增测试通过完整 round 1拒绝 → REWORK round 2流程，覆盖相同 SHA拒绝与直接后继新 commit接受（`tests/test_p0_p1_rectification.py:1511-1623`）。
- **CODE/TEST VERIFIED**：E9 只从 CONSENSUS_CHECK 放行，不再允许 UNKNOWN（`src/macao/workflow/transitions.py:42-51`）。
- **DOC VERIFIED**：冻结提交时目录为 66 份 result、14 份 request，与 `STATUS.md` 标题一致。

这些局部整改不能外推为 L3/PG-2。

## 4. P0：必须先解决

本轮未发现需单列为 P0 的问题。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：E6 未验证提交拓扑，祖先回退或无关分支 SHA可冒充“新 commit”

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:236-254`；`docs/MACAO_PRD_v2.md:212-228,831,839`；`tests/test_p0_p1_rectification.py:1511-1623`

当前 gate 只验证：SHA不同于上一 checkpoint、没有同 SHA consumed dev row、对象存在。它不验证 `previous_checkpoint` 是 `latest_commit` 的祖先，也不验证提交属于任务 source branch。因此旧祖先、其他分支或孤立 commit都可能通过。

独立临时仓库包含 A→B 两个提交，任务 round 2处于 REWORK且 checkpoint=B。提交结构合法、review_round=2但 `latest_commit=A` 的 manifest后，系统返回 READY_FOR_REVIEW并把 checkpoint改为 A。新增测试只覆盖 B→C 正常后继，没有祖先回退和无关分支反例。

**验收标准**：E6 在对象存在之外必须验证上一 checkpoint 是新 checkpoint 的严格祖先（如 `merge-base --is-ancestor prev new`成功且 SHA不同），并验证新 SHA可从预期 source branch解析；测试覆盖相同 SHA、祖先回退、无关分支、孤立 commit、有效直接/多提交后继及重启后的 consumed记录。

### P1-2：review manifest 仍未绑定派发代际，E9 接受作废旧票

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:353-392,496-514,826-843`；`docs/schemas/review_manifest.schema.json:6-21`；`docs/MACAO_PRD_v2.md:840-841`

REVIEW_REQUEST、review schema和 collector仍无 attempt/generation/响应 message ID。第一代 opencode manifest在 retry 后延迟投递，仍与新 codex票形成 APPROVED并进入 MERGING。归档代际只解决输出文件名，不解决输入归属；unlink异常仍被静默忽略。

**验收标准**：将不可变 attempt/message ID贯通 request、delivery、deadline、manifest、ACK、timeout、collector和 artifact；仅接受当前 attempt，旧票隔离；清理/归档失败必须 fail-closed或进入可恢复 HOLD。

### P1-3：timeout 没有生产 scanner、ping、退避、DLQ及升级驱动

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:396-454,456-508`；`src/macao/msg/bus.py:59-138`；`docs/MACAO_PRD_v2.md:832-834,1120-1129,1369-1373`

timeout只有在外部主动调用 detector/collector时推进。`per_reviewer=0s` 派发后不调用 collector，任务仍为 WAITING_REVIEW且无 timeout audit。MessageBus没有自动重试/DLQ worker。

**验收标准**：实现可启停、重启恢复的 deadline/delivery driver，持久化 arrival/ACK/deadline/attempt，自然驱动 ping、最多三次退避、DLQ和持续升级。

### P1-4：REVIEW_REQUEST fan-out 仍可部分提交

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:333-392`；`src/macao/msg/bus.py:21-57`；`docs/MACAO_PRD_v2.md:828-834`

状态、dev消费和全员 dispatch audit先于逐 reviewer publish。第二次 publish失败后，codex有消息、opencode无消息，dev已 consumed，任务仍 WAITING_REVIEW。

**验收标准**：用事务性 outbox/可恢复 generation记录每个 delivery事实；部分失败后幂等补齐或 HOLD，区分 planned/sent/acked。

### P1-5：push 后远端事实不确定时仍只回退本地

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:115-140`；`src/macao/workflow/orchestrator.py:698-722`；`docs/MACAO_PRD_v2.md:1533-1544`

push成功而 `ls-remote` 瞬时失败时，当前代码 reset本地并使 workflow进入 REWORK；远端可能已经前移。独立 stub再次确认 `local_resets=1`。

**验收标准**：持久化 indeterminate/HOLD并有界重查；只有确认远端事实或远端 CAS/revert复验成功后才声明回滚。

### P1-6：artifact 代际追加账本与完整生命周期仍未实现

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:83-165`；`src/macao/storage/store.py:99-139`；`docs/MACAO_PRD_v2.md:852-862,1353-1367`

磁盘保留两代 4 份 review，但 SQLite唯一键无 generation且注册使用 UPSERT，最终仅每 reviewer一行并指向 Gen 2。归档仍为 copy2后标记 consumed，没有 git commit、原子完成标志和源删除；终态 active dev/reviews/vote均存在。

**验收标准**：数据模型纳入 attempt/generation，每次生成/归档追加不可变行；实现 git审计、原子归档、源删除及 reconcile，并覆盖写入边界崩溃。

### P1-7：PG-2 真实 Adapter 消费方链路仍未验证

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:34-130`；`src/macao/workflow/e2e_runner.py:98-122,194-229`；`src/macao/adapter/codex.py:49-71`；`docs/MACAO_PRD_v2.md:1381-1391,1420-1427`

`test-clis` 仍只执行 `--version`；`e2e-run` 全部使用 Mock Adapter、自造 payload/ACK并向协调仓库写 manifest。真实 Adapter没有消费实际 MessageBus envelope、在隔离 worktree生成产物和 ACK delivery。

**验收标准**：至少一个真实 Reviewer Adapter跑通 MessageBus → envelope → isolated worktree → schema-valid manifest → real ACK，并覆盖重复 message、失败不 ACK和重启恢复。

## 6. P2/P3：可延期但必须登记

### P2-1：ANSI 检查未证明 raw 输入实际包含控制序列

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:79-110`；`src/macao/adapter/pty_session.py:71-98`

检查对象已是 strip后的 clean logs，空日志也判 True；本轮未修改。4/4只证明版本进程生命周期和 clean logs无可见残留。

**验收标准**：可控 PTY fixture明确输出 ANSI/OSC，断言 raw含序列、clean不含且语义保留；真实 CLI冒烟单列。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 8296F3C-P1-1 | P1 | Workflow/Git/Checkpoint | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P1-2 | P1 | Workflow/Protocol/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P1-3 | P1 | Workflow/Timeout/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P1-4 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P1-5 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P1-6 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P1-7 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P2-1 | P2 | Adapter/PTY Test | 可延期但须登记 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 保留已验证的局部范围 | E9已对齐；E6拓扑、协议和 artifact仍偏离规范 |
| L3 SCENARIO-VERIFIED | **不通过** | 返工回退、E9旧票、timeout、恢复和真实消费场景未闭环 |
| PG-1 | **不通过** | 仍有 7 项 P1 |
| PG-2 | **不通过** | 继承 PG-1失败，且消费方场景未 VERIFIED |
| “全员一致封板” | **不成立** | 本次 Codex结论为 REJECT，且存在可复现 P1反例 |

## 9. 建议闭环顺序与验收标准

1. 先用 git拓扑和 source branch约束真正关闭 E6 freshness。
2. 将 attempt/message ID贯通 review request、manifest、timeout、ACK、collector和 artifact。
3. 实现 timeout driver及事务性/可恢复 fan-out。
4. 将 artifact改为逐代际追加行，完成 git、原子归档、源删除和 reconcile。
5. 将 post-push未确认态改为持久化 HOLD及远端恢复。
6. 用真实 Adapter完成 PG-2消费链，再重放评审指引 §6全部场景。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Seal.md` 的“E6彻底闭环”应缩窄为“拒绝相同/同任务已消费 SHA”；祖先和无关分支仍可通过。
- 申请仍未列入上一轮 Codex P1-2至 P1-7及 ANSI P2，不得据此宣称核心问题全部关闭。
- “多代际不可变归档完整审计”应注明 SQLite artifact行仍覆盖且无 git/源删除。
- “真实 CLI”“数据库完全匹配”应分别注明 `--version` 冒烟与 Mock E2E边界。
- `STATUS.md` 后续应登记本次未获 L3/PG-2结论；其他 reviewer支持票不能覆盖 P1。

## 11. Reviewer 自审记录

- 冻结实际 commit `8296f3c`，未用动态 HEAD作证据。
- 独立复验本轮两处代码，并重放上一轮全部 Codex P1/P2，不以“全员一致”标题或票数代替证据。
- 区分“SHA不同/存在”与“git拓扑上的新后继 commit”，新增祖先回退反例。
- 每项 P1均给出文件/行号、具体行为和关闭标准；故障测试均使用临时目录并已清理。
- 检查字段路径、Schema、测试体、状态表、确定性声明、注册表计数和文件命名。
