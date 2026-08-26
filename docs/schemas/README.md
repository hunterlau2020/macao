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
- `review_manifest.schema.json` 内含 `opinion.status ↔ vote` 映射的 if/then 形式化约束（与 PRD §2.2 的映射表一致），不一致即校验失败——这就是"无效产物"判定的机器可执行定义。
- `review_context.schema.json` 固化 PRD §5.2 的唯一权威结构：两个传输块 + 六个语义块为顶层键集；`code_changes.refs.*` 必填；最小子集与完整模型共用同一 Schema。
- **fixtures 覆盖范围**：正例覆盖三类产物、review_context 最小/完整两形态、AEP 信封（REVIEW_REQUEST）；反例覆盖 status↔vote 冲突、context 缺 refs、AEP 未知 type。未覆盖的组合（如 dev/vote_result 的全部非法变体）在 Adapter Conformance 扩展时按需补齐，本文表格如实反映当前覆盖面。
- 字段语义以 `MACAO_PRD_v2.md` 为准；Schema 只约束结构，不重复解释语义。
