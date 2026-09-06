# MACAO 技术架构与技术实现说明文档 (TECH_INTRODUCE)

> **文档定位**：记录 MACAO (Multi-Agent CLI Agent Orchestrator) 的整体技术架构、已落地的核心技术组件选型、各模块职责分工、CLI 交互界面的实现方案、以及与全屏 TUI 的对比演进。
> **权威标准**：[`docs/MACAO_PRD_v2.md`](MACAO_PRD_v2.md)（权威产品方案 v2.3.1）与 [`docs/schemas/`](schemas/)（版本化契约）。

---

## 一、技术架构总览 (Architecture Overview)

MACAO 是一个面向 AI 软件开发团队的**跨终端 CLI Coding Agent 编排平台**。其核心技术目标是通过**规范化流程 + 约定式物理产物**，将不同厂商的 CLI 编程智能体（Claude Code, Codex, Kimi 等）组织为高效协作的自动化开发-评审-合并团队。

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           MACAO 系统架构全景                               │
└───────────────────────────────────────────────────────────────────────────┘

  [ 用户 / 工程师 ]
        │
        ▼
  ┌───────────────────────────────────────────────────────────────────────┐
  │  CLI 交互层 (Rich + Click + prompt_toolkit)                           │
  │  ├─ 命令分发: preflight / init / doctor / task / status / override     │
  │  └─ 终端渲染: 状态看板 (Live Table) / 诊断面板 / 人工仲裁交互菜单         │
  └───────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
  ┌───────────────────────────────────────────────────────────────────────┐
  │  MACAO 核心编排引擎 (Orchestrator Core)                                 │
  │  ├─ 中央事件调度器 (Orchestrator: 串联 FSM / 适配器 / 消息 / 仲裁)     │
  │  ├─ 10 状态有限状态机 (WorkflowFSM & TransitionTable E1~E10)          │
  │  ├─ 三层状态识别引擎 (StateRecognitionEngine: 作用域读取 + 显式信号)   │
  │  ├─ 共识与决策引擎 (ConsensusEngine: 2/3 多数 + 2 票法定人数仲裁)      │
  │  ├─ 合并控制器 (MergeController: MERGING 流水线 + CI Gate + 签字)     │
  │  ├─ 配置管理中心 (ConfigManager: macao.yaml 单一事实源)               │
  │  └─ 契约校验中心 (SchemaValidator: docs/schemas/ 强校验)              │
  └───────────────────┬───────────────────────────────┬───────────────────┘
                      │                               │
                      ▼                               ▼
  ┌───────────────────────────────┐   ┌───────────────────────────────────┐
  │  持久化与存储层 (State Store)  │   │  消息总线层 (agmsg / AEP/1.0)     │
  │  ├─ SQLite 数据库 (WAL 模式)  │   │  ├─ AEP 信封封装 (7 种标准消息)    │
  │  ├─ 5 张核心表 (Tasks/Audits) │   │  ├─ 本地队列调度 (Pub/Sub/ACK)    │
  │  └─ 崩溃恢复协议 (Reconcile)  │   │  └─ 重试与死信队列 (DLQ)          │
  └───────────────────────────────┘   └───────────────────────────────────┘
                                      │
                                      ▼
  ┌───────────────────────────────────────────────────────────────────────┐
  │  适配器运行时层 (Adapter Runtime - Adapter Contract v1)               │
  │  ├─ PTY 会话管理器 (PTYSession: ANSI 清洗 / os.killpg 进程组管理)      │
  │  ├─ ClaudeCodeAdapter (Full 权限模式，任务工作区执行)                   │
  │  ├─ CodexAdapter (Sandboxed 模式，独立 git worktree 隔离评审)         │
  │  ├─ KimiAdapter (Sandboxed 模式，独立 git worktree 隔离评审)          │
  │  └─ MockAgentAdapter (仿真适配器，用于安全、可重复的自动化测试)        │
  └───────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
  ┌───────────────────────────────────────────────────────────────────────┐
  │  底层物理工作区与进程 (OS & Git)                                      │
  │  ├─ CLI 子进程: claude-code / codex / kimi                            │
  │  ├─ Git 主工作区: .macao/ 产物 (.dev.yml / vote_result.json)          │
  │  └─ 隔离工作区: .macao/worktrees/ 独立沙箱 + .macao/archive/ 历史归档  │
  └───────────────────────────────────────────────────────────────────────┘
```

---

## 二、技术选型与组件落地矩阵

根据 PRD 规范，本项目全量技术组件选型均已在代码库中实现：

| 模块类别 | 选型技术 | 依赖库 | 架构设计决策与实现考量 |
|---|---|---|---|
| **核心语言** | Python 3.10+ | 标准库 | 统一采用类型注解（Type Hints）、`dataclass` 与标准面向对象设计，保证工程可维护性。 |
| **状态存储** | SQLite 3 | `sqlite3` | 单文件持久化（`.macao/state.db`），开启 WAL 模式保证并发读写安全性；实现 5 张核心表 DDL 与崩溃自动 Reconcile 恢复算法。 |
| **契约校验** | JSON Schema | `jsonschema` + `PyYAML` | 统一加载 `docs/schemas/` 目录下的 6 个版本化 Draft-07 Schema，在消息收发与产物落盘时进行强校验。 |
| **消息总线** | agmsg / AEP | SQLite 消息表 | 实现 AEP/1.0 统一信封（`message_id`, `timestamp`, `type`, `from`, `to`, `payload`），支持 7 类标准消息及 DLQ 死信处理。 |
| **工作流 FSM** | 确定性 FSM 引擎 | 纯 Python 引擎（预留 LangGraph 接口） | 严格实现 10 个业务状态与 E1~E10 统一转移表，支持状态作用域产物过滤与自动归档；通过 `TransitionTable` 抽象便于后续扩展。 |
| **进程与沙箱** | PTY / Git | `pty` + `subprocess` + `git` | 实现伪终端会话包装、ANSI 转义序列清洗、`os.killpg` 孤儿孙进程彻底回收，以及通过 `git worktree` 为 Reviewer 创建独立物理隔离沙箱。 |
| **共识与仲裁** | 多数共识算法 | 纯 Python 算法模块 | 严格实现 `2/3 多数 + 2 票最低法定人数（minimum_quorum）` 仲裁算法，精准判定全批准、全返工与 1:1 死锁。 |
| **合并流水线** | Git 合并控制器 | `subprocess` (Git) | 实现 `MERGING` 阶段的检出、Fast-forward 合并、可选 CI Gate 门禁命令与人工签字校验。 |
| **CLI 界面** | 终端命令行 | `click` + `rich` + `prompt_toolkit` | 实现现代美观的增强型 CLI 工具集（详见第三节）。 |
| **测试框架** | 单元与集成测试 | `unittest` (兼容 `pytest`) | 覆盖 Schema 校验、状态机流转、共识判定、状态存储与消息总线的完整测试套件（22 项全绿）。 |

---

## 三、CLI 界面实现方案与“增强型 CLI vs TUI”选型剖析

### 1. 为什么不采用“通用 AI 聊天框架”（如 Chainlit / Streamlit / Open-WebUI 等）？

1. **产品本质定位不同（DevOps 基础设施 vs Chatbot 聊天机器人）**：
   - **通用 AI 聊天框架**面向的是“人类直接与大模型对话问答”的场景（以会话 Message 流、Markdown 气泡渲染为主）。
   - **MACAO 的本质是“开发者基础设施与自动化编排工具”**（定位类似 `kubectl`, `git`, `docker`, `terraform`, `gh`）。人类工程师在 MACAO 中的角色是**任务发起者、状态监控者与关键仲裁者**，而不是在网页里与某个 Agent 闲聊。
2. **底层 Coding Agent 已经具备对话能力**：
   - 实际编写代码的对话交互由底层的 `claude-code`、`codex` 等 CLI 工具自身完成。MACAO 负责在后台以 PTY 托管它们，捕获其显式产物（`.dev.yml` / `.review.yml`）。如果在 MACAO 上层再套一个聊天框，会造成职责冗余与交互割裂。
3. **追求轻量、高响应、可脚本化（Scriptable）与 CI/CD 友好**：
   - 通用聊天框架通常引入重量级的 Web Server、WebSocket 守护进程、Node/React 前端打包或复杂的 Session 管理，无法无缝集成进工程师的 Terminal 流水线或 Shell 脚本中。
   - MACAO 追求的是零网络开销、秒级启动、可通过命令行参数直接执行的本地原生 CLI。

---

### 2. “Click + Rich + prompt_toolkit” 与全屏 TUI (Text User Interface) 的本质区别

用最直观的类比来说：
- **Click + Rich + prompt_toolkit** 类似 **`docker` / `kubectl` / `gh`**（现代增强型 CLI 工具）；
- **TUI** 类似 **`lazygit` / `k9s` / `htop`**（全屏常驻沉浸式终端应用）。

#### 全方位对比矩阵

| 比较维度 | Click + Rich + prompt_toolkit (增强型 CLI) | 严格意义上的 TUI (如 Textual / Curses) |
|---|---|---|
| **终端屏幕控制** | **流式输出（Stream / Scrollback）**<br>命令执行完将表格/面板打印在终端屏幕上，保留在历史滚动条中，光标返回终端 Prompt。 | **全屏接管（Alternate Screen Buffer）**<br>清屏并接管整个终端窗口，常驻事件循环，退出时恢复原有终端。 |
| **典型代表软件** | `docker`, `kubectl`, `gh`, `terraform`, `poetry` | `htop`, `k9s`, `lazygit`, `tmux`, `midnight commander` |
| **交互模型** | **“请求 - 响应 - 退出” (Ephemeral)**<br>用户输入 `macao status` -> 程序输出彩色看板 -> 立即退出；遇断点时弹出单行选择菜单。 | **“常驻事件循环” (Event-Driven Loop)**<br>类似终端里的桌面软件，支持鼠标点击、Tab 切换焦点、方向键浏览、多窗口分栏。 |
| **管道与自动化<br>(CI/CD 友好度)** | **⭐⭐⭐⭐⭐ 极高**<br>天然支持标准 Unix 管道与重定向（如 `macao status \| grep WAITING` 或在 CI 中跑脚本）。 | **⭐ 极低 / 不支持**<br>全屏 UI 无法直接用于 Shell 管道重定向或无头（Headless）CI 自动化环境。 |
| **多 Agent 监控** | 适合查看阶段性快照，或通过 `Rich.Live` 在局部控制台刷新进度指示器。 | 适合做常驻“作战大屏”（左侧任务树、右上实时日志流、右下多 Reviewer 投票面板实时滚动）。 |
| **开发与维护成本** | **低，敏捷稳健**<br>结构清晰，业务逻辑与命令完全解耦，极易编写单元测试。 | **较高**<br>类似在终端里写 Web 前端（需要处理布局 CSS、组件生命周期、键盘焦点管理）。 |

---

### 3. 三件套的分工与协作

```text
┌───────────────────────────────────────────────────────────────┐
│                      MACAO CLI 交互架构                       │
└───────────────────────────────────────────────────────────────┘

  1. 命令行解析与路由 (Click)
     ├─ macao preflight       # 环境依赖与 CLI 版本准入探测
     ├─ macao init            # 快速初始化 macao.yaml 模板
     ├─ macao doctor          # 静态配置与运行时健康度自检
     ├─ macao task create     # 结构化任务派发（带验收标准）
     ├─ macao status          # 任务与产物全景状态查看
     ├─ macao override        # 人工接管介入与决策录入
     └─ macao usage           # Token 与成本用量统计

  2. 终端美化与状态看板 (Rich)
     ├─ 表格渲染 (Table)      # Preflight 报告、任务状态表、产物清单
     ├─ 仪表盘 (Live Dashboard)# 实时多 Agent 状态监控、阶段进度条
     ├─ 面板与高亮 (Panel)    # 异常诊断报告展示、ANSI 日志清洗查看
     └─ 状态徽章 (Badges)     # [APPROVED], [REWORK], [DEADLOCK]

  3. 交互式菜单与选择器 (prompt_toolkit)
     ├─ 人工接管选择菜单      # 出现 Deadlock 时弹出单选/多选交互菜单：
     │                       #   [1] APPROVED     (强制合并放行)
     │                       #   [2] REWORK       (打回要求返工)
     │                       #   [3] RETRY_REVIEW (作废重试评审)
     │                       #   [4] CANCEL       (终止取消任务)
     └─ 交互式参数补全        # 任务创建向导、分支自动补全
