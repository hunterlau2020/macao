# MACAO Schema 与 Fixtures

本目录是 MACAO 全部机器可校验契约的**唯一权威来源**，随 PRD 版本号演进（当前对应 PRD v2.3）。

| 文件 | 校验对象 | 主要消费方 |
|------|---------|-----------|
| `dev_manifest.schema.json` | `.macao/.dev.yml`（解析后的 YAML） | State Recognition Engine（§3.2）、Adapter |
| `review_manifest.schema.json` | `.macao/.reviews/*.review.yml` | Consensus Engine、Adapter |
| `vote_result.schema.json` | `.macao/vote_result.json` | FSM（E4/E5/E7）、审计 |
| `review_context.schema.json` | AEP `REVIEW_REQUEST.payload.review_context`（PRD §5.2 权威模型） | MACAO 下发端、Reviewer Adapter 消费端 |
| `aep_envelope.schema.json` | 全部 7 类 AEP 消息信封 | agmsg 收发两端 |
| `macao_config.schema.json` | `macao.yaml` | Config Loader（§13） |

## 约定

- 均为 JSON Schema draft-07；YAML 产物先解析为对象再校验。
- `review_manifest.schema.json` 内含 `opinion.status ↔ vote` 映射的 if/then 形式化约束（与 PRD §2.2 的映射表一致），不一致即校验失败——这就是"无效产物"判定的机器可执行定义。**v2.3.1 起 `vote` 枚举不再含 `ABSTAIN`**：Reviewer 无弃权通道，弃权票仅由 Orchestrator 在超时降级时写入 `vote_result.json`。
- `vote_result.schema.json`：`decision` 枚举为 `APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED`；`decision ∈ {RETRY_REVIEW, CANCELLED}` 强制 `resolution: human_override`（Deadlock 人工裁定终局的机器保障，PRD §3.3 E7/E9/E10）。
- `review_context.schema.json` 固化 PRD §5.2 的唯一权威结构：两个传输块 + 六个语义块为顶层键集；`code_changes.refs.*` 必填；`repository.workspace_path` 应为 Reviewer **注入后的独立 worktree 路径**（PRD §12.2/§16.3 强制隔离）；最小子集与完整模型共用同一 Schema。
- **fixtures 覆盖范围**：正例覆盖三类产物（含 human_override 终局 vote_result）、review_context 最小/完整两形态、AEP 信封（REVIEW_REQUEST）；反例覆盖 status↔vote 冲突、Reviewer 弃权 manifest（ABSTAIN 死枚举，必须拒绝）、context 缺 refs、AEP 未知 type。未覆盖的组合（如 dev/vote_result/CANCEL 的全部非法变体）在 Adapter Conformance 扩展时按需补齐，本文表格如实反映当前覆盖面。
- 字段语义以 `MACAO_PRD_v2.md` 为准；Schema 只约束结构，不重复解释语义。
