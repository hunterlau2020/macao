# PRD v2.5 Design-Sync r2 与 UseCases v2.5 Alignment r2 独立评审结论

- **评审日期**：2026-09-02
- **Reviewer**：Codex
- **受审内容 commit**：`6e35a7192f62714bb52444343dc1e034a55e238b`（短 SHA：`6e35a71`）
- **复核增量**：`5583bdd..6e35a71`，同时对 `6e35a71` 完整快照做交叉文档与 Schema 反例复核
- **评审申请**：
  - `docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md`
  - `docs/reviews/2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md`
- **权威基准**：`docs/MACAO_PRD_v2.md`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md` D-1～D-9、`docs/MACAO_REVIEW_GUIDELINES.md`
- **证据状态**：DOC=`CONTRADICTED`；SPEC=`CONTRADICTED`；TEST=`PARTIALLY_VERIFIED`；CODE=`NOT_APPLICABLE`（本轮申请定级仅为 L1）

## 结论

**REJECT：未达到 L1 DOC-ALIGNED，PG-0 不授予。**

本轮确认了上一轮若干用例正文修订确实落地，但“全部阻断项闭环”“100% 机器语义级对齐”“机器契约 fail-closed”等强声明仍不成立。独立反例表明，当前 Draft-07 Schema 会接受空 AEP 业务 payload、约 50 KiB 内联正文、缺少 `task_id/checkpoint_ref/full_document` 的 `.dev.yml`、无加权策略的配置，以及 `DEFERRED/REJECTED + requires_new_checkpoint=true` 的处置件。人工接管、init 歧义和 UC-8 远端失败路径也仍存在互斥规则。

- P0：0
- P1：8
- P2/P3：3
- 两份申请的共同定级：均未通过 L1 / PG-0

## 已对齐 / 已确认项

1. `docs/usecases` 在受审 commit 中是指向 `docs/usercases` 的 Git symlink。
2. `docs/usercases/` 共 13 份 Markdown；控制字符扫描为 0。
3. 受审主文档范围内 27 个标注为 YAML/JSON 的 fenced code block 均可解析。
4. UC-3、UC-6、UC-1-gemini 三个申请点名的示例分别通过对应 Draft-07 Schema。
5. 8 份 valid fixture 全部被接受，7 份 invalid fixture 全部被拒绝；但这只能证明现有 fixture，不证明未覆盖反例也 fail-closed。
6. `docs/schemas/` 与 `src/macao/schemas/` 的 8 份同名 Schema 逐字节一致。
7. `PYTHONPATH=src python3 -m unittest discover tests -q`：`Ran 86 tests in 32.243s — OK`。
8. `python3 -m compileall -q src tests`：通过。
9. UC-7 §2.c 的 `APPROVED` 行本身已经改成“override → `SHOULD_DISPOSE` → Executor FINAL → E4”，UC-8 主成功场景也已把 Pre-merge Evidence 校验列为第 1 关。

上述 TEST 证据不提升为 L2：本轮目标是 L1，且现有测试没有覆盖下述负例与跨文档唯一性问题。

## P0：必须先解决

无。

## P1：进入 PG-0 前必须修正

### P1-1：AEP Schema 没有实现按类型 payload 契约和字节预算，关键非法消息仍被接受

**证据**：

- PRD 在 `docs/MACAO_PRD_v2.md:359-368` 要求单条不超过 16 KiB、单个内联自然语言字段不超过 2048 字节、收发端双向拒绝超限，并规定统一 AEP/1.1 信封。
- UseCases 申请在 `docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md:57` 把这些要求称为“硬约束”；代码清单在 `docs/v2.5_CODE_CHANGE_INVENTORY.md:64` 声称 `aep_envelope.schema.json` 已增加该硬约束。
- 实际 `docs/schemas/aep_envelope.schema.json:6-30` 只校验通用信封和消息类型枚举，`payload` 只是任意 object；它既没有按 `type` 分支，也没有引用 `review_context.schema.json`，更没有字节预算校验。

**独立反例**：以下三项均被当前 Draft-07 接受：

```text
DEVELOPMENT_STARTED + payload={}                 => ACCEPT
REVIEW_REQUEST + payload={}                      => ACCEPT
DEVELOPMENT_STARTED + payload.summary=50000字符  => ACCEPT
```

这意味着 Type A 可缺任务与验收字段，Type B 可缺 10 大 context 块，超限长正文也不会在现有机器契约层被拒绝。现有 `aep_unknown_type.json` 只覆盖未知枚举，不能证明 payload 或预算 fail-closed。

**验收标准**：为 8 类消息定义可执行的 per-type payload Schema（至少 Type A/B/E/H 完整约束），Type B 组合 `review_context` 契约；另以序列化后的 UTF-8 字节数实现 16384/2048 的发送端和接收端校验，并加入空 payload、缺块、超限、多字节字符边界反例。

### P1-2：`.dev.yml` Schema 没有把状态转移所需的核心引用设为必填

**证据**：

- UC-3 要求 Orchestrator 校验“Schema + 指针 + sha256 + `signal: EXPLICIT` + 新 commit + round”，见 `docs/usercases/UC3-dev-checkpoint.md:7`、`:51-53`；其实现落点还明确写着 `full_document` 必填，见 `:104-105`。
- 共享产物表也声明 `.dev.yml` 含 `checkpoint_ref`、`signal: EXPLICIT`、`full_document`，见 `docs/usercases/README.md:93-95`。
- 实际 `docs/schemas/dev_manifest.schema.json:6-13` 的根级 required 未包含 `task_id`、`checkpoint_ref`、`full_document`；`:84-85` 还允许 `signal: IMPLICIT`。

**独立反例**：从 valid fixture 删除 `task_id`、`checkpoint_ref`、`full_document` 后仍为 Schema valid；把 `signal` 改为 `IMPLICIT` 也仍为 Schema valid。

`IMPLICIT` 可被结构层接受、再由运行时保持 HOLD，但这一分层必须被明确写入契约说明；`task_id/checkpoint_ref/full_document` 缺失则无法完成归属、评审对象绑定和全文哈希校验，不应继续被称为完整的 `.dev.yml` 机器契约。

**验收标准**：把三个核心字段加入根级 required；补缺字段反例。若保留 `IMPLICIT`，须在 Schema README 和 UC-3 明确“结构合法但不得触发转移”，并增加该运行时反例测试。

### P1-3：`macao_config` 并未“封闭为 weighted_2/3_v1”

**证据**：

- Design-Sync 申请 `docs/reviews/2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md:27` 明确声称 `macao_config` 已封闭为 `weighted_2/3_v1`。
- PRD `docs/MACAO_PRD_v2.md:329-340` 把五重门禁及配置期独裁帽定义为规范规则。
- 实际 `docs/schemas/macao_config.schema.json:6` 根级只要求 `project`、`team`；`:46-54` 不要求 reviewer 的 `vote_weight`；`:60-75` 虽定义 `policy.consensus_rule`，但根级不要求 `policy`。

**独立反例**：包含两个 Reviewer、但完全没有 `policy` 和 `vote_weight` 的配置被当前 Schema 接受。

**影响**：消费方不能从 Schema 唯一得出采用加权规则、默认权重、独裁帽是否启用及法定人数如何派生，和“配置单一事实源”目标冲突。

**验收标准**：二选一并统一所有文档：A）Schema 强制 `policy.consensus_rule=weighted_2/3_v1` 与所需配置；或 B）规范定义完整、确定性的默认注入结果，并要求 Loader 输出规范化配置后再执行独裁帽/双 quorum 校验。两种方案都要有 policy 缺失、单席位权重达到 2/3、席位与权重 quorum 边界负例。

### P1-4：Disposition Schema 未实现自身规范的枚举联动和审计绑定

**证据**：

- 提案 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:178-193` 规定 `DEFERRED`、`REJECTED`、`EXEMPTED_BY_ADMIN` 必须 `requires_new_checkpoint=false`，并要求 disposition 反向引用冻结的 vote result 与 `issues_index` 哈希。
- UseCases 申请 `docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md:54-55` 同样把 `DEFERRED=false` 与显式布尔守卫列为权威语义。
- 实际 `docs/schemas/review_disposition.schema.json:47-79` 只对 `EXEMPTED_BY_ADMIN` 建立条件约束；`DEFERRED`、`REJECTED` 可配任意布尔。`:6-15` 也没有要求 `issues_index_sha256`，Schema 中没有所声明的冻结 vote-result 引用。

