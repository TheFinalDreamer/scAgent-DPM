"""Perturbation analysis summary report generation."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

import pandas as pd

logger = logging.getLogger("scagent_dpm.perturbation.report")


def generate_perturbation_report(
    dprs_df: pd.DataFrame,
    dprs_metadata: Dict[str, Any],
    proportion_df: pd.DataFrame = None,
    deg_df: pd.DataFrame = None,
    pathway_df: pd.DataFrame = None,
    output_dir: Union[str, Path] = None,
) -> Dict[str, Any]:
    """Generate comprehensive perturbation analysis report."""
    report = {
        "dprs_summary": {
            "n_cell_types_scored": dprs_metadata.get("n_cell_types_scored", 0),
            "available_components": dprs_metadata.get("available_components", []),
            "missing_components": dprs_metadata.get("missing_components", []),
            "top_drug_sensitive_cell_types": dprs_metadata.get("top_drug_sensitive", []),
        },
        "dprs_statistics": {},
        "proportion_shift_summary": {},
        "deg_summary": {},
        "pathway_summary": {},
    }

    if not dprs_df.empty:
        report["dprs_statistics"] = {
            "mean_dprs": round(float(dprs_df["dprs_score"].mean()), 6),
            "median_dprs": round(float(dprs_df["dprs_score"].median()), 6),
            "std_dprs": round(float(dprs_df["dprs_score"].std()), 6),
            "max_dprs": round(float(dprs_df["dprs_score"].max()), 6),
            "min_dprs": round(float(dprs_df["dprs_score"].min()), 6),
            "top_10": dprs_df.head(10)[["cell_type", "dprs_score"]].to_dict("records"),
        }
        if output_dir:
            dprs_df.to_csv(Path(output_dir) / "dprs_scores.csv", index=False)

    if proportion_df is not None and not proportion_df.empty:
        report["proportion_shift_summary"] = {
            "n_cell_types": len(proportion_df),
            "mean_abs_shift": round(float(proportion_df["abs_shift"].mean()), 6),
            "max_shift_cell_type": proportion_df.iloc[0].get("cell_type", "") if not proportion_df.empty else "",
        }
        if output_dir:
            proportion_df.to_csv(Path(output_dir) / "proportion_shift.csv", index=False)

    if deg_df is not None and not deg_df.empty:
        report["deg_summary"] = {
            "n_degs": len(deg_df),
            "n_cell_types_with_degs": deg_df["cell_type"].nunique(),
        }
        if output_dir:
            deg_df.to_csv(Path(output_dir) / "deg_results.csv", index=False)

    if pathway_df is not None and not pathway_df.empty:
        report["pathway_summary"] = {
            "n_enriched_terms": len(pathway_df),
            "n_cell_types": pathway_df["cell_type"].nunique(),
        }
        if output_dir:
            pathway_df.to_csv(Path(output_dir) / "pathway_results.csv", index=False)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "perturbation_summary.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Perturbation report generated")
    return report
