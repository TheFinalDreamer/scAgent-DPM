"""Input data validator for scAgent-DPM pipeline.

Validates h5ad files against pipeline requirements before execution.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.data.validator")


def validate_h5ad(
    input_path: str,
    config: Optional[Dict[str, Any]] = None,
    min_cells: int = 10,
    min_genes: int = 5,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Validate an h5ad file for pipeline compatibility.

    Returns (passed, report, issues).
    """
    import anndata as ad

    report = {}
    issues = []
    path = Path(input_path)

    # 1. File existence
    if not path.exists():
        issues.append(f"File not found: {input_path}")
        return False, {"error": "file_not_found"}, issues

    report["file_path"] = str(path.absolute())
    report["file_size_mb"] = round(path.stat().st_size / (1024 * 1024), 2)

    # 2. Readability
    try:
        adata = ad.read_h5ad(input_path)
    except Exception as e:
        issues.append(f"Cannot read h5ad: {e}")
        return False, {"error": "read_failed", "detail": str(e)}, issues

    # 3. Shape
    report["shape"] = list(adata.shape)
    report["n_cells"] = adata.n_obs
    report["n_genes"] = adata.n_vars
    if adata.n_obs < min_cells:
        issues.append(f"Too few cells: {adata.n_obs} < {min_cells}")
    if adata.n_vars < min_genes:
        issues.append(f"Too few genes: {adata.n_vars} < {min_genes}")

    # 4. X matrix
    report["x_type"] = type(adata.X).__name__
    report["x_sparse"] = hasattr(adata.X, 'tocoo')
    report["x_has_nan"] = bool(np.isnan(adata.X.data).any()) if hasattr(adata.X, 'data') else False
    report["x_has_inf"] = bool(np.isinf(adata.X.data).any()) if hasattr(adata.X, 'data') else False
    if report["x_has_nan"]:
        issues.append("X contains NaN values")
    if report["x_has_inf"]:
        issues.append("X contains Inf values")

    # 5. Raw
    report["has_raw"] = adata.raw is not None
    if adata.raw is not None:
        report["raw_shape"] = list(adata.raw.shape)

    # 6. Layers
    report["layers"] = list(adata.layers.keys()) if adata.layers else []

    # 7. Obs
    report["obs_columns"] = list(adata.obs.columns)
    report["n_obs_columns"] = len(adata.obs.columns)

    # 8. Var
    report["var_columns"] = list(adata.var.columns)
    report["n_var_columns"] = len(adata.var.columns)

    # 9. Duplicates
    dup_obs = adata.obs_names.duplicated().sum()
    dup_var = adata.var_names.duplicated().sum()
    report["duplicate_obs_names"] = int(dup_obs)
    report["duplicate_var_names"] = int(dup_var)
    if dup_obs > 0:
        issues.append(f"{dup_obs} duplicate observation names")
    if dup_var > 0:
        issues.append(f"{dup_var} duplicate variable names")

    # 10. Gene symbol detection
    symbol_cols = ["gene_short_name", "gene_symbol", "symbol", "gene_name", "hgnc_symbol"]
    gsn_found = [c for c in symbol_cols if c in adata.var.columns]
    report["gene_symbol_columns_found"] = gsn_found
    if gsn_found:
        report["gene_symbol_source"] = gsn_found[0]
    else:
        issues.append("No gene symbol column found in var")

    # 11. MT gene detection
    mt_detected = 0
    mt_source = None
    for col in gsn_found:
        mt_mask = adata.var[col].astype(str).str.startswith('MT-')
        n = mt_mask.sum()
        if n > 0:
            mt_detected = int(n)
            mt_source = f"var:{col}"
            break
    report["mt_genes_detected"] = mt_detected
    report["mt_gene_source"] = mt_source
    if mt_detected == 0:
        issues.append("No MT genes detected")

    # 12. Condition/group key validation
    if config:
        _validate_config_keys(adata, config, report, issues)

    # 13. Group-level statistics
    if config and "cell_type_key" in config:
        ctk = config["cell_type_key"]
        if ctk in adata.obs.columns:
            report["n_groups"] = int(adata.obs[ctk].nunique())
            report["group_counts"] = adata.obs[ctk].value_counts().to_dict()

    # 14. Cell counts per condition
    if config and "condition_key" in config:
        ck = config["condition_key"]
        if ck in adata.obs.columns:
            report["condition_counts"] = adata.obs[ck].value_counts().to_dict()

    # 15. Empty groups
    empty_groups = []
    if config:
        ctk = config.get("cell_type_key", "cell_type")
        ck = config.get("condition_key", "condition")
        if ctk in adata.obs.columns and ck in adata.obs.columns:
            for group in adata.obs[ctk].unique():
                for cond in adata.obs[ck].unique():
                    n = ((adata.obs[ctk] == group) & (adata.obs[ck] == cond)).sum()
                    if n == 0:
                        empty_groups.append(f"{group}/{cond}")
    report["empty_groups"] = empty_groups
    if empty_groups:
        issues.append(f"{len(empty_groups)} empty (group, condition) combinations")

    # Overall
    passed = len(issues) == 0
    status = "passed" if passed else "failed"
    report["validation_status"] = status
    report["n_issues"] = len(issues)

    return passed, report, issues


def _validate_config_keys(adata, config, report, issues):
    """Check config keys against actual data columns."""
    for key_name, config_key in [
        ("condition_key", config.get("condition_key")),
        ("cell_type_key", config.get("cell_type_key")),
        ("batch_key", config.get("batch_key")),
        ("perturbation.drug_column", config.get("perturbation", {}).get("drug_column")),
    ]:
        if config_key and config_key not in adata.obs.columns:
            issues.append(f"Config {key_name}='{config_key}' not found in obs columns")


def save_validation_report(report, issues, output_dir):
    """Save validation report as JSON and Markdown."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    with open(output_dir / "data_validation_report.json", "w") as f:
        json.dump({"report": report, "issues": issues}, f, indent=2, default=str)

    # Markdown
    md = ["# Data Validation Report", ""]
    md.append(f"**Status**: {report.get('validation_status', 'unknown').upper()}")
    md.append(f"**Issues**: {len(issues)}")
    md.append("")
    md.append("## Summary")
    md.append(f"- Shape: {report.get('shape', 'N/A')}")
    md.append(f"- X type: {report.get('x_type', 'N/A')}")
    md.append(f"- Raw: {report.get('has_raw', 'N/A')}")
    md.append(f"- MT genes: {report.get('mt_genes_detected', 0)}")
    md.append(f"- Gene symbols: {report.get('gene_symbol_columns_found', [])}")
    md.append(f"- Duplicate obs: {report.get('duplicate_obs_names', 0)}")
    md.append(f"- Duplicate var: {report.get('duplicate_var_names', 0)}")

    if issues:
        md.append("")
        md.append("## Issues")
        for i, issue in enumerate(issues, 1):
            md.append(f"{i}. {issue}")

    with open(output_dir / "data_validation_report.md", "w") as f:
        f.write("\n".join(md))

    logger.info(f"Validation report saved to {output_dir}")
