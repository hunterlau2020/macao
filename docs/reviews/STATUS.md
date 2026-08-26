# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- 更新时间：2026-08-26（v2.3 五份复审后，合并两端记录）
- 最近复审对象：commit `cc77a94`（PRD v2.3，响应 `reviews/2026-08-26-review-request-PRD-v2.3.md`），**共五份独立评审，结论一致：未达 L1，维持 PENDING_REVIEW**：
  - `reviews/2026-08-26-review-result-PRD-v2.3-opencode.md`：上轮（kimi/opencode-8ab9be7）发现全部确认关闭，53 项机验全过；但同 commit 另有三份未跟踪评审的 2 P0 + 2 P1 仍成立，另登记 P1-3 治理缺口 + 9 P2 + 8 P3
  - `reviews/2026-08-26-review-result-cc77a94-kimi.md`：独立复核确认 kimi/opencode 上轮 P0/P1 全部关闭、20+ 项机验全过；同样确认 codex/claude/gemini 的 2 P0 + 2 P1 在 v2.3 未闭环；登记 P1-3 治理缺口与 P2/P3 逐条勘误
  - `reviews/2026-08-26-review-result-cc77a94-codex.md`：PARTIALLY_VERIFIED；机器校验与 context 单一模型闭环，但指出 rebase 审计一致性、worktree 强制性、override 终局模型仍需正文闭环（P0-1/P0-2/P0-3，后降级为各家的 P2-1）
  - `reviews/2026-08-26-review-result-cc77a94-claude.md`：PARTIALLY_VERIFIED；确认机验通过，主张 Deadlock 检测到接管的入口转移边在 §3.3 缺失（维持 P1，见下方"分歧记录"），§3.4 缺推演三，§11.4 DDL 注释"9 态"
  - `reviews/2026-08-26-review-result-cc77a94-gemini.md`：PARTIALLY_VERIFIED；独立机验 14/14 PASS，确认四大高风险区状态，给出定级前最终闭环清单（P0-1/P0-2/P1-1/P1-2/P2-1/P2-2/P3-1）
- commit `8ab9be7`（PRD v2.2）轮共有 **五份**独立评审（此前 STATUS 只登记两份，已按 P1-3 补齐对账）：
  - `reviews/2026-08-26-review-result-8ab9be7-kimi.md`：1 P0 + 5 P1 + 4 P2/P3（已由 v2.3 关闭并经本轮五份复核确认）
  - `reviews/2026-08-26-review-result-8ab9be7-opencode.md`：4 P1 + 4 P2 + 6 P3（已由 v2.3 关闭并经复核确认）
  - `reviews/2026-08-26-review-result-8ab9be7-codex.md`：2 P0 + 4 P1 + 3 P2（补登记；P0-1/P0-2/P1-1/P1-3 未处理，P1-2 部分，P1-4 已顺带关闭）
  - `reviews/2026-08-26-review-result-8ab9be7-claude.md`：1 P0 + 3 P2/P3（补登记；P0 已由 v2.3 设计改法关闭，N1/N2/N3 未处理）
  - `reviews/2026-08-26-review-result-8ab9be7-gemini.md`：3 P0 + 4 P1 + 4 P2/P3（补登记；P0-1/P0-2/P1-1/P1-3 未处理，P0-3/P1-4 已顺带关闭）
- 当前等级：**PENDING_REVIEW**
- 本轮版本：PRD **v2.3**（schemas 6 个 + fixtures 9 个，机验 53/53 全过；review_context 单一结构、Deadlock 终局表达、10 态 FSM 主体已闭环）

## 已确认关闭的项（五份评审共识）

| 项目 | 证据 |
|------|------|
| review_context 唯一权威结构 | §5.2 完整模型（L952-1035，两传输块+六语义块）；§2.4 Type B（L491-545）最小子集，顶层 8 键与嵌套路径与 §5.2 完全一致；`review_context.schema.json` 同接受最小/完整形态 |
| EXEC/IMPROVEMENT 示例 Schema 合规 | 验证器独立复跑 53/53 通过（PRD 8 JSON + 5 YAML、7 AEP、EXEC 三例、IMPROVEMENT context） |
| Deadlock 终局表达（resolution 落盘） | `vote_result.schema.json:52` `resolution: automatic\|human_override`；§3.2 Layer 1c 显式两分支（L778-782）；E7 为出口边 + §6.1 超时总则 HOLD 兜底（L1127） |
| 10 态 FSM 主体 | §3.3（L837）10 态；E9/E10/CANCELLED（L832-833）；§1.1 图 + §1.2 行同步；README L24 |
| §6.1 触发条件 1 口径 | L1090 改 Layer 3/E8，注明 Layer 2 永不触发接管 |
| kimi/opencode（8ab9be7）P0/P1 全部 | 经五份复审逐条复核确认关闭 |

## 待闭环项（v2.3.1 处理）

