# MACAO (Multi-Agent CLI Agent Orchestrator) - 产品方案 v2.0

> **核心理念**：通过**流程规范化** + **输出物标准化**，使 Agent 状态识别从"黑盒推断"转变为"约定式识别"。

> **文档地位：本文档是 MACAO v2.0 的权威基准文档**，其他文档与本文档不一致时，以本文档为准。
>
> **文档体系**（docs/）：
>
> | 文档 | 角色 | 状态 |
> |------|------|------|
> | `SRSv1.md` | v1.0 原始设计（产品暂定名 "A"） | 历史基线，已被 v2.0 取代 |
> | `MACAO_PRD_v2.md` | v2.0 产品方案（本文档） | **权威基准** |
> | `EXECUTIVE_SUMMARY.md` | v2.0 执行摘要与快速参考 | 本文档的摘要 |
> | `IMPROVEMENT_SUMMARY.md` | v1.0 → v2.0 改进对比 | 演进过程说明 |

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
    │  ├─ Reviewer 收信后进入 REVIEWING   │
    │  ├─ 运行本地 CLI 检查（代码、安全等）│
    │  └─ 生成 .review.yml                 │
    └────────┬─────────────────────────────┘
             │
      (达到法定人数或超时降级流程完成)
             │
             v
    ┌──────────────────────────────────────┐
    │  PHASE 4: CONSENSUS CHECK            │
    │  ├─ MACAO 收集所有 .review.yml       │
    │  ├─ 执行投票规则 (2/3 通过)          │
    │  └─ 决定 APPROVED or REJECTED        │
    └────────┬─────────────────────────────┘
             │
          ┌──┴──────────────────┐
          │                     │
          v                     v
    ┌──────────────┐      ┌──────────────────┐
    │  APPROVED    │      │  CHANGES_REQUEST │
    │  ├─ Merge    │      │  ├─ Parse issues │
    │  └─ Done     │      │  └─ Back to Dev  │
    └──────────────┘      └────────┬─────────┘
                                   │
                  (Executor 修复)   │
                                   │
                          (Loop back to PHASE 1)

```

### 1.2 各阶段的严格定义

阶段视图与第三部分的统一转移表（§3.3）一一对应；"进入方式"即该阶段的触发源：

| 阶段 | 主状态 | 进入方式（触发源） | 离开条件 | 关键产物 | 超时 |
|------|--------|------------------|---------|---------|------|
| **REQUIREMENT** | `IDLE` | 用户经 `macao task create` 提交任务（含验收标准，见第十四部分） | Orchestrator 发送 `DEVELOPMENT_STARTED` AEP（E1） | 任务描述 + 验收标准 | - |
| **DEVELOPMENT** | `CODING` | 收到 `DEVELOPMENT_STARTED`，Executor 启动 | 当前轮 `.dev.yml` 通过最小有效性校验 | `.dev.yml` + Git Commit | 2h |
| **CHECKPOINT** | `READY_FOR_REVIEW` | `.dev.yml` 校验通过的瞬间（产物触发） | 消费完成并发送 `REVIEW_REQUEST` AEP（E2） | `.dev.yml`（随即归档） | 1m |
| **REVIEW_REQUEST / REVIEWING** | `WAITING_REVIEW`（Reviewer 侧 `REVIEWING`） | MACAO 发送 `REVIEW_REQUEST` AEP | 有效票达到法定人数或超时降级流程完成（E3） | 各 Reviewer `.review.yml`（当前 round） | 30m（10m/reviewer 触发 ping） |
| **CONSENSUS** | `CONSENSUS_CHECK` | 法定人数达成或超时处置完成 | `vote_result.json` 写出并按决策转移（E4/E5） | `vote_result.json` | 1m |
| **MERGE / REWORK** | `DONE` / `REWORK` | 决策 = APPROVED / REWORK_REQUIRED | 合并完成（`MERGE_COMPLETED`）或返工闭环（E6） | merge commit 或新一轮 `.dev.yml` | - |

---

## 第二部分：标准输出物规范

### 2.1 `.dev.yml` - Development Checkpoint Manifest

**用途**：Executor（Claude Code）明确向 MACAO 宣布"我的工作已完成并准备评审"

**位置**：项目根目录 `.macao/.dev.yml`

**格式**：

```yaml
version: "1.0"
timestamp: "2024-01-15T10:30:45Z"
executor:
  id: "cc-ds4"
  role: "executor"
  cli: "claude-code"
  version: "1.2.3"

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
    - ✓ All tests pass
    - ✓ Code style compliant
    - ✓ Security review passed
    - ✓ Documentation updated
    - ✓ Performance benchmarked
    
  git:
    latest_commit: "a1b2c3d"
    branch: "feature/db-refactor"
    files_changed: 5
    insertions: 120
    deletions: 45

  # 预期的评审重点
  review_focus:
    - "Thread safety in connection pool"
    - "Timeout configuration correctness"
    - "Backward compatibility"

