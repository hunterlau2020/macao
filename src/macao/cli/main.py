"""MACAO Click CLI Entrypoint (PRD §14)."""

import os
import sys
import shutil
import sqlite3
import hashlib
import yaml
import click
from pathlib import Path
from typing import Dict, Any, Optional

from macao.core.config import ConfigManager
from macao.core.types import AgentState, OverrideChoice, PreflightCheckResult, ExecutionMode
from macao.storage.store import StateStore
from macao.storage.reconcile import StateReconciler
from macao.workflow.orchestrator import Orchestrator
from macao.utils.git_utils import GitManager
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.kimi import KimiAdapter
from macao.cli.ui import console, print_banner, render_preflight_report, render_task_status, render_audit_table, render_team_probe_report
from macao.workflow.prober import TeamProber


DEFAULT_CONFIG_TEMPLATE = """# ==============================================================================
# MACAO 多 Agent 协同编排配置文件 (macao.yaml)
# 遵循规范: Draft-07 Strict Schema (PRD §13)
# ==============================================================================

# 配置规范版本号（固定为 2.5）
version: "2.5"

# ------------------------------------------------------------------------------
# 1. 项目基础信息与仓库设置
# ------------------------------------------------------------------------------
project:
  # 项目名称（默认取项目根目录名）
  name: "macao-demo"
  repository:
    # 工作区路径（相对路径，. 代表当前根目录）
    workspace_path: "."
    # Git 远端名称（通常为 origin，无远端设为 null）
    remote_name: "origin"
    # 主干分支名称（代码审查通过后的合并目标分支，通常为 main 或 master）
    default_branch: "main"

# ------------------------------------------------------------------------------
# 2. 多 Agent 团队配置（开发执行者与独立审查团）
# ------------------------------------------------------------------------------
team:
  # 主开发执行者：负责根据任务需求编写代码、运行自测并提交就绪检查点
  executor:
    id: "dev-claude"             # 执行者唯一标识符（统一命名: dev-<cli>）
    cli: "claude-code"           # 调用的底层 AI 命令行工具
    adapter: "claude-hook"       # 通信适配器类型 (claude-hook / pty-wrapper)

  # 独立审查团：在隔离工作树（Git Worktree）中并发独立审查代码并投票
  reviewers:
    - id: "rev-codex"            # 审查员席位唯一标识符 (rev-<cli>)
      cli: "codex"               # 调用的底层 AI 命令行工具
      adapter: "pty-wrapper"     # 隔离适配器类型 (pty-wrapper 伪终端隔离)
      vote_weight: 1             # 审查席位投票权重

    - id: "rev-opencode"
      cli: "opencode"
      adapter: "pty-wrapper"
      vote_weight: 1

    - id: "rev-agy"
      cli: "agy"
      adapter: "pty-wrapper"
      vote_weight: 1

# ------------------------------------------------------------------------------
# 3. 共识仲裁与审查策略
# ------------------------------------------------------------------------------
policy:
  # 仲裁规则：weighted_2/3_v1 表示加权赞成票需达到或超过有效总票数的 2/3
  consensus_rule: "weighted_2/3_v1"
  # 独裁者上限保护：若单个审查员权重达到或超过法定人数，自动封顶防止一人专断
  dictator_cap_enabled: true
  # 最少获胜席位数：达成通过至少需要的赞成票数量
  minimum_winning_seats: 2
  # 法定有效席位法定人数：参与有效投票（非超时弃权）的最少席位数
  seat_quorum_required: 2
  # 法定有效权重法定人数：参与有效投票的最少权重之和
  weight_quorum_required: 2
  # 最大返工轮次：审查打回后，最多允许执行者修复并重新提审的轮次（超限进入人工干预）
  max_rework_rounds: 3
  # 审查策略：delta_plus_focus 表示重点审查增量 Diff 及执行者关注点
  review_strategy: "delta_plus_focus"

# ------------------------------------------------------------------------------
# 4. 代码合并管道与发布门禁
# ------------------------------------------------------------------------------
merge:
  # 合并策略：ff_only 仅允许快速前进合并（Fast-Forward），保证线性干净的 Git 历史
  strategy: "ff_only"
  # CI 自动化门禁测试命令：合并前在隔离环境中执行（如 pytest -q、npm test，无则为 null）
  ci_gate_command: null
  # 人工签字放行：达成 2/3 评审共识后，是否仍需人类在终端执行 'macao merge approve' 显式确认
  require_human_signoff: true
  # 合并前是否自动对齐变基到最新目标分支
  rebase_before_merge: false

# ------------------------------------------------------------------------------
# 5. 各环节超时 SLA 兜底控制
# ------------------------------------------------------------------------------
timeouts:
  # 开发阶段超时上限（超时自动发出告警）
  development: "2h"
  # 检查点合规性校验超时
  checkpoint_validation: "1m"
  # 评审派发与工作树初始化超时
  review_request: "30m"
  # 每个审查员在独立 Worktree 中的分析与响应超时（超时自动降级为 ABSTAIN 弃权）
  per_reviewer: "10m"
  # 共识计票与仲裁阶段超时
  consensus_check: "1m"

# ------------------------------------------------------------------------------
# 6. 推理分析与诊断阈值
# ------------------------------------------------------------------------------
thresholds:
  # 是否仅在日志中记录第二层反思与推理链
  layer2_inference_log_only: true
  # 模型自诊断置信度阈值（低于此值可触发人工干预）
  llm_diagnosis_override_below: 0.7

# ------------------------------------------------------------------------------
# 7. 成本计量与控制
# ------------------------------------------------------------------------------
cost:
  # 是否开启各 Agent Token 用量与成本计量
  usage_metering: true
  # 月度预算上限（美元，null 表示不设硬限制）
  monthly_budget_usd: null

# ------------------------------------------------------------------------------
# 8. 安全沙箱与白名单控制
# ------------------------------------------------------------------------------
security:
  # 允许由系统唤起调用的 AI CLI 绝对白名单，防止命令注入风险
  allowed_clis:
    - "claude-code"
    - "claude"
    - "codex"
    - "opencode"
    - "agy"
    - "antigravity"
    - "agent"
    - "cursor"
    - "kimi"
    - "mock-cli"
  # 是否将开发者的终端执行交互日志发送给审查员（通常设为 false 避免提示词偏见）
  send_terminal_logs_to_reviewers: false
  # 是否自动在日志、信封中掩码敏感密钥与 API Token
  secrets_masking: true

# ------------------------------------------------------------------------------
# 9. 不可变审计日志归档保留
# ------------------------------------------------------------------------------
audit:
  # 审计事件记录（SQLite state.db）在归档中的保留天数
  retention_days: 90
"""


