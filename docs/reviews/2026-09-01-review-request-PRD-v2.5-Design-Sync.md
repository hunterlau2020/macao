# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单评审申请

- **申请日期**：2026-09-01
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码基线**：`origin/main`
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 专家意见闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与申请目标

在对 commit `0bc6247`（PRD v2.5 全文档同步初版）的评审中，评审专家委员会（Claude、Codex、Grok、Kimi、Qwen）出具了 5 份独立评审报告：
1. [`docs/reviews/2026-09-01-review-result-0bc6247-claude.md`](2026-09-01-review-result-0bc6247-claude.md) (`NO_APPROVE`, 10 项阻断)
2. [`docs/reviews/2026-09-01-review-result-0bc6247-codex.md`](2026-09-01-review-result-0bc6247-codex.md) (`NO_APPROVE`, 7 项阻断)
3. [`docs/reviews/2026-09-01-review-result-0bc6247-grok.md`](2026-09-01-review-result-0bc6247-grok.md) (`NO_APPROVE`, 5 项阻断)
4. [`docs/reviews/2026-09-01-review-result-0bc6247-kimi.md`](2026-09-01-review-result-0bc6247-kimi.md) (`NO_APPROVE`, 10 项阻断)
5. [`docs/reviews/2026-09-01-review-result-0bc6247-qwen.md`](2026-09-01-review-result-0bc6247-qwen.md) (`NO_APPROVE`, 2 项阻断)

专家委员会一致肯定了 PRD v2.5 **「零语义创作、内容与控制分层、加权纯整数共识、独立不可变产物、Git Evidence Ref 隔离」**的核心架构方向，但指出了以下关键问题：
1. **FSM 状态识别与推演残留旧语义**：§3.2 Layer 1b 仍有 `minimum_quorum` 提前返回；§3.2 Layer 1c 未处理 `DEADLOCK`、`requires_disposition` 与 `requires_new_checkpoint` 分支，且出现非机器决定的 `RETRY_REVIEW`/`CANCELLED`；§3.4 场景三保留了旧的 "DEADLOCK 不落盘、裁定后写终局 vote_result" 违规流程；
2. **Schema 机器契约断裂**：`review_context` 缺少嵌套 `refs` 模型；`vote_result.schema.json` 缺少 `policy_snapshot` 与整数计票结构；`review_manifest.schema.json` 缺少条件互锁；缺少 `review_disposition.schema.json` 与 `admin_override.schema.json`；
3. **PRD 产物规范与 AEP 缺漏**：PRD §2 缺少 `executor.disposition.yml` 规范；AEP/1.1 缺少 Type E `DISPOSITION_REQUIRED` 完整示例；Type B/C/F 存在 base64 违规；
4. **悬空引用与被删章节**：§14.3～§14.5 及第十五部分被意外清空导致正文多处死链；
5. **代码变更清单与代码库实际模块树不符**。

