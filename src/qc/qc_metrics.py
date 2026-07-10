"""QC metric computation for scRNA-seq data."""

import logging
import re
from typing import Dict, List, Optional, Tuple

import anndata as ann
import numpy as np
import pandas as pd
import scanpy as sc

logger = logging.getLogger("scagent_dpm.qc.metrics")

# Columns to search for MT gene symbols when var_names are not gene symbols
_MT_SEARCH_COLUMNS = ["gene_short_name", "gene_symbol", "symbol", "gene_name", "hgnc_symbol"]


def _detect_mt_genes(adata: ann.AnnData, organism: str = "human") -> Tuple[List[str], str]:
    """Detect mitochondrial genes with fallback to adata.var columns.

    Returns (list_of_mt_gene_ids_or_indices, detection_source).
    """
    mt_prefix = "MT-" if organism == "human" else "mt-"

    # Stage 1: check var_names directly (works for gene symbol data)
    mt_genes = [g for g in adata.var_names if g.startswith(mt_prefix)]
    if mt_genes:
        logger.info(f"MT genes detected from var_names: {len(mt_genes)} genes (prefix '{mt_prefix}')")
        return mt_genes, f"var_names:{mt_prefix}"

    # Stage 2: search adata.var metadata columns for MT gene symbols
    for col in _MT_SEARCH_COLUMNS:
        if col not in adata.var.columns:
            continue
        values = adata.var[col]
        mt_regex = re.compile(r"^MT-[A-Z]") if organism == "human" else re.compile(r"^mt-[a-z]")
        mt_mask = values.astype(str).str.match(mt_regex).fillna(False)
        mt_count = mt_mask.sum()
        if mt_count > 0:
            mt_indices = adata.var_names[mt_mask].tolist()
            mt_symbols = values[mt_mask].tolist()
            logger.info(f"MT genes detected from var.{col}: {mt_count} genes (e.g., {mt_symbols[:5]})")
            return mt_indices, f"var:{col}"

    logger.warning(f"MT genes not detected: var_names do not start with '{mt_prefix}' and no var column "
                   f"({_MT_SEARCH_COLUMNS}) contains MT gene symbols. pct_counts_mt will be 0.")
    return [], "none"


def compute_qc_metrics(
    adata: ann.AnnData,
    organism: str = "human",
) -> pd.DataFrame:
    """Compute standard QC metrics and add to adata.obs.

    Returns a DataFrame with per-cell QC metrics.
    """
    mt_genes, mt_source = _detect_mt_genes(adata, organism)

    if mt_genes:
        adata.var["_mt"] = adata.var_names.isin(mt_genes)
        sc.pp.calculate_qc_metrics(adata, qc_vars=["_mt"], percent_top=None, log1p=False, inplace=True)
        adata.obs.rename(columns={"pct_counts__mt": "pct_counts_mt"}, inplace=True)
        del adata.var["_mt"]
    else:
        sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
        adata.obs["pct_counts_mt"] = 0.0

    adata.uns["mt_gene_source"] = mt_source
    adata.uns["mt_genes_detected"] = len(mt_genes)
    logger.info(f"QC metrics computed: mt_source={mt_source}, mt_genes={len(mt_genes)}, "
                f"mean_mt_pct={adata.obs['pct_counts_mt'].mean():.2f}%")

    return adata.obs[["n_genes_by_counts", "total_counts", "pct_counts_mt"]]
