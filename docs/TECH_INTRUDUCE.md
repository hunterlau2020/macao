# MACAO 技术架构与技术实现说明文档 (TECH_INTRODUCE)

> **文档定位**：记录 MACAO (Multi-Agent CLI Agent Orchestrator) 的整体技术架构、已落地的核心技术组件选型、各模块职责分工、CLI 交互界面的实现方案、以及与全屏 TUI 的对比演进。  
> **权威标准**：[`docs/MACAO_PRD_v2.md`](MACAO_PRD_v2.md)（权威产品方案）与 [`docs/schemas/`](schemas/)（版本化契约）。

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
  │  └─ KimiAdapter (Sandboxed 模式，独立 git worktree 隔离评审)          │
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
| **测试框架** | 单元与集成测试 | `unittest` (兼容 `pytest`) | 覆盖 Schema 校验、状态机流转、共识判定、状态存储与消息总线的完整测试套件。 |

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

## 四、工程源码目录结构与模块说明

```text
macao/
├── pyproject.toml              # 项目打包与依赖定义
├── macao.yaml                  # 默认示例配置文件
├── .gitignore                  # Git 忽略规则
├── docs/                       # 设计文档与机器契约
│   ├── MACAO_PRD_v2.md         # 权威基准 PRD
│   ├── TECH_INTRODUCE.md       # 本文档（技术架构与实现说明）
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
│   │   └── kimi.py             # KimiAdapter（Sandboxed + Worktree 模式）
│   ├── consensus/              # 共识与仲裁引擎
│   │   ├── engine.py           # 2/3 多数 + 2 票最低法定人数算法（PRD §2.3）
│   │   └── vote.py             # .review.yml 收集与 vote_result.json 生成
│   ├── workflow/               # 状态识别与 FSM 编排
│   │   ├── state_engine.py     # 三层识别与作用域产物读取（PRD §3.2）
│   │   ├── transitions.py      # 统一状态转移表（E1~E10 规则校验）
│   │   └── fsm.py              # 10 状态 FSM 驱动器与产物归档
│   ├── merge/                  # 合并控制器
│   │   └── controller.py       # MERGING 流水线（检出、FF merge、CI gate、push）
│   ├── utils/                  # 基础设施工具
│   │   ├── ansi.py             # ANSI 转义序列清洗工具
│   │   └── git_utils.py        # Git 命令封装与 Worktree 独立沙箱管理
│   └── cli/                    # 命令行交互入口
│       ├── ui.py               # Rich 表格、仪表盘与诊断渲染
│       └── main.py             # CLI 命令集合（preflight, init, doctor, task...）
└── tests/                      # 自动化测试套件（12 项测试用例全部通过）
```

---

## 五、运行与验证指引

### 1. 运行自动化测试套件
```bash
PYTHONPATH=src python3 -m unittest discover tests -v
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
