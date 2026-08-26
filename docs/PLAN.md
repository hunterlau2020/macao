# MACAO 详细技术开发计划 (PLAN.md)

> **版本**：v1.0  
> **基准**：基于 [`docs/MACAO_PRD_v2.md`](MACAO_PRD_v2.md)（权威 PRD v2.3）、[`docs/TECH_INTRUDUCE.md`](TECH_INTRUDUCE.md) 与 [`docs/ROADMAP.md`](ROADMAP.md)  
> **周期**：8 周（4 个两周迭代阶段）实现 MVP 交付，后续平滑演进至 v1.1+。

---

## 🗺️ 总体研发计划全景 (Timeline & Milestones)

```text
2026 Q3 / Q4 ─── 8 周 MVP 研发周期
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 0 (Week 1-2): 协议验证与适配器探针 (PoC & Adapter Spikes)                           │
│ ├─ Claude Code / Codex / Kimi 真实 CLI 启停与 PTY 交互验证                                │
│ ├─ .dev.yml / .review.yml 物理产物端到端读写验证                                        │
│ └─ 达成里程碑 M0: PoC 三大核心假设验证闭环                                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 1 (Week 3-4): 核心状态机与共识仲裁引擎 (Core FSM & Consensus Engine)              │
│ ├─ 10 状态有限状态机（E1~E10 转移表）与状态作用域产物读取                                │
│ ├─ 2/3 多数 + 2 票法定人数仲裁引擎与终局 vote_result.json 生成                          │
│ ├─ SQLite State Store 数据持久化与崩溃自动 Reconcile 恢复                                │
│ └─ 达成里程碑 M1: 单机开发-评审-仲裁 Happy Path (S1) 自动化流转                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 2 (Week 5-6): 合并流水线、安全沙箱与容灾治理 (Merge Pipeline & Resilience)        │
│ ├─ MERGING 中间态流水线（Rebase 检查、Fast-forward 合并、CI Gate 门禁）                  │
│ ├─ Reviewer 独立 Git Worktree 沙箱创建/生命周期管理与销毁                                │
│ ├─ Consensus Deadlock 人工接管触发（10 分钟时限）与 E7/E9/E10 落地                       │
│ ├─ agmsg 消息重试与死信队列（DLQ）治理                                                  │
│ └─ 达成里程碑 M2: 返工循环 (S2) 与死锁接管 (S3/S6) 异常分支全闭环                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase 3 (Week 7-8): CLI 生产就绪、全场景演练与 MVP 验收 (UX, E2E & PG-3 Gate)           │
│ ├─ Click + Rich + prompt_toolkit 完整交互终端集成                                      │
│ ├─ 六场景（S1~S6）端到端集成测试演练与 80%+ 自动化测试覆盖                              │
│ ├─ 成本计量（Usage Meter）与日志脱敏审计就绪                                            │
│ └─ 达成里程碑 M3: 满足全部 MVP 成功指标，通过 PG-3 门禁正式交付                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 阶段一：Phase 0 (Week 1–2) 协议验证与适配器探针 (PoC & Adapter Spikes)

### 1. 核心目标
验证跨厂商 CLI 智能体在受控 PTY/Hook 环境下的真实通信能力，证伪或闭环 PoC 三大关键假设：
1. **假设 1**：各 CLI 能够可靠受控启停，无不可控卡死；
2. **假设 2**：显式产物文件（YAML/JSON）能 100% 准确跨 CLI 读取解析；
3. **假设 3**：Reviewer 能够在独立 git worktree 中安全执行 review 任务而不污染主工作区。

### 2. 详细任务分解

| 任务编号 | 任务名称 | 负责模块 | 详细说明与验收要求 |
|---|---|---|---|
| **Task 0.1** | CLI PTY 适配器联调 | `src/macao/adapter/` | 针对 `Claude Code`（Full 模式 Hook/PTY）、`Codex`（Sandboxed 模式 PTY）、`Kimi`（非交互模式 PTY），验证任务提示词注入（`inject_task`）与日志输出捕获。 |
| **Task 0.2** | 物理产物契约读写实测 | `src/macao/core/schema.py` | 验证 Executor 自动输出 `.macao/.dev.yml` 并通过 `dev_manifest.schema.json` 强校验；验证 Reviewer 解析 Context 并输出 `.macao/.reviews/<id>.review.yml`。 |
| **Task 0.3** | PTY 进程组生命周期管理 | `src/macao/adapter/pty_session.py` | 实现基于 `os.killpg` 的深层子进程树强杀机制，确保 CLI 异常或超时退出无孤儿孙进程残留。 |
| **Task 0.4** | Git Worktree 物理隔离实测 | `src/macao/utils/git_utils.py` | 验证为 Reviewer 在 `.macao/worktrees/<id>/` 动态创建独立 worktree 并在评审后可靠清理，验证其无法修改主仓库工作区。 |

### 3. 里程碑交付物 (Milestone M0)
- ✅ 产出《PoC 三假设验证技术报告》（CLI 启停可靠性、产物跨模型解析率 100%、Worktree 隔离零污染）；
- ✅ 3 个 CLI Adapter 均能通过 `macao preflight` 真实探针检测。

---

## 阶段二：Phase 1 (Week 3–4) 核心状态机与共识仲裁引擎 (Core FSM & Consensus Engine)

### 1. 核心目标
构建严密、不可篡改的 10 状态有限状态机（FSM）与 2/3 多数仲裁算法，打通从任务受理到共识达成的单机自动化闭环。

### 2. 详细任务分解

| 任务编号 | 任务名称 | 负责模块 | 详细说明与验收要求 |
|---|---|---|---|
| **Task 1.1** | 10 状态 FSM 驱动器与作用域读取 | `src/macao/workflow/` | 实现 PRD §3.2 三层识别机制（Layer 1 显式产物优先，Layer 2 行为推断仅日志，Layer 3 诊断置信度）；实现状态作用域产物读取（`CODING/REWORK` 只读 `.dev.yml`，`WAITING_REVIEW` 只读本轮 `.review.yml`，`CONSENSUS_CHECK` 只读 `vote_result.json`），杜绝跨轮次旧产物遮蔽。 |
| **Task 1.2** | 2/3 多数 + 2 票法定人数仲裁引擎 | `src/macao/consensus/` | 实现 `ConsensusEngine.evaluate`：精准处理 2 人/3 人配置下的全同意（APPROVED）、全反对（REWORK_REQUIRED）、1:1 僵局（DEADLOCK）与弃权降级；实现 `VoteAggregator` 收集 `.review.yml` 并生成符合 `vote_result.schema.json` 的终局落盘记录（含输入文件 SHA-256 与审计链）。 |
| **Task 1.3** | SQLite State Store 与真理源 Reconcile | `src/macao/storage/` | 完整实现 tasks, artifacts, audit_events, overrides 数据表增删改查；实现进程崩溃拉起后的 `StateReconciler`（物理产物与 SQLite 状态双向对齐）。 |
| **Task 1.4** | 产物生命周期与归档管理 | `src/macao/workflow/fsm.py` | 实现 E2 触发时的 `.dev.yml` 归档到 `.macao/archive/<ref>/r<round>/`；实现 E4/E5 触发时的 `.review.yml` 与 `vote_result.json` 归档。 |

### 3. 里程碑交付物 (Milestone M1)
- ✅ 单机首次开发双批准 Happy Path (S1) 自动化运行通过；
- ✅ 状态转移全量记录于 SQLite 审计日志表与 Git 提交中。

---

## 阶段三：Phase 2 (Week 5–6) 合并流水线、安全沙箱与容灾治理 (Merge Pipeline & Resilience)

### 1. 核心目标
实现生产级代码合并控制流水线、完善多轮返工迭代与死锁人工接管机制，构建健壮的容灾与安全屏障。

### 2. 详细任务分解

| 任务编号 | 任务名称 | 负责模块 | 详细说明与验收要求 |
|---|---|---|---|
| **Task 2.1** | MERGING 中间态流水线与 Merge Controller | `src/macao/merge/` | 实现目标分支检出、Fast-forward 合并检查；实现外部 CI Gate 命令门禁执行（CI 失败触发 E4b 回退至 REWORK，round+1）；实现人工签字校验（`require_human_signoff`）与合并完成通告（`MERGE_COMPLETED`）。 |
| **Task 2.2** | 多轮返工流转控制 (Rework Loop) | `src/macao/workflow/` | 实现 `REWORK_REQUEST` 增量下发（携带上一轮 `issues_to_fix` 清单与 `round+1` 标记）；控制返工次数上限（`max_rework_rounds`），超出上限强制触发人工接管。 |
| **Task 2.3** | Consensus Deadlock 与人工接管子系统 | `src/macao/cli/` & `workflow` | 票数收齐算出死锁时，精准触发 10 分钟超时的人工接管通知；实现 `macao override resolve --choice <APPROVED|REWORK|RETRY_REVIEW|CANCEL>`，将裁决结果落盘为带 `resolution: human_override` 的终局 `vote_result.json` 并分别驱动 E4/E5/E9/E10 转移。 |
| **Task 2.4** | agmsg 消息队列容灾与 DLQ 治理 | `src/macao/msg/` | 实现消息超时重试（最大重试 3 次）、死信转移（`dead_letter_queue` 表）与手动重放机制。 |
| **Task 2.5** | 输出脱敏与 ANSI 自愈 | `src/macao/utils/ansi.py` | 实现终端 ANSI 逃逸码清洗与 API Key/敏感 Token 自动掩码过滤。 |

### 3. 里程碑交付物 (Milestone M2)
- ✅ 返工多轮迭代 (S5)、CI Gate 失败回退 (S2)、1:1 平票死锁人工裁决 (S3) 及重试取消 (S6) 全部实测通过；
- ✅ 异常分支 100% 覆盖，无不可控挂起。

---

## 阶段四：Phase 3 (Week 7–8) CLI 生产就绪、全场景演练与 MVP 验收 (UX, E2E & PG-3 Gate)

### 1. 核心目标
完成 CLI 人机交互体验打磨、六大典型业务场景端到端实操演练，达成全部 MVP 验收标准并正式发布。

### 2. 详细任务分解

| 任务编号 | 任务名称 | 负责模块 | 详细说明与验收要求 |
|---|---|---|---|
| **Task 3.1** | Click + Rich + prompt_toolkit 完整交互集成 | `src/macao/cli/` | 实现高颜值彩色状态看板（`macao status` 实时渲染 FSM 状态、Checkpoint、当前轮次与产物清单）；实现交互式任务创建引导（`macao task create` 交互向导）；实现 Deadlock 交互式光标选择弹窗（`prompt_toolkit` 上下键选择裁定动作）。 |
| **Task 3.2** | 成本与 Token 计量统计 (Usage Meter) | `src/macao/cli/` & `storage` | 统计各 Phase（开发/评审）各 CLI 消耗的 Token 用量与估算 USD 成本，支持 `macao usage` 查询与预算熔断。 |
| **Task 3.3** | 六大业务场景端到端自动化验收套件 (E2E SIM Suite) | `tests/` | 覆盖 S1（双批准）、S2（CI 失败回退）、S3（1:1 平票死锁）、S4（超时弃权）、S5（达到最大返工轮次）、S6（重试与手动取消）。 |
| **Task 3.4** | 文档与发布交付 | `docs/` | 编写《MACAO 用户操作指南》与《CLI Adapter 开发者接入规范》；依据 `docs/MACAO_REVIEW_GUIDELINES.md` 申请并通过 **PG-3 / L4 门禁**。 |

### 3. 里程碑交付物 (Milestone M3)
- ✅ 自动化测试覆盖率 ≥ 80%，六大场景 100% 自动化回归通过；
- ✅ MACAO v0.1.0-mvp 正式打包发布。

---

## 🔮 未来版本演进路线 (Post-MVP Roadmap: v1.1 ~ v2.0)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ v1.1 版本 (生态扩展与全屏看板)                                         │
│ ├─ 异构第 3 Reviewer 支持 (集成 Gemini CLI，形成 Claude+Codex+Gemini)   │
│ ├─ 全屏常驻 TUI 作战大屏 (基于 Textual 实现 macao dashboard / macao ui)│
│ └─ 代码托管平台联动 (自动创建 GitHub PR / GitLab MR 与 Webhook 回调)     │
├────────────────────────────────────────────────────────────────────────┤
│ v1.2 版本 (分布式与团队协作)                                           │
│ ├─ 跨机/远程 Agent 支持 (基于轻量 SSH Gateway 实现多机器部署)           │
│ ├─ 多任务并行编排与 Agent 资源池化调度 (Worker Pool)                    │
│ └─ 评审专家盲审评分与审查质量自动评估 (Reviewer Quality Ranking)         │
├────────────────────────────────────────────────────────────────────────┤
│ v2.0 版本 (自主进化与团队智能)                                         │
│ ├─ 历史代码缺陷库记忆与智能 Review Focus 生成                           │
│ └─ 团队级成本效益分析与自动模型路由选择                                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 质量门禁与研发准则 (Engineering Guidelines)

1. **门禁晋级硬约束**：
   - 每个 Phase 结束前必须经过 `tests/` 自动化测试套件全绿验证；
   - 涉及数据结构或接口变更，必须先修改 `docs/schemas/` 中的 Schema 并跑通正反 fixtures 后方可修改业务代码。
2. **零静默假设原则**：
   - 严禁在无明确显式产物（`.dev.yml` / `.review.yml` / `vote_result.json`）时自动跨状态流转；
   - 任何未识别状态一律保持（HOLD）或进入 `UNKNOWN` 触发人工干预。
3. **代码与测试双轨交付**：
   - 每个核心功能模块必须附带相应的单元测试，保持测试套件始终可一键运行（`PYTHONPATH=src python3 -m unittest discover tests`）。

---
*本文档随项目迭代开发过程滚动更新。*
