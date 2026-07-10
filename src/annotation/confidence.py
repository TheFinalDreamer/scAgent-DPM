"""Confidence analysis for cell type predictions."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.annotation.confidence")


def analyze_confidence(
    pred_df: pd.DataFrame,
    confidence_col: str = "confidence",
    low_threshold: float = 0.5,
) -> Dict:
    """Analyze prediction confidence distribution."""
    conf = pred_df[confidence_col].values
    low_mask = conf < low_threshold
    return {
        "n_total": len(conf),
        "n_low_confidence": int(low_mask.sum()),
        "low_confidence_ratio": float(low_mask.mean()),
        "mean_confidence": float(np.mean(conf)),
        "median_confidence": float(np.median(conf)),
        "std_confidence": float(np.std(conf)),
        "q25_confidence": float(np.percentile(conf, 25)),
        "q75_confidence": float(np.percentile(conf, 75)),
        "low_confidence_threshold": low_threshold,
    }


def identify_low_confidence_cells(
    pred_df: pd.DataFrame,
    confidence_col: str = "confidence",
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Return subset of cells with low confidence predictions."""
    low = pred_df[pred_df[confidence_col] < threshold].copy()
    logger.info(f"Identified {len(low)} low-confidence cells (threshold={threshold})")
    return low


def compute_confidence_weight(
    pred_df: pd.DataFrame,
    cell_type_col: str = "predicted_cell_type",
    confidence_col: str = "confidence",
) -> pd.Series:
    """Compute per-cell-type average confidence weights for DPRS."""
    weights = pred_df.groupby(cell_type_col)[confidence_col].mean()
    weights = weights / weights.max()
    return weights
