"""Digital-banking scam-to-mule scenario generation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pandas as pd

from banking_fraud_lab.generators.minimal_world import (
    DEFAULT_SCALE_PROFILE,
    NOVABANK,
    DatasetScaleProfile,
    build_learner_facing_views,
    generate_minimal_banking_world,
)
from banking_fraud_lab.schema import (
    ACCOUNTS,
    ALERTS,
    CASE_OUTCOMES,
    CASES,
    COLUMN_NAMES,
    PAYMENT_BENEFICIARIES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    SESSIONS,
    SUSPICIOUS_ACTIVITIES,
    TABLE_NAMES,
    TRANSACTIONS,
    USERS,
)

DIGITAL_SCAM_TO_MULE_SCENARIO_NAME = "novabank_digital_scam_to_mule_flow"
DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE = "digital_scam_to_mule_flow"
MONEY_QUANT = Decimal("0.01")
MONEY_ZERO = Decimal("0.00")


def generate_digital_scam_to_mule_world(
    seed: int = 42,
    *,
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
    scenario_prevalence: float = 0.5,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate a minimal world with NovaBank scam-to-mule flows injected."""
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
    scenario_tables = inject_digital_scam_to_mule_flow(
        tables,
        scenario_prevalence=scenario_prevalence,
    )

    if output_dir is not None:
        _write_tables(scenario_tables, output_dir)

    return scenario_tables


