"""Pseudotime trajectory analysis using scanpy."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ann
import numpy as np
import pandas as pd
import scanpy as sc

logger = logging.getLogger("scagent_dpm.dynamics.pseudotime")


def run_pseudotime(
    adata: ann.AnnData,
    method: str = "scanpy_dpt",
    root_cell_prior: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Compute pseudotime ordering for cells.

    Returns pseudotime values per cell and analysis summary.
    """
    adata = adata.copy()

    if "X_pca" not in adata.obsm:
        sc.pp.scale(adata, max_value=10)
        sc.tl.pca(adata, n_comps=50, svd_solver="arpack")

    if "neighbors" not in adata.uns:
        sc.pp.neighbors(adata, n_neighbors=15)

    sc.tl.diffmap(adata)
    sc.tl.dpt(adata)

    pseudotime_df = pd.DataFrame({
        "cell_barcode": adata.obs_names,
        "dpt_pseudotime": adata.obs["dpt_pseudotime"].values,
    })

    if "cell_type" in adata.obs.columns:
        pseudotime_df["cell_type"] = adata.obs["cell_type"].values

    summary = {
        "method": method,
        "n_cells": adata.n_obs,
        "mean_pseudotime": float(adata.obs["dpt_pseudotime"].mean()),
        "median_pseudotime": float(adata.obs["dpt_pseudotime"].median()),
        "std_pseudotime": float(adata.obs["dpt_pseudotime"].std()),
    }

    logger.info(f"Pseudotime computed: mean={summary['mean_pseudotime']:.3f}")
    return pseudotime_df, summary
