"""Tests for data loading and inspection."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.loaders import load_data, inspect_data, generate_data_report
from src.data.preprocessing import preprocess


def test_generate_synthetic_data():
    adata = load_data(input_path=None)
    assert adata.n_obs == 1000
    assert adata.n_vars == 2000
    assert "condition" in adata.obs.columns
    assert "cell_type" in adata.obs.columns
    assert "control" in adata.obs["condition"].values
    assert "treated" in adata.obs["condition"].values


def test_inspect_data():
    adata = load_data(input_path=None)
    summary = inspect_data(adata)
    assert summary["n_cells"] == 1000
    assert summary["n_genes"] == 2000
    assert summary["has_condition_key"] is True
    assert summary["has_cell_type_key"] is True


def test_preprocessing():
    adata = load_data(input_path=None)
    adata_pp = preprocess(adata, n_top_genes=500, n_pcs=20, run_umap=False)
    assert adata_pp.n_vars <= 500
    assert "X_pca" in adata_pp.obsm
