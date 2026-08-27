# MACAO 第一/二阶段受控实机联调与架构装配 独立审批评审申请

> **申请日期**：2026-08-28  
> **申请人**：MACAO 核心研发与实机联调小组  
> **待审对象**：自架构技术框架评审快照（commit `aa173d8`）以来的架构装配整改、4 款真实 AI CLI 适配器矩阵、第一阶段受控联调 Harness、第二阶段端到端微任务协同闭环与全套自动化测试套件  
> **涉及 commit 范围**：`aa173d8` .. `906b17e`  
> **目标等级**：**L3 INTEGRATED / PG-2 门禁准入**（在已达标的 L2 SPEC-CODE-ALIGNED / PG-1 基础上，达成真实 CLI PTY 进程启停、ANSI 清洗回收与微型任务端到端协同闭环）  
> **上位准则**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) (v2.3.1)、[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) 与 [`docs/EXPERT_QUALITY.md`](../EXPERT_QUALITY.md)

---

## 一、本次申请背景与定级目标

在上一轮四方专家（zcode / claude / codex / qwen）的深度架构评审中，MACAO 的核心领域内核（FSM 转移表白名单、2/3 多数仲裁、Deadlock 严格 HOLD 不写盘、Reviewer 去重、Worktree 强制隔离注入与 Fail-closed、SQLite 连接池管理）已获得一致认可。同时，专家团队提出了**“配置单一事实源注入、类型模型收敛、消息总线多播独立 ACK、只读命令去副作用以及国产/生态多模型适配”**等建设性整改意见。

研发团队在此基础上完成了**架构装配的系统性重构**，并遵照严格安全约束（沙箱隔离、超时熔断、进程树强杀、零孤儿残留），成功推进并完成了**第一阶段真实 CLI PTY 生命周期联调**与**第二阶段端到端微任务协同流转闭环**。

现正式向四位独立评审专家（**zcode**、**claude**、**codex**、**qwen**）提请 **L3 INTEGRATED / PG-2 门禁准入独立评审**。

---

## 二、本次评审交付物与核心变更清单

自 commit `aa173d8` 以来，本次提交共交付以下四大核心子系统：

### 1. 架构装配与配置单一事实源接入 (Architecture Assembly & Single Truth)
- **配置系统 100% 对齐 Schema** ([`src/macao/core/config.py`](../../src/macao/core/config.py), [`src/macao/cli/main.py`](../../src/macao/cli/main.py))：
  - 重构 `macao init` 模板与 `macao.yaml`，严格符合 [`docs/schemas/macao_config.schema.json`](../schemas/macao_config.schema.json)（`project`, `team`, `policy`, `merge` 顶层结构）；
  - `ConfigManager` 属性精准对齐 Schema 路径（`require_human_signoff`, `auto_rebase_disabled`, `max_rework_rounds`, `min_effective_votes`, `ci_gate_command`）；
  - CLI 组装根（Composition Root）统一通过 `get_orchestrator()` 注入配置字典，彻底消除硬编码默认值。
- **DTO 领域模型唯一收敛** ([`src/macao/core/types.py`](../../src/macao/core/types.py), [`src/macao/adapter/base.py`](../../src/macao/adapter/base.py))：
  - 统一收敛 `PreflightCheckResult` 与 `CapabilityManifest`，删除了 `adapter/base.py` 中的重复定义，消除了各 Adapter 构造时的 `TypeError`；
  - 完善 `PTYSession` 接口（补齐 `write_input()` 与 `get_clean_logs()`）。
- **消息总线广播多播独立 ACK 机制** ([`src/macao/storage/db.py`](../../src/macao/storage/db.py), [`src/macao/msg/bus.py`](../../src/macao/msg/bus.py))：
  - 引入 `message_deliveries(delivery_id, message_id, recipient, status, ...)` 独立投递表；
  - 向多个 Reviewer 广播时拆分为独立投递项，单个 Reviewer 的 ACK 绝不遮蔽其他 Reviewer 接收消息。
- **CLI 只读观测命令去副作用** ([`src/macao/cli/main.py`](../../src/macao/cli/main.py))：
  - `macao status` 与 `macao doctor` 保持严格只读幂等，移除自动触发 `reconcile`；
  - 新增显式 `macao task recover` 命令用于状态与物理产物对齐。

---

### 2. 真实 AI CLI 适配器矩阵与多模型生态扩展
- **OpenCode 适配器** ([`src/macao/adapter/opencode.py`](../../src/macao/adapter/opencode.py))：
  - 替换原 Kimi 占位，接入系统已安装的 `opencode` CLI（v1.18.23，路径 `/home/debian/.opencode/bin/opencode`）；
  - 支持 Worktree 隔离检出与非交互审查模式。
- **Google Antigravity 适配器** ([`src/macao/adapter/antigravity.py`](../../src/macao/adapter/antigravity.py))：
  - 接入 Google Antigravity CLI `agy`（v1.1.22，路径 `/home/debian/.local/bin/agy`）；
  - 具备执行（Executor）与审查（Reviewer）双重能力。
- **完整真实 CLI 队伍编排** ([`macao.yaml`](../../macao.yaml))：
  - **Executor**：`claude-code` (`claude` v2.1.247)
  - **Reviewer 1**：`codex` (`codex` v2.1.0)
  - **Reviewer 2**：`opencode` (`opencode` v1.18.23)
  - **Reviewer 3**：`antigravity` (`agy` v1.1.22)
  - 法定人数：$\lceil 2 \times 3 / 3 \rceil = 2$ 票（2/3 多数仲裁规则）。

---

### 3. 第一阶段受控实机联调 (Phase 1 PTY Lifecycle & Clean Recycling)
- **联调方案**：[`docs/CONTROLLED_INTEGRATION_PLAN.md`](../CONTROLLED_INTEGRATION_PLAN.md)
- **集成 Harness**：[`src/macao/adapter/integ_harness.py`](../../src/macao/adapter/integ_harness.py)
- **CLI 联调命令**：`macao test-clis`（支持 `--cli all` 或 `--cli <claude|codex|opencode|agy>`）
- **实机机验结论**：在宿主 Linux 系统下对 4 款真实 CLI 逐一验证 PTY 拉起、ANSI 实时清洗与 `killpg(SIGTERM)` $\to$ `SIGKILL` 强杀机制；4/4 真实 CLI 均在 <1s 内完成启动并干净退出，`os.kill(pid, 0)` 确认 **0 孤儿进程、0 僵尸进程残留**。

---

### 4. 第二阶段受控端到端协同闭环 (Phase 2 Micro-Task Collaboration)
- **联调方案**：[`docs/CONTROLLED_E2E_INTEGRATION_PHASE2.md`](../CONTROLLED_E2E_INTEGRATION_PHASE2.md)
- **自动化 Runner**：[`src/macao/workflow/e2e_runner.py`](../../src/macao/workflow/e2e_runner.py)
- **CLI 闭环命令**：`macao e2e-run`
- **全链路流转验证**：
  1. `Task Start`：创建任务进入 `CODING`；
  2. `Executor Commit`：在特性分支实现代码与测试，提交 commit 产出 `checkpoint_ref`，生成合法 `.dev.yml`；
  3. `Checkpoint Check`：校验通过流转至 `READY_FOR_REVIEW`；
  4. `Worktree Dispatch`：为 3 位 Reviewer 分别创建专属物理 Worktree，分发 `REVIEW_REQUEST` 流转至 `WAITING_REVIEW`；
  5. `Reviews Generation`：3 方在各自 Worktree 产出合法 `.review.yml`（全票 `YES_APPROVE`）；
  6. `Consensus Evaluation`：计算 2/3 多数仲裁通过，流转至 `MERGING` 并生成权威 `vote_result.json`；
  7. `Fast-forward Merge`：执行快速合并，校验目标分支最新 HEAD commit **100% 精确等于 `checkpoint_ref`**；
  8. `Archive & Done`：产物非覆盖追加归档至 `.macao/archive/`，任务状态机安全流转至 `DONE`。

---

## 三、机验证据链与自检清单 (Verification Checklist)

