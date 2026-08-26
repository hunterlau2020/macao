# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。

- 更新时间：2026-08-26（v2.3 修订后）
- 最近复审对象：commit `8ab9be7`（PRD v2.2），两份独立评审：
  - `reviews/2026-08-26-review-result-8ab9be7-kimi.md`：1 个 P0 + 5 个 P1 + 4 个 P2/P3
  - `reviews/2026-08-26-review-result-8ab9be7-opencode.md`：4 个 P1 + 4 个 P2 + 6 个 P3（19 项机器校验，PRD 全过）
- 当前等级：**PENDING_REVIEW**
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

## 下一步

1. 对 PRD v2.3 申请下一轮独立复审（重点：review_context 单一结构、Deadlock→终局 vote_result 流程、10 态 FSM 一致性）；
2. SIM 复核五场景（首次双批准 / CI gate 失败 E4b / 1:1 僵局 / 一人弃权 / 返工第二轮）+ Deadlock 人工裁定场景；
3. 复审通过后定级 L1 DOC-ALIGNED / PG-0。
