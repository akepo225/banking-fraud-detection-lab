"""Tests for private-banking feature-family metadata and calculations."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from banking_fraud_lab import (
    build_private_banking_features,
    calculate_amount_to_aum_features,
    calculate_amount_to_baseline_features,
    calculate_cross_border_features,
    calculate_new_counterparty_features,
    calculate_off_hours_features,
    calculate_rm_concentration_features,
    calculate_velocity_features,
    generate_private_banking_transaction_fraud_world,
)
from banking_fraud_lab.features import (
    AMOUNT_TO_AUM,
    AMOUNT_TO_RELATIONSHIP_BASELINE,
    CROSS_BORDER_MOVEMENT,
    FEATURE_FAMILY_IDS,
    NEW_COUNTERPARTY,
    OFF_HOURS_ACTIVITY,
    PRIVATE_BANKING_FEATURE_FAMILIES,
    RM_CONCENTRATION,
    VELOCITY_CHANGE,
    FeatureFamilySpec,
)
from banking_fraud_lab.generators.private_banking import (
    PRIVATE_BANKING_FALSE_POSITIVE_TYPE,
    PRIVATE_BANKING_SCENARIO_NAME,
)
from banking_fraud_lab.schema import (
    PATTERN_IDS,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    TRANSACTIONS,
)

ALPINE_CREST = "Alpine Crest Private Bank"


def test_private_banking_feature_specs_are_pattern_linked() -> None:
    """Feature-family metadata should be complete and tied to Detection patterns."""
    assert len(PRIVATE_BANKING_FEATURE_FAMILIES) == 7
    assert len(FEATURE_FAMILY_IDS) == len(set(FEATURE_FAMILY_IDS))
    assert all(isinstance(spec, FeatureFamilySpec) for spec in PRIVATE_BANKING_FEATURE_FAMILIES)

    for spec in PRIVATE_BANKING_FEATURE_FAMILIES:
        assert spec.family_id
        assert spec.display_name
        assert spec.description
        assert spec.detection_pattern_id in PATTERN_IDS
        assert spec.source_tables
        assert spec.source_columns
        assert spec.output_columns
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in spec.source_tables


def test_private_banking_feature_calculators_return_spec_outputs() -> None:
    """Every calculator should return the columns promised by its feature spec."""
    tables = generate_private_banking_transaction_fraud_world(seed=42, scenario_prevalence=0.2)
    outputs = {
        AMOUNT_TO_AUM.family_id: calculate_amount_to_aum_features(
            tables["transactions"],
            tables["accounts"],
            tables["banking_relationships"],
        ),
        AMOUNT_TO_RELATIONSHIP_BASELINE.family_id: calculate_amount_to_baseline_features(
            tables["transactions"],
            tables["accounts"],
            tables["banking_relationships"],
        ),
        NEW_COUNTERPARTY.family_id: calculate_new_counterparty_features(
            tables["transactions"],
            tables["payment_beneficiaries"],
        ),
        OFF_HOURS_ACTIVITY.family_id: calculate_off_hours_features(tables["transactions"]),
        CROSS_BORDER_MOVEMENT.family_id: calculate_cross_border_features(
            tables["transactions"],
            tables["accounts"],
            tables["banking_relationships"],
            tables["clients"],
            tables["partners"],
            tables["payment_beneficiaries"],
        ),
        VELOCITY_CHANGE.family_id: calculate_velocity_features(
            tables["transactions"],
            tables["accounts"],
            tables["banking_relationships"],
        ),
        RM_CONCENTRATION.family_id: calculate_rm_concentration_features(
            tables["alerts"],
            tables["cases"],
            tables["banking_relationships"],
        ),
    }

    for spec in PRIVATE_BANKING_FEATURE_FAMILIES:
        output = outputs[spec.family_id]
        assert set(spec.output_columns) <= set(output.columns)
        assert not output.empty
        assert output.loc[:, spec.output_columns].notna().all().all()


def test_build_private_banking_features_returns_merged_alpine_crest_frame() -> None:
    """The convenience builder should expose all feature columns for Alpine Crest."""
    tables = generate_private_banking_transaction_fraud_world(seed=42, scenario_prevalence=0.2)
    features = build_private_banking_features(tables)
    expected_output_columns = {
        output_column
        for spec in PRIVATE_BANKING_FEATURE_FAMILIES
        for output_column in spec.output_columns
    }

    assert expected_output_columns <= set(features.columns)
    assert set(features["institution_name"]) == {ALPINE_CREST}
    assert features["transaction_id"].is_unique
    assert features.loc[:, sorted(expected_output_columns)].notna().all().all()
    assert (features["amount_to_aum_ratio"] > 0).any()
    assert (features["relationship_txn_count_30d"] >= features["relationship_txn_count_7d"]).all()


def test_feature_calculations_handle_zero_aum_and_no_prior_history() -> None:
    """Ratio features should avoid inf/nan on zero AUM and first transactions."""
    tables = generate_private_banking_transaction_fraud_world(seed=42, scenario_prevalence=0.2)
    relationships = tables["banking_relationships"].copy()
    relationships.loc[0, "aum_chf"] = 0

    aum_features = calculate_amount_to_aum_features(
        tables["transactions"],
        tables["accounts"],
        relationships,
    )
    baseline_features = calculate_amount_to_baseline_features(
        tables["transactions"].iloc[[0]].copy(),
        tables["accounts"],
        relationships,
    )

    assert np.isfinite(aum_features["amount_to_aum_ratio"]).all()
    assert np.isfinite(baseline_features["amount_to_relationship_baseline_ratio"]).all()
    assert baseline_features["relationship_amount_baseline_chf"].notna().all()


def test_legitimate_private_banking_false_positives_have_feature_values() -> None:
    """False-positive cases should receive features without relying on answer keys."""
    tables = generate_private_banking_transaction_fraud_world(
        seed=42,
        scale="small",
        scenario_prevalence=0.2,
    )
    features = build_private_banking_features(tables)
    false_positive_alerts = tables["alerts"][
        (tables["alerts"]["institution_name"] == ALPINE_CREST)
        & (tables["alerts"]["alert_type"] == PRIVATE_BANKING_FALSE_POSITIVE_TYPE)
    ]
    false_positive_cases = tables["cases"][
        tables["cases"]["alert_id"].isin(false_positive_alerts["alert_id"])
    ]
    protected_private_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"]
        == PRIVATE_BANKING_SCENARIO_NAME
    ]
    false_positive_features = features[
        features["transaction_id"].isin(false_positive_cases["transaction_id"])
    ]

    assert not false_positive_features.empty
    assert false_positive_cases["transaction_id"].is_unique
    assert set(false_positive_cases["transaction_id"]).isdisjoint(
        set(protected_private_keys["entity_id"])
    )
    assert set(protected_private_keys["entity_table"]) == {TRANSACTIONS}
    assert false_positive_features["amount_to_aum_ratio"].gt(0).all()
    assert false_positive_features["amount_to_relationship_baseline_ratio"].ge(0).all()
    assert false_positive_features["rm_alert_share"].ge(0).all()
    assert false_positive_features["payment_beneficiary_id"].notna().any()


def test_feature_documentation_mentions_all_specs() -> None:
    """Feature docs should stay aligned with the metadata registry."""
    docs_path = Path("docs/schema/features.md")
    text = docs_path.read_text(encoding="utf-8")

    assert docs_path.exists()
    for spec in PRIVATE_BANKING_FEATURE_FAMILIES:
        assert spec.family_id in text
        assert spec.detection_pattern_id in text
        for output_column in spec.output_columns:
            assert output_column in text
