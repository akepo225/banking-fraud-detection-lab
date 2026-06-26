"""Deterministic interpretability utilities for fitted fraud-detection models.

Provides two reusable, deterministic explainers that turn a fitted scikit-learn
estimator into inspectable per-feature and per-grid explanations, each tied to a
**Detection pattern** id via the frozen
:mod:`banking_fraud_lab.interpretability.spec` vocabulary.

The explainers are designed for the model surface used across the v0.3/v0.4
supervised-baseline notebooks: a :class:`sklearn.pipeline.Pipeline` whose final
step is a fitted classifier (linear model with ``coef_`` or tree ensemble with
``feature_importances_``), trained on the numeric feature columns produced by
:mod:`banking_fraud_lab.features`.

Outputs are deliberately deterministic or tolerance-bounded (rounded to stable
precision) so the learner notebooks and the test suite are reproducible.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from banking_fraud_lab.interpretability.spec import (
    EXPLANATION_FAMILY_SPECS,
    ExplanationFamilySpec,
    PATTERN_TO_EXPLANATION_FAMILY,
)

# Number of decimals used to round importance and partial-dependence values so
# the same model + data always produces the same explanation output across runs.
_IMPORTANCE_PRECISION = 6
_GRID_PRECISION = 6
# Default partial-dependence grid resolution (number of quantile points).
_DEFAULT_GRID_POINTS = 11
# Lower bound on how many distinct grid points a feature must have to produce a
# partial-dependence curve (constant features fall back to their single value).
_MIN_VARYING_GRID_POINTS = 2


def extract_feature_importance(
    model: Any,
    feature_columns: Sequence[str],
    *,
    feature_frame: pd.DataFrame | None = None,
    detection_pattern_id: str | None = None,
) -> pd.DataFrame:
    """Extract deterministic per-feature importance from a fitted model.

    Supports the two estimator surfaces used across the v0.3/v0.4 baselines:

    * a fitted :class:`sklearn.pipeline.Pipeline` whose final estimator exposes
      either ``coef_`` (linear models, e.g. ``LogisticRegression``) or
      ``feature_importances_`` (tree ensembles); and
    * a bare fitted classifier exposing either of those attributes.

    For linear models the importance is the absolute value of the coefficient
    (the magnitude of each feature's contribution to the positive-class score);
    for tree models it is the impurity-based importance directly. When a
    ``feature_frame`` is supplied, permutation-style importance is computed by
    measuring the score-delta when each feature column is shuffled, which works
    for any model that exposes ``predict_proba`` and keeps the output model-
    agnostic. Permutation and impurity/coefficient importances are each L1-
    normalised to sum to 1.0 so they are comparable across models and patterns.

    Args:
        model: A fitted classifier or Pipeline exposing ``coef_``,
            ``feature_importances_``, or (with ``feature_frame``) ``predict_proba``.
        feature_columns: The ordered feature column names the model was trained
            on. Must match the order the model expects.
        feature_frame: Optional DataFrame the model was scored on. When given,
            permutation importance is reported in the ``permutation_importance``
            column; for models with no native importance signal (neither
            ``coef_`` nor ``feature_importances_``) the native-importance column
            also falls back to the permutation values so the extractor stays
            model-agnostic.
        detection_pattern_id: Optional Detection pattern id from
            :data:`banking_fraud_lab.schema.PATTERN_IDS`. When provided, each row
            is tagged with it and its explanation family; when omitted the
            column is blank.

    Returns:
        A DataFrame with one row per feature, sorted by descending importance,
        with columns ``feature``, ``native_importance`` (and
        ``permutation_importance`` when a feature frame is given), plus
        ``detection_pattern_id`` and ``explanation_family_id`` tag columns.

    Raises:
        ValueError: If the model exposes no supported importance signal, if the
            feature columns do not match the model's expected width, or if the
            provided ``detection_pattern_id`` is not in the explanation
            vocabulary.
    """
    columns = list(feature_columns)
    if not columns:
        raise ValueError("feature_columns must contain at least one feature name")

    estimator = _final_estimator(model)
    has_native = hasattr(estimator, "feature_importances_") or hasattr(estimator, "coef_")
    if not has_native and feature_frame is None:
        raise ValueError(
            "model exposes neither 'feature_importances_' nor 'coef_'; pass a "
            "feature_frame to use permutation importance instead"
        )

    permutation = (
        _permutation_importance(model, feature_frame, columns)
        if feature_frame is not None
        else None
    )
    # When a model exposes no native importance, fall back to permutation so the
    # extractor stays model-agnostic rather than failing on predict_proba-only
    # estimators that supplied a feature frame.
    native = _native_importance(estimator, columns) if has_native else permutation

    result = pd.DataFrame(
        {
            "feature": columns,
            "native_importance": _round_series(native),
        }
    )

    if permutation is not None:
        result["permutation_importance"] = _round_series(permutation)

    pattern_id, family_id = _resolve_pattern_tags(detection_pattern_id)
    result["detection_pattern_id"] = pattern_id
    result["explanation_family_id"] = family_id

    # Stable sort: highest importance first, ties broken alphabetically by
    # feature name so the row order is deterministic.
    sort_columns = ["native_importance", "feature"]
    ascending = [False, True]
    if "permutation_importance" in result.columns:
        sort_columns = ["permutation_importance", "native_importance", "feature"]
        ascending = [False, False, True]
    return result.sort_values(sort_columns, ascending=ascending, kind="stable").reset_index(
        drop=True
    )


def build_partial_dependence_grid(
    model: Any,
    feature_frame: pd.DataFrame,
    feature_column: str,
    *,
    grid_points: int = _DEFAULT_GRID_POINTS,
    detection_pattern_id: str | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Build a deterministic partial-dependence / ICE-style explanation grid.

    For the requested ``feature_column`` the utility sweeps a quantile grid of
    that feature's own values and reports the average positive-class score the
    model assigns when that single column is held at each grid point (the
    partial-dependence mean) plus a per-row centred ICE contribution. This is a
    lightweight, dependency-free analogue of
    :class:`sklearn.inspection.PartialDependenceDisplay` that stays deterministic
    and tolerance-bounded so notebooks and tests are reproducible.

    Args:
        model: A fitted classifier or Pipeline exposing ``predict_proba``.
        feature_frame: The DataFrame the model was scored on. Must contain
            ``feature_column``.
        feature_column: The numeric feature column to sweep.
        grid_points: Number of quantile grid points to evaluate. Clamped to the
            number of distinct values when the feature is near-constant.
        detection_pattern_id: Optional Detection pattern id tag.
        random_state: Seed for any tie-breaking in grid construction (kept for a
            stable contract; the grid itself is quantile-based and deterministic).

    Returns:
        A DataFrame with columns ``grid_value`` (the swept feature value),
        ``mean_score`` (partial-dependence average positive-class score),
        ``ice_spread`` (max - min centred ICE contribution across rows), and the
        ``detection_pattern_id`` / ``explanation_family_id`` tag columns. One row
        per grid point, ordered by ascending ``grid_value``.

    Raises:
        ValueError: If the feature column is missing, non-numeric, or the model
            does not expose ``predict_proba``.
    """
    _require_predict_proba(model)
    if feature_column not in feature_frame.columns:
        raise ValueError(f"feature_frame is missing feature column: {feature_column!r}")
    # pd.to_numeric(errors="raise") guarantees a numeric dtype: any non-numeric
    # column raises here, so no redundant dtype check is needed afterwards.
    series = pd.to_numeric(feature_frame[feature_column], errors="raise")

    grid = _quantile_grid(series, grid_points)
    base_frame = feature_frame.copy()
    base_scores = _positive_scores(model, base_frame)

    rows: list[dict[str, float]] = []
    for value in grid:
        swept = base_frame.copy()
        swept[feature_column] = value
        scores = _positive_scores(model, swept)
        centred = scores - base_scores
        rows.append(
            {
                "grid_value": float(value),
                "mean_score": _round_value(float(np.mean(scores))),
                "ice_spread": _round_value(float(np.max(centred) - np.min(centred))),
            }
        )
    result = pd.DataFrame(rows)
    # Ensure deterministic ordering and dedupe near-equal grid values.
    result = (
        result.drop_duplicates(subset=["grid_value"])
        .sort_values("grid_value", kind="stable")
        .reset_index(drop=True)
    )

    pattern_id, family_id = _resolve_pattern_tags(detection_pattern_id)
    result["detection_pattern_id"] = pattern_id
    result["explanation_family_id"] = family_id
    # Reference random_state in a no-op so the contract is explicit even when the
    # quantile grid does not need randomness (preserves determinism guarantees).
    _ = int(random_state)
    return result


def explain_feature_family(
    model: Any,
    feature_frame: pd.DataFrame,
    spec: ExplanationFamilySpec,
    *,
    grid_points: int = _DEFAULT_GRID_POINTS,
    random_state: int = 42,
) -> dict[str, Any]:
    """Explain one Detection-pattern family end-to-end.

    Convenience wrapper that returns the feature-importance table for the
    family's columns plus a partial-dependence grid for its top feature (the
    highest-native-importance column), all tagged with the family's Detection
    pattern id. Lets a learner pass a fitted model and a feature frame and read
    off both the per-feature drivers and the top feature's marginal behaviour.

    Args:
        model: A fitted classifier or Pipeline.
        feature_frame: The scored DataFrame; must contain the family's feature
            columns.
        spec: The :class:`ExplanationFamilySpec` to explain.
        grid_points: Partial-dependence grid resolution for the top feature.
        random_state: Seed forwarded to the grid builder.

    Returns:
        A dict with keys ``family_id``, ``detection_pattern_id``,
        ``feature_importance`` (DataFrame), and ``top_feature_grid`` (DataFrame).
    """
    missing = [column for column in spec.feature_columns if column not in feature_frame.columns]
    if missing:
        raise ValueError(
            f"feature_frame is missing columns for family {spec.family_id!r}: {missing}"
        )
    # Project the frame down to the family's feature columns so the model is only
    # ever scored on the inputs it was trained on. Without this, a frame carrying
    # extra columns would pass the wrong-width array to ``predict_proba``.
    family_frame = feature_frame.loc[:, list(spec.feature_columns)].copy()
    importance = extract_feature_importance(
        model,
        spec.feature_columns,
        feature_frame=family_frame,
        detection_pattern_id=spec.detection_pattern_id,
    )
    # Select the top feature by NATIVE importance (not permutation importance)
    # so the partial-dependence grid always explains the model's own driver,
    # matching this wrapper's documented contract. Ties break alphabetically.
    native_ranked = importance.sort_values(
        ["native_importance", "feature"], ascending=[False, True], kind="stable"
    )
    top_feature = str(native_ranked.iloc[0]["feature"])
    grid = build_partial_dependence_grid(
        model,
        family_frame,
        top_feature,
        grid_points=grid_points,
        detection_pattern_id=spec.detection_pattern_id,
        random_state=random_state,
    )
    return {
        "family_id": spec.family_id,
        "detection_pattern_id": spec.detection_pattern_id,
        "feature_importance": importance,
        "top_feature_grid": grid,
    }


# --- Internal helpers ------------------------------------------------------


def _final_estimator(model: Any) -> Any:
    """Return the final estimator of a Pipeline, or the model itself."""
    if hasattr(model, "steps"):
        return model.steps[-1][1]
    return model


def _native_importance(estimator: Any, columns: Sequence[str]) -> np.ndarray:
    """Return L1-normalised native importance for linear or tree estimators."""
    importances: np.ndarray | None = None
    if hasattr(estimator, "feature_importances_"):
        importances = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_, dtype=float)
        # Binary classifiers expose a single-row coef_ (shape (1, n_features)),
        # flattened via ravel(); multiclass coef_ (>=2 rows) collapses to the
        # last class row.
        importances = np.abs(coef[-1] if coef.ndim == 2 and coef.shape[0] >= 2 else coef.ravel())
    if importances is None:
        raise ValueError(
            "model exposes neither 'feature_importances_' nor 'coef_'; pass a "
            "feature_frame to use permutation importance instead"
        )
    if len(importances) != len(columns):
        raise ValueError(
            f"model importance length {len(importances)} does not match "
            f"feature_columns length {len(columns)}"
        )
    return _l1_normalise(importances)


def _permutation_importance(
    model: Any, feature_frame: pd.DataFrame, columns: Sequence[str]
) -> np.ndarray:
    """Return L1-normalised permutation importance derived from score change."""
    _require_predict_proba(model)
    base = _positive_scores(model, feature_frame)
    rng = np.random.default_rng(42)
    importances = np.zeros(len(columns), dtype=float)
    for index, column in enumerate(columns):
        shuffled = feature_frame.copy()
        permutation = rng.permutation(len(shuffled))
        shuffled[column] = shuffled[column].to_numpy()[permutation]
        perturbed = _positive_scores(model, shuffled)
        # Use the mean absolute change in positive-class score as the importance.
        importances[index] = float(np.mean(np.abs(perturbed - base)))
    return _l1_normalise(importances)


def _positive_scores(model: Any, frame: pd.DataFrame) -> np.ndarray:
    """Return the positive-class probability vector from predict_proba.

    A Pipeline whose ColumnTransformer was fit on a named-column DataFrame
    selects columns by name and raises when given a bare numpy array, so the
    DataFrame is passed directly when the model signals it was fit on named
    columns (``feature_names_in_`` or a Pipeline wrapping such a transformer).
    Bare estimators fit on numpy receive a numpy array instead.
    """
    array_like = frame.to_numpy() if not _expects_named_columns(model) else frame
    scores = model.predict_proba(array_like)
    if scores.ndim != 2 or scores.shape[1] < 2:
        raise ValueError("model.predict_proba must return a 2-column probability array")
    return np.asarray(scores[:, 1], dtype=float)


def _expects_named_columns(model: Any) -> bool:
    """Return True when the model was fit on named columns and needs a DataFrame."""
    estimator = _final_estimator(model)
    # A Pipeline may wrap a ColumnTransformer that selects columns by name; its
    # final estimator (or the transformer) records feature_names_in_ in that case.
    if hasattr(model, "steps"):
        for _name, step in model.steps:
            if hasattr(step, "feature_names_in_"):
                return True
        return hasattr(estimator, "feature_names_in_")
    return hasattr(estimator, "feature_names_in_")


def _require_predict_proba(model: Any) -> None:
    """Raise a clear error when a model cannot score probabilities."""
    if not hasattr(model, "predict_proba"):
        raise ValueError("model must expose 'predict_proba' for partial-dependence")


def _quantile_grid(series: pd.Series, grid_points: int) -> np.ndarray:
    """Build a deterministic, de-duplicated quantile grid for a numeric series."""
    if grid_points < _MIN_VARYING_GRID_POINTS:
        raise ValueError("grid_points must be at least 2")
    distinct = series.dropna().unique()
    if len(distinct) < _MIN_VARYING_GRID_POINTS:
        # Constant feature: a single-point grid is the only meaningful output.
        return np.asarray([float(distinct[0])])
    resolved_points = min(int(grid_points), len(distinct))
    # linspace quantiles are deterministic and evenly spaced in probability, so
    # the grid is stable for the same input regardless of run.
    quantiles = np.linspace(0.0, 1.0, resolved_points)
    grid = np.quantile(series.dropna().to_numpy(dtype=float), quantiles)
    return np.unique(np.round(grid, decimals=_GRID_PRECISION))


