"""Tests for the v0.7 interpretability explanation utilities and frozen spec.

Covers the frozen ExplanationFamilySpec vocabulary (mirrors the graph feature-
family guard tests) and the deterministic explainers: feature-importance
extraction and partial-dependence / ICE grid construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from banking_fraud_lab import (
    EXPLANATION_FAMILY_IDS,
    EXPLANATION_FAMILY_SPECS,
    ExplanationFamilySpec,
    build_partial_dependence_grid,
    explain_feature_family,
    extract_feature_importance,
)
from banking_fraud_lab.interpretability import (
    PATTERN_TO_EXPLANATION_FAMILY,
    PB_HIGH_VALUE_EXPLANATION,
)
from banking_fraud_lab.schema import PATTERN_IDS


# --- Frozen-spec vocabulary -------------------------------------------------


def test_explanation_family_specs_are_frozen_dataclasses() -> None:
    """Each ExplanationFamilySpec must be a frozen dataclass instance."""
    for spec in EXPLANATION_FAMILY_SPECS:
        assert isinstance(spec, ExplanationFamilySpec)
        with pytest.raises((AttributeError, TypeError)):
            spec.family_id = "mutated"  # type: ignore[misc]  # frozen contract


def test_explanation_family_ids_are_unique_and_stable() -> None:
    """The explanation family ids must be unique and ordered."""
    assert len(EXPLANATION_FAMILY_IDS) == len(set(EXPLANATION_FAMILY_IDS))
    assert EXPLANATION_FAMILY_IDS == tuple(s.family_id for s in EXPLANATION_FAMILY_SPECS)


def test_explanation_families_reference_known_patterns() -> None:
    """Every explanation family must reference a Detection pattern in the registry."""
    ids = set(PATTERN_IDS)
    for spec in EXPLANATION_FAMILY_SPECS:
        assert spec.detection_pattern_id in ids, (
            f"{spec.family_id} references unknown pattern {spec.detection_pattern_id}"
        )


def test_explanation_families_cover_both_tracks() -> None:
    """The vocabulary must cover private-banking and digital-banking tracks."""
    tracks = {spec.track for spec in EXPLANATION_FAMILY_SPECS}
    assert tracks == {"private_banking", "digital_banking"}


def test_pattern_to_explanation_family_lookup_is_complete() -> None:
    """Each family's Detection pattern must map back to that family."""
    for spec in EXPLANATION_FAMILY_SPECS:
        assert PATTERN_TO_EXPLANATION_FAMILY[spec.detection_pattern_id] is spec


def test_explanation_feature_columns_match_feature_family_outputs() -> None:
    """Explanation feature columns must be real model inputs (subset of feature specs)."""
    from banking_fraud_lab import PRIVATE_BANKING_FEATURE_FAMILIES, DIGITAL_BANKING_FEATURE_FAMILIES

    all_outputs = {
        column
        for family in (
            *PRIVATE_BANKING_FEATURE_FAMILIES,
            *DIGITAL_BANKING_FEATURE_FAMILIES,
        )
        for column in family.output_columns
    }
    for spec in EXPLANATION_FAMILY_SPECS:
        for column in spec.feature_columns:
            assert column in all_outputs, (
                f"{spec.family_id} feature {column!r} is not a model input column"
            )


# --- Deterministic test fixtures -------------------------------------------


@pytest.fixture
def linear_model_frame() -> tuple[LogisticRegression, pd.DataFrame, list[str]]:
    """A fitted linear model on a tiny deterministic feature frame."""
    rng = np.random.default_rng(42)
    columns = ["amount_to_aum_ratio", "is_cross_border", "is_new_counterparty"]
    n = 80
    frame = pd.DataFrame(
        {
            "amount_to_aum_ratio": rng.uniform(0.0, 5.0, n),
            "is_cross_border": rng.integers(0, 2, n).astype(float),
            "is_new_counterparty": rng.integers(0, 2, n).astype(float),
        }
    )
    labels = (
        frame["amount_to_aum_ratio"] * 0.6
        + frame["is_new_counterparty"] * 0.8
        > 2.0
    ).astype(int)
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(frame.to_numpy(), labels)
    return model, frame, columns


@pytest.fixture
def tree_model_frame() -> tuple[DecisionTreeClassifier, pd.DataFrame, list[str]]:
    """A fitted tree model exposing feature_importances_."""
    rng = np.random.default_rng(7)
    columns = ["db_session_payment_count", "db_asn_risk_score", "db_account_age_days"]
    n = 60
    frame = pd.DataFrame(
        {
            "db_session_payment_count": rng.integers(1, 10, n).astype(float),
            "db_asn_risk_score": rng.uniform(0.0, 1.0, n),
            "db_account_age_days": rng.integers(1, 400, n).astype(float),
        }
    )
    labels = (frame["db_session_payment_count"] >= 5).astype(int)
    model = DecisionTreeClassifier(random_state=7)
    model.fit(frame.to_numpy(), labels)
    return model, frame, columns


# --- Feature importance extraction -----------------------------------------


def test_extract_feature_importance_linear_shapes_and_fields(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """Linear-model importance must be one row per feature, L1-normalised."""
    model, _, columns = linear_model_frame
    result = extract_feature_importance(model, columns)
    assert list(result.columns) == [
        "feature",
        "native_importance",
        "detection_pattern_id",
        "explanation_family_id",
    ]
    assert len(result) == len(columns)
    assert set(result["feature"]) == set(columns)
    assert pytest.approx(float(result["native_importance"].sum()), abs=1e-6) == 1.0
    # Sorted descending by native importance.
    assert list(result["native_importance"]) == sorted(
        result["native_importance"], reverse=True
    )


def test_extract_feature_importance_is_deterministic(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """The same model + columns must produce identical importance on every call."""
    model, _, columns = linear_model_frame
    first = extract_feature_importance(model, columns)
    second = extract_feature_importance(model, columns)
    pd.testing.assert_frame_equal(first, second)


def test_extract_feature_importance_tree_uses_feature_importances(
    tree_model_frame: tuple[DecisionTreeClassifier, pd.DataFrame, list[str]],
) -> None:
    """Tree-model importance must come from feature_importances_ and be L1-normalised."""
    model, _, columns = tree_model_frame
    result = extract_feature_importance(model, columns)
    expected = np.abs(model.feature_importances_)
    expected = expected / expected.sum()
    by_feature = result.set_index("feature")["native_importance"]
    for index, column in enumerate(columns):
        assert pytest.approx(float(by_feature[column]), abs=1e-6) == float(expected[index])


def test_extract_feature_importance_with_permutation_column(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """Passing a feature frame must add a permutation-importance column."""
    model, frame, columns = linear_model_frame
    result = extract_feature_importance(model, columns, feature_frame=frame)
    assert "permutation_importance" in result.columns
    assert pytest.approx(float(result["permutation_importance"].sum()), abs=1e-6) == 1.0
    assert (result["permutation_importance"] >= 0).all()


def test_extract_feature_importance_pattern_tagging(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """Passing a Detection pattern id tags every row with its family."""
    model, _, columns = linear_model_frame
    result = extract_feature_importance(
        model, columns, detection_pattern_id="pb_high_value_movement"
    )
    assert (result["detection_pattern_id"] == "pb_high_value_movement").all()
    assert (
        result["explanation_family_id"]
        == "explanation_pb_high_value_movement"
    ).all()


def test_extract_feature_importance_rejects_empty_columns(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """An empty feature list must raise a clear error."""
    model, _, _ = linear_model_frame
    with pytest.raises(ValueError, match="at least one feature"):
        extract_feature_importance(model, [])


def test_extract_feature_importance_rejects_unknown_pattern(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """An unknown Detection pattern id must raise a clear error."""
    model, _, columns = linear_model_frame
    with pytest.raises(ValueError, match="no explanation family"):
        extract_feature_importance(model, columns, detection_pattern_id="not_a_pattern")


def test_extract_feature_importance_rejects_width_mismatch(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """A feature list whose width differs from the model must raise."""
    model, _, _ = linear_model_frame
    with pytest.raises(ValueError, match="does not match"):
        extract_feature_importance(model, ["amount_to_aum_ratio"])


def test_extract_feature_importance_falls_back_to_permutation(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """A predict_proba-only model with a feature frame must use permutation importance.

    Models that expose neither ``coef_`` nor ``feature_importances_`` must not
    crash when a feature frame is supplied: the native-importance column falls
    back to the permutation values, keeping the extractor model-agnostic.
    """
    _, frame, columns = linear_model_frame

    class ProbaOnlyModel:
        """A minimal estimator exposing predict_proba but no native importance."""

        def predict_proba(self, x: np.ndarray) -> np.ndarray:
            # Deterministic score: higher when the first feature is large.
            score = 1.0 / (1.0 + np.exp(-(x[:, 0] - 2.5)))
            return np.column_stack([1.0 - score, score])

    result = extract_feature_importance(ProbaOnlyModel(), columns, feature_frame=frame)
    assert "permutation_importance" in result.columns
    # Native column falls back to permutation values for this model.
    np.testing.assert_allclose(
        result["native_importance"].to_numpy(),
        result["permutation_importance"].to_numpy(),
        atol=1e-6,
    )
    assert pytest.approx(float(result["native_importance"].sum()), abs=1e-6) == 1.0


def test_extract_feature_importance_rejects_proba_only_without_frame() -> None:
    """A predict_proba-only model without a feature frame must raise."""

    class ProbaOnlyModel:
        def predict_proba(self, x: np.ndarray) -> np.ndarray:
            return np.column_stack([np.ones(len(x)), np.zeros(len(x))])

    with pytest.raises(ValueError, match="feature_frame to use permutation"):
        extract_feature_importance(ProbaOnlyModel(), ["a", "b"])


# --- Partial-dependence grid -----------------------------------------------


def test_partial_dependence_grid_shape_and_ordering(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """The grid must be sorted ascending by grid_value and carry tag columns."""
    model, frame, _ = linear_model_frame
    grid = build_partial_dependence_grid(
        model, frame, "amount_to_aum_ratio", grid_points=5
    )
    expected_columns = {
        "grid_value",
        "mean_score",
        "ice_spread",
        "detection_pattern_id",
        "explanation_family_id",
    }
    assert expected_columns <= set(grid.columns)
    assert list(grid["grid_value"]) == sorted(grid["grid_value"])
    # Mean scores are valid probabilities in [0, 1].
    assert grid["mean_score"].between(0.0, 1.0).all()


def test_partial_dependence_grid_is_deterministic(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """The same inputs must produce an identical grid on every call."""
    model, frame, _ = linear_model_frame
    first = build_partial_dependence_grid(model, frame, "amount_to_aum_ratio", grid_points=7)
    second = build_partial_dependence_grid(model, frame, "amount_to_aum_ratio", grid_points=7)
    pd.testing.assert_frame_equal(first, second)


def test_partial_dependence_grid_tolerance_bounded(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """Grid values must be rounded to stable precision (tolerance-bounded)."""
    model, frame, _ = linear_model_frame
    grid = build_partial_dependence_grid(model, frame, "amount_to_aum_ratio")
    for column in ("grid_value", "mean_score", "ice_spread"):
        # Rounded to 6 decimals means at most 6 places after the point.
        assert (grid[column].round(6) == grid[column]).all()


def test_partial_dependence_grid_tagging(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """The grid must carry the Detection pattern tag on every row."""
    model, frame, _ = linear_model_frame
    grid = build_partial_dependence_grid(
        model, frame, "amount_to_aum_ratio", detection_pattern_id="pb_high_value_movement"
    )
    assert (grid["detection_pattern_id"] == "pb_high_value_movement").all()


def test_partial_dependence_grid_rejects_missing_column(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """A missing feature column must raise a clear error."""
    model, frame, _ = linear_model_frame
    with pytest.raises(ValueError, match="missing feature column"):
        build_partial_dependence_grid(model, frame, "no_such_column")


def test_partial_dependence_grid_rejects_constant_grid_points(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """Fewer than 2 grid points must raise."""
    model, frame, _ = linear_model_frame
    with pytest.raises(ValueError, match="at least 2"):
        build_partial_dependence_grid(model, frame, "amount_to_aum_ratio", grid_points=1)


def test_partial_dependence_grid_handles_constant_feature(
    linear_model_frame: tuple[LogisticRegression, pd.DataFrame, list[str]],
) -> None:
    """A constant feature must degrade to a single-point grid, not crash."""
    model, frame, _ = linear_model_frame
    constant_frame = frame.assign(is_cross_border=1.0)
    grid = build_partial_dependence_grid(model, constant_frame, "is_cross_border")
    assert len(grid) == 1


# --- End-to-end family explainer -------------------------------------------


def test_explain_feature_family_returns_importance_and_grid() -> None:
    """explain_feature_family must return the importance table and a top-feature grid."""
    spec = PB_HIGH_VALUE_EXPLANATION
    # Build a frame whose columns include the family's feature_columns.
    rng = np.random.default_rng(1)
    family_frame = pd.DataFrame(
        {
            "amount_to_aum_ratio": rng.uniform(0.0, 5.0, 50),
            "amount_to_relationship_baseline_ratio": rng.uniform(0.0, 4.0, 50),
            "is_cross_border": rng.integers(0, 2, 50).astype(float),
        }
    )
    labels = (family_frame["amount_to_aum_ratio"] > 3.0).astype(int)
    family_model = DecisionTreeClassifier(random_state=1).fit(
        family_frame.to_numpy(), labels
    )
    result = explain_feature_family(family_model, family_frame, spec, grid_points=5)
    assert result["family_id"] == spec.family_id
    assert result["detection_pattern_id"] == spec.detection_pattern_id
    assert isinstance(result["feature_importance"], pd.DataFrame)
    assert isinstance(result["top_feature_grid"], pd.DataFrame)
    assert set(result["feature_importance"]["feature"]) == set(spec.feature_columns)
    assert len(result["top_feature_grid"]) >= 1


def test_explain_feature_family_ignores_extra_columns() -> None:
    """A feature frame with extra columns must not break scoring (projected down)."""
    spec = PB_HIGH_VALUE_EXPLANATION
    rng = np.random.default_rng(2)
    family_frame = pd.DataFrame(
        {
            "amount_to_aum_ratio": rng.uniform(0.0, 5.0, 40),
            "amount_to_relationship_baseline_ratio": rng.uniform(0.0, 4.0, 40),
            "is_cross_border": rng.integers(0, 2, 40).astype(float),
            # An unrelated column the model was NOT trained on.
            "unrelated_telemetry": rng.uniform(0.0, 100.0, 40),
        }
    )
    labels = (family_frame["amount_to_aum_ratio"] > 3.0).astype(int)
    family_model = DecisionTreeClassifier(random_state=2).fit(
        family_frame[list(spec.feature_columns)].to_numpy(), labels
    )
    result = explain_feature_family(family_model, family_frame, spec, grid_points=5)
    assert set(result["feature_importance"]["feature"]) == set(spec.feature_columns)
    assert len(result["top_feature_grid"]) >= 1


# --- Pipeline-with-ColumnTransformer regression ----------------------------


def test_partial_dependence_grid_supports_pipeline_with_column_transformer() -> None:
    """A Pipeline(ColumnTransformer) fit on a named-column DataFrame must score.

    Regression: the partial-dependence grid used to convert the frame to numpy,
    which broke ColumnTransformer's name-based column selection. The grid must
    pass the DataFrame through when the model was fit on named columns.
    """
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    rng = np.random.default_rng(11)
    frame = pd.DataFrame(
        {
            "amount_to_aum_ratio": rng.uniform(0.0, 5.0, 60),
            "is_cross_border": rng.integers(0, 2, 60).astype(float),
            "is_new_counterparty": rng.integers(0, 2, 60).astype(float),
        }
    )
    labels = (frame["amount_to_aum_ratio"] > 3.0).astype(int)
    columns = list(frame.columns)
    model = Pipeline(
        [
            ("preprocess", ColumnTransformer([("numeric", StandardScaler(), columns)])),
            ("model", LogisticRegression(random_state=11, max_iter=1000)),
        ]
    )
    model.fit(frame, labels)
    grid = build_partial_dependence_grid(model, frame, "amount_to_aum_ratio", grid_points=5)
    assert len(grid) >= 1
    assert grid["mean_score"].between(0.0, 1.0).all()


def test_extract_feature_importance_supports_pipeline_with_column_transformer() -> None:
    """Permutation importance must also score a Pipeline(ColumnTransformer)."""
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    rng = np.random.default_rng(12)
    frame = pd.DataFrame(
        {
            "amount_to_aum_ratio": rng.uniform(0.0, 5.0, 60),
            "is_cross_border": rng.integers(0, 2, 60).astype(float),
        }
    )
    labels = (frame["amount_to_aum_ratio"] > 3.0).astype(int)
    columns = list(frame.columns)
    model = Pipeline(
        [
            ("preprocess", ColumnTransformer([("numeric", StandardScaler(), columns)])),
            ("model", LogisticRegression(random_state=12, max_iter=1000)),
        ]
    )
    model.fit(frame, labels)
    result = extract_feature_importance(model, columns, feature_frame=frame)
    assert "permutation_importance" in result.columns
    assert len(result) == len(columns)
