# MACAO 产品设计与技术架构全盘评审报告（含 7 大待完善环节深度分析）

> **评审日期**：2026-08-26  
> **评审角色**：Gemini (Antigravity AI)  
> **被评审 Commit**：`684a012`  
> **评审对象**：`docs/` 下全量设计与规范文档（以 [`MACAO_PRD_v2.md`](../MACAO_PRD_v2.md) v2.1 为权威基准，交叉核验 [`EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md)、[`IMPROVEMENT_SUMMARY.md`](../IMPROVEMENT_SUMMARY.md)、[`SRSv1.md`](../SRSv1.md)、[`MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)）  
> **评审核心问题**：
> 1. 当前设计是否满足「产品可用」？
> 2. 当前设计是否满足「可以开始开发（PG-0 门禁）」？
> 3. 通盘检查全案设计，在迈向工业级编码落地时，还有哪些环节存在设计不足与需完善之处？

---

## Executive Summary（评审结论总览）

| 评审维度 | 结论判定 | 评级 / 状态 | 核心依据 |
|---|---|---|---|
| **产品设计可用性** | **满足产品可用** | ⭐⭐⭐⭐⭐ | MVP 范围精准收敛为单机三 CLI 协作 PoC；用户旅程从预检、初始化、任务派发到人工接管和合并归档实现全闭环；核心痛点（黑盒推断改为显式产物）具备强业务价值。 |
| **技术架构完备性** | **满足开发准入** | ⭐⭐⭐⭐⭐ | LangGraph 8 状态机唯一化；状态作用域读取与归档彻底解决产物遮蔽；2/3 多数 + 2 票法定人数决策表严密；AEP 统一信封与 Context refs 契约闭环；代码块机器语法全量通过。 |
| **阶段门禁判定** | **达成 PG-0 / L1 DOC-ALIGNED** | 🟢 **准予开工** | 历史 P0 全部关闭；文档间核心语义与 Schema 一致；具备进入 Week 1-2 PoC 验证与核心编码的前置条件。 |
| **待完善工程环节** | **已定位 7 大关键环节** | 🛠️ **进入优化跟踪** | 覆盖 PTY 交互拦截、多 Reviewer 工作区隔离、SQLite DDL、模型输出自愈、分支 Rebase 策略、agmsg 消息总线细节及文档治理。 |

---

## 第一部分：产品与技术设计就绪度评估

### 1.1 产品设计评估（Product Usability）
- **业务定位清晰收敛**：PRD v2.1 明确将 MVP 定位为「固定三 CLI（Claude Code Executor + Codex/Kimi Reviewers）的本地单机协作 PoC 规格」，移除了远程 SSH、通用调度等高复杂度特性，交付周期收敛为 6-8 周，风险高度可控。
- **用户旅程闭环（PRD 第十四部分）**：
  - **环境自检**：`macao preflight` 执行 CLI 登录态/版本探测并输出修复建议。
  - **初始化与校验**：`macao init` 生成模板配置，`macao doctor` 校验配置与环境。
  - **任务准入**：`macao task create` 强制要求标题与验收标准（`success_criteria`），验收标准缺失直接拒绝创建。
  - **可观测与可审计**：`macao status`（统一展示 FSM 状态、checkpoint_ref、review_round、各 Agent 状态）、`macao logs <agent>`、`macao usage`（Token 用量与成本计量）。
  - **人工接管**：发生 `HUMAN_OVERRIDE_REQUEST` 时，提供 `macao override list` 查看上下文诊断报告与票面证据，通过 `macao override resolve` 录入决策并永久写入审计事件表。
  - **合并与归档**：集成 `Merge Controller`（可选 `ci_gate_command` 门禁），合并后自动将当轮产物归档至 `.macao/archive/<ref>/r<round>/` 并随 git 提交。
- **共识与治理规则严密（PRD §2.3）**：
  - 定义了 `2/3 多数 + 2 票法定人数（minimum_quorum）`。在 MVP 2 人配置下，任何自动判定均需 2 票一致；若发生 1:1 僵局、1 弃权 1 反对、全弃权/超时，系统一律判定为 `Consensus Deadlock` 触发人工仲裁，杜绝单票决定合并的漏洞。
  - 设定 `max_rework_rounds = 3` 防无限死循环；第 n 轮复审采用 `delta_plus_focus` 策略。

