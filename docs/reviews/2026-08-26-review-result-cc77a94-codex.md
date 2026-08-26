# PRD v2.3 文档对齐复审结论

- **评审日期**：2026-08-26
- **评审对象**：commit `cc77a94`（当前 `main` HEAD）；`MACAO_PRD_v2.md` v2.3、`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/schemas/`、`docs/README.md`
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§10；以 `MACAO_PRD_v2.md` 为权威规范
- **结论**：**未达到 L1 DOC-ALIGNED / PG-0，维持 PENDING_REVIEW。** 所有申请列出的格式/fixture 校验已经通过，但仍有 3 个会改变已评审代码、破坏 Reviewer 隔离或使 Deadlock 终局无法唯一落盘的 P0。

## 已对齐 / 已确认项

- `review_context` 的 §2.4 Type B、§5.2 完整模型和 `IMPROVEMENT_SUMMARY.md` 示例使用相同顶层键及嵌套路径；三者均通过 `review_context.schema.json`。Type B 见 `docs/MACAO_PRD_v2.md:491-545`，完整模型见 `:958-1035`，改进摘要见 `docs/IMPROVEMENT_SUMMARY.md:169-220`。
- 机器校验复现通过：6 个有效 fixture 被接受、3 个无效 fixture 被拒绝；PRD 的 8 个 JSON 与 5 个 YAML 代码块均可解析；7 个 AEP 信封、Type B 的 `payload.review_context`、§2.1/§2.2/§13 示例、执行摘要的三类产物和改进摘要 Context 都通过对应 Schema；`git diff --check ec9d841..cc77a94` 无空白错误。
- 权威转移表已列出 10 个业务状态，并引入 E9（重试）与 E10（取消）及 `CANCELLED` 终态，见 `docs/MACAO_PRD_v2.md:819-841`。§6.1 的 Deadlock 提示已补 `RETRY_REVIEW`，见 `:1100-1105`。

## P0：必须先解决

| 编号 | 可复现证据 | 风险与修正要求 |
|---|---|---|
| P0-1 | `docs/MACAO_PRD_v2.md:1504` 规定上游领先时由 Executor 自动 rebase，且“仅改变 commit 哈希、不触发新一轮评审”；而评审基准是 `checkpoint_ref`（`:812`、`:824`）。 | rebase 会生成与已获批准 checkpoint 不同的新 commit；即使没有冲突，最终合入物也不再是 Reviewer 审过的对象。改为：rebase 后更新 checkpoint、重新生成 `.dev.yml` 并进入新的评审轮，或明确只允许不会重写被评审 commit 的合并策略；两者只能择一并写入转移表和验收用例。 |
| P0-2 | MVP 安全契约要求 Reviewer 强制 `sandboxed` + 独立 worktree（`docs/MACAO_PRD_v2.md:1373-1378`），§5.3 也称分发前创建独立 worktree（`:1045-1050`）；但同一 MVP 部署拓扑写成“同一个工作区 clone”并把 worktree 标为“可选”（`:1590-1599`），Type B 示例的 `workspace_path` 也未标明其必须是被注入的隔离 worktree（`:497-500`）。 | 相同的 MVP 场景同时要求和允许不隔离执行，无法安全实现。将 §16.3、Type B 和实际拓扑统一为“每个 Reviewer 必有独立 worktree/sandbox”；若确有不隔离模式，须降为非 MVP、禁止执行命令并另设显式配置与风险边界。 |
| P0-3 | E7 允许 `APPROVED / REWORK / RETRY_REVIEW / CANCEL`，并要求“裁定结果落盘为终局 `vote_result.json`”（`docs/MACAO_PRD_v2.md:831`）；但只明确 APPROVED→E4、REWORK→E5，CANCEL 与 E10 没有连接。`HUMAN_OVERRIDE_REQUEST` 的选项也没有 CANCEL（`:672-688`）。同时 `vote_result.schema.json:6,51-67` 要求 decision 只能是 APPROVED/REWORK_REQUIRED，`resolution` 非必填，`next_step.action` 没有 CANCEL，故无法表示或强制审计 RETRY_REVIEW/CANCEL 的人工裁定；生命周期表也只定义 E4/E5 后归档（`MACAO_PRD_v2.md:845-851`）。 | 1:1 僵局选择 RETRY_REVIEW 或 CANCEL 时，终局记录、唯一转移和归档均无法从规范推出，违背本轮重点核查项。为四个 choice 建立一个可校验的、穷尽的终局模型：例如 `override_choice` 为必填枚举，明确 APPROVED→E4、REWORK→E5、RETRY_REVIEW→E9、CANCEL→E10，并规定 E9/E10 的记录与归档；或将 CANCEL 明确为独立取消命令并从 E7/override 枚举中移除。随后新增四分支正反 fixture 和场景推演。 |

