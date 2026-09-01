# MACAO PRD v2.5 Design Sync 闭环复审结论

- **评审日期**：2026-09-01
- **Reviewer**：Codex
- **被评审提交**：`2766c69`（`docs: close all 5 expert reviews on 0bc6247, align PRD v2.5 schemas and FSM guards`）
- **评审申请**：`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`
- **评审范围**：申请列出的 PRD、变更提案、代码变更清单、SRS、FAQ、PRODUCT-FACTS、UC-1/5/6/7/8/9、STATUS，以及声明为唯一机器契约的 `docs/schemas/` 与 fixtures
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§8–§11；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **复审基线**：上一轮 Codex 结论 `docs/reviews/2026-09-01-review-result-0bc6247-codex.md`
- **证据边界**：本轮申请目标是 L1 / PG-0；代码变更清单中明确标为后续实施的内容不作为 L2/L3 完成证据

## 结论

**不授予 L1 DOC-ALIGNED，不开放 PG-0。**

提交 `2766c69` 已真实修复上一轮多项正文级阻断：E3 改为全席位 accounted 后触发；DEADLOCK 即时写入不可变 `vote_result.json`；人工裁决改写独立 `admin_override.json`；PRD 补入 disposition、AEP Type E、§14.3～§14.5 和第十五部分；merge 的 `ff_only` / `no_ff` OID 守卫也已分开描述。这些不是表面改字，方向和主流程均明显收敛。

但申请在 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md:28,37,57-64` 宣称“全部阻断项 100% 物理闭环”“机器契约严苛测试 100% PASS”，与实测不符。当前 Schema 仍接受旧的人工终局 `vote_result`、五块且带 base64 的 `review_context`、超出预算的任意 AEP payload、违反处置生命周期的 FINAL disposition，以及违反独裁帽的配置；仓库自己的一个 valid fixture 反而不能通过 Schema。权威 PRD 的核心计票公式还被控制字符损坏，提案、PRD 和 disposition Schema 仍是三套结构/写者规则，UC-9 对超时 ABSTAIN 是否计入法定人数也与 PRD 冲突。

这些问题会使两个自称遵循 v2.5 的实现接受不同输入、生成不同产物或走向不同状态，因此 DOC/SPEC 不能判为 VERIFIED。

| 证据域 | 状态 | 结论 |
|---|---|---|
| DOC | `CONTRADICTED` | PRD、提案、Schema README、fixtures 与 UC-9 仍有现行行为冲突 |
| SPEC | `CONTRADICTED` | 关键反例被机器契约接受，无法得到唯一的 fail-closed 行为 |
| fenced YAML/JSON 语法 | `VERIFIED` | 抽取的 25 个 YAML/JSON fenced blocks 均可解析 |
| 本地 Markdown 链接 | `VERIFIED` | 抽查范围内 27 个相对链接均能解析到现有目标 |
| Schema 自身语法 | `VERIFIED` | `docs/schemas/` 与 `src/macao/schemas/` 的 Draft-07 Schema 均可加载，且对应文件字节一致 |
| 现有 TEST | `PARTIALLY_VERIFIED` | `PYTHONPATH=src python3 -m unittest discover tests -q` 为 84/84 PASS，但未覆盖本轮新增机器契约的负例 |
| CODE / OPS | `NOT_APPLICABLE` | 本轮不申请 L2/L4，清单所列 v2.5 代码仍是待实施项 |

## 已对齐 / 已确认项

1. PRD §3.2 Layer 1b 已统一为 `accounted == configured`，不再以“先达到 quorum”提前进入计票。
2. PRD §3.2、§3.4 与 UC-7 的主路径已统一为：DEADLOCK 即时落盘，管理员只新增 `admin_override.json`，不得回写机器决定。
3. PRD 已补入 `executor.disposition.yml`、AEP Type E `DISPOSITION_REQUIRED`、§14.3～§14.5 和第十五部分。
4. PRD §14.5 与代码清单已分别定义 `ff_only` 和 `no_ff` 的 remote OID 关系，上一轮 merge guard 矛盾已关闭。
5. `review_manifest.schema.json` 已加入三值 vote 和 BLOCKING / YES_APPROVE / ABSTAIN 的局部条件互锁。
6. PRD §2.1、§2.2、§2.3、§2.5、§5.2 的正向示例均能通过当前对应 Schema；但这只证明 happy path，不证明 Schema 会拒绝不合法输入。

## P0：必须先解决

无。本轮未发现不可逆数据损坏或立即安全事故。

## P1：进入 v2.5 实施前必须修正

### P1-1：权威 PRD 的纯整数计票公式被控制字符破坏

**证据**：

- `docs/MACAO_PRD_v2.md:332-335` 中 `\forall`、`\times`、`\rceil` 被实际的 Form Feed、Tab、Carriage Return 字节替代；显示结果成为 `$\f orall ... 3<TAB>imes ...` 和断裂的 `ceil`；
- `docs/PRD_CHANGE_PROPOSAL_v2.5.md:404-410` 与 `docs/v2.5_CODE_CHANGE_INVENTORY.md:74-75` 保留了正确公式，证明这不是有意改写；
- 字节扫描在 PRD 中发现 1 个 `0x0c` 与 2 个 `0x0d`，`git diff --check 0bc6247 2766c69` 同时报告该段空白异常。

**影响**：该段是 `weighted_2/3_v1` 的权威确定性定义，损坏后的数学表达式不可复制实现，也无法满足 L1 的“同一行为可唯一推导”。

**修复要求**：恢复正常的 `\forall`、`\times`、`\rceil` 文本，并增加禁止 Markdown 出现非换行 C0 控制字符的文档检查。

### P1-2：`vote_result` 机器契约仍允许 D-1 已废止的人工终局结果

**证据**：

- PRD `docs/MACAO_PRD_v2.md:695-699` 把机器 `decision` 限定为 `APPROVED | REWORK_REQUIRED | DEADLOCK`；代码清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md:61` 同样要求彻底移除旧决定；
- `docs/schemas/vote_result.schema.json:106-107` 仍允许 `RETRY_REVIEW`、`CANCELLED` 与 `resolution: human_override`；`policy_snapshot`、`reviewers_accounted`、`issues_index_sha256`、`requires_disposition` 等 v2.5 审计字段也不是 required；
- 实测最小对象 `{decision: RETRY_REVIEW, resolution: human_override}` 被 Draft-07 validator 接受；
- `docs/schemas/fixtures/valid/vote_result_human_override.json` 仍把人工覆盖后的 APPROVED 当成合法 `vote_result` 正例，并使用旧版 `2/3 majority` 字段。

