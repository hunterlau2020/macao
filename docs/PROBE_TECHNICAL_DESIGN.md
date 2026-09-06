# MACAO 动态运行态探活系统技术设计说明书 (MACAO Probe Technical Design)

> **文档定位**：深入阐述 MACAO 体系中 `macao probe`（及 `macao task probe`）的系统用途、设计原则、底层架构、会话发现机制、物理事实对账算法与审计留痕体系。
> **权威关联**：
> - 产品契约基准：[`docs/MACAO_PRD_v2.md`](MACAO_PRD_v2.md)（权威 PRD v2.3.1）
> - 核心行为准则：[`docs/usercases/PRODUCT-FACTS.md`](usercases/PRODUCT-FACTS.md)（MACAO 业务不介入原则）
> - 实操操作手册：[`docs/CLI_OPERATIONAL_GUIDE.md`](CLI_OPERATIONAL_GUIDE.md)
> - 核心代码实现：[`src/macao/workflow/prober.py`](../src/macao/workflow/prober.py)、[`src/macao/adapter/session_locator.py`](../src/macao/adapter/session_locator.py)

---

## 目录

- [一、背景与问题定义](#一背景与问题定义)
  - [1. 为什么多 Agent 编排需要动态探活？](#1-为什么多-agent-编排需要动态探活)
  - [2. 传统探活与动态探活的混淆痛点](#2-传统探活与动态探活的混淆痛点)
  - [3. 场景 C：接管已有开发项目的核心诉求](#3-场景-c接管已有开发项目的核心诉求)
- [二、核心设计原则 (Core Principles)](#二核心设计原则-core-principles)
  - [1. 不介入业务原则 (Non-Intervention)](#1-不介入业务原则-non-intervention)
  - [2. 严格只读零副作用原则 (Zero-Mutation Guarantee)](#2-严格只读零副作用原则-zero-mutation-guarantee)
  - [3. 零 LLM / Token 开销原则 (Zero-LLM Overhead)](#3-零-llm--token-开销原则-zero-llm-overhead)
  - [4. 全流程可验证留痕原则 (Audit Trail)](#4-全流程可验证留痕原则-audit-trail)
- [三、核心架构与组件剖析](#三核心架构与组件剖析)
  - [1. 整体探活架构全景图](#1-整体探活架构全景图)
  - [2. 原生会话定位器 (SessionLocator)](#2-原生会话定位器-sessionlocator)
  - [3. 物理事实对账与开发进度三元组 (Progress Triplet)](#3-物理事实对账与开发进度三元组-progress-triplet)
  - [4. 审查员真实工作区探测机制 (True Worktree Detection)](#4-审查员真实工作区探测机制-true-worktree-detection)
  - [5. 法定共识仲裁门槛分析 (Quorum Readiness)](#5-法定共识仲裁门槛分析-quorum-readiness)
- [四、全链路审计日志系统 (Probe Logging)](#四全链路审计日志系统-probe-logging)
  - [1. 探活日志的生命周期与落盘结构](#1-探活日志的生命周期与落盘结构)
  - [2. 命令行查阅体验 (macao logs --probe)](#2-命令行查阅体验-macao-logs---probe)
- [五、命令边界与职责矩阵 (Preflight vs Probe vs Doctor vs Status)](#五命令边界与职责矩阵-preflight-vs-probe-vs-doctor-vs-status)
- [六、实战验证案例 (以 english_learning_system 为例)](#六实战验证案例-以-english_learning_system-为例)

---

## 一、背景与问题定义

### 1. 为什么多 Agent 编排需要动态探活？
在传统的单 Agent 对话或单 CLI 使用模式中，人类工程师自行感知上下文与执行进度。但在 **MACAO 多 Agent 协同体系** 中，存在以下复合风险：
1. **盲目派发导致死锁**：若配置了 4 人评审团，但其中 2 个 CLI 本地未安装或版本不兼容，共识引擎（需 3/4 赞成）将永久无法达成仲裁，任务直接陷入死锁。
2. **工作区状态冲突**：执行者（Executor）可能正在写代码且有脏改动，盲目新建任务或切换分支将导致代码被冲刷覆盖或产生大量冲突。
3. **上下文断裂**：CLI 客户端（如 `agy`、`opencode`、`claude`）可能在之前的交互中已经建立了具备深厚上下文的对话 Session。如果编排器每次都机械地开启新 Session，将导致巨大的上下文重学成本和 Token 浪费。

### 2. 传统探活与动态探活的混淆痛点
在早期设计中，探活功能容易陷入两个极端：
- **静态预检误当探活**：仅运行 `--version` 检查可执行文件是否存在，并查询空的 `state.db`，从而机械地向用户报出 `IDLE: waiting for task dispatch`。但实际上，执行者已经在编写核心功能，甚至已经在进行第 44 轮的评审修复。这种虚假空报引发了“编排器数据全靠编”的信任危机。
- **臆测虚假工作区**：在输出中硬编码类似 `.macao/worktrees/<rev_id> (NOT_SPAWNED)` 的路径假象，忽视了大部分单仓项目采用原地直接评审（In-repo Shared Workspace）的客观事实。

### 3. 场景 C：接管已有开发项目的核心诉求
当把 MACAO 引入一个已经在使用 AI 进行开发、此前采用人工介入审查的项目（即典型的“场景 C”，如 `english_learning_system`）时：
- 项目中已经存在 Git 提交历史；
- 物理目录中已经存在由人类或前置脚本生成的评审申请单（`docs/reviews/*-review-request-*.md`）与评审结果（`docs/reviews/*-review-result-*.md`）；
- 底层 CLI 已经有正在交互的会话。

编排器必须能够在**不破坏任何现有状态、不写入数据库、不调用大模型**的前提下，精准识别项目真实运行态。

---

## 二、核心设计原则 (Core Principles)

根据 [`docs/usercases/PRODUCT-FACTS.md`](usercases/PRODUCT-FACTS.md) 与 PRD §1，MACAO 确立了四项不可动摇的探活工程原则：

### 1. 不介入业务原则 (Non-Intervention)
> **MACAO 是外层流程编排器与物理产物信差，绝不代替审查员做业务语义判断，绝不篡改业务 Diff，绝不假造虚假进度。**

执行者负责编写代码并自评，审查员独立在沙箱或代码库中给出裁定（`.review.yml`）。MACAO 不得在探活中替 Executor “想当然”地编造任务标题或业务意图，所有当前状态与进度必须 100% 依托底层物理事实推导。

### 2. 严格只读零副作用原则 (Zero-Mutation Guarantee)
`macao probe`（尤其是带 `--dry-run` 模式）必须保证：
- 数据库连接严格使用 SQLite 只读 URI：`file:<path>/state.db?mode=ro`；
- 若代码库尚未初始化（`.macao/state.db` 不存在），**绝对不自动执行 DDL，绝对不创建空数据库文件或空目录**；
- 绝对不产生任何 Git commit、tag 或暂存变动；
- 保证任何在未初始化或第三方项目上的探活操作均具备 **100% 幂等与无痕性**。

### 3. 零 LLM / Token 开销原则 (Zero-LLM Overhead)
- 探活的目标是验证“运行态基础设施与共识可达性”；
- 探活全过程仅在本地进行毫秒级系统探针调用（`shutil.which` + 子进程 `--version` + 读取本地 session 存储 + Git 命令行解析）；
- **严禁向任何大模型 API 发起请求**，确保探测速度 <1 秒，零网络阻塞，零 Token 费用。

### 4. 全流程可验证留痕原则 (Audit Trail)
- 探活不能是黑匣子，所有探活探测链路、CLI 响应细节、解析出的 Session ID 与共识计算依据必须实时落盘至 `.macao/logs/probe/probe_<timestamp>.log`；
- 提供第一类 CLI 命令 `macao logs --probe`（或 `macao logs -p`），支持随时溯源核对，确保透明可信。

---

## 三、核心架构与组件剖析

### 1. 整体探活架构全景图

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         macao probe [--dry-run]                             │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                  TeamProber (src/macao/workflow/prober.py)                  │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │                                                                             │
 │  1. 本地 CLI 版本探测                                                       │
 │     ├─ shutil.which("<cli>") 路径扫描                                       │
 │     └─ <cli> --version 毫秒级子进程调用                                     │
 │                                                                             │
 │  2. 原生会话发现 (SessionLocator)                                           │
 │     ├─ agy: ~/.gemini/antigravity-cli/history.jsonl                         │
 │     ├─ claude: ~/.claude/projects/<repo-sanitized>/                         │
 │     ├─ opencode: ~/.local/share/opencode/opencode.db (SQLite)               │
 │     ├─ codex: ~/.codex/session_index.jsonl                                  │
 │     └─ agent: ~/.cursor/chats/                                              │
 │                                                                             │
 │  3. 物理事实对账 (Progress Triplet 推导)                                    │
 │     ├─ Last: git log -n 5 提取最新功能 Commit                               │
 │     ├─ Now:  解析 docs/reviews/*-review-request-*.md 及 git status 脏改动   │
 │     └─ Next: 解析 docs/reviews/*-review-result-*.md 待落票审查员名单        │
 │                                                                             │
 │  4. 真实工作树探测 (True Worktree Inspection)                               │
 │     ├─ git worktree list --porcelain 扫描底层挂载                           │
 │     └─ 如实报告: In-repo (Shared Workspace) 或实际独立 Worktree 物理路径    │
 │                                                                             │
 │  5. 法定仲裁门槛分析 (Quorum Readiness)                                     │
 │     ├─ 统计活跃就绪审查员数 vs 门槛 (minimum_winning_seats / weight_quorum) │
 │     └─ 判定共识是否可达 (ACHIEVABLE / BLOCKED)                              │
 │                                                                             │
 └──────────────────────┬───────────────────────────────┬──────────────────────┘
                        │                               │
                        ▼                               ▼
 ┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
 │       Rich 彩色矩阵终端看板           │  │   探活审计日志落盘                 │
 │       (src/macao/cli/ui.py)          │  │   .macao/logs/probe/probe_*.log   │
 └──────────────────────────────────────┘  └───────────────────────────────────┘
```

---

### 2. 原生会话定位器 (SessionLocator)

[`SessionLocator`](file:///home/debian/macao/src/macao/adapter/session_locator.py) 专门解决“编排器如何感知各 CLI 当前正在哪个原生会话中”的难题。

#### 支持的 CLI 及其底层存储映射机制：

| CLI 工具 | 适配器名称 | 会话持久化底层机制 | SessionLocator 探测定位策略 |
|---|---|---|---|
| **Google Antigravity (`agy`)** | `AntigravityAdapter` | `~/.gemini/antigravity-cli/history.jsonl` | 按行逆向读取 JSON Lines，匹配 `workspace == str(project_root)`，提取最新记录的 `conversationId` 与时间戳。 |
| **Claude Code (`claude`)** | `ClaudeCodeAdapter` | `~/.claude/projects/-<sanitized-project-path>/` | 扫描该目录下所有 `<session-uuid>.jsonl` 会话文件，按文件最后修改时间（`mtime`）倒序排序，获取最新会话的 UUID。 |
| **OpenCode (`opencode`)** | `OpenCodeAdapter` | `~/.local/share/opencode/opencode.db` | 以只读模式连接本地 SQLite 数据库，查询 `session` 表中对应 `directory` 的最新 `id` 与 `time_updated`。 |
| **Codex CLI (`codex`)** | `CodexAdapter` | `~/.codex/session_index.jsonl` | 逆向扫描索引文件，提取最近匹配当前项目根目录的会话哈希/ID。 |
| **Cursor Agent (`agent`)** | `CursorAgentAdapter` | `~/.cursor/chats/` 或状态存储 | 扫描对应 workspace 的元数据索引文件，定位最近一次对话会话。 |
| **Kimi CLI (`kimi`)** | `KimiAdapter` | 会话元数据目录 | 读取持久化配置文件中的活跃 session key。 |

#### 特性优势：
- **物理只读**：仅读取本地元数据文件，不启动任何 CLI 会话交互；
- **自愈式回退**：若某个 CLI 尚未在该项目创建过会话，返回 `None` 并优雅降级为 `No active session`，绝不抛出未捕获异常；
- **上下文继承**：支持后续在派发任务或人工恢复时，通过 resume 参数直接接续该会话。

---

### 3. 物理事实对账与开发进度三元组 (Progress Triplet)

编排器绝不通过 AI 假造进度，而是通过“**物理事实对账（Physical Fact Reconciliation）**”构建开发进度三元组：

$$\text{Progress Triplet} = \langle \text{Last}, \text{Now}, \text{Next} \rangle$$

```text
               Git Commit Log           docs/reviews/ 评审产物          Reviewers 状态
                     │                           │                            │
                     ▼                           ▼                            ▼
              ┌──────────────┐            ┌──────────────┐             ┌──────────────┐
              │     Last     │            │     Now      │             │     Next     │
              │  已完成提交  │            │  当前工作态  │             │  下一步计划  │
              └──────────────┘            └──────────────┘             └──────────────┘
```

1. **`Last`（上一个完成的任务）**：
   - 执行 `git log -n 5 --pretty=format:%h|%s`，自动过滤 `merge` 或 `chore` 等琐碎提交；
   - 提取最近由 Executor 提交的功能性 Commit Hash 与提交说明（例如：`Commit 1ad706b: fix(learn): 五家评审修复批 (round 44)`）。
2. **`Now`（当前正在进行的工作态）**：
   - 扫描项目根目录下的 `docs/reviews/`：
     - 若存在最新的 `*-review-request-*.md`，且尚未达成终局裁决，立即将状态标定为：`REVIEW_PENDING`，当前任务明确为 `Pending Review Request: <filename> (Baseline: <sha>)`；
     - 若存在未暂存或已暂存的文件（通过 `git status --porcelain`），则标定为 `Active Coding (<n> modified files)`；
     - 若完全干净且无待审单，标定为 `IDLE: Standby for next dispatch`。
3. **`Next`（下一步计划）**：
   - 若处于 `REVIEW_PENDING`：比对提审单要求的审查员与当前已生成的 `*-review-result-*.md`，列出待落票的审查员名单：`Await reviewer evaluations [rev-opencode, rev-cursor...] before next commit`；
   - 若处于 `Active Coding`：指引执行者提交检查点（`macao task checkpoint`）；
   - 若处于空闲状态：指引创建新任务（`macao task create`）。

---

### 4. 审查员真实工作区探测机制 (True Worktree Detection)

在多 Agent 协同体系中，Reviewer 物理工作区的存在形式遵循**真实反映原则**：

```text
                       git worktree list --porcelain
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
       存在独立隔离沙箱 Worktree                  未挂载独立隔离 Worktree
                 │                                       │
                 ▼                                       ▼
  .macao/worktrees/<rev>/<task>/r<round>        In-repo (Shared Workspace)
         (ACTIVE @ <commit>)                       (Direct / Read-Only)
```

1. **摒弃机械占位符**：
   - 早期版本输出类似 `.macao/worktrees/rev-opencode (NOT_SPAWNED)`，给用户造成“系统故障或初始化未完成”的误解；
   - 实际上，根据审查规范，工作区隔离是按需可选的策略，单代码库项目完全支持原地直接审查。
2. **基于 Git 真实工作树探查**：
   - `TeamProber` 调用 `git worktree list --porcelain` 读取当前 Git 内部注册的所有工作树；
   - 若审查员已被分配独立的物理工作树（如提审后进入深度测试），如实展示路径与 HEAD 提交（`ACTIVE @ <commit>`）；
   - 若未分配独立工作树，如实展示为 **`In-repo (Shared Workspace / Direct Review)`**，清楚告知用户审查员正在当前代码库主工作区下以只读方式直接检视。

---

### 5. 法定共识仲裁门槛分析 (Quorum Readiness)

探活阶段必须防患于未然，提前计算审查团队的法定仲裁达成可能性：

- **输入指标**：
  - 配置的 Reviewer 席位数 $N$；
  - 探活就绪的 Reviewer 席位数 $R_{\text{ready}}$；
  - `macao.yaml` 中配置的法定赞成门槛 $M$（`minimum_winning_seats`，通常为 $\lceil 2N/3 \rceil$）；
  - `macao.yaml` 中配置的法定人数要求 $S$（`seat_quorum_required`）；
  - 权重阈值 $W_{\text{req}}$ 与当前可用权重和 $W_{\text{avail}}$。
- **仲裁可行性判定公式**：

$$\text{QuorumAchievable} = (R_{\text{ready}} \ge S) \land (R_{\text{ready}} \ge M) \land (W_{\text{avail}} \ge W_{\text{req}})$$

- 若任何条件不满足，探活判定为 **`BLOCKED`**，并在终端明确指出阻塞原因（例如：*“Executor 'dev-agy' is ready, but only 1/4 reviewers installed; quorum requires at least 3 seats. Task dispatch blocked.”*），阻断后续盲目派发。

---

## 四、全链路审计日志系统 (Probe Logging)

### 1. 探活日志的生命周期与落盘结构
每次执行 `macao probe`（无论是否带 `--dry-run`），`TeamProber` 均会生成一份不可变的结构化探活审计文件：
- **存储路径**：`.macao/logs/probe/probe_<YYYYMMDD_HHMMSS>.log`
- **内容组织**：
  1. 探活时间戳与 Dry-Run 运行模式标记；
  2. 执行者探活详情（CLI 名称、版本、原生会话 ID、当前 Worktree 路径、进度三元组）；
  3. 各 Reviewer 探活详情（CLI 名称、席位权重、版本、原生会话 ID、工作区形态、评审进展状态）；
  4. Git 仓库物理状态（分支名、HEAD SHA、脏文件统计）；
  5. 物理评审单解析结果（是否有挂起的提审请求、提审基准 Commit）；
  6. 法定共识就绪度判断与派发决议。

### 2. 命令行查阅体验 (`macao logs --probe`)
为确保探活审计日志方便查看，MACAO 在 `logs` 命令组中增加了专用的探活调阅入口：

```bash
# 查看最近一次动态探活审计日志
macao logs --probe

# 简写形式
macao logs -p
```

该命令会自动检索 `.macao/logs/probe/` 目录下按时间戳降序排列的最新日志文件，并以终端友好的格式高亮呈现。

---

## 五、命令边界与职责矩阵 (Preflight vs Probe vs Doctor vs Status)

为了避免概念混淆，下表明确界定了 MACAO 体系中四大监控与诊断命令的职责边界：

| 维度 | `macao preflight` | `macao probe` | `macao doctor` | `macao status` |
|---|---|---|---|---|
| **核心定位** | 宿主底层环境静态预检 | 项目动态运行态与团队探针 | 配置与基础设施健康体检 | 任务工单实时监控看板 |
| **依赖仓库** | 否（可在任意空目录运行） | **是**（必须在项目根目录运行） | **是**（检查当前项目 `macao.yaml`） | **是**（查询当前项目 `.macao/`） |
| **检查内容** | 系统 `PATH` 中的 6 款 CLI 安装情况与版本、Git/SQLite 支持 | 具体的 Executor / Reviewer 实时运行态、CLI Session ID、真实 Worktree、进度三元组、共识仲裁分析 | `macao.yaml` Schema 校验、SQLite WAL 读写完整性、孤儿 Worktree 检查 | 当前活跃任务的 FSM 状态、检查点、投票进展、产物归档 |
| **副作用** | 纯只读（0 修改） | 纯只读（仅落盘 probe 审计日志到 `.macao/logs/`，`--dry-run` 零 DB 写入） | 纯只读（只读校验） | 只读查询 SQLite 表 |
| **产出物** | 终端环境清单 | 终端多维矩阵看板 + `.macao/logs/probe/*.log` | 健康体检报告与修复建议 | 实时 Rich 表格监控看板 |

---

## 六、实战验证案例 (以 `english_learning_system` 为例)

在实际已有项目 `/home/debian/english_learning_system` 中执行动态探活的真实终端记录：

### 1. 执行探活命令
```bash
PYTHONPATH=/home/debian/macao/src python3 -m macao.cli.main probe --dry-run
```

### 2. 输出要点验证
1. **执行者与原生 Session 自动感知**：
   - 识别 CLI：`dev-agy (agy 1.1.27)`
   - 自动扫描并定位到活跃会话：`sess: b5640a62-8159-418a-95f7-da1d5c5a0043 (2026-09-05 17:50:05)`
2. **物理进度三元组准确推导**：
   - `Last`：`Commit 1ad706b: fix(learn): 五家评审修复批 — B1 索引命名空间/B2 合并式去重/IDEM-RACE 占位先行`
   - `Now`：`Review requested for commit 1ad706b: 评审申请 — 五家评审修复批`
   - `Next`：`Await reviewer evaluations and verdicts before next commit`
3. **Reviewer 工作区与评审状态准确推导**：
   - 4 位 Reviewer 均被准确标记为 `In-repo (Shared Workspace)`，无虚假路径；
   - 评审状态全部准确反映为 `AWAITING_REVIEW (@ 1ad706b)`；
   - 原生 Session 全部自动发现（如 `opencode` 发现 `ses_fb1844...`，`agent` 发现 `e3fd5151...`）。
4. **日志留痕可查**：
   - 终端末尾提示：`Audit Log: .macao/logs/probe/probe_20260907_020508.log | View with 'macao logs --probe'`；
   - 执行 `macao logs -p` 完整还原探测物理事实。

---
*本文档由 MACAO 核心架构团队制定，随系统演进持续维护。*
