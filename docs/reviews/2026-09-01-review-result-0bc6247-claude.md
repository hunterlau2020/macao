# MACAO PRD v2.5 产品方案 / 技术设计同步与代码变更清单 评审结论

- **评审日期**：2026-09-01
- **评审人**：`claude`
- **评审对象**：[`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`](2026-09-01-review-request-PRD-v2.5-Design-Sync.md)
- **对应 commit**：`0bc6247`（`docs: sync PRD v2.5 design, add code change inventory, and submit review request`），工作区 clean
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0 §1–§6、§9、§11（按 §1.2「设计文档跨文档对齐评审」裁剪）
- **事实锚点**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **申请定级**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **结构化 issue**：`BLOCKING` × 10（P0 × 2 / P1 × 8），`ADVISORY` × 15（P2 × 10 / P3 × 5）

---

## 结论

**不予授予 L1 DOC-ALIGNED / PG-0；不批准据此进入 Phase 1～5 代码实施。**

v2.5 的**架构方向**（D-1～D-9：零语义创作、内容与控制分层、独立不可变产物、纯整数加权共识、Git Evidence Ref 隔离）是正确的，且在 §3.3 转移表、§14.2 `role_view`、UC-1 h1/h2、UC-5 计票主路径、UC-6 处置守卫这几处已经落到可核验的文字。这部分我逐条独立复算通过，记录在 §二。

但申请 §1 所称「**全量完成同步修改**」、§4.1 所称「契约字段在 PRD、SRS、FAQ、UC 及 Schema 设计间实现 **100%** 命名与语义对齐」、§4.2 所称「**10 状态单一事实源，不存在歧义转移分支**」这三条**不成立**，且不是措辞问题：

1. 权威 PRD 的「状态识别的**唯一规范入口**」（§3.2）与「场景推演三」（§3.4）仍是 v2.3.1 语义，与同一文件的 §3.3 / D-1 / E4 / E5a **互为反命题**；
2. v2.5 的核心新产物 `review_disposition` 在权威 PRD **没有任何 §2.x 契约定义**，全库有 **4 套文件名、2 套字段名、2 处路径**；
3. PRD 自称 `docs/schemas/` 是「**唯一校验依据**」（L1454），我把 PRD 的三份产物示例喂给该目录下的 Draft-07 Schema 实测：`vote_result` **10 项失败**、`review_context` 权威模型 **7 项失败**、§2.2 自称的 5 条「Schema 条件互锁约束」**4 条根本没有被强制**。

按 GUIDELINES §3.3，L1 的最低要求是「DOC/SPEC 为 VERIFIED，即给出确切文件路径 + 行号，且**交叉引用不矛盾**」。本轮交叉引用矛盾是**结构性**的：同一份权威基准内部对同一决策给出互斥答案，实现者按不同章节编码会得到不同的状态机。PG-0 的语义是「允许开始编码」，在此前提下授予 PG-0，等于批准并行长出两套实现。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

**强制自检 5 项**（本轮结果）：

| # | 检查项 | 结果 |
|---|---|---|
| 1 | 字段名 vs 实际读取路径是否一致 | **CONTRADICTED** → P0-2（§5.2 扁平 vs §2.4/§5.3/Schema 嵌套）、P0-1（§3.2 读 `decision` 枚举与 §2.3 不同） |
| 2 | 每处 `[x]` / 「已完成」是否有证据 | PRD 内部 **VERIFIED**：§4.1/§10 共 21 个复选框全部为 `[ ]`，§10 标题明写「未达成前不得勾选」——这一点做得对，予以确认。**申请文件与 STATUS 侧 CONTRADICTED** → P1-3、P1-4、P1-6 |
| 3 | 确定性用语是否标注目标/待验证 | PRD 内部 **VERIFIED**：L686 明确「图中标注的可信度（100%/80%/60%）为设计目标值，以 PoC 实测数据为准」。**申请 §4.1「100% 命名与语义对齐」未标注且已被证伪** → 见 P1-5 |
| 4 | YAML/JSON 代码块是否真能解析 | **PASS**：PRD 8 段 JSON + 5 段 YAML、清单、UC-6 全部 `json.loads` / `yaml.safe_load` 成功。但「能解析」≠「合契约」，见 P1-5 |
| 5 | 每个 P0/P1 是否给出可复现路径 + 行号 | 是；三项 Schema 结论附可直接重跑的脚本（§七） |

**本轮我自己的测量纪律与更正**：

- **主动撤回一项拟议判定**：起初我准备就 §6.2 L1121「弃权票不计入分母」与 §2.3 门禁 3「分母为配置总权重 $W$」提 P2。逐条复核后确认**不矛盾**——§6.2 说的是有效权重 $E_W$ 的构成（弃权不进 $E_W$），门禁 3 说的是 $E_W$ 要与 $\lceil 2W/3 \rceil$ 比较，两者是被比较量与阈值的关系。该项**不予提出**。L1121 真正的问题只是它指向的「§2.3 决策表」在 v2.5 已不存在（P2-6）。
- **一项结论我无法验证到底，如实标 UNKNOWN**：`docs/SRSv1.md` L7–L18 的 blockquote 内表格，表头行带 `>`、其后 12 行不带、随后又以 `>` 恢复。本机无 GFM 渲染器（`markdown` / `mistune` 均未安装），**我没有实测渲染结果**，因此只登记「结构不闭合」这一可验证事实（P3-2），不声称「渲染断裂」。相应地，申请 §4.1「全量 Markdown 符合 GFM 规范」在本轮判为 **CLAIM_ONLY**，而非 CONTRADICTED。
- **连续漏审模式登记**：本轮我针对 GUIDELINES §9-A（字段声明位置 vs 实际读取位置）做了机器化核验而非目视比对——上一轮（`15e8918`）我曾因目视比对导致行号引用漂移。本轮全部行号在写入前用 `sed -n` 逐条回读确认。

**证据类型适用性**：本轮对象是文档体系与实施清单。DOC / SPEC 为主；对 `docs/schemas/` 现存契约做了 Draft-07 实测（记为 **TEST**）；对状态机做了手工重放（记为 **SIM**，§六）。业务实现代码 **NOT_APPLICABLE**，仅核验清单路径存在性。

---

## 一、申请 §3「核心专家意见物理闭环核验表」逐条核验

申请把这张表作为定级的主要依据，因此逐条falsify：

| 申请声称 | 本轮判定 | 决定性证据 |
|---|---|---|
| **Kimi P0-1** E7 豁免与状态转移 | **PARTIALLY_VERIFIED** | §3.3 E7（L797）确有 `exempt_issue_ids` + `admin_override.json` + `override_id`；但 §3.4 场景三 6a–6d（L856–859）与 UC-7 L44/L80 仍规定 E7「产生终局 `vote_result.json`」——即 D-1 明令禁止的二次回写 |
| **Kimi P1-1** E3 全席位 accounted | **PARTIALLY_VERIFIED** | §3.3 E3（L789）已改；但「唯一规范入口」§3.2 Layer 1b（L720–723）仍是 `count_valid >= minimum_quorum` 提前截断；§1.1 流程图 L90、§16.2 阶段 4 同样未改 |
| **Kimi P1-2** DEADLOCK 即时落盘 | **CONTRADICTED** | §3.3 E3（L789）「即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）」 vs §3.4 场景三步骤 5（L855）「**不写 `vote_result.json`**」+ L862「步骤 5 期间没有任何 `vote_result.json` 处于可被读走状态」。同一份权威基准的正反命题 |
| **Kimi P1-3** `NEEDS_ADMIN` 答复闭环 | **CONTRADICTED（相对申请落点）** | 申请写「在 PRD **§6.1** 与 UC-6 中明确」。§6.1 `HUMAN_OVERRIDE_TRIGGERS`（L1070–1108）六条触发器**无 `NEEDS_ADMIN`**。全 PRD `NEEDS_ADMIN` 仅出现在 L383、L1499 两处表格单元格 |
| **Grok P1-1** Disposition 超时 | **CONTRADICTED（相对申请落点）** | 申请写「在 PRD **§6.1** 中定义 `timeouts.review_disposition`（默认 30m）」。`timeouts.review_disposition` 在**全仓库不存在**；§13「单一事实源」的 `timeouts:` 块（L1434–1439）五个键无此项；§6.1 无该触发器。仅 §1.2 表格单元格出现字面「30m (disposition)」 |
| **Grok P1-2** `SHOULD_DISPOSE` 角色投影 | **PARTIALLY_VERIFIED** | PRD §14.2（L1498）与 UC-1 h1/h2（L132、L152）**已补齐且一致**，这一项做到了；但 FAQ Q12 的 `CONSENSUS_CHECK` 行仍写「执行者：等计票结果」，无处置态 |
| **Qwen P1-1** 写者边界 | **PARTIALLY_VERIFIED** | UC-5 §2.c、UC-6、FAQ Q15 已切开双写；但 FAQ **Q13** 仍写「执行者**汇总**问题清单、正文索引、哪些专家发现」——`issues_index` 在 v2.5 是 Orchestrator 原样拼接（UC-5 §2.c-2）。同一份 FAQ 内 Q13 与 Q15 归属相反。且 **F-20 原文未动**，仍写「必须由后续规范显式裁定」 |
| **Gemini P1-1** 纯整数加权 | **VERIFIED** | 我独立复算 §2.3 示例（N=3, W=4, 权重 2/1/1, 2 YES + 1 NO）：门禁 2 席位 $3\ge\lceil6/3\rceil=2$ ✓；门禁 3 权重 $4\ge\lceil8/3\rceil=3$ ✓；门禁 4 $3\times3=9\ge2\times4=8$ ✓；门禁 5 胜方席位 $2\ge2$ ✓ → `APPROVED`，与示例一致。独裁帽 $\forall i,3w_i<2W$ 在该配置下 $3\times2=6<8$ ✓。与 F-22 同向 |

