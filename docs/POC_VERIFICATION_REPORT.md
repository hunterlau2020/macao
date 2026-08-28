# MACAO PoC 三假设验证与第一/二阶段受控联调技术报告 (PoC Verification Report)

- **日期**：2026-08-28（完成 4 位专家评审意见全面整改，38/38 测试全绿通过）
- **验证版本**：Phase 0 / Phase 1 核心框架实现、Phase 1 PTY 实机联调、Phase 2 端到端微任务协同与 P0/P1 闭环整改
- **测试结果**：**38 / 38 测试用例全部 PASS (100%)**
- **验证范围**：物理契约产物规范、共识多数仲裁算法、单进程事件循环与 Worktree 隔离机制、配置装配与单一真理源贯穿、消息广播独立投递表、4 款真实 AI CLI（Claude Code / Codex / OpenCode / AGY）PTY 启停与进程树安全回收、端到端微任务全生命周期协同仿真闭环。

---

## 一、验证假设与实测结论

| 假设编号 | 核心假设内容 | 验证方法与测试套件 | 验证结论 |
|---|---|---|---|
| **假设 1** | **物理契约文件（`.dev.yml`, `.review.yml`, `vote_result.json`）可作为跨 Agent、跨轮次与崩溃恢复的唯一第一真理源** | `test_schema.py`、`test_state_store.py`、`test_reconcile_crash.py` | **✅ VERIFIED**<br>所有产物均严格符合 Draft-07 Schema 校验；SQLite 仅作为加速索引，崩溃后可完全基于磁盘物理产物 100% 恢复真实业务状态。 |
| **假设 2** | **2/3 多数仲裁算法配合法定人数 `ceil(2N/3)` 能有效解决多 Reviewer 决策、死锁与弃权，并安全触发人工接管** | `test_consensus.py`、`test_orchestrator_sim.py` | **✅ VERIFIED**<br>完整覆盖 2 人及 3 人评审场景下的全票通过、2/3 赞成、2/3 反对、1:1 平票死锁、弃权降级与评审人去重；死锁时严格 HOLD 且不伪写错误终局。 |
| **假设 3** | **单进程主调度器结合 Git Worktree 物理路径隔离与 AEP 消息队列，足以稳定驱动 10 态 FSM 全生命周期流转** | `test_fsm.py`、`test_msg_bus.py`、`test_orchestrator_sim.py`、`test_config.py`、`test_p0_p1_rectification.py` | **✅ VERIFIED**<br>通过 `MockAgentAdapter` 成功仿真 S1（Happy Path 到 Merge）、S2（多轮返工推进）、S3（死锁人工接管）、S6（任务取消）及异常回退，转移表白名单强制生效，Reviewer 专属 Worktree 路径隔离 fail-closed（非 git 目录直接拒绝），配置组装根注入与多播消息独立投递表闭环。 |
| **Phase 1 实机** | **真实 AI CLI 进程生命周期与 PTY 交互、ANSI 码流捕获与进程树强杀安全回收** | `test_integ_harness.py`、`macao test-clis` | **✅ VERIFIED (POSIX)**<br>在 Linux 环境下对宿主真实安装的 Claude Code (`claude` 2.1.250)、Codex (`codex` 2.1.0)、OpenCode (`opencode` 1.18.23)、Google Antigravity (`agy` 1.1.22) 逐一验证 PTY 进程拉起、日志清洗与进程组强杀；4/4 真实 CLI 均在 <1s 内完成启动并干净退出，`os.kill(pid, 0)` 确认 0 孤儿/0 僵尸进程残留；Windows 环境优雅跳过。 |
| **Phase 2 协同** | **端到端微型任务协同流转（Task Start -> Coding Checkpoint -> 3-Reviewer Worktrees -> 2/3 仲裁 -> Fast-forward Merge -> DONE）** | `test_e2e_phase2.py`、`test_p0_p1_rectification.py`、`macao e2e-run` | **✅ VERIFIED (Simulated Pipeline)**<br>全自动完成微型算术模块代码开发提交、3 方专属 Worktree 审查分发、2/3 多数票裁决（votes_yes=3, effective_votes=3）、快进合并与目标分支 SHA 硬匹配校验（100% Match），产物非覆盖追加归档至 `.macao/archive/<checkpoint_ref>/r1/`（共 5 份文件：.dev.yml, vote_result.json, 3x review.yml）。 |

---

## 二、Phase 2 端到端微型任务协同实机报告

```text
              MACAO Phase 2 E2E Micro-Task Report (task-21a476b0)               
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Phase / Step             ┃ Details                         ┃ Status / Result ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ 1. Task Start            │ state=CODING,                   │ OK              │
│                          │ task_id=task-21a476b0           │                 │
│ 2. Checkpoint Validation │ state=READY_FOR_REVIEW,         │ OK              │
│                          │ checkpoint_ref=35320b3b         │                 │
│ 3. Worktree Dispatch     │ state=WAITING_REVIEW,           │ OK              │
│                          │ reviewers_count=3,              │                 │
│                          │ reviewers=['codex', 'opencode', │                 │
│                          │ 'antigravity']                  │                 │
│ 4. Consensus Evaluation  │ decision=APPROVED,              │ OK              │
│                          │ state=MERGING, votes_yes=3,     │                 │
│                          │ effective_votes=3,              │                 │
│                          │ confidence=1.0                  │                 │
│ 5. Fast-Forward Merge    │ state=DONE, message=Merge       │ OK              │
│                          │ pipeline completed successfully │                 │
│ 6. Physical Archive      │ Archived 5 files:               │ PERSISTED       │
│                          │ opencode.review.yml,            │                 │
│                          │ codex.review.yml,               │                 │
│                          │ antigravity.review.yml,         │                 │
│                          │ vote_result.json, .dev.yml      │                 │
│ 7. Final FSM State       │ Final task state: DONE          │ DONE            │
└──────────────────────────┴─────────────────────────────────┴─────────────────┘
```
