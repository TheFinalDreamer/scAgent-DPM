"""Tests for configuration loading."""

import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import Config, load_config


def test_config_load_from_dict():
    cfg = Config()
    assert cfg.get("nonexistent", "default") == "default"


def test_config_load_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"pipeline": {"name": "test"}, "seed": 42}, f)
        path = f.name

    try:
        cfg = load_config(path)
        assert cfg.get("pipeline.name") == "test"
        assert cfg.get("seed") == 42
    finally:
        os.unlink(path)


def test_config_overrides():
    cfg = Config(None, {"seed": 99, "qc.adaptive": False})
    assert cfg.get("seed") == 99
    assert cfg.get("qc.adaptive") is False


def test_config_nested_get():
    cfg = Config(None, {"a": {"b": {"c": 123}}})
    assert cfg.get("a.b.c") == 123
    assert cfg.get("a.b.x", "missing") == "missing"


def test_demo_config_loadable():
    """Verify demo.yaml is valid."""
    demo_path = Path(__file__).resolve().parent.parent / "configs" / "demo.yaml"
    cfg = load_config(str(demo_path))
    assert cfg.get("pipeline.name") == "scAgent-DPM-demo"
    assert cfg.get("seed") == 42


def test_all_configs_loadable():
    """Verify all config YAML files are valid."""
    config_dir = Path(__file__).resolve().parent.parent / "configs"
    for cfg_file in config_dir.glob("*.yaml"):
        cfg = load_config(str(cfg_file))
        assert cfg.to_dict() is not None, f"Failed to load {cfg_file.name}"
