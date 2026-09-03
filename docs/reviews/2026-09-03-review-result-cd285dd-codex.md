# PRD v2.5 Design Sync 与 UseCases v2.5 Alignment 独立复审结论

- **评审日期**：2026-09-03
- **评审对象**：`cd285dd`（申请文件：`2026-09-03-review-request-cd285dd-PRD-v2.5-Design-Sync.md`、`2026-09-03-review-request-cd285dd-UseCases-v2.5-Alignment.md`）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md`、全量 `docs/usercases/`
- **结论**：**REJECT — 不授予 L1 DOC-ALIGNED / PG-0。**

本轮补齐了配置期独裁帽、`vote_result_ref` 必填和 AEP 递归字节预算的部分契约；PRD 代码块和新增 fixture 也能通过结构校验。但超时审计的机器契约仍不完整，且申请声称已经闭环的加权计票与 disposition 状态机在当前实现中可被直接反例推翻。按 Guidelines §2、§3、§8，不能以全绿 happy-path 测试替代这些反例。

## 证据状态

| 维度 | 状态 | 结论 |
|---|---|---|
| DOC / SPEC | CONTRADICTED | 超时弃权的来源、deadline 与最后 ping 被 PRD/提案要求严格留痕，但 `vote_result` 契约不强制这些数据。 |
| CODE | CONTRADICTED | 共识引擎仍按未加权票数与浮点比例计票；Orchestrator 仍绕过 disposition 直接进入 `MERGING`。 |
| TEST | VERIFIED（存在覆盖缺口） | 93 个测试通过；现有测试未覆盖 2:1:1 权重反例、带 issue 的批准必须 HOLD，以及 timeout 审计字段。 |
| OPS | NOT_APPLICABLE | 本次目标为文档/实施基线复审，未申请 L4 运行演练。 |

## 已确认项

1. `macao_config` 的配置期语义校验已经覆盖独裁帽、最低席位法定人数、最低权重法定人数与最少胜方席位：`src/macao/core/schema.py:113-157`，新增的三份无效配置 fixture 也已接入 `tests/test_schema.py:194-247`。
2. `review_disposition` 已将 `vote_result_ref` 纳入顶层必填字段：`docs/schemas/review_disposition.schema.json:6-17`；PRD 与 UC-6 示例均已补齐该引用：`docs/MACAO_PRD_v2.md:676-681`、`docs/usercases/UC6-issue-triage-rework.md:44-48`。
3. AEP envelope 的八类顶层 payload 已收紧，运行时预算检查也会递归检查嵌套字符串：`docs/schemas/aep_envelope.schema.json:33-320`、`src/macao/msg/envelope.py:30-60`。
4. 结构测试通过：`tests/test_schema.py`、`tests/test_config.py`、`tests/test_msg_bus.py`、`tests/test_prd_snippets_schema.py`、`tests/test_consensus.py`、`tests/test_context_builder.py`、`tests/test_fsm.py`、`tests/test_state_store.py` 共 33 项；其余回归组 43 项；`tests/test_phase3.py` 17 项，合计 **93/93**。`python3 -m compileall -q src tests` 也通过。

## P0：必须先解决

无。

## P1：发布/进入下一阶段前应修正

### P1-1：`weighted_2/3_v1` 仍未接入真实权重与五重纯整数门禁

- **规范证据**：PRD 要求按配置总权重执行双法定人数、胜方权重与最少胜方席位五重门禁：`docs/MACAO_PRD_v2.md:329-340`；变更清单又将该能力标为 `src/macao/consensus/vote.py` 的实现项：`docs/v2.5_CODE_CHANGE_INVENTORY.md:74-76`；UC-5 规定从 `macao.yaml` 读取静态 `vote_weight`：`docs/usercases/UC5-consensus-tally.md:27`。
- **反例 / CODE 证据**：`src/macao/consensus/engine.py:28-68` 只累加人数，按 `approve_count / effective_votes` 浮点比较，完全未读取 `vote.weight`、配置总权重、两个 quorum 或 `minimum_winning_seats`。`VoteAggregator` 也没有接收 reviewer-weight/policy 快照的参数；它构造的每张 manifest 票没有 `weight`：`src/macao/consensus/vote.py:68-139`，Orchestrator 调用时只传入 `configured_reviewers` 数：`src/macao/workflow/orchestrator.py:674-683`。
- **可复现步骤**：向 `ConsensusEngine.evaluate(votes, 3)` 输入 `[{YES, weight:2}, {NO, weight:1}, {NO, weight:1}]`，实测返回 `REWORK_REQUIRED`。按 PRD，`E_W=4`、YES 权重 2 与 NO 权重 2 均不满足 `3*w >= 2*E_W`，唯一结果应为 `DEADLOCK`。
- **修复与验收**：让 Orchestrator 从已校验 `macao.yaml` 传入冻结的 reviewer 权重及 policy；以整数交叉乘法实现五重门禁；将配置快照、各票 `weight/source` 和 breakdown 从同一输入导出。新增 2:1:1 的 YES/NO/NO、权重 quorum 不足、席位 quorum 不足、胜方席位不足与超时弃权的端到端断言。

### P1-2：带 issue 的批准及 disposition 闭环仍被直接绕过

- **规范证据**：PRD 要求任一 issue 存在时发送 `DISPOSITION_REQUIRED` 并停在 `CONSENSUS_CHECK`：`docs/MACAO_PRD_v2.md:75-85`；E4 仅允许“无 issue”或已存在精确覆盖的 FINAL disposition 时进入 `MERGING`：`docs/MACAO_PRD_v2.md:873-881`。提案与 UC-5 作出同样约束：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:120-129`、`docs/usercases/UC5-consensus-tally.md:54-58`。
- **反例 / CODE 证据**：`src/macao/workflow/orchestrator.py:674-712` 写入 vote result 后，`decision == APPROVED` 无条件执行 E4 → `MERGING`；没有读取或校验 `requires_disposition`，也没有发布 `AEPType.DISPOSITION_REQUIRED`。同一文件中的 E5 只发布 `REWORK_REQUEST`。现有 happy-path 回归还把这种旧行为当作成功：`tests/test_orchestrator_sim.py:97-101`。
- **影响**：任何 `YES_APPROVE + ADVISORY` 或少数 `NO_APPROVE + BLOCKING` 但加权结果为 APPROVED 的检查点，可以不经 Executor 的逐项处置、`vote_result_ref` 反向绑定及 E4/E5a 守卫直接合并。
- **修复与验收**：实现 disposition 的受理、`checkpoint_ref/review_round/vote_result_ref/issues_index_sha256` 交叉验证、精确集合覆盖验证与 E4/E5a 分流。审批含一条 advisory 的场景必须停在 HOLD 并发 Type E；仅提交合法 FINAL 且所有 `requires_new_checkpoint=false` 后才可 MERGING；任一 `true` 必须 E5a 到 REWORK。

