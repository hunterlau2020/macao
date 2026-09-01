# MACAO Schema 与 Fixtures

本目录是 MACAO 全部机器可校验契约的**唯一权威来源**，随 PRD 版本号演进（当前对应 **PRD v2.5 权威基准**）。

| 文件 | 校验对象 | 主要消费方 |
|------|---------|-----------|
| `dev_manifest.schema.json` | `.macao/.dev.yml`（解析后的 YAML） | State Recognition Engine（§3.2）、Adapter |
| `review_manifest.schema.json` | `.macao/.reviews/*.review.yml` | Consensus Engine、Adapter |
| `vote_result.schema.json` | `.macao/vote_result.json` | FSM（E3/E4/E5/E5a）、审计 |
| `review_disposition.schema.json` | `.macao/.dispositions/r<round>/executor.disposition.yml` | FSM（E4/E5a/E6）、Executor |
| `admin_override.schema.json` | `.macao/admin_override.json` | FSM（E7/E9/E10）、管理员裁定 |
| `review_context.schema.json` | AEP `REVIEW_REQUEST.payload.review_context`（PRD §5.2 权威模型） | MACAO 下发端、Reviewer Adapter 消费端 |
| `aep_envelope.schema.json` | 全部 8 类 AEP/1.1 消息信封 | agmsg 收发两端 |
| `macao_config.schema.json` | `macao.yaml` | Config Loader（§13） |

## 约定

- 均为 JSON Schema draft-07；YAML 产物先解析为对象再校验。
- `review_manifest.schema.json` 内含 `opinion.status ↔ vote` 及 `vote ↔ items` 映射的 if/then 形式化约束（与 PRD §2.2 的映射表一致）：
  - `vote == "YES_APPROVE"` $\implies$ 不得包含任何 `BLOCKING` item；
  - `vote == "NO_APPROVE"` $\implies$ 至少包含一条 `BLOCKING` item；
  - `vote == "ABSTAIN"` $\implies$ `items` 必须为空，且必须提供非空 `abstain_reason`。
- `vote_result.schema.json`：`decision` 严格为机器三值枚举 `APPROVED | REWORK_REQUIRED | DEADLOCK`；由 Orchestrator 单一写入且不可变；人工裁定不再修改此文件，而是独立写入 `admin_override.json`（PRD §3.3 E7/E9/E10）。
- `review_disposition.schema.json`：由 Executor 单一写入；`disposition_status: DRAFT | FINAL | PENDING_ADMIN`；当为 `FINAL` 时不得包含未解决的 `NEEDS_ADMIN`；`EXEMPTED_BY_ADMIN` 必须绑定 `override_id`。
- `admin_override.schema.json`：由管理员单一写入；记录 `override_id`、`trigger`、`choice`、`exempt_issue_ids` 与 `note`。
- `review_context.schema.json` 固化 PRD §5.2 的唯一权威结构：10 大必需块（两个传输定位块 + 八个语义块）为顶层键集；`code_changes.refs.*` 必填；禁止 base64 内联。
- `aep_envelope.schema.json`：支持 AEP/1.1 全部 8 类消息类型（Type A 到 Type H）。
- 字段语义以 `MACAO_PRD_v2.md` 为准；Schema 负责结构校验，跨项业务规则由对应运行时模块保证。
