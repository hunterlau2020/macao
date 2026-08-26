# MACAO Schema 与 Fixtures

本目录是 MACAO 全部机器可校验契约的**唯一权威来源**，随 PRD 版本号演进（当前对应 PRD v2.2）。

| 文件 | 校验对象 | 主要消费方 |
|------|---------|-----------|
| `dev_manifest.schema.json` | `.macao/.dev.yml`（解析后的 YAML） | State Recognition Engine（§3.2）、Adapter |
| `review_manifest.schema.json` | `.macao/.reviews/*.review.yml` | Consensus Engine、Adapter |
| `vote_result.schema.json` | `.macao/vote_result.json` | FSM（E4/E5）、审计 |
| `aep_envelope.schema.json` | 全部 7 类 AEP 消息信封 | agmsg 收发两端 |
| `macao_config.schema.json` | `macao.yaml` | Config Loader（§13） |

## 约定

- 均为 JSON Schema draft-07；YAML 产物先解析为对象再校验。
- `review_manifest.schema.json` 内含 `opinion.status ↔ vote` 映射的 if/then 形式化约束（与 PRD §2.2 的映射表一致），不一致即校验失败——这就是"无效产物"判定的机器可执行定义。
- `fixtures/valid/*` 为正向样例；`fixtures/invalid/*` 为必须被拒绝的反例。二者是 §12.4 Adapter Conformance 的强制输入：每个 Adapter 生成的产物必须通过 valid 集合、被 invalid 集合正确拒绝。
- 字段语义以 `MACAO_PRD_v2.md` 为准；Schema 只约束结构，不重复解释语义。