### P1-3：超时弃权的审计来源仍不能由 `vote_result.json` 唯一验证

- **规范证据**：D-3 要求 manifest 与 timeout 弃权严格区分：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:34-36`。该文又规定 timeout 合成票必须记录 `source: timeout`、deadline、最后一次 ping，且 `reviewers_responded` 只统计合法 manifest、`reviewers_accounted` 才加 timeout 席位：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:107-114`；UC-9 也要求 `source: "timeout"`：`docs/usercases/UC9-timeout-daemon.md:29-41`。
- **反例 / SPEC + CODE 证据**：`docs/schemas/vote_result.schema.json:39-47` 将 `source` 设为可选，且根本没有 deadline/last-ping 字段。构造含 `ABSTAIN` 但没有 `source` 的 vote result，`validate_vote_result()` 实测返回 `True`。同时 `VoteAggregator.generate_vote_result()` 合成 timeout 票时没有写入 `source`：`src/macao/consensus/vote.py:128-137`，并把 `reviewers_responded` 设为包含 timeout 的 `len(votes_list)`：`src/macao/consensus/vote.py:172-175`。
- **影响**：审计端无法区分主动弃权、超时弃权和伪造/遗漏来源；响应人数也与 PRD 定义相悖。
- **修复与验收**：为每张 vote 强制 `source`；对 `source=timeout` 强制 `deadline`、最后 ping 的可验证引用/时间与 `confidence=0`，对 `source=manifest` 强制 manifest 输入产物引用。由 manifest 数计算 `reviewers_responded`，由 manifest+timeout 合成票计算 `reviewers_accounted`。补充“缺 source / 缺 timeout 元数据 / timeout 被计入 responded”三组失败关闭测试。

