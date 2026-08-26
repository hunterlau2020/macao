# MACAO 文档对齐评审结论（PRD v2.2）

- 评审日期：2026-08-26
- 被评审 commit：`8ab9be7`
- 范围：`docs/` 下 PRD v2.2、执行摘要、改进总结、历史 SRS、评审方法论、Live Status、版本化 Schema + fixtures
- 权威基准：`docs/MACAO_PRD_v2.md`（v2.2）
- 评审角色：kimi
- 结论：**尚未达成 L1 DOC-ALIGNED / PG-0**。v2.2 已关闭上一轮 `684a012` 的全部 P0/P1（MERGING 中间态、执行权限边界、双写恢复、版本化 Schema 等），但本次评审在权威基准 PRD 内部发现核心 Context 契约矛盾，且两份摘要文档的示例与 Schema/事实状态不一致。需先关闭 P0/P1 后再申请 L1 复审。

## 已对齐 / 已确认项

| 项目 | 结果 | 证据 |
|---|---|---|
| 上一轮回闭项 | **已关闭** | `docs/reviews/STATUS.md` 第 15–38 行记录 `684a012` 的 P0/P1 已全部修订；`docs/schemas/` 已发布 5 个 JSON Schema + 4 个 fixture，且 fixture 经验证通过/被拒正确。 |
| MERGING 中间态与 CI gate 回退 | **已关闭** | PRD `docs/MACAO_PRD_v2.md` §3.3 第 783–808 行新增 E4/E4a/E4b；§14.5 第 1455–1466 行定义合并流水线。 |
| Reviewer 执行权限边界 | **已关闭** | PRD §12.2 第 1324–1333 行定义 `execution_mode`；§12.3 第 1335–1341 行准入矩阵强制 Reviewer 为 `sandboxed` + worktree。 |
| 产物路径与 checkpoint 命名 | **已关闭** | `checkpoint_ref`、`review_context.repository`、`.macao/.reviews/<reviewer_id>.review.yml` 等命名已在 PRD §2.2/§2.4/§5.3 统一。 |
| 状态作用域读取与场景推演 | **已关闭** | PRD §3.2 第 703–775 行、§3.4 第 810–849 行定义生命周期与首次/返工场景推演。 |
| Schema 与 fixture 机器可校验 | **已确认** | 运行 `jsonschema` 验证：`valid/dev.yml`、`valid/review.yml`、`valid/vote_result.json` 通过对应 Schema；`invalid/review_status_vote_conflict.yml` 因 status/vote 冲突被正确拒绝。 |
| PRD 自身 JSON/YAML 示例 | **已确认可解析且通过 Schema** | PRD §2.1 `.dev.yml`、§2.2 `.review.yml`、§2.3 `vote_result.json`、§2.4 全部 7 类 AEP 示例、§13 `macao.yaml` 均通过对应 Schema 校验。 |
| 版本一致性 | **已确认** | `docs/README.md`、`docs/MACAO_PRD_v2.md`、`docs/IMPROVEMENT_SUMMARY.md`、`docs/reviews/STATUS.md` 均指向 v2.2。 |

## P0：必须先解决

