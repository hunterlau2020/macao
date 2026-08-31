# MACAO (Multi-Agent CLI Agent Orchestrator) - 产品方案 v2.5

> **核心理念**：通过**流程规范化** + **输出物标准化** + **零语义创作编排**，使 Agent 状态识别从"黑盒推断"转变为"约定式识别与确定性路由"。

> **文档地位：本文档是 MACAO v2.5 的权威基准文档**，其他文档与本文档不一致时，以本文档为准。
>
> **文档体系**（docs/）：
>
> | 文档 | 角色 | 状态 |
> |------|------|------|
> | `SRSv1.md` | v1.0 原始设计（产品暂定名 "A"） | 历史基线，已被 v2.0/v2.5 取代 |
> | `MACAO_PRD_v2.md` | v2.5 产品方案（本文档） | **权威基准** |
> | `EXECUTIVE_SUMMARY.md` | v2.5 执行摘要与快速参考 | 本文档的摘要 |
> | `IMPROVEMENT_SUMMARY.md` | v1.0 → v2.0 → v2.5 改进对比 | 演进过程说明 |

---

## 执行摘要

### 产品定义
**MACAO** 是一个面向 AI 软件开发团队的**跨终端 CLI 进程编排平台**，通过统一调度不同厂商的 CLI Coding Agent（Claude Code, Codex, Kimi-Code 等），实现跨物理机、多角色、多阶段的软件研发自动化协作。（MVP 阶段聚焦单机本地场景，跨物理机/远程 SSH 支持规划于 v1.1，见 §4.1）

### 核心差异化
- ✅ **不追求支持所有 CLI**，而是建立"标准兼容规范"
- ✅ **用规范化流程替代黑盒状态推断**，提升可靠性
- ✅ **清晰的输出物约定**，使 Agent 通信透明化
- ✅ **分阶段 MVP**，风险可控

### 关键成功要素
1. **流程标准化** - 所有 Agent 遵循统一的开发/评审范式
2. **输出物规范化** - 每个阶段都有明确的物理产物作为状态信号
3. **Adapter 可插拔** - 新增 CLI 不需要修改核心引擎
4. **人工接管点清晰** - 系统何时应该寻求人工介入

---

## 第一部分：规范化开发/评审流程

### 1.1 完整的工作流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MACAO Workflow FSM                          │
└─────────────────────────────────────────────────────────────────────┘

           User Input
              │
              v
    ┌──────────────────┐
    │  REQUIREMENT     │  ◄─── 用户明确需求
    │  (Human Review)  │
    └────────┬─────────┘
             │
             v
    ┌──────────────────────────────────────┐
    │  PHASE 1: DEVELOPMENT                │
    │  ├─ Executor: Claude Code            │
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
    ┌──────────────────────────────────────┐
    │  PHASE 3: REVIEWER WORK              │
    │  ├─ Reviewer 收信后进入 WAITING_REVIEW  │
    │  ├─ 运行本地 CLI 检查（代码、安全等）│
    │  └─ 生成 .review.yml                 │
    └────────┬─────────────────────────────┘
             │
      (达到法定人数或超时降级流程完成)
             │
             v
    ┌──────────────────────────────────────┐
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
     │  └─ Executor 提交 review_disposition (逐项声明改码需求)│
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
| **REVIEW_REQUEST / REVIEWING** | `WAITING_REVIEW`（Reviewer 侧 `REVIEWING`） | MACAO 发送 `REVIEW_REQUEST` AEP | 全部配置席位响应或超时降级流程完成（E3） | 各 Reviewer `.review.yml` 与评审全文（当前 round） | 30m（10m/reviewer 触发 ping） |
| **CONSENSUS & DISPOSITION** | `CONSENSUS_CHECK` | 全席位 accounted（收到有效票或超时标记） | `vote_result.json` 落盘，无 issue 或存在合法的 FINAL `review_disposition`（E4/E5/E5a），Deadlock/超时经人工裁定（E7/E9） | `vote_result.json` + `review_disposition.yml` | 1m (计票) / 30m (disposition) |
| **MERGE / REWORK** | `MERGING` / `DONE` / `REWORK` | 决策 = APPROVED 且处置无改码进入合并（E4）/ 决策 = REWORK_REQUIRED（E5）或处置要求改码（E5a）进入返工 | 合并完成（`MERGE_COMPLETED`，E4a）、CI 失败返工（E4b）、返工闭环（E6）；用户取消进入 `CANCELLED`（E10） | merge commit 或新一轮 `.dev.yml` | - |

---

## 第二部分：标准输出物规范

#### 2.1 `.dev.yml` - Development Checkpoint Manifest

**用途**：Executor（Claude Code）明确向 MACAO 宣布"我的工作已完成并准备评审"

**位置**：项目根目录 `.macao/.dev.yml`（提交至 evidence ref，不污染 source branch）

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
    tests_exempt: false   # 项目无测试时置 true，并在 checklist 中说明原因

  # 关键检查清单
  checklist:
    - "✓ All tests pass"
    - "✓ Lint checks pass"
    - "✓ Type checks pass"
    - "✓ Security scan passed"

status: "ready_for_review"
signal: "EXPLICIT"  # 显式信号，MACAO 强制认可
```

---

### 2.2 `.review.yml` - Reviewer Opinion Manifest

**用途**：每个 Reviewer 返回其审查意见与发现的问题清单，作为加权计票与逐项处置的依据

**位置**：`.macao/.reviews/<reviewer_id>.review.yml`（通过 inbox/staging 提升至 evidence ref）

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

**用途**：MACAO 编排器单一生成的机器计票汇总，记录不可变仲裁结果

**位置**：`.macao/vote_result.json`（及 evidence ref 归档）

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

AEP v1.1 共定义 **8 种消息类型**：

| # | 消息类型 | 方向 | 用途 | 备注 |
|---|---------|------|------|------|
| 1 | `DEVELOPMENT_STARTED` | MACAO → Executor | 下发开发任务与成功标准 | AEP/1.0 兼容 |
| 2 | `REVIEW_REQUEST` | MACAO → Reviewers | 发起评审，携带引用式 `review_context` | 升级为 Ref/Locator 集合 |
| 3 | `REVIEW_RESPONSE` | Reviewer → MACAO | 返回 `.review.yml` 与投票 | 升级三值投票与 Issue 分类 |
| 4 | `REWORK_REQUEST` | MACAO → Executor | 下发返工通知（round+1） | 升级绑定上一轮 disposition |
| 5 | `DISPOSITION_REQUIRED` | MACAO → Executor | **v2.5 新增**：通知执行者对本轮 issue 逐项处置 | 携带 deadline 与 vote_result 引用 |
| 6 | `MERGE_COMPLETED` | MACAO → 全体 | 通告共识达成与合并结果 | 携带 merge_commit |
| 7 | `STATE_CHANGED` | Agent → MACAO | Agent 上报自身状态变化 | 状态只读投影 |
| 8 | `HUMAN_OVERRIDE_REQUEST` | MACAO → User | 请求人工接管决策（DEADLOCK、超时、NEEDS_ADMIN） | 携带 issue 级上下文 |

**AEP 协议字节预算与引用规范**：
- `aep.max_message_bytes` 默认 **16384**（16 KiB）；单个内联自然语言字段上限 **2048** 字节；
- 严禁内联 diff、完整申请、完整结论、处置正文与终端长日志；超限内容必须外置并通过 `path + commit + sha256` 强引用；
- 发送与接收端双向严格校验，超限拒绝发送并报错，严禁静默截断。

以下给出开发/评审主流程的全部 7 个消息类型（1-4 为核心详细篇幅，5-7 为信封级规格）的格式示例。

**统一信封约定**（适用于全部 7 类消息）：

- 信封固定字段：`protocol` / `message_id` / `timestamp` / `type` / `from` / `to` / `payload`
- `from` 为单值字符串；接收方字段**统一为 `to`**——单接收者为字符串，多接收者为字符串数组。不使用 `to_agent` / `to_agents`
- 所有指向被评审开发检查点 commit 的字段**统一命名为 `checkpoint_ref`**（与 `.review.yml`、`vote_result.json` 的产物 Schema 一致）
- 下述 JSON 示例均为合法 JSON（说明性文字一律放在代码块外）

#### Type A：开发阶段通知

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-001",
  "timestamp": "2024-01-15T10:00:00Z",

  "type": "DEVELOPMENT_STARTED",
  "from": "macao",
  "to": "cc-ds4",

  "payload": {
    "project": "macao-demo",
    "task_id": "task-20240115-001",
    "source_branch": "feature/db-refactor",
    "target_branch": "main",
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
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-002",
  "timestamp": "2024-01-15T10:35:00Z",

  "type": "REVIEW_REQUEST",
  "from": "macao",
  "to": ["cc-glm", "kimi"],

  "payload": {
    "project": "macao-demo",
    "executor": "cc-ds4",
    "checkpoint_ref": "a1b2c3d",
    "review_round": 1,

    "review_context": {
      "dev_checkpoint": {
        "path": ".macao/.dev.yml",
        "content_base64": "..."
      },

      "repository": {
        "workspace_path": "~/work/macao-demo/.macao/worktrees/kimi/r1",
        "remote_name": "origin",
        "fetch_policy": "fetch_before_diff"
      },

      "task_info": {
        "description": "Refactored database connection pooling with timeout config",
        "review_focus": [
          "Thread safety in connection pool",
          "Timeout configuration correctness",
          "Backward compatibility"
        ]
      },

      "code_changes": {
        "refs": {
          "base_commit": "b2c3d4e",
          "head_commit": "a1b2c3d"
        },
        "diff_command": "git diff b2c3d4e..a1b2c3d",
        "summary": {
          "files_changed": 5,
          "insertions": 120,
          "deletions": 45
        },
        "files_list": [
          { "path": "src/db/connection.py", "status": "modified", "added_lines": 80, "deleted_lines": 30 },
          { "path": "tests/test_db.py", "status": "modified", "added_lines": 35, "deleted_lines": 12 }
        ]
      },

      "quality_snapshot": {
        "tests": { "passed": 24, "failed": 0, "coverage": 0.87 },
        "static_analysis": { "lint_errors": 0 }
      },

      "executor_self_assessment": {
        "review_focus": [
          "Thread safety in connection pool",
          "Timeout configuration correctness"
        ],
        "known_limitations": ["Connection retry logic not implemented yet"]
      },

      "history": { "previous_reviews": 0, "previous_feedback": [] },

      "references": { "architecture_doc": "docs/db_design.md", "related_tickets": ["TASK-123"] }
    },

    "review_deadline": "2024-01-15T11:05:00Z",
    "expected_output": {
      "format": ".review.yml",
      "location": ".macao/.reviews/{reviewer_id}.review.yml"
    }
  }
}
```

