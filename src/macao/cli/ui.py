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
        spawn_str = "[green]✓ YES[/green]" if r.get("pty_spawn_ok") else "[red]✗ NO[/red]"
        ansi_str = "[green]✓ YES[/green]" if r.get("ansi_stripped_ok") else "[yellow]—[/yellow]"
        kill_str = "[green]✓ DEAD (0 Zombie)[/green]" if r.get("clean_kill_ok") else "[red]✗ ALIVE[/red]"

        table.add_row(
            r.get("cli", ""),
            r.get("version", "N/A"),
            spawn_str,
            ansi_str,
            kill_str,
            f"{r.get('duration_sec', 0.0)}s",
            verdict
        )

    console.print(table)


def render_e2e_report(result: Dict[str, Any]) -> None:
    """Renders the Phase 2 End-to-End Micro-Task Collaboration Report."""
    table = Table(title=f"MACAO Phase 2 E2E Micro-Task Report ({result.get('task_id')})", border_style="cyan")
    table.add_column("Phase / Step", style="bold yellow")
    table.add_column("Details", style="white")
    table.add_column("Status / Result", style="bold green")

    for s in result.get("steps", []):
        step_name = s.get("step", "")
        details = ", ".join(f"{k}={v}" for k, v in s.items() if k != "step")
        table.add_row(step_name, details, "[green]OK[/green]")

    table.add_row("5. Merge Equality", f"Target HEAD ({result.get('main_head', '')[:8]}) == Checkpoint ({result.get('checkpoint_ref', '')[:8]})", "[bold green]100% MATCH[/bold green]" if result.get("merge_exact_match") else "[red]MISMATCH[/red]")
    table.add_row("6. Physical Archive", f"Archived {len(result.get('archived_files', []))} files: {', '.join(result.get('archived_files', []))}", "[green]PERSISTED[/green]")
    table.add_row("7. Final FSM State", f"Final task state: {result.get('final_state')}", f"[bold cyan]{result.get('final_state')}[/bold cyan]")

    console.print(table)
