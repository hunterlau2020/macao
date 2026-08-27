# MACAO PRD v2.3.1 独立复审结论（语义/产品轴，响应 review-request-PRD-v2.3.1）

- 评审日期：2026-08-27
- 被评审 commit：`403ddc7`（PRD v2.3.1；申请方为 `docs/reviews/2026-08-26-review-request-PRD-v2.3.1.md`）
- 承担轴线：按请求第五节排班，本报告只覆盖**语义/产品轴**（FSM/Deadlock/流程一致性）；安全/审计轴（codex）与治理/Schema 契约轴（opencode）留待其各自报告，本报告不代为宣告三轴共同结论。
- **本轴结论：未发现 P0/P1，仅余可登记的 P3 级观察。** 上轮（`cc77a94`）五份评审的全部 2 P0 + 3 P1，以及本人在 `8ab9be7`/`cc77a94` 两轮报告中持续追踪的 Deadlock 入口边问题，本轮均已在 PRD 正文层面正确落地并可独立验证。

## 一、机器校验复现（独立执行）

```
python3 + jsonschema 4.10.3
```

| 检查项 | 结果 |
|---|---|
| 6 个 `docs/schemas/*.schema.json` 自检 | 全部通过 |
| `fixtures/valid/` 7 例（新增 `vote_result_human_override.json`） | 全部 VALID |
| `fixtures/invalid/` 4 例（新增 `review_abstain_invalid.yml`） | 全部按预期被拒绝（`'ABSTAIN' is not one of ['YES_APPROVE', 'NO_APPROVE']`） |
| PRD §2.4 Type B `review_context`、§5.2 完整模型、§2.3 `vote_result.json` 示例 | 全部 VALID，且 `workspace_path` 已改为注入后的 worktree 路径 |
| EXEC 三产物示例、IMPROVEMENT_SUMMARY `review_context` 示例 | 全部 VALID |

与请求第四节列出的 18 项机器校验一致，独立复核通过，未直接采信申请方数字。

## 二、高风险区逐条核查

### 2.1 P0-1 rebase 豁免废除 —— 确认关闭

`MACAO_PRD_v2.md:1554-1556`（§14.5 步骤 1）已将旧的"rebase 不触发复审"豁免明确废除：E4 后至 push 前任何产生新 commit 的操作（含 clean rebase/cherry-pick/amend）一律判为未评审新对象 → E4b 增量复审；`rebase_before_merge` 在 `macao.yaml` 示例中改为 `false`（`MACAO_PRD_v2.md:1468` 附近），v1.1 受控门禁（`git range-diff` + `rebased_from` 元数据 + 重跑 CI/签字）三条件明确写为"三者齐备方可免重审"，与 MVP 禁用表述不矛盾。E4a 行（`MACAO_PRD_v2.md:827`）新增"push 对象 == `vote_result.json.checkpoint_ref` 硬校验"。结合默认 `ff_only` 策略（push 不产生新哈希），该校验在逻辑上可唯一证明合并对象未偏离评审对象。**确认关闭。**

### 2.2 P0-2 worktree 强制化 —— 确认关闭，未发现残留

逐处核对：
- §12.2（`MACAO_PRD_v2.md:1403-1404`）：`supports_worktree=true` 明确列为 Reviewer 准入硬条件，preflight/Conformance 强制校验；
- §16.3 表格与拓扑图（`MACAO_PRD_v2.md:1616-1630`）：拓扑图改为"主工作区（Executor）+ 每 Reviewer 独立 worktree"；隔离行改"**强制**"，并注明"评审专家绝不进入 Executor 主工作区"；
- §2.4 Type B（`MACAO_PRD_v2.md:498`）与 §5.2（`MACAO_PRD_v2.md:985`）示例的 `workspace_path` 均已改为 `~/work/macao-demo/.macao/worktrees/kimi/r1`；
- 三个 fixture（`review_context_full.json`、`review_context_minimal.json`、`aep_review_request.json`）机器校验通过。

另核查了 `MACAO_PRD_v2.md:1451`（§13 `macao.yaml` 示例的 `project.repository.workspace_path: "~/work/macao-demo"`）——这不是残留问题：该字段是**主仓库/Executor 基准路径**（"workspace 解析的唯一来源"），各 Reviewer 的独立 worktree 路径是在此基准之下按 `.macao/worktrees/<reviewer_id>/<round>` 派生，与 §2.4/§5.2 示例的绝对路径写法是同一套约定的两个层级，不构成"可选/主工作区"表述残留。**确认关闭，未发现新残留。**

### 2.3 Deadlock 入口与终局 —— 确认关闭（本人此前两轮报告的核心追踪项，本轮已实质解决）

