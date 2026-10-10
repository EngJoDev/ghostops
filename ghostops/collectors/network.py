"""
GhostOps - Network & Port Diagnostics Collector.
"""

import socket
import psutil
from typing import Dict, Any, List

def get_network_diagnostics() -> Dict[str, Any]:
    """
    Inspects listening network ports, socket connection counts,
    and external DNS resolution.
    """
    listening_ports: List[Dict[str, Any]] = []

    try:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.status == 'LISTEN':
                port = conn.laddr.port if conn.laddr else None
                ip = conn.laddr.ip if conn.laddr else None
                pid = conn.pid
                proc_name = "Unknown"
                if pid:
                    try:
                        proc_name = psutil.Process(pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_name = f"PID:{pid}"
                
                listening_ports.append({
                    "ip": ip,
                    "port": port,
                    "type": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                    "pid": pid,
                    "process": proc_name,
                })
    except (psutil.AccessDenied, PermissionError):
        # Fallback if unprivileged user
        pass

    # Check DNS connectivity with strict timeout
    dns_ok = False
    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(1.5)
        socket.gethostbyname("google.com")
        dns_ok = True
    except Exception:
        dns_ok = False
    finally:
        socket.setdefaulttimeout(old_timeout if 'old_timeout' in locals() else None)

    return {
        "dns_resolution": "OK" if dns_ok else "FAILED",
        "listening_ports_count": len(listening_ports),
        "listening_ports": sorted(listening_ports, key=lambda x: x.get('port') or 0)[:15],
        "has_issues": not dns_ok,
    }
