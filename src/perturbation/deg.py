"""Differential expression analysis for drug perturbation data."""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

try:
    import scanpy as sc
    _SCANPY_AVAILABLE = True
except Exception:
    _SCANPY_AVAILABLE = False

logger = logging.getLogger("scagent_dpm.perturbation.deg")


def run_deg_per_cell_type(
    adata,
    condition_key: str = "condition",
    cell_type_key: str = "cell_type",
    control_label: str = "control",
    treated_label: str = None,
    method: str = "wilcoxon",
    min_log_fc: float = 0.25,
    pval_threshold: float = 0.05,
    min_cells_per_group: int = 10,
    drug_col: str = "drug",
) -> pd.DataFrame:
    """Run DEG analysis per cell type, optionally per drug.

    In per-drug mode: for each drug x cell_type, compares drug-treated vs control within same cell_type.
    In single-mode (treated_label provided): compares treated vs control globally per cell_type.

    Uses log-normalized data (caller must ensure adata.X is log-normalized).
    """
    if not _SCANPY_AVAILABLE:
        logger.warning("scanpy not available — returning empty DEG results")
        return _empty_deg_df()

    all_results = []
    cell_types = adata.obs[cell_type_key].unique()

    # Determine if per-drug mode is active
    per_drug = treated_label is None and drug_col in adata.obs.columns
    if per_drug:
        drug_labels = sorted(adata.obs[drug_col].unique())
        drug_labels = [d for d in drug_labels if d != control_label]
        logger.info(f"Per-drug DEG mode: {len(drug_labels)} drugs, {len(cell_types)} cell types")
    else:
        drug_labels = [treated_label] if treated_label else ["treated"]
        logger.info(f"Single-mode DEG: {len(cell_types)} cell types")

    for ct in cell_types:
        ct_mask = adata.obs[cell_type_key] == ct
        ctrl_mask = ct_mask & (adata.obs[condition_key] == control_label)
        ctrl_cells = ctrl_mask.sum()

        if ctrl_cells < min_cells_per_group:
            logger.info(f"Skipping {ct}: insufficient control cells ({ctrl_cells})")
            continue

        for drug in drug_labels:
            if per_drug:
                treated_mask = ct_mask & (adata.obs[drug_col] == drug)
            else:
                treated_mask = ct_mask & (adata.obs[condition_key] == drug)
            treated_cells = treated_mask.sum()

            if treated_cells < min_cells_per_group:
                logger.info(f"Skipping {ct}/{drug}: insufficient treated cells ({treated_cells})")
                continue

            subset_mask = ctrl_mask | treated_mask
            subset = adata[subset_mask].copy()
            sub_ctrl_count = (subset.obs[condition_key] == control_label).sum()
            sub_treated_count = (~(subset.obs[condition_key] == control_label)).sum()

            try:
                sc.tl.rank_genes_groups(
                    subset, groupby=condition_key, reference=control_label,
                    method=method, key_added=f"deg_{ct}_{drug}",
                )
                # Find the non-control group label
                non_ctrl_labels = [l for l in subset.obs[condition_key].unique() if l != control_label]
                if non_ctrl_labels:
                    result = sc.get.rank_genes_groups_df(subset, group=non_ctrl_labels[0], key=f"deg_{ct}_{drug}")
                    result["cell_type"] = ct
                    result["drug"] = drug
                    result["n_ctrl"] = sub_ctrl_count
                    result["n_treated"] = sub_treated_count
                    all_results.append(result)
            except Exception as e:
                logger.warning(f"DEG failed for {ct}/{drug}: {e}")
                continue

    if not all_results:
        return _empty_deg_df()

    deg_df = pd.concat(all_results, ignore_index=True)

    # Add gene_id from var_names (raw gene IDs)
    deg_df["gene_id"] = deg_df["names"]

    # Add gene_symbol from adata.var metadata
    deg_df = _add_gene_symbols(deg_df, adata)

    # Determine direction
    deg_df["direction"] = deg_df["logfoldchanges"].apply(
        lambda x: "up" if x > 0 else "down" if x < 0 else "ns"
    )

    # Filter by significance
    sig_mask = (deg_df["pvals_adj"] < pval_threshold) & (deg_df["logfoldchanges"].abs() > min_log_fc)
    deg_df["significant"] = sig_mask

    deg_df = deg_df.sort_values(["cell_type", "drug", "pvals_adj"])

    logger.info(
        f"DEG complete: {len(deg_df)} significant DEGs across "
        f"{deg_df['cell_type'].nunique()} cell types, {deg_df['drug'].nunique()} drugs"
    )
    return deg_df


def compute_deg_intensity(deg_df: pd.DataFrame, cell_type: str) -> float:
    """Compute DEG intensity score for a given cell type.

    DEG intensity = mean(|logFC|) * (-log10(mean(padj))) for DEGs in this cell type.
    """
    subset = deg_df[deg_df["cell_type"] == cell_type]
    if subset.empty:
        return 0.0
    mean_abs_lfc = subset["logfoldchanges"].abs().mean()
    mean_padj = max(subset["pvals_adj"].mean(), 1e-300)
    neg_log_padj = -np.log10(mean_padj)
    return float(mean_abs_lfc * neg_log_padj)


def _add_gene_symbols(deg_df: pd.DataFrame, adata) -> pd.DataFrame:
    """Map gene IDs in 'names' column to gene symbols using adata.var metadata."""
    if deg_df.empty or "names" not in deg_df.columns:
        return deg_df

    symbol_cols = ["gene_short_name", "gene_symbol", "symbol", "gene_name", "hgnc_symbol"]
    available = [c for c in symbol_cols if c in adata.var.columns]
    if not available:
        logger.warning("No gene symbol column found in adata.var — DEG output will use gene IDs only")
        deg_df["gene_symbol"] = deg_df["names"]
        return deg_df

    symbol_col = available[0]
    symbol_map = adata.var[symbol_col].to_dict()
    deg_df["gene_symbol"] = deg_df["names"].map(symbol_map).fillna(deg_df["names"])
    logger.info(f"Gene symbols mapped from var.{symbol_col}: "
                f"{(deg_df['gene_symbol'] != deg_df['names']).sum()}/{len(deg_df)} genes resolved")
    return deg_df


def _empty_deg_df() -> pd.DataFrame:
    return pd.DataFrame(columns=["names", "scores", "logfoldchanges", "pvals", "pvals_adj",
                                  "cell_type", "gene_symbol"])
