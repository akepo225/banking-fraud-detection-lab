"""Foundation-level Progressive data view contracts and builders."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from banking_fraud_lab.schema import (
    ALERTS,
    BANKING_RELATIONSHIPS,
    CASE_OUTCOMES,
    CASES,
    CLIENTS,
    PARTNERS,
    RELATIONSHIP_MANAGER_HISTORY,
    SUSPICIOUS_ACTIVITIES,
)


@dataclass(frozen=True)
class ProgressiveViewSpec:
    """Stable contract for one learner-facing Progressive data view."""

    name: str
    purpose: str
    source_tables: tuple[str, ...]
    columns: tuple[str, ...]
    stable_for_case_references: bool = False


FOUNDATION_CLIENT_RELATIONSHIPS = ProgressiveViewSpec(
    name="foundation_client_relationships",
    purpose=(
        "Introduces Clients, Partners, and Banking relationships in one "
        "traceable foundation view before learners work across canonical tables."
    ),
    source_tables=(CLIENTS, PARTNERS, BANKING_RELATIONSHIPS),
    columns=(
        "client_id",
        "partner_id",
        "institution_name",
        "client_segment",
        "client_status",
        "partner_type",
        "partner_country",
        "risk_rating",
        "kyc_risk_effective_from",
        "kyc_risk_reviewed_at",
        "banking_relationship_id",
        "relationship_name",
        "relationship_status",
        "relationship_opened_at",
        "relationship_manager_code",
        "relationship_manager_assigned_at",
    ),
    stable_for_case_references=True,
)

FOUNDATION_ALERT_LIFECYCLE = ProgressiveViewSpec(
    name="foundation_alert_lifecycle",
    purpose=(
        "Shows the Alert lifecycle from suspicious activity through alert, case, "
        "and case outcome while keeping protected scenario answer keys separate."
    ),
    source_tables=(SUSPICIOUS_ACTIVITIES, ALERTS, CASES, CASE_OUTCOMES),
    columns=(
        "suspicious_activity_id",
        "alert_id",
        "case_id",
        "case_outcome_id",
        "institution_name",
        "banking_relationship_id",
        "account_id",
        "transaction_id",
        "user_id",
        "session_id",
        "payment_beneficiary_id",
        "activity_type",
        "detected_at",
        "detection_signal",
        "suspected_amount_chf",
        "review_priority",
        "generated_at",
        "alert_type",
        "alert_status",
        "status_updated_at",
        "severity",
        "opened_at",
        "assigned_team",
        "case_status",
        "closed_at",
        "decided_at",
        "recorded_at",
        "outcome_type",
        "confirmed_fraud",
        "loss_amount_chf",
    ),
)

PB_RELATIONSHIP_CONTEXT = ProgressiveViewSpec(
    name="pb_relationship_context",
    purpose=(
        "Exposes one row per Banking relationship with relationship AUM and current "
        "relationship-manager history for private-banking relationship-context exercises."
    ),
    source_tables=(BANKING_RELATIONSHIPS, RELATIONSHIP_MANAGER_HISTORY),
    columns=(
        "banking_relationship_id",
        "primary_client_id",
        "institution_name",
        "relationship_name",
        "relationship_opened_at",
        "relationship_status",
        "aum_chf",
        "relationship_manager_code",
        "rm_effective_from",
        "rm_effective_to",
    ),
)

FOUNDATION_PROGRESSIVE_VIEW_SPECS = (
    FOUNDATION_CLIENT_RELATIONSHIPS,
    PB_RELATIONSHIP_CONTEXT,
    FOUNDATION_ALERT_LIFECYCLE,
)

FOUNDATION_PROGRESSIVE_VIEW_SQL = {
    FOUNDATION_CLIENT_RELATIONSHIPS.name: """
CREATE VIEW "foundation_client_relationships" AS
SELECT
  c."client_id" AS "client_id",
  c."partner_id" AS "partner_id",
  c."institution_name" AS "institution_name",
  c."client_segment" AS "client_segment",
  c."status" AS "client_status",
  p."partner_type" AS "partner_type",
  p."country" AS "partner_country",
  p."risk_rating" AS "risk_rating",
  p."kyc_risk_effective_from" AS "kyc_risk_effective_from",
  p."kyc_risk_reviewed_at" AS "kyc_risk_reviewed_at",
  br."banking_relationship_id" AS "banking_relationship_id",
  br."relationship_name" AS "relationship_name",
  br."status" AS "relationship_status",
  br."opened_at" AS "relationship_opened_at",
  br."relationship_manager_code" AS "relationship_manager_code",
  br."relationship_manager_assigned_at" AS "relationship_manager_assigned_at"
FROM "clients" AS c
JOIN "partners" AS p
  ON p."partner_id" = c."partner_id"
 AND p."institution_name" = c."institution_name"
JOIN "banking_relationships" AS br
  ON br."primary_client_id" = c."client_id"
 AND br."institution_name" = c."institution_name"
""",
    PB_RELATIONSHIP_CONTEXT.name: """
