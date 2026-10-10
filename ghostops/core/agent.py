"""
GhostOps - Autonomous SRE Agent Orchestrator.
"""

import json
import re
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ghostops.collectors import collect_full_diagnostic_snapshot
from ghostops.core.sandbox import execute_remediation
from ghostops.llm import get_llm_provider, SRE_SYSTEM_PROMPT, SRE_USER_PROMPT_TEMPLATE
from ghostops.ui.console import (
    console, success, info, warning, error,
    create_status_table, create_issue_card
)

class SREAgent:
    """The central Autonomous SRE Agent for GhostOps."""

    def __init__(self):
        self.llm = get_llm_provider()

    def run_diagnostics(self, auto_fix: bool = False, interactive: bool = True) -> Dict[str, Any]:
        """
        Executes a full system scan, analyzes root causes with heuristics and LLM,
        and optionally guides remediation.
        """
        snapshot = {}
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]{task.description}[/bold cyan]"),
            console=console,
            transient=True
        ) as progress:
            task1 = progress.add_task("Gathering host telemetry and logs...", total=None)
            snapshot = collect_full_diagnostic_snapshot()
            progress.update(task1, completed=True)

        # 1. Print vital telemetry summary table
        sys_data = snapshot.get("system", {})
        cpu = sys_data.get("cpu", {})
        mem = sys_data.get("memory", {})
        docker = snapshot.get("docker", {})
        logs = snapshot.get("logs", {})

        metrics_summary = {
            "OS & Kernel": {
                "value": f"{sys_data.get('os', {}).get('distro')} (Kernel {sys_data.get('os', {}).get('kernel')})",
                "health": "OK"
            },
            "CPU Load": {
                "value": f"{cpu.get('percent')}% (1m avg: {cpu.get('load_1m')})",
                "health": cpu.get("health", "OK")
            },
            "Memory (RAM)": {
                "value": f"{mem.get('percent')}% ({mem.get('used_gb')}GB / {mem.get('total_gb')}GB)",
                "health": mem.get("health", "OK")
            },
            "Docker Daemon": {
                "value": (
                    f"{docker.get('total_containers')} containers ({docker.get('crashed_count')} issues)"
                    if docker.get("running") else "Not Running / Disabled"
                ),
                "health": "WARNING" if docker.get("has_crashes") else "OK"
            },
            "Failed Services": {
                "value": f"{logs.get('failed_services_count')} failed units",
                "health": "CRITICAL" if logs.get("failed_services_count", 0) > 0 else "OK"
            }
        }

        console.print(create_status_table(metrics_summary))
        console.print()

        # 2. Heuristic Rule Engine (Always runs, zero-dependency offline safety net)
        heuristic_issues = self._evaluate_heuristics(snapshot)

        # 3. Deep AI Reasoning (if provider is available)
        ai_diagnosis = None
        if self.llm.is_available():
            with Progress(
                SpinnerColumn(spinner_name="aesthetic"),
                TextColumn("[bold magenta]Consulting GhostOps SRE Neural Engine...[/bold magenta]"),
                console=console,
                transient=True
            ) as progress:
                task2 = progress.add_task("Analyzing...", total=None)
                try:
                    ai_diagnosis = self._query_llm_diagnosis(snapshot)
                except Exception as e:
                    console.print(f"[dim yellow]Notice: AI inference skipped ({e}). Proceeding with native heuristics.[/dim yellow]")
                progress.update(task2, completed=True)

        # Combine issues (prioritize AI if valid, fallback to heuristics)
        issues = []
        if ai_diagnosis and ai_diagnosis.get("issues"):
            issues = ai_diagnosis["issues"]
        else:
            issues = heuristic_issues

        # 4. Display findings
        if not issues:
            console.print(Panel(
                "[bold green]✔ Host is operating within healthy parameters.[/bold green]\n"
                "[dim]No critical memory leaks, zombie processes, or failed systemd daemons detected.[/dim]",
                title="[bold green] Diagnostic Result: All Systems Optimal [/bold green]",
                border_style="green"
            ))
            return {"status": "HEALTHY", "issues": []}

        console.print(f"[bold yellow]Found {len(issues)} operational issue(s) requiring attention:[/bold yellow]\n")
        for issue in issues:
            console.print(create_issue_card(
                severity=issue.get("severity", "WARNING"),
                title=issue.get("title", "Detected Anomaly"),
                description=issue.get("root_cause") or issue.get("description", ""),
                remediation=issue.get("remediation_command")
            ))

        # 5. Remediation Execution Loop
        if auto_fix or interactive:
            remediable = [i for i in issues if i.get("remediation_command")]
            if remediable:
                console.print("\n[bold cyan]─── Interactive Remediation Phase ───[/bold cyan]\n")
                for item in remediable:
                    cmd = item["remediation_command"]
                    explanation = item.get("remediation_explanation") or item.get("root_cause")
                    execute_remediation(cmd, explanation=explanation, interactive=interactive)

        return {"status": "DEGRADED" if any(i.get("severity") == "CRITICAL" for i in issues) else "WARNING", "issues": issues}

    def _evaluate_heuristics(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Native offline heuristic rules to detect standard Linux failures."""
        issues: List[Dict[str, Any]] = []

        # Check Failed Systemd Services
        failed_services = snapshot.get("logs", {}).get("failed_services", [])
        for svc in failed_services:
            unit_name = svc.get("unit")
            issues.append({
                "severity": "CRITICAL",
                "title": f"Failed Systemd Service: {unit_name}",
                "root_cause": f"Service '{unit_name}' is in active ({svc.get('sub')}) failed state.",
                "remediation_command": f"systemctl restart {unit_name}",
                "remediation_explanation": f"Restarts the failed systemd service '{unit_name}' to restore functionality."
            })

        # Check Docker Crashes
        crashed_containers = snapshot.get("docker", {}).get("crashed_containers", [])
        for c in crashed_containers:
            c_name = c.get("name")
            reason = c.get("reason", "Unknown container failure")
            issues.append({
                "severity": "WARNING",
                "title": f"Unhealthy Docker Container: {c_name}",
                "root_cause": f"Container '{c_name}' encountered: {reason} (Status: {c.get('status')}).",
                "remediation_command": f"docker restart {c_name}",
                "remediation_explanation": f"Restarts container '{c_name}' to recover from crash state."
            })

        # Check Memory Pressure
        mem = snapshot.get("system", {}).get("memory", {})
        if mem.get("percent", 0) > 90:
            top_mems = snapshot.get("processes", {}).get("top_memory_processes", [])
            top_p = top_mems[0] if top_mems else {}
            issues.append({
                "severity": "CRITICAL",
                "title": f"High Memory Saturation ({mem.get('percent')}%)",
                "root_cause": f"System RAM is at {mem.get('percent')}%. Top consumer is {top_p.get('name')} (PID {top_p.get('pid')}) using {top_p.get('memory_percent')}%.",
                "remediation_command": f"kill -15 {top_p.get('pid')}" if top_p.get("pid") else None,
                "remediation_explanation": f"Sends SIGTERM to process {top_p.get('name')} (PID {top_p.get('pid')}) for graceful memory release."
            })

        # Check Zombie Processes
        zombies = snapshot.get("processes", {}).get("zombies", [])
        if zombies:
            z_names = ", ".join(f"{z['name']}({z['pid']})" for z in zombies[:3])
            issues.append({
                "severity": "WARNING",
                "title": f"Zombie Processes Detected ({len(zombies)})",
                "root_cause": f"Unreaped child processes remaining in process table: {z_names}.",
                "remediation_command": None,
                "remediation_explanation": "Investigate parent process or reap manually."
            })

        # Check Disk Space
        for d in snapshot.get("system", {}).get("disks", []):
            if d.get("percent", 0) > 90:
                issues.append({
                    "severity": "CRITICAL",
                    "title": f"Disk Near Full on {d.get('mount')} ({d.get('percent')}%)",
                    "root_cause": f"Partition {d.get('mount')} has only {d.get('free_gb')} GB remaining.",
                    "remediation_command": "sudo journalctl --vacuum-time=2d && sudo apt-get clean",
                    "remediation_explanation": "Cleans old systemd journal archives and apt package cache to reclaim disk space."
                })

        return issues

    def _query_llm_diagnosis(self, snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Serializes snapshot, prompts LLM, and parses structured SRE output."""
        prompt = SRE_USER_PROMPT_TEMPLATE.format(
            system_json=json.dumps(snapshot.get("system"), indent=2),
            process_json=json.dumps(snapshot.get("processes"), indent=2),
            docker_json=json.dumps(snapshot.get("docker"), indent=2),
            network_json=json.dumps(snapshot.get("network"), indent=2),
            logs_json=json.dumps(snapshot.get("logs"), indent=2),
        )

        response_text = self.llm.generate(prompt, system_prompt=SRE_SYSTEM_PROMPT)
        
        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def ask(self, question: str) -> None:
        """Interactive Linux / DevOps troubleshooting assistant."""
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]Gathering relevant host context...[/bold cyan]"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Scanning...", total=None)
            snapshot = collect_full_diagnostic_snapshot()
            progress.update(task, completed=True)

        user_prompt = f"""User Question: {question}

Host Context:
- OS: {snapshot.get('system', {}).get('os', {}).get('distro')} (Kernel {snapshot.get('system', {}).get('os', {}).get('kernel')})
- CPU Usage: {snapshot.get('system', {}).get('cpu', {}).get('percent')}%
- RAM Usage: {snapshot.get('system', {}).get('memory', {}).get('percent')}%
- Docker Running: {snapshot.get('docker', {}).get('running')}
- Failed Services: {[s.get('unit') for s in snapshot.get('logs', {}).get('failed_services', [])]}

Provide a direct, practical, and expert answer with bash commands where applicable.
"""
        if self.llm.is_available():
            with Progress(
                SpinnerColumn(spinner_name="aesthetic"),
                TextColumn("[bold magenta]GhostOps is formulating response...[/bold magenta]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Thinking...", total=None)
                try:
                    answer = self.llm.generate(user_prompt, system_prompt="You are GhostOps, a Senior Linux SRE expert.")
                except Exception as e:
                    answer = f"Error querying LLM: {e}"
                progress.update(task, completed=True)
            
            console.print(Panel(answer, title=f"[bold cyan]GhostOps SRE Advice[/bold cyan]", border_style="cyan"))
        else:
            console.print(Panel(
                f"[bold yellow]No LLM provider configured or reachable.[/bold yellow]\n\n"
                f"To enable natural language Q&A, run:\n"
                f"  [bold green]ghostops config --provider gemini --api-key YOUR_KEY[/bold green]\n"
                f"or start Ollama locally:\n"
                f"  [bold green]ollama run llama3[/bold green]",
                title="Configuration Needed",
                border_style="yellow"
            ))