## P1：进入下一阶段前应修正

| 编号 | 证据 | 修正要求 |
|---|---|---|
| P1-1 | 10 态权威表见 `docs/MACAO_PRD_v2.md:837`，但 State Store DDL 注释仍称“9 态之一”（`:1294-1302`）；执行摘要的人工接管表仍只给 `APPROVED`/`REWORK`（`docs/EXECUTIVE_SUMMARY.md:244-253`），遗漏重试/取消。 | 将 DDL 注释和摘要操作统一为 10 态/E7-E10 的真实契约，并把 CANCEL 的最终语义与 P0-3 一并定稿。 |
| P1-2 | `.review.yml` 的 `vote` 枚举允许 `ABSTAIN`（`docs/schemas/review_manifest.schema.json:59`，PRD `:305`），但必填 `opinion.status` 只有 APPROVED/CHANGES_REQUESTED/REJECTED（Schema `:22-27`；PRD `:308-317` 的映射也无弃权）；三个条件分支使三种 status 分别强制 YES/NO，因而不存在合法的 Reviewer 弃权 manifest。 | 明确弃权只可由 Orchestrator 在 `vote_result.json` 合成并从 `.review.yml` 删除 ABSTAIN，或增加与 ABSTAIN 一致的 opinion 状态/映射和 fixture；当前“标记为弃权”流程不可由现有 manifest 表达。 |
| P1-3 | PRD 已为 v2.3（`docs/MACAO_PRD_v2.md:1`），但文档地位仍将自身和摘要称为 v2.0（`:5,12-14`）；`docs/EXECUTIVE_SUMMARY.md:3`、`docs/README.md:3` 仍写当前 v2.2；多份既有 Schema 的 `$id` 仍为 `v2.2`，如 `docs/schemas/vote_result.schema.json:3`、`review_manifest.schema.json:3`。 | 统一版本标识；若 Schema 未升级是有意兼容策略，应在 PRD/README 中声明 Schema 独立版本和兼容关系，而非同时称“随 PRD 版本号走”（PRD `:1395`）。 |

## P2/P3：可延期但需登记

- `IMPROVEMENT_SUMMARY.md:157-162` 的文字清单仍写 `quality_metrics`，实际唯一字段为 `quality_snapshot`；虽不影响其 YAML 示例通过校验，仍应改名以免读者照抄旧字段。
- `EXECUTIVE_SUMMARY.md:118` 仍把文件握手称为“100% 可靠”；第 70 行的“全文数字均为设计目标”虽可覆盖它，建议就地标注，降低被摘录时误读的风险。

## 交叉文档需做的文字修订

1. 同时更新 PRD §1.1、§3.3、§3.4、§6.1、§11.4、§14.1、§14.5、§16.3 与 Schema/fixtures，确保 P0-1～P0-3 各分支仅有一个 checkpoint、状态和审计结果。
2. 更新 `EXECUTIVE_SUMMARY.md` 的 Deadlock 操作、版本号和就地目标值说明，更新 `IMPROVEMENT_SUMMARY.md` 的旧字段名，更新 `README.md` 和所有 Schema `$id` 的版本策略。
3. 在上述 P0/P1 全部关闭且经独立复审前，`docs/reviews/STATUS.md` 应继续为 `PENDING_REVIEW`；本次不修改实时门禁状态。

## 建议的闭环顺序与验收标准

1. 先定 P0-3 的四个 Deadlock choice 及取消的唯一命令/产物语义，补齐 Schema 的必填字段、转换表和 E9/E10 生命周期。
2. 消除 P0-1、P0-2 的安全与审计冲突，补充“干净 rebase”和“Reviewer 执行命令”两个反例场景。
3. 修正 P1 后重新运行本申请的全部机器校验，并额外验证：每一种 human override 都有且只有一个合法状态转移、终局记录和归档结果；ABSTAIN 的唯一合法载体也有正/反例。

## Reviewer 自审记录

- 已按方法论 §9 重查字段读取路径、计划性声明、确定性用语和全部 YAML/JSON 代码块。上一轮遗漏了合并 rebase 与部署拓扑对安全契约的交叉矛盾；本轮已将其登记为 P0。未以 STATUS 或先前 reviewer 的结论替代复核证据。