**8 项中：VERIFIED 1、PARTIALLY_VERIFIED 4、CONTRADICTED 3。** 申请 §1「100% 物理闭环」不成立。

需要指出的是，三条 CONTRADICTED 里有两条（Kimi P1-3、Grok P1-1）的性质是相同的：**提案里写了、role_view 表格里提到了、但没有落到规范正文与配置**。GUIDELINES §9-B 正是这一模式——「计划要做」被当成「已完成」合入决策。

---

## 二、已对齐 / 已确认项（独立复现，非采信自述）

按 GUIDELINES §8「真理不等于投票」，以下每条我都自己走了一遍，而不是从提案或 STATUS 抄结论：

1. **D-6 纯整数加权五重门禁**：公式在 PRD §2.3（L358–367）、FAQ Q15、UC-5 §2.b **三处逐字一致**，无第二套表述。示例复算通过（见 §一末行）。这是本轮质量最高的一处收敛。
2. **D-5 显式改码守卫**：`requires_new_checkpoint` 为必填布尔、E5a 只读该布尔、严禁从自然语言推断——PRD §3.3 E5a（L795）、UC-6 §2.b/§2.c、清单 §2.3 同向，与 F-19 逐字对应。
3. **`role_view` 投影表**：PRD §14.2（L1490–1502）与 UC-1 h2（L144–156）各 11 行，我做了**逐单元格机器比对**：11 行的 Executor / Reviewer 枚举值**全部相同**（UC-1 侧其中 4 行另附括号注释，如 `SHOULD_REVIEW（即 REVIEWING）`，枚举本身无差异），含 `SHOULD_DISPOSE`；`NOTIFY_EXECUTOR_DISPOSE` 在 UC-1 h1（L132）侧同值。
4. **F-13 边界在计票侧成立**：UC-5 §边界声明 + §2.c-2「原样拼接、不合并同类项、不标采纳」与 F-5 / F-13 一致；UC-5 §6 验收 2 给出可测断言（「与 fixture 信封逐条零差集」）。
5. **`.review.yml` 示例合契约**：PRD §2.2 示例（L225–261）对 `docs/schemas/review_manifest.schema.json` **Draft-07 校验 PASS**。三份产物示例中唯一通过的一份。
6. **PRD 自身的诚实性做得好**（GUIDELINES §9-B/§9-C）：全文 21 个复选框全为 `[ ]`；§10 标题明写「验收标准（**未达成前不得勾选**）」；L686 明确把 100%/80%/60% 标为「设计目标值，以 PoC 实测数据为准」。这三点是很多项目做不到的，应当保持。
7. **返工轮次隔离可唯一推出**：§3.4 生命周期表 + 场景推演二步骤 6 能唯一推出「r1 `.review.yml` 在 r2 开始前已提升至 `refs/macao/evidence/<task>/r1`，同名覆盖不破坏审计链」。这是 GUIDELINES §6 反例库第 8 条，**通过**。
8. **人工接管超时默认动作可唯一推出**：§6.1 总则（L1110）「除 trigger 1 外，其余触发条件到期后默认动作同样为 HOLD + 持续告警……任何情况下不得因超时静默推进」。GUIDELINES §6 反例库第 9 条，**通过**（仅限已登记的 6 类触发器，见 P1-4）。

---

## 三、P0：必须先解决

### P0-1　权威基准内部互斥，v2.5 状态机不可唯一推出（识别入口与场景推演仍是 v2.3.1）

**证据 A — §3.2 Layer 1c（L728–747）的 `decision` 枚举与 v2.5 不是同一套**

```
735:  # 显式四分支：终局 decision 枚举包含 APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED（Schema 强制）
736:  if result.decision == 'APPROVED':
737:      return AgentState.MERGING                  # E4：进入合并流水线
```

- **无 `DEADLOCK` 分支**。若实现者遵守 §3.3 E3「即时落盘 `decision: DEADLOCK`」，该文件到达 Layer 1c 后落入全部 `elif` 之外，行为未定义——静默 HOLD、误判、抛错三种都无法从正文推出。
- **`decision == APPROVED` 无条件进 `MERGING`**：不读 `requires_disposition`、不读 FINAL disposition、不存在 E5a。与 §3.3 E4（L791，有 issue 必须 FINAL 且全 `requires_new_checkpoint=false`）和 E5a（L795，任一 `true` → `REWORK`）互斥。
- **`RETRY_REVIEW` / `CANCELLED` 被当作机器 `decision`**：与 D-1（机器决策仅 `APPROVED | REWORK_REQUIRED | DEADLOCK`，人工裁定写独立 `admin_override.json`）互斥。
- 注释里「（Schema 强制）」四个字本身是可证伪的强声明：现行 `docs/schemas/vote_result.schema.json:51` 的枚举确为 `["APPROVED","REWORK_REQUIRED","RETRY_REVIEW","CANCELLED"]`——**Schema 强制的是 v2.3.1 那一套，不是 v2.5 那一套**。清单 §2.1 把该文件标为「重构 (v2.0)」但未把「删除 `RETRY_REVIEW`/`CANCELLED` 作为机器 decision」列为破坏性迁移（见 P1-7）。

**证据 B — §3.2 Layer 1b（L720–723）仍提前截断**

```
722:  reviews = load_all_validated('.macao/.reviews/*.review.yml', REVIEW_YML_SCHEMA, ...)
723:  if reviews.count_valid >= minimum_quorum(reviews.configured):
```

与 §3.3 E3（L789）「**所有配置席位已响应……或已被持久化 timeout 纳入 accounted 集合**」互斥。同口径的旧文字还留在 §1.1 流程图 L90（「达到法定人数或超时降级流程完成」）与 §16.2 阶段 4（「有效票 ≥ 法定人数（E3）」）。

**证据 C — §3.4 场景推演三（L855–862）禁止 DEADLOCK 落盘并回写终局**

```
855: | 5 | …（§2.3 决策表第 4 行）→ 发送 HUMAN_OVERRIDE_REQUEST…；**不写 vote_result.json**，CONSENSUS_CHECK HOLD |
856: | 6a | 用户 macao override resolve --choice APPROVED | 裁定落盘终局 vote_result（decision=APPROVED, resolution=human_override）→ MERGING（E4） |
862: - …步骤 5 期间没有任何 .review.yml/vote_result.json 处于可被读走状态…
```

D-1 的正反两个命题写在同一份文件里，相距 66 行。

**SIM 重放（GUIDELINES §6「2-reviewer 1 批准 + 1 反对」）**：N=2、W=2、1 YES + 1 NO。门禁 2 $2\ge2$ ✓、门禁 3 $2\ge\lceil4/3\rceil=2$ ✓、门禁 4 $3\times1=3\ge2\times2=4$ ✗（双向）→ `DEADLOCK`。此后：

| 实现者信哪一节 | 磁盘上有没有 `vote_result.json` | E7 改什么 | `APPROVED` + 未处置 issue 去哪 |
|---|---|---|---|
| §3.3 E3 | 有，`decision: DEADLOCK`，不可变 | 独立 `admin_override.json` | 停 `CONSENSUS_CHECK` 等 FINAL |
| §3.4 场景三 | 没有 | 回写 `vote_result.decision` | — |
| §3.2 Layer 1c | 有即读 | — | 立即 `MERGING` |

三条路径三种结果。**这一条对 L1 是决定性的**：GUIDELINES §2.1 对 L1 的要求是「四份文档字段/术语/勾选状态可用同一张对照表逐条核验」，此处连**同一份文档**都无法自洽。