| 编号 | 发现与证据 | 影响 | 建议 |
|---|---|---|---|
| P0-1 | **PRD 内部核心 Context 契约自相矛盾**。PRD §2.4 Type B `REVIEW_REQUEST` 的 `review_context` 结构（`docs/MACAO_PRD_v2.md` 第 487–523 行）与 §5.2 的 `review_context` 结构（第 923–992 行）不一致：<br>1. 顶层块不同：§2.4 为 `dev_checkpoint`/`repository`/`code_changes`/`quality_metrics`/`task_info`；§5.2 为 `task_info`/`code_changes`/`quality_snapshot`/`executor_self_assessment`/`history`/`references`。<br>2. `code_changes` 子结构不同：§2.4 用 `files_summary`（字符串）；§5.2 用 `summary` + `files_list`（数组）。<br>3. 质量指标块命名与结构不同：§2.4 为 `quality_metrics`（扁平：`tests_passed`/`test_count`/`coverage`/`lint_score`）；§5.2 为 `quality_snapshot`（嵌套：`tests`/`static_analysis`/`performance`）。<br>4. §2.4 缺省 §5.2 中声明为 Reviewer 所需的三块：`executor_self_assessment`、`history`、`references`。<br>§2.4 文字声称"携带完整 `review_context`"，但示例并不完整；§5.3 Reviewer 工作流（第 999–1031 行）消费的 `repository.workspace_path` 和 `code_changes.refs.*` 在两块中均存在，但其余字段无法逐条核验。 | 阻止 L1 DOC-ALIGNED：评审方法论 §2.1 要求"四份文档字段/术语可用同一张对照表逐条核验"；PRD 自身两张表无法对齐。实现者按 §2.4 与按 §5.2 会生成/消费不同 payload，导致 Adapter 互操作失败或 Reviewer 缺少上下文。 | 选定唯一权威结构，全文统一。推荐以 §5.2 的六段式为完整形态，在 §2.4 Type B 示例中补全 `executor_self_assessment`/`history`/`references`，并将 `quality_metrics` 重命名为 `quality_snapshot`、将 `files_summary` 替换为 `summary` + `files_list`；或在 §5.2 顶部明确标注"本节为完整参考模型，§2.4 示例为最小子集"并给出最小子集与完整模型的字段映射表。 |

## P1：发布/进入下一阶段前应修正

| 编号 | 发现与证据 | 影响 | 建议 |
|---|---|---|---|
| P1-1 | **`EXECUTIVE_SUMMARY.md` `.dev.yml` 示例与 Schema 不符**。示例位于 `docs/EXECUTIVE_SUMMARY.md` 第 124–151 行，使用 `coverage: 0.87`（第 141 行），而 `docs/schemas/dev_manifest.schema.json` 与 PRD §2.1 均使用 `test_coverage`；且示例缺少 Schema 必需字段 `review_round`。经验证，该示例无法通过 `dev_manifest.schema.json`。 | 摘要文档的示例会误导实现者直接写出无效产物；与"示例必须可解析"的 L1 条件冲突。 | 将 `coverage` 改为 `test_coverage`，补 `review_round: 1`，其余字段与 PRD §2.1 示例保持一致。 |
| P1-2 | **`EXECUTIVE_SUMMARY.md` `vote_result.json` 示例与 Schema 不符**。示例位于 `docs/EXECUTIVE_SUMMARY.md` 第 180–190 行，缺少 `version`、`review_round`、`vote_breakdown`、`input_artifacts` 等 `docs/schemas/vote_result.schema.json` 的必需字段；且 `next_step` 为字符串 `"Send REWORK_REQUEST to executor"`，而 Schema 要求 `object`。经验证无法通过 Schema。 | 同上，示例与权威 Schema 直接矛盾。 | 重写为与 PRD §2.3 示例一致的最小合规形态（含 `version`、`review_round`、`vote_breakdown`、`input_artifacts`、`next_step` 对象）。 |
| P1-3 | **`EXECUTIVE_SUMMARY.md` `.review.yml` 示例与 Schema 不符**。示例位于 `docs/EXECUTIVE_SUMMARY.md` 第 157–174 行，缺少 `version`、`checkpoint_ref`、`review_round` 等 `docs/schemas/review_manifest.schema.json` 的必需字段；且 `feedback` 被写成数组（`[ { type, severity, ... } ]`），而 Schema 要求 `opinion.feedback` 为对象。经验证无法通过 Schema。 | 同上。 | 补全必需字段，将 `feedback` 改为对象形态（`summary`/`severity_breakdown`/`categories`/`automated_checks`），与 PRD §2.2 示例一致。 |
| P1-4 | **`IMPROVEMENT_SUMMARY.md` 用 ✅ 标记尚未完成的未来目标**。位于 `docs/IMPROVEMENT_SUMMARY.md`：<br>- 第 334–339 行：8 周交付计划每周均标 ✅，暗示已全部完成；<br>- 第 399–404 行：Phase 1 PoC 验证三项假设均标 ✅；<br>- 第 479–483 行：MVP 完成成功指标均标 ✅。<br>但同文档及 PRD 均将 PoC/MVP 描述为 Week 1–2 起的未来工作，仓库中亦无实现代码或测试证据。这违反评审方法论 §9 checklist B："`[x]` / 已完成 / ✅ 是否有对应证据，而非计划？" | 读者会把设计目标/计划误认为已达成事实，影响立项与排期判断。 | 将上述 ✅ 改为 `[ ]` 或文字说明为"目标/待验证"；仅对已有 PoC 报告/测试记录的事实打 ✅。 |
| P1-5 | **`IMPROVEMENT_SUMMARY.md` `quality_snapshot` 示例字段类型不合法**。位于 `docs/IMPROVEMENT_SUMMARY.md` 第 188–193 行：`tests.passed: 24/24 ✅` 为含 emoji 的字符串，而 PRD §5.2 同字段为整数 `passed: 24`；且该示例的 `quality_snapshot` 结构继承自 PRD §5.2，与 PRD §2.4 Type B 的 `quality_metrics` 不一致（已归 P0-1）。 | 示例无法被机器解析；同时加深 Context 结构矛盾。 | 将 `passed` 改为整数（如 `24`），移除 emoji；待 P0-1 解决后统一采用唯一结构。 |

