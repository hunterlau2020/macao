# MACAO PRD v2.5 Design Sync 独立评审结论

- **评审日期**：2026-09-01
- **Reviewer**：Codex
- **被评审提交**：`0bc6247`（`docs: sync PRD v2.5 design, add code change inventory, and submit review request`）
- **评审申请**：`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`
- **评审范围**：申请列出的 PRD、变更提案、代码变更清单、SRS、FAQ、PRODUCT-FACTS、UC-1、UC-5、UC-6、STATUS，以及这些文档声明为机器权威契约的 `docs/schemas/`
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§8–§11；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **证据边界**：本轮是文档与规格同步评审；代码清单属于待实施计划，不作为 L2 CODE 或 L3 TEST 证据

## 结论

**不授予 L1 DOC-ALIGNED，不开放 PG-0。**

核心架构方向可以继续保留：独立 `review_disposition`、不可变机器计票结果、全席位 accounted 后计票、纯整数加权共识、Evidence Ref 隔离、`role_view` 投影均有合理设计基础；加权公式对本轮抽查的 2 席、3 席及 2:1:1 权重反例也能确定性得出结果。

但提交 `0bc6247` 尚未达到申请所称的“全量完成同步修改”。权威 PRD 内仍同时保留 DEADLOCK 不落盘/人工改写 `vote_result` 的旧方案，PRD 示例与仓库 Schema 实测不兼容，`review_context` 有两套互斥字段路径，E7 豁免与 disposition 单一写者无法按同一契约实现，E3 与超时规则仍有旧触发口径，AEP/1.1 第八类消息没有形成协议闭环，合并策略还引用不存在的章节并与 `no_ff` 配置冲突。这些差异会让两个合规实现产生不同状态机、产物和 Git 行为，属于 L1 阻断项。

| 证据域 | 状态 | 结论 |
|---|---|---|
| DOC | `CONTRADICTED` | PRD、提案、FAQ、UC、Schema 和场景推演存在行为级冲突 |
| SPEC | `CONTRADICTED` | DEADLOCK、E3、E7、AEP、review_context、merge guard 不能唯一推出同一行为 |
| fenced YAML/JSON 语法 | `VERIFIED` | 本轮范围内标记为 YAML/JSON 的 Markdown 代码块均可被解析 |
| 本地 Markdown 链接目标 | `VERIFIED` | 本轮范围内相对文件链接未发现缺失目标 |
| CODE / TEST / OPS | `NOT_APPLICABLE` | 本轮申请仅要求 L1；代码变更清单明确仍待实施 |

## 已对齐 / 已确认项

1. `PRODUCT-FACTS.md` 保持陈述句形式，并明确事实锚点不等于现行实现已经满足，边界清楚。
2. PRD §2.3、FAQ Q15 与 UC-5 的加权规则主体一致：配置期独裁帽、席位法定人数、权重法定人数、胜方权重阈值、胜方最少两席均采用整数比较。
3. 以下抽查可由该公式唯一推出：
   - 2 席 1:1，全同意 ⇒ `APPROVED`；1:1 分裂 ⇒ `DEADLOCK`；1 赞成 + 1 超时弃权 ⇒ 未达席位/权重法定人数，`DEADLOCK`；
   - 3 席等权，2 赞成 + 1 反对 ⇒ `APPROVED`；1:1:1（赞成/反对/弃权）⇒ `DEADLOCK`；
   - 3 席权重 2:1:1，权重 2 与权重 1 的两席赞成、另一席反对 ⇒ `APPROVED`；仅权重 2 的单席赞成 ⇒ 被最少两席门禁拒绝自动裁决。
4. PRD §3.3 与 UC-5 的新主路径已经写出“所有配置席位 accounted 后 E3”和“DEADLOCK 即时落盘”的正确目标方案。
5. PRD §14.2、UC-1 与代码清单均包含 `SHOULD_DISPOSE` / `NOTIFY_EXECUTOR_DISPOSE` 的核心投影。
6. Evidence Ref 的 canonical / inbox / staging 三层命名及 post-push 失败不做本地假回滚的原则，方向一致。

