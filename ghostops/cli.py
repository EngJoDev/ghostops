"""
GhostOps - Terminal CLI Interface.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ghostops import __version__
from ghostops.ui.banners import print_banner
from ghostops.ui.console import console, success, info, warning, error
from ghostops.core.agent import SREAgent
from ghostops.collectors import collect_full_diagnostic_snapshot
from ghostops.config import config

@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", "-v", is_flag=True, help="Show GhostOps version.")
def app(ctx: click.Context, version: bool):
    """GhostOps - Autonomous Linux & DevOps SRE Terminal Copilot."""
    if version:
        print_banner(console)
        return
    if ctx.invoked_subcommand is None:
        print_banner(console)
        console.print("[dim]Use [bold cyan]ghostops --help[/bold cyan] to see available commands.[/dim]\n")
        console.print("[bold]Quick commands:[/bold]")
        console.print("  • [cyan]ghostops doctor[/cyan]       Run full host SRE diagnostic & health check")
        console.print("  • [cyan]ghostops doctor --fix[/cyan] Run diagnostic and interactively fix detected issues")
        console.print("  • [cyan]ghostops top[/cyan]          Show live resource consumption and containers")
        console.print("  • [cyan]ghostops ask '<q>'[/cyan]    Ask troubleshooting questions with live context")
        console.print("  • [cyan]ghostops logs[/cyan]         Inspect high-priority system logs")
        console.print("  • [cyan]ghostops config[/cyan]       Configure LLM provider and API keys\n")

@app.command()
@click.option("--fix", is_flag=True, help="Automatically suggest and prompt to execute fixes.")
@click.option("--yes", "-y", is_flag=True, help="Non-interactive mode: auto-approve safe fixes.")
def doctor(fix: bool, yes: bool):
    """Run full host SRE diagnostic & health check."""
    print_banner(console)
    agent = SREAgent()
    agent.run_diagnostics(auto_fix=fix, interactive=not yes)

@app.command()
@click.argument("question")
def ask(question: str):
    """Ask SRE questions with live system context (e.g. ghostops ask 'why is port 80 busy?')."""
    agent = SREAgent()
    agent.ask(question)

@app.command()
def top():
    """Live snapshot of resource consumption and container statuses."""
    snapshot = collect_full_diagnostic_snapshot()
    sys_data = snapshot.get("system", {})
    procs = snapshot.get("processes", {})
    docker = snapshot.get("docker", {})

    console.print(Panel(
        f"[bold cyan]Host:[/bold cyan] {sys_data.get('os', {}).get('distro')} | "
        f"[bold yellow]CPU:[/bold yellow] {sys_data.get('cpu', {}).get('percent')}% | "
        f"[bold magenta]RAM:[/bold magenta] {sys_data.get('memory', {}).get('percent')}% ({sys_data.get('memory', {}).get('used_gb')}GB / {sys_data.get('memory', {}).get('total_gb')}GB) | "
        f"[bold green]Uptime:[/bold green] {sys_data.get('os', {}).get('uptime_hours')} hours",
        title="[bold white] GhostOps Process & Host Monitor [/bold white]",
        border_style="cyan"
    ))

    # Top CPU processes table
    table_cpu = Table(title="Top CPU Processes", border_style="dim")
    table_cpu.add_column("PID", style="cyan", width=8)
    table_cpu.add_column("Name", style="white")
    table_cpu.add_column("User", style="dim")
    table_cpu.add_column("CPU %", justify="right", style="bold yellow")
    table_cpu.add_column("RAM %", justify="right")

    for p in procs.get("top_cpu_processes", []):
        table_cpu.add_row(str(p['pid']), p['name'], p['user'] or "-", f"{p['cpu_percent']}%", f"{p['memory_percent']}%")

    console.print(table_cpu)

    # Docker container summary table if running
    if docker.get("running"):
        table_docker = Table(title="Docker Containers", border_style="dim")
        table_docker.add_column("ID", style="dim", width=12)
        table_docker.add_column("Name", style="cyan")
        table_docker.add_column("Image", style="white")
        table_docker.add_column("Status", style="green")

        for c in docker.get("containers", [])[:8]:
            table_docker.add_row(c.get("id") or "-", c.get("name") or "-", c.get("image") or "-", c.get("status") or "-")

        console.print(table_docker)

@app.command()
@click.option("--lines", "-n", default=20, help="Number of recent log lines to inspect.")
def logs(lines: int):
    """Inspect and analyze recent critical system errors."""
    from ghostops.collectors.logs import get_recent_critical_logs, get_failed_services

    failed_services = get_failed_services()
    critical_logs = get_recent_critical_logs(lines=lines)

    if failed_services:
        console.print("\n[bold red]Failed Systemd Services:[/bold red]")
        for s in failed_services:
            console.print(f"  • [bold red]{s['unit']}[/bold red] ({s['sub']}) - {s.get('description', '')}")

    console.print(f"\n[bold yellow]Recent High-Priority System Logs (Journalctl):[/bold yellow]")
    if critical_logs:
        for log_line in critical_logs:
            console.print(f"  [dim]>[/dim] {log_line}")
    else:
        console.print("  [green]✔ No critical log errors in the requested window.[/green]")

@app.command()
@click.option("--provider", type=click.Choice(["ollama", "gemini", "openai"]), help="Set active LLM provider.")
@click.option("--model", help="Set model name (e.g. llama3, gemini-1.5-flash).")
@click.option("--api-key", help="Set API key for the chosen provider.")
@click.option("--base-url", help="Set custom base URL for Ollama or OpenAI compatible server.")
def config_cmd(provider, model, api_key, base_url):
    """View or update GhostOps configuration."""
    if provider:
        config.set("llm", "provider", provider)
        success(f"Provider set to: {provider}")
    if model:
        config.set("llm", "model", model)
        success(f"Model set to: {model}")
    if api_key:
        config.set("llm", "api_key", api_key)
        success("API Key updated successfully.")
    if base_url:
        config.set("llm", "base_url", base_url)
        success(f"Base URL set to: {base_url}")

    # Display current configuration
    table = Table(title="Current Configuration", border_style="dim")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Active Provider", config.provider)
    table.add_row("Model", config.get("llm", "model"))
    table.add_row("Base URL", config.get("llm", "base_url"))
    
    key_val = config.api_key
    masked_key = f"{key_val[:4]}...{key_val[-4:]}" if len(key_val) > 8 else ("Configured" if key_val else "Not Set")
    table.add_row("API Key", masked_key)
    table.add_row("Config File", str(config.config_path))

    console.print(table)

# Alias config to avoid keyword conflict
app.add_command(config_cmd, name="config")

if __name__ == "__main__":
    app()
