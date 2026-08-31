# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单评审申请

- **申请日期**：2026-09-01
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码基线**：`origin/main`
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 专家意见闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与申请目标

在过去两轮对 `docs/PRD_CHANGE_PROPOSAL_v2.5.md` 的专家评审中，专家委员会（Qwen、Gemini、Kimi、Grok）分别出具了 5 份独立评审报告：
1. [`docs/reviews/2026-09-01-review-result-0042dc3-qwen.md`](2026-09-01-review-result-0042dc3-qwen.md)
2. [`docs/reviews/2026-09-01-review-result-0042dc3-gemini.md`](2026-09-01-review-result-0042dc3-gemini.md)
3. [`docs/reviews/2026-09-01-review-result-PRD-v2.5-v0.2-kimi.md`](2026-09-01-review-result-PRD-v2.5-v0.2-kimi.md)
4. [`docs/reviews/2026-09-01-review-2.5-2-grok.md`](2026-09-01-review-2.5-2-grok.md)
5. [`docs/reviews/2026-09-01-review-2.5-2-gemini.md`](2026-09-01-review-2.5-2-gemini.md)

评审委员会一致肯定了 PRD v2.5 **「零语义创作、内容与控制分层、加权纯整数共识、独立不可变产物、Git Evidence Ref 隔离」**的核心架构方向，并指出了关于 E7 人工豁免状态转移、E3 全席位 accounted 判定、DEADLOCK 即时落盘、Disposition 超时处置与 `SHOULD_DISPOSE` 角色投影等若干关键细节加固项。

本轮申请旨在提请专家委员会对**全量完成同步修改的 PRD v2.5 文档体系与代码变更清单**进行正式定级复核，确认架构设计无冲突、无断裂，为后续代码实施阶段提供权威基准。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威文档）**：全面融入 D-1～D-9 架构裁定、AEP/1.1（16 KiB 预算）、加权 2/3 纯整数五重门禁、独立 `review_disposition` 契约、E5a 改码返工守卫、Git Evidence Ref 拓扑与 `role_view` 投影。 |
| 2 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：逐条记录 9 大架构裁定依据、Kimi/Grok/Qwen/Gemini 意见闭环映射及 §9 全量文档迁移图谱。 |
| 3 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：梳理 6 大模块（Schema、Consensus、Workflow FSM、Git Evidence、CLI、Test Suites）的详细代码修改点与 5 阶段实施排期。 |
| 4 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部重定义映射表，明确 v2.5 对状态识别、AEP 引用、加权共识、Evidence Ref 的最新裁定。 |
| 5 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q11/Q12/Q14/Q15，明确独立 Review Disposition 与不可变 `vote_result.json` 的物理写者边界及纯整数加权规则。 |
| 6 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：22 条事实陈述（F-1～F-22）完整作为设计约束。 |
| 7 | [`docs/usercases/UC1-init-glm.md`](../usercases/UC1-init-glm.md) | **用例 1 同步**：更新任务态调度与 `role_view` 投影表（加入 `SHOULD_DISPOSE` 与 `NOTIFY_EXECUTOR_DISPOSE`）。 |
| 8 | [`docs/usercases/UC5-consensus-tally.md`](../usercases/UC5-consensus-tally.md) | **用例 5 同步**：明确 `weighted_2/3_v1` 五重纯整数门禁、DEADLOCK 即时落盘与不可变单一写入。 |
| 9 | [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) | **用例 6 同步**：升级为独立 `review_disposition` 意见处置用例，明确 `requires_new_checkpoint` 布尔守卫与 E5a/E6 流转。 |
| 10| [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整记录评审履历与对账索引。 |

---

## 3. 核心专家意见物理闭环核验表

| 提出专家与项号 | 专家核心关切 | PRD v2.5 落地位置与物理闭环设计 |
|---|---|---|
| **Kimi P0-1** | E7 Override 状态转移与 issue 豁免机制定义不全 | 1. 在 PRD §3.3、§6.1 与 Schema 中明确：E7 状态源为 HOLD（`CONSENSUS_CHECK` 或 `REWORK`）；<br/>2. 裁决为 APPROVED 时必须满足：存在 FINAL disposition，且所有未修复 `BLOCKING` issue 均显式标记在 `exempt_issue_ids` 中（映射为 `EXEMPTED_BY_ADMIN + override_id`）；<br/>3. 生成独立 `admin_override.json` 与审计事件，保持 `vote_result.json` 不可变。 |
| **Kimi P1-1** | E3 WAITING_REVIEW 转移触发条件存在误解 | 在 PRD §3.3 与 UC-5 中明确：E3 触发条件为**「所有配置席位均已 accounted（收到合法 manifest 或被持久化 timeout 机制纳入 accounted 集合）」**，而非提前法定人数截断。 |
| **Kimi P1-2** | DEADLOCK 落盘与状态机一致性 | 确立 D-1 裁定：DEADLOCK 即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`），随后进入 HOLD；E7 裁决后独立生成 `admin_override.json`，严禁二次回写 `vote_result.json`。 |
| **Kimi P1-3** | `NEEDS_ADMIN` 处置类型缺少答复闭环 | 在 PRD §6.1 与 UC-6 中明确：执行者可声明 `NEEDS_ADMIN`；进入 HOLD 后，管理员通过 E7 override 明确裁决（豁免或要求返工）。 |
| **Grok P1-1** | Disposition 超时未交的处理流程 | 在 PRD §6.1 中定义 `timeouts.review_disposition`（默认 30m）：超时后自动触发 `HUMAN_OVERRIDE_REQUEST`（HOLD）；管理员可裁决强制 REWORK、延期或带豁免合入。 |
| **Grok P1-2** | `CONSENSUS_CHECK` 期间的角色视图状态缺失 | 在 PRD §14.2 与 UC-1 表中补齐：当 `requires_disposition=true` 且尚无 FINAL disposition 时，Executor 视图为 **`SHOULD_DISPOSE`**，系统 `next_action` 为 **`NOTIFY_EXECUTOR_DISPOSE`**。 |
| **Qwen P1-1** | 采纳与处置写者边界及数据一致性 | 确立 D-2 裁定：废除 `vote_result.json` 中的 `issues_summary` 混合写设计，Executor 单一写入按轮隔离的 `review_disposition.yml`，消除双真源冲突。 |
| **Gemini P1-1** | 加权共识算法的整数确定性与防独裁性 | 确立 D-6 裁定：采用 `weighted_2/3_v1` 纯整数五重门禁，配置期独裁帽 $\forall i, 3w_i < 2W$，分母采用配置总权重 $W$，胜方最少席位 $\ge 2$。 |

---

## 4. 验证与一致性自检

1. **Schema 闭环与语法检查**：
   - 全量 Markdown 与引用链接格式符合 GitHub Flavored Markdown 规范；
   - 契约字段在 PRD、SRS、FAQ、UC 及 Schema 设计间实现 100% 命名与语义对齐。
2. **状态机与流转推演**：
   - 10 状态单一事实源，不存在歧义转移分支；
   - 每一步状态流转均由 AEP 指令或作用域内的确定性产物驱动；
   - DEADLOCK、超时、`NEEDS_ADMIN`、Git 冲突与 CI 失败均具备完备的人工接管与豁免闭环。

---

## 5. 申请定级建议

建议专家委员会（Claude、Codex、Gemini、Grok、Kimi、Qwen、ZCode）对本申请进行复核，确认 PRD v2.5 设计基准完备自洽，正式授予 **L1 DOC-ALIGNED / PG-0** 准入，并批准进入 Phase 1~5 代码实施阶段。
