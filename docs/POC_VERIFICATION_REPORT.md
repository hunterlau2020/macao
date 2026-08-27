# MACAO PoC 三假设验证与第一阶段受控联调技术报告 (PoC Verification Report)

- **日期**：2026-08-27
- **验证版本**：Phase 0 / Phase 1 核心框架实现与第一阶段受控实机联调
- **测试结果**：**33 / 33 测试用例全部 PASS (100%)**
- **验证范围**：物理契约产物规范、共识多数仲裁算法、单进程事件循环与 Worktree 隔离机制、配置装配与消息广播独立投递、4 款真实 AI CLI（Claude Code / Codex / OpenCode / AGY）PTY 启停与进程树安全回收。

---

## 一、验证假设与实测结论

| 假设编号 | 核心假设内容 | 验证方法与测试套件 | 验证结论 |
|---|---|---|---|
| **假设 1** | **物理契约文件（`.dev.yml`, `.review.yml`, `vote_result.json`）可作为跨 Agent、跨轮次与崩溃恢复的唯一第一真理源** | `test_schema.py`、`test_state_store.py`、`test_reconcile_crash.py` | **✅ VERIFIED**<br>所有产物均严格符合 Draft-07 Schema 校验；SQLite 仅作为加速索引，崩溃后可完全基于磁盘物理产物 100% 恢复真实业务状态。 |
| **假设 2** | **2/3 多数仲裁算法配合法定人数 `ceil(2N/3)` 能有效解决多 Reviewer 决策、死锁与弃权，并安全触发人工接管** | `test_consensus.py`、`test_orchestrator_sim.py` | **✅ VERIFIED**<br>完整覆盖 2 人及 3 人评审场景下的全票通过、2/3 赞成、2/3 反对、1:1 平票死锁、弃权降级与评审人去重；死锁时严格 HOLD 且不伪写错误终局。 |
| **假设 3** | **单进程主事件循环（Single-process Event Loop）结合 Git Worktree 物理隔离与 AEP 消息队列，足以稳定驱动 10 态 FSM 全生命周期流转** | `test_fsm.py`、`test_msg_bus.py`、`test_orchestrator_sim.py`、`test_config.py` | **✅ VERIFIED**<br>通过 `MockAgentAdapter` 成功仿真 S1（Happy Path 到 Merge）、S2（多轮返工推进）、S3（死锁人工接管）、S6（任务取消）及异常回退，转移表白名单强制生效，Reviewer 专属 Worktree 路径隔离 fail-closed，配置组装根注入与多播消息独立 ACK 闭环。 |
| **实机验证** | **真实 AI CLI 进程生命周期与 PTY 交互、ANSI 码流捕获与进程树强杀安全回收** | `test_integ_harness.py`、`macao test-clis` | **✅ VERIFIED**<br>在 Linux 环境下对宿主真实安装的 Claude Code (`claude`)、Codex (`codex`)、OpenCode (`opencode`)、Google Antigravity (`agy`) 逐一验证 PTY 进程拉起、日志清洗与会话强杀，4/4 真实 CLI 均在 <1s 内完成启动并干净退出，实现 0 孤儿/0 僵尸进程残留。 |

---

## 二、第一阶段真实 CLI PTY 受控联调实机报告

```text
                     MACAO Real CLI PTY Integration Report                      
┏━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃           ┃           ┃ PTY      ┃ ANSI      ┃ Clean    ┃          ┃         ┃
┃ Agent CLI ┃ Version   ┃ Spawn    ┃ Strip     ┃ Kill     ┃ Duration ┃ Verdict ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ claude    │ 2.1.247   │ ✓ YES    │ ✓ YES     │ ✓ DEAD   │ 0.11s    │ PASS    │
│           │ (Claude   │          │           │ (0       │          │         │
│           │ Code)     │          │           │ Zombie)  │          │         │
│ codex     │ 2.1.0     │ ✓ YES    │ ✓ YES     │ ✓ DEAD   │ 0.21s    │ PASS    │
│           │           │          │           │ (0       │          │         │
│           │           │          │           │ Zombie)  │          │         │
│ opencode  │ 1.18.23   │ ✓ YES    │ ✓ YES     │ ✓ DEAD   │ 0.91s    │ PASS    │
│           │           │          │           │ (0       │          │         │
│           │           │          │           │ Zombie)  │          │         │
│ agy       │ 1.1.22    │ ✓ YES    │ ✓ YES     │ ✓ DEAD   │ 0.21s    │ PASS    │
│           │           │          │           │ (0       │          │         │
│           │           │          │           │ Zombie)  │          │         │
└───────────┴───────────┴──────────┴───────────┴──────────┴──────────┴─────────┘
```
