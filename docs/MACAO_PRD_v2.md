# MACAO: Multi-Agent Consensus Architecture for Orchestration
## 面向多 CLI Agent 协同开发与代码评审的轻量级编排平台方案

> **文档状态**：v2.5（权威基准，实施准入稿）  
> **修订日期**：2026-09-01  
> **设计基石**：P-1 零语义创作、内容与控制分层（AEP/1.1 16 KiB 预算）、独立 Review Disposition、加权纯整数共识（`weighted_2/3_v1`）、Git Evidence Ref 隔离拓扑  
> **事实锚点**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-22  
> **前序版本**：v2.4 (Phase 3) / v2.3.1 (L3 SCENARIO-VERIFIED)

---

## 核心设计理念

1. **零语义创作（P-1）**：Orchestrator 是纯粹的确定性规则与路由系统，严禁对 LLM 评审结论进行摘要代写、主观合并或语义二次创作。
2. **内容与控制分层**：AEP 消息只承载状态流转与指针信封（单条上限 16 KiB，内联自然语言上限 2048 字节），完整内容（diff、申请、结论、处置）全部外置于 Git 事实源。
3. **不可变产物与单一写者**：
   - 机器计票结果 `vote_result.json` 严格由 Orchestrator 单一写入，计票完成（含 `DEADLOCK`）即时落盘且物理只读；
   - 审查意见处置 `executor.disposition.yml` 严格由 Executor 单一写入；
   - 管理员人工裁定严格写入独立 `admin_override.json`，严禁回写 `vote_result.json`。
4. **纯整数加权共识（`weighted_2/3_v1`）**：配置期独裁帽、双法定人数门禁、胜方阈值与胜方最少两席门禁全量采用纯整数交叉乘法比较，杜绝浮点误差。
5. **Git Evidence Ref 隔离**：所有过程证据存储于 `refs/macao/evidence/<task_id>/r<round>`，与被管代码分支 HEAD 严格隔离，配合两阶段 Push 校验杜绝伪造与本地假回滚。

---

## 第一部分：规范化开发/评审流程

### 1.1 端到端工作流程图

```text
    ┌──────────────────┐
    │  REQUIREMENT     │  ◄─── 用户明确需求
    │  (Human Review)  │
    └────────┬─────────┘
             │
             v
    ┌──────────────────────────────────────┐
    │  PHASE 1: DEVELOPMENT                │
    │  ├─ Executor: Claude Code / OpenCode │
    │  ├─ State: CODING                    │
    │  └─ Artifact: .dev.yml               │
    └────────┬─────────────────────────────┘
             │
      (Executor 发送显式信号)
             │
             v
    ┌──────────────────────────────────────┐
    │  ARTIFACT CHECKPOINT                 │
    │  ├─ .dev.yml 创建且有效              │
    │  ├─ Git 已 commit                    │
    │  └─ Tests passed (if exists)         │
    └────────┬─────────────────────────────┘
             │
             v
    ┌──────────────────────────────────────┐
    │  PHASE 2: REVIEW REQUEST             │
    │  ├─ MACAO 发送 AEP REVIEW_REQUEST    │
    │  ├─ 包含 context 与 checkpoint info  │
    │  └─ State: WAITING_REVIEW            │
    └────────┬─────────────────────────────┘
             │
      (通过 agmsg 分发给所有 Reviewer)
             │
             v
    ┌──────────────────────────────────────────────┐
    │  PHASE 3: REVIEWER WORK                      │
    │  ├─ Reviewer 收信后进入 WAITING_REVIEW       │
    │  ├─ 运行本地 CLI 检查（代码、安全等）        │
    │  └─ 生成 .review.yml                         │
    └──────────────┬───────────────────────────────┘
                   │
       (全部配置席位已响应或进入持久化超时)
              │
              v
     ┌────────────────────────────────────────────────────────┐
     │  PHASE 4: CONSENSUS CHECK & DISPOSITION                │
     │  ├─ MACAO 收集所有 .review.yml                         │
     │  ├─ 执行加权 2/3 规则 (weighted_2/3_v1 五重门禁)        │
     │  ├─ 即时落盘不可变 vote_result.json                    │
     │  ├─ 若有 issue 发送 DISPOSITION_REQUIRED (HOLD)        │
     │  └─ Executor 提交 executor.disposition.yml (声明改码)  │
     └────────┬───────────────────────────────────────────────┘
              │
           ┌──┴─────────────────────────────────────────┐
           │                                            │
           v (APPROVED 且全 requires_new_checkpoint=false, E4)  v (REWORK_REQUIRED, E5 或 处置要求改码, E5a)
     ┌──────────────┐                             ┌──────────────────────────────────────┐
     │  MERGING     │                             │  REWORK                              │
     │  ├─ merge /  │                             │  ├─ 继承上一轮 disposition 决定      │
     │  │  rebase   │                             │  └─ 产生新 commit + round+1 (E6)     │
     │  ├─ CI gate  │                             └────────┬─────────────────────────────┘
     │  └─ signoff  │                                      │ (Executor 修复开发)
     └──────┬───────┘                                      └──(Loop back to PHASE 1, E6)
            │ CI gate & Push 验证通过 (E4a)
            v
     ┌──────────────┐
     │  DONE        │
     └──────────────┘
```

> 简化视图说明：完整权威转移关系（含 E5a 改码返工、E4b 失败回退、E7 豁免裁决、E9 重试评审、E10 取消）以 §3.3 统一转移表为准。

### 1.2 各阶段的严格定义

阶段视图与第三部分的统一转移表（§3.3）一一对应；"进入方式"即该阶段的触发源：

| 阶段 | 主状态 | 进入方式（触发源） | 离开条件 | 关键产物 | 超时 |
|------|--------|------------------|---------|---------|------|
| **REQUIREMENT** | `IDLE` | 用户经 `macao task create` 提交任务（含验收标准，见第十四部分） | Orchestrator 发送 `DEVELOPMENT_STARTED` AEP（E1） | 任务描述 + 验收标准 | - |
| **DEVELOPMENT** | `CODING` | 收到 `DEVELOPMENT_STARTED`，Executor 启动 | 当前轮 `.dev.yml` 与评审申请全文通过最小有效性校验 | `.dev.yml` + Git Commit + Review Request | 2h |
| **CHECKPOINT** | `READY_FOR_REVIEW` | `.dev.yml` 校验通过的瞬间（产物触发） | 消费完成并发送 `REVIEW_REQUEST` AEP（E2） | `.dev.yml`（归档至 evidence ref） | 1m |
| **REVIEW_REQUEST / REVIEWING** | `WAITING_REVIEW`（Reviewer 侧 `REVIEWING`） | MACAO 发送 `REVIEW_REQUEST` AEP | 全部配置席位已响应或进入持久化超时（E3） | 各 Reviewer `.review.yml` 与评审全文（当前 round） | 30m（10m/reviewer 触发 ping） |
| **CONSENSUS & DISPOSITION** | `CONSENSUS_CHECK` | 全席位 accounted（收到有效票或超时标记） | `vote_result.json` 落盘，无 issue 或存在合法的 FINAL `executor.disposition.yml`（E4/E5/E5a），Deadlock/超时经人工裁定（E7/E9） | `vote_result.json` + `executor.disposition.yml` | 1m (计票) / 30m (disposition) |
| **MERGE / REWORK** | `MERGING` / `DONE` / `REWORK` | 决策 = APPROVED 且处置无改码进入合并（E4）/ 决策 = REWORK_REQUIRED（E5）或处置要求改码（E5a）进入返工 | 合并完成（`MERGE_COMPLETED`，E4a）、CI 失败返工（E4b）、返工闭环（E6）；用户取消进入 `CANCELLED`（E10） | merge commit 或新一轮 `.dev.yml` | - |

---

## 第二部分：标准输出物规范

### 2.1 `.dev.yml` - Development Checkpoint Manifest

**用途**：Executor（Claude Code 等）明确向 MACAO 宣布"我的工作已完成并准备评审"。

**位置**：项目根目录 `.macao/.dev.yml`（提交至 evidence ref，不污染 source branch）。

**格式**：

```yaml
version: "1.0"
task_id: "task-1"
checkpoint_ref: "a1b2c3d"
review_round: 1
timestamp: "2026-09-01T10:30:45Z"
executor:
  id: "cc-ds4"
  role: "executor"
  cli: "claude-code"
  version: "1.2.3"

# 评审申请全文引用
full_document:
  path: "docs/reviews/2026-09-01-review-request-task-1.md"
  evidence_commit: "e5f6a7b"
  sha256: "<sha256>"

development:
  phase: "backend-refactor"
  description: "Refactored database connection pooling with timeout config"

  git:
    latest_commit: "a1b2c3d"
    branch: "feature/db-refactor"
    files_changed: 5
    insertions: 120
    deletions: 45

  # 核心产物
  artifacts:
    - type: "source_code"
      path: "src/db/connection.py"
      changed_lines: 45
    - type: "test_code"
      path: "tests/test_db.py"
      coverage: 0.87
    - type: "documentation"
      path: "docs/db_design.md"
      updated: true

  # 质量指标
  quality_metrics:
    tests_passed: true
    tests_total: 24
    test_coverage: 0.87
    lint_errors: 0
    security_scan_passed: true
    tests_exempt: false

  # 关键检查清单
  checklist:
    - "✓ All tests pass"
    - "✓ Lint checks pass"
    - "✓ Type checks pass"
    - "✓ Security scan passed"

status: "ready_for_review"
signal: "EXPLICIT"
```

---

### 2.2 `.review.yml` - Reviewer Opinion Manifest

**用途**：每个 Reviewer 返回其审查意见与发现的问题清单，作为加权计票与逐项处置的依据。

**位置**：`.macao/.reviews/<reviewer_id>.review.yml`（通过 inbox/staging 提升至 evidence ref）。

**格式**：

```yaml
version: "1.0"
timestamp: "2026-09-01T10:45:30Z"
task_id: "task-1"
checkpoint_ref: "a1b2c3d"  # 评审的源 commit
review_round: 1            # 评审轮次；checkpoint_ref + review_round 双匹配才被受理

reviewer:
  id: "codex"
  role: "reviewer"
  cli: "codex"
  version: "2.1.0"

# 评审全文引用
full_document:
  path: "docs/reviews/2026-09-01-review-result-a1b2c3d-codex.md"
  evidence_commit: "b1c2d3e"
  sha256: "<sha256>"

# 核心评审意见与结构化 issue 清单
opinion:
  status: "CHANGES_REQUESTED"  # APPROVED | CHANGES_REQUESTED | REJECTED | ABSTAINED
  confidence: 0.92
  feedback_summary: "设计合理，但需补充异常处理"

items:
  - issue_id: "codex/SEC-01"
    disposition_class: "BLOCKING"  # BLOCKING (阻断合并，必须修复或豁免) | ADVISORY (建议性，必须确认处置)
    severity: "major"
    title: "缺少网络超时异常处理"
    full_document:
      path: "docs/reviews/2026-09-01-review-result-a1b2c3d-codex.md"
      evidence_commit: "b1c2d3e"
      sha256: "<sha256>"
      anchor: "#sec-01"

vote: "NO_APPROVE"  # YES_APPROVE | NO_APPROVE | ABSTAIN
abstain_reason: null # 显式 ABSTAIN 时必填，此时 items 必须为空
```

