# MACAO PRD v2.3 对齐评审结论

- 评审日期：2026-08-26
- 被评审 commit：`cc77a94`
- 评审范围：`docs/MACAO_PRD_v2.md` v2.3、`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/schemas/*`、`docs/README.md`、`docs/reviews/STATUS.md` 及复审申请
- 权威基准：`docs/MACAO_PRD_v2.md`（v2.3）
- 评审角色：kimi
- 结论：**未达 L1 DOC-ALIGNED / PG-0，维持 PENDING_REVIEW**。kimi/opencode 两份 `8ab9be7` 评审的 P0/P1 已确认全部关闭（含 20+ 项机器校验全过）；但 `docs/reviews/` 目录中同 commit `8ab9be7` 实际存在五份评审，**codex/claude/gemini 三份的 2 个 P0 与 2 个 P1 经本轮对 v2.3 现文逐条复现后仍然成立**，阻止 L1 宣告。

## 已对齐 / 已确认项（kimi/opencode 上轮发现，v2.3 已关闭）

| 项目 | 结果 | 证据 |
|---|---|---|
| review_context 唯一权威结构 | **已关闭** | PRD §5.2（第 952–1035 行）声明为唯一权威完整模型；§2.4 Type B（第 491–545 行）收敛为最小子集，顶层键名与嵌套路径与 §5.2 完全一致；`docs/schemas/review_context.schema.json` 同时接受最小/完整形态。 |
| Deadlock 终局表达与转移 | **已关闭** | `vote_result.schema.json` 新增 `resolution` 枚举；PRD §3.2 Layer 1c（第 771–782 行）显式两分支；§3.3 新增 E7/E9/E10，FSM 扩至 10 态（第 837 行）。 |
| §6.1 触发条件 1 口径 | **已关闭** | PRD §6.1（第 1089–1092 行）改为 Layer 3/E8 口径，并注明 Layer 2 永不触发接管；第 1127 行新增人工接管超时总则。 |
| §1.1/§1.2 与 §3.3 同步 | **已关闭** | §1.1 图重绘（第 103–113 行）并注明"以 §3.3 为准"；§1.2 补 E7/E9/E10（第 129–130 行）；README.md 第 24 行导航已修正。 |
| EXEC 三处产物示例 | **已关闭** | `EXECUTIVE_SUMMARY.md` 第 126–155、161–186、192–209 行三示例重写并通过对应 Schema 校验。 |
| IMPROVEMENT_SUMMARY 计划类标记 | **已关闭** | 第 343–349 行 8 周计划改为【计划】；第 408–410、486–491 行改为 `[ ]` 待验证。 |
| fixtures 与 Schema 机器校验 | **已确认** | 6 个 Schema 均合法；valid/ 6 例通过对应 Schema；invalid/ 3 例被正确拒绝；PRD 内嵌 8 个 JSON 块、5 个 YAML 块全部通过；EXEC 三示例、IMPROVEMENT_SUMMARY context 示例均通过。 |

## P0：必须先解决（codex/claude/gemini 8ab9be7 遗留，v2.3 未处理）

| 编号 | 发现与证据 | 影响 | 建议 |
|---|---|---|---|
| P0-1 | **clean rebase 破坏"评审对象 = 合并对象"的 checkpoint 绑定**。PRD §14.5（第 1504 行）规定 rebase "仅改变 commit 哈希、不触发新一轮评审"；而 §3.2/§3.3 以 `checkpoint_ref + review_round` 为受理作用域，E4a（第 827 行）完成条件不含"最终 push 对象 == checkpoint_ref"的硬校验。 | 被批准对象与进入 target 的对象在哈希层面断裂，上游变更可经 rebase 通道不经评审合入，违反审计链承诺。 | 二选一并写入 E4a 硬校验：① 严格模式——rebase 产生任何新 hash 即 E4b 重审；② 受控门禁——`git range-diff` 无内容差异 + `rebased_from` 元数据入 vote_result/审计 + CI gate 与人工签字在 rebase 后新 commit 上重跑记录。 |
| P0-2 | **Reviewer worktree 强制安全边界被 §16.3 与 Type B 示例削弱**。§12.2（第 1378 行）"MVP 阶段强制 sandboxed + 独立 worktree"；§5.3（第 1046–1049 行）也声明注入 worktree 路径；但 §16.3（第 1599 行）写"可选 git worktree"，§2.4 Type B 示例（第 498 行）仍为主工作区路径 `~/work/macao-demo`。 | 按示例实现会把具备任意 shell 能力的 Reviewer 放进 Executor 主工作区，与 prompt injection 防护承诺正面冲突。 | §16.3 "可选"→"强制"；Type B 示例改为 worktree 注入路径或注明该值为占位；preflight/Conformance 将 `supports_worktree` 设为 Reviewer 准入硬条件。 |

## P1：进入 L1 前应修正（codex/claude/gemini 8ab9be7 遗留 + 本轮流程发现）

