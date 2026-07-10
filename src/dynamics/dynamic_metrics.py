"""Evaluation metrics for dynamic state modeling."""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

logger = logging.getLogger("scagent_dpm.dynamics.metrics")


def evaluate_trajectory_shift(
    shift_df: pd.DataFrame,
    perturbation_labels: pd.Series = None,
) -> Dict:
    """Evaluate trajectory shift predictions against perturbation labels."""
    metrics = {
        "n_cell_types": len(shift_df),
    }
    if "abs_shift" in shift_df.columns:
        metrics.update({
            "mean_abs_shift": float(shift_df["abs_shift"].mean()),
            "max_abs_shift": float(shift_df["abs_shift"].max()),
            "cell_type_max_shift": shift_df.loc[shift_df["abs_shift"].idxmax(), "cell_type"]
            if not shift_df.empty else "",
        })
    return metrics


def rank_stability(
    score_1: pd.Series,
    score_2: pd.Series,
    label: str = "",
) -> Dict:
    """Compute Spearman rank correlation between two scores."""
    common_idx = score_1.index.intersection(score_2.index)
    if len(common_idx) < 3:
        return {"spearman_r": None, "p_value": None, "n_common": len(common_idx)}
    r, p = spearmanr(score_1[common_idx], score_2[common_idx])
    return {"spearman_r": round(r, 4), "p_value": round(p, 4), "n_common": len(common_idx), "label": label}
