"""
GhostOps - Docker Diagnostics and Container Health Collector.
"""

import subprocess
import json
import shutil
from typing import Dict, Any, List

def is_docker_available() -> bool:
    """Checks if the docker binary exists in system PATH."""
    return shutil.which("docker") is not None

def get_docker_telemetry() -> Dict[str, Any]:
    """
    Collects Docker container health status, failed containers,
    and restart loop indicators.
    """
    if not is_docker_available():
        return {
            "installed": False,
            "running": False,
            "error": "Docker binary not found on host",
            "containers": [],
            "crashed_containers": []
        }

    # Check if docker daemon is accessible
    try:
        check_proc = subprocess.run(
            ["docker", "info", "--format", "{{json .}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if check_proc.returncode != 0:
            return {
                "installed": True,
                "running": False,
                "error": check_proc.stderr.strip() or "Docker daemon is not running or socket permission denied",
                "containers": [],
                "crashed_containers": []
            }
    except Exception as e:
        return {
            "installed": True,
            "running": False,
            "error": str(e),
            "containers": [],
            "crashed_containers": []
        }

    # List all containers (running and stopped)
    try:
        ps_proc = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        
        containers: List[Dict[str, Any]] = []
        crashed: List[Dict[str, Any]] = []

        if ps_proc.returncode == 0 and ps_proc.stdout.strip():
            for line in ps_proc.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    c = json.loads(line)
                    status_str = c.get("Status", "").lower()
                    state_str = c.get("State", "").lower()
                    
                    is_unhealthy = "unhealthy" in status_str
                    is_restarting = "restarting" in status_str or state_str == "restarting"
                    is_exited_error = "exited (" in status_str and "exited (0)" not in status_str

                    container_info = {
                        "id": c.get("ID"),
                        "name": c.get("Names"),
                        "image": c.get("Image"),
                        "state": c.get("State"),
                        "status": c.get("Status"),
                        "ports": c.get("Ports"),
                    }
                    containers.append(container_info)

                    if is_unhealthy or is_restarting or is_exited_error:
                        container_info["reason"] = (
                            "Unhealthy Healthcheck" if is_unhealthy
                            else ("Crash Restart Loop" if is_restarting else "Exited with non-zero exit code")
                        )
                        crashed.append(container_info)
                except json.JSONDecodeError:
                    continue

        return {
            "installed": True,
            "running": True,
            "total_containers": len(containers),
            "crashed_count": len(crashed),
            "containers": containers,
            "crashed_containers": crashed,
            "has_crashes": len(crashed) > 0
        }
    except Exception as e:
        return {
            "installed": True,
            "running": True,
            "error": f"Failed to list containers: {e}",
            "containers": [],
            "crashed_containers": []
        }

def get_container_logs(container_id_or_name: str, lines: int = 40) -> str:
    """Fetches the last N lines of logs from a specific container."""
    if not is_docker_available():
        return "Docker not available."
    try:
        proc = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_id_or_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8
        )
        return proc.stdout + proc.stderr
    except Exception as e:
        return f"Failed to retrieve logs: {e}"
