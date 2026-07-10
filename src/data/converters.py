"""Format converters for scRNA-seq data."""

from pathlib import Path
from typing import Optional, Union

import anndata as ann
import pandas as pd


def anndata_to_csv(adata: ann.AnnData, output_path: Union[str, Path], layer: Optional[str] = None) -> None:
    """Export AnnData expression matrix to CSV."""
    if layer is not None:
        expr = pd.DataFrame(adata.layers[layer].toarray() if hasattr(adata.layers[layer], "toarray")
                           else adata.layers[layer],
                           index=adata.obs_names, columns=adata.var_names)
    else:
        expr = pd.DataFrame(adata.X.toarray() if hasattr(adata.X, "toarray") else adata.X,
                           index=adata.obs_names, columns=adata.var_names)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    expr.to_csv(output_path)


def obs_to_csv(adata: ann.AnnData, output_path: Union[str, Path], columns: Optional[list] = None) -> None:
    """Export AnnData obs to CSV."""
    df = adata.obs[columns] if columns else adata.obs
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path)
