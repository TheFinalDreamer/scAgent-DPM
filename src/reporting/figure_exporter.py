"""Figure export utilities for scAgent-DPM."""

import logging
from pathlib import Path
from typing import Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger("scagent_dpm.reporting.figure")


def save_figure(
    fig: plt.Figure,
    filename: Union[str, Path],
    output_dir: Union[str, Path],
    formats: list = None,
    dpi: int = 300,
    bbox_inches: str = "tight",
) -> list:
    """Save a matplotlib figure in multiple formats."""
    if formats is None:
        formats = ["png", "pdf"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    for fmt in formats:
        path = output_dir / f"{filename}.{fmt}"
        fig.savefig(path, dpi=dpi, bbox_inches=bbox_inches, format=fmt)
        saved_paths.append(str(path))
    plt.close(fig)
    return saved_paths


def figure_to_base64(fig: plt.Figure) -> str:
    """Convert figure to base64 for HTML embedding."""
    import base64
    from io import BytesIO
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
