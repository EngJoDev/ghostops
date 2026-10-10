"""
GhostOps - Telemetry Collectors Package.
"""

from ghostops.collectors.system import get_system_vitals
from ghostops.collectors.docker import get_docker_telemetry, get_container_logs
from ghostops.collectors.process import get_process_anomalies
from ghostops.collectors.network import get_network_diagnostics
from ghostops.collectors.logs import get_log_telemetry

def collect_full_diagnostic_snapshot() -> dict:
    """
    Gathers a complete snapshot of the machine across:
    System hardware, running processes, Docker containers, network, and logs.
    """
    return {
        "system": get_system_vitals(),
        "processes": get_process_anomalies(),
        "docker": get_docker_telemetry(),
        "network": get_network_diagnostics(),
        "logs": get_log_telemetry(),
    }