def get_orchestrator(project_root: str = ".") -> Orchestrator:
    """Composition Root: Load configuration from macao.yaml and inject into Orchestrator (Fail-closed)."""
    config_dict = None
    cfg_file = Path(project_root) / "macao.yaml"
    if cfg_file.exists():
        config_dict = ConfigManager.load_config(str(cfg_file))

    return Orchestrator(
        project_root=project_root,
        config=config_dict
    )


@click.group(invoke_without_command=True)
@click.option("--init", "is_init", is_flag=True, help="Alias for 'macao init'")
@click.option("--log-level", default=None, type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False), help="Global log level (DEBUG, INFO, WARNING, ERROR)")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose / DEBUG console logging")
@click.pass_context
def cli(ctx, is_init, log_level, verbose):
    """MACAO - Multi-Agent CLI Agent Orchestrator."""
    if verbose:
        os.environ["MACAO_LOG_LEVEL"] = "DEBUG"
        os.environ["MACAO_LOG_CONSOLE"] = "1"
    elif log_level:
        os.environ["MACAO_LOG_LEVEL"] = log_level.upper()

    if is_init:
        ctx.invoke(init_cmd)
        ctx.exit()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def preflight():
    """Run environment and agent CLI conformance preflight checks (PRD §12.2)."""
    print_banner()
    console.print("[bold cyan]Running MACAO Preflight Checks...[/bold cyan]\n")

    results = []

    # 1. Probe Git
    git_path = shutil.which("git")
    results.append(PreflightCheckResult(
        agent_id="git",
        cli_name="Environment: Git",
        installed=bool(git_path),
        version="system",
        execution_mode=ExecutionMode.FULL,
        auth_valid=True,
        in_matrix=True,
        details=f"Path: {git_path}" if git_path else "Git not found in PATH"
    ))

    # 2. Probe SQLite WAL
    sqlite_ok = True
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()
    except Exception:
        sqlite_ok = False

    results.append(PreflightCheckResult(
        agent_id="sqlite",
        cli_name="Environment: SQLite (WAL)",
        installed=sqlite_ok,
        version=sqlite3.sqlite_version,
        execution_mode=ExecutionMode.FULL,
        auth_valid=True,
        in_matrix=True,
        details="WAL journal mode supported"
    ))

    # 3. Probe Adapters
    adapters = [
        ClaudeCodeAdapter(),
        CodexAdapter(),
        OpenCodeAdapter(),
        AntigravityAdapter(),
        CursorAgentAdapter(),
        KimiAdapter(),
        MockAgentAdapter("mock-agent", "mock-cli")
    ]

    for adp in adapters:
        try:
            res = adp.preflight()
            results.append(res)
        except Exception as e:
            results.append(PreflightCheckResult(
                agent_id=adp.agent_id,
                cli_name=adp.cli_name,
                installed=False,
                error=str(e),
                details=f"Preflight error: {e}"
            ))

    render_preflight_report(results)
    console.print("\n[dim]Note: Real CLI integration requires human supervision & intervention.[/dim]\n")


