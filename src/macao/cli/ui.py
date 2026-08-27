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

        table.add_row(
            str(name),
            "[green]YES[/green]" if inst else "[red]NO[/red]",
            str(ver),
            str(mode),
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