## P2/P3：可延期但需登记

| 编号 | 发现与证据 | 影响 | 建议 |
|---|---|---|---|
| P2-1 | **缺少 `review_context` 与 AEP payload 级 Schema**。`docs/schemas/README.md` 第 5–12 行列出 5 个 Schema，覆盖三类产物、AEP 信封、`macao.yaml`，但未覆盖 `review_context` 结构；AEP 仅覆盖信封，`payload` 为自由对象。PRD §2.4 声称给出 4 类消息"详细格式示例"，但目前只能人眼核对。 | L2 及以后需要机器校验 Adapter 生成的 AEP payload 与 MACAO 下发的 Context；当前缺失会增加代码联调成本。 | 新增 `review_context.schema.json`，并为 7 类 AEP 消息新增 per-type payload Schema（至少覆盖 DEVELOPMENT_STARTED / REVIEW_REQUEST / REVIEW_RESPONSE / REWORK_REQUEST）；将 fixture 扩展为覆盖这些 Schema 的正反例。 |
| P2-2 | **部分 Schema 对嵌套结构约束不足**。`vote_result.schema.json` 未定义 `summary` 与 `next_step` 的内部字段；`dev_manifest.schema.json` 未定义 `artifacts`/`checklist` 元素结构；`review_manifest.schema.json` 的 `opinion.feedback` 仅为 `object`。PRD 示例中这些字段都有具体形态，但 Schema 未 enforce。 | 产物仍可能被解析但字段语义不一致； Adapter Conformance 测试无法细粒度断言。 | 补充嵌套字段定义，保持与 PRD 示例一致；如需允许 Adapter 扩展，可用 `additionalProperties: true` 兜底。 |
| P2-3 | **`EXECUTIVE_SUMMARY.md` 对 `.review.yml` 路径表述过于笼统**。第 25 行仅称".review.yml - 评审意见的投票券"，未说明其实际路径 `.macao/.reviews/<reviewer_id>.review.yml`（PRD §2.2 第 233 行）。 | 新读者可能误解为单文件投票，造成实现偏差。 | 在首次提到 `.review.yml` 时补充路径说明，或加脚注指向 PRD §2.2。 |
| P3-1 | **`IMPROVEMENT_SUMMARY.md` 标题仍以 v2.0 为叙事**。文件名为 "MACAO v2.0 改进对比总结"，正文多处称 "v2.0"；虽然开头已指向 v2.2 PRD，但标题与版本历史中的 v2.2 不完全对应。 | 造成版本叙事混乱，属文案债。 | 下次整理时将标题改为 "MACAO v2.x 改进对比总结" 或保留 "v2.0" 作为该文档的起始版本、在标题中注明 "截至 v2.2"。 |