CREATE VIEW "pb_relationship_context" AS
SELECT
  br."banking_relationship_id" AS "banking_relationship_id",
  br."primary_client_id" AS "primary_client_id",
  br."institution_name" AS "institution_name",
  br."relationship_name" AS "relationship_name",
  br."opened_at" AS "relationship_opened_at",
  br."status" AS "relationship_status",
  br."aum_chf" AS "aum_chf",
  rmh."relationship_manager_code" AS "relationship_manager_code",
  rmh."effective_from" AS "rm_effective_from",
  rmh."effective_to" AS "rm_effective_to"
FROM "banking_relationships" AS br
LEFT JOIN (
  SELECT
    ranked_rmh."banking_relationship_id",
    ranked_rmh."relationship_manager_code",
    ranked_rmh."effective_from",
    ranked_rmh."effective_to"
  FROM (
    SELECT
      rmh_source."banking_relationship_id" AS "banking_relationship_id",
      rmh_source."relationship_manager_code" AS "relationship_manager_code",
      rmh_source."effective_from" AS "effective_from",
      rmh_source."effective_to" AS "effective_to",
      ROW_NUMBER() OVER (
        PARTITION BY rmh_source."banking_relationship_id"
        ORDER BY rmh_source."effective_from" DESC, rmh_source."rm_history_id" DESC
      ) AS "current_rank"
    FROM "relationship_manager_history" AS rmh_source
    WHERE rmh_source."effective_to" IS NULL
  ) AS ranked_rmh
  WHERE ranked_rmh."current_rank" = 1
) AS rmh
  ON rmh."banking_relationship_id" = br."banking_relationship_id"
""",
    FOUNDATION_ALERT_LIFECYCLE.name: """
CREATE VIEW "foundation_alert_lifecycle" AS
SELECT
  sa."suspicious_activity_id" AS "suspicious_activity_id",
  al."alert_id" AS "alert_id",
  ca."case_id" AS "case_id",
  co."case_outcome_id" AS "case_outcome_id",
  sa."institution_name" AS "institution_name",
  sa."banking_relationship_id" AS "banking_relationship_id",
  sa."account_id" AS "account_id",
  sa."transaction_id" AS "transaction_id",
  sa."user_id" AS "user_id",
  sa."session_id" AS "session_id",
  sa."payment_beneficiary_id" AS "payment_beneficiary_id",
  sa."activity_type" AS "activity_type",
  sa."detected_at" AS "detected_at",
  sa."detection_signal" AS "detection_signal",
  sa."suspected_amount_chf" AS "suspected_amount_chf",
  sa."review_priority" AS "review_priority",
  al."generated_at" AS "generated_at",
  al."alert_type" AS "alert_type",
  al."alert_status" AS "alert_status",
  al."status_updated_at" AS "status_updated_at",
  al."severity" AS "severity",
  ca."opened_at" AS "opened_at",
  ca."assigned_team" AS "assigned_team",
  ca."case_status" AS "case_status",
  ca."closed_at" AS "closed_at",
  co."decided_at" AS "decided_at",
  co."recorded_at" AS "recorded_at",
  co."outcome_type" AS "outcome_type",
  co."confirmed_fraud" AS "confirmed_fraud",
  co."loss_amount_chf" AS "loss_amount_chf"
FROM "suspicious_activities" AS sa
LEFT JOIN "alerts" AS al
  ON al."suspicious_activity_id" = sa."suspicious_activity_id"
LEFT JOIN "cases" AS ca
  ON ca."alert_id" = al."alert_id"
LEFT JOIN "case_outcomes" AS co
  ON co."case_id" = ca."case_id"
""",
}


def build_foundation_progressive_views(
    tables: Mapping[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Build foundation-level Progressive data views from canonical tables."""
    return {
        spec.name: build_foundation_progressive_view(spec.name, tables)
        for spec in FOUNDATION_PROGRESSIVE_VIEW_SPECS
    }


