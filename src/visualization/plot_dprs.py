"""DPRS visualization."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Union


def plot_dprs_ranking(
    dprs_df: pd.DataFrame,
    output_dir: Union[str, Path] = None,
    filename: str = "dprs_ranking",
    top_n: int = 20,
) -> "plt.Figure":
    """Horizontal bar chart of DPRS rankings."""
    if dprs_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No DPRS data available", ha="center", va="center")
        return fig

    df = dprs_df.head(top_n).sort_values("dprs_score")

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.3)))
    cmap = plt.cm.RdYlGn
    norm = plt.Normalize(df["dprs_score"].min(), df["dprs_score"].max())
    colors = cmap(norm(df["dprs_score"].values))

    ax.barh(range(len(df)), df["dprs_score"], color=colors, edgecolor="#333", linewidth=0.5)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["cell_type"])
    ax.set_xlabel("DPRS Score")
    ax.set_title("Drug Perturbation Response Score (DPRS) Ranking")

    for i, score in enumerate(df["dprs_score"]):
        ax.text(score + 0.01, i, f"{score:.3f}", va="center", fontsize=8)

    plt.tight_layout()
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_dprs_components(
    dprs_df: pd.DataFrame,
    output_dir: Union[str, Path] = None,
    filename: str = "dprs_components",
    top_n: int = 10,
) -> "plt.Figure":
    """Stacked bar chart showing DPRS component contributions."""
    if dprs_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data", ha="center")
        return fig

    df = dprs_df.head(top_n).set_index("cell_type")
    component_cols = [c for c in df.columns if c.endswith("_component")]
    if not component_cols:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No component breakdown available", ha="center")
        return fig

    fig, ax = plt.subplots(figsize=(12, 6))
    df[component_cols].plot(kind="barh", stacked=True, ax=ax, colormap="Set2", edgecolor="#333", linewidth=0.3)
    ax.set_xlabel("Component Contribution")
    ax.set_title("DPRS Component Breakdown")
    ax.legend(loc="lower right", fontsize=7)
    plt.tight_layout()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig
