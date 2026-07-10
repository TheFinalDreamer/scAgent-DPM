"""Build sequential representations of cell state trajectories."""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("scagent_dpm.dynamics.sequence")


def build_state_sequence(
    expression_matrix: np.ndarray,
    pseudotime: np.ndarray,
    cell_types: Optional[np.ndarray] = None,
    n_bins: int = 100,
) -> Tuple[np.ndarray, np.ndarray]:
    """Bin cells by pseudotime and build expression sequence.

    Returns:
        sequence: (n_bins, n_genes) binned expression matrix
        bin_edges: pseudotime bin boundaries
    """
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    sequence = np.zeros((n_bins, expression_matrix.shape[1]))
    bin_counts = np.zeros(n_bins)

    for i in range(n_bins):
        mask = (pseudotime >= bins[i]) & (pseudotime < bins[i + 1])
        if mask.sum() > 0:
            sequence[i] = expression_matrix[mask].mean(axis=0)
            bin_counts[i] = mask.sum()
        elif i > 0:
            sequence[i] = sequence[i - 1]

    scaler = StandardScaler()
    sequence = scaler.fit_transform(sequence.T).T

    logger.info(f"Built state sequence: {n_bins} bins, {expression_matrix.shape[1]} features")
    return sequence, bin_centers


def build_condition_sequences(
    adata,
    pseudotime_df: pd.DataFrame,
    condition_key: str = "condition",
    n_bins: int = 100,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Build separate sequences for control and treated conditions."""
    conditions = pseudotime_df.index.map(
        lambda c: adata.obs.loc[c, condition_key] if c in adata.obs_names else "unknown"
    )
    pseudotime_df["condition"] = conditions

    sequences = {}
    for cond in pseudotime_df["condition"].unique():
        subset = pseudotime_df[pseudotime_df["condition"] == cond]
        if len(subset) < 10:
            continue
        idx = subset.index
        expr = adata[idx].X.toarray() if hasattr(adata[idx].X, "toarray") else adata[idx].X
        pt = subset["dpt_pseudotime"].values
        pt_norm = (pt - pt.min()) / (pt.max() - pt.min() + 1e-8)
        seq, _ = build_state_sequence(expr, pt_norm, n_bins=n_bins)
        sequences[cond] = seq

    return sequences
