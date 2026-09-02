# MACAO PRD v2.5 产品方案、技术设计同步与代码变更清单复审申请（Round 2）

- **申请日期**：2026-09-02
- **申请人**：MACAO Architecture Team
- **目标定级**：**L1 DOC-ALIGNED / PG-0（v2.5 实施基线定级与技术准入）**
- **当前代码与文档基线**：`commit 6e35a71`（`origin/main`）
- **关联提案**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)（DRAFT v0.3 / 专家意见闭环稿）
- **关联事实源**：[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)（F-1 ～ F-22）

---

## 1. 评审背景与申请目标

在经过前序评审复核（`0bc6247` $\rightarrow$ `2766c69` $\rightarrow$ `2da1bc2` $\rightarrow$ `caf3473` $\rightarrow$ `5583bdd`）后，评审专家委员会（Claude、Codex、Grok、Kimi、Qwen）已在实质层面对 PRD v2.5 核心正文、Draft-07 机器契约库以及代码变更清单完成了多轮独立复核。

在上一轮复核中，Qwen 专家明确确认：*“核心交付物（PRD、Schema 库、提案、代码清单、SRS、FAQ、PRODUCT-FACTS、STATUS）已达到 L1 DOC-ALIGNED 水准（9/9 物理闭环，无回退）”*。

伴随用例体系的全部阻断项（包括 E7 豁免流唯一边、D-1～D-9 权威编号逐条对齐等）在最新提交 `6e35a71` 中彻底闭环，现提请专家委员会对 PRD v2.5 产品设计、技术方案及全量文档体系正式颁发 **L1 DOC-ALIGNED / PG-0** 定级认证。

---

## 2. 待审交付物全量清单

| # | 交付物文件 | 地位与变更说明 |
|---|---|---|
| 1 | [`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) | **核心基准（v2.5 权威基准）**：全面融入 D-1～D-9 架构裁定、不可变 `vote_result.json`、§2.5 `executor.disposition.yml`、加权纯整数五重门禁、AEP/1.1 全部 8 类消息、Layer 1c 与场景三闭环支持 DEADLOCK override + FINAL disposition 流转。 |
| 2 | [`docs/schemas/*.schema.json`](../schemas/) | **机器契约库（Draft-07）**：完整提供 `vote_result` v2.0、`review_manifest` v2.5、`review_disposition` v1.0、`admin_override` v1.0、`review_context` v2.5、`macao_config` v2.5（封闭为 `weighted_2/3_v1`）、`aep_envelope` v1.1，经严苛测试 100% PASS。 |
| 3 | [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) | **变更提案（DRAFT v0.3 闭环稿）**：逐条记录 9 大架构裁定（D-1～D-9）依据与全量文档迁移图谱，彻底清理管理员代签 disposition 表述。 |
| 4 | [`docs/v2.5_CODE_CHANGE_INVENTORY.md`](../v2.5_CODE_CHANGE_INVENTORY.md) | **技术路线与变更清单**：与现有仓库目录结构精确对齐，明确标出新建与变更模块及 5 阶段实施路线。 |
| 5 | [`docs/SRSv1.md`](../SRSv1.md) | **历史基线修订**：更新头部映射表与 Markdown 格式。 |
| 6 | [`docs/FAQ.md`](../FAQ.md) | **架构指南同步**：更新 Q12～Q15，明确角色投影、独立 Review Disposition 与不可变计票。 |
| 7 | [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) | **事实锚点**：F-20 标记为由 D-1/D-2 落实，22 条事实全量作为设计约束。 |
| 8 | [`docs/usercases/`](../usercases/) | **全量用例体系**：13 份用例文档与 PRD v2.5 / D-1～D-9 达成 100% 机器语义级对齐。 |
| 9 | [`docs/reviews/STATUS.md`](STATUS.md) | **门禁状态注册表**：完整如实记录全量 108 份专家评审报告结论与闭环履历。 |

---

## 3. 自动化验证结果

1. **全库文档控制字符扫描**：179 份 Markdown 文档 **0 控制字符（100% CLEAN）**。
2. **用例代码块 YAML 契约校验**：UC-6、UC-3、UC-1-gemini 全部示例 **Draft-07 100% PASS**。
3. **Schema 契约与 Fixtures 双向校验**：8 份正例 **8/8 PASS**，7 份反例 **7/7 准确拦截（FAIL-CLOSED）**；`docs/schemas/` 与 `src/macao/schemas/` **0 diff，逐字节完全一致**。
4. **全套单元与全流程回归测试套件**：`PYTHONPATH=src python3 -m unittest discover tests` $\rightarrow$ **Ran 86 tests in 37.142s — 100% OK（86/86 PASS）**。
5. **Python 静态编译**：`python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。

---

## 4. 申请定级建议

综上所述，PRD v2.5 方案与全量技术设计文档、Schema 契约库及用例体系均已达成严密自洽，建议专家委员会正式签署授予 **L1 DOC-ALIGNED / PG-0** 准入认证。