## P0：必须先解决

无。本轮发现均可通过规格收敛修复，不涉及不可逆数据损坏或立即安全事故。

## P1：进入 v2.5 实施前必须修正

### P1-1：DEADLOCK 的不可变产物规则在同一权威 PRD 内自相矛盾

**证据**：

- `docs/MACAO_PRD_v2.md:355-366` 规定所有未满足门禁的情况产生 `decision = DEADLOCK`，即时落盘后 HOLD；
- `docs/MACAO_PRD_v2.md:789` 和 `docs/usercases/UC5-consensus-tally.md:43-54` 重申 DEADLOCK 即时写入不可变 `vote_result.json`；
- 但 `docs/MACAO_PRD_v2.md:855-863` 的权威场景推演仍规定 DEADLOCK **不写** `vote_result.json`，随后由人工裁定写入 APPROVED / REWORK_REQUIRED / RETRY_REVIEW / CANCELLED 的“终局 vote_result”。

**影响**：D-1 的单一写入时点和不可变性无法实现；实现者无法判断 DEADLOCK 是否已有审计产物，也无法判断人工 override 应写独立 `admin_override.json` 还是改写机器结果。

**修复要求**：删除场景推演中的旧方案。步骤 5 必须先写 `decision: DEADLOCK`；步骤 6 只新增 `admin_override.json` 与审计事件，任何选择均不得创建第二份或改写原 `vote_result.json`。

### P1-2：仓库中的机器 Schema 尚未迁移，申请所称“100% 命名与语义对齐”不成立

**证据**：