| 编号 | 发现与证据 | 影响 | 建议 |
|---|---|---|---|
| P1-1 | **`review_manifest` 的 ABSTAIN 是不可表达的死枚举**。`review_manifest.schema.json` 第 59 行 `vote` 枚举含 `ABSTAIN`，但 `opinion.status` 仅 APPROVED/CHANGES_REQUESTED/REJECTED（第 26 行）且三条 if/then（第 61–74 行）强制映射到 YES/NO——任何合法 status 与 `vote: ABSTAIN` 组合必被拒绝；PRD §2.2 映射表亦无 ABSTAIN 行。 | Reviewer 侧弃权在机器契约层不可表达；与 §6.1/§6.2/E3 的弃权由 Orchestrator 标记后记入 vote_result 的口径未裁决，Adapter 实现必然分叉。 | 二选一并补正/反 fixture：① status 增加 `ABSTAIN`→`vote: ABSTAIN` 映射；② 从 review_manifest vote 枚举移除 ABSTAIN，并注明"弃权仅由 Orchestrator 在超时降级时写入 vote_result"。 |
| P1-2 | **State Store `artifacts.path` 全局主键与多轮/多任务同路径生命周期矛盾**。PRD §11.4（第 1303–1307 行）`path TEXT PRIMARY KEY`；而 §3.4 生命周期表（第 847–853 行）下 `.macao/.dev.yml`、`.macao/vote_result.json` 每轮同路径再生，§2.3（第 415 行）承诺"git 历史保留每一轮记录"。 | 插入语义（同路径 upsert 还是按归档路径新插）未定义，两种实现审计行为不同。 | 改复合键 `(task_id, kind, checkpoint_ref, review_round, reviewer_id)` 或 `artifact_id` 自增主键，并写明归档后的插入/更新语义。 |
| P1-3 | **评审闭环治理缺口：同 commit 五份评审仅两份进入跟踪（流程级）**。`docs/reviews/` 含 `2026-08-26-review-result-8ab9be7-{kimi,opencode,codex,claude,gemini}.md` 五份；STATUS.md 此前仅登记两份；复审申请 §二亦仅以两份为闭环对象。 | 若仅按申请方提供的闭环清单核验，20+ 项机验全过即会误授 L1——评审审计链自身不完整，违反 Guidelines §1.1(5) 与 §8。 | STATUS.md 补登记三份评审与本报告 P0/P1 的处理行；确立规则——每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账。 |

## P2/P3：可延期但需登记

| 编号 | 发现与证据 | 影响 | 建议 |
|---|---|---|---|
| P2-1 | **override 选项枚举在消息示例与操作手册中不完全一致**。PRD §2.4 Type G（第 685 行）与 §6.1 trigger 3（第 1103 行）未含 `CANCEL`；而 §14.1（第 1476 行）与 E7（第 831 行）含 `CANCEL`。 | Deadlock 裁定是否支持取消的表述不一致。 | 统一为含 `CANCEL` 的完整枚举，或明确 CANCEL 仅由 `macao cancel` 触发。 |
| P2-2 | **Layer 1c 伪代码缺 max_rework_rounds 守卫**。PRD §3.2（第 771–782 行）decision=REWORK_REQUIRED 无条件返回 REWORK，未体现 E5 守卫 `round < max_rework_rounds`（第 829 行）。 | max 轮时自动 vote_result 是否落盘未定义，与"与 §3.3 严格一致"承诺偏差。 | 伪代码补守卫注释；明确 max 轮 "不落盘自动 decision，直接 Type G→E7" 或等价规则。 |
| P2-3 | **State Store DDL 注释未同步 10 态 FSM**。PRD §11.4 第 1299 行注释"9 态之一"与 §3.3 第 837 行"共 10 个"矛盾。 | 数据库约束文字与状态机定义不一致。 | 注释改为"10 态之一（含 CANCELLED）"。 |
| P2-4 | **PRD §10 "成功标志 (MVP 完成)" 五项均标 ✅ 无证据**（第 1242–1246 行），与 IMPROVEMENT_SUMMARY 第 486 行"未达成前不得勾选"冲突。 | 同一准则跨文档勾选状态不一致。 | 改为 `[ ]` 或「验收标准」措辞。 |
| P2-5 | **AEP payload 仍无 per-type Schema**。`aep_envelope.schema.json` 第 29 行 payload 为自由 object；仅 review_context 已补。 | Adapter Conformance 缺少可执行的 per-type payload 契约。 | 随 PoC 前置工作补 DEVELOPMENT_STARTED/REVIEW_RESPONSE/REWORK_REQUEST payload Schema 与 fixtures。 |
| P2-6 | **Deadlock 场景推演未回填 PRD §3.4**；fixtures 无 `resolution=human_override` 正例。 | 关键场景缺少可复现推演。 | §3.4 补 1:1 → E7 推演；补终局 vote_result fixture。 |
| P3-1 | **版本引用滞后**。`EXECUTIVE_SUMMARY.md` 第 3 行、`docs/README.md` 第 3 行、`docs/IMPROVEMENT_SUMMARY.md` 第 1 行仍写 v2.2，而 PRD 已至 v2.3。 | 文档导航与事实不符，属文案债。 | 统一改为 v2.3（或"v2.x"）。 |
| P3-2 | **PRD §14.1 内部章节引用错误**。第 1477 行"见 14.6 Merge Policy"实际章节为 14.5（第 1500 行）。 | 内部引用失效。 | 改为"见 14.5 Merge Policy"。 |
| P3-3 | **§16.1 "FSM 推进（E1~E8）"**（第 1557 行）未随 E9/E10 更新。 | 章节引用不完整。 | 改为 E1~E10。 |
| P3-4 | **Schema `$id` 版本串不一致**。`review_context.schema.json` 为 v2.3，其余 5 个为 v2.2；`schemas/README.md` 第 3 行称"当前对应 PRD v2.3"。 | 版本串与内容演进不匹配。 | 随 v2.3.1 统一 $id。 |
| P3-5 | **§12.4 与 `docs/README.md` 第 18 行的 Schema 清单未含 review_context**。 | 清单不完整。 | 补齐枚举。 |
| P3-6 | **`docs/README.md` 第 20 行 "L0~L4"** 应为方法论正文的 "L1~L4"。 | 术语不一致。 | 勘误。 |