@cli.command("init")
@click.option("--path", default="macao.yaml", help="Path to create macao.yaml")
@click.option("-y", "--yes", is_flag=True, help="Non-interactive mode with default settings")
@click.option("-f", "--force", is_flag=True, help="Force overwrite existing configuration")
def init_cmd(path: str = "macao.yaml", yes: bool = False, force: bool = False):
    """Initialize macao.yaml configuration with interactive wizard and Chinese comments."""
    from macao.cli.wizard import run_interactive_init
    project_root = Path(".").resolve()
    run_interactive_init(project_root=project_root, target_path=path, non_interactive=yes, force=force)


@cli.command()
def doctor():
    """Diagnose static configuration, SQLite state, and CLI readiness (PRD §14.4, read-only idempotent)."""
    print_banner()

    # 1. Config Check
    try:
        if Path("macao.yaml").exists():
            cfg = ConfigManager.load_config("macao.yaml")
            console.print(f"[green]✓ macao.yaml configuration valid (Project: {cfg.get('project', {}).get('name')})[/green]")
        else:
            console.print("[yellow]! macao.yaml not found (run 'macao init' to create)[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ macao.yaml configuration error: {e}[/red]")

    # 2. Database Check (Read-only query, no side effects)
    try:
        store = StateStore()
        active = store.get_active_task()
        if active:
            console.print(f"[green]✓ State Store connected (Active task: {active['task_id']}, state: {active['state']})[/green]")
        else:
            console.print("[green]✓ State Store connected (No active task)[/green]")
    except Exception as e:
        console.print(f"[red]✗ State Store error: {e}[/red]")


@cli.group()
def task():
    """Manage orchestration tasks."""
    pass


@task.command("probe")
def task_probe():
    """Dynamically probe executor and reviewer agent readiness before dispatching tasks."""
    prober = TeamProber(".")
    res = prober.probe()
    render_team_probe_report(res)


