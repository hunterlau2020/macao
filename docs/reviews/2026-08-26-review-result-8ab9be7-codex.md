# MACAO 最新文档评审结论（PRD v2.2）

- 评审日期：2026-08-26
- 被评审 commit：`8ab9be7`
- 评审范围：`docs/` 下所有当前文档、`docs/schemas/` 及 fixtures
- 权威基准：`docs/MACAO_PRD_v2.md`（v2.2）
- 结论：**PARTIALLY_VERIFIED，未达 L1 DOC-ALIGNED / PG-0。** v2.2 已高质量关闭上一轮大部分 P0/P1：MERGING 中间态、Task/merge 配置、State Store 恢复、Adapter 安全契约、版本化 Schema 与文档索引均有实质落地。但仍有 2 个 P0：最终合并对象可偏离已评审 checkpoint，且 Reviewer 隔离规则在架构图/协议示例中被削弱。

## 已对齐 / 已确认项

| 项目 | 结果 | 证据 |
|---|---|---|
| 合并流水线状态 | **已改善** | PRD §3.3 增加 `MERGING`、E4/E4a/E4b，将审批、CI、签字、push 与 `DONE` 分离；首次成功与返工场景推演同步更新。 |
| 任务与合并配置闭环 | **已改善** | Type A 已携带 `task_id`、source/target branch；§13 增加 `merge` 段；§14.1 定义 Task 最小字段。 |
| 状态持久化与消息可靠性 | **已改善** | §11.4–§11.6 给出 SQLite DDL、写入顺序、三类 Reconcile、ACK/TTL/DLQ 规则。 |
| Adapter 与 Reviewer 安全 | **已改善** | §12.2–§12.6 定义 `execution_mode`、sandbox/worktree、输出自愈和 PTY 进程组回收。 |
| 机器契约 | **已改善且已验证** | 新增五个 draft-07 Schema；`dev.yml`、`review.yml`、`vote_result.json` 正向 fixture 经 `jsonschema` 通过，status/vote 冲突反例被正确拒绝。 |
| 文档格式 | **已验证** | `docs/*.md` 的 9 段 JSON、13 段 YAML 代码块均可解析；全部 Schema JSON 可解析；`git diff --check` 通过。 |
| 历史/实时文档治理 | **已改善** | SRS 历史 JSON 改为 text；Status 改为 `PENDING_REVIEW`，不再提前宣称 L1。 |

## P0：必须先解决

### P0-1 干净 rebase 会改变被合并 commit，却被定义为“不触发新一轮评审”

**证据（SPEC）**：PRD §3.2/§3.3 以 `checkpoint_ref + review_round` 作为产物受理和状态转移的作用域，审核的是该 checkpoint；但 Merge Policy 第 1459 行规定上游领先时 Executor 自动 rebase，且“仅改变 commit 哈希、不触发新一轮评审”。rebase 后的 head commit 已不同于 `vote_result.json.checkpoint_ref` 和两份 `.review.yml` 评审的 commit，E4a 仍可 push 这个未被当前 round 绑定的提交。

**影响**：破坏“评审对象 = 最终合并对象”的核心可审计性。即便无冲突，新的 parent、依赖解析或生成产物也可能改变行为；审计链无法证明被批准的对象实际进入目标分支。

**建议**：二选一并写入 E4a 的硬校验：

1. MVP 最保守方案：`checkpoint_ref` 必须等于最终待 merge 的 source HEAD；rebase 产生任何新 hash 即 E4b 返工/重审。
2. 若保留 clean rebase 优化：定义可验证的等价条件（例如 `git range-diff` 无内容变化、重跑全部质量门禁、生成新的 rebase checkpoint 和明确的人类确认），并将新的 commit 与审批链记录到 `vote_result.json`/审计事件；不满足任一条件即重审。

### P0-2 Reviewer worktree/sandbox 是强制安全边界，却被部署与 AEP 示例写成可选或主工作区

**证据（DOC/SPEC）**：PRD 第 1330–1333 行规定 MVP Reviewer 必须 `sandboxed + 独立 git worktree`；§5.3 也说 MACAO 会注入每个 Reviewer 的 worktree 路径。可是 AEP `REVIEW_REQUEST` 示例第 490–494 行仍给出主工作区 `~/work/macao-demo`，第十六部分单机场景第 1552–1554 行称 Reviewer worktree 为“可选”。

**影响**：按示例实现会把有任意 shell 能力的 Reviewer 放到 Executor 主工作区，与 prompt injection 防护承诺相反；不同团队会得到不一致的安全部署。

