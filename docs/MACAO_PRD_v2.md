# MACAO (Multi-Agent CLI Agent Orchestrator) - 产品方案 v2.0

> **核心理念**：通过**流程规范化** + **输出物标准化**，使 Agent 状态识别从"黑盒推断"转变为"约定式识别"。

---

## 执行摘要

### 产品定义
**MACAO** 是一个面向 AI 软件开发团队的**跨终端 CLI 进程编排平台**，通过统一调度不同厂商的 CLI Coding Agent（Claude Code, Codex, Kimi-Code 等），实现跨物理机、多角色、多阶段的软件研发自动化协作。

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
      (所有 Reviewer 返回意见)
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
| **REVIEW_REQUEST** | `WAITING_REVIEW` | MACAO 发送 AEP 消息 | Reviewer 全部返回意见 | 所有 `.review.yml` | 30m |
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
def check_explicit_signal(checkpoint_file):
    if os.path.exists('.macao/.dev.yml'):
        manifest = parse_yaml(checkpoint_file)
        if (manifest['status'] == 'ready_for_review' and
            manifest['quality_metrics']['tests_passed'] and
            manifest['git']['latest_commit'] is not None):
            return StateChange(from_state='CODING', 
                              to_state='READY_FOR_REVIEW',
                              source='EXPLICIT_SIGNAL')
    return None  # 无法判断，进入第二层推断
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
  "reviewers_total": 3,
  "reviewers_responded": 3,
  
  "votes": [
    {
      "reviewer": "cc-glm",
      "vote": "NO_APPROVE",
      "confidence": 0.92,
      "issues_count": 3
    },
    {
      "reviewer": "qwen",
      "vote": "YES_APPROVE",
      "confidence": 0.88,
      "issues_count": 0
    },
    {
      "reviewer": "kimi",
      "vote": "YES_APPROVE",
      "confidence": 0.85,
      "issues_count": 1
    }
  ],
  
  "consensus_rule": "2/3_majority",
  "vote_breakdown": {
    "approve": 2,
    "reject": 1,
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

---

### 2.4 AEP (Agent Event Protocol) Message 规范

#### Type A：开发阶段通知

```json
{
  "protocol": "AEP/1.0",
  "message_id": "msg-20240115-001",
  "timestamp": "2024-01-15T10:00:00Z",
  
  "type": "DEVELOPMENT_STARTED",
  "from": "macao",
  "to_agent": "cc-ds4",
  
  "payload": {
    "project": "washdb",
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
  "to_agents": ["cc-glm", "qwen", "kimi"],
  
  "payload": {
    "project": "washdb",
    "executor": "cc-ds4",
    "checkpoint_id": "a1b2c3d",
    
    # 核心 Context 包：Reviewer 需要的所有信息
    "review_context": {
      "dev_checkpoint": {
        "path": ".macao/.dev.yml",
        "content_base64": "..."  # Base64 encoded .dev.yml
      },
      
      "code_changes": {
        "diff": "git diff a1b2c3d^..a1b2c3d",
        "summary": "5 files changed, 120 insertions, 45 deletions"
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
    "project": "washdb",
    "checkpoint_id": "a1b2c3d",
    
    "review_file": {
      "path": ".macao/.reviews/cc-glm.review.yml",
      "content_base64": "..."  # Base64 encoded review
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
  "to_agent": "cc-ds4",
  
  "payload": {
    "project": "washdb",
    "checkpoint_id": "a1b2c3d",
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

### 3.2 状态识别的优先级规则

```python
def recognize_agent_state(agent_id: str, project: str) -> AgentState:
    """
    状态识别的决策流程：
    1. 优先检查显式信号（.yml 文件）
    2. 其次进行行为推断（系统监控）
    3. 最后才调用 LLM（仅用于异常诊断）
    """
    
    # ===== Layer 1: Explicit Signal =====
    dev_checkpoint = read_file(f'.macao/.dev.yml')
    if dev_checkpoint and is_valid_yaml(dev_checkpoint):
        status = dev_checkpoint.get('status')
        signal = dev_checkpoint.get('signal')
        
        if signal == 'EXPLICIT':
            # 信任开发者的显式声明
            return map_explicit_status_to_state(status)
    
    # ===== Layer 2: Behavioral Inference =====
    git_status = run_cmd('git status --porcelain')
    test_result = run_cmd('pytest --tb=no -q')
    pty_activity = check_pty_idle_time(agent_id)
    
    behavior_signals = {
        'git_changed': len(git_status) > 0,
        'tests_passed': test_result.returncode == 0,
        'pty_idle': pty_activity > 60,
        'dev_yml_exists': os.path.exists('.macao/.dev.yml')
    }
    
    # 根据行为推断状态（仅作参考，不改变实际状态）
    inferred_state = infer_state_from_behavior(behavior_signals)
    log_behavior_inference(agent_id, inferred_state, confidence=0.75)
    
    # 如果没有显式信号，发出预警
    if not dev_checkpoint:
        emit_warning(f"Agent {agent_id}: No explicit checkpoint, "
                     f"inferred state {inferred_state} (low confidence)")
    
    # ===== Layer 3: LLM Judgment (故障诊断用) =====
    if is_agent_suspected_deadlock(agent_id):
        logs = get_terminal_logs(agent_id, lines=300)
        diagnosis = call_llm_for_diagnosis(logs, behavior_signals)
        
        if diagnosis.confidence < 0.6:
            trigger_human_override(
                agent_id=agent_id,
                reason="State ambiguous, awaiting human decision",
                diagnostic_info=diagnosis
            )
            return AgentState.UNKNOWN
    
    # 正常情况：返回显式状态或推断状态
    return dev_checkpoint.state if dev_checkpoint else inferred_state
```

### 3.3 关键的状态转换表

| 当前状态 | 触发条件 | 目标状态 | 来源 | 可靠性 |
|---------|--------|--------|------|--------|
| `IDLE` | 用户/MACAO 发送 `DEVELOPMENT_STARTED` AEP 消息 | `CODING` | Explicit | ✅✅✅ |
| `CODING` | `.dev.yml` 状态字段 = `ready_for_review` | `READY_FOR_REVIEW` | Explicit | ✅✅✅ |
| `READY_FOR_REVIEW` | MACAO 发送 `REVIEW_REQUEST` AEP 消息 | `WAITING_REVIEW` | Explicit | ✅✅✅ |
| `WAITING_REVIEW` | 所有 Reviewer 返回 `.review.yml` | `CONSENSUS_CHECK` | Explicit | ✅✅✅ |
| `CONSENSUS_CHECK` | `vote_result.json` 决策字段 = `APPROVED` | `DONE` | Explicit | ✅✅✅ |
| `CONSENSUS_CHECK` | `vote_result.json` 决策字段 = `REWORK_REQUIRED` | `REWORK` | Explicit | ✅✅✅ |
| `REWORK` | `.dev.yml` 被重新创建 + 新 commit | `CODING` | Explicit | ✅✅✅ |
| `*` (任意) | 60min 无进展 + Layer 3 置信度 <0.6 | `UNKNOWN` + 人工介入 | LLM | ⚠️ |

---

## 第四部分：改进的 MVP 范围与交付计划

### 4.1 严格的 MVP 范围（第一期，6-8 周）

#### 必做 (P0)
- [x] **单机 Claude Code Adapter**（基于 PTY + Hook）
- [x] **本地 Codex 和 Kimi 的 Wrapper Adapter**（基于 PTY 监听）
- [x] **LangGraph Workflow 引擎**（FSM 实现）
- [x] **`.dev.yml` 和 `.review.yml` 规范的完整实现**
- [x] **投票与共识逻辑**（2/3 多数投票）
- [x] **CLI 界面**（Rich + prompt_toolkit 交互）
- [x] **本地 agmsg 集成**（Queue-based 通信）
- [x] **单机编排的完整端到端测试**

#### 不做 (P1+)
- [ ] ~~远程 SSH Agent 支持~~（移至 v1.1）
- [ ] ~~Capability Registry & Scheduler~~（移至 v1.2）
- [ ] ~~Multi-Reviewer Consensus 高级算法~~（2/3 投票先用，后续优化）
- [ ] ~~Web Dashboard~~（CLI 先行，后续补 Web）

### 4.2 分期交付计划

```
Week 1-2: Architecture & .yml Schema Design
  ├─ 完成 .dev.yml, .review.yml, vote_result.json 详细设计
  ├─ 定义 AEP 消息格式
  └─ 完成 State Recognition FSM 文档

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
reviewer_context:
  # 1. 任务背景
  task_info:
    description: "Refactored database connection pooling"
    business_impact: "Improves connection pool efficiency by 30%"
    timeline_info: "This is the second iteration after cc-glm feedback"
    
  # 2. 代码变更
  code_changes:
    summary:
      files_changed: 5
      insertions: 120
      deletions: 45
    detailed_diff: "git diff a1b2c3d^..a1b2c3d"  # 完整 diff
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

# Step 2: 检查代码变更
cd <project_dir>
git apply /tmp/code_changes.patch  # 应用变更到本地

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

---

## 第六部分：人工接管点与错误恢复

### 6.1 明确的人工接管条件

```python
HUMAN_OVERRIDE_TRIGGERS = [
    {
        "condition": "State ambiguity",
        "description": "Layer 1 signal missing AND Layer 2 confidence < 0.7",
        "action": "Ask user: 'What should the state be?'",
        "timeout": "5 minutes (default proceed with high-confidence state)"
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
    }
]
```

### 6.2 优雅的降级策略

```
Normal Path:
  Executor → Dev Complete → Review Request → Reviewers Work → Consensus → Merge

Degraded Path (1 Reviewer unavailable):
  Executor → Dev Complete → Review Request → (2/3 Reviewers) → Consensus → Merge
  (Skip unavailable reviewer, proceed with 2/3)

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
| Service | Agent Registry | 本地 JSON + 远程 SSH 配置 |
| ConfigMap | `.dev.yml` + `.review.yml` | YAML 文件 |
| Event | AEP Message | agmsg Queue |
| StatefulSet | Agent Lifecycle | LangGraph FSM |
| Ingress | Review Workflow | AEP REVIEW_REQUEST 路由 |

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
| **State Recognition Accuracy** | >95% | 自动化测试覆盖 |
| **Workflow Completion Rate** | >90% | 无人工介入的完成比例 |
| **Human Override Frequency** | <10% | 总流程数中人工接管比例 |
| **Reviewer Average Response Time** | <5min | 从消息发送到响应 |
| **False Positive Alerts** | <5% | 不实警告占总警告比 |

### 8.2 用户 KPI

| KPI | Target | 说明 |
|-----|--------|------|
| **Code Review Turnaround Time** | 从 2h 降至 15min | 自动化评审的加速 |
| **Multi-Reviewer Consensus Time** | 从 3h 降至 8min | 并行评审 vs 串行 |
| **Developer Cognitive Load** | 从 5 reviewer emails 降至 1 dashboard | 信息整合 |

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
- [ ] **方案评审**：与 Anthropic、ByteDance（Codex/Kimi）接洽，确认 API 承诺
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
- v1.0 (Original): 高阶架构设计
- v2.0 (This): 规范化流程 + 标准输出物 + 改进状态识别
