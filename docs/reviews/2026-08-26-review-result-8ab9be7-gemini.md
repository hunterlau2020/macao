# MACAO 最新文档评审报告（PRD v2.2 / Commit 8ab9be7）

> **评审日期**：2026-08-26  
> **评审角色**：Gemini (Antigravity AI)  
> **被评审 Commit**：`8ab9be7`（PRD v2.2）  
> **评审范围**：`docs/` 下全量文档（以 [`MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) v2.2 为权威基准，覆盖 `docs/schemas/`、`docs/schemas/fixtures/`、[`EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md)、[`IMPROVEMENT_SUMMARY.md`](../IMPROVEMENT_SUMMARY.md)、[`SRSv1.md`](../SRSv1.md)、[`MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)、[`STATUS.md`](STATUS.md)）  
> **权威标准**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)

---

## 评审核心结论

| 维度 | 结论判定 | 评级 / 状态 |
|---|---|---|
| **v2.2 演进成果** | **实质关闭上一轮全部遗留项**：MERGING 中间态与 CI gate 回退边、Reviewer 执行权限边界（`sandboxed+worktree`）、SQLite State Store DDL/恢复算法、agmsg DLQ 机制、输出自愈、PTY 规范及 `docs/schemas/` 5 个版本化 Schema 与正反 fixtures 全部落地。 | ⭐⭐⭐⭐⭐ **显著提升** |
| **阶段门禁判定** | **PARTIALLY_VERIFIED，暂未达 L1 DOC-ALIGNED / PG-0**：与 Codex 和 Claude 两份独立评审结论完全一致，本轮发现 **3 个 P0 阻塞性缺陷**（Rebase 破坏审计哈希绑定、Worktree 强制性被示例削弱、Deadlock 决策在 Schema 与状态机中缺失合法表达路径）以及 4 个 P1。 | 🟡 **PENDING_REVIEW（待闭环 P0 后复审）** |

---

## 一、v2.2 已闭环与确认项（VERIFIED）

通过对 `8ab9be7` commit 全量 diff 与相关文件交叉核验，确认上一轮提出的核心问题已高质量闭环：

| 编号 | 闭环项 | 验证事实与证据 | 状态 |
|---|---|---|---|
| 1 | **MERGING 中间态与 CI gate 回退** | PRD §3.3 统一转移表新增 `MERGING` 状态（E4 触发合并，E4a 成功转 `DONE`，E4b 失败转 `REWORK`）；§14.5 重写为完整合并流水线；§3.4 场景推演同步更新。 | ✅ **已闭环** |
| 2 | **Reviewer 执行权限边界** | PRD §12.2 定义 `execution_mode`（`read_only / sandboxed / full`），明确 Reviewer 强制 `sandboxed` + 独立 worktree；§12.3 准入矩阵补齐；§15.3 补充命令执行与代码外传风险对策。 | ✅ **已闭环** |
| 3 | **State Store DDL 与 Reconcile** | PRD §11.4 给出 5 张核心 SQLite 表 DDL（tasks, artifacts, audit_events, overrides, dead_letter_queue）；§11.5 明确写入顺序与 A/B/C 三场景恢复规则。 | ✅ **已闭环** |
| 4 | **输出自愈与 PTY 规范** | PRD §12.5 增加两级输出自愈（Extractor 清洗 + 局部 Re-prompt 纠错，限 1 次）；§12.6 补充非交互参数、ANSI 清洗与 `killpg` 进程组回收规范。 | ✅ **已闭环** |
| 5 | **版本化 JSON Schema 与 Fixtures** | 新增 `docs/schemas/` 目录，包含 5 个 draft-07 Schema；正向 fixture 与反向冲突 fixture 经 `jsonschema` 实测校验通过。 | ✅ **已闭环** |
| 6 | **文档索引与代码块语法** | `docs/README.md` 补齐；全量 Markdown 内 9 段 JSON、13 段 YAML 代码块均通过解析校验。 | ✅ **已闭环** |

---

## 二、P0：阻塞性缺陷（必须在开始正式编码前修正）

### 🚨 P0-1：Clean Rebase 改变被合并 Commit 哈希，破坏“评审对象 = 合并对象”的一致性与审计链

- **证据（SPEC / PRD §14.5 第 1 步）**：
  > PRD 第 1459 行：“上游领先且 `rebase_before_merge: true`，由 Executor 自动 rebase 并重跑本地验证——**rebase 仅改变 commit 哈希、不触发新一轮评审**”。
- **矛盾点与危害**：
  1. 整个 MACAO 状态机与产物生命周期的基石是 **`checkpoint_ref + review_round` 的精确绑定**。Reviewer 签署的 `.review.yml` 与共识记录 `vote_result.json` 针对的是特定 commit（如 `a1b2c3d`）。
  2. 当发生 rebase 时，即便代码内容无逻辑冲突，其 commit hash 也必然变更为新的 commit（如 `c9d8e7f`），甚至因上游改动而改变运行时行为。
  3. 若允许 E4a 直接 push 这个未经任何 Reviewer 签名的全新 commit，不仅**审计链在密码学哈希层面断裂**（无法证明最终 push 的代码等于被批准的代码），更可能将未经审查的隐式行为变更合入主干。
- **建议修复方案（二选一）**：
  - **方案 A（严格安全基线，推荐 MVP 采用）**：待合并的 source commit 必须严格等于 `vote_result.json.checkpoint_ref`；若 target 领先导致无法 Fast-forward，rebase 产生新 commit 后必须强制触发 `E4b`（生成带增量上下文的新轮次复审，确保合入代码 100% 经过审查）。
  - **方案 B（受控 Rebase 门禁）**：若保留自动 rebase 优化，必须在 E4a 前增加硬校验门禁：① `git range-diff` 证明除 parent 变更外无代码差异；② 自动更新生成带有 `rebased_from` 签名的合并元数据；③ CI gate 与人工签字（`macao merge approve`）必须在 rebase 后的新 commit 上重新执行并记录审计日志。

---

### 🚨 P0-2：Reviewer Worktree 强制安全隔离在 AEP 示例与单机拓扑中被削弱为“主工作区/可选”

- **证据（DOC / SPEC 冲突）**：
  1. PRD 第 1333 行与第 1486 行明确声明：“担任 Reviewer 的 CLI 必须 `execution_mode ∈ {read_only, sandboxed}` 且 **MVP 阶段强制 sandboxed + 独立 git worktree**”；
  2. 但在 PRD §2.4 Type B `REVIEW_REQUEST` 消息示例（第 493–497 行）中，`repository.workspace_path` 仍然写为 Executor 的主工作区 `~/work/macao-demo`；
  3. 在 PRD §16.3 单机场景表（第 1554 行）中，隔离策略被描述为：“隔离 \| **可选 git worktree**（`supports_worktree` 能力位）”。
- **矛盾点与危害**：
  - 示例与架构表格将“强制安全红线”降级为“可选/直接使用主工作区”。如果 Adapter 按照 AEP 示例实现，具备任意 Shell 执行能力的 Reviewer 将直接在 Executor 主工作区运行，一旦遭遇恶意代码 Prompt Injection，将直接篡改主工作区文件或窃取未提交代码，彻底击穿安全防御。
- **建议修复方案**：
  1. 将 AEP `REVIEW_REQUEST` 示例中的 `workspace_path` 修正为规范的隔离路径（如 `.macao/worktrees/{reviewer_id}/{task_id}/r{round}`）；
  2. 将 PRD §16.3 单机场景表中的“可选 git worktree”明确改为“**强制独立 git worktree**”；
  3. 在 `preflight` 与 Conformance 准入套件中，将 `supports_worktree == true` 设为 Reviewer Adapter 的硬性前置条件。

---

### 🚨 P0-3：`vote_result.json` Schema 与状态机无法合法表达并处理 Consensus Deadlock（1:1 平票）

- **证据（SPEC / Schema / 伪代码断裂）**：
  1. **业务规则**：PRD §2.3（第 395 行）与决策表（第 404–409 行）明确将 `Consensus Deadlock`（如 2 Reviewer 下的 1:1 平票、低于法定人数、全弃权）作为核心判定结果，要求立即触发人工接管。
  2. **Schema 缺失**：`docs/schemas/vote_result.schema.json` 第 51 行定义为 `"decision": { "enum": ["APPROVED", "REWORK_REQUIRED"] }`，**完全缺少 `"DEADLOCK"` 枚举值**。
  3. **状态机伪代码二元误判**：PRD §3.2 Layer 1c 状态识别伪代码（第 750–751 行）写道：
     ```python
     if result.valid:
         archive_round_artifacts(ref, rnd)
         return (AgentState.DONE if result.decision == 'APPROVED' else AgentState.REWORK)
     ```
     只要 `decision` 不为 `APPROVED`，就一律判定为 `AgentState.REWORK`。
  4. **转移表边缺失**：统一转移表 §3.3 中，仅有针对 APPROVED（E4）和 REWORK_REQUIRED（E5）的产物边，缺少“检测到 DEADLOCK 产物时转移至 `UNKNOWN` / 人工接管”的入口转移边（表中的 E7 仅代表人工做出裁定后的落地命令）。
- **矛盾点与危害**：
  - 在 MVP 明确采用的 2-Reviewer（Codex + Kimi）配置下，**1 赞成 + 1 反对的 1:1 平票是极其常见的高频路径**。
  - 当前设计下，若 Orchestrator 写出包含 `DEADLOCK` 的 `vote_result.json`，会因 Schema 校验失败被判为无效产物；若绕过 Schema，伪代码会将其**静默误判为自动返工（REWORK）**，直接剥夺了用户的人工仲裁权，与决策表规则严重冲突。
- **建议修复方案**：
  1. `vote_result.schema.json` 的 `decision` 枚举扩展为 `["APPROVED", "REWORK_REQUIRED", "DEADLOCK"]`；
  2. 修改 Layer 1c 状态识别逻辑为三元分支：
     ```python
     if result.valid:
         if result.decision == 'APPROVED':
             return AgentState.MERGING
         elif result.decision == 'REWORK_REQUIRED':
             archive_round_artifacts(ref, rnd)
             return AgentState.REWORK
         elif result.decision == 'DEADLOCK':
             trigger_human_override(agent_id='orchestrator', reason='Consensus Deadlock', diagnostic_info=result)
             return AgentState.UNKNOWN
     ```
  3. 在统一转移表 §3.3 中新增一条产物触发转移边（如 `E3a: CONSENSUS_CHECK + decision=DEADLOCK → UNKNOWN (触发 HUMAN_OVERRIDE)`）；并在 §3.4 补充 1:1 平票场景推演。

---

## 三、P1：重要缺陷（发布前/下一迭代应修正）

| 编号 | 模块 | 发现与事实证据 | 建议修复方案 |
|---|---|---|---|
| **P1-1** | Schema 互斥矛盾 | `review_manifest.schema.json` 顶层 `vote` 枚举允许 `ABSTAIN`，但 `opinion.status` 仅有 APPROVED/CHANGES_REQUESTED/REJECTED，且 `if-then` 条件强制 status 必须映射到 YES 或 NO。导致任何合法的弃权票无法通过 Schema 校验。 | 在 `opinion.status` 中增加 `ABSTAIN` 枚举并建立 `ABSTAIN → ABSTAIN` 映射；或明确弃权票仅由 Orchestrator 写入 `vote_result.json`，在 Reviewer manifest 中移除该枚举。 |
| **P1-2** | AEP 消息契约 | `aep_envelope.schema.json` 中的 `payload` 仅定义为通用 `object`，缺乏针对 7 类消息的 `oneOf` 强类型鉴别；且缺少 Task 与 Capability Manifest 的独立 Schema。 | 将 AEP Envelope 改造为基于 `type` 的 `oneOf` 强校验 Schema，并补齐 Task 和 Capability 的独立 Schema 文件与 fixtures。 |
| **P1-3** | State Store 主键冲突 | SQLite DDL 中 `artifacts` 表以 `path TEXT PRIMARY KEY` 作为主键。而在多任务或多轮次返工中，`.macao/.dev.yml`、`vote_result.json` 及各 Reviewer 产物路径完全相同，会导致主键冲突。 | 将主键重构为 `(task_id, kind, checkpoint_ref, review_round, reviewer_id)` 复合主键，或使用自增 `artifact_id`。 |
| **P1-4** | 审计与日志生命周期 | PRD 第 1449 行声明审计事件“永久保留”，第 1416 行又定义 `audit.retention_days = 90`。两者未做数据分类界定。 | 明确解耦：结构化 `audit_events` 永久保留于 SQLite；非结构化 `terminal_logs` 文本文件按 `retention_days` 轮转清理。 |

---

## 四、P2 / P3：次要细节与勘误（登记并随文优化）

- **N1（P2，命令表补齐）**：`macao merge approve` 是默认配置（`require_human_signoff: true`）下正常合并流水线的必经命令，需补入 §14.2 日常运维命令表。
- **N2（P3，章节号勘误）**：PRD §14.1 第 6 步“见 14.6 Merge Policy”修正为“见 14.5 Merge Policy”。
- **N3（P2，用户体感描述修正）**：PRD §16.3 中“其余全自动”修改为“status 查看进度、merge approve 签字放行、override resolve 处理接管，其余自动”。
- **N4（P3，方法论术语对齐）**：`docs/README.md` 中的“L0~L4”修正为方法论正文的“L1~L4”。

---

## 五、闭环路线与实施建议

为确保在启动正式编码前消除所有设计层面的逻辑分叉，建议按以下顺序进行最终闭环：

```text
第一步（集中攻坚 3 个 P0 级设计语义一致性）：
  ├─ 1. [P0-1 闭环] 锁定 E4a 合并对象的 commit hash 硬校验，明确 rebase 产生新 hash 必须重跑复审（或受控 range-diff 门禁）；
  ├─ 2. [P0-2 闭环] 统一 AEP 示例与单机场景表为强制独立 worktree 路径；
  └─ 3. [P0-3 闭环] 补全 vote_result.schema.json 中的 DEADLOCK 枚举，重构 Layer 1c 伪代码与转移表。

第二步（补全 Schema 与数据模型 P1 项）：
  ├─ 4. 修复 review_manifest 中的 ABSTAIN 映射冲突；
  ├─ 5. 重构 State Store artifacts 复合主键；
  └─ 6. 完善 AEP type-specific payload 校验。

第三步（复审定级）：
  └─ 补齐 1:1 平票死锁推演场景与 fixtures，完成下一轮独立复审，正式定级 L1 DOC-ALIGNED / PG-0。
```

---
*本报告由 Gemini (Antigravity AI) 生成并记录于 `docs/reviews/2026-08-26-review-result-8ab9be7-gemini.md`。*
