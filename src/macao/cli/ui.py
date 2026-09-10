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
    exec_table.add_column("CLI & Session", style="yellow")
    exec_table.add_column("Status", style="bold")
    exec_table.add_column("Current Worktree (Branch & State)", style="white")
    exec_table.add_column("Work Progress (Last, Current, Next)", style="bold")

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
    elif prog == "REVIEW_PENDING":
        prog_styled = "[bold magenta]REVIEW_PENDING[/bold magenta]"
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

    triplet = exec_info.get("progress_triplet") or {}
    last_c = triplet.get("last_completed")
    curr_t = triplet.get("current_task")
    next_p = triplet.get("next_planned")

    if last_c and curr_t and next_p:
        prog_cell = (
            f"{prog_styled}\n"
            f"[cyan]• Last:[/cyan] [dim]{last_c[:60]}[/dim]\n"
            f"[cyan]• Now:[/cyan] [dim]{curr_t[:60]}[/dim]\n"
            f"[cyan]• Next:[/cyan] [dim]{next_p[:60]}[/dim]"
        )
    else:
        p_desc = exec_info.get("progress_desc", "")
        prog_cell = f"{prog_styled}\n[dim]{p_desc}[/dim]" if p_desc else prog_styled

    exec_m = exec_info.get("model")
    exec_p = exec_info.get("provider")
    if exec_p and exec_m:
        model_spec = f" ({exec_p}/{exec_m})"
    elif exec_m:
        model_spec = f" ({exec_m})"
    elif exec_p:
        model_spec = f" (provider: {exec_p})"
    else:
        model_spec = ""
    cli_base = f"{exec_info.get('cli', 'N/A')}{model_spec}"
    exec_sess = exec_info.get("session")
    if exec_sess and exec_sess.get("session_id"):
        sid_short = exec_sess.get("session_id")[:12]
        s_name = exec_sess.get("session_name") or exec_sess.get("title")
        tot = exec_sess.get("total_sessions", 1)
        tot_suffix = f" [1 of {tot}]" if tot > 1 else ""
        if s_name and s_name != sid_short:
            sess_line = f"sess: {s_name} ({sid_short}...){tot_suffix}"
        else:
            sess_line = f"sess: {sid_short}...{tot_suffix}"
        cli_model = f"{cli_base}\n[dim cyan]{sess_line}[/dim cyan]\n[dim]({exec_sess.get('last_active', 'active')})[/dim]"
    else:
        cli_model = cli_base

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
    min_w = quorum.get("minimum_winning_seats", 2)
    seat_q = quorum.get("seat_quorum_required", 2)
    weight_q = float(quorum.get("weight_quorum_required", 2.0))
    rev_table = Table(
        title=f"[bold blue]2. Configured Reviewers ({len(rev_list)} Agents | Quorum: min {min_w} win, {seat_q} seat-q, {weight_q:.1f} wt-q)[/bold blue]",
        border_style="blue"
    )
    rev_table.add_column("Agent ID", style="bold cyan")
    rev_table.add_column("CLI & Model (Weight & Sess)", style="yellow")
    rev_table.add_column("CLI Status", style="bold")
    rev_table.add_column("Worktree (Sandbox / Repo)", style="white")
    rev_table.add_column("Review Progress & Verdict", style="bold")

    for r in rev_list:
        rst_color = "green" if r.get("status") == "READY" else "red"
        rst_text = f"[{rst_color}]{r.get('status')}[/{rst_color}]"

        r_wt = r.get("worktree", {})
        wt_type = r_wt.get("type", "isolated_worktree")
        wt_exists = r_wt.get("exists", False)
        wt_path_str = r_wt.get("relative_path") or r_wt.get("expected_path", "")

        if wt_type == "in_repo":
            wt_cell = "[dim]In-repo (Shared Workspace)[/dim]"
        elif wt_exists:
            wt_cell = f"{wt_path_str} ([green]ACTIVE @ {r_wt.get('commit', 'HEAD')}[/green])"
        else:
            wt_cell = f"{wt_path_str} ([dim]NOT_SPAWNED[/dim])"

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
        elif r_prog == "AWAITING_REVIEW":
            r_prog_disp = f"[bold cyan]{r_rev.get('status_display', 'AWAITING_REVIEW')}[/bold cyan]"
        elif r_prog == "IN_PROGRESS":
            r_prog_disp = "[bold yellow]IN_PROGRESS (Reviewing...)[/bold yellow]"
        elif r_prog == "PENDING":
            r_prog_disp = "[bold cyan]PENDING (Queued)[/bold cyan]"
        elif r_prog == "WAITING_DEV":
            r_prog_disp = "[dim yellow]WAITING_DEV (Waiting for dev checkpoint)[/dim yellow]"
        else:
            r_prog_disp = "[dim]IDLE (Standby)[/dim]"

        r_model = r.get("model")
        r_provider = r.get("provider")
        if r_provider and r_model:
            model_spec = f" ({r_provider}/{r_model})"
        elif r_model:
            model_spec = f" ({r_model})"
        elif r_provider:
            model_spec = f" (provider: {r_provider})"
        else:
            model_spec = ""
        r_cli_display = f"{r.get('cli')}{model_spec} (w:{r.get('weight', 1.0)})"

        r_sess = r.get("session")
        if r_sess:
            r_sid_short = str(r_sess.get("session_id", ""))[:8]
            r_s_name = r_sess.get("session_name")
            r_tot = r_sess.get("total_sessions", 1)
            r_tot_suffix = f" [1 of {r_tot}]" if r_tot > 1 else ""
            if r_s_name and r_s_name != r_sid_short:
                r_sess_line = f"sess: {r_s_name} ({r_sid_short}...){r_tot_suffix}"
            else:
                r_sess_line = f"sess: {r_sid_short}...{r_tot_suffix}"
            r_sess_cell = f"{r_cli_display}\n[dim cyan]{r_sess_line}[/dim cyan]\n[dim]({r_sess.get('last_active', 'active')})[/dim]"
        else:
            r_sess_cell = f"{r_cli_display}\n[dim]no session[/dim]"

        rev_table.add_row(
            str(r.get("id")),
            r_sess_cell,
            rst_text,
            wt_cell,
            r_prog_disp
        )
    console.print(rev_table)

    # 3. Summary & Quorum Table
    git = probe.get("git", {})
    state_store = probe.get("state_store", {})
    active = probe.get("active_task")
    phys_reviews = probe.get("physical_reviews", {})

    summary_table = Table(title="[bold magenta]3. Workspace & Consensus Readiness[/bold magenta]", border_style="magenta")
    summary_table.add_column("Dimension", style="bold white", width=22)
    summary_table.add_column("Observed Value", style="cyan")
    summary_table.add_column("Readiness / Verdict", style="bold")

    git_status = "[green]CLEAN[/green]" if git.get("is_clean") else f"[yellow]DIRTY ({git.get('modified_files_count', 0)} files uncommitted)[/yellow]"
    summary_table.add_row("Git Repository", f"Branch: {git.get('branch')} (HEAD: {git.get('commit')})", git_status)

    ss_status = state_store.get("status", "CONNECTED (RO)")
    ss_color = "green" if "CONNECTED" in ss_status else "dim"
    summary_table.add_row("State Store", state_store.get("path", ".macao/state.db"), f"[{ss_color}]{ss_status}[/{ss_color}]")

    if phys_reviews.get("has_pending_request"):
        summary_table.add_row(
            "Review Baseline",
            f"{phys_reviews.get('latest_request_file')} (Baseline: {phys_reviews.get('latest_request_baseline')})",
            "[bold yellow]AWAITING REVIEW VERDICTS[/bold yellow]"
        )

    if active:
        summary_table.add_row(
            "Active Task",
            f"{active['task_id']} ({active.get('title', '')[:30]}) [Round {active.get('review_round', 1)}]",
            f"[bold yellow]IN PROGRESS ({active['state']})[/bold yellow]"
        )
    else:
        if phys_reviews.get("has_pending_request"):
            base_disp = (phys_reviews.get('latest_request_baseline') or 'HEAD')[:8]
            summary_table.add_row(
                "Active Task",
                f"Review Pending @ {base_disp} ({phys_reviews.get('latest_request_file')})",
                "[bold cyan]SCENARIO_C (Adopt via 'macao task adopt')[/bold cyan]"
            )
        elif not git.get("is_clean", True):
            summary_table.add_row(
                "Active Task",
                f"None ({git.get('modified_files_count', 0)} files uncommitted in git)",
                "[bold yellow]UNTRACKED DEV (Run 'macao task create' to adopt)[/bold yellow]"
            )
        else:
            summary_table.add_row("Active Task", "None (Idle)", "[bold green]READY FOR NEW TASK[/bold green]")

    q_achieve = quorum.get("achievable", False)
    q_str = f"{quorum.get('ready_count')}/{quorum.get('total_configured')} seats ({quorum.get('total_effective_weight', 0.0):.1f}w) [Req: min {min_w} win, {seat_q} seat-q, {weight_q:.1f} wt-q]"
    achieve_disp = "[bold green]ACHIEVABLE (达到法定仲裁席位)[/bold green]" if q_achieve else "[bold red]BLOCKED (可用席位不足)[/bold red]"
    summary_table.add_row("Consensus Quorum", q_str, achieve_disp)

    console.print(summary_table)

    # 4. Final Verdict & Actionable Guidance
    if probe.get("can_dispatch"):
        console.print(
            f"[bold green]✓ Pre-execution Probing Passed:[/bold green] Executor '{exec_info.get('id')}' and {quorum.get('ready_count')} reviewer(s) are operational."
        )
        if not active:
            if phys_reviews.get("has_pending_request"):
                missing = phys_reviews.get("missing_reviewers", [])
                if missing:
                    missing_str = f" Awaiting: {', '.join(missing)}."
                    console.print(
                        f"  [cyan]• Detected pending review request: '{phys_reviews.get('latest_request_file')}' (Baseline: {phys_reviews.get('latest_request_baseline', '')[:8]}).{missing_str}[/cyan]\n"
                        "  [dim]• Run 'macao task adopt' to adopt this in-flight review into MACAO without resetting state.[/dim]\n"
                    )
                else:
                    console.print(
                        f"  [cyan]• Detected completed review request: '{phys_reviews.get('latest_request_file')}' (Baseline: {phys_reviews.get('latest_request_baseline', '')[:8]}). All {len(phys_reviews.get('submitted_reviewers', []))} reviewer(s) submitted.[/cyan]\n"
                        "  [dim]• Run 'macao task adopt' to adopt into MACAO and evaluate consensus.[/dim]\n"
                    )
            elif not git.get("is_clean", True):
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

    if probe.get("log_file"):
        console.print(f"[dim]Audit Log: {probe.get('log_file')} | View with 'macao logs --probe'[/dim]\n")