## 交叉文档需做的文字修订

1. **统一 `review_context` 结构（P0-1）**：
   - `docs/MACAO_PRD_v2.md` §2.4 Type B 示例（第 487–523 行）需与 §5.2（第 923–992 行）对齐。
   - `docs/IMPROVEMENT_SUMMARY.md` §三 Context 示例（第 169–212 行）需与最终选定的权威结构一致。
   - 新增 `docs/schemas/review_context.schema.json` 后，`docs/schemas/README.md` 需更新表格。

2. **修复摘要文档示例以匹配 Schema（P1-1/1-2/1-3）**：
   - `docs/EXECUTIVE_SUMMARY.md` 第 124–151 行 `.dev.yml` 示例。
   - `docs/EXECUTIVE_SUMMARY.md` 第 157–174 行 `.review.yml` 示例。
   - `docs/EXECUTIVE_SUMMARY.md` 第 180–190 行 `vote_result.json` 示例。

3. **修正完成度勾选状态（P1-4）**：
   - `docs/IMPROVEMENT_SUMMARY.md` 第 334–339、399–404、479–483 行的 ✅ 改为 `[ ]` 或"目标"说明。

4. **Schema 完善（P2-1/2-2）**：
   - 扩展 `docs/schemas/` 目录，新增/细化 Schema 后更新 `docs/schemas/README.md` 与 PRD §12.4。

## 建议的闭环顺序与验收标准

1. **优先关闭 P0-1**：在 PRD 内选定 `review_context` 唯一权威结构，同时修订 §2.4 与 §5.2，并给出字段对照表。验收标准：用同一张 JSON Schema 能同时校验 §2.4 Type B 示例与 §5.2 完整示例（允许 §2.4 为最小子集，但字段名与嵌套路径必须一致）。
2. **并行修复 P1-1/1-2/1-3**：重写 `EXECUTIVE_SUMMARY.md` 三处示例，使其通过对应 Schema。验收标准：运行 `jsonschema` 校验三个示例均返回 VALID。
3. **修复 P1-4/1-5**：调整勾选标记与 `quality_snapshot` 字段类型。验收标准：无 `[x]`/`✅` 无证据；示例字段类型与 PRD 一致。
4. **补充 Schema（P2-1/2-2）**：新增 `review_context.schema.json` 与 AEP payload Schema，扩展 fixtures。验收标准：所有新 fixture 正确通过/被拒；`docs/schemas/README.md` 表格更新。
5. **申请 L1 复审**：以上全部关闭后，由另一名 reviewer 独立复审。若仅余 P2/P3，可宣告 **L1 DOC-ALIGNED / PG-0**；代码、CLI 兼容性尚未存在，不能外推至 L2 及以上。

## Reviewer 自审记录

本轮按评审方法论 §9 强制自检：

- **A（字段声明位置 vs 实际读取路径）**：已核对 `repository.workspace_path`、`code_changes.refs.*` 在 PRD §2.4/§5.2/§5.3 中路径一致；但发现 §2.4 与 §5.2 的顶层字段命名不一致。
- **B（`[x]`/`✅` ≠ 完成证据）**：在 `IMPROVEMENT_SUMMARY.md` 中发现多处无证据的 ✅，已登记为 P1-4。
- **C（确定性用语 99%/100%）**：PRD、执行摘要、改进总结均已在显著位置标注"设计目标值/以 PoC 实测为准"，此项无遗漏。
- **D（代码块可执行性）**：已运行 `jsonschema` 验证全部 fixture 与 PRD 示例；发现 `EXECUTIVE_SUMMARY.md` 三处示例与 Schema 不符，已登记 P1-1/1-2/1-3。

本轮未声称任何厂商 CLI 或 Adapter 代码已验证；结论仅覆盖文档静态一致性、Schema 校验与手工场景推演。
