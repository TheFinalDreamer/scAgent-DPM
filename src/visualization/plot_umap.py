"""UMAP visualization for cell types and conditions."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scanpy as sc
from pathlib import Path
from typing import Optional, Union


def plot_umap_cell_types(
    adata,
    cell_type_key: str = "predicted_cell_type",
    output_dir: Union[str, Path] = None,
    filename: str = "umap_cell_types",
) -> "plt.Figure":
    """Plot UMAP colored by predicted cell type."""
    if "X_umap" not in adata.obsm:
        sc.tl.umap(adata)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc.pl.umap(adata, color=cell_type_key, ax=ax, show=False, legend_loc="right margin",
               title="UMAP by predicted cell type")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_umap_condition(
    adata,
    condition_key: str = "condition",
    output_dir: Union[str, Path] = None,
    filename: str = "umap_condition",
) -> "plt.Figure":
    """Plot UMAP colored by condition (control vs treated)."""
    if "X_umap" not in adata.obsm:
        sc.tl.umap(adata)
    fig, ax = plt.subplots(figsize=(10, 8))
    sc.pl.umap(adata, color=condition_key, ax=ax, show=False, legend_loc="right margin",
               title="UMAP by condition")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig
