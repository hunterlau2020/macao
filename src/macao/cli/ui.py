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
    table.add_column("CLI", style="cyan", no_wrap=True)
    table.add_column("Installed", style="bold")
    table.add_column("Version", style="green")
    table.add_column("Matrix", style="magenta")
    table.add_column("Status / Remediation", style="white")

    for r in results:
        status_text = "[green]OK[/green]" if r.installed and r.in_matrix else f"[red]FAIL[/red] ({r.remediation or r.details})"
        table.add_row(
            r.cli_name,
            "[green]YES[/green]" if r.installed else "[red]NO[/red]",
            r.version or "N/A",
            "[green]IN MATRIX[/green]" if r.in_matrix else "[yellow]UNKNOWN[/yellow]",
            status_text
        )

    console.print(table)


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
        art_table.add_column("SHA256 (tail)", style="dim")

        for a in artifacts:
            art_table.add_row(
                a["kind"],
                a["path"],
                str(a["review_round"]),
                "[green]YES[/green]" if a["consumed"] else "[yellow]NO[/yellow]",
                (a.get("sha256") or "")[:8]
            )
        console.print(art_table)