**验收标准**（四条须同时成立）：
1. §3.2 Layer 1b 的谓词与 §3.3 E3 同构（全席位 accounted），删除 `minimum_quorum` 提前 return；
2. §3.2 Layer 1c 增加 `DEADLOCK` → HOLD 分支；`APPROVED` 且 `requires_disposition=true` 且无 FINAL → 不转移；有 FINAL 后按布尔分流 E4 / E5a；删除 `RETRY_REVIEW` / `CANCELLED` 作为 `vote_result.decision` 的分支与 L735 注释；
3. §3.4 场景三步骤 5 改为即时落盘 `DEADLOCK`，6a–6d 改为生成 `admin_override.json`；删除 L862 的「无 vote_result」断言；
4. §1.1 流程图 L90 与 §16.2 阶段 4 同步改口径。

---

### P0-2　`review_context` 的「唯一权威完整模型」与它自己指定的机器契约互斥（7 项校验失败）

PRD 对同一组字段给出**两个互斥的「唯一权威路径」声明**：

- §2.4 Type B 注 1（L514）：「`code_changes.refs.{base_commit, head_commit}` 是**唯一权威路径**（全文所有示例、消费代码一律使用该嵌套结构，**不允许扁平写法**）」
- §5.2 首行（L937）：「本节是 `review_context` 的**唯一权威完整模型**……机器契约见 `docs/schemas/review_context.schema.json`」，而其正文 L980–983 恰恰用的是被禁止的扁平写法：

```yaml
  code_changes:
    base_commit: "b2c3d4e"
    head_commit: "a1b2c3d"
    diff_policy: "generate_locally"
```

而 §5.3 Reviewer 标准工作流 L1036–1037 读的是嵌套路径：

```bash
BASE=$(jq -r '.code_changes.refs.base_commit' /tmp/context.json)
HEAD_COMMIT=$(jq -r '.code_changes.refs.head_commit' /tmp/context.json)
```

**这正是 GUIDELINES §9 漏审模式 A 的教科书形态**：字段声明在扁平路径，消费方从嵌套路径读取，实现后 `jq` 返回 `null`，`git diff ".." ".."` 静默失败。

**TEST（可重跑，见 §七脚本 1）**——按 §5.2（L937–1000）逐字构造实例，用 §5.2 自己指定的 `docs/schemas/review_context.schema.json` 做 Draft-07 校验：

```
PRD §5.2 实例 vs review_context.schema.json -> FAIL (7)
   - ['code_changes'] 'refs' is a required property
   - ['code_changes'] Additional properties are not allowed ('base_commit','diff_policy','head_commit' were unexpected)
   - ['dev_checkpoint'] 'path' is a required property
   - ['history'] [] is not of type 'object'
   - ['quality_snapshot'] 'tests' is a required property
   - ['references'] [] is not of type 'object'
   - ['task_info'] 'description' is a required property
```

注意 `additionalProperties: false` 已在生效：按「唯一权威完整模型」写出的 context **一定**被现行契约拒收，不是宽松兼容问题。

**附带的三处结构缺陷**：

- **块数三种说法**：§5.2 标题「**9 大**语义块」、§5.2 首行「两个传输块 + **七个**语义块，共 9」、§2.4 注 4（L517）「两个传输块 + **六个**语义块」。2+6=8≠9。
- **`evidence` 块被定义但未列入 `required_blocks`**：`required_blocks` 九项（L944–952）不含 `evidence`，正文却定义了 `evidence:`（L964–969），且 `quality_snapshot.source: "evidence.dev_manifest"`（L987）**指向它**。只校验 `required_blocks` 的实现会放过一个缺 `evidence` 的 context，导致 `quality_snapshot` 悬空。
- **`review_guidelines` 块在机器契约中不存在**：`review_context.schema.json` 的 `properties` 为 `[dev_checkpoint, repository, task_info, code_changes, quality_snapshot, executor_self_assessment, history, references]`，既无 `evidence` 也无 `review_guidelines`，而 §5.2 把 `review_guidelines` 列为九大**必需**块之一。

**为什么判 P0**：GUIDELINES §6 反例库明列一条「`review_context` 中的 diff/patch 字段与 Reviewer 工作流期望的载体（命令/文件/ref）不一致」。这是方法论**点名要求推演的场景**，本轮实测不通过。同时 §4 声明验证矩阵要求「`review_context` 完整，reviewer 一眼看懂」必须验证「Reviewer 标准工作流读取的字段名是否与实际发送的字段名一致」——不一致。

**验收标准**：§5.2 改为嵌套 `code_changes.refs.*`；三处块数统一；`evidence` 与 `review_guidelines` 要么进 `required_blocks` 并同步进 Schema，要么从正文删除；`history` / `references` 的类型（数组 vs 对象）与 Schema 对齐；改完后 §5.2 实例对 Schema 校验须 PASS（§七脚本 1 应输出 PASS）。

---

## 四、P1：进入下一阶段前必须修正

### P1-1　v2.5 核心新产物 `review_disposition` 在权威 PRD 无契约定义，全库 4 套文件名 / 2 套字段名

第二部分「标准输出物规范」只有 2.1 `.dev.yml`、2.2 `.review.yml`、2.3 `vote_result.json`、2.4 AEP——**没有 2.5**。整个 v2.5 架构的支点产物，在权威基准里只以文件名形式散见于表格单元格。

| 出处 | 文件名 | 路径 |
|---|---|---|
| PRD §1.2（L145）、附录（L1529） | `review_disposition.yml` | — |
| PRD §3.4 生命周期表（L818） | `executor.disposition.yml` | — |
| UC-6 §2.b、FAQ Q15 | `executor.disposition.yml` | `.macao/.dispositions/r<round>/` |
| 清单 §2.1 | `review_disposition.schema.json` | `docs/schemas/` |

字段名两套：提案 §4.3 `status` / `items[]` / `decision` / `reason_ref` / `artifact_revision`，UC-6 与清单 `disposition_status` / `dispositions[]` / `disposition_type` / `rationale`。GUIDELINES §5 明文禁止：「禁止用不同名词描述同一决策结果」「摘要文档中的示例字段名与权威基准 Schema 字段名不一致」。

派生的语义空洞：`DRAFT`（UC-6）与 `PENDING_ADMIN`（提案）不是同一概念。`NEEDS_ADMIN` 处置在 UC-6 里只能落成 `disposition_status: DRAFT`，而 E4/E5a 守卫只认 `FINAL`——**「执行者还没写完」与「执行者写完了、等管理员」在守卫层不可区分**，两者都停在 HOLD 且无法区分该催谁。这恰是 Kimi P1-3 要闭环的问题。

**验收标准**：在 PRD 第二部分新增 `2.5 review_disposition` 唯一信封（用途 / 位置 / 完整格式 / 字段语义 / 与 evidence ref 的关系），UC-6、FAQ Q15、清单、未来 Schema 逐字段同名同枚举；`DRAFT` 与 `PENDING_ADMIN` 二选一并写入 §3.3 转移表说明其是否触发守卫。

### P1-2　AEP/1.1：声明 8 类、正文 7 类、缺核心新消息示例、全部示例版本号写反

| # | 事实 | 行号 |
|---|---|---|
| 1 | 「AEP v1.1 共定义 **8 种**消息类型」，第 5 类为 `DISPOSITION_REQUIRED` | L372、L380 |
| 2 | 18 行后：「以下给出……全部 **7 个**消息类型」「**统一信封约定**（适用于全部 **7 类**消息）」 | L390、L392 |
| 3 | 实际示例 Type A–G 共 7 段，**`DISPOSITION_REQUIRED` 无任何 payload 示例** | L399–648 |
| 4 | 7 段示例的 `"protocol"` **全部**为 `"AEP/1.0"` | L403/434/523/553/585/606/631 |
| 5 | §3.3 E3 称 `HUMAN_OVERRIDE_REQUEST` 为「**Type H**」，§2.4 与 §3.4 称「**Type G**」；全文无 Type H | L789 vs L627/L855 |
| 6 | Type G `options` 为 `["APPROVED","REWORK","RETRY_REVIEW","CANCEL"]`，缺 §3.3 E7 的 `EXTEND`；无 `exempt_issue_ids` | L642 vs L797 |

GUIDELINES §4 声明验证矩阵**点名**这一条：「『AEP 定义 N 种消息类型』——文档中出现『完整格式』『详细格式』等措辞时，是否与实际给出详细 Schema 的消息类型数一致」。第 8 类是 v2.5 的调度主通道（E5 伴随动作要发它、UC-1 h1 要发它、UC-5 §2.e 要发它），只出现在表头。