本人在 `8ab9be7`（新增 P0）与 `cc77a94`（收窄为 P1）两轮报告中持续追踪的问题——"票已收齐、算出 Deadlock 后，如何在 §6.1 承诺的 10 分钟时限内确定性触发人工接管，而不是退化到 60 分钟的 Layer 3 模糊诊断"——本轮的修法（"并集方案 B"）是把判定逻辑**内联进 E3 的伴随动作**（`MACAO_PRD_v2.md:824-825`）：quorum 达成的同一时刻，若按决策表算出 Deadlock，直接同步发送 `HUMAN_OVERRIDE_REQUEST`（Type G）并 HOLD，且**明确不写 `vote_result.json`**——这就避开了此前"CONSENSUS_CHECK 只能靠读 vote_result.json 才能继续"的路径依赖，不再需要额外的转移表边。这是一个比我此前建议的"新增 E3a 边"更简洁的方案，且逻辑自洽。

更关键的是，此前被我指出"STATUS.md 声称已验证的六场景 SIM，实际未写入 PRD 权威文本 §3.4"的证据缺口，本轮已经**真正写入正文**：`MACAO_PRD_v2.md:888-902`"场景推演三：1:1 平票 → Deadlock → 人工裁定"完整覆盖 APPROVED/REWORK/RETRY_REVIEW/CANCEL 四个分支与弃权变体，并显式声明"步骤 5 期间没有任何 `.review.yml`/`vote_result.json` 处于可被读走状态，不存在 Deadlock 被误读为 REWORK 的路径"。`vote_result.schema.json` 的 `decision` 枚举扩展为四值且用 `if/then` 强制 `RETRY_REVIEW`/`CANCELLED` 必须带 `resolution: human_override`（已机器验证）。**确认关闭。**

### 2.4 ABSTAIN / artifacts —— 确认关闭

- `review_manifest.schema.json:59` 的 `vote` 枚举已移除 `ABSTAIN`（现为 `["YES_APPROVE", "NO_APPROVE"]`），新增反例 fixture `review_abstain_invalid.yml` 机器验证被正确拒绝；`vote_result.schema.json` 的 `votes[].vote` 保留 `ABSTAIN`——这是正确的不对称设计：`.review.yml`（Reviewer 产出）不能表达弃权，`vote_result.json`（Orchestrator 终局产出）才记录弃权，与"弃权仅由 Orchestrator 记票"的口径一致。
- `MACAO_PRD_v2.md:1329-1334`（§11.4 DDL）`artifacts` 表已改为 `artifact_id` 自增主键 + `UNIQUE(task_id, kind, checkpoint_ref, review_round, reviewer_id)`，§11.5 新增"追加语义"说明（新插入行而非同路径 upsert，历史行标记 `consumed` 后只读），与 §3.4 产物生命周期表的归档描述（"复制到 archive 目录"）不冲突——两者分属物理归档与 SQLite 账本两层，互不矛盾。

## 三、附带验证：此前两轮报告的其余遗留项

- `MACAO_PRD_v2.md:1317`（原 `8ab9be7`/`cc77a94` 两轮报告指出的 §11.4 DDL 注释）现已改为"当前 FSM 状态（10 态之一，含 CANCELLED，见 §3.3）"，与全文一致。**确认关闭。**
- `MACAO_PRD_v2.md:85`（§1.1 简化图非正式术语 "REVIEWING"）本轮已改为 `WAITING_REVIEW`；§1.1 图中 "REJECTED" 也已改为 `REWORK_REQUIRED`（`MACAO_PRD_v2.md:97`）。**此前登记的 P3 一并关闭。**
- §14.1 章节引用勘误（原"见 14.6"）已改为"见 14.5"（`MACAO_PRD_v2.md:1524`）。**确认关闭。**

## 四、新观察（P3，登记不阻塞）

- `docs/reviews/STATUS.md:20` 当前把本轮（`403ddc7`）的"评审状态/结论"栏直接写为"修订闭环完成（机验 18/18 PASS）"，而截至本报告提交前，`docs/reviews/` 目录内尚无任何独立评审报告针对 `403ddc7` 落地——该栏目实质是申请方自评而非独立复核结论，容易被后续读者误读为已完成独立验收。建议该列在收到至少一份独立评审前统一标注为 `PENDING_REVIEW`（与本文件同批的申请文档已遵循此惯例），机验通过与独立复审通过是两件事，不应共用同一个"已完成"表述。

## 五、结论与建议

语义/产品轴（FSM 转移完整性、Deadlock 生命周期、review_context 单一结构、worktree 强制化的正文一致性）复核完毕，**未发现新的或残留的 P0/P1**。本报告不单方面宣告 L1 DOC-ALIGNED——按请求第五节的三轴分工，正式定级应等待 codex（安全/审计轴）与 opencode（治理/Schema 契约轴）各自报告后，由三份报告共同确认方可在 `docs/reviews/STATUS.md` 落定级结论。

## Reviewer 自审记录

方法：不采信申请方"已修订"清单的文字描述本身，逐条回到 `MACAO_PRD_v2.md` 原文行号核对，并用 jsonschema 重新实测全部 fixture 与内嵌示例；对本人此前两轮持续追踪的 Deadlock 入口边问题，专门验证了"证据是否真的写入被评审的权威文档正文"（吸取上一轮"STATUS 记录验证结果但未同步进 PRD 正文"的教训）。未验证真实代码、CLI 行为；结论仅覆盖文档、Schema 与 fixture 级证据。