**独立反例**：`DEFERRED + requires_new_checkpoint=true` 与 `REJECTED + requires_new_checkpoint=true` 均被 Schema 接受。前者会让同一处置同时表达“延期、不改当前代码”和“本轮必须产生新 checkpoint”，足以改变 E4/E5a 分流。

**验收标准**：补全 disposition_type 条件矩阵；要求冻结 vote-result 引用与 `issues_index_sha256`；加入每种枚举的正反 fixture，以及缺/错 vote-result hash、重复 issue、未知 issue、覆盖不全的运行时反例。

### P1-5：E7 的唯一出口和 disposition 单写者在 PRD/提案中仍未收敛

**证据**：

- UC-7 的正确详细边是 override 只解除 HOLD 并投影 `SHOULD_DISPOSE`，Executor 提交 FINAL 后才触发 E4，见 `docs/usercases/UC7-human-override.md:31-39`。
- PRD 场景也采用两步边，见 `docs/MACAO_PRD_v2.md:911-912`；但统一状态表 `:859` 仍写成管理员选择 `APPROVED → E4`，没有表现中间等待 FINAL 的状态/守卫。
- 同一行允许 E7 从 `REWORK` 选择 `RETRY_REVIEW → E9`，但 E9 的源状态在 `:860` 仅为 `CONSENSUS_CHECK`，组合后不是闭合状态机。
- 更直接的单写者冲突仍保留在 `docs/PRD_CHANGE_PROPOSAL_v2.5.md:215`：FINAL disposition 可由 “Executor（或 Admin）” 生成；这与 D-2、同文件 `:133-136`、UC-7 及申请中“彻底清理管理员代签”的声明相反。

