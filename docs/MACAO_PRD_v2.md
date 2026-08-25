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

| 阶段 | 状态 | 入口条件 | 出口条件 | 关键产物 | 超时 |
|------|------|--------|--------|---------|------|
| **REQUIREMENT** | `IDLE` | 用户给出指令 | Executor 收到任务 | 任务描述文本 | - |
| **DEVELOPMENT** | `CODING` | Executor 启动 CLI | `.dev.yml` 创建有效 | `.dev.yml` + Git Commit | 2h |
| **CHECKPOINT** | `READY_FOR_REVIEW` | Git Diff 存在 + Tests Pass | `.dev.yml` 内容有效 | `.dev.yml` 文件 | 1m |
| **REVIEW_REQUEST** | `WAITING_REVIEW` | MACAO 发送 AEP 消息 | 达到法定人数判定条件或超时降级流程完成 | 所有 `.review.yml` | 30m |
| **REVIEWING** | `REVIEWING` | Reviewer 接收消息 | `.review.yml` 生成 | `.review.yml` | 10m/reviewer |
| **CONSENSUS** | `CONSENSUS_CHECK` | 所有 `.review.yml` 收集完毕 | 投票结果产生 | `vote_result.json` | 1m |
| **MERGE / REWORK** | `DONE` / `REWORK` | 共识达成 | - | 最终产物或返工清单 | - |

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
    #   + tests_passed 为 true（或 tests_exempt 为 true）
    #   + latest_commit 非空且存在于本地 git 历史
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
    
    "review_context": {
      "dev_checkpoint": {
        "path": ".macao/.dev.yml",
        "content_base64": "..."
      },
      
      "code_changes": {
        "base_commit": "b2c3d4e",
        "head_commit": "a1b2c3d",
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

> **代码变更载体约定（重要）**：`code_changes` 只传输 **refs**（`base_commit` / `head_commit`），不内联 diff 文本或 patch 内容。`diff_command` 仅是给 Reviewer 的参考命令，不是传输内容。Reviewer 在本地工作区自行执行 `git fetch` + `git diff` 取得变更（见 §5.3）。此约定避免了消息体积上限、编码与截断问题；若未来需要离线评审再扩展内联 patch（需另行定义大小上限与摘要校验）。

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
   ✓ 直接转换到目标状态，不进入后续层

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
   🚨 立即触发 HUMAN_OVERRIDE，等待用户确认

```

> 注：图中标注的可信度（100% / 80% / 60%）为设计目标值，以 PoC 实测数据为准（验收阈值见第八部分 KPI）。

### 3.2 状态识别的优先级规则

```python
def recognize_agent_state(agent_id: str, project: str) -> AgentState:
    """
    状态识别的唯一规范入口（三层严格分层，只有 Layer 1 能产生业务状态转移）：
    1. Layer 1 显式产物：三类文件逐一校验，命中即返回映射的业务状态
    2. Layer 2 行为推断：仅写日志与预警，禁止返回业务状态（不推进状态机）
    3. Layer 3 LLM 诊断：仅在疑似卡死时触发，产出报告供人工决策，自身不产生业务状态
    """

    checkpoint_ref = current_checkpoint(project)

    # ===== Layer 1a: .dev.yml（Executor 产物）→ READY_FOR_REVIEW =====
    dev = load_and_validate('.macao/.dev.yml', DEV_YML_SCHEMA)   # 最小有效性规则见 §2.1
    if dev.valid:
        return map_status_to_state(dev.status)   # 'ready_for_review' → READY_FOR_REVIEW

    # ===== Layer 1b: .review.yml（各 Reviewer 产物）→ CONSENSUS_CHECK =====
    reviews = load_all_validated('.macao/.reviews/*.review.yml', REVIEW_YML_SCHEMA,
                                 expect_checkpoint_ref=checkpoint_ref)
    if reviews.count_valid >= minimum_quorum(reviews.configured):   # 法定人数见 §2.3
        return AgentState.CONSENSUS_CHECK        # 有效票达到法定人数，进入共识判定

    # ===== Layer 1c: vote_result.json（MACAO 产物）→ DONE / REWORK =====
    result = load_and_validate('.macao/vote_result.json', VOTE_RESULT_SCHEMA,
                               expect_checkpoint_ref=checkpoint_ref)
    if result.valid:
        return (AgentState.DONE if result.decision == 'APPROVED'
                else AgentState.REWORK)

    # ===== Layer 2: 行为推断 —— 只记录与预警，永不改变业务状态 =====
    signals = collect_behavior_signals(agent_id)          # git / tests / pty_idle
    inferred = infer_state_from_behavior(signals)
    log_behavior_inference(agent_id, inferred, confidence=0.8)
    emit_warning(f"Agent {agent_id}: 无有效显式产物，推断状态 {inferred} 仅供参考，"
                 f"保持上一个已确认状态")   # 不返回 inferred，不推进状态机

    # ===== Layer 3: LLM Judgment（仅故障诊断用，不产生业务状态）=====
    if is_agent_suspected_deadlock(agent_id):
        logs = get_terminal_logs(agent_id, lines=300)
        diagnosis = call_llm_for_diagnosis(logs, signals)
        report_diagnosis(diagnosis)               # 只提示用户，不自动决策

        if diagnosis.confidence < 0.7:
            trigger_human_override(
                agent_id=agent_id,
                reason="State ambiguous, awaiting human decision",
                diagnostic_info=diagnosis
            )
            return AgentState.UNKNOWN             # 等待用户确认后人工设定状态

    # 未命中显式信号且未触发人工接管：保持上一个已确认状态（HOLD），不推进
    return last_confirmed_state(agent_id)
```

> **行为约定**（与 §3.1 的分层承诺严格一致）：
> 1. 业务状态只能由三类显式产物驱动；Layer 2 的推断结果只进入日志与告警。
> 2. 无显式信号且未触发人工接管时，系统保持（HOLD）上一个已确认状态，绝不静默推进。
> 3. `.review.yml` / `vote_result.json` 必须校验 `checkpoint_ref` 与当前轮次匹配，防止跨轮次误读。

### 3.3 关键的状态转换表

| 当前状态 | 触发条件 | 目标状态 | 来源 | 可靠性 |
|---------|--------|--------|------|--------|
| `IDLE` | 用户/MACAO 发送 `DEVELOPMENT_STARTED` AEP 消息 | `CODING` | Explicit | ✅✅✅ |
| `CODING` | `.dev.yml` 状态字段 = `ready_for_review` | `READY_FOR_REVIEW` | Explicit | ✅✅✅ |
| `READY_FOR_REVIEW` | MACAO 发送 `REVIEW_REQUEST` AEP 消息 | `WAITING_REVIEW` | Explicit | ✅✅✅ |
| `WAITING_REVIEW` | 有效票达到法定人数或超时降级完成 | `CONSENSUS_CHECK` | Explicit | ✅✅✅ |
| `CONSENSUS_CHECK` | `vote_result.json` 决策字段 = `APPROVED` | `DONE` | Explicit | ✅✅✅ |
| `CONSENSUS_CHECK` | `vote_result.json` 决策字段 = `REWORK_REQUIRED` | `REWORK` | Explicit | ✅✅✅ |
| `REWORK` | `.dev.yml` 被重新创建 + 新 commit | `CODING` | Explicit | ✅✅✅ |
| `*` (任意) | 60min 无进展 + Layer 3 置信度 <0.7 | `UNKNOWN` + 人工介入 | LLM | ⚠️ |

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

# Step 2: 按 refs 取得代码变更（在项目工作区内）
cd <workspace>
git fetch --all
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
- ✅ 所有关键状态转换由显式信号驱动，无 LLM 裁判
- ✅ 三个 CLI 的 Adapter 都能正常启停与通信
- ✅ 自动化测试覆盖 80% 以上逻辑
- ✅ 用户手册与内部文档完备

---

**版本历史**
- v1.0: 高阶架构设计（即 `SRSv1.md`，产品暂定名 "A"）
- v1.5: 专家评审意见反馈（见 `IMPROVEMENT_SUMMARY.md` 第四节）
- v2.0: 规范化流程 + 标准输出物 + 改进状态识别
- v2.0.1: 按 `docs/reviews/2026-08-25-review-result-ec60f70-*` 三份评审反馈闭环 P0/P1/P2 问题
  （状态机唯一化、共识规则引入最低法定人数与决策表、diff 载体统一为 refs、
   字段命名统一 checkpoint_ref 与 to、AEP 补齐 7 类示例、status↔vote 映射等）
