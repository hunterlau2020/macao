# L3 / PG-2 Final 独立复审（Codex）

- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-PG2-Final.md`
- **冻结代码提交**：`7973853`
- **冻结差异范围**：`3e1a991..7973853`
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/EXPERT_QUALITY.md`、`docs/schemas/*.schema.json`
- **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS
- **结论**：**REJECT；不授予 L3 SCENARIO-VERIFIED，不通过 PG-2**

## 1. 结论摘要

本轮有四项可确认进展：E9 两代不同内容的磁盘归档不再直接互相覆盖；`RETRY_REVIEW` 正常路径会删除活跃 `vote_result.json`；迟到票隔离日志在同一派发代际内实现幂等；dev checkpoint 会拒绝明确的 `tests_passed: false` 和不存在的 commit。64/64 自动化测试、真实 CLI `--version` PTY 冒烟、Mock E2E、编译与差异洁净度均通过，冻结提交时 58 份 result / 12 份 request 的目录计数也属实。

但申请将上一轮 Codex P1-1误写成“E9 归档覆盖”。Codex P1-1实际是“review manifest 未绑定派发代际、作废旧票可在 retry 后迟到并参与新共识”；本轮没有修改 REVIEW_REQUEST、review schema 或 collector 的代际关联，该反例仍可自动推进至 `MERGING`。

本轮新增 dev checkpoint 校验还存在直接 fail-open：缺少 `version`、`executor`、`signal` 和整个 `quality_metrics` 的 manifest 被正式 Schema 判无效，却仍被代码接受并触发 `READY_FOR_REVIEW`。新增测试标题声称覆盖 missing EXPLICIT，但实际没有该用例，其“有效”fixture 自身也缺少 Schema 必需的 `executor`。

此外，timeout 生产驱动、消息部分扇出、push 后远端不确定态、artifact 完整生命周期/追加账本、真实 Adapter 消费链仍未整改并再次复现或静态确认。当前共 7 项 P1 未关闭；按评审指引，PG-1/PG-2 的 P0/P1 必须为零，故终局定级不通过。

## 2. 独立机验结果

| 检查项 | 独立结果 | 验证状态 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 64/64 PASS | VERIFIED（仅限现有覆盖） |
| `PYTHONPATH=src python3 -m compileall -q src` | PASS | VERIFIED |
| `git diff --check 3e1a991..7973853` | 返回码 0 | VERIFIED |
| `PYTHONPATH=src python3 -m macao.cli.main test-clis` | 4/4 PASS；实际命令均为 `--version` | VERIFIED（仅限 PTY 冒烟） |
| `PYTHONPATH=src python3 -m macao.cli.main e2e-run` | 7 步显示通过，终态 DONE | VERIFIED（仅限 Mock happy path） |
| 两代不同 review 的磁盘归档 | Gen 1 裸文件和 Gen 2 `g2_*` 均存在 | VERIFIED（仅限磁盘副本） |
| E9 正常路径清理活跃 vote result | 文件不存在 | VERIFIED |
| 迟到票隔离日志重复轮询 | 同代际保持 1 条 | VERIFIED |
| Schema-invalid dev manifest | Schema FAIL，但状态进入 READY_FOR_REVIEW | CONTRADICTED |
| E9 延迟旧代际 review | 被当作新票，自动进入 MERGING | CONTRADICTED |
| timeout 到期但无运行驱动 | 保持 WAITING_REVIEW，无 timeout audit | CONTRADICTED |
| 第二个 reviewer 发布失败 | 已部分提交且 dev 已 consumed | CONTRADICTED |
| push 成功、远端查询瞬时失败 | 仅回退本地 | CONTRADICTED |
| 两代 review 的 artifact ledger | 磁盘 4 份，ledger 仅 2 行且只指向 Gen 2 | CONTRADICTED |

独立反例输出：

```text
invalid_dev_fail_open {'schema_ok': False, 'schema_error': "'version' is a required property", 'transition': 'READY_FOR_REVIEW', 'state': 'READY_FOR_REVIEW'}
stale_generation {'state': 'MERGING', 'change': 'MERGING', 'decision': 'APPROVED', 'manifest_has_generation': False}
timeout_without_driver {'state': 'WAITING_REVIEW', 'timeout_audits': 0}
partial_publish {'state': 'WAITING_REVIEW', 'codex': 1, 'opencode': 0, 'dev_consumed': 1}
post_push_uncertainty {'ok': False, 'local_resets': 1}
generation_ledger {'archive_reviews': ['codex.review.yml', 'g2_codex.review.yml', 'g2_opencode.review.yml', 'opencode.review.yml'], 'ledger_review_rows': 2, 'ledger_paths': ['.../g2_codex.review.yml', '.../g2_opencode.review.yml'], 'active_reviews': 2, 'active_dev': True, 'active_vote': True}
```