review_round: 1         # 返工轮次，从 1 起；必须与当前轮次一致才被受理
status: "ready_for_review"
signal: "EXPLICIT"  # 显式信号，MACAO 强制认可
```

**状态转换规则**：

```python
# MACAO 状态识别逻辑（第一层：显式信号）
# 注意：字段路径必须与上方 Schema 一致 —— quality_metrics 与 git 嵌套在 development 之下
def check_explicit_signal(path='.macao/.dev.yml'):
    manifest = parse_yaml(path)          # 解析失败 → 视为无效产物，返回 None

    # .dev.yml 最小有效性规则：
    #   version 存在 + signal == EXPLICIT + status == ready_for_review
    #   + review_round 与当前轮次一致
    #   + tests_passed 为 true（或 tests_exempt 为 true）
    #   + latest_commit 非空、存在于本地 git 历史且未被消费过
    if (manifest.get('version') and
        manifest.get('signal') == 'EXPLICIT' and
        manifest.get('status') == 'ready_for_review'):
        qm = manifest['development']['quality_metrics']
        commit = manifest['development']['git']['latest_commit']
        tests_ok = (qm.get('tests_passed') is True or
                    qm.get('tests_exempt') is True)
        if tests_ok and commit and commit_exists(commit):
            return StateChange(from_state='CODING',
                              to_state='READY_FOR_REVIEW',
                              source='EXPLICIT_SIGNAL')
    return None  # 无效或缺省 → 不产生状态转移，转入 Layer 2 预警流程（见 §3.2）
```

---

### 2.2 `.review.yml` - Reviewer Opinion Manifest

**用途**：每个 Reviewer 返回其审查意见，作为投票凭证

**位置**：`.macao/.reviews/<reviewer_id>.review.yml`

**格式**：

```yaml
version: "1.0"
timestamp: "2024-01-15T10:45:30Z"

reviewer:
  id: "cc-glm"
  role: "reviewer"
  cli: "codex"
  version: "2.1.0"

checkpoint_ref: "a1b2c3d"  # 评审的源 commit
review_round: 1            # 评审轮次；checkpoint_ref + review_round 双匹配才被受理

# 核心评审意见
opinion:
  status: "CHANGES_REQUESTED"  # APPROVED | CHANGES_REQUESTED | REJECTED
  confidence: 0.92
  
  # 对 Executor 的反馈
  feedback:
    summary: "设计合理，但需补充异常处理"
    severity_breakdown:
      critical: 0
      major: 1
      minor: 2
    categories:
      - type: "logic"
        severity: "major"
        location: "src/db/connection.py:82"
        issue: "Missing exception handling for socket timeout"
        suggestion: "Wrap in try-except with proper logging"
        
      - type: "style"
        severity: "minor"
        location: "src/db/connection.py:105"
        issue: "Variable naming inconsistent with codebase"
        suggestion: "Rename pool_cfg to connection_pool_config"
  
  # 检查清单
  review_checklist:
    - "✓ Logic is sound"
    - "✓ Security considerations addressed"
    - "⚠ Error handling incomplete"
    - "✓ Tests are comprehensive"
    - "✓ Documentation is clear"
  
  # 可选：自动工具检查结果
  automated_checks:
    - tool: "bandit"
      status: "PASSED"
      findings: 0
    - tool: "pylint"
      status: "WARNING"
      score: 8.5
    - tool: "mypy"
      status: "PASSED"
      issues: 0

# 元数据
metadata:
  review_duration_seconds: 180
  methods: ["code_analysis", "security_scan", "performance_check"]
  certainty: "high"

