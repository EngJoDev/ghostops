"""
GhostOps - Configuration Management.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "ghostops"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG: Dict[str, Any] = {
    "llm": {
        "provider": "ollama",  # options: 'ollama', 'gemini', 'openai'
        "model": "llama3:latest",
        "api_key": "",
        "base_url": "http://localhost:11434",
        "timeout": 45,
    },
    "safety": {
        "require_confirmation": True,
        "allow_dangerous_commands": False,
        "auto_fix": False,
    },
    "collectors": {
        "docker_enabled": True,
        "system_enabled": True,
        "journal_logs_lines": 50,
    }
}

class Config:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads configuration from YAML or creates default if not exists."""
        if not self.config_path.exists():
            self._save_default()
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                # Merge loaded with default to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                for key, val in loaded.items():
                    if isinstance(val, dict) and key in merged:
                        merged[key].update(val)
                    else:
                        merged[key] = val
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def _save_default(self) -> None:
        """Writes the default configuration to disk, falling back gracefully if read-only."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        except (OSError, PermissionError):
            # Fallback to local directory or silent memory fallback
            try:
                local_dir = Path.cwd() / ".ghostops"
                local_dir.mkdir(parents=True, exist_ok=True)
                self.config_path = local_dir / "config.yaml"
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
            except Exception:
                pass

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value with fallback."""
        sec = self.data.get(section, {})
        if isinstance(sec, dict):
            return sec.get(key, default)
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Sets a configuration value and persists to disk."""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.save()

    def save(self) -> None:
        """Persists current configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.data, f, default_flow_style=False)
        except (OSError, PermissionError):
            try:
                local_dir = Path.cwd() / ".ghostops"
                local_dir.mkdir(parents=True, exist_ok=True)
                self.config_path = local_dir / "config.yaml"
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(self.data, f, default_flow_style=False)
            except Exception:
                pass

    @property
    def provider(self) -> str:
        # Check environment variable override
        env_provider = os.getenv("GHOSTOPS_PROVIDER")
        return env_provider or self.get("llm", "provider", "ollama")

    @property
    def api_key(self) -> str:
        # Check GEMINI_API_KEY, OPENAI_API_KEY, or config
        if self.provider == "gemini":
            return os.getenv("GEMINI_API_KEY") or self.get("llm", "api_key", "")
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY") or self.get("llm", "api_key", "")
        return self.get("llm", "api_key", "")

# Global singleton instance
config = Config()