所有故障注入均在临时 git 仓库和临时 SQLite 中完成，测试脚本已删除，未修改项目业务状态。

## 3. 已确认的有效整改

- **CODE/TEST VERIFIED**：`WorkflowFSM` 在基础归档文件已存在且内容不同时，按当前 dispatch 数量生成 `g{generation}_*` 路径；两代不同 review 的磁盘证据可同时保留（`src/macao/workflow/fsm.py:83-165`）。
- **CODE/TEST VERIFIED**：`resolve_override(RETRY_REVIEW)` 在正常 unlink 路径下会删除活跃 `vote_result.json`（`src/macao/workflow/orchestrator.py:806-823`）。
- **CODE/TEST VERIFIED**：`LATE_REVIEW_ISOLATED` 使用最新 dispatch sequence 做同代际去重（`src/macao/workflow/orchestrator.py:507-527`）。
- **CODE/TEST VERIFIED**：明确给出 `tests_passed: false` 且未豁免时会拒绝 checkpoint；git 仓库内不存在的 commit 也会被拒绝（`src/macao/workflow/orchestrator.py:221-234`）。
- **DOC VERIFIED**：冻结提交的目录计数确为 58 份 result、12 份 request，与 `STATUS.md` 标题一致。

上述均为局部结论，不外推为 L3/PG-2。

## 4. P0：必须先解决

本轮未发现需要单列为 P0 的问题。

## 5. P1：进入 L3 / PG-2 前必须解决

### P1-1：dev checkpoint 未执行正式 Schema，缺省关键字段时 fail-open

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:194-255`；`docs/schemas/dev_manifest.schema.json:1-67`；`docs/MACAO_PRD_v2.md:204-228`；`tests/test_p0_p1_rectification.py:1340-1402`

代码未调用 `validate_dev_manifest()`，且把 `signal` 缺省成 `EXPLICIT`、把 `tests_passed` 缺省成 True；也不检查 `version` 和 `executor`。独立输入只含 status、round 和存在的 commit，缺少 `version`、`executor`、`signal`、`quality_metrics`。Schema 返回失败，Orchestrator 却推进到 `READY_FOR_REVIEW`。

新增测试的方法名和 docstring 声称验证 missing EXPLICIT，实际三个 case 分别是 tests false、伪造 commit、所谓 valid；没有删除 signal 的 case。第三个“valid”fixture也缺少 Schema 必需的 `executor`，恰好证明代码没有执行 Schema。

代码还只检查 commit “存在”，未检查 PRD §3.3 E6 要求的“相对上一 checkpoint 是新 commit、未被消费”；返工轮可重用旧 checkpoint。

**验收标准**：在任何状态变化和 artifact 注册前调用版本化 `validate_dev_manifest()`；缺少 required 字段一律拒绝；质量门禁使用显式 `is True`；E6 比较当前 task checkpoint 和消费记录，拒绝旧/已消费 commit。正反测试至少覆盖缺 version、executor、signal、quality_metrics、tests 字段、错误类型、旧 commit 和有效 exempt。

### P1-2：review manifest 仍未绑定派发代际，E9 会接受已作废的延迟旧票

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:333-372,462-494,806-823`；`docs/schemas/review_manifest.schema.json:6-21`；`docs/MACAO_PRD_v2.md:840-841`

本轮新增的 generation 只用于选择 archive 文件名。REVIEW_REQUEST payload、review schema 和 collector 仍没有 `dispatch_generation`、`attempt_id` 或被响应的 AEP `message_id`。物理保存旧票不能阻止旧 CLI 进程在 retry 后重新写回活跃目录。

独立重放在 E9 前生成第一代 opencode manifest并暂存；经历 timeout → HOLD → RETRY_REVIEW 后，提交新 codex 票并延迟投递第一代 opencode 票。系统输出 APPROVED 并自动进入 `MERGING`。申请把 Codex P1-1映射为 archive overwrite，未关闭原问题。

此外，E9 对 review/vote 的 unlink 异常全部静默忽略，删除失败后仍重新派发，也会让旧活跃票留在新代际。