**影响**：实现按 Schema 可以重建上一轮已明确废止的“人工改写终局 vote_result”路径，破坏不可变机器事实与人工决定分离。

**修复要求**：Schema 的 decision 收敛为三值；删除 `human_override` resolution；将 v2.5 决策所需审计字段设为 required 并添加跨字段约束；旧 fixture 移入 migration/invalid 集并明确失败原因。

### P1-3：`review_context` 与 AEP/1.1 对“9 个必需块、禁止内联、16 KiB”均 fail-open

**证据**：

- PRD `docs/MACAO_PRD_v2.md:15,948-952` 要求完整内容只通过引用传递，并把两个传输块加七个语义块定义为 9 个必需块；
- `docs/schemas/review_context.schema.json:6` 只要求 5 个块，且 `:17` 继续允许 `dev_checkpoint.content_base64`；实测仅提供这 5 块并内联 50 KiB base64 的对象仍通过；
- `docs/schemas/aep_envelope.schema.json:8,30` 同时接受 AEP/1.0 / 1.1，payload 仅约束为任意 object，没有消息类型对应 payload Schema，也没有 serialized-byte / inline-text 校验；实测 50 KiB `DISPOSITION_REQUIRED` 消息通过；
- 申请 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md:59` 与清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md:64` 却把 16 KiB / 2048 byte 称为硬约束；
- 正例 `docs/schemas/fixtures/valid/aep_review_request.json` 仍是 AEP/1.0，并携带 `content_base64`。

**影响**：发送端可按 Schema 产生 agmsg 无法承载、且违反“零语义创作/引用传输”的消息；接收端也无法按 type fail-closed 校验 payload。

**修复要求**：让 review_context Schema 要求权威模型列出的全部必需块并禁止 base64；为 8 类 AEP 建立按 `type` 选择的 payload 条件 Schema；明确字节预算属于 envelope Schema 之外的序列化后 validator，并在清单中给出其唯一实现位置和边界负例。

### P1-4：disposition 在提案、PRD 与 Schema 中仍不是同一个契约

**证据**：

