"""Annotation evaluation metrics: accuracy, F1, confidence calibration."""

import logging
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger("scagent_dpm.annotation.metrics")


def evaluate_annotation(
    true_labels: pd.Series,
    pred_labels: pd.Series,
    confidence: pd.Series = None,
) -> Dict:
    """Compute annotation performance metrics.

    If true_labels are not available (e.g., unlabeled data), returns empty metrics.
    """
    le = LabelEncoder()
    y_true = le.fit_transform(true_labels.astype(str))
    y_pred = le.transform(pred_labels.astype(str))

    metrics = {
        "n_cells": len(y_true),
        "n_classes": len(le.classes_),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }

    if confidence is not None:
        metrics["mean_confidence"] = float(confidence.mean())
        metrics["median_confidence"] = float(confidence.median())

        # Confidence calibration: mean confidence for correct vs incorrect
        correct = (y_true == y_pred)
        metrics["confidence_correct_mean"] = float(confidence[correct].mean()) if correct.any() else 0.0
        metrics["confidence_incorrect_mean"] = float(confidence[~correct].mean()) if (~correct).any() else 0.0

    return metrics
