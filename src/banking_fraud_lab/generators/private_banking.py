"""Private-banking transaction-fraud scenario generation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pandas as pd

from banking_fraud_lab.generators.minimal_world import (
    ALPINE_CREST,
    build_learner_facing_views,
    generate_minimal_banking_world,
)
from banking_fraud_lab.schema import (
    ACCOUNTS,
    ALERTS,
    CASE_OUTCOMES,
    CASES,
    COLUMN_NAMES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    SUSPICIOUS_ACTIVITIES,
    TABLE_NAMES,
    TRANSACTIONS,
)

PRIVATE_BANKING_SCENARIO_NAME = "alpine_crest_private_banking_transaction_fraud"
PRIVATE_BANKING_ACTIVITY_TYPE = "private_banking_transaction_fraud"
PRIVATE_BANKING_FALSE_POSITIVE_TYPE = "private_banking_high_value"
MONEY_ZERO = Decimal("0.00")


def generate_private_banking_transaction_fraud_world(
    seed: int = 42,
    *,
    scenario_prevalence: float = 0.2,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate a minimal world with Alpine Crest transaction-fraud labels injected."""
    tables = generate_minimal_banking_world(seed=seed)
    scenario_tables = inject_private_banking_transaction_fraud(
        tables,
        scenario_prevalence=scenario_prevalence,
    )

    if output_dir is not None:
        _write_tables(scenario_tables, output_dir)

    return scenario_tables


