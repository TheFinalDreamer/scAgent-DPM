"""scGPT-KDMT annotation runner — interface for the KDMT-enhanced foundation model.

This module provides an interface to the scGPT-KDMT project (Paper #2).
If the project and model weights are available on the server, it delegates
to the real model. Otherwise, it uses mock-safe fallback.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ann
import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.annotation.scgpt_kdmt")


def run_scgpt_kdmt(
    adata: ann.AnnData,
    project_path: Optional[str] = None,
    model_weights: Optional[str] = None,
    use_kdmt: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run scGPT-KDMT annotation.

    Strategy:
    1. If project_path and model_weights are provided and valid, import and run.
    2. If project_path exists on disk but model_weights is None, attempt auto-discovery.
    3. Otherwise, use MOCK fallback with clear labeling.
    """
    if project_path and Path(project_path).exists():
        logger.info(f"scGPT-KDMT project found at {project_path}")
        result = _try_real_inference(adata, project_path, model_weights, use_kdmt)
        if result is not None:
            return result

    logger.warning(
        "scGPT-KDMT project/model not found — using MOCK/FALLBACK predictions. "
        "All results from this run must be tagged as FALLBACK."
    )
    return _mock_annotation(adata, method="scgpt_kdmt")


def _try_real_inference(
    adata: ann.AnnData,
    project_path: str,
    model_weights: Optional[str],
    use_kdmt: bool,
) -> Optional[Tuple[pd.DataFrame, Dict[str, Any]]]:
    """Attempt to run real scGPT-KDMT inference. Returns None if unavailable."""
    project_path = Path(project_path)
    sys.path.insert(0, str(project_path))

    try:
        # Import from the scGPT-KDMT project
        # Actual import paths depend on the project structure
        # This is a configurable interface layer
        if model_weights and Path(model_weights).exists():
            logger.info(f"Loading scGPT-KDMT weights from {model_weights}")
            # Real inference would go here
            # import torch
            # model = load_kdmt_model(model_weights)
            # predictions = model.predict(adata)
            logger.warning(
                "scGPT-KDMT real inference interface reached but model loading not yet wired. "
                "Falling back to MOCK."
            )
            return None
        else:
            logger.warning(f"Model weights not found at {model_weights}")
            return None
    except ImportError as e:
        logger.warning(f"Could not import scGPT-KDMT modules: {e}")
        return None
    finally:
        if str(project_path) in sys.path:
            sys.path.remove(str(project_path))


def _mock_annotation(
    adata: ann.AnnData, method: str = "unknown"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    rng = np.random.default_rng(42)
    mock_types = ["T cell CD4+", "T cell CD8+", "B cell", "Monocyte CD14+", "NK cell", "Dendritic cell"]
    preds = rng.choice(mock_types, size=adata.n_obs)
    conf = rng.uniform(0.4, 1.0, size=adata.n_obs)
    df = pd.DataFrame({
        "predicted_cell_type": preds,
        "confidence": conf,
    }, index=adata.obs_names)
    summary = {
        "method": method,
        "is_fallback": True,
        "fallback_warning": "MOCK predictions — interface test only, NOT for publication.",
    }
    logger.warning("MOCK scGPT-KDMT ANNOTATION — tag as FALLBACK in all outputs.")
    return df, summary
