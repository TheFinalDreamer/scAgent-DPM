"""Tests for Agent resume, audit, manifest, and state propagation."""
import sys, os, json, tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent.planner import AgentPlanner
from src.agent.state import PipelineState
from src.perturbation.dprs import compute_dprs

class TestAgentResume:
    def test_agentplanner_plan_generation(self):
        config = {'run_qc': True, 'run_annotation': False, 'run_perturbation': True, 'run_dynamics': False}
        planner = AgentPlanner(config, output_dir=tempfile.mkdtemp())
        plan = planner.plan()
        assert 'modules' in plan
        assert 'data_ingestion' in plan['modules']

    def test_pipeline_state_records_module_status(self):
        state = PipelineState(run_name='test_state')
        state.record_step(module='qc', status='success', params={}, is_fallback=False, error=None, duration_seconds=1.0)
        state.record_step(module='annotation', status='skipped', params={'reason': 'disabled'}, is_fallback=False, error=None, duration_seconds=0.0)
        summary = state._summarize()
        assert summary['success'] == 1
        assert summary['skipped'] == 1

    def test_fallback_flag_recording(self):
        state = PipelineState(run_name='test_fb')
        state.record_step(module='pathway', status='fallback', params={}, is_fallback=True, error='Enrichr down', duration_seconds=2.0)
        summary = state._summarize()
        assert summary['fallback'] == 1
        assert summary['has_fallbacks'] is True

class TestAgentAudit:
    def test_manifest_save_and_load(self):
        state = PipelineState(run_name='test_audit')
        state.record_step(module='qc', status='success', params={}, is_fallback=False, error=None, duration_seconds=1.0)
        tmpdir = tempfile.mkdtemp()
        manifest_path = state.save_manifest(Path(tmpdir))
        assert os.path.exists(manifest_path)
        loaded = json.load(open(manifest_path))
        assert loaded['run_name'] == 'test_audit'

class TestManifestIntegrity:
    def test_execution_graph_saved(self):
        state = PipelineState(run_name='test_graph')
        state.record_step(module='deg', status='success', params={}, is_fallback=False, error=None, duration_seconds=0.5)
        tmpdir = Path(tempfile.mkdtemp())
        state.save_manifest(tmpdir)
        state.save_execution_graph(tmpdir)
        assert (tmpdir / 'execution_graph.json').exists()

class TestStatePropagation:
    def test_sequential_module_status(self):
        state = PipelineState(run_name='test_seq')
        for mod in ['data_ingestion','qc','preprocessing','perturbation','dprs','reporting']:
            state.record_step(module=mod, status='success', params={}, is_fallback=False, error=None, duration_seconds=0.5)
        summary = state._summarize()
        assert summary['success'] == 6

    def test_mixed_status_scenario(self):
        state = PipelineState(run_name='test_mixed')
        steps = [('data_ingestion','success'),('qc','success'),('annotation','skipped'),('perturbation','success'),('dynamics','skipped'),('dprs','success')]
        for mod, st in steps:
            state.record_step(module=mod, status=st, params={}, is_fallback=False, error=None, duration_seconds=0.1)
        summary = state._summarize()
        assert summary['success'] == 4
        assert summary['skipped'] == 2

    def test_failure_propagation(self):
        state = PipelineState(run_name='test_fail')
        state.record_step(module='perturbation', status='failure', params={}, is_fallback=False, error='DEG error', duration_seconds=10.0)
        state.record_step(module='dprs', status='success', params={}, is_fallback=False, error=None, duration_seconds=0.1)
        summary = state._summarize()
        assert summary['failure'] == 1

class TestResourceAvailability:
    def test_annotation_skipped(self):
        state = PipelineState(run_name='test_skip')
        state.record_step(module='annotation', status='skipped', params={'reason':'disabled'}, is_fallback=False, error=None, duration_seconds=0.0)
        assert state._summarize()['skipped'] == 1

    def test_dprs_partial_tracking(self):
        dprs_df, meta = compute_dprs()
        assert dprs_df.empty
        assert 'missing_components' in meta
        assert len(meta['missing_components']) == 5

    def test_dynamics_skipped_independent(self):
        state = PipelineState(run_name='test_dyn')
        state.record_step(module='dynamics', status='skipped', params={'reason':'disabled'}, is_fallback=False, error=None, duration_seconds=0.0)
        state.record_step(module='dprs', status='success', params={}, is_fallback=False, error=None, duration_seconds=0.1)
        summary = state._summarize()
        assert summary['skipped'] == 1
        assert summary['success'] == 1