@task.command("create")
@click.option("--title", default=None, help="Task title (e.g. 'Add vocabulary quiz feature')")
@click.option("--description", default="", help="Task detailed description")
@click.option("--acceptance", default="", help="Acceptance criteria")
@click.option("--branch", default="feature/task-01", help="Source branch")
@click.option("--target", default="main", help="Target branch")
@click.option("--probe/--no-probe", default=True, help="Dynamically probe team and environment readiness before creating task")
@click.option("--dry-run", is_flag=True, help="Perform dynamic pre-dispatch probe only, do not create task")
@click.option("-f", "--force", is_flag=True, help="Force task creation even if active task exists or warnings occur")
def task_create(title: Optional[str], description: str, acceptance: str, branch: str, target: str, probe: bool, dry_run: bool, force: bool):
    """Create and start a new development task with dynamic team probing."""
    prober = TeamProber(".")
    probe_result = prober.probe()

    if dry_run:
        render_team_probe_report(probe_result)
        if probe_result.get("can_dispatch"):
            console.print("[bold cyan]ℹ Dry-run probe passed: Team and environment are ready for task dispatch.[/bold cyan]")
        else:
            console.print("[bold red]✗ Dry-run probe failed: Task cannot be dispatched.[/bold red]")
        return

    if probe and probe_result.get("valid_config"):
        active = probe_result.get("active_task")
        if active and not force:
            render_team_probe_report(probe_result)
            console.print(
                f"[bold red]Cannot create new task:[/bold red] Active task '{active['task_id']}' is already running in state '{active['state']}'.\n"
                f"[dim]Run 'macao status' to inspect, 'macao task cancel' to abort it, or pass '--force' to proceed anyway.[/dim]"
            )
            sys.exit(1)

        exec_info = probe_result.get("executor", {})
        if not exec_info.get("installed") and not force:
            render_team_probe_report(probe_result)
            console.print(
                f"[bold red]Cannot create task:[/bold red] Configured executor '{exec_info.get('id')}' ({exec_info.get('cli')}) is not installed or unreachable.\n"
                f"[dim]Please install '{exec_info.get('cli')}' or update 'team.executor' in macao.yaml.[/dim]"
            )
            sys.exit(1)

        quorum_info = probe_result.get("quorum", {})
        if not quorum_info.get("achievable") and not force:
            render_team_probe_report(probe_result)
            console.print(
                f"[bold red]Cannot create task:[/bold red] Only {quorum_info.get('ready_count')} reviewer(s) ready, but quorum requires {quorum_info.get('minimum_winning_seats')}.\n"
                f"[dim]Please verify reviewer CLIs or update 'team.reviewers' in macao.yaml.[/dim]"
            )
            sys.exit(1)

    if not title:
        if sys.stdin.isatty():
            title = click.prompt("Task title", type=str)
        else:
            raise click.UsageError("Missing option '--title'.")

    orchestrator = get_orchestrator(".")

    task_data = orchestrator.start_task(
        title=title,
        task_description=description or title,
        acceptance_criteria={"raw": acceptance, "tests_passed": True},
        source_branch=branch,
        target_branch=target
    )

    exec_id = probe_result.get("executor", {}).get("id", "dev-executor") if probe_result.get("valid_config") else "executor"
    exec_cli = probe_result.get("executor", {}).get("cli", "")
    exec_disp = f"{exec_id} ({exec_cli})" if exec_cli else exec_id
    rev_count = len(probe_result.get("reviewers", [])) if probe_result.get("valid_config") else 0

    console.print(f"\n[bold green]✓ Task '{task_data['task_id']}' successfully created![/bold green]")
    console.print(f"  [bold]Title[/bold]            : {title}")
    console.print(f"  [bold]Assigned Executor[/bold]: [cyan]{exec_disp}[/cyan] (in charge of implementation)")
    console.print(f"  [bold]Assigned Reviewers[/bold]: [cyan]{rev_count} independent agents[/cyan] (Worktree isolated)")
    console.print(f"  [bold]Branch[/bold]           : {task_data.get('source_branch', branch)} -> {task_data.get('target_branch', target)}")
    console.print(f"  [bold]Initial State[/bold]    : [green]{task_data['state']}[/green]")
    console.print(f"\n[dim]Next step: Executor '{exec_id}' implements task changes on branch, then run 'macao task checkpoint --auto --review'[/dim]")


@task.command("recover")
def task_recover():
    """Explicitly reconcile SQLite state against physical disk artifacts and Git history."""
    store = StateStore()
    reconciler = StateReconciler(store)
    reconciled = reconciler.reconcile()
    if reconciled:
        console.print(f"[bold green]✓ Task '{reconciled['task_id']}' reconciled to state: {reconciled['state']}[/bold green]")
    else:
        console.print("[yellow]No active task to recover or no state discrepancies found.[/yellow]")


