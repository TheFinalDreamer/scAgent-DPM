#!/usr/bin/env python
"""Track A v2 Post-Power-Outage Recovery Inspection Script.

Scans partial/complete Track A v2 results and generates a full audit of
what was completed before the outage, what's missing, and what can be
resumed.

Usage:
    python scripts/recovery_inspect_track_a_v2.py \
        --base-dir results/real_experiments/sciPlex3_medium_multicellline_v2 \
        --output-dir 00_project_management/recovery_YYYYMMDD_HHMMSS
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# Expected outputs
# ---------------------------------------------------------------------------

EXPECTED_FILES = [
    "run_manifest.json",
    "execution_graph.json",
    "config_snapshot.yaml",
    "environment_snapshot.json",
    "merged_deg_results.csv",
    "merged_pathway_results.csv",
    "merged_dprs_components.csv",
    "merged_dprs_ranking.csv",
    "dprs_status_summary.json",
]

EXPECTED_DRUGS = [
    "Tacedinaline",
    "Baricitinib",
    "Alvespimycin",
    "Belinostat",
    "Birinapant",
    "Cerdulatinib",
    "Dacinostat",
    "Danusertib",
    "Flavopiridol",
    "Givinostat",
]

EXPECTED_CELL_LINES = ["MCF7", "A549", "K562"]


# ---------------------------------------------------------------------------
# Core inspection
# ---------------------------------------------------------------------------

def find_track_a_v2_dirs(base_dir: str) -> List[Path]:
    """Find all directories related to Track A v2 multicellline."""
    base = Path(base_dir)
    if not base.exists():
        return []
    candidates = list(base.rglob("*multicellline*v2*"))
    # Also check for timestamped run dirs inside
    for d in sorted(base.glob("*")):
        if d.is_dir() and d not in candidates:
            candidates.append(d)
    return sorted(set(candidates))


def scan_directory(run_dir: Path) -> Dict[str, Any]:
    """Scan a single run directory and return its status."""
    result = {
        "run_dir": str(run_dir),
        "exists": run_dir.exists(),
        "files_found": [],
        "files_missing": [],
        "manifest": None,
        "manifest_valid": False,
        "module_status": {},
        "deg_file": None,
        "deg_rows": 0,
        "pathway_file": None,
        "pathway_rows": 0,
        "dprs_components_file": None,
        "dprs_ranking_file": None,
        "dprs_status_file": None,
        "drugs_completed": [],
        "drugs_missing": [],
        "drug_deg_counts": {},
        "drug_pathway_counts": {},
        "gene_symbol_issues": 0,
        "raw_count_warnings": 0,
        "is_complete": False,
        "errors": [],
    }

    if not run_dir.exists():
        result["errors"].append("Run directory does not exist")
        return result

    # Check expected files
    for fname in EXPECTED_FILES:
        fpath = run_dir / fname
        if fpath.exists():
            result["files_found"].append(fname)
        else:
            result["files_missing"].append(fname)

    # Read manifest
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                result["manifest"] = json.load(f)
            result["manifest_valid"] = True
            # Extract module status
            summary = result["manifest"].get("status_summary", {})
            result["module_status"] = {
                s.get("module", s.get("step", "unknown")): s.get("status", "unknown")
                for s in result["manifest"].get("steps", [])
            }
        except (json.JSONDecodeError, Exception) as e:
            result["errors"].append(f"Manifest read error: {e}")

    # Check DEG
    deg_files = list(run_dir.glob("*deg*results*.csv")) + list(run_dir.glob("merged_deg_results.csv"))
    if deg_files:
        result["deg_file"] = str(deg_files[0])
        try:
            deg_df = pd.read_csv(deg_files[0])
            result["deg_rows"] = len(deg_df)
            # Check for gene_symbol column
            if "gene_symbol" in deg_df.columns:
                symbol_match = deg_df["gene_symbol"].notna().sum()
                result["gene_symbol_mapping"] = f"{symbol_match}/{len(deg_df)}"
                if symbol_match < len(deg_df):
                    result["gene_symbol_issues"] = len(deg_df) - symbol_match
            # Check for raw-count warnings in manifest
            if result["manifest_valid"]:
                for step in result["manifest"].get("steps", []):
                    if "raw_count" in str(step.get("warnings", "")).lower():
                        result["raw_count_warnings"] += 1
            # Count drugs
            for col in ["drug", "perturbation", "condition"]:
                if col in deg_df.columns:
                    drugs = deg_df[col].dropna().unique()
                    result["drugs_completed"] = sorted([d for d in drugs if d != "Vehicle"])
                    break
            # Per-drug DEG counts
            drug_col = None
            for col in ["drug", "perturbation", "condition"]:
                if col in deg_df.columns:
                    drug_col = col
                    break
            if drug_col:
                result["drug_deg_counts"] = (
                    deg_df[deg_df[drug_col] != "Vehicle"]
                    .groupby(drug_col)
                    .size()
                    .to_dict()
                )
        except Exception as e:
            result["errors"].append(f"DEG read error: {e}")

    # Check Pathway
    pw_files = list(run_dir.glob("*pathway*results*.csv")) + list(run_dir.glob("merged_pathway_results.csv"))
    if pw_files:
        result["pathway_file"] = str(pw_files[0])
        try:
            pw_df = pd.read_csv(pw_files[0])
            result["pathway_rows"] = len(pw_df)
            # Count by status if available
            if "status" in pw_df.columns:
                result["pathway_status_counts"] = pw_df["status"].value_counts().to_dict()
            # Check for tested vs significant
            for col in ["fdr_significant_count", "tested_pathway_count"]:
                if col in pw_df.columns:
                    result[f"pathway_{col}"] = int(pw_df[col].sum()) if pw_df[col].notna().any() else 0
        except Exception as e:
            result["errors"].append(f"Pathway read error: {e}")

    # Check DPRS
    dprs_comp = run_dir / "merged_dprs_components.csv"
    dprs_rank = run_dir / "merged_dprs_ranking.csv"
    dprs_status = run_dir / "dprs_status_summary.json"

    if dprs_comp.exists():
        result["dprs_components_file"] = str(dprs_comp)
        try:
            comp_df = pd.read_csv(dprs_comp)
            result["dprs_components_rows"] = len(comp_df)
            if "status" in comp_df.columns:
                result["dprs_status_counts"] = comp_df["status"].value_counts().to_dict()
            # Check for 0.5 placeholders
            for col in ["PS", "DE", "PA", "TS", "CW"]:
                if col in comp_df.columns:
                    placeholder_count = (comp_df[col] == 0.5).sum()
                    if placeholder_count > 0:
                        result["errors"].append(
                            f"DPRS 0.5 PLACEHOLDER DETECTED: {col} has {placeholder_count} placeholder values"
                        )
        except Exception as e:
            result["errors"].append(f"DPRS components read error: {e}")

    if dprs_rank.exists():
        result["dprs_ranking_file"] = str(dprs_rank)
    if dprs_status.exists():
        result["dprs_status_file"] = str(dprs_status)
        try:
            with open(dprs_status) as f:
                result["dprs_status_summary"] = json.load(f)
        except Exception:
            pass

    # Determine completeness
    result["missing_drugs"] = sorted(set(EXPECTED_DRUGS) - set(result.get("drugs_completed", [])))
    result["is_complete"] = (
        len(result.get("drugs_completed", [])) == len(EXPECTED_DRUGS)
        and result["manifest_valid"]
        and result["deg_rows"] > 0
        and result["pathway_rows"] > 0
    )

    return result


def determine_recovery_strategy(scans: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Determine which recovery strategy to use."""
    strategy = {
        "case": "UNKNOWN",
        "reason": "",
        "can_resume": False,
        "need_rerun": False,
        "need_partial": False,
        "recommendation": "",
    }

    # Find the most complete run
    run_dirs = [s for s in scans if s["exists"]]
    if not run_dirs:
        strategy["case"] = "D"
        strategy["reason"] = "No Track A v2 run directories found"
        strategy["recommendation"] = "Full rerun from scratch"
        return strategy

    # Sort by deg_rows descending (most complete first)
    best = max(run_dirs, key=lambda s: s.get("deg_rows", 0))

    if best["is_complete"]:
        strategy["case"] = "A"
        strategy["reason"] = "Track A v2 appears complete"
        strategy["recommendation"] = "Only supplement audit/summary/figures — NO rerun"
    elif best["manifest_valid"] and len(best.get("drugs_completed", [])) > 0:
        strategy["case"] = "B"
        strategy["reason"] = f"Partial completion: {len(best['drugs_completed'])}/{len(EXPECTED_DRUGS)} drugs done"
        strategy["can_resume"] = True
        strategy["resume_from"] = best["run_dir"]
        strategy["completed_drugs"] = best["drugs_completed"]
        strategy["missing_drugs"] = best.get("missing_drugs", [])
        strategy["recommendation"] = (
            f"Resume from {best['run_dir']} — "
            f"skip {len(best['drugs_completed'])} completed drugs, "
            f"run {len(best.get('missing_drugs', []))} remaining"
        )
    elif best["deg_rows"] > 0:
        strategy["case"] = "C"
        strategy["reason"] = "Partial results exist but manifest is damaged or incomplete"
        strategy["need_rerun"] = True
        strategy["recommendation"] = "Create recovery run, preserve old partial as reference, rerun missing drugs"
    else:
        strategy["case"] = "C"
        strategy["reason"] = "Track A v2 directory exists but no usable results found"
        strategy["need_rerun"] = True
        strategy["recommendation"] = "Full rerun in new recovery directory"

    return strategy


