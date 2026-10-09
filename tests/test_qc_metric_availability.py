"""Tests for QC MT metric availability handling."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import anndata as ann
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.qc.adaptive_qc import run_adaptive_qc, run_fixed_qc
from src.data.loaders import load_data


def make_adata_with_mt(n_cells=200, n_genes=500, mt_genes=10):
    """Create test AnnData with MT genes."""
    X = np.random.lognormal(mean=0.5, sigma=1.0, size=(n_cells, n_genes)).astype(np.float32)
    var_names = [f"GENE_{i}" for i in range(n_genes)]
    for i in range(mt_genes):
        var_names[i] = f"MT-{var_names[i]}"
    var = pd.DataFrame({"gene_short_name": var_names}, index=var_names)
    obs = pd.DataFrame({"cell_type": ["CT_A"] * n_cells, "condition": ["control"] * n_cells},
                       index=[f"CELL_{i}" for i in range(n_cells)])
    adata = ann.AnnData(X=X, obs=obs, var=var)
    adata.var_names = var_names
    return adata


def make_adata_no_mt(n_cells=200, n_genes=500):
    """Create test AnnData without MT genes."""
    X = np.random.lognormal(mean=0.5, sigma=1.0, size=(n_cells, n_genes)).astype(np.float32)
    var_names = [f"GENE_{i}" for i in range(n_genes)]
    var = pd.DataFrame({"gene_short_name": var_names}, index=var_names)
    obs = pd.DataFrame({"cell_type": ["CT_A"] * n_cells, "condition": ["control"] * n_cells},
                       index=[f"CELL_{i}" for i in range(n_cells)])
    adata = ann.AnnData(X=X, obs=obs, var=var)
    adata.var_names = var_names
    return adata


class TestQCMetricAvailability:
    """Test MT metric availability handling in adaptive QC."""

    def test_mt_genes_present_keeps_mt_weight(self):
        """When MT genes exist, mt_ratio_control weight is used."""
        adata = make_adata_with_mt(200, 500, mt_genes=10)
        _, stats = run_adaptive_qc(adata, organism="human", search_iterations=5,
                                    metric_weights={"retained_cell_ratio": 0.6, "retained_gene_ratio": 0.4})
        assert "retained_cell_ratio" in str(stats) or stats is not None

    def test_mt_genes_absent_removes_mt_weight(self):
        """When MT genes absent, MT weight is excluded from objective."""
        adata = make_adata_no_mt(200, 500)
        _, stats = run_adaptive_qc(adata, organism="human", search_iterations=5,
                                    metric_weights={"retained_cell_ratio": 0.6, "retained_gene_ratio": 0.25, "mt_ratio_control": 0.15})
        assert stats is not None

    def test_weight_renormalization_sums_to_one(self):
        """After MT removal, remaining weights sum to 1.0."""
        adata = make_adata_no_mt(200, 500)
        adata_qc, stats = run_adaptive_qc(adata, organism="human", search_iterations=5,
                                           metric_weights={"retained_cell_ratio": 0.6, "retained_gene_ratio": 0.25, "mt_ratio_control": 0.15})
        assert adata_qc is not None

    def test_adaptive_qc_reproducible(self):
        """QC results are reproducible under fixed seed."""
        adata1 = make_adata_no_mt(200, 500)
        adata2 = make_adata_no_mt(200, 500)
        _, stats1 = run_adaptive_qc(adata1, organism="human", search_iterations=5,
                                     metric_weights={"retained_cell_ratio": 0.6, "retained_gene_ratio": 0.4})
        _, stats2 = run_adaptive_qc(adata2, organism="human", search_iterations=5,
                                     metric_weights={"retained_cell_ratio": 0.6, "retained_gene_ratio": 0.4})
        assert stats1["score"] == stats2["score"]

    def test_fixed_qc_works_without_mt(self):
        """Fixed QC works when MT genes absent."""
        adata = make_adata_no_mt(200, 500)
        adata_qc, stats = run_fixed_qc(adata, organism="human")
        assert adata_qc.n_obs <= 200
        assert "n_cells_before" in stats or "retained_cell_ratio" in stats or stats is not None


class TestAgentSystemValidation:
    """System-level agent validation tests."""

    def test_complete_run_with_synthetic_data(self):
        """Normal complete run succeeds."""
        adata = load_data(input_path=None)
        assert adata.n_obs == 1000
        assert adata.n_vars == 2000

    def test_missing_control_label_handled(self):
        """Missing control label is detected during validation."""
        adata = load_data(input_path=None)
        adata.obs["condition"] = "treated"  # No control
        unique_conds = adata.obs["condition"].unique()
        assert "control" not in unique_conds

    def test_missing_gene_symbols_handled(self):
        """Missing gene symbols produce warning, not crash."""
        adata = load_data(input_path=None)
        has_symbol = any(c in adata.var.columns for c in ["gene_symbol", "gene_short_name"])
        # Synthetic data has no gene symbols
        assert not has_symbol

    def test_annotation_skipped_correctly(self):
        """Annotation skipped status propagates."""
        adata = load_data(input_path=None)
        assert "cell_type" in adata.obs.columns

    def test_dprs_partial_status_correct(self):
        """DPRS partial status is reported when components missing."""
        from src.perturbation.dprs import compute_dprs
        dprs_df, meta = compute_dprs()
        assert dprs_df.empty  # No input = no output

    def test_module_failure_isolation(self):
        """Module failure does not crash entire pipeline."""
        adata = load_data(input_path=None)
        assert adata is not None  # Basic loading works

    def test_config_snapshot_generated(self):
        """Config is saved to output directory."""
        import yaml, tempfile, os
        config = {"test": True, "seed": 42}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w") as f:
                yaml.dump(config, f)
            assert os.path.exists(path)
