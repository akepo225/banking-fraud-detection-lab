"""Tests for the Alpine Crest private-banking transaction-fraud scenario."""

from __future__ import annotations

import math

import pytest

from banking_fraud_lab import (
    build_learner_facing_views,
    generate_private_banking_transaction_fraud_world,
)
from banking_fraud_lab.generators.private_banking import (
    PRIVATE_BANKING_ACTIVITY_TYPE,
    PRIVATE_BANKING_SCENARIO_NAME,
)
from banking_fraud_lab.schema import PROTECTED_SCENARIO_ANSWER_KEYS, TRANSACTIONS

ALPINE_CREST = "Alpine Crest Private Bank"


def test_private_banking_scenario_prevalence_is_configurable() -> None:
    """Private-banking scenario labels should scale with requested prevalence."""
    low_prevalence_tables = generate_private_banking_transaction_fraud_world(
        seed=42,
        scenario_prevalence=0.1,
    )
    high_prevalence_tables = generate_private_banking_transaction_fraud_world(
        seed=42,
        scenario_prevalence=0.3,
    )
    private_transaction_count = _private_transaction_count(high_prevalence_tables)

    low_count = _scenario_answer_key_count(low_prevalence_tables)
    high_count = _scenario_answer_key_count(high_prevalence_tables)

    assert low_count == math.ceil(private_transaction_count * 0.1)
    assert high_count == math.ceil(private_transaction_count * 0.3)
    assert high_count > low_count
    assert 0.25 <= high_count / private_transaction_count <= 0.35


def test_private_banking_scenario_preserves_context_and_learner_views() -> None:
    """Generated records must keep Partner, Role, Banking relationship, account, and RM context."""
    tables = generate_private_banking_transaction_fraud_world(seed=42, scenario_prevalence=0.2)
    learner_tables = build_learner_facing_views(tables)

    assert PROTECTED_SCENARIO_ANSWER_KEYS in tables
    assert PROTECTED_SCENARIO_ANSWER_KEYS not in learner_tables

    scenario_alerts = tables["alerts"][
        tables["alerts"]["alert_type"] == PRIVATE_BANKING_ACTIVITY_TYPE
    ]
    scenario_context = (
        scenario_alerts.merge(
            tables["banking_relationships"][
                [
                    "banking_relationship_id",
                    "primary_client_id",
                    "relationship_manager_code",
                ]
            ],
            on="banking_relationship_id",
            how="left",
            validate="many_to_one",
        )
        .merge(
            tables["partner_roles"][["partner_id", "role_id", "banking_relationship_id"]],
            on="banking_relationship_id",
            how="left",
            validate="many_to_many",
        )
        .merge(
            tables["roles"][["role_id", "role_code"]],
            on="role_id",
            how="left",
            validate="many_to_one",
        )
    )

    assert not scenario_context.empty
    assert scenario_context["relationship_manager_code"].notna().all()
    assert scenario_context["partner_id"].notna().all()
    assert {"primary_client", "beneficial_owner", "authorized_signatory"} & set(
        scenario_context["role_code"]
    )


def test_private_banking_scenario_referential_integrity() -> None:
    """Scenario activities, alerts, cases, outcomes, and protected keys must join cleanly."""
    tables = generate_private_banking_transaction_fraud_world(seed=42, scenario_prevalence=0.2)

    scenario_activities = tables["suspicious_activities"][
        tables["suspicious_activities"]["activity_type"] == PRIVATE_BANKING_ACTIVITY_TYPE
    ]
    scenario_alerts = tables["alerts"][
        tables["alerts"]["alert_type"] == PRIVATE_BANKING_ACTIVITY_TYPE
    ]
    scenario_cases = tables["cases"][tables["cases"]["alert_id"].isin(scenario_alerts["alert_id"])]
    scenario_outcomes = tables["case_outcomes"][
        tables["case_outcomes"]["case_id"].isin(scenario_cases["case_id"])
    ]
    scenario_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS][
        tables[PROTECTED_SCENARIO_ANSWER_KEYS]["scenario_name"]
        == PRIVATE_BANKING_SCENARIO_NAME
    ]

    assert len(scenario_activities) == len(scenario_alerts) == len(scenario_cases)
    assert len(scenario_cases) == len(scenario_outcomes) == len(scenario_keys)
    assert set(scenario_activities["transaction_id"]) <= set(tables["transactions"]["transaction_id"])
    assert set(scenario_activities["account_id"]) <= set(tables["accounts"]["account_id"])
    assert set(scenario_activities["banking_relationship_id"]) <= set(
        tables["banking_relationships"]["banking_relationship_id"]
    )
    assert set(scenario_alerts["suspicious_activity_id"]) == set(
        scenario_activities["suspicious_activity_id"]
    )
    assert set(scenario_cases["alert_id"]) == set(scenario_alerts["alert_id"])
    assert set(scenario_outcomes["case_id"]) == set(scenario_cases["case_id"])
    assert set(scenario_keys["entity_id"]) == set(scenario_activities["transaction_id"])
    assert set(scenario_keys["entity_table"]) == {TRANSACTIONS}
    assert scenario_outcomes["confirmed_fraud"].all()


def test_private_banking_scenario_rejects_invalid_prevalence() -> None:
    """Prevalence must be a proportion."""
    with pytest.raises(ValueError, match="scenario_prevalence"):
        generate_private_banking_transaction_fraud_world(scenario_prevalence=1.5)


def _private_transaction_count(tables: dict[str, object]) -> int:
    """Count Alpine Crest transactions in generated tables."""
    transactions = tables["transactions"]
    accounts = tables["accounts"][["account_id", "institution_name"]]
    return int(
        transactions.merge(accounts, on="account_id", how="inner")
        .query("institution_name == @ALPINE_CREST")
        .shape[0]
    )


def _scenario_answer_key_count(tables: dict[str, object]) -> int:
    """Count protected transaction labels for the private-banking scenario."""
    answer_keys = tables[PROTECTED_SCENARIO_ANSWER_KEYS]
    return int(
        answer_keys[
            (answer_keys["scenario_name"] == PRIVATE_BANKING_SCENARIO_NAME)
            & (answer_keys["entity_table"] == TRANSACTIONS)
            & (answer_keys["label_value"] == "confirmed_fraud")
        ].shape[0]
    )