**与 §2.4 自身字节预算规则互斥的三处示例**（同时违反 F-8「agmsg/AEP 不是长正文仓库」与 F-14「超限正文必须外置引用，发送端不得静默截断」）：

- Type B（L450–451）：`review_context.dev_checkpoint` 用 `content_base64` 内联 `.dev.yml` 全文，而 §2.1 已为它定义了 `full_document: {path, evidence_commit, sha256}`；
- Type C（L536–537）：`review_file.content_base64` 内联整份 `.review.yml`；且 `vote_summary.status` 仍是旧词表，无三值 `vote`、无 `review_round`；
- Type F（L619）：`attachments[].content_base64`。

**Type D 保留了清单声明已删除的字段**：L571–572 的 `issues_to_fix[].description` / `.suggestion`，而清单 §2.1 明写「**彻底移除**旧 `issues_summary` 混合写字段与 `issues_to_fix.description` **代写**字段」，UC-1 h0(2) 也明写「现 Schema 里由编排器填写的 `next_step.issues_to_fix.description/suggestion` **废止**（那是内容写作）」。权威基准的示例仍在示范被废止的代写行为——这直接违反 P-1 零语义创作与 F-11。

**验收标准**：正文「8 类」与 8 段示例一致（补 `DISPOSITION_REQUIRED` payload：至少含 `task_id`/`checkpoint_ref`/`review_round`/`vote_result` 引用三元组/`issues_index_sha256`/`deadline`）；Type 字母唯一；`protocol` 统一为 `AEP/1.1` 并写明与 1.0 的兼容规则；Type B/C/F 的 `content_base64` 改为 `path + evidence_commit + sha256`（跨机场景 §16.4 δ2 若确需内联，需单独定义上限与摘要校验并写入 §2.4）；Type D 删除 `description`/`suggestion` 并改为引用上一轮 disposition；Type G `options` 与 E7 同一枚举并增加 `exempt_issue_ids`。

### P1-3　§13「macao.yaml 单一事实源」未随 v2.5 升级，加权共识与处置超时**没有配置面**

§13 开篇（L1407）声明：「正文出现的全部数值（超时/阈值/法定人数/轮次上限）均为该文件的默认值」。实测该章节仍是 v2.3.1 原样：

| v2.5 要求的配置项 | 出处 | §13 现状 |
|---|---|---|
| `team.reviewers[].vote_weight` | §2.3 门禁、FAQ Q15、清单 §2.2、F-16 | **缺失**（L1421–1423 两个 reviewer 条目只有 `id`/`cli`/`adapter`） |
| 配置期独裁帽校验 $\forall i,3w_i<2W$ | §2.3 门禁 1、清单 §2.2 | **缺失**（`policy:` 块无相关键） |
| `minimum_winning_seats`（默认 2） | §2.3 门禁 5、`policy_snapshot` | **缺失** |
| 权重法定人数 $\lceil 2W/3\rceil$ | §2.3 门禁 3 | **缺失**（只有席位向的 `min_effective_votes`） |
| `timeouts.review_disposition`（30m） | 申请 §3 Grok P1-1、§1.2 表格 | **缺失**（L1434–1439 五键无此项） |
| `aep.max_message_bytes = 16384` | §2.4「`aep.max_message_bytes` 默认 16384」 | **缺失**（全文无 `aep:` 配置块） |
| `consensus_rule` | §2.3 `policy_snapshot.rule = "weighted_2/3_v1"` | L1425 仍为 `"2/3_majority"` |
| `model:` 透传 | §19（L1664）「在 `macao.yaml` 中通过 `model:` 显式声明」 | **缺失** |

`security.allowed_clis`（L1447）仍为 `["claude-code","codex","kimi"]`，而 §19（L1663）声明 `opencode` / `agy` / `agent` 均支持任意角色。

**这一条把申请 §3 的 Grok P1-1 闭环声明证伪到底**：不仅 §6.1 没有该触发器，**定义配置项的唯一章节里也没有这个键**。一个「默认 30m」的超时，在单一事实源里不存在。

**验收标准**：§13 补齐上表 8 项；`consensus_rule` 改为 `weighted_2/3_v1`；`allowed_clis` 与 §19 一致；补 §13 与 `docs/schemas/macao_config.schema.json` 的对应关系。

### P1-4　§6.1 人工接管触发器缺 v2.5 新增的两类 HOLD 来源

`HUMAN_OVERRIDE_TRIGGERS`（L1070–1108）六条：State ambiguity / Reviewer timeout / Consensus deadlock / Process crash / Git conflict / Unknown state。**无 disposition 超时、无 `NEEDS_ADMIN`**，Consensus deadlock 的 `--choice` 枚举（L1086）也缺 `EXTEND`。

后果是可推演的：v2.5 新增了两条通往 HOLD 的路径（`requires_disposition=true` 且执行者逾期未交；执行者显式声明 `NEEDS_ADMIN`），而 §6.1 是全文唯一规定「HOLD 之后系统默认做什么」的地方（L1110 总则）。这两类 HOLD 的默认动作、超时时限、升级路径**均不可从文档推出**。

放大问题的是**三份文档同时指向这个不存在的落点**：申请 §3 两行、`docs/SRSv1.md` L16（「人工接管仅提概念 → 明确 DEADLOCK、超时、门禁失败、`NEEDS_ADMIN` 与 E7 豁免等完整接管闭环（**见 PRD §6.1**）」）、提案 §4.2。

**验收标准**：§6.1 增加 `Disposition timeout`（含 `timeouts.review_disposition` 引用、到期动作、E7 可选项）与 `NEEDS_ADMIN` 两条触发器；Consensus deadlock 的 `--choice` 补 `EXTEND` 与 `--exempt-issue-ids`。

### P1-5　PRD 产物示例与其自称的「唯一校验依据」互斥；§2.2 的五条「Schema 条件互锁约束」四条未被强制

§13 末段（L1454）明写：「三类产物与 AEP 信封同样以 `docs/schemas/` 的版本化 Schema 为**唯一校验依据**」；§3.4（L863）进一步声称「`resolution: human_override` 的终局 vote_result **由 Schema 强制**（`docs/schemas/vote_result.schema.json`）」。这两句是**现在时的强声明**，可直接证伪。

**TEST 结果（§七脚本 2、3）**：

```
PRD §2.3 vote_result 示例（L285–352） vs docs/schemas/vote_result.schema.json -> FAIL (10)
   - ['resolution'] 'AUTO_WEIGHTED_CONSENSUS' is not one of ['automatic','human_override']
   - ['vote_breakdown'] 'approve' / 'reject' / 'abstain' is a required property   (×3)
   - ['input_artifacts',0..2] 'kind' / 'message_id' is a required property        (×6)

PRD §2.1 .dev.yml 示例（L161–211） vs docs/schemas/dev_manifest.schema.json -> FAIL (1)
   - ['development'] 'git' is a required property
```

`AUTO_WEIGHTED_CONSENSUS` 这个值在**全仓库只出现两次**：PRD L351 与提案 L287。它不在现行 Schema 枚举里，也不在 v2.5 目标枚举的任何定义中——即改完 Schema 之后它**仍然**是一个无定义的值。

**§2.2 互锁约束的实测（§七脚本 3）**——PRD §2.2（L264–270）以「**`vote` 与 `items` 的 Schema 条件互锁约束**」为题列了 5 条，并声明「不一致 ⟹ 判为**无效产物**」：

| PRD 声明的约束 | 现行 Schema 实测 |
|---|---|
| 存在 BLOCKING ⟹ vote 必为 NO_APPROVE | **接受（未强制）** |
| YES_APPROVE ⟹ 不得含 BLOCKING | **接受（未强制）** |
| NO_APPROVE ⟹ 至少一条 BLOCKING | **接受（未强制）** |
| ABSTAIN ⟹ items 为空且 abstain_reason 非空 | **接受（未强制）**（两种违例均通过） |
| （PRD **未**声明）status ↔ vote 一致性 | **拒绝（已强制）** |

即：**PRD 规定的四条没有被强制，被强制的那条 PRD 没有写。**且清单 §2.1 的 `review_manifest.schema.json` 变更计划只覆盖其中第 1 条（「存在 BLOCKING 则 vote 必为 NO_APPROVE」）与 `abstain_reason` 必填——**按清单实施完 Phase 1，第 2、3 条与「ABSTAIN ⟹ items 为空」仍无强制**，而现存的 status↔vote 强制的去留（`opinion.status` 双词表是保留还是废止）在整个 v2.5 文档体系里**没有裁定**（P2-9）。

