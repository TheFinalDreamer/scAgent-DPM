"""Minimal fault-injection audit for scAgent-DPM manuscript revision.

The script uses the sci-Plex4 A549 analysis input and canonical output manifest
as read-only sources. It writes only audit artifacts under final_audit/robustness.
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

import scanpy as sc


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agent.validators import validate_anndata_for_pipeline
from validator import validate_h5ad

INPUT = ROOT / "03_external_validation/03_processed_data/sciplex4/sciplex4_A549_control_3compounds.h5ad"
CLEAN_RUN = ROOT / "03_external_validation/05_runs/sciplex4_A549"
OUT_DIR = ROOT / "final_audit/robustness"


def audit_output_manifest(run_dir: Path) -> tuple[str, str]:
    manifest_path = run_dir / "output_manifest.csv"
    if not manifest_path.exists():
        return "failed_integrity", "output_manifest.csv missing"
    missing = []
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rel = row.get("path")
            if rel and not (run_dir / rel).exists():
                missing.append(rel)
    if missing:
        return "failed_integrity", "manifest-listed files missing: " + "; ".join(missing)
    return "passed_integrity", "all manifest-listed files present"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    adata = sc.read_h5ad(INPUT)

    # R1: remove a required metadata field in memory and run the validation layer.
    r1 = adata.copy()
    if "condition" in r1.obs.columns:
        r1.obs = r1.obs.drop(columns=["condition"])
    r1_report = validate_anndata_for_pipeline(r1, required_keys=["condition", "cell_type"])
    rows.append(
        {
            "scenario": "R1_missing_required_metadata",
            "dataset": "sci-Plex4 A549",
            "fault": "Removed obs['condition'] from an in-memory copy",
            "expected_behavior": "validation failure with explicit missing-field report",
            "actual_status": "failed_validation" if not r1_report["valid"] else "unexpected_pass",
            "completed_modules_reused": "not applicable; validation-layer test",
            "modules_rerun": "none",
            "manual_intervention": "no",
            "output_match_clean_run": "not applicable",
            "notes": "; ".join(r1_report.get("warnings", []) + r1_report.get("issues", [])),
        }
    )

    # R2: delete a manifest-listed intermediate output in an audit copy.
    r2_dir = OUT_DIR / "R2_deleted_intermediate_copy"
    if r2_dir.exists():
        shutil.rmtree(r2_dir)
    shutil.copytree(CLEAN_RUN, r2_dir)
    deleted = r2_dir / "merged_pathway_results.csv"
    if deleted.exists():
        deleted.unlink()
    r2_status, r2_note = audit_output_manifest(r2_dir)
    rows.append(
        {
            "scenario": "R2_deleted_intermediate_output",
            "dataset": "sci-Plex4 A549",
            "fault": "Deleted merged_pathway_results.csv from copied clean run output",
            "expected_behavior": "audit detects missing manifest-listed output",
            "actual_status": r2_status,
            "completed_modules_reused": "not tested; no executable resume CLI is implemented",
            "modules_rerun": "none",
            "manual_intervention": "yes; rerun or restore missing output required",
            "output_match_clean_run": "no; copied run intentionally missing one output",
            "notes": r2_note,
        }
    )

    # R3: use the real H5AD with a mismatched configuration key.
    r3_config = {
        "condition_key": "condition_DOES_NOT_EXIST",
        "cell_type_key": "cell_type",
        "control_label": "control",
    }
    passed, report, issues = validate_h5ad(str(INPUT), config=r3_config)
    rows.append(
        {
            "scenario": "R3_schema_mismatch_invalid_config",
            "dataset": "sci-Plex4 A549",
            "fault": "Set condition_key to a non-existent obs column",
            "expected_behavior": "validation failure with explicit config-key mismatch",
            "actual_status": "failed_validation" if not passed else "unexpected_pass",
            "completed_modules_reused": "not applicable; validation-layer test",
            "modules_rerun": "none",
            "manual_intervention": "no",
            "output_match_clean_run": "not applicable",
            "notes": "; ".join(issues) or json.dumps(report, default=str),
        }
    )

    result_csv = OUT_DIR / "ROBUSTNESS_TEST_RESULTS.csv"
    with result_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    result_md = OUT_DIR / "ROBUSTNESS_TEST_RESULTS.md"
    lines = [
        "# Robustness Fault-Injection Results",
        "",
        "These tests used the sci-Plex4 A549 analysis input and a copied clean run directory.",
        "They did not modify canonical raw data or canonical output records.",
        "",
        "| Scenario | Actual status | Manual intervention | Notes |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['actual_status']} | {row['manual_intervention']} | {row['notes']} |"
        )
    result_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(result_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