### 1. 全量自动化测试用例（34/34 PASS）
```text
PYTHONPATH=src python3 -m unittest discover tests -v
----------------------------------------------------------------------
Ran 34 tests in 7.639s — OK (34/34 PASS, 100%)
```

### 2. 环境真实探针检测 (`macao preflight`)
```text
                       MACAO Preflight Environment Report                       
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ CLI / Component           ┃ Installed ┃ Version         ┃ Mode      ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ Environment: Git          │ YES       │ system          │ full      │ OK     │
│ Environment: SQLite (WAL) │ YES       │ 3.45.1          │ full      │ OK     │
│ claude-code               │ YES       │ 2.1.247 (Claude │ full      │ OK     │
│                           │           │ Code)           │           │        │
│ codex                     │ YES       │ 2.1.0           │ sandboxed │ OK     │
│ opencode                  │ YES       │ 1.18.23         │ sandboxed │ OK     │
│ agy (Google Antigravity)  │ YES       │ 1.1.22          │ sandboxed │ OK     │
│ kimi                      │ NO        │ N/A             │ N/A       │ FAIL   │
│ mock-cli                  │ YES       │ 1.0.0-mock      │ sandboxed │ OK     │
└───────────────────────────┴───────────┴─────────────────┴───────────┴────────┘
```

### 3. 第一阶段真实 CLI PTY 进程生命周期联调 (`macao test-clis`)
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

### 4. 第二阶段端到端微任务协同实机闭环 (`macao e2e-run`)
```text
              MACAO Phase 2 E2E Micro-Task Report (task-bb795860)               
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Phase / Step             ┃ Details                         ┃ Status / Result ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ 1. Task Start            │ state=CODING,                   │ OK              │
│                          │ task_id=task-bb795860           │                 │
│ 2. Checkpoint Validation │ state=READY_FOR_REVIEW,         │ OK              │
│                          │ checkpoint_ref=b239103c         │                 │
│ 3. Worktree Dispatch     │ state=WAITING_REVIEW,           │ OK              │
│                          │ reviewers_count=3,              │                 │
│                          │ reviewers=['codex', 'opencode', │                 │
│                          │ 'antigravity']                  │                 │
│ 4. Consensus Evaluation  │ decision=APPROVED,              │ OK              │
│                          │ state=MERGING, votes_yes=3,     │                 │
│                          │ effective_votes=3               │                 │
│ 5. Fast-Forward Merge    │ state=DONE, message=Merge       │ OK              │
│                          │ pipeline completed successfully │                 │
│ 5. Merge Equality        │ Target HEAD (b239103c) ==       │ 100% MATCH      │
│                          │ Checkpoint (b239103c)           │                 │
│ 6. Physical Archive      │ Archived files persisted        │ PERSISTED       │
│ 7. Final FSM State       │ Final task state: DONE          │ DONE            │
└──────────────────────────┴─────────────────────────────────┴─────────────────┘
```

### 5. 代码洁净度机验
- `git diff --check`：**0 errors (clean)**
- 全库无未定义变量、无循环依赖、无跨平台死导入。

---

## 四、待专家独立评审核心要点提请

提请四位独立评审专家就以下核心维度进行独立复核与定级评审：

1. **真实 CLI 适配器与 PTY 生命周期**：
   - 4 款真实 CLI（`claude-code`, `codex`, `opencode`, `agy`）的 PTY 进程组隔离与 `SIGTERM/SIGKILL` 强杀回收机制是否严密可靠？
2. **架构装配与单一事实源**：
   - `macao init` 模板、`ConfigManager`、`Orchestrator` 组装根依赖注入与 DTO 类型收敛是否彻底解决了此前评审指出的配置断层？
3. **消息总线独立投递表**：
   - `message_deliveries` 的设计是否彻底解决了广播多播场景下的独立 ACK 语义？
4. **端到端微任务协同与合并安全**：
   - Phase 2 端到端协同流程中的三方 Worktree 物理隔离、2/3 多数仲裁计算与 Fast-forward 合并 HEAD 强一致性校验是否达到生产就绪标准？
5. **门禁定级结论判定**：
   - 综合上述交付物与实测证据，是否准予评定为 **L3 INTEGRATED / PG-2 门禁准入**？

---
