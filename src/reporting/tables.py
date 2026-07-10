"""Table formatting utilities for reports."""

import pandas as pd
from pathlib import Path
from typing import Optional, Union


def format_metrics_table(metrics: dict, title: str = "Metrics") -> pd.DataFrame:
    """Convert metrics dict to a formatted DataFrame."""
    rows = []
    for key, value in metrics.items():
        if isinstance(value, float):
            value = round(value, 4)
        rows.append({"Metric": key, "Value": value})
    return pd.DataFrame(rows)


def format_comparison_table(results: list, columns: list = None) -> pd.DataFrame:
    """Format a list of result dicts as comparison table."""
    df = pd.DataFrame(results)
    if columns:
        df = df[columns]
    return df


def save_table(df: pd.DataFrame, filename: str, output_dir: Union[str, Path]) -> Path:
    """Save DataFrame as CSV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{filename}.csv"
    df.to_csv(path, index=False)
    return path
