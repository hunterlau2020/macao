# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。

- 更新时间：2026-08-26（v2.3 复审后）
- 最近复审（两份独立复审，结论一致：未达 L1，维持 PENDING_REVIEW）：
  - `reviews/2026-08-26-review-result-PRD-v2.3-opencode.md`（kimi/opencode 上轮发现全部确认关闭，53 项机验全过；但同 commit 另有三份未跟踪评审的 2 P0 + 2 P1 仍成立，见下节）
  - `reviews/2026-08-26-review-result-cc77a94-kimi.md`（独立复核确认 kimi/opencode 上轮 P0/P1 全部关闭，20+ 项机验全过；同样确认 codex/claude/gemini 三份的 2 P0 + 2 P1 在 v2.3 未闭环，登记治理缺口 P1-3，另附 P2/P3 勘误清单）
- commit `8ab9be7`（PRD v2.2）轮共有 **五份**独立评审（STATUS 此前只登记两份，已补齐）：
  - `reviews/2026-08-26-review-result-8ab9be7-kimi.md`：1 P0 + 5 P1 + 4 P2/P3（已由 v2.3 关闭并经本轮复核确认）
  - `reviews/2026-08-26-review-result-8ab9be7-opencode.md`：4 P1 + 4 P2 + 6 P3（已由 v2.3 关闭并经本轮复核确认）
  - `reviews/2026-08-26-review-result-8ab9be7-codex.md`：2 P0 + 4 P1 + 3 P2（**本轮补登记**；P0-1/P0-2/P1-1/P1-3 未处理，P1-2 部分，P1-4 已顺带关闭）
  - `reviews/2026-08-26-review-result-8ab9be7-claude.md`：1 P0（+确认 codex 各项）+ 3 P2/P3（**本轮补登记**；P0 已被 v2.3 设计改法关闭，N1/N2/N3 未处理）
  - `reviews/2026-08-26-review-result-8ab9be7-gemini.md`：3 P0 + 4 P1 + 4 P2/P3（**本轮补登记**；P0-3 已顺带关闭，P0-1/P0-2/P1-1/P1-3 未处理，P1-4 已顺带关闭）
- 当前等级：**PENDING_REVIEW**（L1 申请被驳回，理由与待办见"v2.3 复审结论"节）
- 本轮修订：PRD **v2.3**（schemas 扩充至 6 个 Schema + 9 个 fixtures，全部经 jsonschema 实测通过/拒绝正确）

## 针对 8ab9be7 两份评审的处理状态

| 来源 | 编号 | 发现 | 状态 | 处理位置 |
|------|------|------|------|---------|
| kimi | P0-1 / opencode P1-3 | review_context 双结构并存（quality_metrics vs quality_snapshot、files_summary vs summary+files_list、§2.4 缺三块） | 已修订 | PRD §5.2 声明为唯一权威完整模型（补两传输块）；§2.4 收敛为最小子集（quality_snapshot 嵌套、summary+files_list、补 executor_self_assessment/history/references）；新增 `review_context.schema.json` |
| opencode | P1-1 | §6.1 触发条件 1 残留 "Layer 2 confidence < 0.7" 陈旧文案 | 已修订 | PRD §6.1 条件改为 Layer 3/E8 口径，并注明 Layer 2 仅日志永不触发接管 |
| opencode | P1-2 | §1.1 图无 MERGING、"Loop back to PHASE 1" 与 E6 不符；§1.2 行缺 MERGING/E7 | 已修订 | PRD §1.1 图重绘（MERGING/DONE/REWORK + E4a/E6 标注）+ 简化视图说明；§1.2 CONSENSUS/MERGE 行同步；README 导航行修正 |
| kimi/opencode | P1-4 | Deadlock 轮 decision 无法表达、Layer 1c 静默 else、override 枚举三处不一致、CANCEL 无终态 | 已修订 | 裁定结果落盘终局 vote_result（resolution=human_override）；Layer 1c 显式两分支；枚举统一 APPROVED/REWORK/RETRY_REVIEW/CANCEL；转移表新增 E9（重试评审）/E10（取消→CANCELLED 终态），FSM 10 态 |
| kimi | P1-1/2/3 / opencode P2-2 | EXEC 三处产物示例未通过 Schema | 已修订 | 三示例重写并通过对应 Schema（机验 PASS） |
| kimi | P1-4 | IMPROVEMENT_SUMMARY 计划类条目标 ✅ 无证据 | 已修订 | 8 周计划改【计划】、PoC 三假设与 MVP 成功指标改 [ ] 待验证 |
| kimi | P1-5 | quality_snapshot 字段类型不合法（24/24 ✅） | 已修订 | 改为整数并去除 emoji |
| kimi | P2-1 | 缺 review_context Schema | 已修订 | 新增 review_context.schema.json（最小子集与完整模型共用） |
| kimi | P2-2 / opencode P2-3 | Schema 嵌套约束不足；fixtures 覆盖宣称不符 | 已修订 | vote_result/dev/review Schema 细化嵌套结构；README 覆盖范围如实表述并补 fixtures（9 个） |
| kimi | P2-3 | EXEC .review.yml 未标路径 | 已修订 | 补 `.macao/.reviews/<reviewer_id>.review.yml` |
| kimi | P3-1 | 标题 v2.0 叙事 | 已修订 | 改为「改进对比总结（v2.0 → v2.2）」 |
| opencode | P2-1 | Type D round=1 与规则矛盾 | 已修订 | 示例改为 round=2 并在消息表注明语义（即将开始的返工轮次） |
| opencode | P2-2 | EXEC 架构速写模块名不一致；"↑500%" 无出处 | 已修订 | 速写对齐 §11.1 组件清单；500% 删除并标注设计目标 |
| opencode | P2-4 | 人工接管超时默认动作未定义 | 已修订 | §6.1 新增超时总则：一律 HOLD+持续告警，绝不静默推进 |
| opencode | P3-1~P3-6 | KPI 分母、timeouts 关系、Type F attachments、标题版本、full 模式机制、占位符 | 已修订 | 分别落位于 §8.1 / §13 timeouts 注释 / Type F attachments / 标题 v2.3 / §12.2 / §5.3 |

