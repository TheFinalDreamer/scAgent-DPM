"""Tests for Drug Perturbation Response Score (DPRS v2)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.perturbation.dprs import (
    compute_dprs,
    compute_dprs_per_drug,
    identify_drug_sensitive_cell_types,
    _normalize_component,
    _determine_status,
    _compute_confidence,
)


def test_normalize_component():
    s = pd.Series([0, 5, 10], index=["a", "b", "c"])
    result = _normalize_component(s, "test")
    assert result["a"] == 0.0
    assert result["c"] == 1.0
    assert 0.4 < result["b"] < 0.6


def test_normalize_component_all_same():
    s = pd.Series([5, 5, 5], index=["a", "b", "c"])
    result = _normalize_component(s, "test")
    assert all(v == 0.5 for v in result.values())


def test_determine_status_valid():
    status, _ = _determine_status(5, {})
    assert status == "valid"


def test_determine_status_partial():
    status, _ = _determine_status(3, {"TS": "unavailable", "CW": "unavailable"})
    assert status == "partial"


def test_determine_status_insufficient():
    status, _ = _determine_status(1, {"PS": "unavailable", "DE": "unavailable", "PA": "unavailable", "TS": "unavailable"})
    assert status == "insufficient_components"


def test_compute_confidence():
    conf = _compute_confidence(5, 5, {"PS": 0.5, "DE": 0.3, "PA": 0.7, "TS": 0.2, "CW": 0.8})
    assert conf > 0.5  # Full components, good spread


def test_compute_dprs_empty():
    dprs_df, meta = compute_dprs()
    assert dprs_df.empty
    assert meta["n_cell_types_scored"] == 0


def test_compute_dprs_with_proportion():
    prop_df = pd.DataFrame({
        "cell_type": ["T cell", "B cell", "Monocyte"],
        "abs_shift": [0.05, 0.12, 0.03],
    })
    dprs_df, meta = compute_dprs(proportion_df=prop_df)
    assert len(dprs_df) == 3
    assert "proportion_shift" in meta["available_components"]
    assert "normalized_score" in dprs_df.columns


def test_compute_dprs_with_confidence_weights():
    prop_df = pd.DataFrame({
        "cell_type": ["T cell", "B cell", "Monocyte"],
        "abs_shift": [0.05, 0.12, 0.03],
    })
    conf_weights = pd.Series([0.8, 0.9, 0.3], index=["T cell", "B cell", "Monocyte"])
    dprs_df, meta = compute_dprs(proportion_df=prop_df, confidence_weights=conf_weights)
    assert len(dprs_df) == 3


def test_identify_drug_sensitive():
    dprs_df = pd.DataFrame({
        "group": [f"CT_{i}" for i in range(10)],
        "drug": ["Drug_A"] * 10,
        "normalized_score": np.linspace(0, 1, 10),
        "status": ["valid"] * 3 + ["partial"] * 4 + ["insufficient_components"] * 3,
    })
    sensitive = identify_drug_sensitive_cell_types(dprs_df, threshold_percentile=70)
    # Only valid/partial rows are considered (7 out of 10)
    assert len(sensitive) > 0
    assert all(sensitive["status"].isin(["valid", "partial"]))


def test_dprs_metadata():
    prop_df = pd.DataFrame({
        "cell_type": ["CT_A", "CT_B"],
        "abs_shift": [0.1, 0.2],
    })
    dprs_df, meta = compute_dprs(proportion_df=prop_df)
    assert meta["n_cell_types_scored"] == 2
    assert "missing_components" in meta


def test_dprs_no_placeholder():
    """Verify missing components are NaN, not 0.0 or 0.5."""
    prop_df = pd.DataFrame({
        "cell_type": ["CT_A"],
        "abs_shift": [0.1],
    })
    dprs_df, meta = compute_dprs(proportion_df=prop_df)
    # Check that unavailable components are NaN, not 0.0
    for comp in ["DE", "PA", "TS", "CW"]:
        if comp in dprs_df.columns:
            val = dprs_df[comp].iloc[0]
            assert np.isnan(val), f"{comp} should be NaN (missing), got {val}"


def test_per_drug_dprs():
    """Test per-drug DPRS mode."""
    deg_df = pd.DataFrame({
        "cell_type": ["CT_A", "CT_A", "CT_B", "CT_B"],
        "drug": ["Drug_X", "Drug_Y", "Drug_X", "Drug_Y"],
        "logfoldchanges": [0.5, -0.3, 1.2, -0.8],
        "pvals_adj": [0.01, 0.02, 0.001, 0.05],
    })
    prop_df = pd.DataFrame({
        "cell_type": ["CT_A", "CT_B"],
        "drug": ["Drug_X", "Drug_Y"],
        "abs_shift": [0.1, 0.2],
    })
    dprs_df, meta = compute_dprs_per_drug(
        deg_df=deg_df, proportion_df=prop_df,
        drug_col="drug", group_col="cell_type",
    )
    assert len(dprs_df) > 0
    assert "drug" in dprs_df.columns
    assert "status" in dprs_df.columns


def test_dprs_status_semantics():
    """Verify status values are correct."""
    dprs_df = pd.DataFrame({
        "group": ["A", "B", "C"],
        "drug": ["D1", "D1", "D1"],
        "normalized_score": [0.9, 0.5, np.nan],
        "status": ["valid", "partial", "insufficient_components"],
    })
    # insufficient should not be in ranking
    sensitive = identify_drug_sensitive_cell_types(dprs_df, threshold_percentile=50)
    assert all(sensitive["status"] != "insufficient_components")