### 1.2 技术设计评估（Technical Readiness）
- **状态机与识别引擎（PRD 第三部分）**：
  - 统一为 8 个标准 FSM 状态（`IDLE`, `CODING`, `READY_FOR_REVIEW`, `WAITING_REVIEW`, `CONSENSUS_CHECK`, `DONE`, `REWORK`, `UNKNOWN`），命令型转移与产物型转移汇总至同一张统一转移表（§3.3）。
  - 核心突破：`recognize_agent_state` 按照「当前 FSM 状态 + 当前 checkpoint_ref / review_round」作为过滤作用域，每个状态仅读取当前阶段合法的产物类型，消费后立即标记 `consumed` 并归档，彻底根治了持久 `.dev.yml` 遮蔽后续状态的问题。
- **AEP 协议与 Context 契约（PRD §2.4 / §5.2）**：
  - 全部 7 类 AEP 消息严格统一为 `protocol` / `message_id` / `timestamp` / `type` / `from` / `to` / `payload` 信封结构。
  - 代码变更载体统一采用 `code_changes.refs.{base_commit, head_commit}`，Reviewer 在本地工作区通过 `git fetch` + `git diff` 提取代码变更，不内联传输大文本 diff/patch，避免了截断与编码问题。
- **机器语法全量验证**：
  - 对 `docs/` 下全部 Markdown 代码块进行了 Python `yaml.safe_load`（12 段）与 `json.loads`（9 段）全量校验，全部通过，无非法字符与非法注释。

---

## 第二部分：通盘检查发现的 7 大待完善环节深度剖析

通盘审视整个系统设计，从「高质量设计规范」迈向「工业级稳健实现」时，仍存在以下 7 个需要细化和完善的工程技术环节：

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MACAO 设计待完善环节全景图                        │
└────────────────────────────────────────────────────────────────────────┘
  1. 进程与交互层   ──► PTY 会话交互拦截、ANSI 过滤与孤儿进程回收机制
  2. 工作区与文件层 ──► 多 Reviewer 本地并发隔离（git worktree 缺失）
  3. 持久化与数据层 ──► SQLite State Store 缺失具体 DDL 表结构与恢复算法
  4. 提示词与模型层 ──► Reviewer Prompt 模板定义与非结构化输出自愈机制
  5. 分支与版本控制 ──► 上游分支变更同步（Rebase）与分支生命周期管理
  6. 消息总线细节   ──► agmsg 本地运行形态、持久化与死信重试契约
  7. 运维与可观测层 ──► Token 遥测缺失时的降级估算规则 & docs/README 索引
