"""Rich Terminal UI Rendering Components (PRD §14)."""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_banner() -> None:
    console.print(Panel.fit(
        "[bold cyan]MACAO[/bold cyan] - [dim]Multi-Agent CLI Agent Orchestrator[/dim]\n"
        "[dim]Standardized Process + Explicit Artifact Signals[/dim]",
        border_style="cyan"
    ))


def render_preflight_report(results: List[Any]) -> None:
    table = Table(title="MACAO Preflight Environment Report", border_style="blue")
    table.add_column("CLI / Component", style="cyan", no_wrap=True)
    table.add_column("Installed", style="bold")
    table.add_column("Version", style="green")
    table.add_column("Mode", style="magenta")
    table.add_column("Status", style="white")

    for r in results:
        if isinstance(r, dict):
            name = r.get("agent") or r.get("cli_name", "")
            inst = r.get("installed", False)
            ver = r.get("version", "N/A")
            mode = r.get("mode", "sandboxed")
            st = "[green]OK[/green]" if r.get("status", True) else "[red]FAIL[/red]"
        else:
            name = getattr(r, "cli_name", getattr(r, "agent_id", ""))
            inst = getattr(r, "installed", False)
            ver = getattr(r, "version", "N/A") or "N/A"
            mode = getattr(r, "execution_mode", "sandboxed")
            st = "[green]OK[/green]" if getattr(r, "is_ok", True) else "[red]FAIL[/red]"

        mode_val = getattr(mode, "value", str(mode)) if mode is not None else "N/A"

        table.add_row(
            str(name),
            "[green]YES[/green]" if inst else "[red]NO[/red]",
            str(ver),
            str(mode_val),
            st
        )

    console.print(table)


render_preflight_table = render_preflight_report


def render_task_status(task: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> None:
    status_table = Table(title=f"Task: {task['task_id']} ({task['title']})", border_style="cyan")
    status_table.add_column("Field", style="bold yellow")
    status_table.add_column("Value", style="bold white")

    status_table.add_row("FSM State", f"[bold green]{task['state']}[/bold green]")
    status_table.add_row("Checkpoint Ref", task.get("checkpoint_ref") or "[dim]None[/dim]")
    status_table.add_row("Review Round", str(task.get("review_round", 1)))
    status_table.add_row("Source Branch", task.get("source_branch") or "[dim]N/A[/dim]")
    status_table.add_row("Target Branch", task.get("target_branch") or "[dim]N/A[/dim]")
    status_table.add_row("Updated At", task.get("updated_at", ""))

    console.print(status_table)

    if artifacts:
        art_table = Table(title="Tracked Physical Artifacts", border_style="magenta")
        art_table.add_column("Kind", style="cyan")
        art_table.add_column("Path", style="white")
        art_table.add_column("Round", style="yellow")
        art_table.add_column("Consumed", style="green")

        for a in artifacts:
            consumed_str = "[green]YES[/green]" if a.get("consumed") else "[yellow]NO[/yellow]"
            art_table.add_row(
                a.get("kind", ""),
                a.get("path", ""),
                str(a.get("review_round", "")),
                consumed_str
            )
        console.print(art_table)


def render_cli_integ_report(results: List[Dict[str, Any]]) -> None:
    """Renders the Real CLI PTY Integration Test Report."""
    table = Table(title="MACAO Real CLI PTY Integration Report", border_style="cyan")
    table.add_column("Agent CLI", style="bold cyan")
    table.add_column("Version", style="green")
    table.add_column("PTY Spawn", style="white")
    table.add_column("ANSI Strip", style="white")
    table.add_column("Clean Kill", style="white")
    table.add_column("Duration", style="yellow")
    table.add_column("Verdict", style="bold")

    for r in results:
        status = r.get("status", "UNKNOWN")
        verdict = f"[bold green]PASS[/bold green]" if status == "PASS" else f"[bold red]{status}[/bold red]"
        spawn_ok = r.get("pty_spawn", r.get("pty_spawn_ok", False))
        ansi_ok = r.get("ansi_stripped", r.get("ansi_stripped_ok", False))
        kill_ok = r.get("clean_kill", r.get("clean_kill_ok", False))

        spawn_str = "[green]✓ YES[/green]" if spawn_ok else "[red]✗ NO[/red]"
        ansi_str = "[green]✓ YES[/green]" if ansi_ok else "[yellow]—[/yellow]"
        kill_str = "[green]✓ DEAD (0 Zombie)[/green]" if kill_ok else "[red]✗ ALIVE[/red]"
        dur_str = str(r.get("duration", f"{r.get('duration_sec', 0.0)}s"))

        table.add_row(
            r.get("cli", ""),
            r.get("version", "N/A"),
            spawn_str,
            ansi_str,
            kill_str,
            dur_str,
            verdict
        )

    console.print(table)


def render_e2e_report(result: Dict[str, Any]) -> None:
    """Renders the Phase 3 Live Multi-Agent Collaboration Report."""
    table = Table(title=f"MACAO Phase 3 Live Multi-Agent Collaboration Report ({result.get('task_id')})", border_style="cyan")
    table.add_column("Phase / Step", style="bold yellow")
    table.add_column("Details", style="white")
    table.add_column("Status / Result", style="bold green")

    for s in result.get("steps", []):
        step_name = s.get("step", "")
        details = ", ".join(f"{k}={v}" for k, v in s.items() if k != "step")
        status_text = s.get("status", "OK")
        status_style = "[green]OK[/green]" if status_text == "OK" else f"[red]{status_text}[/red]"
        table.add_row(step_name, details, status_style)

    archived_files = result.get('archived_files', [])
    archived_count = result.get('archived_count', len(archived_files))
    archive_status = "[green]PERSISTED[/green]" if archived_count > 0 else "[red]EMPTY[/red]"
    archived_summary = f"Archived {archived_count} files" + (f": {', '.join(archived_files)}" if archived_files else "")
    table.add_row("8. Physical Archive", archived_summary, archive_status)
    table.add_row("9. Final FSM State", f"Final task state: {result.get('final_state')}", f"[bold cyan]{result.get('final_state')}[/bold cyan]")
    console.print(table)


def render_audit_table(events: List[Dict[str, Any]]) -> None:
    """Renders formatted audit events table."""
    table = Table(title="MACAO Audit Events Log", border_style="cyan")
    table.add_column("Seq", style="dim", justify="right", width=5)
    table.add_column("Timestamp", style="green", no_wrap=True)
    table.add_column("Task ID", style="cyan", no_wrap=True)
    table.add_column("Event Type", style="bold yellow")
    table.add_column("Details", style="white")

    for ev in events:
        detail = ev.get("detail", {})
        if isinstance(detail, dict):
            summary_items = [f"{k}={v}" for k, v in detail.items() if k not in ("full_document",)]
            detail_str = ", ".join(summary_items[:4])
            if len(summary_items) > 4:
                detail_str += "..."
        else:
            detail_str = str(detail)

        ts = str(ev.get("ts", ""))
        if "T" in ts:
            ts = ts.replace("T", " ")[:19]

        table.add_row(
            str(ev.get("sequence_id", "")),
            ts,
            str(ev.get("task_id", "") or "-"),
            str(ev.get("type", "")),
            detail_str
        )

    console.print(table)


def render_team_probe_report(probe: Dict[str, Any]) -> None:
    """Renders comprehensive team and environment dynamic probe report."""
    project_name = probe.get("project_name", "Unknown Project")
    console.print(f"\n[bold cyan]=== MACAO Team & Environment Pre-dispatch Probe: {project_name} ===[/bold cyan]")

    if not probe.get("valid_config"):
        console.print(f"[bold red]Configuration Error:[/bold red] {probe.get('error')}\n")
        return

    # 1. Executor Table
    exec_info = probe.get("executor", {})
    exec_table = Table(title="[bold green]Configured Executor (Implementation Agent)[/bold green]", border_style="green")
    exec_table.add_column("Agent ID", style="bold cyan")
    exec_table.add_column("CLI Tool", style="yellow")
    exec_table.add_column("Model", style="white")
    exec_table.add_column("Version", style="magenta")
    exec_table.add_column("Status", style="bold")
    exec_table.add_column("Dispatch Target", style="dim white")

    st_color = "green" if exec_info.get("status") == "READY" else "red"
    exec_table.add_row(
        str(exec_info.get("id", "N/A")),
        str(exec_info.get("cli", "N/A")),
        str(exec_info.get("model") or "default"),
        str(exec_info.get("version", "unknown")),
        f"[{st_color}]{exec_info.get('status')}[/{st_color}]",
        "Primary developer assigned for task implementation"
    )
    console.print(exec_table)

    # 2. Reviewers Table
    rev_list = probe.get("reviewers", [])
    quorum = probe.get("quorum", {})
    rev_table = Table(
        title=f"[bold blue]Configured Reviewers ({len(rev_list)} Agents | Quorum Required: {quorum.get('minimum_winning_seats', 2)} of {len(rev_list)})[/bold blue]",
        border_style="blue"
    )
    rev_table.add_column("Agent ID", style="bold cyan")
    rev_table.add_column("CLI Tool", style="yellow")
    rev_table.add_column("Vote Weight", style="dim yellow")
    rev_table.add_column("Version", style="magenta")
    rev_table.add_column("Status", style="bold")
    rev_table.add_column("Details", style="dim white")

    for r in rev_list:
        rst_color = "green" if r.get("status") == "READY" else "red"
        rev_table.add_row(
            str(r.get("id", "N/A")),
            str(r.get("cli", "N/A")),
            str(r.get("weight", 1.0)),
            str(r.get("version", "unknown")),
            f"[{rst_color}]{r.get('status')}[/{rst_color}]",
            str(r.get("details", ""))[:50]
        )
    console.print(rev_table)

    # 3. Workspace & Active Task Summary
    git = probe.get("git", {})
    active = probe.get("active_task")

    summary_table = Table(title="[bold magenta]Workspace & Dispatch Readiness[/bold magenta]", border_style="magenta")
    summary_table.add_column("Item", style="bold white")
    summary_table.add_column("Value", style="cyan")
    summary_table.add_column("Readiness", style="bold")

    git_status = "[green]CLEAN[/green]" if git.get("is_clean") else "[yellow]DIRTY / UNCOMMITTED[/yellow]"
    summary_table.add_row("Git Branch", f"{git.get('branch')} (HEAD: {git.get('commit')})", git_status)

    if active:
        summary_table.add_row(
            "Active Task",
            f"{active['task_id']} ({active.get('title', '')[:30]})",
            f"[bold yellow]IN PROGRESS ({active['state']})[/bold yellow]"
        )
    else:
        summary_table.add_row("Active Task", "None (Idle)", "[bold green]READY FOR NEW TASK[/bold green]")

    q_achieve = quorum.get("achievable", False)
    q_str = f"{quorum.get('ready_count')}/{quorum.get('total_configured')} Ready (Need {quorum.get('minimum_winning_seats')})"
    summary_table.add_row("Consensus Quorum", q_str, "[bold green]ACHIEVABLE[/bold green]" if q_achieve else "[bold red]BLOCKED[/bold red]")

    console.print(summary_table)

    # 4. Final Verdict
    if probe.get("can_dispatch"):
        console.print(
            f"[bold green]✓ Pre-execution Probing Passed:[/bold green] All {quorum.get('ready_count')} reviewers and executor '{exec_info.get('id')}' are healthy.\n"
        )
    else:
        reasons = "\n  - ".join(probe.get("blocking_reasons", []))
        console.print(
            f"[bold red]✗ Pre-execution Probing Blocked:[/bold red]\n  - {reasons}\n"
        )