## P2/P3：可延期但需登记

### P2-1：`review_disposition` 未按提案承诺封闭根对象，未知控制字段会静默通过

- **证据**：提案把 Schema 收紧为 `additionalProperties: false` 列为实施顺序第 2 步：`docs/PRD_CHANGE_PROPOSAL_v2.5.md:498-505`。但 `docs/schemas/review_disposition.schema.json:5-138` 没有根级 `additionalProperties: false`，`executor`、`full_document` 和 disposition item 也未封闭。将 `unrecognized_control_field: accepted` 加到其他完整合法 disposition 后，`validate_review_disposition()` 实测返回 `True`。
- **建议**：封闭每个具有固定契约的对象；为顶层未知字段、伪造控制字段和嵌套未知 ref 字段添加负例 fixture。

### P2-2：补丁未通过 whitespace 检查

- **证据**：`git diff --check cd285dd^ cd285dd` 报告 `src/macao/core/schema.py:166: new blank line at EOF.`
- **建议**：移除多余空白行，并把 `git diff --check` 纳入申请所称的自动化验证。

## 交叉文档需做的文字修订

1. 在两份申请中，把“已完成代码与文档级物理闭环”“当前实现基线”等完成性表述改为“Schema/文档阶段已完成，运行时代码尚待 P1-1～P1-3 闭环”，或在完成实现与反例测试后再恢复该表述。
2. `docs/usercases/README.md:9` 将“设计稿 = …已与 PRD v2.5 全面实装对账”与 UC-4/5/8/9 的“待实现”状态统一，避免把设计对账误读为运行时实现完成。
3. 将 `docs/v2.5_CODE_CHANGE_INVENTORY.md` 中的实现描述明确标成计划项，直到源文件和测试路径真实存在并已验收；例如其列出的 `src/macao/storage/evidence.py` 与 `tests/unit/test_consensus_weighted.py`、`tests/unit/test_review_disposition.py` 当前均不存在。

## 建议的闭环顺序与验收标准

1. 先实现并端到端验证 P1-1 的统一权重输入、纯整数五重门禁和不可变 policy snapshot。
2. 再实现 P1-3 的 timeout 票据模型与 terminal artifact 语义，确保超时场景可审计且计数正确。
3. 实现 P1-2 的 Type E、disposition 受理与 E4/E5a 守卫；用“批准但含 issue”覆盖不能直接合并的关键反例。
4. 收紧 disposition Schema、修正 whitespace，并更新申请/README/变更清单中的实施状态。
5. 重新申请时提供上述反例的自动化测试输出；届时可重新判定 DOC/SPEC 与 CODE 的对应门禁，不能以现有 93 个测试替代。

## Reviewer 自审记录

- 已执行 Guidelines §9 强制检查：字段读取路径、完成性表述、确定性语言与 YAML/JSON 可解析性均已抽查。
- 本轮新增重点：对上轮“Schema 必填/预算”修复继续追踪到运行时消费路径、终端审计产物和非等权票型，避免将静态 schema 正例误判为闭环。
