"""Tests for quality control modules."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.loaders import load_data
from src.qc.qc_metrics import compute_qc_metrics
from src.qc.adaptive_qc import run_fixed_qc, run_adaptive_qc


def test_compute_qc_metrics():
    adata = load_data(input_path=None)
    metrics_df = compute_qc_metrics(adata)
    assert "n_genes_by_counts" in metrics_df.columns
    assert "total_counts" in metrics_df.columns
    assert "pct_counts_mt" in metrics_df.columns
    assert len(metrics_df) == adata.n_obs


def test_fixed_qc():
    adata = load_data(input_path=None)
    adata_qc, stats = run_fixed_qc(adata, min_genes=200, max_mt_pct=20)
    assert adata_qc.n_obs <= adata.n_obs
    assert adata_qc.n_vars <= adata.n_vars
    assert stats["method"] == "fixed_qc"
    assert "retained_cell_ratio" in stats


def test_adaptive_qc():
    adata = load_data(input_path=None)
    adata_qc, stats = run_adaptive_qc(adata, search_iterations=5)
    assert adata_qc.n_obs <= adata.n_obs
    assert stats["method"] == "adaptive_qc"
    assert "score" in stats
    assert len(stats["search_history"]) == 5