| 编号 | 级别 | 发现（证据） | 来源（共识/分歧） | 修正要求 |
|------|------|-------------|------------------|---------|
| P0-1 | P0 | clean rebase 豁免破坏"评审对象=合并对象"：§14.5（L1504）"rebase 仅改变 commit 哈希、不触发新一轮评审"，而受理作用域为 checkpoint_ref+review_round（L744-746/L824-830），E4a（L827）无"最终 push 对象==checkpoint_ref"硬校验 | codex/claude/gemini/kimi/opencode **共识** | 二选一写入 E4a 硬校验：①严格——rebase 产生新 hash 即 E4b 重审；②受控门禁——range-diff 无内容差异 + rebased_from 元数据 + CI/签字重跑记录 |
| P0-2 | P0 | worktree 强制边界被削弱：§12.2（L1378）/§5.3（L1046-1049）强制 sandboxed+独立 worktree；但 §16.3（L1599）"可选 git worktree"、Type B 示例 workspace_path 为主工作区（L498） | codex/gemini/kimi/opencode **共识**（claude 未主张冲突） | 三处对账一致：§16.3 改"强制（Reviewer）"；Type B 示例改注入后 worktree 路径或注明占位；Conformance 将 supports_worktree 设为准入硬条件 |
| P1-1 | P1 | ABSTAIN 为不可表达死枚举：review_manifest.schema.json vote 含 ABSTAIN（L59）但 opinion.status 无（L26），三条 if/then 强制映射 YES/NO（L61-74）；§2.2 映射表无 ABSTAIN 行 | codex/claude/gemini/kimi/opencode **共识** | 二选一：①status 增 ABSTAIN→vote:ABSTAIN；②vote 枚举移除 ABSTAIN，注明"弃权仅由 Orchestrator 超时降级时写入 vote_result"。补正/反 fixture |
| P1-2 | P1 | artifacts.path 全局主键 vs 多轮同路径生命周期矛盾：§11.4（L1303-1307）path TEXT PRIMARY KEY，§3.4（L847-853）每轮同路径再生 | codex(claude 确认)/kimi/opencode **共识** | 改复合键 `(task_id, kind, checkpoint_ref, review_round, reviewer_id)` 或自增主键 + 一句话归档插入/更新语义 |
| P1-3 | P1 | 治理缺口：同 commit（8ab9be7）五份评审仅两份进跟踪，导致上轮一度将被误授 L1（流程级，违反 Guidelines §1.1(5)/§8） | kimi/opencode **共识**（本轮新发现） | 本科本轮即执行：STATUS 与 reviews/ 全量对账（已补登记三份）；确立每轮对账规则（见本文档引言） |
| P2-1 | P2 | E7 四选项中 CANCEL 无显式落位：E7 伴随动作只写 APPROVED→E4/REWORK→E5（L831）；E10 触发仅为 macao cancel；Type G（L685）/§6.1（L1103）/§2.3（L399）未列 CANCEL | codex P0-3（降级）+opencode+kimi | E7 补 CANCEL→E10；E10 触发补 override 路径；各枚举展示统一 |
| P2-2 | P2 | Layer 1c 伪代码（L771-782）缺 max_rework_rounds 守卫（E5 L829/E7 L831）；max 轮自动 decision 是否落盘未定义 | opencode+kimi | 伪代码补守卫；明确 max 轮"不落盘自动 decision，直接 Type G→E7" |
| P2-3 | P2 | §11.4 DDL 注释"9 态之一"（L1299）vs §3.3"共 10 个"（L837） | claude/gemini/codex/opencode **共识** | 注释改"10 态之一（含 CANCELLED）" |
| P2-4 | P2 | IMPROVEMENT_SUMMARY L160 结构图仍写 "quality_metrics"，v2.3 已统一 quality_snapshot | opencode | L160 改名 |
| P2-5 | P2 | PRD §10 "成功标志" 五项均标 ✅（L1242-1246），无完成证据，与"未达成前不得勾选"（IMPROVEMENT L486）冲突 | kimi+opencode | 改 [ ] 或「验收标准」措辞 |
| P2-6 | P2 | `macao merge approve` 为默认 require_human_signoff 正常路径必经命令（L1507），但 §14.2 命令表（L1482-1488）未列 | claude N1/gemini N1 → opencode/kimi 采纳 | 补入命令表并注明与 override resolve 区别 |
| P2-7 | P2 | §16.3"其余全自动"（L1601）与默认强制人工签字矛盾 | claude N3/gemini N3 → opencode | 改"…merge approve 签字放行，其余自动" |
| P2-8 | P2 | AEP payload 仍无 per-type Schema（aep_envelope.schema.json:29 payload 自由对象）；Task/Capability Schema 缺 | codex/gemini P1-2 残余 → opencode/kimi 降级 P2 | 随 PoC 前置补 DEVELOPMENT_STARTED/REVIEW_RESPONSE/REWORK_REQUEST payload Schema 与 fixtures |
| P2-9 | P2 | Deadlock 场景推演未回填 PRD §3.4（正文仅场景一/二）；fixtures 无 resolution=human_override 正例 | claude/gemini（入口边 P1 的分歧收敛点）+opencode | §3.4 补 1:1 平票→裁定→E7 推演；补终局 vote_result fixture |