**`vote` 与 `items` 的 Schema 条件互锁约束**：

- 存在任一 `BLOCKING` issue $\implies$ `vote` 必须为 `NO_APPROVE`；
- `vote == "YES_APPROVE"` $\implies$ 不得包含任何 `BLOCKING` issue（可包含 `ADVISORY`）；
- `vote == "NO_APPROVE"` $\implies$ 至少包含一条 `BLOCKING` issue；
- `vote == "ABSTAIN"` $\implies$ `items` 必须为空，且必须提供非空 `abstain_reason`。
- 不一致 $\implies$ 判为**无效产物**（不计入响应席位，记录审计告警）。

> 写入约定：各 `.review.yml` 由 Reviewer Adapter 写入 staging 或 inbox ref；MACAO 校验后串行提升至 canonical evidence ref（`refs/macao/evidence/<task_id>/r<round>`），**严禁直接提交到 source branch 破坏代码检查点**。

---

### 2.3 `vote_result.json` - Consensus Result Record

**用途**：MACAO 编排器单一生成的机器计票汇总，记录不可变仲裁结果。

**位置**：`.macao/vote_result.json`（及 evidence ref 归档）。

**格式**：

```json
{
  "version": "2.0",
  "generated_at": "2026-09-01T12:00:00Z",
  "task_id": "task-1",
  "checkpoint_ref": "a1b2c3d",
  "review_round": 1,
  "executor_id": "cc-ds4",
  "reviewers_total": 3,
  "reviewers_responded": 3,
  "reviewers_accounted": 3,

  "input_artifacts": [
    {"reviewer": "codex", "path": ".macao/.reviews/codex.review.yml", "evidence_commit": "b1c2d3e", "sha256": "<sha256>"},
    {"reviewer": "kimi", "path": ".macao/.reviews/kimi.review.yml", "evidence_commit": "b1c2d3e", "sha256": "<sha256>"},
    {"reviewer": "gemini", "path": ".macao/.reviews/gemini.review.yml", "evidence_commit": "b1c2d3e", "sha256": "<sha256>"}
  ],

  "votes": [
    {"reviewer": "codex", "vote": "YES_APPROVE", "weight": 2, "source": "manifest"},
    {"reviewer": "kimi", "vote": "YES_APPROVE", "weight": 1, "source": "manifest"},
    {"reviewer": "gemini", "vote": "NO_APPROVE", "weight": 1, "source": "manifest"}
  ],

  "policy_snapshot": {
    "rule": "weighted_2/3_v1",
    "configured_seats": 3,
    "configured_weight": 4,
    "seat_quorum_required": 2,
    "weight_quorum_required": 3,
    "decision_threshold_numerator": 2,
    "decision_threshold_denominator": 3,
    "minimum_winning_seats": 2,
    "max_single_weight_share_numerator": 2,
    "max_single_weight_share_denominator": 3
  },

  "vote_breakdown": {
    "effective_seats": 3,
    "effective_weight": 4,
    "approve_seats": 2,
    "approve_weight": 3,
    "reject_seats": 1,
    "reject_weight": 1,
    "abstain_seats": 0,
    "abstain_weight": 0
  },

  "issues_index": [
    {
      "issue_id": "gemini/SEC-01",
      "reviewer": "gemini",
      "disposition_class": "BLOCKING",
      "severity": "major",
      "title": "缺少超时异常处理",
      "full_document": {
        "path": "docs/reviews/2026-09-01-review-result-a1b2c3d-gemini.md",
        "evidence_commit": "b1c2d3e",
        "sha256": "<sha256>",
        "anchor": "#sec-01"
      }
    }
  ],
  "issues_index_sha256": "<sha256>",

  "requires_disposition": true,
  "decision": "APPROVED",
  "resolution": "AUTO_WEIGHTED_CONSENSUS"
}
```

**加权 2/3 共识规则（`weighted_2/3_v1` 五重纯整数门禁）**：

设配置席位数为 $N$，配置总权重为 $W$，非弃权有效席位数为 $E_N$，非弃权有效权重为 $E_W$：
1. **配置期独裁帽**：$\forall i, 3 \times w_i < 2 \times W$（单席位权重达 2/3 拒绝启动系统）；
2. **席位法定人数**：$E_N \ge \lceil 2N/3 \rceil$；
3. **权重法定人数**：$E_W \ge \lceil 2W/3 \rceil$（分母为配置总权重 $W$）；
4. **胜方权重阈值**：赞成满足 $3 \times approve\_weight \ge 2 \times E_W$，或反对满足 $3 \times reject\_weight \ge 2 \times E_W$；
5. **胜方最少席位门禁**：胜方有效席位数 $\ge minimum\_winning\_seats$（默认 2）。
6. **判定结果**：
   - 赞成满足 4、5 $\implies$ `decision = APPROVED`；
   - 反对满足 4、5 $\implies$ `decision = REWORK_REQUIRED`；
   - 其余一切情形 $\implies$ `decision = DEADLOCK`，即时落盘后 HOLD，发送 `HUMAN_OVERRIDE_REQUEST` 由管理员裁决。

---

### 2.4 AEP (Agent Event Protocol) v1.1 消息规范

AEP v1.1 共定义 **8 种消息类型（Type A 到 Type H）**：

| # | 消息类型 | 标识 | 方向 | 用途 | 备注 |
|---|---------|------|------|------|------|
| 1 | `DEVELOPMENT_STARTED` | Type A | MACAO → Executor | 下发开发任务与成功标准 | AEP/1.0 兼容 |
| 2 | `REVIEW_REQUEST` | Type B | MACAO → Reviewers | 发起评审，携带引用式 `review_context` | 升级为 Ref/Locator 集合 |
| 3 | `REVIEW_RESPONSE` | Type C | Reviewer → MACAO | 返回 `.review.yml` 与投票 | 升级三值投票与 Issue 分类 |
| 4 | `REWORK_REQUEST` | Type D | MACAO → Executor | 下发返工通知（round+1） | 升级绑定上一轮 disposition |
| 5 | `DISPOSITION_REQUIRED` | Type E | MACAO → Executor | **v2.5 新增**：通知执行者对本轮 issue 逐项处置 | 携带 deadline 与 vote_result 引用 |
| 6 | `MERGE_COMPLETED` | Type F | MACAO → 全体 | 通告共识达成与合并结果 | 携带 merge_commit |
| 7 | `STATE_CHANGED` | Type G | Agent → MACAO | Agent 上报自身状态变化 | 状态只读投影 |
| 8 | `HUMAN_OVERRIDE_REQUEST` | Type H | MACAO → User | 请求人工接管决策（DEADLOCK、超时、NEEDS_ADMIN） | 携带 issue 级上下文与豁免选项 |

**AEP 协议字节预算与引用规范**：
- `aep.max_message_bytes` 默认 **16384**（16 KiB）；单个内联自然语言字段上限 **2048** 字节；
- 严禁内联 diff、完整申请、完整结论、处置正文与终端长日志；超限内容必须外置并通过 `path + commit + sha256` 强引用；
- 发送与接收端双向严格校验，超限拒绝发送并报错，严禁静默截断。

**统一信封约定**（适用于全部 8 类消息）：
- 信封固定字段：`protocol` / `message_id` / `timestamp` / `type` / `from` / `to` / `payload`；
- `protocol` 统一为 `"AEP/1.1"`（兼容读取 AEP/1.0）；
- `from` 为单值字符串；接收方字段**统一为 `to`**——单接收者为字符串，多接收者为字符串数组；
- 所有指向被评审开发检查点 commit 的字段**统一命名为 `checkpoint_ref`**。

#### Type A：开发阶段通知

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-001",
  "timestamp": "2026-09-01T10:00:00Z",

  "type": "DEVELOPMENT_STARTED",
  "from": "macao",
  "to": "cc-ds4",

  "payload": {
    "project": "macao-demo",
    "task_id": "task-1",
    "source_branch": "feature/db-refactor",
    "target_branch": "main",
    "specification_summary": "Refactor database connection pooling with configurable timeout",
    "acceptance_criteria": [
      "Thread safety in connection acquisition and release",
      "Configurable pool timeout with default fallback",
      "All unit and integration tests pass cleanly"
    ],
    "task_description": "Refactor database connection pooling with configurable timeout",
    "expected_output": {
      "code_path": "src/db/connection.py",
      "test_path": "tests/test_db.py"
    },
    "success_criteria": {
      "all_tests_must_pass": true,
      "min_coverage": 0.85,
      "lint_passed": true
    }
  }
}
```

#### Type B：评审申请

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-002",
  "timestamp": "2026-09-01T10:35:00Z",

  "type": "REVIEW_REQUEST",
  "from": "macao",
  "to": ["codex", "kimi", "gemini"],

  "payload": {
    "project": "macao-demo",
    "executor": "cc-ds4",
    "checkpoint_ref": "a1b2c3d",
    "review_round": 1,

    "review_context": {
      "repository": {
        "workspace_path": ".macao/worktrees/codex/task-1/r1",
        "remote_name": "origin",
        "fetch_policy": "fetch_source_and_evidence_before_diff"
      },

      "dev_checkpoint": {
        "path": ".macao/.dev.yml",
        "commit": "e5f6a7b",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "base_commit": "b2c3d4e",
        "head_commit": "a1b2c3d",
        "review_round": 1
      },

      "evidence": {
        "ref": "refs/macao/evidence/task-1/r1",
        "commit": "e5f6a7b",
        "dev_manifest": {
          "path": ".macao/.dev.yml",
          "commit": "e5f6a7b",
          "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
      },

      "task_info": {
        "description": "Refactored database connection pooling with timeout config",
        "source": "review_request",
        "path": "docs/reviews/2026-09-01-review-request-task-1.md",
        "commit": "e5f6a7b",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },

      "code_changes": {
        "refs": {
          "base_commit": "b2c3d4e",
          "head_commit": "a1b2c3d"
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
        "commit": "a1b2c3d",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },

      "history": [],
      "references": []
    },

    "review_deadline": "2026-09-01T11:05:00Z",
    "expected_output": {
      "format": ".review.yml",
      "location": ".macao/.reviews/{reviewer_id}.review.yml"
    }
  }
}
```

