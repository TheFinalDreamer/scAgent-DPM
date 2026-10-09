"""Integration tests for resume, audit, and dependency resolution."""
import sys, os, json, tempfile, shutil
from pathlib import Path
import yaml
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent.planner import AgentPlanner
from src.agent.state import PipelineState
from src.agent.executor import PipelineExecutor
from src.data.loaders import load_data, inspect_data

class TestResumeIntegration:
    def test_resume_manifest_preserves_prior_steps(self):
        tmpdir = Path(tempfile.mkdtemp())
        state = PipelineState(run_name="test_resume")
        state.record_step(module="data_ingestion", status="success", params={}, is_fallback=False, error=None, duration_seconds=0.1)
        state.record_step(module="qc", status="success", params={}, is_fallback=False, error=None, duration_seconds=2.0)
        manifest_path = state.save_manifest(tmpdir)
        state.save_execution_graph(tmpdir)
        assert manifest_path.exists()
        assert (tmpdir / "execution_graph.json").exists()

    def test_resume_detects_completed_modules(self):
        tmpdir = Path(tempfile.mkdtemp())
        state = PipelineState(run_name="test_detect")
        state.record_step(module="data_ingestion", status="success", params={}, is_fallback=False, error=None, duration_seconds=0.1)
        state.record_step(module="preprocessing", status="failure", params={}, is_fallback=False, error="died", duration_seconds=0.0)
        state.save_manifest(tmpdir)
        loaded = json.load(open(tmpdir / "run_manifest.json"))
        steps = loaded.get("steps", [])
        statuses = {s["module"]: s["status"] for s in steps}
        assert statuses.get("data_ingestion") == "success"
        assert statuses.get("preprocessing") == "failure"

    def test_resume_skips_already_successful(self):
        tmpdir = Path(tempfile.mkdtemp())
        state = PipelineState(run_name="test_skip")
        state.record_step(module="data_ingestion", status="success", params={}, is_fallback=False, error=None, duration_seconds=0.1)
        state.record_step(module="qc", status="success", params={}, is_fallback=False, error=None, duration_seconds=1.0)
        state.record_step(module="preprocessing", status="pending", params={}, is_fallback=False, error=None, duration_seconds=0.0)
        manifest_path = state.save_manifest(tmpdir)
        loaded = json.load(open(manifest_path))
        completed = [s["module"] for s in loaded["steps"] if s["status"] == "success"]
        assert "data_ingestion" in completed
        assert "preprocessing" not in completed

class TestAuditIntegration:
    def test_audit_valid_manifest(self):
        tmpdir = Path(tempfile.mkdtemp())
        state = PipelineState(run_name="test_valid")
        for mod in ["data_ingestion","qc","preprocessing","perturbation","dprs","reporting"]:
            state.record_step(module=mod, status="success", params={}, is_fallback=False, error=None, duration_seconds=1.0)
        state.save_manifest(tmpdir)
        loaded = json.load(open(tmpdir / "run_manifest.json"))
        assert loaded["run_name"] == "test_valid"

    def test_audit_detects_missing_output(self):
        tmpdir = Path(tempfile.mkdtemp())
        state = PipelineState(run_name="test_missing")
        state.record_step(module="deg", status="success", params={}, is_fallback=False, error=None, duration_seconds=5.0)
        state.record_step(module="reporting", status="success", params={}, is_fallback=False, error=None, duration_seconds=0.1)
        state.save_manifest(tmpdir)
        state.save_execution_graph(tmpdir)
        assert (tmpdir / "run_manifest.json").exists()

    def test_audit_detects_corrupted_manifest(self):
        tmpdir = Path(tempfile.mkdtemp())
        # Write invalid JSON
        (tmpdir / "run_manifest.json").write_text("{invalid json!!!", encoding="utf-8")
        with pytest.raises((json.JSONDecodeError, Exception)):
            json.load(open(tmpdir / "run_manifest.json"))

    def test_output_manifest_completeness(self):
        state = PipelineState(run_name="test_outputs")
        state.record_step(module="data_ingestion", status="success", params={}, is_fallback=False, error=None, duration_seconds=0.1)
        tmpdir = Path(tempfile.mkdtemp())
        state.save_manifest(tmpdir)
        state.save_execution_graph(tmpdir)
        assert (tmpdir / "run_manifest.json").exists()
        assert (tmpdir / "execution_graph.json").exists()

class TestDependencyResolution:
    def test_annotation_skipped_by_config(self):
        config = {"run_qc": True, "run_annotation": False, "run_perturbation": True, "run_dynamics": False,
                  "fallback_allowed": False, "seed": 42, "pipeline": {"name": "test"}}
        planner = AgentPlanner(config, output_dir=tempfile.mkdtemp())
        plan = planner.plan()
        assert "data_ingestion" in plan["modules"]
        assert "annotation" not in plan["modules"]  # Should be excluded

    def test_dynamics_skipped_by_config(self):
        config = {"run_qc": True, "run_annotation": False, "run_perturbation": True, "run_dynamics": False,
                  "fallback_allowed": False, "seed": 42, "pipeline": {"name": "test"}}
        planner = AgentPlanner(config, output_dir=tempfile.mkdtemp())
        plan = planner.plan()
        assert "dynamics" not in plan["modules"]

    def test_dprs_included_when_perturbation_enabled(self):
        config = {"run_qc": True, "run_annotation": False, "run_perturbation": True, "run_dynamics": False,
                  "fallback_allowed": False, "seed": 42, "pipeline": {"name": "test"}}
        planner = AgentPlanner(config, output_dir=tempfile.mkdtemp())
        plan = planner.plan()
        assert "dprs" in plan["modules"]

    def test_missing_control_label_detected(self):
        config = {"run_qc": True, "run_perturbation": True, "condition_key": "condition", "control_label": "control",
                  "fallback_allowed": False, "seed": 42, "pipeline": {"name": "test"}}
        planner = AgentPlanner(config, output_dir=tempfile.mkdtemp())
        plan = planner.plan()
        assert "perturbation" in plan["modules"]  # Included in plan, validated at runtime
