"""Cell-type proportion shift analysis between control and treated conditions."""

import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

logger = logging.getLogger("scagent_dpm.perturbation.proportion")


def compute_proportion_shift(
    adata,
    condition_key: str = "condition",
    cell_type_key: str = "cell_type",
    control_label: str = "control",
    treated_label: str = "treated",
    min_cells_per_type: int = 20,
) -> pd.DataFrame:
    """Compute cell-type proportion differences between conditions.

    Returns DataFrame with proportion shift metrics per cell type.
    """
    obs = adata.obs
    ct_table = pd.crosstab(obs[cell_type_key], obs[condition_key])
    ct_table = ct_table[[control_label, treated_label]]

    total_ctrl = ct_table[control_label].sum()
    total_treated = ct_table[treated_label].sum()

    results = []
    for ct in ct_table.index:
        n_ctrl = ct_table.loc[ct, control_label]
        n_treated = ct_table.loc[ct, treated_label]

        if n_ctrl + n_treated < min_cells_per_type:
            continue

        prop_ctrl = n_ctrl / total_ctrl if total_ctrl > 0 else 0
        prop_treated = n_treated / total_treated if total_treated > 0 else 0
        shift = prop_treated - prop_ctrl
        fold_change = prop_treated / prop_ctrl if prop_ctrl > 0 else np.inf

        chi2, p_value = _chi2_test_for_cell_type(ct_table, ct, total_ctrl, total_treated)

        results.append({
            "cell_type": ct,
            "n_control": n_ctrl,
            "n_treated": n_treated,
            "prop_control": round(prop_ctrl, 6),
            "prop_treated": round(prop_treated, 6),
            "proportion_shift": round(shift, 6),
            "fold_change": round(fold_change, 4) if np.isfinite(fold_change) else float("inf"),
            "chi2_statistic": round(chi2, 4),
            "p_value": round(p_value, 6),
        })

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df["abs_shift"] = result_df["proportion_shift"].abs()
        result_df = result_df.sort_values("abs_shift", ascending=False)

    logger.info(f"Proportion shift computed for {len(result_df)} cell types")
    return result_df


def _chi2_test_for_cell_type(
    ct_table: pd.DataFrame, ct: str, total_ctrl: int, total_treated: int
) -> Tuple[float, float]:
    """Chi-squared test for a single cell type proportion difference."""
    n_ctrl = ct_table.loc[ct, ct_table.columns[0]]
    n_treated = ct_table.loc[ct, ct_table.columns[1]]
    other_ctrl = total_ctrl - n_ctrl
    other_treated = total_treated - n_treated
    table = np.array([[n_ctrl, n_treated], [other_ctrl, other_treated]])
    try:
        chi2, p, _, _ = chi2_contingency(table)
        return float(chi2), float(p)
    except ValueError:
        return 0.0, 1.0
