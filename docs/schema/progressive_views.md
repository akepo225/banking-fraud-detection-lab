# Progressive Data Views

Progressive data views are simplified, traceable extracts from the canonical
synthetic data model. They are learner-facing query surfaces, not separate
schemas. Each view keeps its source tables visible so learners can move from the
simplified foundation surface back to canonical tables when later modules need
more detail.

SQLite databases created by the loader expose these contracts as SQLite `VIEW`s.
Python users can build the same views with
`build_foundation_progressive_views(tables)`.

## `foundation_client_relationships`

Introduces Clients, Partners, and Banking relationships in one traceable
foundation view before learners work across canonical tables.

This view is stable for future v0.5 case-pack cross-references. Case packs may
use `client_id`, `partner_id`, and `banking_relationship_id` from this view when
they need a compact Client and Banking relationship anchor.

Source tables:

- `clients`
- `partners`
- `banking_relationships`

Columns:

| Column | Learner purpose |
| --- | --- |
| `client_id` | Client identifier for the legal customer. |
| `partner_id` | Partner record that represents the Client. |
| `institution_name` | Fictional institution owning the records. |
| `client_segment` | Segment context for early cohorting. |
| `client_status` | Current Client status. |
| `partner_type` | Natural-person or legal-entity context. |
| `partner_country` | Primary Partner country. |
| `risk_rating` | Current KYC risk band. |
| `kyc_risk_effective_from` | When the current KYC risk band became effective. |
| `kyc_risk_reviewed_at` | When the current KYC risk band was reviewed. |
| `banking_relationship_id` | Banking relationship container identifier. |
| `relationship_name` | Learner-readable relationship label. |
| `relationship_status` | Current Banking relationship status. |
| `relationship_opened_at` | Banking relationship opening timestamp. |
| `relationship_manager_code` | Synthetic relationship manager assignment code. |
| `relationship_manager_assigned_at` | When the relationship manager assignment became effective. |

## `pb_relationship_context`

Exposes one row per Banking relationship with relationship AUM and current
relationship-manager history for private-banking relationship-context exercises.

This view supports private-banking lessons that need relationship-manager
context before learners work directly with effective-dated history tables. It
is module-specific and is not marked as a stable cross-module case-reference
surface.

Source tables:

- `banking_relationships`
- `relationship_manager_history`

Columns:

| Column | Learner purpose |
| --- | --- |
| `banking_relationship_id` | Banking relationship container identifier. |
| `primary_client_id` | Primary legal Client for the relationship. |
| `institution_name` | Fictional institution owning the relationship. |
| `relationship_name` | Learner-readable relationship label. |
| `relationship_opened_at` | Banking relationship opening timestamp. |
| `relationship_status` | Current Banking relationship status. |
| `aum_chf` | Relationship-level CHF assets under management context. |
| `relationship_manager_code` | Current synthetic relationship manager assignment code. |
| `rm_effective_from` | When the current relationship manager assignment became effective. |
| `rm_effective_to` | When the current relationship manager assignment ended, if superseded. |

## `foundation_alert_lifecycle`

Shows the Alert lifecycle from suspicious activity through alert, case, and case
outcome while keeping protected scenario answer keys separate.

This view is for foundation lessons that need to inspect lifecycle state without
joining four tables immediately. It keeps one row per suspicious activity, so
alerts that have not opened a case are still visible.

Source tables:

- `suspicious_activities`
- `alerts`
- `cases`
- `case_outcomes`

Columns:

| Column | Learner purpose |
| --- | --- |
| `suspicious_activity_id` | Suspicious activity observation. |
| `alert_id` | Alert generated from the suspicious activity, if present. |
| `case_id` | Case opened from the alert, if present. |
| `case_outcome_id` | Outcome assigned to the case, if present. |
| `institution_name` | Fictional institution owning the lifecycle row. |
| `banking_relationship_id` | Banking relationship linked to the activity. |
| `account_id` | Account linked to the activity. |
| `transaction_id` | Transaction that carried the suspicious activity. |
| `user_id` | Digital login identity when the activity is digital. |
| `session_id` | Digital session when applicable. |
| `payment_beneficiary_id` | Payment beneficiary when applicable. |
| `activity_type` | Detection pattern observed. |
| `detected_at` | Suspicious activity detection timestamp. |
| `detection_signal` | Learner-readable detection signal. |
| `suspected_amount_chf` | CHF-normalized amount under review. |
| `review_priority` | Review priority at suspicious-activity stage. |
| `generated_at` | Alert generation timestamp. |
| `alert_type` | Alert typology or rule family. |
| `alert_status` | Current alert status. |
| `status_updated_at` | When the current alert status was assigned. |
| `severity` | Alert severity. |
| `opened_at` | Case opening timestamp, if a case exists. |
| `assigned_team` | Investigation team assignment. |
| `case_status` | Current case status. |
| `closed_at` | Case closure timestamp, if closed. |
| `decided_at` | Outcome decision timestamp, if decided. |
| `recorded_at` | Outcome recording timestamp, if recorded. |
| `outcome_type` | Outcome classification, if present. |
| `confirmed_fraud` | Case outcome fraud determination, if present. |
| `loss_amount_chf` | CHF-normalized loss amount, if present. |

The view intentionally excludes `protected_scenario_answer_keys` and all
protected answer-key columns such as `available_to_learners`, `label_type`, and
`label_value`.
