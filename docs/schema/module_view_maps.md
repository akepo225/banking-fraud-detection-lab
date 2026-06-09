# Module View Maps

Module view maps show how foundation Progressive data views derive from
canonical tables. They keep **Partner**, **Client**, **User**, **Banking
relationship**, **Detection pattern**, and **Alert lifecycle** language aligned
with `CONTEXT.md` while giving learners a smaller starting surface.

This v0.2 map covers the required `00_foundations` path. Later releases may add
track-specific maps, but those should remain additive to the canonical schema.

## `foundation_client_relationships`

Introduces Clients, Partners, and Banking relationships in one traceable
foundation view before learners work across canonical tables.

Module path:

- `00_foundations`

Source tables:

- `clients`
- `partners`
- `banking_relationships`

Stable cross-reference surface:

- `client_id`
- `partner_id`
- `banking_relationship_id`

Columns:

| Column | Canonical source |
| --- | --- |
| `client_id` | `clients.client_id` |
| `partner_id` | `clients.partner_id` |
| `institution_name` | `clients.institution_name` |
| `client_segment` | `clients.client_segment` |
| `client_status` | `clients.status` |
| `partner_type` | `partners.partner_type` |
| `partner_country` | `partners.country` |
| `risk_rating` | `partners.risk_rating` |
| `kyc_risk_effective_from` | `partners.kyc_risk_effective_from` |
| `kyc_risk_reviewed_at` | `partners.kyc_risk_reviewed_at` |
| `banking_relationship_id` | `banking_relationships.banking_relationship_id` |
| `relationship_name` | `banking_relationships.relationship_name` |
| `relationship_status` | `banking_relationships.status` |
| `relationship_opened_at` | `banking_relationships.opened_at` |
| `relationship_manager_code` | `banking_relationships.relationship_manager_code` |
| `relationship_manager_assigned_at` | `banking_relationships.relationship_manager_assigned_at` |

## `pb_relationship_context`

Exposes one row per Banking relationship with current relationship-manager
history for private-banking relationship-context exercises.

Module path:

- `01_private_banking_transaction_fraud`

Source tables:

- `banking_relationships`
- `relationship_manager_history`

Learner use:

- Inspect current relationship-manager context for private-banking relationship
  analytics before querying effective-dated history directly.
- Keep one row per Banking relationship so feature exercises can join accounts,
  transactions, roles, and alerts deliberately.

Columns:

| Column | Canonical source |
| --- | --- |
| `banking_relationship_id` | `banking_relationships.banking_relationship_id` |
| `primary_client_id` | `banking_relationships.primary_client_id` |
| `institution_name` | `banking_relationships.institution_name` |
| `relationship_name` | `banking_relationships.relationship_name` |
| `relationship_opened_at` | `banking_relationships.opened_at` |
| `relationship_status` | `banking_relationships.status` |
| `relationship_manager_code` | `relationship_manager_history.relationship_manager_code` |
| `rm_effective_from` | `relationship_manager_history.effective_from` |
| `rm_effective_to` | `relationship_manager_history.effective_to` |

## `foundation_alert_lifecycle`

Shows the Alert lifecycle from suspicious activity through alert, case, and case
outcome while keeping protected scenario answer keys separate.

Module path:

- `00_foundations`

Source tables:

- `suspicious_activities`
- `alerts`
- `cases`
- `case_outcomes`

Learner use:

- Inspect a **Detection pattern** observation and its downstream **Alert
  lifecycle** state in one view.
- Keep unanswered or uninvestigated lifecycle stages visible with nullable case
  and outcome columns.
- Avoid `protected_scenario_answer_keys` in learner-facing SQL and notebook
  exercises.

Columns:

| Column | Canonical source |
| --- | --- |
| `suspicious_activity_id` | `suspicious_activities.suspicious_activity_id` |
| `alert_id` | `alerts.alert_id` |
| `case_id` | `cases.case_id` |
| `case_outcome_id` | `case_outcomes.case_outcome_id` |
| `institution_name` | `suspicious_activities.institution_name` |
| `banking_relationship_id` | `suspicious_activities.banking_relationship_id` |
| `account_id` | `suspicious_activities.account_id` |
| `transaction_id` | `suspicious_activities.transaction_id` |
| `user_id` | `suspicious_activities.user_id` |
| `session_id` | `suspicious_activities.session_id` |
| `payment_beneficiary_id` | `suspicious_activities.payment_beneficiary_id` |
| `activity_type` | `suspicious_activities.activity_type` |
| `detected_at` | `suspicious_activities.detected_at` |
| `detection_signal` | `suspicious_activities.detection_signal` |
| `suspected_amount_chf` | `suspicious_activities.suspected_amount_chf` |
| `review_priority` | `suspicious_activities.review_priority` |
| `generated_at` | `alerts.generated_at` |
| `alert_type` | `alerts.alert_type` |
| `alert_status` | `alerts.alert_status` |
| `status_updated_at` | `alerts.status_updated_at` |
| `severity` | `alerts.severity` |
| `opened_at` | `cases.opened_at` |
| `assigned_team` | `cases.assigned_team` |
| `case_status` | `cases.case_status` |
| `closed_at` | `cases.closed_at` |
| `decided_at` | `case_outcomes.decided_at` |
| `recorded_at` | `case_outcomes.recorded_at` |
| `outcome_type` | `case_outcomes.outcome_type` |
| `confirmed_fraud` | `case_outcomes.confirmed_fraud` |
| `loss_amount_chf` | `case_outcomes.loss_amount_chf` |