**说明我为什么把它判 P1 而不是「Schema 本来就要在 Phase 1 改」**：Schema 落后于设计是正常的，写「将改为」也是正常的。问题在于 PRD 用**现在时**断言了两条具体的强制事实（L1454「唯一校验依据」、L863「由 Schema 强制」），而两条在本 commit 都为假；GUIDELINES §9-C 要求确定性语言必须区分「设计目标」与「已验证事实」。PRD 在 L686 对置信度做到了这一点，在这两处没有做到。

**验收标准**：L1454 / L863 改为标注目标态并指向清单条目；`AUTO_WEIGHTED_CONSENSUS` 要么进入 v2.5 `resolution` 枚举定义并写入 PRD 与 Schema，要么改用已定义值；§2.1 示例补 `development.git`；§2.2 五条互锁全部进入清单的 Schema 变更范围，并对 `opinion.status` 的存废给出裁定。

### P1-6　申请列为「已同步」的交叉文档未同步

| 交付物 | 申请声明 | 实际（本轮实测） |
|---|---|---|
| `PRODUCT-FACTS.md` F-20 | §2 item 6「22 条完整作为设计约束」；提案 §9.2「F-20 解析为独立 disposition」 | L47 原文未动，仍为「**具体采用同一文件的分区写入还是独立产物必须由后续规范显式裁定**」。该文件自身规则要求「与现行规范不一致时必须通过显式变更提案完成迁移，**不得把冲突静默解释为已经落地**」 |
| `FAQ.md` Q12 | §2 item 5「更新 Q11/Q12/Q14/Q15」 | `CONSENSUS_CHECK` 行仍为「执行者：等计票结果 / 编排器：加权决策表；僵局问管理员」，无 `SHOULD_DISPOSE`；`CODING/REWORK` 行仍写「返工时读意见并**筛选采纳**」（v2.5 应为按上轮 FINAL disposition 返工） |
| `FAQ.md` Q13 | 与 Q15 写者边界一致 | 仍写执行者「**汇总**问题清单、正文索引、哪些专家发现」——`issues_index` 在 UC-5 §2.c-2 与 Q15 同一文件里归 Orchestrator 原样拼接。同一份 FAQ 内两问归属相反 |
| `FAQ.md` Q15 E4 条件 | — | 「全为 false 进 `MERGING`（E4）」漏了 `decision == APPROVED` 前提与「无未豁免 BLOCKING」子句；照此 `REWORK_REQUIRED` + 全 false 会进 `MERGING`，与 §3.3 E5 互斥 |
| `UC5-consensus-tally.md` | §2 item 8「明确五重门禁与不可变单一写入」 | 主路径确已 v2.5 化（见 §二）；但文件头「关联：PRD **v2.4**」；前置条件 P2「有效票 ≥ `minimum_quorum`」与本文件异常流 E2「席位尚未全部 accounted 不进 CONSENSUS_CHECK」**自相矛盾** |
| `UC1-init-glm.md` | §2 item 7「更新任务态调度与 role_view」 | h1/h2 已对齐（见 §二）；但 L80「意见筛选……写采纳清单（下轮 `.dev.yml` 或 `adoption.yml`）」与 D-2 独立 disposition 并存 |
| `UC7-human-override.md`（邻接交付物） | 提案 §9.2 要求 E7 关联 D-1 | 全文仍 v2.4：文件头「PRD **v2.4**」；L44「裁定产生终局 `vote_result.json`……DEADLOCK HOLD 期间**不存在**中间版 vote_result」；**L80 把它写成了验收标准**：「DEADLOCK HOLD 期间 `vote_result.json` 不存在；裁定后存在且 `resolution=human_override`」。E7 的验收标准与 D-1 完全相反 |
| `STATUS.md` | §2 item 10「完整记录评审履历与对账索引」 | 已登记本申请（L67），这点做到了；但 L66 记「**Gemini & Grok 批准实施**」，而 grok 上轮 `2026-09-01-review-2.5-2-grok.md` 原文机器票为 `NO_APPROVE`；L66 记「所有专家关切已在 PRD v2.5 正式版中 **100% 物理闭环**」，与 §一 三条 CONTRADICTED 冲突。我按 STATUS 自身治理规则做了全量对账：**登记了但文件不存在 —— 无；存在但未登记 —— `2026-09-01-review-result-0bc6247-grok.md`（1 份）** |

UC-7 这一条我判得比其他几条重：它是 GUIDELINES §6 反例库「1:1 僵局」「全弃权」的落点用例，其**验收标准**与权威基准的 D-1 互斥，意味着按 UC-7 写的测试会把正确实现判为失败。

**验收标准**：F-20 改为已裁定（或加显式 `SUPERSEDED-BY: D-2` 指针）；Q12 与 §14.2 逐行同值；Q13 的「汇总」改为「逐项处置」并把索引归 Orchestrator；Q15 E4 条件补全；UC-5 文件头与 P2 改口径；UC-1 L80 删除 `adoption.yml` 分支；UC-7 按 D-1 重写含验收标准；STATUS 更正 L66 票型与「100% 物理闭环」措辞，并登记 grok 报告。

### P1-7　代码变更清单不能作为实施准入图：10 条目标路径在仓库不存在

申请 §5 要求「批准进入 Phase 1~5 代码实施阶段」，路线图即 `docs/v2.5_CODE_CHANGE_INVENTORY.md`。逐条 `test -f` 实测：

| 清单路径 | 存在 | 仓库实情 |
|---|---|---|
| `src/macao/workflow/state.py` | ✗ | `workflow/` 下为 `fsm.py` / `state_engine.py` 等 |
| `src/macao/workflow/override.py` | ✗ | override 逻辑在 `orchestrator.py` 与 `cli/main.py` |
| `src/macao/git/evidence.py` | ✗ | **无 `git/` 包** |
| `src/macao/git/merge.py` | ✗ | 实为 `src/macao/merge/controller.py` |
| `src/macao/git/worktree.py` | ✗ | 实为 `src/macao/utils/git_utils.py` |
| `src/macao/cli/commands/{init,doctor,reconcile,reviews,status}.py` | ✗ ×5 | **无 `cli/commands/` 包**，实为 `cli/main.py` |
| `docs/schemas/aep_message.schema.json` | ✗ | 实为 `docs/schemas/aep_envelope.schema.json`（PRD L1454 也称「AEP 信封」） |

存在的有：`core/schema.py`、`core/config.py`、`consensus/vote.py`、`consensus/engine.py`、`cli/main.py`、`docs/schemas/{dev_manifest,review_manifest,vote_result,review_context}.schema.json`。

清单把这 10 条全部标为「**变更**」（而非「新建」），按此实施会在既有模块树旁平行长出第二套目录，且新旧两套 FSM 并存——正好复现 P0-1 的形态。

另：清单 §2.1 对 `vote_result.schema.json` 标「重构 (v2.0)」，但未把**破坏性迁移**列出——现行枚举 `["APPROVED","REWORK_REQUIRED","RETRY_REVIEW","CANCELLED"]` 需删 `RETRY_REVIEW` / `CANCELLED` 两值、增 `DEADLOCK`，并处理 `resolution` 枚举与 `vote_breakdown` 字段改名（`approve`→`approve_seats`/`approve_weight`）。存量产物与 fixtures 的迁移未提及。

**验收标准**：每个「变更」行指向现存文件或明确标「新建」；补 `vote_result` 枚举与 `vote_breakdown` 字段的破坏性迁移条目及存量 fixtures 处理；字段名与 P1-1 的唯一信封一致。

### P1-8　缺失章节：§14.5 与「第十五部分」被 8 处引用，实体不存在

`grep '^## 第'` 结果显示 PRD 章节序列为 …第十四部分 → **第十六部分**…；第十四部分只有 14.1 与 14.2。

**§14.5（Merge Policy）被引用 4 次**：§3.3 E4 伴随动作（L791，「§14.5：检出 → pre-merge evidence push 校验 → merge → CI gate → 人工签字 → push」）、§13 `rebase_before_merge` 注释（L1433）、§14.1 步骤 6（L1469）、§14.2 合并签字行（L1483）。E4 的伴随动作——即 `MERGING` 状态内部的全部规范——**没有落点**。

**「第十五部分」被引用 4 次**：§3.2 伪代码内 `# → E7 人工裁定（§15.2）`（L740）、§9.1 风险表（L1201）、§11.1 组件图 Usage Meter（L1246）、§13 `usage_metering`（L1444）。UC-6 文件头亦引用「PRD v2.5 §15.2（返工策略）」。

`docs/EXECUTIVE_SUMMARY.md` L285 记载第十五部分原为「边界声明与非功能需求含安全/成本/评审质量评测」——可见该章在某次编辑中被移除而引用未清理。§3.2 从「唯一规范入口」里指向 §15.2 作为人工裁定的规范落点，这一指针是断的。

