# PRD v2.5 Design Sync 与 UseCases v2.5 Alignment 独立复审结论

- **评审日期**：2026-09-03
- **评审范围**：`docs/reviews/2026-09-03-review-request-73576c5-PRD-v2.5-Design-Sync.md`、`docs/reviews/2026-09-03-review-request-73576c5-UseCases-v2.5-Alignment.md`，以及目标提交 `73576c5`
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md`、UC-4/5/6/9
- **结论**：**REJECT；不授予 L1 DOC-ALIGNED / PG-0（作为 v2.5 实施基线的认证）**。

文档对加权门禁、处置分流和超时票据的规则表述能够相互对应，但申请声称的运行时闭环仍有会改变 FSM 结果或破坏审计锚定的 P1。因而不能把“Schema 可解析、局部单测通过”外推为实施基线已经对齐。

## 已对齐 / 已确认项

1. **DOC/SPEC — VERIFIED**：PRD 的五重加权门禁定义（`docs/MACAO_PRD_v2.md:329-340`）与 UC-5/UC-9 的有效席位、有效权重定义一致；`macao.yaml` 的四席位 `seat_quorum_required`、`weight_quorum_required` 均已改为 3，符合 `ceil(2N/3)`。
2. **CODE/TEST — PARTIALLY_VERIFIED**：`ConsensusEngine.evaluate()` 已以整数交叉乘法实现权重 quorum 与胜方门禁（`src/macao/consensus/engine.py:86-105`）。直接重放 `[YES,w=2] [NO,w=1] [NO,w=1]` 且 `N=3,W=4` 得到 `DEADLOCK`，与 PRD 一致。
3. **CODE/SPEC — VERIFIED**：`review_disposition.schema.json` 的根、`executor`、`full_document`、`vote_result_ref` 与条目对象均已封闭；未知字段 fixture 被拒绝。
4. **TEST — VERIFIED**：分两组执行全部测试，共 **97** 项通过（52 + 45）；`python3 -m compileall -q src tests` 通过。测试通过不覆盖下列反例。

## P0：必须先解决

无。

## P1：发布/进入下一阶段前应修正

### P1-1：编排器仍以未加权的预判结果驱动 FSM

- **证据**：`src/macao/workflow/orchestrator.py:566-600` 组装 `votes_list` 时没有 `weight`，并在 597-600 行调用 `ConsensusEngine.evaluate()` 时没有传入 `configured_weight` 或 `policy`。该未加权 `decision` 随后直接控制 DEADLOCK/HOLD（605 行）、返工上限（652 行）和 E4/E5 分流（708、758、760 行）。虽然 676-697 行之后调用生成器时才传入权重与 policy，生成器所得 `vdata["decision"]` 没有回写前述 `decision`。
- **可复现反例**：配置 `N=3,W=4`、权重 `2:1:1`，票为高权 `YES_APPROVE`、两低权 `NO_APPROVE`。按 PRD，YES 与 NO 均为权重 2，必须 `DEADLOCK`；直接调用加权引擎的结果也是 `DEADLOCK`。但编排器 566-600 行的输入退化为 `YES, NO, NO` 三张等权票，得到 `REWORK_REQUIRED`，随后 760 行 E5 进入 `REWORK`，而生成的 `vote_result.json` 可能记录 `DEADLOCK`。
- **影响**：机器产物与 SQLite/FSM 状态可互相矛盾，且 v2.5 的 D-6 加权规则未实际控制工作流。
- **修正与验收**：先从冻结的 team/policy 建立一次带权、带全量配置总权重的票面，使用同一个 `vdata.decision`（或同一纯函数返回值）决定所有早退和 E3/E4/E5 分支。加入 orchestrator 级的 `2:1:1` 正反例、权重 quorum 不足和最少胜方席位反例，断言状态、消息和 `vote_result.json.decision` 三者一致。

### P1-2：FINAL disposition 没有与当前计票结果绑定，也没有 100% issue 覆盖守卫

- **证据**：PRD 要求只接受当前 FSM 的 task/checkpoint/round 产物（`docs/MACAO_PRD_v2.md:735-737`），并要求 E4/E5a 的 FINAL disposition 精确覆盖 `issues_index`（`docs/MACAO_PRD_v2.md:708-715,875,879`；`docs/usercases/UC6-issue-triage-rework.md:62-70,79-91`）。但 `src/macao/workflow/orchestrator.py:798-830` 仅作静态 Schema 校验，然后对任意 `FINAL` 以 `any(requires_new_checkpoint)` 分流；它从不读取并比对当前 `vote_result.json`，也不校验 task_id、checkpoint_ref、round、executor、`vote_result_ref.sha256`、`issues_index_sha256` 或 issue-id 集合。
- **可复现反例**：将有效 fixture 的 `task_id` 改为 `foreign-task`、`checkpoint_ref` 改为 `foreign-ref`、两个 hash 改为任意非空字符串并令 `dispositions: []`；`validate_review_disposition()` 返回 `(True, None)`。在 `CONSENSUS_CHECK` 调用 `submit_disposition()` 后，空列表令 824 行的 `any(...)` 为 false，829 行执行 E4 进入 `MERGING`。同一缺陷也存在于 716-758 行对已存在文件的快捷读取路径，`all([])` 为 true。
- **影响**：任何无关、过期或空的 FINAL 文件均可越过有 issue 的 HOLD，违背 F-11 的“引用、完整性和状态守卫”边界，也使 `vote_result_ref`/`issues_index_sha256` 失去审计意义。
- **修正与验收**：在写入或提升 disposition 前加载当前轮不可变 vote result，逐项校验 task/ref/round/executor、vote-result 路径和 SHA、issues hash，以及 dispositions 的 issue_id 集合与 `issues_index` 的严格相等；同时拒绝非 `APPROVED` 的 E4/E5a disposition。空、漏项、未知项、错 task/ref/round/hash、错 executor、旧轮次和 DEADLOCK/REWORK 的 FINAL disposition 都必须保持 `CONSENSUS_CHECK` 且不写/不覆盖 canonical 文件。

### P1-3：超时终局产物没有保存规定的 deadline/最后 ping，且走了另一套缺失上下文的计票调用

- **证据**：D-3 明定超时合成弃权必须记录 `source: timeout`、deadline 和最后一次 ping（`docs/PRD_CHANGE_PROPOSAL_v2.5.md:109-114`）；UC-9 也要求以持久化 deadline 为单一事实源并审计超时（`docs/usercases/UC9-timeout-daemon.md:25-31`）。但 `src/macao/consensus/vote.py:136-148` 合成的 timeout vote 只写入 source/confidence/weight，未写 `deadline`、`last_ping_at`；Schema 将两字段设为可选（`docs/schemas/vote_result.schema.json:42-53`）。`orchestrator.py:589-594` 的审计 detail 也只有 reviewer/ref/round。
- **进一步证据**：超时/DEADLOCK 分支在 `src/macao/workflow/orchestrator.py:607-615` 调用生成器时又没有传入 `task_id`、`reviewer_weights` 和 `policy`，与正常分支 684-697 行不同。因此终局 vote result 会回退为 `task-<checkpoint-prefix>`、默认/票面权重和默认策略快照，不能作为当前任务的可重放证据。
- **影响**：审计无法证明弃权是在哪个 deadline、哪次 re-ping 后生成；对于非等权团队，超时终局的权重快照和决策也可能错误。
- **修正与验收**：将持久化的 per-reviewer deadline 和 last-ping 时间传给 timeout 票并设为 timeout source 的必填条件；以与正常路径相同的冻结 task、reviewer weights 和 policy 调用唯一计票函数。增加非等权的 1-timeout、全-timeout、重启重扫与迟到票隔离测试，断言 task_id、policy snapshot、deadline、last_ping_at、responded/accounted、审计事件和终局 vote result 完整一致。

### P1-4：所谓“不可变、物理只读”的 vote result 仍可被同轮重算覆盖

- **证据**：PRD 将 `vote_result.json` 定义为计票完成即落盘且“物理只读”（`docs/MACAO_PRD_v2.md:17-20,329-340`）。然而 `src/macao/consensus/vote.py:282-286` 每次都以 `open(..., "w")` 重写 `.macao/vote_result.json`，没有存在性检查、round/sha 冲突拒绝或 evidence-ref seal。`CONSENSUS_CHECK` 中重试 `collect_and_evaluate_consensus()` 即可重建带新 timestamp 的同一逻辑终局。
- **影响**：同一轮的原始票面、issues hash 和决策时间可被后续调用覆盖，不能满足 D-1 的不可变审计链。
- **修正与验收**：将 canonical vote result 写入按 task/ref/round 隔离的 evidence/artifact 路径，采用原子 create-if-absent 与 hash 比对；若已存在则只读取并复用，内容不一致 fail-closed。加入同轮重复调用、崩溃恢复及迟到票后的字节级不变性测试。

## P2/P3：可延期但需登记

无新增 P2/P3。本轮 P1 完成前，不应以文案同步替代这些实现闭环。

## 交叉文档需做的文字修订

1. 两份申请中“彻底打通”“严密驻留”“全面对齐”“全部阻断项完成”的完成式措辞，应改为“目标实现中/待 P1 验收”，直至上述运行时反例被覆盖。
2. `docs/usercases/UC6-issue-triage-rework.md:106-108` 已把“100% 覆盖率校验”列为实现落点；在实现前不得在申请或 README 中称其已经落地。
3. `docs/schemas/vote_result.schema.json` 应表达 timeout 来源的条件必填字段，或权威文档明确将 deadline/ping 只放 SQLite 审计并使两者字段与查询接口可重放；当前“必须记录”与可选 Schema 相冲突。

## 建议的闭环顺序与验收标准

1. 先统一编排器与生成器的加权输入和唯一 decision 来源，覆盖 P1-1 的状态/产物一致性反例。
2. 实现 disposition 的当前轮反向锚定和精确集合校验，先完成 P1-2 的所有拒绝用例，再允许 E4/E5a。
3. 固化 timeout 的 deadline/ping 与冻结策略快照，完成 P1-3 的重启、迟到和非等权场景。
4. 最后把 vote result 改为 round 级不可变写入，做重复调用和恢复测试；通过后重新申请 L2/场景级复审，而非只以 L1 文档定级覆盖代码承诺。

## Reviewer 自审记录

- 按方法论 §9 检查了字段读取路径、完成式声明、确定性用语和 JSON/YAML Schema。重点补查了前一轮已修复的加权反例是否真正进入 FSM，而非只验证 `ConsensusEngine` 单元函数。
- 本报告未采用其他 reviewer 的结论作为证据；所有 P1 均由目标提交的源码、权威文档和上述可复现输入独立得出。