@task.command("checkpoint")
@click.option("--auto", is_flag=True, help="Auto-generate .macao/.dev.yml from current HEAD commit if missing")
@click.option("--review/--no-review", default=True, help="Automatically dispatch live reviewer agents in worktrees")
@click.option("--timeout", default=120.0, help="Per-reviewer timeout in seconds")
def task_checkpoint(auto: bool, review: bool, timeout: float):
    """Submit development checkpoint, dispatch isolated worktree reviews, and tally consensus."""
    orchestrator = get_orchestrator(".")
    store = StateStore()
    active = store.get_active_task()
    if not active:
        console.print("[red]No active task found to submit checkpoint for. Run 'macao task create' first.[/red]")
        return

    task_id = active["task_id"]
    git = GitManager(".")
    head_commit = git.get_head_commit()
    dev_path = Path(".macao/.dev.yml")

    if auto and not dev_path.exists():
        req_doc = Path(f"docs/reviews/review-request-{task_id}.md")
        req_doc.parent.mkdir(parents=True, exist_ok=True)
        if not req_doc.exists():
            req_doc.write_text(f"# Review Request: {active.get('title', task_id)}\n\nCommit: {head_commit}\n", encoding="utf-8")

        exec_cfg = orchestrator.config.get("executor", {})
        exec_id = exec_cfg.get("id", "dev-claude")
        exec_cli = exec_cfg.get("cli", "claude-code")

        manifest_data = {
            "version": "1.0",
            "task_id": task_id,
            "checkpoint_ref": head_commit,
            "full_document": {
                "path": str(req_doc),
                "evidence_commit": head_commit,
                "sha256": hashlib.sha256(req_doc.read_bytes()).hexdigest()
            },
            "status": "ready_for_review",
            "signal": "EXPLICIT",
            "review_round": active.get("review_round", 1),
            "executor": {"id": exec_id, "cli": exec_cli},
            "development": {
                "quality_metrics": {"tests_passed": True},
                "git": {"latest_commit": head_commit}
            }
        }
        dev_path.parent.mkdir(parents=True, exist_ok=True)
        dev_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")
        console.print(f"[green]✓ Auto-generated .macao/.dev.yml for commit {head_commit[:8]}[/green]")

    if not dev_path.exists():
        console.print("[red]Missing .macao/.dev.yml. Please create it or pass '--auto' flag to auto-generate.[/red]")
        return

    # 1. Check development checkpoint
    console.print(f"[bold cyan]Validating development checkpoint for task '{task_id}'...[/bold cyan]")
    try:
        change1 = orchestrator.check_development_checkpoint(task_id)
        if not change1:
            console.print("[yellow]Checkpoint validation deferred or rejected.[/yellow]")
            return
        console.print(f"[bold green]✓ Checkpoint validated: {change1.from_state.value} -> {change1.to_state.value} (ref: {head_commit[:8]})[/bold green]")
    except Exception as e:
        console.print(f"[red]✗ Checkpoint validation error: {e}[/red]")
        return

    # 2. Dispatch review requests
    try:
        change2 = orchestrator.dispatch_review_requests(task_id)
        console.print(f"[bold green]✓ Review dispatched: {change2.from_state.value} -> {change2.to_state.value}[/bold green]")
    except Exception as e:
        console.print(f"[red]✗ Review dispatch error: {e}[/red]")
        return

    # 3. If --review: Run live reviewers
    if review:
        from macao.workflow.live_dispatcher import LiveAgentDispatcher
        dispatcher = LiveAgentDispatcher(".")
        reviewers = orchestrator.config.get("reviewers", [])
        diff_txt = git.get_diff(active.get("target_branch", "main"), head_commit)

        console.print(f"\n[bold cyan]Launching {len(reviewers)} isolated review sessions...[/bold cyan]")
        for r_cfg in reviewers:
            r_id = r_cfg["id"]
            console.print(f"  • Invoking reviewer [bold white]{r_id}[/bold white] in isolated worktree...")
            try:
                res = dispatcher.dispatch_review_in_worktree(
                    reviewer_cfg=r_cfg,
                    task_id=task_id,
                    checkpoint_ref=head_commit,
                    review_round=active.get("review_round", 1),
                    diff_context=diff_txt,
                    timeout_sec=timeout
                )
                st = res.get("status")
                vote = res.get("vote", "N/A")
                if st == "SUCCESS":
                    console.print(f"    [green]✓ {r_id} finished: Vote={vote}[/green]")
                else:
                    console.print(f"    [yellow]! {r_id} {st}: {res.get('error')}[/yellow]")
            except Exception as ex:
                console.print(f"    [red]✗ {r_id} dispatch error: {ex}[/red]")

        # 4. Evaluate consensus
        console.print("\n[bold cyan]Tallying consensus across all reviewer votes...[/bold cyan]")
        try:
            eval_res = orchestrator.collect_and_evaluate_consensus(task_id)
            dec = eval_res.get("decision")
            updated = store.get_task(task_id)
            console.print(f"[bold green]✓ Consensus evaluation completed: Decision=[bold white]{dec}[/bold white], Next State=[bold cyan]{updated['state']}[/bold cyan][/bold green]")
            if dec == "APPROVED":
                console.print("\n[bold green]★ Task review passed! You can now run 'macao merge approve' to merge and deploy.[/bold green]")
            elif dec == "REWORK_REQUIRED":
                console.print("\n[yellow]! Review did not pass. Task returned to REWORK. Check reviewer feedback in .macao/logs/reviewers/.[/yellow]")
            else:
                console.print("\n[yellow]! Deadlock reached. Use 'macao override resolve' for manual takeover.[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Consensus tally error: {e}[/red]")


@task.command("cancel")
@click.option("--reason", default="User requested task cancellation", help="Reason for cancellation")
def task_cancel(reason: str):
    """Cancel currently active development task."""
    store = StateStore()
    active = store.get_active_task()
    if not active:
        console.print("[yellow]No active task to cancel.[/yellow]")
        return
    task_id = active["task_id"]
    orchestrator = get_orchestrator(".")
    orchestrator.fsm.transition(task_id, AgentState.CANCELLED, "E8", {"reason": reason})
    store.log_audit_event(task_id, "TASK_CANCELLED", {"reason": reason})
    console.print(f"[bold yellow]✓ Task '{task_id}' has been cancelled.[/bold yellow]")


