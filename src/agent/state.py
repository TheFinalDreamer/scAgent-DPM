"""Pipeline state tracking and run manifest management."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PipelineState:
    """Tracks the state of each pipeline module execution."""

    def __init__(self, run_name: str = None):
        self.run_name = run_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now().isoformat()
        self.steps: List[Dict[str, Any]] = []
        self._step_idx = 0

    def record_step(
        self,
        module: str,
        status: str,
        input_files: Optional[List[str]] = None,
        output_files: Optional[List[str]] = None,
        params: Optional[Dict[str, Any]] = None,
        is_fallback: bool = False,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        entry = {
            "step_index": self._step_idx,
            "module": module,
            "status": status,  # success | failure | fallback | skipped
            "is_fallback": is_fallback,
            "timestamp": datetime.now().isoformat(),
            "input_files": input_files or [],
            "output_files": output_files or [],
            "params": params or {},
            "error": error,
            "duration_seconds": round(duration_seconds, 2) if duration_seconds else None,
        }
        self.steps.append(entry)
        self._step_idx += 1

    def to_manifest(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "run_name": self.run_name,
            "start_time": self.start_time,
            "end_time": datetime.now().isoformat(),
            "total_steps": len(self.steps),
            "steps": self.steps,
            "config_snapshot": config,
            "status_summary": self._summarize(),
        }

    def _summarize(self) -> Dict[str, int]:
        summary = {"success": 0, "failure": 0, "fallback": 0, "skipped": 0}
        for step in self.steps:
            status = step["status"]
            if status in summary:
                summary[status] += 1
        summary["has_fallbacks"] = summary["fallback"] > 0
        summary["has_failures"] = summary["failure"] > 0
        return summary

    def save_manifest(self, output_dir: str) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.to_manifest()
        path = output_dir / "run_manifest.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False, default=str)
        return path

    def save_execution_graph(self, output_dir: str) -> Path:
        """Save execution DAG as JSON."""
        graph = {
            "run_name": self.run_name,
            "nodes": [],
            "edges": [],
        }
        module_deps = {
            "data_ingestion": [],
            "qc": ["data_ingestion"],
            "preprocessing": ["qc"],
            "annotation": ["preprocessing"],
            "perturbation": ["annotation"],
            "dynamics": ["annotation"],
            "dprs": ["perturbation", "dynamics"],
            "reporting": ["dprs"],
        }
        for step in self.steps:
            mod = step["module"]
            graph["nodes"].append({
                "id": f"{mod}_{step['step_index']}",
                "module": mod,
                "status": step["status"],
                "is_fallback": step["is_fallback"],
            })
        for mod, deps in module_deps.items():
            for dep in deps:
                graph["edges"].append({"from": dep, "to": mod})
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "execution_graph.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)
        return path
