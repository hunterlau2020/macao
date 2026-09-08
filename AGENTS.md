# Repository Guidelines

## Project Structure & Module Organization

MACAO (Multi-Agent CLI Agent Orchestrator) lives in `src/macao/`. Its key architectural modules are organized as follows:
- `src/macao/core/`: Core definitions, JSON Schema contracts (`docs/schemas/`), and configuration manager (`ConfigManager`).
- `src/macao/workflow/`: Workflow FSM (`WorkflowFSM`), state transition engine (`TransitionTable`), orchestrator central controller (`Orchestrator`), dynamic prober (`TeamProber`), live runner (`LiveWorkflowRunner`), and background daemon (`OrchestratorDaemon`).
- `src/macao/adapter/`: AI CLI runtime adapters (`ClaudeCodeAdapter`, `CodexAdapter`, `OpenCodeAdapter`, `AntigravityAdapter`, `CursorAgentAdapter`, `KimiAdapter`, `MockAgentAdapter`) and PTY session wrapper (`PTYSession`).
- `src/macao/consensus/`: Consensus evaluation engine (`ConsensusEngine`) and vote aggregator (`VoteAggregator`).
- `src/macao/storage/`: SQLite state store (`StateStore`, `DatabaseManager`) and crash recovery reconciler (`StateReconciler`).
- `src/macao/merge/`: Merge pipeline controller (`MergeController`).
- `src/macao/utils/`: Infrastructure utilities including Git manager (`GitManager`), ANSI stripper (`strip_ansi`), review context builder (`ReviewContextBuilder`), and logger.
- `src/macao/cli/`: Click commands (`main.py`), Rich UI renderer (`ui.py`), and interactive init wizard (`wizard.py`).
- `tests/`: Comprehensive unit and integration tests (164 tests passing).

## Build, Test, and Development Commands

Run commands from project root `/home/debian/macao`:

```bash
# 1. Run all unit and integration tests (164 tests)
python3 -m unittest discover tests

# 2. Run specific test file
python3 -m unittest tests/test_team_probe_and_dispatch.py

# 3. Dynamic team and environment probe (strictly read-only)
python3 -m macao.cli.main probe --dry-run

# 4. Probe as JSON
python3 -m macao.cli.main probe --json

# 5. Run static health diagnosis (pure read-only)
python3 -m macao.cli.main doctor

# 6. View probe audit logs
python3 -m macao.cli.main logs --probe
```

## Coding Style & Naming Conventions

- Target Python 3.10+ with type hints (`typing.Optional`, `typing.List`, `typing.Dict`, `typing.Tuple`).
- Follow standard PEP 8 naming: `snake_case` for functions, variables, and modules; `PascalCase` for classes and dataclasses; `UPPER_CASE` for constants and enum members.
- Fail-Closed Principle: If a configuration, CLI tool, or Schema is unrecognized or invalid, fail fast and reject progression; never fabricate synthetic approvals or ignore schema violations.
- Non-Destructive / Read-Only Probing: All probe and doctor commands must be strictly read-only (`mode=ro`), never creating SQLite files, tables, or Git commits as side effects.

## Testing Guidelines

- Standard framework is Python `unittest` (compatible with `pytest`).
- Test files live in `tests/test_*.py`.
- Always use `tempfile.mkdtemp()` and restore original working directory in `tearDown()` to prevent test cross-contamination.
- Never make real LLM API calls in automated tests; use `MockAgentAdapter` or mock CLI subprocesses.

## 项目状态速览 (memory, 更新于 2026-09-08)

> 给新会话的快速上下文；详细技术说明见 `docs/TECH_INTRODUCE.md`、操作指南见 `docs/CLI_OPERATIONAL_GUIDE.md`。

1. **系统定位与不介入原则（PRD §1 & PRODUCT-FACTS.md）**：
   - MACAO 是外层**流程编排器与物理产物信差**，绝不代替审查员做业务语义判断或篡改业务 Diff。
   - 执行者负责编写代码自评，审查员独立在沙箱中给出裁定（`.review.yml`），MACAO 负责路由、仲裁与状态推进。

2. **动态运行态探活规范（`macao probe` 与 `preflight` 的严格分工）**：
   - **`preflight` 专司基础设施预检**：检查本地 CLI 安装路径与版本（`shutil.which` + `<cli> --version`）；
   - **`probe` 专司项目鲜活运行态**：
     - **SessionLocator 会话发现**：自动定位 `agy`, `claude`, `opencode`, `codex`, `agent/cursor`, `kimi` 本地活跃 session，获取最近活动时间与上下文；
     - **Git 与评审物理事实对账（三问进度）**：结合最新 commit 与 `docs/reviews/` 下的 `*-review-request-*.md`，精准推断 **上一个完成任务 (Last)**、**当前任务 (Now)** 与 **下一步计划 (Next)**，杜绝假空报 `IDLE`；
     - **严格只读零副作用**：SQLite 只读连接（`file:...state.db?mode=ro`），绝不擅自初始化 DDL；
     - **全流程日志留痕**：探活审计完整记录至 `.macao/logs/probe/probe_<timestamp>.log`，支持 `macao logs --probe` 随时溯源。

3. **工作区（Worktree）如实探测而非硬编**：
   - **工作区是可选的**：评审规范与实际项目中，隔离 Worktree 只是沙箱手段之一，单仓项目直接使用 `In-repo (Shared Workspace)`，绝不硬编虚构的 `.macao/worktrees/... (NOT_SPAWNED)` 路径；
   - **真实 Git 探查**：通过 `git worktree list --porcelain` 检视本地实际挂载的工作树，如实呈现。

4. **终端会话日志（PTY Transcript Logs）机制**：
   - 探活阶段自动落盘探活审计日志至 `.macao/logs/probe/`；
   - 审查阶段由 `PTYSession` 实时截获终端输出、剥离 ANSI 码并落盘至 `.macao/logs/reviewers/<reviewer_id>_r<round>.log`，支持 `macao logs -r <id>` 随时审计。

5. **当前测试与交付状态**：
   - 164 项测试全部通过（`Ran 164 tests in 94s, OK`）；
   - 主干分支保持清洁并与 `origin/main` 实时同步。

6. **研发方法论：实战实操先于纸面定论（拒绝纯纸上谈兵）**：
   - 涉及多 Agent CLI 进程组、PTY 交互、Session 发现与 Worktree 沙箱的复杂机制，光靠纸面推演无法想透；
   - 必须先在真实工程（如 `english_learning_system`，场景 C）中实操演练，暴露真实深水区物理问题后，返回代码库深度打磨自愈，再带着实操证据合并提审。
