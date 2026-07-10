"""Input validation and data field checking for scAgent-DPM."""

import logging
from typing import Any, Dict, List

import anndata as ann

logger = logging.getLogger("scagent_dpm.agent.validators")


def validate_anndata_for_pipeline(
    adata: ann.AnnData,
    required_keys: List[str] = None,
) -> Dict[str, Any]:
    """Validate that an AnnData object meets pipeline requirements."""
    if required_keys is None:
        required_keys = ["condition"]

    report = {
        "valid": True,
        "n_cells": adata.n_obs,
        "n_genes": adata.n_vars,
        "issues": [],
        "warnings": [],
    }

    if adata.n_obs < 50:
        report["issues"].append(f"Very few cells ({adata.n_obs}). Pipeline may not work correctly.")

    if adata.n_vars < 100:
        report["issues"].append(f"Very few genes ({adata.n_vars}).")

    for key in required_keys:
        if key not in adata.obs.columns:
            report["warnings"].append(f"Required obs key '{key}' not found.")
            report["valid"] = False

    # Check for raw counts
    if adata.raw is None:
        report["warnings"].append("No .raw attribute — raw counts may be missing.")

    # Check for condition groups
    if "condition" in adata.obs.columns:
        groups = adata.obs["condition"].value_counts()
        if len(groups) < 2:
            report["warnings"].append(
                f"Only {len(groups)} condition group(s) found. Need at least 2 for perturbation analysis."
            )
        for group, count in groups.items():
            if count < 10:
                report["warnings"].append(f"Condition '{group}' has only {count} cells.")

    if report["issues"]:
        logger.warning(f"Validation found {len(report['issues'])} issues")
    if report["warnings"]:
        logger.warning(f"Validation found {len(report['warnings'])} warnings")

    return report


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pipeline configuration completeness."""
    issues = []
    checks = {
        "condition_key": "Missing condition_key",
        "control_label": "Missing control_label",
        "treated_label": "Missing treated_label",
    }
    for key, msg in checks.items():
        if not config.get(key):
            issues.append(msg)

    if config.get("run_annotation") and not config.get("cell_type_key"):
        issues.append("run_annotation=True but cell_type_key not set")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "config_loaded": bool(config),
    }
