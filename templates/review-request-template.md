# 开发检查点与评审申请模板（Review Request）

- **文档归档路径**: `docs/reviews/<yyyy-MM-dd>-review-request-<mid>[-<topic>].md`
- **申请日期 (Date)**: `YYYY-MM-DD`
- **申请人 (Author)**: `[执行席位 ID / 开发者姓名]`
- **目标定级 (Target Level)**: `L1 DOC-ALIGNED` / `L2 SPEC-CODE-ALIGNED` / `L3 SCENARIO-VERIFIED` / `L4 RELEASE-READY`
- **被审 Commit (Checkpoint Ref)**: `<mid>` (例如 `95b7b35`)
- **评审轮次 (Review Round)**: `1` (返工轮递增为 2, 3...)
- **关联任务 ID (Task ID)**: `task-<id>`

---

## 1. 变更摘要与目标 (Summary & Rationale)
清晰说明本轮迭代解决了什么问题、实现了哪些功能、有哪些非显然的设计决策。

## 2. 影响文件与修改清单 (Changed Files)
- `[修改文件路径 A]`: 说明核心变动点
- `[新增测试路径 B]`: 说明新增用例覆盖的场景

## 3. 本地验证与证据 (Verification & Evidence)
列出本地已执行并通过的命令及测试输出摘要：
```bash
PYTHONPATH=src python3 -m unittest discover tests
# 104 tests — 100% OK
```
- [x] 单元测试全绿（0 Failures, 0 Errors）
- [x] 全库 Markdown 0 控制字符扫描通过
- [x] Schema 契约校验 100% 通过

## 4. 提请专家重点关注事项 (Review Focus)
- 请专家重点核验 [某边界场景或并发状态]
- 关注 [某外部 API 调用的降级逻辑] 是否满足预期

---

## 伴随机器信封：`.macao/.dev.yml`

```yaml
version: "1.0"
task_id: "task-001"
checkpoint_ref: "95b7b35"
review_round: 1
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "claude-code"
  cli: "claude-code"
full_document:
  path: "docs/reviews/2026-09-05-review-request-95b7b35.md"
  evidence_commit: "95b7b35"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
development:
  quality_metrics:
    tests_passed: true
  git:
    latest_commit: "95b7b35"
```