> **代码变更载体与仓库定位约定（重要）**：
> 1. `code_changes.refs.{base_commit, head_commit}` 是**唯一权威路径**（全文所有示例、消费代码一律使用该嵌套结构，不允许扁平写法）；`diff_command` 仅是给 Reviewer 的参考命令，不是传输内容。
> 2. 仓库/工作区定位：优先取 `review_context.repository` 块（与上方示例一致）；缺省时按 `project` 名称从项目配置 `macao.yaml` 的 `repository` 段解析（见第十三部分）。两者必居其一，否则该 `REVIEW_REQUEST` 判为无效消息。
> 3. Reviewer 在本地工作区执行 `git fetch` + `git diff` 取得变更（见 §5.3），不内联 diff 文本或 patch 内容，规避消息体积上限、编码与截断问题；若未来需要离线评审再扩展内联 patch（需另行定义大小上限与摘要校验）。
> 4. **review_context 唯一权威完整模型见 §5.2**（两个传输块 + 六个语义块）；本示例为其最小子集——顶层键名与嵌套路径必须与 §5.2 完全一致，可选块（`quality_snapshot.performance` 等）可省略。机器可校验契约：`docs/schemas/review_context.schema.json`。

#### Type C：评审反馈

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-003",
  "timestamp": "2024-01-15T10:48:00Z",

  "type": "REVIEW_RESPONSE",
  "from": "cc-glm",
  "to": "macao",

  "payload": {
    "project": "macao-demo",
    "checkpoint_ref": "a1b2c3d",

    "review_file": {
      "path": ".macao/.reviews/cc-glm.review.yml",
      "content_base64": "..."
    },

    "vote_summary": {
      "status": "CHANGES_REQUESTED",
      "issues_count": 3,
      "can_auto_fix": false
    }
  }
}
```

#### Type D：Rework 请求

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-004",
  "timestamp": "2024-01-15T10:56:00Z",

  "type": "REWORK_REQUEST",
  "from": "macao",
  "to": "cc-ds4",

  "payload": {
    "project": "macao-demo",
    "checkpoint_ref": "a1b2c3d",
    "round": 2,

    "issues_to_fix": [
      {
        "reviewer": "cc-glm",
        "type": "logic",
        "severity": "major",
        "description": "Missing exception handling for socket timeout",
        "suggestion": "Wrap in try-except with proper logging"
      }
    ],

    "next_checkpoint_deadline": "2024-01-15T12:56:00Z"
  }
}
```

#### Type E：合并完成通告

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-005",
  "timestamp": "2024-01-15T11:00:00Z",

  "type": "MERGE_COMPLETED",
  "from": "macao",
  "to": ["cc-ds4", "cc-glm", "kimi"],

  "payload": {
    "project": "macao-demo",
    "checkpoint_ref": "a1b2c3d",
    "vote_result_path": ".macao/vote_result.json",
    "merge_commit": "d4e5f6a"
  }
}
```

#### Type F：状态上报

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-006",
  "timestamp": "2024-01-15T10:20:00Z",

  "type": "STATE_CHANGED",
  "from": "cc-ds4",
  "to": "macao",

  "payload": {
    "project": "macao-demo",
    "state": "CODING",
    "detail": "refactoring connection pool",
    "attachments": [
      { "name": "dev_checkpoint", "path": ".macao/.dev.yml", "content_base64": "..." }
    ]
  }
}
```

> 跨机部署（§16.4 δ2）时，产物随 `attachments` 以 content_base64 上行，git 提交仍是存证。

#### Type G：人工接管请求

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-007",
  "timestamp": "2024-01-15T10:58:00Z",

  "type": "HUMAN_OVERRIDE_REQUEST",
  "from": "macao",
  "to": "user",

  "payload": {
    "trigger": "consensus_deadlock",
    "context": "2 Reviewer 配置下 1 弃权 + 1 反对，有效票低于法定人数 2",
    "options": ["APPROVED", "REWORK", "RETRY_REVIEW", "CANCEL"],
    "deadline": "2024-01-15T11:08:00Z"
  }
}
```

---

## 第三部分：改进的状态识别策略

### 3.1 三层识别架构（改进版）

```
┌──────────────────────────────────────────────────────────────┐
│              State Recognition Engine v2                     │
│         (Explicit Signal First, Inference Last)              │
└──────────────────────────────────────────────────────────────┘