#### Type C：评审反馈

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-003",
  "timestamp": "2026-09-01T10:48:00Z",

  "type": "REVIEW_RESPONSE",
  "from": "codex",
  "to": "macao",

  "payload": {
    "project": "macao-demo",
    "checkpoint_ref": "a1b2c3d",
    "review_round": 1,

    "review_file": {
      "path": ".macao/.reviews/codex.review.yml",
      "evidence_commit": "b1c2d3e",
      "sha256": "<sha256>"
    },

    "vote_summary": {
      "vote": "NO_APPROVE",
      "issues_count": 1,
      "blocking_count": 1
    }
  }
}
```

#### Type D：Rework 请求

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-004",
  "timestamp": "2026-09-01T10:56:00Z",

  "type": "REWORK_REQUEST",
  "from": "macao",
  "to": "cc-ds4",

  "payload": {
    "project": "macao-demo",
    "checkpoint_ref": "a1b2c3d",
    "round": 2,
    "disposition_reference": {
      "path": ".macao/.dispositions/r1/executor.disposition.yml",
      "evidence_commit": "b1c2d3e",
      "sha256": "<sha256>"
    },
    "next_checkpoint_deadline": "2026-09-01T12:56:00Z"
  }
}
```

#### Type E：Disposition 处置通知（v2.5 新增）

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-005",
  "timestamp": "2026-09-01T10:50:00Z",

  "type": "DISPOSITION_REQUIRED",
  "from": "macao",
  "to": "cc-ds4",

  "payload": {
    "project": "macao-demo",
    "task_id": "task-1",
    "checkpoint_ref": "a1b2c3d",
    "review_round": 1,
    "vote_result_ref": {
      "path": ".macao/vote_result.json",
      "evidence_commit": "b1c2d3e",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "issues_index_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "timeout_deadline": "2026-09-01T11:20:00Z",
    "deadline": "2026-09-01T11:20:00Z",
    "expected_output": ".macao/.dispositions/r1/executor.disposition.yml"
  }
}
```

#### Type F：合并完成通告

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-006",
  "timestamp": "2026-09-01T11:00:00Z",

  "type": "MERGE_COMPLETED",
  "from": "macao",
  "to": ["cc-ds4", "codex", "kimi", "gemini"],

  "payload": {
    "project": "macao-demo",
    "checkpoint_ref": "a1b2c3d",
    "vote_result_path": ".macao/vote_result.json",
    "merge_commit": "d4e5f6a"
  }
}
```

#### Type G：状态上报

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-007",
  "timestamp": "2026-09-01T10:20:00Z",

  "type": "STATE_CHANGED",
  "from": "cc-ds4",
  "to": "macao",

  "payload": {
    "project": "macao-demo",
    "state": "CODING",
    "detail": "refactoring connection pool",
    "attachments": [
      { "name": "dev_checkpoint", "path": ".macao/.dev.yml", "sha256": "<sha256>" }
    ]
  }
}
```

#### Type H：人工接管请求

```json
{
  "protocol": "AEP/1.1",
  "message_id": "msg-20260901-008",
  "timestamp": "2026-09-01T10:58:00Z",

  "type": "HUMAN_OVERRIDE_REQUEST",
  "from": "macao",
  "to": "user",

  "payload": {
    "trigger": "consensus_deadlock",
    "context": "3 Reviewer 配置下 1 赞成 + 1 反对 + 1 弃权，未达法定人数",
    "options": ["APPROVED", "REWORK", "RETRY_REVIEW", "CANCEL", "EXTEND"],
    "exempt_issue_ids_available": ["gemini/SEC-01"],
    "deadline": "2026-09-01T11:08:00Z"
  }
}
```

---

### 2.5 `executor.disposition.yml` - Review Disposition Manifest

**用途**：Executor（执行者）对评审专家提出的所有结构化 issue 进行逐项处置声明。

**位置**：`.macao/.dispositions/r<round>/executor.disposition.yml`（通过 inbox/staging 提升至 evidence ref）。

**格式**：

```yaml
version: "1.0"
timestamp: "2026-09-01T11:05:00Z"
task_id: "task-1"
checkpoint_ref: "a1b2c3d"
review_round: 1

executor:
  id: "cc-ds4"
  role: "executor"
  cli: "claude-code"
  version: "1.2.3"

full_document:
  path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
  evidence_commit: "c2d3e4f"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

vote_result_ref:
  path: ".macao/vote_result.json"
  evidence_commit: "c2d3e4f"
  sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

issues_index_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
disposition_status: "FINAL"  # DRAFT | FINAL | PENDING_ADMIN

dispositions:
  - issue_id: "gemini/SEC-01"
    reviewer_id: "gemini"
    disposition_type: "ADOPTED"  # ADOPTED | DEFERRED | REJECTED | NEEDS_ADMIN | EXEMPTED_BY_ADMIN
    requires_new_checkpoint: false
    rationale: "已在配置层增加默认 30s 超时处理，无需修改核心连接池代码"
    full_document:
      path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
      evidence_commit: "c2d3e4f"
      sha256: "<sha256>"
      anchor: "#gemini-sec-01"
  - issue_id: "codex/ARCH-02"
    reviewer_id: "codex"
    disposition_type: "EXEMPTED_BY_ADMIN"
    override_id: "override-20260901-abcd"
    requires_new_checkpoint: false
    rationale: "管理员在 admin_override.json 中已豁免此项非阻塞架构建议"
    full_document:
      path: "docs/reviews/2026-09-01-review-disposition-task-1-r1.md"
      evidence_commit: "c2d3e4f"
      sha256: "<sha256>"
      anchor: "#codex-arch-02"
```

**处置规则与守卫**：
1. **精确穷尽原则**：`dispositions` 列表必须 100% 覆盖本轮 `vote_result.json.issues_index` 中的每一个 `issue_id`，不得遗漏、不得新增；
2. **显式改码守卫（`requires_new_checkpoint`）**：
   - 每项 issue 必须提供非空布尔值 `requires_new_checkpoint`；
   - 若任一 issue 的 `requires_new_checkpoint == true` $\implies$ 触发 E5a 进入 `REWORK`；
   - 若全部 issue 的 `requires_new_checkpoint == false` $\implies$ 触发 E4 进入 `MERGING`；
3. **状态守卫**：只有 `disposition_status == "FINAL"` 的产物才能触发 E4/E5a；`DRAFT` 或 `PENDING_ADMIN` 状态下保持在 `CONSENSUS_CHECK` HOLD 状态，等待执行者完善或管理员 E7 override；在 `FINAL` 状态下，所有 issue 必须已得出明确处置，严禁遗留 `NEEDS_ADMIN`；
4. **管理员豁免关联守卫**：若 `disposition_type == "EXEMPTED_BY_ADMIN"`，必须关联非空的 `override_id`，且 `requires_new_checkpoint` 必须为 `false`。

---

## 第三部分：改进的状态识别策略

### 3.1 三层识别架构（改进版）

```
┌──────────────────────────────────────────────────────────────┐
│              State Recognition Engine v2.5                   │
│         (Explicit Signal First, Inference Last)              │
└──────────────────────────────────────────────────────────────┘

Layer 1: Explicit Signal (100% 可信)
├─ .dev.yml 状态字段 = "ready_for_review"
├─ .review.yml 投票字段 = "YES_APPROVE" | "NO_APPROVE" | "ABSTAIN"
├─ vote_result.json 决策字段 = "APPROVED" | "REWORK_REQUIRED" | "DEADLOCK"
└─ executor.disposition.yml 处置状态 = "FINAL"
   ⬇
   ✓ 仅接受「当前 FSM 状态 + 当前 checkpoint_ref/round」匹配的产物
     （作用域与生命周期规则见 §3.2/§3.4，旧产物一律忽略或已归档），
     直接转换到目标状态，不进入后续层

Layer 2: Behavioral Inference (80% 可信，仅作辅助)
├─ Git 检测：new commit 存在且有实质变更
├─ 文件系统：.dev.yml 存在且 YAML 有效
├─ 进程监控：Executor PTY 输出稳定 >60s
└─ 测试检测：pytest 成功或失败记录
   ⬇
   ⚠ 仅在 Layer 1 信号缺失时使用，触发预警而非状态转换

Layer 3: LLM Judgment (60% 可信，仅用于故障诊断)
├─ 输入：最后 300 行 Terminal Log + 所有 .yml 文件
├─ 任务：判断是否处于卡死/异常状态
└─ 输出：诊断报告 + 建议的人工接管点
   ⬇
   ⚠️ 始终向用户提示诊断报告；仅当置信度 < 0.7 时触发 HUMAN_OVERRIDE
