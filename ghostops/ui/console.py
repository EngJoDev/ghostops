"""
GhostOps - Console Utilities and Rich UI Elements.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import List, Dict, Any, Optional

console = Console()

def success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✔[/bold green] {message}")

def info(message: str) -> None:
    """Print informational message."""
    console.print(f"[bold cyan]ℹ[/bold cyan] {message}")

def warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[bold yellow]▲[/bold yellow] {message}")

def error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]✖[/bold red] {message}")

def create_status_table(metrics: Dict[str, Any]) -> Table:
    """Generate a clean status table from a metrics dictionary."""
    table = Table(title="System Vital Telemetry", show_header=True, header_style="bold magenta", border_style="dim")
    table.add_column("Component", style="cyan", width=18)
    table.add_column("Status / Metric", style="white")
    table.add_column("Health", justify="right", width=12)

    for comp, data in metrics.items():
        status_val = str(data.get("value", "N/A"))
        health = data.get("health", "OK")
        
        if health == "CRITICAL":
            health_badge = "[bold white on red] CRITICAL [/bold white on red]"
        elif health == "WARNING":
            health_badge = "[bold black on yellow] WARNING [/bold black on yellow]"
        else:
            health_badge = "[bold green]● OK[/bold green]"
            
        table.add_row(comp, status_val, health_badge)

    return table

def create_issue_card(severity: str, title: str, description: str, remediation: Optional[str] = None) -> Panel:
    """Render a highlighted issue diagnostic card."""
    border_color = "red" if severity == "CRITICAL" else ("yellow" if severity == "WARNING" else "cyan")
    
    content = Text()
    content.append(f"Issue: {title}\n", style="bold white")
    content.append(f"{description}\n\n", style="dim white")
    
    if remediation:
        content.append("Suggested Remediation:\n", style="bold green")
        content.append(f"{remediation}\n", style="italic white")
        
    badge = f"[{'bold white on red' if severity == 'CRITICAL' else 'bold black on yellow'}] {severity} [/{'bold white on red' if severity == 'CRITICAL' else 'bold black on yellow'}]"
    
    return Panel(
        content,
        title=f"{badge} {title}",
        border_style=border_color,
        padding=(1, 2)
    )
