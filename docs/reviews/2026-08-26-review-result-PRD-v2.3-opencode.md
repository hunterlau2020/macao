# MACAO PRD v2.3 独立复审结论（L1 DOC-ALIGNED 申请）

- **评审日期**：2026-08-26
- **评审角色**：opencode
- **评审对象**：`docs/MACAO_PRD_v2.md` v2.3 及配套（`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/schemas/*`（6 Schema + 9 fixtures）、`docs/README.md`、`docs/reviews/STATUS.md`）
- **评审依据**：`docs/reviews/2026-08-26-review-request-PRD-v2.3.md`（申请目标 L1 DOC-ALIGNED / PG-0）；方法按 `docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11
- **证据类型**：DOC/SPEC（全部给出路径+行号）+ SIM（场景推演）+ 机器校验（53 项，见附录）
- **commit 说明**：评审环境无 git，无法捕获 hash；以 2026-08-26 工作区状态为准（申请方合入 main 后应在本文件补记 hash）
- **结论**：**未达 L1 DOC-ALIGNED / PG-0，维持 PENDING_REVIEW**。

## 结论摘要（为什么未授予 L1）

申请所列上一轮闭环对象——`8ab9be7` 的 **kimi / opencode 两份评审**——其 P0/P1 **全部确认已关闭**（见下节，含 53 项机器校验全过）。但 `docs/reviews/` 目录中同一 commit `8ab9be7` 实际存在 **五份**评审报告，`STATUS.md` 与复审申请只登记并闭环了其中两份；**codex / claude / gemini 三份评审未进入闭环跟踪**，经本轮逐条对当前 v2.3 文本复核，其中 **2 个 P0 与 2 个 P1 仍然成立**（另 1 个 P0、1 个 P1 已被 v2.3 顺带关闭）。按 Guidelines §8（"真理不等于投票：每项 REJECT/P0/P1 必须附可复现证据"；"沉默 ≠ 同意"），这些带有效证据的未处理 P0/P1 阻止 L1 宣告。

---

## 已对齐 / 已确认项

### 1. kimi / opencode（8ab9be7）上轮发现逐条复核：全部关闭

| 来源 | 发现 | 复核结果（证据） |
|---|---|---|
| kimi P0-1 / opencode P1-3 | review_context 双结构并存 | **已关闭**。§5.2 为唯一权威完整模型（`MACAO_PRD_v2.md:952-1035`，两传输块+六语义块）；§2.4 Type B（L491-545）为其最小子集，顶层 8 键名与嵌套路径与 §5.2 完全一致（逐键比对：dev_checkpoint/repository/task_info/code_changes/quality_snapshot/executor_self_assessment/history/references）；`review_context.schema.json` 同时接受最小/完整两种形态（机验：fixtures minimal/full、§2.4 Type B payload、§5.2 示例、IMPROVEMENT 示例 5 例全过；缺 refs 反例被正确拒绝） |
| opencode P1-1 | §6.1 触发条件 1 残留 Layer 2 阈值 | **已关闭**。`MACAO_PRD_v2.md:1090` 改为 Layer 3 置信度 <0.7 + E8 口径，并注明 Layer 2 永不触发接管 |
| opencode P1-2 | §1.1/§1.2 与 FSM 不同步 | **已关闭**。§1.1 图补 MERGING（L103-113）+ 简化视图说明（L117）；§1.2 CONSENSUS/MERGE 行补 E4/E4a/E4b/E5/E6/E7/E9/E10（L129-130）；`docs/README.md:24` 行同步 |
| opencode P1-4 | Deadlock 终局表达 / Layer 1c 静默 else / 枚举不一致 / CANCEL 无终态 | **核心已关闭**。E7 裁定结果落盘终局 vote_result（`resolution: human_override`，L831；Schema `vote_result.schema.json:52` 有该枚举）；Layer 1c 显式两分支+注释（L778-782）；override 枚举统一 APPROVED/REWORK/RETRY_REVIEW/CANCEL（L831/L1476）；新增 E9（L832）/E10（L833）与 CANCELLED 终态，FSM 10 态（L837）。残余见 P2-1/P2-2 |
| kimi P1-1/2/3 | EXEC 三示例不过 Schema | **已关闭**。机验 PASS：EXEC `.dev.yml`/`.review.yml`/`vote_result.json`（L126-155/L161-186/L192-209）分别过对应 Schema |
| kimi P1-4/P1-5 | 计划类 ✅ 无证据；字段类型非法 | **已关闭**。IMPROVEMENT_SUMMARY L343-347 改【计划】、L408-410 待验证、L486-491 改 `[ ]` 并注明"未达成前不得勾选"；quality_snapshot 整数化（L199）。残余（PRD §10）见 P2-5 |
| 双方 P2/P3 | Type D round、Type F attachments、KPI 分母、timeouts 注释、占位符、标题、速写对齐、500%、fixtures 宣称 | **均已落文**：Type D `round: 2` + 语义注（L428/L607）；Type F attachments + δ2 注（L661-663/L668）；KPI 分母排除命令型转移（L1190）；timeouts 注释（L1445-1446）；`<reviewer_id>` 占位符（L1066）；PRD 标题 v2.3（L1）；速写对齐注（EXECUTIVE_SUMMARY.md:94）；`schemas/README.md:19` 覆盖面如实 |

### 2. 申请方重点核查项（申请 §三）

| # | 核查项 | 结果 |
|---|---|---|
| 1 | review_context 单一结构 | **VERIFIED**（同上，逐键一致 + 机验 5 例全过） |
| 2 | Deadlock 流程唯一性 | **PARTIALLY_VERIFIED**：S3（1:1 → 裁定 APPROVED）、S4（弃权+反对 → 降级 → 裁定 REWORK）、S6（RETRY_REVIEW/CANCEL）可从 §2.3(L399)+§3.3(E3'/E7/E9/E10)+§6.1(L1101-1104)+Layer 1c 注释唯一推导（本评审独立重放）；**例外**：`--choice CANCEL` 的转移落位不可唯一推导（P2-1），max_rework_rounds 轮的伪代码分支与 E5/E7 不一致（P2-2） |
| 3 | 10 态 FSM 一致性 | **PARTIALLY_VERIFIED**：§1.1/§1.2/§3.3/EXEC(L267)/README(L24) 一致；**例外**：§11.4 DDL 注释"9 态之一"（P2-3）、§16.1"E1~E8"（P3-4） |
| 4 | 摘要文档示例过 Schema | **VERIFIED**（机验 53/53，含 EXEC 三例与 IMPROVEMENT context 例） |

### 3. 同 commit 未跟踪三份评审（codex/claude/gemini）中已被 v2.3 顺带关闭的项

| 来源 | 发现 | 复核结果 |
|---|---|---|
| claude P0 / gemini P0-3 | Deadlock 无法表达、Layer 1c 二元误判、缺入口边 | **已关闭（设计改法）**：v2.3 采纳"先人工裁定、后写终局 decision（resolution=human_override）"路径，E7 即 Deadlock 的出口边，CONSENSUS_CHECK 停留期由 §6.1 超时总则（L1127）HOLD 兜底；可唯一推导（见上表#2）。验收建议残余（§3.4 推演回填、fixture）→ P2-9 |
| codex P1-4 / gemini P1-4 | 审计永久保留 vs retention_days=90 未分类 | **已关闭**：§14.3（`MACAO_PRD_v2.md:1494`）区分 terminal logs（90 天滚动）与 audit events（永久） |
| codex P2 | §16.4 hosts 段不受当前 Schema 校验未注明 | **已关闭**：L1640 标注"扩展草案，v1.1 实现" |

---

## P0：必须先解决

**P0-1 clean rebase 豁免破坏"评审对象 = 合并对象"的 checkpoint 绑定（sustained：codex P0-1 / claude 复核确认 / gemini P0-1，v2.3 未处理）**
- 证据：`MACAO_PRD_v2.md:1504`（§14.5 步 1）"由 Executor 自动 rebase 并重跑本地验证——**rebase 仅改变 commit 哈希、不触发新一轮评审**"；而 §3.2/§3.3 以 `checkpoint_ref + review_round` 为受理作用域（L744-746、L824-830），`.review.yml`/`vote_result.json` 绑定的是 rebase 前的 hash；E4a（L827）完成条件不含"最终 push 对象 == checkpoint_ref"的硬校验。
- 影响：被批准对象与进入 target 的对象在哈希层面断裂，违反 §2.3 审计链承诺（L415）与 §16.2"round + checkpoint_ref 双匹配"原则；上游变更可通过 rebase 通道不经评审合入。
- 修复（二选一，写入 E4a 硬校验）：① 严格模式——rebase 产生任何新 hash 即 E4b 重审；② 受控门禁——`git range-diff` 无内容差异 + `rebased_from` 元数据入 vote_result/审计 + CI gate 与人工签字在 rebase 后新 commit 上重跑记录。

**P0-2 Reviewer worktree 强制安全边界被 §16.3 与 Type B 示例削弱为"可选/主工作区"（sustained：codex P0-2 / gemini P0-2，v2.3 未处理）**
- 证据：§12.2（`MACAO_PRD_v2.md:1378`）"MVP 阶段强制 `sandboxed` + 独立 worktree"；§5.3（L1046-1049）MACAO 为每个 Reviewer 创建 worktree 并"把 worktree 路径作为 workspace_path 注入"；**但** §16.3 场景一表格（L1599）隔离行写"**可选** git worktree（`supports_worktree` 能力位）"；§2.4 Type B 示例 `repository.workspace_path: "~/work/macao-demo"`（L498）仍为主工作区路径。
- 影响：按 §16.3/示例实现的部署会把具备任意 shell 能力的 Reviewer 放进 Executor 主工作区，与 §12.2 的 prompt injection 防护承诺（P0 安全约束）正面冲突；三处文档不可用同一张对照表核验。
- 修复：§16.3 "可选"→"强制（Reviewer）"；Type B 示例改为注入后的 worktree 路径（如 `.macao/worktrees/cc-glm/...`）或注明该值是注入前占位；preflight/Conformance 将 `supports_worktree` 设为 Reviewer 准入硬条件。

## P1：进入 L1 前应修正

**P1-1 `review_manifest` 的 ABSTAIN 是不可表达的死枚举（sustained：codex P1-1 / claude 确认 / gemini P1-1，v2.3 未处理）**
- 证据：`review_manifest.schema.json:59` vote 枚举含 `ABSTAIN`，但 `opinion.status` 仅 APPROVED/CHANGES_REQUESTED/REJECTED（L26）且三条 if/then（L61-74）强制映射到 YES/NO——任何合法 status 与 `vote: ABSTAIN` 组合必被拒绝；§2.2 映射表（`MACAO_PRD_v2.md:308-317`）亦无 ABSTAIN 行。
- 影响：Reviewer 侧弃权在机器契约层不可表达；而 §6.1/§6.2/E3'（L825）的弃权均由 Orchestrator/用户标记后记入 vote_result——两套口径未裁决，Adapter 实现必然分叉。
- 修复：二选一并补正/反 fixture——① status 增加 `ABSTAIN`→`vote: ABSTAIN` 映射；② 从 review_manifest vote 枚举移除 ABSTAIN，并在 §2.2 注明"弃权仅由 Orchestrator 在超时降级时写入 vote_result"。

**P1-2 State Store `artifacts.path` 全局主键与多轮/多任务同路径生命周期矛盾（sustained：codex P1-3 / claude 确认，v2.3 未处理）**
- 证据：`MACAO_PRD_v2.md:1303-1307` `path TEXT PRIMARY KEY`；而 §3.4 生命周期表（L847-853）下 `.macao/.dev.yml`、`.macao/vote_result.json` 每轮同路径再生，§2.3（L415）承诺"git 历史保留每一轮记录"。插入语义（同路径 upsert 还是按归档路径新插）未定义，两种实现审计行为不同。
- 修复：改复合键 `(task_id, kind, checkpoint_ref, review_round, reviewer_id)` 或 `artifact_id` 自增主键，并一句话写明归档后的插入/更新语义。

**P1-3 评审闭环治理缺口：同 commit 五份评审仅两份进入跟踪（本轮新发现，流程级）**
- 证据：`docs/reviews/` 含 `2026-08-26-review-result-8ab9be7-{kimi,opencode,codex,claude,gemini}.md` 五份；`STATUS.md:6-8` 仅登记"两份独立评审"；复审申请 §二（L10）亦仅以两份为闭环对象——codex/claude/gemini 三份的 2 P0 + 4 P1（其中 2 项已被 v2.3 顺带关闭，见上）未进入处理表。
- 影响：本轮若仅按申请方提供的闭环清单核验，53 项机验全过即会误授 L1——评审审计链自身不完整，违反 Guidelines §1.1(5)（reviewer 遗漏同样进入审计记录）与 §8（多 reviewer 共识原则）。
- 修复：STATUS.md 补登记三份评审与本报告 P0/P1 的处理行；确立规则——每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账。

## P2/P3：可延期但需登记

| # | 级别 | 发现（证据） | 建议 |
|---|---|---|---|
| P2-1 | P2 | E7 四选项中 CANCEL 无显式落位：E7 伴随动作只写 "APPROVED→E4；REWORK→E5"（`MACAO_PRD_v2.md:831`）；E10 触发词仅为 `macao cancel <task>`（L833），未覆盖 `override resolve --choice CANCEL`（L1476）；Type G options（L685）、§6.1（L1103）、§2.3（L399）均未列 CANCEL | E7 伴随动作补 "CANCEL→E10（CANCELLED）"，E10 触发补 override 路径；Type G/§6.1/§2.3 枚举展示统一 |
| P2-2 | P2 | Layer 1c 伪代码（L771-782）decision=REWORK_REQUIRED 无条件返回 REWORK，未体现 E5 守卫 `round < max_rework_rounds`（L829）与 E7 max 轮分支（L831/§15.2 L1523）；max 轮时自动 vote_result 是否落盘未定义，与 §3.2 开头"与 §3.3 严格一致"承诺偏差 | 伪代码补守卫注释；明确 max 轮 "不落盘自动 decision，直接 Type G→E7" 或等价规则 |
| P2-3 | P2 | §11.4 DDL 注释"当前 FSM 状态（**9 态之一**）"（L1299）与 §3.3 "共 **10 个**"（L837）矛盾 | 注释改 10 态（申请§三.3 曾断言此处无矛盾） |
| P2-4 | P2 | `IMPROVEMENT_SUMMARY.md:160` review_context 结构图仍写 "`quality_metrics`（质量快照）"——v2.3 已统一为 `quality_snapshot`（该文档自身示例 L198 与 Schema 均正确） | L160 改 quality_snapshot |
| P2-5 | P2 | PRD §10 "成功标志 (MVP 完成)" 五项均标 ✅（`MACAO_PRD_v2.md:1242-1246`），无完成证据；与项目自订约定"未达成前不得勾选"（IMPROVEMENT L486）冲突，同一准则跨文档勾选状态不一致 | 改 `[ ]` 或「验收标准」措辞 |
| P2-6 | P2 | `macao merge approve` 为默认配置（require_human_signoff=true）正常路径必经命令（L1507），但 §14.2 命令表（L1482-1488）未列（sustained claude N1/gemini N1） | 补入命令表并注明与 override resolve 的区别 |
| P2-7 | P2 | §16.3 "其余全自动"（L1601）与默认强制人工签字矛盾（sustained claude N3/gemini N3） | 改"…`merge approve` 签字放行，其余自动" |
| P2-8 | P2 | AEP payload 仍无 per-type Schema（`aep_envelope.schema.json:29` payload 自由对象；仅 review_context 已补），Task/Capability Schema 缺（sustained codex/gemini P1-2 残余；`schemas/README.md:19` 已如实表述覆盖面，故降级 P2） | 随 PoC 前置工作补 DEVELOPMENT_STARTED/REVIEW_RESPONSE/REWORK_REQUEST payload Schema 与 fixtures |
| P2-9 | P2 | Deadlock 场景推演仅存于 `STATUS.md` SIM 表，未回填 PRD §3.4（claude P0 验收建议）；fixtures 无 `resolution=human_override` 正例（`valid/vote_result.json` 无 resolution） | §3.4 补 1:1 → E7 推演；补终局 vote_result fixture |
| P3-1 | P3 | 版本指针滞后：`EXECUTIVE_SUMMARY.md:3` 与 `docs/README.md:3` 仍"v2.2"；`IMPROVEMENT_SUMMARY.md:1` 标题"（v2.0 → v2.2）"而其版本历史已含 v2.3（L511-515） | 统一指向 v2.3（或"截至 v2.3"） |
| P3-2 | P3 | §1.1 图 "决定 APPROVED or REJECTED"（L97）——decision 枚举无 REJECTED（Guidelines §5 明令禁止该混用；REJECTED 仅是 opinion.status 枚举） | 改 "APPROVED or REWORK_REQUIRED" |
| P3-3 | P3 | §2.4 "以下给出…**4 个**核心消息类型（1-4）的详细格式示例"（L433），实际给出全部 7 个（Type A–G）——措辞与实际数量不符（Guidelines §4 声明矩阵项） | 删句或改 7 个 |
| P3-4 | P3 | §16.1 "FSM 推进（E1~E8）"（L1557）未随 E9/E10 更新 | 改 E1~E10 |
| P3-5 | P3 | Schema `$id` 版本串不一致：review_context 为 v2.3，其余 5 个为 v2.2（如 `vote_result.schema.json:3`，其内容在 v2.3 实际变更过——resolution 字段）；`schemas/README.md:3` 称"当前对应 PRD v2.3" | 随 v2.3.1 统一 $id |
| P3-6 | P3 | §12.4（L1395）与 `docs/README.md:18` 的 Schema 清单"三类产物 + AEP 信封 + macao.yaml"未含 review_context.schema.json | 补齐枚举 |
| P3-7 | P3 | §14.1 第 6 步 "见 14.6 Merge Policy"（L1477）应为 §14.5（sustained claude N2/gemini N2） | 勘误 |
| P3-8 | P3 | `docs/README.md:20` "L0~L4" 应为方法论正文的 "L1~L4"（sustained codex P2/gemini N4） | 勘误 |

## 交叉文档需做的文字修订

1. PRD：P0-1/P0-2/P1-1/P1-2/P2-1/P2-2/P2-3/P2-5/P2-6/P2-7/P3-2/P3-3/P3-4/P3-7（§14.5、§16.3、§2.4、§3.2、§3.3、§11.4、§10、§14.1、§14.2、§2.2 映射表旁注）。
2. `review_manifest.schema.json`（P1-1）与 `docs/schemas/fixtures/`（补 ABSTAIN 与 human_override 正/反例，P1-1/P2-9）。
3. `EXECUTIVE_SUMMARY.md` / `docs/README.md` / `IMPROVEMENT_SUMMARY.md`：P3-1、P2-4、P3-6、P3-8。
4. `STATUS.md`：P1-3（补登记三份评审 + 本报告全部 P0/P1/P2/P3 处理行）。

## 建议的闭环顺序与验收标准

1. **P1-3（治理）先行**：STATUS.md 与 `reviews/` 全量对账，补登记 codex/claude/gemini 三份与本报告；此后每轮复审申请必须附目录对账声明。验收：STATUS 表覆盖五份 8ab9be7 报告全部 P0/P1 的状态。
2. **P0-1（rebase 绑定）**：作出显式设计决策（严格 or 受控门禁）并写入 E4a 硬校验。验收：以"target 领先、clean rebase"场景推演可唯一证明不存在未评审内容进入 push。
3. **P0-2（worktree 强制）**：三处（§12.2/§16.3/Type B 示例）对账一致，Conformance 增加 supports_worktree 硬校验项。验收：同一张安全边界对照表逐行核验无矛盾。
4. **P1-1/P1-2**：ABSTAIN 口径裁决 + Schema/fixture；artifacts 键改 + 语义一句话。验收：机验 fixtures 含 ABSTAIN 与 human_override 正反例；DDL 与 §3.4 生命周期推演一致。
5. P2/P3 随 v2.3.1 一并处理（多为文字同步与示例补齐）。
6. 完成后申请下一轮独立复审；若仅余 P2/P3，可定 **L1 DOC-ALIGNED / PG-0**。本轮申请中"仅余 P2/P3 即宣告"的条款本次不适用，因其前提（上轮发现已全部闭环）不成立。

## Reviewer 自审记录

- **§9 五项自检**：A 字段路径——review_context 顶层键/嵌套路径、Layer 1a 读取路径、§5.3 jq 路径逐条核对一致（发现 P2-4 残留）；B ✅ 证据——IMPROVEMENT 已修，PRD §10 残留（P2-5）；C 确定性用语——99%/100% 各处均有目标值标注（PRD L729、EXEC L70、IMPROVEMENT L121）✓；D 代码块可执行性——53 项机验全过 ✓；每项 P0/P1 均附路径+行号 ✓。
- **连续漏审登记（§0）**：本轮前段仅按复审申请所列两份上轮评审核闭环，53 项机验全过后一度接近判 L1；随后对 `reviews/` 目录全量对账发现同 commit 另有三份未跟踪报告，其 P0/P1 经逐条复现仍然成立。登记盲点：**闭环核验不得以 STATUS.md 登记子集为界，必须与 reviews/ 目录全量对账**（该教训已转化为 P1-3 的对账规则）。
- **未覆盖项**：git 不可用（hash 未捕获、`git diff --check` 未复现）；IMPROVEMENT 历史叙事数字（33%/89%/75%）未核查（历史记录性质，同上轮豁免）；代码/CLI 验证不存在，不外推 L2+。

---

### 附录：机器校验结果（摘要）

环境：Python 3.13.14 / jsonschema 4.26.0 / PyYAML 6.0.3（Windows；评审环境预装缺失，本次安装后执行）。脚本：逐块提取 Markdown fenced 代码块 → 对应 Schema 校验（可复现）。

```text
PASS  6 个 Schema 自检（draft-07 check_schema）
PASS  fixtures：valid 6 例全过（dev/review/vote_result/context_min/context_full/aep）
PASS  fixtures：invalid 3 例被正确拒绝（status↔vote 冲突、context 缺 refs、AEP 未知 type）
PASS  PRD 8/8 JSON 块解析；7 AEP 示例过信封 Schema；vote_result 示例过 Schema
PASS  PRD Type B payload.review_context 与 §5.2 示例均过 review_context.schema.json
PASS  PRD 5/5 YAML 块解析；§2.1/§2.2/§13 过对应 Schema（§16.4 为 v1.1 草案，仅解析）
PASS  EXEC 三例过对应 Schema；IMPROVEMENT_SUMMARY context 过 Schema
53 checks, 0 failed
```