```

> 注：图中标注的可信度（100% / 80% / 60%）为设计目标值，以 PoC 实测数据为准（验收阈值见第八部分 KPI）。

### 3.2 状态识别的优先级规则

```python
def recognize_agent_state(agent_id: str, project: str) -> AgentState:
    """
    状态识别的唯一规范入口。
    核心规则：按「当前 FSM 状态 + 当前 checkpoint_ref / review_round」做作用域读取，
    每个状态只接受该阶段合法的产物类型；已被消费的产物标记 consumed 并归档，
    不再参与识别 —— 因此持久化的旧产物（如一直存在的 .dev.yml）不会遮蔽后续阶段。
    """
    st  = current_state(agent_id)        # 当前已确认 FSM 状态（State Store，见第十一部分）
    ref = current_checkpoint(project)    # 当前轮被评审 commit；新任务/新轮次开始时更新
    rnd = current_round(project)         # 当前返工轮次，从 1 起；发送 REWORK_REQUEST 时 +1

    # ===== Layer 1a: 开发侧产物 .dev.yml —— 仅 CODING/REWORK 状态受理 =====
    if st in (AgentState.CODING, AgentState.REWORK):
        dev = load_and_validate('.macao/.dev.yml', DEV_YML_SCHEMA,
                                expect_review_round=rnd,
                                not_consumed=True,
                                require_new_commit=True)
        if dev.valid:
            update_checkpoint(dev.latest_commit, rnd)
            return AgentState.READY_FOR_REVIEW

    # ===== READY_FOR_REVIEW 不读取产物，仅由命令型转移离开 =====
    elif st == AgentState.READY_FOR_REVIEW:
        pass   # Orchestrator 归档 .dev.yml 并发送 REVIEW_REQUEST 后，经 E2 进入 WAITING_REVIEW

    # ===== Layer 1b: WAITING_REVIEW 全席位 accounted 后转移 =====
    elif st == AgentState.WAITING_REVIEW:
        accounted = get_accounted_reviewers_count(project, ref, rnd)
        configured = get_configured_reviewers_count(project)
        if accounted == configured:
            return AgentState.CONSENSUS_CHECK

    # ===== Layer 1c: CONSENSUS_CHECK 只收当前 ref/round 的 vote_result.json =====
    elif st == AgentState.CONSENSUS_CHECK:
        result = load_and_validate('.macao/vote_result.json', VOTE_RESULT_SCHEMA,
                                   expect_checkpoint_ref=ref,
                                   expect_review_round=rnd)
        if result.valid:
            if result.decision == 'DEADLOCK':
                ovr = load_and_validate('.macao/admin_override.json', ADMIN_OVERRIDE_SCHEMA,
                                        expect_checkpoint_ref=ref, expect_review_round=rnd)
                if ovr.valid and ovr.choice == 'APPROVED':
                    disp = load_and_validate(f'.macao/.dispositions/r{rnd}/executor.disposition.yml',
                                             DISPOSITION_SCHEMA,
                                             expect_checkpoint_ref=ref,
                                             expect_review_round=rnd)
                    if disp.valid and disp.disposition_status == 'FINAL':
                        archive_round_artifacts(ref, rnd)
                        if any(d.requires_new_checkpoint for d in disp.dispositions):
                            return AgentState.REWORK      # E5a：改码返工
                        return AgentState.MERGING          # E4：无改码合并
                    # 管理员已批准但执行者尚未提交 FINAL disposition：保持 CONSENSUS_CHECK (HOLD，等待执行者处置)
                    return AgentState.CONSENSUS_CHECK
                return AgentState.CONSENSUS_CHECK  # 保持 HOLD，等待 E7 人工裁定
            elif result.decision == 'APPROVED':
                if result.requires_disposition:
                    disp = load_and_validate(f'.macao/.dispositions/r{rnd}/executor.disposition.yml',
                                             DISPOSITION_SCHEMA,
                                             expect_checkpoint_ref=ref,
                                             expect_review_round=rnd)
                    if disp.valid and disp.disposition_status == 'FINAL':
                        archive_round_artifacts(ref, rnd)
                        if any(d.requires_new_checkpoint for d in disp.dispositions):
                            return AgentState.REWORK      # E5a：改码返工
                        return AgentState.MERGING          # E4：无改码合并
                    # 尚未提交 FINAL disposition：保持 CONSENSUS_CHECK (HOLD)
                    return AgentState.CONSENSUS_CHECK
                else:
                    archive_round_artifacts(ref, rnd)
                    return AgentState.MERGING              # E4：无 issue 直接合并
            elif result.decision == 'REWORK_REQUIRED':
                archive_round_artifacts(ref, rnd)
                if rnd < max_rework_rounds:
                    return AgentState.REWORK               # E5：返工
                return request_human_override(agent_id='orchestrator', reason='max_rework_rounds_failed')

    # ===== Layer 2: 行为推断 —— 只记录与预警，永不改变业务状态 =====
    signals = collect_behavior_signals(agent_id)
    inferred = infer_state_from_behavior(signals)
    log_behavior_inference(agent_id, inferred, confidence=0.8)
    emit_warning(f"Agent {agent_id}: 状态 {st} 下无有效显式产物，推断 {inferred} 仅供参考")

    # ===== Layer 3: LLM Judgment（仅故障诊断用，不产生业务状态）=====
    if is_agent_suspected_deadlock(agent_id):
        logs = get_terminal_logs(agent_id, lines=300)
        diagnosis = call_llm_for_diagnosis(logs, signals)
        report_diagnosis(diagnosis)

        if diagnosis.confidence < 0.7:
            trigger_human_override(
                agent_id=agent_id,
                reason="State ambiguous, awaiting human decision",
                diagnostic_info=diagnosis
            )
            return AgentState.UNKNOWN

    # 未命中显式信号且未触发人工接管：保持上一个已确认状态（HOLD），不推进
    return last_confirmed_state(agent_id)
