"""Cell-type proportion shift visualization."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Union


def plot_proportion_shift(
    proportion_df: pd.DataFrame,
    output_dir: Union[str, Path] = None,
    filename: str = "proportion_shift",
    top_n: int = 15,
) -> "plt.Figure":
    """Horizontal bar chart of cell-type proportion shifts."""
    if proportion_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No proportion shift data available", ha="center", va="center")
        return fig

    df = proportion_df.head(top_n).copy()
    df = df.sort_values("abs_shift")

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#ef4444" if s < 0 else "#22c55e" for s in df["proportion_shift"]]
    ax.barh(range(len(df)), df["abs_shift"], color=colors, alpha=0.8)

    labels = []
    for _, row in df.iterrows():
        direction = "+" if row["proportion_shift"] >= 0 else "-"
        labels.append(f"{row['cell_type']} ({direction})")
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Absolute Proportion Shift")
    ax.set_title("Cell-type Proportion Shift (Control vs Treated)")
    ax.axvline(x=0, color="black", linewidth=0.5)
    plt.tight_layout()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_proportion_comparison(
    proportion_df: pd.DataFrame,
    output_dir: Union[str, Path] = None,
    filename: str = "proportion_comparison",
    top_n: int = 10,
) -> "plt.Figure":
    """Grouped bar chart comparing control vs treated proportions."""
    if proportion_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No data", ha="center")
        return fig

    df = proportion_df.head(top_n)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df))
    width = 0.35
    ax.bar(x - width/2, df["prop_control"], width, label="Control", color="#94a3b8", alpha=0.8)
    ax.bar(x + width/2, df["prop_treated"], width, label="Treated", color="#2563eb", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(df["cell_type"], rotation=45, ha="right")
    ax.set_ylabel("Proportion")
    ax.set_title("Cell-type Proportions: Control vs Treated")
    ax.legend()
    plt.tight_layout()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig
