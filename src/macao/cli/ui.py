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


def render_team_probe_report(probe: Dict[str, Any], dry_run: bool = False) -> None:
    """Renders comprehensive team and environment dynamic probe report."""
    project_name = probe.get("project_name", "Unknown Project")
    is_dry = dry_run or probe.get("dry_run", False)
    dry_badge = " [bold yellow][DRY-RUN (Pure Read-Only)][/bold yellow]" if is_dry else ""
    console.print(f"\n[bold cyan]=== MACAO Team & Environment Dynamic Probe: {project_name}{dry_badge} ===[/bold cyan]")

    if not probe.get("valid_config"):
        console.print(f"[bold red]Configuration Error:[/bold red] {probe.get('error')}\n")
        return

    # 1. Executor Table
    exec_info = probe.get("executor", {})
    exec_table = Table(title="[bold green]1. Configured Executor (Implementation Agent)[/bold green]", border_style="green")
    exec_table.add_column("Agent ID", style="bold cyan")
    exec_table.add_column("CLI & Model", style="yellow")
    exec_table.add_column("Status", style="bold")
    exec_table.add_column("Current Worktree (Branch & State)", style="white")
    exec_table.add_column("Work Progress & Details", style="bold")

    st_color = "green" if exec_info.get("status") == "READY" else "red"
    st_text = f"[{st_color}]{exec_info.get('status')}[/{st_color}]"

    exec_wt = exec_info.get("worktree", {})
    wt_clean = "[green]clean[/green]" if exec_wt.get("is_clean", True) else f"[yellow]{exec_wt.get('modified_files_count', 1)} dirty[/yellow]"
    wt_display = f"{exec_wt.get('path', 'root')}\n[dim]branch: {exec_wt.get('branch', 'main')} @ {exec_wt.get('commit', 'HEAD')} ({wt_clean})[/dim]"

    prog = exec_info.get("progress", "IDLE")
    if prog == "IDLE":
        prog_styled = "[dim green]IDLE[/dim green]"
    elif prog == "ACTIVE_DEV (UNTRACKED)":
        prog_styled = "[bold yellow]ACTIVE_DEV (UNTRACKED)[/bold yellow]"
    elif prog in ("CODING_IN_PROGRESS", "REWORK"):
        prog_styled = "[bold yellow]CODING_IN_PROGRESS[/bold yellow]"
    elif prog == "CHECKPOINT_SUBMITTED":
        prog_styled = "[bold cyan]CHECKPOINT_SUBMITTED[/bold cyan]"
    elif prog == "READY_TO_MERGE":
        prog_styled = "[bold green]READY_TO_MERGE[/bold green]"
    elif prog == "WAITING_REVIEW_VERDICT":
        prog_styled = "[bold magenta]WAITING_REVIEW[/bold magenta]"
    else:
        prog_styled = f"[cyan]{prog}[/cyan]"

    p_desc = exec_info.get("progress_desc", "")
    prog_cell = f"{prog_styled}\n[dim]{p_desc}[/dim]" if p_desc else prog_styled

    cli_model = f"{exec_info.get('cli', 'N/A')}" + (f" ({exec_info.get('model')})" if exec_info.get("model") else "")

    exec_table.add_row(
        str(exec_info.get("id", "N/A")),
        cli_model,
        st_text,
        wt_display,
        prog_cell
    )
    console.print(exec_table)

    # 2. Reviewers Table
    rev_list = probe.get("reviewers", [])
    quorum = probe.get("quorum", {})
    rev_table = Table(
        title=f"[bold blue]2. Configured Reviewers ({len(rev_list)} Agents | Quorum Required: {quorum.get('minimum_winning_seats', 2)} of {len(rev_list)})[/bold blue]",
        border_style="blue"
    )
    rev_table.add_column("Agent ID", style="bold cyan")
    rev_table.add_column("CLI (Weight)", style="yellow")
    rev_table.add_column("Status", style="bold")
    rev_table.add_column("Isolated Worktree", style="white")
    rev_table.add_column("Review Progress & Verdict", style="bold")

    for r in rev_list:
        rst_color = "green" if r.get("status") == "READY" else "red"
        rst_text = f"[{rst_color}]{r.get('status')}[/{rst_color}]"

        r_wt = r.get("worktree", {})
        wt_exists = r_wt.get("exists", False)
        wt_path_str = r_wt.get("relative_path") or r_wt.get("expected_path", "")
        if wt_exists:
            wt_badge = f"[green]ACTIVE @ {r_wt.get('commit', 'HEAD')}[/green]"
        else:
            wt_badge = "[dim]NOT_SPAWNED[/dim]"
        wt_cell = f"{wt_path_str} ({wt_badge})"

        r_rev = r.get("review", {})
        r_prog = r_rev.get("progress", "IDLE")
        r_vote = r_rev.get("vote")

        if r_prog == "COMPLETED":
            if r_vote == "YES_APPROVE":
                r_prog_disp = "[bold green]COMPLETED (APPROVED)[/bold green]"
            elif r_vote == "NO_APPROVE":
                r_prog_disp = "[bold red]COMPLETED (CHANGES_REQ)[/bold red]"
            elif r_vote == "ABSTAIN":
                r_prog_disp = "[yellow]COMPLETED (ABSTAINED)[/yellow]"
            else:
                r_prog_disp = f"[bold green]COMPLETED ({r_vote})[/bold green]"
        elif r_prog == "IN_PROGRESS":
            r_prog_disp = "[bold yellow]IN_PROGRESS (Reviewing...)[/bold yellow]"
        elif r_prog == "PENDING":
            r_prog_disp = "[bold cyan]PENDING (Queued)[/bold cyan]"
        elif r_prog == "WAITING_DEV":
            r_prog_disp = "[dim yellow]WAITING_DEV (Waiting for dev checkpoint)[/dim yellow]"
        else:
            r_prog_disp = "[dim]IDLE (Standby)[/dim]"

        details_str = str(r.get("details", ""))
        rev_cell = f"{r_prog_disp}\n[dim]{details_str}[/dim]" if (details_str and details_str != "Standby (Awaiting task dispatch)") else r_prog_disp

        cli_disp = f"{r.get('cli', 'N/A')} (w:{r.get('weight', 1.0):.1f})"

        rev_table.add_row(
            str(r.get("id", "N/A")),
            cli_disp,
            rst_text,
            wt_cell,
            rev_cell
        )
    console.print(rev_table)

    # 3. Workspace & Active Task Summary
    git = probe.get("git", {})
    active = probe.get("active_task")
    state_store = probe.get("state_store", {})

    summary_table = Table(title="[bold magenta]3. Workspace & Consensus Readiness[/bold magenta]", border_style="magenta")
    summary_table.add_column("Dimension", style="bold white", width=22)
    summary_table.add_column("Observed Value", style="cyan")
    summary_table.add_column("Readiness / Verdict", style="bold")

    git_status = "[green]CLEAN[/green]" if git.get("is_clean") else f"[yellow]DIRTY ({git.get('modified_files_count', 0)} files uncommitted)[/yellow]"
    summary_table.add_row("Git Repository", f"Branch: {git.get('branch')} (HEAD: {git.get('commit')})", git_status)

    ss_status = state_store.get("status", "CONNECTED (RO)")
    ss_color = "green" if "CONNECTED" in ss_status else "dim"
    summary_table.add_row("State Store", state_store.get("path", ".macao/state.db"), f"[{ss_color}]{ss_status}[/{ss_color}]")

    if active:
        summary_table.add_row(
            "Active Task",
            f"{active['task_id']} ({active.get('title', '')[:30]}) [Round {active.get('review_round', 1)}]",
            f"[bold yellow]IN PROGRESS ({active['state']})[/bold yellow]"
        )
    else:
        if not git.get("is_clean", True):
            summary_table.add_row(
                "Active Task",
                f"None ({git.get('modified_files_count', 0)} files uncommitted in git)",
                "[bold yellow]UNTRACKED DEV (Run 'macao task create' to adopt)[/bold yellow]"
            )
        else:
            summary_table.add_row("Active Task", "None (Idle)", "[bold green]READY FOR NEW TASK[/bold green]")

    q_achieve = quorum.get("achievable", False)
    q_str = f"{quorum.get('ready_count')}/{quorum.get('total_configured')} Ready (Required: {quorum.get('minimum_winning_seats')})"
    summary_table.add_row("Consensus Quorum", q_str, "[bold green]ACHIEVABLE[/bold green]" if q_achieve else "[bold red]BLOCKED[/bold red]")

    console.print(summary_table)

    # 4. Final Verdict & Actionable Guidance
    if probe.get("can_dispatch"):
        console.print(
            f"[bold green]✓ Pre-execution Probing Passed:[/bold green] Executor '{exec_info.get('id')}' and {quorum.get('ready_count')} reviewer(s) are operational."
        )
        if not active:
            if not git.get("is_clean", True):
                console.print(
                    f"  [yellow]• Note: Detected active development in working tree ({git.get('modified_files_count', 0)} uncommitted files).[/yellow]\n"
                    "  [dim]• Run 'macao task create --title \"...\"' to adopt existing changes into a managed task and trigger review.[/dim]\n"
                )
            else:
                console.print("  [dim]→ Run 'macao task create --title \"...\"' to dispatch a new task.[/dim]\n")
        elif active.get("state") in ("CODING", "REWORK"):
            if exec_info.get("progress") == "CHECKPOINT_SUBMITTED":
                console.print(f"  [dim]→ Checkpoint submitted. Run 'macao task checkpoint' to dispatch {quorum.get('total_configured')} reviewers.[/dim]\n")
            else:
                console.print(f"  [dim]→ Executor is implementing '{active['task_id']}'. Once done, submit checkpoint with 'macao task checkpoint --auto'.[/dim]\n")
        elif active.get("state") in ("WAITING_REVIEW", "IN_REVIEW"):
            console.print(f"  [dim]→ Reviewers are evaluating '{active['task_id']}'. Run 'macao status' or check logs with 'macao logs -r all'.[/dim]\n")
        elif active.get("state") == "MERGING":
            console.print(f"  [dim]→ Review passed! Run 'macao merge approve --merge' to finalize and close task.[/dim]\n")
        else:
            console.print(f"  [dim]→ Task state: {active.get('state')}. Run 'macao status' for details.[/dim]\n")
    else:
        reasons = "\n  - ".join(probe.get("blocking_reasons", []))
        console.print(
            f"[bold red]✗ Pre-execution Probing Blocked:[/bold red]\n  - {reasons}\n"
        )


