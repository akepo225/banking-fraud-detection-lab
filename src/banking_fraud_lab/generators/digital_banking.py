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

# Activity types for the expanded v0.4 digital scenarios. These map to existing
# Detection pattern IDs (see src/banking_fraud_lab/schema/detection_patterns.py);
# no new pattern IDs are introduced.
ACCOUNT_TAKEOVER_BENEFICIARY_ACTIVITY_TYPE = "new_beneficiary_payment"
ACCOUNT_TAKEOVER_VELOCITY_ACTIVITY_TYPE = "session_payment_velocity"
SUSPICIOUS_BENEFICIARY_CHANGE_ACTIVITY_TYPE = "new_beneficiary_payment"
ONBOARDING_ABUSE_ACTIVITY_TYPE = "digital_scam_to_mule_flow"

ACCOUNT_TAKEOVER_SCENARIO_NAME = "novabank_digital_account_takeover"
ONBOARDING_ABUSE_SCENARIO_NAME = "novabank_digital_onboarding_abuse"
SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME = "novabank_digital_suspicious_beneficiary_change"

# Protected answer-key label values that capture the *true* fraud status behind a
# noisy alert-triage outcome. These are stored in protected_scenario_answer_keys so
# learners never see a clean ground-truth label, while reviewers can validate the
# label noise.
LABEL_TRUE_FRAUD = "true_confirmed_fraud"
LABEL_TRUE_BENIGN = "true_false_positive"


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


