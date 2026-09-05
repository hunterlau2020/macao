# 专家审查结论与证据报告模板（Review Result）

- **文档归档路径**: `docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<reviewer>.md`
- **审查日期 (Review Date)**: `YYYY-MM-DD`
- **审查专家 (Reviewer)**: `[claude / codex / opencode / agy]`
- **被审 Commit (Checkpoint Ref)**: `<mid>`
- **审查轮次 (Review Round)**: `1`
- **审查结论 (Verdict)**: `L1 DOC-ALIGNED` / `L2 SPEC-CODE-ALIGNED` / `L3 SCENARIO-VERIFIED` / `L4 RELEASE-READY`
- **最终投票 (Vote)**: `YES_APPROVE` / `NO_APPROVE` / `ABSTAIN`

---

## 1. 结论综述 (Executive Summary)
简要总结本轮审查的总体质量评价、是否达到目标定级以及核心阻断原因。

## 2. 已确认与对齐项 (Verified & Aligned Items)
列出通过核验的正确实现与合规项：
- [x] [功能 A / 规范 B] 经核验符合 PRD 要求
- [x] [自动化测试 C] 真实运行并通过

## 3. 阻断性缺陷 (P0 / P1 Blocking Issues)
> **注意**：若存在任何 P0/P1 缺陷，必须投出 `NO_APPROVE`（F-17 规则）。

### P1-1 [简明缺陷标题]
- **位置**: `[代码路径:行号]` 或 `[文档路径:行号]`
- **严重级别**: `P1` (BLOCKING)
- **现象描述**: 说明何种输入或场景下会导致系统错误或违反规范
- **复现证据 / 命令**:
  ```bash
  # 提供能复现该缺陷的独立测试或命令
  python3 -m unittest tests/test_example.py
  ```
- **修复建议**: 说明预期应如何修改

## 4. 建议性问题 (P2 / P3 Advisory Issues)
列出非阻塞的技术债、可延期项或轻微文档勘误：
- `P2-1`: [建议描述，位置，后续演进建议]

## 5. Reviewer 自审记录 (Self-Audit Log)
- [x] 已核验所有修改文件的语法与逻辑
- [x] 已执行自动化验证命令，证据真实有效
- [x] 未发现未报告的 P0/P1 缺陷

---

## 伴随机器信封：`.macao/.reviews/r<round>/<reviewer>.review.yml`

```yaml
version: "1.0"
task_id: "task-001"
checkpoint_ref: "95b7b35"
review_round: 1
reviewer:
  id: "codex"
  role: "reviewer"
  cli: "codex"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
  confidence: 0.95
  summary: "代码实现规范，测试完备，无阻塞性缺陷"
full_document:
  path: "docs/reviews/2026-09-05-review-result-95b7b35-codex.md"
  evidence_commit: "95b7b35"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
items:
  - issue_id: "codex/ISSUE-01"
    disposition_class: "ADVISORY"
    severity: "minor"
    title: "建议对长耗时任务补充进度日志"
```