本轮申请在当前提交中**对上述专家提出的全部阻断项实施了 100% 物理闭环修复**，现提请专家委员会对 PRD v2.5 全文档体系进行终局定级复核。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威基准）**：全面融入 D-1～D-9 架构裁定、不可变 `vote_result.json`、§2.5 `executor.disposition.yml`、加权纯整数五重门禁、AEP/1.1 全部 8 类消息、恢复 §14.3～§14.5 与第十五部分全部规范。 |
| 2 | [`docs/schemas/*.schema.json`](../schemas/) | **机器契约库（Draft-07）**：完整提供 `vote_result` v2.0、`review_manifest` v2.5、`review_disposition` v1.0、`admin_override` v1.0、`review_context` v2.5、`macao_config` v2.5、`aep_envelope` v1.1，经严苛测试 100% PASS。 |
| 3 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：逐条记录 9 大架构裁定依据与全量文档迁移图谱。 |
| 4 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：与现有仓库目录结构精确对齐，明确标出新建与变更模块及 5 阶段实施路线。 |
| 5 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部映射表与 Markdown 格式。 |
| 6 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q12～Q15，明确角色投影、独立 Review Disposition 与不可变计票。 |
| 7 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：F-20 标记为由 D-1/D-2 落实，22 条事实全量作为设计约束。 |
| 8 | [`docs/usercases/UC1-init-glm.md`](../usercases/UC1-init-glm.md) | **用例 1 同步**：更新任务态调度与 `role_view` 投影表（加入 `SHOULD_DISPOSE` 与 `NOTIFY_EXECUTOR_DISPOSE`），废除旧 `adoption.yml`。 |
| 9 | [`docs/usercases/UC5-consensus-tally.md`](../usercases/UC5-consensus-tally.md) | **用例 5 同步**：明确 `weighted_2/3_v1` 五重纯整数门禁、P2 全席位 accounted 判定、DEADLOCK 即时落盘与不可变单一写入。 |
| 10| [`docs/usercases/UC6-issue-triage-rework.md`](../usercases/UC6-issue-triage-rework.md) | **用例 6 同步**：升级为独立 `executor.disposition.yml` 意见处置用例，明确 `requires_new_checkpoint` 布尔守卫与 E5a/E6 流转。 |
| 11| [`docs/usercases/UC7-human-override.md`](../usercases/UC7-human-override.md) | **用例 7 重写**：严格对齐 D-1/D-2，DEADLOCK 即时落盘不可变 `vote_result.json`，管理员裁定写入独立 `admin_override.json`，支持 5 大选项与 `--exempt-issue-ids`。 |
| 12| [`docs/usercases/UC8-merge-signoff.md`](../usercases/UC8-merge-signoff.md) & [`UC9-timeout-daemon.md`](../usercases/UC9-timeout-daemon.md) | **用例 8/9 同步**：更新 PRD v2.5 引用、证据归档至 Evidence Ref 与不可变计票约定。 |
| 13| [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整如实记录全部 5 份专家评审报告结论与闭环履历。 |

---

## 3. 五方专家评审意见物理闭环核验表

| 提出专家与项号 | 专家核心关切 | PRD v2.5 落地位置与物理闭环设计 |
|---|---|---|
| **Claude P0-1 / Kimi P0-1 / Grok P0-1** | PRD §3.2/§3.4 状态机与场景推演残留旧语义（DEADLOCK 不落盘、回写终局 vote_result） | 1. §3.2 Layer 1b 判定更新为 `accounted == configured`，废除提前法定人数截断；<br/>2. §3.2 Layer 1c 补充 DEADLOCK（进入 HOLD）、APPROVED 带 disposition 判定与 E5a 改码返工分支，移除 RETRY_REVIEW/CANCELLED 机器决策；<br/>3. §3.4 场景三严格执行 D-1 裁定：Step 5 即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）并 HOLD，Step 6 生成独立 `admin_override.json`，严禁二次回写 `vote_result.json`。 |
| **Claude P0-2 / Codex P1-3 / Kimi P1-7** | `review_context` 机器契约与 PRD §5.2 结构不一致 | 1. 统一为规范的 `code_changes.refs: {base_commit, head_commit}` 嵌套模型；<br/>2. 规范化 9 大必需语义块；<br/>3. Draft-07 Schema 校验测试 100% PASS。 |
| **Claude P1-1 / Grok P1-4 / Codex P1-4** | PRD §2 缺少 `review_disposition` 规范与独立 Schema | 1. 在 PRD §2.5 完整定义 `executor.disposition.yml` 契约（包含 `disposition_status`、`dispositions[]`、`requires_new_checkpoint: boolean`）；<br/>2. 建立 `review_disposition.schema.json` 并通过 Draft-07 强校验。 |
| **Claude P1-2 / Codex P1-2 / Grok P1-2** | AEP/1.1 协议规范不完备（缺 Type E 示例、存在 base64 违规、16 KiB 预算） | 1. AEP 升级为 AEP/1.1 共 8 类消息（Type A～Type H）；<br/>2. 增加 Type E `DISPOSITION_REQUIRED` 完整 JSON 示例；<br/>3. 移除全部 base64 内联，统一为 `{path, evidence_commit, sha256}`；<br/>4. 增加 16 KiB 字节预算与 2048 字节内联文本硬约束。 |
| **Claude P1-3 / Grok P1-3 / Codex P1-3** | §14.3～§14.5 与第十五部分被意外删除导致正文多处死链 | 1. 完整恢复 §14.3（日志与保留）、§14.4（升级与降级）、§14.5（Merge Policy 合并流水线）；<br/>2. 完整恢复第十五部分（§15.1～§15.5 边界声明与非功能需求）；<br/>3. 附录下移至文末。 |
| **Claude P1-4 / Kimi P1-4** | `admin_override` 产物契约与垄断权规范缺失 | 1. 建立 `docs/schemas/admin_override.schema.json`；<br/>2. 明确管理员排他写入权限，记录于 §3.4 生命周期表与 §16.1 垄断权表。 |
| **Claude P1-5 / Codex P1-5** | `review_manifest.schema.json` 缺少条件互锁强校验 | 1. 增加 Schema `allOf` 互锁：BLOCKING $\implies$ vote 必为 NO_APPROVE；YES_APPROVE 不得含 BLOCKING；ABSTAIN 必填理由且 items 必为空；<br/>2. 自动化测试脚本 100% 拦截非法构造。 |
| **Claude P1-8 / Grok P1-8** | 代码变更清单与代码库实际模块树不符 | 在 `docs/v2.5_CODE_CHANGE_INVENTORY.md` 中修正模块映射，精确标注现有文件（`fsm.py`、`controller.py`、`main.py`）与新建模块（`evidence.py`）。 |
| **Qwen P1-1 / Grok P1-1** | 状态与用例文档（PRODUCT-FACTS, UC-1, UC-7）未对账 | 1. `PRODUCT-FACTS.md` F-20 标记为由 D-1/D-2 落实；<br/>2. `UC-1` 移除 `adoption.yml`，对齐 `role_view`；<br/>3. `UC-7` 全面重写为 D-1/D-2 规范。 |

---

## 4. 自动化验证结果（100% 通过）

1. **Schema 机器契约校验**：
   - 脚本 1（PRD §5.2 review_context 实例校验）: **PASS**
   - 脚本 2（PRD §2.1 / §2.2 / §2.3 / §2.5 代码块实例校验）: **4/4 PASS**
   - 脚本 3（PRD §2.2 五重条件互锁测试）: **5/5 PASS（全部非法输入被正确拒绝）**
2. **测试套件回归**：
   - `python3 -m unittest discover tests`: **84/84 PASS**
   - `python3 -m compileall -q src tests`: **0 Errors**

---

## 5. 申请定级建议

建议专家委员会（Claude、Codex、Gemini、Grok、Kimi、Qwen、ZCode）对本闭环申请进行终局复核，正式授予 **L1 DOC-ALIGNED / PG-0** 准入，并批准启动 Phase 1~5 代码实施阶段。
