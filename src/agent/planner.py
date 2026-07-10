"""Agent planner: reads config, validates data, orchestrates module execution."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .state import PipelineState

logger = logging.getLogger("scagent_dpm.agent.planner")


class AgentPlanner:
    """Lightweight agent planner for scAgent-DPM pipeline orchestration."""

    def __init__(self, config: Dict[str, Any], output_dir: str = "results"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state = PipelineState(run_name=config.get("pipeline", {}).get("name", "scagent_run"))
        self._available_modules = self._detect_modules()

    def _detect_modules(self) -> Dict[str, bool]:
        """Detect which modules are available for execution."""
        available = {
            "qc": self.config.get("run_qc", True),
            "annotation": self.config.get("run_annotation", True),
            "perturbation": self.config.get("run_perturbation", True),
            "dynamics": self.config.get("run_dynamics", True),
        }
        return available

    def plan(self) -> Dict[str, Any]:
        """Generate execution plan from config and data inspection."""
        plan = {
            "run_name": self.state.run_name,
            "output_dir": str(self.output_dir),
            "modules": [],
            "estimated_steps": 0,
        }

        required = ["data_ingestion"]
        if self._available_modules.get("qc"):
            required.append("qc")
        required.append("preprocessing")
        if self._available_modules.get("annotation"):
            required.append("annotation")
        if self._available_modules.get("perturbation"):
            required.append("perturbation")
        if self._available_modules.get("dynamics"):
            required.append("dynamics")
        if any([self._available_modules.get("perturbation"),
               self._available_modules.get("dynamics")]):
            required.append("dprs")
        required.append("reporting")

        plan["modules"] = required
        plan["estimated_steps"] = len(required)
        plan["server_mode"] = self.config.get("server_mode", False)
        plan["fallback_allowed"] = self.config.get("fallback_allowed", False)
        plan["seed"] = self.config.get("seed", 42)

        logger.info(f"Pipeline plan: {len(required)} modules: {required}")
        return plan

    def execute_module(self, module_name: str, execute_fn, **kwargs) -> Dict[str, Any]:
        """Execute a single module with state tracking."""
        t0 = time.time()
        is_fallback = False
        error = None
        result = None

        try:
            result = execute_fn(**kwargs)
            if isinstance(result, tuple) and len(result) >= 2:
                meta = result[1] if isinstance(result[1], dict) else {}
                is_fallback = meta.get("is_fallback", False)
            duration = time.time() - t0
            status = "fallback" if is_fallback else "success"
            logger.info(f"[{module_name}] {status} ({duration:.1f}s)")
        except Exception as e:
            duration = time.time() - t0
            status = "failure"
            error = str(e)
            logger.error(f"[{module_name}] FAILED: {e}")

            if self.config.get("fallback_allowed", False):
                status = "fallback"
                is_fallback = True
                logger.warning(f"[{module_name}] Fallback allowed, continuing with degraded mode")

        self.state.record_step(
            module=module_name,
            status=status,
            params=kwargs,
            is_fallback=is_fallback,
            error=error,
            duration_seconds=duration,
        )
        return {"status": status, "result": result, "is_fallback": is_fallback, "error": error}

    def finalize(self) -> Path:
        """Save manifest and execution graph."""
        manifest_path = self.state.save_manifest(self.output_dir)
        self.state.save_execution_graph(self.output_dir)
        logger.info(f"Pipeline finalized: manifest at {manifest_path}")
        return manifest_path

    def record_module(self, module_name: str, status: str, reason: str = ""):
        """Record a module that was skipped/unavailable without execution."""
        self.state.record_step(
            module=module_name,
            status=status,
            params={"reason": reason},
            is_fallback=False,
            error=None,
            duration_seconds=0.0,
        )

    def get_summary(self) -> Dict[str, Any]:
        return self.state._summarize()
