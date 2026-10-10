"""
GhostOps - Safe Execution Engine & Risk Classification Sandbox.
"""

import re
import subprocess
import shlex
from typing import Tuple, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

FORBIDDEN_PATTERNS = [
    r"\brm\s+-(?:r|f|rf|fr)\s+/(?:\s|$|\*)",       # rm -rf /
    r"\bmkfs\b",                                   # Format filesystem
    r"\bdd\s+if=.*?of=/dev/[a-z]+",                # Raw disk overwrite
    r">:?\s*/dev/sd[a-z]",                         # Direct disk redirection
    r"\bchmod\s+-(?:R)\s+777\s+/(?:\s|$)",        # Dangerous root permissions
]

SAFE_COMMANDS = {
    "ls", "cat", "df", "free", "uptime", "ps", "top", "htop", "btop",
    "grep", "tail", "head", "wc", "dmesg", "journalctl", "uname",
    "whoami", "id", "docker ps", "docker stats", "docker logs",
    "systemctl status", "netstat", "ss", "ip", "ifconfig", "ping"
}

CAUTION_COMMANDS = {
    "systemctl restart", "systemctl reload", "docker restart",
    "docker stop", "docker start", "service", "systemctl start",
    "apt-get clean", "sync"
}

class RiskLevel:
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGEROUS = "DANGEROUS"
    FORBIDDEN = "FORBIDDEN"

def classify_command_risk(command: str) -> Tuple[str, str]:
    """
    Analyzes bash command string and returns (RiskLevel, Reason).
    """
    cmd_clean = command.strip()

    # 1. Check strictly forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return RiskLevel.FORBIDDEN, "Command matches destructive system pattern and is blocked for safety."

    # 2. Check if dangerous
    if any(k in cmd_clean for k in ["rm ", "kill -9", "killall", "fdisk", "parted", "iptables -F", "shutdown", "reboot"]):
        return RiskLevel.DANGEROUS, "Command modifies system processes, firewall, or deletes files."

    # 3. Check if caution
    for prefix in CAUTION_COMMANDS:
        if cmd_clean.startswith(prefix) or f"sudo {prefix}" in cmd_clean:
            return RiskLevel.CAUTION, "Command alters service states or restarts daemons."

    # 4. Check if safe
    for prefix in SAFE_COMMANDS:
        if cmd_clean.startswith(prefix) or f"sudo {prefix}" in cmd_clean:
            return RiskLevel.SAFE, "Read-only inspection command."

    # Default to Caution for unknown commands
    return RiskLevel.CAUTION, "Standard administrative command."

def execute_remediation(
    command: str,
    explanation: Optional[str] = None,
    interactive: bool = True
) -> Dict[str, Any]:
    """
    Safely prompts user and executes the proposed remediation command.
    """
    risk, reason = classify_command_risk(command)

    # If Forbidden, block immediately
    if risk == RiskLevel.FORBIDDEN:
        console.print(Panel(
            f"[bold red]BLOCKED:[/bold red] {reason}\n[dim]Command: {command}[/dim]",
            title="[bold white on red] FORBIDDEN COMMAND [/bold white on red]",
            border_style="red"
        ))
        return {"success": False, "blocked": True, "error": reason}

    # Format risk badge
    if risk == RiskLevel.SAFE:
        risk_style = "bold white on green"
    elif risk == RiskLevel.CAUTION:
        risk_style = "bold black on yellow"
    else:
        risk_style = "bold white on red"

    # Display execution proposal panel
    info_text = f"[bold white]Proposed Remediation:[/bold white]\n[bold green]$ {command}[/bold green]\n\n"
    if explanation:
        info_text += f"[dim]{explanation}[/dim]\n"
    info_text += f"[bold]Risk Assessment:[/bold] [{risk_style}] {risk} [/{risk_style}] - {reason}"

    console.print(Panel(info_text, title="GhostOps Remediation Engine", border_style="cyan"))

    if interactive:
        confirmed = Confirm.ask("Do you want GhostOps to execute this remediation?", default=True)
        if not confirmed:
            console.print("[dim yellow]Operation skipped by user.[/dim yellow]")
            return {"success": False, "skipped": True}

    # Execute command
    try:
        console.print(f"[dim cyan]Executing: {command}...[/dim cyan]")
        proc = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        success = proc.returncode == 0
        if success:
            console.print("[bold green]✔ Remediation completed successfully![/bold green]")
            if proc.stdout.strip():
                console.print(Panel(proc.stdout.strip(), title="Output", border_style="green"))
        else:
            console.print(f"[bold red]✖ Command exited with status {proc.returncode}[/bold red]")
            if proc.stderr.strip():
                console.print(Panel(proc.stderr.strip(), title="Error Output", border_style="red"))

        return {
            "success": success,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }
    except subprocess.TimeoutExpired:
        console.print("[bold red]✖ Command execution timed out after 30 seconds.[/bold red]")
        return {"success": False, "error": "Execution timed out"}
    except Exception as e:
        console.print(f"[bold red]✖ Failed to execute command: {e}[/bold red]")
        return {"success": False, "error": str(e)}