# ---------------------------------------------------------------------------
# Output generators
# ---------------------------------------------------------------------------

def generate_markdown_report(
    scans: List[Dict[str, Any]],
    strategy: Dict[str, Any],
    output_dir: Path,
) -> str:
    """Generate a Markdown audit report."""
    lines = []
    lines.append("# Track A v2 — Partial Result Audit Report")
    lines.append(f"\n**Generated:** {datetime.now().isoformat()}")
    lines.append(f"**Base directory:** {scans[0]['run_dir'] if scans else 'N/A'}")

    lines.append("\n---\n")
    lines.append("## 1. Directory Scan Results\n")
    for s in scans:
        lines.append(f"### {Path(s['run_dir']).name}")
        lines.append(f"- Exists: {s['exists']}")
        lines.append(f"- Files found: {len(s['files_found'])}/{len(EXPECTED_FILES)}")
        if s["files_missing"]:
            lines.append(f"- **Files missing:** {', '.join(s['files_missing'])}")
        lines.append(f"- Manifest valid: {s['manifest_valid']}")
        lines.append(f"- DEG rows: {s['deg_rows']}")
        lines.append(f"- Pathway rows: {s['pathway_rows']}")
        lines.append(f"- Drugs completed: {len(s.get('drugs_completed', []))}/10")
        if s.get("drugs_completed"):
            lines.append(f"  - {', '.join(s['drugs_completed'])}")
        if s.get("missing_drugs"):
            lines.append(f"- **Drugs missing:** {', '.join(s['missing_drugs'])}")
        if s.get("drug_deg_counts"):
            lines.append(f"- Per-drug DEG counts: {json.dumps(s['drug_deg_counts'], indent=2)}")
        if s.get("gene_symbol_issues", 0) > 0:
            lines.append(f"- **Gene symbol issues:** {s['gene_symbol_issues']}")
        if s.get("raw_count_warnings", 0) > 0:
            lines.append(f"- **Raw-count warnings:** {s['raw_count_warnings']}")
        if s.get("dprs_status_counts"):
            lines.append(f"- DPRS status: {json.dumps(s['dprs_status_counts'])}")
        if s.get("pathway_status_counts"):
            lines.append(f"- Pathway status: {json.dumps(s['pathway_status_counts'])}")
        if s["errors"]:
            lines.append(f"- **Errors:** {', '.join(s['errors'])}")
        lines.append("")

    lines.append("\n---\n")
    lines.append("## 2. Recovery Strategy\n")
    lines.append(f"- **Case:** {strategy['case']}")
    lines.append(f"- **Reason:** {strategy['reason']}")
    lines.append(f"- **Can resume:** {strategy.get('can_resume', False)}")
    lines.append(f"- **Need rerun:** {strategy.get('need_rerun', False)}")
    if strategy.get("completed_drugs"):
        lines.append(f"- **Completed drugs:** {', '.join(strategy['completed_drugs'])}")
    if strategy.get("missing_drugs"):
        lines.append(f"- **Missing drugs:** {', '.join(strategy['missing_drugs'])}")
    lines.append(f"\n**Recommendation:** {strategy['recommendation']}")

    lines.append("\n---\n")
    lines.append("## 3. Next Actions\n")
    if strategy["case"] == "A":
        lines.append("1. Supplement audit, summary, and figures")
        lines.append("2. Run pathway strict review (544 terms check)")
        lines.append("3. Run DPRS strict review (30 records check)")
    elif strategy["case"] == "B":
        lines.append("1. Run `python main.py resume-run --run-dir <DIR>`")
        lines.append("2. Verify completed drugs are not re-run")
        lines.append("3. After completion, run full audit")
    elif strategy["case"] == "C":
        lines.append("1. Create recovery run directory")
        lines.append("2. Backup old partial results")
        lines.append("3. Run missing drugs or full rerun")
        lines.append("4. Merge results with old partial where possible")
    else:
        lines.append("1. Fix missing scripts first")
        lines.append("2. Run full Track A v2 from scratch")

    report_path = output_dir / "TRACK_A_V2_PARTIAL_RESULT_AUDIT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return str(report_path)


def generate_json_report(
    scans: List[Dict[str, Any]],
    strategy: Dict[str, Any],
    output_dir: Path,
) -> str:
    """Generate a JSON audit report."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "scans": scans,
        "strategy": strategy,
    }
    json_path = output_dir / "TRACK_A_V2_PARTIAL_RESULT_AUDIT.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    return str(json_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Track A v2 Post-Power-Outage Recovery Inspection"
    )
    parser.add_argument(
        "--base-dir",
        default="results/real_experiments/sciPlex3_medium_multicellline_v2",
        help="Base directory for Track A v2 results",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for audit reports",
    )
    parser.add_argument(
        "--json-only", action="store_true", help="Output JSON only"
    )
    parser.add_argument(
        "--md-only", action="store_true", help="Output Markdown only"
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning: {base_dir}")
    print(f"Output:   {output_dir}")

    # Step 1: Find run directories
    run_dirs = find_track_a_v2_dirs(str(base_dir))
    print(f"\nFound {len(run_dirs)} candidate directories:")
    for d in run_dirs:
        print(f"  {d}")

    if not run_dirs:
        # Also check the base directory itself
        if base_dir.exists():
            run_dirs = [base_dir]
            print(f"  (using base directory: {base_dir})")

    # Step 2: Scan each directory
    scans = []
    for d in run_dirs:
        print(f"\nScanning: {d}")
        result = scan_directory(d)
        scans.append(result)
        print(f"  DEG rows: {result['deg_rows']}")
        print(f"  Pathway rows: {result['pathway_rows']}")
        print(f"  Drugs completed: {len(result.get('drugs_completed', []))}/10")
        if result["errors"]:
            for e in result["errors"]:
                print(f"  ERROR: {e}")

    # Step 3: Determine strategy
    strategy = determine_recovery_strategy(scans)
    print(f"\n=== RECOVERY STRATEGY ===")
    print(f"Case: {strategy['case']}")
    print(f"Reason: {strategy['reason']}")
    print(f"Recommendation: {strategy['recommendation']}")

    # Step 4: Generate reports
    if not args.md_only:
        json_path = generate_json_report(scans, strategy, output_dir)
        print(f"\nJSON report: {json_path}")

    if not args.json_only:
        md_path = generate_markdown_report(scans, strategy, output_dir)
        print(f"Markdown report: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
