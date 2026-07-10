"""CellTypist annotation runner."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ann
import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.annotation.celltypist")


def run_celltypist(
    adata: ann.AnnData,
    model_name: str = "Immune_All_Low.pkl",
    majority_voting: bool = True,
    organism: str = "human",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run CellTypist annotation.

    If CellTypist is not installed or model is unavailable, falls back to
    mock predictions. All fallback runs are clearly labeled.
    """
    try:
        import celltypist
    except ImportError:
        logger.warning("CellTypist not installed — using MOCK/FALLBACK predictions")
        return _mock_annotation(adata, method="celltypist")

    try:
        predictions = celltypist.annotate(
            adata, model=model_name, majority_voting=majority_voting,
        )
        pred_df = predictions.predicted_labels
        is_fallback = False
    except Exception as e:
        logger.warning(f"CellTypist failed: {e} — using MOCK/FALLBACK predictions")
        pred_df, _ = _mock_annotation(adata, method="celltypist")
        is_fallback = True

    summary = {
        "method": "celltypist",
        "model": model_name,
        "n_cells_annotated": len(pred_df),
        "is_fallback": is_fallback,
        "fallback_warning": "Results are MOCK predictions — not for publication." if is_fallback else "",
    }
    return pred_df, summary


def _mock_annotation(
    adata: ann.AnnData, method: str = "unknown"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate mock cell type predictions for interface testing."""
    rng = np.random.default_rng(42)
    mock_types = ["T cell", "B cell", "Monocyte", "NK cell", "Dendritic cell"]
    preds = rng.choice(mock_types, size=adata.n_obs)
    conf = rng.uniform(0.3, 1.0, size=adata.n_obs)
    df = pd.DataFrame({
        "predicted_cell_type": preds,
        "confidence": conf,
    }, index=adata.obs_names)
    summary = {
        "method": method,
        "is_fallback": True,
        "fallback_warning": "MOCK predictions — interface test only, NOT for publication.",
    }
    logger.warning("MOCK ANNOTATION generated — tag as FALLBACK in all outputs.")
    return df, summary
