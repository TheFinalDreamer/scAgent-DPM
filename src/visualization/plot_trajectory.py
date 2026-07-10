"""Trajectory and pseudotime visualization."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Union


def plot_pseudotime_distribution(
    pseudotime_df: pd.DataFrame,
    condition_key: str = "condition",
    output_dir: Union[str, Path] = None,
    filename: str = "pseudotime_distribution",
) -> "plt.Figure":
    """Overlaid density plots of pseudotime by condition."""
    fig, ax = plt.subplots(figsize=(10, 5))

    for cond in pseudotime_df[condition_key].unique():
        subset = pseudotime_df[pseudotime_df[condition_key] == cond]
        if "dpt_pseudotime" in subset.columns:
            subset["dpt_pseudotime"].hist(
                bins=50, alpha=0.5, label=cond, density=True, ax=ax,
            )

    ax.set_xlabel("Pseudotime")
    ax.set_ylabel("Density")
    ax.set_title("Pseudotime Distribution by Condition")
    ax.legend()
    plt.tight_layout()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_trajectory_shift(
    shift_df: pd.DataFrame,
    output_dir: Union[str, Path] = None,
    filename: str = "trajectory_shift",
) -> "plt.Figure":
    """Bar chart of trajectory shifts per cell type."""
    if shift_df.empty or "trajectory_shift" not in shift_df.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No trajectory shift data available", ha="center", va="center")
        return fig

    df = shift_df.sort_values("abs_shift" if "abs_shift" in shift_df.columns else "trajectory_shift")

    fig, ax = plt.subplots(figsize=(10, max(5, len(df) * 0.3)))
    colors = ["#2563eb" if s >= 0 else "#ef4444" for s in df["trajectory_shift"]]
    ax.barh(range(len(df)), df["trajectory_shift"], color=colors, alpha=0.8)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["cell_type"])
    ax.set_xlabel("Trajectory Shift")
    ax.set_title("Trajectory Shift by Cell Type (Treated - Control)")
    ax.axvline(x=0, color="black", linewidth=0.5)
    plt.tight_layout()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    return fig