**验收标准**：恢复或重编号这两处；全文交叉引用做一次可脚本化的存在性核验（`grep -o '§1[0-9]\.[0-9]'` 与实际标题集合求差）。

---

## 五、P2：登记，回写时必须处理

| ID | 问题 | 证据 |
|---|---|---|
| **P2-1** | §17.2 ReviewExtractor「若仅有 `opinion.status` 则**自动对齐 `vote`**，**自动补齐 `checkpoint_ref` 与 `review_round`**」与 P-1 零语义创作、F-12（确定性规则不得改写机器决策）、F-13（Orchestrator **原样提取**票面）互斥；更直接的是与 §3.2 行为约定 4（「`.review.yml` 必须校验 `checkpoint_ref` 与 `review_round` **双匹配**」）互斥——无法对自己补齐的字段做双匹配校验 | L1649 vs L777 |
| **P2-2** | §18 守护进程「超时自动降级……**确定性推进**：自动触发共识仲裁，推动状态机进入 `CONSENSUS_CHECK` (HOLD) 并生成 `HUMAN_OVERRIDE_REQUEST`」把「超时 ⟹ HOLD + 人工」写成无条件。N=3、1 超时 + 2 赞成时，§2.3 门禁全过应为 `APPROVED`，二者互斥 | L1656–1657 vs L358–367 |
| **P2-3** | §4.1 MVP 范围（8 项 P0）与 §4.2 分期交付计划（Week 1-8）**完全不含** v2.5 任何内容：无 disposition、无加权共识（L877 仍写「2/3 多数投票」）、无 evidence ref、无 `role_view`、无 `doctor/reconcile/adopt`；L885 还把「Multi-Reviewer Consensus 高级算法」列为**不做 (P1+)**。与清单 §3「Phase 1–5 / Day 1–7」并存两套互斥交付计划，而申请正是要批准后者 | L872–887、L889–920 vs 清单 §3 |
| **P2-4** | §19 声明 `opencode`/`agy`/`agent` 可任意组合角色、`model:` 可在 `macao.yaml` 声明；§13 `security.allowed_clis` 仍为三项且无 `model` 键（见 P1-3） | L1663–1664 vs L1447 |
| **P2-5** | worktree 路径 **6 种写法**：`.macao/worktrees/kimi/r1`（L455）、`.macao/worktrees/codex/task-1/r1`（L957）、`.macao/worktrees/<reviewer_id>`（L1031）、`.macao/worktrees/<task_id>/<reviewer_id>`（L1643，**层级顺序相反**）、`.macao/worktrees/<reviewer>/<task>/r<round>`（FAQ L245）、`.macao/worktrees/<agent_id>/<task_id>/r<round>`（UC-4 L32）。GUIDELINES §5 禁止同一实体多套路径 | — |
| **P2-6** | 悬空交叉引用「§2.3 决策表」×2（L1121 §6.2、L855 §3.4 场景三「第 4 行」）——§2.3 在 v2.5 已改为五重门禁公式，无决策表、无行号 | L1121、L855 |
| **P2-7** | 两份互斥的版本演进记录：「## 附录：版本演进记录」（L1520，含「v2.5（现行权威基准）」）与文末「**版本历史**」（L1673–1685，止于 v2.4，**从未提及 v2.5**），而文档标题为 v2.5。且「附录」被物理插在 §16.1 与 §16.2 之间，切断第十六部分 | L1520、L1673 |
| **P2-8** | 文末版本历史 L1685 记 v2.4「（**达成 L4 RELEASE-READY / PG-3 规格**）」。`docs/reviews/STATUS.md`（本申请交付物 #10）记当前定级为「维持 L3 SCENARIO-VERIFIED / PG-2」，L4/PG-3 尚在复审中。权威基准记录了一个未被授予的门禁——GUIDELINES §9-B | L1685 vs STATUS L8 |
| **P2-9** | `.review.yml` 双词表未裁定：`opinion.status`（`APPROVED\|CHANGES_REQUESTED\|REJECTED\|ABSTAINED`）与 `vote`（`YES_APPROVE\|NO_APPROVE\|ABSTAIN`）并存；`ABSTAINED` vs `ABSTAIN` 同义异形。互锁约束只绑 `vote`↔`items`，未定义 `status` 与 `vote` 冲突时谁胜（而现行 Schema 恰恰强制了这一条，见 P1-5） | L228、L260 |
| **P2-10** | §1.1 工作流程图**物理断裂**：L84–88 与 L96–101 两个「PHASE 3: REVIEWER WORK」重复块，其间 L93–94 为一个只有顶边、无内容无底边的空框。GUIDELINES §9-D（代码块/图示可用性） | L84–101 |

---

## 六、P3：可延期

| ID | 问题 | 证据 |
|---|---|---|
| P3-1 | §5.3 Step 5 代码块不可执行：`cat > .macao/.reviews/<reviewer_id>.review.yml <<EOF` 中 `<` 在 shell 中是重定向符，直接粘贴报语法错误；同段 `git worktree add .macao/worktrees/<reviewer_id> <head_commit>` 同理。GUIDELINES §9-D | L1031、L1050 |
| P3-2 | `docs/SRSv1.md` L7–L18 blockquote 内表格结构不闭合（表头行带 `>`，其后 12 行不带，随后以 `>` 恢复）。**渲染后果未实测**（本机无 GFM 渲染器），仅登记结构事实 | SRS L7–L18 |
| P3-3 | `docs/SRSv1.md` L5 正文写「已在 **v2.0**（`MACAO_PRD_v2.md`，权威基准）中更新」，而其下表格列头写「v2.5 调整」 | SRS L5 |
| P3-4 | §5.4 与 §5.3 顺序倒置（§5.4 在 L1007，§5.3 在 L1020） | — |
| P3-5 | UC-5 §7「实现落点」表 `src/macao/core/config.py` 与 `tests/` 两行**重复出现**；PRD 示例日期混用 `2024-01-15` 与 `2026-09-01` | UC-5 §7 |

---

## 七、反例与边界场景推演（GUIDELINES §6 全量）

对方法论点名的 11 个场景逐一推演「预期结果能否从文档**唯一**推出」：

| # | 场景 | 可唯一推出 | 依据 / 阻断点 |
|---|---|---|---|
| 1 | 2-reviewer 全部弃权 | **否** | 门禁 2：$E_N=0 \ge \lceil4/3\rceil=2$ ✗ → `DEADLOCK`（§2.3 规则 6、UC-5 A2 一致）。但此后落盘与否由 P0-1 阻断；且 §3.2 Layer 1b 的 `count_valid` 是否含 ABSTAIN 未定义 |
| 2 | 2-reviewer 1 超时 + 1 批准 | **部分** | N=2 时 §6.2 降级路径与门禁计算一致（→ DEADLOCK）✓；但 N=3、1 超时 + 2 赞成时 §18（L1657）无条件 HOLD 与门禁结果 `APPROVED` 互斥（P2-2） |
| 3 | 2-reviewer 1:1 僵局 | **否** | P0-1 决定性阻断，三条路径三种结果（见 §三 表） |
| 4 | 3-reviewer 1:1:1 | **否** | 门禁计算可推（$E_N=2$✓、$E_W=2\ge2$✓、门禁 4 $3\times1=3\ge2\times2=4$✗、门禁 5 胜方席位 $1<2$✗ → `DEADLOCK`）；落盘同 #3 阻断 |
| 5 | Reviewer 崩溃重启后重复提交投票 | **否** | 全 PRD 的幂等去重只定义在 **AEP 消息层**（L1331「消费端以 `message_id` 幂等去重」、L1346 `ack(message_id)`），**产物层无去重规则**。§2.2 路径 `.macao/.reviews/<reviewer_id>.review.yml` 每 reviewer 单文件，重投即覆盖；新 `message_id` 可绕过消息层去重。UC-5 P3 把去重委派给 UC-4 f1–f4（不在本申请交付物清单内） |
| 6 | 同一 checkpoint 两份同 reviewer_id 的 `.review.yml` | **否** | 同 #5 |
| 7 | `.dev.yml` 缺必需字段但 `signal=EXPLICIT` | **否** | L211 注释「显式信号，MACAO **强制认可**」vs §3.2 Layer 1a `load_and_validate(..., DEV_YML_SCHEMA)` 校验失败即不转移。`signal` 字段在全 PRD 仅此一次出现，无规范条文界定其与 Schema 校验的优先级。另：该示例本身对现行 `dev_manifest.schema.json` 校验失败（缺 `development.git`，P1-5） |
| 8 | 第二轮返工时 `.review.yml` 是否覆盖第一轮 | **是** ✓ | §3.4 生命周期表 + 场景推演二步骤 6：r1 产物在 r2 前已提升至 `refs/macao/evidence/<task>/r1`，同名覆盖不破坏审计链 |
| 9 | 人工接管超时后系统默认动作 | **部分** | §6.1 总则（L1110）对**已登记的 6 类**触发器唯一可推（HOLD + 持续告警，不静默推进）✓；对 v2.5 新增的 disposition 超时与 `NEEDS_ADMIN` 不可推（P1-4） |
| 10 | Git 冲突导致 checkpoint 与工作区不一致 | **是** ✓ | §3.3 E4a 硬校验「最终 push 对象 == `vote_result.json.checkpoint_ref`」+ §6.1 Git conflict 触发器 + E4b 回退路径，三者闭合 |
| 11 | `review_context` 的 diff/patch 字段与 Reviewer 工作流期望载体不一致 | **否** | **P0-2**：§5.2 扁平 vs §2.4/§5.3/Schema 嵌套；实测 7 项 Draft-07 校验失败 |