def generate_learner_facing_private_banking_transaction_fraud_world(
    seed: int = 42,
    *,
    scenario_prevalence: float = 0.2,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate learner-facing Alpine Crest scenario tables without protected keys."""
    tables = generate_private_banking_transaction_fraud_world(
        seed=seed,
        scenario_prevalence=scenario_prevalence,
    )
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        _write_tables(learner_tables, output_dir)

    return learner_tables


def inject_private_banking_transaction_fraud(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float = 0.2,
) -> dict[str, pd.DataFrame]:
    """Inject a configurable Alpine Crest transaction-fraud pattern into tables."""
    _validate_prevalence(scenario_prevalence)
    scenario_tables = {table_name: frame.copy() for table_name, frame in tables.items()}
    selected_transactions = _select_private_transactions(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
    )
    if selected_transactions.empty:
        return scenario_tables

    fraud_activity_rows = _private_fraud_activity_rows(
        scenario_tables,
        selected_transactions,
    )
    fraud_alert_rows = _private_fraud_alert_rows(scenario_tables, fraud_activity_rows)
    fraud_case_rows = _private_fraud_case_rows(scenario_tables, fraud_alert_rows)
    fraud_outcome_rows = _private_fraud_outcome_rows(
        scenario_tables,
        fraud_case_rows,
        selected_transactions,
    )
    answer_key_rows = _private_fraud_answer_key_rows(
        scenario_tables,
        selected_transactions,
    )

    _append_rows(scenario_tables, SUSPICIOUS_ACTIVITIES, fraud_activity_rows)
    _append_rows(scenario_tables, ALERTS, fraud_alert_rows)
    _append_rows(scenario_tables, CASES, fraud_case_rows)
    _append_rows(scenario_tables, CASE_OUTCOMES, fraud_outcome_rows)
    _append_rows(scenario_tables, PROTECTED_SCENARIO_ANSWER_KEYS, answer_key_rows)
    _add_private_false_positive_case(
        scenario_tables,
        selected_transaction_ids=set(selected_transactions["transaction_id"]),
    )

    return scenario_tables


def _select_private_transactions(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float,
) -> pd.DataFrame:
    """Select deterministic private-banking transactions for scenario labels."""
    transactions = tables[TRANSACTIONS]
    accounts = tables[ACCOUNTS][
        ["account_id", "banking_relationship_id", "institution_name", "balance_chf"]
    ]
    private_transactions = transactions.merge(
        accounts,
        on="account_id",
        how="inner",
        validate="many_to_one",
    )
    private_transactions = private_transactions[
        private_transactions["institution_name"] == ALPINE_CREST
    ].copy()
    if private_transactions.empty or scenario_prevalence == 0:
        return private_transactions.iloc[0:0]

    target_count = min(
        len(private_transactions),
        max(1, math.ceil(len(private_transactions) * scenario_prevalence)),
    )
    private_transactions["amount_chf_numeric"] = private_transactions["amount_chf"].map(float)
    private_transactions["debit_rank"] = private_transactions["direction"].ne("debit").astype(int)
    return private_transactions.sort_values(
        ["debit_rank", "amount_chf_numeric", "transaction_id"],
        ascending=[True, False, True],
    ).head(target_count)


def _private_fraud_activity_rows(
    tables: Mapping[str, pd.DataFrame],
    selected_transactions: pd.DataFrame,
) -> list[dict[str, object]]:
    """Build suspicious activity rows for selected private-banking transactions."""
    start_index = _next_identifier_index(
        tables[SUSPICIOUS_ACTIVITIES],
        "suspicious_activity_id",
    )
    rows = []
    for offset, transaction in enumerate(selected_transactions.itertuples(index=False)):
        rows.append(
            {
                "suspicious_activity_id": _identifier("SA", start_index + offset),
                "institution_name": ALPINE_CREST,
                "banking_relationship_id": transaction.banking_relationship_id,
                "account_id": transaction.account_id,
                "transaction_id": transaction.transaction_id,
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": None,
                "activity_type": PRIVATE_BANKING_ACTIVITY_TYPE,
                "detected_at": pd.Timestamp(transaction.booked_at) + pd.Timedelta(minutes=20),
                "detection_signal": (
                    "Large private-banking debit relative to account and relationship context."
                ),
                "suspected_amount_chf": transaction.amount_chf,
                "review_priority": "high",
            }
        )
    return rows


def _private_fraud_alert_rows(
    tables: Mapping[str, pd.DataFrame],
    activity_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build alert rows from private-banking suspicious activities."""
    start_index = _next_identifier_index(tables[ALERTS], "alert_id")
    rows = []
    for offset, activity in enumerate(activity_rows):
        rows.append(
            {
                "alert_id": _identifier("AL", start_index + offset),
                "suspicious_activity_id": activity["suspicious_activity_id"],
                "banking_relationship_id": activity["banking_relationship_id"],
                "account_id": activity["account_id"],
                "triggered_transaction_id": activity["transaction_id"],
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": None,
                "institution_name": ALPINE_CREST,
                "generated_at": pd.Timestamp(activity["detected_at"]) + pd.Timedelta(minutes=5),
                "alert_type": PRIVATE_BANKING_ACTIVITY_TYPE,
                "alert_status": "closed",
                "severity": "high",
                "reason": activity["detection_signal"],
            }
        )
    return rows


def _private_fraud_case_rows(
    tables: Mapping[str, pd.DataFrame],
    alert_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build investigation cases for private-banking fraud alerts."""
    start_index = _next_identifier_index(tables[CASES], "case_id")
    rows = []
    for offset, alert in enumerate(alert_rows):
        rows.append(
            {
                "case_id": _identifier("CASE", start_index + offset),
                "alert_id": alert["alert_id"],
                "suspicious_activity_id": alert["suspicious_activity_id"],
                "banking_relationship_id": alert["banking_relationship_id"],
                "account_id": alert["account_id"],
                "transaction_id": alert["triggered_transaction_id"],
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": None,
                "opened_at": pd.Timestamp(alert["generated_at"]) + pd.Timedelta(hours=4),
                "assigned_team": "private banking investigations",
                "case_status": "closed",
                "investigation_summary": (
                    "Case reviewed relationship-manager context, relationship roles, "
                    "account balance, and transaction amount."
                ),
            }
        )
    return rows


def _private_fraud_outcome_rows(
    tables: Mapping[str, pd.DataFrame],
    case_rows: list[dict[str, object]],
    selected_transactions: pd.DataFrame,
) -> list[dict[str, object]]:
    """Build confirmed-fraud case outcomes for private-banking cases."""
    start_index = _next_identifier_index(tables[CASE_OUTCOMES], "case_outcome_id")
    selected_by_id = selected_transactions.set_index("transaction_id")
    rows = []
    for offset, case in enumerate(case_rows):
        transaction = selected_by_id.loc[case["transaction_id"]]
        rows.append(
            {
                "case_outcome_id": _identifier("OUT", start_index + offset),
                "case_id": case["case_id"],
                "decided_at": pd.Timestamp(case["opened_at"]) + pd.Timedelta(days=2),
                "outcome_type": "confirmed-fraud",
                "confirmed_fraud": True,
                "loss_amount_original": transaction["amount_original"],
                "loss_currency": transaction["currency"],
                "loss_amount_chf": transaction["amount_chf"],
                "notes": (
                    "Private-banking transaction-fraud scenario confirmed; protected "
                    "answer keys remain separate."
                ),
            }
        )
    return rows


def _private_fraud_answer_key_rows(
    tables: Mapping[str, pd.DataFrame],
    selected_transactions: pd.DataFrame,
) -> list[dict[str, object]]:
    """Build protected answer-key rows for selected scenario transactions."""
    start_index = _next_identifier_index(
        tables[PROTECTED_SCENARIO_ANSWER_KEYS],
        "answer_key_id",
    )
    rows = []
    for offset, transaction in enumerate(selected_transactions.itertuples(index=False)):
        rows.append(
            {
                "answer_key_id": _identifier("AK", start_index + offset),
                "scenario_name": PRIVATE_BANKING_SCENARIO_NAME,
                "entity_table": TRANSACTIONS,
                "entity_id": transaction.transaction_id,
                "label_type": "scenario_label",
                "label_value": "confirmed_fraud",
                "available_to_learners": False,
            }
        )
    return rows


def _add_private_false_positive_case(
    tables: dict[str, pd.DataFrame],
    *,
    selected_transaction_ids: set[str],
) -> None:
    """Close one existing Alpine Crest alert as a non-fraud operational outcome."""
    alerts = tables[ALERTS]
    candidate_alerts = alerts[
        (alerts["institution_name"] == ALPINE_CREST)
        & (alerts["alert_type"] == PRIVATE_BANKING_FALSE_POSITIVE_TYPE)
        & (~alerts["triggered_transaction_id"].isin(selected_transaction_ids))
    ]
    if candidate_alerts.empty:
        return

    alert = candidate_alerts.iloc[0]
    alert_id = str(alert["alert_id"])
    tables[ALERTS].loc[tables[ALERTS]["alert_id"] == alert_id, "alert_status"] = "closed"

    case_id = _identifier("CASE", _next_identifier_index(tables[CASES], "case_id"))
    case_row = {
        "case_id": case_id,
        "alert_id": alert_id,
        "suspicious_activity_id": alert["suspicious_activity_id"],
        "banking_relationship_id": alert["banking_relationship_id"],
        "account_id": alert["account_id"],
        "transaction_id": alert["triggered_transaction_id"],
        "user_id": None,
        "session_id": None,
        "payment_beneficiary_id": None,
        "opened_at": pd.Timestamp(alert["generated_at"]) + pd.Timedelta(hours=4),
        "assigned_team": "private banking investigations",
        "case_status": "closed",
        "investigation_summary": (
            "Case reviewed the high-value movement and closed without fraud confirmation."
        ),
    }
    outcome_row = {
        "case_outcome_id": _identifier(
            "OUT",
            _next_identifier_index(tables[CASE_OUTCOMES], "case_outcome_id"),
        ),
        "case_id": case_id,
        "decided_at": pd.Timestamp(case_row["opened_at"]) + pd.Timedelta(days=1),
        "outcome_type": "false-positive",
        "confirmed_fraud": False,
        "loss_amount_original": MONEY_ZERO,
        "loss_currency": "CHF",
        "loss_amount_chf": MONEY_ZERO,
        "notes": "Private-banking review closed without a fraud confirmation.",
    }
    _append_rows(tables, CASES, [case_row])
    _append_rows(tables, CASE_OUTCOMES, [outcome_row])


def _append_rows(
    tables: dict[str, pd.DataFrame],
    table_name: str,
    rows: list[dict[str, object]],
) -> None:
    """Append schema-ordered rows to a generated table."""
    if not rows:
        return
    tables[table_name] = pd.concat(
        [tables[table_name], pd.DataFrame(rows, columns=COLUMN_NAMES[table_name])],
        ignore_index=True,
    )


def _next_identifier_index(frame: pd.DataFrame, column_name: str) -> int:
    """Return the next numeric identifier suffix for IDs like ``CASE-0003``."""
    if frame.empty:
        return 1
    suffixes = frame[column_name].astype(str).str.rsplit("-", n=1).str[-1].astype(int)
    return int(suffixes.max()) + 1


def _identifier(prefix: str, index: int) -> str:
    """Format a zero-padded scenario identifier."""
    return f"{prefix}-{index:04d}"


def _validate_prevalence(scenario_prevalence: float) -> None:
    """Validate the requested scenario prevalence proportion."""
    if scenario_prevalence < 0 or scenario_prevalence > 1:
        raise ValueError("scenario_prevalence must be between 0 and 1")


def _write_tables(tables: Mapping[str, pd.DataFrame], output_dir: Path) -> None:
    """Write generated tables in schema order to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for table_name in TABLE_NAMES:
        if table_name in tables:
            tables[table_name].to_csv(output_path / f"{table_name}.csv", index=False)


__all__ = [
    "PRIVATE_BANKING_ACTIVITY_TYPE",
    "PRIVATE_BANKING_SCENARIO_NAME",
    "generate_learner_facing_private_banking_transaction_fraud_world",
    "generate_private_banking_transaction_fraud_world",
    "inject_private_banking_transaction_fraud",
]
