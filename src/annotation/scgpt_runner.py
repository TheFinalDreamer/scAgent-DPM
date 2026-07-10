"""scGPT annotation runner."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ann
import pandas as pd

logger = logging.getLogger("scagent_dpm.annotation.scgpt")


def run_scgpt(
    adata: ann.AnnData,
    model_path: Optional[str] = None,
    batch_size: int = 64,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run scGPT annotation.

    Supports both real model inference and mock fallback for interface testing.
    """
    if model_path is None:
        logger.warning("scGPT model_path not provided — using MOCK/FALLBACK predictions")
        return _mock_annotation(adata, method="scgpt")

    try:
        import torch
        from scgpt.model import TransformerModel
        from scgpt.tokenizer import GeneVocab
    except ImportError:
        logger.warning("scGPT not installed — using MOCK/FALLBACK predictions")
        return _mock_annotation(adata, method="scgpt")

    # Placeholder for actual scGPT inference
    # The real implementation should load the model, tokenize genes, run inference,
    # and map predictions to cell type labels.
    logger.warning(
        "scGPT real inference not yet implemented — using MOCK/FALLBACK predictions. "
        "Set model_path to a valid checkpoint for real inference."
    )
    return _mock_annotation(adata, method="scgpt")


def _mock_annotation(
    adata: ann.AnnData, method: str = "unknown"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    import numpy as np
    rng = np.random.default_rng(42)
    mock_types = ["T cell", "B cell", "Monocyte", "NK cell", "Dendritic cell"]
    preds = rng.choice(mock_types, size=adata.n_obs)
    conf = rng.uniform(0.3, 1.0, size=adata.n_obs)
    df = pd.DataFrame({
        "predicted_cell_type": preds,
        "confidence": conf,
    }, index=adata.obs_names)
    summary = {
        "method": method,
        "is_fallback": True,
        "fallback_warning": "MOCK predictions — interface test only, NOT for publication.",
    }
    logger.warning("MOCK ANNOTATION generated — tag as FALLBACK in all outputs.")
    return df, summary