```

> **行为约定**（与 §3.1 分层承诺及 §3.3 统一转移表严格一致）：
> 1. 业务状态的转移只有两类来源：**命令型**（AEP 指令）与**产物型**（作用域内的显式产物），不存在第三种来源。
> 2. 产物识别是**状态作用域化**的：每个状态只读取属于自己的产物，旧产物一律忽略或已归档。
> 3. Layer 2 的推断结果只进入日志与告警；无有效产物时保持（HOLD）上一个已确认状态，绝不静默推进。
> 4. `.review.yml` / `vote_result.json` / `executor.disposition.yml` 必须校验 `checkpoint_ref` 与 `review_round` 双匹配。

### 3.3 统一状态转移表（命令 + 产物）

| 编号 | 当前状态 | 来源类型 | 触发条件（含校验） | 目标状态 | 伴随动作（消费/归档/通知） |
|------|---------|---------|------------------|---------|--------------------------|
| E1 | `IDLE` | 命令 | 用户受理任务，发送 `DEVELOPMENT_STARTED` AEP | `CODING` | 创建任务记录（State Store）；round=1 |
| — | `CODING` / `REWORK` | 产物 | 当前轮 `.dev.yml` 与评审申请通过最小有效性校验（新 commit + round 匹配） | `READY_FOR_REVIEW` | 锁定 checkpoint_ref；检查点窗口计时（1m） |
| E2 | `READY_FOR_REVIEW` | 命令 | `.dev.yml` 消费完成，发送 `REVIEW_REQUEST` AEP | `WAITING_REVIEW` | 提升至 canonical evidence ref；记录评审 deadline |
| E3 | `WAITING_REVIEW` | 产物/超时 | **所有配置席位已响应（收到有效 .review.yml）或已被持久化 timeout 机制纳入 accounted 集合** | `CONSENSUS_CHECK` | 提升至 evidence ref；**票数判定是确定性函数**——若算出 Deadlock，即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）并在伴随动作内发送 `HUMAN_OVERRIDE_REQUEST`（Type H，§6.1）进入 **HOLD**，等待 E7 裁定 |
| — | `WAITING_REVIEW` | 超时 | 席位到达超时时间（如 10m/reviewer）触发 timeout scanner | `WAITING_REVIEW` | 记录超时弃权票据（`source: timeout`），不提前截断其他席位，计入 accounted 集合 |
| E4 | `CONSENSUS_CHECK` | 产物/命令 | 机器决策为 `APPROVED`（或经合法 E7 override 裁决）；无 issue，或存在 FINAL `executor.disposition.yml` 精确覆盖全部 issue 且所有 `requires_new_checkpoint=false` | `MERGING` | Merge Controller 启动六道关卡合并流水线（§14.5：关卡 1 pre-merge evidence push 校验 (ls-remote) → 关卡 2 检出 → 关卡 3 ff_only 技术合并 → 关卡 4 CI gate → 关卡 5 人工签字 → 关卡 6 源码 push 与 post-merge evidence 封存归档） |
| E4a | `MERGING` | 命令 | 合并流水线全部成功，且**最终 push 对象 == `vote_result.json.checkpoint_ref` 硬校验通过**（`ff_only` 下 remote tip == checkpoint_ref；`no_ff` 下 merge commit 第二父 == checkpoint_ref） | `DONE` | 发送 `MERGE_COMPLETED`（含 merge_commit）；本轮产物归档 |
| E4b | `MERGING` | 命令 | CI gate 失败，或 push 失败不可自动恢复，或签字被拒绝，或 Git conflict | `REWORK` | 生成新一轮 `REWORK_REQUEST`（round+1，注明原因）；本轮产物归档 |
| E5 | `CONSENSUS_CHECK` | 产物 | 决策 = `REWORK_REQUIRED` 且 round < max_rework_rounds | `REWORK` | 发送 `REWORK_REQUEST`（round+1）与 `DISPOSITION_REQUIRED`；本轮产物归档至 evidence ref |
| E5a | `CONSENSUS_CHECK` | 产物 | **v2.5 新增**：决策 = `APPROVED`，FINAL disposition 精确覆盖全部 issue，且**至少一项 `requires_new_checkpoint=true`** | `REWORK` | 发送 `REWORK_REQUEST`（round+1，附处置决定）；本轮产物归档 |
| E6 | `REWORK` | 产物 | 前一轮 FINAL disposition 已覆盖全部 issue；新一轮 `.dev.yml` 有效（round+1、新 source commit != 上一轮，且为上一轮 checkpoint_ref 之拓扑子孙） | `READY_FOR_REVIEW` | 更新当前 checkpoint_ref |
| E7 | `HOLD`（`CONSENSUS_CHECK`） | 命令 | 管理员人工裁定（`--choice APPROVED \| REWORK \| RETRY_REVIEW \| CANCEL \| EXTEND`），支持带 `exempt_issue_ids` 与 note 豁免 | 见伴随动作 | 落盘独立 `admin_override.json` 与审计事件，生成 `override_id`。按 choice 转移：APPROVED（解除 HOLD，执行者角色投影 `SHOULD_DISPOSE`，待执行者出具带 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL disposition 校验通过后分流 E4 `MERGING` 或 E5a `REWORK`）；REWORK（触发 E5 → `REWORK`）；RETRY_REVIEW（触发 E9 → `WAITING_REVIEW`，重试当前轮评审）；CANCEL（触发 E10 → `CANCELLED`）；EXTEND（重置超时倒计时，保持当前状态）。 |
| E9 | `CONSENSUS_CHECK` | 命令 | 用户裁定 RETRY_REVIEW（重试当前轮评审，round 不变） | `WAITING_REVIEW` | 本轮已收意见作废归档；重新发送 `REVIEW_REQUEST`（全新 message_id 与 deadline） |
| E10 | `*`（任意活动态，即除 DONE/CANCELLED 外） | 命令 | 用户执行 `macao cancel <task>`，或 override 裁定 `--choice CANCEL`（E7） | `CANCELLED`（终态） | 通知全体 Agent；现场归档；审计记录 |
| E8 | `*`（任意） | 诊断 | 60min 无进展 + Layer 3 置信度 <0.7 | `UNKNOWN` | HUMAN_OVERRIDE，等待用户裁定 |

> 状态说明：
> - 业务状态共 **10 个**：`IDLE` / `CODING` / `READY_FOR_REVIEW` / `WAITING_REVIEW` / `CONSENSUS_CHECK` / `MERGING` / `DONE` / `REWORK` / `CANCELLED` / `UNKNOWN`；其中 `DONE` 与 `CANCELLED` 为终态；
> - `HOLD` 为受控暂停子状态（任务处于 `CONSENSUS_CHECK` 等待处置/人工介入）；
> - 除本表所列来源外，任何实现不得引入其他状态转移路径。

### 3.4 产物生命周期与场景推演

**生命周期表**：

| 产物 | 生成者 | 受理窗口（FSM 状态 × ref/round） | 消费/归档动作 |
|------|--------|--------------------------------|--------------|
| `.dev.yml` | Executor | 仅 `CODING` / `REWORK`，未被消费、本轮新 commit、round 匹配 | E2 触发时标记 consumed 并提升至 `refs/macao/evidence/<task>/r<round>` |
| `.review.yml` | 各 Reviewer | 仅 `WAITING_REVIEW`，checkpoint_ref + review_round 双匹配 | E3 触发时提升至 `refs/macao/evidence/<task>/r<round>` 归档存档 |
| `vote_result.json` | Orchestrator | 仅 `CONSENSUS_CHECK`，ref + round 双匹配 | 计票完成即时落盘，并归档至 evidence ref |
| `executor.disposition.yml` | Executor | 仅 `CONSENSUS_CHECK` / `REWORK`，精确覆盖本轮 issue | E4/E5a/E6 触发时消费，并提升至 evidence ref 归档 |
| `admin_override.json` | Orchestrator (Admin) | 仅 `HOLD` 状态 | E7 触发时生成并提升至 evidence ref |

**场景推演一：首次开发，三 Reviewer 批准，带建议处置**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1 | 用户受理任务 | `IDLE` → `CODING`（E1） | — |
| 2 | Claude 生成 `.dev.yml`（commit `a1b2c3d`，round 1） | `CODING` → `READY_FOR_REVIEW` | `.dev.yml`（校验通过） |
| 3 | Orchestrator 发送 `REVIEW_REQUEST` | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2） | —（`.dev.yml` 已归档） |
| 4 | Codex、Kimi、Gemini 各写 `.review.yml`（round 1），全席位 accounted | `WAITING_REVIEW` → `CONSENSUS_CHECK`（E3） | 3 × `.review.yml` |
| 5 | MACAO 计票落盘 `vote_result.json`（APPROVED，带 1 条 ADVISORY issue） | `CONSENSUS_CHECK`（等待处置） | `vote_result.json` |
| 6 | Executor 提交 `executor.disposition.yml`（FINAL，`requires_new_checkpoint=false`） | `CONSENSUS_CHECK` → `MERGING`（E4） | `executor.disposition.yml` |
| 7 | merge/CI gate/签字/push 全部成功 | `MERGING` → `DONE`（E4a） | —（发送 `MERGE_COMPLETED`；归档） |

**场景推演二：发现阻断 Issue，执行处置后返工第二轮**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1-4 | 同场景一步骤 1-4 | `IDLE` → … → `CONSENSUS_CHECK` | 同场景一 |
| 5 | MACAO 计票落盘 `vote_result.json`（APPROVED 但含 BLOCKING issue，或 REWORK_REQUIRED） | `CONSENSUS_CHECK`（发 DISPOSITION_REQUIRED） | `vote_result.json` |
| 6 | Executor 提交 `executor.disposition.yml`（FINAL，`requires_new_checkpoint=true`） | `CONSENSUS_CHECK` → `REWORK`（E5a 或 E5） | `executor.disposition.yml` |
| 7 | 发送 `REWORK_REQUEST`（round=2）；r1 产物已归档 | （伴随动作） | — |
| 8 | Claude 修复后生成新 `.dev.yml`（commit `d4e5f6a`，round 2） | `REWORK` → `READY_FOR_REVIEW`（E6） | 新 `.dev.yml`（双匹配） |
| 9 | 发送 `REVIEW_REQUEST`（携带 r1 处置作为上下文） | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2） | — |
| 10 | Reviewers 返回 round 2 意见并达成全批准 | 同场景一步骤 4-7 | 当前轮产物 |

**场景推演三：1:1:1 平票 → Deadlock → 人工裁定带豁免放行**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1-4 | 同场景一步骤 1-4；1 赞成 + 1 反对 + 1 弃权（round 1） | `IDLE` → … → `CONSENSUS_CHECK`（E3） | 3 × `.review.yml` |
| 5 | E3 伴随动作：门禁判定未通过，**即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）**，发送 `HUMAN_OVERRIDE_REQUEST`（Type H，10 分钟时限），进入 `CONSENSUS_CHECK` HOLD | （保持 HOLD 待裁定） | `vote_result.json`（DEADLOCK） |
| 6a | 管理员 `macao override resolve --choice APPROVED --exempt-issue-ids gemini/SEC-01` | 落盘独立 `admin_override.json`（含 override_id），解除 DEADLOCK HOLD，通知执行者进行最终处置（`role_view=SHOULD_DISPOSE`） | `admin_override.json` |
| 6a-1 | Executor 提交 `executor.disposition.yml`（FINAL，`EXEMPTED_BY_ADMIN`+`override_id`，`requires_new_checkpoint=false`） | `CONSENSUS_CHECK` → `MERGING`（E4；编排器校验所有阻断 issue 均已豁免且 FINAL 合法后触发合并） | `executor.disposition.yml` + `admin_override.json` |
| 6b | 管理员选 REWORK | 落盘 `admin_override.json` → `REWORK`（E5） | `admin_override.json` |
| 6c | 管理员选 RETRY_REVIEW | 落盘 `admin_override.json` → `WAITING_REVIEW`（E9；意见作废归档、round 不变） | `admin_override.json` |
| 6d | 管理员选 CANCEL | 落盘 `admin_override.json` → `CANCELLED`（E10 终态） | `admin_override.json` |
| 6e | 管理员选 EXTEND | 落盘 `admin_override.json` → 重置超时保持 HOLD | `admin_override.json` |
| 7 | （仅 6a-1）合并流水线完成 | `MERGING` → `DONE`（E4a） | — |

---

## 第四部分：改进的 MVP 范围与交付计划

### 4.1 严格的 MVP 范围（第一期）

#### 必做 (P0)
- [ ] **多 CLI Adapter 运行时**（基于 PTY 封装与 Hook）
- [ ] **LangGraph Workflow 引擎**（FSM 10 状态机实现）
- [ ] **`.dev.yml`, `.review.yml`, `vote_result.json`, `executor.disposition.yml` 规范实现**
- [ ] **加权共识引擎**（`weighted_2/3_v1` 纯整数五重门禁与配置期独裁帽）
- [ ] **Git Evidence Ref 隔离**（`refs/macao/evidence/...` 与两阶段 Push 校验）
- [ ] **CLI 运维命令**（`init / doctor / reconcile / adopt / reviews show / reviews export / status / override`）
- [ ] **本地 agmsg 集成**（AEP/1.1 协议栈与 16 KiB 字节预算约束）
- [ ] **单机编排的完整端到端测试与真实子进程 OPS 演练**

#### 不做 (P1+)
- [ ] ~~远程 SSH Agent Gateway~~（移至 v1.1）
- [ ] ~~Capability Registry & 动态分布式调度器~~（移至 v1.2）
- [ ] ~~Web Dashboard~~（CLI 先行，后续补 Web）

### 4.2 分期交付计划

```
Phase 1: 契约规范与加权共识核心 (Day 1-2)
  ├─ 固化 Schema (vote_result v2.0, review_disposition, admin_override, review_manifest)
  ├─ 实现 weighted_2/3_v1 纯整数五重门禁算法与独裁帽校验
  └─ 不可变 vote_result.json 计票单一写者落盘

Phase 2: 状态机守卫与意见处置闭环 (Day 3-4)
  ├─ 实现 FSM E3~E7 状态转移守卫与 E5a 改码返工流转
  ├─ 实现 executor.disposition.yml 覆盖率校验与 requires_new_checkpoint 判定
  └─ 实现带 issue 豁免与 override_id 绑定的 admin_override.json

Phase 3: Git Evidence Ref 与合并流水线 (Day 4-5)
  ├─ 实现 refs/macao/evidence/... 拓扑、inbox/staging 提升与 Promotion 机制
  ├─ 实现 Pre-merge Seal (ls-remote 证据校验) 与 Post-merge Seal 两阶段 Push
  └─ 实现 ff_only 与 no_ff 策略下的精确 commit OID 硬校验

Phase 4: CLI 工具链与角色视图投影 (Day 5-6)
  ├─ 升级 init / doctor / reconcile / adopt 命令
  ├─ 实现 reviews show / reviews export 证据查阅命令
  └─ 完善 role_view 角色状态投影

Phase 5: 全量测试集与真实 OPS 验证 (Day 6-7)
  ├─ 加权门禁边界、处置覆盖率、两阶段 Push 单元测试
  └─ 真实 PTY 子进程黑盒端到端场景演练
```

---

## 第五部分：Reviewer Context 设计（解决评审质量问题）

### 5.1 为什么需要规范化 Context？

**问题**：每个 Reviewer CLI 运行在独立进程中，对 Executor 的工作缺乏完整理解。
**解决**：提供标准化的 Reviewer Context 包，涵盖 10 大必需块，以引用与定位器形式高效传递。

### 5.2 标准化的 Reviewer Context 包与 10 大必需块

> 本节是 `review_context` 的**唯一权威完整模型**（两个传输定位块 + 八个语义块，共 10 大必需块）。AEP `REVIEW_REQUEST` 通过引用与定位器传递，机器契约见 `docs/schemas/review_context.schema.json`。

```yaml
review_context:
  # 0. 必需块声明
  required_blocks:
    - repository
    - dev_checkpoint
    - evidence
    - task_info
    - code_changes
    - quality_snapshot
    - executor_self_assessment
    - review_guidelines
    - history
    - references

  # 1. 传输与定位块
  repository:
    workspace_path: ".macao/worktrees/codex/task-1/r1"
    remote_name: "origin"
    fetch_policy: "fetch_source_and_evidence_before_diff"

  dev_checkpoint:
    path: ".macao/.dev.yml"
    commit: "e5f6a7b"
    sha256: "<sha256>"
    base_commit: "b2c3d4e"
    head_commit: "a1b2c3d"
    review_round: 1

  evidence:
    ref: "refs/macao/evidence/task-1/r1"
    commit: "e5f6a7b"
    dev_manifest:
      path: ".macao/.dev.yml"
      commit: "e5f6a7b"
      sha256: "<sha256>"

  # 2. 任务背景与申请全文引用
  task_info:
    description: "Refactored database connection pooling with timeout config"
    source: "review_request"
    path: "docs/reviews/2026-09-01-review-request-task-1.md"
    commit: "e5f6a7b"
    sha256: "<sha256>"

  # 3. 代码变更（传 refs，Reviewer 在本地隔离 worktree 生成 diff）
  code_changes:
    refs:
      base_commit: "b2c3d4e"
      head_commit: "a1b2c3d"
    diff_policy: "generate_locally"

  # 4. 质量指标（引用自 .dev.yml）
  quality_snapshot:
    source: "evidence.dev_manifest"

  # 5. Executor 自评与重点
  executor_self_assessment:
    source: "task_info"
    anchor: "#self-assessment"

  # 6. 评审指引与方法论
  review_guidelines:
    path: "docs/MACAO_REVIEW_GUIDELINES.md"
    commit: "a1b2c3d"
    sha256: "<sha256>"

  # 7. 历史上下文
  history: []

  # 8. 参考资源
  references: []
