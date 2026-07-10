"""QC visualization: violin plots, scatter plots, metric distributions."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
from pathlib import Path
from typing import Optional, Union


def plot_qc_violins(
    adata,
    output_dir: Union[str, Path],
    filename: str = "qc_violins",
) -> Path:
    """Generate QC violin plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    metrics = ["n_genes_by_counts", "total_counts", "pct_counts_mt"]
    titles = ["Genes per cell", "UMI counts per cell", "MT fraction (%)"]
    for ax, metric, title in zip(axes, metrics, titles):
        if metric in adata.obs.columns:
            sc.pl.violin(adata, metric, ax=ax, show=False)
            ax.set_title(title)
    plt.tight_layout()
    path = output_dir / f"{filename}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_qc_comparison(
    before_stats: dict,
    after_stats: dict,
    output_dir: Union[str, Path],
    filename: str = "qc_comparison",
) -> Path:
    """Bar chart comparing before/after QC metrics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    labels = ["Before QC", "After QC"]
    cells = [before_stats.get("cells_before", 0), after_stats.get("cells_after", 0)]
    genes = [before_stats.get("genes_before", 0), after_stats.get("genes_after", 0)]
    axes[0].bar(labels, cells, color=["#94a3b8", "#2563eb"])
    axes[0].set_title("Cells retained")
    axes[0].set_ylabel("Count")
    axes[1].bar(labels, genes, color=["#94a3b8", "#2563eb"])
    axes[1].set_title("Genes retained")
    axes[1].set_ylabel("Count")
    plt.tight_layout()
    path = output_dir / f"{filename}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