def _resolve_pattern_tags(
    detection_pattern_id: str | None,
) -> tuple[str, str]:
    """Resolve a Detection pattern id to its tag pair (blank when None)."""
    if detection_pattern_id is None:
        return "", ""
    family = PATTERN_TO_EXPLANATION_FAMILY.get(detection_pattern_id)
    if family is None:
        known = ", ".join(sorted(PATTERN_TO_EXPLANATION_FAMILY))
        raise ValueError(
            f"detection_pattern_id {detection_pattern_id!r} has no explanation "
            f"family; known patterns: {known}"
        )
    return detection_pattern_id, family.family_id


def _l1_normalise(values: np.ndarray) -> np.ndarray:
    """L1-normalise a vector, returning zeros unchanged."""
    total = float(np.sum(np.abs(values)))
    if total <= 0.0:
        return np.zeros_like(values, dtype=float)
    return np.asarray(values, dtype=float) / total


def _round_value(value: float) -> float:
    """Round a single metric to stable notebook-friendly precision."""
    return round(float(value), _IMPORTANCE_PRECISION)


def _round_series(values: np.ndarray) -> np.ndarray:
    """Round a vector to stable notebook-friendly precision."""
    return np.round(np.asarray(values, dtype=float), decimals=_IMPORTANCE_PRECISION)


__all__ = [
    "EXPLANATION_FAMILY_SPECS",
    "ExplanationFamilySpec",
    "build_partial_dependence_grid",
    "explain_feature_family",
    "extract_feature_importance",
]
