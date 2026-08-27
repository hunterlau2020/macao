# MACAO 整体技术框架与工程落地独立评审结论 (Qwen 专家评审)

- **评审日期**：2026-08-27
- **评审专家**：qwen（通义千问 / 独立专家评审，阿里生态视角）
- **评审对象**：commit `aa173d8`（含 PRD v2.3.1、Phase 0/1 全套代码、24 项自动化测试套件、PoC 验证报告及历史各轮专家评审）
- **评审性质**：整体技术选型、架构分层、代码质量与生态工程落地横向独立评审（与 zcode / claude / codex 评审互为印证与补充）
- **依据基准**：`docs/MACAO_PRD_v2.md` (v2.3.1)、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/EXPERT_QUALITY.md`

---

## Executive Summary (执行摘要)

MACAO 框架以 **“物理产物为第一真理源 + 10 态确定性 FSM + 2/3 多数仲裁算法 + Worktree 沙箱隔离”** 构建了一套逻辑高度自洽的多 Agent 协同门禁系统。

在经历了 commit `23dfad5` 的系统性整改后，前序评审指出的 **Deadlock 提前伪写落盘、Reviewer 重复计票、Worktree 降级安全隐患、FSM 转移表死代码、SQLite 连接泄漏** 等核心缺陷已全部闭环修复，24 项单元与场景仿真测试全部绿灯通过（POSIX 与 Windows 双平台实测通过）。

然而，从**真实多模型集成与生产级工程落地（特别是国产大模型生态适配）**的视角审视，当前技术框架仍处于 **“高质量领域内核（Domain Core）就绪，但运行时装配（Composition & Runtime Wiring）与真实环境接口存在断层”** 的状态。本报告将从技术选型、架构分层、实现质量与生态演进四个维度提供详细评估与整改建议。

---

## 一、技术选型与多模型生态适配评估

### 1.1 核心基础选型评价

| 选型组件 | 选型评估与依据 | 适用性评级 |
|---|---|---|
| **Python 3.10+** | 作为 Agent 调度中枢与 CLI 框架，语法表现力强，便于跨平台集成与协议演进。 | **优秀 (Highly Suitable)** |
| **SQLite (WAL 模式)** | 单机/单控制进程形态下的理想状态快照与审计存储，零运维成本，天然支持事务原子性与并发只读。 | **优秀 (Highly Suitable)** |
| **JSON Schema (Draft-07)** | 契约强校验与权威事实源的基石，配合 `docs/schemas/` 单一源头管理，有效防止跨模型协议幻觉。 | **优秀 (Highly Suitable)** |
| **Click + Rich** | 兼顾命令行脚本化（Scriptable）与开发者终端可读性（Rich Tables/Panels）。 | **合适 (Suitable)** |
| **PTY Session (`openpty` + `killpg`)** | 在三方 CLI 缺乏标准无头 API 时的非侵入式兼容手段，进程树强杀机制设计规范。 | **合理过渡方案 (Pragmatic Transition)** |
| **手写确定性 FSM** | 明确放弃引入冗余的 LangGraph 重型框架，采用纯状态转移表驱动，杜绝了非确定性调度隐患。 | **非常正确 (Commendable)** |

---

### 1.2 国产大模型生态适配深度分析（Qwen 视角）

当前 Adapter 矩阵主要面向 `claude-code`、`codex` 和 `kimi`。在实际国内开发者与企业私有化场景中，**通义千问 (Qwen / Qwen-Coder)、DeepSeek、GLM** 等模型的接入需求极为迫切：

1. **CLI 交互模式的差异性**：
   - 国产大模型生态（如基于 DashScope / Ollama / vLLM 或开源 CLI 包装工具）通常提供以下三种接口形态：
     - **形态 A（Headless Pipe）**：标准输入输出管道（`stdin/stdout` JSON 模式），无需昂贵的伪终端（PTY）分配；
     - **形态 B（PTY TUI）**：类似 Claude Code 的交互式终端；
     - **形态 C（API Direct Hook）**：通过 OpenAI 兼容接口直接执行 Code Review / Diff 分析。
   - **架构建议**：将 `AgentAdapter` 的底层执行能力解耦为可插拔的 `TransportLayer`（`PTYTransport` vs `SubprocessPipeTransport` vs `DirectAPITransport`），而非强绑定 PTY。这不仅大幅提升在 Linux/Windows 上的运行稳定性，更能直接无缝支持 Qwen-Coder 等以 Headless 管道为首选输出的模型。

2. **Prompt 注入防御与 Token 开销控制**：
   - 国产模型在处理长上下文 Diff 时，对 Token 成本和中文反馈格式有明确偏好；
   - `ReviewContextBuilder` 中应支持按模型能力（Context Window / 语言偏好）进行上下文分片（Diff Chunking）和提示词模板本地化。

---

## 二、代码组织与架构分层评审

### 2.1 分层架构评述 (Hexagonal / Clean Architecture)

当前仓库目录分工清晰，符合高内聚低耦合原则：
```text
src/macao/
├── core/         # 领域枚举、Schema 验证器、配置管理 (Domain Core)
├── storage/      # SQLite 数据访问、审计日志、状态修复 (Infrastructure / Persistence)
├── msg/          # AEP 消息信封与消息总线 (Messaging Port & Adapter)
├── adapter/      # 多 Agent 适配器与 PTY 会话 (Agent Execution Port)
├── consensus/    # 2/3 多数仲裁、计票聚合器 (Domain Service)
├── workflow/     # 10 态 FSM、作用域读取、Orchestrator 编排 (Application Services)
├── merge/        # Fast-forward 合并与 CI 门禁控制器 (Merge Pipeline)
├── utils/        # Git Worktree 管理、ANSI 清洗、Context 组装 (Infrastructure / Utils)
└── cli/          # Click 命令行交互与 Rich 视图渲染 (Presentation / Entrypoint)
```

---

### 2.2 结构性问题与重构建议

#### 🔴 问题一：配置管理（`ConfigManager`）未作为单例/依赖注入至核心调度链
- **现象**：`src/macao/cli/main.py` 在执行 `task create`、`override resolve` 等命令时，直接实例化 `Orchestrator(project_root=".")`，未加载 `macao.yaml`；`Orchestrator` 内部采用硬编码默认参数运行。
- **影响**：用户在 `macao.yaml` 中配置的 `max_rework_rounds`、`ci_gate_command`、`require_signoff` 等关键策略在实际 CLI 执行时失效。
- **整改方案**：将 CLI 定位为 **Composition Root（组装根）**，统一通过 `ConfigManager.load_config()` 加载配置对象，并作为参数显式注入到 `Orchestrator` 与 `MergeController` 中。

#### 🔴 问题二：领域类型双重定义与命名脱节
- **现象**：
  - `PreflightCheckResult` 在 `core/types.py` 中的定义与 `adapter/claude.py`、`adapter/codex.py`、`adapter/kimi.py` 中的构造参数存在历史字段名不匹配（如 `cli_name` vs `agent_id`）；
  - `CapabilityManifest` 在 `core/types.py` 与 `adapter/base.py` 中重复定义且字段不一致。
- **整改方案**：将所有跨模块通信的数据模型（DTO / Value Objects）统一收敛至 `core/types.py`，Adapter 模块严禁二次定义同名类型。

#### 🔴 问题三：消息总线 SQLite 队列的 Fan-out 语义缺陷
- **现象**：`src/macao/storage/db.py` 的 `message_queue` 记录中，`to_agent` 为 JSON 数组（如 `["cc-glm", "kimi"]`），但整行只有一个 `status = 'PENDING'` 与单次 ACK。
- **影响**：当 Orchestrator 向多个 Reviewer 广播消息时，只要第一个 Reviewer 调用 `msg_bus.ack()`，消息状态即变为 `ACKED`，导致后续 Reviewer 无法在 `receive_pending()` 中查出该消息。
- **整改方案**：在发布广播消息时，按接收方拆分为独立投递项（Delivery Table），或将 ACK 粒度细化至 `(message_id, recipient)` 二元组。

---

## 三、代码实现质量与安全防御深度

### 3.1 最新整改（commit 23dfad5）核验结论

对 `23dfad5` 的所有整改项进行了全量代码核读与测试重放：

| 整改项目 | 核验结果 | 证据与代码位置 |
|---|---|---|
| **P0-1: Deadlock HOLD 与零落盘** | **VERIFIED PASS** | `src/macao/workflow/orchestrator.py:284-307` 决策分支中，`DEADLOCK` 仅触发 `HUMAN_OVERRIDE_REQUEST` 并不写盘；`src/macao/consensus/vote.py:146-149` 显式拦截 `DEADLOCK` 写盘。测试 `test_p0_deadlock_does_not_write_fake_vote_result_and_holds` 成功断言文件不存在。 |
| **P0-2: Reviewer 身份去重** | **VERIFIED PASS** | `src/macao/consensus/vote.py:46-52` 与 `state_engine.py:70-84` 基于 `reviewer_id` 字典与集合去重，伪造副本文件无法突破法定人数。 |
| **P0-3: Worktree 强制隔离与 Fail-closed** | **VERIFIED PASS** | `orchestrator.py:157-168` 在创建 Worktree 失败时直接抛出 `RuntimeError` 并中断流程，绝无回退主工作区路径；权威 Context 注入专属 Worktree 绝对路径。 |
| **P0-4: FSM 状态转移白名单拦截** | **VERIFIED PASS** | `src/macao/workflow/fsm.py:32-41` 每次转移前显式校验 `TransitionTable.can_transition()`，非法转移直接阻断并记审计日志。 |
| **P0-5: MergeController 接入与硬校验** | **VERIFIED PASS** | `src/macao/merge/controller.py:53-73` 实现了 Fast-forward 校验、安全 shlex 命令执行、签字审计检查与 HEAD == checkpoint_ref 强校验。 |
| **P1-3: Artifacts 追加归档语义** | **VERIFIED PASS** | `src/macao/storage/db.py:26-38` 迁移为 `artifact_id AUTOINCREMENT`，`store.py:90-105` 避免了覆盖写，保留历史轮次审计足迹。 |
| **P1-5: SQLite 连接管理与 PTY 保护** | **VERIFIED PASS** | `src/macao/storage/db.py:92-105` 引入上下文管理器并强制 `close()`；`pty_session.py:16-30` 引入平台判断，双平台 24 项测试全绿。 |

---

### 3.2 深度安全防御建议 (Defense in Depth)

1. **Git Worktree 的安全边界定性**：
   - 当前实现的 Git Worktree 物理隔离能够有效杜绝工作区文件冲突、覆盖与 Git HEAD 竞态，是极其优秀的工程隔离机制；
   - 但从 OS 安全视角，Reviewer 进程依然运行在同宿主用户下。在后续技术文档与产品说明中，应严谨定性为 **“代码检出物理隔离（Workspace Checkout Isolation）”**，避免与容器级/命名空间级（如 Docker / Bubblewrap / gVisor）的安全沙箱混淆。
2. **只读命令的副作用剥离**：
   - `macao status` 与 `macao doctor` 命令不应在查询时自动调用 `reconciler.reconcile()` 修改数据库状态；建议将状态修复作为独立的显式命令（如 `macao task repair` / `macao recover`），保持观测命令的严格幂等与只读。

---

## 四、演进路线与生产就绪度建议

为推动 MACAO 从当前 Phase 0/1（单机原型）平稳进入 Phase 2/3（生产可用与多模型实战），建议按以下路线落地：

```
[当前阶段: Phase 0/1 完成]
   ↓