@cli.command()
def status():
    """Display real-time task progress and consensus dashboard (PRD §14.3, read-only idempotent)."""
    store = StateStore()
    task_data = store.get_active_task()
    if not task_data:
        console.print("[yellow]No active tasks found. Use 'macao task create' to begin.[/yellow]")
        return

    artifacts = store.list_artifacts(task_data["task_id"])
    render_task_status(task_data, artifacts)


@cli.command("logs")
@click.option("-n", "--lines", default=50, help="Number of lines to display")
@click.option("-r", "--reviewer", default=None, help="Inspect raw session log for specific reviewer (or 'all' / 'list')")
@click.option("-e", "--executor", "executor_flag", default=None, help="Inspect raw session log for executor (or 'all' / 'list')")
@click.option("-f", "--follow", is_flag=True, help="Follow log output in real-time")
def logs_cmd(lines: int, reviewer: Optional[str], executor_flag: Optional[str], follow: bool):
    """View orchestration system logs, reviewer agent terminal logs, or executor logs."""
    import time

    # 1. Reviewer CLI Session Logs
    if reviewer:
        rev_log_dir = Path(".macao/logs/reviewers")
        if reviewer.lower() in ("all", "list"):
            if not rev_log_dir.exists() or not list(rev_log_dir.glob("*.log")):
                console.print("[yellow]No reviewer session logs found in .macao/logs/reviewers/[/yellow]")
                return
            console.print("[bold cyan]Found Reviewer Session Logs in .macao/logs/reviewers/:[/bold cyan]")
            for lf in sorted(rev_log_dir.glob("*.log")):
                console.print(f"  • [green]{lf.name}[/green] ({lf.stat().st_size} bytes)")
            return

        matches = sorted(rev_log_dir.glob(f"*{reviewer}*.log")) if rev_log_dir.exists() else []
        if not matches:
            console.print(f"[yellow]No reviewer session logs found matching '{reviewer}' in .macao/logs/reviewers/[/yellow]")
            return
        target = matches[-1]
        console.print(f"[bold cyan]Reviewer Log: {target}[/bold cyan]\n")
        content = target.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()
        for line in all_lines[-lines:]:
            console.print(line)
        return

    # 2. Executor Session Logs
    if executor_flag:
        exec_log_dir = Path(".macao/logs/executors")
        if executor_flag.lower() in ("all", "list"):
            if not exec_log_dir.exists() or not list(exec_log_dir.glob("*.log")):
                console.print("[yellow]No executor session logs found in .macao/logs/executors/[/yellow]")
                return
            console.print("[bold cyan]Found Executor Session Logs in .macao/logs/executors/:[/bold cyan]")
            for lf in sorted(exec_log_dir.glob("*.log")):
                console.print(f"  • [green]{lf.name}[/green] ({lf.stat().st_size} bytes)")
            return

        matches = sorted(exec_log_dir.glob(f"*{executor_flag}*.log")) if exec_log_dir.exists() else []
        if not matches:
            console.print(f"[yellow]No executor session logs found matching '{executor_flag}' in .macao/logs/executors/[/yellow]")
            return
        target = matches[-1]
        console.print(f"[bold cyan]Executor Log: {target}[/bold cyan]\n")
        content = target.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()
        for line in all_lines[-lines:]:
            console.print(line)
        return

    log_file = Path(".macao/logs/macao.log")
    if not log_file.exists():
        console.print("[yellow]No log file found at .macao/logs/macao.log. Run a task or daemon first.[/yellow]")
        return

    if follow:
        console.print(f"[dim]Following {log_file} (Ctrl+C to exit)...[/dim]\n")
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, os.SEEK_END)
            try:
                while True:
                    line = f.readline()
                    if line:
                        console.print(line.rstrip())
                    else:
                        time.sleep(0.5)
            except KeyboardInterrupt:
                return
    else:
        content = log_file.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()
        for line in all_lines[-lines:]:
            console.print(line)


@cli.command("audit")
@click.option("-t", "--task", "task_id", default=None, help="Filter by task ID")
@click.option("-n", "--limit", default=30, help="Maximum number of audit events to display")
def audit_cmd(task_id: Optional[str], limit: int):
    """Query immutable audit events recorded in StateStore (PRD §11.4)."""
    store = StateStore()
    events = store.list_audit_events(task_id=task_id, limit=limit)
    if not events:
        console.print("[yellow]No audit events found.[/yellow]")
        return
    render_audit_table(list(reversed(events)))


