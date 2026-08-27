# PRD v2.3.1 独立复审结论

- **评审日期**：2026-08-27
- **评审对象**：commit `403ddc7` 的 `docs/MACAO_PRD_v2.md` v2.3.1、版本化 Schema 与 fixtures；申请见 `docs/reviews/2026-08-26-review-request-PRD-v2.3.1.md`
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§10
- **结论**：**未达到 L1 DOC-ALIGNED / PG-0。** Schema/fixture 的弃权与人工接管终局模型已补齐，但权威状态识别伪代码仍把终局 decision 收窄为两个值，与同一 PRD 的状态表、场景推演及 Schema 不一致。

## 已确认项

- `vote_result.schema.json` 已将 `decision` 枚举扩展为 `APPROVED`、`REWORK_REQUIRED`、`RETRY_REVIEW`、`CANCELLED`，且对 `RETRY_REVIEW` / `CANCELLED` 强制 `resolution=human_override`，见 `docs/schemas/vote_result.schema.json:51-52,86-94`。
- §3.3 E7 与 §3.4 场景三已分别列出 `APPROVED`、`REWORK`、`RETRY_REVIEW`、`CANCEL` 四个落点，见 `docs/MACAO_PRD_v2.md:836-838,888-902`。
- `.review.yml` 的 Schema 已不允许 `ABSTAIN`，符合“弃权仅由 Orchestrator 终局落盘”的口径，见 `docs/schemas/review_manifest.schema.json:26,59-74`。

## P1：进入下一阶段前应修正

| 编号 | 可复现证据 | 风险与修正要求 |
|---|---|---|
| P1-1 | 状态识别的权威伪代码称 `decision` “仅 `APPROVED \| REWORK_REQUIRED`（Schema 强制）”，并且只处理这两个分支，见 `docs/MACAO_PRD_v2.md:772-787`。这与 Schema 的四值枚举（`docs/schemas/vote_result.schema.json:51`）、E7/E9/E10（`docs/MACAO_PRD_v2.md:836-838`）和 Deadlock 场景的 `RETRY_REVIEW` / `CANCELLED` 终局（`:894-897`）直接矛盾。 | 按现有伪代码实现时，合法且已人工裁定的 `RETRY_REVIEW` 或 `CANCELLED` 会落入未处理路径并保持 `CONSENSUS_CHECK`，而非 E9/E10。因此不能从文档唯一推导四分支终局。删除“两值 / Schema 强制”的旧表述，显式处理四个合法 decision，并与 E4/E5/E9/E10 的归档语义逐项对齐；补两项 SIM/fixture 消费验证。 |

## 验收结论与建议

1. 修正 P1-1 后，对 `RETRY_REVIEW` 和 `CANCELLED` 各做一次“合法 `vote_result.json` → 状态识别 → 唯一 E9/E10 落点”的独立重放。
2. 在该矛盾关闭前，`STATUS.md` 不应将 v2.3.1 标记为“修订闭环完成”或作为代码 L2 的完整前置；本报告不修改实时状态。

## Reviewer 自审记录

- 已按方法论 §9 重查四值终局的 Schema、状态表、场景推演与状态识别伪代码；本轮发现的是 v2.3.1 引入四值 Schema 后遗留的两值实现规范。