[近期优化: 1~2 天]
 1. 统一 core/types 与 adapter/base 的数据模型，删除死定义与向后兼容别名；
 2. 修复 macao init 模板与 macao_config.schema.json 的 100% 对齐；
 3. CLI 入口统一接入 ConfigManager 依赖注入；
 4. 扩充 Qwen-Coder / DeepSeek 真实 CLI 适配器接口标准；
   ↓
[中期演进: Phase 2]
 5. 实现单进程后台调度事件循环（带计时器、心跳与超时降级机制）；
 6. 申请人工介入，开展 Claude Code / Codex / Kimi / Qwen 真实 CLI 实机联调；
 7. 搭建 GitHub Actions 多平台自动化 CI 门禁。
```

---

## 五、Reviewer 声明与自审记录

- **独立性声明**：本评审由 Qwen 独立完成，严格遵循 `docs/MACAO_REVIEW_GUIDELINES.md`；
- **机验声明**：本报告引用的测试结论均基于本地环境运行 `PYTHONPATH=src python3 -m unittest discover tests -v` 独立重跑（24/24 PASS）；
- **门禁结论**：鉴于核心缺陷（2 P0 + 7 P1）已在 `23dfad5` / `aa173d8` 闭环修复，且 24 项回归测试全绿，**认可 Phase 0 / Phase 1 核心代码达成 L2 SPEC-CODE-ALIGNED / PG-1 阶段性质量基线**，同意进入受控真实 CLI 实机联调准备阶段。

---