**11 个场景：唯一可推出 2、部分 2、不可推出 7。** GUIDELINES §2.1 对 L1 的门槛虽低于 L3，但 §3.3 要求 DOC/SPEC 为 VERIFIED 且「交叉引用不矛盾」；第 3、11 两条不可推出的直接成因是同一份权威基准的自相矛盾，不是尚未展开的细节。

**追加推演（v2.5 新引入，方法论未列但必须查）——「场景推演二能否满足 E6」**：§3.4 场景推演二（L836–850）步骤 5–7 为「`vote_result`(REWORK_REQUIRED) → 发 `REWORK_REQUEST` → Claude 修复后生成新 `.dev.yml` → E6」。但 §3.3 E6（L796）要求「**前一轮 FINAL disposition 已覆盖全部 issue**」；`REWORK_REQUIRED` 蕴含存在 BLOCKING issue，故 `requires_disposition=true`。场景二**从未出现 disposition 步骤**，按 E6 守卫将永久停在 `REWORK`。§3.4 的场景推演与 §3.3 的守卫不同步——与 P0-1 同源。

### 复现脚本

```bash
cd /path/to/macao && python3 - <<'PY'
import json, yaml, jsonschema
# 脚本 1：PRD §5.2「唯一权威完整模型」 vs 它自己指定的机器契约
schema = json.load(open('docs/schemas/review_context.schema.json'))
inst = {  # 按 PRD L937-1000 逐字构造
 "repository":{"workspace_path":".macao/worktrees/codex/task-1/r1","remote_name":"origin",
               "fetch_policy":"fetch_source_and_evidence_before_diff"},
 "dev_checkpoint":{"base_commit":"b2c3d4e","head_commit":"a1b2c3d","review_round":1},
 "evidence":{"ref":"refs/macao/evidence/task-1/r1","commit":"e5f6a7b"},
 "task_info":{"source":"review_request","path":"docs/reviews/x.md","commit":"e5f6a7b","sha256":"x"},
 "code_changes":{"base_commit":"b2c3d4e","head_commit":"a1b2c3d","diff_policy":"generate_locally"},
 "quality_snapshot":{"source":"evidence.dev_manifest"},
 "executor_self_assessment":{"source":"task_info","anchor":"#self-assessment"},
 "review_guidelines":{"path":"docs/MACAO_REVIEW_GUIDELINES.md","commit":"a1b2c3d","sha256":"x"},
 "history":[], "references":[]}
errs = sorted(jsonschema.Draft7Validator(schema).iter_errors(inst), key=lambda e: list(e.path))
print("脚本1 §5.2 ->", "PASS" if not errs else "FAIL(%d)" % len(errs))
for e in errs: print("   -", list(e.path), e.message[:120])

# 脚本 2：PRD 三份产物示例 vs docs/schemas/（PRD L1454 自称「唯一校验依据」）
lines = open('docs/MACAO_PRD_v2.md').read().split('\n')
def block(after, lang):
    for i, l in enumerate(lines):
        if i > after and l.strip() == '```' + lang:
            s = i + 1; e = s
            while lines[e].strip() != '```': e += 1
            return '\n'.join(lines[s:e])
for name, after, lang, sf, load in [
    ('§2.1 .dev.yml', 158, 'yaml', 'dev_manifest', yaml.safe_load),
    ('§2.2 .review.yml', 216, 'yaml', 'review_manifest', yaml.safe_load),
    ('§2.3 vote_result', 280, 'json', 'vote_result', json.loads)]:
    sch = json.load(open('docs/schemas/%s.schema.json' % sf))
    errs = sorted(jsonschema.Draft7Validator(sch).iter_errors(load(block(after, lang))),
                  key=lambda e: list(e.path))
    print("脚本2 %-18s -> %s" % (name, "PASS" if not errs else "FAIL(%d)" % len(errs)))
    for e in errs: print("   -", list(e.path), e.message[:120])

# 脚本 3：PRD §2.2 五条「Schema 条件互锁约束」是否真被强制
sch = json.load(open('docs/schemas/review_manifest.schema.json'))
V = jsonschema.Draft7Validator(sch)
def mk(vote, items, ar=None, st="APPROVED"):
    d = {"version":"1.0","timestamp":"2026-09-01T10:45:30Z","task_id":"task-1",
         "checkpoint_ref":"a1b2c3d","review_round":1,
         "reviewer":{"id":"codex","role":"reviewer","cli":"codex","version":"2.1.0"},
         "opinion":{"status":st,"confidence":0.9,"feedback_summary":"x"},
         "items":items,"vote":vote}
    if ar is not None: d["abstain_reason"] = ar
    return d
B = [{"issue_id":"codex/SEC-01","disposition_class":"BLOCKING","severity":"major","title":"t"}]
for name, inst in [
  ("互锁1 BLOCKING+YES_APPROVE 应拒", mk("YES_APPROVE", B)),
  ("互锁3 NO_APPROVE+空items 应拒",   mk("NO_APPROVE", [], st="CHANGES_REQUESTED")),
  ("互锁4 ABSTAIN+非空items 应拒",    mk("ABSTAIN", B, ar="x", st="ABSTAINED")),
  ("互锁4 ABSTAIN 缺 reason 应拒",    mk("ABSTAIN", [], st="ABSTAINED")),
  ("(未声明) status/vote 冲突 应拒",  mk("NO_APPROVE", B, st="APPROVED"))]:
    print("脚本3 %s %s" % ("拒绝OK  " if list(V.iter_errors(inst)) else "**接受✗**", name))
PY

# 脚本 4：清单路径存在性
for f in src/macao/workflow/state.py src/macao/workflow/override.py \
         src/macao/git/evidence.py src/macao/git/merge.py src/macao/git/worktree.py \
         src/macao/cli/commands/init.py src/macao/cli/commands/doctor.py \
         src/macao/cli/commands/reconcile.py src/macao/cli/commands/reviews.py \
         src/macao/cli/commands/status.py docs/schemas/aep_message.schema.json; do
  [ -f "$f" ] && echo "EXISTS  $f" || echo "MISSING $f"