def generate_learner_facing_digital_scam_to_mule_world(
    seed: int = 42,
    *,
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
    scenario_prevalence: float = 0.5,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate learner-facing NovaBank scam-to-mule tables without protected keys."""
    tables = generate_digital_scam_to_mule_world(
        seed=seed,
        scale=scale,
        scenario_prevalence=scenario_prevalence,
    )
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        _write_tables(learner_tables, output_dir)

    return learner_tables


def inject_digital_scam_to_mule_flow(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float = 0.5,
) -> dict[str, pd.DataFrame]:
    """Inject configurable NovaBank scam-to-mule behavior into generated tables."""
    _validate_prevalence(scenario_prevalence)
    scenario_tables = {table_name: frame.copy() for table_name, frame in tables.items()}
    selected_accounts = _select_mule_accounts(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
    )
    if selected_accounts.empty:
        return scenario_tables

    flow_rows = _build_flow_rows(scenario_tables, selected_accounts)
    _apply_early_life_account_updates(scenario_tables, flow_rows["account_updates"])
    _append_rows(scenario_tables, SESSIONS, flow_rows["sessions"])
    _append_rows(scenario_tables, PAYMENT_BENEFICIARIES, flow_rows["beneficiaries"])
    _append_rows(scenario_tables, TRANSACTIONS, flow_rows["transactions"])
    _append_rows(scenario_tables, SUSPICIOUS_ACTIVITIES, flow_rows["activities"])
    _append_rows(scenario_tables, ALERTS, flow_rows["alerts"])
    _append_rows(scenario_tables, CASES, flow_rows["cases"])
    _append_rows(scenario_tables, CASE_OUTCOMES, flow_rows["outcomes"])
    _append_rows(scenario_tables, PROTECTED_SCENARIO_ANSWER_KEYS, flow_rows["answer_keys"])

    return scenario_tables


def _select_mule_accounts(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float,
) -> pd.DataFrame:
    """Select deterministic NovaBank accounts to behave like mule accounts."""
    accounts = tables[ACCOUNTS]
    digital_accounts = accounts[accounts["institution_name"] == NOVABANK].copy()
    if digital_accounts.empty or scenario_prevalence == 0:
        return digital_accounts.iloc[0:0]

    target_count = min(
        len(digital_accounts),
        max(1, math.ceil(len(digital_accounts) * scenario_prevalence)),
    )
    digital_accounts["balance_chf_numeric"] = digital_accounts["balance_chf"].map(float)
    return digital_accounts.sort_values(
        ["balance_chf_numeric", "account_id"],
        ascending=[True, True],
    ).head(target_count)


def _build_flow_rows(
    tables: Mapping[str, pd.DataFrame],
    selected_accounts: pd.DataFrame,
) -> dict[str, list[dict[str, object]]]:
    """Build all rows needed for scam-to-mule flows."""
    users_by_client = _primary_users_by_client(tables[USERS])
    relationships = tables["banking_relationships"].set_index("banking_relationship_id")
    all_users = tuple(tables[USERS]["user_id"])
    session_index = _next_identifier_index(tables[SESSIONS], "session_id")
    beneficiary_index = _next_identifier_index(
        tables[PAYMENT_BENEFICIARIES],
        "payment_beneficiary_id",
    )
    transaction_index = _next_identifier_index(tables[TRANSACTIONS], "transaction_id")
    activity_index = _next_identifier_index(
        tables[SUSPICIOUS_ACTIVITIES],
        "suspicious_activity_id",
    )
    alert_index = _next_identifier_index(tables[ALERTS], "alert_id")
    case_index = _next_identifier_index(tables[CASES], "case_id")
    outcome_index = _next_identifier_index(tables[CASE_OUTCOMES], "case_outcome_id")
    answer_key_index = _next_identifier_index(
        tables[PROTECTED_SCENARIO_ANSWER_KEYS],
        "answer_key_id",
    )

    account_updates = []
    sessions = []
    beneficiaries = []
    transactions = []
    activities = []
    alerts = []
    cases = []
    outcomes = []
    answer_keys = []
    shared_device_hash = "dev_shared_mule_network_001"

    for offset, account in enumerate(selected_accounts.itertuples(index=False)):
        relationship = relationships.loc[account.banking_relationship_id]
        client_id = str(relationship["primary_client_id"])
        user = users_by_client.loc[client_id]
        user_id = str(user["user_id"])
        companion_user_id = _companion_user_id(all_users, user_id)
        incoming_at = pd.Timestamp(user["created_at"]) + pd.Timedelta(days=1, hours=9 + offset)
        pass_through_at = incoming_at + pd.Timedelta(minutes=42)
        account_updates.append(
            {
                "account_id": account.account_id,
                "opened_at": incoming_at - pd.Timedelta(days=2),
            }
        )

        owner_session_id = _identifier("S", session_index)
        companion_session_id = _identifier("S", session_index + 1)
        session_index += 2
        beneficiary_id = _identifier("B", beneficiary_index)
        beneficiary_index += 1
        incoming_transaction_id = _identifier("T", transaction_index)
        pass_through_transaction_id = _identifier("T", transaction_index + 1)
        transaction_index += 2
        activity_id = _identifier("SA", activity_index)
        activity_index += 1
        alert_id = _identifier("AL", alert_index)
        alert_index += 1
        case_id = _identifier("CASE", case_index)
        case_index += 1
        outcome_id = _identifier("OUT", outcome_index)
        outcome_index += 1
        answer_key_id = _identifier("AK", answer_key_index)
        answer_key_index += 1
        incoming_amount = Decimal(2800 + offset * 650).quantize(MONEY_QUANT)
        pass_through_amount = (incoming_amount * Decimal("0.92")).quantize(MONEY_QUANT)

        sessions.extend(
            [
                _session_row(
                    session_id=owner_session_id,
                    user_id=user_id,
                    started_at=incoming_at - pd.Timedelta(minutes=25),
                    device_fingerprint_hash=shared_device_hash,
                    session_event="payment_authorized",
                ),
                _session_row(
                    session_id=companion_session_id,
                    user_id=companion_user_id,
                    started_at=incoming_at - pd.Timedelta(minutes=18),
                    device_fingerprint_hash=shared_device_hash,
                    session_event="login",
                ),
            ]
        )
        beneficiaries.append(
            {
                "payment_beneficiary_id": beneficiary_id,
                "client_id": client_id,
                "added_by_user_id": user_id,
                "beneficiary_name": f"Nova transfer recipient {offset + 1}",
                "beneficiary_account_country": "LT",
                "beneficiary_bank_country": "LT",
                "beneficiary_change_event": "new_beneficiary_added",
                "created_at": incoming_at - pd.Timedelta(minutes=30),
                "status": "active",
            }
        )
        transactions.extend(
            [
                {
                    "transaction_id": incoming_transaction_id,
                    "account_id": account.account_id,
                    "payment_beneficiary_id": None,
                    "booked_at": incoming_at,
                    "transaction_type": "instant_payment",
                    "channel": "mobile_app",
                    "direction": "credit",
                    "amount_original": incoming_amount,
                    "currency": "CHF",
                    "amount_chf": incoming_amount,
                    "description": "Incoming victim payment to early-life mule account",
                },
                {
                    "transaction_id": pass_through_transaction_id,
                    "account_id": account.account_id,
                    "payment_beneficiary_id": beneficiary_id,
                    "booked_at": pass_through_at,
                    "transaction_type": "instant_payment",
                    "channel": "mobile_app",
                    "direction": "debit",
                    "amount_original": pass_through_amount,
                    "currency": "CHF",
                    "amount_chf": pass_through_amount,
                    "description": "Rapid pass-through to new beneficiary",
                },
            ]
        )
        activities.append(
            {
                "suspicious_activity_id": activity_id,
                "institution_name": NOVABANK,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "transaction_id": pass_through_transaction_id,
                "user_id": user_id,
                "session_id": owner_session_id,
                "payment_beneficiary_id": beneficiary_id,
                "activity_type": DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE,
                "detected_at": pass_through_at + pd.Timedelta(minutes=5),
                "detection_signal": (
                    "Early-life account received an incoming victim payment, added a new "
                    "beneficiary, used a shared device and high-risk network, then rapidly "
                    "passed funds onward."
                ),
                "suspected_amount_chf": pass_through_amount,
                "review_priority": "high",
            }
        )
        alerts.append(
            {
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "triggered_transaction_id": pass_through_transaction_id,
                "user_id": user_id,
                "session_id": owner_session_id,
                "payment_beneficiary_id": beneficiary_id,
                "institution_name": NOVABANK,
                "generated_at": pass_through_at + pd.Timedelta(minutes=8),
                "alert_type": DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE,
                "alert_status": "closed",
                "severity": "high",
                "reason": "Scam-to-mule flow with rapid pass-through and shared device signals.",
            }
        )
        cases.append(
            {
                "case_id": case_id,
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "transaction_id": pass_through_transaction_id,
                "user_id": user_id,
                "session_id": owner_session_id,
                "payment_beneficiary_id": beneficiary_id,
                "opened_at": pass_through_at + pd.Timedelta(hours=2),
                "assigned_team": "digital investigations",
                "case_status": "closed",
                "investigation_summary": (
                    "Case reviewed Client, User, device, beneficiary, session, and "
                    "pass-through transaction context."
                ),
            }
        )
        outcomes.append(
            {
                "case_outcome_id": outcome_id,
                "case_id": case_id,
                "decided_at": pass_through_at + pd.Timedelta(days=1),
                "outcome_type": "confirmed-fraud",
                "confirmed_fraud": True,
                "loss_amount_original": pass_through_amount,
                "loss_currency": "CHF",
                "loss_amount_chf": pass_through_amount,
                "notes": (
                    "Scam-to-mule flow confirmed with noisy operational outcomes retained "
                    "elsewhere in the alert lifecycle."
                ),
            }
        )
        answer_keys.append(
            {
                "answer_key_id": answer_key_id,
                "scenario_name": DIGITAL_SCAM_TO_MULE_SCENARIO_NAME,
                "entity_table": TRANSACTIONS,
                "entity_id": pass_through_transaction_id,
                "label_type": "scenario_label",
                "label_value": "confirmed_fraud",
                "available_to_learners": False,
            }
        )

    return {
        "account_updates": account_updates,
        "sessions": sessions,
        "beneficiaries": beneficiaries,
        "transactions": transactions,
        "activities": activities,
        "alerts": alerts,
        "cases": cases,
        "outcomes": outcomes,
        "answer_keys": answer_keys,
    }


def _apply_early_life_account_updates(
    tables: dict[str, pd.DataFrame],
    account_updates: list[dict[str, object]],
) -> None:
    """Mark selected mule accounts as early-life accounts for the scenario flow."""
    for update in account_updates:
        account_mask = tables[ACCOUNTS]["account_id"] == update["account_id"]
        tables[ACCOUNTS].loc[account_mask, "opened_at"] = update["opened_at"]


def _primary_users_by_client(users: pd.DataFrame) -> pd.DataFrame:
    """Return one deterministic User row per Client for scenario injection."""
    primary_users = (
        users.sort_values(["client_id", "created_at", "user_id"], kind="mergesort")
        .drop_duplicates("client_id", keep="first")
        .set_index("client_id")
    )
    if not primary_users.index.is_unique:
        raise ValueError("Expected one selected User per Client after deterministic selection")
    return primary_users


def _session_row(
    *,
    session_id: str,
    user_id: str,
    started_at: pd.Timestamp,
    device_fingerprint_hash: str,
    session_event: str,
) -> dict[str, object]:
    """Create a high-risk digital telemetry session row."""
    return {
        "session_id": session_id,
        "user_id": user_id,
        "started_at": started_at,
        "channel": "mobile_app",
        "user_agent": "NovaBankMobile/Android",
        "app_or_browser_version": "14.9",
        "device_fingerprint_hash": device_fingerprint_hash,
        "ip_country": "LT",
        "asn_risk_score": 92,
        "coarse_geolocation": "Vilnius-LT",
        "is_vpn_or_proxy": True,
        "auth_method": "password_sms",
        "session_event": session_event,
    }


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
    """Return the next numeric identifier suffix for IDs like ``T-0013``."""
    if frame.empty:
        return 1
    suffixes = frame[column_name].astype(str).str.rsplit("-", n=1).str[-1].astype(int)
    return int(suffixes.max()) + 1


def _identifier(prefix: str, index: int) -> str:
    """Format a zero-padded scenario identifier."""
    return f"{prefix}-{index:04d}"


def _companion_user_id(user_ids: tuple[str, ...], selected_user_id: str) -> str:
    """Pick another User to demonstrate shared-device behavior."""
    for user_id in user_ids:
        if user_id != selected_user_id:
            return user_id
    return selected_user_id


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
    "DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE",
    "DIGITAL_SCAM_TO_MULE_SCENARIO_NAME",
    "generate_digital_scam_to_mule_world",
    "generate_learner_facing_digital_scam_to_mule_world",
    "inject_digital_scam_to_mule_flow",
]
