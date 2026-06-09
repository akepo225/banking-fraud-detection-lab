"""Private-banking transaction-fraud scenario generation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pandas as pd

from banking_fraud_lab.generators.minimal_world import (
    ALPINE_CREST,
    DEFAULT_SCALE_PROFILE,
    DatasetScaleProfile,
    build_learner_facing_views,
    generate_minimal_banking_world,
)
from banking_fraud_lab.schema import (
    ACCOUNTS,
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASE_OUTCOMES,
    CASES,
    COLUMN_NAMES,
    PAYMENT_BENEFICIARIES,
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
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
    scenario_prevalence: float = 0.2,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate a minimal world with Alpine Crest transaction-fraud labels injected."""
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
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
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
    scenario_prevalence: float = 0.2,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate learner-facing Alpine Crest scenario tables without protected keys."""
    tables = generate_private_banking_transaction_fraud_world(
        seed=seed,
        scale=scale,
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
    false_positive_rows = _generate_private_false_positives(
        scenario_tables,
        selected_transaction_ids=set(selected_transactions["transaction_id"]),
    )
    _append_rows(scenario_tables, SUSPICIOUS_ACTIVITIES, false_positive_rows["activities"])
    _append_rows(scenario_tables, ALERTS, false_positive_rows["alerts"])
    _append_rows(scenario_tables, CASES, false_positive_rows["cases"])
    _append_rows(scenario_tables, CASE_OUTCOMES, false_positive_rows["outcomes"])

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
        beneficiary_id = _normalize_beneficiary_id(transaction.payment_beneficiary_id)
        rows.append(
            {
                "suspicious_activity_id": _identifier("SA", start_index + offset),
                "institution_name": ALPINE_CREST,
                "banking_relationship_id": transaction.banking_relationship_id,
                "account_id": transaction.account_id,
                "transaction_id": transaction.transaction_id,
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": beneficiary_id,
                "activity_type": PRIVATE_BANKING_ACTIVITY_TYPE,
                "detected_at": pd.Timestamp(transaction.booked_at) + pd.Timedelta(minutes=20),
                "detection_signal": (
                    "Large private-banking debit relative to account, counterparty, "
                    "and relationship context."
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
        generated_at = pd.Timestamp(activity["detected_at"]) + pd.Timedelta(minutes=5)
        rows.append(
            {
                "alert_id": _identifier("AL", start_index + offset),
                "suspicious_activity_id": activity["suspicious_activity_id"],
                "banking_relationship_id": activity["banking_relationship_id"],
                "account_id": activity["account_id"],
                "triggered_transaction_id": activity["transaction_id"],
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": activity["payment_beneficiary_id"],
                "institution_name": ALPINE_CREST,
                "generated_at": generated_at,
                "alert_type": PRIVATE_BANKING_ACTIVITY_TYPE,
                "alert_status": "closed",
                "status_updated_at": generated_at + pd.Timedelta(minutes=30),
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
        opened_at = pd.Timestamp(alert["generated_at"]) + pd.Timedelta(hours=4)
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
                "payment_beneficiary_id": alert["payment_beneficiary_id"],
                "opened_at": opened_at,
                "assigned_team": "private banking investigations",
                "case_status": "closed",
                "closed_at": opened_at + pd.Timedelta(days=2),
                "investigation_summary": (
                    "Case reviewed relationship-manager context, relationship roles, "
                    "AUM, account balance, counterparty context, and transaction amount."
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
        decided_at = pd.Timestamp(case["opened_at"]) + pd.Timedelta(days=2)
        rows.append(
            {
                "case_outcome_id": _identifier("OUT", start_index + offset),
                "case_id": case["case_id"],
                "decided_at": decided_at,
                "recorded_at": decided_at + pd.Timedelta(hours=1),
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


def _generate_private_false_positives(
    tables: Mapping[str, pd.DataFrame],
    *,
    selected_transaction_ids: set[str],
) -> dict[str, list[dict[str, object]]]:
    """Build legitimate high-net-worth false positives with cases and outcomes."""
    selected = _select_false_positive_transactions(
        tables,
        selected_transaction_ids=selected_transaction_ids,
    )
    rows = {
        "activities": [],
        "alerts": [],
        "cases": [],
        "outcomes": [],
    }
    if selected.empty:
        return rows

    activity_index = _next_identifier_index(tables[SUSPICIOUS_ACTIVITIES], "suspicious_activity_id")
    alert_index = _next_identifier_index(tables[ALERTS], "alert_id")
    case_index = _next_identifier_index(tables[CASES], "case_id")
    outcome_index = _next_identifier_index(tables[CASE_OUTCOMES], "case_outcome_id")

    for offset, transaction in enumerate(selected.itertuples(index=False)):
        activity_id = _identifier("SA", activity_index + offset)
        alert_id = _identifier("AL", alert_index + offset)
        case_id = _identifier("CASE", case_index + offset)
        outcome_id = _identifier("OUT", outcome_index + offset)
        beneficiary_id = _normalize_beneficiary_id(transaction.payment_beneficiary_id)
        detected_at = pd.Timestamp(transaction.booked_at) + pd.Timedelta(minutes=18)
        generated_at = detected_at + pd.Timedelta(minutes=5)
        opened_at = generated_at + pd.Timedelta(hours=4)
        decided_at = opened_at + pd.Timedelta(days=1)
        detection_signal = _false_positive_signal(transaction.false_positive_pattern)

        rows["activities"].append(
            {
                "suspicious_activity_id": activity_id,
                "institution_name": ALPINE_CREST,
                "banking_relationship_id": transaction.banking_relationship_id,
                "account_id": transaction.account_id,
                "transaction_id": transaction.transaction_id,
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": beneficiary_id,
                "activity_type": PRIVATE_BANKING_FALSE_POSITIVE_TYPE,
                "detected_at": detected_at,
                "detection_signal": detection_signal,
                "suspected_amount_chf": transaction.amount_chf,
                "review_priority": "medium",
            }
        )
        rows["alerts"].append(
            {
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": transaction.banking_relationship_id,
                "account_id": transaction.account_id,
                "triggered_transaction_id": transaction.transaction_id,
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": beneficiary_id,
                "institution_name": ALPINE_CREST,
                "generated_at": generated_at,
                "alert_type": PRIVATE_BANKING_FALSE_POSITIVE_TYPE,
                "alert_status": "closed",
                "status_updated_at": generated_at + pd.Timedelta(minutes=30),
                "severity": "medium",
                "reason": detection_signal,
            }
        )
        rows["cases"].append(
            {
                "case_id": case_id,
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": transaction.banking_relationship_id,
                "account_id": transaction.account_id,
                "transaction_id": transaction.transaction_id,
                "user_id": None,
                "session_id": None,
                "payment_beneficiary_id": beneficiary_id,
                "opened_at": opened_at,
                "assigned_team": "private banking investigations",
                "case_status": "closed",
                "closed_at": opened_at + pd.Timedelta(days=1),
                "investigation_summary": _false_positive_investigation_summary(transaction),
            }
        )
        rows["outcomes"].append(
            {
                "case_outcome_id": outcome_id,
                "case_id": case_id,
                "decided_at": decided_at,
                "recorded_at": decided_at + pd.Timedelta(hours=1),
                "outcome_type": "false-positive",
                "confirmed_fraud": False,
                "loss_amount_original": MONEY_ZERO,
                "loss_currency": transaction.currency,
                "loss_amount_chf": MONEY_ZERO,
                "notes": "Private-banking review closed without a fraud confirmation.",
            }
        )

    return rows


def _select_false_positive_transactions(
    tables: Mapping[str, pd.DataFrame],
    *,
    selected_transaction_ids: set[str],
) -> pd.DataFrame:
    """Select deterministic legitimate high-net-worth false-positive examples."""
    transactions = tables[TRANSACTIONS]
    accounts = tables[ACCOUNTS][
        ["account_id", "banking_relationship_id", "institution_name", "balance_chf"]
    ]
    relationships = tables[BANKING_RELATIONSHIPS][
        ["banking_relationship_id", "primary_client_id", "aum_chf"]
    ]
    beneficiaries = tables[PAYMENT_BENEFICIARIES][
        [
            "payment_beneficiary_id",
            "beneficiary_name",
            "beneficiary_account_country",
            "beneficiary_change_event",
            "created_at",
        ]
    ]
    used_transaction_ids = set(tables[SUSPICIOUS_ACTIVITIES]["transaction_id"]) | set(
        selected_transaction_ids
    )
    candidates = (
        transactions.merge(accounts, on="account_id", how="inner", validate="many_to_one")
        .merge(
            relationships,
            on="banking_relationship_id",
            how="left",
            validate="many_to_one",
        )
        .merge(
            beneficiaries,
            on="payment_beneficiary_id",
            how="left",
            validate="many_to_one",
        )
    )
    candidates = candidates[
        (candidates["institution_name"] == ALPINE_CREST)
        & (~candidates["transaction_id"].isin(used_transaction_ids))
    ].copy()
    if candidates.empty:
        return candidates

    candidates["amount_chf_numeric"] = candidates["amount_chf"].map(float)
    candidates["false_positive_pattern"] = "relationship_context"
    selected_frames = [
        _first_false_positive_pattern(
            candidates,
            pattern_name="large_repatriation",
            mask=(
                (candidates["transaction_type"] == "wire_transfer")
                & (candidates["payment_beneficiary_id"].notna())
                & (candidates["beneficiary_change_event"] == "established_beneficiary")
            ),
        ),
        _first_false_positive_pattern(
            candidates,
            pattern_name="routine_fx",
            mask=candidates["transaction_type"] == "fx_trade",
        ),
        _first_false_positive_pattern(
            candidates,
            pattern_name="expected_fee",
            mask=candidates["transaction_type"].isin(("management_fee", "custody_fee")),
        ),
    ]
    non_empty_selected_frames = [frame for frame in selected_frames if not frame.empty]
    selected = (
        pd.concat(non_empty_selected_frames, ignore_index=True)
        if non_empty_selected_frames
        else candidates.iloc[0:0].copy()
    )
    target_count = _false_positive_target_count(len(candidates))
    if len(selected) < target_count:
        remaining = candidates[~candidates["transaction_id"].isin(selected["transaction_id"])]
        remaining = remaining.sort_values(
            ["amount_chf_numeric", "transaction_id"],
            ascending=[False, True],
            kind="stable",
        ).head(target_count - len(selected))
        selected = pd.concat([selected, remaining], ignore_index=True)

    return selected.head(target_count)


def _first_false_positive_pattern(
    candidates: pd.DataFrame,
    *,
    pattern_name: str,
    mask: pd.Series,
) -> pd.DataFrame:
    """Return one highest-amount candidate tagged with a false-positive pattern."""
    pattern_candidates = candidates[mask].copy()
    if pattern_candidates.empty:
        return pattern_candidates
    pattern_candidates = pattern_candidates.sort_values(
        ["amount_chf_numeric", "transaction_id"],
        ascending=[False, True],
        kind="stable",
    ).head(1)
    pattern_candidates.loc[:, "false_positive_pattern"] = pattern_name
    return pattern_candidates


def _false_positive_target_count(candidate_count: int) -> int:
    """Scale false positives to 3-5 examples when enough candidates exist."""
    if candidate_count == 0:
        return 0
    return min(candidate_count, min(5, max(3, math.ceil(candidate_count * 0.02))))


def _false_positive_signal(pattern_name: str) -> str:
    """Return the alert signal for a legitimate private-banking review pattern."""
    signals = {
        "large_repatriation": "High-value wire matched established counterparty context.",
        "routine_fx": "FX trade reviewed against documented relationship activity.",
        "expected_fee": "Private-banking fee amount matched the relationship AUM tier.",
    }
    return signals.get(
        pattern_name,
        "High-value private-banking movement matched expected relationship context.",
    )


def _false_positive_investigation_summary(transaction: object) -> str:
    """Return a distinct learner-readable rationale for clearing a false positive."""
    if transaction.false_positive_pattern == "large_repatriation":
        beneficiary_name = (
            "known counterparty"
            if pd.isna(transaction.beneficiary_name)
            else transaction.beneficiary_name
        )
        country = (
            "documented country"
            if pd.isna(transaction.beneficiary_account_country)
            else transaction.beneficiary_account_country
        )
        created_at = (
            "relationship history"
            if pd.isna(transaction.created_at)
            else pd.Timestamp(transaction.created_at).date().isoformat()
        )
        return (
            f"High-value wire involving {country} reviewed. Counterparty "
            f"{beneficiary_name} is an established relationship since {created_at}. "
            "Movement consistent with the Client's repatriation pattern."
        )
    if transaction.false_positive_pattern == "routine_fx":
        return (
            "FX trade reviewed. Client has documented FX activity history. "
            "Trade size within established limits."
        )
    if transaction.false_positive_pattern == "expected_fee":
        return (
            "Management fee reviewed. Amount consistent with relationship AUM tier "
            "and fee schedule."
        )
    return (
        "High-value movement reviewed with Banking relationship, AUM, and counterparty "
        "context; no fraud confirmation was recorded."
    )


def _normalize_beneficiary_id(value: object) -> object | None:
    """Return None for pandas null beneficiary values."""
    if pd.isna(value):
        return None
    return value


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
    "PRIVATE_BANKING_FALSE_POSITIVE_TYPE",
    "PRIVATE_BANKING_SCENARIO_NAME",
    "generate_learner_facing_private_banking_transaction_fraud_world",
    "generate_private_banking_transaction_fraud_world",
    "inject_private_banking_transaction_fraud",
]
