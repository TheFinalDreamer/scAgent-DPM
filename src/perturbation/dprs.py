"""Drug Perturbation Response Score (DPRS) — component-aware multi-metric scoring.

DPRS(c, d) = sum(w_i * component_i) / sum(w_i) for available components only.

Each component is normalized to [0, 1] before weighting.
Missing/unavailable components are excluded; weights are re-normalized.
Status: valid | partial | insufficient_components | failed
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.perturbation.dprs")

COMPONENT_DEFS = {
    "PS": {"name": "proportion_shift", "weight_key": "proportion_shift", "label": "Proportion Shift"},
    "DE": {"name": "deg_intensity", "weight_key": "deg_intensity", "label": "DEG Intensity"},
    "PA": {"name": "pathway_activity", "weight_key": "pathway_activity", "label": "Pathway Activity"},
    "TS": {"name": "trajectory_shift", "weight_key": "trajectory_shift", "label": "Trajectory Shift"},
    "CW": {"name": "confidence_weight", "weight_key": "confidence_weight", "label": "Confidence Weight"},
}

DEFAULT_WEIGHTS = {
    "proportion_shift": 0.30,
    "deg_intensity": 0.25,
    "pathway_activity": 0.20,
    "trajectory_shift": 0.15,
    "confidence_weight": 0.10,
}


def compute_dprs(
    proportion_df=None, deg_df=None, pathway_df=None,
    trajectory_df=None, confidence_weights=None,
    weights=None, cell_types=None,
):
    """Compute DPRS per cell type (legacy single-experiment mode)."""
    if weights is None:
        weights = dict(DEFAULT_WEIGHTS)
    all_cts = _collect_cell_types(proportion_df, deg_df, cell_types)
    components = {
        "proportion_shift": _build_proportion_shift(proportion_df, all_cts),
        "deg_intensity": _build_deg_intensity(deg_df, all_cts),
        "pathway_activity": _build_pathway_activity(pathway_df, all_cts),
        "trajectory_shift": _build_trajectory_shift(trajectory_df, all_cts),
        "confidence_weight": _build_confidence_weight(confidence_weights, all_cts),
    }
    rows = [_build_dprs_row(ct, None, components, weights) for ct in all_cts]
    dprs_df = pd.DataFrame(rows)
    if not dprs_df.empty and "normalized_score" in dprs_df.columns:
        dprs_df = dprs_df.sort_values("normalized_score", ascending=False)
    return dprs_df, _build_metadata(all_cts, components)


def compute_dprs_per_drug(
    proportion_df=None, deg_df=None, pathway_df=None,
    trajectory_df=None, confidence_weights=None,
    weights=None, drug_col="drug", group_col="cell_type",
):
    """Compute DPRS per drug x group (cell line) combination."""
    if weights is None:
        weights = dict(DEFAULT_WEIGHTS)
    pairs = set()
    for df in [deg_df, proportion_df, pathway_df]:
        if df is not None and not df.empty:
            if group_col in df.columns and drug_col in df.columns:
                pairs.update((r[group_col], r[drug_col]) for _, r in df.iterrows())
    if not pairs:
        return pd.DataFrame(), {"n_pairs": 0, "reason": "no_data"}
    rows = []
    for group, drug in sorted(pairs):
        deg_sub = _subset_df(deg_df, group_col, group, drug_col, drug)
        prop_sub = _subset_df(proportion_df, group_col, group, drug_col, drug)
        path_sub = _subset_df(pathway_df, group_col, group, drug_col, drug)
        components = {
            "proportion_shift": _build_proportion_shift(prop_sub, [group]),
            "deg_intensity": _build_deg_intensity(deg_sub, [group]),
            "pathway_activity": _build_pathway_activity(path_sub, [group]),
            "trajectory_shift": _build_trajectory_shift(trajectory_df, [group]),
            "confidence_weight": _build_confidence_weight(confidence_weights, [group]),
        }
        rows.append(_build_dprs_row(group, drug, components, weights))
    dprs_df = pd.DataFrame(rows)
    if not dprs_df.empty and "normalized_score" in dprs_df.columns:
        dprs_df = dprs_df.sort_values("normalized_score", ascending=False)
    return dprs_df, _build_metadata_per_drug(dprs_df)


def _subset_df(df, group_col, group, drug_col, drug):
    if df is None or df.empty:
        return None
    if group_col in df.columns and drug_col in df.columns:
        return df[(df[group_col] == group) & (df[drug_col] == drug)]
    return None


def _build_dprs_row(group, drug, components, weights):
    available = {}
    unavailable = {}
    for comp_key, comp_def in COMPONENT_DEFS.items():
        comp_name = comp_def["name"]
        scores = components.get(comp_name, {})
        if group in scores and not np.isnan(scores[group]):
            available[comp_key] = scores[group]
        else:
            unavailable[comp_key] = "unavailable"
    effective_weights = {}
    total_w = 0.0
    for comp_key in available:
        wk = COMPONENT_DEFS[comp_key]["weight_key"]
        w = weights.get(wk, DEFAULT_WEIGHTS.get(wk, 0.0))
        effective_weights[comp_key] = w
        total_w += w
    renormalized_weights = {}
    if total_w > 0:
        for comp_key, w in effective_weights.items():
            renormalized_weights[comp_key] = round(w / total_w, 6)
    raw_score = 0.0
    for comp_key, w in renormalized_weights.items():
        raw_score += w * available[comp_key]
    n_available = len(available)
    status, reason = _determine_status(n_available, unavailable)
    confidence = _compute_confidence(n_available, len(COMPONENT_DEFS), available)
    normalized_score = round(raw_score, 6) if status != "insufficient_components" else np.nan
    return {
        "group": group,
        "drug": drug if drug else group,
        "PS": round(available.get("PS", np.nan), 6),
        "DE": round(available.get("DE", np.nan), 6),
        "PA": round(available.get("PA", np.nan), 6),
        "TS": round(available.get("TS", np.nan), 6),
        "CW": round(available.get("CW", np.nan), 6),
        "available_components": sorted(available.keys()),
        "unavailable_components": sorted(unavailable.keys()),
        "effective_weights": json.dumps(renormalized_weights),
        "raw_score": round(raw_score, 6),
        "normalized_score": normalized_score,
        "confidence": round(confidence, 6),
        "status": status,
        "unavailable_reason": "; ".join(f"{k}: {v}" for k, v in unavailable.items()),
    }


def _determine_status(n_available, unavailable):
    if n_available >= 4:
        return "valid", ""
    elif n_available >= 2:
        return "partial", f"Only {n_available}/5 components available"
    elif n_available == 1:
        return "insufficient_components", f"Only {n_available}/5 components; min 2 required"
    else:
        return "insufficient_components", "No components available"


def _compute_confidence(n_available, n_total, available):
    base_conf = n_available / n_total
    if n_available >= 2:
        vals = list(available.values())
        spread = max(vals) - min(vals) if len(vals) > 1 else 0.0
        base_conf = base_conf * (0.5 + 0.5 * min(spread, 1.0))
    return base_conf


def _build_proportion_shift(proportion_df, all_cts):
    scores = {}
    if proportion_df is not None and not proportion_df.empty:
        if "abs_shift" in proportion_df.columns and "cell_type" in proportion_df.columns:
            raw = proportion_df.set_index("cell_type")["abs_shift"]
            scores = _normalize_component(raw, "proportion_shift")
    return scores


def _build_deg_intensity(deg_df, all_cts):
    scores = {}
    if deg_df is not None and not deg_df.empty:
        try:
            from .deg import compute_deg_intensity
            raw_dict = {ct: compute_deg_intensity(deg_df, ct) for ct in all_cts}
            scores = _normalize_component(pd.Series(raw_dict), "deg_intensity")
        except ImportError:
            pass
    return scores


def _build_pathway_activity(pathway_df, all_cts):
    scores = {}
    if pathway_df is not None and not pathway_df.empty:
        try:
            from .pathway import compute_pathway_activity
            raw_dict = {ct: compute_pathway_activity(pathway_df, ct) for ct in all_cts}
            scores = _normalize_component(pd.Series(raw_dict), "pathway_activity")
        except ImportError:
            pass
    return scores


def _build_trajectory_shift(trajectory_df, all_cts):
    scores = {}
    if trajectory_df is not None and not trajectory_df.empty:
        if "trajectory_shift" in trajectory_df.columns and "cell_type" in trajectory_df.columns:
            raw = trajectory_df.set_index("cell_type")["trajectory_shift"]
        elif "shift_score" in trajectory_df.columns and "cell_type" in trajectory_df.columns:
            raw = trajectory_df.set_index("cell_type")["shift_score"]
        else:
            return scores
        scores = _normalize_component(raw, "trajectory_shift")
    return scores


def _build_confidence_weight(confidence_weights, all_cts):
    scores = {}
    if confidence_weights is not None and len(confidence_weights) > 0:
        scores = _normalize_component(confidence_weights, "confidence_weight")
    return scores


def _normalize_component(series, name):
    """Normalize component scores to [0, 1] via min-max scaling."""
    s = series.dropna()
    if len(s) == 0:
        return {}
    if s.max() == s.min():
        return {k: 0.5 for k in series.index}
    normalized = (s - s.min()) / (s.max() - s.min())
    return normalized.to_dict()


def _collect_cell_types(proportion_df, deg_df, cell_types):
    all_cts = set()
    for df in [proportion_df, deg_df]:
        if df is not None and not df.empty and "cell_type" in df.columns:
            all_cts.update(df["cell_type"].unique())
    if cell_types:
        all_cts.update(cell_types)
    return sorted(all_cts)


def _build_metadata(all_cts, components):
    available = [k for k, v in components.items() if v]
    missing = [k for k, v in components.items() if not v]
    return {
        "n_cell_types_scored": len(all_cts),
        "available_components": available,
        "missing_components": missing,
    }


def _build_metadata_per_drug(dprs_df):
    if dprs_df.empty:
        return {"n_pairs": 0, "reason": "no_data"}
    return {
        "n_pairs": len(dprs_df),
        "n_valid": int((dprs_df["status"] == "valid").sum()),
        "n_partial": int((dprs_df["status"] == "partial").sum()),
        "n_insufficient": int((dprs_df["status"] == "insufficient_components").sum()),
        "n_failed": int((dprs_df["status"] == "failed").sum()),
    }


def identify_drug_sensitive_cell_types(dprs_df, threshold_percentile=75.0):
    """Identify cell types with high DPRS (only valid/partial rows)."""
    if dprs_df.empty:
        return dprs_df
    eligible = dprs_df[dprs_df["status"].isin(["valid", "partial"])]
    if eligible.empty:
        return pd.DataFrame()
    threshold = np.percentile(eligible["normalized_score"], threshold_percentile)
    sensitive = eligible[eligible["normalized_score"] >= threshold].copy()
    sensitive["is_drug_sensitive"] = True
    logger.info(f"Identified {len(sensitive)} drug-sensitive entries (threshold={threshold:.4f})")
    return sensitive
