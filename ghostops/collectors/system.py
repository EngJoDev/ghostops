"""
GhostOps - System Telemetry Collector (CPU, RAM, Disk, OS).
"""

import os
import platform
import time
import psutil
from typing import Dict, Any, List

def get_system_vitals() -> Dict[str, Any]:
    """
    Collects real-time hardware and OS metrics.
    Returns clean dictionary with human-readable and raw metrics.
    """
    # CPU Metrics
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count_logical = psutil.cpu_count(logical=True) or 1
    cpu_count_physical = psutil.cpu_count(logical=False) or 1
    
    try:
        load_avg = os.getloadavg()
    except (AttributeError, OSError):
        load_avg = (0.0, 0.0, 0.0)

    # Memory Metrics
    vmem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk Metrics (deduplicate physical mounts by device)
    disks: List[Dict[str, Any]] = []
    seen_devices = set()
    for part in psutil.disk_partitions(all=False):
        if part.fstype and not part.mountpoint.startswith(('/snap', '/boot/efi')):
            # Prevent duplicate device reporting for container bind mounts
            dev_key = part.device
            if dev_key in seen_devices:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                seen_devices.add(dev_key)
                disks.append({
                    "mount": part.mountpoint,
                    "device": part.device,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                continue

    # OS / Kernel info
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    uptime_hours = round(uptime_seconds / 3600, 1)

    return {
        "os": {
            "system": platform.system(),
            "distro": _get_distro_name(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "uptime_hours": uptime_hours,
        },
        "cpu": {
            "percent": cpu_percent,
            "logical_cores": cpu_count_logical,
            "physical_cores": cpu_count_physical,
            "load_1m": round(load_avg[0], 2),
            "load_5m": round(load_avg[1], 2),
            "load_15m": round(load_avg[2], 2),
            "health": "CRITICAL" if cpu_percent > 90 else ("WARNING" if cpu_percent > 75 else "OK"),
        },
        "memory": {
            "total_gb": round(vmem.total / (1024**3), 2),
            "used_gb": round(vmem.used / (1024**3), 2),
            "available_gb": round(vmem.available / (1024**3), 2),
            "percent": vmem.percent,
            "swap_used_percent": swap.percent,
            "health": "CRITICAL" if vmem.percent > 92 else ("WARNING" if vmem.percent > 80 else "OK"),
        },
        "disks": disks,
    }

def _get_distro_name() -> str:
    """Detects Linux distribution name if available in /etc/os-release."""
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
    return platform.platform()
