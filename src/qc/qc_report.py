"""QC report generation: summary JSON and visual summaries."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

logger = logging.getLogger("scagent_dpm.qc.report")


def generate_qc_report(
    qc_stats: Dict[str, Any],
    output_dir: Union[str, Path],
    qc_baselines: list = None,
) -> Path:
    """Generate QC summary report as JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "qc_method": qc_stats.get("method", "unknown"),
        "cells_before": qc_stats.get("cells_before"),
        "cells_after": qc_stats.get("cells_after"),
        "genes_before": qc_stats.get("genes_before"),
        "genes_after": qc_stats.get("genes_after"),
        "retained_cell_ratio": qc_stats.get("retained_cell_ratio"),
        "retained_gene_ratio": qc_stats.get("retained_gene_ratio"),
        "mt_ratio_after": qc_stats.get("mt_ratio_after"),
        "params": qc_stats.get("params", {}),
        "score": qc_stats.get("score"),
    }

    if qc_baselines:
        report["baseline_comparison"] = qc_baselines

    report_path = output_dir / "qc_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"QC report saved to {report_path}")
    return report_path
