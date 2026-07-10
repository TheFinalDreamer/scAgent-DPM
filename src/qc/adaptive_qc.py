"""Adaptive quality control with parameter search and multi-objective scoring."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anndata as ann
import numpy as np
import pandas as pd
import scanpy as sc

from .qc_metrics import compute_qc_metrics

logger = logging.getLogger("scagent_dpm.qc.adaptive")


def run_fixed_qc(
    adata: ann.AnnData,
    min_genes: int = 200,
    min_cells: int = 3,
    max_mt_pct: float = 20.0,
    organism: str = "human",
) -> Tuple[ann.AnnData, Dict[str, Any]]:
    """Run fixed-threshold QC filtering."""
    adata = adata.copy()
    compute_qc_metrics(adata, organism)
    n_before = adata.n_obs
    g_before = adata.n_vars

    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)
    if "pct_counts_mt" in adata.obs.columns:
        adata = adata[adata.obs["pct_counts_mt"] < max_mt_pct, :].copy()

    stats = {
        "method": "fixed_qc",
        "cells_before": n_before,
        "cells_after": adata.n_obs,
        "genes_before": g_before,
        "genes_after": adata.n_vars,
        "retained_cell_ratio": adata.n_obs / n_before if n_before > 0 else 0,
        "retained_gene_ratio": adata.n_vars / g_before if g_before > 0 else 0,
        "params": {"min_genes": min_genes, "min_cells": min_cells, "max_mt_pct": max_mt_pct},
    }
    logger.info(f"Fixed QC: {n_before} -> {adata.n_obs} cells, {g_before} -> {adata.n_vars} genes")
    return adata, stats


def run_adaptive_qc(
    adata: ann.AnnData,
    organism: str = "human",
    search_iterations: int = 50,
    metric_weights: Optional[Dict[str, float]] = None,
) -> Tuple[ann.AnnData, Dict[str, Any]]:
    """Run adaptive QC with parameter search.

    Searches over min_genes, max_mt_pct parameter space to optimize
    a composite score balancing cell/gene retention and quality.
    """
    if metric_weights is None:
        metric_weights = {
            "retained_cell_ratio": 0.25,
            "retained_gene_ratio": 0.20,
            "mt_ratio_control": 0.15,
            "n_genes_by_counts_min": 0.15,
            "total_counts_min": 0.10,
            "doublet_removal": 0.15,
        }

    adata = adata.copy()
    compute_qc_metrics(adata, organism)
    n_before = adata.n_obs
    g_before = adata.n_vars

    rng = np.random.default_rng(42)
    best_score = -np.inf
    best_params = {}
    best_stats = {}

    param_space = _build_param_space(adata)
    search_history = []

    for iteration in range(search_iterations):
        params = _sample_params(param_space, rng)
        filtered, result = _apply_qc_params(adata, params)
        score = _compute_qc_score(result, metric_weights, adata.n_obs, adata.n_vars)
        result["score"] = score
        result["iteration"] = iteration
        search_history.append(result)

        if score > best_score:
            best_score = score
            best_params = params
            best_stats = result

    # Apply best params
    adata_filtered, _ = _apply_qc_params(adata, best_params)

    best_stats["method"] = "adaptive_qc"
    best_stats["search_iterations"] = search_iterations
    best_stats["search_history"] = search_history
    best_stats["param_space_bounds"] = param_space
    best_stats["metric_weights"] = metric_weights
    best_stats["score"] = best_score

    logger.info(
        f"Adaptive QC: {n_before} -> {adata_filtered.n_obs} cells, "
        f"{g_before} -> {adata_filtered.n_vars} genes, "
        f"best_score={best_score:.4f}, params={best_params}"
    )
    return adata_filtered, best_stats


def _build_param_space(adata: ann.AnnData) -> Dict[str, List[float]]:
    """Build parameter search bounds from data statistics."""
    if "n_genes_by_counts" not in adata.obs.columns:
        compute_qc_metrics(adata)
    n_genes = adata.obs["n_genes_by_counts"]
    mt_pct = adata.obs.get("pct_counts_mt", pd.Series([0]))

    q01_genes = max(50, int(np.percentile(n_genes, 1)))
    q50_genes = int(np.percentile(n_genes, 50))
    q99_mt = float(np.percentile(mt_pct, 99))

    return {
        "min_genes": [q01_genes, q50_genes],
        "max_mt_pct": [5.0, min(50.0, q99_mt + 5)],
    }


def _sample_params(param_space: Dict[str, List[float]], rng: np.random.Generator) -> Dict[str, float]:
    params = {}
    for key, bounds in param_space.items():
        if isinstance(bounds[0], int):
            params[key] = int(rng.integers(max(1, bounds[0]), bounds[1] + 1))
        else:
            params[key] = float(rng.uniform(bounds[0], bounds[1]))
    return params


def _apply_qc_params(
    adata: ann.AnnData, params: Dict[str, float]
) -> Tuple[ann.AnnData, Dict[str, Any]]:
    """Apply QC parameters and return filtered AnnData + stats."""
    adata_f = adata.copy()
    nc_before, ng_before = adata_f.n_obs, adata_f.n_vars

    if "min_genes" in params:
        sc.pp.filter_cells(adata_f, min_genes=int(params["min_genes"]))
    sc.pp.filter_genes(adata_f, min_cells=3)

    if "max_mt_pct" in params and "pct_counts_mt" in adata_f.obs.columns:
        adata_f = adata_f[adata_f.obs["pct_counts_mt"] < params["max_mt_pct"], :].copy()

    mt_after = adata_f.obs["pct_counts_mt"].mean() if "pct_counts_mt" in adata_f.obs.columns else 0

    return adata_f, {
        "cells_before": nc_before,
        "cells_after": adata_f.n_obs,
        "genes_before": ng_before,
        "genes_after": adata_f.n_vars,
        "retained_cell_ratio": adata_f.n_obs / nc_before if nc_before > 0 else 0,
        "retained_gene_ratio": adata_f.n_vars / ng_before if ng_before > 0 else 0,
        "mt_ratio_after": float(mt_after),
        "params": {k: (int(v) if isinstance(v, (np.integer, int)) else float(v)) for k, v in params.items()},
    }


def _compute_qc_score(
    stats: Dict[str, Any],
    weights: Dict[str, float],
    n_cells_orig: int,
    n_genes_orig: int,
) -> float:
    """Compute composite QC quality score."""
    score = 0.0
    if "retained_cell_ratio" in weights:
        score += weights["retained_cell_ratio"] * stats.get("retained_cell_ratio", 0)
    if "retained_gene_ratio" in weights:
        score += weights["retained_gene_ratio"] * stats.get("retained_gene_ratio", 0)
    if "mt_ratio_control" in weights:
        mt = stats.get("mt_ratio_after", 0)
        score += weights["mt_ratio_control"] * max(0, 1 - mt / 20)
    return score


def run_qc_pipeline(
    adata: ann.AnnData,
    config: Dict[str, Any],
) -> Tuple[ann.AnnData, Dict[str, Any]]:
    """Run full QC pipeline based on config."""
    qc_cfg = config.get("qc", {})
    organism = config.get("organism", "human")

    if qc_cfg.get("adaptive", True):
        adata_qc, stats = run_adaptive_qc(
            adata,
            organism=organism,
            search_iterations=qc_cfg.get("search_iterations", 50),
            metric_weights=qc_cfg.get("metric_weights"),
        )
    else:
        adata_qc, stats = run_fixed_qc(adata, organism=organism)

    return adata_qc, stats
