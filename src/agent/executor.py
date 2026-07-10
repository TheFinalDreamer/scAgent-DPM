"""Pipeline executor: runs the full scAgent-DPM pipeline end-to-end.

v2: Integrated DPRS v2 (per-drug scoring) and Pathway v2 (structured status).
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anndata as ann
import numpy as np
import pandas as pd
import scanpy as sc

from .planner import AgentPlanner
from .state import PipelineState
from ..data.loaders import load_data, inspect_data, generate_data_report
from ..data.preprocessing import preprocess
from ..qc.adaptive_qc import run_qc_pipeline
from ..qc.qc_report import generate_qc_report
from ..annotation.celltypist_runner import run_celltypist
from ..annotation.scgpt_runner import run_scgpt
from ..annotation.scgpt_kdmt_runner import run_scgpt_kdmt
from ..annotation.confidence import compute_confidence_weight
from ..perturbation.proportion_shift import compute_proportion_shift
from ..perturbation.deg import run_deg_per_cell_type
from ..perturbation.pathway import run_pathway_enrichment
from ..perturbation.dprs import compute_dprs, compute_dprs_per_drug, identify_drug_sensitive_cell_types
from ..perturbation.perturbation_report import generate_perturbation_report
from ..dynamics.pseudotime import run_pseudotime
from ..dynamics.mamba_lstm_interface import run_mamba_lstm
from ..dynamics.trajectory_shift import compute_trajectory_shift_metrics
from ..reporting.markdown_report import generate_markdown_report
from ..reporting.html_report import generate_html_report
from ..utils.reproducibility import set_seed, save_reproducibility_metadata

logger = logging.getLogger("scagent_dpm.agent.executor")


class PipelineExecutor:
    """Executes the full scAgent-DPM pipeline (v2)."""

    def __init__(self, config: Dict[str, Any], output_dir: str = "results"):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.planner = AgentPlanner(config, output_dir)
        self.adata: Optional[ann.AnnData] = None
        self._results: Dict[str, Any] = {}
        self._start_time = time.time()

        seed = config.get("seed", 42)
        set_seed(seed)

        # Save config snapshot
        self._save_config_snapshot()

    def _save_config_snapshot(self):
        """Save config snapshot to output directory."""
        import yaml
        snapshot_path = self.output_dir / "config_snapshot.yaml"
        try:
            with open(snapshot_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.warning(f"Failed to save config snapshot: {e}")

    def run(self) -> Dict[str, Any]:
        """Execute the full pipeline with v2 DPRS and Pathway."""
        plan = self.planner.plan()
        logger.info(f"Starting pipeline v2: {plan['run_name']}")
        t0 = time.time()

        # Step 1: Data ingestion + validation
        self.planner.execute_module("data_ingestion", self._run_data_ingestion)
        self.planner.execute_module("data_validation", self._run_data_validation)

        # Step 2: QC
        if self.config.get("run_qc", True):
            self.planner.execute_module("qc", self._run_qc)

        # Step 3: Preprocessing
        self.planner.execute_module("preprocessing", self._run_preprocessing)

        # Step 4: Annotation (with unavailable handling)
        if self.config.get("run_annotation", False):
            self.planner.execute_module("annotation", self._run_annotation)
        else:
            self.planner.record_module("annotation", "skipped", reason="run_annotation=false")

        # Step 5: Perturbation (DEG + Pathway v2)
        if self.config.get("run_perturbation", True):
            self.planner.execute_module("perturbation", self._run_perturbation)

        # Step 6: Dynamics (with unavailable handling)
        if self.config.get("run_dynamics", False):
            self.planner.execute_module("dynamics", self._run_dynamics)
        else:
            self.planner.record_module("dynamics", "skipped", reason="run_dynamics=false")

        # Step 7: DPRS v2 (per-drug scoring)
        self.planner.execute_module("dprs", self._run_dprs)

        # Step 8: Reporting
        self.planner.execute_module("reporting", self._run_reporting)

        # Finalize
        runtime = round(time.time() - t0, 1)
        manifest_path = self.planner.finalize()
        self._save_environment_snapshot(runtime)
        save_reproducibility_metadata(self.output_dir, self.config.get("seed", 42), self.config)

        summary = self.planner.get_summary()
        logger.info(f"Pipeline complete: {summary} (runtime={runtime}s)")
        return {
            "manifest_path": str(manifest_path),
            "summary": summary,
            "output_dir": str(self.output_dir),
            "runtime_seconds": runtime,
        }

    def _save_environment_snapshot(self, runtime: float):
        """Save environment info."""
        import platform, sys
        env = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "runtime_seconds": runtime,
            "timestamp": pd.Timestamp.now().isoformat(),
        }
        try:
            import scanpy as _sc
            env["scanpy_version"] = _sc.__version__
        except Exception:
            pass
        try:
            import anndata as _ad
            env["anndata_version"] = _ad.__version__
        except Exception:
            pass
        env_path = self.output_dir / "environment_snapshot.json"
        with open(env_path, "w", encoding="utf-8") as f:
            json.dump(env, f, indent=2, default=str)

    def _run_data_ingestion(self) -> ann.AnnData:
        input_path = self.config.get("input_path")
        self.adata = load_data(input_path=input_path)
        summary = inspect_data(self.adata)
        generate_data_report(self.adata, self.output_dir / "data_summary.json")
        logger.info(f"Data loaded: {summary['n_cells']} cells, {summary['n_genes']} genes")
        self._results["data_summary"] = summary
        return self.adata

    def _run_data_validation(self) -> dict:
        """Validate input data and record issues (inline validation)."""
        issues = []
        warnings = []
        try:
            # Check required obs columns
            condition_key = self.config.get("condition_key", "condition")
            cell_type_key = self.config.get("cell_type_key", "cell_type")
            for key in [condition_key, cell_type_key]:
                if key not in self.adata.obs.columns:
                    issues.append(f"Missing obs column: {key}")

            # Check NaN/Inf
            if hasattr(self.adata.X, 'data'):
                if np.isnan(self.adata.X.data).any():
                    issues.append("NaN values in expression matrix")
                if np.isinf(self.adata.X.data).any():
                    issues.append("Inf values in expression matrix")

            # Check min cells/genes
            if self.adata.n_obs < 50:
                warnings.append(f"Low cell count: {self.adata.n_obs}")
            if self.adata.n_vars < 100:
                warnings.append(f"Low gene count: {self.adata.n_vars}")

            # Check gene symbols
            symbol_cols = ["gene_short_name", "gene_symbol", "symbol", "gene_name", "hgnc_symbol"]
            has_symbol = any(c in self.adata.var.columns for c in symbol_cols)
            if not has_symbol:
                warnings.append("No gene symbol column found in var — DEG will use var_names")

            # Check control label
            control_label = self.config.get("control_label", "control")
            if control_label not in self.adata.obs[condition_key].values:
                issues.append(f"Control label '{control_label}' not found in obs.{condition_key}")

            report = {
                "valid": len(issues) == 0,
                "n_issues": len(issues),
                "n_warnings": len(warnings),
                "issues": issues,
                "warnings": warnings,
                "n_cells": self.adata.n_obs,
                "n_genes": self.adata.n_vars,
                "control_label": control_label,
                "condition_values": self.adata.obs[condition_key].value_counts().to_dict(),
            }
        except Exception as e:
            report = {"valid": False, "issues": [f"Validation error: {e}"], "warnings": [], "n_issues": 1, "n_warnings": 0}

        self._results["data_validation"] = report
        if issues:
            logger.warning(f"Data validation: {len(issues)} issues, {len(warnings)} warnings")
        else:
            logger.info(f"Data validation passed ({len(warnings)} warnings)")
        return report

    def _run_qc(self) -> tuple:
        adata_qc, qc_stats = run_qc_pipeline(self.adata, self.config)
        self.adata = adata_qc
        generate_qc_report(qc_stats, self.output_dir)
        self._results["qc"] = qc_stats
        logger.info(
            f"QC: {qc_stats.get('n_cells_before', '?')} -> {qc_stats.get('n_cells_after', '?')} cells"
        )
        return adata_qc, qc_stats

    def _run_preprocessing(self) -> ann.AnnData:
        self.adata = preprocess(self.adata)
        logger.info(f"Preprocessing: {self.adata.shape} after HVG filtering")
        self._results["preprocessing"] = {
            "n_cells": self.adata.n_obs,
            "n_genes": self.adata.n_vars,
            "has_raw": self.adata.raw is not None,
        }
        return self.adata

    def _run_annotation(self) -> tuple:
        method = self.config.get("annotation_method", "celltypist")
        organism = self.config.get("organism", "human")

        if method == "celltypist":
            pred_df, anno_summary = run_celltypist(self.adata, organism=organism)
        elif method == "scgpt":
            scgpt_cfg = self.config.get("annotation", {}).get("scgpt", {})
            pred_df, anno_summary = run_scgpt(self.adata, model_path=scgpt_cfg.get("model_path"))
        elif method == "scgpt_kdmt":
            kdmt_cfg = self.config.get("annotation", {}).get("scgpt_kdmt", {})
            pred_df, anno_summary = run_scgpt_kdmt(
                self.adata,
                project_path=kdmt_cfg.get("project_path"),
                model_weights=kdmt_cfg.get("model_weights"),
            )
        elif method in ("none", "metadata", None):
            anno_summary = {"method": method or "none", "is_fallback": False,
                            "status": "skipped", "reason": "annotation_method=none or no checkpoint"}
            self._results["annotation"] = anno_summary
            return pd.DataFrame(), anno_summary
        else:
            anno_summary = {"method": method, "status": "unavailable",
                            "reason": f"Unknown annotation method: {method}"}
            self._results["annotation"] = anno_summary
            return pd.DataFrame(), anno_summary

        # Check for fallback
        if anno_summary.get("is_fallback"):
            logger.warning(f"Annotation ({method}) used FALLBACK — results marked as unavailable")
            anno_summary["status"] = "fallback"

        self.adata.obs["predicted_cell_type"] = pred_df["predicted_cell_type"].values
        if "confidence" in pred_df.columns:
            self.adata.obs["annotation_confidence"] = pred_df["confidence"].values
        self._results["annotation"] = anno_summary

        pred_df.to_csv(self.output_dir / "cell_annotation.csv", index=True)
        return pred_df, anno_summary

    def _run_perturbation(self) -> tuple:
        condition_key = self.config.get("condition_key", "condition")
        cell_type_key = self.config.get("cell_type_key", "cell_type")
        control_label = self.config.get("control_label", "control")
        organism = self.config.get("organism", "human")
        per_drug_mode = self.config.get("per_drug_mode", True)
        drug_col = self.config.get("drug_column", "drug")

        # Use log-normalized full-gene matrix for DEG (from raw layer)
        adata_for_deg = self._prepare_deg_adata()

        # Auto-detect non-control labels for treated_label
        all_cond_vals = self.adata.obs[condition_key].unique()
        non_ctrl = [v for v in all_cond_vals if v != control_label]
        treated_label = non_ctrl[0] if non_ctrl else "treated"
        logger.info(f"Auto-detected treated label: '{treated_label}' (non-control of '{control_label}')")

        # Proportion shift
        proportion_df = compute_proportion_shift(
            self.adata, condition_key=condition_key, cell_type_key=cell_type_key,
            control_label=control_label, treated_label=treated_label,
        )
        logger.info(f"Proportion shift: {len(proportion_df)} entries")

        # DEG with per-drug x cell_type decomposition
        deg_df = run_deg_per_cell_type(
            adata_for_deg, condition_key=condition_key, cell_type_key=cell_type_key,
            control_label=control_label, drug_col=drug_col,
        )
        logger.info(f"DEG: {len(deg_df)} entries, {deg_df['drug'].nunique() if 'drug' in deg_df.columns else 0} drugs")

        # Gene symbol mapping summary
        if "gene_symbol" in deg_df.columns and "names" in deg_df.columns:
            total = len(deg_df)
            mapped = deg_df["gene_symbol"].notna().sum()
            logger.info(f"Gene symbol mapping: {mapped}/{total} ({100*mapped/total:.1f}%)")

        # Pathway v2
        pt_cfg = self.config.get("perturbation", {})
        pw_cfg = pt_cfg.get("pathway", {})
        pathway_df, pathway_status_df = run_pathway_enrichment(
            deg_df,
            databases=pw_cfg.get("databases", ["KEGG_2021_Human"]),
            organism=organism,
            gene_col="gene_symbol",
            fallback_gene_col="names",
            cell_type_col=cell_type_key,
            drug_col=drug_col,
            direction_col="logfoldchanges" if "logfoldchanges" in deg_df.columns else None,
            min_genes=pw_cfg.get("min_genes", 5),
            local_gmt_paths=pw_cfg.get("local_gmt_paths"),
            online=pw_cfg.get("online", True),
        )
        logger.info(f"Pathway v2: {len(pathway_df)} enrichment results, {len(pathway_status_df)} status records")

        # Save outputs
        proportion_df.to_csv(self.output_dir / "merged_proportion_shift.csv", index=False)
        deg_df.to_csv(self.output_dir / "merged_deg_results.csv", index=False)
        pathway_df.to_csv(self.output_dir / "merged_pathway_results.csv", index=False)
        pathway_status_df.to_csv(self.output_dir / "pathway_status_summary.csv", index=False)

        self._results["proportion_df"] = proportion_df
        self._results["deg_df"] = deg_df
        self._results["pathway_df"] = pathway_df
        self._results["pathway_status_df"] = pathway_status_df
        return proportion_df, deg_df, pathway_df

    def _prepare_deg_adata(self) -> ann.AnnData:
        """Prepare log-normalized full-gene AnnData for DEG analysis.

        Uses adata.raw (raw counts) → normalize_total → log1p on ALL genes.
        This ensures DEG uses log-normalized data on the full gene set, not just HVGs.
        """
        if self.adata.raw is not None:
            deg_adata = self.adata.raw.to_adata()
            sc.pp.normalize_total(deg_adata, target_sum=1e4)
            sc.pp.log1p(deg_adata)
            # Copy obs annotations from processed adata
            for col in self.adata.obs.columns:
                if col in self.adata.obs.columns:
                    deg_adata.obs[col] = self.adata.obs.loc[deg_adata.obs_names, col]
            logger.info(f"DEG data prepared: {deg_adata.shape} (log-normalized full-gene)")
            self._results["deg_data_info"] = {
                "source": "adata.raw → normalize_total → log1p",
                "n_genes": deg_adata.n_vars,
                "n_cells": deg_adata.n_obs,
                "is_log_normalized": True,
            }
            return deg_adata
        else:
            # Fallback: use current adata (already log-normalized, may be HVG-filtered)
            logger.warning("adata.raw not available — using current adata for DEG (may be HVG-filtered)")
            self._results["deg_data_info"] = {
                "source": "current adata (fallback — .raw unavailable)",
                "n_genes": self.adata.n_vars,
                "n_cells": self.adata.n_obs,
                "is_log_normalized": True,
                "warning": "raw-count warning: .raw unavailable, DEG may use HVG subset",
            }
            return self.adata

    def _run_dynamics(self) -> tuple:
        method = self.config.get("dynamics_method", "pseudotime")

        if method in ("none", None):
            dyn_meta = {"method": "none", "status": "skipped",
                        "reason": "dynamics_method=none"}
            self._results["dynamics"] = dyn_meta
            return pd.DataFrame(), dyn_meta

        pseudotime_df, pt_summary = run_pseudotime(self.adata)
        self.adata.obs["dpt_pseudotime"] = pseudotime_df["dpt_pseudotime"].values

        if method == "mamba_lstm":
            dyn_cfg = self.config.get("dynamics", {}).get("mamba_lstm", {})
            dyn_result, dyn_meta = run_mamba_lstm(
                self.adata, pseudotime_df,
                project_path=dyn_cfg.get("project_path"),
                model_weights=dyn_cfg.get("model_weights"),
            )
            if dyn_meta.get("is_fallback"):
                dyn_meta["status"] = "fallback"
                logger.warning("Mamba-LSTM used fallback — pseudotime baseline only")
        else:
            trajectory_metrics = compute_trajectory_shift_metrics(
                self.adata, pseudotime_df,
                condition_key=self.config.get("condition_key", "condition"),
                control_label=self.config.get("control_label", "control"),
            )
            dyn_meta = {
                "method": "pseudotime",
                "status": "available",
                "is_fallback": False,
                "trajectory_metrics": trajectory_metrics,
            }

        self._results["pseudotime_df"] = pseudotime_df
        self._results["dynamics"] = dyn_meta
        pseudotime_df.to_csv(self.output_dir / "pseudotime.csv", index=False)
        return pseudotime_df, dyn_meta

    def _run_dprs(self) -> tuple:
        """DPRS v2: per-drug x cell_type component-aware scoring."""
        confidence_weights = None
        if "annotation_confidence" in self.adata.obs.columns:
            conf_series = self.adata.obs.groupby(
                self.adata.obs.get(self.config.get("cell_type_key", "cell_type"), self.adata.obs_names)
            )["annotation_confidence"].mean()
            confidence_weights = conf_series

        traj_df = None
        dyn_result = self._results.get("dynamics", {})
        if isinstance(dyn_result, dict):
            traj_metrics = dyn_result.get("trajectory_metrics", [])
            if traj_metrics:
                traj_df = pd.DataFrame(traj_metrics)

        dprs_weights = self.config.get("perturbation", {}).get("dprs_weights")
        cell_type_key = self.config.get("cell_type_key", "cell_type")
        drug_col = self.config.get("drug_column", "drug")

        deg_df = self._results.get("deg_df")
        proportion_df = self._results.get("proportion_df")
        pathway_df = self._results.get("pathway_df")

        # Use per-drug DPRS if drug column exists in DEG results
        if deg_df is not None and not deg_df.empty and drug_col in deg_df.columns:
            dprs_df, dprs_meta = compute_dprs_per_drug(
                proportion_df=proportion_df,
                deg_df=deg_df,
                pathway_df=pathway_df,
                trajectory_df=traj_df,
                confidence_weights=confidence_weights,
                weights=dprs_weights,
                drug_col=drug_col,
                group_col=cell_type_key,
            )
            logger.info(
                f"DPRS v2 (per-drug): {len(dprs_df)} entries, "
                f"valid={dprs_meta.get('n_valid', 0)}, "
                f"partial={dprs_meta.get('n_partial', 0)}, "
                f"insufficient={dprs_meta.get('n_insufficient', 0)}"
            )
        else:
            # Legacy mode: per-cell-type only
            dprs_df, dprs_meta = compute_dprs(
                proportion_df=proportion_df,
                deg_df=deg_df,
                pathway_df=pathway_df,
                trajectory_df=traj_df,
                confidence_weights=confidence_weights,
                weights=dprs_weights,
            )
            logger.info(f"DPRS (legacy mode): {len(dprs_df)} entries")

        sensitive = identify_drug_sensitive_cell_types(dprs_df)

        # Save DPRS outputs
        dprs_df.to_csv(self.output_dir / "merged_dprs_components.csv", index=False)
        if not dprs_df.empty:
            ranking_cols = [c for c in ["drug", "group", "normalized_score", "status", "available_components"] if c in dprs_df.columns]
            dprs_df[ranking_cols].sort_values("normalized_score", ascending=False).to_csv(
                self.output_dir / "merged_dprs_ranking.csv", index=False
            )
        if not sensitive.empty:
            sensitive.to_csv(self.output_dir / "drug_sensitive_cell_types.csv", index=False)

        # DPRS status summary
        dprs_status = {
            "n_total": len(dprs_df),
            "n_valid": int((dprs_df["status"] == "valid").sum()) if "status" in dprs_df.columns else 0,
            "n_partial": int((dprs_df["status"] == "partial").sum()) if "status" in dprs_df.columns else 0,
            "n_insufficient": int((dprs_df["status"] == "insufficient_components").sum()) if "status" in dprs_df.columns else 0,
            "n_failed": int((dprs_df["status"] == "failed").sum()) if "status" in dprs_df.columns else 0,
        }
        with open(self.output_dir / "dprs_status_summary.json", "w") as f:
            json.dump(dprs_status, f, indent=2)

        self._results["dprs_df"] = dprs_df
        self._results["dprs_meta"] = dprs_meta
        self._results["dprs_status"] = dprs_status
        self._results["drug_sensitive"] = sensitive

        return dprs_df, dprs_meta

    def _run_reporting(self) -> dict:
        formats = self.config.get("reporting", {}).get("formats", ["markdown", "html"])
        generated = []

        # Build module status summary for reporting
        module_status = self.planner.get_summary()
        self._results["module_status"] = module_status

        if "markdown" in formats:
            md_path = generate_markdown_report(self._results, str(self.output_dir))
            generated.append(("markdown", md_path))

        if "html" in formats:
            html_path = generate_html_report(self._results, str(self.output_dir))
            generated.append(("html", html_path))

        # JSON report
        json_path = self.output_dir / "report.json"
        try:
            report_data = {
                "module_status": module_status,
                "runtime_seconds": round(time.time() - self._start_time, 1),
                "output_dir": str(self.output_dir),
            }
            # Add summary stats from results
            for key in ["dprs_status", "data_summary", "qc", "annotation", "dynamics"]:
                val = self._results.get(key)
                if val is not None:
                    report_data[key] = val if isinstance(val, dict) else str(val)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, default=str)
            generated.append(("json", str(json_path)))
        except Exception as e:
            logger.warning(f"JSON report generation failed: {e}")

        # Output manifest
        manifest_rows = []
        for f in self.output_dir.rglob("*"):
            if f.is_file():
                manifest_rows.append({
                    "path": str(f.relative_to(self.output_dir)),
                    "size_bytes": f.stat().st_size,
                })
        manifest_df = pd.DataFrame(manifest_rows)
        manifest_df.to_csv(self.output_dir / "output_manifest.csv", index=False)

        logger.info(f"Reports generated: {[f for _, f in generated]}")
        return {"formats_generated": [fmt for fmt, _ in generated], "files": generated}
