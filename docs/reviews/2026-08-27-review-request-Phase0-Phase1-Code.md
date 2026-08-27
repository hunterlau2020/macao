# MACAO Phase 0 / Phase 1 核心代码与测试套件 独立审批评审申请

> **申请日期**：2026-08-27
> **申请人**：技术架构与核心研发团队
> **待审对象**：自 `2026-08-26-review-request-PRD-v2.3.1.md` 之后的所有技术架构设计、核心代码实现与全套自动化测试套件
> **涉及 commit 范围**：`d137a05` .. `435eeea`（涵盖 `d137a05`, `9198d61`, `435eeea`）
> **基准规范**：[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) (权威 PRD v2.3.1)、[`docs/schemas/`](../schemas/) (版本化 Draft-07 Schema 契约) 与 [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)

---

## 一、性质与定级目标

- **评审性质**：**Phase 0 (PoC 框架与适配器) 与 Phase 1 (核心状态机与共识引擎) 代码级定级评审 (L2 SPEC-CODE-ALIGNED)**；
- **目标等级**：**L2 SPEC-CODE-ALIGNED / PG-1 门禁预准入**；
- **安全与环境前置声明（强制合规项）**：
  - 遵照用户指示与安全规范，**未自行启动或执行真实三方 CLI（`claude-code`, `codex`, `kimi`）二进制进行联网交互测试**；
  - 研发阶段通过全新设计的 [`MockAgentAdapter`](../../src/macao/adapter/mock.py) 完成 100% 离线、确定性、高覆盖的单机多 Agent 协同与异常场景仿真；
  - 真实 CLI 适配器代码接口已就绪，已明确登记为**待人工介入监督测试项**。

---

## 二、本次评审涉及的变更全景清单

自 PRD v2.3.1 审批申请（commit `403ddc7`）以来，本次提交共完成以下三大类交付物：

### 1. 技术设计与规划文档体系 (`docs/`)
- [`docs/TECH_INTRUDUCE.md`](../TECH_INTRUDUCE.md)：系统总体架构设计、技术组件选型落地矩阵、增强型 CLI（Click + Rich + prompt_toolkit）与全屏 TUI 的全方位对比剖析与演进路径；
- [`docs/PLAN.md`](../PLAN.md) (升级至 v1.1)：8 周 MVP 研发详细计划、Phase 0~3 任务分解（WBS）以及当前 Phase 0/1 的完成状态；
- [`docs/ROADMAP.md`](../ROADMAP.md) (升级至 v1.1)：中长期技术演进路线（MVP -> v1.1 -> v1.2 -> v2.0）；
- [`docs/EXPERT_QUALITY.md`](../EXPERT_QUALITY.md)：四轮 16 份评审报告的专家质量评分与排班规则；
- [`docs/README.md`](../README.md)：文档中心全景索引导航。

### 2. 核心 Python 技术框架实现 (`src/macao/`，共 18 个模块)
- **核心契约层 (`core/`)**：
  - [`types.py`](../../src/macao/core/types.py)：10 状态 FSM 枚举、7 类 AEP/1.0 消息类型、三值投票与四值终局决策枚举；
  - [`schema.py`](../../src/macao/core/schema.py)：严格绑定 `docs/schemas/` 的 Draft-07 强校验器；
  - [`config.py`](../../src/macao/core/config.py)：`macao.yaml` 加载器与最低法定人数（`minimum_quorum`）推导。
- **持久化存储层 (`storage/`)**：
  - [`db.py`](../../src/macao/storage/db.py)：SQLite WAL 模式连接池管理与 5 张核心业务表 DDL（tasks, artifacts, audit_events, overrides, dead_letter_queue）；
  - [`store.py`](../../src/macao/storage/store.py)：任务生命周期、产物登记、审计日志、人工接管记录与死信队列 CRUD；
  - [`reconcile.py`](../../src/macao/storage/reconcile.py)：PRD §11.5 崩溃恢复协议，以物理磁盘产物为第一真理源双向对齐数据库。
- **消息总线层 (`msg/`)**：
  - [`envelope.py`](../../src/macao/msg/envelope.py)：AEP/1.0 统一信封封装与解包；
  - [`bus.py`](../../src/macao/msg/bus.py)：基于 SQLite 的本地消息队列调度器，支持 Pub/Sub、ACK、TTL 超时与 DLQ 转移。
- **适配器层 (`adapter/`)**：
  - [`base.py`](../../src/macao/adapter/base.py)：`AgentAdapter` 抽象基类与 `CapabilityManifest` 能力清单；
  - [`pty_session.py`](../../src/macao/adapter/pty_session.py)：基于 `pty.openpty()` 的非阻塞读取、ANSI 清洗与基于 `os.killpg` 的深层进程组强杀机制；
  - [`claude.py`](../../src/macao/adapter/claude.py)、[`codex.py`](../../src/macao/adapter/codex.py)、[`kimi.py`](../../src/macao/adapter/kimi.py)：真实 CLI 适配器接口与指令构建；
  - [`mock.py`](../../src/macao/adapter/mock.py)：可编程仿真适配器，用于自动化回归。