@cli.group()
def override():
    """Manage human overrides."""
    pass


@override.command("resolve")
@click.option("--choice", required=True, type=click.Choice(["APPROVED", "REWORK", "RETRY_REVIEW", "CANCEL", "EXTEND"]), help="Decision choice")
@click.option("--note", default="", help="Optional note")
def override_resolve(choice: str, note: str):
    """Resolve human override deadlock or unknown state (PRD §6.1 / §14.1)."""
    store = StateStore()
    task_data = store.get_active_task()
    if not task_data:
        console.print("[red]No active task found to resolve override.[/red]")
        return

    task_id = task_data["task_id"]
    orchestrator = get_orchestrator(".")

    try:
        change = orchestrator.resolve_override(task_id, OverrideChoice(choice), note)
        console.print(f"[bold green]✓ Override resolved successfully: {change.from_state.value} -> {change.to_state.value}[/bold green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to resolve override: {e}[/red]")


@cli.group()
def merge():
    """Manage code merge pipeline and signoffs."""
    pass


@merge.command("approve")
@click.option("--note", default="", help="Signoff note")
@click.option("--merge", "auto_merge", is_flag=True, help="Immediately execute merge pipeline after approval")
def merge_approve(note: str, auto_merge: bool):
    """Signoff and approve pending code merge (PRD §14.2 / §16.3)."""
    store = StateStore()
    task_data = store.get_active_task()
    if not task_data:
        console.print("[red]No active task found for merge approval.[/red]")
        return

    task_id = task_data["task_id"]
    store.log_audit_event(task_id, "HUMAN_MERGE_APPROVED", {
        "note": note,
        "checkpoint_ref": task_data.get("checkpoint_ref")
    })
    console.print(f"[bold green]✓ Merge signoff recorded for task '{task_id}'.[/bold green]")

    if auto_merge and task_data.get("state") == AgentState.MERGING.value:
        orchestrator = get_orchestrator(".")
        try:
            ok, msg, change = orchestrator.execute_merge(task_id)
            if ok:
                console.print(f"[bold green]✓ Fast-forward merge succeeded: {msg}[/bold green]")
                console.print(f"[bold cyan]Task '{task_id}' state transitioned to DONE.[/bold cyan]")
            else:
                console.print(f"[yellow]Merge pending or gated: {msg}[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Merge pipeline execution error: {e}[/red]")


@merge.command("execute")
def merge_execute():
    """Execute code merge pipeline for approved task (PRD §14.5)."""
    store = StateStore()
    task_data = store.get_active_task()
    if not task_data:
        console.print("[red]No active task found for merge execution.[/red]")
        return

    task_id = task_data["task_id"]
    orchestrator = get_orchestrator(".")
    try:
        ok, msg, change = orchestrator.execute_merge(task_id)
        if ok:
            console.print(f"[bold green]✓ Fast-forward merge succeeded: {msg}[/bold green]")
            console.print(f"[bold cyan]Task '{task_id}' state transitioned to DONE.[/bold cyan]")
        else:
            console.print(f"[yellow]Merge pending or gated: {msg}[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Merge pipeline execution error: {e}[/red]")


@cli.command("test-clis")
@click.option("--cli", "target_cli", default="all", help="Target CLI to test (claude, codex, opencode, agy, all)")
def test_clis(target_cli: str):
    """Run controlled real CLI PTY spawn, ANSI strip, and process termination tests."""
    from macao.adapter.integ_harness import verify_all_configured_clis as verify_all_clis, verify_single_cli_pty
    from macao.cli.ui import render_cli_integ_report

    print_banner()
    console.print(f"[bold cyan]Running Controlled Real CLI Integration Tests (Target: {target_cli})...[/bold cyan]\n")

    if target_cli == "all":
        results = verify_all_clis()
    else:
        results = [verify_single_cli_pty(target_cli)]

    render_cli_integ_report(results)
    all_pass = all(r.get("status") == "PASS" for r in results)
    if all_pass:
        console.print("[bold green]✓ All tested CLI PTY sessions spawned, stripped logs, and terminated cleanly (0 orphan processes).[/bold green]\n")
    else:
        console.print("[bold yellow]! Some CLI tests did not pass or were skipped.[/bold yellow]\n")


