"""Optional SHAP explainability path (non-core, optional extra).

This module is deliberately **optional**. It wraps :mod:`shap` to provide a
common-tooling view of model explanations for a fitted fraud-detection model,
without making SHAP mandatory for the curriculum or CI.

``shap`` is an optional dependency declared behind the ``shap`` extra in
``pyproject.toml``. ``uv sync --extra dev`` and CI do NOT install it. The
:func:`shap` import is guarded so ``import banking_fraud_lab.interpretability``
succeeds when ``shap`` is absent. The optional :func:`explain_with_shap` helper
degrades gracefully (raising a clear :class:`RuntimeError` with install
guidance) when ``shap`` is not installed.

Mirrors the v0.6 Neo4j optional-extra precedent
(:mod:`banking_fraud_lab.graph.export_neo4j`).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

SHAP_AVAILABLE = False
try:  # pragma: no cover - exercised only when the optional shap package is installed
    import shap  # type: ignore[import-not-found]

    SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover - the default environment lacks shap
    shap = None  # type: ignore[assignment]


def explain_with_shap(
    model: Any,
    feature_frame: pd.DataFrame,
    feature_columns: list[str],
    *,
    detection_pattern_id: str | None = None,
) -> pd.DataFrame:
    """Compute a deterministic, tolerance-bounded SHAP explanation for a fitted model.

    Returns a DataFrame with one row per feature, the mean absolute SHAP value
    per feature (L1-normalised so it is comparable to the native/permutation
    importance from :mod:`banking_fraud_lab.interpretability.explanations`),
    plus the ``detection_pattern_id`` tag column when supplied.

    Args:
        model: A fitted classifier or Pipeline exposing ``predict_proba``.
        feature_frame: The DataFrame the model was scored on.
        feature_columns: The feature columns to explain.
        detection_pattern_id: Optional Detection pattern id tag.

    Returns:
        A DataFrame sorted by descending ``mean_abs_shap`` with columns
        ``feature``, ``mean_abs_shap``, ``detection_pattern_id``.

    Raises:
        RuntimeError: When the optional ``shap`` extra is not installed. The
            error carries install guidance so a learner can opt in deliberately.
    """
    if not SHAP_AVAILABLE:
        raise RuntimeError(
            "The 'shap' optional extra is not installed. Install it with "
            "`uv sync --extra shap` (or `pip install banking-fraud-detection-lab[shap]`) "
            "to use SHAP explanations. SHAP is intentionally optional and is not "
            "installed by `uv sync --extra dev` or required by CI."
        )
    if not feature_columns:
        raise ValueError("feature_columns must contain at least one feature name")

    family_frame = feature_frame.loc[:, feature_columns]
    # shap.Explainer dispatches to Linear/Tree/GradientExplainer based on the model.
    explainer = shap.Explainer(model, family_frame)  # type: ignore[union-attr]
    # Modern SHAP API: call the explainer to get an Explanation, then read .values.
    explanation = explainer(family_frame)  # type: ignore[operator]
    shap_values = getattr(explanation, "values", explanation)
    mean_abs = np.mean(np.abs(_positive_class_values(shap_values)), axis=0)
    total = float(np.sum(mean_abs))
    normalised = mean_abs / total if total > 0 else mean_abs

    result = pd.DataFrame(
        {
            "feature": feature_columns,
            "mean_abs_shap": np.round(normalised, decimals=6),
        }
    )
    result["detection_pattern_id"] = detection_pattern_id or ""
    return result.sort_values(
        ["mean_abs_shap", "feature"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)


def _positive_class_values(shap_values: Any) -> np.ndarray:
    """Return the positive-class SHAP slice for binary classifiers.

    Accepts a numpy array, a list/tuple of per-class arrays (older SHAP API), or
    an object with a ``.values`` attribute (the modern Explanation object).
    ``shap`` returns either a 2-d array (n_samples, n_features) for single-output
    models, or a 3-d / list form for multi-class. For a binary classifier we want
    the positive-class (index 1) contribution.
    """
    # Modern Explanation objects expose .values; normalise to an ndarray first so
    # the list/tuple branch below is actually reachable for the older API.
    values = getattr(shap_values, "values", shap_values)
    if isinstance(values, (list, tuple)) and len(values) == 2:
        return np.asarray(values[1])
    array = np.asarray(values)
    if array.ndim == 3:
        # (n_samples, n_features, n_classes) or (n_classes, n_samples, n_features).
        if array.shape[-1] == 2:
            return array[..., 1]
        if array.shape[0] == 2:
            return array[1]
        return array[..., -1]
    return array


__all__ = ["SHAP_AVAILABLE", "explain_with_shap"]
