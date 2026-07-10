"""Structured logging with per-module log files and run manifest tracking."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class PipelineLogger:
    """Central logger that writes to console and timestamped log files."""

    def __init__(self, log_dir: str = "logs", run_name: Optional[str] = None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_name = run_name or f"run_{timestamp}"
        self.run_log_path = self.log_dir / f"{self.run_name}.log"
        self._loggers: dict = {}
        self._setup_root_logger()

    def _setup_root_logger(self) -> None:
        root = logging.getLogger("scagent_dpm")
        root.setLevel(logging.DEBUG)
        root.handlers.clear()

        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        fh = logging.FileHandler(str(self.run_log_path), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        root.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        root.addHandler(ch)

    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(f"scagent_dpm.{name}")
        return self._loggers[name]

    def log_config(self, config_dict: dict) -> None:
        logger = self.get_logger("config")
        logger.info("Pipeline configuration loaded:")
        for key, value in config_dict.items():
            logger.info(f"  {key}: {value}")

    def log_section(self, title: str) -> None:
        logger = self.get_logger("pipeline")
        logger.info("=" * 60)
        logger.info(f"  {title}")
        logger.info("=" * 60)

    def get_run_log_path(self) -> Path:
        return self.run_log_path
