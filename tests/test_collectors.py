"""
Tests for GhostOps Telemetry Collectors.
"""

import unittest
from ghostops.collectors.system import get_system_vitals
from ghostops.collectors.process import get_process_anomalies
from ghostops.collectors.network import get_network_diagnostics
from ghostops.collectors.docker import get_docker_telemetry
from ghostops.collectors.logs import get_log_telemetry

class TestCollectors(unittest.TestCase):

    def test_system_vitals(self):
        vitals = get_system_vitals()
        self.assertIn("cpu", vitals)
        self.assertIn("memory", vitals)
        self.assertIn("os", vitals)
        self.assertIsInstance(vitals["cpu"]["percent"], (int, float))
        self.assertIsInstance(vitals["memory"]["percent"], (int, float))
        self.assertGreater(vitals["memory"]["total_gb"], 0)

    def test_process_anomalies(self):
        procs = get_process_anomalies(top_limit=3)
        self.assertIn("total_processes", procs)
        self.assertIn("top_cpu_processes", procs)
        self.assertIn("top_memory_processes", procs)
        self.assertIsInstance(procs["top_cpu_processes"], list)

    def test_network_diagnostics(self):
        net = get_network_diagnostics()
        self.assertIn("dns_resolution", net)
        self.assertIn("listening_ports", net)

    def test_docker_telemetry(self):
        docker = get_docker_telemetry()
        self.assertIn("installed", docker)
        self.assertIn("running", docker)

    def test_log_telemetry(self):
        logs = get_log_telemetry()
        self.assertIn("failed_services", logs)
        self.assertIn("critical_logs", logs)

if __name__ == "__main__":
    unittest.main()