Layer 1: Explicit Signal (100% 可信)
├─ .dev.yml 状态字段 = "ready_for_review"
├─ .review.yml 状态字段 = "CHANGES_REQUESTED"
└─ vote_result.json 决策字段 = "APPROVED"
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
    分层约束不变：仅 Layer 1 产生业务状态转移；Layer 2 仅日志/预警；
    Layer 3 仅诊断，置信度 < 0.7 时才触发人工接管（与 §3.1 一致）。
    AEP 命令是命令型显式转移，由 Orchestrator 执行，与产物同表登记于 §3.3。
    """
    st  = current_state(agent_id)        # 当前已确认 FSM 状态（State Store，见第十一部分）
    ref = current_checkpoint(project)    # 当前轮被评审 commit；新任务/新轮次开始时更新
    rnd = current_round(project)         # 当前返工轮次，从 1 起；发送 REWORK_REQUEST 时 +1

    # ===== Layer 1a: 开发侧产物 .dev.yml —— 仅 CODING/REWORK 状态受理 =====
    if st in (AgentState.CODING, AgentState.REWORK):
        dev = load_and_validate('.macao/.dev.yml', DEV_YML_SCHEMA,
                                expect_review_round=rnd,
                                not_consumed=True,
                                require_new_commit=True)   # commit 必须是未消费过的新 commit
        if dev.valid:                                      # 最小有效性规则见 §2.1
            update_checkpoint(dev.latest_commit, rnd)      # 锁定本轮被评审对象
            return AgentState.READY_FOR_REVIEW             # 进入检查点窗口（超时 1m）

    # ===== READY_FOR_REVIEW 不读取产物，仅由命令型转移离开 =====
    elif st == AgentState.READY_FOR_REVIEW:
        pass   # Orchestrator 归档 .dev.yml 并发送 REVIEW_REQUEST 后，
               # 经统一转移表 E2 进入 WAITING_REVIEW（§3.3）

    # ===== Layer 1b: WAITING_REVIEW 只收当前 ref/round 的 .review.yml =====
    elif st == AgentState.WAITING_REVIEW:
        reviews = load_all_validated('.macao/.reviews/*.review.yml', REVIEW_YML_SCHEMA,
                                     expect_checkpoint_ref=ref,
                                     expect_review_round=rnd)
        if reviews.count_valid >= minimum_quorum(reviews.configured):   # 法定人数见 §2.3
            return AgentState.CONSENSUS_CHECK

    # ===== Layer 1c: CONSENSUS_CHECK 只收当前 ref/round 的 vote_result.json =====
    elif st == AgentState.CONSENSUS_CHECK:
        result = load_and_validate('.macao/vote_result.json', VOTE_RESULT_SCHEMA,
                                   expect_checkpoint_ref=ref,
                                   expect_review_round=rnd)
        if result.valid:
            archive_round_artifacts(ref, rnd)              # 本轮产物归档（§3.4）
            # 显式四分支：终局 decision 枚举包含 APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED（Schema 强制）
            if result.decision == 'APPROVED':
                return AgentState.MERGING                  # E4：进入合并流水线（E4a/E4b 命令驱动）
            elif result.decision == 'REWORK_REQUIRED':
                # E5 守卫：round 已达到 max_rework_rounds 时不得自动返回 REWORK，
                # 改由 Orchestrator 发 HUMAN_OVERRIDE_REQUEST（Type G）→ E7 人工裁定（§15.2）
                if rnd < max_rework_rounds:
                    return AgentState.REWORK               # E5
                return request_human_override(agent_id='orchestrator', reason='max_rework_rounds_failed')
            elif result.decision == 'RETRY_REVIEW':
                return AgentState.WAITING_REVIEW           # E9：作废重试当前评审轮次
            elif result.decision == 'CANCELLED':
                return AgentState.CANCELLED                # E10：任务终止取消终态

    # ===== Layer 2: 行为推断 —— 只记录与预警，永不改变业务状态 =====
    signals = collect_behavior_signals(agent_id)          # git / tests / pty_idle
    inferred = infer_state_from_behavior(signals)
    log_behavior_inference(agent_id, inferred, confidence=0.8)
    emit_warning(f"Agent {agent_id}: 状态 {st} 下无有效显式产物，推断 {inferred} 仅供参考")

    # ===== Layer 3: LLM Judgment（仅故障诊断用，不产生业务状态）=====
    if is_agent_suspected_deadlock(agent_id):
        logs = get_terminal_logs(agent_id, lines=300)
        diagnosis = call_llm_for_diagnosis(logs, signals)
        report_diagnosis(diagnosis)                # 始终提示用户，不自动决策

        if diagnosis.confidence < 0.7:             # 仅低置信度触发人工接管
            trigger_human_override(
                agent_id=agent_id,
                reason="State ambiguous, awaiting human decision",
                diagnostic_info=diagnosis
            )
            return AgentState.UNKNOWN              # 等待用户确认后人工设定状态

    # 未命中显式信号且未触发人工接管：保持上一个已确认状态（HOLD），不推进
    return last_confirmed_state(agent_id)
```

> **行为约定**（与 §3.1 分层承诺及 §3.3 统一转移表严格一致）：
> 1. 业务状态的转移只有两类来源：**命令型**（Orchestrator 发出的 AEP 指令：`DEVELOPMENT_STARTED` / `REVIEW_REQUEST` / `REWORK_REQUEST` 等）与**产物型**（作用域内的显式产物）。两者同表登记于 §3.3，不存在第三种来源。
> 2. 产物识别是**状态作用域化**的：每个状态只读取属于自己的产物（生命周期见 §3.4），旧产物一律忽略或已归档——对全部文件做固定顺序扫描被明确禁止。
> 3. Layer 2 的推断结果只进入日志与告警；无有效产物时保持（HOLD）上一个已确认状态，绝不静默推进。
> 4. `.review.yml` / `vote_result.json` 必须校验 `checkpoint_ref` 与 `review_round` 双匹配；`.dev.yml` 校验 `review_round` 与"新 commit"两个条件，防止跨轮次误读。

### 3.3 统一状态转移表（命令 + 产物）

业务状态转移只有两类来源：**AEP 命令**（命令型）与**显式产物**（产物型），二者在同一张表登记。
验收标准：任意时刻每一步最多命中一个合法转移（推演见 §3.4）。

| 编号 | 当前状态 | 来源类型 | 触发条件（含校验） | 目标状态 | 伴随动作（消费/归档/通知） |
|------|---------|---------|------------------|---------|--------------------------|
| E1 | `IDLE` | 命令 | 用户受理任务，发送 `DEVELOPMENT_STARTED` AEP | `CODING` | 创建任务记录（State Store）；round=1 |
| — | `CODING` / `REWORK` | 产物 | 当前轮 `.dev.yml` 与评审申请通过最小有效性校验（新 commit + round 匹配） | `READY_FOR_REVIEW` | 锁定 checkpoint_ref；检查点窗口计时（1m） |
| E2 | `READY_FOR_REVIEW` | 命令 | `.dev.yml` 消费完成，发送 `REVIEW_REQUEST` AEP | `WAITING_REVIEW` | 提升至 canonical evidence ref；记录评审 deadline |
| E3 | `WAITING_REVIEW` | 产物/超时 | **所有配置席位已响应（收到有效 .review.yml）或已被持久化 timeout 机制纳入 accounted 集合** | `CONSENSUS_CHECK` | 提升至 evidence ref；**票数判定是确定性函数**——若算出 Deadlock，即时落盘不可变 `vote_result.json`（`decision: DEADLOCK`）并在伴随动作内发送 `HUMAN_OVERRIDE_REQUEST`（Type H，§6.1）进入 **HOLD**，等待 E7 裁定 |
| — | `WAITING_REVIEW` | 超时 | 席位到达超时时间（如 10m/reviewer）触发 timeout scanner | `WAITING_REVIEW` | 记录超时弃权票据（`source: timeout`），不提前截断其他席位，计入 accounted 集合 |
| E4 | `CONSENSUS_CHECK` | 产物/命令 | 机器决策为 `APPROVED`（或经合法 E7 override 裁决）；无 issue，或存在 FINAL `review_disposition` 精确覆盖全部 issue 且所有 `requires_new_checkpoint=false` | `MERGING` | Merge Controller 启动合并流水线（§14.5：检出 → pre-merge evidence push 校验 → merge → CI gate → 人工签字 → push） |
| E4a | `MERGING` | 命令 | 合并流水线全部成功，且**最终 push 对象 == `vote_result.json.checkpoint_ref` 硬校验通过**（期间未产生任何新 commit；CI gate 通过、push 完成、签字按策略收集、post-merge audit evidence 生成） | `DONE` | 发送 `MERGE_COMPLETED`（含 merge_commit）；本轮产物归档 |
| E4b | `MERGING` | 命令 | CI gate 失败，或 push 失败不可自动恢复，或签字被拒绝 | `REWORK` | 生成新一轮 `REWORK_REQUEST`（round+1，注明原因）；本轮产物归档 |
| E5 | `CONSENSUS_CHECK` | 产物 | 决策 = `REWORK_REQUIRED` 且 round < max_rework_rounds | `REWORK` | 发送 `REWORK_REQUEST`（round+1）与 `DISPOSITION_REQUIRED`；本轮产物归档至 evidence ref |
| E5a | `CONSENSUS_CHECK` | 产物 | **v2.5 新增**：决策 = `APPROVED`，FINAL disposition 精确覆盖全部 issue，且**至少一项 `requires_new_checkpoint=true`** | `REWORK` | 发送 `REWORK_REQUEST`（round+1，附处置决定）；本轮产物归档 |
| E6 | `REWORK` | 产物 | 前一轮 FINAL disposition 已覆盖全部 issue；新一轮 `.dev.yml` 有效（round+1、新 source commit != 上一轮） | `READY_FOR_REVIEW` | 更新当前 checkpoint_ref |
| E7 | `HOLD`（`CONSENSUS_CHECK` 或 `REWORK`） | 命令 | 管理员人工裁定（`--choice APPROVED \| REWORK \| RETRY_REVIEW \| CANCEL \| EXTEND`），支持带 `exempt_issue_ids` 与 note 豁免 | 见下 | 记录独立 `admin_override.json` 与审计事件，生成 `override_id`。按选择转移：APPROVED（豁免未修复 BLOCKING）→E4；REWORK→E5；RETRY_REVIEW→E9；CANCEL→E10；EXTEND→重置超时保持 HOLD |
| E9 | `CONSENSUS_CHECK` | 命令 | 用户裁定 RETRY_REVIEW（重试当前轮评审，round 不变） | `WAITING_REVIEW` | 本轮已收意见作废归档；重新发送 `REVIEW_REQUEST`（全新 message_id 与 deadline） |
| E10 | `*`（任意活动态，即除 DONE/CANCELLED 外） | 命令 | 用户执行 `macao cancel <task>`，或 override 裁定 `--choice CANCEL`（E7） | `CANCELLED`（终态） | 通知全体 Agent；现场归档；审计记录 |
| E8 | `*`（任意） | 诊断 | 60min 无进展 + Layer 3 置信度 <0.7 | `UNKNOWN` | HUMAN_OVERRIDE，等待用户裁定 |

> 说明：
> - 业务状态共 **10 个**：`IDLE` / `CODING` / `READY_FOR_REVIEW` / `WAITING_REVIEW` / `CONSENSUS_CHECK` / `MERGING` / `DONE` / `REWORK` / `CANCELLED` / `UNKNOWN`；其中 `DONE` 与 `CANCELLED` 为终态；`MERGING` 是合并流水线的中间状态——merge/rebase/CI gate/push 是多步异步过程，必须与终态 `DONE` 区分；
> - Git Conflict 发生在 MERGING 阶段内：触发 §6.1 Git Conflict 人工接管，裁定结果经 E4a 或 E4b 落地；
> - `CODING`/`REWORK` → `READY_FOR_REVIEW` 由产物触发（`.dev.yml` 校验通过，见 §3.2 Layer 1a），因入口状态有两个故不单独编号；
> - 超时不是独立的状态来源：超时降级的结果（弃权票/人工裁定）最终仍通过 E3、E7 或 E9 生效；
> - 除本表所列来源外，任何实现不得引入其他状态转移路径。

### 3.4 产物生命周期与场景推演

**生命周期表**（与 §3.2 状态作用域读取配合，保证旧产物不遮蔽后续阶段）：

| 产物 | 生成者 | 受理窗口（FSM 状态 × ref/round） | 消费/归档动作 |
|------|--------|--------------------------------|--------------|
| `.dev.yml` | Executor | 仅 `CODING` / `REWORK`，未被消费、本轮新 commit、round 匹配 | E2 触发时标记 consumed 并提升至 `refs/macao/evidence/<task>/r<round>` |
| `.review.yml` | 各 Reviewer | 仅 `WAITING_REVIEW`，checkpoint_ref + review_round 双匹配 | E3 触发时提升至 `refs/macao/evidence/<task>/r<round>` 归档存档 |
| `vote_result.json` | Orchestrator | 仅 `CONSENSUS_CHECK`，ref + round 双匹配 | 计票完成即时落盘，并归档至 evidence ref |
| `executor.disposition.yml` | Executor | 仅 `CONSENSUS_CHECK` / `REWORK`，精确覆盖本轮 issue | E4/E5a/E6 触发时消费，并提升至 evidence ref 归档 |

> 归档动作 = "校验 Hash → 串行 promotion 提升至 evidence ref → 归档快照至 archive 目录"，保证 source 分支 HEAD 洁净且审计链完整。

**场景推演一：首次开发，双 Reviewer 批准**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1 | 用户受理任务 | `IDLE` → `CODING`（E1） | — |
| 2 | Claude 生成 `.dev.yml`（commit `a1b2c3d`，round 1） | `CODING` → `READY_FOR_REVIEW` | `.dev.yml`（校验通过） |
| 3 | Orchestrator 发送 `REVIEW_REQUEST` | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2） | —（`.dev.yml` 已归档） |
| 4 | cc-glm、kimi 各写 `.review.yml`（round 1），有效票 2 ≥ 2 | `WAITING_REVIEW` → `CONSENSUS_CHECK`（E3） | 2 × `.review.yml` |
| 5 | MACAO 写 `vote_result.json`（APPROVED） | `CONSENSUS_CHECK` → `MERGING`（E4） | `vote_result.json` |
| 6 | merge/rebase 检查/CI gate/签字/push 全部成功 | `MERGING` → `DONE`（E4a） | —（发送 `MERGE_COMPLETED`；归档） |

每步恰好命中一个合法转移；步骤 3 之后 `.dev.yml` 已归档，不会再被 Layer 1a 读到。
若步骤 6 中 CI gate 失败或 push 失败 → `MERGING` → `REWORK`（E4b），转入场景二的返工循环。

**场景推演二：返工第二轮**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1-4 | 同场景一步骤 1-4 | `IDLE` → … → `CONSENSUS_CHECK` | 同场景一 |
| 5 | MACAO 写 `vote_result.json`（REWORK_REQUIRED，round 1） | `CONSENSUS_CHECK` → `REWORK`（E5） | `vote_result.json`（round 1） |
| 6 | 发送 `REWORK_REQUEST`（round=2）；r1 产物已归档 | （伴随动作） | — |
| 7 | Claude 修复后生成新 `.dev.yml`（commit `d4e5f6a`，round 2） | `REWORK` → `READY_FOR_REVIEW`（E6） | 新 `.dev.yml`（双匹配） |
| 8 | 发送 `REVIEW_REQUEST`（携带 r1 反馈作为增量复审上下文） | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2） | — |
| 9 | 双 Reviewer 返回 round 2 意见 | 同场景一步骤 4-5 | 当前轮产物 |

旧 r1 `.review.yml` 在步骤 6 前已归档——即使 Reviewer 尚未覆盖同名文件也不会被误读；
若 round 已达 `max_rework_rounds` 仍为返工决策，则走 E7 人工裁定。

**场景推演三：1:1 平票 → Deadlock → 人工裁定**（含弃权/取消变体）

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1-4 | 同场景一步骤 1-4；cc-glm 投 YES_APPROVE、kimi 投 NO_APPROVE（round 1） | `IDLE` → … → `CONSENSUS_CHECK`（E3） | 2 × `.review.yml` |
| 5 | E3 伴随动作：票数判定为确定性函数——有效票 2 但双方占比均 < 2/3（§2.3 决策表第 4 行）→ 发送 `HUMAN_OVERRIDE_REQUEST`（Type G，`options` 含 CANCEL，10 分钟时限）；**不写 `vote_result.json`**，`CONSENSUS_CHECK` HOLD | （无转移，HOLD 待裁定） | — |
| 6a | 用户 `macao override resolve --choice APPROVED` | 裁定落盘终局 vote_result（decision=APPROVED, resolution=human_override）→ `MERGING`（E4） | 终局 `vote_result.json` |
| 6b | 用户选 REWORK | 终局 vote_result（decision=REWORK_REQUIRED, resolution=human_override）→ `REWORK`（E5 同规则） | 终局 `vote_result.json` |
| 6c | 用户选 RETRY_REVIEW | 终局 vote_result（decision=RETRY_REVIEW）→ `WAITING_REVIEW`（E9；意见作废归档、round 不变、新 deadline） | 终局 `vote_result.json` |
| 6d | 用户选 CANCEL | 终局 vote_result（decision=CANCELLED）→ `CANCELLED`（E10 终态）；通知全体、现场归档 | 终局 `vote_result.json` |
| 7 | （仅 6a）同场景一步骤 6 | `MERGING` → `DONE`（E4a） | — |

- 每一步恰好命中一个合法转移；步骤 5 期间没有任何 `.review.yml`/`vote_result.json` 处于可被读走状态，不存在"Deadlock 被误读为 REWORK"的路径。
- `resolution: human_override` 的终局 vote_result 由 Schema 强制（`docs/schemas/vote_result.schema.json`），E9/E10 的落点由转移表 E9/E10 行唯一确定。
- 弃权变体：1 人弃权 + 1 反对（有效票 1 < 法定人数）经由超时降级流程进入 `CONSENSUS_CHECK`，其余与步骤 5-7 一致；用户超时未裁定时按 §6.1 总则 HOLD + 持续告警，绝不静默推进。

---

## 第四部分：改进的 MVP 范围与交付计划

### 4.1 严格的 MVP 范围（第一期，6-8 周）

#### 必做 (P0)
- [ ] **单机 Claude Code Adapter**（基于 PTY + Hook）
- [ ] **本地 Codex 和 Kimi 的 Wrapper Adapter**（基于 PTY 监听）
- [ ] **LangGraph Workflow 引擎**（FSM 实现）
- [ ] **`.dev.yml` 和 `.review.yml` 规范的完整实现**
- [ ] **投票与共识逻辑**（2/3 多数投票 + 最低法定人数，见 §2.3）
- [ ] **CLI 界面**（Rich + prompt_toolkit 交互）
- [ ] **本地 agmsg 集成**（Queue-based 通信）
- [ ] **单机编排的完整端到端测试**

#### 不做 (P1+)
- [ ] ~~远程 SSH Agent 支持~~（移至 v1.1）
- [ ] ~~Capability Registry & Scheduler~~（移至 v1.2）
- [ ] ~~Multi-Reviewer Consensus 高级算法~~（2/3 投票先用，后续优化）
- [ ] ~~Web Dashboard~~（CLI 先行，后续补 Web）
- [ ] ~~扩展 CLI 支持~~（Gemini CLI / Cursor Agent 等，视需求在 v1.1+ 排期）

### 4.2 分期交付计划

```
Week 1-2: 方案定敲 + PoC 验证
  ├─ 完成 .dev.yml, .review.yml, vote_result.json 详细设计
  ├─ 定义 AEP 消息格式
  ├─ 完成 State Recognition FSM 文档
  ├─ PoC：验证 Claude Code Hook API 与 Codex/Kimi PTY 交互
  └─ 里程碑：单 Executor + 单 Reviewer 工作流 PoC 跑通

Week 3-4: Core Adapter Layer
  ├─ Claude Code Adapter (PTY + Hook)
  ├─ Codex Adapter (PTY Wrapper)
  └─ Kimi Adapter (PTY Wrapper)

Week 5: Workflow Engine
  ├─ LangGraph FSM 实现
  ├─ Vote Logic 实现
  └─ .yml 生成与解析

Week 6: Integration & Testing
  ├─ 本地 agmsg 集成
  ├─ 端到端工作流测试
  └─ CLI 交互界面

Week 7-8: Polish & Documentation
  ├─ 错误处理与恢复
  ├─ 日志与监控
  └─ 用户手册与内部文档
```

---

## 第五部分：Reviewer Context 设计（解决评审质量问题）

### 5.1 为什么需要规范化 Context？

**问题**：每个 Reviewer CLI 运行在独立进程中，对 Executor 的工作缺乏完整理解。

**现象**：
- Reviewer 不知道为什么要评审（任务背景）
- Reviewer 不知道做了什么（代码变更）
- Reviewer 不知道质量指标是否达标（测试覆盖率）

**结果**：评审效果差，需要反复沟通。

### 5.2 标准化的 Reviewer Context 包与 9 大语义块

> 本节是 `review_context` 的**唯一权威完整模型**（两个传输块 + 七个语义块，共 9 大必需块）。AEP `REVIEW_REQUEST` 通过引用与定位器传递，机器契约见 `docs/schemas/review_context.schema.json`。

MACAO 在发送 `REVIEW_REQUEST` 时，提供完整的 Context 引用结构：

```yaml
review_context:
  # 0. 必需块声明
  required_blocks:
    - repository
    - dev_checkpoint
    - task_info
    - code_changes
    - quality_snapshot
    - executor_self_assessment
    - history
    - references
    - review_guidelines

  # 1. 传输与定位块
  repository:
    workspace_path: ".macao/worktrees/codex/task-1/r1"   # 独立隔离 worktree 路径（§16.3）
    remote_name: "origin"
    fetch_policy: "fetch_source_and_evidence_before_diff"
  dev_checkpoint:
    base_commit: "b2c3d4e"     # 变更前 source commit
    head_commit: "a1b2c3d"     # 被评审 source commit，即 checkpoint_ref
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
    source: "review_request"
    path: "docs/reviews/2026-09-01-review-request-task-1.md"
    commit: "e5f6a7b"
    sha256: "<sha256>"

  # 3. 代码变更（传 refs，Reviewer 在本地隔离 worktree 本地生成 diff）
  code_changes:
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

  # 7. 历史上下文（多轮复审时提供前序 vote_result 与 disposition 引用）
  history: []

  # 8. 参考资源
  references: []
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

### 5.3 Reviewer 的标准工作流程

每个 Reviewer 收到 `REVIEW_REQUEST` 后，应该按照这个流程操作：

```bash
# Step 1: 提取 Context
cat <<< "$REVIEW_REQUEST" | jq '.payload.review_context' > /tmp/context.json

# Step 2: 定位工作区并按 refs 取得代码变更
#   仓库定位：优先读消息的 repository 块，缺省时由 MACAO 按 macao.yaml 解析后注入
#   工作区隔离：MVP 下 MACAO 在分发前已为每个 Reviewer 创建独立 worktree
#   （git worktree add .macao/worktrees/<reviewer_id> <head_commit>），
#    并把 worktree 路径作为 workspace_path 注入——Reviewer 只在该目录内操作
cd "$(jq -r '.repository.workspace_path' /tmp/context.json)" || exit 1
REMOTE=$(jq -r '.repository.remote_name // "origin"' /tmp/context.json)
git fetch "$REMOTE"
BASE=$(jq -r '.code_changes.refs.base_commit' /tmp/context.json)
HEAD_COMMIT=$(jq -r '.code_changes.refs.head_commit' /tmp/context.json)
git diff "$BASE".."$HEAD_COMMIT"          # 直接阅读；也可导出到临时文件辅助分析

# Step 3: 运行自动检查（lint, security, test）
pylint src/
bandit -r src/
mypy src/

# Step 4: 根据 review_focus 进行代码审查
# 使用 Reviewer CLI（Codex, Kimi 等）分析代码

# Step 5: 生成 .review.yml
cat > .macao/.reviews/<reviewer_id>.review.yml <<EOF
version: "1.0"
...
EOF

# Step 6: 发送 REVIEW_RESPONSE 给 MACAO
macao send-message REVIEW_RESPONSE \
  --review-file .macao/.reviews/<reviewer_id>.review.yml
```

> 注：`quality_snapshot.performance` 为可选扩展项——无性能基准数据时可省略该子块。摘要类文档的 Context 示例从简，允许省略可选字段，以本节 Schema 为准。
>
> 注：仓库定位遵循 §2.4 约定——优先 `review_context.repository` 块，缺省时按 `project` 从 `macao.yaml` 的 `repository` 段解析（第十三部分）；`code_changes.refs.*` 为唯一权威路径。

---

## 第六部分：人工接管点与错误恢复

### 6.1 明确的人工接管条件

```python
HUMAN_OVERRIDE_TRIGGERS = [
    {
        "condition": "State ambiguity",
        "description": "No valid explicit artifact AND suspected stall (Layer 3 diagnosis confidence < 0.7, see E8). Note: Layer 2 inference is log-only and NEVER triggers override",
        "action": "Ask user: 'What should the state be?'",
        "timeout": "5 minutes (default: HOLD last confirmed state and keep alerting — never silently proceed; state updates only after user confirmation, recorded in audit log)"
    },
    {
        "condition": "Reviewer timeout",
        "description": "Reviewer didn't respond within 10 minutes",
        "action": "Ping reviewer via agmsg, then wait 2 more minutes",
        "escalation": "If still no response, ask user: 'Mark as abstain?'"
    },
    {
        "condition": "Consensus deadlock",
        "description": "No consensus achievable (e.g., 50-50 vote)",
        "action": "Ask user: '--choice APPROVED | REWORK | RETRY_REVIEW | CANCEL'（枚举与落位见 E7/E9/E10）",
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
  Executor → Dev Complete → Review Request → Reviewers Work → Consensus → Merge

Degraded Path (1 Reviewer 超时/不可用 → 标记弃权):
  Executor → Dev Complete → Review Request → 剩余 1 张有效票（< 法定人数 2）
  → Consensus Deadlock → HUMAN_OVERRIDE：用户裁定 APPROVED / REWORK / 重试评审
  (弃权票不计入分母；MVP 2 Reviewer 配置下任何自动判定都要求 ≥2 张有效票，见 §2.3 决策表)

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

> 说明：v1.0 架构中的 Project Manager 模块（项目定义、团队定义、Agent 角色绑定）在 v2.0 中并入 Workflow Controller（任务编排）与 Agent Registry（角色绑定配置）；项目/团队配置沿用 agmsg team 定义。

### 7.2 对标 CI/CD 流程

```
GitLab CI / GitHub Actions    |    MACAO Workflow
─────────────────────────────────────────────────────
.gitlab-ci.yml                |    Project Config YAML
Pipeline: Trigger             |    DEVELOPMENT_STARTED
Build Stage: Compile          |    CODING Stage
Test Stage: Run Tests         |    Quality Metrics
Artifact: Upload              |    .dev.yml Created
Review Apps: Deploy for QA    |    REVIEW_REQUEST
Manual Approval               |    Reviewer Voting
Merge: Push to main           |    Consensus + Merge
```

---

## 第八部分：成功指标 (KPIs)

### 8.1 技术 KPI

| KPI | Target | 测量方式 |
|-----|--------|---------|
| **State Recognition Accuracy** | >95% | 标注样本集评测（分母 = 观察窗口内全部状态转换次数） |
| **Explicit Signal Usage Rate** | >99% | 产物驱动转移占全部业务状态转移的比例（分母不含命令型转移 E1/E2/E4a/E7/E9/E10） |
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
| **Reviewer 被 prompt injection 操纵投票** | 低 | 高 | 评审输出 Schema 强校验（status↔vote 映射）；review_focus 白名单注入；异常投票模式告警（见第十五部分） |
| **第三方 CLI 服务条款限制自动化编排** | 中 | 中 | PoC 前完成 ToS/法务核实；必要时降级为半自动模式 |
| **跨机器网络延迟** | 低 | 低 | MVP 仅支持本地；后续优化 |

---

## 第十部分：总结与下一步行动

### 核心创新
1. **规范化流程** - 从黑盒推断转为显式约定
2. **标准输出物** - `.dev.yml`, `.review.yml` 作为系统间通信的"手写签名"
3. **可靠的状态转换** - 三层识别，优先显式信号
4. **清晰的人工接管点** - 系统何时需要人工确认

### 立即行动项 (Next 2 weeks)

- [ ] **技术 PoC**：实现 Claude Code Adapter，验证 Hook API 可用性
- [ ] **方案评审**：与 Anthropic、OpenAI（Codex）、Moonshot（Kimi）接洽，确认 API 承诺
- [ ] **用户研究**：采访 5-10 个多人开发团队，验证场景真实性和痛点优先级
- [ ] **Prototype UI**：用 `rich` 库实现简单的 CLI 交互 demo
- [ ] **文档完善**：补全本 PRD 中的 edge cases 和错误处理细节

### 成功标志 (MVP 完成)——验收标准（未达成前不得勾选）

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
  macao status / task create / override resolve / logs / usage
        │
Orchestrator（单进程事件循环，LangGraph FSM）
  ├─ State Recognition Engine ......... 第三部分（作用域读取 + HOLD）
  ├─ Consensus Engine ................ §2.3（法定人数/投票/决策表）
  ├─ Merge Controller ................ APPROVED 后执行合并策略（第十四部分）
  ├─ Config Loader ................... macao.yaml 单一事实源（第十三部分）
  ├─ Usage Meter ..................... 成本计量（第十五部分）
  └─ State Store（SQLite：任务/轮次/FSM 状态/审计事件）
        │ agmsg 本地队列（AEP/1.0 消息）
Adapter Runtime（契约见第十二部分）
  ├─ ClaudeCodeAdapter（PTY + Hook）
  ├─ CodexAdapter（PTY Wrapper）
  └─ KimiAdapter（PTY Wrapper）
        │ PTY 子进程
claude-code / codex / kimi CLI 进程
工作区 git 仓库（.macao/ 产物 + archive 归档目录）
```

### 11.2 进程模型与数据流

- Orchestrator 为单进程事件循环；各 CLI 由 Adapter 以 PTY 子进程方式拉起，随任务结束回收。
- 状态事实源 = State Store（SQLite）+ git 提交的产物文件双写；任一崩溃后可由两者重建内存态（对应 Failure Path 的"从最近检查点恢复"）。
- 主数据流：任务指令 → `DEVELOPMENT_STARTED` → `.dev.yml` → `REVIEW_REQUEST`（携带 context）→ `.review.yml × N` → `vote_result.json` → 合并 → `MERGE_COMPLETED`；每次状态转移写入审计事件表。

### 11.3 技术选型（继承 v1.0 并按 MVP 裁剪）

| 模块 | 技术 | 说明 |
|------|------|------|
| Workflow | LangGraph | FSM 编排 |
| 消息 | agmsg + AEP/1.0 | 本地队列；远程传输 v1.1 再议 |
| 进程管理 | PTY（pty/subprocess） | tmux 为可选调试手段，非依赖 |
| 状态存储 | SQLite 单文件 | MVP 不引入 PostgreSQL |
| UI | Rich + prompt_toolkit | 仅 CLI |
| 远程 Agent | 不支持 | 移除 v1.0 的 SSH Gateway 设想（v1.1） |

### 11.4 State Store DDL（核心表）

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
  kind TEXT NOT NULL,            -- dev_manifest|review_manifest|vote_result
  path TEXT NOT NULL,            -- 物理路径（展示/恢复用，非唯一键）
  sha256 TEXT, checkpoint_ref TEXT, review_round INTEGER, reviewer_id TEXT,
  consumed INTEGER NOT NULL DEFAULT 0, archived_path TEXT,
  created_at TEXT,
  UNIQUE(task_id, kind, checkpoint_ref, review_round, reviewer_id)
);
CREATE TABLE audit_events(
  sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL, task_id TEXT, type TEXT NOT NULL, detail TEXT   -- JSON
);
CREATE TABLE overrides(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sequence_id INTEGER REFERENCES audit_events(sequence_id),
  trigger TEXT, choice TEXT NOT NULL, note TEXT
);
CREATE TABLE dead_letter_queue(
  message_id TEXT PRIMARY KEY, payload TEXT,
  retry_count INTEGER, reason TEXT, ts TEXT
);
```

### 11.5 双写与崩溃恢复（Reconcile）

**写入顺序约定**：① 物理产物落盘并 fsync → ② SQLite 事务提交 → ③ git 提交（异步，失败可补偿重放）。

**artifacts 追加语义**：归档采用"新增行"而非同路径 upsert——归档时在 `artifacts` 新插一行并填写 `archived_path`，原行标记 `consumed=true` 后转为只读；多轮/多任务下同路径产物各自一行（`artifact_id` 自增，唯一约束见 §11.4 DDL），git 历史与 SQLite 双账本按"latest row per (task, kind, ref, round)"查询，任何情况下不用覆盖式写入抹掉历史审计行。

**第一真理源优先级**：git 已提交产物 > 磁盘上通过 Schema 校验的产物文件 > SQLite 记录。

启动扫描重建规则（所有修复动作写审计）：

| 半完成场景 | 处理 |
|-----------|------|
| A：SQLite 已写、产物归档未完成 | 以磁盘文件为准，幂等重放归档动作 |
| B：git 已提交、SQLite 未写 | 从 git 历史与磁盘产物重放补齐 SQLite |
| C：归档复制中崩溃 | copy+rename 天然幂等，重扫后补齐 archive 目录 |

### 11.6 agmsg 本地形态与死信队列

- MVP 选型：SQLite 消息表（单机进程间生产/消费；跨机 v1.1 经 Gateway 复用同一表结构同步）；
- 消息 TTL = 所属阶段 deadline；未 ACK 按退避重试最多 3 次；超限移入 `dead_letter_queue` 并告警；
- 消费端以 message_id 幂等去重（与 Adapter Contract 的 ack 语义一致）。

---

## 第十二部分：Adapter Contract v1 与能力矩阵

"Adapter 可插拔、新增 CLI 不改核心引擎"的承诺由本契约兑现；v1.0 SRS 的接口设想在此正式化。

### 12.1 契约接口

```text
capabilities() -> CapabilityManifest      # 能力声明（12.2），启动时上报
preflight()    -> PreflightReport         # 安装/登录态/版本探测，输出可执行修复建议
start(agent) / stop(agent, reason)        # 进程生命周期
inject_task(agent, aep_development_started)
ack(message_id)                           # 消息幂等回执（去重键 = message_id）
subscribe_events(callback) / get_logs(tail)
cancel(reason)                            # 取消当前任务并回收子进程
```

### 12.2 Capability Manifest 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| can_execute | bool | 可担任 Executor |
| can_review | bool | 可担任 Reviewer |
| supports_hook | bool | 支持官方 Hook 事件 |
| supports_noninteractive | bool | 支持非交互模式 |
| supports_worktree | bool | 支持 git worktree 隔离评审 |
| **execution_mode** | enum：`read_only` / `sandboxed` / `full` | **执行权限边界**（P0 安全约束，见下） |
| supported_os / cli_version_range | - | 平台与版本兼容范围 |

**execution_mode 语义与强制规则**：

- `read_only`：只读挂载评审工作区，禁止任何写操作与命令执行（静态分析类工具适用）
- `sandboxed`：在独立 git worktree + 容器/受限环境中执行；网络访问与包安装默认禁止，白名单放行
- `full`：完全执行权限，仅允许 Executor 在其任务工作区内使用（以任务 worktree/路径白名单 + 命令审计为界；具体沙箱机制在 PoC 验证后固化）
- **强制约束**：担任 Reviewer 的 CLI 必须 `execution_mode ∈ {read_only, sandboxed}` 且 MVP 阶段强制 `sandboxed` + 独立 worktree——通用 coding Agent 具备任意 shell/网络能力，若不加边界，被 prompt injection 后的危害是"破坏工作区/外传代码"而不只是"投错票"。`supports_worktree=true` 是 Reviewer 的**准入硬条件**：preflight 与 Conformance 均强制校验，不支持者拒绝接入（§16.3 同口径）。

### 12.3 MVP 准入矩阵

| CLI | can_execute | can_review | hook | noninteractive | worktree | execution_mode | Adapter 类型 |
|-----|-------------|------------|------|----------------|----------|----------------|--------------|
| claude-code | ✓ | — | ✓ | 部分 | n/a | full（限任务工作区） | claude-hook |
| codex | — | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |
| kimi | — | ✓ | — | ✓ | ✓ | sandboxed | pty-wrapper |

### 12.4 兼容性验收（Conformance）

每个 Adapter 通过统一测试套件后方可标记"支持"：

- preflight 全绿；版本探测与 `cli_version_range` 一致；
- 五类一致性场景：PTY 断开重连、重复 message_id 回执去重、CLI 升级后探测、厂商限流退避、凭据失效报错；
- producer→consumer 端到端：Adapter 生成的产物 fixture 直接喂给消费方命令（如 §5.3 的 jq 路径）验证可解析；
- 校验输入为**版本化 JSON Schema 与正/反 fixture**，统一维护于 `docs/schemas/`（三类产物 + AEP 信封 + review_context + macao.yaml），Schema 演进随 PRD 版本号走。

### 12.5 Reviewer 输出自愈（两级）

LLM CLI 自由文本生成 YAML 的常见失败：包裹 Markdown 代码栅栏、带客套话前后缀、字段缺失、status↔vote 不一致、缩进错误。Adapter 在落盘前执行两级自愈：

1. **提取清洗（Extractor）**：正则提取首个合法 YAML 代码块，剥离栅栏与无关文本后再解析；
2. **局部纠错重试（Local Re-prompt）**：Schema 校验失败时，在同一会话内追加一次纠错提示（附具体校验错误，如 "vote 字段与 status 映射冲突，请仅输出合法 YAML"）；自愈成功才落盘。

约束：同轮最多自愈 1 次，仍在 per_reviewer 超时窗口内；仍失败才按无效产物处理（§2.2 一致性校验规则），避免一次格式错误浪费整轮评审窗口。

### 12.6 PTY 运行规范

- **非交互参数**：各 CLI 以非交互模式启动（权限确认关闭/自动允许清单），具体参数登记于 Capability Manifest 并在 preflight 时验证；
- **ANSI 清洗**：所有 PTY 输出经 `strip_ansi()` 过滤后才写入 State Store 日志或送 Layer 3 LLM 诊断（省 token 且避免转义序列干扰语义）；
- **进程组回收**：以进程组为单位管理子进程（`killpg(SIGTERM)` → 宽限期 → `SIGKILL`），确保 cancel/崩溃时编译、测试等孙进程一并回收；
- **挂起检测**：权限弹窗等导致的输出静默由 pty_idle 监控捕获，进入 §3.1 Layer 2 预警与 Layer 3 诊断流程。

---

## 第十三部分：配置规范（macao.yaml 单一事实源）

位置：仓库根目录 `macao.yaml`。正文出现的全部数值（超时/阈值/法定人数/轮次上限）均为该文件的默认值；修改配置不改行为语义，只改参数。

```yaml
project:
  name: "macao-demo"
  repository:                    # workspace 解析的唯一来源（§2.4 / §5.3）
    workspace_path: "~/work/macao-demo"
    remote_name: "origin"
    default_branch: "main"
team:
  executor:
    id: "cc-ds4"
    cli: "claude-code"
    adapter: "claude-hook"
  reviewers:
    - { id: "cc-glm", cli: "codex", adapter: "pty-wrapper" }
    - { id: "kimi", cli: "kimi", adapter: "pty-wrapper" }
policy:
  consensus_rule: "2/3_majority"
  min_effective_votes: 2         # ⌈2N/3⌉，N = configured reviewers
  max_rework_rounds: 3           # 超过则触发人工裁定（E7）
  review_strategy: "delta_plus_focus"
merge:
  strategy: "ff_only"            # ff_only | no_ff
  ci_gate_command: null          # 例: "make ci"；null 表示无门禁（MERGING 内执行）
  require_human_signoff: true    # 推送前人工签字开关；默认保守值 true（刻意的安全默认）
  rebase_before_merge: false     # MVP 禁用；受控门禁（range-diff 三重条件）规划于 v1.1，见 §14.5
timeouts:
  development: "2h"              # 总上限；期间每 60min 无进展即触发 E8 检查（见 §6.1）
  checkpoint_validation: "1m"    # 超时处置：保持原状态并告警，走 Layer 2 预警路径
  review_request: "30m"
  per_reviewer: "10m"
  consensus_check: "1m"
thresholds:
  layer2_inference_log_only: true
  llm_diagnosis_override_below: 0.7
cost:
  usage_metering: true           # 按阶段/agent 记录用量（第十五部分）
  monthly_budget_usd: null       # MVP 仅告警不硬限
security:
  allowed_clis: ["claude-code", "codex", "kimi"]
  send_terminal_logs_to_reviewers: false
  secrets_masking: true
audit:
  retention_days: 90
```

加载规则：Config Loader 启动时读取并做 JSON Schema 校验（Schema 文件见 `docs/schemas/`），失败则拒绝启动并列出错误项；运行中变更需显式 `macao config reload`，且不影响进行中的 round。`min_effective_votes` 由 Loader 按 `⌈2 × N / 3⌉` 推导填充，显式覆盖时不得低于推导值。三类产物与 AEP 信封同样以 `docs/schemas/` 的版本化 Schema 为唯一校验依据。

---

## 第十四部分：用户旅程与运行手册

### 14.1 从零到第一次合并（主旅程）

1. 安装预检：`macao preflight` —— 校验各 CLI 已安装、登录态有效、版本在支持矩阵内，输出 PreflightReport 与修复建议；
2. 初始化：`macao init --new`（新项目）或 `macao init --adopt-existing`（既有项目状态接管）生成 `macao.yaml` 模板 → `macao doctor` 校验配置与环境；
3. 创建任务：`macao task create --title … --acceptance … --branch feature/x` —— **Task 最小 Schema** = `task_id`（State Store 生成）+ 标题 + 验收标准数组（可测试判据，映射 `DEVELOPMENT_STARTED.success_criteria`）+ `source_branch` + `target_branch` + 期望产物路径；验收标准或目标分支缺失则拒绝创建；字段随任务写入 State Store 的 tasks 表并进入 AEP 消息；
4. 观察：`macao status`（FSM 状态 / `role_view` 角色投影 / 当前 ref 与 round / 各 agent 状态）、`macao logs <agent>`；
5. 处置与接管：
   - 机器批准但有建议：Executor 提交 `review_disposition` 完成逐项闭环；
   - 出现 HUMAN_OVERRIDE_REQUEST 时，`macao override list` 查看证据（诊断报告/票面/冲突详情）→ `macao override resolve --choice APPROVED|REWORK|RETRY_REVIEW|CANCEL|EXTEND [--note] [--exempt-issue-ids]`;
6. 合并与发布：见 14.5 Merge Policy；
7. 归档：流程结束后本轮产物提升至 canonical evidence ref（`refs/macao/evidence/<task>/r<round>`）并归档至 `.macao/archive/<ref>/r<round>/`，不污染 source 分支。

### 14.2 日常运维操作与角色投影（role_view）

| 操作 | 命令 | 语义 |
|------|------|------|
| 既有项目接管 | `macao init --adopt-existing` / `macao adopt` | 收集证据并执行受控接管事务（歧义时问管理员） |
| 环境与状态诊断 | `macao doctor` | 只读收集证据、输出候选状态与冲突分析 |
| 状态受控恢复 | `macao reconcile` | 按确定性恢复计划执行受控状态迁移 |
| 证据查阅与导出 | `macao reviews show <task>` / `export` | 读取或导出 evidence ref 中的评审及处置产物 |
| 暂停观察 | `macao pause <task>` | 进入 HOLD，停止状态推进 |
| 取消 | `macao cancel <task>` | 终止任务，通知全体 agent，归档现场 |
| 重试 | `macao retry <task>` | 从最后检查点重放 |
| 合并签字 | `macao merge approve [--note]` | `require_human_signoff: true` 下推送前的强制人工放行（§14.5 第 4 步） |
| 用量查询 | `macao usage` | 按阶段/CLI 汇总 token 与调用次数 |

#### 统一角色视图（`role_view`）

State Store 仅持久化唯一 `tasks.state`，界面通过 `role_view` 投影呈现：

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

---

## 第十六部分：部署形态与协作拓扑

### 16.1 角色定义与垄断权（单一写者原则）

| 角色 | 实体 | 核心职责 | 垄断权（单一写者原则） |
|------|------|---------|----------------------|
| **编排者** | 用户 + MACAO Orchestrator | 任务受理、FSM 推进（E1~E10）、加权共识仲裁、合并执行、人工接管处理 | 唯一写不可变 `vote_result.json`、唯一执行 merge、唯一管理 evidence promotion |
| **执行者** | Executor CLI（如 Claude Code / OpenCode） | 理解需求 → 改码 → 自测 → commit → 生成 `.dev.yml` + 申请全文；写 `review_disposition` | 唯一写 `.dev.yml`、唯一产生业务 commit、唯一写 `review_disposition` |
| **评审专家** | Reviewer CLI ×N（Codex / Kimi / Gemini 等） | 按 review_context 取 diff → 审查 → 产出结构化 issue 清单 → 投票 | 各自唯一写自己的 `.review.yml` 与评审全文 |

> **第一性原则**：三个角色之间的协作依赖：**① source git 仓库（代码检查点事实源）② evidence git ref（评审与处置证据事实源）③ AEP 消息（控制流信封）④ SQLite（运行时 FSM 与机器审计）**。

---

## 附录：版本演进记录

- v1.0: 初始高阶架构设计（产品代号 "A"）
- v2.0: 规范化产物信封、FSM 状态机收敛、双 Reviewer 共识与 PTY 封装
- v2.3: review_context 权威结构收敛、Deadlock HOLD 方案 B、E9/E10 状态机收敛
- v2.3.1: 评审对象与合并对象硬绑定、Worktree 强制化、跨平台断言修复、is_ancestor 拓扑校验（达成 L3 SCENARIO-VERIFIED / PG-2 认证）
- **v2.5（现行权威基准）**：
  - **P-1 零语义创作**：Orchestrator 收敛为确定性规则与路由系统，彻底消除代写摘要与语义合并；
  - **内容与控制分层**：AEP/1.1 引入 16 KiB 字节预算，增加 `DISPOSITION_REQUIRED` 调度通道；
  - **独立 Review Disposition**：Executor 单一写入按轮隔离的 `review_disposition.yml`，消除 `issues_summary` 双写冲突；
  - **显式改码守卫**：引入 `requires_new_checkpoint: boolean` 与 E5a 状态流转；
  - **加权 2/3 共识**：引入 `weighted_2/3_v1` 纯整数五重门禁与配置期独裁帽，防单模型支配；
  - **独立 Evidence Git Ref**：建立 `refs/macao/evidence/...` 拓扑与两阶段 Push 校验，实现 source HEAD 隔离；
  - **动态状态接管**：规范 `init / doctor / reconcile / adopt` 边界，确立 `role_view` 投影与 AI diagnostic-only 纪律。

### 16.2 端到端开发流程总览（标注交接通道）

| # | 阶段 | 发起 → 接受 | 交接物与通道 | 完成标志 |
|---|------|------------|-------------|---------|
| 0 | 部署预检 | 用户 → Orchestrator | `macao preflight`（CLI 安装/登录态/版本矩阵） | PreflightReport 全绿 |
| 1 | 任务受理 | 用户 → Orchestrator | `macao task create`（标题 + 可测验收标准 + 目标分支） | E1：`DEVELOPMENT_STARTED` 下发 |
| 2 | 开发 | Orchestrator → 执行者 | AEP 任务指令；执行者在工作区 commit | 有效 `.dev.yml` 出现（新 commit + round 匹配） |
| 3 | 检查点与分发 | 执行者 → Orchestrator → 评审专家 | `.dev.yml`（产物型转移）→ `REVIEW_REQUEST` 携带 context（refs + repository 定位） | E2：`.dev.yml` 归档，评审 deadline 生效 |
| 4 | 并行评审 | Orchestrator ⇄ 各评审专家 | 各专家独立取 diff（`fetch_before_diff`）→ 各写 `.review.yml` | 有效票 ≥ 法定人数（E3） |
| 5 | 共识判定 | Orchestrator（内部） | 决策表裁决 → `vote_result.json` | APPROVED / REWORK / Deadlock 转人工 |
| 6 | 合并发布 | Orchestrator → git remote | Merge Policy：merge → CI gate → push → `MERGE_COMPLETED` | merge commit + 审计记录 |
| 7 | 返工/归档 | Orchestrator → 执行者 | `REWORK_REQUEST`（round+1，附增量上下文）或产物归档 | 闭环或 E7 人工裁定 |

阶段 2~5 为核心循环；round + checkpoint_ref 双匹配保证任何一轮产物不污染另一轮。

### 16.3 场景一：单机同置（v2.x MVP，规格已全覆盖）

```text
┌────────────────── 物理机 M ──────────────────────────┐
│  用户 ⇄ macao CLI                                    │
│      │                                               │
│  Orchestrator（FSM/共识/合并，SQLite State Store）    │
│      │  本地 agmsg 队列（文件型，AEP 消息）            │
│  ├─ ClaudeCodeAdapter ── PTY ── claude-code（执行者） │
│  ├─ CodexAdapter ─────── PTY ── codex（评审专家 A）   │
│  └─ KimiAdapter ───────── PTY ── kimi（评审专家 B）   │
│      │                                               │
│  同一仓库：主工作区（Executor）+ 每 Reviewer 独立      │
│  worktree；.macao/ 产物 + archive + git               │
└──────────────────────────────────────────────────────┘
```

| 协作面 | 实现方式 | 说明 |
|--------|---------|------|
| 控制流 | 本地 agmsg 文件队列 | 零网络延迟；消息可靠性由队列落盘保证 |
| 代码共享 | 同一仓库、独立 worktree | 执行者 commit 后，各评审专家在自己的 worktree 内 `git diff base..head`；无跨机同步动作 |
| 产物落盘 | 同一文件系统 | 三类产物直接读写 `.macao/`；归档即本地 mv + git 提交 |
| 隔离 | **强制**独立 git worktree（`supports_worktree=true` 为准入硬条件，preflight/Conformance 强制校验） | 评审专家绝不进入 Executor 主工作区；跑构建/测试只在自带 worktree 内（§12.2 安全红线） |

故障面仅限本机：进程崩溃（State Store 恢复）、PTY 卡死（Layer 3 诊断）、磁盘资源耗尽。用户体感为单终端交互：`status` 看进度、`override resolve` 处理接管、`merge approve` 完成签字放行，其余自动。

### 16.4 场景二：跨机分布（v1.1 规划）

示例布局（规则适配任意切分）：**M1 = Orchestrator + 评审专家 A（cc-glm）；M2 = 执行者（cc-ds4）+ 评审专家 B（kimi）**。

```text
┌──────────── M1（决策域）────────────┐      ┌──────────── M2（执行域）────────────┐
│ 用户 ⇄ macao CLI                    │      │                                     │
│ Orchestrator（FSM/共识/Merge）       │      │ claude-code（执行者）                │
│ 评审专家 A：codex                    │      │ 评审专家 B：kimi                     │
│ 本地 .macao/（唯一写者）+ clone      │      │ 自己的 clone（同 origin）            │
└──────────────┬──────────────────────┘      └──────────────┬──────────────────────┘
               │        ① Agent Gateway（SSH 隧道/mTLS）     │
               └──────────── agmsg 网桥（AEP 双向）───────────┘
               ② 共享 git origin（代码与检查点的唯一事实源）
```

**三条通道**：

| 通道 | 承载 | 场景一实现 | 场景二实现 |
|------|------|-----------|-----------|
| C1 代码 | commit / push / fetch / diff | 同仓直读 | 共享 origin：M2 push → M1/M2 各自 fetch；checkpoint_ref 必须双方可见 |
| C2 控制+产物 | AEP 消息（`content_base64` 内嵌产物内容） | 本地 agmsg | agmsg 网桥 + Agent Gateway（SSH 隧道或 mTLS） |
| C3 共识产物落盘 | `.macao/` 文件 | 同盘直写 | 仅 M1 可写（单一写者）；远端产物经 C2 上送，由 M1 落盘并 git 提交留证 |

**分工铁律**：M2 是执行域——产码、产检查点、产本机评审意见；M1 是决策域——共识、合并、审计。M2 不写 `vote_result.json`，不触碰 M1 的 `.macao/` 写权限。

**相对场景一的差异点（δ）**：

| δ# | 差异 | 机制 |
|----|------|------|
| δ1 | E2 分发新增前置校验 **R1**：head_commit 必须已推送至 origin（以 push 回执为准），否则不发 `REVIEW_REQUEST` | 杜绝"评审一个对端看不到的 commit" |
| δ2 | `.dev.yml` 上行：包含在被 push 的 commit 中，同时发 `STATE_CHANGED`（Type F，附 content_base64）通知 M1；M1 落盘到本地 clone 后进入原有识别逻辑 | 消息是触发，git 是存证——与状态作用域读取完全兼容 |
| δ3 | 评审意见回传：M2 的 Reviewer 写好 `.review.yml` 后经 `REVIEW_RESPONSE`（Type C，content_base64）上送，M1 落盘提交 | Type B/C 内嵌字段正是为此预留 |
| δ4 | 远端评审取码：按 repository 块在自己 clone 上 `fetch_before_diff`；取不到 ref → 幂等重试（message_id 去重），超限转人工 | |
| δ5 | deadline 统一以 Orchestrator（M1）时钟为准，容忍 ±5min 时钟偏差 | |
| δ6 | 新增故障面：网关断连（队列积压+重放，幂等去重）、M2 整机离线（development/per_reviewer 超时照常降级）、push 凭据失败（preflight 前置拦截 + 运行期转人工） | |

**配置增量**（macao.yaml 扩展草案，v1.1 实现）：

```yaml
team:
  executor: { id: cc-ds4, cli: "claude-code", host: m2 }
  reviewers:
    - { id: cc-glm, cli: codex, host: m1 }
    - { id: kimi,   cli: kimi,  host: m2 }
hosts:
  m1: { role: [orchestrator, reviewer] }
  m2: { gateway: "ssh://user@m2.example:2222", role: [executor, reviewer] }
```

### 16.5 两场景对比与落地差距

| 维度 | 场景一（同机） | 场景二（跨机） |
|------|--------------|---------------|
| 控制通道 | 本地 agmsg 文件队列 | agmsg 网桥 + Gateway（SSH/mTLS） |
| 代码共享 | 同一 clone 直读 | 共享 origin：push → fetch |
| 产物落盘 | 同盘直写 | 单一写者（M1）+ AEP 内容上送 |
| 故障面 | 本机进程/PTY/磁盘 | + 网络分区、时钟漂移、push 失败、整机离线 |
| 适用版本 | v2.x MVP（已覆盖） | v1.1 |

场景二需新增的实现项共三项：**① Agent Gateway 守护进程；② R1 push 前置校验；③ hosts 配置段**。其余（FSM、共识、产物契约、round 匹配、Adapter Contract）全部复用，无需修改。

---

## 第十七部分：Phase 3 真实多 Agent 调度与输出自愈机制 (Phase 3 Spec)

### 17.1 LiveAgentDispatcher 真实工作区派发
- **Worktree 动态隔离**：在状态推进至 `WAITING_REVIEW` 时，根据配置的审查者列表在 `.macao/worktrees/<task_id>/<reviewer_id>` 动态创建物理独立的 Git Worktree；
- **PTY 伪终端会话生命周期**：为每个 CLI 进程分配独立子终端，注入 non-interactive 与 sandboxed 参数，实时捕获终端输出；
- **原子清理保障**：审查结束或任务终结后，执行 `git worktree remove --force` 原子销毁工作区，杜绝磁盘泄漏。

### 17.2 ReviewExtractor 两级输出自愈器
- **Level 1 正则与 ANSI 剥离**：自动去除 ANSI 终端颜色转义码，匹配 Markdown 代码栅栏（```yaml ... ```）提取纯净 YAML；
- **Level 2 Schema 强校验与语义对齐**：使用 Draft-07 `review_manifest.schema.json` 强校验；若仅有 `opinion.status` 则自动对齐 `vote`，自动补齐 `checkpoint_ref` 与 `review_round`。

---

## 第十八部分：后台超时扫描守护进程 (OrchestratorDaemon)

- **轮询驱动**：基于系统时钟定时扫描活跃任务的截止时间（Deadline Epoch）；
- **超时自动降级**：审查员超时自动记入 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件，并将未提交票置为 `ABSTAIN`；
- **确定性推进**：自动触发共识仲裁，推动状态机进入 `CONSENSUS_CHECK` (HOLD) 并生成 `HUMAN_OVERRIDE_REQUEST`。

---

## 第十九部分：细粒度模型透传与多元角色矩阵

- **全角色自由组合**：`opencode`, `agy` (Google Antigravity), `agent` (Cursor), `claude-code`, `codex`, `kimi` 均支持作为 `executor` 或 `reviewers`；
- **模型参数透传**：在 `macao.yaml` 中通过 `model: "<model_id>"` 显式声明具体模型（如 `GLM 5.3 max`, `Qwen3.8 max`, `claude-3-7-sonnet`, `gemini-2.0-pro` 等），底层 PTY 进程自动透传 `-m / --model` 参数。

---

## 第二十部分：智能向导与运行时环境隔离 (Setup Wizard & Isolation)

- **`macao setup` 智能向导**：自动探活系统 PATH 中的 AI CLI 资产、探测 Git 分支与测试命令，生成强合规配置；
- **`.gitignore` 运行时自动隔离**：自动在被管项目 `.gitignore` 中追加 `.macao/worktrees/` 与 `*.db`，彻底杜绝仓库污染。

---

**版本历史**
- v1.0: 高阶架构设计（即 `SRSv1.md`，产品暂定名 "A"）
- v1.5: 专家评审意见反馈（见 `IMPROVEMENT_SUMMARY.md` 第四节）
- v2.0: 规范化流程 + 标准输出物 + 改进状态识别
- v2.0.1: 按 `docs/reviews/2026-08-25-review-result-ec60f70-*` 三份评审反馈闭环 P0/P1/P2 问题
- v2.1: 按 `docs/reviews/2026-08-26-review-result-47f54f2-codex.md` 复审闭环 P0-1/P0-2 与 P1
- v2.1.1: 新增第十六部分《部署形态与协作拓扑》
- v2.2: 新增 MERGING 中间状态与 CI gate、Reviewer sandboxed 执行权限、两级自愈规范
- v2.3: review_context 权威结构收敛、Deadlock HOLD 方案 B、E9/E10 状态机收敛
- v2.3.1: 评审对象与合并对象硬绑定、Worktree 强制化、跨平台断言修复、is_ancestor 拓扑校验（达成 L3 SCENARIO-VERIFIED / PG-2 认证）
- v2.4 (Phase 3): 新增第十七～二十部分——Phase 3 真实 Worktree 调度与 ReviewExtractor 两级自愈、OrchestratorDaemon 后台守护、细粒度模型控制与 Cursor Agent 接入、macao setup 智能向导与 Python 包数据打包（达成 L4 RELEASE-READY / PG-3 规格）