vote: "NO_APPROVE"  # YES_APPROVE | NO_APPROVE | ABSTAIN
```

**`opinion.status` ↔ `vote` 映射与一致性校验**：

| opinion.status | vote（计票字段） |
|---------------|------------------|
| APPROVED | YES_APPROVE |
| CHANGES_REQUESTED | NO_APPROVE |
| REJECTED | NO_APPROVE |

- `vote` 是唯一计票依据；MACAO 解析 `.review.yml` 时按上表校验二者一致性
- 不一致（如 status=APPROVED 但 vote=NO_APPROVE）→ 该 `.review.yml` 判为**无效产物**：不计入有效票，发出告警并记录审计日志

---

### 2.3 `vote_result.json` - Consensus Result Record

**用途**：MACAO 生成的投票汇总，记录仲裁结果

**位置**：`.macao/vote_result.json`

**格式**：

```json
{
  "version": "1.0",
  "timestamp": "2024-01-15T10:55:00Z",
  
  "checkpoint_ref": "a1b2c3d",
  "executor": "cc-ds4",
  
  "review_round": 1,
  "reviewers_total": 2,
  "reviewers_responded": 2,
  
  "votes": [
    {
      "reviewer": "cc-glm",
      "vote": "NO_APPROVE",
      "confidence": 0.92,
      "issues_count": 3
    },
    {
      "reviewer": "kimi",
      "vote": "NO_APPROVE",
      "confidence": 0.85,
      "issues_count": 1
    }
  ],
  
  "input_artifacts": [
    {"kind": "review", "path": ".macao/.reviews/cc-glm.review.yml", "sha256": "9f2a7c1e5bd0", "message_id": "msg-20240115-003"},
    {"kind": "review", "path": ".macao/.reviews/kimi.review.yml", "sha256": "b91c04d8e3af", "message_id": "msg-20240115-004"}
  ],

  "consensus_rule": "2/3_majority",
  "vote_breakdown": {
    "approve": 0,
    "reject": 2,
    "abstain": 0
  },
  
  "decision": "REWORK_REQUIRED",
  "decision_confidence": 0.88,
  
  "summary": {
    "critical_issues": 0,
    "major_issues": 1,
    "minor_issues": 3,
    "action": "Send REWORK_REQUEST to executor"
  },
  
  "next_step": {
    "action": "REWORK",
    "deadline": "2024-01-15T12:55:00Z",
    "issues_to_fix": [
      {
        "id": "cc-glm/1",
        "type": "logic",
        "severity": "major",
        "description": "Missing exception handling for socket timeout"
      }
    ]
  }
}
```

**共识规则（2/3 多数 + 最低法定人数）**：

- 有效票 = 响应的 Reviewer 票数 − 弃权票（弃权不计入分母）
- 最低法定人数 `minimum_quorum = ⌈2 × configured_reviewers / 3⌉`，2 人与 3 人配置下均为 **2**
- 有效票 ≥ 法定人数 且 赞成占比 ≥ 2/3 → 决策 `APPROVED`（进入合并）
- 有效票 ≥ 法定人数 且 反对占比 ≥ 2/3 → 决策 `REWORK_REQUIRED`（进入返工）
- 其余一切情形（含 1:1、有效票低于法定人数、全弃权/全超时）→ Consensus Deadlock，触发人工接管（见 §6.1），由用户裁定 `APPROVED` / `REWORK` / 重试评审
- Reviewer 配置：MVP 阶段为 2 Reviewer（Codex + Kimi），此时规则等价于全票通过；3 Reviewer 为目标配置（如引入第二个 Codex 实例），协议本身支持 N 个 Reviewer（N ≥ 2）

**决策表**：

| configured | 场景 | 有效票 | 判定 |
|-----------|------|-------|------|
| 2 | 2 同意 | 2 | `APPROVED` |
| 2 | 2 反对 | 2 | `REWORK_REQUIRED` |
| 2 | 1 同意 + 1 反对 | 2 | 双方占比均未达 2/3 → Deadlock → 人工裁定 |
| 2 | 1 弃权 + 1 同意或反对 | 1 | 低于法定人数 → Deadlock → 人工裁定（剩余 1 票不得单独决定结果） |
| 2 | 全弃权 / 全超时 | 0 | Deadlock → 人工裁定 |
| 3 | ≥2 同意 | ≥2 | `APPROVED` |
| 3 | ≥2 反对 | ≥2 | `REWORK_REQUIRED` |
| 3 | 其他组合（如 1:1:1） | ≤2 | 未达比例 → Deadlock → 人工裁定 |

> 写入约定：各 `.review.yml` 由 Reviewer Adapter 以原子方式写入（临时文件 + rename）；MACAO 收集后立即将其纳入 git 提交——第二轮返工会覆盖同名文件，但 git 历史保留每一轮记录。`vote_result.json` 生成时必须记录本轮全部输入文件的 SHA-256 与对应 AEP `message_id`，保证审计链完整。

---

### 2.4 AEP (Agent Event Protocol) Message 规范

AEP v1.0 共定义 **7 种消息类型**（与 v1.0 `SRSv1.md` §7 的对应关系）：

| # | 消息类型 | 方向 | 用途 | v1.0 对应 |
|---|---------|------|------|----------|
| 1 | `DEVELOPMENT_STARTED` | MACAO → Executor | 下发开发任务与成功标准 | `TASK_ASSIGN` |
| 2 | `REVIEW_REQUEST` | MACAO → Reviewers | 发起评审，携带完整 `review_context` | 同名 |
| 3 | `REVIEW_RESPONSE` | Reviewer → MACAO | 返回 `.review.yml` 与投票 | `REVIEW_RESULT` |
| 4 | `REWORK_REQUEST` | MACAO → Executor | 下发返工问题清单 | v2.0 新增 |
| 5 | `MERGE_COMPLETED` | MACAO → 全体 | 通告共识达成与合并结果 | v2.0 新增 |
| 6 | `STATE_CHANGED` | Agent → MACAO | Agent 上报自身状态变化 | 同名 |
| 7 | `HUMAN_OVERRIDE_REQUEST` | MACAO → User | 请求人工接管决策 | v2.0 新增 |

以下给出开发/评审主流程的 4 个核心消息类型（1-4）的详细格式示例。

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
        "workspace_path": "~/work/macao-demo",
        "remote_name": "origin",
        "fetch_policy": "fetch_before_diff"
      },

      "code_changes": {
        "refs": {
          "base_commit": "b2c3d4e",
          "head_commit": "a1b2c3d"
        },
        "diff_command": "git diff b2c3d4e..a1b2c3d",
        "files_summary": "5 files changed, 120 insertions, 45 deletions"
      },
      
      "quality_metrics": {
        "tests_passed": true,
        "test_count": 24,
        "coverage": 0.87,
        "lint_score": 10
      },
      
      "task_info": {
        "description": "Refactored database connection pooling with timeout config",
        "review_focus": [
          "Thread safety in connection pool",
          "Timeout configuration correctness",
          "Backward compatibility"
        ]
      }
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
> 2. 仓库/工作区定位：优先取 `payload.repository` 块；缺省时按 `project` 名称从项目配置 `macao.yaml` 的 `repository` 段解析（见第十三部分）。两者必居其一，否则该 `REVIEW_REQUEST` 判为无效消息。
> 3. Reviewer 在本地工作区执行 `git fetch` + `git diff` 取得变更（见 §5.3），不内联 diff 文本或 patch 内容，规避消息体积上限、编码与截断问题；若未来需要离线评审再扩展内联 patch（需另行定义大小上限与摘要校验）。

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
    "round": 1,
    
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
    "detail": "refactoring connection pool"
  }
}
```

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
    "options": ["APPROVED", "REWORK", "RETRY_REVIEW"],
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
            return (AgentState.DONE if result.decision == 'APPROVED'
                    else AgentState.REWORK)

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
| — | `CODING` / `REWORK` | 产物 | 当前轮 `.dev.yml` 通过最小有效性校验（新 commit + round 匹配） | `READY_FOR_REVIEW` | 锁定 checkpoint_ref；检查点窗口计时（1m） |
| E2 | `READY_FOR_REVIEW` | 命令 | `.dev.yml` 消费完成，发送 `REVIEW_REQUEST` AEP | `WAITING_REVIEW` | `.dev.yml` 归档；记录评审 deadline |
| E3 | `WAITING_REVIEW` | 产物 | 有效票 ≥ minimum_quorum（当前 ref/round 的 `.review.yml`） | `CONSENSUS_CHECK` | 收集到的 `.review.yml` 纳入 git 提交 |
| — | `WAITING_REVIEW` | 超时 | 超时降级流程完成（ping/弃权/人工裁定，见 §6.1） | `CONSENSUS_CHECK` | 弃权票记入 `vote_result.json` |
| E4 | `CONSENSUS_CHECK` | 产物 | `vote_result.json` 决策 = `APPROVED` | `DONE` | Merge Controller 执行合并策略（第十四部分）；发送 `MERGE_COMPLETED`；本轮产物归档 |
| E5 | `CONSENSUS_CHECK` | 产物 | 决策 = `REWORK_REQUIRED` 且 round < max_rework_rounds | `REWORK` | 发送 `REWORK_REQUEST`（round+1）；本轮产物归档 |
| E6 | `REWORK` | 产物 | 新一轮 `.dev.yml` 有效（round+1、新 commit） | `READY_FOR_REVIEW` | 更新当前 checkpoint_ref |
| E7 | `CONSENSUS_CHECK` | 命令 | round ≥ max_rework_rounds 仍返工，或 Deadlock 人工裁定 | `DONE` / `REWORK` / 终止 | 人工裁定写入审计日志 |
| E8 | `*`（任意） | 诊断 | 60min 无进展 + Layer 3 置信度 <0.7 | `UNKNOWN` | HUMAN_OVERRIDE，等待用户裁定 |

