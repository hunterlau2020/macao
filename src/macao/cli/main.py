"""MACAO Click CLI Entrypoint (PRD §14)."""

import os
import sys
import shutil
import sqlite3
import click
from pathlib import Path
from typing import Dict, Any, Optional

from macao.core.config import ConfigManager
from macao.core.types import AgentState, OverrideChoice, PreflightCheckResult, ExecutionMode
from macao.storage.store import StateStore
from macao.storage.reconcile import StateReconciler
from macao.workflow.orchestrator import Orchestrator
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.opencode import OpenCodeAdapter
from macao.adapter.antigravity import AntigravityAdapter
from macao.adapter.cursor import CursorAgentAdapter
from macao.adapter.kimi import KimiAdapter
from macao.adapter.mock import MockAgentAdapter
from macao.cli.ui import console, print_banner, render_preflight_report, render_task_status


DEFAULT_CONFIG_TEMPLATE = """# MACAO macao.yaml Orchestration Configuration (PRD §13)
version: "2.5"
project:
  name: "macao-demo"
  repository:
    workspace_path: "."
    remote_name: "origin"
    default_branch: "main"

team:
  executor:
    id: "cc-ds4"
    cli: "claude-code"
    adapter: "claude-hook"
  reviewers:
    - id: "codex"
      cli: "codex"
      adapter: "pty-wrapper"
      vote_weight: 1
    - id: "opencode"
      cli: "opencode"
      adapter: "pty-wrapper"
      vote_weight: 1
    - id: "antigravity"
      cli: "agy"
      adapter: "pty-wrapper"
      vote_weight: 1

policy:
  consensus_rule: "weighted_2/3_v1"
  dictator_cap_enabled: true
  minimum_winning_seats: 2
  seat_quorum_required: 2
  weight_quorum_required: 2
  max_rework_rounds: 3
  review_strategy: "delta_plus_focus"

merge:
  strategy: "ff_only"
  ci_gate_command: null
  require_human_signoff: true
  rebase_before_merge: false

timeouts:
  development: "2h"
  checkpoint_validation: "1m"
  review_request: "30m"
  per_reviewer: "10m"
  consensus_check: "1m"

thresholds:
  layer2_inference_log_only: true
  llm_diagnosis_override_below: 0.7

cost:
  usage_metering: true
  monthly_budget_usd: null

security:
  allowed_clis: ["claude-code", "codex", "opencode", "agy", "antigravity", "kimi"]
  send_terminal_logs_to_reviewers: false
  secrets_masking: true

audit:
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


@click.group()
def cli():
    """MACAO - Multi-Agent CLI Agent Orchestrator."""
    pass


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


@cli.command()
@click.option("--path", default="macao.yaml", help="Path to create macao.yaml")
def init(path: str):
    """Initialize a default macao.yaml configuration file conforming to schema."""
    p = Path(path)
    if p.exists():
        console.print(f"[yellow]Configuration file '{path}' already exists.[/yellow]")
        return

    p.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    console.print(f"[bold green]✓ Initialized valid configuration template at '{path}'[/bold green]")


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


@task.command("create")
@click.option("--title", required=True, help="Task title")
@click.option("--description", default="", help="Task detailed description")
@click.option("--acceptance", default="", help="Acceptance criteria")
@click.option("--branch", default="feature/task-01", help="Source branch")
@click.option("--target", default="main", help="Target branch")
def task_create(title: str, description: str, acceptance: str, branch: str, target: str):
    """Create and start a new development task."""
    orchestrator = get_orchestrator(".")

    task_data = orchestrator.start_task(
        title=title,
        task_description=description or title,
        acceptance_criteria={"raw": acceptance, "tests_passed": True},
        source_branch=branch,
        target_branch=target
    )
    console.print(f"[bold green]✓ Task '{task_data['task_id']}' created in state: {task_data['state']}[/bold green]")


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


@cli.group()
def override():
    """Manage human overrides."""
    pass


@override.command("resolve")
@click.option("--choice", required=True, type=click.Choice(["APPROVED", "REWORK", "RETRY_REVIEW", "CANCEL"]), help="Decision choice")
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
def merge_approve(note: str):
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
@click.option("--executor", default="opencode", help="Default executor CLI")
@click.option("--model", default="GLM 5.3 max", help="Executor model name")
@click.option("--force", is_flag=True, help="Force overwrite existing configuration")
def setup_wizard(executor: str, model: str, force: bool):
    """Run interactive setup wizard to auto-detect environment and configure macao.yaml."""
    from macao.cli.wizard import probe_available_clis, generate_smart_config, ensure_gitignore_isolation
    import yaml
    import shutil
    import time

    print_banner()
    console.print("[bold cyan]Running MACAO Smart Setup Wizard...[/bold cyan]\n")

    clis = probe_available_clis()
    console.print(f"[green]✓ Detected {len(clis)} available AI Agent CLIs on system:[/green]")
    for c in clis:
        console.print(f"  • [bold white]{c['cli']}[/bold white] ({c['version']}) -> [dim]{c['binary']}[/dim]")

    project_root = Path(".").resolve()
    cfg_file = project_root / "macao.yaml"
    if cfg_file.exists() and not force:
        backup_file = project_root / f"macao.yaml.bak.{int(time.time())}"
        shutil.copy(cfg_file, backup_file)
        console.print(f"[yellow]Notice: Existing macao.yaml backed up to {backup_file.name}[/yellow]")

    cfg = generate_smart_config(project_root, executor_cli=executor, executor_model=model, detected_clis=clis)

    yaml_str = yaml.safe_dump(cfg, sort_keys=False)
    cfg_file.write_text(yaml_str, encoding="utf-8")
    console.print(f"\n[bold green]✓ Generated valid and tailored macao.yaml configuration![/bold green]")

    isolated = ensure_gitignore_isolation(project_root)
    if isolated:
        console.print("[green]✓ Updated .gitignore with .macao/worktrees/ and *.db runtime isolation.[/green]")

    console.print("\n[bold cyan]Setup completed! You can now run 'macao doctor' or 'macao task create' to begin.[/bold cyan]\n")


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



if __name__ == "__main__":
    cli()