```

### 5.3 Reviewer 的标准工作流程

每个 Reviewer 收到 `REVIEW_REQUEST` 后，按照此流程操作：

```bash
# Step 1: 提取 Context
cat <<< "$REVIEW_REQUEST" | jq '.payload.review_context' > /tmp/context.json

# Step 2: 定位工作区并按 refs 取得代码变更
cd "$(jq -r '.repository.workspace_path' /tmp/context.json)" || exit 1
REMOTE=$(jq -r '.repository.remote_name // "origin"' /tmp/context.json)
git fetch "$REMOTE"
BASE=$(jq -r '.code_changes.refs.base_commit' /tmp/context.json)
HEAD_COMMIT=$(jq -r '.code_changes.refs.head_commit' /tmp/context.json)
git diff "$BASE".."$HEAD_COMMIT"

# Step 3: 运行自动检查（lint, security, test）
pylint src/
bandit -r src/
mypy src/

# Step 4: 根据 review_focus 进行代码审查

# Step 5: 生成 .review.yml
cat > .macao/.reviews/codex.review.yml <<EOF
version: "1.0"
...
EOF

# Step 6: 发送 REVIEW_RESPONSE 给 MACAO
macao send-message REVIEW_RESPONSE   --review-file .macao/.reviews/codex.review.yml
```

### 5.4 Evidence Git Ref 生命周期与查阅规范

1. **Ref 拓扑与隔离**：
   - Canonical Ref：`refs/macao/evidence/<task_id>/r<round>`；
   - Remote Inbox：`refs/macao/inbox/<task_id>/r<round>/<actor_id>/<message_id>`；
   - 本地 Staging：`.macao/inbox/<task_id>/r<round>/<actor_id>/<message_id>/`。
2. **两阶段验证**：
   - Pre-merge Seal：在进入源码合并前，Orchestrator 必须验证 evidence 已成功 push（经 `ls-remote` 校验）；
   - Post-merge Seal：源码合并并 push 成功后，生成最终审计快照。若 post-merge push 临时失败，保持 `MERGING` 状态并重试，**严禁本地回滚已成功的源码分支**。
3. **查阅与导出**：
   - 证据文档不自动并入 source 分支代码；
   - 用户通过 `macao reviews show <task_id> [--round N]` 与 `macao reviews export <task_id> --to <dir>` 查阅和导出。

---

## 第六部分：人工接管点与错误恢复

### 6.1 明确的人工接管条件

```python
HUMAN_OVERRIDE_TRIGGERS = [
    {
        "condition": "State ambiguity",
        "description": "No valid explicit artifact AND suspected stall (Layer 3 diagnosis confidence < 0.7, see E8)",
        "action": "Ask user: 'What should the state be?'",
        "timeout": "5 minutes (default: HOLD last confirmed state and keep alerting)"
    },
    {
        "condition": "Reviewer timeout",
        "description": "Reviewer didn't respond within 10 minutes",
        "action": "Record timeout abstain ticket (source: timeout), account into seat set, and proceed deterministically",
        "timeout": "10 minutes"
    },
    {
        "condition": "Consensus deadlock",
        "description": "No consensus achievable (e.g., tie vote or lack of quorum)",
        "action": "Ask user: '--choice APPROVED | REWORK | RETRY_REVIEW | CANCEL | EXTEND [--exempt-issue-ids]'",
        "timeout": "10 minutes"
    },
    {
        "condition": "Disposition timeout",
        "description": "Executor failed to submit executor.disposition.yml within timeouts.review_disposition (default 30m)",
        "action": "Ask user: '--choice APPROVED | REWORK | CANCEL | EXTEND [--exempt-issue-ids]'",
        "timeout": "30 minutes (timeouts.review_disposition)"
    },
    {
        "condition": "NEEDS_ADMIN unresolved",
        "description": "Executor marked one or more issues as NEEDS_ADMIN in review disposition",
        "action": "Ask user: '--choice APPROVED (with exemption) | REWORK | CANCEL'",
        "timeout": "10 minutes"
    },
    {
        "condition": "Process crash",
        "description": "Executor CLI crashed unexpectedly",
        "action": "Attempt restart 1x, then ask user: 'Retry or abandon?'",
        "timeout": "Immediate"
    },
    {
        "condition": "Git conflict",
        "description": "Merge failed due to git conflicts",
        "action": "Ask user: 'Resolve conflict manually and continue?'",
        "timeout": "Until conflict resolved"
    },
    {
        "condition": "Unknown state",
        "description": "System stuck > 60min AND Layer 3 diagnosis confidence < 0.7",
        "action": "Ask user: 'Reset to last known state?'",
        "timeout": "Immediate"
    }
]
```

> **人工接管超时总则**：除 trigger 1 已定义 HOLD 默认外，其余全部触发条件到期后的默认动作同样为 **HOLD 当前状态 + 持续告警（升级通知）**——系统在任何情况下都不得因超时而静默推进或自动选择结果。

### 6.2 优雅的降级策略

```
Normal Path:
  Executor → Dev Complete → Review Request → Reviewers Work → Consensus → Disposition → Merge

Degraded Path (1 Reviewer 超时 → 标记弃权):
  Executor → Dev Complete → Review Request → 记录超时弃权票 (source: timeout)
  → 进入 CONSENSUS_CHECK 计票 → 若满足加权门禁则 APPROVED，否则 DEADLOCK 转人工接管

Failure Path (Executor crashed):
  Executor → CRASH → Manual state reset → Resume from last checkpoint
  (User manually confirms: "Reset to READY_FOR_REVIEW")

Abort Path (Too many conflicts):
  Executor → Multiple Rework Rounds → User decides "Give up"
  (Store checkpoint for manual intervention later)
```

---

## 第七部分：与现有产品的对标

### 7.1 对标 Kubernetes 概念

| K8s 概念 | MACAO 对应 | 实现方式 |
|---------|----------|--------|
| Pod | CLI Agent Session | PTY Process + Adapter |
| Service | Agent Registry | 本地 JSON 配置（远程 SSH 配置预留 v1.1） |
| ConfigMap | `.dev.yml` + `.review.yml` | YAML 文件 |
| Event | AEP Message | agmsg Queue |
| StatefulSet | Agent Lifecycle | LangGraph FSM |
| Ingress | Review Workflow | AEP REVIEW_REQUEST 路由 |

### 7.2 对标 CI/CD 流程

```
GitLab CI / GitHub Actions    |    MACAO Workflow
─────────────────────────────────────────────────────
.gitlab-ci.yml                |    Project Config YAML (macao.yaml)
Pipeline: Trigger             |    DEVELOPMENT_STARTED
Build Stage: Compile          |    CODING Stage
Test Stage: Run Tests         |    Quality Metrics (.dev.yml)
Artifact: Upload              |    Evidence Ref Promotion
Review Apps: Deploy for QA    |    REVIEW_REQUEST + Worktree Isolation
Manual Approval               |    Reviewer Voting + Review Disposition
Merge: Push to main           |    Weighted Consensus + Merge
```

---

## 第八部分：成功指标 (KPIs)

### 8.1 技术 KPI

| KPI | Target | 测量方式 |
|-----|--------|---------|
| **State Recognition Accuracy** | >95% | 标注样本集评测（分母 = 观察窗口内全部状态转换次数） |
| **Explicit Signal Usage Rate** | >99% | 产物驱动转移占全部业务状态转移的比例 |
| **Workflow Completion Rate** | >90% | 无人工介入的完成比例 |
| **Human Override Frequency** | <10% | 总流程数中人工接管比例 |
| **Reviewer Average Response Time** | <5min | 从消息发送到响应 |
| **False Positive Alerts** | <5% | 不实警告占总警告比 |
| **MACAO Recovery Time** | <30s | 从崩溃恢复（故障测试） |

### 8.2 用户 KPI

| KPI | Baseline | Target | 改善 |
|-----|----------|--------|------|
| **Code Review Turnaround Time** | 2 小时 | 15 分钟 | ↓ 87% |
| **Multi-Reviewer Consensus Time** | 3 小时 | 8 分钟 | ↓ 96% |
| **Developer Cognitive Load** | 5 封评审消息 | 1 条汇总消息 | ↓ 80% |
| **Rework Cycles (平均)** | 2-3 轮 | <2 轮 | ↓ 30% |

---

## 第九部分：风险与缓解措施

### 9.1 关键风险

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|---------|
| **CLI Hook API 不稳定** | 中 | 高 | PoC 第一阶段验证；备选 PTY 方案 |
| **Reviewer CLI 响应慢** | 中 | 中 | 设置合理超时；实现降级投票 |
| **Git Conflict 导致卡死** | 低 | 高 | 自动检测；提前预警用户 |
| **.yml 格式破坏** | 低 | 中 | YAML Schema 验证；版本控制 |
| **Reviewer 被 prompt injection 操纵投票** | 低 | 高 | 评审输出 Schema 强校验；review_focus 白名单注入；异常投票模式告警（见第十五部分） |
| **第三方 CLI 服务条款限制自动化编排** | 中 | 中 | PoC 前完成 ToS/法务核实；必要时降级为半自动模式 |
| **跨机器网络延迟** | 低 | 低 | MVP 仅支持本地；后续优化 |

---

## 第十部分：总结与验收标准

### 核心创新
1. **规范化流程** - 从黑盒推断转为显式约定；
2. **标准输出物** - `.dev.yml`, `.review.yml`, `vote_result.json`, `executor.disposition.yml` 作为系统间契约；
3. **可靠的状态转换** - 三层识别，优先显式信号；
4. **加权纯整数共识** - 纯整数五重门禁，无浮点误差；
5. **独立 Git Evidence Ref** - 过程存证与源码分支物理隔离。

### 验收标准（未达成前不得勾选）

- [ ] 单机 Claude Code + 2x Reviewer 的完整工作流运行通过
- [ ] 所有关键状态转换由显式产物与命令型转移驱动，无 LLM 裁判（见 §3.3 统一转移表）
- [ ] 三个 CLI 的 Adapter 都能正常启停与通信
- [ ] 自动化测试覆盖 80% 以上逻辑
- [ ] 用户手册与内部文档完备

---

## 第十一部分：系统架构与技术栈

### 11.1 组件图（本地单机）

```text
CLI UI (Rich + prompt_toolkit)
  macao status / task create / override resolve / logs / usage / reviews
        │
