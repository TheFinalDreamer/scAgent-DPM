"""Mamba-LSTM interface for dynamic state modeling.

This module provides an interface to the scLifeMamba/Mamba-LSTM project (Paper #3).
Delegates to the real model when available; falls back to pseudotime-only analysis
when the model or weights are missing.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.dynamics.mamba_lstm")


def run_mamba_lstm(
    adata,
    pseudotime_df: pd.DataFrame,
    project_path: Optional[str] = None,
    model_weights: Optional[str] = None,
    sequence_length: int = 100,
    hidden_dim: int = 128,
    num_layers: int = 2,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run Mamba-LSTM dynamic state modeling.

    Returns:
        result: dict with trajectory_shift, state_transition data
        metadata: dict with model info, is_fallback flag
    """
    if project_path and Path(project_path).exists():
        logger.info(f"Mamba-LSTM project found at {project_path}")
        result = _try_real_mamba_lstm(adata, pseudotime_df, project_path, model_weights,
                                      sequence_length, hidden_dim, num_layers)
        if result is not None:
            return result

    logger.warning(
        "Mamba-LSTM project/model not available — using pseudotime-only baseline as FALLBACK. "
        "Trajectory shift will be computed from pseudotime statistics only."
    )
    return _pseudotime_fallback(adata, pseudotime_df)


def _try_real_mamba_lstm(
    adata,
    pseudotime_df: pd.DataFrame,
    project_path: str,
    model_weights: Optional[str],
    sequence_length: int,
    hidden_dim: int,
    num_layers: int,
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Attempt real Mamba-LSTM inference. Returns None if unavailable."""
    project_path = Path(project_path)
    sys.path.insert(0, str(project_path))

    try:
        if model_weights and Path(model_weights).exists():
            logger.info(f"Loading Mamba-LSTM weights from {model_weights}")
            # Real inference would go here
            # from model import MambaLSTM
            # model = MambaLSTM(...)
            # model.load_state_dict(torch.load(model_weights))
            # results = model.predict_shift(adata, pseudotime_df)
            logger.warning(
                "Mamba-LSTM real inference interface reached but model loading not yet wired. "
                "Falling back to pseudotime baseline."
            )
            return None
        else:
            logger.warning(f"Mamba-LSTM weights not found at {model_weights}")
            return None
    except ImportError as e:
        logger.warning(f"Could not import Mamba-LSTM modules: {e}")
        return None
    finally:
        if str(project_path) in sys.path:
            sys.path.remove(str(project_path))


def _pseudotime_fallback(
    adata,
    pseudotime_df: pd.DataFrame,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Pseudotime-only baseline for trajectory shift estimation."""
    if "condition" in pseudotime_df.columns and "cell_type" in pseudotime_df.columns:
        ctrl = pseudotime_df[pseudotime_df["condition"] == "control"]
        treated = pseudotime_df[pseudotime_df["condition"] == "treated"]

        shift_rows = []
        for ct in pseudotime_df["cell_type"].unique():
            ctrl_ct = ctrl[ctrl["cell_type"] == ct]
            treated_ct = treated[treated["cell_type"] == ct]
            if len(ctrl_ct) < 10 or len(treated_ct) < 10:
                continue
            shift = float(treated_ct["dpt_pseudotime"].mean() - ctrl_ct["dpt_pseudotime"].mean())
            shift_rows.append({
                "cell_type": ct,
                "ctrl_mean_pt": float(ctrl_ct["dpt_pseudotime"].mean()),
                "treated_mean_pt": float(treated_ct["dpt_pseudotime"].mean()),
                "trajectory_shift": shift,
                "abs_shift": abs(shift),
            })
        shift_df = pd.DataFrame(shift_rows)
    else:
        shift_df = pd.DataFrame(columns=["cell_type", "trajectory_shift"])

    metadata = {
        "method": "pseudotime_baseline",
        "is_fallback": True,
        "fallback_warning": (
            "Mamba-LSTM model not available — trajectory shift from pseudotime statistics only. "
            "NOT for publication as Mamba-LSTM result."
        ),
        "n_cell_types_with_shift": len(shift_df),
    }

    logger.warning("Pseudotime fallback used for dynamic modeling — tag in all outputs.")
    return {
        "trajectory_shift": shift_df.to_dict("records") if not shift_df.empty else [],
        "state_transition_summary": metadata,
    }, metadata
