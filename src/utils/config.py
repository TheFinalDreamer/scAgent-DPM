"""Configuration loader with validation and override support."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Loads, validates, and provides access to pipeline configuration."""

    def __init__(self, config_path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, Any] = {}
        self._config_path = config_path
        if config_path:
            self.load(config_path)
        if overrides:
            self._apply_overrides(overrides)

    def load(self, config_path: str) -> "Config":
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}
        self._config_path = config_path
        return self

    def _apply_overrides(self, overrides: Dict[str, Any]) -> None:
        for key, value in overrides.items():
            parts = key.split(".")
            target = self._data
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        target = self._data
        for part in parts:
            if isinstance(target, dict) and part in target:
                target = target[part]
            else:
                return default
        return target

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Config(path={self._config_path})"


def load_config(config_path: str, overrides: Optional[Dict[str, Any]] = None) -> Config:
    return Config(config_path, overrides)
