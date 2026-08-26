# MACAO 最新文档评审结论（PRD v2.1）

- 评审日期：2026-08-26
- 被评审 commit：`684a012`
- 范围：`docs/` 下 PRD、执行摘要、改进总结、历史 SRS、评审方法论、Live Status 及既有评审结论
- 权威基准：`docs/MACAO_PRD_v2.md`（v2.1）
- 结论：**核心文档已实质对齐，上一轮 P0 全部关闭；可进入受控 PoC，但尚不宜宣告完全 L1 DOC-ALIGNED。** 余下问题均为 P1/P2，集中在可配置字段的闭环、故障恢复的一致性规则与跨文档引用精度。

## 已对齐 / 已确认项

| 项目 | 结果 | 证据 |
|---|---|---|
| 产物遮蔽与状态优先级 | **已关闭** | PRD §3.2 第 703–778 行按当前 FSM、checkpoint 与 round 作用域读取；§3.3/§3.4（第 780–838 行）将命令/产物统一登记，并定义消费、归档和首次/返工场景推演。 |
| Review Context 契约 | **已关闭** | AEP 第 478–534 行、Context 工作流第 988–1022 行统一使用 `code_changes.refs.*`；`repository` 块和 `macao.yaml` 回退解析已经定义。抽取 `REVIEW_REQUEST` JSON 后，实际可读出 `~/work/macao-demo`、`b2c3d4e`、`a1b2c3d`。 |
| 产品使用流程 | **明显完善** | PRD 第 1281–1365 行新增单一配置源、preflight/init/doctor/task/status/override、串行并发边界和 Merge Policy。 |
| 跨 CLI 接入 | **明显完善** | PRD 第 1236–1277 行新增 Adapter Contract、能力矩阵及含断连、幂等、限流和凭据失效的 conformance 要求；产品边界明确收敛为固定三 CLI 本地 PoC（第 1369–1373 行）。 |
| 评审与安全边界 | **已补齐设计层约束** | 第 1375–1400 行补充返工上限、prompt injection、凭据/日志、第三方服务条款、成本计量及评审有效性测试计划。 |
| 历史文档和实时状态治理 | **已改善** | SRS 的历史伪 JSON 已改为 `text`；方法论将 Live Status 移到 `docs/reviews/STATUS.md`。 |
| 代码块格式 | **已验证** | 对 `docs/*.md` 中全部 9 段 `json` 代码块执行 `jq empty`、全部 12 段 `yaml` 代码块执行 Ruby Psych 解析，均通过；`git diff --check` 通过。 |

## P0：必须先解决

无。上一轮 P0-1（持久 `.dev.yml` 遮蔽）与 P0-2（Context 的扁平/嵌套路径冲突）均有可追溯的规范修订和场景验证。

## P1：发布/进入下一阶段前应修正

| 编号 | 发现与证据 | 建议 |
|---|---|---|
| P1-1 | `repository` 实际位于 `payload.review_context.repository`（PRD 第 484–503 行），而第 533 行及第 1022 行写成 `payload.repository`。尽管 §5.3 的消费路径正确，这会误导新的 Adapter 实现。 | 统一正文为 `payload.review_context.repository`，或将 repository 上移到真正的 `payload.repository` 并同步所有示例/`jq` 命令；只能保留一种路径。 |
| P1-2 | 用户旅程要求 `macao task create --branch feature/x`（第 1335 行），但 `DEVELOPMENT_STARTED` AEP 示例没有 branch 字段（第 450–462 行）；Merge Policy 又引用未出现在 `macao.yaml` 示例中的 `merge.ci_gate_command` 和 `merge` 段（第 1362–1365 行）。 | 定义 `Task` 最小 Schema，并在 AEP/State Store 中保存 `source_branch`、`target_branch`、任务 ID；把 `merge` 段及 CI gate 的默认值、启用条件和失败语义补入 `macao.yaml` Schema。 |
| P1-3 | 文档声明 State Store 与 git 产物“双写”，崩溃后可由二者重建（第 1219–1221 行），但没有事务顺序、版本/事件序号、冲突判定和恢复算法。 | 定义 append-only audit event 的 sequence/round/ref、写入顺序与恢复优先级；覆盖“SQLite 已写但 git 未提交”“git 已提交但 SQLite 未写”“归档中崩溃”三种恢复场景。 |
| P1-4 | 文中多处要求 JSON Schema 校验（如第 1325 行），但仓库只给示例和文字规则，未给三类产物、AEP、`macao.yaml` 的正式 Schema 或字段必填表。 | 在 `docs/schemas/`（或 PRD 附录）发布版本化 JSON Schema，并以正/反 fixture 作为 Adapter Conformance 的输入。 |
| P1-5 | `STATUS.md` 第 6 行仍记录上一次“未达 L1 / PG-0”的结论，第 7 行却标为当前 **PG-0**；而方法论第 70 行规定 PG-0 以前提 L1。当前 v2.1 刚修订、尚未经本次结论回填，状态含义不唯一。 | 本次结论确认并关闭 P1 后再更新 Status；在此之前标记为 `PENDING_REVIEW`，不要同时声明“未达 L1”与“当前 PG-0”。 |

## P2/P3：可延期但需登记

- `EXECUTIVE_SUMMARY.md` 第 409 行仍提及 `macao checkin`，PRD v2.1 的用户命令表没有定义该命令。应将其纳入 Adapter/CLI 命令表或删除该兜底说明。
- 摘要与改进总结仍以“v2.0”为历史叙事标题；虽然开头已指向 v2.1 PRD，不影响当前设计，但下次版本整理时建议更新标题/措辞，避免读者误解其覆盖范围。
- `min_effective_votes` 在配置示例中为固定 2，同时注释写为 `⌈2N/3⌉`；固定三 CLI 的 MVP 无影响。未来允许 N 变化时，应由 Loader 推导、校验或明确该字段的覆盖优先级。

## 建议的闭环顺序与验收标准

1. 先统一 `repository` 路径，并为任务/分支/合并补齐 Schema（P1-1、P1-2）。用一个 `task create → DEVELOPMENT_STARTED → REVIEW_REQUEST → merge` fixture 验证字段不丢失。
2. 定义 State Store 与 git 的崩溃恢复顺序（P1-3），至少手工推演并记录三种半完成写入场景。
3. 发布版本化 Schema 和正反 fixture（P1-4）；将其接入 §12.4 Adapter Conformance。
4. 更新 `STATUS.md` 后复审。若 P1 全部关闭，可给出 **L1 DOC-ALIGNED / PG-0**；代码、测试和真实 CLI 兼容性尚未存在，不能外推至 L2 以上。

## Reviewer 自审记录

本轮复查了上一轮遗漏模式：生产者 JSON 与消费者 `jq` 路径、持久产物的作用域、配置字段是否被下游流程消费，以及所有 Markdown JSON/YAML 的可解析性。未声称代码或厂商 CLI 已验证；本结论仅覆盖文档与手工 fixture 级证据。
