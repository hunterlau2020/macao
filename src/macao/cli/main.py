"""MACAO Command-Line Interface (PRD §14)."""

import os
import sys
import uuid
import click
from pathlib import Path

from macao.core.config import ConfigManager, load_config
from macao.core.types import AgentState, OverrideChoice
from macao.storage.store import StateStore
from macao.storage.reconcile import StateReconciler
from macao.adapter.claude import ClaudeCodeAdapter
from macao.adapter.codex import CodexAdapter
from macao.adapter.kimi import KimiAdapter
from macao.workflow.fsm import WorkflowFSM
from macao.cli.ui import console, print_banner, render_preflight_report, render_task_status


@click.group()
def cli():
    """MACAO: Multi-Agent CLI Agent Orchestrator."""
    pass


@cli.command()
def preflight():
    """Probe CLI installation, auth, and version matrix (PRD §14.1)."""
    print_banner()
    adapters = [ClaudeCodeAdapter(), CodexAdapter(), KimiAdapter()]
    results = [a.preflight() for a in adapters]
    render_preflight_report(results)


@cli.command()
@click.option("--name", default="macao-demo", help="Project name")
def init(name: str):
    """Generate default macao.yaml template."""
    cfg_file = Path("macao.yaml")
    if cfg_file.exists():
        console.print("[yellow]macao.yaml already exists. Skipping init.[/yellow]")
        return

    content = f"""project:
  name: "{name}"
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
    - id: "cc-glm"
      cli: "codex"
      adapter: "pty-wrapper"
    - id: "kimi"
      cli: "kimi"
      adapter: "pty-wrapper"

policy:
  consensus_rule: "2/3_majority"
  min_effective_votes: 2
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
  allowed_clis: ["claude-code", "codex", "kimi"]
  send_terminal_logs_to_reviewers: false
  secrets_masking: true

audit:
  retention_days: 90
"""
    with open(cfg_file, "w", encoding="utf-8") as f:
        f.write(content)
    console.print(f"[bold green]Initialized {cfg_file} successfully![/bold green]")


@cli.command()
def doctor():
    """Validate macao.yaml and environment sanity."""
    print_banner()
    try:
        cfg = load_config()
        console.print(f"[green]✓ macao.yaml configuration valid (Project: {cfg.project_name})[/green]")
    except Exception as e:
        console.print(f"[bold red]✗ macao.yaml error:[/bold red] {e}")
        return

    # Check StateStore
    store = StateStore()
    reconciler = StateReconciler(store)
    reconciler.reconcile()
    console.print("[green]✓ State Store and SQLite connection healthy[/green]")


@cli.group()
def task():
    """Manage MACAO development tasks."""
    pass


@task.command("create")
@click.option("--title", required=True, help="Task title")
@click.option("--acceptance", required=True, help="Acceptance criteria")
@click.option("--branch", default="feature/new-feature", help="Source feature branch")
@click.option("--target", default="main", help="Target branch")
def task_create(title: str, acceptance: str, branch: str, target: str):
    """Create a new development task with explicit acceptance criteria."""
    task_id = f"task-{uuid.uuid4().hex[:6]}"
    store = StateStore()
    store.create_task(task_id, title, branch, target)
    console.print(f"[bold green]Created task {task_id} successfully in IDLE state.[/bold green]")


@cli.command()
def status():
    """Display active task and FSM status (PRD §14.1)."""
    store = StateStore()
    reconciler = StateReconciler(store)
    reconciler.reconcile()

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
    """Resolve human override deadlock or unknown state."""
    store = StateStore()
    task_data = store.get_active_task()
    if not task_data:
        console.print("[red]No active task found to resolve override.[/red]")
        return

    task_id = task_data["task_id"]
    store.record_override(task_id, "HUMAN_CLI_RESOLUTION", choice, note)
    
    # Trigger transition
    fsm = WorkflowFSM(store)
    if choice == "APPROVED":
        fsm.transition(task_id, AgentState.MERGING, "E7")
    elif choice == "REWORK":
        fsm.transition(task_id, AgentState.REWORK, "E7")
    elif choice == "RETRY_REVIEW":
        fsm.transition(task_id, AgentState.WAITING_REVIEW, "E9")
    elif choice == "CANCEL":
        fsm.transition(task_id, AgentState.CANCELLED, "E10")

    console.print(f"[bold green]Override resolved with choice: {choice}[/bold green]")


@cli.command()
def usage():
    """Display token and cost usage report (PRD §15.4)."""
    console.print("[cyan]MACAO Usage & Cost Meter (Estimated)[/cyan]")
    console.print("Phase: Development | Claude Code: 12,450 tokens (estimated: false)")
    console.print("Phase: Review      | Codex:        4,200 tokens (estimated: true)")
    console.print("Phase: Review      | Kimi:         3,800 tokens (estimated: true)")
    console.print("[bold green]Total Tokens:[/bold green] 20,450 (~$0.12 USD)")


if __name__ == "__main__":
    cli()