- 提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:149-189` 使用 `artifact_revision`、`executor_id`、`status`、冻结 vote-result 引用、`issues_index_sha256`、`items[].decision/reason_ref`，并规定 PENDING_ADMIN 通过更高 revision 产生 FINAL；
- PRD `docs/MACAO_PRD_v2.md:660-681` 和 `docs/schemas/review_disposition.schema.json:6-55` 改为 `executor`、`disposition_status`、`dispositions[].disposition_type/rationale`，却丢失 revision、冻结 vote-result 引用和 issues-index 哈希；
- 提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:133-135,211` 一处要求 Executor 在 override 后生成 FINAL，另一处允许 Admin 签署替代 FINAL 或由 Executor/Admin 生成，与 PRD §16.1 的 Executor 单一写者冲突；
- Schema 没有条件守卫。实测 `FINAL + NEEDS_ADMIN` 被接受；`FINAL + EXEMPTED_BY_ADMIN + requires_new_checkpoint=true + 无 override_id` 也被接受。

**影响**：管理员接管后无法唯一确定谁写下一版、是否允许原地修改、E4 应验证哪些冻结关联；非法 FINAL 可以直接越过 HOLD / E4 守卫。

**修复要求**：从提案和 PRD 中选择一套 canonical 字段及 revision 模型；坚持 Admin 只写 override、Executor 只写 disposition，或正式修改单一写者裁定；补齐 NEEDS_ADMIN、EXEMPTED_BY_ADMIN、DEFERRED/REJECTED 的条件 Schema，以及跨产物精确覆盖/哈希关联的 fail-closed validator 和负例。

### P1-5：v2.5 配置 Schema 没有封闭加权策略与独裁帽

**证据**：

- PRD `docs/MACAO_PRD_v2.md:329-340,1355-1365` 只定义 `weighted_2/3_v1`，并要求启动时执行独裁帽；
- `docs/schemas/macao_config.schema.json:2-4,55-67` 标为 v2.5，却仍接受 `2/3_majority`，且 `policy`、`vote_weight`、`dictator_cap_enabled` 均非 required；
- 实测两 reviewer 权重 2:1、`dictator_cap_enabled: true` 的配置通过 Schema，尽管 `3*2 < 2*3` 为假，应拒绝启动；
- PRD、Schema README 与清单没有清楚区分“结构 Schema”与“必须由运行时完成的跨项语义校验”。

**影响**：同一 v2.5 配置可能在不同实现中按等权旧算法运行，或者允许单席达到 2/3，总体行为不唯一。

**修复要求**：若保留旧规则，必须定义明确的版本迁移/兼容模式；否则从 v2.5 Schema 移除。把 policy 和关键权重字段设为 required，并在 `config.py` 计划中给出独裁帽、quorum 派生值一致性及最少胜方席位边界的语义 validator 负例。

### P1-6：Schema README、dev contract 与 fixtures 仍停留在 v2.3，不能作为“唯一权威来源”

**证据**：

- `docs/schemas/README.md:3,11,17-20` 仍称当前对应 PRD v2.3、AEP 共 7 类、Reviewer 不得 ABSTAIN、vote_result 可由 human_override 产生 RETRY_REVIEW/CANCELLED、review_context 只有旧块集合；
- `docs/schemas/dev_manifest.schema.json:3,6` 的 `$id` 仍为 v2.3，required 中没有清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md:59` 承诺的 `task_id`、`checkpoint_ref`、`full_document`；
- 对 `docs/schemas/fixtures/valid/` 全量回放时，`review.yml` 因缺少现在必需的 `items` 被拒绝；其余旧式 context、AEP/1.0 和 human-override vote_result 仍被接受。

**影响**：README 所称“唯一权威来源”内部自相矛盾，正例集不能作为 conformance suite；申请的 4/4 happy path 不能支持“机器契约 100% PASS”。

**修复要求**：同步 README 和 dev Schema；重建 v2.5 正反 fixtures；CI 必须遍历全部 valid/invalid fixture，并断言每个反例因预期 keyword/path 被拒绝，防止“因另一个偶然错误而通过负测”。

### P1-7：UC-9 把超时 ABSTAIN 同时排除和计入法定人数

**证据**：

- PRD `docs/MACAO_PRD_v2.md:331-335` 定义 $E_N$ / $E_W$ 为非弃权有效席位/权重，席位与权重法定人数均使用该集合；
- `docs/usercases/UC9-timeout-daemon.md:31-35` 先把超时席位记为 ABSTAIN，随后称其“不进加权分母、计入法定人数判定”；
- 同一用例 `:46` 又称迟到合法票可覆盖已经持久化的弃权标记，与“先到先得”和不可变终局票据的边界未定义。

**影响**：1 APPROVE + 1 timeout 的两席场景可能被一种实现判为满足席位 quorum，另一种实现判为 DEADLOCK；重扫/迟到票还可能改变已经计票的结果。

**修复要求**：统一三个集合：timeout ABSTAIN 计入 `accounted` 以允许 E3，绝不计入非弃权 $E_N/E_W$；明确只有在 `vote_result` 尚未生成前，合法票才可替换 pending timeout 标记，终局产物生成后不得覆盖。

## P2 / P3：可在 P1 收敛后登记处理

### P2-1：本轮申请和 STATUS 未冻结实际复审提交

申请 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md:6` 仍写可移动的 `origin/main`；STATUS `docs/reviews/STATUS.md:67` 只登记初版 `0bc6247`，却称“当前提交”已闭环，没有为本次 `2766c69` 新增独立行。评审可由 Git 历史锁定目标，但未来无法仅凭申请和状态表复现。