**影响**：实现者按统一表、提案超时段或 UC-7 会得到不同写者和不同转移时点，上一轮的核心 blocker 尚未在全量权威文本中闭环。

**验收标准**：唯一规范边写成 `E7 APPROVED: HOLD → CONSENSUS_CHECK/SHOULD_DISPOSE`（只生成 override），`Executor FINAL → E4 → MERGING`；删除所有 Admin 写 FINAL 的表述；为 E7 各源状态×五种 choice 给出闭合转移矩阵，不能调用源状态不满足的 E5/E9。

### P1-6：UC-7 把不相容的 init 与 MERGING 异常塞进同一五选项，无法确定性执行

**证据**：

- `docs/usercases/UC7-human-override.md:14-19` 把 init 歧义（P3）和 `MERGING` 冲突（P6）列为同一接管入口；`:29-41` 只定义 `APPROVED/REWORK/RETRY_REVIEW/CANCEL/EXTEND` 五选项；`:61` 又称 init 使用“同一选项集”。
- 但 UC-1 的 init 权威交互是“指定 10 态之一 / 当作新项目 / 中止动态落盘”，见 `docs/usercases/UC1-init-glm.md:166-178`。五个运行期投票选项无法表示 10 态选择。
- P6 的进入态为 `MERGING`，而 PRD E7 的源状态仅是 `HOLD(CONSENSUS_CHECK 或 REWORK)`，见 `docs/MACAO_PRD_v2.md:859`。

**影响**：同一个 init 歧义输入无法从 UC-7 唯一推出合法命令参数；MERGING 冲突究竟先 E4b 进入 REWORK，还是直接调用 E7，也没有唯一答案。

**验收标准**：把 init 的 `ADMIN_STATE_RESOLVED` 从运行期 E7 五选项中分离；为 MERGING 冲突定义唯一边（建议先 E4b/新 checkpoint，再进入适用的人工裁定），并删除不合法的 E7 源状态。

### P1-7：UC-8 对远端不可达给出 fail-closed 与降级成功两种互斥结果

**证据**：

- `docs/usercases/UC8-merge-signoff.md:21-23` 规定 `ls-remote` 未推送或校验失败一律 fail-closed，不得进入合并。
- 同文件 `:55` 又规定“远端不可达（本地/个人仓库场景）”可降级为本地 merge 完成并记录 `PUSH_SKIPPED_LOCAL`。
- `:64-66` 又把 push 瞬时错误重试后转 E4b；申请 `docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md:38` 则宣称 Gate 1 强制验证远端证据已推送。

**影响**：对于同一 `ls-remote` 失败，系统可被实现成拒绝合并、重试后返工或本地成功三种行为，且没有可机器判定的 repository mode 区分条件。这直接影响 D-8 审计完整性。

**验收标准**：在 `macao.yaml` 定义显式 repository mode/remote-required 策略；共享模式严格 fail-closed；若允许纯本地模式，需定义没有 remote 时的本地 evidence seal 等价物，并对 DNS/认证/不存在 ref/无 remote 四类失败逐项给出唯一结果。

### P1-8：SRS 的现行映射仍把 AEP 写成 7 类，与头部映射和 PRD 的 8 类冲突

**证据**：

- `docs/SRSv1.md:7-16` 的 v2.5 映射表正确写为 AEP/1.1 共 8 类。
- 但同文件 `:610-613` 的“历史内容已更名”提示却写成“统一为 7 类 AEP 消息，并以 PRD §2.4 为准”。PRD `docs/MACAO_PRD_v2.md:344-357` 明确是 8 类。

这不是未加历史标记的旧正文，而是历史段上方用于告诉读者“当前替代规范是什么”的迁移提示本身写错，因此会直接误导实现与测试清单。

**验收标准**：把该提示改成 8 类并点名新增 Type E；全文扫描所有现行迁移提示，确保旧正文被明确降级且不会与头部映射竞争。

## P2/P3：可延期但需登记

### P2-1：UC-3 的事件编号仍错误地写成 E1/E6

