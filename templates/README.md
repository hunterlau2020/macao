# MACAO 全生命周期规范模板库

本目录（`templates/`）汇集了 MACAO 架构中各个协作环节的标准化输出物模板。

MACAO 遵循**“双轨约束（Dual-Track Specification）”**模型：
1. **机器轨（结构化信封 / Manifest）**：用严格的 Draft-07 Schema 闭环约束，供编排器（Orchestrator）、状态机（FSM）与守护进程自动解析，驱动任务状态跃迁；
2. **人类/理解轨（标准化 Markdown 文档）**：为人类工程师、管理员及 LLM Agent 提供完整的背景上下文、因果推导、代码 Diff 分析与复现证据。

---

## 模板清单与映射索引

| 环节 | 模板文件 | 对应旅程/用例 | 机器轨伴生产物 (Schema) | 人类/理解轨伴生产物 (Markdown) |
|---|---|---|---|---|
| **1. 需求与任务受理** | [`task-template.md`](task-template.md) | UC-2 任务受理 | Type A AEP 消息信封 | 任务设计与验收卡 |
| **2. 开发与检查点** | [`review-request-template.md`](review-request-template.md) | UC-3 开发与检查点 | `.macao/.dev.yml` (`dev_manifest`) | `docs/reviews/<yyyy-MM-dd>-review-request-<mid>.md` |
| **3. 评审要求与派发** | [`review-instructions-template.md`](review-instructions-template.md) | UC-4 评审派发与审查 | Type B AEP 消息信封 | Reviewer 审查标准与 Prompt 模板 |
| **4. 专家审查报告** | [`review-result-template.md`](review-result-template.md) | UC-4 专家审查输出 | `.macao/.reviews/r<round>/<rev>.review.yml` | `docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<rev>.md` |
| **5. 意见处置与返工** | [`disposition-template.md`](disposition-template.md) | UC-6 意见处置与返工 | `.macao/.dispositions/r<round>/executor.disposition.yml` | 处置答辩与分流说明 |
| **6. 人工接管备忘** | [`admin-override-template.md`](admin-override-template.md) | UC-7 人工接管 | `.macao/admin_override.json` | 人工接管审计备忘录 |

---

## 使用原则

1. **命名规范不可变**：
   - 评审申请文件必须命名为：`docs/reviews/<yyyy-MM-dd>-review-request-<mid>[-<topic>].md`；
   - 评审结论文件必须命名为：`docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<reviewer>.md`；
   - 其中 `<mid>` 必须使用当前被审 Git Commit 的短哈希（如 `95b7b35`），严禁跨轮次同名覆盖。
2. **字段命名唯一**：
   - 时间戳一律使用 `timestamp`（ISO 8601 UTC 格式，如 `2026-09-05T12:00:00Z`），严禁使用已废弃的别名。
3. **机器信封与全文强绑定**：
   - 所有 Manifest 必须包含 `full_document` 对象（含 `path`, `evidence_commit`, `sha256`），实现结构化摘要与长篇 Markdown 报告的确定性密码学绑定。
