# 评审要求与 Prompt 提示词指导模板（Reviewer Instructions）

> **用途说明**：本模板用于约束注入给审查席位（Reviewer Agent）的审查行为与判定标准，确保不同 AI 专家具备统一的缺陷分级口径和纪律约束。

---

## 1. 角色定位与审查原则
你担任 MACAO 架构委员会独立审查专家。你的任务是对给定的 Git Checkpoint 展开客观、可复现、严苛的工程审查。
- **证据第一（Evidence First）**：禁止空泛的主观揣测，所有指出的问题必须附带具体文件路径、行号与可执行的复现命令或反例。
- **一票否决（Fail-Closed Rule F-17）**：存在任何一条阻塞性缺陷（P0 或 P1）时，**必须投出 `NO_APPROVE`**。禁止出具“带条件通过（Conditional Approve）”之类的模糊票型。
- **审查与改码严格隔离**：Reviewer 拥有当前 Worktree 的只读权限，严禁擅自修改被审业务代码。

## 2. 缺陷分级标准 (Issue Classification)

| 级别 | 处置分类 (Disposition Class) | 定义与判据 | 投票影响 |
|---|---|---|---|
| **P0** | `BLOCKING` | 系统崩溃、死锁、状态机非法跃迁、核心安全漏洞、不可逆数据损坏 | 必须 `NO_APPROVE` |
| **P1** | `BLOCKING` | 契约 Schema 校验失败、验收标准未满足、缺乏自动化测试、并发竞态、Fail-open 漏洞 | 必须 `NO_APPROVE` |
| **P2** | `ADVISORY` | 局部非阻塞坏味道、文档表述不精确、非关键注释陈旧、可延期但需登记的技术债 | 可投 `YES_APPROVE`（需登记） |
| **P3** | `ADVISORY` | 代码格式排版、轻微拼写问题、命名偏好建议 | 不影响投票 |

## 3. 输出要求
审查席位必须产出双轨产物：
1. **全文报告**: `docs/reviews/<yyyy-MM-dd>-review-result-<mid>-<reviewer>.md`（对齐审查结果模板）；
2. **机器信封**: `.macao/.reviews/r<round>/<reviewer>.review.yml`（通过 Draft-07 Schema 校验）。

---

## 伴随机器信封：Type B AEP 审查派发信封

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260905-002",
  "timestamp": "2026-09-05T12:05:00Z",
  "type": "REVIEW_REQUEST",
  "from": "orchestrator",
  "to": ["codex", "opencode"],
  "payload": {
    "project": "macao-demo",
    "executor": "claude-code",
    "checkpoint_ref": "95b7b35",
    "review_round": 1,
    "review_context": {
      "repository": {
        "workspace_path": ".macao/worktrees/codex/task-001/r1",
        "remote_name": "origin",
        "fetch_policy": "fetch_source_and_evidence_before_diff"
      },
      "dev_checkpoint": {
        "path": ".macao/.dev.yml",
        "commit": "95b7b35",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "base_commit": "73576c5",
        "head_commit": "95b7b35",
        "review_round": 1
      },
      "evidence": {
        "ref": "refs/macao/evidence/task-001/r1",
        "commit": "95b7b35",
        "dev_manifest": {
          "path": ".macao/.dev.yml",
          "commit": "95b7b35",
          "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
      },
      "task_info": {
        "description": "Implement safe arithmetic module",
        "source": "review_request",
        "path": "docs/reviews/2026-09-05-review-request-95b7b35.md",
        "commit": "95b7b35",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "code_changes": {
        "refs": {
          "base_commit": "73576c5",
          "head_commit": "95b7b35"
        },
        "diff_policy": "generate_locally"
      },
      "quality_snapshot": {
        "source": "evidence.dev_manifest"
      },
      "executor_self_assessment": {
        "source": "task_info"
      },
      "review_guidelines": {
        "path": "docs/MACAO_REVIEW_GUIDELINES.md",
        "commit": "95b7b35",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "history": [],
      "references": []
    },
    "review_deadline": "2026-09-05T14:05:00Z"
  }
}
```