**验收标准**：把不可变 attempt/message ID贯通 REVIEW_REQUEST、delivery、deadline、manifest、ACK、timeout 和 consensus；只接受当前 attempt；旧 attempt 延迟票必须隔离。删除/归档失败应 fail-closed 或进入可恢复 HOLD，不得继续派发。

### P1-3：timeout 没有生产 scanner、ping、退避重试、DLQ 与升级驱动

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:376-434,436-488`；`src/macao/msg/bus.py:59-138`；`docs/MACAO_PRD_v2.md:832-834,1152-1163,1369-1373`

timeout 只有在外部主动调用 detector/collector 时才计算。MessageBus 只有手工 DLQ 方法，没有未 ACK delivery 的生产 retry worker。独立以 `per_reviewer=0s` 派发后不调用 collector，任务保持 `WAITING_REVIEW`，timeout audit 为 0。

**验收标准**：实现可运行、可停止、重启可恢复的 deadline/queue driver，以持久化 arrival/ACK/deadline/attempt 自然驱动 ping、最多三次退避、DLQ 和持续升级；测试不应直接注入超时名单作为唯一证据。

### P1-4：REVIEW_REQUEST fan-out 仍可部分提交并虚报全员已派发

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/orchestrator.py:319-372`；`src/macao/msg/bus.py:21-57`；`docs/MACAO_PRD_v2.md:828-834`

任务和 dev artifact 先进入 `WAITING_REVIEW`/consumed，dispatch audit 先声称全员已派发，之后才逐 reviewer 独立 publish。第二次 publish 失败后，独立结果为 codex 1 条、opencode 0 条、dev consumed=1、任务仍 WAITING_REVIEW。

**验收标准**：使用事务性 outbox/可恢复 generation，记录每个 delivery 的真实状态；部分失败后幂等补齐或进入明确 HOLD，审计不得把计划接收人写成成功投递人。

### P1-5：push 后无法确认远端事实时仍只做本地 reset

**验证状态**：CONTRADICTED

**证据**：`src/macao/merge/controller.py:115-140`；`src/macao/workflow/orchestrator.py:664-702`；`docs/MACAO_PRD_v2.md:1533-1544`

push 成功而 `ls-remote` 瞬时失败时，远端可能已前移。当前路径 reset 本地并返回失败，workflow 随后进入 REWORK。独立 stub 再次确认 `local_resets=1`，无法消除远端、本地与任务状态分叉。

**验收标准**：将 post-push 未确认持久化为 indeterminate/HOLD，执行有界重查并升级；仅在确认远端事实或完成远端 compare-and-set/revert 并复验后，才能声明确定失败/回滚。

### P1-6：代际磁盘副本保留，但 artifact 追加账本和完整生命周期仍不成立

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/fsm.py:83-165`；`src/macao/storage/store.py:99-139`；`docs/MACAO_PRD_v2.md:852-862,1353-1367`

磁盘侧现在能得到 4 份两代 review 文件，但 `artifacts` 唯一键不包含 generation，`register_artifact()` 仍 `ON CONFLICT ... DO UPDATE`，`mark_artifact_consumed()` 也更新同一行。独立结果只有每 reviewer 一行，共 2 行，且两行 `archived_path` 都已变成 Gen 2；Gen 1 的 artifact row 被覆盖。这与 PRD §11.5“归档新增行、原行只读、不得覆盖历史审计行”直接矛盾。

归档仍是 `copy2()` 后标记 consumed，没有 git commit、原子 rename/完成标记和源删除；两代流程结束后活跃 `.dev.yml`、2 份 `.review.yml` 和 `vote_result.json` 仍存在。因此“物理产物与数据库记录完全匹配”仍不成立。

**验收标准**：Schema/唯一键显式纳入 generation/attempt；每次生成和归档追加独立不可变 artifact row；实现 git 审计、原子归档、源删除与启动补偿，并测试复制/DB/git 各边界崩溃恢复。

### P1-7：PG-2 所需真实 Adapter 消费方链路仍未验证

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:34-130`；`src/macao/workflow/e2e_runner.py:98-122,194-229`；`src/macao/adapter/codex.py:49-71`；`docs/MACAO_PRD_v2.md:1381-1391,1420-1427`

`test-clis` 仍仅执行四个二进制的 `--version`；`e2e-run` 仍全部使用 Mock Adapter，自行构造 payload和假 ACK，并把 manifest直接写入协调仓库。没有真实 Adapter 从 MessageBus 消费权威 REVIEW_REQUEST、在隔离 worktree 评审、生成 manifest并 ACK delivery。