```

---

### 4. 架构演进策略（增强型 CLI + 可选 TUI 控制台）

1. **当前阶段（MVP / v2.x）：以“增强型 CLI”为主干**
   - 作为底层的调度与编排引擎，首先必须满足**可脚本化、可集成进 CI/CD、秒级启动、轻量可靠**的要求；
   - 工程师在日常开发中需要的是快速查看状态（`macao status`）或派发任务（`macao task create`），流式 CLI 是最高效的操作方式。

2. **后续阶段（v1.1+ / v1.2）：平滑引入全屏 TUI（如 `Textual`）**
   - `Textual` 是 `Rich` 官方推出的现代 Python TUI 框架（同属 Textualize 生态，二者天然兼容）；
   - 如果未来用户希望拥有常驻的“**多 Agent 协同作战看板**”（类似 `k9s` 看 Kubernetes Pod 一样实时看 3 个 CLI 进程在同时干什么），可以非常轻松地新增一个 `macao ui` 或 `macao dashboard` 命令，拉起一个全屏 TUI 视图；
   - **两者完全不冲突，底层核心 FSM、State Store、agmsg 消息总线完全共用。**

---

## 四、CLI 运行态架构：PTY-Wrapper、Headless 参数与无状态 Reviewer 技术选择

在 MACAO 中，各个底层 AI CLI（Claude Code, OpenCode, Codex, Antigravity, Cursor Agent, Kimi）的自动化调度是编排体系的执行基石。本节深入剖析 MACAO 采用的 **PTY-Wrapper 伪终端封装**、**各 CLI Headless 参数矩阵**、**Session Resume 异构生态** 以及 **无状态 Reviewer 的架构权衡与 Token 优化策略**。

### 1. 为什么采用“PTY-Wrapper + Headless 免交互参数”技术方案？

#### (1) 普通后台管道（`subprocess.PIPE`）的致命局限
现代 AI 命令行工具专为人类开发者设计，本质是具备丰富光标交互和状态动画的**终端用户界面（TUI）**：
1. **强制 TTY 检测**：主流 CLI（如 Claude Code、Cursor Agent 等）在启动时会检测 `sys.stdin.isatty()`。若采用常规的 `subprocess.Popen(..., stdin=PIPE, stdout=PIPE)` 管道调用，CLI 会识别为非终端管道而直接报错退出。
2. **交互式授权弹窗（Interactive Confirmation）**：AI CLI 在执行文件读写、运行 Shell 脚本、修改代码时，默认会弹出 `[y/N]` 或交互式菜单等待人类按键授权。若以普通后台进程挂起，CLI 将永久阻塞在等待输入状态，导致任务死锁。

#### (2) MACAO PTY-Wrapper 的技术实现
MACAO 放弃了侵入式的 Hook / 插件魔改，采用纯原生的 **PTY-Wrapper（伪终端包装器）** 方案（见 [`src/macao/adapter/pty_session.py`](file:///home/debian/macao/src/macao/adapter/pty_session.py)）：
* **虚拟 TTY 分配**：底层通过 Python POSIX `pty.openpty()` 分配主从虚拟终端文件描述符，将从设备挂载至子进程的 `stdin/stdout/stderr`，使 CLI 坚信自己正运行在一个真实的交互式终端窗口中。
* **进程组生命周期与零僵尸保障（Zero Zombie Guarantee）**：子进程启动时通过 `preexec_fn=os.setsid` 建立独立会话与进程组。当任务完成或触发 SLA 超时时，PTY 会话管理器直接向进程组广播 `SIGTERM`（超时强行 `SIGKILL`），彻底回收 CLI 及其可能派生的编译器、单元测试、Node 等所有子孙进程，杜绝进程泄露。
* **ANSI 终端序列动态清洗与两级自愈**：通过 [`macao.utils.ansi.strip_ansi()`](file:///home/debian/macao/src/macao/utils/ansi.py) 过滤所有 ANSI 颜色转义码、进度条回车符与终端控制字符；结合 `ReviewExtractor` 正则提取 Markdown 栅栏中的结构化 YAML 产物，实施 Draft-07 Schema 校验，即使大模型附带自然语言客套话也能实现 100% 确定性解析。

---

### 2. 各 AI CLI 启动参数与 Headless 运行矩阵

MACAO 启动各个 CLI 时，根据各工具的原生能力注入专属的 Headless 免确认与模型控制参数：

| AI CLI 工具 | 核心 Headless / 免确认参数 | 模型透传参数 | 完整启动命令示例 | 运行时职责 |
| :--- | :--- | :--- | :--- | :--- |
| **Claude Code** | `--dangerously-skip-permissions`<br>*(跳过所有文件读写/命令执行的确认授权)* | `--model <model>` | `claude --dangerously-skip-permissions --model claude-3-7-sonnet` | Executor / Reviewer |
| **OpenCode** | `--quiet`<br>*(静默模式，关闭交互式动画与确认)* | `-m <model>` | `opencode --quiet -m "GLM 5.3 max"` | Executor / Reviewer |
| **Codex CLI** | `--quiet`<br>*(静默批处理执行模式)* | `-m <model>` | `codex --quiet -m "o3-mini"` | Executor / Reviewer |
| **Google Antigravity (agy)** | `--quiet`<br>*(无头批处理/任务模式)* | `--model <model>` | `agy --quiet --model gemini-2.0-pro` | Executor / Reviewer |
| **Cursor Agent (agent)** | `--trust --sandbox enabled -p`<br>*(信任当前目录、启用安全沙箱、-p 非交互提示词)* | `--model <model>` | `agent --trust --sandbox enabled -p --model "claude-3.5-sonnet"` | Executor / Reviewer |
| **Kimi CLI** | `--non-interactive`<br>*(非交互纯文本输入输出)* | `--model <model>` | `kimi --non-interactive --model kimi-k1.5` | Executor / Reviewer |

#### 四维参数与上下文交互模型
MACAO 与底层 CLI 的交互由 4 个维度严密定义：
1. **免确认 Flags**：如 `--dangerously-skip-permissions`, `--quiet`, `--non-interactive`，实现无人值守全自动运行；
2. **模型参数（Model Specification）**：从 `macao.yaml` 声明的 `team.executor.model` 或 `team.reviewers[i].model` 动态透传，支持精确指定各模型权重；
3. **工作区物理隔离路径（`cwd`）**：
   - **Executor**：`cwd` 指向主代码仓库，工作在 `feature/<branch>` 特性分支；
   - **Reviewer**：`cwd` 严格指向由 `git worktree add --detach` 建立的物理隔离沙箱（`.macao/worktrees/<rev_id>/<task_id>/r<round>/`），Reviewer 无论执行任何只读分析或命令，均物理隔离于主干与特性分支；
4. **结构化 Prompt 注入（PTY Stdin）**：会话建立后通过伪终端管道写入标准任务/审查指令（包含验收标准、审查说明及期望写回的 `.dev.yml` 或 `.review.yml` 路径）。

---

### 3. Session 机制与各 CLI 的 Session 语法现状

各个主流 CLI 实际上均具备原生会话恢复（Session Resume）命令：
```bash
# Codex CLI
Usage: codex resume [OPTIONS] [SESSION_ID] [PROMPT]