def generate_digital_fraud_scenarios_world(
    seed: int = 42,
    *,
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
    scenario_prevalence: float = 0.5,
    noisy_outcome_rate: float = 0.3,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate a NovaBank Digital world with the full v0.4 scenario mix.

    Runs the existing scam-to-mule injection together with the account-takeover,
    onboarding-abuse, and suspicious-beneficiary-change injections introduced in
    v0.4. A deterministic subset of scenario cases receive noisy alert-triage
    outcomes so confirmed-fraud labels stay imperfect and explainable.

    Args:
        seed: Deterministic generation seed.
        scale: Named scale profile or a ``DatasetScaleProfile``.
        scenario_prevalence: Bounded proportion of NovaBank Digital accounts that
            participate in each scenario family.
        noisy_outcome_rate: Bounded proportion of scenario cases whose
            triage outcome deliberately disagrees with the true protected label.
        output_dir: Optional directory to write generated CSV tables.

    Returns:
        Generated tables with all scenario injections applied.
    """
    tables = generate_minimal_banking_world(seed=seed, scale=scale)
    scenario_tables = inject_digital_fraud_scenarios(
        tables,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
    )

    if output_dir is not None:
        _write_tables(scenario_tables, output_dir)

    return scenario_tables


def generate_learner_facing_digital_fraud_scenarios_world(
    seed: int = 42,
    *,
    scale: str | DatasetScaleProfile = DEFAULT_SCALE_PROFILE,
    scenario_prevalence: float = 0.5,
    noisy_outcome_rate: float = 0.3,
    output_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate learner-facing NovaBank Digital scenario tables without protected keys."""
    tables = generate_digital_fraud_scenarios_world(
        seed=seed,
        scale=scale,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
    )
    learner_tables = build_learner_facing_views(tables)

    if output_dir is not None:
        _write_tables(learner_tables, output_dir)

    return learner_tables


def inject_digital_fraud_scenarios(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float = 0.5,
    noisy_outcome_rate: float = 0.3,
) -> dict[str, pd.DataFrame]:
    """Inject the full v0.4 NovaBank Digital scenario mix into generated tables.

    Applies the scam-to-mule, account-takeover, onboarding-abuse, and
    suspicious-beneficiary-change injections in sequence. Each injection is
    bounded by ``scenario_prevalence`` and runs against the output of the prior
    injection so identifier suffixes never collide.
    """
    _validate_prevalence(scenario_prevalence)
    _validate_prevalence(noisy_outcome_rate)
    # scam-to-mule is intentionally the clean v0.1 baseline scenario: its case
    # outcomes are always confirmed-fraud (test_digital_scam_to_mule_scenario
    # asserts confirmed_fraud.all()), so it is injected WITHOUT noisy_outcome_rate.
    # The v0.4 families (account-takeover, onboarding-abuse,
    # suspicious-beneficiary-change) carry the noisy confirmed-fraud labels.
    scenario_tables = inject_digital_scam_to_mule_flow(
        tables,
        scenario_prevalence=scenario_prevalence,
    )
    scenario_tables = inject_account_takeover_scenario(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
    )
    # Accounts whose lifecycle (opened_at) scam-to-mule rewrote as early-life
    # mules must be skipped by onboarding-abuse so the two injections target
    # disjoint accounts and never overwrite each other's opened_at.
    rewritten_account_ids = _early_life_account_ids(scenario_tables)
    scenario_tables = inject_onboarding_abuse_scenario(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
        exclude_account_ids=rewritten_account_ids,
    )
    scenario_tables = inject_suspicious_beneficiary_change_scenario(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
    )
    return scenario_tables


def _early_life_account_ids(tables: Mapping[str, pd.DataFrame]) -> frozenset[str]:
    """Return NovaBank account ids whose opened_at a scenario injection rewrote.

    scam-to-mule rewrites opened_at on its mule accounts to mark them early-life.
    We identify them by joining the scam-to-mule answer keys (entity transactions)
    back to their accounts.
    """
    answer_keys = tables.get(PROTECTED_SCENARIO_ANSWER_KEYS)
    if answer_keys is None or answer_keys.empty:
        return frozenset()
    scam_keys = answer_keys[
        answer_keys["scenario_name"] == DIGITAL_SCAM_TO_MULE_SCENARIO_NAME
    ]
    if scam_keys.empty:
        return frozenset()
    cases = tables.get("cases")
    if cases is None or cases.empty:
        return frozenset()
    scam_transactions = cases.merge(
        scam_keys[["entity_id"]],
        left_on="transaction_id",
        right_on="entity_id",
        how="inner",
    )
    return frozenset(scam_transactions["account_id"].dropna())


def inject_account_takeover_scenario(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float = 0.5,
    noisy_outcome_rate: float = 0.3,
) -> dict[str, pd.DataFrame]:
    """Inject account-takeover behavior modeled under new-beneficiary and velocity patterns."""
    return _inject_takeover_style_scenario(
        tables,
        scenario_name=ACCOUNT_TAKEOVER_SCENARIO_NAME,
        primary_activity_type=ACCOUNT_TAKEOVER_BENEFICIARY_ACTIVITY_TYPE,
        velocity_activity_type=ACCOUNT_TAKEOVER_VELOCITY_ACTIVITY_TYPE,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
        detection_signal=(
            "Account-takeover session added a new beneficiary, paid from an "
            "unfamiliar device and high-risk network, and triggered elevated "
            "session payment velocity."
        ),
        beneficiary_change_event="new_beneficiary_added",
        session_event="payment_authorized",
    )


def inject_suspicious_beneficiary_change_scenario(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float = 0.5,
    noisy_outcome_rate: float = 0.3,
) -> dict[str, pd.DataFrame]:
    """Inject suspicious beneficiary-change behavior modeled under new-beneficiary payment."""
    return _inject_takeover_style_scenario(
        tables,
        scenario_name=SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME,
        primary_activity_type=SUSPICIOUS_BENEFICIARY_CHANGE_ACTIVITY_TYPE,
        velocity_activity_type=None,
        scenario_prevalence=scenario_prevalence,
        noisy_outcome_rate=noisy_outcome_rate,
        detection_signal=(
            "Beneficiary details were changed shortly before a high-value outbound "
            "payment, consistent with a suspicious beneficiary-change attempt."
        ),
        beneficiary_change_event="beneficiary_updated",
        session_event="add_beneficiary",
    )


def inject_onboarding_abuse_scenario(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float = 0.5,
    noisy_outcome_rate: float = 0.3,
    exclude_account_ids: frozenset[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Inject onboarding-abuse behavior modeled under the digital scam-to-mule pattern."""
    _validate_prevalence(scenario_prevalence)
    _validate_prevalence(noisy_outcome_rate)
    scenario_tables = {table_name: frame.copy() for table_name, frame in tables.items()}
    selected_accounts = _select_nova_accounts_by_prevalence(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
        prefer_lower_balance=True,
        exclude_account_ids=exclude_account_ids,
    )
    if selected_accounts.empty:
        return scenario_tables

    rows = _build_onboarding_abuse_rows(
        scenario_tables,
        selected_accounts,
        noisy_outcome_rate=noisy_outcome_rate,
    )
    _apply_early_life_account_updates(scenario_tables, rows["account_updates"])
    _append_rows(scenario_tables, SESSIONS, rows["sessions"])
    _append_rows(scenario_tables, PAYMENT_BENEFICIARIES, rows["beneficiaries"])
    _append_rows(scenario_tables, TRANSACTIONS, rows["transactions"])
    _append_rows(scenario_tables, SUSPICIOUS_ACTIVITIES, rows["activities"])
    _append_rows(scenario_tables, ALERTS, rows["alerts"])
    _append_rows(scenario_tables, CASES, rows["cases"])
    _append_rows(scenario_tables, CASE_OUTCOMES, rows["outcomes"])
    _append_rows(scenario_tables, PROTECTED_SCENARIO_ANSWER_KEYS, rows["answer_keys"])
    return scenario_tables


def _inject_takeover_style_scenario(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_name: str,
    primary_activity_type: str,
    velocity_activity_type: str | None,
    scenario_prevalence: float,
    noisy_outcome_rate: float,
    detection_signal: str,
    beneficiary_change_event: str,
    session_event: str,
) -> dict[str, pd.DataFrame]:
    """Shared builder for account-takeover and suspicious-beneficiary-change scenarios."""
    _validate_prevalence(scenario_prevalence)
    _validate_prevalence(noisy_outcome_rate)
    scenario_tables = {table_name: frame.copy() for table_name, frame in tables.items()}
    selected_accounts = _select_nova_accounts_by_prevalence(
        scenario_tables,
        scenario_prevalence=scenario_prevalence,
        prefer_lower_balance=False,
    )
    if selected_accounts.empty:
        return scenario_tables

    rows = _build_takeover_style_rows(
        scenario_tables,
        selected_accounts,
        scenario_name=scenario_name,
        primary_activity_type=primary_activity_type,
        velocity_activity_type=velocity_activity_type,
        noisy_outcome_rate=noisy_outcome_rate,
        detection_signal=detection_signal,
        beneficiary_change_event=beneficiary_change_event,
        session_event=session_event,
    )
    _append_rows(scenario_tables, SESSIONS, rows["sessions"])
    _append_rows(scenario_tables, PAYMENT_BENEFICIARIES, rows["beneficiaries"])
    _append_rows(scenario_tables, TRANSACTIONS, rows["transactions"])
    _append_rows(scenario_tables, SUSPICIOUS_ACTIVITIES, rows["activities"])
    _append_rows(scenario_tables, ALERTS, rows["alerts"])
    _append_rows(scenario_tables, CASES, rows["cases"])
    _append_rows(scenario_tables, CASE_OUTCOMES, rows["outcomes"])
    _append_rows(scenario_tables, PROTECTED_SCENARIO_ANSWER_KEYS, rows["answer_keys"])
    return scenario_tables


def _select_nova_accounts_by_prevalence(
    tables: Mapping[str, pd.DataFrame],
    *,
    scenario_prevalence: float,
    prefer_lower_balance: bool,
    exclude_account_ids: frozenset[str] | None = None,
) -> pd.DataFrame:
    """Select deterministic NovaBank accounts for a scenario family.

    ``prefer_lower_balance=True`` sorts ascending so the lowest-balance accounts
    are selected first (used for onboarding-abuse / early-life mule selection).
    ``prefer_lower_balance=False`` sorts descending so the highest-balance
    accounts are selected first (used for account-takeover and
    suspicious-beneficiary-change).

    ``exclude_account_ids`` skips accounts whose lifecycle a prior injection has
    already rewritten (for example ``opened_at``), so a later injection targets a
    disjoint account set and never corrupts another injection's account lifecycle.
    """
    accounts = tables[ACCOUNTS]
    digital_accounts = accounts[accounts["institution_name"] == NOVABANK].copy()
    if digital_accounts.empty or scenario_prevalence == 0:
        return digital_accounts.iloc[0:0]

    if exclude_account_ids:
        digital_accounts = digital_accounts[
            ~digital_accounts["account_id"].isin(exclude_account_ids)
        ]
    if digital_accounts.empty:
        return digital_accounts.iloc[0:0]

    target_count = min(
        len(digital_accounts),
        max(1, math.ceil(len(accounts[accounts["institution_name"] == NOVABANK]) * scenario_prevalence)),
    )
    digital_accounts = digital_accounts.copy()
    digital_accounts["balance_chf_numeric"] = digital_accounts["balance_chf"].map(float)
    sort_ascending = [True, True] if prefer_lower_balance else [False, True]
    return digital_accounts.sort_values(
        ["balance_chf_numeric", "account_id"],
        ascending=sort_ascending,
    ).head(target_count)


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
                "status_effective_from": incoming_at - pd.Timedelta(days=2),
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
                "status_updated_at": pass_through_at + pd.Timedelta(minutes=38),
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
                "closed_at": pass_through_at + pd.Timedelta(days=1),
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
                "recorded_at": pass_through_at + pd.Timedelta(days=1, hours=1),
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
        tables[ACCOUNTS].loc[account_mask, "status_effective_from"] = update[
            "status_effective_from"
        ]


def _build_takeover_style_rows(
    tables: Mapping[str, pd.DataFrame],
    selected_accounts: pd.DataFrame,
    *,
    scenario_name: str,
    primary_activity_type: str,
    velocity_activity_type: str | None,
    noisy_outcome_rate: float,
    detection_signal: str,
    beneficiary_change_event: str,
    session_event: str,
) -> dict[str, list[dict[str, object]]]:
    """Build rows for account-takeover and suspicious-beneficiary-change scenarios."""
    users_by_client = _primary_users_by_client(tables[USERS])
    relationships = tables["banking_relationships"].set_index("banking_relationship_id")
    session_index = _next_identifier_index(tables[SESSIONS], "session_id")
    beneficiary_index = _next_identifier_index(
        tables[PAYMENT_BENEFICIARIES], "payment_beneficiary_id"
    )
    transaction_index = _next_identifier_index(tables[TRANSACTIONS], "transaction_id")
    activity_index = _next_identifier_index(tables[SUSPICIOUS_ACTIVITIES], "suspicious_activity_id")
    alert_index = _next_identifier_index(tables[ALERTS], "alert_id")
    case_index = _next_identifier_index(tables[CASES], "case_id")
    outcome_index = _next_identifier_index(tables[CASE_OUTCOMES], "case_outcome_id")
    answer_key_index = _next_identifier_index(
        tables[PROTECTED_SCENARIO_ANSWER_KEYS], "answer_key_id"
    )

    sessions: list[dict[str, object]] = []
    beneficiaries: list[dict[str, object]] = []
    transactions: list[dict[str, object]] = []
    activities: list[dict[str, object]] = []
    alerts: list[dict[str, object]] = []
    cases: list[dict[str, object]] = []
    outcomes: list[dict[str, object]] = []
    answer_keys: list[dict[str, object]] = []
    takeover_device_hash = "dev_ato_takeover_network_002"

    for offset, account in enumerate(selected_accounts.itertuples(index=False)):
        relationship = relationships.loc[account.banking_relationship_id]
        client_id = str(relationship["primary_client_id"])
        user = users_by_client.loc[client_id]
        user_id = str(user["user_id"])
        event_at = pd.Timestamp(user["created_at"]) + pd.Timedelta(days=20, hours=offset)
        payment_amount = Decimal(1900 + offset * 540).quantize(MONEY_QUANT)

        session_id = _identifier("S", session_index)
        session_index += 1
        beneficiary_id = _identifier("B", beneficiary_index)
        beneficiary_index += 1
        transaction_id = _identifier("T", transaction_index)
        transaction_index += 1
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

        sessions.append(
            _session_row(
                session_id=session_id,
                user_id=user_id,
                started_at=event_at - pd.Timedelta(minutes=15),
                device_fingerprint_hash=takeover_device_hash,
                session_event=session_event,
            )
        )
        beneficiaries.append(
            {
                "payment_beneficiary_id": beneficiary_id,
                "client_id": client_id,
                "added_by_user_id": user_id,
                "beneficiary_name": f"Nova takeover recipient {offset + 1}",
                "beneficiary_account_country": "RU",
                "beneficiary_bank_country": "RU",
                "beneficiary_change_event": beneficiary_change_event,
                "created_at": event_at - pd.Timedelta(minutes=20),
                "status": "active",
            }
        )
        transactions.append(
            {
                "transaction_id": transaction_id,
                "account_id": account.account_id,
                "payment_beneficiary_id": beneficiary_id,
                "booked_at": event_at,
                "transaction_type": "instant_payment",
                "channel": "mobile_app",
                "direction": "debit",
                "amount_original": payment_amount,
                "currency": "CHF",
                "amount_chf": payment_amount,
                "description": "Takeover-style outbound payment to newly changed beneficiary",
            }
        )
        activities.append(
            {
                "suspicious_activity_id": activity_id,
                "institution_name": NOVABANK,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "transaction_id": transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "activity_type": primary_activity_type,
                "detected_at": event_at + pd.Timedelta(minutes=4),
                "detection_signal": detection_signal,
                "suspected_amount_chf": payment_amount,
                "review_priority": "high",
            }
        )
        velocity_reason = (
            " Elevated session payment velocity also flagged under "
            "session_payment_velocity."
            if velocity_activity_type is not None
            else ""
        )
        alerts.append(
            {
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "triggered_transaction_id": transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "institution_name": NOVABANK,
                "generated_at": event_at + pd.Timedelta(minutes=7),
                "alert_type": primary_activity_type,
                "alert_status": "closed",
                "status_updated_at": event_at + pd.Timedelta(minutes=40),
                "severity": "high",
                "reason": detection_signal + velocity_reason,
            }
        )
        cases.append(
            {
                "case_id": case_id,
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "transaction_id": transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "opened_at": event_at + pd.Timedelta(hours=3),
                "assigned_team": "digital investigations",
                "case_status": "closed",
                "closed_at": event_at + pd.Timedelta(days=2),
                "investigation_summary": (
                    "Case reviewed session, device, beneficiary-change, and payment "
                    "velocity context for the takeover-style activity."
                ),
            }
        )
        outcome, answer_key = _build_scenario_outcome_with_noise(
            outcome_id=outcome_id,
            answer_key_id=answer_key_id,
            case_id=case_id,
            scenario_name=scenario_name,
            decided_at=event_at + pd.Timedelta(hours=3, days=1),
            transaction_id=transaction_id,
            loss_amount=payment_amount,
            case_index=offset,
            noisy_outcome_rate=noisy_outcome_rate,
        )
        outcomes.append(outcome)
        answer_keys.append(answer_key)

    return {
        "sessions": sessions,
        "beneficiaries": beneficiaries,
        "transactions": transactions,
        "activities": activities,
        "alerts": alerts,
        "cases": cases,
        "outcomes": outcomes,
        "answer_keys": answer_keys,
    }


def _build_onboarding_abuse_rows(
    tables: Mapping[str, pd.DataFrame],
    selected_accounts: pd.DataFrame,
    *,
    noisy_outcome_rate: float = 0.0,
) -> dict[str, list[dict[str, object]]]:
    """Build rows for the onboarding-abuse scenario under the scam-to-mule pattern."""
    users_by_client = _primary_users_by_client(tables[USERS])
    relationships = tables["banking_relationships"].set_index("banking_relationship_id")
    session_index = _next_identifier_index(tables[SESSIONS], "session_id")
    beneficiary_index = _next_identifier_index(
        tables[PAYMENT_BENEFICIARIES], "payment_beneficiary_id"
    )
    transaction_index = _next_identifier_index(tables[TRANSACTIONS], "transaction_id")
    activity_index = _next_identifier_index(tables[SUSPICIOUS_ACTIVITIES], "suspicious_activity_id")
    alert_index = _next_identifier_index(tables[ALERTS], "alert_id")
    case_index = _next_identifier_index(tables[CASES], "case_id")
    outcome_index = _next_identifier_index(tables[CASE_OUTCOMES], "case_outcome_id")
    answer_key_index = _next_identifier_index(
        tables[PROTECTED_SCENARIO_ANSWER_KEYS], "answer_key_id"
    )

    account_updates: list[dict[str, object]] = []
    sessions: list[dict[str, object]] = []
    beneficiaries: list[dict[str, object]] = []
    transactions: list[dict[str, object]] = []
    activities: list[dict[str, object]] = []
    alerts: list[dict[str, object]] = []
    cases: list[dict[str, object]] = []
    outcomes: list[dict[str, object]] = []
    answer_keys: list[dict[str, object]] = []
    onboarding_device_hash = "dev_onboarding_abuse_003"

    for offset, account in enumerate(selected_accounts.itertuples(index=False)):
        relationship = relationships.loc[account.banking_relationship_id]
        client_id = str(relationship["primary_client_id"])
        user = users_by_client.loc[client_id]
        user_id = str(user["user_id"])
        onboarding_at = pd.Timestamp(user["created_at"]) + pd.Timedelta(days=3, hours=offset)
        incoming_amount = Decimal(1500 + offset * 410).quantize(MONEY_QUANT)
        onward_amount = (incoming_amount * Decimal("0.95")).quantize(MONEY_QUANT)

        session_id = _identifier("S", session_index)
        session_index += 1
        beneficiary_id = _identifier("B", beneficiary_index)
        beneficiary_index += 1
        incoming_transaction_id = _identifier("T", transaction_index)
        onward_transaction_id = _identifier("T", transaction_index + 1)
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

        account_updates.append(
            {
                "account_id": account.account_id,
                "opened_at": onboarding_at - pd.Timedelta(days=1),
                "status_effective_from": onboarding_at - pd.Timedelta(days=1),
            }
        )
        sessions.append(
            _session_row(
                session_id=session_id,
                user_id=user_id,
                started_at=onboarding_at - pd.Timedelta(minutes=10),
                device_fingerprint_hash=onboarding_device_hash,
                session_event="payment_authorized",
            )
        )
        beneficiaries.append(
            {
                "payment_beneficiary_id": beneficiary_id,
                "client_id": client_id,
                "added_by_user_id": user_id,
                "beneficiary_name": f"Nova onboarding recipient {offset + 1}",
                "beneficiary_account_country": "BG",
                "beneficiary_bank_country": "BG",
                "beneficiary_change_event": "new_beneficiary_added",
                "created_at": onboarding_at - pd.Timedelta(minutes=15),
                "status": "active",
            }
        )
        transactions.extend(
            [
                {
                    "transaction_id": incoming_transaction_id,
                    "account_id": account.account_id,
                    "payment_beneficiary_id": None,
                    "booked_at": onboarding_at,
                    "transaction_type": "instant_payment",
                    "channel": "mobile_app",
                    "direction": "credit",
                    "amount_original": incoming_amount,
                    "currency": "CHF",
                    "amount_chf": incoming_amount,
                    "description": "Incoming funds into a recently onboarded NovaBank account",
                },
                {
                    "transaction_id": onward_transaction_id,
                    "account_id": account.account_id,
                    "payment_beneficiary_id": beneficiary_id,
                    "booked_at": onboarding_at + pd.Timedelta(minutes=35),
                    "transaction_type": "instant_payment",
                    "channel": "mobile_app",
                    "direction": "debit",
                    "amount_original": onward_amount,
                    "currency": "CHF",
                    "amount_chf": onward_amount,
                    "description": "Rapid onward payment from an onboarding-abuse account",
                },
            ]
        )
        activities.append(
            {
                "suspicious_activity_id": activity_id,
                "institution_name": NOVABANK,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "transaction_id": onward_transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "activity_type": ONBOARDING_ABUSE_ACTIVITY_TYPE,
                "detected_at": onboarding_at + pd.Timedelta(minutes=40),
                "detection_signal": (
                    "Recently onboarded account received incoming funds and rapidly "
                    "moved them onward to a new beneficiary, consistent with "
                    "onboarding-abuse under the digital scam-to-mule pattern."
                ),
                "suspected_amount_chf": onward_amount,
                "review_priority": "high",
            }
        )
        alerts.append(
            {
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "triggered_transaction_id": onward_transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "institution_name": NOVABANK,
                "generated_at": onboarding_at + pd.Timedelta(minutes=44),
                "alert_type": ONBOARDING_ABUSE_ACTIVITY_TYPE,
                "alert_status": "closed",
                "status_updated_at": onboarding_at + pd.Timedelta(hours=1),
                "severity": "high",
                "reason": (
                    "Onboarding-abuse flow with rapid onward movement to a new "
                    "beneficiary from a recently opened account."
                ),
            }
        )
        cases.append(
            {
                "case_id": case_id,
                "alert_id": alert_id,
                "suspicious_activity_id": activity_id,
                "banking_relationship_id": account.banking_relationship_id,
                "account_id": account.account_id,
                "transaction_id": onward_transaction_id,
                "user_id": user_id,
                "session_id": session_id,
                "payment_beneficiary_id": beneficiary_id,
                "opened_at": onboarding_at + pd.Timedelta(hours=3),
                "assigned_team": "digital investigations",
                "case_status": "closed",
                "closed_at": onboarding_at + pd.Timedelta(days=1),
                "investigation_summary": (
                    "Case reviewed onboarding recency, beneficiary novelty, and "
                    "rapid onward payment velocity."
                ),
            }
        )
        outcome, answer_key = _build_scenario_outcome_with_noise(
            outcome_id=outcome_id,
            answer_key_id=answer_key_id,
            case_id=case_id,
            scenario_name=ONBOARDING_ABUSE_SCENARIO_NAME,
            decided_at=onboarding_at + pd.Timedelta(days=1),
            transaction_id=onward_transaction_id,
            loss_amount=onward_amount,
            case_index=offset,
            noisy_outcome_rate=noisy_outcome_rate,
        )
        outcomes.append(outcome)
        answer_keys.append(answer_key)

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


def _build_scenario_outcome_with_noise(
    *,
    outcome_id: str,
    answer_key_id: str,
    case_id: str,
    scenario_name: str,
    decided_at: pd.Timestamp,
    transaction_id: str,
    loss_amount: Decimal,
    case_index: int,
    noisy_outcome_rate: float,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build a case outcome and protected answer key with deliberate label noise.

    ``decided_at`` is the outcome decision timestamp; callers must pass a value
    that respects the case ``closed_at`` (decided at or before closure) and the
    lifecycle ordering invariants (decided at or after ``opened_at``).

    A deterministic subset of cases (controlled by ``noisy_outcome_rate``) receive
    a triage outcome that disagrees with the true protected label, so
    confirmed-fraud is an imperfect, explainable signal:

    - Even-indexed noisy cases are *uninvestigated-but-fraud*: the triage outcome
      is ``unresolved`` with ``confirmed_fraud=False`` even though the protected
      answer key records ``true_confirmed_fraud``.
    - Odd-indexed noisy cases are *confirmed-but-benign*: the triage outcome is
      ``confirmed-fraud`` with ``confirmed_fraud=True`` even though the protected
      answer key records ``true_false_positive``.
    """
    noise_period = max(1, round(1.0 / noisy_outcome_rate)) if noisy_outcome_rate > 0 else 0
    # Note: noise selection is intentionally deterministic and anchored at the
    # first case of each family (case_index 0). This guarantees both noise
    # directions (uninvestigated-but-fraud and confirmed-but-benign) appear in
    # the small learner datasets regardless of the requested rate. Tests rely on
    # this determinism to find noisy outcomes.
    is_noisy = noisy_outcome_rate > 0 and (case_index % noise_period == 0)
    uninvestigated_noise = is_noisy and (case_index // max(noise_period, 1)) % 2 == 0

    if is_noisy and uninvestigated_noise:
        outcome = {
            "case_outcome_id": outcome_id,
            "case_id": case_id,
            "decided_at": decided_at,
            "recorded_at": decided_at + pd.Timedelta(hours=1),
            "outcome_type": "unresolved",
            "confirmed_fraud": False,
            "loss_amount_original": MONEY_ZERO,
            "loss_currency": "CHF",
            "loss_amount_chf": MONEY_ZERO,
            "notes": (
                "Case closed without a fraud confirmation due to investigation "
                "capacity limits; the triage outcome is intentionally noisy."
            ),
        }
        true_label = LABEL_TRUE_FRAUD
    elif is_noisy:
        outcome = {
            "case_outcome_id": outcome_id,
            "case_id": case_id,
            "decided_at": decided_at,
            "recorded_at": decided_at + pd.Timedelta(hours=1),
            "outcome_type": "confirmed-fraud",
            "confirmed_fraud": True,
            "loss_amount_original": loss_amount,
            "loss_currency": "CHF",
            "loss_amount_chf": loss_amount,
            "notes": (
                "Case confirmed as fraud on review, but the underlying activity was "
                "legitimate; the triage outcome is intentionally noisy."
            ),
        }
        true_label = LABEL_TRUE_BENIGN
    else:
        outcome = {
            "case_outcome_id": outcome_id,
            "case_id": case_id,
            "decided_at": decided_at,
            "recorded_at": decided_at + pd.Timedelta(hours=1),
            "outcome_type": "confirmed-fraud",
            "confirmed_fraud": True,
            "loss_amount_original": loss_amount,
            "loss_currency": "CHF",
            "loss_amount_chf": loss_amount,
            "notes": (
                "Scenario activity confirmed as fraud; protected answer keys stay "
                "separate from learner-facing outputs."
            ),
        }
        true_label = LABEL_TRUE_FRAUD

    answer_key = {
        "answer_key_id": answer_key_id,
        "scenario_name": scenario_name,
        "entity_table": TRANSACTIONS,
        "entity_id": transaction_id,
        "label_type": "scenario_label",
        "label_value": true_label,
        "available_to_learners": False,
    }
    return outcome, answer_key


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
    "ACCOUNT_TAKEOVER_BENEFICIARY_ACTIVITY_TYPE",
    "ACCOUNT_TAKEOVER_SCENARIO_NAME",
    "ACCOUNT_TAKEOVER_VELOCITY_ACTIVITY_TYPE",
    "DIGITAL_SCAM_TO_MULE_ACTIVITY_TYPE",
    "DIGITAL_SCAM_TO_MULE_SCENARIO_NAME",
    "LABEL_TRUE_BENIGN",
    "LABEL_TRUE_FRAUD",
    "ONBOARDING_ABUSE_ACTIVITY_TYPE",
    "ONBOARDING_ABUSE_SCENARIO_NAME",
    "SUSPICIOUS_BENEFICIARY_CHANGE_ACTIVITY_TYPE",
    "SUSPICIOUS_BENEFICIARY_CHANGE_SCENARIO_NAME",
    "generate_digital_fraud_scenarios_world",
    "generate_digital_scam_to_mule_world",
    "generate_learner_facing_digital_fraud_scenarios_world",
    "generate_learner_facing_digital_scam_to_mule_world",
    "inject_account_takeover_scenario",
    "inject_digital_fraud_scenarios",
    "inject_digital_scam_to_mule_flow",
    "inject_onboarding_abuse_scenario",
    "inject_suspicious_beneficiary_change_scenario",
]