def render_task_adopt_plan(plan: Dict[str, Any], dry_run: bool = False) -> None:
    """Renders Rich table for Scenario C task adoption plan."""
    mode_str = " [DRY-RUN (Preview Only)]" if dry_run else ""
    table = Table(title=f"MACAO Scenario C In-Flight Task Adoption Plan{mode_str}", border_style="cyan")
    table.add_column("Dimension", style="bold yellow", width=25)
    table.add_column("Observed / Planned Value", style="white", width=55)

    table.add_row("Adoption Scenario", plan.get("scenario", "Scenario C (In-Flight Brownfield Adoption)"))
    table.add_row("Physical Reality", plan.get("physical_state", "N/A"))
    table.add_row("Adopted Task ID", f"[bold cyan]{plan.get('task_id')}[/bold cyan]")
    table.add_row("Task Title", str(plan.get("title", "N/A")))
    table.add_row("Target FSM State", f"[bold green]{plan.get('target_state')}[/bold green]")
    table.add_row("Checkpoint Baseline", str(plan.get("checkpoint_ref", "HEAD")))
    table.add_row("Assigned Responsibility", str(plan.get("assigned_role", "N/A")))
    table.add_row("Target Agents", ", ".join(plan.get("assigned_agents", [])) or "None")
    table.add_row("Executor Status", str(plan.get("executor_status", "STANDBY")))
    if plan.get("missing_reviewers"):
        table.add_row("Missing Reviewers", f"[bold red]{', '.join(plan.get('missing_reviewers'))}[/bold red]")
    if plan.get("submitted_reviewers"):
        table.add_row("Submitted Reviewers", f"[bold green]{', '.join(plan.get('submitted_reviewers'))}[/bold green]")
    table.add_row("Review Dispatch Policy", "Dispatch to missing reviewers" if plan.get("review") else "Deferred (--no-review)")

    console.print(table)

    rev_details = plan.get("reviewers_detail", [])
    if rev_details:
        rtable = Table(title="Reviewers Adoption & Session Status", border_style="blue")
        rtable.add_column("Reviewer ID", style="bold cyan")
        rtable.add_column("CLI & Model", style="yellow")
        rtable.add_column("Session (ID & Active)", style="white")
        rtable.add_column("CLI Status", style="bold")
        rtable.add_column("Progress & Verdict", style="bold")

        for rd in rev_details:
            rst_color = "green" if rd.get("status") == "READY" else "red"
            rst_text = f"[{rst_color}]{rd.get('status', 'READY')}[/{rst_color}]"

            m_spec = f" ({rd.get('model')})" if rd.get("model") else ""
            cli_col = f"{rd.get('cli')}{m_spec}"

            sid = rd.get("session_id")
            sname = rd.get("session_name")
            lact = rd.get("last_active")
            if sid:
                sid_short = str(sid)[:8]
                if sname and sname != sid_short:
                    sess_text = f"{sname} ({sid_short}...)\n[dim]({lact or 'active'})[/dim]"
                else:
                    sess_text = f"{sid_short}...\n[dim]({lact or 'active'})[/dim]"
            else:
                sess_text = "[dim]no session[/dim]"

            prog = rd.get("progress", "IDLE")
            vote = rd.get("vote")
            if prog == "COMPLETED":
                if vote == "YES_APPROVE":
                    prog_text = "[bold green]COMPLETED (APPROVED)[/bold green]"
                elif vote == "NO_APPROVE":
                    prog_text = "[bold red]COMPLETED (CHANGES_REQ)[/bold red]"
                elif vote == "ABSTAIN":
                    prog_text = "[yellow]COMPLETED (ABSTAINED)[/yellow]"
                else:
                    prog_text = f"[bold green]COMPLETED ({vote})[/bold green]"
            elif prog == "IN_PROGRESS":
                prog_text = "[bold yellow]IN_PROGRESS (Reviewing...)[/bold yellow]"
            elif prog == "AWAITING_REVIEW":
                prog_text = "[bold cyan]AWAITING_REVIEW[/bold cyan]"
            else:
                prog_text = f"[dim]{prog}[/dim]"

            rtable.add_row(
                str(rd.get("id")),
                cli_col,
                sess_text,
                rst_text,
                prog_text
            )
        console.print(rtable)
