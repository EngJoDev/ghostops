"""
GhostOps - Linux System Logs & Failed Services Collector.
"""

import subprocess
import shutil
from typing import Dict, Any, List

def get_failed_services() -> List[Dict[str, str]]:
    """Inspects systemd for failed units."""
    if not shutil.which("systemctl"):
        return []

    try:
        proc = subprocess.run(
            ["systemctl", "--failed", "--no-legend", "--plain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        failed: List[Dict[str, str]] = []
        if proc.returncode == 0 and proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 4:
                    failed.append({
                        "unit": parts[0],
                        "load": parts[1],
                        "active": parts[2],
                        "sub": parts[3],
                        "description": " ".join(parts[4:]) if len(parts) > 4 else ""
                    })
        return failed
    except Exception:
        return []

def get_recent_critical_logs(lines: int = 30) -> List[str]:
    """Retrieves high-priority error logs from journalctl."""
    if not shutil.which("journalctl"):
        return []

    try:
        proc = subprocess.run(
            ["journalctl", "-p", "err..emerg", "-n", str(lines), "--no-pager"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=6
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return [line.strip() for line in proc.stdout.strip().split("\n") if line.strip()]
        return []
    except Exception:
        return []

def get_log_telemetry() -> Dict[str, Any]:
    """Collects system-level errors and failed service telemetry."""
    failed_services = get_failed_services()
    critical_logs = get_recent_critical_logs(lines=25)

    return {
        "failed_services_count": len(failed_services),
        "failed_services": failed_services,
        "critical_logs_count": len(critical_logs),
        "critical_logs": critical_logs[-15:],
        "has_issues": len(failed_services) > 0 or len(critical_logs) > 0
    }