**建议**：MVP 中把 worktree 从可选改为强制：

1. AEP 示例改为 `.macao/worktrees/<reviewer_id>/<task_id>/r<round>` 等注入路径；主工作区只能给 Executor/Merge Controller。
2. §16.3 的“同一个工作区 clone”和“可选 worktree”改为“同一仓库、每 Reviewer 独立 worktree”；配置与 Capability preflight 必须拒绝不支持该能力的 Reviewer。
3. 明确 sandbox 生命周期、挂载权限、网络白名单与工作区回收作为 Conformance 必测项。

## P1：发布/进入下一阶段前应修正

| 编号 | 发现与证据 | 建议 |
|---|---|---|
| P1-1 | `review_manifest.schema.json` 允许 `vote: ABSTAIN`，但 `opinion.status` 只有 APPROVED/CHANGES_REQUESTED/REJECTED，且三条 if/then 分别强制 YES/NO；因此任何带必填 status 的 Reviewer manifest 都无法合法表达弃权。PRD §2.3/§6.2 又将弃权作为超时降级的重要结果。 | 增加 `opinion.status: ABSTAIN` → `vote: ABSTAIN` 映射，或明确弃权只能由 Orchestrator 在 `vote_result.json` 写入并从 review manifest 枚举中移除 `ABSTAIN`；补正/反 fixture。 |
| P1-2 | `docs/schemas/README.md` 声称这里是“全部机器可校验契约的唯一权威来源”，但只有 AEP 信封 Schema，`payload` 未按七类消息判别；Task Schema、Capability Manifest Schema、AEP/`macao.yaml` 正反 fixture 也未提供。 | 将 AEP 改为 `oneOf` 的 type-specific payload Schema，补 Task/Capability Schema 和每类关键消息、配置的 valid/invalid fixture；否则把 README 收窄为“当前覆盖的结构契约”。 |
| P1-3 | State Store 的 `artifacts.path` 是全局主键（第 1258–1262 行），但 `.macao/.dev.yml`、`vote_result.json` 和每个 reviewer 的同名文件会被不同任务/轮次重复使用；DDL 无 task_id/唯一复合键，恢复规则也未说明归档后如何保留多任务历史。 | 使用 `artifact_id` 或 `(task_id, kind, checkpoint_ref, review_round, reviewer_id)` 唯一键，保留原路径为非唯一展示字段；Reconcile 按 task+round 恢复。 |
| P1-4 | 审计事件承诺永久保留（第 1449 行），而 `audit.retention_days=90` 表示日志保留；两者的存储位置、备份、磁盘满时策略及敏感日志脱敏后的保留边界未定义。 | 区分 audit event 与 terminal log 的数据分类、保留/清理/备份/容量告警策略，并在 Config Schema 表达相应字段。 |

## P2/P3：可延期但需登记

- `README.md` 第 20 行写“L0~L4”，评审方法论实际只有 L1~L4；统一术语。
- 第十六部分是清晰的 v1.1 规划，但 Schema 尚不接受其 `hosts` 段；应在该章节明确为“草案，不受 v2.2 `macao_config.schema.json` 校验”，或发布 v1.1 schema 版本。
- 产物 Schema 多数未设置 `additionalProperties: false`，有利于前向兼容但会让拼写错误静默通过。建议关键顶层字段采用严格模式，扩展置于显式 `extensions` 块。

## 建议的闭环顺序与验收标准

1. 先关闭 P0-1：将最终 merge HEAD 与评审 checkpoint 的一致性变为 E4a 的机器校验；用“target 分支领先、clean rebase”场景证明不会绕过评审。
2. 关闭 P0-2：把 AEP fixture 和单机场景图改为强制独立 worktree，并用恶意 Reviewer 的写入尝试证明主工作区不可改。
3. 补齐弃权、type-specific AEP/Task/Capability Schema 与 fixtures（P1-1/P1-2），再用 Adapter Conformance 验证。
4. 处理 State Store 任务隔离与保留策略（P1-3/P1-4）。以上关闭并经独立复审后，方可定级 **L1 DOC-ALIGNED / PG-0**；当前仍不应开始依赖该规格的正式实现。

## Reviewer 自审记录

本轮除字段名和代码块格式外，重点检查了“安全强制规则是否被架构示例削弱”“状态/审计引用是否仍绑定同一个 commit”“Schema 枚举是否能表示正文的所有业务结果”。验证只覆盖文档、Schema 与 fixture；未声称真实 CLI、sandbox 或 git rebase 行为已实际测试。