> 说明：
> - `CODING`/`REWORK` → `READY_FOR_REVIEW` 由产物触发（`.dev.yml` 校验通过，见 §3.2 Layer 1a），因入口状态有两个故不单独编号；
> - 超时不是独立的状态来源：超时降级的结果（弃权票/人工裁定）最终仍通过 E3 或 E7 生效；
> - 除本表所列来源外，任何实现不得引入其他状态转移路径。

### 3.4 产物生命周期与场景推演

**生命周期表**（与 §3.2 状态作用域读取配合，保证旧产物不遮蔽后续阶段）：

| 产物 | 生成者 | 受理窗口（FSM 状态 × ref/round） | 消费/归档动作 |
|------|--------|--------------------------------|--------------|
| `.dev.yml` | Executor | 仅 `CODING` / `REWORK`，未被消费、本轮新 commit、round 匹配 | E2 触发时标记 consumed 并复制到 `.macao/archive/<checkpoint_ref>/r<round>/` |
| `.review.yml` | 各 Reviewer | 仅 `WAITING_REVIEW`，checkpoint_ref + review_round 双匹配 | E3 触发时随 git 提交存档；进入下一轮前上一轮文件已固化于归档目录 |
| `vote_result.json` | MACAO | 仅 `CONSENSUS_CHECK`，ref + round 双匹配 | E4/E5 执行后归档 |

