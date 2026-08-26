# MACAO PRD v2.3 独立复审报告（响应 review-request-PRD-v2.3）

> **评审日期**：2026-08-26  
> **评审角色**：Gemini (Antigravity AI)  
> **被评审 Commit**：`cc77a94`（PRD v2.3）  
> **复审申请来源**：[`docs/reviews/2026-08-26-review-request-PRD-v2.3.md`](2026-08-26-review-request-PRD-v2.3.md)  
> **评审范围**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md)（v2.3 权威基准）、`docs/schemas/*`（含新增 `review_context.schema.json` 与 9 个 fixtures）、[`docs/EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md)、[`docs/IMPROVEMENT_SUMMARY.md`](../IMPROVEMENT_SUMMARY.md)、[`docs/README.md`](../README.md)、[`docs/reviews/STATUS.md`](STATUS.md)  
> **定级申请目标**：L1 DOC-ALIGNED / PG-0

---

## 评审核心结论

| 评审维度 | 结论判定 | 评级 / 状态 | 核心事实依据 |
|---|---|---|---|
| **机器契约与语法校验** | **完全通过（14/14 PASS）** | ✅ **VERIFIED** | 6 个 Draft-07 Schema 自检通过；6 个有效 fixture / 3 个无效 fixture 行为完全符合预期；PRD 内嵌 8 个 JSON / 5 个 YAML、执行摘要 3 产物示例、改进摘要 Context 示例全部通过对应 Schema；`git diff --check` 无空白错误。 |
| **review_context 单一模型** | **完全通过（闭环成功）** | ✅ **VERIFIED** | §2.4 最小子集与 §5.2 完整模型顶层键集合（8 块）与嵌套路径（`code_changes.refs.*`）严格一致；`review_context.schema.json` 完美兼容两者。 |
| **10 态 FSM 与 Deadlock 终局** | **部分通过，存在关键缺口** | ⚠️ **PARTIALLY_VERIFIED** | `vote_result.schema.json` 引入 `resolution` 字段解决了终局序列化问题；但 Deadlock 判定到人工接管的**入口转移边**在 §3.3 仍未独立；PRD §3.4 缺少 Deadlock/RETRY/CANCEL 的实际推演文本。 |
| **阶段门禁裁决** | **维持 PENDING_REVIEW** | 🟡 **未达 L1 / PG-0** | 格式与数据结构层已全面达标；但核心状态机仍存 2 个 P0 级规则一致性缺口（Rebase 哈希一致性、Worktree 强制性被表格削弱）与 1 个 P1（Deadlock 入口边/场景推演），待收尾闭环后定级。 |

---

## 一、机器校验复现矩阵（独立执行实测）

严格按照申请文档第四节指引，在独立 Python 3 环境下通过 `jsonschema` 与 `PyYAML` 进行了机器校验：

| 校验项 | 校验规则 / 目标 | 实测结果 | 证据位置 |
|---|---|---|---|
| **Schema 自检** | 6 个 `docs/schemas/*.schema.json` 经 `Draft7Validator.check_schema` | **全部 PASS** | `docs/schemas/*.schema.json` |
| **有效 Fixtures** | 6 个 valid fixture 经对应 Schema 校验 | **全部 PASS** | `docs/schemas/fixtures/valid/*` |
| **无效 Fixtures** | 3 个 invalid fixture 拦截测试 | **全部正确拒绝** | `aep_unknown_type` / `context_missing_refs` / `review_status_vote_conflict` |
| **PRD AEP 信封** | 7 个 AEP 消息示例 vs `aep_envelope.schema.json` | **全部 PASS** | PRD §2.4（Type A~G） |
| **PRD Review Context** | §2.4 Type B `payload.review_context` 与 §5.2 完整模型 vs `review_context.schema.json` | **全部 PASS** | PRD §2.4（L488-554）、§5.2（L958-1035） |
| **PRD 产物示例** | §2.1 `.dev.yml`、§2.2 `.review.yml`、§2.3 `vote_result.json`、§13 `macao.yaml` vs 对应 Schema | **全部 PASS** | PRD §2.1、§2.2、§2.3、§13 |
| **执行摘要示例** | EXEC 内 `.dev.yml`、`.review.yml`、`vote_result.json` vs 对应 Schema | **全部 PASS** | `EXECUTIVE_SUMMARY.md:126-210` |
| **改进摘要示例** | IMPROVEMENT_SUMMARY 内 `review_context` 示例 vs `review_context.schema.json` | **全部 PASS** | `IMPROVEMENT_SUMMARY.md:169-220` |
| **空白与格式** | `git diff --check` 扫描 | **0 错误** | 全仓 |

---

## 二、复审申请四大重点核查区深度复核

### 1. [核查区 1] `review_context` 单一结构一致性：✅ 完全确认（PASS）
- **核查事实**：
  - §2.4 最小子集（Type B payload）与 §5.2 完整模型拥有完全相同的顶层键集合：`dev_checkpoint`, `repository`, `code_changes`, `quality_snapshot`, `task_info`, `executor_self_assessment`, `history`, `references`；
  - 核心变更路径统一收敛为 `code_changes.refs.{base_commit, head_commit}`，无任何扁平化或歧义路径；
  - `docs/schemas/review_context.schema.json` 将传输必需块（`dev_checkpoint`, `repository`, `code_changes`, `quality_snapshot`, `task_info`）设为 required，其余扩展块设为 optional，同时完美兼容最小子集与完整模型。

---

### 2. [核查区 2] Consensus Deadlock 流程唯一性与终局落盘：⚠️ 存在缺口（未完全闭环）

#### ✅ 已妥善修复部分：
- `vote_result.schema.json:52` 补充了 `"resolution": {"enum": ["automatic", "human_override"]}`，使人工裁定后的终局结果能够合法落盘；
- PRD §3.2 Layer 1c 伪代码将隐式 `else` 改写为显式两分支（`APPROVED → MERGING` / `REWORK_REQUIRED → REWORK`）。

#### ❌ 仍未闭环的逻辑断裂：
1. **Deadlock 检测到接管的入口转移边在转移表中缺失**：
   - PRD §2.3（L395）与决策表（L404–413）明确将 Deadlock 列为独立于 APPROVED/REWORK 的判定结果，§6.1 承诺 10 分钟内触发人工接管。
   - 但在 §3.3 统一转移表中，唯一涉及 Deadlock 的 `E7` 行是“**命令型**”转移（即人工已经给出 choice 之后的落地转移）。当有效票收齐且算得 Deadlock 时，系统**从哪里转移、以何种信号进入人工接管状态**在 E1~E10 中没有对应的入口边（Layer 1c 伪代码因 `vote_result.json` 尚未落盘而跳过 if 块，退化落入 Layer 3 的 60 分钟卡死诊断，与 §6.1 的 10 分钟独立时限冲突）。
2. **§3.4 场景推演证据未同步写入 PRD 权威正文**：
   - `docs/reviews/STATUS.md` 中声称已完成包含 Deadlock 与 RETRY/CANCEL 在内的六场景 SIM 推演（S1~S6）。
   - 但查验权威规范 [`docs/MACAO_PRD_v2.md:843-884`](../MACAO_PRD_v2.md) §3.4，正文中**依然只有“场景推演一（首次批准）”与“场景推演二（返工第二轮）”两个场景**，未包含 Deadlock 1:1 平票、弃权或取消的推演过程。“每步最多命中一个合法转移”的验收标准在权威正文中缺乏实际推演证据。
3. **E7 裁定选项与 E10/CANCEL 终态衔接不完整**：
   - E7 允许用户输入 `--choice APPROVED | REWORK | RETRY_REVIEW | CANCEL`。但伴随动作仅说明了 `APPROVED→E4` 与 `REWORK→E5`，未明确如果用户选择 `CANCEL` 应直接流转至 `E10`（`CANCELLED` 终态）并执行现场归档。

---

### 3. [核查区 3] 10 态 FSM 一致性：⚠️ 存在 1 处 DDL 注释矛盾
- §3.3、§1.2、`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/README.md` 均已统一为 **10 个业务状态**（`IDLE`, `CODING`, `READY_FOR_REVIEW`, `WAITING_REVIEW`, `CONSENSUS_CHECK`, `MERGING`, `DONE`, `REWORK`, `CANCELLED`, `UNKNOWN`）；
- **矛盾点**：PRD §11.4 `tasks` 表 SQLite DDL（`docs/MACAO_PRD_v2.md:1299`）注释仍残留 `-- 当前 FSM 状态（9 态之一）`，属于文档自洽性校验不一致（P2 级勘误）。

---

### 4. [核查区 4] 遗留的两个 P0 级设计语义冲突（延续自上一轮，需同步修正）
1. **P0-1（Rebase 改变 Commit Hash 破坏审计一致性）**：
   - PRD §14.5 第 1 步（第 1504 行）仍规定“上游领先时由 Executor 自动 rebase，且**仅改变 commit 哈希、不触发新一轮评审**”。
   - 必须在 E4a 明确硬校验：若 rebase 改变了 head commit hash，必须触发 E4b 进入新一轮复审（或由受控 range-diff 门禁重新核验），防止未经审查的代码合入主干。
2. **P0-2（Reviewer Worktree 强制性被单机拓扑表削弱）**：
   - PRD §16.3 单机场景表（第 1599 行）仍写为“隔离：**可选 git worktree**”，与 §12.2 / §15.3 的“强制 sandboxed + 独立 worktree”安全红线矛盾，需修正为“强制独立 git worktree”。

---

## 三、待闭环缺陷清单汇总

| 编号 | 严重级 | 模块 | 缺陷事实与证据 | 修正要求 |
|---|---|---|---|---|
| **P0-1** | **P0** | Merge Policy | PRD L1504 允许 rebase 改变 commit 哈希而不触发复审，破坏 `checkpoint_ref` 审计链 | 明确 rebase 产生新 hash 必须触发增量复审，或建立严格的 range-diff + CI 门禁 |
| **P0-2** | **P0** | 安全与拓扑 | PRD L1599 表格将 worktree 标为“可选”，削弱 §12.2 强制隔离安全红线 | 统一修正为“强制独立 git worktree” |
| **P1-1** | **P1** | 状态机与推演 | Deadlock 检测到接管的入口转移边在 §3.3 缺失；§3.4 正文缺少 S3~S6 场景推演证据 | 在 §3.3 增加 Deadlock 入口转移边（或显式写明判定逻辑）；在 §3.4 权威正文补齐 1:1 平票推演 |
| **P1-2** | **P1** | Schema 矛盾 | `review_manifest.schema.json` 顶层 `vote` 含 ABSTAIN，但 `opinion.status` 无 ABSTAIN 导致弃权票校验失败 | 补充 `opinion.status: ABSTAIN → vote: ABSTAIN` 映射 |
| **P2-1** | P2 | DDL 注释勘误 | PRD L1299 DDL 注释仍写“9 态之一” | 修正为“10 态之一” |
| **P2-2** | P2 | E7 选项衔接 | E7 伴随动作未明确 `CANCEL` 选项直接对接 E10 | 补充 `CANCEL → E10` 终态流转说明 |
| **P3-1** | P3 | 简化图措辞 | §1.1 简化图中 Phase 3 标有非正式术语 "REVIEWING" | 登记优化，非阻塞 |

---

## 四、最终定级与闭环操作指引

### 🏁 门禁判定：维持 `PENDING_REVIEW`
- **判定理由**：当前版本（PRD v2.3 / `cc77a94`）在机器契约、Schema 一致性及 Context 架构上取得了决定性进展，**距 L1 仅一步之遥**。但为捍卫 `MACAO_REVIEW_GUIDELINES.md` 的严肃性，在 P0-1（Rebase 哈希审计）、P0-2（Worktree 强制性）及 P1-1（Deadlock 转移边与 §3.4 场景推演落盘）正式写入 PRD 权威正文前，维持 `PENDING_REVIEW` 状态。

### 🛠️ 建议闭环操作步骤：
1. **修正 PRD 正文**：
   - 修正 §14.5 第 1 步 Rebase 审计规则；
   - 修正 §16.3 表格为强制 Worktree；
   - 在 §3.3 补齐 Deadlock 入口边并完善 E7 CANCEL 衔接；
   - 在 §3.4 正文补齐场景三（1:1 平票死锁与人工裁定）；
   - 修正 §11.4 DDL 注释为 10 态。
2. **修正 Schema**：
   - 修复 `review_manifest.schema.json` 中的 ABSTAIN 映射。
3. **完成上述修订后，即可宣告达成 `L1 DOC-ALIGNED / PG-0` 准入门禁，正式启动开发！**

---
*本报告由 Gemini (Antigravity AI) 生成并记录于 `docs/reviews/2026-08-26-review-result-cc77a94-gemini.md`。*
