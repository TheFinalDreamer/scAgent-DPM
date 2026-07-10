"""Data ingestion layer: load scRNA-seq from multiple formats into AnnData."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import anndata as ann
import numpy as np
import pandas as pd
import scanpy as sc

logger = logging.getLogger("scagent_dpm.data.loaders")


def load_data(
    input_path: Optional[Union[str, Path]] = None,
    mtx_dir: Optional[str] = None,
    csv_path: Optional[str] = None,
) -> ann.AnnData:
    """Load scRNA-seq data. If input_path is None, generates synthetic demo data."""
    if input_path is not None:
        path = Path(input_path)
        suffix = path.suffix.lower()
        if suffix in {".h5ad", ".h5"}:
            adata = sc.read_h5ad(path)
        elif suffix == ".loom":
            adata = sc.read_loom(path)
        else:
            raise ValueError(f"Unsupported format: {suffix}")
    elif mtx_dir is not None:
        adata = sc.read_10x_mtx(mtx_dir, var_names="gene_symbols", cache=True)
    elif csv_path is not None:
        expr = pd.read_csv(csv_path, index_col=0)
        adata = ann.AnnData(expr.T)
    else:
        adata = _generate_synthetic_data()
    return adata


def _generate_synthetic_data(
    n_cells: int = 1000,
    n_genes: int = 2000,
    n_cell_types: int = 5,
    seed: int = 42,
) -> ann.AnnData:
    """Generate synthetic AnnData for demo/testing purposes.

    This data is NOT suitable for reporting as real experimental results.
    All outputs from synthetic data must be tagged as DEMO/FALLBACK.
    """
    rng = np.random.default_rng(seed)
    X = rng.lognormal(mean=1.0, sigma=1.0, size=(n_cells, n_genes))
    X = np.round(X).astype(np.float32)
    X[X < 0] = 0

    cell_types = [f"CellType_{i}" for i in range(n_cell_types)]
    ct_labels = rng.choice(cell_types, size=n_cells)
    ct_labels_half = n_cells // 2
    conditions = np.array(["control"] * ct_labels_half + ["treated"] * (n_cells - ct_labels_half))
    rng.shuffle(conditions)

    gene_names = [f"GENE_{i}" for i in range(n_genes)]
    mt_indices = rng.choice(n_genes, size=min(30, n_genes), replace=False)
    for idx in mt_indices[:13]:
        gene_names[idx] = f"MT-{gene_names[idx]}"

    adata = ann.AnnData(X)
    adata.obs_names = [f"Cell_{i}" for i in range(n_cells)]
    adata.var_names = gene_names
    adata.obs["cell_type"] = ct_labels
    adata.obs["condition"] = conditions
    adata.obs["batch"] = "batch_1"
    adata.raw = adata.copy()

    logger.warning(
        "SYNTHETIC DATA GENERATED — results from this data are for DEMO/FALLBACK only, "
        "not for publication."
    )
    return adata


def inspect_data(adata: ann.AnnData) -> Dict[str, Any]:
    """Generate a data summary JSON for downstream consumers."""
    summary = {
        "n_cells": adata.n_obs,
        "n_genes": adata.n_vars,
        "has_raw": adata.raw is not None,
        "obs_columns": list(adata.obs.columns),
        "var_columns": list(adata.var.columns) if adata.var.shape[1] > 0 else [],
        "has_condition_key": "condition" in adata.obs.columns,
        "has_batch_key": "batch" in adata.obs.columns,
        "has_cell_type_key": "cell_type" in adata.obs.columns,
        "sparse": str(type(adata.X)),
    }

    if "condition" in adata.obs.columns:
        vc = adata.obs["condition"].value_counts()
        summary["condition_counts"] = vc.to_dict()

    if "cell_type" in adata.obs.columns:
        summary["n_cell_types"] = adata.obs["cell_type"].nunique()

    mt_prefixes = ["MT-", "mt-"]
    mt_genes = []
    for prefix in mt_prefixes:
        mt_genes.extend([g for g in adata.var_names if g.startswith(prefix)])

    # Fallback: search adata.var columns for MT gene symbols (e.g., when var_names are Ensembl IDs)
    if not mt_genes:
        search_cols = ["gene_short_name", "gene_symbol", "symbol", "gene_name", "hgnc_symbol"]
        import re
        for col in search_cols:
            if col not in adata.var.columns:
                continue
            mt_regex = re.compile(r"^MT-[A-Z]")
            mt_mask = adata.var[col].astype(str).str.match(mt_regex).fillna(False)
            mt_count = mt_mask.sum()
            if mt_count > 0:
                mt_genes = adata.var_names[mt_mask].tolist()
                summary["mt_gene_source"] = f"var:{col}"
                break

    summary["mt_genes_detected"] = len(mt_genes)
    summary["mt_gene_prefix_found"] = summary.get("mt_gene_source", (
        "MT-" if any(str(g).startswith("MT-") for g in mt_genes) else (
            "mt-" if any(str(g).startswith("mt-") for g in mt_genes) else "none"
        )
    ))

    return summary


def generate_data_report(adata: ann.AnnData, output_path: Union[str, Path]) -> None:
    """Write data inspection report to JSON."""
    summary = inspect_data(adata)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