PRD 统一表 `docs/MACAO_PRD_v2.md:848-850` 定义 E1 是 `IDLE → CODING`；首次 `.dev.yml` 使 `CODING → READY_FOR_REVIEW` 的产物边没有编号，只有返工边是 E6。`docs/usercases/README.md:16`、`:44`、`:64` 以及 r2 申请 `docs/reviews/2026-09-02-review-request-UseCases-v2.5-Alignment-r2.md:33` 仍把首次检查点写成 E1/E6。状态名本身正确，但事件 ID 会污染追踪矩阵与测试命名。

### P2-2：PRD 对合并关卡顺序有一处摘要漂移

PRD §14.5 `docs/MACAO_PRD_v2.md:1478-1489` 与 UC-8 都规定 Pre-merge Evidence Push 在检出前；但统一转移表 E4 的伴随动作 `:853` 写成“检出 → pre-merge evidence push 校验 → merge”。应使摘要顺序与权威流水线一致。

### P3-1：申请的文档计数无法在受审 commit 复现

Design-Sync 申请 `docs/reviews/2026-09-02-review-request-PRD-v2.5-Design-Sync-r2.md:40` 声称扫描 179 份 Markdown；`git ls-tree -r --name-only 6e35a71` 在受审 commit 只能计得 167 份 `.md`（其中 `docs/` 下 166 份）。控制字符为 0 的方向性结论可以复现，但文件数和扫描命令必须记录清楚，避免把工作区未跟踪文件或 symlink 展开结果算入已提交基线。

## 独立反例矩阵

| 反例 | 当前结果 | 规范期望 | 结论 |
|---|---:|---:|---|
| AEP Type A 空 payload | ACCEPT | REJECT | CONTRADICTED |
| AEP Type B 空 payload | ACCEPT | REJECT | CONTRADICTED |
| AEP 约 50 KiB 内联文本 | ACCEPT | REJECT | CONTRADICTED |
| `.dev.yml` 缺 task/ref/full_document | ACCEPT | REJECT | CONTRADICTED |
| `.dev.yml signal=IMPLICIT` | Schema ACCEPT | 结构/运行时边界需明确，FSM 不转移 | PARTIALLY_SPECIFIED |
| `macao.yaml` 缺 policy/weights | ACCEPT | 强制加权或确定性默认 | CONTRADICTED |
| `DEFERRED + requires_new_checkpoint=true` | ACCEPT | REJECT | CONTRADICTED |
| `REJECTED + requires_new_checkpoint=true` | ACCEPT | REJECT | CONTRADICTED |

## 交叉文档需做的文字修订

1. `MACAO_PRD_v2.md`：收敛 E7/E9 的源状态、APPROVED 两步边和 E4 关卡顺序。
2. `PRD_CHANGE_PROPOSAL_v2.5.md`：删除 `Executor（或 Admin）`，补齐 disposition 的冻结 vote-result 引用字段。
3. `SRSv1.md`：把迁移提示中的 7 类改成 8 类；若保留旧正文，所有替代提示必须与头部 v2.5 映射一致。
4. `docs/usercases/README.md` 与 r2 申请：首次 checkpoint 不再标 E1；用正式编号或“未编号产物边”。
5. UC-7：分离 init 管理员状态确认与运行期 E7；限定每个源状态可用 choice。
6. UC-8：显式区分 remote-required 与 local-only，消除同一远端错误的三种结果。
7. Schema README/代码清单：区分“JSON Schema 可校验”“运行时跨项校验”“UTF-8 字节预算校验”，不得用 7 个既有 invalid fixture 外推“全部 fail-closed”。

## 建议的闭环顺序与验收标准

1. 先冻结一张唯一的 E7/初始化/合并失败转移矩阵，消除 P1-5～P1-7。
2. 再补 AEP、dev、config、disposition 四类机器契约和上述 8 个负例；正反 fixture 应覆盖每条会改变 FSM 的守卫。
3. 同步 PRD、提案、SRS、FAQ、README、UC 分册和代码清单；用 `rg` 清除旧的 7 类、Admin 写 FINAL、E1/E6 等现行表述。
4. 重跑代码块解析、Schema 正反例、镜像 Schema byte diff、全套单测；报告必须给出 commit 内可复现的扫描命令和准确文件数。
5. 重新申请 L1 时，要求 DOC/SPEC 均为 VERIFIED，且 P0/P1 为 0；86 项旧回归通过不能替代新增设计负例。

## Reviewer 自审记录

- 已检查字段声明位置与实际 required 列表，未以正例通过代替负例验证。
- 已检查 `[x]`/“全部闭环”/“100%”等强声明；本报告未把申请方或其他 reviewer 的结论当作证据。
- 已解析受审范围内全部 27 个 YAML/JSON 标注代码块。
- 每个 P1 均给出文件、行号、冲突规则及可复现反例或状态推演。
- 本轮未因现有 86 项测试通过而外推 L2/L3，也未修改 `docs/reviews/STATUS.md`。
