"""Trajectory shift analysis between conditions."""

import logging
from typing import Dict

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance

logger = logging.getLogger("scagent_dpm.dynamics.trajectory_shift")


def compute_trajectory_shift_metrics(
    ctrl_pseudotime: np.ndarray,
    treated_pseudotime: np.ndarray,
    n_bins: int = 50,
) -> Dict[str, float]:
    """Compute quantitative trajectory shift metrics between conditions.

    Returns dict with wasserstein_distance, kl_divergence, earth_mover_distance,
    mean_shift, and ks_statistic.
    """
    ctrl_hist, bins = np.histogram(ctrl_pseudotime, bins=n_bins, density=True)
    treated_hist, _ = np.histogram(treated_pseudotime, bins=bins, density=True)
    eps = 1e-10
    ctrl_hist = ctrl_hist + eps
    treated_hist = treated_hist + eps
    ctrl_hist = ctrl_hist / ctrl_hist.sum()
    treated_hist = treated_hist / treated_hist.sum()

    try:
        w_dist = wasserstein_distance(ctrl_pseudotime, treated_pseudotime)
    except Exception:
        w_dist = float("nan")

    try:
        js_div = jensenshannon(ctrl_hist, treated_hist) ** 2
    except Exception:
        js_div = float("nan")

    try:
        emd = wasserstein_distance(ctrl_hist, treated_hist)
    except Exception:
        emd = float("nan")

    mean_shift = float(treated_pseudotime.mean() - ctrl_pseudotime.mean())

    return {
        "wasserstein_distance": round(w_dist, 6) if not np.isnan(w_dist) else None,
        "js_divergence": round(js_div, 6) if not np.isnan(js_div) else None,
        "earth_mover_distance": round(emd, 6) if not np.isnan(emd) else None,
        "mean_shift": round(mean_shift, 6),
        "ctrl_mean": round(float(ctrl_pseudotime.mean()), 6),
        "treated_mean": round(float(treated_pseudotime.mean()), 6),
    }
