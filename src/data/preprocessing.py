"""Standard preprocessing pipeline: normalization, log-transform, HVG selection, PCA."""

import logging
from typing import Optional

import anndata as ann
import numpy as np
import scanpy as sc

logger = logging.getLogger("scagent_dpm.data.preprocessing")


def preprocess(
    adata: ann.AnnData,
    target_sum: float = 1e4,
    n_top_genes: int = 2000,
    n_pcs: int = 50,
    n_neighbors: int = 15,
    batch_key: Optional[str] = None,
    run_pca: bool = True,
    run_neighbors: bool = True,
    run_umap: bool = True,
) -> ann.AnnData:
    """Standard preprocessing pipeline on a copy of the AnnData object."""
    adata = adata.copy()

    # Detect if input is already log-normalized (max expr < 20, non-integer values)
    import numpy as _np
    if hasattr(adata.X, 'data'):
        _d = _np.asarray(adata.X.data).flatten()
    else:
        _d = _np.asarray(adata.X.toarray()).flatten()
    _is_log_norm = (_d.max() < 20) and (_np.mean(_np.abs(_d - _np.round(_d)) < 1e-6) < 0.1)
    
    if _is_log_norm:
        logger.info("Input appears log-normalized (max=%.2f, integer-fraction=%.4f). Skipping normalize_total+log1p." % (_d.max(), _np.mean(_np.abs(_d - _np.round(_d)) < 1e-6)))
        if adata.raw is None:
            adata.raw = adata.copy()  # preserve log-normalized full-gene matrix
    else:
        if adata.raw is None:
            adata.raw = adata.copy()  # preserve raw counts
        sc.pp.normalize_total(adata, target_sum=target_sum)
        sc.pp.log1p(adata)
        logger.info(f"Applied normalize_total({target_sum}) + log1p to raw counts")
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, batch_key=batch_key)
    adata = adata[:, adata.var.highly_variable].copy()

    if run_pca:
        sc.pp.scale(adata, max_value=10)
        sc.tl.pca(adata, n_comps=n_pcs, svd_solver="arpack")

    if run_neighbors:
        sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)

    if run_umap:
        sc.tl.umap(adata)

    logger.info(f"Preprocessing complete: {adata.n_obs} cells x {adata.n_vars} genes")
    return adata
