# UC-6 意见处置与返工（E5/E5a/E6 循环）

- **设计日期**：2026-09-01
- **状态**：用例设计稿（v2.5 规范）
- **关联**：PRD v2.5 §3.3（E5/E5a/E6）、§15.2（返工策略）；FAQ Q13/Q15；UC-5 `issues_index`；UC-3。
- **边界声明**：**处置与采纳是执行者的内容工作**（FAQ Q13 / Q15、PRODUCT-FACTS F-13/F-16/F-21）：针对本轮全部 issue 逐项声明处置决定（`ADOPTED / DEFERRED / REJECTED / NEEDS_ADMIN / EXEMPTED_BY_ADMIN`）、必填布尔值 `requires_new_checkpoint`、理由与全文哈希。执行者不写、不改 `vote_result.json`。编排器只检测 disposition Schema、覆盖率 100%、布尔有效性与 hash 匹配。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务处于 `CONSENSUS_CHECK`（收到 `DISPOSITION_REQUIRED`）或 `REWORK`（收到 `REWORK_REQUEST`） | E1 |
| P2 | 本轮 `vote_result.json` 已落盘（含 `issues_index`） | E2 |
| P3 | 执行者可读 `docs/reviews/` 全文与 `issues_index` | E3 |

## 2. 主成功场景

### a. 执行者读取意见
读 `vote_result.json` 的 `issues_index` 目录，按需要读取各 Reviewer 在 `docs/reviews/` 的全文。

### b. 执行者编写独立 Review Disposition 产物
执行者在 `.macao/.dispositions/r<round>/executor.disposition.yml` 与 `docs/reviews/` 输出不可变处置产物：

```yaml
version: "1.0"
task_id: "task-1"
checkpoint_ref: "a1b2c3d"
review_round: 1
executor_id: "cc-ds4"
disposition_status: "FINAL"  # DRAFT | FINAL | PENDING_ADMIN (仅 FINAL 触发 FSM 守卫)
generated_at: "2026-09-01T12:10:00Z"
issues_index_sha256: "<sha256>"

full_document:
  path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
  evidence_commit: "c2d3e4f"
  sha256: "<sha256>"

dispositions:
  - issue_id: "codex/SEC-01"
    disposition_type: "ADOPTED"
    requires_new_checkpoint: true
    rationale: "已在代码中增加超时捕获与重试机制"
    full_document:
      path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
      evidence_commit: "c2d3e4f"
      sha256: "<sha256>"
      anchor: "#sec-01"
```

规则：
- 清单必须**精确穷尽**本轮 `issues_index` 的全部 `issue_id`（无差集、无未知 id）；
- 每条必填 `requires_new_checkpoint: boolean`，严禁编排器从自然语言文本中猜测。

### c. 状态流转守卫（FSM Guards）
1. **全项无改码需求（E4）**：若 `vote_result.decision == APPROVED` 且所有 issue 的 `requires_new_checkpoint == false`，且无未豁免的 BLOCKING issue $\implies$ 转移至 `MERGING`（E4）。
2. **改码返工流（E5a）**：若 `vote_result.decision == APPROVED` 且存在至少一项 `requires_new_checkpoint == true` $\implies$ 转移至 `REWORK`（E5a），下发 `REWORK_REQUEST`（round+1）。
3. **机器否决返工流（E5）**：若 `vote_result.decision == REWORK_REQUIRED` $\implies$ 转移至 `REWORK`（E5）。
4. **返工提交与复审（E6）**：在 `REWORK` 状态下，执行者修复并产生新 commit，提交新 `.dev.yml`（round+1）$\implies$ 校验前序 round 的 FINAL disposition 存在后转移至 `READY_FOR_REVIEW`（E6）。

### d. 返工上限与人工接管
`round ≥ max_rework_rounds` 仍 `REWORK_REQUIRED` $\implies$ 触发 E7 交管理员人工裁定（支持 issue 级豁免 `exempt_issue_ids`）。

## 3. 备选流与异常流

- **A1 执行者拒绝意见**：合法（`REJECTED` + `requires_new_checkpoint: false` + `rationale`）；若为 BLOCKING 则下一轮 Reviewer 仍可能投反对票。
- **A2 管理员豁免**：管理员通过 `macao override resolve --choice APPROVED --exempt-issue-ids [...]` 将 BLOCKING issue 标记为 `EXEMPTED_BY_ADMIN`，生成 `override_id` 并放行至 `MERGING`。
- **E1 清单遗漏或包含未知 id**：拒收（fail-closed），维持当前状态并告警。
- **E2 缺失 requires_new_checkpoint**：Schema 校验失败拒收。

## 4. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/workflow/orchestrator.py` | Disposition 100% 覆盖率校验、E4/E5/E5a/E6 守卫判定 |
| `src/macao/core/schema.py` | `review_disposition` Schema v1.0 |
| `tests/` | 覆盖 E5a、E6、遗漏/未知 id 校验、issue 豁免测试 |