def build_foundation_progressive_view(
    view_name: str,
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build one foundation-level Progressive data view by name."""
    view_builders = {
        FOUNDATION_CLIENT_RELATIONSHIPS.name: _build_foundation_client_relationships,
        PB_RELATIONSHIP_CONTEXT.name: _build_pb_relationship_context,
        FOUNDATION_ALERT_LIFECYCLE.name: _build_foundation_alert_lifecycle,
    }
    try:
        builder = view_builders[view_name]
    except KeyError as error:
        raise ValueError(f"Unknown foundation Progressive data view: {view_name}") from error
    return builder(tables)


def _build_foundation_client_relationships(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return the foundation Client, Partner, and Banking relationship join."""
    _require_source_tables(FOUNDATION_CLIENT_RELATIONSHIPS, tables)

    clients = tables[CLIENTS][
        ["client_id", "partner_id", "institution_name", "client_segment", "status"]
    ].rename(columns={"status": "client_status"})
    partners = tables[PARTNERS][
        [
            "partner_id",
            "institution_name",
            "partner_type",
            "country",
            "risk_rating",
            "kyc_risk_effective_from",
            "kyc_risk_reviewed_at",
        ]
    ].rename(columns={"country": "partner_country"})
    relationships = tables[BANKING_RELATIONSHIPS][
        [
            "banking_relationship_id",
            "primary_client_id",
            "institution_name",
            "relationship_name",
            "opened_at",
            "status",
            "relationship_manager_code",
            "relationship_manager_assigned_at",
        ]
    ].rename(
        columns={
            "opened_at": "relationship_opened_at",
            "status": "relationship_status",
        }
    )

    view = clients.merge(
        partners,
        on=("partner_id", "institution_name"),
        how="inner",
        validate="one_to_one",
    ).merge(
        relationships,
        left_on=("client_id", "institution_name"),
        right_on=("primary_client_id", "institution_name"),
        how="inner",
        validate="one_to_many",
    )

    return view.loc[:, FOUNDATION_CLIENT_RELATIONSHIPS.columns].copy()


def _build_pb_relationship_context(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return the private-banking relationship context view with current RM history."""
    _require_source_tables(PB_RELATIONSHIP_CONTEXT, tables)

    relationships = tables[BANKING_RELATIONSHIPS][
        [
            "banking_relationship_id",
            "primary_client_id",
            "institution_name",
            "relationship_name",
            "opened_at",
            "status",
            "aum_chf",
        ]
    ].rename(
        columns={
            "opened_at": "relationship_opened_at",
            "status": "relationship_status",
        }
    )
    current_rm_history = tables[RELATIONSHIP_MANAGER_HISTORY][
        [
            "rm_history_id",
            "banking_relationship_id",
            "relationship_manager_code",
            "effective_from",
            "effective_to",
        ]
    ]
    current_rm_history = (
        current_rm_history[current_rm_history["effective_to"].isna()]
        .sort_values(
            ["banking_relationship_id", "effective_from", "rm_history_id"],
            ascending=[True, False, False],
            kind="stable",
        )
        .drop_duplicates("banking_relationship_id", keep="first")
        .drop(columns="rm_history_id")
        .rename(
            columns={
                "effective_from": "rm_effective_from",
                "effective_to": "rm_effective_to",
            }
        )
    )

    view = relationships.merge(
        current_rm_history,
        on="banking_relationship_id",
        how="left",
        validate="one_to_one",
    )

    return view.loc[:, PB_RELATIONSHIP_CONTEXT.columns].copy()


def _build_foundation_alert_lifecycle(
    tables: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Return the foundation Alert lifecycle view."""
    _require_source_tables(FOUNDATION_ALERT_LIFECYCLE, tables)

    suspicious_activities = tables[SUSPICIOUS_ACTIVITIES][
        [
            "suspicious_activity_id",
            "institution_name",
            "banking_relationship_id",
            "account_id",
            "transaction_id",
            "user_id",
            "session_id",
            "payment_beneficiary_id",
            "activity_type",
            "detected_at",
            "detection_signal",
            "suspected_amount_chf",
            "review_priority",
        ]
    ]
    alerts = tables[ALERTS][
        [
            "alert_id",
            "suspicious_activity_id",
            "generated_at",
            "alert_type",
            "alert_status",
            "status_updated_at",
            "severity",
        ]
    ]
    cases = tables[CASES][
        [
            "case_id",
            "alert_id",
            "opened_at",
            "assigned_team",
            "case_status",
            "closed_at",
        ]
    ]
    case_outcomes = tables[CASE_OUTCOMES][
        [
            "case_outcome_id",
            "case_id",
            "decided_at",
            "recorded_at",
            "outcome_type",
            "confirmed_fraud",
            "loss_amount_chf",
        ]
    ]

    view = (
        suspicious_activities.merge(
            alerts,
            on="suspicious_activity_id",
            how="left",
            validate="one_to_many",
        )
        .merge(cases, on="alert_id", how="left", validate="one_to_many")
        .merge(case_outcomes, on="case_id", how="left", validate="many_to_many")
    )

    return view.loc[:, FOUNDATION_ALERT_LIFECYCLE.columns].copy()


def _require_source_tables(
    spec: ProgressiveViewSpec,
    tables: Mapping[str, pd.DataFrame],
) -> None:
    """Raise a clear error when a Progressive view source table is missing."""
    missing_tables = sorted(set(spec.source_tables) - set(tables))
    if missing_tables:
        raise ValueError(
            f"{spec.name} requires source tables that are missing: {missing_tables}"
        )


__all__ = [
    "FOUNDATION_ALERT_LIFECYCLE",
    "FOUNDATION_CLIENT_RELATIONSHIPS",
    "FOUNDATION_PROGRESSIVE_VIEW_SPECS",
    "FOUNDATION_PROGRESSIVE_VIEW_SQL",
    "PB_RELATIONSHIP_CONTEXT",
    "ProgressiveViewSpec",
    "build_foundation_progressive_view",
    "build_foundation_progressive_views",
]