**验收标准**：至少用一个真实 Reviewer Adapter 完成 MessageBus → actual envelope → isolated worktree → schema-valid manifest → real delivery ACK，覆盖重复 message、失败不 ACK、重启恢复和消费者解析。

## 6. P2/P3：可延期但必须登记

### P2-1：ANSI 检查仍未证明输入中实际存在控制序列

**验证状态**：PARTIALLY_VERIFIED

**证据**：`src/macao/adapter/integ_harness.py:79-110`；`src/macao/adapter/pty_session.py:71-98`

扫描对象已经是 `strip_ansi()` 后的 clean logs，harness 不断言 raw 输出含 ANSI，空日志也判 True。本轮未修改该路径。因此 4/4结果只支持“清洗后未见残留”，不能支持“真实 ANSI 输入已验证”。

**验收标准**：用可控 PTY fixture 明确输出 ANSI/OSC，断言 raw 含控制序列、clean 不含且语义保留；真实 CLI 版本冒烟单独报告。

## 7. Known Issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 7973853-P1-1 | P1 | Workflow/Schema/Checkpoint | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P1-2 | P1 | Workflow/Protocol/Consensus | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P1-3 | P1 | Workflow/Timeout/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P1-4 | P1 | Workflow/MessageBus | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P1-5 | P1 | MergeController | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P1-6 | P1 | Artifact/FSM/Recovery | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P1-7 | P1 | Adapter/E2E | 下次 L3 申请前 | 待补 | OPEN |
| 7973853-P2-1 | P2 | Adapter/PTY Test | 可延期但须登记 | 待补 | OPEN |

## 8. 门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L2 SPEC-CODE-ALIGNED | 保留已验证的局部范围 | 部分整改有效，但 checkpoint、协议和 artifact 与 PRD 不一致 |
| L3 SCENARIO-VERIFIED | **不通过** | invalid artifact、E9 旧票、timeout、恢复和真实消费者场景未闭环 |
| PG-1 | **不通过** | 仍有 7 项 P1 |
| PG-2 | **不通过** | 继承 PG-1 失败，且消费方场景未 VERIFIED |
| PG-3 / L4 | **不评定** | 非本次目标，且 L3 未通过 |

## 9. 建议闭环顺序与验收标准

1. 先让 dev checkpoint 统一调用正式 Schema validator，并关闭缺省字段与旧 commit fail-open。
2. 将 attempt/message ID贯通 review 请求、manifest、timeout、ACK、collector和 artifact。
3. 在统一 delivery 模型上实现 timeout worker和事务性/可恢复 fan-out。
4. 修正 artifact 数据模型为逐代际追加行，完成 git、原子归档、源删除和 reconcile。
5. 将 post-push 未确认态改为持久化 HOLD及远端恢复。
6. 以真实 Adapter 跑通 PG-2 消费链，再重放评审指引 §6全部场景。

## 10. 交叉文档需做的文字修订

- `docs/reviews/2026-08-30-review-request-L3-PG2-Final.md` 的“P1-NEW-9 (Claude) / P1-1 (Codex)”合并映射不正确：Codex P1-1不是磁盘归档覆盖，而是 manifest 没有派发代际。
- “`check_development_checkpoint` 强校验 signal/tests/version”应撤回；当前缺失字段可通过且 version 未读取。
- “代际不可变归档确保审计链”应缩窄为“不同内容的磁盘副本不再覆盖”；SQLite artifacts 仍覆盖代际行，也没有 git 审计。
- “5 份产物物理归档且哈希一致/数据库完全匹配”应注明源仍存在、ledger不是追加语义。
- “真实 CLI PTY跨 Agent 验证”应注明只是 `--version` 进程冒烟；`e2e-run` 应注明为 Mock 仿真。
- `docs/reviews/STATUS.md` 后续登记本次结果时应保持“未获 L3/PG-2、待整改”，不得把申请方完成声明作为定级事实。

## 11. Reviewer 自审记录

- 冻结实际 commit `7973853`，没有将动态 HEAD 带入报告。
- 未以其他 reviewer 的票数代替证据；逐项复验本轮代码和上一轮未决项。
- 专门核对“强校验”“不可变”“100%”“真实”“完全匹配”等确定性声明，发现并重放了缺省字段和代际账本反例。
- 每项 P1 均给出文件/行号、具体行为和关闭标准；故障测试全部使用临时目录并已清理。
- 检查了字段读取位置、Schema required、测试名称与测试体、YAML/JSON 可解析性、注册表计数和评审文件命名。