### P3-1：`git diff --check` 未通过

`git diff --check 0bc6247 2766c69` 报告 PRD 头部/公式附近及既有评审报告中的 trailing whitespace。除 P1-1 的控制字符外，其余属于机械清洁问题，可在同次文档修复中清除。

## 交叉文档需做的文字与契约修订

1. 生成“PRD 产物字段 → Schema required/conditional → semantic validator → valid fixture → invalid fixture”的可执行追踪表，避免把“Schema 可加载”误报为“契约严格”。
2. 明确三种约束边界：JSON Schema 负责局部结构；运行时 validator 负责字节预算、权重求和、跨产物精确覆盖；FSM guard 负责状态与不可变生命周期。
3. 对 vote_result、review_context、AEP、disposition、admin_override、macao_config 和 dev manifest 各保留一个当前版本；旧版仅能存在于明确命名的 migration fixture 中。
4. 在 PRD 唯一术语表中固定 `responded`、`accounted`、`effective/non-abstain`，UC 只引用，不另写口径。
5. 清除提案中“Admin 可替代 Executor 写 FINAL disposition”的分支，或正式修改 D-2 并同步 PRD、FAQ、UC、Schema 和写者权限表。

## 建议的闭环顺序与验收标准

1. 先修复 PRD 控制字符、vote-result 三值决定和 ABSTAIN 集合定义。
2. 裁定 disposition 的唯一字段模型、revision 规则及 override 后写者。
3. 收紧 7 类 v2.5 Schema，并补充无法由 Draft-07 表达的唯一语义 validator 规范。
4. 重建 fixtures 和 conformance tests；至少加入本报告 6 个已被错误接受的负例。
5. 同步 README、提案、UC-9、代码清单、申请 SHA 与 STATUS 后重新申请 L1。

重新申请的最低验收条件：

- PRD 不含非换行 C0 控制字符，所有公式可复制解析；
- `RETRY_REVIEW/CANCELLED + human_override` 不再是合法 vote_result；
- 5-block/base64 context 与超预算 AEP 必须 fail-closed；
- `FINAL + NEEDS_ADMIN`、无 override 的 EXEMPTED、非法 `requires_new_checkpoint` 组合必须 fail-closed；
- 违反独裁帽或缺关键 v2.5 policy 的配置必须 fail-closed；
- `fixtures/valid` 全部通过、`fixtures/invalid` 全部按预期原因失败；
- 2-reviewer `1 APPROVE + 1 timeout ABSTAIN` 在 PRD、UC、fixture 与推演中唯一得到 DEADLOCK。

## Reviewer 自审记录

- 已锁定实际评审 SHA `2766c69`，没有把可移动的 `origin/main` 当作证据标识。
- 已逐项复核上一轮 Codex P1，而非采信申请中的“100% 闭环”自述。
- 已解析范围内 YAML/JSON fenced blocks，并将“能解析”“通过 Schema”“能拒绝反例”分开验证。
- 已用 Draft-07 validator 独立构造并重放 vote_result、review_context、AEP、disposition、config 负例。
- 已回放 `docs/schemas/fixtures/valid/`，确认存在一项 unexpected failure 和多项旧语义 unexpected pass。
- 已运行 84 项现有测试；未把与本轮新 Schema 负例无关的绿灯外推为 L1 对齐证据。
- 每项 P1 均给出文件路径、行号、冲突双方、可复现输入类别与明确修复要求。
- 未采用其他 reviewer 的票作为本结论依据。

## 最终判定

**REJECT L1 / REJECT PG-0 for commit `2766c69`.**

建议保留本次已完成的正文收敛成果，但将 v2.5 继续视为待闭环设计基线。清零上述 P1、以固定 SHA 重新提交后再做 L1 复审；本结论不评价清单中尚待实施的 v2.5 代码是否达到 L2/L3。