> 归档动作 = "git 提交 → 复制到 archive 目录 → 删除原位置"，顺序保证审计链完整。

**场景推演一：首次开发，双 Reviewer 批准**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1 | 用户受理任务 | `IDLE` → `CODING`（E1） | — |
| 2 | Claude 生成 `.dev.yml`（commit `a1b2c3d`，round 1） | `CODING` → `READY_FOR_REVIEW` | `.dev.yml`（校验通过） |
| 3 | Orchestrator 发送 `REVIEW_REQUEST` | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2） | —（`.dev.yml` 已归档） |
| 4 | cc-glm、kimi 各写 `.review.yml`（round 1），有效票 2 ≥ 2 | `WAITING_REVIEW` → `CONSENSUS_CHECK`（E3） | 2 × `.review.yml` |
| 5 | MACAO 写 `vote_result.json`（APPROVED） | `CONSENSUS_CHECK` → `DONE`（E4） | `vote_result.json` |

每步恰好命中一个合法转移；步骤 3 之后 `.dev.yml` 已归档，不会再被 Layer 1a 读到。

**场景推演二：返工第二轮**

| 步骤 | 触发 | 状态变化（命中转移） | 作用域内读取的产物 |
|------|------|--------------------|------------------|
| 1-5 | 同场景一步骤 1-5，但步骤 5 决策 = `REWORK_REQUIRED` | `CONSENSUS_CHECK` → `REWORK`（E5） | `vote_result.json`（round 1） |
| 6 | 发送 `REWORK_REQUEST`（round=2）；r1 产物已归档 | （伴随动作） | — |
| 7 | Claude 修复后生成新 `.dev.yml`（commit `d4e5f6a`，round 2） | `REWORK` → `READY_FOR_REVIEW`（E6） | 新 `.dev.yml`（双匹配） |
| 8 | 发送 `REVIEW_REQUEST`（携带 r1 反馈作为增量复审上下文） | `READY_FOR_REVIEW` → `WAITING_REVIEW`（E2） | — |
| 9 | 双 Reviewer 返回 round 2 意见 | 同场景一步骤 4-5 | 当前轮产物 |