- **共识仲裁层 (`consensus/`)**：
  - [`engine.py`](../../src/macao/consensus/engine.py)：PRD §2.3 规定的 `2/3 多数 + 2 票最低法定人数` 确定性仲裁算法；
  - [`vote.py`](../../src/macao/consensus/vote.py)：`.review.yml` 收集、SHA-256 审计链计算与终局 `vote_result.json` 生成。
- **工作流与状态机 (`workflow/`)**：
  - [`state_engine.py`](../../src/macao/workflow/state_engine.py)：PRD §3.2 三层状态识别与状态作用域产物读取（彻底隔离跨轮历史产物）；
  - [`transitions.py`](../../src/macao/workflow/transitions.py)：E1~E10 统一状态转移表合法性判定；
  - [`fsm.py`](../../src/macao/workflow/fsm.py)：10 状态驱动器与产物自动归档流水线（`.macao/archive/<ref>/r<round>/`）；
  - [`orchestrator.py`](../../src/macao/workflow/orchestrator.py)：中央事件调度器，串联 FSM、消息总线、适配器、仲裁引擎与物理沙箱。
- **合并控制器 (`merge/`)**：
  - [`controller.py`](../../src/macao/merge/controller.py)：MERGING 流水线（目标分支检出、Fast-forward 合并、CI Gate 门禁执行与人工签字校验）。
- **基础设施与工具 (`utils/`)**：
  - [`ansi.py`](../../src/macao/utils/ansi.py)：ANSI 逃逸码清洗工具；
  - [`git_utils.py`](../../src/macao/utils/git_utils.py)：Git 操作与 Reviewer 独立 Git Worktree 沙箱管理；
  - [`context_builder.py`](../../src/macao/utils/context_builder.py)：PRD §5.2 权威 `review_context` 结构化构建器。
- **命令行交互入口 (`cli/`)**：
  - [`ui.py`](../../src/macao/cli/ui.py)：Rich 状态看板、彩色表格与诊断面板渲染；
  - [`main.py`](../../src/macao/cli/main.py)：Click 命令集（`preflight`, `init`, `doctor`, `task create`, `status`, `override resolve`, `usage`）。

### 3. 全量自动化测试套件 (`tests/`，9 大测试套件共 22 项测试全绿)
- `tests/test_schema.py`：6 个 Draft-07 JSON Schema 强校验及正反向 fixture 测试；
- `tests/test_context_builder.py`：`ReviewContextBuilder` 最小/全量结构 Schema 校验测试；
- `tests/test_mock_adapter.py`：Mock 适配器能力声明与物理产物生成测试；
- `tests/test_consensus.py`：2 人/3 人配置、弃权降级与死锁裁定算法测试；
- `tests/test_state_store.py`：SQLite 状态持久化、产物登记与审计流测试；
- `tests/test_reconcile_crash.py`：未消费产物与中途崩溃的真理源对齐测试；
- `tests/test_fsm.py`：10 态 FSM 流转与 E1~E10 转移合法性测试；
- `tests/test_msg_bus.py`：AEP 消息发布、订阅、消费与 ACK 测试；
- `tests/test_orchestrator_sim.py`：端到端多 Agent 协作场景仿真：
  - **S1 (Happy Path)**：开发 -> 2 票全批准 -> 自动 MERGING；
  - **S2 (多轮返工循环)**：开发 -> 反对打回 (REWORK, round 2) -> 修复 -> 全批准 -> MERGING；
  - **S3 (1:1 平票死锁 + 人工接管)**：1 赞成 1 反对 -> DEADLOCK -> 人工裁决 APPROVED -> MERGING；
  - **S6 (异常取消)**：任务死锁 -> 人工裁决 CANCEL -> CANCELLED。

---

## 三、代码实现与 PRD v2.3.1 核心契约追溯对照表 (Traceability Matrix)