done
```

---

## 八、交叉文档需做的文字修订（最小闭环）

1. **只改 PRD §3.3 不够**：必须让 §1.1 流程图、§3.2 伪代码、§3.4 三个场景推演、§6.1 触发器、§16.2 阶段表成为 §3.3 的**同一张表的五个投影**。这是 P0-1 的完整边界，也是本轮唯一的 P0 级返工量。
2. **`review_disposition` 唯一信封写进 PRD 第二部分**，再回写 UC-6、FAQ Q15、清单、Schema；`DRAFT` / `PENDING_ADMIN` 二选一。
3. **AEP 补第 8 段示例**、统一 `protocol` 与 Type 字母、清掉三处 `content_base64` 与 Type D 的 `description`。
4. **§13 补齐 v2.5 全部配置面**（`vote_weight` / 独裁帽 / `minimum_winning_seats` / `timeouts.review_disposition` / `aep.max_message_bytes` / `consensus_rule` / `model` / `allowed_clis`）——这是 Grok P1-1 与 Gemini P1-1 真正的落点。
5. **F-20 结案**；**UC-7 按 D-1 重写含验收标准**；**FAQ Q12/Q13** 与 §14.2/UC-5 同向。
6. **§5.2 改嵌套并与 `review_context.schema.json` 对齐**（P0-2）。
7. **清单对齐现存模块树**，并补 `vote_result` 枚举/字段的破坏性迁移条目。
8. **恢复或重编号 §14.5 与第十五部分**，清理 8 处悬空引用；合并两份版本演进记录；修正 L1685 未授予的 PG-3 记录。
9. **STATUS.md**：更正 L66 grok 票型与「100% 物理闭环」，登记 `2026-09-01-review-result-0bc6247-grok.md`。

---

## 九、建议的闭环顺序与验收标准

| 序 | 事项 | 验收标准（可机器核验部分已给脚本） |
|---|---|---|
| 1 | P0-1 | 按 GUIDELINES §6 手工重放「1:1 僵局」「全弃权」「APPROVED + 未处置 ADVISORY」「处置超时后 E7 APPROVED」四条，每步**只能命中 §3.3 一行**；§3.2/§3.4/§1.1/§16.2 无反向句子 |
| 2 | P0-2 | §七脚本 1 输出 `PASS`；`grep -n 'code_changes' docs/ -r` 全部为嵌套 `refs.*` 形式；三处块数一致 |
| 3 | P1-1 | PRD 出现 `### 2.5 review_disposition`；`grep -n 'disposition_status\|disposition_type\|PENDING_ADMIN\|artifact_revision\|executor.disposition\|review_disposition' docs/ -r` 中文件名与字段名各只剩一套 |
| 4 | P1-5 | §七脚本 2 三行全 `PASS`；脚本 3 前四行全 `拒绝OK`（或 PRD 明确标注为目标态并指向清单条目） |
| 5 | P1-2、P1-3、P1-4 | 8 段 AEP 示例齐备且 `protocol` 一致；§13 上表 8 项齐备；§6.1 触发器含 disposition 超时与 `NEEDS_ADMIN` |
| 6 | P1-6、P1-7、P1-8 | 申请 §3 每一行可指到 PRD/UC 具体行号且无反向句；§七脚本 4 全 `EXISTS` 或清单标「新建」；悬空章节引用清零 |
| 7 | 复评 L1 / PG-0 | 上述闭合后重新申请。期间现行实现与 v2.3.1 行为不变 |

**不建议**：以 STATUS「100% 物理闭环」、提案 DRAFT v0.3 文首「完备闭环稿」或本轮申请 §4「验证与一致性自检」代替正文核验——这三处的自述与正文实测均不一致（§一）。也不建议在 §3.2 Layer 1c 仍直跳 `MERGING` 的情况下启动 Phase 1 Schema 与计票编码。

---

## 十、与其他 Reviewer 的交叉核对（GUIDELINES §8）

本轮我读到 `docs/reviews/2026-09-01-review-result-0bc6247-grok.md`（同一 commit，未被 STATUS 登记）。按「真理不等于投票」，凡采纳者均先自行复现：

**独立复现后确认一致**（结论相同，行号与推演均为我自行核验）：grok P0-1（§3.2/§3.4 vs §3.3）、P1-1（disposition 契约分裂）、P1-2 中的 F-20 / FAQ Q12·Q13 / §6.1 / UC-7 / STATUS 六项、P1-3（AEP 8 vs 7、Type G/H、缺示例、`AEP/1.0`）、P1-4（清单路径）、P2-2（`status`/`vote` 双词表）、P2-3（UC-1 `adoption.yml`）、P2-5（UC-5 头部与 P2 自相矛盾）。

**我补充的、grok 未登记的独立发现**：
1. **P0-2 §5.2 与其自称机器契约的 7 项 Draft-07 校验失败**——grok 报告了 disposition 契约分裂，未对 `review_context` 做契约实测，也未指出 §2.4 与 §5.2 各自声明了互斥的「唯一权威路径」；
2. **P1-5 §2.3 示例 10 项校验失败 + §2.2 五条互锁四条未被强制**——两条 PRD 现在时强声明（L1454、L863）被证伪；
3. **P1-3 §13 配置章节整体未升级**——grok 指出 §6.1 缺 `timeouts.review_disposition`，我进一步确认**定义配置项的唯一章节里也没有该键**，加权共识（`vote_weight`/独裁帽/`minimum_winning_seats`）同样无配置面；
4. **P1-8 §14.5 与第十五部分缺失（8 处悬空引用）**，含 §3.2 伪代码自引 §15.2、UC-6 头部引用 §15.2，成因见 `EXECUTIVE_SUMMARY.md` L285；
5. **P2-1/P2-2/P2-4 第十七～二十部分未纳入 v2.5 收敛**——§17.2 自愈器的「自动对齐 vote / 自动补齐 `checkpoint_ref`·`review_round`」与 P-1 零语义创作及 §3.2 双匹配校验互斥；§18 无条件 HOLD 与门禁互斥；§19/§20 与 §13 互斥。grok 报告未覆盖这四章；
6. **P2-3 §4.1/§4.2 MVP 范围与交付计划仍为 v2.0**，与清单 Phase 1–5 并存两套互斥计划；
7. **P2-7/P2-8 两份互斥版本演进记录，且 L1685 记录了未被授予的 L4/PG-3**（与本申请交付物 STATUS.md 冲突）；
8. **P2-10 §1.1 流程图物理断裂**（重复块 + 空框）；
9. **§六 反例库第 5/6 条（重复投票去重）不可唯一推出**——去重只定义在 AEP `message_id` 层，产物层无规则；
10. **§六 追加推演：场景推演二无法满足 E6 守卫**。

**我未采纳 / 未提出的**：grok P2-7（提案 §7.2 YYN 公式叙述误用）我复算后确认结果正确、叙述可改，属提案文本而非本轮定级分子，不单列。我原拟提出的 §6.2「弃权票不计入分母」矛盾经复核**不成立**，已在 §0 撤回。

**票型**：`claude` = `NO_APPROVE`；`grok` = `NO_APPROVE`。两份报告在 P0 上独立收敛于同一处（§3.2/§3.4 vs §3.3）。按 GUIDELINES §8「沉默 ≠ 同意」，Codex / Gemini / Kimi / Qwen / ZCode / GLM 本轮尚未出具报告，不计入任何一方。

---

## 附：机器票与结构化 issue 清单

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/P0-1` | critical | `BLOCKING` | §3.2 唯一规范入口与 §3.4 场景三仍为 v2.3.1，与同文件 §3.3 / D-1 / E4 / E5a 互斥，v2.5 状态机不可唯一推出 |
| `claude/P0-2` | critical | `BLOCKING` | §5.2「唯一权威完整模型」与其指定的 `review_context.schema.json` 互斥（实测 7 项失败）；§2.4 与 §5.2 各声明互斥的「唯一权威路径」 |
| `claude/P1-1` | major | `BLOCKING` | `review_disposition` 无 PRD §2.x 契约；4 套文件名、2 套字段名、`DRAFT`/`PENDING_ADMIN` 语义空洞 |
| `claude/P1-2` | major | `BLOCKING` | AEP/1.1 声明 8 类实给 7 类、缺 `DISPOSITION_REQUIRED` 示例、示例版本号全为 1.0、Type G/H 冲突、三处 `content_base64` 违反 16 KiB 与 F-14、Type D 保留已废止的代写字段 |
| `claude/P1-3` | major | `BLOCKING` | §13 单一事实源未升级：`vote_weight` / 独裁帽 / `minimum_winning_seats` / `timeouts.review_disposition` / `aep.max_message_bytes` / `model` 全缺，`consensus_rule` 仍为 `2/3_majority` |
| `claude/P1-4` | major | `BLOCKING` | §6.1 触发器缺 disposition 超时与 `NEEDS_ADMIN`，缺 `EXTEND`；三份文档同时指向该不存在的落点 |
| `claude/P1-5` | major | `BLOCKING` | PRD 现在时强声明「唯一校验依据」「由 Schema 强制」被证伪：`vote_result` 示例 10 项失败、`AUTO_WEIGHTED_CONSENSUS` 无定义、§2.2 五条互锁四条未被强制且清单只计划补两条 |
| `claude/P1-6` | major | `BLOCKING` | F-20 / FAQ Q12·Q13·Q15 / UC-5 头部与 P2 / UC-1 `adoption.yml` / UC-7 验收标准 / STATUS 票型与「100% 闭环」未同步 |
| `claude/P1-7` | major | `BLOCKING` | 清单 10 条目标路径在仓库不存在且标为「变更」；`vote_result` 枚举与字段的破坏性迁移未列 |
| `claude/P1-8` | major | `BLOCKING` | §14.5 与第十五部分被 8 处引用但实体不存在，E4 合并流水线规范无落点 |
| `claude/P2-1`…`P2-10` | minor | `ADVISORY` | 见 §五 |
| `claude/P3-1`…`P3-5` | trivial | `ADVISORY` | 见 §六（P3 表） |

```
vote: NO_APPROVE
requires_new_checkpoint: true   # 本轮为文档体系返工，需产生新的文档 checkpoint 后重新送审
```
