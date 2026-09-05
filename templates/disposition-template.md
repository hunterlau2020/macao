# 意见处置与答辩说明模板（Issue Disposition）

- **任务 ID (Task ID)**: `task-<id>`
- **被审 Commit (Checkpoint Ref)**: `<mid>`
- **评审轮次 (Review Round)**: `1`
- **执行席位 (Executor)**: `claude-code` (或 `opencode` / `codex` / `agy`)
- **处置状态 (Disposition Status)**: `FINAL` (或 `DRAFT` / `PENDING_ADMIN`)

---

## 1. 意见处置总览 (Disposition Overview)
简述上轮评审共识结果（如：共收集 3 位专家共计 2 条缺陷意见），本次处置策略与分流预期。

## 2. 缺陷逐条处置清单 (Detailed Item Dispositions)
> **强约束规则**：必须 100% 穷尽覆盖上轮共识 `vote_result.json` 中的 `issues_index`，不得遗漏任何一条，也不得虚构不存在的 `issue_id`。

| 问题 ID (`issue_id`) | 提问专家 | 处置类型 (`disposition_type`) | 是否需新 Checkpoint (`requires_new_checkpoint`) | 答辩理由与修复对账 (`rationale`) |
|---|---|---|---|---|
| `codex/ISSUE-01` | codex | `ADOPTED` | `true` | 已采纳并在新 commit 补充缺失的边界空值校验及对应单元测试 |
| `gemini/ISSUE-02` | gemini | `DEFERRED` | `false` | 属于次要日志排版建议，经确认不阻断业务功能，已登记至技术债看板后续优化 |
| `claude/ISSUE-03` | claude | `REJECTED` | `false` | 专家指出的竞态已在底层数据库唯一索引处自然防护，经构造测试确认不可复现，故维持原设计 |

## 3. 分流与状态机跃迁路径 (State Transition Routing)
- [ ] **路径 A (返工轮 E5a)**: 清单中存在任何 `requires_new_checkpoint: true` 的项 $\rightarrow$ 必须进入 `REWORK`（Round + 1），要求提交全新的拓扑子孙 Commit 供下轮复审；
- [ ] **路径 B (直接放行 E4)**: 清单中所有项的 `requires_new_checkpoint: false` $\rightarrow$ 无需改动代码，直接放行进入 `MERGING`。

---

## 伴随机器信封：`.macao/.dispositions/r<round>/executor.disposition.yml`

```yaml
version: "1.0"
timestamp: "2026-09-05T12:30:00Z"
task_id: "task-001"
checkpoint_ref: "95b7b35"
review_round: 1
executor:
  id: "claude-code"
disposition_status: "FINAL"
vote_result_ref:
  path: ".macao/vote_result.json"
  evidence_commit: "95b7b35"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
issues_index_sha256: "0000000000000000000000000000000000000000000000000000000000000000"
full_document:
  path: "docs/reviews/2026-09-05-disposition-task-001-r1.md"
  evidence_commit: "95b7b35"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
dispositions:
  - issue_id: "codex/ISSUE-01"
    reviewer_id: "codex"
    disposition_type: "ADOPTED"
    requires_new_checkpoint: true
    rationale: "采纳建议并已修复空指针检查"
  - issue_id: "gemini/ISSUE-02"
    reviewer_id: "gemini"
    disposition_type: "DEFERRED"
    requires_new_checkpoint: false
    rationale: "次要建议，已登记至技术债看板"
```