- 申请 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md:61-67` 声明 Schema 及状态机已闭环；
- `docs/schemas/vote_result.schema.json:3-6,28-52` 仍是 v2.3 契约：没有 `policy_snapshot`、`issues_index`、`reviewers_accounted` 和 `DEADLOCK`，却仍允许人工终局 `RETRY_REVIEW` / `CANCELLED`；
- `docs/schemas/macao_config.schema.json:54-60` 仍把 `consensus_rule` 固定为 `2/3_majority`，没有 `vote_weight`、独裁帽或 disposition timeout；
- `docs/schemas/aep_envelope.schema.json:3-20` 仍是 AEP/1.0 七类消息；
- `docs/schemas/review_disposition.schema.json`、`docs/schemas/admin_override.schema.json` 和代码清单所写的 `docs/schemas/aep_message.schema.json` 均不存在；
- `docs/schemas/review_manifest.schema.json:22-59` 没有 v2.5 的 `items`、`full_document`、`abstain_reason` 与 BLOCKING/vote 条件互锁，因此会把不满足新语义的产物判为合法。

**可复现结果**：使用 Draft-07 validator 将 PRD §2.3 的 `vote_result` 示例直接送入当前 Schema，得到 10 个错误（包括每个 `input_artifacts` 缺 `kind/message_id`、旧 `vote_breakdown` 必填项缺失、`AUTO_WEIGHTED_CONSENSUS` 不在旧枚举）；PRD §5.2 的 `review_context` 示例得到 7 个错误。

**影响**：若按 PRD 编码，唯一校验依据会拒绝 PRD 自己的产物；若按现行 Schema 编码，则不会实现 v2.5。

**修复要求**：L1 定级前先落地全部 v2.5 Schema 与正反 fixtures，并把 PRD、UC 和代码清单中的每个规范示例作为 fixture 直接校验。Schema 可以仍标注“待代码实现”，但不能与实施基线同时存在两套互斥机器契约。

### P1-3：`review_context` 的“唯一权威结构”实际存在两套互斥路径

**证据**：

- `docs/MACAO_PRD_v2.md:513-517` 声明 `code_changes.refs.{base_commit, head_commit}` 是唯一权威路径，并要求示例与 §5.2 完全一致；
- `docs/MACAO_PRD_v2.md:937-1005` 的 §5.2 却使用 `code_changes.base_commit` / `head_commit` 平铺路径，`dev_checkpoint` 也从 `path/content_base64` 改为 commit/round 结构；
- §5.2 声称“9 大必需块”，但 `required_blocks` 列表没有 `evidence`，而示例又额外提供 `evidence`；
- 当前 `docs/schemas/review_context.schema.json:6-104` 只要求 5 个块，并要求旧形态 `dev_checkpoint.path`、`code_changes.refs`、对象型 `history/references`，与 §5.2 示例不兼容。

**影响**：Reviewer 取 diff、取申请全文和取 evidence 的字段路径不确定，直接触发评审上下文丢失或消息拒收。

**修复要求**：只保留一套 canonical JSON model；统一 §2.4、§5.2、消费命令、Schema 与 fixtures，明确 9 个块究竟哪些 required、哪些 optional，以及 `evidence` 是否属于必需块。

### P1-4：AEP/1.1 宣称八类消息，但正文与 Schema 只有七类，新增 disposition 通道不可实现

**证据**：

- `docs/MACAO_PRD_v2.md:370-388` 声称 AEP/1.1 有 8 类并新增 `DISPOSITION_REQUIRED`；
- `docs/MACAO_PRD_v2.md:390-397` 随即称“全部 7 类消息”，实际 `docs/MACAO_PRD_v2.md:399-646` 只给 Type A～G，没有 `DISPOSITION_REQUIRED`，且每个信封仍写 `protocol: AEP/1.0`；
- `docs/MACAO_PRD_v2.md:1248,1269` 的架构与技术选型仍把运行协议定义为 AEP/1.0；
- 当前 AEP Schema 也只接受 AEP/1.0 的 7 类消息。

**影响**：E5/E5a、处置等待与 `SHOULD_DISPOSE` 没有可校验的控制边；16 KiB/2048 字节限制也没有机器契约。

**修复要求**：确定协议版本迁移策略（严格切换或明确兼容窗口），补齐第八类消息的完整信封/payload Schema、大小校验和正反例，并清除“7 类/8 类、1.0/1.1”的混用。

### P1-5：E7 豁免与 disposition 的写者、字段和状态生命周期没有收敛

**证据**：

- 提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:149-189` 使用 `artifact_revision`、`status`、`items[].decision/reason_ref/override_id`，允许 `PENDING_ADMIN → 更高 revision FINAL`；
- UC-6 `docs/usercases/UC6-issue-triage-rework.md:26-55` 和代码清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md:64` 改用 `disposition_status`、`dispositions[].disposition_type/rationale/full_document`，没有 `artifact_revision`、顶层状态迁移或逐项 `override_id`；
- 提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:133-135` 一处要求 Executor 在 override 后再产出 FINAL，另一处又允许 Admin 签署替代 FINAL disposition；后者与 D-2/FAQ Q15 的 Executor 单一写者边界冲突；
- PRD E7 `docs/MACAO_PRD_v2.md:797` 直接写“APPROVED → E4”，但没有定义在 FINAL disposition 尚未形成时先等待哪一个产物，也没有给 `EXEMPTED_BY_ADMIN + override_id` 的可校验 Schema；
- 申请 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md:48,51-52` 声称这些项已经在 PRD §6.1 与 Schema 中闭环，实际 PRD §6.1 没有 disposition timeout 或 NEEDS_ADMIN 的协议条目，`macao.yaml` 的 `timeouts` 也缺 `review_disposition`。

**影响**：管理员批准后可能直接绕过 FINAL disposition，也可能等待一个无法按统一 Schema 生成的产物；不可变产物与 revision 更新规则相互冲突。

**修复要求**：选择并固化一种生命周期。至少明确：谁能写 DRAFT/PENDING_ADMIN/FINAL；Admin 是否只能写 override；override 后由谁生成新 revision；每个 EXEMPTED 项如何绑定 `override_id`；E7 APPROVED 到 E4 之间的精确守卫；timeout deadline/ping/EXTEND 的持久化字段。

### P1-6：E3 “全席位 accounted”仍与法定人数提前触发的旧口径并存

**证据**：

- 正确的新守卫见 `docs/MACAO_PRD_v2.md:789-790` 与 `docs/usercases/UC5-consensus-tally.md:73-75`：所有席位收到合法 manifest 或被 timeout 计入 accounted 后才进入 `CONSENSUS_CHECK`；
- 但 `docs/MACAO_PRD_v2.md:1543` 仍把 E3 完成标志写成“有效票 ≥ 法定人数”；
- `docs/usercases/UC5-consensus-tally.md:15-17` 的前置条件也写“当前 ref/round 有效票 ≥ minimum_quorum（含超时 ABSTAIN）”，把“收到/超时已 accounted”和“非弃权有效票法定人数”混成一个概念；
- `docs/MACAO_PRD_v2.md:1078-1082` 又要求 Reviewer 超时后询问用户是否标记弃权，与 §3.3 自动持久化 timeout accounted 的规则冲突。

**影响**：实现可能在法定人数一到就提前计票，遗漏迟到席位；也可能在 timeout 后等待人工确认，导致任务永久停留 `WAITING_REVIEW`。

**修复要求**：全体系区分 `responded`、`accounted`、`effective/non-abstain` 三个集合。E3 只看 `accounted == configured seats`；法定人数只在随后计票时检查；timeout 到期由确定性 scanner 生成 timeout 票据，不再询问是否记弃权。

### P1-7：状态与合并规范引用缺失，且 E4a 守卫与允许的 `no_ff` 策略互斥

**证据**：

- PRD `docs/MACAO_PRD_v2.md:791-792,1433,1469,1483` 多次把合并行为指向 §14.5，但本文只有 §14.1 和 §14.2；UC-6 `docs/usercases/UC6-issue-triage-rework.md:5` 引用的 §15.2 也不存在；
- PRD `docs/MACAO_PRD_v2.md:792` 和代码清单 `docs/v2.5_CODE_CHANGE_INVENTORY.md:96` 要求“最终 push 对象哈希精确等于 `vote_result.checkpoint_ref`”；
- 同一 PRD `docs/MACAO_PRD_v2.md:1430` 却允许 `merge.strategy: ff_only | no_ff`。`no_ff` 会产生新的 merge commit，目标分支 tip 按定义不可能等于被评审 source checkpoint；
- `docs/MACAO_PRD_v2.md:803` 声明只有 10 个业务状态且没有 HOLD，但 `docs/MACAO_PRD_v2.md:1480` 又规定 `macao pause`“进入 HOLD”，同时 DDL 没有独立 paused/hold 字段。

**影响**：实现无法从权威文档确定 merge target OID 校验对象、`no_ff` 是否合法、push/CI/signoff 的严格次序，也无法确定 HOLD 是状态、标志还是纯描述。申请关于“10 状态单一事实源、不存在歧义转移”的声明因此不可验证。

**修复要求**：补回或重写权威 Merge Policy；对 `ff_only` 与 `no_ff` 分别定义 source checkpoint、生成 merge commit、目标 remote tip 的校验关系；将 HOLD 明确定义为持久化标志/子状态并给出 DDL，或禁止使用“进入 HOLD”作为状态转移措辞。

## P2 / P3：可在 P1 收敛后登记处理

### P2-1：PRD 声明为 v2.5 摘要的文档仍停留在 v2.3

`docs/MACAO_PRD_v2.md:7-15` 把 `EXECUTIVE_SUMMARY.md` 和 `IMPROVEMENT_SUMMARY.md` 列为 v2.5 摘要/演进说明；但两文件标题或头部仍明确写 v2.3，并保留旧计票与旧产物描述。要么纳入本次迁移，要么在 PRD 文档体系表中标记为历史资料，避免读者把它们当作 v2.5 快速参考。

### P2-2：评审申请与 STATUS 没有冻结被评审 commit

申请 `docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md:6` 使用可移动的 `origin/main`，`docs/reviews/STATUS.md:67` 使用 `HEAD`。本轮 reviewer 可从提交历史锁定为 `0bc6247`，但后续审计无法仅凭申请复现。按 GUIDELINES §1.3/§3.3，应把待审对象固定为短 SHA。

### P3-1：文档结构与清单有机械性残留

- PRD §5 的顺序为 §5.2 → §5.4 → §5.3；第十四部分后直接进入第十六部分；附录插在第十六部分内部；
- `docs/usercases/UC5-consensus-tally.md:95-100` 重复列出 `config.py` 与 `tests/` 两行；
- PRD §4.1 仍称 Multi-Reviewer Consensus 高级算法“不做”，与 v2.5 已把加权共识列为实施基线的表述不一致。

这些不一定单独改变运行结果，但会显著增加后续迁移遗漏概率。

## 交叉文档需做的文字与契约修订

1. 以提案 D-1～D-9 生成一张“裁定 → PRD 权威段 → Schema → UC → fixture → 代码清单”的逐字段追踪表；所有旧段落必须删除或显式标为历史反例。
2. 为 `.dev.yml`、`.review.yml`、`vote_result.json`、`review_disposition.yml`、`admin_override.json`、AEP envelope/payload、`review_context`、`macao.yaml` 各建立唯一版本号和唯一 Schema 路径。
3. 将 `reviewers_responded`、`reviewers_accounted`、`effective_seats/effective_weight` 的定义放入 PRD 唯一术语表，其他文档只引用。
4. 为 E3、E4、E5、E5a、E6、E7、E9 分别写出 source state、trigger artifact/command、guard、target state、side effects、不可变产物和 timeout 行为。
5. 对 DEADLOCK、NEEDS_ADMIN、disposition timeout、管理员豁免、`no_ff`、post-merge evidence push 失败各给一个完整、与 Schema 可互验的场景。

## 建议的闭环顺序与验收标准

1. **先冻结语义**：裁定 DEADLOCK、E7/disposition writer、HOLD 表示法、E3 集合定义和 merge OID 关系。
2. **再建立 Schema**：完成 v2.5 Schema 与正反 fixtures；禁止用“代码阶段再改 Schema”掩盖实施基线的机器契约冲突。
3. **回写权威 PRD**：删除旧场景、补齐 AEP 第八类消息、§14.5 Merge Policy、disposition timeout/NEEDS_ADMIN 和统一 review_context。
4. **同步消费文档**：更新 FAQ、UC-1/5/6、SRS 映射、执行摘要、改进摘要、STATUS 与代码清单。
5. **重新申请 L1**，最低验收：
   - 所有 JSON/YAML 示例语法可解析，并能通过对应版本 Schema；
   - DEADLOCK 前后只存在一份不可变 `vote_result.json`，人工结果只在 `admin_override.json`；
   - E3 不可被 quorum 提前触发，timeout 无需用户确认即可进入 accounted；
   - `review_context` 任一字段只有一个 canonical 路径，Reviewer 标准命令能直接消费 fixture；
   - E7 的每种 choice 都能唯一推出目标状态和所需产物，未豁免 BLOCKING 不得进入 MERGING；
   - `ff_only` / `no_ff` 各自的 remote OID 断言不矛盾；
   - 全文搜索不再出现作为现行规范的 “DEADLOCK 不写 vote_result”、AEP/1.0 七类、`2/3_majority` 旧配置或“有效票达到 quorum 即 E3”。

## Reviewer 自审记录

- 已检查字段声明位置与示例/Schema 实际读取路径，发现 `code_changes.refs` 与平铺路径冲突。
- 已区分 checklist/申请自述与可验证完成证据；“100% 对齐”“全部物理闭环”未直接采信。
- 本轮范围内 Markdown 的 JSON/YAML fenced blocks 均做了解析检查；解析成功不等于通过 Schema，后者已单独验证。
- 每项 P1 均给出文件路径、行号、矛盾双方与可复现影响。
- 未将其他 reviewer 的批准或反对票作为本结论依据。

## 最终判定

**REJECT L1 / REJECT PG-0 for commit `0bc6247`.**

建议保持 v2.5 为设计迁移草案，完成上述 P1 后重新提交固定 commit 的 Design Sync 复审；本结论不否定 D-1～D-9 的架构方向，也不评价尚未实施的代码质量。