## 交叉文档需做的文字修订

1. `docs/MACAO_PRD_v2.md`：P0-1/P0-2/P1-1/P1-2/P2-1/P2-2/P2-3/P2-4/P3-2/P3-3/P3-5（§14.5、§16.3、§2.4、§3.2、§3.3、§11.4、§10、§14.1、§12.4）。
2. `review_manifest.schema.json`（P1-1）与 `docs/schemas/fixtures/`（补 ABSTAIN 与 human_override 正/反例，P1-1/P2-6）。
3. `EXECUTIVE_SUMMARY.md` / `docs/README.md` / `IMPROVEMENT_SUMMARY.md`：P3-1、P3-5、P3-6。
4. `STATUS.md`：P1-3（补登记 codex/claude/gemini 三份与本报告全部处理行）。

## 建议的闭环顺序与验收标准

1. **P1-3（治理）先行**：STATUS.md 与 `reviews/` 全量对账，补登记 codex/claude/gemini 三份与本报告；此后每轮复审申请必须附目录对账声明。
2. **P0-1（rebase 绑定）**：作出显式设计决策（严格 or 受控门禁）并写入 E4a 硬校验。验收：以"target 领先、clean rebase"场景推演可唯一证明不存在未评审内容进入 push。
3. **P0-2（worktree 强制）**：三处（§12.2/§16.3/Type B 示例）对账一致，Conformance 增加 supports_worktree 硬校验项。验收：同一张安全边界对照表逐行核验无矛盾。
4. **P1-1/P1-2**：ABSTAIN 口径裁决 + Schema/fixture；artifacts 键改 + 语义一句话。验收：机验 fixtures 含 ABSTAIN 与 human_override 正反例；DDL 与 §3.4 生命周期推演一致。
5. P2/P3 随 v2.3.1 一并处理（多为文字同步与示例补齐）。
6. 完成后申请下一轮独立复审；若仅余 P2/P3，可定 **L1 DOC-ALIGNED / PG-0**。本轮申请中"仅余 P2/P3 即宣告"的条款本次不适用，因其前提（上轮发现已全部闭环）不成立。

## Reviewer 自审记录

按评审方法论 §9 强制自检：

- **A（字段声明位置 vs 实际读取路径）**：已核对 `repository.workspace_path`、`code_changes.refs.*`、`quality_snapshot.tests.*` 在 PRD §2.4/§5.2/§5.3、`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md` 中路径一致。
- **B（`[x]`/`✅` ≠ 完成证据）**：`IMPROVEMENT_SUMMARY.md` 计划类条目已改为 `[ ]`/`【计划】`；但 PRD §10 仍残留 ✅（P2-4）。
- **C（确定性用语 99%/100%）**：各文档均在显著位置标注"设计目标值/以 PoC 实测为准"，无未标注的既成事实表述。
- **D（代码块可执行性）**：运行机器校验 20+ 项，PRD/EXEC/IMPROVEMENT_SUMMARY 全部 JSON/YAML 示例均通过解析与对应 Schema；fixtures 行为正确。
- **连续漏审登记**：本轮前段仅按复审申请所列两份上轮评审核闭环，20+ 项机验全过后一度接近判 L1；随后对 `reviews/` 目录全量对账发现同 commit 另有三份未跟踪报告，其 P0/P1 经逐条复现仍然成立。登记盲点：**闭环核验不得以 STATUS.md 登记子集为界，必须与 reviews/ 目录全量对账**（该教训已转化为 P1-3 的对账规则）。

本轮未声称任何厂商 CLI 或 Adapter 代码已验证；结论仅覆盖文档静态一致性、Schema 校验与手工场景推演。
