"""
GhostOps - Process Analyzer and Anomaly Detection.
"""

import psutil
from typing import List, Dict, Any

def get_process_anomalies(top_limit: int = 5) -> Dict[str, Any]:
    """
    Scans running processes to detect hogs, zombies, and unresponsive states.
    """
    processes: List[Dict[str, Any]] = []
    zombies: List[Dict[str, Any]] = []

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = proc.info
            # Check for zombie processes
            if info.get('status') == psutil.STATUS_ZOMBIE:
                zombies.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "user": info['username'],
                })
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by CPU usage
    top_cpu = sorted(processes, key=lambda p: p.get('cpu_percent') or 0.0, reverse=True)[:top_limit]
    # Sort by Memory usage
    top_mem = sorted(processes, key=lambda p: p.get('memory_percent') or 0.0, reverse=True)[:top_limit]

    return {
        "total_processes": len(processes),
        "zombie_count": len(zombies),
        "zombies": zombies,
        "top_cpu_processes": [
            {
                "pid": p['pid'],
                "name": p['name'],
                "user": p['username'],
                "cpu_percent": round(p.get('cpu_percent') or 0.0, 1),
                "memory_percent": round(p.get('memory_percent') or 0.0, 1),
            }
            for p in top_cpu
        ],
        "top_memory_processes": [
            {
                "pid": p['pid'],
                "name": p['name'],
                "user": p['username'],
                "cpu_percent": round(p.get('cpu_percent') or 0.0, 1),
                "memory_percent": round(p.get('memory_percent') or 0.0, 1),
            }
            for p in top_mem
        ],
        "has_issues": len(zombies) > 0 or any((p.get('cpu_percent') or 0.0) > 85.0 for p in top_cpu)
    }