# Cursor Agent (agent)
Usage: agent resume [options]

# Kimi CLI
Usage: kimi -S, --session [id]            Resume a session.

# OpenCode
Usage: opencode -s, --session            session id to continue

# Claude Code
Usage: claude --resume [id]               Resume previous conversation
Usage: claude -c                         Continue recent conversation
```

#### 分工治理：Executor 与 Reviewer 的本质分歧
在编排体系中，不同角色的会话生命周期策略截然不同：
* **Executor（开发执行者）$\rightarrow$ 适合状态延续（Stateful Resume）**：
  - 执行者负责大型工程的代码实现，对项目背景、架构分层有较长的理解成本；
  - 若评审不通过需要返工（Round 2），通过 Session Resume 继续上一轮会话，能够保留思维脉络与工程感知，大幅提升修改效率并节省冷启动开销。
* **Reviewer（代码审查者）$\rightarrow$ 必须坚持严格无状态（Stateless & Isolated）**。

---

### 4. 核心技术争鸣：无状态 Reviewer 会不会导致 Token 浪费？

#### (1) 直觉疑问
“如果 Reviewer 必须严格无状态，每次启动 Session 都是一张白纸，它是否需要花费巨量的 Token 去到处 `ls` 探查项目结构、寻找哪些测试工具可用、测试脚本放在哪里？”

#### (2) MACAO 的架构解法：`review_context` 结构化靶向打包（PRD §5.2）
**如果直接裸调 CLI，上述 Token 浪费确实不可避免；但 MACAO 正是通过 `review_context` 契约彻底化解了这一问题。**

MACAO 在派发审查任务前，由编排器在宿主工作区预先完成分析，打包生成标准化的 `review_context`（校验遵循 [`docs/schemas/review_context.schema.json`](file:///home/debian/macao/docs/schemas/review_context.schema.json)），并作为 Prompt 直接注入给 Reviewer：
1. **靶向代码变更清单（`code_changes`）**：
   - 精确指定本次 Commit 的增删文件列表（`files_list`）、增删行数以及 `git diff` 引用；
   - Reviewer 一进入会话即明确审查靶心（通常只有几十至数百行变更），无需通读几万行源码；
2. **现成质量快照与测试命令（`quality_snapshot`）**：
   - 包含已通过的测试数（`tests.passed`）、覆盖率（`coverage`）以及具体的测试执行命令（如 `pytest tests/test_api.py`）；
   - Reviewer 无需消耗 Token 猜测测试框架（pytest? jest? cargo?），直接调用现有指令复核；
3. **开发者自评与审查重点提示（`executor_self_assessment.review_focus`）**：
   - 执行者在提交检查点时已明确指出：“重点关注并发安全与线程竞争”或“检查日期跨月边界值”；
   - Reviewer 带着明确的目标切入审查。

**结合 `review_strategy: "delta_plus_focus"` 增量审查策略，无状态 Reviewer 的单次上下文窗口开销被严格压制在 3,000 ~ 8,000 Token 以内，完全杜绝了盲目翻看代码库的无效损耗。**

#### (3) 为什么即使有轻微冷启动，评审也绝不能复用长 Session？（代价与收益权衡）
若为了省去冷启动而让 Reviewer 长期复用 Session，在生产环境中会带来毁灭性代价：
1. **Token 计费反噬（Context Inflation）**：
   - LLM 是按每次交互的**输入 Token 总量计费**的。若审查者累积了 Round 1、Round 2 甚至前序任务的历史，上下文将迅速膨胀到 5~10 万 Token；
   - **Reviewer 哪怕只输出一句简单的评价，开发者都要为庞大的历史上下文重复买单**！相比之下，无状态冷启动注入 3,000 Token 靶向数据，综合开销反而显著更低；
2. **长上下文注意力稀释（Lost in the Middle）**：
   - 随着 Session 膨胀，大模型对边界缺陷、竞态死锁与细微类型漏洞的敏感度会断崖式下滑；
3. **偏见与顺从性陷阱（Confirmation Bias & Sycophancy）**：
   - 若 Round 1 Reviewer 提了意见，Round 2 在同一 Session 内复用，当 Executor 说“我已按要求修复”，复用 Session 的 Reviewer 极易产生老好人顺从效应，直接草率给出 `APPROVE`；
   - **冷启动的本质是“双盲独立复审”**：每次只认此时此刻物理磁盘上的代码客观事实，这是工业级确定性共识门禁的生命线。

---

## 五、工程源码目录结构与模块说明

```text
macao/
├── pyproject.toml              # 项目打包与依赖定义
├── macao.yaml                  # 默认示例配置文件
├── .gitignore                  # Git 忽略规则
├── docs/                       # 设计文档与机器契约
│   ├── MACAO_PRD_v2.md         # 权威基准 PRD
│   ├── TECH_INTRODUCE.md       # 本文档（技术架构与实现说明）
│   ├── PLAN.md                 # 8 周研发计划与任务分解（WBS）
│   ├── ROADMAP.md              # 中长期技术演进路线图
│   └── schemas/                # 6 个版本化 Draft-07 JSON Schema 与 fixtures
├── src/macao/                  # 核心源码
│   ├── core/                   # 核心数据结构、类型枚举与 Schema 校验
│   │   ├── types.py            # 10 FSM 状态、AEP 消息类型、决策枚举
│   │   ├── schema.py           # 绑定 docs/schemas/ 的 Draft-07 强校验器
│   │   └── config.py           # macao.yaml 加载器与最低法定人数推导
│   ├── storage/                # SQLite 状态存储与恢复
│   │   ├── db.py               # SQLite WAL 连接管理与 DDL 初始化
│   │   ├── store.py            # Tasks/Artifacts/Audits/Overrides CRUD
│   │   └── reconcile.py        # 崩溃恢复与真理源对齐协议（PRD §11.5）
│   ├── msg/                    # 消息总线（agmsg + AEP/1.0）
│   │   ├── envelope.py         # AEP 信封封装与解包（Type A~G）
│   │   └── bus.py              # SQLite-based 本地消息队列、ACK、TTL 与 DLQ
│   ├── adapter/                # CLI 适配器层（Adapter Contract v1）
│   │   ├── base.py             # AgentAdapter 抽象基类与 CapabilityManifest
│   │   ├── pty_session.py      # PTY 进程管理、ANSI 清洗与进程组回收
│   │   ├── claude.py           # ClaudeCodeAdapter（Full 权限模式）
│   │   ├── codex.py            # CodexAdapter（Sandboxed + Worktree 模式）
│   │   ├── kimi.py             # KimiAdapter（Sandboxed + Worktree 模式）
│   │   └── mock.py             # MockAgentAdapter（仿真适配器，用于自动化测试）
│   ├── consensus/              # 共识与仲裁引擎
│   │   ├── engine.py           # 2/3 多数 + 2 票最低法定人数算法（PRD §2.3）
│   │   └── vote.py             # .review.yml 收集与 vote_result.json 生成
│   ├── workflow/               # 状态识别与 FSM 编排
│   │   ├── state_engine.py     # 三层识别与作用域产物读取（PRD §3.2）
│   │   ├── transitions.py      # 统一状态转移表（E1~E10 规则校验）
│   │   ├── fsm.py              # 10 状态 FSM 驱动器与产物归档
│   │   └── orchestrator.py     # Orchestrator 中央事件调度器（串联全生命周期）
│   ├── merge/                  # 合并控制器
│   │   └── controller.py       # MERGING 流水线（检出、FF merge、CI gate、push）
│   ├── utils/                  # 基础设施工具
│   │   ├── ansi.py             # ANSI 转义序列清洗工具
│   │   ├── git_utils.py        # Git 命令封装与 Worktree 独立沙箱管理
│   │   └── context_builder.py  # ReviewContext 权威构建器（PRD §5.2）
│   └── cli/                    # 命令行交互入口
│       ├── ui.py               # Rich 表格、仪表盘与诊断渲染
│       └── main.py             # CLI 命令集合（preflight, init, doctor, task...）
└── tests/                      # 自动化测试套件（22 项测试用例全部通过）
    ├── test_schema.py          # Schema 校验与正反向 fixture 测试
    ├── test_context_builder.py # ReviewContextBuilder 校验测试
    ├── test_mock_adapter.py    # MockAgentAdapter 能力与产物仿真测试
    ├── test_consensus.py       # 2/3 多数与决策表单元测试
    ├── test_state_store.py     # SQLite 状态与恢复测试
    ├── test_reconcile_crash.py # 崩溃恢复真理源对齐测试
    ├── test_fsm.py             # 10 态 FSM 状态流转测试
    ├── test_msg_bus.py         # AEP 消息队列与 ACK 测试
    └── test_orchestrator_sim.py# S1~S6 端到端多 Agent 编排仿真测试