旧 r1 `.review.yml` 在步骤 6 前已归档——即使 Reviewer 尚未覆盖同名文件也不会被误读；
若 round 已达 `max_rework_rounds` 仍为返工决策，则走 E7 人工裁定。

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

### 5.2 标准化的 Reviewer Context 包

MACAO 在发送 `REVIEW_REQUEST` 时，必须提供完整的 Context：

```yaml
review_context:
  # 1. 任务背景
  task_info:
    description: "Refactored database connection pooling"
    business_impact: "Improves connection pool efficiency by 30%"
    timeline_info: "This is the second iteration after cc-glm feedback"
    
  # 2. 代码变更（传 refs，Reviewer 在本地工作区自行取 diff）
  code_changes:
    summary:
      files_changed: 5
      insertions: 120
      deletions: 45
    refs:
      base_commit: "b2c3d4e"     # 变更前 commit
      head_commit: "a1b2c3d"     # 被评审 commit，即 checkpoint_ref
    diff_command: "git diff b2c3d4e..a1b2c3d"   # 参考命令，非传输内容
    files_list:
      - path: "src/db/connection.py"
        status: "modified"
        added_lines: 80
        deleted_lines: 30
      - path: "tests/test_db.py"
        status: "modified"
        added_lines: 35
        deleted_lines: 12
    
  # 3. 质量指标（来自 .dev.yml）
  quality_snapshot:
    tests:
      passed: 24
      failed: 0
      coverage: 0.87
    static_analysis:
      lint_errors: 0
      security_issues: 0
      type_check_errors: 0
    performance:
      avg_query_time_ms: 45
      p99_query_time_ms: 120
    
  # 4. Executor 的自评与重点
  executor_self_assessment:
    what_was_done: |
      - Refactored connection pooling logic
      - Added configurable timeout parameters
      - Added comprehensive test suite
      - Updated documentation
    
    review_focus:
      - "Thread safety in connection pool"
      - "Timeout configuration correctness"
      - "Backward compatibility with existing code"
    
    known_limitations:
      - "Connection retry logic not implemented yet"
      - "Performance benchmarks pending"
    
  # 5. 历史上下文（重复评审时有用）
  history:
    previous_reviews: 0  # 这是第一次评审
    previous_feedback: []  # 无前序反馈
    
  # 6. 参考资源
  references:
    architecture_doc: "docs/db_design.md"
    related_tickets: ["TASK-123", "TASK-124"]
    related_commits: ["a1b2c3d", "b2c3d4e"]
```

### 5.3 Reviewer 的标准工作流程

每个 Reviewer 收到 `REVIEW_REQUEST` 后，应该按照这个流程操作：

```bash
# Step 1: 提取 Context
cat <<< "$REVIEW_REQUEST" | jq '.payload.review_context' > /tmp/context.json

# Step 2: 定位工作区并按 refs 取得代码变更
#   仓库定位：优先读消息的 repository 块，缺省时由 MACAO 按 macao.yaml 解析后注入
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
cat > .macao/.reviews/reviewer_id.review.yml <<EOF
version: "1.0"
...
EOF

# Step 6: 发送 REVIEW_RESPONSE 给 MACAO
macao send-message REVIEW_RESPONSE \
  --review-file .macao/.reviews/reviewer_id.review.yml
```

> 注：`quality_snapshot.performance` 为可选扩展项——无性能基准数据时可省略该子块。摘要类文档的 Context 示例从简，允许省略可选字段，以本节 Schema 为准。
>
> 注：仓库定位遵循 §2.4 约定——优先 `payload.repository` 块，缺省时按 `project` 从 `macao.yaml` 的 `repository` 段解析（第十三部分）；`code_changes.refs.*` 为唯一权威路径。

---

## 第六部分：人工接管点与错误恢复

### 6.1 明确的人工接管条件

