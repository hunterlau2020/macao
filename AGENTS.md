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
- `tests/`: Comprehensive unit and integration tests (126 tests passing).

## Build, Test, and Development Commands

Run commands from project root `/home/debian/macao`:

```bash
# 1. Run all unit and integration tests (126 tests)
python3 -m unittest discover tests

# 2. Run specific test file
python3 -m unittest tests/test_team_probe_and_dispatch.py

# 3. Dynamic team and environment probe (strictly read-only)
python3 -m macao.cli.main probe --dry-run

# 4. Probe as JSON
python3 -m macao.cli.main probe --json

# 5. Run static health diagnosis (pure read-only)
python3 -m macao.cli.main doctor
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

## 项目状态速览 (memory, 更新于 2026-09-07)

> 给新会话的快速上下文；详细技术说明见 `docs/TECH_INTRODUCE.md`、操作指南见 `docs/CLI_OPERATIONAL_GUIDE.md`。

1. **系统定位与不介入原则（PRD §1 & PRODUCT-FACTS.md）**：
   - MACAO 是外层**流程编排器与物理产物信差**，绝不代替审查员做业务语义判断或篡改业务 Diff。
   - 执行者负责编写代码自评，审查员独立在沙箱中给出裁定（`.review.yml`），MACAO 负责路由、仲裁与状态推进。

2. **动态探活规范（`macao probe` 与 `--dry-run`）**：
   - **真实本地探活**：调用本地子进程 `shutil.which` + `<cli> --version` 探活已安装的真实 CLI（如 `agy 1.1.27`, `opencode 1.18.29`, `agent 2026.09.02-c22c1a3`, `claude 2.1.263`, `codex 2.1.0`），**严禁在探活阶段调用 LLM**。
   - **严格只读零副作用**：通过 `file:...state.db?mode=ro` 连接 SQLite；若 `.macao/state.db` 不存在，绝不创建文件或初始化 DDL。
   - **场景 C（已有项目接管）识别**：若 `state.db` 无任务，但 Git 检测到未提交修改（Dirty files），准确识别并展示为 **`ACTIVE_DEV (UNTRACKED)`**，指引开发者通过 `macao task create` 纳管，绝不机械报 `IDLE`。

3. **审查员工作区（Worktree）生命周期**：
   - **按需延迟挂载（Ephemeral & Lazy-allocated）**：任务未提审时，Reviewer 工作区状态为 `(NOT_SPAWNED)`，不占磁盘与 Git 锁。
   - **提审挂载**：仅在 `macao task checkpoint --review` 触发时，通过 `git worktree add --detach .macao/worktrees/<rev_id>/<task_id>/r<round> <commit>` 建立独立隔离沙箱。
   - **评审终局清理**：投票完成并归档后，原子执行 `git worktree remove --force` 彻底卸载。

4. **终端会话日志（PTY Transcript Logs）机制**：
   - 探活阶段不启动评审会话，不调起长周期 AI，因此探活期日志为空。
   - 审查阶段由 `PTYSession` 实时截获终端输出、剥离 ANSI 码并落盘至 `.macao/logs/reviewers/<reviewer_id>_r<round>.log`，支持 `macao logs -r <id>` 随时审计。

5. **当前测试与交付状态**：
   - 126 项测试全部通过（`Ran 126 tests in 46.136s, OK`）；
   - 主干分支保持清洁并与 `origin/main` 实时同步。