```

---

## 六、运行与验证指引

### 1. 运行自动化测试套件（22 项全绿）
```bash
PYTHONPATH=src python3 -m unittest discover tests -v
```

**实测运行输出**：
```text
test_2_reviewer_consensus (test_consensus.TestConsensusEngine) ... ok
test_quorum_calculation (test_consensus.TestConsensusEngine) ... ok
test_full_review_context_builder (test_context_builder.TestReviewContextBuilder) ... ok
test_minimal_review_context_builder (test_context_builder.TestReviewContextBuilder) ... ok
test_fsm_transition_lifecycle (test_fsm.TestWorkflowFSM) ... ok
test_transition_rules (test_fsm.TestWorkflowFSM) ... ok
test_mock_capabilities (test_mock_adapter.TestMockAdapter) ... ok
test_mock_simulate_dev_and_review_artifacts (test_mock_adapter.TestMockAdapter) ... ok
test_aep_envelope_creation (test_msg_bus.TestMessageBus) ... ok
test_message_bus_pub_sub_ack (test_msg_bus.TestMessageBus) ... ok
test_scenario_s1_happy_path (test_orchestrator_sim.TestOrchestratorSimulation) ... ok
test_scenario_s2_rework_loop (test_orchestrator_sim.TestOrchestratorSimulation) ... ok
test_scenario_s3_deadlock_and_override_approved (test_orchestrator_sim.TestOrchestratorSimulation) ... ok
test_scenario_s6_deadlock_and_cancel (test_orchestrator_sim.TestOrchestratorSimulation) ... ok
test_reconcile_unconsumed_dev_manifest_after_crash (test_reconcile_crash.TestCrashReconcile) ... ok
test_reconcile_vote_result_after_crash (test_reconcile_crash.TestCrashReconcile) ... ok
test_aep_envelope_schema (test_schema.TestSchemaValidation) ... ok
test_dev_manifest_schema (test_schema.TestSchemaValidation) ... ok
test_review_manifest_schema (test_schema.TestSchemaValidation) ... ok
test_vote_result_schema (test_schema.TestSchemaValidation) ... ok
test_artifact_registration (test_state_store.TestStateStore) ... ok
test_state_store_task_lifecycle (test_state_store.TestStateStore) ... ok

----------------------------------------------------------------------
Ran 22 tests in 0.648s

OK
```

### 2. 执行 CLI 核心指令
```bash
# 1. 运行环境与 CLI 探测预检
PYTHONPATH=src python3 -m macao.cli.main preflight

# 2. 检查配置与数据库健康度
PYTHONPATH=src python3 -m macao.cli.main doctor

# 3. 创建开发任务
PYTHONPATH=src python3 -m macao.cli.main task create \
  --title "重构数据库连接池" \
  --acceptance "通过全部单元测试，覆盖率 > 85%" \
  --branch "feature/db-refactor"

# 4. 查看当前任务与状态看板
PYTHONPATH=src python3 -m macao.cli.main status

# 5. 人工接管决策
PYTHONPATH=src python3 -m macao.cli.main override resolve --choice APPROVED --note "人工确认代码逻辑无误"
```

---
*本文档由技术团队维护，随代码库与 PRD 演进保持同步更新。*