```python
HUMAN_OVERRIDE_TRIGGERS = [
    {
        "condition": "State ambiguity",
        "description": "Layer 1 signal missing AND Layer 2 confidence < 0.7",
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
        "action": "Ask user: 'APPROVED or REWORK?'",
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
| **Explicit Signal Usage Rate** | >99% | 状态转换由 .yml 驱动的比例 |
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

### 成功标志 (MVP 完成)

- ✅ 单机 Claude Code + 2x Reviewer 的完整工作流运行通过
- ✅ 所有关键状态转换由显式产物与命令型转移驱动，无 LLM 裁判（见 §3.3 统一转移表）
- ✅ 三个 CLI 的 Adapter 都能正常启停与通信
- ✅ 自动化测试覆盖 80% 以上逻辑
- ✅ 用户手册与内部文档完备

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
| supported_os / cli_version_range | - | 平台与版本兼容范围 |

### 12.3 MVP 准入矩阵

| CLI | can_execute | can_review | hook | noninteractive | Adapter 类型 |
|-----|-------------|------------|------|----------------|--------------|
| claude-code | ✓ | — | ✓ | 部分 | claude-hook |
| codex | — | ✓ | — | ✓ | pty-wrapper |
| kimi | — | ✓ | — | ✓ | pty-wrapper |

### 12.4 兼容性验收（Conformance）

每个 Adapter 通过统一测试套件后方可标记"支持"：

- preflight 全绿；版本探测与 `cli_version_range` 一致；
- 五类一致性场景：PTY 断开重连、重复 message_id 回执去重、CLI 升级后探测、厂商限流退避、凭据失效报错；
- producer→consumer 端到端：Adapter 生成的产物 fixture 直接喂给消费方命令（如 §5.3 的 jq 路径）验证可解析。

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
timeouts:
  development: "2h"
  checkpoint_validation: "1m"
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

加载规则：Config Loader 启动时读取并做 JSON Schema 校验，失败则拒绝启动并列出错误项；运行中变更需显式 `macao config reload`，且不影响进行中的 round。

---

## 第十四部分：用户旅程与运行手册

### 14.1 从零到第一次合并（主旅程）

1. 安装预检：`macao preflight` —— 校验三个 CLI 已安装、登录态有效、版本在支持矩阵内，输出 PreflightReport 与修复建议；
2. 初始化：`macao init` 生成 `macao.yaml` 模板 → 编辑团队与仓库段 → `macao doctor` 校验配置与环境；
3. 创建任务：`macao task create --title … --acceptance … --branch feature/x` —— 需求最小集 = 标题 + 可测试的验收标准（写入 `DEVELOPMENT_STARTED.success_criteria`）+ 目标仓库/分支 + 期望产物路径；验收标准缺失则拒绝创建；
4. 观察：`macao status`（FSM 状态 / 当前 ref 与 round / 各 agent 状态）、`macao logs <agent>`；
5. 人工处置：出现 HUMAN_OVERRIDE_REQUEST 时，`macao override list` 查看证据（诊断报告/票面/冲突详情）→ `macao override resolve --choice APPROVED|REWORK|RETRY|CANCEL [--note]`；每笔决策写入审计并向请求方回执；
6. 合并与发布：见 14.6 Merge Policy；
7. 归档：流程结束后本轮产物自动归档至 `.macao/archive/<ref>/r<round>/` 并随 git 提交。

### 14.2 日常运维操作

| 操作 | 命令 | 语义 |
|------|------|------|
| 暂停观察 | `macao pause <task>` | 进入 HOLD，停止状态推进 |
| 取消 | `macao cancel <task>` | 终止任务，通知全体 agent，归档现场 |
| 重试 | `macao retry <task>` | 从最后检查点重放 |
| 用量查询 | `macao usage` | 按阶段/CLI 汇总 token 与调用次数 |

> **并发声明**：MVP 单机同一时刻仅允许一个活动任务（串行编排）；多任务并发与调度属 Scheduler 范畴，延至 v1.2。

### 14.3 日志与保留

Terminal 日志滚动保留 `audit.retention_days`（默认 90 天）；审计事件（状态转移/人工决策/override 回执）永久保留于 State Store。

### 14.4 升级与降级

CLI 版本超出支持矩阵 → preflight 告警并要求显式确认；某 Reviewer Adapter 故障时可临时将其标记弃权，走超时降级路径（§6.2）。

### 14.5 Merge Policy（从批准到合并）

- E4 触发后由 Merge Controller 执行：检出工作分支 → merge 到 `default_branch` → 冲突即触发 Git Conflict 人工接管；
- CI gate（可选）：`merge.ci_gate_command` 配置的命令通过后才推送；CI 失败视为返工，生成新一轮 `REWORK_REQUEST`（注明 CI 失败原因）；
- 合并完成推送 `MERGE_COMPLETED`（含 merge_commit）；合并事故用 git revert 回滚，回滚事件入审计；
- 默认 fast-forward 优先，no-ff 可在 `merge` 段配置。

---

## 第十五部分：边界声明与非功能需求

### 15.1 产品边界（重要）

v2.x 定位为**「固定三 CLI（Claude Code + Codex/Kimi）的本地单机协作 PoC 规格」**，不是通用跨 CLI 编排平台。以下能力明确不在 MVP 内：跨物理机/远程 SSH（v1.1）、多任务并行与调度（v1.2）、Web Dashboard（v1.1+）、RBAC/多租户（企业版）。

### 15.2 返工策略

- `max_rework_rounds = 3`：达到上限仍返工 → E7 人工裁定（放弃 / 继续 / 缩小范围）；
- `review_strategy = delta_plus_focus`：第 n 轮 `REVIEW_REQUEST` 附带上一轮 `issues_to_fix` 与增量 diff（base = 上轮 head_commit）；Reviewer 对未改动部分做聚焦抽查而非全量重评。

### 15.3 安全边界

| 风险 | 缓解措施 |
|------|---------|
| Reviewer 读到恶意代码被 prompt injection，操纵共识 | 评审产物 Schema 强校验（含 status↔vote 映射校验）；`review_focus` 白名单注入；异常投票模式告警；关键决策保留人工抽查点 |
| 凭据泄露 | CLI 凭据经环境变量/keyring 注入子进程，不落盘明文；日志脱敏（`secrets_masking`） |
| 代码/diff 发送至第三方厂商 | `security.allowed_clis` 白名单约束可用 CLI；`send_terminal_logs_to_reviewers` 默认关闭；企业部署前须完成数据出境评估 |
| 自动化编排触碰第三方 CLI 服务条款 | PoC 前完成 ToS/法务核实（已列入风险表）；必要时提供半自动触发模式 |

### 15.4 成本计量

Usage Meter 记录每次流程各阶段的 token 用量与调用次数（数据来自 CLI 输出与适配器统计，精度受厂商遥测限制，PoC 以可获得为准）；预算超限仅告警不硬限（`monthly_budget_usd: null`）。

### 15.5 评审质量评测计划（核心价值验证）

KPI 之外增加共识有效性评测，回答"双 Reviewer 共识是否真能抓住缺陷"：

- 构造 N ≥ 20 的含已知缺陷样本集（缺陷分层：逻辑 / 安全 / 风格）；
- 测量指标：共识召回率（已知缺陷被 ≥1 个 Reviewer 标记且进入返工的比例）与误报率；
- 验收线：召回率 < 60% 则重新评估角色分配与 Context 设计，再进入 v1.1 角色扩展；
- 结果记入 PoC 报告，作为对外宣称"评审有效性"的唯一依据。

---

**版本历史**
- v1.0: 高阶架构设计（即 `SRSv1.md`，产品暂定名 "A"）
- v1.5: 专家评审意见反馈（见 `IMPROVEMENT_SUMMARY.md` 第四节）
- v2.0: 规范化流程 + 标准输出物 + 改进状态识别
- v2.0.1: 按 `docs/reviews/2026-08-25-review-result-ec60f70-*` 三份评审反馈闭环 P0/P1/P2 问题
  （状态机唯一化、共识规则引入最低法定人数与决策表、diff 载体统一为 refs、
   字段命名统一 checkpoint_ref 与 to、AEP 补齐 7 类示例、status↔vote 映射等）
- v2.1: 按 `docs/reviews/2026-08-26-review-result-47f54f2-codex.md` 复审闭环 P0-1/P0-2 与 P1，
  并补齐产品完整性章节：
  - 状态识别改为「当前 FSM 状态 + checkpoint/round」作用域读取，新增产物生命周期与场景推演（§3.2–§3.4）
  - 统一转移表纳入 AEP 命令与超时来源；§1.2 阶段表与之一致
  - `code_changes.refs.*` 唯一路径 + `repository` 定位块（解析源 = macao.yaml）
  - 产物补 `review_round` / `input_artifacts` 字段；Layer 3 图示统一"始终提示、低置信度接管"
  - 新增第十一～十五部分：系统架构与技术栈、Adapter Contract v1 与能力矩阵、配置规范、用户旅程与运行手册、边界声明与非功能需求