## v2.3 复审结论（2026-08-26，opencode；kimi 独立复核结论一致）

未达 L1 DOC-ALIGNED / PG-0。kimi/opencode 两份评审的 P0/P1 已确认全部关闭（含 53 项机验全过）；阻断项来自补登记的三份评审（证据均已对 v2.3 现文逐条复现）+ 本轮新发现：

| 编号 | 级别 | 发现 | 状态 | 来源 |
|------|------|------|------|------|
| P0-1 | P0 | clean rebase 豁免破坏 checkpoint 绑定（§14.5 L1504 vs §3.2/§3.3/E4a） | **待修订** | codex P0-1 / claude / gemini P0-1 |
| P0-2 | P0 | §16.3 "可选 worktree"（L1599）与 Type B 主工作区示例（L498）vs §12.2 强制（L1378） | **待修订** | codex P0-2 / gemini P0-2 |
| P1-1 | P1 | review_manifest 的 ABSTAIN 为不可表达死枚举（schema L26/L59/L61-74 vs §2.2 映射表） | **待修订** | codex/claude/gemini P1-1 |
| P1-2 | P1 | artifacts.path 全局主键与多轮同路径生命周期矛盾（L1303-1307 vs §3.4） | **待修订** | codex P1-3 |
| P1-3 | P1 | 闭环治理缺口：五份 8ab9be7 评审仅两份进跟踪（本节补登记即修复第一步） | **修订中** | 本轮新发现 |
| P2-1~P2-9 | P2 | E7 CANCEL 落位；Layer 1c 缺 max 轮守卫；§11.4 "9 态"；IMPROVEMENT L160 旧命名；PRD §10 ✅；§14.2 缺 merge approve；§16.3 "其余全自动"；AEP per-type Schema 残余；Deadlock 推演/fixture 未回填 | **待修订** | 本轮 + claude N1/N3 + codex/gemini P1-2 残余 + claude P0 验收残余 |
| P3-1~P3-8 | P3 | 版本指针 v2.2 滞后；§1.1 "REJECTED"；§2.4 "4 个"；§16.1 "E1~E8"；$id 版本串；Schema 清单未含 review_context；§14.1 "14.6"；README "L0~L4" | **待修订** | 本轮 + claude N2/N4 + codex P2 |

## 下一步

1. **v2.3 L1 复审申请：未通过**（`reviews/2026-08-26-review-result-PRD-v2.3-opencode.md`、`reviews/2026-08-26-review-result-cc77a94-kimi.md`，两份独立复审结论一致）。按其"闭环顺序"处理：① STATUS 与 reviews/ 目录全量对账常态化（P1-3）；② 裁决 rebase 绑定方案并写入 E4a 硬校验（P0-1）；③ worktree 三处对账一致 + Conformance 硬校验（P0-2）；④ ABSTAIN 口径 + artifacts 键（P1-1/P1-2）；⑤ P2/P3 随 v2.3.1 一并落文（kimi 报告另附逐条勘误清单可对照）。
2. 以上关闭后申请下一轮独立复审；届时若仅余 P2/P3，可宣告 **L1 DOC-ALIGNED / PG-0**。
3. 历史：~~五场景 + Deadlock 场景 SIM 复核~~ 已完成（2026-08-26，随 v2.3 修订执行；结论已被本轮复审独立重放确认，其中 CANCEL 落位与 max 轮守卫两处推导缺口登记为 P2-1/P2-2）：

   | 场景 | 转移链（逐步命中） | 每步唯一性 |
   |------|--------------------|-----------|
   | S1 首次双批准 | E1 → 产物(.dev.yml) → E2 → E3 → E4 → E4a | ✓ |
   | S2 CI gate 失败 | S1 至 MERGING → E4b → 产物(.dev.yml r2) → E6 → E2 → … 循环 | ✓ |
   | S3 1:1 僵局 → 裁定 APPROVED | E1→…→E3（有效票 2 = 法定人数，占比均 <2/3）→ Deadlock → E7 落盘终局 vote_result(APPROVED, human_override) → E4 → E4a | ✓ |
   | S4 一人弃权 + 1 反对 | …→ WAITING_REVIEW；超时降级流程完成 → CONSENSUS_CHECK（有效票 1 < 法定人数，不产出自动 decision）→ E7 裁定 REWORK → 落盘 → 按 E5 同规则转 REWORK | ✓ |
   | S5 返工第二轮 | E5 → REWORK_REQUEST(round=2) → 产物(.dev.yml r2 新 commit) → E6 → E2 → … （r1 产物已归档，无遮蔽） | ✓ |
   | S6 RETRY_REVIEW / CANCEL | CONSENSUS_CHECK —E9→ WAITING_REVIEW（意见作废归档、round 不变）；任意活动态 —E10→ CANCELLED 终态 | ✓ |

   推演中修正一处残留：§6.1 Consensus Deadlock 提示语补齐 RETRY_REVIEW 选项（与 E7/E9 枚举一致）。
   全部文档示例已通过对应 JSON Schema 机验（PRD 8 JSON + 5 YAML、EXEC 三示例、IMPROVEMENT_SUMMARY context）。
