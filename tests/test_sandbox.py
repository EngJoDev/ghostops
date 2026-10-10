"""
Tests for GhostOps Sandbox and Risk Classifier.
"""

import unittest
from ghostops.core.sandbox import classify_command_risk, RiskLevel

class TestSandbox(unittest.TestCase):

    def test_classify_safe_commands(self):
        safe_cmds = ["df -h", "ps aux", "cat /etc/os-release", "uptime", "docker ps", "systemctl status nginx"]
        for cmd in safe_cmds:
            risk, _ = classify_command_risk(cmd)
            self.assertEqual(risk, RiskLevel.SAFE, f"Expected SAFE for: {cmd}")

    def test_classify_caution_commands(self):
        caution_cmds = ["systemctl restart nginx", "docker restart web", "sync"]
        for cmd in caution_cmds:
            risk, _ = classify_command_risk(cmd)
            self.assertEqual(risk, RiskLevel.CAUTION, f"Expected CAUTION for: {cmd}")

    def test_classify_dangerous_commands(self):
        dangerous_cmds = ["rm -rf ./old_logs", "kill -9 1234", "reboot"]
        for cmd in dangerous_cmds:
            risk, _ = classify_command_risk(cmd)
            self.assertEqual(risk, RiskLevel.DANGEROUS, f"Expected DANGEROUS for: {cmd}")

    def test_classify_forbidden_destructive_commands(self):
        forbidden_cmds = ["rm -rf /", "mkfs.ext4 /dev/sda1", "dd if=/dev/zero of=/dev/sda"]
        for cmd in forbidden_cmds:
            risk, _ = classify_command_risk(cmd)
            self.assertEqual(risk, RiskLevel.FORBIDDEN, f"Expected FORBIDDEN for: {cmd}")

if __name__ == "__main__":
    unittest.main()
