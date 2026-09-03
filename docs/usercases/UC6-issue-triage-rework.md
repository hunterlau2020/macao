# UC-6 意见处置与返工（E5/E5a/E6 循环）

- **设计日期**：2026-09-01
- **状态**：用例设计稿（v2.5 规范）
- **关联**：PRD v2.5 §3.3（E5/E5a/E6）、§15.2（返工策略）；FAQ Q13/Q15；UC-5 `issues_index`；UC-3。
- **边界声明**：**处置与采纳是执行者的内容工作**（FAQ Q13 / Q15、PRODUCT-FACTS F-13/F-16/F-20）：针对本轮全部 issue 逐项声明处置决定（`ADOPTED / DEFERRED / REJECTED / NEEDS_ADMIN / EXEMPTED_BY_ADMIN`）、必填布尔值 `requires_new_checkpoint`、理由与全文哈希。执行者不写、不改 `vote_result.json`。编排器只检测 disposition Schema、覆盖率 100%、布尔有效性与 hash 匹配。

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
执行者在 `.macao/.dispositions/r<round>/executor.disposition.yml`（归档至 `.macao/archive/<checkpoint_ref>/r<round>/executor.disposition.yml`）与 `docs/reviews/` 输出不可变处置产物：

```yaml
version: "1.0"
task_id: "task-1"
checkpoint_ref: "a1b2c3d"
review_round: 1
executor:
  id: "cc-ds4"
  role: "executor"
  cli: "claude-code"
disposition_status: "FINAL"  # DRAFT | FINAL | PENDING_ADMIN (仅 FINAL 触发 FSM 守卫)
timestamp: "2026-09-01T12:10:00Z"
issues_index_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

full_document:
  path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
  evidence_commit: "c2d3e4f"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

vote_result_ref:
  path: ".macao/vote_result.json"
  evidence_commit: "c2d3e4f"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

dispositions:
  - issue_id: "codex/SEC-01"
    reviewer_id: "codex"
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
- `disposition_status: "FINAL"` 时，所有 issue 必须已得出明确处置，严禁遗留 `NEEDS_ADMIN`；
- `disposition_type: "EXEMPTED_BY_ADMIN"` 时，必须填写非空 `override_id` 且 `requires_new_checkpoint: false`；
- 每条必填 `requires_new_checkpoint: boolean`，严禁编排器从自然语言文本中猜测。

### c. 状态流转守卫（FSM Guards）
1. **全项无改码需求（E4）**：若 `vote_result.decision == APPROVED` 且所有 issue 的 `requires_new_checkpoint == false`，且无未豁免的 BLOCKING issue $\implies$ 转移至 `MERGING`（E4）。
2. **改码返工流（E5a）**：若 `vote_result.decision == APPROVED` 且存在至少一项 `requires_new_checkpoint == true` $\implies$ 转移至 `REWORK`（E5a），下发 `REWORK_REQUEST`（round+1）。
3. **机器否决返工流（E5）**：若 `vote_result.decision == REWORK_REQUIRED` $\implies$ 转移至 `REWORK`（E5）。
4. **返工提交与复审（E6）**：在 `REWORK` 状态下，执行者修复并产生新 commit，提交新 `.dev.yml`（round+1）$\implies$ 校验前序 round 的 FINAL disposition 存在后转移至 `READY_FOR_REVIEW`（E6）。

### d. 返工上限与人工接管
`round ≥ max_rework_rounds` 仍 `REWORK_REQUIRED` $\implies$ 触发 E7 交管理员人工裁定（支持 issue 级豁免 `exempt_issue_ids`）。

## 4. 异常流

- **E1 清单遗漏或包含未知 id**：拒收（fail-closed），维持当前状态并告警。
- **E2 缺失 requires_new_checkpoint**：Schema 校验失败拒收。
- **E3 FINAL 遗留 NEEDS_ADMIN**：Schema 校验失败拒收，要求进入管理员裁定或得出确定处置。
- **E4 非法 requires_new_checkpoint 组合**：`DEFERRED`、`REJECTED` 或 `EXEMPTED_BY_ADMIN` 配 `true` 被 Schema 拒绝。

## 5. 后置条件

- **成功**：独立 `.macao/.dispositions/r<round>/executor.disposition.yml` 落地并校验通过（100% 覆盖率，FINAL 状态），依据 `requires_new_checkpoint` 布尔值准确分流至 E4 `MERGING` 或 E5a `REWORK`；
- **失败**：维持原状态（`CONSENSUS_CHECK` HOLD 或 `REWORK`），不发生非法状态转移。

## 6. 验收标准（可测）

1. **覆盖率 100% 强检验**：缺任一 `issue_id` 或包含未登记 `issue_id` $\implies$ 100% fail-closed 拦截；
2. **三态枚举与布尔守卫互锁**：
   - `DEFERRED` + `requires_new_checkpoint: true` $\implies$ Schema 校验拒绝；
   - `REJECTED` + `requires_new_checkpoint: true` $\implies$ Schema 校验拒绝；
   - `EXEMPTED_BY_ADMIN` 缺 `override_id` 或 `requires_new_checkpoint: true` $\implies$ Schema 校验拒绝；
   - `disposition_status: "FINAL"` 包含 `NEEDS_ADMIN` $\implies$ Schema 校验拒绝；
3. **E4 / E5a 分流确定性**：
   - `decision == APPROVED` 且所有 issue `requires_new_checkpoint == false` $\implies$ 唯一转移至 E4 `MERGING`；
   - `decision == APPROVED` 且任一 issue `requires_new_checkpoint == true` $\implies$ 唯一转移至 E5a `REWORK`；
4. **返工拓扑守卫**：E6 转移必须校验当前 commit 为前序 `checkpoint_ref` 之严格拓扑子孙。

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/workflow/orchestrator.py` | Disposition 100% 覆盖率校验、E4/E5/E5a/E6 守卫判定 |
| `src/macao/core/schema.py` | `review_disposition` Schema v1.0 验证器与条件约束 |
| `tests/` | 覆盖 E5a、E6、遗漏/未知 id 校验、issue 豁免测试 |

## 8. 设计自审（Design Self-Review）

- **单写者垄断**：执行者独占 `.macao/.dispositions/r<round>/executor.disposition.yml`，严禁编排器或管理员代写；
- **零自然语言猜测**：Orchestrator 仅依循机器字段 `requires_new_checkpoint` 布尔值与 `decision` 做确定性 FSM 转移；
- **不可变审计链**：`issues_index_sha256` 保证对本轮不可变 `vote_result.json` 的严格反向锚定。