## 分歧记录（未强行统一，交由 v2.3.1 闭环处理）

**Deadlock 检测→人工接管入口边**：claude/gemini 主张"票收齐算出 Deadlock → 进入人工接管"这一入口在 §3.3 E1~E10 中无对应边，Layer 1c 会退化为 60 分钟卡死诊断，无法兑现 §6.1 的 10 分钟独立时限承诺，维持 **P1**；opencode/kimi 主张该路径已由设计改法闭环（先人工裁定、后写终局 decision；CONSENSUS_CHECK 停留期由 §6.1 超时总则 HOLD 兜底），仅缺口是 §3.4 推演文本与 CANCEL 落位（P2-1/P2-9）。
处理取向：v2.3.1 按**并集**处理——在 E3 行补充一条"票数判定即确定性函数"的入口说明（或显式 E3a），并在 §3.4 补第三场景推演，同时消除 P2-1/P2-9；满足两家验收标准，不做二选一。

## P3 待修（不阻塞定级，随 v2.3.1 一并）

| 编号 | 发现（证据） |
|------|-------------|
| P3-1 | 版本指针滞后：EXECUTIVE_SUMMARY.md:3、README.md:3 仍 "v2.2"；IMPROVEMENT_SUMMARY.md:1 标题 "(v2.0 → v2.2)" 而其版本历史已含 v2.3 |
| P3-2 | §1.1 图 "决定 APPROVED or REJECTED"（L97）——decision 枚举无 REJECTED，改 "REWORK_REQUIRED" |
| P3-3 | §2.4 "…4 个核心消息类型"（L433）实际给出 7 个（Type A–G） |
| P3-4 | §16.1 "FSM 推进（E1~E8）"（L1557）未随 E9/E10 更新 |
| P3-5 | Schema $id 版本串不一致：review_context v2.3，其余 5 个 v2.2（vote_result 内容已在 v2.3 变更）；schemas/README.md:3 称"当前对应 PRD v2.3" —— 或声明 Schema 独立版本策略 |
| P3-6 | §12.4（L1395）与 README.md:18 Schema 清单未含 review_context.schema.json |
| P3-7 | §14.1 第 6 步 "见 14.6 Merge Policy"（L1477）实际为 §14.5 |
| P3-8 | README.md:20 "L0~L4" 应为方法论正文 "L1~L4" |
| P3-9 | §1.1 简化图非正式术语 "REVIEWING"（L85），与 10 态正式列表不对应（图已自称简化，非强制） |
| P3-10 | EXECUTIVE_SUMMARY.md:118 "文件握手 100% 可靠" 建议就地标注为设计目标 |
| P3-11 | IMPROVEMENT_SUMMARY 历史叙事数字（33%/89%/75%）出处核查（历史记录性质，多份评审豁免） |

## 已确认的治理闭环动作（本轮同步执行）

1. **P1-3 对账**：STATUS 已补登记 8ab9be7 的 codex/claude/gemini 三份 + cc77a94 全部五份评审。
2. 机器校验维持 **53/53 全过**（opencode 独立复跑；claude/gemini 亦独立复跑一致）；`git diff --check` 无空白错误。
3. SIM 六场景推导：opencode 本轮独立重放 S3/S4/S6 可唯一推导（CANCEL 落位、max 轮守卫两处缺口登记为 P2-1/P2-2）。

## 下一步（v2.3.1 闭环顺序）

1. **P0-1**：裁决 rebase 绑定（严格 or 受控门禁二选一）写入 E4a 硬校验；验收：以"target 领先、clean rebase"场景推演唯一证明不存在未评审内容进入 push。
2. **P0-2**：三处（§12.2/§16.3/Type B 示例）worktree 对账一致 + Conformance supports_worktree 硬校验项。
3. **P1-1**：ABSTAIN 口径裁决 + Schema/fixture 正反例。
4. **P1-2**：artifacts 复合键改 + 生命周期语义一句话。
5. **P2-1/P2-2/P2-3/P2-9**：E7 CANCEL→E10 落位、Layer 1c max 轮守卫、DDL 注释 10 态、§3.4 补场景三、补 resolution=human_override fixture。
6. **P2/P3 其余 + P1-3 对账规则固化** 随 v2.3.1 一并落文。
7. 完成后申请下一轮独立复审；若仅余 P2/P3，可宣告 **L1 DOC-ALIGNED / PG-0**，正式启动开发。本轮申请"仅余 P2/P3 即宣告"条款不适用，因其前提（上轮发现全部闭环）不成立。