Orchestrator（单进程事件循环，LangGraph FSM）
  ├─ State Recognition Engine ......... 第三部分（作用域读取 + HOLD）
  ├─ Consensus Engine ................ §2.3（加权 2/3 纯整数门禁）
  ├─ Merge Controller ................ §14.5（Merge Policy 合并流水线）
  ├─ Config Loader ................... macao.yaml 单一事实源（第十三部分）
  ├─ Usage Meter ..................... 成本计量（第十五部分）
  └─ State Store（SQLite：任务/轮次/FSM 状态/审计事件）
        │ agmsg 本地队列（AEP/1.1 消息）
Adapter Runtime（契约见第十二部分）
  ├─ ClaudeCodeAdapter（PTY + Hook）
  ├─ CodexAdapter（PTY Wrapper）
  ├─ KimiAdapter（PTY Wrapper）
  ├─ OpenCodeAdapter（PTY Wrapper）
  └─ AgOpenAgentAdapter（PTY Wrapper）
        │ PTY 子进程
CLI 进程在独立 Git Worktree 中运行
工作区 git 仓库（.macao/ 产物 + refs/macao/evidence/ 归档）
```

### 11.2 State Store DDL（核心表）

```sql
CREATE TABLE tasks(
  task_id       TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  source_branch TEXT, target_branch TEXT,
  state         TEXT NOT NULL,              -- 当前 FSM 状态（10 态之一，含 CANCELLED，见 §3.3）
  checkpoint_ref TEXT, review_round INTEGER NOT NULL DEFAULT 1,
  created_at TEXT, updated_at TEXT
);
CREATE TABLE artifacts(
  artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  kind TEXT NOT NULL,            -- dev_manifest|review_manifest|vote_result|disposition|admin_override
  path TEXT NOT NULL,            -- 物理路径
  sha256 TEXT, checkpoint_ref TEXT, review_round INTEGER, reviewer_id TEXT,
  consumed INTEGER NOT NULL DEFAULT 0, archived_path TEXT,
  created_at TEXT,
  UNIQUE(task_id, kind, checkpoint_ref, review_round, reviewer_id)
);
CREATE TABLE audit_events(
  sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL, task_id TEXT, type TEXT NOT NULL, detail TEXT
);
CREATE TABLE overrides(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  override_id TEXT NOT NULL,
  sequence_id INTEGER REFERENCES audit_events(sequence_id),
  trigger TEXT, choice TEXT NOT NULL, exempt_issue_ids TEXT, note TEXT
);
CREATE TABLE dead_letter_queue(
  message_id TEXT PRIMARY KEY, payload TEXT,
  retry_count INTEGER, reason TEXT, ts TEXT
);
```

---

## 第十二部分：Adapter Contract v1 与能力矩阵

### 12.1 契约接口

```text
capabilities() -> CapabilityManifest      # 能力声明，启动时上报
preflight()    -> PreflightReport         # 安装/登录态/版本探测
start(agent) / stop(agent, reason)        # 进程生命周期
inject_task(agent, aep_development_started)
ack(message_id)                           # 消息幂等回执
subscribe_events(callback) / get_logs(tail)
cancel(reason)                            # 取消当前任务并回收子进程
```

### 12.2 Capability Manifest 与执行权限

| CLI | can_execute | can_review | hook | noninteractive | worktree | execution_mode | Adapter 类型 |
|-----|-------------|------------|------|----------------|----------|----------------|--------------|
| claude-code | ✓ | ✓ | ✓ | 部分 | ✓ | full（限任务工作区） | claude-hook |
| codex | ✓ | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |
| kimi | ✓ | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |
| opencode | ✓ | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |
| agy | ✓ | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |
| agent | ✓ | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |

---

## 第十三部分：配置规范（macao.yaml 单一事实源）

位置：仓库根目录 `macao.yaml`。正文出现的全部数值（超时/阈值/法定人数/轮次上限）均为该文件的默认值。

```yaml
version: "2.5"
project:
  name: "macao-demo"
  repository:
    workspace_path: "~/work/macao-demo"
    remote_name: "origin"
    default_branch: "main"
team:
  executor:
    id: "cc-ds4"
    cli: "claude-code"
    adapter: "claude-hook"
    model: "claude-3-7-sonnet-20250219"
  reviewers:
    - { id: "codex", cli: "codex", adapter: "pty-wrapper", vote_weight: 2, model: "o3-mini" }
    - { id: "kimi",  cli: "kimi",  adapter: "pty-wrapper", vote_weight: 1, model: "moonshot-v1-32k" }
    - { id: "gemini", cli: "opencode", adapter: "pty-wrapper", vote_weight: 1, model: "gemini-2.0-flash" }
policy:
  consensus_rule: "weighted_2/3_v1"
  dictator_cap_enabled: true     # 3*w_i < 2*W
  minimum_winning_seats: 2       # 胜方最少席位
  seat_quorum_required: 2        # ⌈2N/3⌉
  weight_quorum_required: 3      # ⌈2W/3⌉
  max_rework_rounds: 3
  review_strategy: "delta_plus_focus"
merge:
  strategy: "ff_only"            # ff_only | no_ff
  ci_gate_command: null
  require_human_signoff: true
  rebase_before_merge: false
timeouts:
  development: "2h"
  checkpoint_validation: "1m"
  review_request: "30m"
  per_reviewer: "10m"
  consensus_check: "1m"
  review_disposition: "30m"
thresholds:
  layer2_inference_log_only: true
  llm_diagnosis_override_below: 0.7
cost:
  usage_metering: true
  monthly_budget_usd: null
aep:
  max_message_bytes: 16384
  max_inline_text_bytes: 2048
security:
  allowed_clis: ["claude-code", "codex", "kimi", "opencode", "agy", "agent", "mock-cli"]
  send_terminal_logs_to_reviewers: false
  secrets_masking: true
audit:
  retention_days: 90