```

---

### 环节一：PTY 进程交互拦截、ANSI 过滤与子进程回收（进程与交互层）

#### 🔍 现状与隐患
PRD §11.2 和第十二部分定义了 PTY 子进程模型，但缺少对真实交互式命令行特有行为的防御性设计：
1. **自动确认与权限弹窗（Auto-Approval / Permission Prompts）**：
   - 真实场景中，Claude Code CLI 在执行 Bash 命令或写文件时经常会弹出交互式确认提示（如 `Allow this command? [y/n]` 或 `Do you want to proceed?`）。若在后台 PTY 运行且无应答逻辑，进程会发生静默挂起（Hang），直到触发 2h 超时。
   - **缺失**：未明确 Adapter 是通过 CLI 启动参数（如 `--dangerously-skip-permissions` / `--non-interactive`）规避，还是在 PTY Wrapper 中实现正则匹配自动应答机制。
2. **ANSI 控制码与终端转义清洗（ANSI Stripping）**：
   - CLI 进程输出包含大量光标控制、色彩高亮、Spinner 动画等 ANSI 转义字符。若直接截取后 300 行喂给 Layer 3 LLM 诊断，不仅消耗大量无用 Token，还会严重干扰 LLM 的语义理解。
3. **孤儿进程组回收（Orphan Process Cleanup）**：
   - Claude Code 可能会派生编译、测试（如 `pytest`、`npm test`）等子子进程。如果 Orchestrator 异常崩溃或执行 `cancel`，仅 `kill(pid)` 无法回收派生子进程。

#### 💡 完善建议
- 在 Adapter Contract（第十二部分）中增加 **PTY 运行规范**：
  - 规定统一使用进程组发送信号（`os.killpg(os.getpgid(p.pid), signal.SIGTERM)`）；
  - 增加统一的 `strip_ansi()` 过滤器，清洗日志后再存入 State Store 与 LLM 诊断；
  - 明确各 CLI 的非交互运行参数（如 Claude Code 的无提示模式配置）。

---

### 环节二：多 Reviewer 本地工作区并发冲突与隔离（文件系统与 Git 层）

#### 🔍 现状与隐患
- PRD §5.3 的 Reviewer 标准工作流中，Codex 和 Kimi 收到 `REVIEW_REQUEST` 后，均执行：
  ```bash
  cd "$(jq -r '.repository.workspace_path' /tmp/context.json)"
  pylint src/ && bandit -r src/ && mypy src/
  ```
- **问题**：MVP 为 Codex + Kimi 双 Reviewer 并发执行。如果两个 Reviewer CLI **直接在同一个物理目录**并发运行静态检查或自动化测试，会产生：
  1. Python `__pycache__` / `.mypy_cache` / `.pytest_cache` 目录的文件读写竞态；
  2. 测试中若有本地 SQLite 数据库或端口监听，会发生冲突互锁；
  3. 若某 Reviewer 尝试运行 `git checkout` 检出被审 commit，会直接破坏另一个 Reviewer 的工作区。

#### 💡 完善建议
- 在 PRD §5.3 中引入 **`git worktree` 临时隔离机制**：
  - Orchestrator 在分发评审任务前，为每个 Reviewer 创建专用的临时 worktree：
    `git worktree add -d .macao/worktrees/cc-glm <checkpoint_ref>`
  - Reviewer 在各自独立的 worktree 目录中执行审查与测试，互不干扰；
  - 评审结束后由 Orchestrator 自动清理 worktree（`git worktree remove`）。

---

### 环节三：State Store 数据模型（DDL）与崩溃恢复 Reconcile 算法（数据层）

#### 🔍 现状与隐患
- PRD §11.2 和 §13 声明使用 SQLite 作为 State Store 单文件存储，但**未给出任何具体的表结构设计（DDL）**。
- PRD 声明 SQLite 与 Git 产物双写可用于崩溃恢复，但未定义**双写不一致时的仲裁算法（Reconciliation Protocol）**：
  - 场景 A：SQLite 已更新状态为 `READY_FOR_REVIEW`，但磁盘上的 `.dev.yml` 归档到 archive 目录中断；
  - 场景 B：Git 已完成 commit，但 SQLite 事务未提交即断电。

#### 💡 完善建议
- 在 PRD 第十一部分补全 **SQLite 核心 DDL**：
  - `tasks`（任务元数据、目标分支、当前轮次、当前 FSM 状态）；
  - `artifacts`（产物路径、类型、SHA-256、review_round、consumed 标志）；
  - `audit_events`（自增 sequence_id、时间戳、状态跃迁记录、伴随 payload）；
  - `overrides`（人工接管记录、用户 choice 与理由）。
- 明确 **Reconcile 仲裁规则**：以工作区 Git 历史和磁盘上已验证的物理 YAML/JSON 文件作为第一真理源（Physical Source of Truth），系统重启时自动扫描并修复 SQLite 内存态。

---

### 环节四：Reviewer 提示词工程与非结构化 YAML 输出自愈（模型层）

#### 🔍 现状与隐患
- PRD 规定 Reviewer 必须生成规范的 `.review.yml`。然而，底层驱动 Codex / Kimi 的大模型在实际生成 YAML 时可能存在：
  1. 输出包裹在 Markdown 标记中（如 ```` ```yaml ... ``` ````）或包含前置客套话；
  2. 遗漏关键字段或 `opinion.status` 与 `vote` 出现映射不一致；
  3. 语法错误（如缩进混乱导致 YAML 解析失败）。
- 目前设计中，YAML 解析失败直接被判定为无效产物并忽略，这极易导致 Reviewer 超时并进入人工接管流程。

#### 💡 完善建议
- 在 Adapter 内部增加 **两级输出自愈逻辑（Self-Correction）**：
  1. **提取清洗器（Extractor）**：正则提取首个合法的 YAML 代码块，剔除多余文本；
  2. **局部重试（Local Re-prompt）**：若 Schema 校验失败（如 status ↔ vote 冲突），Adapter 在超时窗口内直接在会话中追加一次纠错提示（如 *"Your review YAML failed schema validation on field 'vote'. Please output valid YAML only."*），自愈成功后再落盘。

---

### 环节五：Git 分支生命周期与上游主干变更高频同步（版本控制层）

#### 🔍 现状与隐患
- PRD §14.5 定义了 Merge Controller，但在真实的团队研发场景中：
  - 当 Executor 在 `feature/x` 上开发、Reviewer 进行多轮评审的过程中，上游 `main` 分支很可能已经合入了其他人的代码；
  - 此时直接合并很可能产生 Git Conflict，触发人工接管。
- **缺失**：未定义在何时、由谁执行上游分支同步（Sync / Rebase）策略，以及 Rebase 产生新 Commit 后是否需要触发增量复审。

#### 💡 完善建议
- 在 §14.5 补充 **Pre-merge Rebase / Sync 规则**：
  - Merge Controller 在执行 Fast-forward 前，先探测目标分支是否有领先 commit；
  - 若有，可配置由 Executor 自动 rebase 并跑通 CI gate，再推送合并；若 rebase 发生代码冲突则上报人工接管。

---

### 环节六：agmsg 本地消息总线契约与死信队列（消息通信层）

#### 🔍 现状与隐患
- 文档统一采用了 `agmsg` + `AEP/1.0` 协议，但在单机本地实现中：
  - `agmsg` 的物理形态（是基于 Unix Domain Socket、基于内存 Queue、还是基于 SQLite 消息表）未明确约束；
  - 缺少**死信队列（Dead Letter Queue, DLQ）**与消息超时重发机制：如果某 Agent 消费异常导致消息一直未 ACK，该消息是否重新入队？何时丢弃？

#### 💡 完善建议
- 在 PRD 第十一部分明确 MVP 阶段的本地 `agmsg` 选型规范（推荐基于 SQLite 或进程间轻量 FIFO/UDS），并定义消息超时（TTL）、最大重试次数（如 3 次）与 DLQ 落盘机制。

---

### 环节七：Token 遥测缺失时的降级估算 & 文档导航索引（运维与文档治理）

#### 🔍 现状与隐患
1. **Token 遥测缺失降级**：PRD §15.4 提到 Usage Meter 依赖 CLI 输出，但部分 CLI 在 non-interactive 模式下完全不打印 Token 消耗。
2. **`docs/README.md` 为空**：`docs/README.md` 目前为 0 字节文件，缺少作为整个文档体系的总入口和阅读导航索引。

#### 💡 完善建议
- **用量估算兜底**：在 Usage Meter 中增加兜底算法（当 CLI 未提供 Token 数据时，基于输入上下文和输出文本字符数，按 `1 token ≈ 4 chars` 或 `tiktoken` 粗估记录并标记 `estimated: true`）。
- **补全 `docs/README.md`**：为 `docs/` 目录编写总览索引，清晰呈现各文档的定位与跳转链接。

---

## 第三部分：待完善项优先级与落地路线图

| 优先级 | 环节分类 | 具体改进项 | 建议落实位置 | 推荐处理阶段 |
|---|---|---|---|---|
| **P1** | 工作区隔离 | 引入 `git worktree` 机制隔离各 Reviewer 的本地测试与检查环境 | `MACAO_PRD_v2.md` §5.3 | Week 1-2 PoC 阶段 |
| **P1** | 进程与交互 | 增加 PTY ANSI 清洗、进程组全生命周期回收与自动确认策略 | `MACAO_PRD_v2.md` 第十二部分 | Week 1-2 PoC 阶段 |
| **P1** | 数据模型 | 补全 SQLite State Store 的核心 DDL 表结构定义与恢复算法 | `MACAO_PRD_v2.md` 第十一部分 | Week 1-2 骨架阶段 |
| **P2** | 模型输出自愈 | Adapter 增加 YAML 提取清洗与 1 轮本地 Schema 纠错重试机制 | `MACAO_PRD_v2.md` 第十二部分 | Week 3-4 Adapter 阶段 |
| **P2** | 分支合并 | 补充 Pre-merge 目标分支 Rebase 检查与冲突策略 | `MACAO_PRD_v2.md` §14.5 | Week 5 工作流阶段 |
| **P2** | 消息契约 | 明确本地 agmsg 的 IPC 物理形态（UDS/SQLite）与 DLQ 规则 | `MACAO_PRD_v2.md` 第十一部分 | Week 3-4 通信层阶段 |
| **P3** | 文档治理 | 补全 `docs/README.md` 目录索引与架构导航 | `docs/README.md` | 即刻处理 |

---

## 第四部分：总结与开工建议

1. **当前文档成熟度判定**：
   - 当前设计已达到工业级产品方案的**高成熟度水准**，核心业务流、状态机流转、共识裁定与产物通信全部闭环，**达到 PG-0 门禁要求，可以立即开始开发**。
2. **开工建议**：
   - 在 Week 1–2 的 PoC 与基础骨架开发过程中，优先将 **P1（Worktree 隔离、PTY 交互防护、SQLite DDL）** 作为核心架构模块同步编码落地，确保后续多 Reviewer 并发与进程调度的极高稳定性。

---
*本报告由 Gemini (Antigravity AI) 生成并记录于 `docs/reviews/2026-08-26-review-result-684a012-gemini.md`。*