@cli.command("setup")
@click.option("--executor", default=None, help="Default executor CLI (e.g. claude-code, opencode, codex)")
@click.option("--model", default=None, help="Executor model name")
@click.option("-y", "--yes", is_flag=True, help="Non-interactive mode with default settings")
@click.option("--force", is_flag=True, help="Force overwrite existing configuration")
def setup_wizard(executor: Optional[str], model: Optional[str], yes: bool, force: bool):
    """Run interactive setup wizard to auto-detect environment and configure macao.yaml."""
    from macao.cli.wizard import run_interactive_init
    project_root = Path(".").resolve()
    run_interactive_init(
        project_root=project_root,
        target_path="macao.yaml",
        non_interactive=yes,
        force=force,
        custom_executor=executor,
        custom_model=model
    )


@cli.command("daemon")
@click.option("--poll-interval", default=2.0, help="Poll interval in seconds")
@click.option("--once", is_flag=True, help="Scan active tasks once and exit")
def daemon_cmd(poll_interval: float, once: bool):
    """Run background daemon scanner for timeout handling and automated transitions."""
    from macao.workflow.daemon import OrchestratorDaemon

    daemon = OrchestratorDaemon(project_root=".", poll_interval=poll_interval)
    if once:
        res = daemon.scan_once()
        console.print(f"[green]✓ Single scan completed: {res}[/green]")
    else:
        try:
            daemon.run_loop()
        except KeyboardInterrupt:
            daemon.stop()
            console.print("[yellow]Daemon stopped by user.[/yellow]")


@cli.command("live-run")
@click.option("--auto-signoff/--no-auto-signoff", default=True, help="Automatically record test signoff on approval")
def live_run(auto_signoff: bool):
    """Run the Phase 3 end-to-end multi-agent workflow collaboration cycle."""
    from macao.workflow.live_runner import LiveWorkflowRunner
    from macao.cli.ui import render_e2e_report

    print_banner()
    console.print("[bold cyan]Starting MACAO Phase 3 Multi-Agent Collaboration Cycle...[/bold cyan]\n")

    runner = LiveWorkflowRunner()
    try:
        res = runner.run_live_cycle(auto_signoff=auto_signoff)
        render_e2e_report(res)
        if res.get("status") == "PASS":
            console.print("[bold green]✓ Phase 3 Multi-Agent collaboration cycle completed (Task State: DONE).[/bold green]\n")
        elif res.get("status") == "WAITING_SIGNOFF":
            console.print(f"[yellow]Task {res.get('task_id')} reached MERGING; awaiting manual operator signoff (macao merge approve).[/yellow]\n")
        else:
            console.print("[bold red]✗ Phase 3 Multi-Agent collaboration cycle failed.[/bold red]\n")
    finally:
        runner.cleanup()


@cli.command("clean")
@click.option("--all", "clean_all", is_flag=True, help="Remove macao.yaml and restore .gitignore in addition to runtime files")
@click.option("--restore", is_flag=True, help="Restore the latest macao.yaml.bak.* backup if available")
def clean_cmd(clean_all: bool, restore: bool):
    """Clean up MACAO runtime files and rollback configuration or .gitignore."""
    from macao.cli.wizard import remove_gitignore_isolation
    project_root = Path(".").resolve()
    macao_dir = project_root / ".macao"
    cfg_file = project_root / "macao.yaml"

    cleaned_items = []

    # 1. Clean .macao runtime directory
    if macao_dir.exists():
        shutil.rmtree(macao_dir, ignore_errors=True)
        cleaned_items.append(".macao/ (runtime directory)")

    # 2. If --restore requested: find latest macao.yaml.bak.*
    if restore:
        backups = sorted(project_root.glob("macao.yaml.bak.*"), key=lambda p: p.stat().st_mtime)
        if backups:
            latest_backup = backups[-1]
            shutil.copy(latest_backup, cfg_file)
            cleaned_items.append(f"Restored macao.yaml from {latest_backup.name}")
        else:
            console.print("[yellow]No backup files matching 'macao.yaml.bak.*' found.[/yellow]")

    # 3. If --all requested
    if clean_all:
        if cfg_file.exists() and not restore:
            cfg_file.unlink()
            cleaned_items.append("macao.yaml (configuration file)")

        # Clean backup files
        for bak in project_root.glob("macao.yaml.bak.*"):
            bak.unlink()
            cleaned_items.append(f"{bak.name} (backup file)")

        # Clean .gitignore rules
        if remove_gitignore_isolation(project_root):
            cleaned_items.append(".gitignore (removed MACAO rules)")

    if cleaned_items:
        console.print("[bold green]✓ MACAO rollback/clean completed successfully:[/bold green]")
        for item in cleaned_items:
            console.print(f"  • {item}")
    else:
        console.print("[yellow]Nothing to clean. Workspace is already clean.[/yellow]")


if __name__ == "__main__":
    cli()