```

---

## 第十四部分：用户旅程与运行手册

### 14.1 从零到第一次合并（主旅程）

1. **安装预检**：`macao preflight`；
2. **初始化**：`macao init --new` 或 `macao init --adopt-existing`；
3. **创建任务**：`macao task create --title … --acceptance … --branch feature/x`；
4. **观察**：`macao status` 查看状态与 `role_view` 投影；
5. **处置与接管**：
   - 机器批准但有建议：Executor 提交 `executor.disposition.yml` 逐项闭环；
   - 出现 HUMAN_OVERRIDE_REQUEST 时，`macao override list` → `macao override resolve --choice APPROVED|REWORK|RETRY_REVIEW|CANCEL|EXTEND [--note] [--exempt-issue-ids]`;
6. **合并与发布**：执行 §14.5 Merge Policy；
7. **证据导出**：`macao reviews show <task>` / `macao reviews export <task> --to <dir>`。

### 14.2 日常运维操作与角色投影（role_view）

| 操作 | 命令 | 语义 |
|------|------|------|
| 既有项目接管 | `macao init --adopt-existing` / `macao adopt` | 收集证据并执行受控接管事务 |
| 环境与状态诊断 | `macao doctor` | 只读收集证据、输出候选状态与冲突分析 |
| 状态受控恢复 | `macao reconcile` | 按确定性恢复计划执行受控状态迁移 |
| 证据查阅与导出 | `macao reviews show <task>` / `export` | 读取或导出 evidence ref 中的评审及处置产物 |
| 暂停观察 | `macao pause <task>` | 进入 HOLD，停止状态推进 |
| 取消 | `macao cancel <task>` | 终止任务，通知全体 agent，归档现场 |
| 重试 | `macao retry <task>` | 从最后检查点重放 |
| 合并签字 | `macao merge approve [--note]` | `require_human_signoff: true` 下推送前的人工放行 |
| 用量查询 | `macao usage` | 按阶段/CLI 汇总 token 与调用次数 |

#### 统一角色视图（`role_view`）

| 任务状态与前置条件 | Executor `role_view` | Reviewer `role_view` | `next_action` |
|---|---|---|---|
| `IDLE` / 无活动任务 | `AWAIT_TASK` | `AWAIT_TASK` | `WAIT_TASK_INPUT` |
| `CODING` / `REWORK` | `SHOULD_CODE` | `IDLE_WAIT_DISPATCH` | `EXECUTOR_DEVELOPING` |
| `READY_FOR_REVIEW` | `CHECKPOINT_SUBMITTED` | `IDLE_WAIT_DISPATCH` | `DISPATCH_REVIEWS` |
| `WAITING_REVIEW`（席位未交且有效） | `AWAIT_REVIEWS` | `SHOULD_REVIEW` | `AWAIT_REVIEW_SUBMISSIONS` |
| `WAITING_REVIEW`（席位已提交有效产物）| `AWAIT_REVIEWS` | `REVIEW_SUBMITTED` | `AWAIT_REMAINING_OR_TIMEOUT` |
| `CONSENSUS_CHECK`（尚无 vote_result） | `AWAIT_DECISION` | `AWAIT_DECISION` | `TALLY_CONSENSUS` |
| `CONSENSUS_CHECK`（`requires_disposition` 且无 FINAL） | `SHOULD_DISPOSE` | `AWAIT_DECISION` | `NOTIFY_EXECUTOR_DISPOSE` |
| `CONSENSUS_CHECK`（HOLD: DEADLOCK/超时/NEEDS_ADMIN） | `AWAIT_HUMAN` | `AWAIT_HUMAN` | `ASK_ADMIN` |
| `MERGING` | `AWAIT_MERGE` | `AWAIT_MERGE` | `PERFORM_MERGE_AND_PUSH` |
| `UNKNOWN` | `AWAIT_HUMAN` | `AWAIT_HUMAN` | `RUN_DOCTOR_OR_ASK_ADMIN` |
| `DONE` / `CANCELLED` | `AWAIT_TASK` | `AWAIT_TASK` | `TASK_COMPLETED` |

### 14.3 日志与保留

Terminal 日志滚动保留 `audit.retention_days`（默认 90 天）；审计事件（状态转移/人工决策/override 回执）永久保留于 State Store。

### 14.4 升级与降级

CLI 版本超出支持矩阵 → preflight 告警并要求显式确认；某 Reviewer Adapter 故障时可临时将其标记弃权，走超时降级路径（§6.2）。

### 14.5 Merge Policy（MERGING 状态内的合并流水线）

E4 进入 `MERGING` 后，Merge Controller 顺序执行：

1. **Pre-merge Evidence 校验（远端共享 / 纯本地两模式）**：
   - **远端共享模式**（`repository.remote_name` 配置非空，默认 `origin`）：Orchestrator 通过 `git ls-remote --exit-code <remote> refs/macao/evidence/<task_id>/r<round>` 严格校验证据引用已成功同步至远端；若远端不可达或推送失败，100% fail-closed 拦截并触发 E4b；
   - **纯本地模式**（`repository.remote_name: null` 显式声明）：跳过远端 `ls-remote` 校验与推送，仅强校验本地 `refs/macao/evidence/<task_id>/r<round>` 引用存在性与不可篡改哈希；
2. **检出与校验**：检出 target 分支。
   - 在 `merge.strategy == "ff_only"` 策略下：fast-forward 合并，最终 remote tip 必须精确等于 `vote_result.checkpoint_ref`；
   - 在 `merge.strategy == "no_ff"` 策略下：创建 merge commit，其第二父必须精确等于 `vote_result.checkpoint_ref`；
3. **CI Gate**：`merge.ci_gate_command` 非空时执行测试；失败 $\implies$ 触发 E4b 返工；
4. **人工签字**：`require_human_signoff: true` 时，推送前须用户执行 `macao merge approve`；拒绝 $\implies$ 触发 E4b；
5. **推送与 Post-merge Seal**：推送合并后的 target 分支，生成 post-merge 审计快照。若 post-merge push 临时失败，保持 `MERGING` 重试，**严禁本地回滚已成功的源码分支**；
6. **通告完成**：发送 `MERGE_COMPLETED`（Type F），进入 `DONE`（E4a）。

---

## 第十五部分：边界声明与非功能需求

### 15.1 产品边界

v2.x 定位为本地单机与隔离 Worktree 协作规格。以下能力明确不在 MVP 内：跨物理机网关（v1.1）、多任务并行动态调度（v1.2）、Web Dashboard（v1.1+）。

### 15.2 返工策略

- `max_rework_rounds = 3`：达到上限仍返工 → E7 人工裁定（放弃 / 继续 / 缩小范围）；
- `review_strategy = delta_plus_focus`：第 n 轮 `REVIEW_REQUEST` 附带上一轮处置决定与增量 diff，Reviewer 做聚焦抽查。

### 15.3 安全边界

| 风险 | 缓解措施 |
|------|---------|
| Reviewer 读到恶意代码被 prompt injection | 评审产物 Schema 强校验；review_focus 白名单注入；异常投票模式告警 |
| Reviewer 执行破坏性命令 | 执行权限边界强制：Reviewer 必须 sandboxed + 独立 Git Worktree |
| 凭据泄露 | 凭据经环境变量/keyring 注入子进程，不落盘明文；日志脱敏 |
| 代码外传 | `security.allowed_clis` 白名单约束可用 CLI；`send_terminal_logs_to_reviewers` 默认关闭 |

### 15.4 成本计量

Usage Meter 记录每次流程各阶段的 token 用量与调用次数。预算超限仅告警不硬限（`monthly_budget_usd: null`）。

### 15.5 评审质量评测计划

KPI 之外增加共识有效性评测：构造 N ≥ 20 的含已知缺陷样本集，测量共识召回率与误报率，结果记入 PoC 报告。

---

## 第十六部分：部署形态与协作拓扑

### 16.1 角色定义与垄断权（单一写者原则）

| 角色 | 实体 | 核心职责 | 垄断权（单一写者原则） |
|------|------|---------|----------------------|
| **编排者/管理员** | 用户 (Admin) + MACAO Orchestrator | 任务受理、FSM 推进（E1~E10）、加权共识仲裁、合并执行、人工接管处理与豁免裁决 | 唯一写不可变 `vote_result.json`、唯一写 `admin_override.json`、唯一执行 merge、唯一管理 evidence promotion |
| **执行者** | Executor CLI（Claude Code / OpenCode） | 理解需求 → 改码 → 自测 → commit → 生成 `.dev.yml`；写 `executor.disposition.yml` | 唯一写 `.dev.yml`、唯一产生业务 commit、唯一写 `executor.disposition.yml` |
| **评审专家** | Reviewer CLI ×N（Codex / Kimi / Gemini 等） | 按 review_context 取 diff → 审查 → 产出结构化 issue 清单 → 投票 | 各自唯一写自己的 `.review.yml` 与评审全文 |

### 16.2 端到端开发流程总览

| # | 阶段 | 发起 → 接受 | 交接物与通道 | 完成标志 |
|---|------|------------|-------------|---------|
| 0 | 部署预检 | 用户 → Orchestrator | `macao preflight` | PreflightReport 全绿 |
| 1 | 任务受理 | 用户 → Orchestrator | `macao task create` | E1：`DEVELOPMENT_STARTED` 下发 |
| 2 | 开发 | Orchestrator → 执行者 | AEP 任务指令；执行者在工作区 commit | 有效 `.dev.yml` 出现 |
| 3 | 检查点与分发 | 执行者 → Orchestrator → 评审专家 | `.dev.yml` → `REVIEW_REQUEST` 携带 context | E2：`.dev.yml` 归档，评审 deadline 生效 |
| 4 | 并行评审 | Orchestrator ⇄ 各评审专家 | 各专家独立取 diff → 各写 `.review.yml` | 全席位 accounted（E3） |
| 5 | 共识与处置 | Orchestrator ⇄ 执行者 | 加权门禁裁决 `vote_result.json`；提交 disposition | APPROVED（无改码进 E4 / 改码进 E5a）或 REWORK（E5） |
| 6 | 合并发布 | Orchestrator → git remote | Merge Policy：merge → CI gate → push → `MERGE_COMPLETED` | E4a：merge commit + 审计记录 |
| 7 | 返工循环 | Orchestrator → 执行者 | `REWORK_REQUEST`（round+1） | E6：闭环或 E7 人工裁定 |

### 16.3 单机同置（v2.5 MVP 规格）

```text
┌────────────────── 物理机 M ──────────────────────────┐
│  用户 ⇄ macao CLI                                    │
│      │                                               │
│  Orchestrator（FSM/加权共识/Merge/SQLite State Store） │
│      │  本地 agmsg 队列（文件型，AEP/1.1 消息）         │
│  ├─ ClaudeCodeAdapter ── PTY ── claude-code（执行者） │
│  ├─ CodexAdapter ─────── PTY ── codex（评审专家 A）   │
│  ├─ KimiAdapter ───────── PTY ── kimi（评审专家 B）   │
│  └─ OpenCodeAdapter ──── PTY ── opencode（评审专家 C）│
│      │                                               │
│  同一仓库：主工作区（Executor）+ 每 Reviewer 独立      │
│  worktree；.macao/ 产物 + refs/macao/evidence/ 归档   │
└──────────────────────────────────────────────────────┘
```

---

## 第十七部分：Phase 3 真实多 Agent 调度与输出自愈机制

### 17.1 LiveAgentDispatcher 真实工作区派发
- **Worktree 动态隔离**：在状态推进至 `WAITING_REVIEW` 时，在 `.macao/worktrees/<reviewer_id>/<task_id>/r<round>` 动态创建物理独立的 Git Worktree；
- **PTY 伪终端会话生命周期**：为每个 CLI 进程分配独立子终端，注入 non-interactive 与 sandboxed 参数，实时捕获终端输出；
- **原子清理保障**：审查结束或任务终结后，执行 `git worktree remove --force` 原子销毁工作区。

### 17.2 ReviewExtractor 输出清洗与提取
- **Level 1 正则与 ANSI 剥离**：自动去除 ANSI 终端颜色转义码，匹配 Markdown 代码栅栏（```yaml ... ```）提取纯净 YAML；
- **Level 2 Schema 强校验**：使用 Draft-07 `review_manifest.schema.json` 强校验，原样提取票面，严禁代写或修改任何投票决策。

---

## 第十八部分：后台超时扫描守护进程 (OrchestratorDaemon)

- **轮询驱动**：基于系统时钟定时扫描活跃任务的截止时间（Deadline Epoch）；
- **超时自动持久化**：审查员超时自动记入 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件，记录 `source: timeout` 的超时票据并纳入 accounted 集合；
- **确定性推进**：所有席位 accounted 后自动触发共识仲裁，推动状态机进入 `CONSENSUS_CHECK`。若无法达成共识则即时落盘 `DEADLOCK` 并发送 `HUMAN_OVERRIDE_REQUEST`。

---

## 第十九部分：细粒度模型透传与多元角色矩阵

- **全角色自由组合**：`opencode`, `agy`, `agent`, `claude-code`, `codex`, `kimi` 均支持作为 `executor` 或 `reviewers`；
- **模型参数透传**：在 `macao.yaml` 中通过 `model: "<model_id>"` 显式声明具体模型，底层 PTY 进程自动透传参数。

---

## 第二十部分：智能向导与运行时环境隔离

- **`macao setup` 智能向导**：自动探活系统 PATH 中的 AI CLI 资产、探测 Git 分支与测试命令，生成强合规配置；
- **`.gitignore` 运行时自动隔离**：自动在被管项目 `.gitignore` 中追加 `.macao/worktrees/` 与 `*.db`，彻底杜绝仓库污染。

---

## 附录：版本演进记录

- **v1.0**: 初始高阶架构设计（产品代号 "A"）
- **v2.0**: 规范化产物信封、FSM 状态机收敛、双 Reviewer 共识与 PTY 封装
- **v2.3**: review_context 权威结构收敛、Deadlock HOLD 方案 B、E9/E10 状态机收敛
- **v2.3.1**: 评审对象与合并对象硬绑定、Worktree 强制化、跨平台断言修复、is_ancestor 拓扑校验（达成 L3 SCENARIO-VERIFIED / PG-2 认证）
- **v2.4**: Phase 3 真实 Worktree 调度、ReviewExtractor 输出自愈、OrchestratorDaemon 后台守护、细粒度模型控制与 Cursor Agent 接入
- **v2.5（现行权威基准）**：
  - **P-1 零语义创作**：Orchestrator 收敛为确定性规则与路由系统，彻底消除代写摘要与语义合并；
  - **内容与控制分层**：AEP/1.1 引入 16 KiB 字节预算，增加 `DISPOSITION_REQUIRED` 调度通道；
  - **独立 Review Disposition**：Executor 单一写入按轮隔离的 `executor.disposition.yml`，消除 `issues_summary` 双写冲突；
  - **显式改码守卫**：引入 `requires_new_checkpoint: boolean` 与 E5a 状态流转；
  - **加权 2/3 共识**：引入 `weighted_2/3_v1` 纯整数五重门禁与配置期独裁帽，防单模型支配；
  - **独立 Evidence Git Ref**：建立 `refs/macao/evidence/...` 拓扑与两阶段 Push 校验，实现 source HEAD 隔离；
  - **动态状态接管**：规范 `init / doctor / reconcile / adopt` 边界，确立 `role_view` 投影与 AI diagnostic-only 纪律。
