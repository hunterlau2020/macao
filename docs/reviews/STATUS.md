# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。

- 更新时间：2026-08-26（8ab9be7 三方复审后）
- 最近复审对象：commit `8ab9be7`（PRD v2.2），三份独立评审结论一致：
  - `reviews/2026-08-26-review-result-8ab9be7-codex.md`：PARTIALLY_VERIFIED，未达 L1；发现 P0-1（clean rebase 改变哈希破坏审计一致性）、P0-2（worktree 强制性被架构图/示例削弱）+ 4 个 P1。
  - `reviews/2026-08-26-review-result-8ab9be7-claude.md`：独立核对 codex 全部引用后采纳，追加 P0-3（`vote_result.json.decision` 无法表达 Consensus Deadlock 且伪代码二元误判）+ 3 个 P2/P3。
  - `reviews/2026-08-26-review-result-8ab9be7-gemini.md`：通过实测（含 `jsonschema` 校验）全面确认上述 3 个 P0 缺陷与 4 个 P1 项，给出闭环路线与实施建议。
- 当前等级：**PENDING_REVIEW**
  - 说明：PRD v2.2 已实质关闭 684a012 轮的全部遗留项；但三方独立复审共同锁定了 3 个新的 P0 阻塞性缺陷（集中在决策/安全规则与 Schema/转移表的一致性映射上），待修订闭环后重新申请 L1 / PG-0 定级。
- 本轮版本：PRD **v2.2**（含 `docs/schemas/`、`docs/README.md`）

## 针对 8ab9be7 三方评审的处理状态（本轮，待处理）

| 来源 | 编号 | 发现与危害 | 状态 | 建议处理位置 |
|------|------|------------|------|---------|
| codex / gemini | **P0-1** | clean rebase 改变被合并 commit 哈希却定义为"不触发复审"，导致最终 push 的 commit 脱离已批准的 checkpoint_ref 审计链 | 待处理 | §14.5 步骤 1 / E4a 硬校验（PRD:1459） |
| codex / gemini | **P0-2** | Reviewer worktree 隔离在 §12.2 是强制安全规则，但在 AEP 示例（PRD:493-496）与 §16.3（PRD:1554）仍写为主工作区/可选 | 待处理 | 统一 AEP 示例为 worktree 隔离路径；§16.3 表述改为强制 |
| claude / gemini | **P0-3** | `vote_result.schema.json` 缺少 `DEADLOCK` 枚举；Layer 1c 伪代码非 APPROVED 即判 REWORK，导致 1:1 平票死锁无法触发人工接管；统一转移表缺少 Deadlock 产物边 | 待处理 | `vote_result.schema.json` 增加 `DEADLOCK` 枚举；重构 Layer 1c 伪代码三元分支与转移表 E3a 边；§3.4 补充 1:1 死锁场景推演 |
| codex / gemini | **P1-1** | `review_manifest.schema.json` 顶层 `vote` 含 ABSTAIN，但 `opinion.status` 无 ABSTAIN 且 if-then 强制映射导致合法弃权票永远校验失败 | 待处理 | 补充 `opinion.status: ABSTAIN → vote: ABSTAIN` 映射规则 |
| codex / gemini | **P1-2** | AEP payload 仅为通用 object 缺乏基于 type 的 `oneOf` 强校验；Task / Capability Manifest 缺少独立 Schema | 待处理 | `docs/schemas/` 补齐 type-specific payload 鉴别与对应 fixtures |
| codex / gemini | **P1-3** | State Store `artifacts.path` 为全局主键，多任务/多轮次返工时同名产物会产生主键冲突 | 待处理 | 重构为 `(task_id, kind, checkpoint_ref, review_round, reviewer_id)` 复合主键 |
| codex / gemini | **P1-4** | 审计事件"永久保留"与终端日志 `audit.retention_days=90` 策略未在数据分类与存储层显式解耦 | 待处理 | 明确结构化审计表永久保留 vs 文本日志文件按天轮转清理 |
| claude / gemini | **N1 (P2)** | `macao merge approve` 是默认配置（`require_human_signoff: true`）下的常规必经命令，未列入 §14.2 命令表 | 待处理 | 补入 §14.2 日常运维命令表 |
| claude / gemini | **N2 (P3)** | §14.1 第 6 步引用"见 14.6 Merge Policy"，实际章节号为 §14.5 | 待处理 | 勘误修正为 §14.5 |
| claude / gemini | **N3 (P2)** | §16.3 "其余全自动"表述与默认 `require_human_signoff: true` 强制人工签字步骤存在框架性矛盾 | 待处理 | 措辞补充 "merge approve 完成签字放行" |

## 历史轮次：684a012（PRD v2.1，已在 v2.2 闭环）

| 编号 | 历史发现 | 状态 | v2.2 落地位置与证据 |
|------|---------|------|-------------------|
| F1 (P0) | E4 即达 DONE 与 Merge Policy 的 CI gate 时序矛盾 | 已关闭 | PRD §3.3 新增 `MERGING` 中间态（E4/E4a/E4b）；§14.5 重写合并流水线；§3.4 场景推演同步 |
| F2 (P0) | Reviewer 执行权限边界未定义 | 已关闭 | PRD §12.2 `execution_mode` 强制规则、§12.3 准入矩阵补列、§15.3 补充命令执行风险对策 |
| P1-1 | repository 路径两种写法并存 | 已关闭 | 统一为 `review_context.repository`（PRD §2.4 注 / §5.2 注） |
| P1-2 | Task 缺 Schema/branch 字段；merge 配置段未定义 | 已关闭 | PRD §14.1 Task 最小 Schema、Type A 增 task_id/source/target_branch、§13 merge 段 |
| P1-3 | 双写缺恢复算法 | 已关闭 | PRD §11.4 DDL + §11.5 写入顺序与三场景 Reconcile 规则 |
| P1-4 | 缺版本化 Schema 与 fixtures | 已关闭 | 新增 `docs/schemas/`（5 个 Schema + 正反 fixtures，已通过 jsonschema 校验） |
| P1-5 | STATUS 同时声明"未达 L1"与"当前 PG-0" | 已关闭 | 本文件改为 PENDING_REVIEW 单一表述 |
| 其他 P1~P3 | ANSI清洗/进程组回收/worktree注入/YAML输出自愈/DLQ/README | 已关闭 | PRD §12.5 自愈、§12.6 PTY规范、§11.6 DLQ、§15.4 用量估算、`docs/README.md` |

## 下一步闭环路线

1. **第一步（集中闭环 3 个 P0）**：
   - 锁定 E4a 合并对象的 commit hash 硬校验，明确 rebase 产生新 hash 必须触发复审（或受控 range-diff 门禁）；
   - 统一 AEP 示例与单机场景表为强制独立 worktree 路径；
   - `vote_result.schema.json` 补全 `DEADLOCK` 枚举，重构 Layer 1c 伪代码三元分支与统一转移表 E3a 边。
2. **第二步（补全 Schema 与数据模型 P1 项）**：
   - 修复 review_manifest 中的 ABSTAIN 映射冲突；
   - 重构 State Store artifacts 复合主键；
   - 完善 AEP type-specific payload 鉴别。
3. **第三步（复审定级）**：
   - 补齐 1:1 平票死锁推演场景与 fixtures，完成下一轮独立复审，正式定级 L1 DOC-ALIGNED / PG-0。