| PRD 规范章节 / 核心约束 | 对应的代码落点 | 单元/仿真测试落点 | 实现与校验状态 |
|---|---|---|---|
| **PRD §3.1 / 10 状态 FSM** | `src/macao/core/types.py`<br>`src/macao/workflow/fsm.py` | `tests/test_fsm.py` | ✅ **对齐**：完整支持 10 状态（含 `UNKNOWN`, `CANCELLED`），无模糊中间态。 |
| **PRD §3.2 / 三层识别与作用域读取** | `src/macao/workflow/state_engine.py` | `tests/test_fsm.py`<br>`tests/test_orchestrator_sim.py` | ✅ **对齐**：Layer 1 显式产物优先，Layer 2 仅日志，Layer 3 诊断置信度；严格按当前状态过滤作用域产物。 |
| **PRD §3.3 / E1~E10 状态转移表** | `src/macao/workflow/transitions.py` | `tests/test_fsm.py` | ✅ **对齐**：转移表白名单校验，非法前置条件一律拒绝并触发审计。 |
| **PRD §2.3 / 2/3 多数仲裁算法** | `src/macao/consensus/engine.py`<br>`src/macao/consensus/vote.py` | `tests/test_consensus.py` | ✅ **对齐**：公式 $Q=\lceil 2N/3 \rceil$；精准判定 APPROVED, REWORK_REQUIRED, DEADLOCK 与 ABSTAIN 扣除。 |
| **PRD §16.3 / P0-2 Worktree 物理隔离** | `src/macao/utils/git_utils.py` | `tests/test_mock_adapter.py` | ✅ **对齐**：强制为每个 Reviewer 创建独立 worktree，审查完成后自动安全清理。 |
| **PRD §5.2 / Review Context 权威结构** | `src/macao/utils/context_builder.py` | `tests/test_context_builder.py` | ✅ **对齐**：严格生成带 `refs`、质量快照、代码变更摘要与自评信息的单一权威结构。 |
| **PRD §11.4 & §11.5 / SQLite 存储与 Reconcile** | `src/macao/storage/db.py`<br>`src/macao/storage/reconcile.py` | `tests/test_state_store.py`<br>`tests/test_reconcile_crash.py` | ✅ **对齐**：WAL 模式 5 表 DDL；重启后以物理磁盘产物为真理源完成状态校正。 |
| **PRD §2.4 / AEP/1.0 统一消息信封** | `src/macao/msg/envelope.py`<br>`src/macao/msg/bus.py` | `tests/test_msg_bus.py` | ✅ **对齐**：标准 7 类消息类型，带 UUID、毫秒时间戳与 JSON Schema 校验。 |
| **PRD §14.5 / MERGING 中间态与 CI 门禁** | `src/macao/merge/controller.py` | `tests/test_orchestrator_sim.py` | ✅ **对齐**：Fast-forward 检查、外部 CI 命令执行与人工签字放行（`require_human_signoff`）。 |
| **PRD §3.4 / 场景 S1~S6 与死锁接管** | `src/macao/workflow/orchestrator.py` | `tests/test_orchestrator_sim.py` | ✅ **对齐**：完整支持平票死锁超时接管、`macao override resolve` 四分支裁定。 |

---

## 四、机器校验与复现验证指引

本申请包含的代码与测试可通过以下标准指令 100% 独立复现：

```bash
# 1. 运行全量单元与端到端多 Agent 仿真测试套件 (22 项测试全绿)
PYTHONPATH=src python3 -m unittest discover tests -v

# 2. 运行 MACAO CLI 健康自检与配置探针
PYTHONPATH=src python3 -m macao.cli.main doctor

# 3. 检查代码与文档格式空白规范 (0 errors)
git diff --check
```

---

## 五、专家评审排班与重点核查要点

依据 [`docs/EXPERT_QUALITY.md`](../EXPERT_QUALITY.md) 的排班与分工原则，本轮代码级审批评审阵容建议如下：

- **Claude（语义/业务流转轴）**：
  - 重点核查：10 态 FSM 事件流转（E1~E10）、多轮返工（Round 递增与 Context 继承）及 Orchestrator 事件循环是否完全贴合 PRD 业务逻辑。
- **Codex（安全/沙箱/存储轴）**：
  - 重点核查：Git Worktree 沙箱隔离生命周期、PTY 会话 `os.killpg` 孤儿进程强杀、SQLite WAL 并发安全与 StateReconciler 崩溃恢复逻辑。
- **OpenCode（治理/Schema 契约轴）**：
  - 重点核查：代码中所有的产物生成与解析是否 100% 通过 `docs/schemas/` 强校验、AEP 消息信封规范性、以及与 STATUS/GUIDELINES 的审计闭环。

---

## 六、期望产出与后续计划

1. 专家根据 [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) 对本申请范围的代码及测试进行独立复审，输出 `docs/reviews/2026-08-27-review-result-<commit>-<reviewer>.md`；
2. 若无阻断性 P0/P1 问题，正式宣告代码达成 **L2 SPEC-CODE-ALIGNED / PG-1 准入**，并更新 `docs/reviews/STATUS.md`；
3. **后续实机联调申请**：在此之后，向用户正式申请人工介入监督，开展真实 `claude-code`、`codex` 与 `kimi` CLI 的受控连通性与实机联调测试（Phase 0 Task 0.1 闭环）。
